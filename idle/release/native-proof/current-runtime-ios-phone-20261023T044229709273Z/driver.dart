import 'dart:convert';
import 'dart:io';

import 'package:integration_test/integration_test_driver.dart';

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
