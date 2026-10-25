"""Python-only rejection probes: no Flutter, simulator, or physical device calls."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

import verify_current_runtime as v

GOOD_LOG = 'flutter: 00:05 +1: All tests passed!\nAll tests passed.\n'
DEVICE = 'F05BE4B0-52C1-4CA1-B721-BD64AE559E3F'


def context(scenario='runtime-lock-exclusion', **updates):
    value = dict(verification_id='current-runtime-phone-fixture', candidate_fingerprint='a' * 64,
                 harness_sha256='b' * 64, device=DEVICE, label='phone', platform='ios',
                 scenario=scenario, run_id='synthetic-unit')
    value.update(updates)
    return value


def native_observation(c, native_pid=123):
    return dict(version=1, status='available', source='native_process_observation_v1',
                native_pid=native_pid, platform=c['platform'], application_id=v.BUNDLE,
                application_version='0.1.0', application_build='1', observed_start_utc_ms=100000)


def payload(c):
    result = dict(v.identities(c), completed=True, process_id=123,
                  fixture_kind='INTERNAL SYNTHETIC QUALIFICATION ONLY', checks=['Actual fixture assertion'])
    if c['scenario'].startswith('runtime-study-'):
        result['native_study_samples'] = 0 if c['scenario'] in ('runtime-study-default', 'runtime-study-withdraw-reopen') else 1
        if result['native_study_samples']:
            result['native_study_process_context'] = native_observation(c)
    return result


def checkpoint(c):
    return dict(candidate_fingerprint=c['candidate_fingerprint'], harness_sha256=c['harness_sha256'],
                device_label=c['label'], run_id=c['run_id'], preparation_verification_id=c['verification_id'],
                native_process_id=123, stage=c['scenario'].rsplit('-', 1)[1])


def marker(c):
    return dict(verification_id=c['verification_id'], candidate_fingerprint=c['candidate_fingerprint'],
                harness_sha256=c['harness_sha256'], scenario=c['scenario'], process_id=123,
                checkpoint='/fixture/checkpoint.json', checkpoint_sha256='c' * 64)


def marker_log(m):
    return 'flutter: TIDEGLASS_RUNTIME_KILL_READY ' + json.dumps(m) + '\n'


def ledger(c, log=None):
    raw = (log if log is not None else marker_log(marker(c))).encode()
    return dict(identity_validated=True, termination_observed=True, native_process_id=123,
                device=c['device'], action='SIGKILL', signal_sent=True, after_alive=False,
                before_alive=True, pre_kill_log_bytes=len(raw), pre_kill_log_sha256=v.digest(raw), observations=[{'observed': 'matching process alive'}, {'observed': 'matching process absent'}])


class CurrentRuntimeVerificationTests(unittest.TestCase):
    def test_current_context_observation_and_sampling_are_required(self):
        c = context('runtime-study-enroll')
        p = payload(c)
        self.assertEqual(v.payload_errors(p, c), [])
        for key, value in [('native_pid', 124), ('version', True), ('platform', 'android'),
                           ('application_build', 'other'), ('observed_start_utc_ms', 1.0)]:
            bad = dict(p, native_study_process_context=dict(p['native_study_process_context'], **{key: value}))
            self.assertTrue(v.payload_errors(bad, c), key)
        self.assertTrue(v.payload_errors(dict(p, native_study_samples=0), c))
        self.assertTrue(v.payload_errors(dict(p, native_study_process_context=None), c))
        default = context('runtime-study-default')
        self.assertEqual(v.payload_errors(payload(default), default), [])
        self.assertTrue(v.payload_errors(dict(payload(default), native_study_samples=1), default))

    def test_protected_tablet_rejected_before_any_external_process(self):
        with patch.object(v.subprocess, 'run') as run, patch.object(v.subprocess, 'Popen') as popen:
            for device in (v.PROTECTED_DEVICE, v.PROTECTED_DEVICE.lower()):
                with self.assertRaisesRegex(ValueError, 'Protected tablet'):
                    v.run(SimpleNamespace(device=device, label='tablet', scenario='runtime-study-default', run_id='r'))
            run.assert_not_called()
            popen.assert_not_called()

    def test_request_allowlist_and_simulator_only(self):
        self.assertEqual(v.validate_request(DEVICE, 'phone', 'runtime-lock-exclusion', 'r1'), 'ios')
        self.assertEqual(v.validate_request('emulator-5556', 'android', 'runtime-cache-grace', 'r1'), 'android')
        for device, label, scenario, run_id in [('physical-device', 'p', 'runtime-lock-exclusion', 'r'),
                (DEVICE, '../p', 'runtime-lock-exclusion', 'r'), (DEVICE, 'p', 'made-up', 'r'),
                (DEVICE, 'p', 'runtime-study-default', '')]:
            with self.assertRaises(ValueError):
                v.validate_request(device, label, scenario, run_id)

    def test_harness_allowlist_matches_all_18_scenarios(self):
        installed = v.ROOT / 'game/mobile/integration_test/current_runtime_test.dart'
        staged = v.ROOT / 'release/native-proof/current-runtime-preparation/staged/current_runtime_test.dart'
        source = (installed if installed.is_file() else staged).read_text()
        block = source.split('const allowedScenarios = <String>{', 1)[1].split('};', 1)[0]
        cases = {line.strip().strip("',") for line in block.splitlines() if line.strip()}
        self.assertEqual(cases, v.SCENARIOS)
        self.assertEqual(len(cases), 18)

    def test_android_path_requires_exact_private_fixture(self):
        c = context('runtime-save-hold-afterFlush', platform='android', device='emulator-5556')
        good = '/data/user/0/dev.tideglass.game/files/native-current-verification/phone-synthetic-unit/save-afterFlush'
        self.assertEqual(v.fixture_path(good, c), Path(good))
        for bad in [good + '/../save-afterFlush', good.replace('synthetic-unit', 'another'), good.replace('dev.tideglass.game', 'another.app'), '/sdcard/' + good, good.replace('save-afterFlush', 'study')]:
            with self.assertRaises(ValueError):
                v.fixture_path(bad, c)

    def test_ios_path_requires_current_container_and_rejects_symlink(self):
        with TemporaryDirectory() as temp, TemporaryDirectory() as outside:
            good = Path(temp) / 'Library/Application Support/native-current-verification/phone-synthetic-unit/study'
            good.mkdir(parents=True)
            c = context('runtime-study-enroll')
            self.assertEqual(v.fixture_path(str(good), c, temp), good.resolve())
            with self.assertRaises(ValueError):
                v.fixture_path(str(good), c, outside)
            good.rmdir()
            good.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                v.fixture_path(str(good), c, temp)

    def test_marker_requires_real_native_prefix_one_occurrence_and_exact_identity(self):
        c = context('runtime-save-hold-beforeWrite')
        m = marker(c)
        self.assertEqual(v.marker_from_log(marker_log(m), c), m)
        self.assertEqual(v.marker_from_log(marker_log(m).replace('flutter:', 'I/flutter ( 123):'), c), m)
        for log in [marker_log(m).replace('flutter:', 'quoted:'), marker_log(m) * 2,
                    'flutter: EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\n' + marker_log(m)]:
            with self.assertRaises(ValueError):
                v.marker_from_log(log, c)
        for key, bad in [('verification_id', 'other'), ('harness_sha256', 'd' * 64), ('candidate_fingerprint', 'd' * 64), ('scenario', 'runtime-study-crash-hold'), ('process_id', True), ('process_id', 0), ('checkpoint_sha256', 'no')]:
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                v.marker_from_log(marker_log(dict(m, **{key: bad})), c)

    def test_checkpoint_binds_commit_stage_and_preparation(self):
        c = context('runtime-save-hold-afterRename')
        good = checkpoint(c)
        self.assertEqual(v.validate_checkpoint(json.dumps(good).encode(), c, 123), good)
        for key, bad in [('native_process_id', 124), ('stage', 'afterFlush'), ('run_id', 'old'), ('preparation_verification_id', 'old')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_checkpoint(json.dumps(dict(good, **{key: bad})).encode(), c, 123)
        with self.assertRaises(ValueError):
            v.validate_checkpoint(b' ' * 65537, c, 123)

    def test_study_checkpoint_requires_logical_process_and_retained_record_hash(self):
        c = context('runtime-study-crash-hold')
        base = checkpoint(c)
        with self.assertRaisesRegex(ValueError, 'logical study process'):
            v.validate_checkpoint(json.dumps(base).encode(), c, 123)
        base.update(study_process_id='synthetic-logical', first_record_sha256='d' * 64, native_process_observation=native_observation(c))
        self.assertEqual(v.validate_checkpoint(json.dumps(base).encode(), c, 123), base)

    def test_interrupted_preparation_never_accepts_success_or_unobserved_kill(self):
        c = context('runtime-study-crash-hold')
        m, host = marker(c), ledger(c)
        self.assertEqual(v.interrupted_errors(marker_log(m), c, m, host), [])
        self.assertTrue(v.interrupted_errors(marker_log(m) + GOOD_LOG, c, m, host))
        for key, bad in [('identity_validated', False), ('termination_observed', False), ('native_process_id', 124),
                         ('device', 'other'), ('action', 'force-stop'), ('signal_sent', False),
                         ('after_alive', True), ('before_alive', False), ('observations', [])]:
            with self.subTest(key=key):
                self.assertTrue(v.interrupted_errors(marker_log(m), c, m, dict(host, **{key: bad})))

    def test_post_marker_pre_kill_failure_is_rejected_but_lost_connection_after_kill_is_separate(self):
        c = context('runtime-study-crash-hold')
        m = marker(c)
        good = marker_log(m)
        for failure in ['flutter: EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\n',
                        'E/flutter ( 123): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: callback\n']:
            bad = good + failure
            with TemporaryDirectory() as temp, self.assertRaisesRegex(ValueError, 'complete host-observed'):
                v.bind_pre_kill_prefix(bad.encode(), c, Path(temp), {})
            self.assertTrue(v.interrupted_errors(bad, c, m, ledger(c, bad)))
        valid_after = good + 'Lost connection to device.\nDriver error after externally observed termination.\n'
        self.assertEqual(v.interrupted_errors(valid_after, c, m, ledger(c, good)), [])
        self.assertTrue(v.interrupted_errors(valid_after, c, m, dict(ledger(c), pre_kill_log_sha256='d' * 64)))
        with TemporaryDirectory() as temp:
            bound = {}
            v.bind_pre_kill_prefix(good.encode(), c, Path(temp), bound)
            self.assertEqual((Path(temp) / 'pre-kill.log').read_bytes(), good.encode())
            self.assertEqual(bound['pre_kill_log_sha256'], v.digest(good.encode()))

    def test_actual_ios_kill_is_bound_to_executable_and_exact_pid(self):
        host = v.NativeHost.__new__(v.NativeHost)
        host.context, host.observations = context('runtime-study-crash-hold'), []
        host.identity, host.wait_absent = Mock(return_value=True), Mock(return_value=False)
        with patch.object(v.os, 'kill') as kill:
            result = host.kill(123, before_signal=lambda record: record.update(pre_kill_log_sha256='synthetic'))
            kill.assert_called_once_with(123, v.signal.SIGKILL)
        self.assertTrue(result['termination_observed'])
        host.identity = Mock(return_value=False)
        with patch.object(v.os, 'kill') as kill, self.assertRaisesRegex(ValueError, 'not the declared'):
            host.kill(123)
        kill.assert_not_called()

    def test_ios_identity_cannot_match_another_app_or_device_container(self):
        host = v.NativeHost.__new__(v.NativeHost)
        host.context, host.app_container = context(), '/simulator/this-device/app/Runner.app'
        host.command = Mock(return_value=b'/simulator/this-device/app/Runner.app/Runner\n')
        self.assertTrue(host.identity(123))
        host.command = Mock(return_value=b'/simulator/other-device/app/Runner.app/Runner\n')
        self.assertFalse(host.identity(123))

    def test_android_identity_requires_pid_and_exact_cmdline(self):
        host = v.NativeHost.__new__(v.NativeHost)
        host.context, host.adb = context(platform='android', device='emulator-5556'), '/fixture/adb'
        host.command = Mock(side_effect=[b'123\n', b'dev.tideglass.game\0'])
        self.assertTrue(host.identity(123))
        host.command = Mock(side_effect=[b'123\n', b'dev.tideglass.game:other\0'])
        self.assertFalse(host.identity(123))
        host.command = Mock(return_value=b'456\n')
        self.assertFalse(host.identity(123))
        self.assertEqual(host.command.call_count, 1)

    def test_normal_payload_requires_identity_completed_and_concrete_checks(self):
        c = context()
        p = payload(c)
        self.assertEqual(v.payload_errors(p, c), [])
        for key, bad in [('harness_sha256', 'old'), ('verification_id', 'old'), ('completed', False), ('process_id', True),
                         ('fixture_kind', 'real participants'), ('checks', []), ('checks', [False]), ('expected_interruption', True)]:
            with self.subTest(key=key):
                self.assertTrue(v.payload_errors(dict(p, **{key: bad}), c))

    def test_recovery_requires_checkpoint_link_different_native_pid_and_exact_amounts(self):
        c = context('runtime-save-recover-afterRename')
        prior = dict(verification_id='prepare', checkpoint_sha256='c' * 64, native_process_id=122)
        p = dict(payload(c), preparation_verification_id='prepare', preparation_checkpoint_sha256='c' * 64,
                 previous_native_process_id=122, recovered_stage='afterRename', save_loaded_amount=1, save_after_recovery_amount=2)
        self.assertEqual(v.payload_errors(p, c, prior), [])
        self.assertTrue(v.payload_errors(p, c))
        for key, bad in [('process_id', 122), ('preparation_checkpoint_sha256', 'd' * 64), ('recovered_stage', 'afterFlush'),
                         ('save_loaded_amount', 0), ('save_loaded_amount', True), ('save_after_recovery_amount', 1)]:
            with self.subTest(key=key):
                self.assertTrue(v.payload_errors(dict(p, **{key: bad}), c, prior))

    def test_transition_distinguishes_old_settlement_and_new_rules_reopen(self):
        c = context('runtime-transition-start')
        p = dict(payload(c), lifetime_micros='90000000', default_predecessor_registration=False, same_cursor_reopen_checked=False)
        self.assertEqual(v.payload_errors(p, c), [])
        self.assertTrue(v.payload_errors(dict(p, lifetime_micros='60000000'), c))
        self.assertTrue(v.payload_errors(dict(p, default_predecessor_registration=True), c))

    def test_capacity_and_cache_bounds_cannot_be_claimed_without_results(self):
        c = context('runtime-study-capacity')
        p = dict(payload(c), study_capacity_gap=True, study_capacity_records=8, study_capacity_bytes=10000)
        self.assertEqual(v.payload_errors(p, c), [])
        for key, bad in [('study_capacity_records', 9), ('study_capacity_bytes', 32769), ('study_capacity_gap', False)]:
            self.assertTrue(v.payload_errors(dict(p, **{key: bad}), c))
        c = context('runtime-cache-grace')
        self.assertTrue(v.payload_errors(payload(c), c))
        self.assertEqual(v.payload_errors(dict(payload(c), cache_limits=dict(exports=3, bytes=192*1024*1024, grace_seconds=86400)), c), [])

    def test_existing_strict_completion_rejects_known_false_positives(self):
        self.assertEqual(v.verify_native.native_log_errors(GOOD_LOG), [])
        for bad in ['All tests passed.\n', GOOD_LOG.replace('+1', '+0'), 'Some tests failed.\n' + GOOD_LOG,
                    GOOD_LOG + 'E/flutter ( 123): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: late teardown\n']:
            self.assertTrue(v.verify_native.native_log_errors(bad))

    def make_predecessor(self, directory):
        c = context('runtime-save-hold-afterFlush')
        c['harness_sha256'] = v.digest(b'synthetic harness')
        raw = json.dumps(checkpoint(c)).encode()
        m = marker(c)
        m['checkpoint_sha256'] = v.digest(raw)
        files = {'checkpoint.json': raw, 'harness.dart': b'synthetic harness', 'run.log': marker_log(m).encode(), 'pre-kill.log': marker_log(m).encode(),
                 'runner.py': Path(v.__file__).read_bytes(), 'build_native.py': b'fixture helper',
                 'verify_native.py': b'fixture helper', 'driver.dart': b'fixture driver', 'generation-0.json': b'{"fixture":0}'}
        for name, data in files.items():
            (directory / name).write_bytes(data)
        prior = dict(c, status='expected-interrupted', passed=False, production_input_differences_after_run=[],
                     source_snapshot_unchanged=True, verification_errors=[], checkpoint_sha256=v.digest(raw), native_process_id=123,
                     kill_marker=m, native_kill=ledger(c, marker_log(m)), evidence_sha256={n: v.digest(b) for n, b in files.items()},
                     generations={'generation-0.json': {'size': len(files['generation-0.json']), 'sha256': v.digest(files['generation-0.json'])}})
        path = directory / 'verification.json'
        path.write_text(json.dumps(prior))
        current = dict(c, scenario='runtime-save-recover-afterFlush', verification_id='recovery')
        return path, prior, current

    def test_predecessor_replays_kill_and_pins_exact_generation_bytes(self):
        with TemporaryDirectory() as temp:
            path, prior, c = self.make_predecessor(Path(temp))
            self.assertEqual(v.validate_predecessor(path, c), prior)
            (Path(temp) / 'generation-0.json').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'evidence changed'):
                v.validate_predecessor(path, c)

    def test_normal_predecessor_replays_framework_driver_payload_and_observed_stop(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            c = context('runtime-transition-start', harness_sha256=v.digest(b'synthetic harness'))
            raw = json.dumps(checkpoint(c)).encode()
            data = dict(payload(c), lifetime_micros='90000000', default_predecessor_registration=False, same_cursor_reopen_checked=False)
            files = {'checkpoint.json': raw, 'harness.dart': b'synthetic harness', 'run.log': GOOD_LOG.encode(),
                     'runner.py': Path(v.__file__).read_bytes(), 'build_native.py': b'fixture helper',
                     'verify_native.py': b'fixture helper', 'driver.dart': b'fixture driver',
                     'generation-0.json': b'fixture generation', 'result.json': json.dumps(data).encode()}
            prior = dict(c, status='passed', passed=True, exit_code=0, verification_errors=[],
                         production_input_differences_after_run=[], source_snapshot_unchanged=True,
                         native_process_id=123, checkpoint_sha256=v.digest(raw), native_process_stop={'termination_observed': True},
                         generations={'generation-0.json': {'size': len(files['generation-0.json']), 'sha256': v.digest(files['generation-0.json'])}})
            def write():
                for name, content in files.items():
                    (folder / name).write_bytes(content)
                prior['evidence_sha256'] = {name: v.digest(content) for name, content in files.items()}
                (folder / 'verification.json').write_text(json.dumps(prior))
            write()
            current = dict(c, scenario='runtime-transition-reopen', verification_id='recovery')
            self.assertEqual(v.validate_predecessor(folder / 'verification.json', current), prior)
            files['run.log'] = (GOOD_LOG + 'E/flutter ( 123): Unhandled Exception: late teardown\n').encode()
            write()
            with self.assertRaisesRegex(ValueError, 'native/driver completion'):
                v.validate_predecessor(folder / 'verification.json', current)
            files['run.log'] = GOOD_LOG.encode()
            files['result.json'] = json.dumps(dict(data, completed=False)).encode()
            write()
            with self.assertRaisesRegex(ValueError, 'harness result'):
                v.validate_predecessor(folder / 'verification.json', current)
            files['result.json'] = json.dumps(data).encode()
            prior['native_process_stop']['termination_observed'] = False
            write()
            with self.assertRaisesRegex(ValueError, 'termination was not observed'):
                v.validate_predecessor(folder / 'verification.json', current)

    def test_predecessor_mismatch_cannot_be_reused_for_another_candidate_or_run(self):
        with TemporaryDirectory() as temp:
            path, prior, c = self.make_predecessor(Path(temp))
            for key, bad in [('candidate_fingerprint', 'd' * 64), ('harness_sha256', 'd' * 64), ('device', 'emulator-5556'),
                             ('run_id', 'other'), ('scenario', 'runtime-save-recover-beforeWrite')]:
                with self.subTest(key=key), self.assertRaises(ValueError):
                    v.validate_predecessor(path, dict(c, **{key: bad}))

    def test_predecessor_cannot_relabel_killed_test_passed(self):
        with TemporaryDirectory() as temp:
            path, prior, c = self.make_predecessor(Path(temp))
            for change in [dict(status='passed', passed=True), dict(native_kill=dict(ledger(c), termination_observed=False)),
                           dict(generations={}), dict(checkpoint_sha256='d' * 64), dict(verification_errors=['failure']),
                           dict(generations={'generation-0.json': {'size': 1, 'sha256': 'd' * 64}})]:
                path.write_text(json.dumps(dict(prior, **change)))
                with self.subTest(change=change), self.assertRaises(ValueError):
                    v.validate_predecessor(path, c)

    def native_study_files(self, directory, c):
        eligibility = {'schema_version': 1, 'check': 'no_prior_game_directory_entries',
                       'checked_at': '2026-10-21T12:00:00Z', 'study_id': 'synthetic-native-study',
                       'candidate_sha256': c['candidate_fingerprint']}
        epoch = 1792584000
        registry = {'install_id': '1' * 32, 'first_launch': epoch, 'enrolled_at': epoch,
                    'synthetic': True, 'acquisition': 'internal_test', 'study_id': 'synthetic-native-study',
                    'eligibility_evidence_sha256': v.study_adjudicate.digest(eligibility),
                    'baseline': {'candidate_sha256': c['candidate_fingerprint'], 'economy_sha256': 'e' * 64,
                                 'content_sha256': 'f' * 64, 'config': 'synthetic_native_qualification'}}
        event = {'seq': 0, 'event_id': '2' * 32, 'at': epoch, 'process_id': '3' * 32, 'session_id': '4' * 32,
                 'kind': 'app_start', 'payload': {'config': registry['baseline'], 'reason': 'enrollment'},
                 'previous_sha256': v.study_adjudicate.digest(registry)}
        event['sha256'] = v.study_adjudicate.digest(event)
        raw = {'schema_version': 1, 'registry': registry, 'records': [event], 'status': 'active'}
        (directory / 'study-raw.json').write_text(json.dumps(raw))
        (directory / 'study-eligibility.json').write_text(json.dumps(eligibility))
        return raw

    def artifact_pins(self, directory):
        result = {}
        for name in v.STUDY_FILES:
            file = directory / name
            data = file.read_bytes() if file.is_file() else None
            result[name] = dict(present=data is not None, size=len(data) if data is not None else 0,
                                sha256=v.digest(data) if data is not None else None)
        return result

    def test_native_study_raw_chain_and_eligibility_are_independently_decoded(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            c = context('runtime-study-enroll')
            raw = self.native_study_files(directory, c)
            result = v.inspect_study_artifacts(directory, c, self.artifact_pins(directory))
            self.assertEqual(result['decoded_sessions'], 1)
            raw['records'][0]['sha256'] = 'd' * 64
            (directory / 'study-raw.json').write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, 'Broken raw chain'):
                v.inspect_study_artifacts(directory, c, self.artifact_pins(directory))

    def test_native_study_archive_refuses_non_synthetic_or_wrong_candidate(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            c = context('runtime-study-enroll')
            for field, value in [('synthetic', False), ('acquisition', 'organic')]:
                raw = self.native_study_files(directory, c)
                raw['registry'][field] = value
                (directory / 'study-raw.json').write_text(json.dumps(raw))
                with self.assertRaisesRegex(ValueError, 'non-synthetic'):
                    v.inspect_study_artifacts(directory, c, self.artifact_pins(directory))
            self.native_study_files(directory, c)
            with self.assertRaisesRegex(ValueError, 'configuration differs'):
                v.inspect_study_artifacts(directory, dict(c, candidate_fingerprint='d' * 64), self.artifact_pins(directory))

    def test_native_study_default_absence_and_durable_withdrawal_are_distinct(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            self.assertTrue(v.inspect_study_artifacts(directory, context('runtime-study-default'), self.artifact_pins(directory))['default_files_absent'])
            raw = {'schema_version': 1, 'registry': None, 'records': [], 'status': 'withdrawn'}
            (directory / 'study-raw.json').write_text(json.dumps(raw))
            (directory / 'study-withdrawn.marker').write_text('stop')
            c = context('runtime-study-withdraw-reopen')
            self.assertTrue(v.inspect_study_artifacts(directory, c, self.artifact_pins(directory))['withdrawal_tombstone_verified'])
            with self.assertRaisesRegex(ValueError, 'Default study path'):
                v.inspect_study_artifacts(directory, context('runtime-study-default'), self.artifact_pins(directory))
            (directory / 'study-eligibility.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'sidecar'):
                v.inspect_study_artifacts(directory, c, self.artifact_pins(directory))

    def test_study_artifact_pins_detect_replaced_bytes_or_unpinned_file(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            c = context('runtime-study-enroll')
            self.native_study_files(directory, c)
            pins = self.artifact_pins(directory)
            (directory / 'study-raw.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                v.inspect_study_artifacts(directory, c, pins)
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                v.inspect_study_artifacts(directory, c, {})

    def test_study_capture_reads_only_allowlisted_paths_with_limits(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            c = context('runtime-study-default')
            host = Mock()
            host.read_fixture.return_value = None
            result = v.archive_fixture(host, '/fixture/study', dict(c, native_process_id=123), directory)
            self.assertTrue(result['study_structure']['default_files_absent'])
            self.assertEqual(host.read_fixture.call_count, 3)
            self.assertEqual({call.args[1] for call in host.read_fixture.call_args_list}, {entry[0] for entry in v.STUDY_FILES.values()})
            for call in host.read_fixture.call_args_list:
                self.assertTrue(call.kwargs['optional'])
                self.assertLessEqual(call.kwargs['limit'], 2 * 1024 * 1024)

    def test_workspace_integrity_catches_native_entrypoint_and_dependency_drift(self):
        with TemporaryDirectory() as temp:
            candidate = Path(temp)
            path = 'game/mobile/ios/Runner/AppDelegate.swift'
            file = candidate / 'workspace' / path
            file.parent.mkdir(parents=True)
            file.write_text('original')
            pins = {path: v.digest(file.read_bytes())}
            self.assertEqual(v.source_differences(candidate, pins), [])
            file.write_text('changed')
            self.assertEqual(v.source_differences(candidate, pins), [path])


if __name__ == '__main__':
    unittest.main()
