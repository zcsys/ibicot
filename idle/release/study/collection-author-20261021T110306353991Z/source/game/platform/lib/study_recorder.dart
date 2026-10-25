/// Separate, explicitly enrolled study collection. Never operational telemetry.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:crypto/crypto.dart';

String studyCanonical(Object? value) {
  Object? ordered(Object? item) {
    if (item is Map) {
      final keys = item.keys.cast<String>().toList()..sort();
      return {for (final key in keys) key: ordered(item[key])};
    }
    if (item is List) return item.map(ordered).toList();
    return item;
  }

  return jsonEncode(ordered(value));
}

String studyDigest(String value) =>
    sha256.convert(utf8.encode(value)).toString();
String _id() {
  final random = Random.secure();
  return List.generate(
    16,
    (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0'),
  ).join();
}

void _require(bool value, String code) {
  if (!value) throw StudyException(code);
}

final _hash = RegExp(r'^[a-f0-9]{64}$');
final _opaque = RegExp(r'^[a-f0-9]{32}$');
final _code = RegExp(r'^[A-Za-z0-9_-]{1,80}$');

class StudyException implements Exception {
  const StudyException(this.code);
  final String code;
  @override
  String toString() => 'StudyException($code)';
}

class StudyConfig {
  StudyConfig({
    required this.candidateSha256,
    required this.economySha256,
    required this.contentSha256,
    required this.config,
  }) {
    _require(
      [candidateSha256, economySha256, contentSha256].every(_hash.hasMatch) &&
          _code.hasMatch(config),
      'invalid_config',
    );
  }
  final String candidateSha256, economySha256, contentSha256, config;
  Map<String, Object?> toJson() => {
    'candidate_sha256': candidateSha256,
    'economy_sha256': economySha256,
    'content_sha256': contentSha256,
    'config': config,
  };
}

class StudyEnrollment {
  StudyEnrollment({
    required this.studyId,
    required this.protocolSha256,
    required this.informationSha256,
    required this.consentVersion,
    required this.eligibilityEvidenceSha256,
    required this.synthetic,
    required this.platform,
    required this.deviceGroup,
    required this.acquisition,
  }) {
    _require(
      _code.hasMatch(studyId) &&
          _code.hasMatch(consentVersion) &&
          [
            protocolSha256,
            informationSha256,
            eligibilityEvidenceSha256,
          ].every(_hash.hasMatch),
      'invalid_enrollment',
    );
    _require(
      {'ios', 'android', 'test'}.contains(platform) &&
          (synthetic || platform != 'test'),
      'invalid_platform',
    );
    _require(
      {
        'phone_compact',
        'phone_large',
        'tablet',
        'unclassified',
      }.contains(deviceGroup),
      'invalid_device_group',
    );
    _require(
      {'moderated', 'panel', 'organic', 'internal_test'}.contains(acquisition),
      'invalid_acquisition',
    );
    _require(
      synthetic || acquisition != 'internal_test',
      'test_acquisition_in_real_study',
    );
  }
  final String studyId,
      protocolSha256,
      informationSha256,
      consentVersion,
      eligibilityEvidenceSha256,
      platform,
      deviceGroup,
      acquisition;
  final bool synthetic;
}

enum StudyActivity {
  interaction,
  purchase,
  rechart,
  navigation,
  calibration,
  contract,
  help,
}

enum StudyGapReason {
  storageFailure,
  clockDiscontinuity,
  instrumentationUnavailable,
  capacity,
}

enum StudyTerminal { explicitlyObservedCleanExit }

/// CAS must be durable and atomic. Returning false must preserve old contents.
/// A single recorder serializes calls; CAS rejects stale parallel writers.
abstract interface class StudyStore {
  Future<String?> read();
  Future<bool> compareAndSwap(String? expectedSha256, String next);
}

/// App-private directory required. No file/directory is created by read().
/// Canonical payload is flushed in a unique temporary directory then renamed.
/// Detected symlinks and oversized files fail closed. This is not native
/// anti-tamper, cross-device identity, or a substitute for sandbox qualification.
class AtomicStudyFileStore implements StudyStore {
  AtomicStudyFileStore(this.path, {this.maximumBytes = 2 * 1024 * 1024});
  final String path;
  final int maximumBytes;
  Future<void> _regular(String name, {bool missingAllowed = true}) async {
    final type = await FileSystemEntity.type(name, followLinks: false);
    _require(
      type == FileSystemEntityType.file ||
          (missingAllowed && type == FileSystemEntityType.notFound),
      'unsafe_store_path',
    );
  }

  @override
  Future<String?> read() async {
    await _regular(path);
    if (!await File(path).exists()) return null;
    final file = await File(path).open(mode: FileMode.read);
    try {
      _require(await file.length() <= maximumBytes, 'store_oversize');
      final bytes = await file.read(maximumBytes + 1);
      _require(bytes.length <= maximumBytes, 'store_oversize');
      return utf8.decode(bytes);
    } on StudyException {
      rethrow;
    } catch (_) {
      throw const StudyException('store_read_failed');
    } finally {
      await file.close();
    }
  }

  @override
  Future<bool> compareAndSwap(String? expectedSha256, String next) async {
    _require(utf8.encode(next).length <= maximumBytes, 'store_oversize');
    final parent = File(path).parent;
    _require(
      await FileSystemEntity.type(parent.path, followLinks: false) ==
          FileSystemEntityType.directory,
      'unsafe_store_directory',
    );
    final lockPath = '$path.lock';
    await _regular(lockPath);
    final lock = await File(lockPath).open(mode: FileMode.append);
    Directory? temporary;
    try {
      await lock.lock(FileLock.blockingExclusive);
      final current = await read();
      if ((current == null ? null : studyDigest(current)) != expectedSha256)
        return false;
      temporary = await parent.createTemp('.tideglass-study-');
      final pending = File('${temporary.path}/pending');
      await pending.writeAsString(next, flush: true);
      await _regular(path);
      await pending.rename(path);
      return true;
    } on StudyException {
      rethrow;
    } catch (_) {
      throw const StudyException('store_write_failed');
    } finally {
      if (temporary != null && await temporary.exists())
        await temporary.delete(recursive: true);
      await lock.close();
    }
  }
}

class StudyRecorder {
  StudyRecorder._(
    this.store,
    this.clock,
    this.idGenerator,
    this.maximumRecords,
    this.maximumBytes,
    this._document,
    this._storedHash,
  );
  final StudyStore store;
  final DateTime Function() clock;
  final String Function() idGenerator;
  final int maximumRecords, maximumBytes;
  Map<String, dynamic>? _document;
  String? _storedHash;
  Future<void> _queue = Future.value();
  bool _begun = false, _foreground = true, _interactive = false;
  String? _process, _session;
  int? _lastActivity, _lastAt;
  StudyConfig? _config;
  bool _writeFailed = false;
  final Set<String> _usedIds = {};
  bool get enrolled => _document?['registry'] != null && !withdrawn;
  bool get withdrawn => _document?['status'] == 'withdrawn';
  bool get exhausted => _document?['status'] == 'exhausted';
  bool get hasPendingStorageGap => _writeFailed;
  String? get installId =>
      (_document?['registry'] as Map?)?['install_id'] as String?;
  String? get sessionId => _session;
  String? get processId => _process;
  Map<String, dynamic>? get registry => _document?['registry'] == null
      ? null
      : jsonDecode(jsonEncode(_document!['registry'])) as Map<String, dynamic>;
  String? exportRaw() => _document == null ? null : studyCanonical(_document);

  static Future<StudyRecorder> open(
    StudyStore store, {
    DateTime Function()? clock,
    String Function()? idGenerator,
    int maximumRecords = 4096,
    int maximumBytes = 2 * 1024 * 1024,
  }) async {
    _require(
      maximumRecords >= 8 &&
          maximumRecords <= 100000 &&
          maximumBytes >= 32768 &&
          maximumBytes <= 32 * 1024 * 1024,
      'invalid_bounds',
    );
    final text = await store.read();
    Map<String, dynamic>? doc;
    if (text != null) {
      _require(utf8.encode(text).length <= maximumBytes, 'store_oversize');
      try {
        doc = jsonDecode(text) as Map<String, dynamic>;
        _require(
          studyCanonical(doc) == text,
          'noncanonical_or_duplicate_store',
        );
        _validate(doc, maximumRecords);
      } on StudyException {
        rethrow;
      } catch (_) {
        throw const StudyException('invalid_store');
      }
    }
    final result = StudyRecorder._(
      store,
      clock ?? DateTime.now,
      idGenerator ?? _id,
      maximumRecords,
      maximumBytes,
      doc,
      text == null ? null : studyDigest(text),
    );
    final records = doc?['records'] as List?;
    if (records != null && records.isNotEmpty) {
      result._lastAt = records.last['at'] as int;
      result._process = records.last['process_id'] as String;
      result._session = records.last['session_id'] as String;
      result._usedIds.add(doc!['registry']['install_id'] as String);
      for (final event in records) {
        result._usedIds.addAll([
          event['event_id'] as String,
          event['process_id'] as String,
          event['session_id'] as String,
        ]);
      }
    }
    return result;
  }

  static bool _shape(Map value, Set<String> fields) =>
      value.length == fields.length && value.keys.toSet().containsAll(fields);
  static bool _time(Object? value) =>
      value is int && value >= 0 && value < 9007199254740992;
  static void _configShape(Object? raw) {
    if (raw == null) return;
    final value = raw as Map<String, dynamic>;
    _require(
      _shape(value, {
        'candidate_sha256',
        'economy_sha256',
        'content_sha256',
        'config',
      }),
      'invalid_config_fields',
    );
    StudyConfig(
      candidateSha256: value['candidate_sha256'] as String,
      economySha256: value['economy_sha256'] as String,
      contentSha256: value['content_sha256'] as String,
      config: value['config'] as String,
    );
  }

  static void _registryShape(Map<String, dynamic> value) {
    _require(
      _shape(value, {
        'study_id',
        'install_id',
        'enrolled_at',
        'first_launch',
        'protocol_sha256',
        'information_sha256',
        'consent_version',
        'eligibility_evidence_sha256',
        'synthetic',
        'platform',
        'device_group',
        'acquisition',
        'baseline',
      }),
      'invalid_registry_fields',
    );
    _require(
      _opaque.hasMatch(value['install_id'] as String) &&
          _time(value['enrolled_at']) &&
          value['first_launch'] == value['enrolled_at'] &&
          value['baseline'] != null,
      'invalid_registry',
    );
    _configShape(value['baseline']);
    StudyEnrollment(
      studyId: value['study_id'] as String,
      protocolSha256: value['protocol_sha256'] as String,
      informationSha256: value['information_sha256'] as String,
      consentVersion: value['consent_version'] as String,
      eligibilityEvidenceSha256: value['eligibility_evidence_sha256'] as String,
      synthetic: value['synthetic'] as bool,
      platform: value['platform'] as String,
      deviceGroup: value['device_group'] as String,
      acquisition: value['acquisition'] as String,
    );
  }

  static void _payloadShape(Map<String, dynamic> event) {
    final payload = event['payload'] as Map<String, dynamic>;
    switch (event['kind']) {
      case 'app_start':
      case 'session_start':
        _require(
          _shape(payload, {'config', 'reason'}),
          'invalid_start_payload',
        );
        _configShape(payload['config']);
        _require(
          event['kind'] == 'session_start'
              ? payload['reason'] == 'inactivity'
              : {'enrollment', 'process_restart'}.contains(payload['reason']),
          'invalid_start_reason',
        );
      case 'foreground':
      case 'background':
      case 'harbor_interactive':
        _require(payload.isEmpty, 'invalid_empty_payload');
      case 'activity':
        _require(
          _shape(payload, {'activity'}) &&
              StudyActivity.values.any((v) => v.name == payload['activity']),
          'invalid_activity',
        );
      case 'gap':
        _require(
          _shape(payload, {'reason', 'from', 'to'}) &&
              (StudyGapReason.values.any((v) => v.name == payload['reason']) ||
                  payload['reason'] == 'withdrawalErasure') &&
              _time(payload['from']) &&
              (payload['to'] == null ||
                  (_time(payload['to']) &&
                      (payload['to'] as int) >= (payload['from'] as int))),
          'invalid_gap',
        );
      case 'terminal':
        _require(
          _shape(payload, {'reason'}) &&
              payload['reason'] == 'explicitlyObservedCleanExit',
          'invalid_terminal',
        );
      case 'withdrawal':
        _require(
          _shape(payload, {'retained_registry_policy'}) &&
              payload['retained_registry_policy'] == true,
          'invalid_withdrawal',
        );
      default:
        throw const StudyException('unknown_record_kind');
    }
  }

  static void _validate(Map<String, dynamic> doc, int bound) {
    _require(
      doc.keys.toSet().length == 4 &&
          doc.keys.toSet().containsAll({
            'schema_version',
            'registry',
            'records',
            'status',
          }) &&
          doc['schema_version'] == 1,
      'invalid_store_fields',
    );
    _require(
      {'active', 'exhausted', 'withdrawn'}.contains(doc['status']) &&
          doc['records'] is List &&
          (doc['records'] as List).length <= bound,
      'invalid_store_status',
    );
    if (doc['registry'] == null) {
      _require(
        doc['status'] == 'withdrawn' && (doc['records'] as List).isEmpty,
        'invalid_erased_store',
      );
      return;
    }
    final registry = doc['registry'] as Map<String, dynamic>;
    _registryShape(registry);
    var previous = studyDigest(studyCanonical(registry));
    var sequence = 0;
    var lastAt = -1;
    final events = <String>{};
    for (final raw in doc['records'] as List) {
      final event = Map<String, dynamic>.from(raw as Map);
      // Nine exact fields; keeping shape validation separate avoids accepting
      // hidden account/contact fields even if their hash was recomputed.
      _require(
        event.length == 9 &&
            event.keys.toSet().containsAll({
              'seq',
              'event_id',
              'at',
              'process_id',
              'session_id',
              'kind',
              'payload',
              'previous_sha256',
              'sha256',
            }),
        'invalid_record_fields',
      );
      _payloadShape(event);
      _require(
        _opaque.hasMatch(event['process_id'] as String) &&
            _opaque.hasMatch(event['session_id'] as String) &&
            events.add(event['event_id'] as String),
        'invalid_or_duplicate_record_identity',
      );
      final hash = event.remove('sha256');
      _require(
        event['seq'] == sequence++ &&
            event['previous_sha256'] == previous &&
            hash == studyDigest(studyCanonical(event)) &&
            _opaque.hasMatch(event['event_id'] as String) &&
            _time(event['at']) &&
            (event['at'] as int) >= lastAt,
        'broken_record_chain',
      );
      previous = hash as String;
      lastAt = event['at'] as int;
    }
    _require(
      (doc['records'] as List).isNotEmpty &&
          doc['records'][0]['kind'] == 'app_start' &&
          doc['records'][0]['at'] == registry['first_launch'],
      'missing_earliest_start',
    );
    final records = doc['records'] as List;
    _require(
      (doc['status'] == 'withdrawn') == (records.last['kind'] == 'withdrawal'),
      'inconsistent_withdrawal_status',
    );
    if (doc['status'] == 'exhausted') {
      _require(
        records.last['kind'] == 'gap' && records.last['payload']['to'] == null,
        'exhaustion_without_gap',
      );
    }
    _require(
      studyCanonical(records.first['payload']['config']) ==
          studyCanonical(registry['baseline']),
      'initial_config_mismatch',
    );
  }

  Future<T> _serial<T>(Future<T> Function() operation) {
    final completer = Completer<T>();
    _queue = _queue.then((_) async {
      try {
        completer.complete(await operation());
      } catch (error, stack) {
        completer.completeError(error, stack);
      }
    });
    return completer.future;
  }

  int _now() => clock().toUtc().millisecondsSinceEpoch ~/ 1000;
  String _newId() {
    final value = idGenerator();
    _require(
      _opaque.hasMatch(value) && _usedIds.add(value),
      'invalid_generated_id',
    );
    return value;
  }

  Map<String, dynamic> _copy() =>
      jsonDecode(studyCanonical(_document)) as Map<String, dynamic>;
  void _append(
    Map<String, dynamic> doc,
    String kind,
    Map<String, Object?> payload,
    int at,
  ) {
    final records = doc['records'] as List;
    final event = <String, Object?>{
      'seq': records.length,
      'event_id': _newId(),
      'at': at,
      'process_id': _process,
      'session_id': _session,
      'kind': kind,
      'payload': payload,
      'previous_sha256': records.isEmpty
          ? studyDigest(studyCanonical(doc['registry']))
          : records.last['sha256'],
    };
    event['sha256'] = studyDigest(studyCanonical(event));
    records.add(event);
  }

  Future<void> _commit(Map<String, dynamic> doc) async {
    final encoded = studyCanonical(doc);
    _require(utf8.encode(encoded).length <= maximumBytes, 'store_oversize');
    try {
      _require(
        await store.compareAndSwap(_storedHash, encoded),
        'stale_store_writer',
      );
      _document = doc;
      _storedHash = studyDigest(encoded);
      final records = doc['records'] as List;
      if (records.isNotEmpty) _lastAt = records.last['at'] as int;
    } catch (_) {
      _writeFailed = true;
      rethrow;
    }
  }

  /// Caller must have separately checked fresh install/no ordinary save before
  /// bootstrap. The evidence hash is audited independently; this local guard
  /// alone cannot establish study eligibility or authorise live recruitment.
  Future<void> enroll(
    StudyEnrollment enrollment,
    StudyConfig baseline, {
    required bool eligibleFreshInstall,
  }) => _serial(() async {
    _require(
      _document == null && eligibleFreshInstall,
      'enrollment_not_allowed',
    );
    final now = _now();
    _require(now >= 0, 'invalid_clock');
    _process = _newId();
    _session = _newId();
    _config = baseline;
    final registry = <String, Object?>{
      'study_id': enrollment.studyId,
      'install_id': _newId(),
      'enrolled_at': now,
      'first_launch': now,
      'protocol_sha256': enrollment.protocolSha256,
      'information_sha256': enrollment.informationSha256,
      'consent_version': enrollment.consentVersion,
      'eligibility_evidence_sha256': enrollment.eligibilityEvidenceSha256,
      'synthetic': enrollment.synthetic,
      'platform': enrollment.platform,
      'device_group': enrollment.deviceGroup,
      'acquisition': enrollment.acquisition,
      'baseline': baseline.toJson(),
    };
    final doc = <String, dynamic>{
      'schema_version': 1,
      'registry': registry,
      'records': <Map<String, Object?>>[],
      'status': 'active',
    };
    _append(doc, 'app_start', {
      'config': baseline.toJson(),
      'reason': 'enrollment',
    }, now);
    await _commit(doc);
    _begun = true;
    _foreground = true;
    _lastActivity = now;
  });

  Future<void> beginProcess({required StudyConfig? config}) =>
      _serial(() async {
        if (!enrolled || exhausted || _begun) return;
        _process = _newId();
        _session = _newId();
        _config = config;
        _foreground = true;
        _interactive = false;
        await _record('app_start', {
          'config': config?.toJson(),
          'reason': 'process_restart',
        }, split: false);
        _begun = true;
        _lastActivity = _now();
      });

  Future<void> _record(
    String kind,
    Map<String, Object?> payload, {
    bool split = true,
  }) async {
    if (!enrolled || exhausted) return;
    final now = _now();
    if (_lastAt != null && now < _lastAt!) {
      final doc = _copy();
      _append(doc, 'gap', {
        'reason': 'clockDiscontinuity',
        'from': now,
        'to': null,
      }, _lastAt!);
      doc['status'] = 'exhausted';
      await _commit(doc);
      throw const StudyException('clock_discontinuity');
    }
    final doc = _copy();
    if (_writeFailed) {
      _append(doc, 'gap', {
        'reason': 'storageFailure',
        'from': _lastAt ?? now,
        'to': now,
      }, now);
    }
    final startsSession =
        split && _lastActivity != null && now - _lastActivity! >= 1800;
    if (startsSession) {
      _session = _newId();
      _interactive = false;
      _append(doc, 'session_start', {
        'config': _config?.toJson(),
        'reason': 'inactivity',
      }, now);
    }
    _append(doc, kind, payload, now);
    if ((doc['records'] as List).length > maximumRecords - 2 ||
        utf8.encode(studyCanonical(doc)).length > maximumBytes - 8192) {
      final stopped = _copy();
      _append(stopped, 'gap', {
        'reason': 'capacity',
        'from': _lastAt ?? now,
        'to': null,
      }, now);
      stopped['status'] = 'exhausted';
      await _commit(stopped);
      return;
    }
    await _commit(doc);
    _writeFailed = false;
    if (startsSession) _lastActivity = now;
  }

  Future<void> foreground() => _serial(() async {
    if (!_begun || !enrolled || exhausted) return;
    await _record('foreground', {});
    _foreground = true;
  });
  Future<void> background() => _serial(() async {
    if (!_begun || !enrolled || exhausted || !_foreground) return;
    await _record('background', {}, split: false);
    _foreground = false;
  });
  Future<void> interactiveHarbor() => _serial(() async {
    if (!_begun || !_foreground || !enrolled || exhausted || _interactive)
      return;
    await _record('harbor_interactive', {});
    _interactive = true;
    _lastActivity = _now();
  });
  Future<void> activity(StudyActivity activity) => _serial(() async {
    if (!_begun || !_foreground || !_interactive || !enrolled || exhausted)
      return;
    // A >=30 minute boundary requires a fresh interactive observation in the
    // newly started session; do not carry the old harbor proof into it.
    final idle = _lastActivity != null && _now() - _lastActivity! >= 1800;
    if (idle) {
      await _record('harbor_interactive', {});
      _interactive = true;
    }
    await _record('activity', {'activity': activity.name}, split: !idle);
    _lastActivity = _now();
  });
  Future<void> noteGap(StudyGapReason reason) => _serial(() async {
    if (!_begun || !enrolled || exhausted) return;
    await _record('gap', {
      'reason': reason.name,
      'from': _lastAt ?? _now(),
      'to': _now(),
    }, split: false);
  });
  Future<void> terminal(StudyTerminal terminal) => _serial(() async {
    if (!_begun || !enrolled || exhausted) return;
    await _record('terminal', {'reason': terminal.name}, split: false);
    _begun = false;
  });

  /// Default withdrawal erases all local study identifiers/records and leaves a
  /// nonidentifying stop marker. Retaining a minimal registry requires explicit
  /// approved study policy; caller must not infer that permission from consent.
  Future<void> withdraw({bool retainMinimalRegistry = false}) =>
      _serial(() async {
        if (_document == null || withdrawn) return;
        if (!retainMinimalRegistry) {
          await _commit({
            'schema_version': 1,
            'registry': null,
            'records': [],
            'status': 'withdrawn',
          });
        } else {
          final doc = _copy();
          final first = (doc['records'] as List).first;
          doc['records'] = [first];
          _process = first['process_id'] as String;
          _session = first['session_id'] as String;
          _append(doc, 'gap', {
            'reason': 'withdrawalErasure',
            'from': first['at'],
            'to': null,
          }, max(_now(), _lastAt ?? 0));
          _append(doc, 'withdrawal', {
            'retained_registry_policy': true,
          }, max(_now(), _lastAt ?? 0));
          doc['status'] = 'withdrawn';
          await _commit(doc);
        }
        _begun = false;
        _foreground = false;
        _interactive = false;
      });
}
