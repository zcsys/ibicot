"""Different-author Python-only probes; no Flutter/native/device invocation.
Set TIDEGLASS_REVIEW_WORKSPACE to the frozen prospective integrated workspace.
"""
import ast
import copy
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

WORKSPACE = Path(os.environ['TIDEGLASS_REVIEW_WORKSPACE']).resolve()
sys.path.insert(0, str(WORKSPACE / 'tool'))
import verify_current_runtime as v


def context(scenario='runtime-study-enroll', platform='ios'):
    return dict(verification_id='synthetic-context-review', candidate_fingerprint='a' * 64,
                harness_sha256='b' * 64, device='F05BE4B0-52C1-4CA1-B721-BD64AE559E3F',
                label='review', platform=platform, scenario=scenario, run_id='review-only')


def observation(platform='ios', pid=123, stamp=1792584000000):
    return dict(version=1, status='available', source='native_process_observation_v1',
                native_pid=pid, platform=platform, application_id='dev.tideglass.game',
                application_version='0.1.0', application_build='1', observed_start_utc_ms=stamp)


def payload(c):
    p = dict(v.identities(c), completed=True, process_id=123,
             fixture_kind='INTERNAL SYNTHETIC QUALIFICATION ONLY', checks=['review fixture'])
    p['native_study_samples'] = 0 if c['scenario'] in {'runtime-study-default', 'runtime-study-withdraw-reopen'} else 1
    if p['native_study_samples']:
        p['native_study_process_context'] = observation(c['platform'])
    if c['scenario'] == 'runtime-study-withdraw-reopen':
        p.update(withdrawal_durable=True, preparation_verification_id='previous',
                 preparation_checkpoint_sha256='d' * 64, previous_native_process_id=122)
    return p


def checkpoint(c):
    return dict(candidate_fingerprint=c['candidate_fingerprint'], harness_sha256=c['harness_sha256'],
                device_label=c['label'], run_id=c['run_id'], preparation_verification_id=c['verification_id'],
                native_process_id=123, study_process_id='3' * 32,
                native_process_observation=observation(c['platform']), first_record_sha256='c' * 64)


def seal(raw):
    previous = v.study_adjudicate.digest(raw['registry'])
    for i, event in enumerate(raw['records']):
        event['seq'] = i
        event['previous_sha256'] = previous
        event.pop('sha256', None)
        event['sha256'] = v.study_adjudicate.digest(event)
        previous = event['sha256']
    return raw


def fixtures(c, *, pid=123):
    eligibility = dict(schema_version=1, check='no_prior_game_directory_entries', checked_at='2026-10-21T12:00:00Z',
                       study_id='synthetic-context-review', candidate_sha256=c['candidate_fingerprint'])
    registry = dict(install_id='1' * 32, first_launch=1792584000, enrolled_at=1792584000,
                    synthetic=True, acquisition='internal_test', study_id='synthetic-context-review', platform=c['platform'],
                    eligibility_evidence_sha256=v.study_adjudicate.digest(eligibility),
                    baseline=dict(candidate_sha256=c['candidate_fingerprint'], economy_sha256='e' * 64,
                                  content_sha256='f' * 64, config='synthetic_native_qualification'))
    event = dict(seq=0, event_id='2' * 32, at=registry['first_launch'], process_id='3' * 32, session_id='4' * 32,
                 kind='app_start', payload=dict(config=registry['baseline'], reason='enrollment', native_context=observation(c['platform'], pid)))
    raw = seal(dict(schema_version=2, registry=registry, records=[event], status='active'))
    return raw, eligibility


def archive(raw, eligibility, c, directory, marker=None):
    data = {'support/tideglass-study.json': json.dumps(raw).encode() if raw is not None else None,
            'support/tideglass-study-eligibility.json': json.dumps(eligibility).encode() if eligibility is not None else None,
            'support/tideglass-study.json.withdrawn': marker}
    host = Mock()
    host.read_fixture.side_effect = lambda root, relative, **kwargs: data[relative]
    return v.archive_fixture(host, '/exact/synthetic/fixture', c, directory)


class NativeContextReview(unittest.TestCase):
    def test_payload_positive_both_platforms(self):
        for platform in ('ios', 'android'):
            c = context(platform=platform)
            self.assertEqual(v.payload_errors(payload(c), c), [])

    def test_payload_context_exact_types_fields_and_identity(self):
        c = context()
        p = payload(c)
        for key, bad in [('version', True), ('version', 1.0), ('native_pid', 123.0), ('native_pid', True),
                         ('observed_start_utc_ms', True), ('observed_start_utc_ms', 1792584000000.0),
                         ('observed_start_utc_ms', -1), ('observed_start_utc_ms', 2**53),
                         ('platform', 'android'), ('application_id', 'other.app'), ('application_version', '1.0.0'),
                         ('application_build', 1), ('status', 'unavailable')]:
            with self.subTest(key=key, bad=bad):
                altered = copy.deepcopy(p)
                altered['native_study_process_context'][key] = bad
                self.assertTrue(v.payload_errors(altered, c))
        for mode in ('extra', 'missing'):
            altered = copy.deepcopy(p)
            if mode == 'extra': altered['native_study_process_context']['uptime'] = 12
            else: del altered['native_study_process_context']['source']
            self.assertTrue(v.payload_errors(altered, c))

    def test_checkpoint_positive_and_nested_type_rejections(self):
        c = context()
        good = checkpoint(c)
        self.assertEqual(v.validate_checkpoint(json.dumps(good).encode(), c, 123), good)
        for key, bad in [('version', 1.0), ('native_pid', 123.0), ('application_build', 1), ('observed_start_utc_ms', True)]:
            altered = copy.deepcopy(good)
            altered['native_process_observation'][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_checkpoint(json.dumps(altered).encode(), c, 123)

    def test_checkpoint_top_level_pid_must_be_integer(self):
        c = context()
        good = checkpoint(c)
        v.validate_checkpoint(json.dumps(good).encode(), c, 123)
        bad = dict(good, native_process_id=123.0)
        with self.assertRaises(ValueError):
            v.validate_checkpoint(json.dumps(bad).encode(), c, 123)

    def test_zero_sample_payload_must_not_contain_collected_context(self):
        c = context('runtime-study-default')
        good = payload(c)
        self.assertEqual(v.payload_errors(good, c), [])
        bad = dict(good, native_study_process_context=observation())
        self.assertTrue(v.payload_errors(bad, c), 'A zero-sampling result must not also retain an available observation')

    def test_archive_requires_host_pid_before_any_read(self):
        with TemporaryDirectory() as temp:
            host = Mock()
            for value in (None, True, 123.0, 0):
                c = dict(context(), native_process_id=value)
                with self.subTest(value=value), self.assertRaises(ValueError):
                    v.archive_fixture(host, '/fixture', c, Path(temp))
            host.read_fixture.assert_not_called()

    def test_native_archive_positive_both_platforms(self):
        for platform in ('ios', 'android'):
            c = dict(context(platform=platform), native_process_id=123)
            raw, proof = fixtures(c)
            with TemporaryDirectory() as temp:
                result = archive(raw, proof, c, Path(temp))
                self.assertEqual(result['study_structure']['records'], 1)
                self.assertEqual(result['study_structure']['logical_processes'], 1)

    def test_native_archive_rejects_schema1_contextless_and_wrong_pid(self):
        for case in ('legacy', 'wrong_pid'):
            c = dict(context(), native_process_id=123)
            raw, proof = fixtures(c)
            if case == 'legacy':
                raw['schema_version'] = 1
                del raw['records'][0]['payload']['native_context']
            else:
                raw['records'][0]['payload']['native_context']['native_pid'] = 124
            seal(raw)
            with TemporaryDirectory() as temp, self.subTest(case=case), self.assertRaises(ValueError):
                archive(raw, proof, c, Path(temp))

    def test_raw_native_event_time_boundary_is_real_decoder_checked(self):
        c = dict(context(), native_process_id=123)
        for offset, accepted in ((5000, True), (-5000, True), (5001, False), (-5001, False)):
            raw, proof = fixtures(c)
            raw['records'][0]['payload']['native_context']['observed_start_utc_ms'] += offset
            seal(raw)
            with TemporaryDirectory() as temp, self.subTest(offset=offset):
                if accepted: archive(raw, proof, c, Path(temp))
                else:
                    with self.assertRaisesRegex(ValueError, 'identity/time'):
                        archive(raw, proof, c, Path(temp))

    def test_raw_typed_versions_and_removed_uptime_rejected(self):
        c = dict(context(), native_process_id=123)
        for field, value in [('schema_version', 2.0), ('version', 1.0), ('native_pid', 123.0), ('observed_start_utc_ms', True), ('uptime', 10)]:
            raw, proof = fixtures(c)
            if field == 'schema_version': raw[field] = value
            else: raw['records'][0]['payload']['native_context'][field] = value
            seal(raw)
            with TemporaryDirectory() as temp, self.subTest(field=field), self.assertRaises(ValueError):
                archive(raw, proof, c, Path(temp))

    def test_actual_archive_checks_latest_start_not_first(self):
        c = dict(context('runtime-study-restart'), native_process_id=124)
        raw, proof = fixtures(c)
        second = copy.deepcopy(raw['records'][0])
        second.update(event_id='5'*32, process_id='6'*32, session_id='7'*32, at=1792584001)
        second['payload'].update(reason='process_restart', native_context=observation(pid=124, stamp=1792584001000))
        raw['records'].append(second)
        seal(raw)
        with TemporaryDirectory() as temp:
            self.assertEqual(archive(raw, proof, c, Path(temp))['study_structure']['logical_processes'], 2)
        with TemporaryDirectory() as temp, self.assertRaisesRegex(ValueError, 'host native process'):
            archive(raw, proof, dict(c, native_process_id=123), Path(temp))

    def test_actual_archive_default_and_withdrawal_no_context_required(self):
        with TemporaryDirectory() as temp:
            c = dict(context('runtime-study-default'), native_process_id=123)
            self.assertTrue(archive(None, None, c, Path(temp))['study_structure']['default_files_absent'])
        raw = dict(schema_version=2, registry=None, records=[], status='withdrawn')
        c = dict(context('runtime-study-withdraw-reopen'), native_process_id=123)
        with TemporaryDirectory() as temp:
            self.assertTrue(archive(raw, None, c, Path(temp), b'stop')['study_structure']['withdrawal_tombstone_verified'])
        with TemporaryDirectory() as temp, self.assertRaises(ValueError):
            archive(raw, None, c, Path(temp))

    def test_raw_archive_rejects_unknown_unavailable_as_actual_available(self):
        c = dict(context(), native_process_id=123)
        raw, proof = fixtures(c)
        raw['records'][0]['payload']['native_context'] = dict(version=1, status='unavailable', reason='native_unavailable')
        gap = copy.deepcopy(raw['records'][0])
        gap.update(event_id='5'*32, kind='gap', payload=dict(reason='instrumentationUnavailable', **{'from':1792584000, 'to':1792584000}))
        raw['records'].append(gap)
        seal(raw)
        with TemporaryDirectory() as temp, self.assertRaisesRegex(ValueError, 'host native process'):
            archive(raw, proof, c, Path(temp))

    def test_native_diagnostics_transitive_source_is_pinned(self):
        tree = ast.parse(Path(v.__file__).read_text())
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run')
        assign = next(node for node in ast.walk(run) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id=='sources' for t in node.targets))
        keys = {k.value for k in assign.value.keys if isinstance(k, ast.Constant)}
        self.assertIn('study_native_diagnostics.py', keys)


if __name__ == '__main__':
    unittest.main(verbosity=2)
