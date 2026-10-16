import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:tideglass_platform/tideglass_platform.dart';

const tideglassStoreProducts = <String>{
  'dev.tideglass.cosmetic.01',
  'dev.tideglass.cosmetic.02',
  'dev.tideglass.cosmetic.03',
  'dev.tideglass.cosmetic.04',
  'dev.tideglass.pass.01',
  'dev.tideglass.supporter',
};

class NativeServiceConfiguration {
  const NativeServiceConfiguration({
    this.commerceEnabled = false,
    this.adsEnabled = false,
    this.rewardedAdUnitId,
  });
  final bool commerceEnabled, adsEnabled;
  final String? rewardedAdUnitId;
}

abstract interface class CredentialStore {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
}

class SecureCredentialStore implements CredentialStore {
  SecureCredentialStore({FlutterSecureStorage? storage})
    : _storage =
          storage ??
          const FlutterSecureStorage(
            iOptions: IOSOptions(
              accessibility: KeychainAccessibility.first_unlock_this_device,
            ),
            aOptions: AndroidOptions(migrateWithBackup: true),
            mOptions: MacOsOptions(usesDataProtectionKeychain: false),
          );
  final FlutterSecureStorage _storage;
  @override
  Future<String?> read(String key) => _storage.read(key: key);
  @override
  Future<void> write(String key, String value) =>
      _storage.write(key: key, value: value);
  @override
  Future<void> delete(String key) => _storage.delete(key: key);
}

abstract interface class StoreGateway {
  Stream<List<PurchaseDetails>> get purchases;
  Future<bool> isAvailable();
  Future<ProductDetailsResponse> query(Set<String> products);
  Future<bool> buy(ProductDetails product, String accountId);
  Future<void> restore(String accountId);
  Future<void> complete(PurchaseDetails purchase);
}

class SdkStoreGateway implements StoreGateway {
  InAppPurchase get _sdk => InAppPurchase.instance;
  @override
  Stream<List<PurchaseDetails>> get purchases => _sdk.purchaseStream;
  @override
  Future<bool> isAvailable() => _sdk.isAvailable();
  @override
  Future<ProductDetailsResponse> query(Set<String> products) =>
      _sdk.queryProductDetails(products);
  @override
  Future<bool> buy(ProductDetails product, String accountId) =>
      _sdk.buyNonConsumable(
        purchaseParam: PurchaseParam(
          productDetails: product,
          applicationUserName: accountId,
        ),
      );
  @override
  Future<void> restore(String accountId) =>
      _sdk.restorePurchases(applicationUserName: accountId);
  @override
  Future<void> complete(PurchaseDetails purchase) =>
      _sdk.completePurchase(purchase);
}

/// Boundary preserves the real SDK lifecycle while making failure races testable.
abstract interface class RewardedGateway {
  Future<bool> requestConsent();
  Future<NativeRewardedAd> load(String unitId);
}

abstract interface class NativeRewardedAd {
  Future<void> configure({
    required String accountId,
    required int dayId,
    required int slot,
  });
  Future<bool> show();
  Future<void> dispose();
}

class SdkRewardedGateway implements RewardedGateway {
  @override
  Future<bool> requestConsent() async {
    final consent = Completer<void>();
    void fail() {
      if (!consent.isCompleted) {
        consent.completeError(const ServiceException('ad_consent_unavailable'));
      }
    }

    ConsentInformation.instance.requestConsentInfoUpdate(
      ConsentRequestParameters(),
      () async {
        try {
          await ConsentForm.loadAndShowConsentFormIfRequired((error) {
            if (error != null) {
              fail();
            } else if (!consent.isCompleted) {
              consent.complete();
            }
          });
        } catch (_) {
          fail();
        }
      },
      (_) => fail(),
    );
    await consent.future.timeout(const Duration(seconds: 30));
    return ConsentInformation.instance.canRequestAds();
  }

  @override
  Future<NativeRewardedAd> load(String unitId) async {
    await MobileAds.instance.initialize();
    final loaded = Completer<NativeRewardedAd>();
    RewardedAd.load(
      adUnitId: unitId,
      request: const AdRequest(),
      rewardedAdLoadCallback: RewardedAdLoadCallback(
        onAdLoaded: (ad) => loaded.complete(SdkNativeRewardedAd(ad)),
        onAdFailedToLoad: (_) =>
            loaded.completeError(const ServiceException('ad_unavailable')),
      ),
    );
    return loaded.future;
  }
}

class SdkNativeRewardedAd implements NativeRewardedAd {
  SdkNativeRewardedAd(this.ad);
  final RewardedAd ad;
  @override
  Future<void> configure({
    required String accountId,
    required int dayId,
    required int slot,
  }) => ad.setServerSideOptions(
    ServerSideVerificationOptions(
      userId: accountId,
      customData: jsonEncode({'day_id': dayId, 'slot': slot}),
    ),
  );
  @override
  Future<bool> show() async {
    final finished = Completer<bool>();
    var earned = false;
    ad.fullScreenContentCallback = FullScreenContentCallback(
      onAdDismissedFullScreenContent: (_) {
        if (!finished.isCompleted) finished.complete(earned);
      },
      onAdFailedToShowFullScreenContent: (_, _) {
        if (!finished.isCompleted) finished.complete(false);
      },
    );
    await ad.show(
      onUserEarnedReward: (_, _) {
        earned = true;
      },
    );
    return finished.future;
  }

  @override
  Future<void> dispose() => ad.dispose();
}

/// Optional native adapter. Constructor/guest initialization does not initialize
/// advertising or billing SDKs. No gameplay balances or local ownership flags
/// can authorize a commercial grant.
class NativeServicesManager extends ChangeNotifier {
  NativeServicesManager({
    this.client,
    CredentialStore? credentials,
    StoreGateway? store,
    RewardedGateway? rewarded,
    this.adLoadTimeout = const Duration(seconds: 30),
    this.configuration = const NativeServiceConfiguration(),
    this.localAccountSeed,
    String? platformOverride,
  }) : credentials = credentials ?? SecureCredentialStore(),
       _store = store ?? SdkStoreGateway(),
       _rewarded = rewarded ?? SdkRewardedGateway(),
       _platform =
           platformOverride ??
           (Platform.isIOS
               ? 'apple'
               : Platform.isAndroid
               ? 'google'
               : null);
  final TideglassServiceClient? client;
  final CredentialStore credentials;
  final StoreGateway _store;
  final RewardedGateway _rewarded;
  final Duration adLoadTimeout;
  final NativeServiceConfiguration configuration;
  final String? Function()? localAccountSeed;
  final String? _platform;
  bool _disposed = false, _initialized = false, _storeAvailable = false;
  bool busy = false, _recoveryAcknowledged = false;
  ServiceSession? _recoverySession;
  bool get recoveryAcknowledged =>
      _recoveryAcknowledged && identical(session, _recoverySession);
  set recoveryAcknowledged(bool value) {
    _recoveryAcknowledged = value;
    _recoverySession = session;
  }

  bool telemetryEnabled = false, pendingTelemetryDeletion = false;
  int _privacyIntent = 0;
  int _accountIntent = 0;
  Future<void> _credentialTail = Future.value();
  Future<void> _privacyWriteTail = Future.value();
  Future<void> _privacyRemoteTail = Future.value();
  String status = 'not_configured';
  String? lastError;
  List<ProductDetails> offers = [];
  Set<String> _ownedEntitlementIds = {};
  final Map<String, Duration> _ownershipValidity = {};
  final Stopwatch _ownershipAge = Stopwatch();
  String? _ownershipAccount, _ownershipSeed;
  Timer? _ownershipExpiryTimer;
  Set<String> get ownedEntitlementIds {
    if (session == null ||
        !session!.expiresAt.isAfter(DateTime.now().toUtc()) ||
        session?.accountId != _ownershipAccount ||
        localAccountSeed?.call() != _ownershipSeed ||
        _ownershipSeed == null) {
      return const {};
    }
    return Set.unmodifiable(
      _ownedEntitlementIds.where(
        (id) =>
            (_ownershipValidity[id] ?? Duration.zero) > _ownershipAge.elapsed,
      ),
    );
  }

  void _clearOwnership() {
    _ownedEntitlementIds = {};
    _ownershipValidity.clear();
    _ownershipAccount = null;
    _ownershipSeed = null;
    _ownershipAge.stop();
    _ownershipAge.reset();
    _ownershipExpiryTimer?.cancel();
  }

  void _armOwnershipExpiry() {
    _ownershipExpiryTimer?.cancel();
    final remaining =
        _ownershipValidity.values
            .map((value) => value - _ownershipAge.elapsed)
            .where((value) => value > Duration.zero)
            .toList()
          ..sort();
    if (remaining.isEmpty) return;
    _ownershipExpiryTimer = Timer(remaining.first, () {
      _notify();
      _armOwnershipExpiry();
    });
  }

  final Map<String, String> purchaseStates = {};
  final Map<String, PurchaseDetails> _retryPurchases = {};
  StreamSubscription<List<PurchaseDetails>>? _purchaseSubscription;
  Future<void> _purchaseTail = Future.value();
  bool get configured => client != null;
  ServiceSession? get session => client?.session;
  bool get signedIn => session != null;
  bool get commerceAvailable =>
      configured &&
      signedIn &&
      configuration.commerceEnabled &&
      _platform != null &&
      _storeAvailable;
  bool get adsAvailable =>
      configured &&
      signedIn &&
      configuration.adsEnabled &&
      _platform != null &&
      configuration.rewardedAdUnitId != null &&
      !configuration.rewardedAdUnitId!.contains('3940256099942544');
  String get _key =>
      'tideglass.${sha256.convert(utf8.encode(client!.endpoint.origin))}';

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    if (!configured) return;
    status = 'signed_out';
    final initialIntent = _accountIntent;
    final initialGeneration = client!.sessionGeneration;
    try {
      final raw = await credentials.read('$_key.session');
      if (raw != null &&
          initialIntent == _accountIntent &&
          initialGeneration == client!.sessionGeneration) {
        final data = jsonDecode(raw) as Map<String, dynamic>;
        final saved = ServiceSession.fromJson(data);
        if (saved.expiresAt.isAfter(DateTime.now().toUtc())) {
          client!.session = saved;
          recoveryAcknowledged = data['recovery_acknowledged'] == true;
          status = 'connected';
        } else {
          await _saveSession();
        }
      }
      await _loadPrivacy();
    } catch (_) {
      lastError = 'secure_session_unavailable';
    }
    if (configuration.commerceEnabled && _platform != null) {
      _purchaseSubscription = _store.purchases.listen(
        (batch) {
          _purchaseTail = _purchaseTail
              .then((_) => _handlePurchases(batch))
              .catchError((Object _) {
                lastError = 'purchase_delivery_needs_retry';
                _notify();
              });
        },
        onError: (Object _) {
          lastError = 'store_connection_unavailable';
          _notify();
        },
      );
    }
    _notify();
  }

  Future<void> _saveSession() {
    final next = _credentialTail.then((_) async {
      // Serialize secure writes and repair a session changed while the OS was
      // writing. An old logout can never be the final write over a new login.
      while (!_disposed) {
        final generation = client!.sessionGeneration;
        final current = session;
        if (current == null) {
          await credentials.delete('$_key.session');
        } else {
          await credentials.write(
            '$_key.session',
            jsonEncode({
              'account_id': current.accountId,
              'session_token': current.token,
              'expires_at': current.expiresAt.millisecondsSinceEpoch ~/ 1000,
              'recovery_acknowledged': recoveryAcknowledged,
            }),
          );
        }
        if (generation == client!.sessionGeneration) break;
      }
    });
    _credentialTail = next.catchError((Object _) {});
    return next;
  }

  Future<void> _rememberWithoutHidingRecovery(
    ServiceSession expected,
    int intent,
  ) async {
    if (_disposed || intent != _accountIntent || !identical(session, expected)) {
      return;
    }
    try {
      await _saveSession();
    } catch (_) {
      lastError = 'secure_session_not_saved';
    }
    if (_disposed || intent != _accountIntent || !identical(session, expected)) {
      return;
    }
    status = 'connected';
    _notify();
  }

  void _requireClient() {
    if (!configured) throw const ServiceException('service_not_configured');
  }

  Future<AccountCreated> createAccount({required bool cloudConsent}) async {
    _requireClient();
    final intent = ++_accountIntent;
    lastError = null;
    final result = await client!.createAccount(cloudConsent: cloudConsent);
    if (intent != _accountIntent || !identical(session, result.session)) {
      return result;
    }
    recoveryAcknowledged = false;
    _clearOwnership();
    await _loadPrivacy();
    await _rememberWithoutHidingRecovery(result.session, intent);
    return result;
  }

  Future<void> acknowledgeRecoveryCode() async {
    if (!signedIn) throw const ServiceException('authentication_required');
    final current = session;
    recoveryAcknowledged = true;
    try {
      await _saveSession();
      if (!identical(session, current)) {
        throw const ServiceException('account_changed');
      }
      lastError = null;
    } catch (_) {
      if (identical(session, current)) recoveryAcknowledged = false;
      rethrow;
    }
    _notify();
  }

  Future<ServiceSession> recoverAccount({
    required String accountId,
    required String recoveryCode,
  }) async {
    _requireClient();
    final intent = ++_accountIntent;
    lastError = null;
    final result = await client!.recoverAccount(
      accountId: accountId,
      recoveryCode: recoveryCode,
    );
    if (intent != _accountIntent || !identical(session, result)) return result;
    recoveryAcknowledged = true;
    _clearOwnership();
    await _loadPrivacy();
    await _rememberWithoutHidingRecovery(result, intent);
    return result;
  }

  Future<AccountCreated> rotateRecoveryCode(
    String currentCode, {
    required String newRecoveryCode,
  }) async {
    _requireClient();
    final intent = ++_accountIntent;
    lastError = null;
    final result = await client!.rotateRecoveryCode(
      currentCode,
      newRecoveryCode: newRecoveryCode,
    );
    if (intent != _accountIntent || !identical(session, result.session)) {
      return result;
    }
    recoveryAcknowledged = true;
    await _loadPrivacy();
    await _rememberWithoutHidingRecovery(result.session, intent);
    return result;
  }

  Future<void> signOut({
    bool allDevices = false,
    bool localOnly = false,
  }) async {
    _requireClient();
    final intent = ++_accountIntent;
    if (!localOnly) {
      await client!.signOut(allDevices: allDevices);
    } else {
      client!.forgetSession();
    }
    if (intent != _accountIntent || session != null) return;
    _clearOwnership();
    recoveryAcknowledged = false;
    status = 'signed_out';
    telemetryEnabled = false;
    pendingTelemetryDeletion = false;
    _notify();
    try {
      await _saveSession();
    } catch (_) {
      if (intent == _accountIntent) {
        lastError = 'secure_session_cleanup_required';
      }
    }
    _notify();
  }

  Future<void> deleteAccount({
    required String recoveryCode,
    required bool confirmDelete,
  }) async {
    _requireClient();
    final intent = ++_accountIntent;
    final deletingAccountId = session?.accountId;
    await client!.deleteAccount(
      recoveryCode: recoveryCode,
      confirmDelete: confirmDelete,
    );
    if (intent != _accountIntent || session != null) return;
    _clearOwnership();
    recoveryAcknowledged = false;
    telemetryEnabled = false;
    pendingTelemetryDeletion = false;
    status = 'signed_out';
    _notify();
    try {
      await _saveSession();
    } catch (_) {
      if (intent == _accountIntent) {
        lastError = 'secure_session_cleanup_required';
      }
    }
    if (deletingAccountId != null) {
      try {
        await credentials.delete('$_key.privacy.$deletingAccountId');
      } catch (_) {
        if (intent == _accountIntent) {
          lastError = 'secure_session_cleanup_required';
        }
      }
    }
    _notify();
  }

  Future<void> setTelemetryConsent(bool enabled) async {
    _requireClient();
    final intent = ++_privacyIntent;
    final generation = client!.sessionGeneration;
    bool current() =>
        !_disposed &&
        intent == _privacyIntent &&
        generation == client!.sessionGeneration;
    if (!signedIn) {
      telemetryEnabled = false;
      pendingTelemetryDeletion = false;
      _notify();
      if (enabled) throw const ServiceException('authentication_required');
      return;
    }
    final consentingAccount = session!.accountId;
    if (!enabled) {
      telemetryEnabled = false;
      pendingTelemetryDeletion = true;
      await _savePrivacy();
      if (!current() || session?.accountId != consentingAccount) return;
      _notify();
    }
    final operation = _privacyRemoteTail.then((_) async {
      if (!current()) return;
      await client!.setTelemetryConsent(enabled);
      if (!current()) return;
      telemetryEnabled = enabled;
      pendingTelemetryDeletion = false;
      await _savePrivacy();
      if (current()) _notify();
    });
    _privacyRemoteTail = operation.catchError((Object _) {});
    await operation;
  }

  Future<void> retryTelemetryDeletion() async {
    if (pendingTelemetryDeletion) await setTelemetryConsent(false);
  }

  Future<void> _loadPrivacy() async {
    telemetryEnabled = false;
    pendingTelemetryDeletion = false;
    if (!signedIn) return;
    final privacyAccount = session!.accountId;
    final generation = client!.sessionGeneration;
    final intent = _privacyIntent;
    try {
      final raw = await credentials.read('$_key.privacy.$privacyAccount');
      if (session?.accountId != privacyAccount ||
          raw == null ||
          generation != client!.sessionGeneration ||
          intent != _privacyIntent) {
        return;
      }
      final data = jsonDecode(raw) as Map;
      pendingTelemetryDeletion = data['pending_delete'] == true;
      telemetryEnabled = data['enabled'] == true && !pendingTelemetryDeletion;
    } catch (_) {
      // A remote account/rotation may already be committed. Never hide its
      // recovery result because an unrelated local privacy read failed.
      if (generation == client!.sessionGeneration && intent == _privacyIntent) {
        lastError = 'secure_privacy_unavailable';
      }
    }
  }

  Future<void> _savePrivacy() {
    if (!signedIn) return Future.value();
    final key = '$_key.privacy.${session!.accountId}';
    final data = jsonEncode({
      'enabled': telemetryEnabled,
      'pending_delete': pendingTelemetryDeletion,
    });
    final next = _privacyWriteTail.then((_) => credentials.write(key, data));
    _privacyWriteTail = next.catchError((Object _) {});
    return next;
  }

  Future<void> refreshOwnership() async {
    _requireClient();
    final generation = client!.sessionGeneration;
    final seed = localAccountSeed?.call();
    bool current() =>
        !_disposed &&
        generation == client!.sessionGeneration &&
        seed == localAccountSeed?.call();
    try {
      final response = await client!.entitlements();
      if (!current()) return;
      _acceptOwnership(response);
      lastError = null;
    } catch (_) {
      if (current()) {
        _clearOwnership();
        lastError = 'ownership_verification_unavailable';
      }
      rethrow;
    } finally {
      _notify();
    }
  }

  void _acceptOwnership(Map<String, dynamic> result) {
    _clearOwnership();
    final seed = localAccountSeed?.call();
    final verifiedAt = result['verified_at'];
    final maximumAge = result['maximum_verification_age_seconds'];
    if (session == null ||
        result['account_id'] != session!.accountId ||
        seed == null ||
        result['linked_account_seed'] != seed ||
        verifiedAt is! int ||
        maximumAge is! int ||
        maximumAge < 1 ||
        maximumAge > 86400 ||
        result['purchases'] is! List ||
        result['entitlements'] is! List) {
      return;
    }
    final observations = <String, int>{};
    for (final row in result['purchases'] as List) {
      if (row is Map &&
          row['state'] == 'purchased' &&
          row['verification_id'] is String &&
          row['updated'] is int) {
        observations[row['verification_id'] as String] = row['updated'] as int;
      }
    }
    for (final row in result['entitlements'] as List) {
      if (row is! Map || row['id'] is! String) continue;
      final observedAt = observations[row['verification_receipt_id']];
      if (observedAt == null || observedAt > verifiedAt + 300) continue;
      final remaining = (observedAt + maximumAge - verifiedAt).clamp(
        0,
        maximumAge,
      );
      if (remaining > 0) {
        _ownedEntitlementIds.add(row['id'] as String);
        _ownershipValidity[row['id'] as String] = Duration(seconds: remaining);
      }
    }
    _ownershipAccount = session!.accountId;
    _ownershipSeed = seed;
    _ownershipAge.start();
    _armOwnershipExpiry();
  }

  Future<void> loadOffers() async {
    if (!configured ||
        !signedIn ||
        !configuration.commerceEnabled ||
        _platform == null) {
      throw const ServiceException('commerce_not_configured');
    }
    busy = true;
    _notify();
    try {
      _storeAvailable = await _store.isAvailable();
      if (!_storeAvailable) throw const ServiceException('store_unavailable');
      final response = await _store.query(tideglassStoreProducts);
      if (response.error != null) {
        throw const ServiceException('store_catalogue_unavailable');
      }
      offers = response.productDetails
          .where((product) => tideglassStoreProducts.contains(product.id))
          .toList(growable: false);
      lastError = response.notFoundIDs.isEmpty
          ? null
          : 'some_products_unavailable';
    } finally {
      busy = false;
      _notify();
    }
  }

  Future<void> buy(String productId) async {
    if (!commerceAvailable || !recoveryAcknowledged) {
      throw const ServiceException('commerce_not_available');
    }
    final matching = offers.where((offer) => offer.id == productId).toList();
    if (matching.length != 1) {
      throw const ServiceException('product_not_available');
    }
    final binding = await client!.entitlements();
    if (binding['account_id'] != session!.accountId ||
        localAccountSeed?.call() == null ||
        binding['linked_account_seed'] != localAccountSeed!.call()) {
      throw const ServiceException('link_progress_before_purchase');
    }
    purchaseStates[productId] = 'opening_store';
    _notify();
    if (!await _store.buy(matching.single, session!.accountId)) {
      purchaseStates[productId] = 'not_started';
      _notify();
      throw const ServiceException('purchase_not_started');
    }
  }

  Future<void> restorePurchases() async {
    if (!configured ||
        !signedIn ||
        !configuration.commerceEnabled ||
        _platform == null) {
      throw const ServiceException('commerce_not_configured');
    }
    await _store.restore(session!.accountId);
  }

  Future<void> retryPurchases() {
    _purchaseTail = _purchaseTail.then(
      (_) => _handlePurchases(_retryPurchases.values.toList()),
    );
    return _purchaseTail;
  }

  Future<void> _handlePurchases(List<PurchaseDetails> batch) async {
    for (final purchase in batch) {
      if (!tideglassStoreProducts.contains(purchase.productID)) continue;
      if (purchase.status == PurchaseStatus.pending) {
        purchaseStates[purchase.productID] = 'pending';
        _notify();
        continue;
      }
      if (purchase.status == PurchaseStatus.canceled ||
          purchase.status == PurchaseStatus.error) {
        purchaseStates[purchase.productID] =
            purchase.status == PurchaseStatus.canceled ? 'cancelled' : 'failed';
        _notify();
        continue;
      }
      if (purchase.status != PurchaseStatus.purchased &&
          purchase.status != PurchaseStatus.restored) {
        continue;
      }
      _retryPurchases[purchase.productID] = purchase;
      if (!signedIn) {
        purchaseStates[purchase.productID] = 'account_recovery_required';
        _notify();
        continue;
      }
      final verifyingSession = session;
      final verifyingGeneration = client!.sessionGeneration;
      final verifyingSeed = localAccountSeed?.call();
      bool current() =>
          !_disposed &&
          identical(session, verifyingSession) &&
          client!.sessionGeneration == verifyingGeneration &&
          localAccountSeed?.call() == verifyingSeed;
      try {
        purchaseStates[purchase.productID] = 'verifying';
        _notify();
        final proof = _platform == 'apple'
            ? {
                'transaction_id': purchase.purchaseID,
                'expected_product_id': purchase.productID,
              }
            : {
                'purchase_token':
                    purchase.verificationData.serverVerificationData,
                'expected_product_id': purchase.productID,
              };
        final result = await client!.verifyPurchase(
          platform: _platform!,
          proof: jsonEncode(proof),
        );
        if (!current() ||
            result['account_id'] != verifyingSession!.accountId ||
            result['linked_account_seed'] != verifyingSeed) {
          purchaseStates[purchase.productID] = 'account_recovery_required';
          _notify();
          continue;
        }
        final granted =
            {
              'purchased',
              'granted_awaiting_acknowledgement',
            }.contains(result['delivery_state']) &&
            (result['purchases'] as List).any(
              (row) =>
                  row['product_id'] == purchase.productID &&
                  row['state'] == 'purchased',
            );
        if (!granted) {
          purchaseStates[purchase.productID] =
              result['delivery_state'] == 'revoked'
              ? 'revoked'
              : 'pending_verification';
          _acceptOwnership(result);
          _notify();
          continue;
        }
        _acceptOwnership(result);
        if (purchase.pendingCompletePurchase) await _store.complete(purchase);
        if (!current()) {
          purchaseStates[purchase.productID] = 'account_recovery_required';
          _notify();
          continue;
        }
        _retryPurchases.remove(purchase.productID);
        purchaseStates[purchase.productID] = 'verified';
        lastError = null;
      } catch (_) {
        purchaseStates[purchase.productID] = 'delivery_needs_retry';
        lastError = 'purchase_delivery_needs_retry';
      }
      _notify();
    }
  }

  /// SDK reward callbacks trigger a server-ledger lookup, never a direct token.
  /// The configured provider callback must independently verify and store the
  /// signed account/day/slot receipt before any claim is returned to the core.
  Future<Map<String, dynamic>?> requestRewardedSupport({
    required int dayId,
    required int slot,
    bool Function()? isStillEligible,
  }) async {
    if (!adsAvailable || slot < 0 || slot > 5) {
      throw const ServiceException('ads_not_configured');
    }
    final requestingAccount = session!.accountId;
    final requestingSeed = localAccountSeed?.call();
    bool stillEligible() =>
        !_disposed &&
        signedIn &&
        session!.accountId == requestingAccount &&
        localAccountSeed?.call() == requestingSeed &&
        (isStillEligible?.call() ?? true);
    if (!stillEligible()) return null;
    if (!await _rewarded.requestConsent() || !stillEligible()) return null;
    var abandoned = false;
    NativeRewardedAd? ad;
    try {
      ad = await _rewarded
          .load(configuration.rewardedAdUnitId!)
          .then((loaded) async {
            if (abandoned || !stillEligible()) {
              await loaded.dispose();
              throw const ServiceException('ad_request_expired');
            }
            return loaded;
          })
          .timeout(adLoadTimeout);
      if (!stillEligible()) return null;
      await ad.configure(
        accountId: requestingAccount,
        dayId: dayId,
        slot: slot,
      );
      if (!stillEligible()) return null;
      final earned = await ad.show();
      if (!earned || !stillEligible()) return null;
    } finally {
      abandoned = true;
      await ad?.dispose();
    }
    for (var attempt = 0; attempt < 5; attempt++) {
      if (!stillEligible()) return null;
      final result = await client!.supportClaims();
      if (!stillEligible()) return null;
      for (final value in result['claims'] as List) {
        if (value['day_id'] == dayId && value['slot'] == slot) {
          return (value as Map).cast<String, dynamic>();
        }
      }
      if (attempt < 4) await Future<void>.delayed(const Duration(seconds: 2));
    }
    return null; // A late provider receipt is recovered separately by the host.
  }

  @override
  void dispose() {
    _disposed = true;
    _ownershipExpiryTimer?.cancel();
    unawaited(_purchaseSubscription?.cancel());
    super.dispose();
  }
}
