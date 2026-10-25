import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'package:tideglass/native_services.dart';

class MemoryCredentials implements CredentialStore {
  final Map<String, String> values = {};
  bool fail = false, readFailure = false, deleteFailure = false;
  @override
  Future<String?> read(String key) async {
    if (readFailure) throw StateError('read failure');
    return values[key];
  }

  @override
  Future<void> write(String key, String value) async {
    if (fail) throw StateError('storage failure');
    values[key] = value;
  }

  @override
  Future<void> delete(String key) async {
    if (deleteFailure) throw StateError('delete failure');
    values.remove(key);
  }
}

class TestClient extends TideglassServiceClient {
  TestClient({String origin = 'https://example.invalid'})
    : super(endpoint: Uri.parse(origin));
  bool unavailable = false, grant = false;
  String identity = '00000000-0000-4000-8000-000000000001';
  Completer<void>? consentResponse;
  int verifies = 0;
  int maximumAge = 86400, observedAge = 0;
  String? seed = 'main.seed';
  @override
  Future<AccountCreated> createAccount({required bool cloudConsent}) async {
    session = ServiceSession(
      accountId: identity,
      token: 'secret-session',
      expiresAt: DateTime.utc(2030),
    );
    return AccountCreated(session!, 'retained-recovery-code');
  }

  @override
  Future<ServiceSession> recoverAccount({
    required String accountId,
    required String recoveryCode,
  }) async => (await createAccount(cloudConsent: true)).session;
  @override
  Future<AccountCreated> rotateRecoveryCode(
    String currentCode, {
    required String newRecoveryCode,
  }) async {
    final created = await createAccount(cloudConsent: true);
    return AccountCreated(created.session, newRecoveryCode);
  }

  @override
  Future<void> deleteAccount({
    required String recoveryCode,
    required bool confirmDelete,
  }) async {
    if (unavailable) throw const ServiceException('service_unavailable');
    session = null;
  }

  @override
  Future<void> signOut({bool allDevices = false}) async {
    if (unavailable) throw const ServiceException('service_unavailable');
    session = null;
  }

  @override
  Future<int> setTelemetryConsent(bool enabled) async {
    await consentResponse?.future;
    if (unavailable) throw const ServiceException('service_unavailable');
    return 1;
  }

  @override
  Future<Map<String, dynamic>> entitlements() async {
    if (unavailable) throw const ServiceException('service_unavailable');
    return {
      'account_id': session!.accountId,
      'linked_account_seed': seed,
      'verified_at': DateTime.now().millisecondsSinceEpoch ~/ 1000,
      'maximum_verification_age_seconds': maximumAge,
      'purchases': [
        {
          'product_id': 'dev.tideglass.pass.01',
          'state': grant ? 'purchased' : 'pending',
          'verification_id': 'receipt.pass',
          'updated':
              DateTime.now().millisecondsSinceEpoch ~/ 1000 - observedAge,
        },
      ],
      'entitlements': grant
          ? [
              {'id': 'pass.01', 'verification_receipt_id': 'receipt.pass'},
            ]
          : [],
    };
  }

  @override
  Future<Map<String, dynamic>> verifyPurchase({
    required String platform,
    required String proof,
  }) async {
    verifies++;
    if (unavailable) throw const ServiceException('verification_unavailable');
    final data = jsonDecode(proof) as Map;
    expect(data['expected_product_id'], 'dev.tideglass.pass.01');
    return {
      ...await entitlements(),
      'delivery_state': grant ? 'granted_awaiting_acknowledgement' : 'pending',
      'purchases': [
        {
          'product_id': 'dev.tideglass.pass.01',
          'state': grant ? 'purchased' : 'pending',
          'verification_id': 'receipt.pass',
          'updated':
              DateTime.now().millisecondsSinceEpoch ~/ 1000 - observedAge,
        },
      ],
    };
  }
}

class TestStore implements StoreGateway {
  final updates = StreamController<List<PurchaseDetails>>.broadcast();
  int completes = 0, queries = 0, buys = 0, restores = 0;
  String? boundAccount;
  @override
  Stream<List<PurchaseDetails>> get purchases => updates.stream;
  @override
  Future<bool> isAvailable() async => true;
  @override
  Future<ProductDetailsResponse> query(Set<String> products) async {
    queries++;
    return ProductDetailsResponse(
      productDetails: [
        ProductDetails(
          id: 'dev.tideglass.pass.01',
          title: 'Pass',
          description: 'Cosmetics',
          price: '₺249,99',
          rawPrice: 249.99,
          currencyCode: 'TRY',
        ),
      ],
      notFoundIDs: [],
    );
  }

  @override
  Future<bool> buy(ProductDetails product, String accountId) async {
    buys++;
    boundAccount = accountId;
    return true;
  }

  @override
  Future<void> restore(String accountId) async {
    restores++;
    boundAccount = accountId;
  }

  @override
  Future<void> complete(PurchaseDetails purchase) async {
    completes++;
    purchase.pendingCompletePurchase = false;
  }
}

class TestRewarded implements RewardedGateway {
  Completer<bool>? consent;
  Completer<NativeRewardedAd>? loading;
  final ad = TestRewardedAd();
  int loads = 0;
  @override
  Future<bool> requestConsent() async =>
      consent == null ? true : consent!.future;
  @override
  Future<NativeRewardedAd> load(String unitId) async {
    loads++;
    return loading == null ? ad : loading!.future;
  }
}

class TestRewardedAd implements NativeRewardedAd {
  int shows = 0, disposes = 0;
  bool failConfigure = false, failShow = false;
  Completer<void>? configuring;
  @override
  Future<void> configure({
    required String accountId,
    required int dayId,
    required int slot,
  }) async {
    if (failConfigure) throw StateError('setup failed');
    await configuring?.future;
  }

  @override
  Future<bool> show() async {
    shows++;
    if (failShow) throw StateError('show failed');
    return false;
  }

  @override
  Future<void> dispose() async {
    disposes++;
  }
}

PurchaseDetails purchase(PurchaseStatus status) => PurchaseDetails(
  purchaseID: 'transaction.1',
  productID: 'dev.tideglass.pass.01',
  verificationData: PurchaseVerificationData(
    localVerificationData: '',
    serverVerificationData: 'opaque-proof',
    source: 'test',
  ),
  transactionDate: '1',
  status: status,
)..pendingCompletePurchase = true;

void main() {
  test(
    'delayed privacy response never grants consent to a recovered different account',
    () async {
      final client = TestClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: MemoryCredentials(),
      );
      await manager.createAccount(cloudConsent: true);
      client.consentResponse = Completer<void>();
      final pending = manager.setTelemetryConsent(true);
      await manager.signOut(localOnly: true);
      client.identity = '00000000-0000-4000-8000-000000000002';
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'retained',
      );
      client.consentResponse!.complete();
      await pending;
      expect(manager.telemetryEnabled, false);
      expect(manager.pendingTelemetryDeletion, false);
      manager.dispose();
      client.close();
    },
  );

  test(
    'ownership expires and rechecks current account and seed on every read',
    () async {
      final client = TestClient()..grant = true;
      var localSeed = 'main.seed';
      final manager = NativeServicesManager(
        client: client,
        credentials: MemoryCredentials(),
        localAccountSeed: () => localSeed,
      );
      await manager.createAccount(cloudConsent: true);
      await manager.refreshOwnership();
      expect(manager.ownedEntitlementIds, {'pass.01'});
      localSeed = 'imported.seed';
      expect(manager.ownedEntitlementIds, isEmpty);
      localSeed = 'main.seed';
      expect(manager.ownedEntitlementIds, {'pass.01'});
      client.identity = 'another-account';
      await client.createAccount(cloudConsent: true);
      expect(manager.ownedEntitlementIds, isEmpty);
      client.maximumAge = 1;
      client.observedAge = 1;
      await manager.refreshOwnership();
      expect(manager.ownedEntitlementIds, isEmpty);
      client.observedAge = 0;
      await manager.refreshOwnership();
      expect(manager.ownedEntitlementIds, {'pass.01'});
      var notified = false;
      manager.addListener(() {
        notified = true;
      });
      await Future<void>.delayed(const Duration(milliseconds: 1100));
      expect(notified, true);
      expect(manager.ownedEntitlementIds, isEmpty);
      manager.dispose();
      client.close();
    },
  );

  test('late loaded rewarded ad is disposed after timeout', () async {
    final client = TestClient();
    final gateway = TestRewarded()..loading = Completer<NativeRewardedAd>();
    final manager = NativeServicesManager(
      client: client,
      credentials: MemoryCredentials(),
      rewarded: gateway,
      configuration: const NativeServiceConfiguration(
        adsEnabled: true,
        rewardedAdUnitId: 'configured-real-unit',
      ),
      platformOverride: 'apple',
      adLoadTimeout: const Duration(milliseconds: 10),
    );
    await manager.createAccount(cloudConsent: true);
    await expectLater(
      manager.requestRewardedSupport(dayId: 1, slot: 0),
      throwsA(isA<TimeoutException>()),
    );
    gateway.loading!.complete(gateway.ad);
    await Future<void>.delayed(Duration.zero);
    expect(gateway.ad.disposes, 1);
    expect(gateway.ad.shows, 0);
    manager.dispose();
    client.close();
  });

  test(
    'account or slot changes during consent and configuration prevent ad show',
    () async {
      final client = TestClient();
      final gateway = TestRewarded()..consent = Completer<bool>();
      var eligible = true;
      final manager = NativeServicesManager(
        client: client,
        credentials: MemoryCredentials(),
        rewarded: gateway,
        configuration: const NativeServiceConfiguration(
          adsEnabled: true,
          rewardedAdUnitId: 'configured-real-unit',
        ),
        platformOverride: 'apple',
      );
      await manager.createAccount(cloudConsent: true);
      final request = manager.requestRewardedSupport(
        dayId: 1,
        slot: 0,
        isStillEligible: () => eligible,
      );
      await manager.signOut(localOnly: true);
      gateway.consent!.complete(true);
      expect(await request, null);
      expect(gateway.loads, 0);
      await manager.createAccount(cloudConsent: true);
      gateway.consent = null;
      gateway.ad.configuring = Completer<void>();
      final second = manager.requestRewardedSupport(
        dayId: 1,
        slot: 0,
        isStillEligible: () => eligible,
      );
      await Future<void>.delayed(Duration.zero);
      eligible = false;
      gateway.ad.configuring!.complete();
      expect(await second, null);
      expect(gateway.ad.shows, 0);
      expect(gateway.ad.disposes, 1);
      manager.dispose();
      client.close();
    },
  );

  test('rewarded setup and show failures both dispose loaded ad', () async {
    for (final failSetup in [true, false]) {
      final client = TestClient();
      final gateway = TestRewarded();
      gateway.ad.failConfigure = failSetup;
      gateway.ad.failShow = !failSetup;
      final manager = NativeServicesManager(
        client: client,
        credentials: MemoryCredentials(),
        rewarded: gateway,
        configuration: const NativeServiceConfiguration(
          adsEnabled: true,
          rewardedAdUnitId: 'configured-real-unit',
        ),
        platformOverride: 'apple',
      );
      await manager.createAccount(cloudConsent: true);
      await expectLater(
        manager.requestRewardedSupport(dayId: 1, slot: 0),
        throwsStateError,
      );
      expect(gateway.ad.disposes, 1);
      manager.dispose();
      client.close();
    }
  });

  test(
    'secure privacy read failure never hides committed recovery results',
    () async {
      final credentials = MemoryCredentials()..readFailure = true;
      final client = TestClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: credentials,
      );
      final created = await manager.createAccount(cloudConsent: true);
      expect(created.recoveryCode, 'retained-recovery-code');
      expect(manager.lastError, 'secure_privacy_unavailable');
      expect(
        (await manager.recoverAccount(
          accountId: client.identity,
          recoveryCode: 'retained',
        )).accountId,
        client.identity,
      );
      final rotated = await manager.rotateRecoveryCode(
        'old',
        newRecoveryCode: 'already-retained-new-code',
      );
      expect(rotated.recoveryCode, 'already-retained-new-code');
      expect(manager.telemetryEnabled, false);
      client.close();
      manager.dispose();
    },
  );
  test(
    'successful remote logout/deletion clear memory despite secure cleanup failure',
    () async {
      final credentials = MemoryCredentials();
      final client = TestClient()..grant = true;
      final manager = NativeServicesManager(
        client: client,
        credentials: credentials,
        localAccountSeed: () => 'main.seed',
      );
      await manager.createAccount(cloudConsent: true);
      await manager.refreshOwnership();
      credentials.deleteFailure = true;
      await manager.signOut();
      expect(manager.signedIn, false);
      expect(manager.ownedEntitlementIds, isEmpty);
      expect(manager.lastError, 'secure_session_cleanup_required');
      await manager.createAccount(cloudConsent: true);
      await manager.refreshOwnership();
      await manager.deleteAccount(
        recoveryCode: 'retained',
        confirmDelete: true,
      );
      expect(manager.signedIn, false);
      expect(manager.ownedEntitlementIds, isEmpty);
      expect(manager.lastError, 'secure_session_cleanup_required');
      client.close();
      manager.dispose();
    },
  );

  test(
    'unconfigured guest initialization touches neither secure store nor billing',
    () async {
      final store = TestStore();
      final credentials = MemoryCredentials()..fail = true;
      final manager = NativeServicesManager(
        credentials: credentials,
        store: store,
      );
      await manager.initialize();
      expect(manager.configured, false);
      expect(store.queries, 0);
      await expectLater(manager.loadOffers(), throwsA(isA<ServiceException>()));
      expect(manager.adsAvailable, false);
      manager.dispose();
      await store.updates.close();
    },
  );
  test(
    'creation acknowledgement persists; credentials never cross service origins',
    () async {
      final credentials = MemoryCredentials();
      final client = TestClient();
      final first = NativeServicesManager(
        client: client,
        credentials: credentials,
      );
      await first.initialize();
      final created = await first.createAccount(cloudConsent: true);
      expect(first.recoveryAcknowledged, false);
      expect(
        credentials.values.values.join(),
        isNot(contains(created.recoveryCode)),
      );
      final second = NativeServicesManager(
        client: TestClient(),
        credentials: credentials,
      );
      await second.initialize();
      expect(second.recoveryAcknowledged, false);
      await first.acknowledgeRecoveryCode();
      final third = NativeServicesManager(
        client: TestClient(),
        credentials: credentials,
      );
      await third.initialize();
      expect(third.recoveryAcknowledged, true);
      final different = NativeServicesManager(
        client: TestClient(origin: 'https://other.invalid'),
        credentials: credentials,
      );
      await different.initialize();
      expect(different.signedIn, false);
      for (final manager in [first, second, third, different]) {
        manager.client?.close();
        manager.dispose();
      }
    },
  );
  test(
    'storage failure does not hide recovery code and cannot acknowledge upload',
    () async {
      final credentials = MemoryCredentials()..fail = true;
      final client = TestClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: credentials,
      );
      final result = await manager.createAccount(cloudConsent: true);
      expect(result.recoveryCode, 'retained-recovery-code');
      expect(manager.lastError, 'secure_session_not_saved');
      await expectLater(manager.acknowledgeRecoveryCode(), throwsStateError);
      expect(manager.recoveryAcknowledged, false);
      client.close();
      manager.dispose();
    },
  );
  test(
    'native pending and outage grant nothing; retry verifies before completing',
    () async {
      final client = TestClient();
      final store = TestStore();
      final manager = NativeServicesManager(
        client: client,
        store: store,
        credentials: MemoryCredentials(),
        configuration: const NativeServiceConfiguration(commerceEnabled: true),
        platformOverride: 'apple',
        localAccountSeed: () => 'main.seed',
      );
      await manager.initialize();
      await manager.createAccount(cloudConsent: true);
      await manager.acknowledgeRecoveryCode();
      await manager.loadOffers();
      expect(manager.offers.single.price, '₺249,99');
      await manager.buy('dev.tideglass.pass.01');
      expect(store.boundAccount, client.session!.accountId);
      store.updates.add([purchase(PurchaseStatus.pending)]);
      await Future<void>.delayed(Duration.zero);
      expect(client.verifies, 0);
      expect(store.completes, 0);
      client.unavailable = true;
      store.updates.add([purchase(PurchaseStatus.purchased)]);
      await Future<void>.delayed(Duration.zero);
      expect(store.completes, 0);
      expect(manager.ownedEntitlementIds, isEmpty);
      client.unavailable = false;
      client.grant = true;
      await manager.retryPurchases();
      expect(store.completes, 1);
      expect(manager.ownedEntitlementIds, {'pass.01'});
      await manager.restorePurchases();
      expect(store.restores, 1);
      client.grant = false;
      await manager.refreshOwnership();
      expect(manager.ownedEntitlementIds, isEmpty);
      manager.dispose();
      client.close();
      await store.updates.close();
    },
  );
  test(
    'privacy withdrawal belongs only to its account across sign-out and recovery',
    () async {
      final credentials = MemoryCredentials();
      final client = TestClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: credentials,
      );
      await manager.createAccount(cloudConsent: true);
      await manager.setTelemetryConsent(true);
      client.unavailable = true;
      await expectLater(
        manager.setTelemetryConsent(false),
        throwsA(isA<ServiceException>()),
      );
      await manager.signOut(localOnly: true);
      expect(manager.telemetryEnabled, false);
      expect(manager.pendingTelemetryDeletion, false);
      client.unavailable = false;
      client.identity = '00000000-0000-4000-8000-000000000002';
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'retained',
      );
      expect(manager.pendingTelemetryDeletion, false);
      expect(manager.telemetryEnabled, false);
      client.identity = '00000000-0000-4000-8000-000000000001';
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'retained',
      );
      expect(manager.pendingTelemetryDeletion, true);
      expect(manager.telemetryEnabled, false);
      client.close();
      manager.dispose();
    },
  );
  test(
    'ownership requires linked main seed; privacy refusal remains pending after outage',
    () async {
      final client = TestClient()..grant = true;
      final credentials = MemoryCredentials();
      final manager = NativeServicesManager(
        client: client,
        credentials: credentials,
        localAccountSeed: () => 'different.seed',
      );
      await manager.createAccount(cloudConsent: true);
      await manager.refreshOwnership();
      expect(manager.ownedEntitlementIds, isEmpty);
      await manager.setTelemetryConsent(true);
      client.unavailable = true;
      await expectLater(
        manager.setTelemetryConsent(false),
        throwsA(isA<ServiceException>()),
      );
      expect(manager.telemetryEnabled, false);
      expect(manager.pendingTelemetryDeletion, true);
      final reload = NativeServicesManager(
        client: TestClient(),
        credentials: credentials,
      );
      await reload.initialize();
      expect(reload.pendingTelemetryDeletion, true);
      expect(reload.telemetryEnabled, false);
      client.unavailable = false;
      await manager.retryTelemetryDeletion();
      expect(manager.pendingTelemetryDeletion, false);
      manager.dispose();
      reload.dispose();
      client.close();
      reload.client!.close();
    },
  );
}
