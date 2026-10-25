import 'dart:io';
import 'soundtrack_delivery.dart';

/// Recent shares may still be in use. Refuse a new export at capacity instead
/// of evicting one. The OS may clear its cache earlier than this app policy.
class SoundtrackExportCache {
  SoundtrackExportCache(this.directory, {DateTime Function()? now})
    : _now = now ?? DateTime.now;
  final Directory directory;
  final DateTime Function() _now;
  static const retention = Duration(hours: 24);
  static const maximumExports = 3;
  static const maximumBytes = maximumExports * SoundtrackDelivery.maximumBytes;
  static const scanLimit = 128;
  static bool _busy = false;
  static final _ownedName = RegExp(r'^soundtrack-[A-Za-z0-9]+$');

  /// Serializes cleanup/download/share across in-process callers. The download
  /// retains its existing byte/hash/session checks and failed-transfer cleanup.
  Future<T> export<T>(Future<T> Function(Directory) action) async {
    if (_busy) throw const SoundtrackCacheException('export_in_progress');
    _busy = true;
    try {
      final retained = await _clean();
      if (retained.$1 >= maximumExports ||
          retained.$2 > maximumBytes - SoundtrackDelivery.maximumBytes) {
        throw const SoundtrackCacheException('recent_exports_at_capacity');
      }
      return await action(directory);
    } finally {
      _busy = false;
    }
  }

  /// Also called at startup. Never follows links or recursively deletes an
  /// unrecognized directory. Future timestamps stay protected after clock skew.
  Future<void> cleanExpired() async {
    if (_busy) return;
    _busy = true;
    try {
      await _clean();
    } finally {
      _busy = false;
    }
  }

  Future<(int, int)> _clean() async {
    try {
      var type = await FileSystemEntity.type(
        directory.path,
        followLinks: false,
      );
      if (type == FileSystemEntityType.notFound) {
        await directory.create(recursive: true);
        type = await FileSystemEntity.type(directory.path, followLinks: false);
      }
      if (type != FileSystemEntityType.directory) {
        throw const SoundtrackCacheException('cache_not_directory');
      }
      final entries = <Directory>[];
      await for (final entry in directory.list(followLinks: false)) {
        if (entries.length >= scanLimit ||
            entry is! Directory ||
            !_ownedName.hasMatch(
              entry.uri.pathSegments.where((s) => s.isNotEmpty).last,
            )) {
          throw const SoundtrackCacheException('unrecognized_cache_entries');
        }
        entries.add(entry);
      }
      final now = _now().toUtc();
      var retained = 0, bytes = 0;
      // Validate everything before deleting anything. Partial traversal never
      // becomes a successful capacity check.
      final inspected = <(Directory, List<File>, DateTime, int)>[];
      for (final entry in entries) {
        var newest = (await entry.stat()).modified.toUtc();
        var size = 0;
        final files = <File>[];
        await for (final child in entry.list(followLinks: false)) {
          final name = child.uri.pathSegments.last;
          if (child is! File ||
              files.isNotEmpty ||
              (name != SoundtrackDelivery.filename &&
                  name != 'download.part')) {
            throw const SoundtrackCacheException('unrecognized_cache_entries');
          }
          final info = await child.stat();
          if (info.size > SoundtrackDelivery.maximumBytes) {
            throw const SoundtrackCacheException('oversized_cache_entry');
          }
          if (info.modified.toUtc().isAfter(newest))
            newest = info.modified.toUtc();
          size += info.size;
          files.add(child);
        }
        inspected.add((entry, files, newest, size));
      }
      for (final item in inspected) {
        if (now.difference(item.$3) >= retention) {
          for (final file in item.$2) {
            await file.delete();
          }
          // Non-recursive removal refuses newly introduced contents.
          await item.$1.delete();
        } else {
          retained++;
          bytes += item.$4;
        }
      }
      return (retained, bytes);
    } on SoundtrackCacheException {
      rethrow;
    } on FileSystemException {
      throw const SoundtrackCacheException('cache_unavailable');
    }
  }
}

class SoundtrackCacheException implements Exception {
  const SoundtrackCacheException(this.code);
  final String code;
  @override
  String toString() => 'Soundtrack cache: $code';
}
