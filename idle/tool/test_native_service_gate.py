"""Real subprocess orchestration regressions; no Flutter/device/provider calls."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import build_native


class ServiceHostGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        self.report = {'host_checks': {}}
        self.hook = patch.object(build_native, 'ROOT', self.root)
        self.hook.start()
        self.addCleanup(self.hook.stop)
        self.python = self.root / '.tooling/services-venv/bin/python'
        self.python.parent.mkdir(parents=True)
        self.python.symlink_to(sys.executable)
        self.write('services/requirements-providers.lock', 'qualified\n')
        # An explicit tiny validation stand-in exercises ordering/failure paths.
        # The author run separately executes the actual version-lock checker.
        self.write('tool/check_provider_environment.py',
                   'from pathlib import Path\nimport sys\n'
                   'with Path("journal").open("a") as f: f.write("environment\\n")\n'
                   'raise SystemExit(0 if Path(sys.argv[1]).read_text()=="qualified\\n" else 7)\n')
        self.write_suite('services-test', 'tests/services/test_base.py')
        self.write_suite('operations-test', 'tests/services/operations/test_operation.py')
        self.write_suite('provider-test', 'tests/services/providers/test_provider.py')
        self.write('release/downloads/tideglass-original-soundtrack.zip', 'synthetic fixture')
        (self.root / 'game/mobile').mkdir(parents=True)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def write_suite(self, key, relative, fail=False):
        self.write(relative,
                   'from pathlib import Path\nimport unittest\n'
                   'class Probe(unittest.TestCase):\n'
                   '    def test_gate(self):\n'
                   f'        with Path("journal").open("a") as f: f.write({key!r}+"\\n")\n'
                   f'        self.assertFalse({fail!r}, "explicit {key} failure")\n')

    def journal(self, root=None):
        path = (root or self.root) / 'journal'
        return path.read_text().splitlines() if path.is_file() else []

    def run_gates(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return build_native.run_service_host_checks(self.root, self.evidence, self.report)

    def test_command_interpreters_and_candidate_lock_are_exact(self):
        commands = build_native.service_commands(self.root)
        self.assertEqual(commands['services-test'][0], sys.executable)
        self.assertEqual(commands['operations-test'][0], str(self.python))
        self.assertIn('tests/services/operations', commands['operations-test'])
        environment = build_native.provider_commands(self.root)['provider-environment']
        self.assertEqual(environment, [str(self.python), str(self.root / 'tool/check_provider_environment.py'),
                                       str(self.root / 'services/requirements-providers.lock')])

    def test_real_subprocess_order_and_both_nested_suites(self):
        self.assertEqual(self.run_gates(), [])
        self.assertEqual(self.journal(), ['services-test', 'environment', 'operations-test', 'provider-test'])
        self.assertEqual(self.report['provider_fixture_sha256'], hashlib.sha256(b'synthetic fixture').hexdigest())
        for name in ('services-test', 'operations-test', 'provider-test'):
            self.assertIn('Ran 1 test', (self.evidence / (name + '.log')).read_text())
            self.assertEqual(self.report['host_checks'][name]['exit_code'], 0)

    def test_operations_alone_still_requires_environment(self):
        (self.root / 'tests/services/providers/test_provider.py').unlink()
        (self.root / 'tests/services/providers').rmdir()
        (self.root / 'release/downloads/tideglass-original-soundtrack.zip').unlink()
        self.assertEqual(self.run_gates(), [])
        self.assertEqual(self.journal(), ['services-test', 'environment', 'operations-test'])
        self.assertNotIn('provider_fixture_sha256', self.report)

    def test_missing_environment_blocks_both_dependent_suites(self):
        self.python.unlink()
        failed = self.run_gates()
        self.assertEqual(failed, ['provider-environment', 'operations-test', 'provider-test'])
        self.assertEqual(self.journal(), ['services-test'])
        for name in ('operations-test', 'provider-test'):
            self.assertEqual(self.report['host_checks'][name]['status'], 'blocked')
            self.assertEqual(self.report['host_checks'][name]['exit_code'], 1)
        self.assertIn('FileNotFoundError', self.report['host_checks']['provider-environment']['error'])

    def test_lock_mismatch_never_runs_dependent_suites(self):
        self.write('services/requirements-providers.lock', 'mismatched\n')
        self.assertEqual(self.run_gates(), ['provider-environment', 'operations-test', 'provider-test'])
        self.assertEqual(self.journal(), ['services-test', 'environment'])
        self.assertEqual(self.report['host_checks']['provider-environment']['exit_code'], 7)

    def test_non_executable_environment_records_failure(self):
        self.python.unlink()
        self.python.write_text('not an executable interpreter')
        self.python.chmod(0o600)
        self.assertEqual(self.run_gates(), ['provider-environment', 'operations-test', 'provider-test'])
        self.assertIn('PermissionError', self.report['host_checks']['provider-environment']['error'])
        self.assertEqual(self.journal(), ['services-test'])

    def test_missing_provider_fixture_keeps_operations_evidence(self):
        (self.root / 'release/downloads/tideglass-original-soundtrack.zip').unlink()
        self.assertEqual(self.run_gates(), ['provider-fixture', 'provider-test'])
        self.assertEqual(self.journal(), ['services-test', 'environment', 'operations-test'])
        self.assertEqual(self.report['host_checks']['operations-test']['exit_code'], 0)
        self.assertEqual(self.report['host_checks']['provider-test']['status'], 'blocked')

    def test_operations_failure_preserved_provider_still_runs(self):
        self.write_suite('operations-test', 'tests/services/operations/test_operation.py', fail=True)
        self.assertEqual(self.run_gates(), ['operations-test'])
        self.assertEqual(self.journal(), ['services-test', 'environment', 'operations-test', 'provider-test'])
        self.assertIn('explicit operations-test failure', (self.evidence / 'operations-test.log').read_text())

    def test_provider_failure_preserved_after_operations(self):
        self.write_suite('provider-test', 'tests/services/providers/test_provider.py', fail=True)
        self.assertEqual(self.run_gates(), ['provider-test'])
        self.assertEqual(self.journal(), ['services-test', 'environment', 'operations-test', 'provider-test'])

    def test_independent_stdlib_failure_is_not_hidden_by_valid_environment(self):
        self.write_suite('services-test', 'tests/services/test_base.py', fail=True)
        self.assertEqual(self.run_gates(), ['services-test'])
        self.assertEqual(self.journal(), ['services-test', 'environment', 'operations-test', 'provider-test'])

    def test_operations_failure_stops_main_before_any_native_export(self):
        self.write_suite('operations-test', 'tests/services/operations/test_operation.py', fail=True)
        initial = self.root / 'release/native-proof/initial'
        initial.mkdir(parents=True)
        candidate, _ = build_native.snapshot('initial', initial)
        # An empty native app directory is not a frozen input, so recreate it
        # in the disposable build workspace for the mocked SDK preparation.
        (candidate / 'workspace/game/mobile').mkdir(parents=True, exist_ok=True)
        original_run = subprocess.run
        native_commands = []

        def run(command, **kwargs):
            if command[0] == str(self.root / 'tool/flutter'):
                if command[1] == 'build':
                    native_commands.append(command)
                    raise AssertionError('Native export after failed operations gate')
                return subprocess.CompletedProcess(command, 0)
            return original_run(command, **kwargs)

        with patch('sys.argv', ['build', '--candidate', str(candidate), '--host-checks', 'android']), \
             patch.object(build_native, 'prepare_sdk_assets', return_value={'test_fixture': True}), \
             patch.object(build_native.subprocess, 'run', side_effect=run), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_native.main(), 1)
        report_path = next((self.root / 'release/native-proof').glob('*/build-report.json'))
        report = json.loads(report_path.read_text())
        self.assertEqual(report['host_test_gate'], 'failed')
        self.assertEqual(report['failed_host_checks'], ['operations-test'])
        self.assertEqual(report['results'], {})
        self.assertEqual(native_commands, [])
        self.assertEqual(self.journal(candidate / 'workspace'), ['services-test', 'environment', 'operations-test', 'provider-test'])


if __name__ == '__main__':
    unittest.main()
