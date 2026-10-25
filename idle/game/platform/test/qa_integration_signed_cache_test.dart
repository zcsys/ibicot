import 'dart:async';
import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'package:test/test.dart';
import 'package:tideglass_platform/signed_entitlements.dart';

const issuer = 'https://service.example.invalid';
const account = 'independent-account';
const seed = 'independent.seed';
final start = DateTime.fromMillisecondsSinceEpoch(1792368000000, isUtc: true);
final algorithm = Ed25519();
late SimpleKeyPair key;
late SignedOwnershipVerifier verifier;
Future<Map<String, dynamic>> lease({int revision = 1, List<String> ids = const ['pass.01']}) async {
  final payload = utf8.encode(jsonEncode({'v': 1, 'issuer': issuer, 'account_id': account,
    'linked_account_seed': seed, 'issued_at': start.millisecondsSinceEpoch ~/ 1000,
    'expires_at': start.millisecondsSinceEpoch ~/ 1000 + 60, 'revision': revision,
    'lease_id': 'explicit-independent-fixture', 'entitlements': ids}));
  final signature = await algorithm.sign(payload, keyPair: key);
  String b64(List<int> bytes) => base64Url.encode(bytes).replaceAll('=', '');
  return {'key_id': 'independent-key', 'payload': b64(payload), 'signature': b64(signature.bytes)};
}
void main() {
  setUp(() async {
    key = await algorithm.newKeyPairFromSeed(List.generate(32, (i) => 255 - i));
    verifier = SignedOwnershipVerifier(issuer: issuer, pinnedPublicKeys: {
      'independent-key': (await key.extractPublicKey()).bytes});
  });
  test('accept storage read cannot restart a lease after trusted elapsed expiry', () async {
    final gate = Completer<String?>(), entered = Completer<void>();
    var elapsed = 0;
    final cache = SecureOwnershipLeaseCache(verifier: verifier,
      read: (k) { entered.complete(); return gate.future; }, write: (k, v) async {},
      clock: () => start, deviceTime: () => TrustedDeviceTime(bootId: 'device-and-boot', elapsedMicroseconds: elapsed));
    final pending = cache.accept(await lease(), accountId: account, localAccountSeed: seed);
    await entered.future;
    elapsed = const Duration(seconds: 61).inMicroseconds;
    gate.complete(null);
    Set<String> returned = {};
    try { returned = await pending; } on OwnershipLeaseException { /* Rejection is safe. */ }
    final projected = cache.currentEntitlementIds(accountId: account, localAccountSeed: seed);
    expect({'returned': returned, 'projected': projected}, {'returned': <String>{}, 'projected': <String>{}},
      reason: 'QA017: trusted elapsed time spent awaiting secure read must count against the original lease');
  });
  test('accept return rechecks expiry after secure persistence finishes', () async {
    final entered = Completer<void>(), gate = Completer<void>();
    var now = start, elapsed = 0;
    final cache = SecureOwnershipLeaseCache(verifier: verifier, read: (k) async => null,
      write: (k, v) { entered.complete(); return gate.future; }, clock: () => now,
      deviceTime: () => TrustedDeviceTime(bootId: 'device-and-boot', elapsedMicroseconds: elapsed));
    final pending = cache.accept(await lease(), accountId: account, localAccountSeed: seed);
    await entered.future; now = start.add(const Duration(seconds: 61)); elapsed = 61000000; gate.complete();
    Set<String> returned = {};
    try { returned = await pending; } on OwnershipLeaseException { /* Safe rejection. */ }
    expect(cache.currentEntitlementIds(accountId: account, localAccountSeed: seed), isEmpty);
    expect(returned, isEmpty, reason: 'QA017: accept returned expired ownership after durable write');
  });
  test('load return rechecks expiry after secure persistence finishes', () async {
    final storage = <String, String>{}; var now = start, elapsed = 0;
    TrustedDeviceTime device() => TrustedDeviceTime(bootId: 'device-and-boot', elapsedMicroseconds: elapsed);
    final first = SecureOwnershipLeaseCache(verifier: verifier, read: (k) async => storage[k],
      write: (k, v) async { storage[k] = v; }, clock: () => now, deviceTime: device);
    await first.accept(await lease(), accountId: account, localAccountSeed: seed);
    final entered = Completer<void>(), gate = Completer<void>();
    final reopened = SecureOwnershipLeaseCache(verifier: verifier, read: (k) async => storage[k],
      write: (k, v) async { entered.complete(); await gate.future; storage[k] = v; }, clock: () => now, deviceTime: device);
    final pending = reopened.load(accountId: account, localAccountSeed: seed);
    await entered.future; now = start.add(const Duration(seconds: 61)); elapsed = 61000000; gate.complete();
    Set<String> returned = {};
    try { returned = await pending; } on OwnershipLeaseException { /* Safe rejection. */ }
    expect(reopened.currentEntitlementIds(accountId: account, localAccountSeed: seed), isEmpty);
    expect(returned, isEmpty, reason: 'QA017: load returned expired ownership after durable write');
  });
  test('empty lease serialization blocks replay across a fresh instance', () async {
    final storage = <String, String>{};
    SecureOwnershipLeaseCache cache() => SecureOwnershipLeaseCache(verifier: verifier,
      read: (k) async => storage[k], write: (k, v) async { storage[k] = v; }, clock: () => start,
      deviceTime: () => const TrustedDeviceTime(bootId: 'device-and-boot', elapsedMicroseconds: 100));
    final c = cache();
    await c.accept(await lease(), accountId: account, localAccountSeed: seed);
    await c.accept(await lease(revision: 2, ids: []), accountId: account, localAccountSeed: seed);
    final second = cache(); expect(await second.load(accountId: account, localAccountSeed: seed), isEmpty);
    await expectLater(second.accept(await lease(), accountId: account, localAccountSeed: seed), throwsA(isA<OwnershipLeaseException>()));
  });
  test('failed secure write never replaces valid storage with a partial lease', () async {
    final storage = <String, String>{}; var fail = false;
    final c = SecureOwnershipLeaseCache(verifier: verifier, read: (k) async => storage[k],
      write: (k, v) async { if (fail) throw StateError('fixture unavailable'); storage[k] = v; }, clock: () => start);
    await c.accept(await lease(), accountId: account, localAccountSeed: seed); final before = Map<String, String>.from(storage); fail = true;
    await expectLater(c.accept(await lease(revision: 2, ids: []), accountId: account, localAccountSeed: seed), throwsStateError);
    expect(storage, before); expect(c.currentEntitlementIds(accountId: account, localAccountSeed: seed), isEmpty);
  });
  test('unknown pinned key and changed exact payload bytes reject before secure write', () async {
    var writes = 0;
    final c = SecureOwnershipLeaseCache(verifier: verifier, read: (k) async => null,
      write: (k, v) async { writes++; }, clock: () => start);
    final envelope = await lease();
    for (final bad in [ {...envelope, 'key_id': 'untrusted'}, {...envelope, 'payload': base64Url.encode(utf8.encode('{}')).replaceAll('=', '')} ]) {
      await expectLater(c.accept(bad, accountId: account, localAccountSeed: seed), throwsA(isA<OwnershipLeaseException>()));
    }
    expect(writes, 0); expect(c.currentEntitlementIds(accountId: account, localAccountSeed: seed), isEmpty);
  });
}
