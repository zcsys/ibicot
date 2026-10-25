"""Candidate integrity checks; no SDK, network, signing or native execution."""
import contextlib
import io
import json
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_native
import derive_native_candidate


class CandidateIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.files = {
            'game/mobile/lib/main.dart': 'void main() {}\n',
            'game/core/test/core_test.dart': 'old assertion\n',
            'implementation/content/launch_manifest.json': '{}\n',
            'services/tideglass_service/__init__.py': '',
            'tests/services/test_service.py': '# service tests\n',
            'tool/build_native.py': '# test tool\n',
            'economy.json': '{}\n',
        }
        for relative, text in self.files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        for module in (build_native, derive_native_candidate):
            hook = patch.object(module, 'ROOT', self.root)
            hook.start()
            self.addCleanup(hook.stop)

    def capture(self):
        evidence = self.root / 'release/native-proof/initial'
        evidence.mkdir(parents=True)
        return build_native.snapshot('initial', evidence)

    def test_snapshot_contains_test_dependencies_and_separates_generated_work(self):
        candidate, manifest = self.capture()
        self.assertEqual(set(manifest['source_sha256']), set(self.files))
        self.assertEqual(build_native.source_hashes(candidate / 'source'), manifest['source_sha256'])
        (candidate / 'workspace/game/mobile/lib/main.dart').write_text('generated change\n')
        self.assertEqual(build_native.source_hashes(candidate / 'source'), manifest['source_sha256'])
        self.assertEqual((candidate / 'source/game/mobile/lib/main.dart').stat().st_mode & 0o222, 0)

    def test_derivation_includes_only_declared_overlay_and_preserves_parent(self):
        candidate, parent = self.capture()
        (self.root / 'game/core/test/core_test.dart').write_text('fixed assertion\n')
        (self.root / 'game/mobile/lib/main.dart').write_text('unrelated unfinished development\n')
        with patch('sys.argv', ['derive', str(candidate), 'game/core/test/core_test.dart']), contextlib.redirect_stdout(io.StringIO()):
            derive_native_candidate.main()
        derived = next(p for p in (self.root / '.tooling/build-candidates').iterdir() if p != candidate)
        current = json.loads((derived / 'manifest.json').read_text())
        differences = {key for key in current['source_sha256'] if current['source_sha256'][key] != parent['source_sha256'].get(key)}
        self.assertEqual(differences, {'game/core/test/core_test.dart'})
        self.assertEqual(current['parent_fingerprint'], parent['source_fingerprint'])
        self.assertEqual(build_native.source_hashes(candidate / 'source'), parent['source_sha256'])

    def test_tampered_parent_refuses_derivation(self):
        candidate, _ = self.capture()
        source = candidate / 'source/game/mobile/lib/main.dart'
        source.chmod(source.stat().st_mode | 0o200)
        source.write_text('tampered parent\n')
        with patch('sys.argv', ['derive', str(candidate), 'game/core/test/core_test.dart']):
            with self.assertRaisesRegex(RuntimeError, 'Parent source no longer matches'):
                derive_native_candidate.main()

    def test_android_release_regenerates_sdk_plugin_registration(self):
        # Regression for an actual AAB compile failure: the SDK skips removing
        # dev-only integration_test registration when --no-pub is supplied.
        command = build_native.native_build_command('/pinned/flutter', 'android', 'release')
        self.assertIn('appbundle', command)
        self.assertNotIn('--no-pub', command)
        self.assertIn('--no-pub', build_native.native_build_command('/pinned/flutter', 'android', 'debug'))
        self.assertIn('--no-codesign', build_native.native_build_command('/pinned/flutter', 'ios', 'release'))

    def test_snapshot_includes_actual_soundtrack_provider_fixture(self):
        fixture = self.root / 'release/downloads/tideglass-original-soundtrack.zip'
        fixture.parent.mkdir(parents=True)
        fixture.write_bytes(b'explicit provider fixture')
        candidate, manifest = self.capture()
        relative = str(fixture.relative_to(self.root))
        self.assertIn(relative, manifest['source_sha256'])
        self.assertEqual((candidate / 'source' / relative).read_bytes(), fixture.read_bytes())

    def test_sdk_fonts_use_recorded_external_link_without_changing_source(self):
        candidate, manifest = self.capture()
        sdk = self.root / '.tooling/flutter'
        fonts = sdk / 'bin/cache/artifacts/material_fonts'
        fonts.mkdir(parents=True)
        for name in ['Roboto-Regular.ttf', 'MaterialIcons-Regular.otf']:
            (fonts / name).write_bytes(b'unit fixture font')
        record = build_native.prepare_sdk_assets(candidate / 'workspace', sdk)
        self.assertEqual(Path(record['workspace_link']).resolve(), sdk.resolve())
        self.assertEqual(build_native.source_hashes(candidate / 'source'), manifest['source_sha256'])
        build_native.prepare_sdk_assets(candidate / 'workspace', sdk)
        with self.assertRaisesRegex(RuntimeError, 'Refusing to replace'):
            other = self.root / 'other-sdk'
            shutil.copytree(sdk, other)
            build_native.prepare_sdk_assets(candidate / 'workspace', other)

    def test_provider_gate_explicitly_discovers_nested_suite_in_pinned_venv(self):
        candidate, _ = self.capture()
        commands = build_native.provider_commands(candidate / 'workspace')
        self.assertEqual(commands['provider-test'][0], str(self.root / '.tooling/services-venv/bin/python'))
        self.assertIn('tests/services/providers', commands['provider-test'])
        self.assertTrue(commands['provider-environment'][-1].endswith('services/requirements-providers.lock'))

    def test_operations_failure_is_discovered_without_package_init(self):
        (self.root / 'tests/services/test_service.py').write_text(
            'import unittest\nclass Base(unittest.TestCase):\n'
            '    def test_base(self):\n'
            '        self.assertTrue(True)\n')
        nested = self.root / 'tests/services/operations'
        nested.mkdir()
        (nested / 'test_probe.py').write_text(
            'import unittest\nclass Probe(unittest.TestCase):\n'
            '    def test_operations_gate(self):\n'
            '        self.fail("nested operations fixture must be discovered")\n')
        commands = build_native.service_commands(self.root)
        base = subprocess.run(commands['services-test'], cwd=self.root,
                              capture_output=True, text=True)
        operations = subprocess.run(commands['operations-test'], cwd=self.root,
                                    capture_output=True, text=True)
        self.assertEqual(base.returncode, 0)
        self.assertNotEqual(operations.returncode, 0)
        self.assertIn('nested operations fixture must be discovered', operations.stderr)
        self.assertIn('Ran 1 test', operations.stderr)

    def test_only_synthetic_study_fixture_folder_is_frozen(self):
        fixture = self.root / 'release/study/fixtures/example/protocol.json'
        fixture.parent.mkdir(parents=True)
        fixture.write_text('{"synthetic":true}\n')
        excluded = self.root / 'release/study/participant-exports/real.json'
        excluded.parent.mkdir()
        excluded.write_text('not a fixture; never capture\n')
        (self.root / 'release/study/NOTES.md').write_text('not a fixture\n')
        candidate, manifest = self.capture()
        relative = str(fixture.relative_to(self.root))
        self.assertIn(relative, manifest['source_sha256'])
        self.assertNotIn(str(excluded.relative_to(self.root)), manifest['source_sha256'])
        self.assertNotIn('release/study/NOTES.md', manifest['source_sha256'])
        fixture.write_text('{"synthetic":true,"later_change":true}\n')
        self.assertEqual((candidate / 'source' / relative).read_text(), '{"synthetic":true}\n')
        self.assertEqual(build_native.source_hashes(candidate / 'source'), manifest['source_sha256'])

    def test_failing_study_test_stops_native_export_host_gate(self):
        (self.root / 'tests/services/test_service.py').write_text(
            'import unittest\nclass Base(unittest.TestCase):\n'
            '    def test_base(self): self.assertTrue(True)\n')
        (self.root / 'tool/test_study_probe.py').write_text(
            'import unittest\nclass Study(unittest.TestCase):\n'
            '    def test_measurement_gate(self):\n'
            '        self.fail("study fixture must stop native export")\n')
        candidate, _ = self.capture()
        original_run = subprocess.run
        native_commands = []
        def run(command, **kwargs):
            if command[0] == str(self.root / 'tool/flutter'):
                if command[1] == 'build':
                    native_commands.append(command)
                    raise AssertionError('Native export must not run after a failed study test')
                return subprocess.CompletedProcess(command, 0)
            return original_run(command, **kwargs)
        with patch('sys.argv', ['build', '--candidate', str(candidate), '--host-checks', 'android']), \
             patch.object(build_native, 'prepare_sdk_assets', return_value={'unit_fixture': True}), \
             patch.object(build_native.subprocess, 'run', side_effect=run), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_native.main(), 1)
        report_path = next((self.root / 'release/native-proof').glob('*/build-report.json'))
        report = json.loads(report_path.read_text())
        self.assertEqual(report['failed_host_checks'], ['study-test'])
        self.assertEqual(report['host_test_gate'], 'failed')
        self.assertEqual(report['results'], {})
        self.assertEqual(native_commands, [])
        self.assertIn('study fixture must stop native export',
                      (report_path.parent / 'study-test.log').read_text())


if __name__ == '__main__':
    unittest.main()
