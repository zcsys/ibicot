import 'dart:async';
import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass_platform/signed_entitlements.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'native_services_test.dart' show MemoryCredentials, TestClient;

class LeaseClient extends TestClient {
  late Future<Map<String, dynamic>> Function() signLease;
  bool failLease = false;
  Completer<Map<String, dynamic>>? pendingOwnership;
  @override
  Future<Map<String, dynamic>> ownershipLease() async {
    if (failLease) throw const ServiceException('verification_unavailable');
    return {'lease': await signLease()};
  }

  @override
  Future<Map<String, dynamic>> entitlements() async {
    final pending = pendingOwnership;
    pendingOwnership = null;
    return pending == null ? super.entitlements() : pending.future;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final algorithm = Ed25519();
  late SimpleKeyPair key;
  late SignedOwnershipVerifier verifier;
  late MemoryCredentials storage;
  late LeaseClient client;
  late NativeServicesManager manager;
  late SecureOwnershipLeaseCache cache;
  late DateTime now;
  var revision = 0, elapsed = 0;
  var ids = <String>['pass.01'];
  var seed = 'main.seed';
  var boot = 'device-only-fixture-boot';
  SecureOwnershipLeaseCache makeCache({bool nativeClock = true}) =>
      SecureOwnershipLeaseCache(
        verifier: verifier,
        read: storage.read,
        write: storage.write,
        delete: storage.delete,
        clock: () => now,
        deviceTime: nativeClock
            ? () =>
                  TrustedDeviceTime(bootId: boot, elapsedMicroseconds: elapsed)
            : null,
      );
  setUp(() async {
    key = await algorithm.newKeyPairFromSeed(List.generate(32, (i) => i));
    verifier = SignedOwnershipVerifier(
      issuer: 'https://example.invalid',
      pinnedPublicKeys: {'test-only': (await key.extractPublicKey()).bytes},
    );
    storage = MemoryCredentials();
    client = LeaseClient()..grant = true;
    now = DateTime.now().toUtc();
    revision = 0;
    elapsed = 0;
    ids = ['pass.01'];
    seed = 'main.seed';
    boot = 'device-only-fixture-boot';
    client.signLease = () async {
      final bytes = utf8.encode(
        jsonEncode({
          'v': 1,
          'issuer': 'https://example.invalid',
          'account_id': client.identity,
          'linked_account_seed': 'main.seed',
          'issued_at': now.millisecondsSinceEpoch ~/ 1000,
          'expires_at': now.millisecondsSinceEpoch ~/ 1000 + 3600,
          'revision': ++revision,
          'lease_id': 'synthetic-lease-$revision',
          'entitlements': ids,
        }),
      );
      final signature = await algorithm.sign(bytes, keyPair: key);
      String b64(List<int> v) => base64Url.encode(v).replaceAll('=', '');
      return {
        'key_id': 'test-only',
        'payload': b64(bytes),
        'signature': b64(signature.bytes),
      };
    };
    cache = makeCache();
    manager = NativeServicesManager(
      client: client,
      credentials: storage,
      localAccountSeed: () => seed,
      ownershipCache: cache,
    );
    await manager.createAccount(cloudConsent: true);
  });
  tearDown(() {
    manager.dispose();
    client.close();
  });

  test(
    'actual signed grant covers outage only until its elapsed expiry',
    () async {
      await manager.refreshOwnership();
      expect(manager.ownedEntitlementIds, {'pass.01'});
      client.unavailable = true;
      await expectLater(
        manager.refreshOwnership(),
        throwsA(isA<ServiceException>()),
      );
      expect(manager.ownedEntitlementIds, {'pass.01'});
      elapsed += 3600000001;
      expect(manager.ownedEntitlementIds, isEmpty);
    },
  );
  test(
    'fresh refund replaces the cached grant and cannot revive offline',
    () async {
      await manager.refreshOwnership();
      ids = [];
      client.grant = false;
      await manager.refreshOwnership();
      expect(manager.ownedEntitlementIds, isEmpty);
      client.unavailable = true;
      await expectLater(
        manager.refreshOwnership(),
        throwsA(isA<ServiceException>()),
      );
      expect(manager.ownedEntitlementIds, isEmpty);
    },
  );
  test(
    'a superseded same-account ownership response cannot undo newer refund',
    () async {
      await manager.refreshOwnership();
      final oldResponse = await client.entitlements();
      final pending = Completer<Map<String, dynamic>>();
      client.pendingOwnership = pending;
      final old = manager.refreshOwnership();
      ids = [];
      client.grant = false;
      await manager.refreshOwnership();
      pending.complete(oldResponse);
      await old;
      expect(manager.ownedEntitlementIds, isEmpty);
      expect(revision, 2);
    },
  );
  test('progression seed mismatch and lease outage fail closed', () async {
    await manager.refreshOwnership();
    seed = 'another.seed';
    expect(manager.ownedEntitlementIds, isEmpty);
    await expectLater(
      manager.refreshOwnership(),
      throwsA(isA<OwnershipLeaseException>()),
    );
    expect(manager.ownedEntitlementIds, isEmpty);
    seed = 'main.seed';
    client.failLease = true;
    await expectLater(
      manager.refreshOwnership(),
      throwsA(isA<ServiceException>()),
    );
    expect(manager.ownedEntitlementIds, isEmpty);
  });
  test(
    'secure restore requires matching device boot and remaining time',
    () async {
      await manager.refreshOwnership();
      await manager.checkpointOwnership();
      manager.dispose();
      elapsed += 600000000;
      now = now.add(const Duration(minutes: 10));
      cache = makeCache();
      manager = NativeServicesManager(
        client: client,
        credentials: storage,
        localAccountSeed: () => seed,
        ownershipCache: cache,
      );
      await manager.restoreCachedOwnership();
      expect(manager.ownedEntitlementIds, {'pass.01'});
      boot = 'another-device-or-boot';
      expect(manager.ownedEntitlementIds, isEmpty);
    },
  );
  test(
    'process restart without native evidence cannot restore ownership',
    () async {
      await manager.refreshOwnership();
      manager.dispose();
      cache = makeCache(nativeClock: false);
      manager = NativeServicesManager(
        client: client,
        credentials: storage,
        localAccountSeed: () => seed,
        ownershipCache: cache,
      );
      await manager.restoreCachedOwnership();
      expect(manager.ownedEntitlementIds, isEmpty);
    },
  );
  test(
    'explicit local signout clears device grant as well as session',
    () async {
      await manager.refreshOwnership();
      await manager.signOut(localOnly: true);
      expect(manager.ownedEntitlementIds, isEmpty);
      await manager.createAccount(cloudConsent: true);
      await manager.restoreCachedOwnership();
      expect(manager.ownedEntitlementIds, isEmpty);
    },
  );
  test(
    'confirmed account deletion removes the signed lease device record',
    () async {
      await manager.refreshOwnership();
      expect(
        storage.values.keys.any(
          (key) => key.startsWith('tideglass.ownership.v1.'),
        ),
        isTrue,
      );
      await manager.deleteAccount(recoveryCode: 'fixture', confirmDelete: true);
      expect(manager.ownedEntitlementIds, isEmpty);
      expect(
        storage.values.keys.any(
          (key) => key.startsWith('tideglass.ownership.v1.'),
        ),
        isFalse,
      );
    },
  );
}
