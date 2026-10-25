"""Independent completion-boundary probes; synthetic strings are not device results."""
import sys
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tool'))
import verify_native

class CompletionReview(unittest.TestCase):
    def test_zero_executed_tests_cannot_qualify(self):
        self.assertTrue(verify_native.native_log_errors(
            'flutter: 00:00 +0: All tests passed!\nAll tests passed.\n'))
    def test_uncaught_error_after_native_completion_cannot_qualify(self):
        self.assertTrue(verify_native.native_log_errors(
            'flutter: 00:05 +1: All tests passed!\n'
            'Unhandled Exception: late teardown\nAll tests passed.\n'))
    def test_prefixed_native_error_after_success_cannot_qualify(self):
        for error in ['flutter: Unhandled Exception: late error',
                      'E/flutter ( 123): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: error']:
            with self.subTest(error=error):
                self.assertTrue(verify_native.native_log_errors(
                    'flutter: 00:05 +2: All tests passed!\nAll tests passed.\n' + error + '\n'))
    def test_completion_is_a_line_boundary_not_application_text(self):
        for native in ['app said flutter: 00:05 +2: All tests passed!',
                       'flutter: 00:05 +2 -1: All tests passed!',
                       'flutter: 00:05 +2: All tests passed! (fixture)',
                       'flutter: 00:05 +2: Some tests failed.']:
            with self.subTest(native=native):
                self.assertTrue(verify_native.native_log_errors(native + '\nAll tests passed.\n'))
    def test_both_completions_required(self):
        for only in ['All tests passed.\n', 'flutter: 00:05 +2: All tests passed!\n']:
            self.assertTrue(verify_native.native_log_errors(only))
    def test_positive_native_and_driver_completion(self):
        for native in ['flutter: 00:05 +2: All tests passed!',
                       'I/flutter ( 123): 01:02:03 +12: All tests passed!']:
            with self.subTest(native=native):
                self.assertEqual(verify_native.native_log_errors(native + '\nAll tests passed.\n'), [])
    def test_failure_wins_even_if_other_suite_succeeded(self):
        self.assertTrue(verify_native.native_log_errors(
            'flutter: 00:01 +1: All tests passed!\n'
            'flutter: 00:02 +1 -1: teardown [E]\n'
            'All tests passed.\n'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
