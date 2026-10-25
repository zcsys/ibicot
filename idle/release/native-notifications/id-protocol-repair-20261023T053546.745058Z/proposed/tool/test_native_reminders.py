"""Verifier rejection checks only; these fixtures never qualify OS behavior."""
import copy
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import verify_native_reminders as verify

GOOD_LOG = 'flutter: 00:06 +1: All tests passed!\nAll tests passed.\n'


def specimen(scenario):
    context = {'verification_id': 'native-evidence-1', 'candidate_fingerprint': 'a'*64,
               'harness_sha256': 'b'*64, 'scenario': scenario, 'run_id': 'one',
               'device_label': 'ios-phone', 'platform': 'ios'}
    actions = [{**context, 'process_id': 42, 'utc_ms': 1000000+i,
                'action': name} for i, name in enumerate(verify.ACTIONS[scenario])]
    value = {**context, 'process_id': 42, 'completed': True,
             'gateway': 'NativeNotificationGateway', 'preference_store': 'FileNotificationPreferences',
             'fixture_kind': 'SYNTHETIC GAMEPLAY SNAPSHOT; REAL OS NOTIFICATION API',
             'clock': 'actual_utc_and_monotonic_stopwatch', 'default_opted_out': True,
             'default_preferences_file_absent': True, 'default_pending_ids': [],
             'permission_before_initialize': 'denied', 'permission_after_initialize': 'denied',
             'initialization_lifecycle_events': [], 'lifecycle_events': [
                 {'state': 'paused', 'utc_ms': 1000010}, {'state': 'resumed', 'utc_ms': 1360000}],
             'actions': actions}
    if scenario != 'default':
        value.update(permission_after_opt_in='denied' if scenario == 'denied' else 'allowed',
                     preferences_after_opt_in={'enabled': scenario != 'denied'}, preferences_sha256='c'*64)
    if scenario == 'denied': value['denied_pending_ids'] = []
    if scenario in {'quiet-cancel', 'delivery', 'revoked'}:
        value['plan'] = {'ids': [77101], 'kinds': ['focus'], 'production_lifecycle': True,
                         'body': 'A Focus charge is ready.', 'zone': 'UTC',
                         'background_call_utc_ms': 1000010, 'scheduled_observed_utc_ms': 1000020,
                         'due_utc_ms': 1360000, 'settled_through_utc_ms': 1000010,
                         'saved_payload_sha256': 'd'*64, 'saved_snapshot_id': 'saved-one'}
    if scenario == 'quiet-cancel':
        value.update(quiet_window={'zone': 'UTC', 'start_minute': 60, 'end_minute': 120},
                     quiet_due_local_minute=120, return_pending_ids=[])
    if scenario == 'revoked':
        value.update(permission_after_revoke='denied', revoke_pending_ids=[], revoked_opt_in_stays_disabled=True)
    if scenario == 'delivery':
        value.update(actual_background_and_return=True, return_pending_ids=[], return_active_ids=[],
                     delivered_records=[{'id': 77101, 'body': value['plan']['body']}],
                     returned_utc_ms=1360000, returned_elapsed_ms=360000, scheduled_elapsed_ms=20)
    return context, value


def log_for(value):
    return ''.join('flutter: TIDEGLASS_REMINDER_ACTION ' + json.dumps(x) + '\n' for x in value['actions']) + GOOD_LOG


class ReminderVerifierTests(unittest.TestCase):
    def test_exact_positive_shapes_for_all_five_scenarios(self):
        for scenario in sorted(verify.SCENARIOS):
            with self.subTest(scenario=scenario):
                context, value = specimen(scenario)
                self.assertEqual(verify.payload_errors(value, context, log_for(value)), [])

    def test_protected_target_and_physical_device_refusal(self):
        for device in [verify.PROTECTED_DEVICE, verify.PROTECTED_DEVICE.lower(), 'R58-device', 'emulator-1;rm', 'macos']:
            with self.subTest(device=device), self.assertRaises(ValueError):
                verify.validate_request(device, 'phone', 'default', 'fresh')
        self.assertEqual(verify.validate_request('emulator-5554', 'phone', 'default', 'fresh'), 'android')
        self.assertEqual(verify.validate_request('01234567-1234-1234-1234-123456789abc', 'phone', 'default', 'fresh'), 'ios')

    def test_invalid_or_reused_identity_shape(self):
        for label, scenario, run in [('bad/path', 'default', 'one'), ('phone','fake','one'), ('phone','default','')]:
            with self.assertRaises(ValueError):
                verify.validate_request('emulator-5554', label, scenario, run)
        context, value = specimen('delivery'); value['candidate_fingerprint'] = 'e'*64
        self.assertTrue(verify.payload_errors(value, context, log_for(value)))

    def test_default_cannot_request_permission_or_write_optin(self):
        context, value = specimen('default')
        for key, bad in [('default_preferences_file_absent', False), ('permission_after_initialize', 'allowed'),
                         ('initialization_lifecycle_events', [{'state':'inactive','utc_ms':1}]), ('default_pending_ids', [77101])]:
            changed = copy.deepcopy(value); changed[key] = bad
            self.assertTrue(verify.payload_errors(changed, context, log_for(changed)), key)

    def test_completed_true_native_and_driver_markers_are_all_required(self):
        context, value = specimen('default')
        for bad in [False, 1, None]:
            changed=copy.deepcopy(value); changed['completed']=bad
            self.assertTrue(verify.payload_errors(changed, context, GOOD_LOG))
        for bad in ['All tests passed.\n', 'flutter: 00:00 +0: All tests passed!\nAll tests passed.\n',
                    GOOD_LOG+'flutter: Unhandled Exception: late\n', GOOD_LOG+'flutter: 00:05 +1: teardown [E]\n']:
            self.assertTrue(verify.payload_errors(value, context, bad))

    def test_stale_quoted_duplicate_or_missing_actions_fail(self):
        context, value = specimen('delivery'); log = log_for(value)
        for bad in [GOOD_LOG, 'UI says '+log, log.replace('native-evidence-1','another-run'), log+log]:
            self.assertTrue(verify.payload_errors(value, context, bad))

    def test_scheduled_pending_is_not_actual_delivery(self):
        context, value = specimen('delivery'); value['delivered_records']=[]
        self.assertTrue(verify.payload_errors(value, context, log_for(value)))
        value['delivered_records']=[{'id':77101,'body':'Different notification'}]
        self.assertTrue(verify.payload_errors(value, context, log_for(value)))

    def test_five_minute_production_plan_cannot_be_shortened(self):
        context, value = specimen('delivery'); value['plan']['due_utc_ms']=1005000
        self.assertTrue(verify.payload_errors(value, context, log_for(value)))

    def test_wall_clock_and_monotonic_delivery_both_required(self):
        context, value = specimen('delivery')
        for key, bad in [('returned_utc_ms',1359999), ('returned_elapsed_ms',30000), ('scheduled_elapsed_ms', True)]:
            changed=copy.deepcopy(value);changed[key]=bad
            self.assertTrue(verify.payload_errors(changed, context, log_for(changed)), key)

    def test_permission_dialog_lifecycle_cannot_stand_in_for_delivery(self):
        context, value = specimen('delivery')
        value['lifecycle_events']=[{'state':'paused','utc_ms':1},{'state':'resumed','utc_ms':2}]
        self.assertTrue(verify.payload_errors(value, context, log_for(value)))

    def test_quiet_hour_and_cancel_evidence_cannot_be_faked_by_plan_presence(self):
        context, value = specimen('quiet-cancel'); value['quiet_due_local_minute']=65
        self.assertTrue(verify.payload_errors(value, context, log_for(value)))
        context,value=specimen('delivery');value['return_active_ids']=[77101]
        self.assertTrue(verify.payload_errors(value, context, log_for(value)))

    def test_revoked_requires_actual_settings_return_and_denial(self):
        context, value=specimen('revoked')
        for key,bad in [('permission_after_revoke','allowed'),('lifecycle_events',[]),('revoke_pending_ids',[77101])]:
            changed=copy.deepcopy(value);changed[key]=bad
            self.assertTrue(verify.payload_errors(changed,context,log_for(changed)),key)

    def test_changed_production_and_installed_artifact_are_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'lib.dart';p.write_text('before');pins={'lib.dart':verify.sha(p)}
            self.assertEqual(verify.production_differences(root,pins),[])
            p.write_text('after');self.assertEqual(verify.production_differences(root,pins),['lib.dart'])
            with patch.object(verify,'call',side_effect=['package:/data/app/synthetic/base.apk\n', 'f'*64+'  /data/app/synthetic/base.apk\n']):
                with self.assertRaises(ValueError):
                    verify.installed_artifact_check(root,'android','emulator-5554',{'host.apk':'a'*64})


    def test_final_missing_input_and_os_timeout_are_retained(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp); (base/'source').mkdir(); report={}; errors=[]
            with patch.object(verify.subprocess, 'run', side_effect=subprocess.TimeoutExpired('stop', 20)):
                verify.finish_observations(report, errors, candidate=base, frozen={}, workspace=base,
                    production={}, sources={'harness.dart':base/'missing.dart'},
                    pins={'harness.dart':'a'*64,'driver.dart':'b'*64},
                    target=base/'missing.dart', driver=base/'missing-driver.dart',
                    platform='ios', device='01234567-1234-1234-1234-123456789abc')
            self.assertTrue(errors)
            self.assertEqual(report['source_differences_during_run'], ['harness.dart'])
            self.assertIs(report['generated_harness_matches'], False)
            self.assertEqual(report['stop']['observation_error'], 'TimeoutExpired')
            # The caller can serialize a failed report rather than losing it.
            path=base/'verification.json';path.write_text(json.dumps({**report,'passed':False,'errors':errors}))
            self.assertIs(json.loads(path.read_text())['passed'], False)

    def test_hash_failure_does_not_skip_remaining_final_observations(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp); (base/'source').mkdir(); file=base/'file';file.write_text('x')
            report={};errors=[]
            with patch.object(verify,'sha',side_effect=OSError('read disappeared')), patch.object(
                    verify.subprocess,'run',return_value=subprocess.CompletedProcess(['stop'],0,'','')):
                verify.finish_observations(report,errors,candidate=base,frozen={},workspace=base,
                    production={'file':'a'*64},sources={'harness.dart':file},
                    pins={'harness.dart':'a'*64,'driver.dart':'b'*64},target=file,driver=file,
                    platform='ios',device='01234567-1234-1234-1234-123456789abc')
            self.assertTrue(errors)
            self.assertEqual(report['production_differences_after']['observation_error'],'OSError')
            self.assertEqual(report['stop']['exit_code'],0)


class ReminderIdentityProtocolTests(unittest.TestCase):
    """Real runner preparation, with native launch deliberately blocked."""
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.harness = (Path(__file__).resolve().parents[1] /
                        'game/mobile/integration_test/native_reminders_test.dart').read_bytes()
        # This reads the actual unchanged Dart consumer's ID constraint.
        expression = re.search(
            r"for \(final value in \[label, runId, verification\]\) \{\s*"
            r"expect\(RegExp\(r'([^']+)'\)\.hasMatch\(value\), isTrue\);",
            self.harness.decode())
        self.assertIsNotNone(expression)
        self.consumer = re.compile(expression.group(1))
        for name, data in {
            'game/mobile/integration_test/native_reminders_test.dart': self.harness,
            'tool/native_integration_driver.dart': b'// synthetic driver, never executed\n',
            'candidate/source/game/mobile/lib/probe.dart': b'// synthetic production source\n',
            'candidate/workspace/game/mobile/lib/probe.dart': b'// synthetic production source\n',
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.candidate = self.root / 'candidate'
        (self.candidate / 'workspace/game/mobile/integration_test').mkdir()
        frozen = verify.build_native.source_hashes(self.candidate / 'source')
        manifest = {'source_sha256': frozen,
                    'source_fingerprint': verify.build_native.fingerprint(frozen)}
        (self.candidate / 'manifest.json').write_text(json.dumps(manifest))

    def prepare(self, label='ios-phone', run='fresh',
                at=datetime(2026, 10, 23, 5, 31, 7, 547418, tzinfo=timezone.utc)):
        class FixedTime:
            @staticmethod
            def now(zone):
                self.assertEqual(zone, timezone.utc)
                return at
        args = ['verify_native_reminders.py', str(self.candidate), '--device',
                '01234567-1234-1234-1234-123456789abc', '--label', label,
                '--scenario', 'default', '--run-id', run]
        with patch.object(verify, 'ROOT', self.root), patch.object(verify, 'datetime', FixedTime), \
                patch('sys.argv', args), patch.object(verify, 'device_ready') as ready, \
                patch.object(verify.subprocess, 'Popen', side_effect=RuntimeError('HOST TEST: native launch blocked')) as launch, \
                patch.object(verify.subprocess, 'run', return_value=subprocess.CompletedProcess(['synthetic-stop'], 0, '', '')) as stop, \
                redirect_stdout(io.StringIO()):
            code = verify.main()
        self.assertEqual(code, 1)  # Blocked launch must never become a native pass.
        ready.assert_called_once()
        launch.assert_called_once()
        stop.assert_called_once()
        self.assertEqual(stop.call_args.args[0][:3], ['xcrun', 'simctl', 'terminate'])
        evidence = Path(launch.call_args.kwargs['env']['TIDEGLASS_NATIVE_EVIDENCE'])
        started = json.loads((evidence/'started.json').read_text())
        terminal = json.loads((evidence/'verification.json').read_text())
        self.assertFalse(terminal['passed'])
        self.assertIn('RuntimeError: HOST TEST: native launch blocked', terminal['errors'])
        return evidence, started, terminal, launch.call_args

    def test_generated_id_is_accepted_by_actual_unchanged_Dart_contract(self):
        evidence, started, terminal, launch = self.prepare()
        identity = started['verification_id']
        self.assertIsNotNone(self.consumer.fullmatch(identity))
        self.assertEqual(identity, evidence.name)
        self.assertEqual(terminal['verification_id'], identity)
        self.assertIn('--dart-define=TIDEGLASS_VERIFICATION_ID='+identity, started['command'])
        self.assertEqual(launch.kwargs['env']['TIDEGLASS_NATIVE_EVIDENCE'], str(evidence))
        self.assertEqual(started['harness_sha256'], verify.sha(evidence/'harness.dart'))
        self.assertEqual((evidence/'harness.dart').read_bytes(), self.harness)
        self.assertEqual(evidence.parent, self.root/'release/native-notifications')
        self.assertIsNone(self.consumer.fullmatch('integration-ios-phone-20261023T053107.547418Z'))

    def test_maximum_host_label_and_run_id_remain_inside_Dart_limit(self):
        evidence, started, _, _ = self.prepare(label='a'*80, run='z'*80)
        for key in ['verification_id', 'device_label', 'run_id']:
            self.assertIsNotNone(self.consumer.fullmatch(started[key]), key)
        self.assertLessEqual(len(evidence.name), 160)

    def test_utc_zero_microseconds_and_single_character_tokens(self):
        evidence, started, _, _ = self.prepare(label='x', run='y',
            at=datetime(2028, 2, 29, 0, 0, 0, 0, tzinfo=timezone.utc))
        self.assertIsNotNone(self.consumer.fullmatch(evidence.name))
        self.assertEqual(started['device_label'], 'x')
        self.assertEqual(started['run_id'], 'y')

    def test_existing_evidence_is_never_reused_or_overwritten(self):
        evidence, _, _, _ = self.prepare()
        before = {p.name: p.read_bytes() for p in evidence.iterdir() if p.is_file()}
        with self.assertRaises(FileExistsError):
            self.prepare(run='another-fresh-run')
        self.assertEqual({p.name: p.read_bytes() for p in evidence.iterdir() if p.is_file()}, before)

    def test_symlinked_evidence_target_is_refused_before_copying(self):
        evidence, _, _, _ = self.prepare()
        evidence.rename(evidence.with_name('retained-original'))
        outside = self.root/'outside'
        outside.mkdir()
        evidence.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(list(outside.iterdir()), [])

    def test_fractional_precision_still_distinguishes_fresh_evidence(self):
        first, _, _, _ = self.prepare()
        second, started, _, _ = self.prepare(run='second',
            at=datetime(2026, 10, 23, 5, 31, 7, 547419, tzinfo=timezone.utc))
        self.assertNotEqual(first, second)
        self.assertTrue(first.is_dir() and second.is_dir())
        self.assertEqual(started['verification_id'], second.name)
        self.assertIsNotNone(self.consumer.fullmatch(second.name))

    def test_unsafe_or_overlong_path_tokens_rejected_before_any_OS_action(self):
        bad = ['', '.', '..', '../escape', '/absolute', 'a/b', 'a\\b',
               'a.b', 'a b', 'a\n', 'a\x00', '%2f', 'ş', 'a'*81]
        with patch.object(verify, 'device_ready', side_effect=AssertionError('OS access forbidden')):
            for value in bad:
                for label, run in [(value, 'valid'), ('valid', value)]:
                    with self.subTest(label=label, run=run), self.assertRaises(ValueError):
                        verify.validate_request('emulator-5556', label, 'default', run)


if __name__ == '__main__':
    unittest.main()
