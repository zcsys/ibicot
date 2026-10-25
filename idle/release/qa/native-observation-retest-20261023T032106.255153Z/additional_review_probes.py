"""Independent current-source and finalization probes; disposable files only."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE = ROOT / 'release/native-privacy/runtime-observation-repaired'
spec = importlib.util.spec_from_file_location('review_fixture', STAGE / 'test_runtime_observation.py')
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
o = author.o


class CurrentSourceReview(unittest.TestCase):
    def fixture(self, directory):
        return author.FinalizationTests().prepare(Path(directory).resolve())

    def test_late_native_failures_cannot_be_overridden_by_cached_verifier(self):
        failures = [
            'flutter: 00:21 +1: native teardown [E]\n',
            'E/flutter ( 123): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: actual late failure\n',
            'flutter: EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\n',
            'Some tests failed.\n',
        ]
        for error in failures:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory:
                evidence, output, verification = self.fixture(directory)
                raw = (evidence / 'run.log').read_bytes() + error.encode()
                (evidence / 'run.log').write_bytes(raw)
                verification['evidence_sha256']['run.log'] = o.sha(raw)
                (evidence / 'verification.json').write_text(json.dumps(verification))
                fake = types.SimpleNamespace(native_log_errors=lambda _: [])
                with patch.dict(sys.modules, {'verify_native': fake}):
                    with self.assertRaisesRegex(ValueError, 'completion failed'):
                        o.finalize(output, Path('/unrelated-unread-root'))
                self.assertFalse((output / 'finalization.json').exists())

    def test_current_collector_replacement_during_decision_prevents_output(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = self.fixture(directory)
            live_copy = Path(directory).resolve() / 'live-collector.py'
            live_copy.write_bytes(o.COLLECTOR_BYTES)
            original = o.archived_completion_errors

            def changed_during_decision(source, log):
                result = original(source, log)
                live_copy.write_bytes(o.COLLECTOR_BYTES + b'\n# MUTATED LIVE SOURCE\n')
                return result

            with patch.object(o, 'COLLECTOR_PATH', live_copy), patch.object(o, 'archived_completion_errors', changed_during_decision):
                with self.assertRaisesRegex(ValueError, 'Collector source changed'):
                    o.finalize(output, ROOT)
            self.assertFalse((output / 'finalization.json').exists())

    def test_candidate_verifier_replacement_during_decision_prevents_output(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = self.fixture(directory)
            report = json.loads((output / 'observation.json').read_text())
            path = Path(report['candidate']) / 'source/tool/verify_native.py'
            original = o.archived_completion_errors

            def changed_during_decision(source, log):
                result = original(source, log)
                path.write_bytes(path.read_bytes() + b'\n# MUTATED CANDIDATE VERIFIER\n')
                return result

            with patch.object(o, 'archived_completion_errors', changed_during_decision):
                with self.assertRaisesRegex(ValueError, 'Candidate source drift'):
                    o.finalize(output, ROOT)
            self.assertFalse((output / 'finalization.json').exists())

    def test_decision_input_mutations_are_checked_before_publish(self):
        for target in ('observation.json', 'verification.json', 'result.json', 'run.log'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                evidence, output, _ = self.fixture(directory)
                path = (output if target == 'observation.json' else evidence) / target
                original = o.archived_completion_errors

                def changed_during_decision(source, log):
                    result = original(source, log)
                    path.write_bytes(path.read_bytes() + b'\n')
                    return result

                with patch.object(o, 'archived_completion_errors', changed_during_decision):
                    with self.assertRaisesRegex(ValueError, 'Finalization input changed'):
                        o.finalize(output, ROOT)
                self.assertFalse((output / 'finalization.json').exists())

    def test_archive_check_does_not_import_module_top_level_or_root(self):
        source = b'raise RuntimeError("must not execute module body")\n\ndef native_log_errors(log):\n    return [] if re.fullmatch("VALID", log) else ["bad"]\n'
        self.assertEqual(o.archived_completion_errors(source, 'VALID'), [])
        self.assertEqual(o.archived_completion_errors(source, 'INVALID'), ['bad'])
        for bad in [b'def different(log): return []\n', b'def native_log_errors(log): return []\ndef native_log_errors(log): return []\n', b'@decorator\ndef native_log_errors(log): return []\n']:
            with self.assertRaises(ValueError): o.archived_completion_errors(bad, 'VALID')

    def test_missing_storage_remains_partial_and_immutable_finalization(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = self.fixture(directory)
            path = output / 'observation.json'
            report = json.loads(path.read_text())
            report['samples'][0]['storage'] = {'status': 'unavailable', 'reason': 'No qualified Android storage reader'}
            path.write_text(json.dumps(report))
            final = o.finalize(output, ROOT)
            self.assertEqual(final['status'], 'finalized-partial-observation')
            self.assertEqual(final['paired_socket_storage_samples'], 0)
            self.assertFalse(final['release_acceptance'])
            self.assertFalse(final['traffic_absence_claim'])
            raw = (output / 'finalization.json').read_bytes()
            with self.assertRaisesRegex(ValueError, 'already exists'):
                o.finalize(output, ROOT)
            self.assertEqual((output / 'finalization.json').read_bytes(), raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
