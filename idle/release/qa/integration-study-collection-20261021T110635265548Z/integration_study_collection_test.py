"""Adversarial raw-study boundaries against an explicitly pinned tool tree."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(os.environ['STUDY_COLLECTION_SOURCE'])
sys.path.insert(0, str(SOURCE/'tool'))
import study_adjudicate as adjudicator


class CollectionReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        fixtures = SOURCE/'release/study/fixtures/collection-v1'
        self.protocol = json.loads((fixtures/'protocol.json').read_text())
        self.protocol_hash = hashlib.sha256((fixtures/'protocol.json').read_bytes()).hexdigest()
        self.counter = 1000
        self.entry = copy.deepcopy(json.loads((fixtures/'registry.json').read_text())['entries'][0])
        self.entry['protocol_sha256'] = self.protocol_hash
        self.proof = self.evidence(b'independent synthetic eligibility fixture')
        self.entry['eligibility_evidence_sha256'] = self.proof
        self.entry['enrolled_at'] = self.entry['first_launch'] = 100
        self.registry = {'schema_version': 1, 'study_id': self.protocol['study_id'], 'synthetic': True, 'entries': [self.entry]}
        self.document = {'schema_version': 1, 'registry': copy.deepcopy(self.entry), 'records': [], 'status': 'active'}
        self.raw = {'schema_version': 1, 'study_id': self.protocol['study_id'], 'synthetic': True, 'exports': [{'install_id': self.entry['install_id'], 'raw': self.document}]}
        self.review = {'schema_version': 1, 'study_id': self.protocol['study_id'], 'synthetic': True, 'cutoff': 32*86400, 'installs': [{'install_id': self.entry['install_id'], 'eligibility_review': 'qualified', 'eligibility_evidence_sha256': self.proof, 'exclusion': None, 'coverage': []}], 'native_crashes': [], 'terminal_reviews': []}
        self.process, self.session = self.identity(), self.identity()
        self.event('app_start', 100, {'config': self.protocol['baseline'], 'reason': 'enrollment'})

    def identity(self):
        self.counter += 1
        return f'{self.counter:032x}'

    def evidence(self, data):
        h = hashlib.sha256(data).hexdigest()
        (self.folder/(h+'.evidence')).write_bytes(data)
        return h

    def event(self, kind, at, payload):
        rows = self.document['records']
        value = {'seq': len(rows), 'event_id': self.identity(), 'at': at, 'process_id': self.process, 'session_id': self.session, 'kind': kind, 'payload': payload, 'previous_sha256': rows[-1]['sha256'] if rows else adjudicator.digest(self.entry)}
        value['sha256'] = adjudicator.digest(value)
        rows.append(value)
        return value

    def analyze(self):
        return adjudicator.adjudicate(self.protocol, self.registry, self.raw, self.review, protocol_sha256=self.protocol_hash, evidence_dir=self.folder)

    def test_terminal_cannot_be_followed_by_same_process_inactivity_restart(self):
        self.event('terminal', 101, {'reason': 'explicitlyObservedCleanExit'})
        self.session = self.identity()
        self.event('session_start', 1900, {'config': self.protocol['baseline'], 'reason': 'inactivity'})
        self.event('harbor_interactive', 1900, {})
        self.event('activity', 1900, {'activity': 'interaction'})
        with self.assertRaises(ValueError):
            self.analyze()

    def test_background_only_inactivity_start_cannot_create_valid_session(self):
        self.event('background', 101, {})
        self.session = self.identity()
        self.event('session_start', 1900, {'config': self.protocol['baseline'], 'reason': 'inactivity'})
        with self.assertRaises(ValueError):
            self.analyze()

    def test_crash_cannot_cross_later_restart_with_equal_second_timestamp(self):
        original_process, original_session = self.process, self.session
        self.process, self.session = self.identity(), self.identity()
        self.event('app_start', 100, {'config': self.protocol['baseline'], 'reason': 'process_restart'})
        self.review['native_crashes'] = [{'install_id': self.entry['install_id'], 'session_id': original_session, 'process_id': original_process, 'crash_at': 101, 'report_sha256': self.evidence(b'independent synthetic native crash report'), 'linkage_reviewed': True}]
        with self.assertRaises(ValueError):
            self.analyze()

    def test_crash_exact_next_restart_boundary_is_rejected(self):
        original_process, original_session = self.process, self.session
        self.process, self.session = self.identity(), self.identity()
        self.event('app_start', 101, {'config': self.protocol['baseline'], 'reason': 'process_restart'})
        self.review['native_crashes'] = [{'install_id': self.entry['install_id'], 'session_id': original_session, 'process_id': original_process, 'crash_at': 101, 'report_sha256': self.evidence(b'independent synthetic native crash report'), 'linkage_reviewed': True}]
        with self.assertRaises(ValueError):
            self.analyze()

    def test_exact_clock_gap_preserves_positive_pre_gap_return_but_removes_coverage(self):
        self.process, self.session = self.identity(), self.identity()
        day7 = 100 + 7*86400
        self.event('app_start', day7, {'config': self.protocol['baseline'], 'reason': 'process_restart'})
        self.event('harbor_interactive', day7, {})
        self.event('activity', day7, {'activity': 'interaction'})
        self.event('gap', day7+1, {'reason': 'clockDiscontinuity', 'from': day7, 'to': None})
        self.document['status'] = 'exhausted'
        self.review['installs'][0]['coverage'] = [{'start': 100, 'end': self.review['cutoff'], 'evidence_sha256': self.evidence(b'independent synthetic observation coverage')}]
        data, _ = self.analyze()
        self.assertEqual(data['installs'][0]['observable_intervals'], [[100, day7]])
        self.assertTrue(data['sessions'][-1]['return_eligible'])
        self.assertIsNone(data['sessions'][-1]['end'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
