library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:crypto/crypto.dart';

typedef PayloadValidator = void Function(Map<String, dynamic> payload);
typedef SnapshotValidator =
    void Function(Map<String, dynamic> payload, DateTime settledThrough);
typedef CommitProbe = Future<void> Function(CommitStage stage);

enum CommitStage { beforeWrite, afterFlush, afterRename }

class SaveException implements Exception {
  const SaveException(this.message);
  final String message;
  @override
  String toString() => '$runtimeType: $message';
}

class CorruptSaveException extends SaveException {
  const CorruptSaveException(super.message);
}

class IncompatibleSaveException extends SaveException {
  const IncompatibleSaveException(super.message);
}

class SaveConflictException extends SaveException {
  const SaveConflictException(super.message);
}

/// A decoded snapshot contains local progression, never trusted paid ownership.
class SaveSnapshot {
  SaveSnapshot._(Map<String, dynamic> envelope) : _envelope = _copy(envelope);
  final Map<String, dynamic> _envelope;
  Map<String, dynamic> get envelope => _copy(_envelope);
  Map<String, dynamic> get payload =>
      _copy((_envelope['gameplay_state'] as Map)['payload'] as Map);
  int get revision => _envelope['revision'] as int;
  String get saveId => _envelope['save_id'] as String;
  String get branchId => _envelope['branch_id'] as String;
  DateTime get settledThrough =>
      DateTime.parse(_envelope['settled_through_utc'] as String);
}

class LoadResult {
  const LoadResult({
    this.snapshot,
    this.recoveredFromBackup = false,
    this.issues = const [],
  });
  final SaveSnapshot? snapshot;
  final bool recoveredFromBackup;
  final List<String> issues;
}

/// Alternating committed snapshots keep a prior valid generation available.
/// Writes flush before atomic same-filesystem rename. This protects process
/// interruption; device power-loss durability still needs native-device tests.
class SaveRepository {
  SaveRepository(
    this.directory, {
    required this.economicVersion,
    required this.economicDigest,
    required this.validatePayload,
    this.validateSnapshot,
    DateTime Function()? now,
    this.commitProbe,
  }) : _now = now ?? DateTime.now {
    if (!RegExp(
          r'^tideglass-economy-\d+\.\d+\.\d+$',
        ).hasMatch(economicVersion) ||
        !RegExp(r'^[a-f0-9]{64}$').hasMatch(economicDigest)) {
      throw ArgumentError(
        'A version and SHA-256 economic configuration are required.',
      );
    }
  }

  final Directory directory;
  final String economicVersion;
  final String economicDigest;
  final PayloadValidator validatePayload;

  /// Cross-partition time checks run before any generation is committed or
  /// selected. A payload-only validator cannot compare a fleet with its cursor.
  final SnapshotValidator? validateSnapshot;
  final DateTime Function() _now;
  final CommitProbe? commitProbe;
  static const maxImportBytes = 2 * 1024 * 1024;
  static final Map<String, Future<void>> _locks = {};
  bool _loaded = false;
  int? _knownRevision;
  String? _knownSaveId;
  String? _knownBranchId;

  File _slot(int index) => File('${directory.path}/progress.$index.json');

  Future<T> _exclusive<T>(Future<T> Function() operation) async {
    final key = directory.absolute.path;
    final previous = _locks[key] ?? Future<void>.value();
    final completed = Completer<void>();
    _locks[key] = completed.future;
    await previous;
    RandomAccessFile? lock;
    try {
      await directory.create(recursive: true);
      lock = await File(
        '${directory.path}/writer.lock',
      ).open(mode: FileMode.append);
      await lock.lock(FileLock.exclusive);
      return await operation();
    } finally {
      try {
        if (lock != null) {
          try {
            await lock.unlock();
          } finally {
            await lock.close();
          }
        }
      } finally {
        completed.complete();
        if (identical(_locks[key], completed.future)) _locks.remove(key);
      }
    }
  }

  Future<LoadResult> load() => _exclusive(() async {
    final result = await _read();
    _remember(result.snapshot);
    return result;
  });

  void _remember(SaveSnapshot? snapshot) {
    _loaded = true;
    _knownRevision = snapshot?.revision;
    _knownSaveId = snapshot?.saveId;
    _knownBranchId = snapshot?.branchId;
  }

  Future<LoadResult> _read() async {
    final candidates = <SaveSnapshot>[];
    final issues = <String>[];
    var filesFound = 0;
    for (var i = 0; i < 2; i++) {
      final file = _slot(i);
      if (!await file.exists()) continue;
      filesFound++;
      try {
        candidates.add(_decode(await file.readAsString()));
      } on IncompatibleSaveException {
        // Do not silently roll back to an old compatible generation after an
        // update. The user must use the correct runtime/configuration.
        rethrow;
      } catch (error) {
        issues.add('Snapshot $i could not be loaded: $error');
      }
    }
    if (candidates.isEmpty && filesFound > 0) {
      throw CorruptSaveException(
        'No valid saved generation. Preserve files and import a recovery copy. ${issues.join(' ')}',
      );
    }
    candidates.sort((a, b) => b.revision.compareTo(a.revision));
    if (candidates.length == 2) {
      final current = candidates[0], previous = candidates[1];
      if (current.revision == previous.revision &&
          jsonEncode(current.envelope) != jsonEncode(previous.envelope)) {
        throw const SaveConflictException(
          'Conflicting saved progress requires explicit selection.',
        );
      }
      final parent = current.envelope['parent'] as Map?;
      if (current.revision != previous.revision &&
          (parent?['revision'] != previous.revision ||
              parent?['save_id'] != previous.saveId ||
              parent?['branch_id'] != previous.branchId)) {
        throw const SaveConflictException(
          'Snapshot lineage is not contiguous; preserve both branches.',
        );
      }
    }
    return LoadResult(
      snapshot: candidates.isEmpty ? null : candidates.first,
      recoveredFromBackup: candidates.isNotEmpty && issues.isNotEmpty,
      issues: List.unmodifiable(issues),
    );
  }

  Future<SaveSnapshot> save(
    Map<String, dynamic> payload, {
    required DateTime settledThrough,
  }) {
    final captured = _copy(payload);
    return _exclusive(() async {
      if (!_loaded) throw StateError('Load the repository before saving.');
      validatePayload(_copy(captured));
      validateSnapshot?.call(_copy(captured), settledThrough.toUtc());
      final previous = (await _read()).snapshot;
      _checkRevision(previous);
      if (previous != null &&
          settledThrough.isBefore(previous.settledThrough)) {
        throw const SaveConflictException(
          'A normal save cannot rewind settled time.',
        );
      }
      final envelope = _makeEnvelope(captured, settledThrough, previous);
      final saved = await _commit(envelope);
      _remember(saved);
      return saved;
    });
  }

  void _checkRevision(SaveSnapshot? current) {
    if (current?.revision != _knownRevision ||
        current?.saveId != _knownSaveId ||
        current?.branchId != _knownBranchId) {
      throw const SaveConflictException(
        'Another writer changed progress. Reload and choose the retained state.',
      );
    }
  }

  Map<String, dynamic> _makeEnvelope(
    Map<String, dynamic> payload,
    DateTime settled,
    SaveSnapshot? previous, {
    String? branchId,
    List<Map<String, dynamic>>? preserved,
  }) => {
    'format': 'tideglass-save-envelope',
    'schema_version': 1,
    'save_id': _uuid(),
    'branch_id': branchId ?? previous?.branchId ?? _uuid(),
    'revision': previous == null ? 0 : previous.revision + 1,
    'parent': previous == null
        ? null
        : {
            'save_id': previous.saveId,
            'branch_id': previous.branchId,
            'revision': previous.revision,
          },
    'written_at_utc': _utc(_now()),
    'settled_through_utc': _utc(settled),
    'economic_config': {'version': economicVersion, 'sha256': economicDigest},
    'gameplay_state': {'schema_version': 1, 'payload': _copy(payload)},
    'merge_policy': 'select_one_progression_branch',
    'preserved_branches':
        preserved ?? previous?.envelope['preserved_branches'] ?? [],
    'pending_operations': <Object>[],
    'applied_operation_ids': <String>[],
    'commerce_cache': {
      'trust': 'display_cache_only',
      'authority': 'independent_verifier_required',
      'snapshot_reference': null,
      'entries': <Object>[],
    },
  };

  Future<SaveSnapshot> _commit(Map<String, dynamic> envelope) async {
    final record = _encode(envelope);
    final index = (envelope['revision'] as int) % 2;
    final temporary = File('${directory.path}/progress.$index.pending');
    await commitProbe?.call(CommitStage.beforeWrite);
    await temporary.writeAsString(record, flush: true);
    await commitProbe?.call(CommitStage.afterFlush);
    await temporary.rename(_slot(index).path);
    await commitProbe?.call(CommitStage.afterRename);
    return SaveSnapshot._(envelope);
  }

  Future<String> exportSave() => _exclusive(() async {
    final snapshot = (await _read()).snapshot;
    if (snapshot == null)
      throw const SaveException('There is no saved game to export.');
    return _encode(snapshot.envelope);
  });

  /// Import is an explicit selection of progression, never a sum or a purchase
  /// restoration. The displaced local branch is saved before committing.
  Future<SaveSnapshot> importSave(
    String text, {
    bool recoverCorrupt = false,
  }) => _exclusive(() async {
    final imported = _decode(text);
    SaveSnapshot? current;
    var corrupted = false;
    try {
      current = (await _read()).snapshot;
      if (!_loaded) throw StateError('Load the repository before importing.');
      _checkRevision(current);
    } on CorruptSaveException {
      if (!recoverCorrupt) rethrow;
      corrupted = true;
      final recovery = Directory(
        '${directory.path}/recovery/corrupt-${_uuid()}',
      );
      await recovery.create(recursive: true);
      for (var i = 0; i < 2; i++) {
        final file = _slot(i);
        if (await file.exists())
          await file.copy('${recovery.path}/progress.$i.json');
      }
    }
    final preserved = <Map<String, dynamic>>[];
    if (current != null) {
      final archive = File(
        '${directory.path}/recovery/${current.branchId}-${current.revision}.json',
      );
      await archive.parent.create(recursive: true);
      await archive.writeAsString(_encode(current.envelope), flush: true);
      preserved.add({
        'save_id': current.saveId,
        'branch_id': current.branchId,
        'revision': current.revision,
        'recovery_reference':
            'recovery/${current.branchId}-${current.revision}.json',
      });
    }
    final envelope = _makeEnvelope(
      imported.payload,
      imported.settledThrough,
      current,
      branchId: _uuid(),
      preserved: preserved,
    );
    final saved = await _commit(envelope);
    if (corrupted && await _slot(1).exists()) {
      // The recovery copy is durable before the bad secondary generation is
      // removed; committed slot 0 now contains the explicitly selected import.
      await _slot(1).delete();
    }
    _remember(saved);
    return saved;
  });

  SaveSnapshot _decode(String text) {
    if (utf8.encode(text).length > maxImportBytes) {
      throw const CorruptSaveException(
        'Save exceeds the supported import size.',
      );
    }
    final decoded = jsonDecode(text);
    if (decoded is! Map ||
        decoded['format'] != 'tideglass-checksummed-save' ||
        decoded['envelope'] is! Map ||
        decoded['checksum'] is! String) {
      throw const CorruptSaveException('Invalid save container.');
    }
    final envelope = _copy(decoded['envelope'] as Map);
    if (decoded['checksum'] != _digest(envelope)) {
      throw const CorruptSaveException('Snapshot checksum mismatch.');
    }
    if (envelope['schema_version'] != 1 ||
        envelope['format'] != 'tideglass-save-envelope') {
      throw const IncompatibleSaveException(
        'Unsupported save format/version; no data was overwritten.',
      );
    }
    final config = envelope['economic_config'];
    if (config is! Map ||
        config['version'] != economicVersion ||
        config['sha256'] != economicDigest) {
      throw const IncompatibleSaveException(
        'Pinned economic configuration is unavailable; do not settle with different rules.',
      );
    }
    final revision = envelope['revision'];
    final parent = envelope['parent'];
    if (revision is! int ||
        revision < 0 ||
        !_isUuid(envelope['save_id']) ||
        !_isUuid(envelope['branch_id']) ||
        (revision == 0
            ? parent != null
            : (parent is! Map ||
                  parent['revision'] != revision - 1 ||
                  !_isUuid(parent['save_id']) ||
                  parent['save_id'] == envelope['save_id'] ||
                  !_isUuid(parent['branch_id'])))) {
      throw const CorruptSaveException(
        'Invalid snapshot identity or revision lineage.',
      );
    }
    for (final key in ['written_at_utc', 'settled_through_utc']) {
      final value = envelope[key];
      if (value is! String || !_validUtc(value)) {
        throw CorruptSaveException('Invalid $key.');
      }
    }
    if (envelope['merge_policy'] != 'select_one_progression_branch' ||
        envelope['preserved_branches'] is! List ||
        envelope['pending_operations'] is! List ||
        (envelope['pending_operations'] as List).isNotEmpty ||
        envelope['applied_operation_ids'] is! List) {
      throw const IncompatibleSaveException(
        'Unsupported claim or merge state; preserve this snapshot.',
      );
    }
    final game = envelope['gameplay_state'];
    if (game is! Map ||
        game['schema_version'] != 1 ||
        game['payload'] is! Map) {
      throw const IncompatibleSaveException('Unsupported gameplay state.');
    }
    try {
      validatePayload(_copy(game['payload'] as Map));
      validateSnapshot?.call(
        _copy(game['payload'] as Map),
        DateTime.parse(envelope['settled_through_utc'] as String),
      );
    } on SaveException {
      rethrow;
    } catch (error) {
      throw CorruptSaveException('Invalid gameplay snapshot: $error');
    }
    // Imported ownership cache is never used for authority. Every new write
    // clears it; verified purchase restoration belongs to the service ledger.
    return SaveSnapshot._(envelope);
  }
}

Map<String, dynamic> _copy(Map value) =>
    (jsonDecode(jsonEncode(value)) as Map).cast<String, dynamic>();
Object? _canonical(Object? value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return {for (final key in keys) key: _canonical(value[key])};
  }
  if (value is List) return value.map(_canonical).toList();
  return value;
}

String _digest(Map<String, dynamic> value) =>
    sha256.convert(utf8.encode(jsonEncode(_canonical(value)))).toString();
String _encode(Map<String, dynamic> envelope) => jsonEncode({
  'format': 'tideglass-checksummed-save',
  'checksum': _digest(envelope),
  'envelope': envelope,
});
String _utc(DateTime value) => value.toUtc().toIso8601String();
bool _validUtc(String value) {
  if (!RegExp(
    r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z$',
  ).hasMatch(value))
    return false;
  final parsed = DateTime.tryParse(value);
  if (parsed == null) return false;
  // DateTime.parse normalizes invalid dates, which must not silently enter a save.
  return parsed.toIso8601String().substring(0, 19) == value.substring(0, 19);
}

bool _isUuid(Object? value) =>
    value is String &&
    RegExp(
      r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
    ).hasMatch(value);
String _uuid() {
  final random = Random.secure();
  final bytes = List.generate(16, (_) => random.nextInt(256));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
}
