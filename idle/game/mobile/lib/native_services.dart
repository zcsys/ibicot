import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'package:tideglass_platform/signed_entitlements.dart';
import 'package:tideglass_platform/soundtrack_delivery.dart';

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
    this.supporterEnabled = false,
    this.signedOwnershipRequired = false,
  });
  final bool commerceEnabled, adsEnabled;
  final String? rewardedAdUnitId;
  final bool supporterEnabled;
  final bool signedOwnershipRequired;
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

enum AdPrivacyRequirement { unknown, notRequired, required }

class AdPrivacySnapshot {
  const AdPrivacySnapshot({
    required this.requirement,
    required this.canRequestAds,
  });
  final AdPrivacyRequirement requirement;
  final bool canRequestAds;
}

/// Optional capability keeps existing RewardedGateway test/adapters compatible.
abstract interface class AdPrivacyGateway {
  Future<AdPrivacySnapshot> readAdPrivacyState();
  Future<AdPrivacySnapshot> updateAdPrivacyState();
  Future<AdPrivacySnapshot> showAdPrivacyOptions();
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

class SdkRewardedGateway implements RewardedGateway, AdPrivacyGateway {
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
  Future<AdPrivacySnapshot> readAdPrivacyState() async {
    final required = await ConsentInformation.instance
        .getPrivacyOptionsRequirementStatus();
    final allowed = await ConsentInformation.instance.canRequestAds();
    return AdPrivacySnapshot(
      requirement: switch (required) {
        PrivacyOptionsRequirementStatus.required =>
          AdPrivacyRequirement.required,
        PrivacyOptionsRequirementStatus.notRequired =>
          AdPrivacyRequirement.notRequired,
        PrivacyOptionsRequirementStatus.unknown => AdPrivacyRequirement.unknown,
      },
      canRequestAds: allowed,
    );
  }

  @override
  Future<AdPrivacySnapshot> updateAdPrivacyState() async {
    // Explicit Check action only. Updating information does not show a consent
    // form or initialize/load an ad; a required options form remains a separate
    // player action after the updated requirement has been presented.
    final updated = Completer<void>();
    ConsentInformation.instance.requestConsentInfoUpdate(
      ConsentRequestParameters(),
      () {
        if (!updated.isCompleted) updated.complete();
      },
      (_) {
        if (!updated.isCompleted) {
          updated.completeError(
            const ServiceException('ad_privacy_unavailable'),
          );
        }
      },
    );
    await updated.future.timeout(const Duration(seconds: 30));
    return readAdPrivacyState().timeout(const Duration(seconds: 5));
  }

  @override
  Future<AdPrivacySnapshot> showAdPrivacyOptions() async {
    FormError? failure;
    await ConsentForm.showPrivacyOptionsForm((error) => failure = error);
    if (failure != null) {
      throw const ServiceException('ad_privacy_unavailable');
    }
    return readAdPrivacyState().timeout(const Duration(seconds: 5));
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
    this.ownershipCache,
    this.prepareOwnershipClock,
    SoundtrackDelivery? soundtrack,
    String? platformOverride,
  }) : credentials = credentials ?? SecureCredentialStore(),
       _store = store ?? SdkStoreGateway(),
       _rewarded = rewarded ?? SdkRewardedGateway(),
       _soundtrack =
           soundtrack ?? (client == null ? null : SoundtrackDelivery(client)),
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
  final SecureOwnershipLeaseCache? ownershipCache;
  final Future<bool> Function()? prepareOwnershipClock;
  final SoundtrackDelivery? _soundtrack;
  ServiceSession? _soundtrackCapabilitySession;
  bool _soundtrackReady = false;
  bool get supporterDeliveryReady =>
      configuration.supporterEnabled &&
      _soundtrackReady &&
      identical(session, _soundtrackCapabilitySession) &&
      session?.expiresAt.isAfter(DateTime.now().toUtc()) == true;
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
  int? _telemetryConsentRevision;
  ServiceSession? _telemetryConsentSession;
  int? get telemetryConsentRevision =>
      telemetryEnabled &&
          !pendingTelemetryDeletion &&
          session != null &&
          session!.expiresAt.isAfter(DateTime.now().toUtc()) &&
          identical(session, _telemetryConsentSession)
      ? _telemetryConsentRevision
      : null;
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
  int _ownershipIntent = 0;
  // A newer online observation burns the older lease's authority immediately,
  // including while clock/storage work is pending or has failed.
  final Set<String> _ownershipRequiresFreshLease = {};
  Timer? _ownershipExpiryTimer;
  Set<String> get ownedEntitlementIds {
    if (configuration.signedOwnershipRequired && ownershipCache == null) {
      return const {};
    }
    if (session == null ||
        _ownershipRequiresFreshLease.contains(session!.accountId) ||
        !session!.expiresAt.isAfter(DateTime.now().toUtc()) ||
        session?.accountId != _ownershipAccount ||
        localAccountSeed?.call() != _ownershipSeed ||
        _ownershipSeed == null) {
      return const {};
    }
    if (ownershipCache != null) {
      return ownershipCache!.currentEntitlementIds(
        accountId: session!.accountId,
        localAccountSeed: _ownershipSeed!,
      );
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
    if (ownershipCache != null) {
      final remaining = ownershipCache!.remaining;
      if (remaining > Duration.zero) {
        _ownershipExpiryTimer = Timer(remaining, () => _notify());
      }
      return;
    }
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
      (!configuration.signedOwnershipRequired || ownershipCache != null) &&
      _platform != null &&
      _storeAvailable;
  bool get adsAvailable =>
      configured &&
      signedIn &&
      configuration.adsEnabled &&
      _platform != null &&
      configuration.rewardedAdUnitId != null &&
      !configuration.rewardedAdUnitId!.contains('3940256099942544');
  int _adPrivacyRevision = 0;
  bool _adPrivacyBusy = false;
  AdPrivacySnapshot _adPrivacy = const AdPrivacySnapshot(
    requirement: AdPrivacyRequirement.unknown,
    canRequestAds: false,
  );
  String? _adPrivacyError;
  AdPrivacyGateway? get _adPrivacyGateway =>
      _rewarded is AdPrivacyGateway ? _rewarded as AdPrivacyGateway : null;
  // Device-level choices remain reachable after sign-out. No query is made
  // from initialize(), a build(), or an unconfigured guest launch.
  bool get adPrivacyAvailable =>
      configured &&
      configuration.adsEnabled &&
      _platform != null &&
      configuration.rewardedAdUnitId != null &&
      !configuration.rewardedAdUnitId!.contains('3940256099942544') &&
      _adPrivacyGateway != null;
  AdPrivacyRequirement get adPrivacyRequirement => _adPrivacy.requirement;
  bool get adPrivacyBusy => _adPrivacyBusy;
  String? get adPrivacyError => _adPrivacyError;

  Future<void> refreshAdPrivacyOptions() => _adPrivacyAction(show: false);
  Future<void> updateAdPrivacyOptions() =>
      _adPrivacyAction(show: false, update: true);
  Future<void> showAdPrivacyOptions() => _adPrivacyAction(show: true);

  Future<void> _adPrivacyAction({
    required bool show,
    bool update = false,
  }) async {
    if (!adPrivacyAvailable) {
      if (show) throw const ServiceException('ad_privacy_unavailable');
      return;
    }
    if (_adPrivacyBusy) return;
    // Invalidate uncompleted ad work synchronously, before any SDK future.
    final revision = ++_adPrivacyRevision;
    final accountIntent = _accountIntent;
    final expectedSession = session;
    final sessionGeneration = client!.sessionGeneration;
    final seed = localAccountSeed?.call();
    bool current() =>
        !_disposed &&
        revision == _adPrivacyRevision &&
        accountIntent == _accountIntent &&
        identical(session, expectedSession) &&
        client!.sessionGeneration == sessionGeneration &&
        localAccountSeed?.call() == seed;
    _adPrivacyBusy = true;
    _adPrivacyError = null;
    _notify();
    try {
      var state = update
          ? await _adPrivacyGateway!.updateAdPrivacyState().timeout(
              const Duration(seconds: 35),
            )
          : await _adPrivacyGateway!.readAdPrivacyState().timeout(
              const Duration(seconds: 5),
            );
      if (!current()) return;
      if (show && state.requirement == AdPrivacyRequirement.required) {
        // User interaction may take as long as needed. Do not time out a visible
        // form and resume optional ads while that form is still open.
        state = await _adPrivacyGateway!.showAdPrivacyOptions();
      }
      if (current()) _adPrivacy = state;
    } catch (_) {
      if (current()) _adPrivacyError = 'ad_privacy_unavailable';
    } finally {
      if (revision == _adPrivacyRevision) {
        _adPrivacyBusy = false;
        _notify();
      }
    }
  }

  String get _key =>
      'tideglass.${sha256.convert(utf8.encode(client!.endpoint.origin))}';

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  /// Native elapsed-clock changes can hide/restore valid cached cosmetics.
  /// This updates their projection without mutating gameplay or contacting a service.
  void refreshOwnershipPresentation() => _notify();

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
    if (_disposed ||
        intent != _accountIntent ||
        !identical(session, expected)) {
      return;
    }
    try {
      await _saveSession();
    } catch (_) {
      lastError = 'secure_session_not_saved';
    }
    if (_disposed ||
        intent != _accountIntent ||
        !identical(session, expected)) {
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
    final leavingAccount = session?.accountId;
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
      if (leavingAccount != null) {
        await ownershipCache?.clear(accountId: leavingAccount);
      }
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
    var leaseCleanupFailed = false;
    if (deletingAccountId != null) {
      try {
        await ownershipCache?.erase(accountId: deletingAccountId);
      } catch (_) {
        leaseCleanupFailed = true;
      }
    }
    if (intent != _accountIntent || session != null) return;
    _clearOwnership();
    recoveryAcknowledged = false;
    telemetryEnabled = false;
    pendingTelemetryDeletion = false;
    status = 'signed_out';
    if (leaseCleanupFailed) lastError = 'secure_session_cleanup_required';
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
      _telemetryConsentRevision = null;
      _telemetryConsentSession = null;
      _notify();
      await _savePrivacy();
      if (!current() || session?.accountId != consentingAccount) return;
      _notify();
    }
    final operation = _privacyRemoteTail.then((_) async {
      if (!current()) return;
      final revision = await client!.setTelemetryConsent(enabled);
      if (!current()) return;
      telemetryEnabled = enabled;
      pendingTelemetryDeletion = false;
      _telemetryConsentRevision = enabled ? revision : null;
      _telemetryConsentSession = enabled ? session : null;
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
    _telemetryConsentRevision = null;
    _telemetryConsentSession = null;
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
      final revision = data['revision'];
      if (telemetryEnabled && revision is int && revision > 0) {
        _telemetryConsentRevision = revision;
        _telemetryConsentSession = session;
      }
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
      'revision': telemetryConsentRevision,
    });
    final next = _privacyWriteTail.then((_) => credentials.write(key, data));
    _privacyWriteTail = next.catchError((Object _) {});
    return next;
  }

  /// Recheck remote withdrawal without ever writing a new opt-in. An outage
  /// retains only the player's existing local choice; the service still checks
  /// the recorded revision before accepting any queued event.
  Future<void> refreshTelemetryConsent() async {
    if (!signedIn || !telemetryEnabled || pendingTelemetryDeletion) return;
    final requestedSession = session;
    final generation = client!.sessionGeneration;
    final intent = _privacyIntent;
    final result = await client!.readTelemetryConsent();
    if (_disposed ||
        generation != client!.sessionGeneration ||
        intent != _privacyIntent ||
        !identical(session, requestedSession) ||
        !telemetryEnabled ||
        pendingTelemetryDeletion) {
      return;
    }
    final enabled = result['enabled'] == true;
    final revision = result['revision'];
    if (revision is! int || revision < 0 || (enabled && revision == 0)) {
      throw const ServiceException('invalid_consent_response');
    }
    if (_telemetryConsentRevision != null &&
        revision < _telemetryConsentRevision!) {
      return;
    }
    telemetryEnabled = enabled;
    _telemetryConsentRevision = enabled ? revision : null;
    _telemetryConsentSession = enabled ? session : null;
    _notify();
    await _savePrivacy();
  }

  Future<void> refreshOwnership() async {
    _requireClient();
    if (configuration.signedOwnershipRequired && ownershipCache == null) {
      _clearOwnership();
      lastError = 'ownership_verification_unavailable';
      _notify();
      throw const ServiceException('ownership_verification_not_configured');
    }
    final intent = ++_ownershipIntent;
    final generation = client!.sessionGeneration;
    final seed = localAccountSeed?.call();
    bool current() =>
        !_disposed &&
        intent == _ownershipIntent &&
        generation == client!.sessionGeneration &&
        seed == localAccountSeed?.call();
    try {
      final response = await client!.entitlements();
      if (!current()) return;
      _acceptOwnership(response);
      await _refreshSignedOwnership(current);
      if (!current()) return;
      lastError = null;
    } catch (_) {
      if (current()) {
        if (ownershipCache == null) {
          _clearOwnership();
        } else if (!_ownershipRequiresFreshLease.contains(session?.accountId)) {
          await restoreCachedOwnership();
        }
        if (current()) lastError = 'ownership_verification_unavailable';
      }
      rethrow;
    } finally {
      _notify();
    }
  }

  /// A previously signed lease may cover an outage, but never a new account,
  /// another progression seed, an expired budget or an observed revocation.
  Future<void> restoreCachedOwnership() async {
    final cache = ownershipCache, expected = session;
    final seed = localAccountSeed?.call();
    if (cache == null ||
        expected == null ||
        seed == null ||
        _ownershipRequiresFreshLease.contains(expected.accountId)) {
      return;
    }
    final generation = client!.sessionGeneration;
    bool current() =>
        !_disposed &&
        !_ownershipRequiresFreshLease.contains(expected.accountId) &&
        identical(session, expected) &&
        generation == client!.sessionGeneration &&
        seed == localAccountSeed?.call();
    try {
      if (prepareOwnershipClock != null && !await prepareOwnershipClock!()) {
        return;
      }
      if (!current()) return;
      if (_ownershipAccount != expected.accountId ||
          _ownershipSeed != seed ||
          cache.remaining <= Duration.zero) {
        await cache.load(accountId: expected.accountId, localAccountSeed: seed);
      }
      if (!current()) return;
      _ownershipAccount = expected.accountId;
      _ownershipSeed = seed;
      _armOwnershipExpiry();
    } catch (_) {
      if (current()) _clearOwnership();
    }
    _notify();
  }

  Future<void> _refreshSignedOwnership(bool Function() current) async {
    final cache = ownershipCache, expected = session;
    final seed = localAccountSeed?.call();
    if (cache == null || expected == null || seed == null || !current()) return;
    // Persist supersession before any clock wait. The synchronous quarantine
    // already denies older grants, even if this secure write fails.
    await cache.clear(accountId: expected.accountId);
    if (!current()) return;
    if (prepareOwnershipClock != null && !await prepareOwnershipClock!()) {
      throw const ServiceException('ownership_clock_unavailable');
    }
    if (!current()) return;
    final response = await client!.ownershipLease();
    if (!current()) return;
    final envelope = response['lease'];
    if (envelope is! Map<String, dynamic>) {
      throw const ServiceException('invalid_ownership_lease');
    }
    await cache.accept(
      envelope,
      accountId: expected.accountId,
      localAccountSeed: seed,
    );
    if (!current()) return;
    _ownershipRequiresFreshLease.remove(expected.accountId);
    _ownershipAccount = expected.accountId;
    _ownershipSeed = seed;
    _armOwnershipExpiry();
  }

  Future<void> checkpointOwnership() async {
    final account = session?.accountId;
    if (ownershipCache == null ||
        account == null ||
        _ownershipRequiresFreshLease.contains(account)) {
      return;
    }
    try {
      if (prepareOwnershipClock != null && !await prepareOwnershipClock!()) {
        return;
      }
      await ownershipCache!.checkpoint(accountId: account);
    } catch (_) {
      // Storage failure must not extend a lease or interrupt local gameplay.
    }
  }

  Future<File> downloadSoundtrack(Directory destination) async {
    if (_soundtrack == null || !ownedEntitlementIds.contains('soundtrack.01')) {
      throw const ServiceException('soundtrack_ownership_required');
    }
    final expected = session;
    try {
      return await _soundtrack.download(destination);
    } on ServiceException catch (error) {
      if (error.status == 403 && identical(session, expected)) {
        try {
          await refreshOwnership();
        } catch (_) {
          // The refused export remains refused even if refresh is unavailable.
        }
      }
      rethrow;
    }
  }

  void _acceptOwnership(Map<String, dynamic> result) {
    _clearOwnership();
    if (ownershipCache != null) {
      final account = session?.accountId;
      if (account != null) _ownershipRequiresFreshLease.add(account);
      _notify();
      return;
    }
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
      _soundtrackReady = false;
      _soundtrackCapabilitySession = null;
      if (configuration.supporterEnabled && _soundtrack != null) {
        final expected = session;
        try {
          final ready = await _soundtrack.ready();
          if (identical(session, expected)) {
            _soundtrackReady = ready;
            _soundtrackCapabilitySession = expected;
          }
        } catch (_) {
          // Other cosmetic offers remain usable when soundtrack delivery fails.
        }
      }
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
    if (productId == 'dev.tideglass.supporter' && !supporterDeliveryReady) {
      throw const ServiceException('soundtrack_delivery_unavailable');
    }
    if (productId == 'dev.tideglass.supporter') {
      final expected = session;
      try {
        if (!await _soundtrack!.ready() || !identical(session, expected)) {
          throw const ServiceException('soundtrack_delivery_unavailable');
        }
      } catch (_) {
        _soundtrackReady = false;
        _soundtrackCapabilitySession = null;
        _notify();
        throw const ServiceException('soundtrack_delivery_unavailable');
      }
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
      final ownershipIntent = ++_ownershipIntent;
      final verifyingGeneration = client!.sessionGeneration;
      final verifyingSeed = localAccountSeed?.call();
      bool current() =>
          !_disposed &&
          identical(session, verifyingSession) &&
          client!.sessionGeneration == verifyingGeneration &&
          localAccountSeed?.call() == verifyingSeed;
      bool currentOwnership() =>
          current() && ownershipIntent == _ownershipIntent;
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
          if (currentOwnership()) {
            _acceptOwnership(result);
            await _refreshSignedOwnership(currentOwnership);
          }
          _notify();
          continue;
        }
        if (currentOwnership()) {
          _acceptOwnership(result);
          await _refreshSignedOwnership(currentOwnership);
        }
        if (!current()) continue;
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
    if (_adPrivacyBusy) return null;
    final requestingAccount = session!.accountId;
    final requestingSession = session;
    final requestingGeneration = client!.sessionGeneration;
    final requestingAccountIntent = _accountIntent;
    final privacyRevision = _adPrivacyRevision;
    final requestingSeed = localAccountSeed?.call();
    var displayCompleted = false;
    bool stillEligible() =>
        !_disposed &&
        signedIn &&
        identical(session, requestingSession) &&
        client!.sessionGeneration == requestingGeneration &&
        _accountIntent == requestingAccountIntent &&
        session!.accountId == requestingAccount &&
        localAccountSeed?.call() == requestingSeed &&
        (displayCompleted ||
            (!_adPrivacyBusy && privacyRevision == _adPrivacyRevision)) &&
        (isStillEligible?.call() ?? true);
    if (!stillEligible()) return null;
    if (!await _rewarded.requestConsent() || !stillEligible()) return null;
    if (_adPrivacyGateway != null) {
      try {
        final state = await _adPrivacyGateway!.readAdPrivacyState().timeout(
          const Duration(seconds: 5),
        );
        if (!stillEligible()) return null;
        _adPrivacy = state;
        _adPrivacyError = null;
        _notify();
        if (!state.canRequestAds ||
            state.requirement == AdPrivacyRequirement.unknown) {
          return null;
        }
      } catch (_) {
        if (stillEligible()) {
          _adPrivacyError = 'ad_privacy_unavailable';
          _notify();
        }
        return null;
      }
    }
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
      // Later privacy changes affect future optional ads, not a completed
      // display's verified server receipt. Account/seed/slot guards still apply.
      displayCompleted = true;
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
