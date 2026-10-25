import 'dart:convert';
import 'dart:io';
import 'package:cryptography/cryptography.dart';
import 'package:test/test.dart';
import 'package:tideglass_platform/signed_entitlements.dart';

const origin = 'https://service.example.invalid',
    account = 'test-account',
    seed = 'harbor.seed';
final start = DateTime.fromMillisecondsSinceEpoch(1792368000000, isUtc: true);
final algorithm = Ed25519();
late SimpleKeyPair key;
late SignedOwnershipVerifier verifier;
Future<Map<String, dynamic>> signed({
  int revision = 1,
  int lifetime = 60,
  List<String> ids = const ['pass.01'],
  String issuer = origin,
  String aid = account,
}) async {
  final bytes = utf8.encode(
    jsonEncode({
      'v': 1,
      'issuer': issuer,
      'account_id': aid,
      'linked_account_seed': seed,
      'issued_at': start.millisecondsSinceEpoch ~/ 1000,
      'expires_at': start.millisecondsSinceEpoch ~/ 1000 + lifetime,
      'revision': revision,
      'lease_id': 'synthetic-test-fixture',
      'entitlements': ids,
    }),
  );
  final signature = await algorithm.sign(bytes, keyPair: key);
  String b64(List<int> bytes) => base64Url.encode(bytes).replaceAll('=', '');
  return {
    'key_id': 'test-only',
    'payload': b64(bytes),
    'signature': b64(signature.bytes),
  };
}

void main() {
  setUp(() async {
    key = await algorithm.newKeyPairFromSeed(List.generate(32, (i) => i));
    verifier = SignedOwnershipVerifier(
      issuer: origin,
      pinnedPublicKeys: {'test-only': (await key.extractPublicKey()).bytes},
    );
  });
  test(
    'HTTP issuer requires explicit loopback-only development opt-in',
    () async {
      final pins = {'test-only': (await key.extractPublicKey()).bytes};
      expect(
        () => SignedOwnershipVerifier(
          issuer: 'http://localhost:8765',
          pinnedPublicKeys: pins,
        ),
        throwsArgumentError,
      );
      SignedOwnershipVerifier(
        issuer: 'http://localhost:8765',
        pinnedPublicKeys: pins,
        allowLocalDevelopment: true,
      );
      expect(
        () => SignedOwnershipVerifier(
          issuer: 'http://external.invalid',
          pinnedPublicKeys: pins,
          allowLocalDevelopment: true,
        ),
        throwsArgumentError,
      );
    },
  );
  test(
    'real Ed25519 verifies exact Python bytes and bound entitlement set',
    () async {
      final data =
          jsonDecode(
                File(
                  'test/fixtures/python_signed_lease.json',
                ).readAsStringSync(),
              )
              as Map;
      final value = await verifier.verify(
        (data['lease'] as Map).cast<String, dynamic>(),
        accountId: account,
        localAccountSeed: seed,
        now: start,
      );
      expect(value.entitlementIds, {'pass.01', 'soundtrack.01'});
    },
  );
  test(
    'tampering, unpinned keys, wrong identity, excessive TTL and expired leases reject',
    () async {
      final valid = await signed();
      final cases = [
        {...valid, 'signature': 'A' * 86},
        {...valid, 'key_id': 'untrusted'},
        await signed(issuer: 'https://other.invalid'),
        await signed(aid: 'other'),
        await signed(lifetime: 86401),
        await signed(lifetime: 0),
        await signed(ids: ['wallet.multiplier']),
      ];
      for (final envelope in cases) {
        await expectLater(
          verifier.verify(
            envelope,
            accountId: account,
            localAccountSeed: seed,
            now: start,
          ),
          throwsA(isA<OwnershipLeaseException>()),
        );
      }
      await expectLater(
        verifier.verify(
          valid,
          accountId: account,
          localAccountSeed: 'other',
          now: start,
        ),
        throwsA(isA<OwnershipLeaseException>()),
      );
      await expectLater(
        verifier.verify(
          valid,
          accountId: account,
          localAccountSeed: seed,
          now: start.add(const Duration(seconds: 60)),
        ),
        throwsA(isA<OwnershipLeaseException>()),
      );
    },
  );
  test(
    'secure reload requires continuing trusted device time; expiry includes sleep',
    () async {
      final storage = <String, String>{};
      var now = start;
      var elapsed = 1000000;
      var boot = 'boot.one';
      SecureOwnershipLeaseCache cache() => SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => storage[k],
        write: (k, v) async {
          storage[k] = v;
        },
        clock: () => now,
        deviceTime: () =>
            TrustedDeviceTime(bootId: boot, elapsedMicroseconds: elapsed),
      );
      final first = cache();
      expect(
        await first.accept(
          await signed(),
          accountId: account,
          localAccountSeed: seed,
        ),
        {'pass.01'},
      );
      elapsed += 30000000;
      now = now.add(const Duration(seconds: 30));
      final reloaded = cache();
      expect(await reloaded.load(accountId: account, localAccountSeed: seed), {
        'pass.01',
      });
      expect(reloaded.remaining.inSeconds, lessThanOrEqualTo(30));
      expect(
        reloaded.currentEntitlementIds(
          accountId: 'other',
          localAccountSeed: seed,
        ),
        isEmpty,
      );
      expect(
        reloaded.currentEntitlementIds(
          accountId: account,
          localAccountSeed: 'imported',
        ),
        isEmpty,
      );
      // Wall clock cannot extend the 60-second budget after another 31s asleep.
      elapsed += 31000000;
      expect(
        reloaded.currentEntitlementIds(
          accountId: account,
          localAccountSeed: seed,
        ),
        isEmpty,
      );
      boot = 'boot.two';
      expect(
        await cache().load(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
    },
  );
  test(
    'without persistent device evidence restart requires online refresh',
    () async {
      final storage = <String, String>{};
      SecureOwnershipLeaseCache cache() => SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => storage[k],
        write: (k, v) async {
          storage[k] = v;
        },
        clock: () => start,
      );
      final first = cache();
      await first.accept(
        await signed(),
        accountId: account,
        localAccountSeed: seed,
      );
      expect(
        first.currentEntitlementIds(accountId: account, localAccountSeed: seed),
        {'pass.01'},
      );
      expect(
        await cache().load(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
    },
  );
  test(
    'observed rollback across launches and native clock rollback reject',
    () async {
      final storage = <String, String>{};
      var now = start;
      var elapsed = 1000000;
      SecureOwnershipLeaseCache cache() => SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => storage[k],
        write: (k, v) async {
          storage[k] = v;
        },
        clock: () => now,
        deviceTime: () =>
            TrustedDeviceTime(bootId: 'boot', elapsedMicroseconds: elapsed),
      );
      final first = cache();
      await first.accept(
        await signed(),
        accountId: account,
        localAccountSeed: seed,
      );
      now = now.add(const Duration(seconds: 10));
      elapsed += 10000000;
      await first.checkpoint(accountId: account);
      now = now.subtract(const Duration(seconds: 1));
      await expectLater(
        cache().load(accountId: account, localAccountSeed: seed),
        throwsA(isA<OwnershipLeaseException>()),
      );
      expect(
        first.currentEntitlementIds(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
      now = start.add(const Duration(seconds: 11));
      elapsed = 0;
      expect(
        await cache().load(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
    },
  );
  test(
    'higher empty lease and logout retain high-water revision against replay',
    () async {
      final storage = <String, String>{};
      final cache = SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => storage[k],
        write: (k, v) async {
          storage[k] = v;
        },
        clock: () => start,
      );
      final original = await signed();
      await cache.accept(original, accountId: account, localAccountSeed: seed);
      await cache.accept(
        await signed(revision: 2, ids: []),
        accountId: account,
        localAccountSeed: seed,
      );
      expect(
        cache.currentEntitlementIds(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
      await expectLater(
        cache.accept(original, accountId: account, localAccountSeed: seed),
        throwsA(isA<OwnershipLeaseException>()),
      );
      await cache.clear(accountId: account);
      await expectLater(
        cache.accept(
          await signed(revision: 2),
          accountId: account,
          localAccountSeed: seed,
        ),
        throwsA(isA<OwnershipLeaseException>()),
      );
    },
  );
  test(
    'secure-write failure cannot expose an otherwise valid signed grant',
    () async {
      final cache = SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => null,
        write: (k, v) async {
          throw StateError('secure store unavailable');
        },
        clock: () => start,
      );
      await expectLater(
        cache.accept(
          await signed(),
          accountId: account,
          localAccountSeed: seed,
        ),
        throwsStateError,
      );
      expect(
        cache.currentEntitlementIds(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
    },
  );
  test(
    'missing sample hides without burning checkpoint or reload; sleep still expires',
    () async {
      final storage = <String, String>{};
      TrustedDeviceTime? device = const TrustedDeviceTime(
        bootId: 'boot.a',
        elapsedMicroseconds: 1000000,
      );
      SecureOwnershipLeaseCache make() => SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => storage[k],
        write: (k, v) async {
          storage[k] = v;
        },
        clock: () => start,
        deviceTime: () => device,
      );
      final cache = make();
      await cache.accept(
        await signed(),
        accountId: account,
        localAccountSeed: seed,
      );
      final before = jsonDecode(storage.values.single) as Map;
      device = null;
      expect(
        cache.currentEntitlementIds(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
      await cache.checkpoint(accountId: account);
      expect(
        (jsonDecode(storage.values.single) as Map)['device'],
        before['device'],
      );
      expect(
        (jsonDecode(storage.values.single) as Map)['lease'],
        before['lease'],
      );
      expect(
        await make().load(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
      expect((jsonDecode(storage.values.single) as Map)['lease'], isNotNull);
      device = const TrustedDeviceTime(
        bootId: 'boot.a',
        elapsedMicroseconds: 31000000,
      );
      expect(
        cache.currentEntitlementIds(accountId: account, localAccountSeed: seed),
        {'pass.01'},
      );
      expect(await make().load(accountId: account, localAccountSeed: seed), {
        'pass.01',
      });
      device = const TrustedDeviceTime(
        bootId: 'boot.a',
        elapsedMicroseconds: 62000000,
      );
      expect(
        cache.currentEntitlementIds(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
    },
  );

  test(
    'channel uncertainty charges upper bound and survives checkpoint reload',
    () async {
      final storage = <String, String>{};
      var elapsed = 1000000;
      SecureOwnershipLeaseCache make() => SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => storage[k],
        write: (k, v) async {
          storage[k] = v;
        },
        clock: () => start,
        deviceTime: () => TrustedDeviceTime(
          bootId: 'boot.a',
          elapsedMicroseconds: elapsed,
          uncertaintyMicroseconds: 2000000,
        ),
      );
      final cache = make();
      await cache.accept(
        await signed(),
        accountId: account,
        localAccountSeed: seed,
      );
      expect(cache.remaining.inMicroseconds, lessThanOrEqualTo(58000000));
      elapsed += 56000000;
      expect(cache.remaining.inMicroseconds, lessThanOrEqualTo(2000000));
      await cache.checkpoint(accountId: account);
      expect(
        await make().load(accountId: account, localAccountSeed: seed),
        isEmpty,
      );
    },
  );

  test(
    'old account clear and erase never drop current account grants',
    () async {
      final storage = <String, String>{};
      final cache = SecureOwnershipLeaseCache(
        verifier: verifier,
        read: (k) async => storage[k],
        write: (k, v) async {
          storage[k] = v;
        },
        delete: (k) async {
          storage.remove(k);
        },
        clock: () => start,
      );
      await cache.accept(
        await signed(),
        accountId: account,
        localAccountSeed: seed,
      );
      await cache.accept(
        await signed(aid: 'account.b'),
        accountId: 'account.b',
        localAccountSeed: seed,
      );
      await cache.clear(accountId: account);
      expect(
        cache.currentEntitlementIds(
          accountId: 'account.b',
          localAccountSeed: seed,
        ),
        {'pass.01'},
      );
      await cache.erase(accountId: account);
      expect(storage, hasLength(1));
      expect(
        cache.currentEntitlementIds(
          accountId: 'account.b',
          localAccountSeed: seed,
        ),
        {'pass.01'},
      );
      await cache.erase(accountId: 'account.b');
      expect(storage, isEmpty);
      expect(
        cache.currentEntitlementIds(
          accountId: 'account.b',
          localAccountSeed: seed,
        ),
        isEmpty,
      );
    },
  );

  test(
    'failed or unconfigured erase hides grants and reports cleanup failure',
    () async {
      for (final configured in [true, false]) {
        final storage = <String, String>{};
        final cache = SecureOwnershipLeaseCache(
          verifier: verifier,
          read: (k) async => storage[k],
          write: (k, v) async {
            storage[k] = v;
          },
          delete: configured
              ? (k) async {
                  throw StateError('device locked');
                }
              : null,
          clock: () => start,
        );
        await cache.accept(
          await signed(),
          accountId: account,
          localAccountSeed: seed,
        );
        await expectLater(
          cache.erase(accountId: account),
          throwsA(
            configured ? isA<StateError>() : isA<OwnershipLeaseException>(),
          ),
        );
        expect(
          cache.currentEntitlementIds(
            accountId: account,
            localAccountSeed: seed,
          ),
          isEmpty,
        );
        expect(storage, hasLength(1));
      }
    },
  );

  test(
    'key replacement or new Apple process invalidates persisted ownership',
    () async {
      for (final epoch in ['android.new_key', 'apple.process.new']) {
        final storage = <String, String>{};
        var identity = 'previous.epoch';
        SecureOwnershipLeaseCache make() => SecureOwnershipLeaseCache(
          verifier: verifier,
          read: (k) async => storage[k],
          write: (k, v) async {
            storage[k] = v;
          },
          clock: () => start,
          deviceTime: () =>
              TrustedDeviceTime(bootId: identity, elapsedMicroseconds: 1000000),
        );
        await make().accept(
          await signed(),
          accountId: account,
          localAccountSeed: seed,
        );
        identity = epoch;
        expect(
          await make().load(accountId: account, localAccountSeed: seed),
          isEmpty,
        );
        expect((jsonDecode(storage.values.single) as Map)['lease'], isNull);
      }
    },
  );
}
