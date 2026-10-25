from pathlib import Path
P=Path(__file__).resolve().parent/'staged';p=P/'platform_smoke_test.dart';s=p.read_text();start=s.index('void captureGalleryScenario(');end=s.index('\nvoid naturalScenario(',start);g=s[start:end]
g=g.replace("    final startSignal = File('${directory.path}/recording-started');", """    final startSignal = File('${directory.path}/recording-started');
    final stopSignal = File('${directory.path}/recording-stopped.json');
    final watch = Stopwatch();
    final androidScreencaps = <Map<String, dynamic>>[];
    final captureIdentity = {
      for (final key in [
        'verification_id', 'candidate_fingerprint', 'harness_sha256',
        'device_label', 'run_id', 'platform', 'scenario',
      ]) key: binding.reportData![key],
      'directory': directory.path,
    };
    Future<void> screenshot(String screen) async {
      if (!Platform.isAndroid) {
        await binding.takeScreenshot('$label-capture-$screen');
        return;
      }
      // The integration_test Android image-view conversion retains a frozen
      // display between screenshot acquisitions. Capture the real OS surface
      // externally; do not convert/revert it or invoke UI callbacks directly.
      final sequence = androidScreencaps.length + 1;
      final request = {
        ...captureIdentity,
        'sequence': sequence,
        'file': '$label-capture-$screen.png',
        'width': tester.view.physicalSize.width.toInt(),
        'height': tester.view.physicalSize.height.toInt(),
        'gameplay_elapsed_ms': watch.elapsedMilliseconds,
      };
      final ack = File('${directory.path}/screenshot-$sequence-ready.json');
      expect(await ack.exists(), isFalse);
      await tester.pump();
      debugPrint('TIDEGLASS_NATIVE_SCREENSHOT_READY ${jsonEncode(request)}');
      await waitForNativeCondition(
        tester, ack.existsSync,
        reason: 'The exact Android raw screenshot must be captured and acknowledged',
        timeout: const Duration(seconds: 10),
      );
      final receipt = Map<String, dynamic>.from(
        jsonDecode(await ack.readAsString()) as Map,
      );
      for (final entry in request.entries) {
        expect(receipt[entry.key], entry.value);
      }
      expect(receipt['capture_method'], 'adb exec-out screencap -p');
      expect(receipt['sha256'], matches(RegExp(r'^[a-f0-9]{64}$')));
      expect(receipt['bytes'], greaterThan(0));
      androidScreencaps.add(receipt);
    }""")
g=g.replace('    if (Platform.isAndroid) await binding.convertFlutterSurfaceToImage();\n','')
for name in ['main','chapter','challenge','season']:
 g=g.replace("await binding.takeScreenshot('$label-capture-"+name+"');", "await screenshot('"+name+"');")
g=g.replace("'TIDEGLASS_NATIVE_CAPTURE_READY ${jsonEncode({'directory': directory.path})}',", "'TIDEGLASS_NATIVE_CAPTURE_READY ${jsonEncode(Platform.isAndroid ? captureIdentity : {'directory': directory.path})}',")
g=g.replace('    final watch = Stopwatch()..start();','    watch.start();')
g=g.replace("    debugPrint('TIDEGLASS_NATIVE_CAPTURE_DONE');\n    binding.reportData!.addAll({\n      'real_gameplay_elapsed_ms': watch.elapsedMilliseconds,", """    final gameplayElapsedMs = watch.elapsedMilliseconds;
    if (Platform.isAndroid) {
      final request = {
        ...captureIdentity, 'gameplay_elapsed_ms': gameplayElapsedMs,
      };
      debugPrint('TIDEGLASS_NATIVE_CAPTURE_DONE ${jsonEncode(request)}');
      // Keep the final production screen present until the owned OS recorder
      // has stopped. This does not change the gameplay timeline or its speed.
      await waitForNativeCondition(
        tester, stopSignal.existsSync,
        reason: 'The exact Android recorder must stop before removing its UI',
        timeout: const Duration(seconds: 15),
      );
      final receipt = Map<String, dynamic>.from(
        jsonDecode(await stopSignal.readAsString()) as Map,
      );
      for (final entry in request.entries) {
        expect(receipt[entry.key], entry.value);
      }
      expect(receipt['recorder_stopped'], isTrue);
      binding.reportData!['android_screencaps'] = androidScreencaps;
      binding.reportData!['android_recording_stop'] = receipt;
    } else {
      debugPrint('TIDEGLASS_NATIVE_CAPTURE_DONE');
    }
    binding.reportData!.addAll({
      'real_gameplay_elapsed_ms': gameplayElapsedMs,""")
assert 'convertFlutterSurfaceToImage' not in g
assert g.count("await screenshot('")==4
p.write_text(s[:start]+g+s[end:])
p=P/'native_integration_driver.dart';s=p.read_text();s=s.replace("import 'package:integration_test/integration_test_driver.dart';", "import 'package:integration_test/integration_test_driver.dart';\nimport 'package:crypto/crypto.dart';")
s=s.replace("      final paths = <String>[];", """      final paths = <String>[];
      final external = result['android_screencaps'];
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
      }""")
p.write_text(s)
