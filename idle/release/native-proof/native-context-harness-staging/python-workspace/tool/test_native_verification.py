"""Provenance regressions for native entrypoints and failure cleanup targeting."""
import unittest
import base64
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

import native_recording
import verify_native


class NativeVerificationTests(unittest.TestCase):
    def test_native_teardown_failure_overrides_driver_success_line(self):
        misleading = ('flutter: 00:10 +0: native audio [E]\n'
                      'flutter: PlatformException: already disposed\n'
                      'flutter: 00:10 +1 -1: Some tests failed.\n'
                      'All tests passed.\nLeaving the application running.\n')
        self.assertTrue(verify_native.native_log_errors(misleading))
        self.assertTrue(verify_native.native_log_errors('BUILD FAILED\nAll tests passed.\n'))
        self.assertTrue(verify_native.native_log_errors('Test never completed\n'))
        self.assertEqual(verify_native.native_log_errors(
            'flutter: 00:05 +2: All tests passed!\nAll tests passed.\n'), [])

    def test_native_and_driver_completion_are_both_required(self):
        for incomplete in ['All tests passed.\n',
                           'flutter: 00:05 +2: All tests passed!\n',
                           'app text says All tests passed.\n']:
            self.assertTrue(verify_native.native_log_errors(incomplete))

    def test_android_native_status_is_checked_including_teardown_errors(self):
        good = 'I/flutter ( 3734): 00:15 +2: All tests passed!\nAll tests passed.\n'
        self.assertEqual(verify_native.native_log_errors(good), [])
        self.assertTrue(verify_native.native_log_errors(
            'I/flutter ( 3734): 00:15 +1: teardown [E]\n' + good))

    def test_zero_completed_native_tests_cannot_pass(self):
        for prefix in ['flutter:', 'I/flutter ( 42):']:
            self.assertTrue(verify_native.native_log_errors(
                prefix + ' 00:00 +0: All tests passed!\nAll tests passed.\n'))

    def test_late_uncaught_exceptions_override_success(self):
        good = 'flutter: 00:05 +2: All tests passed!\nAll tests passed.\n'
        for failure in ['Unhandled Exception: late teardown',
                        'flutter: Unhandled Exception: late teardown',
                        'I/flutter ( 42): Uncaught Error: callback failed',
                        'E/flutter ( 42): Uncaught Error: callback failed',
                        '[ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: late callback',
                        'I/flutter ( 42): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: late callback',
                        'E/flutter ( 42): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: late callback']:
            with self.subTest(failure=failure):
                self.assertIn('Uncaught Dart/native exception in log',
                              verify_native.native_log_errors(good + failure + '\n'))
        self.assertEqual(verify_native.native_log_errors(
            good + 'flutter: Help text explains Unhandled Exception: as an example\n'), [])

    def test_clock_entrypoints_privacy_manifests_and_locks_are_pinned(self):
        required = [
            'game/mobile/lib/ownership_clock.dart',
            'game/mobile/android/app/src/main/kotlin/dev/tideglass/game/MainActivity.kt',
            'game/mobile/android/app/src/main/AndroidManifest.xml',
            'game/mobile/ios/Runner/AppDelegate.swift',
            'game/mobile/ios/Runner/PrivacyInfo.xcprivacy',
            'game/mobile/macos/Runner/MainFlutterWindow.swift',
            'game/mobile/pubspec.yaml',
            'game/mobile/pubspec.lock',
            'game/platform/pubspec.lock',
        ]
        actual = verify_native.production_inputs({path: 'expected' for path in required})
        self.assertEqual(set(actual), set(required))

    def test_sdk_generated_registration_is_separate_from_production_inputs(self):
        paths = {
            'game/mobile/android/app/src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java': 'mode-specific',
            'game/mobile/ios/Runner/GeneratedPluginRegistrant.m': 'mode-specific',
            'game/mobile/integration_test/platform_smoke_test.dart': 'separately-captured',
            'game/mobile/lib/soundtrack_export.dart': 'production',
        }
        self.assertEqual(verify_native.production_inputs(paths), {
            'game/mobile/lib/soundtrack_export.dart': 'production',
        })

    def test_early_failure_cleanup_uses_declared_device_without_runtime_payload(self):
        self.assertEqual(verify_native.native_platform('F05BE4B0-52C1-4CA1-B721-BD64AE559E3F', None), 'ios')
        self.assertEqual(verify_native.native_platform('emulator-5556', None), 'android')
        self.assertEqual(verify_native.native_platform('physical-serial', 'android'), 'android')
        with self.assertRaisesRegex(ValueError, 'Specify --platform'):
            verify_native.native_platform('unknown', None)

    def test_android_capture_signal_accepts_only_exact_private_run_directory(self):
        good = '/data/user/0/dev.tideglass.game/files/native-verification/capture-phone-run1'
        self.assertEqual(native_recording.signal_path('android', good, 'phone', 'run1'), Path(good) / 'recording-started')
        for bad in [good.replace('run1', 'run2'), good.replace('dev.tideglass.game', 'other.app'),
                    '/sdcard/native-verification/capture-phone-run1', good + '/..']:
            with self.assertRaises(ValueError):
                native_recording.signal_path('android', bad, 'phone', 'run1')

    def test_ios_capture_signal_is_bound_to_actual_app_container(self):
        with TemporaryDirectory() as directory:
            expected = Path(directory) / 'Library/Application Support/native-verification/capture-ipad-run1'
            expected.mkdir(parents=True)
            self.assertEqual(native_recording.signal_path('ios', str(expected), 'ipad', 'run1', directory), expected / 'recording-started')
            with self.assertRaises(ValueError):
                native_recording.signal_path('ios', str(expected), 'ipad', 'run1', directory + '-other')
            with self.assertRaises(ValueError):
                native_recording.signal_path('ios', str(expected), 'ipad', '../run1', directory)

    def test_ios_capture_signal_rejects_symlink_outside_container(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            support = Path(directory) / 'Library/Application Support'
            support.mkdir(parents=True)
            (support / 'native-verification').symlink_to(outside, target_is_directory=True)
            unsafe = support / 'native-verification/capture-phone-run1'
            with self.assertRaises(ValueError):
                native_recording.signal_path('ios', str(unsafe), 'phone', 'run1', directory)

    def test_capture_manifest_pins_four_distinct_raw_files_and_video(self):
        with TemporaryDirectory() as directory:
            evidence = Path(directory)
            png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a8s8AAAAASUVORK5CYII=')
            screens = []
            for name in ('main', 'chapter', 'challenge', 'season'):
                file = evidence / f'phone-capture-{name}.png'
                file.write_bytes(png)
                screens.append(str(file))
            # This is only a manifest unit fixture, never native video evidence.
            (evidence / 'gameplay.mp4').write_bytes(b'manifest-unit-fixture')
            payload = {'screenshots': screens, 'device_label': 'phone',
                       'candidate_fingerprint': 'candidate', 'verification_id': 'verification',
                       'harness_sha256': 'harness', 'platform': 'ios', 'os_version': 'test',
                       'run_id': 'run1', 'provenance': 'unit fixture', 'platform_locale': 'en_US',
                       'seeded_core': {}, 'seeded_story': {},
                       'actual_purchase_count_delta': 1, 'real_gameplay_elapsed_ms': 25000}
            recording = {'passed': True, 'media': {'duration_seconds': 26, 'width': 1, 'height': 1, 'audio_track_count': 0}}
            result = native_recording.capture_manifest(evidence, payload, recording, 'device')
            self.assertEqual(len(result['screenshots']), 4)
            self.assertEqual(result['screenshots'][0]['sha256'], hashlib.sha256(png).hexdigest())
            self.assertEqual(result['screenshots'][0]['width'], 1)
            self.assertEqual(result['video']['sha256'], hashlib.sha256(b'manifest-unit-fixture').hexdigest())
            self.assertEqual(result['candidate_fingerprint'], 'candidate')
            payload['screenshots'] = screens[:3]
            with self.assertRaisesRegex(ValueError, 'four distinct'):
                native_recording.capture_manifest(evidence, payload, recording, 'device')
            payload['screenshots'] = screens[:3] + [screens[0]]
            with self.assertRaisesRegex(ValueError, 'four distinct'):
                native_recording.capture_manifest(evidence, payload, recording, 'device')

    def test_capture_manifest_rejects_screenshots_outside_evidence(self):
        with TemporaryDirectory() as directory:
            payload = {'device_label': 'phone', 'screenshots': [str(Path(directory).parent / 'phone-capture-main.png')]}
            with self.assertRaisesRegex(ValueError, 'Unexpected gallery'):
                native_recording.capture_manifest(Path(directory), payload, {}, 'device')


if __name__ == '__main__':
    unittest.main()
