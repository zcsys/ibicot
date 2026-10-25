"""Independent native-export gate probes. Only synthetic Python subprocesses run."""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tool'))
import build_native


class RuntimeBuildGateReview(unittest.TestCase):
    def probe(self, *, frozen_pass: bool, live_pass: bool):
        with tempfile.TemporaryDirectory(prefix='TideglassRuntimeGateReview-') as temp:
            root = Path(temp)
            app = root / 'game/mobile'
            app.mkdir(parents=True)
            (app / 'main.dart').write_text('void main() {}\n')
            tool = root / 'tool'
            tool.mkdir()
            target = tool / 'test_current_runtime_verification.py'
            def fixture(passed):
                return ('import unittest\nclass RuntimeProbe(unittest.TestCase):\n'
                        '    def test_real_subprocess(self):\n'
                        f'        self.assertTrue({passed!r}, "independent runtime gate failure")\n')
            target.write_text(fixture(frozen_pass))
            evidence = root / 'release/native-proof/frozen'
            evidence.mkdir(parents=True)
            with patch.object(build_native, 'ROOT', root):
                candidate, manifest = build_native.snapshot('frozen', evidence)
                target.write_text(fixture(live_pass))
                commands = build_native.tool_commands(candidate / 'workspace')
                self.assertEqual(list(commands), ['current-runtime-verifier-test'])
                self.assertEqual(commands['current-runtime-verifier-test'], [
                    sys.executable, '-m', 'unittest', 'discover', '-s', 'tool',
                    '-p', 'test_current_runtime_verification.py', '-v'])
                original_run = subprocess.run
                python_calls = []
                intercepted_exports = []
                def guarded_run(command, **kwargs):
                    if command[0] == str(root / 'tool/flutter'):
                        if command[1] == 'build':
                            intercepted_exports.append(command)
                            # Record that a passed host gate reached export, but
                            # never invoke a native process or manufacture an artifact.
                            return subprocess.CompletedProcess(command, 99)
                        self.assertIn(command[1], ['--version', 'pub'])
                        return subprocess.CompletedProcess(command, 0)
                    self.assertEqual(command, commands['current-runtime-verifier-test'])
                    self.assertEqual(kwargs['cwd'], candidate / 'workspace')
                    python_calls.append(command)
                    return original_run(command, **kwargs)
                with patch('sys.argv', ['build', '--candidate', str(candidate), '--host-checks', 'android']), \
                     patch.object(build_native, 'prepare_sdk_assets', return_value={'host_fixture_only': True}), \
                     patch.object(build_native.subprocess, 'run', side_effect=guarded_run), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(build_native.main(), 1)
                report_path = next((root / 'release/native-proof').glob('*/build-report.json'))
                report = json.loads(report_path.read_text())
                self.assertEqual(len(python_calls), 1)
                self.assertEqual(report['candidate_fingerprint'], manifest['source_fingerprint'])
                self.assertEqual(report['host_test_gate'], 'passed' if frozen_pass else 'failed')
                self.assertEqual(report['failed_host_checks'], [] if frozen_pass else ['current-runtime-verifier-test'])
                log = (report_path.parent / 'current-runtime-verifier-test.log').read_text()
                self.assertIn('Ran 1 test', log)
                if frozen_pass:
                    self.assertIn('OK', log)
                    self.assertEqual(len(intercepted_exports), 1)
                    self.assertFalse(report['results']['android']['build_succeeded'])
                    self.assertFalse(report['results']['android']['runtime_launch_proven'])
                else:
                    self.assertIn('independent runtime gate failure', log)
                    self.assertEqual(intercepted_exports, [])
                    self.assertEqual(report['results'], {})
                self.assertEqual(build_native.source_hashes(candidate / 'source'), manifest['source_sha256'])

    def test_failed_frozen_verifier_blocks_export_even_if_live_test_passes(self):
        self.probe(frozen_pass=False, live_pass=True)

    def test_passed_frozen_verifier_reaches_guarded_export_even_if_live_test_fails(self):
        self.probe(frozen_pass=True, live_pass=False)

    def test_runtime_verifier_gate_is_not_hidden_by_other_tool_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tool').mkdir()
            for name in ['test_native_probe.py', 'test_current_runtime_verification.py', 'test_study_probe.py']:
                (root / 'tool' / name).write_text('# discovery fixture\n')
            self.assertEqual(list(build_native.tool_commands(root)), [
                'candidate-integrity-test', 'current-runtime-verifier-test', 'study-test'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
