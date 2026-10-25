/// Independent signed ownership only; saved gameplay cannot authorize access.
library;

import 'dart:async';
import 'dart:convert';
import 'package:cryptography/cryptography.dart';

class OwnershipLeaseException implements Exception {
  const OwnershipLeaseException(this.code);
  final String code;
  @override
  String toString() => 'OwnershipLeaseException($code)';
}

const _allowed = {
  'cosmetic.shop.01',
  'cosmetic.shop.02',
  'cosmetic.shop.03',
  'cosmetic.shop.04',
  'pass.01',
  'soundtrack.01',
};

class VerifiedOwnershipLease {
  VerifiedOwnershipLease._(
    this.accountId,
    this.localAccountSeed,
    this.expiresAt,
    this.revision,
    this.entitlementIds,
    this.envelope,
  );
  final String accountId, localAccountSeed;
  final DateTime expiresAt;
  final int revision;
  final Set<String> entitlementIds;
  final Map<String, dynamic> envelope;
}

class SignedOwnershipVerifier {
  SignedOwnershipVerifier({
    required this.issuer,
    required Map<String, List<int>> pinnedPublicKeys,
    bool allowLocalDevelopment = false,
  }) : _keys = Map.unmodifiable(
         pinnedPublicKeys.map(
           (id, bytes) => MapEntry(
             id,
             SimplePublicKey(
               List<int>.unmodifiable(bytes),
               type: KeyPairType.ed25519,
             ),
           ),
         ),
       ) {
    final uri = Uri.parse(issuer);
    final local =
        allowLocalDevelopment &&
        uri.scheme == 'http' &&
        {'localhost', '127.0.0.1', '::1'}.contains(uri.host);
    if ((uri.scheme != 'https' && !local) ||
        uri.host.isEmpty ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment ||
        uri.path.isNotEmpty ||
        _keys.isEmpty ||
        _keys.values.any((key) => key.bytes.length != 32)) {
      throw ArgumentError(
        'Pin Ed25519 public keys and exact HTTPS issuer origin.',
      );
    }
  }
  final String issuer;
  final Map<String, SimplePublicKey> _keys;
  final _algorithm = Ed25519();
  Future<VerifiedOwnershipLease> verify(
    Map<String, dynamic> envelope, {
    required String accountId,
    required String localAccountSeed,
    required DateTime now,
  }) async {
    try {
      if (envelope.length != 3 ||
          !envelope.keys.toSet().containsAll({
            'key_id',
            'payload',
            'signature',
          }) ||
          envelope['key_id'] is! String ||
          envelope['payload'] is! String ||
          envelope['signature'] is! String) {
        throw const OwnershipLeaseException('invalid_lease');
      }
      final key = _keys[envelope['key_id']];
      if (key == null)
        throw const OwnershipLeaseException('untrusted_signing_key');
      final encoded = envelope['payload'] as String,
          signed = envelope['signature'] as String;
      final pattern = RegExp(r'^[A-Za-z0-9_-]+$');
      if (encoded.length > 16384 ||
          !pattern.hasMatch(encoded) ||
          signed.length != 86 ||
          !pattern.hasMatch(signed))
        throw const OwnershipLeaseException('invalid_lease');
      final bytes = base64Url.decode(base64Url.normalize(encoded));
      if (!await _algorithm.verify(
        bytes,
        signature: Signature(
          base64Url.decode(base64Url.normalize(signed)),
          publicKey: key,
        ),
      ))
        throw const OwnershipLeaseException('invalid_signature');
      final value = jsonDecode(utf8.decode(bytes));
      const fields = {
        'v',
        'issuer',
        'account_id',
        'linked_account_seed',
        'issued_at',
        'expires_at',
        'revision',
        'lease_id',
        'entitlements',
      };
      if (value is! Map ||
          value.length != fields.length ||
          !value.keys.toSet().containsAll(fields) ||
          value['v'] != 1 ||
          value['issuer'] != issuer ||
          value['account_id'] != accountId ||
          value['linked_account_seed'] != localAccountSeed ||
          localAccountSeed.isEmpty ||
          value['issued_at'] is! int ||
          value['expires_at'] is! int ||
          value['revision'] is! int ||
          value['revision'] <= 0 ||
          value['lease_id'] is! String ||
          value['entitlements'] is! List)
        throw const OwnershipLeaseException('lease_binding_rejected');
      final issued = value['issued_at'] as int,
          expires = value['expires_at'] as int;
      if (issued < 0 ||
          expires <= issued ||
          expires - issued > 86400 ||
          now.millisecondsSinceEpoch ~/ 1000 < issued ||
          now.millisecondsSinceEpoch ~/ 1000 >= expires)
        throw const OwnershipLeaseException('lease_expired_or_clock_invalid');
      final ids = value['entitlements'] as List;
      if (ids.length > _allowed.length ||
          ids.any((id) => id is! String || !_allowed.contains(id)) ||
          ids.toSet().length != ids.length)
        throw const OwnershipLeaseException('invalid_entitlement');
      return VerifiedOwnershipLease._(
        accountId,
        localAccountSeed,
        DateTime.fromMillisecondsSinceEpoch(expires * 1000, isUtc: true),
        value['revision'] as int,
        Set<String>.unmodifiable(ids.cast<String>()),
        Map<String, dynamic>.unmodifiable(envelope),
      );
    } on OwnershipLeaseException {
      rethrow;
    } catch (_) {
      throw const OwnershipLeaseException('invalid_lease');
    }
  }
}

/// Native clock includes sleep. Epoch binds this device/boot, or is unique to
/// this process when reliable native boot identity is unavailable.
/// Secure storage must be device-only, excluded from migration and backups.
class TrustedDeviceTime {
  const TrustedDeviceTime({
    required this.bootId,
    required this.elapsedMicroseconds,
    this.uncertaintyMicroseconds = 0,
  });
  final String bootId;
  final int elapsedMicroseconds, uncertaintyMicroseconds;
}

typedef SecureLeaseRead = Future<String?> Function(String key);
typedef SecureLeaseWrite = Future<void> Function(String key, String value);
typedef SecureLeaseDelete = Future<void> Function(String key);

/// Keychain/Keystore callbacks only. Without native elapsed evidence, persisted
/// grants require online refresh after process exit; wall time alone is unsafe.
class SecureOwnershipLeaseCache {
  SecureOwnershipLeaseCache({
    required this.verifier,
    required SecureLeaseRead read,
    required SecureLeaseWrite write,
    SecureLeaseDelete? delete,
    DateTime Function()? clock,
    this.deviceTime,
  }) : _read = read,
       _write = write,
       _delete = delete,
       _clock = clock ?? (() => DateTime.now().toUtc());
  final SignedOwnershipVerifier verifier;
  final SecureLeaseRead _read;
  final SecureLeaseWrite _write;
  final SecureLeaseDelete? _delete;
  final DateTime Function() _clock;
  final TrustedDeviceTime? Function()? deviceTime;
  Future<void> _tail = Future.value();
  VerifiedOwnershipLease? _lease;
  DateTime? _lastObserved;
  Duration _budget = Duration.zero;
  Stopwatch _elapsed = Stopwatch();
  TrustedDeviceTime? _anchor;
  bool _rollback = false;
  Future<T> _serial<T>(Future<T> Function() action) {
    final result = _tail.then((_) => action());
    _tail = result.then<void>((_) {}, onError: (Object _) {});
    return result;
  }

  String _key(String account) =>
      'tideglass.ownership.v1.${base64Url.encode(utf8.encode('${verifier.issuer}|$account'))}';
  Future<Map<String, dynamic>> _record(String account) async {
    final raw = await _read(_key(account));
    if (raw == null) return {'revision': 0, 'last_seen_us': 0};
    if (raw.length > 32768)
      throw const OwnershipLeaseException('secure_cache_invalid');
    final data = jsonDecode(raw);
    if (data is! Map<String, dynamic> ||
        data['revision'] is! int ||
        data['last_seen_us'] is! int ||
        data['revision'] < 0 ||
        data['last_seen_us'] < 0)
      throw const OwnershipLeaseException('secure_cache_invalid');
    return data;
  }

  Future<void> _burn(String account, Map<String, dynamic> record) async {
    final observed = _lastObserved?.microsecondsSinceEpoch ?? 0;
    final now = _clock().toUtc().microsecondsSinceEpoch;
    var high = record['last_seen_us'] as int;
    if (observed > high) high = observed;
    if (now > high) high = now;
    await _write(
      _key(account),
      jsonEncode({'revision': record['revision'], 'last_seen_us': high}),
    );
  }

  void _invalidate(VerifiedOwnershipLease lease) {
    _rollback = true;
    _drop();
    unawaited(
      _serial(() async {
        await _burn(lease.accountId, await _record(lease.accountId));
      }).catchError((Object _) {}),
    );
  }

  void _drop() {
    _lease = null;
    _budget = Duration.zero;
    _elapsed.stop();
    _elapsed.reset();
    _anchor = null;
  }

  Duration get remaining {
    final lease = _lease;
    if (lease == null || _rollback) return Duration.zero;
    final now = _clock().toUtc();
    if (_lastObserved != null && now.isBefore(_lastObserved!)) {
      _invalidate(lease);
      return Duration.zero;
    }
    _lastObserved = now;
    var elapsed = _elapsed.elapsed;
    if (_anchor != null) {
      final device = deviceTime?.call();
      if (device == null) return Duration.zero;
      if (device.uncertaintyMicroseconds < 0 ||
          device.bootId != _anchor!.bootId ||
          device.elapsedMicroseconds < _anchor!.elapsedMicroseconds) {
        _invalidate(lease);
        return Duration.zero;
      }
      final native = Duration(
        microseconds:
            device.elapsedMicroseconds +
            device.uncertaintyMicroseconds -
            _anchor!.elapsedMicroseconds,
      );
      if (native > elapsed) elapsed = native;
    }
    final wall = lease.expiresAt.difference(now), monotonic = _budget - elapsed;
    final left = wall < monotonic ? wall : monotonic;
    if (left <= Duration.zero) {
      _drop();
      return Duration.zero;
    }
    return left;
  }

  Set<String> currentEntitlementIds({
    required String accountId,
    required String localAccountSeed,
  }) {
    if (remaining <= Duration.zero ||
        _lease?.accountId != accountId ||
        _lease?.localAccountSeed != localAccountSeed)
      return const {};
    return _lease!.entitlementIds;
  }

  void _activate(
    VerifiedOwnershipLease lease,
    Duration budget,
    TrustedDeviceTime? device,
    DateTime now, {
    Stopwatch? operationElapsed,
  }) {
    _drop();
    _rollback = false;
    _lease = lease;
    _budget = budget;
    _lastObserved = now;
    _anchor = device;
    if (operationElapsed != null) _elapsed = operationElapsed;
    _elapsed.start();
  }

  Map<String, dynamic> _stored(
    VerifiedOwnershipLease lease,
    DateTime now,
    Duration budget,
    TrustedDeviceTime? device,
  ) => {
    'revision': lease.revision,
    'last_seen_us': now.microsecondsSinceEpoch,
    'lease': lease.envelope,
    'remaining_us': budget.inMicroseconds,
    if (device != null)
      'device': {
        'boot_id': device.bootId,
        'elapsed_us': device.elapsedMicroseconds,
      },
  };
  Future<Set<String>> accept(
    Map<String, dynamic> envelope, {
    required String accountId,
    required String localAccountSeed,
  }) {
    // Capture before queueing or any storage/crypto await. Channel, queue and
    // secure-storage latency must never restart a signed lease's lifetime.
    final now = _clock().toUtc(), device = deviceTime?.call();
    final operationElapsed = Stopwatch()..start();
    return _serial(() async {
      _drop();
      if (deviceTime != null && device == null)
        throw const OwnershipLeaseException('device_clock_unavailable');
      if (device != null &&
          (device.bootId.isEmpty ||
              device.elapsedMicroseconds < 0 ||
              device.uncertaintyMicroseconds < 0))
        throw const OwnershipLeaseException('device_clock_invalid');
      final previous = await _record(accountId);
      if (now.microsecondsSinceEpoch < previous['last_seen_us'])
        throw const OwnershipLeaseException('clock_rollback');
      final lease = await verifier.verify(
        envelope,
        accountId: accountId,
        localAccountSeed: localAccountSeed,
        now: now,
      );
      if (lease.revision <= previous['revision'])
        throw const OwnershipLeaseException('lease_replay');
      final budget = lease.expiresAt.difference(now);
      await _write(
        _key(accountId),
        jsonEncode(_stored(lease, now, budget, device)),
      );
      _activate(lease, budget, device, now, operationElapsed: operationElapsed);
      // Durable high-water remains even when an await crossed expiry. Never
      // return the signed IDs directly: recheck current wall/native evidence.
      return currentEntitlementIds(
        accountId: accountId,
        localAccountSeed: localAccountSeed,
      );
    });
  }

  Future<Set<String>> load({
    required String accountId,
    required String localAccountSeed,
  }) {
    final now = _clock().toUtc(), device = deviceTime?.call();
    final operationElapsed = Stopwatch()..start();
    return _serial(() async {
      _drop();
      final record = await _record(accountId);
      if (now.microsecondsSinceEpoch < record['last_seen_us']) {
        await _burn(accountId, record);
        throw const OwnershipLeaseException('clock_rollback');
      }
      final saved = record['device'];
      if (device == null) return <String>{};
      if (record['lease'] == null ||
          saved is! Map ||
          device.uncertaintyMicroseconds < 0 ||
          saved['boot_id'] != device.bootId ||
          saved['elapsed_us'] is! int ||
          device.elapsedMicroseconds < saved['elapsed_us'] ||
          record['remaining_us'] is! int ||
          record['remaining_us'] <= 0) {
        await _burn(accountId, record);
        return <String>{};
      }
      late VerifiedOwnershipLease lease;
      try {
        lease = await verifier.verify(
          (record['lease'] as Map).cast<String, dynamic>(),
          accountId: accountId,
          localAccountSeed: localAccountSeed,
          now: now,
        );
      } catch (_) {
        await _burn(accountId, record);
        rethrow;
      }
      if (lease.revision != record['revision'])
        throw const OwnershipLeaseException('lease_replay');
      final elapsed =
          device.elapsedMicroseconds +
          device.uncertaintyMicroseconds -
          (saved['elapsed_us'] as int);
      var budget = Duration(
        microseconds: (record['remaining_us'] as int) - elapsed,
      );
      if (budget <= Duration.zero) {
        await _burn(accountId, record);
        return <String>{};
      }
      final wall = lease.expiresAt.difference(now);
      if (wall < budget) budget = wall;
      await _write(
        _key(accountId),
        jsonEncode(_stored(lease, now, budget, device)),
      );
      _activate(lease, budget, device, now, operationElapsed: operationElapsed);
      return currentEntitlementIds(
        accountId: accountId,
        localAccountSeed: localAccountSeed,
      );
    });
  }

  /// Call on background/suspend. Preserves observed wall-clock high-water mark.
  Future<void> checkpoint({required String accountId}) => _serial(() async {
    final record = await _record(accountId),
        now = _clock().toUtc(),
        device = deviceTime?.call(),
        left = remaining;
    final previous = record['last_seen_us'] as int;
    final high = now.microsecondsSinceEpoch > previous
        ? now.microsecondsSinceEpoch
        : previous;
    if (_lease?.accountId == accountId && left > Duration.zero) {
      await _write(
        _key(accountId),
        jsonEncode(
          _stored(
            _lease!,
            DateTime.fromMicrosecondsSinceEpoch(high, isUtc: true),
            left,
            device,
          ),
        ),
      );
    } else if (_lease?.accountId == accountId &&
        _anchor != null &&
        device == null) {
      // No new clock sample is temporary unavailability, not revocation.
      await _write(
        _key(accountId),
        jsonEncode({...record, 'last_seen_us': high}),
      );
    } else {
      await _write(
        _key(accountId),
        jsonEncode({'revision': record['revision'], 'last_seen_us': high}),
      );
    }
  });

  /// Remove grants on logout/revocation; retain the anti-replay high water.
  Future<void> clear({required String accountId}) => _serial(() async {
    if (_lease?.accountId == accountId) _drop();
    final record = await _record(accountId),
        now = _clock().toUtc().microsecondsSinceEpoch;
    await _write(
      _key(accountId),
      jsonEncode({
        'revision': record['revision'],
        'last_seen_us': now > record['last_seen_us']
            ? now
            : record['last_seen_us'],
      }),
    );
  });

  /// Confirmed remote account deletion removes its device-local personal record.
  Future<void> erase({required String accountId}) => _serial(() async {
    if (_lease?.accountId == accountId) _drop();
    final delete = _delete;
    if (delete == null)
      throw const OwnershipLeaseException('secure_delete_unavailable');
    await delete(_key(accountId));
  });
}
