import 'dart:convert';
import 'dart:io';

import 'package:integration_test/integration_test_driver.dart';
import 'package:crypto/crypto.dart';

Future<void> main() async {
  final directory = Directory(
    Platform.environment['TIDEGLASS_NATIVE_EVIDENCE'] ??
        '../../release/native-proof/integration',
  );
  await directory.create(recursive: true);
  await integrationDriver(
    writeResponseOnFailure: true,
    responseDataCallback: (data) async {
      final result = Map<String, dynamic>.from(data ?? {});
      final screenshots = result.remove('screenshots') as List<dynamic>? ?? [];
      final paths = <String>[];
      final external = result['android_screencaps'];
      try {
        if (external != null) {
          if (result['platform'] != 'android' ||
              result['scenario'] != 'capture-gallery' ||
              screenshots.isNotEmpty || external is! List || external.length != 4) {
            throw FormatException('Unexpected external gallery screenshots');
          }
          final label = result['device_label'];
          if (label is! String || !RegExp(r'^[a-zA-Z0-9_-]+$').hasMatch(label)) {
            throw FormatException('Unsafe gallery device label');
          }
          const screens = ['main', 'chapter', 'challenge', 'season'];
          for (var index = 0; index < screens.length; index++) {
            final receipt = Map<String, dynamic>.from(external[index] as Map);
            final name = '$label-capture-${screens[index]}.png';
            if (receipt['file'] != name || receipt['sequence'] != index + 1 ||
                receipt['capture_method'] != 'adb exec-out screencap -p') {
              throw FormatException('Unexpected raw gallery screenshot identity');
            }
            for (final key in [
              'verification_id', 'candidate_fingerprint', 'harness_sha256',
              'device_label', 'run_id', 'platform', 'scenario',
            ]) {
              if (receipt[key] != result[key]) {
                throw FormatException('Raw screenshot identity differs: $key');
              }
            }
            final file = File('${directory.path}/$name');
            if (FileSystemEntity.typeSync(file.path, followLinks: false) !=
                FileSystemEntityType.file) {
              throw FormatException('Raw screenshot is missing or is a symlink');
            }
            final bytes = await file.readAsBytes();
            if (bytes.length != receipt['bytes'] ||
                sha256.convert(bytes).toString() != receipt['sha256']) {
              throw FormatException('Raw screenshot differs from acknowledged bytes');
            }
            paths.add(file.path);
          }
        } else if (result['platform'] == 'android' &&
            result['scenario'] == 'capture-gallery') {
          throw FormatException('Android gallery raw screenshot receipts are missing');
        }
      } catch (error) {
        // Retain failed Android acknowledgement/hash evidence as well as the
        // raw files. Rethrow so a partial gallery cannot become a passing run.
        result['screenshots'] = paths;
        result['screenshot_collection_error'] = error.toString();
        await File('${directory.path}/result.json').writeAsString(
          const JsonEncoder.withIndent('  ').convert(result),
        );
        rethrow;
      }
      for (final raw in screenshots) {
        final screenshot = Map<String, dynamic>.from(raw as Map);
        final name = screenshot['screenshotName'] as String;
        if (!RegExp(r'^[a-zA-Z0-9_-]+$').hasMatch(name))
          throw FormatException('Unsafe screenshot name');
        final path = '${directory.path}/$name.png';
        await File(path)
            .writeAsBytes(List<int>.from(screenshot['bytes'] as List));
        paths.add(path);
      }
      result['screenshots'] = paths;
      await File('${directory.path}/result.json')
          .writeAsString(const JsonEncoder.withIndent('  ').convert(result));
    },
  );
}
