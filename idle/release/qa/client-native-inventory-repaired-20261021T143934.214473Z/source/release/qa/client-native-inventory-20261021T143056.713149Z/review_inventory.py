"""Independent synthetic integrity probes; fake decoders never prove native behavior."""
import hashlib
import importlib.util
import json
import plistlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('collector_under_review', ROOT / 'release/native-privacy/inspect_artifacts.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Fixture:
    def __init__(self, root):
        self.root = root
        self.candidate = root / 'candidate'
        self.source = self.candidate / 'source/app/source.dart'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('frozen source')
        pins = {'app/source.dart': digest(self.source)}
        self.fingerprint = hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        (self.candidate / 'manifest.json').write_text(json.dumps({'source_sha256': pins, 'source_fingerprint': self.fingerprint}))
        self.tool = root / 'tool.bin'
        self.tool.write_bytes(b'synthetic tool; never executed')
        self.reports = []
        self.artifacts = []
        for mode, platforms in [('debug', ['ios', 'android', 'macos']), ('release', ['ios', 'android'])]:
            records = {}
            for platform in platforms:
                artifact = root / f'{platform}-{mode}.zip'
                with zipfile.ZipFile(artifact, 'w') as z:
                    if platform in ['ios', 'macos']:
                        z.writestr('Runner.app/Info.plist', plistlib.dumps({'CFBundleIdentifier': 'synthetic.example', 'mode': mode, 'platform': platform}))
                    else:
                        z.writestr('base/root/sdk.properties', f'version=synthetic-{mode}')
                self.artifacts.append(artifact)
                records[platform] = {'build_succeeded': True, 'exit_code': 0, 'artifact': artifact.name, 'artifact_sha256': digest(artifact), 'artifact_bytes': artifact.stat().st_size}
            report = root / f'{mode}.json'
            report.write_text(json.dumps({'candidate_fingerprint': self.fingerprint, 'candidate_directory': str(self.candidate), 'source_snapshot_unchanged': True, 'dependency_locks_unchanged': True, 'mode': mode, 'results': records}))
            self.reports.append(report)

    def command(self, argv, output):
        data = b'<manifest package="synthetic.example"><application/></manifest>' if output.suffix == '.xml' else b'synthetic decoder output\n'
        output.write_bytes(data)
        err = output.with_suffix(output.suffix + '.stderr')
        err.write_bytes(b'')
        return {'argv': argv, 'exit_code': 0, 'stdout_sha256': digest(output), 'stderr_sha256': digest(err)}

    def run(self):
        return m.inspect(self.root, self.candidate, self.reports, self.root / 'out', 'never-executed-java', self.tool, self.tool)

    def alter_report(self, key, value):
        document = json.loads(self.reports[0].read_text())
        document[key] = value
        self.reports[0].write_text(json.dumps(document))


class Review(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=OUT)
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(Path(self.temp.name))
        self.mock = patch.object(m, 'command', self.f.command)
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def test_positive_five_exports_retains_nonapproval_flags(self):
        result = self.f.run()
        self.assertEqual(len(result['artifacts']), 5)
        self.assertIs(result['release_acceptance'], False)
        self.assertIs(result['runtime_traffic_observed'], False)
        self.assertIs(result['store_disclosure_approved'], False)
        for row in result['artifacts']:
            report = json.loads(Path(row['build_report']).read_text())
            self.assertEqual(row['artifact_sha256'], report['results'][row['platform']]['artifact_sha256'])
        self.assertEqual(result['collector_sha256'], digest(self.f.root / 'out/collector.py'))

    def test_preexisting_artifact_drift_rejects(self):
        self.f.artifacts[0].write_bytes(b'changed before validation')
        with self.assertRaisesRegex(ValueError, 'artifact hash/size'):
            self.f.run()

    def test_different_candidate_report_rejects(self):
        self.f.alter_report('candidate_fingerprint', 'f' * 64)
        with self.assertRaisesRegex(ValueError, 'different artifact candidate'):
            self.f.run()

    def test_source_lock_truthy_string_rejects(self):
        self.f.alter_report('source_snapshot_unchanged', 'true')
        with self.assertRaisesRegex(ValueError, 'source/locks'):
            self.f.run()

    def test_duplicate_report_identity_rejects(self):
        self.f.reports.insert(1, self.f.reports[0])
        with self.assertRaisesRegex(ValueError, 'duplicate platform/mode'):
            self.f.run()

    def test_inflight_artifact_mutation_must_reject(self):
        original = m.selected_members
        changed = False
        def collect(archive):
            nonlocal changed
            result = original(archive)
            if not changed:
                changed = True
                self.f.artifacts[0].write_bytes(b'changed after successful original hash and member decoding')
            return result
        with patch.object(m, 'selected_members', collect):
            try:
                result = self.f.run()
            except ValueError:
                return
        row = result['artifacts'][0]
        report = json.loads(Path(row['build_report']).read_text())
        (OUT / 'accepted-artifact-drift.json').write_text(json.dumps({'published_artifact_sha256': row['artifact_sha256'], 'expected_build_report_sha256': report['results']['ios']['artifact_sha256'], 'published_member_sha256': row['members'][0]['sha256'], 'report_accepted': True}, indent=2) + '\n')
        self.fail('Collector published artifact hash differing from its successful build report after in-flight mutation')

    def test_inflight_candidate_source_mutation_must_reject(self):
        def decoder(argv, output):
            self.f.source.write_text('changed during manifest decoding')
            return self.f.command(argv, output)
        with patch.object(m, 'command', decoder):
            try:
                result = self.f.run()
            except ValueError:
                return
        (OUT / 'accepted-source-drift.json').write_text(json.dumps({'reported_candidate': result['candidate_fingerprint'], 'source_hash_at_end': digest(self.f.source), 'expected_source_hash': json.loads((self.f.candidate / 'manifest.json').read_text())['source_sha256']['app/source.dart'], 'report_accepted': True}, indent=2) + '\n')
        self.fail('Collector published candidate source identity after pinned source changed during decoding')

    def test_inflight_collector_mutation_must_not_repin_preserved_copy(self):
        collector = self.f.root / 'review-owned-collector.py'
        collector.write_bytes(Path(m.__file__).read_bytes())
        def decoder(argv, output):
            collector.write_text('# changed collector source, never executed\n')
            return self.f.command(argv, output)
        with patch.object(m, '__file__', str(collector)), patch.object(m, 'command', decoder):
            try:
                result = self.f.run()
            except ValueError:
                return
        actual = digest(self.f.root / 'out/collector.py')
        if actual == result['collector_sha256']:
            return
        (OUT / 'accepted-collector-drift.json').write_text(json.dumps({'published_collector_sha256': result['collector_sha256'], 'preserved_collector_sha256': actual, 'report_accepted': True}, indent=2) + '\n')
        self.fail('Published collector hash does not identify preserved collector.py')


if __name__ == '__main__':
    unittest.main(verbosity=2)
