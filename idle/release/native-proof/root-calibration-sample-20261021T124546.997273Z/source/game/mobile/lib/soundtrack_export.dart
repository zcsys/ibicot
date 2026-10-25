import 'dart:io';
import 'dart:ui';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:tideglass_platform/soundtrack_cache.dart';
import 'native_services.dart';

enum SoundtrackExportResult { handedOff, cancelled, unknown }

/// Called only by the player's download button. Authentication and hash checks
/// finish before any local archive is offered to the native export sheet.
Future<SoundtrackExportResult> exportSoundtrack(
  NativeServicesManager manager,
  Rect anchor,
) async {
  final temporary = await getTemporaryDirectory();
  final directory = Directory('${temporary.path}/tideglass-soundtrack-exports');
  return SoundtrackExportCache(directory).export((directory) async {
    final account = manager.session;
    final file = await manager.downloadSoundtrack(directory);
    if (!identical(manager.session, account)) {
      await file.parent.delete(recursive: true);
      throw StateError('Account changed before soundtrack export.');
    }
    final result = await SharePlus.instance.share(
      ShareParams(
        files: [XFile(file.path, mimeType: 'application/zip')],
        sharePositionOrigin: anchor,
      ),
    );
    // Keep recent files for receiving apps. Startup and the next export remove
    // files after 24 hours; at capacity, refuse another download instead.
    return switch (result.status) {
      ShareResultStatus.success => SoundtrackExportResult.handedOff,
      ShareResultStatus.dismissed => SoundtrackExportResult.cancelled,
      ShareResultStatus.unavailable => SoundtrackExportResult.unknown,
    };
  });
}

/// Optional maintenance must never prevent opening the player's harbor.
Future<void> cleanSoundtrackExports() async {
  try {
    final temporary = await getTemporaryDirectory();
    await SoundtrackExportCache(
      Directory('${temporary.path}/tideglass-soundtrack-exports'),
    ).cleanExpired();
  } catch (_) {
    // Export itself surfaces cache errors; guest startup remains available.
  }
}
