library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:tideglass_events/tideglass_events.dart';

class ServiceException implements Exception {
  const ServiceException(this.code, {this.status, this.requestId});
  final String code;
  final int? status;
  final String? requestId;
  @override
  String toString() =>
      'ServiceException($code${status == null ? '' : ', $status'})';
}

/// Credentials never belong in a gameplay export, telemetry event, or log.
/// The caller must keep session tokens in platform secure storage. Recovery
/// codes are shown once and retained by the player; no automatic file storage.
class ServiceSession {
  ServiceSession({
    required this.accountId,
    required this.token,
    required this.expiresAt,
  });
  final String accountId, token;
  final DateTime expiresAt;
  factory ServiceSession.fromJson(Map<String, dynamic> json) => ServiceSession(
    accountId: json['account_id'] as String,
    token: json['session_token'] as String,
    expiresAt: DateTime.fromMillisecondsSinceEpoch(
      (json['expires_at'] as int) * 1000,
      isUtc: true,
    ),
  );
  @override
  String toString() => 'ServiceSession(redacted)';
}

class AccountCreated {
  AccountCreated(this.session, this.recoveryCode);
  final ServiceSession session;
  final String recoveryCode;
  @override
  String toString() => 'AccountCreated(redacted)';
}

class CloudSnapshotInfo {
  CloudSnapshotInfo.fromJson(Map<String, dynamic> json)
    : saveId = json['save_id'] as String,
      branchId = json['branch_id'] as String,
      revision = json['revision'] as int,
      parentId = json['parent_id'] as String?,
      settledThrough = DateTime.parse(json['settled'] as String),
      digest = json['digest'] as String,
      isTip = json['is_tip'] as bool;
  final String saveId, branchId, digest;
  final String? parentId;
  final int revision;
  final DateTime settledThrough;
  final bool isTip;
}

class CloudIndex {
  CloudIndex.fromJson(Map<String, dynamic> json)
    : generation = json['generation'] as int,
      selectedSaveId = json['selected_save_id'] as String?,
      selectionRequired = json['selection_required'] == true,
      duplicate = json['duplicate'] == true,
      snapshots = (json['snapshots'] as List)
          .map(
            (e) =>
                CloudSnapshotInfo.fromJson((e as Map).cast<String, dynamic>()),
          )
          .toList(growable: false);
  final int generation;
  final String? selectedSaveId;
  final bool selectionRequired, duplicate;
  final List<CloudSnapshotInfo> snapshots;
}

/// No automatic sync, login, analytics or economic mutation. An unavailable
/// optional service leaves local play and its saved branch entirely untouched.
class TideglassServiceClient {
  TideglassServiceClient({
    required this.endpoint,
    this.allowLocalDevelopment = false,
    HttpClient? httpClient,
    this.timeout = const Duration(seconds: 15),
  }) : _http = httpClient ?? HttpClient() {
    final local = {'localhost', '127.0.0.1', '::1'}.contains(endpoint.host);
    if (!endpoint.hasAuthority ||
        endpoint.host.isEmpty ||
        endpoint.userInfo.isNotEmpty ||
        endpoint.hasQuery ||
        endpoint.hasFragment ||
        (endpoint.path.isNotEmpty && endpoint.path != '/') ||
        !(endpoint.scheme == 'https' ||
            (allowLocalDevelopment && local && endpoint.scheme == 'http'))) {
      throw ArgumentError(
        'Use an HTTPS service origin or explicit loopback development endpoint.',
      );
    }
  }
  final Uri endpoint;
  final bool allowLocalDevelopment;
  final Duration timeout;
  final HttpClient _http;
  ServiceSession? session;

  Future<Map<String, dynamic>> _request(
    String method,
    String path, [
    Map<String, dynamic>? body,
    bool authenticated = true,
  ]) async {
    if (authenticated && session == null)
      throw const ServiceException('authentication_required');
    HttpClientRequest? request;
    try {
      request = await _http
          .openUrl(method, endpoint.resolve(path))
          .timeout(timeout);
      request.followRedirects =
          false; // Never forward a bearer token to a redirect.
      if (authenticated)
        request.headers.set(
          HttpHeaders.authorizationHeader,
          'Bearer ${session!.token}',
        );
      if (body != null) {
        request.headers.contentType = ContentType.json;
        final encodedBody = utf8.encode(jsonEncode(body));
        request.contentLength = encodedBody.length;
        request.add(encodedBody);
      }
      final response = await request.close().timeout(timeout);
      final bytes = <int>[];
      await for (final chunk in response.timeout(timeout)) {
        bytes.addAll(chunk);
        // Account exports may contain the 64 MiB cloud quota. Ordinary calls
        // are bounded far below this; a hostile server still cannot grow forever.
        if (bytes.length > 70 * 1024 * 1024) {
          throw const ServiceException('response_too_large');
        }
      }
      final decoded = (jsonDecode(utf8.decode(bytes)) as Map)
          .cast<String, dynamic>();
      if (response.statusCode >= 300) {
        throw ServiceException(
          decoded['error'] as String? ?? 'service_error',
          status: response.statusCode,
          requestId: decoded['request_id'] as String?,
        );
      }
      return decoded;
    } on ServiceException {
      rethrow;
    } on TimeoutException {
      request?.abort();
      throw const ServiceException('service_timeout');
    } on SocketException {
      throw const ServiceException('service_unavailable');
    } on HandshakeException {
      throw const ServiceException('service_tls_failure');
    } on FormatException {
      throw const ServiceException('invalid_service_response');
    }
  }

  Future<AccountCreated> createAccount({required bool cloudConsent}) async {
    final result = await _request('POST', '/v1/accounts', {
      'consent_cloud': cloudConsent,
    }, false);
    session = ServiceSession.fromJson(result);
    return AccountCreated(session!, result['recovery_code'] as String);
  }

  Future<ServiceSession> recoverAccount({
    required String accountId,
    required String recoveryCode,
  }) async {
    final result = await _request('POST', '/v1/sessions', {
      'account_id': accountId,
      'recovery_code': recoveryCode,
    }, false);
    session = ServiceSession.fromJson(result);
    return session!;
  }

  /// Retain the new code before calling: it remains usable if the response is lost.
  Future<AccountCreated> rotateRecoveryCode(
    String currentCode, {
    required String newRecoveryCode,
  }) async {
    final result = await _request('POST', '/v1/account/recovery-code', {
      'recovery_code': currentCode,
      'new_recovery_code': newRecoveryCode,
    });
    session = ServiceSession.fromJson(result);
    return AccountCreated(session!, result['recovery_code'] as String);
  }

  Future<void> signOut({bool allDevices = false}) async {
    await _request('POST', '/v1/sessions/revoke', {'all_devices': allDevices});
    session = null;
  }

  /// Forget this device credential during an outage; does not assert server revocation.
  void forgetSession() => session = null;
  Future<void> deleteAccount({
    required String recoveryCode,
    required bool confirmDelete,
  }) async {
    await _request('DELETE', '/v1/account', {
      'recovery_code': recoveryCode,
      'confirm_delete': confirmDelete,
    });
    session = null;
  }

  Future<Map<String, dynamic>> exportAccount() =>
      _request('GET', '/v1/account/export');
  Future<CloudIndex> cloudIndex() async =>
      CloudIndex.fromJson(await _request('GET', '/v1/cloud'));
  Future<CloudIndex> uploadSnapshot(
    String exportedSave, {
    required int expectedGeneration,
  }) async => CloudIndex.fromJson(
    await _request('POST', '/v1/cloud/snapshots', {
      'export_json': exportedSave,
      'expected_generation': expectedGeneration,
    }),
  );
  Future<String> downloadSnapshot(String saveId) async {
    _uuid(saveId);
    return (await _request('GET', '/v1/cloud/snapshots/$saveId'))['export_json']
        as String;
  }

  Future<CloudIndex> selectSnapshot(
    String saveId, {
    required int expectedGeneration,
    required bool confirmSelection,
  }) async {
    _uuid(saveId);
    return CloudIndex.fromJson(
      await _request('POST', '/v1/cloud/select', {
        'save_id': saveId,
        'expected_generation': expectedGeneration,
        'confirm_selection': confirmSelection,
      }),
    );
  }

  Future<Map<String, dynamic>> entitlements() =>
      _request('GET', '/v1/entitlements');
  Future<Map<String, dynamic>> verifyPurchase({
    required String platform,
    required String proof,
  }) => _request('POST', '/v1/purchases/verify', {
    'platform': platform,
    'proof': proof,
  });
  Future<Map<String, dynamic>> claimSupport({
    required int dayId,
    required int slot,
    required String route,
    String? proof,
  }) => _request('POST', '/v1/support/claims', {
    'day_id': dayId,
    'slot': slot,
    'route': route,
    if (proof != null) 'proof': proof,
  });
  Future<Map<String, dynamic>> supportClaims() =>
      _request('GET', '/v1/support/claims');
  Future<void> acknowledgeSupport({
    required String receiptId,
    required String saveId,
  }) async => _request('POST', '/v1/support/acknowledge', {
    'receipt_id': receiptId,
    'save_id': saveId,
  });
  Future<int> setTelemetryConsent(bool enabled) async =>
      (await _request('PUT', '/v1/telemetry/consent', {
            'enabled': enabled,
          }))['revision']
          as int;
  Future<Map<String, dynamic>> sendTelemetry({
    required int consentRevision,
    required List<Map<String, dynamic>> events,
  }) => _request('POST', '/v1/telemetry/events', {
    'consent_revision': consentRevision,
    'events': events,
  });
  Future<Map<String, dynamic>> features() => _request('GET', '/v1/features');
  static String generateRecoveryCode() => base64Url
      .encode(List.generate(32, (_) => Random.secure().nextInt(256)))
      .replaceAll('=', '');
  void close() => _http.close(force: true);
  static void _uuid(String value) {
    if (!RegExp(
      r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
    ).hasMatch(value))
      throw ArgumentError('Invalid save identity.');
  }
}

/// Every call rechecks current server ownership. An outage returns no paid
/// ownership; a persisted cosmetic/pass boolean can never satisfy this reader.
/// Account binding must be provided by the integration owner from the linked
/// local account seed, never from a user-editable entitlement cache.
class ServicePassEntitlementReader implements VerifiedPassEntitlementReader {
  ServicePassEntitlementReader(this.client, {required this.localAccountId});
  final TideglassServiceClient client;
  final String localAccountId;
  @override
  Future<VerifiedPassEntitlement?> read({
    required String accountId,
    required String passId,
  }) async {
    if (accountId != localAccountId || client.session == null) return null;
    try {
      final data = await client.entitlements();
      if (data['account_id'] != client.session!.accountId ||
          data['linked_account_seed'] != localAccountId)
        return null;
      for (final row in data['entitlements'] as List) {
        if (row['id'] == passId)
          return VerifiedPassEntitlement(
            accountId: accountId,
            passId: passId,
            verificationReceiptId: row['verification_receipt_id'] as String,
            authority: row['authority'] as String,
          );
      }
    } on ServiceException {
      return null;
    }
    return null;
  }
}

/// Consent is separate from cloud opt-in. This bounded in-memory queue makes no
/// background network calls and never writes events into a gameplay save. The
/// host explicitly flushes; retries retain event IDs for server deduplication.
/// Events are lost on process exit, and droppedEventCount exposes that limit.
class ConsentTelemetryBuffer {
  ConsentTelemetryBuffer(
    this.client, {
    required this.platform,
    required this.build,
    required this.deviceClass,
    this.capacity = 256,
    DateTime Function()? clock,
  }) : _clock = clock ?? DateTime.now {
    if (capacity < 1 ||
        capacity > 1000 ||
        !{'ios', 'android', 'macos', 'test'}.contains(platform)) {
      throw ArgumentError('Unsupported telemetry configuration.');
    }
  }
  final TideglassServiceClient client;
  final String platform, build, deviceClass;
  final int capacity;
  final DateTime Function() _clock;
  final List<Map<String, dynamic>> _events = [];
  bool enabled = false;
  bool pendingRemoteOptOut = false;
  int? _consentRevision;
  int droppedEventCount = 0;
  bool _flushing = false;
  int get pendingEventCount => _events.length;

  Future<void> optIn() async {
    final revision = await client.setTelemetryConsent(true);
    _consentRevision = revision;
    pendingRemoteOptOut = false;
    enabled = true;
  }

  /// Local collection stops immediately, even when remote deletion is offline.
  Future<void> optOut() async {
    enabled = false;
    _events.clear();
    _consentRevision = null;
    pendingRemoteOptOut = true;
    await client.setTelemetryConsent(false);
    pendingRemoteOptOut = false;
  }

  String newSessionId() => _uuidV4();
  void record(
    String name, {
    required String sessionId,
    Map<String, dynamic> properties = const {},
  }) {
    if (!enabled) return;
    const names = {
      'session_start',
      'session_end',
      'session_crash',
      'resume_result',
      'save_result',
      'rechart',
      'chapter_complete',
      'dossier_complete',
      'contract_claim',
      'service_result',
    };
    const allowed = {
      'flow',
      'outcome',
      'chapter',
      'duration_seconds',
      'schema_version',
    };
    if (!names.contains(name) || !properties.keys.every(allowed.contains)) {
      throw ArgumentError(
        'Telemetry only accepts defined event names and fields.',
      );
    }
    TideglassServiceClient._uuid(sessionId);
    _prune();
    if (_events.length == capacity) {
      _events.removeAt(0);
      droppedEventCount++;
    }
    _events.add({
      'id': _uuidV4(),
      'session_id': sessionId,
      'name': name,
      'observed_at': _clock().toUtc().millisecondsSinceEpoch ~/ 1000,
      'properties': {
        'platform': platform,
        'build': build,
        'device_class': deviceClass,
        ...properties,
      },
    });
  }

  Future<void> flush() async {
    if (_flushing) return;
    _flushing = true;
    try {
      if (pendingRemoteOptOut) {
        await client.setTelemetryConsent(false);
        pendingRemoteOptOut = false;
      }
      if (!enabled || _consentRevision == null) return;
      _prune();
      while (enabled && _events.isNotEmpty) {
        final batch = _events.take(100).toList(growable: false);
        try {
          await client.sendTelemetry(
            consentRevision: _consentRevision!,
            events: batch,
          );
        } on ServiceException catch (error) {
          if (error.status == 403 || error.code == 'consent_revision_changed') {
            enabled = false;
            _consentRevision = null;
            _events.clear();
          }
          rethrow;
        }
        final acknowledged = batch.map((event) => event['id']).toSet();
        _events.removeWhere((event) => acknowledged.contains(event['id']));
      }
    } finally {
      _flushing = false;
    }
  }

  void _prune() {
    final threshold =
        _clock().toUtc().millisecondsSinceEpoch ~/ 1000 - 7 * 86400;
    final before = _events.length;
    _events.removeWhere((event) => (event['observed_at'] as int) < threshold);
    droppedEventCount += before - _events.length;
  }

  static String _uuidV4() {
    final random = Random.secure();
    final bytes = List.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    final hex = bytes
        .map((value) => value.toRadixString(16).padLeft(2, '0'))
        .join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }
}
