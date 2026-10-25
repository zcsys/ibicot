import 'dart:async';
import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass_platform/signed_entitlements.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'native_services_test.dart' show MemoryCredentials;
import 'signed_ownership_integration_test.dart' show LeaseClient;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final algorithm = Ed25519();
  late MemoryCredentials storage;
  late LeaseClient client;
  late SecureOwnershipLeaseCache cache;
  late NativeServicesManager manager;
  late DateTime now;
  var ids = <String>['pass.01'];
  var seed = 'main.seed', revision = 0, elapsed = 0;
  var clockAvailable = true, prepareSucceeds = true;
  Completer<bool>? prepareGate;
  Completer<void>? prepareEntered;
  setUp(() async {
    final key = await algorithm.newKeyPairFromSeed(List.generate(32, (i) => 200 - i));
    final verifier = SignedOwnershipVerifier(issuer: 'https://example.invalid',
      pinnedPublicKeys: {'qa-only': (await key.extractPublicKey()).bytes});
    storage = MemoryCredentials(); client = LeaseClient()..grant = true;
    now = DateTime.now().toUtc(); ids = ['pass.01']; seed = 'main.seed'; revision = 0; elapsed = 0;
    clockAvailable = true; prepareSucceeds = true; prepareGate = null; prepareEntered = null;
    client.signLease = () async {
      final payload = utf8.encode(jsonEncode({'v': 1, 'issuer': 'https://example.invalid',
        'account_id': client.identity, 'linked_account_seed': 'main.seed',
        'issued_at': now.millisecondsSinceEpoch ~/ 1000, 'expires_at': now.millisecondsSinceEpoch ~/ 1000 + 3600,
        'revision': ++revision, 'lease_id': 'independent-fixture-$revision', 'entitlements': ids}));
      final signature = await algorithm.sign(payload, keyPair: key);
      String b64(List<int> v) => base64Url.encode(v).replaceAll('=', '');
      return {'key_id': 'qa-only', 'payload': b64(payload), 'signature': b64(signature.bytes)};
    };
    cache = SecureOwnershipLeaseCache(verifier: verifier, read: storage.read, write: storage.write,
      delete: storage.delete, clock: () => now, deviceTime: () => clockAvailable
        ? TrustedDeviceTime(bootId: 'qa-device-boot', elapsedMicroseconds: elapsed) : null);
    manager = NativeServicesManager(client: client, credentials: storage, ownershipCache: cache,
      localAccountSeed: () => seed, prepareOwnershipClock: () async {
        if (prepareEntered != null && !prepareEntered!.isCompleted) prepareEntered!.complete();
        if (prepareGate != null) return prepareGate!.future;
        return prepareSucceeds;
      });
    await manager.createAccount(cloudConsent: true);
  });
  tearDown(() { manager.dispose(); client.close(); });

  test('observed revocation cannot revive when a temporarily missing clock recovers', () async {
    await manager.refreshOwnership(); expect(manager.ownedEntitlementIds, {'pass.01'});
    client.grant = false; ids = []; prepareSucceeds = false; clockAvailable = false;
    await expectLater(manager.refreshOwnership(), throwsA(isA<ServiceException>()));
    expect(manager.ownedEntitlementIds, isEmpty);
    clockAvailable = true; prepareSucceeds = true;
    expect(manager.ownedEntitlementIds, isEmpty,
      reason: 'QA019: a previously observed empty online entitlement set must invalidate the older signed grant before native clock recovery');
  });
  test('observed revocation is hidden while replacement clock sampling is pending', () async {
    await manager.refreshOwnership(); client.grant = false; ids = [];
    prepareGate = Completer<bool>(); prepareEntered = Completer<void>();
    final pending = manager.refreshOwnership(); await prepareEntered!.future;
    final during = manager.ownedEntitlementIds;
    prepareGate!.complete(true); await pending;
    expect(manager.ownedEntitlementIds, isEmpty);
    expect(during, isEmpty, reason: 'QA019: known revocation must hide older ownership before async sampling completes');
  });
  test('lease endpoint failure after fresh online observation denies old grant', () async {
    await manager.refreshOwnership(); client.failLease = true;
    await expectLater(manager.refreshOwnership(), throwsA(isA<ServiceException>()));
    expect(manager.ownedEntitlementIds, isEmpty);
    client.unavailable = true;
    await expectLater(manager.refreshOwnership(), throwsA(isA<ServiceException>()));
    expect(manager.ownedEntitlementIds, isEmpty);
  });
  test('session change during clock sampling cannot install stale lease', () async {
    prepareGate = Completer<bool>(); prepareEntered = Completer<void>();
    final pending = manager.refreshOwnership(); await prepareEntered!.future;
    client.identity = '00000000-0000-4000-8000-000000000002';
    await manager.createAccount(cloudConsent: true);
    prepareGate!.complete(true); await pending;
    expect(manager.ownedEntitlementIds, isEmpty); expect(revision, 0);
  });
  test('seed change during clock sampling cannot install old-seed grant', () async {
    prepareGate = Completer<bool>(); prepareEntered = Completer<void>();
    final pending = manager.refreshOwnership(); await prepareEntered!.future;
    seed = 'other.seed'; prepareGate!.complete(true); await pending;
    expect(manager.ownedEntitlementIds, isEmpty); expect(revision, 0);
  });
  test('unavailable account service retains only independently unexpired lease', () async {
    await manager.refreshOwnership(); client.unavailable = true;
    await expectLater(manager.refreshOwnership(), throwsA(isA<ServiceException>()));
    expect(manager.ownedEntitlementIds, {'pass.01'});
    elapsed = 3600000001;
    expect(manager.ownedEntitlementIds, isEmpty);
  });
  test('secure clear failure cannot reload a superseded grant after storage recovers', () async {
    await manager.refreshOwnership(); client.grant = false; ids = []; storage.fail = true;
    await expectLater(manager.refreshOwnership(), throwsA(isA<StateError>()));
    expect(manager.ownedEntitlementIds, isEmpty);
    storage.fail = false;
    await manager.restoreCachedOwnership();
    expect(manager.ownedEntitlementIds, isEmpty,
      reason: 'QA019: storage recovery must not reload an older lease after observed supersession');
  });
  test('a restore already waiting for a clock cannot undo newer revocation', () async {
    await manager.refreshOwnership();
    final oldGate = Completer<bool>(); prepareGate = oldGate; prepareEntered = Completer<void>();
    final restoring = manager.restoreCachedOwnership(); await prepareEntered!.future;
    prepareGate = null; prepareEntered = null; client.grant = false; ids = [];
    prepareSucceeds = false; clockAvailable = false;
    await expectLater(manager.refreshOwnership(), throwsA(isA<ServiceException>()));
    clockAvailable = true; prepareSucceeds = true; oldGate.complete(true); await restoring;
    expect(manager.ownedEntitlementIds, isEmpty,
      reason: 'QA019: an older restore must honor a newer online supersession');
  });
}
