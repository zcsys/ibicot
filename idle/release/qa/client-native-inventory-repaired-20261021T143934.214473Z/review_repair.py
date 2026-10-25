"""Independent persistent-input-drift/publication boundary review; no native execution."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
original = ROOT / 'release/qa/client-native-inventory-20261021T143056.713149Z/review_inventory.py'
spec = importlib.util.spec_from_file_location('original_review_fixtures', original)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
m = fixtures.m


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RepairReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=OUT)
        self.addCleanup(self.temp.cleanup)
        self.f = fixtures.Fixture(Path(self.temp.name))
        self.aapt = self.f.root / 'aapt-tool.bin'
        self.aapt.write_bytes(b'distinct synthetic aapt; never executed')
        self.collector = self.f.root / 'review-owned-collector.py'
        self.collector.write_bytes(Path(m.__file__).read_bytes())
        self.collector_hash = sha(self.collector)
        patcher = patch.object(m, '__file__', str(self.collector))
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_collector(self):
        return m.inspect(self.f.root, self.f.candidate, self.f.reports, self.f.root / 'out', 'synthetic-java-not-executed', self.f.tool, self.aapt)

    def assert_drift_rejects(self, target, remove=False):
        changed = False
        def decoder(argv, output):
            nonlocal changed
            result = self.f.command(argv, output)
            if not changed:
                changed = True
                if remove:
                    target.unlink()
                else:
                    target.write_bytes(b'changed after initial validation')
            return result
        with patch.object(m, 'command', decoder):
            with self.assertRaisesRegex(ValueError, 'input drift during collection'):
                self.run_collector()
        self.assertTrue(changed)
        self.assertFalse((self.f.root / 'out/inventory.json').exists())
        self.assertEqual(sha(self.f.root / 'out/collector.py'), self.collector_hash)

    def test_candidate_manifest_drift_cannot_publish(self):
        self.assert_drift_rejects(self.f.candidate / 'manifest.json')

    def test_debug_build_report_drift_cannot_publish(self):
        self.assert_drift_rejects(self.f.reports[0])

    def test_release_build_report_drift_cannot_publish(self):
        self.assert_drift_rejects(self.f.reports[1])

    def test_bundletool_drift_cannot_publish(self):
        self.assert_drift_rejects(self.f.tool)

    def test_aapt_drift_cannot_publish(self):
        self.assert_drift_rejects(self.aapt)

    def test_candidate_source_removal_cannot_publish(self):
        self.assert_drift_rejects(self.f.source, remove=True)

    def test_artifact_drift_during_decoder_cannot_publish(self):
        self.assert_drift_rejects(self.f.artifacts[0])

    def test_collector_drift_cannot_publish(self):
        self.assert_drift_rejects(self.collector)

    def test_positive_tool_and_preserved_source_hashes_are_exact(self):
        with patch.object(m, 'command', self.f.command):
            result = self.run_collector()
        self.assertEqual(result['collector_sha256'], self.collector_hash)
        self.assertEqual(result['collector_sha256'], sha(self.f.root / 'out/collector.py'))
        self.assertEqual(result['tools']['aapt2_sha256'], sha(self.aapt))
        self.assertEqual(result['tools']['bundletool_sha256'], sha(self.f.tool))
        self.assertNotEqual(result['tools']['aapt2_sha256'], result['tools']['bundletool_sha256'])
        self.assertFalse(result['runtime_traffic_observed'])
        self.assertFalse(result['release_acceptance'])
        self.assertTrue((self.f.root / 'out/inventory.json').is_file())
        for row in result['artifacts']:
            self.assertEqual(row['build_report_sha256'], sha(Path(row['build_report'])))
            self.assertEqual(row['artifact_sha256'], sha(Path(row['artifact'])))


if __name__ == '__main__':
    unittest.main(verbosity=2)
