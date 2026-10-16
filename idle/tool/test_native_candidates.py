"""Candidate integrity checks; no SDK, network, signing or native execution."""
import contextlib
import io
import json
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


if __name__ == '__main__':
    unittest.main()
