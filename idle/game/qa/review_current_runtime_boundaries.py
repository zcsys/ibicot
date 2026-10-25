"""Independent host-only review probes. No device, Flutter or native commands.

Set TIDEGLASS_REVIEW_TOOL_DIR to an archived source/tool directory to replay the
exact rejected revision. The default imports the current implementation for a
repair replay. Failing rejection assertions deliberately preserve real findings.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.environ.get('TIDEGLASS_REVIEW_TOOL_DIR', str(ROOT / 'tool')))
sys.path.append(str(ROOT / 'tool'))  # Archived verifier's unchanged helper imports.
import verify_current_runtime as v

DEVICE = 'F05BE4B0-52C1-4CA1-B721-BD64AE559E3F'


def context(scenario='runtime-study-crash-hold', **overrides):
    return dict(dict(verification_id='independent-synthetic-start',
                     candidate_fingerprint='a' * 64, harness_sha256='b' * 64,
                     device=DEVICE, label='phone', platform='ios',
                     scenario=scenario, run_id='independent-review'), **overrides)


def kill_fixture():
    c = context()
    marker = dict(verification_id=c['verification_id'],
                  candidate_fingerprint=c['candidate_fingerprint'],
                  harness_sha256=c['harness_sha256'], scenario=c['scenario'],
                  process_id=801, checkpoint='/synthetic/checkpoint.json',
                  checkpoint_sha256='c' * 64)
    prefix = 'flutter: TIDEGLASS_RUNTIME_KILL_READY ' + json.dumps(marker) + '\n'
    ledger = dict(identity_validated=True, termination_observed=True,
                  native_process_id=801, device=DEVICE, action='SIGKILL',
                  signal_sent=True, before_alive=True, after_alive=False,
                  observations=[{'synthetic_observation': 'alive'}, {'synthetic_observation': 'absent'}],
                  pre_kill_log_bytes=len(prefix.encode()),
                  pre_kill_log_sha256=v.digest(prefix.encode()))
    return c, marker, prefix, ledger


def prior_files(directory):
    c = context('runtime-save-hold-afterFlush', harness_sha256=v.digest(b'review fixture harness'))
    checkpoint = dict(candidate_fingerprint=c['candidate_fingerprint'],
                      harness_sha256=c['harness_sha256'], device_label=c['label'],
                      run_id=c['run_id'], preparation_verification_id=c['verification_id'],
                      native_process_id=801, stage='afterFlush')
    raw = json.dumps(checkpoint).encode()
    _, marker, _, ledger = kill_fixture()
    marker.update({key: c[key] for key in ('verification_id', 'candidate_fingerprint', 'harness_sha256', 'scenario')})
    marker['checkpoint_sha256'] = v.digest(raw)
    log = ('flutter: TIDEGLASS_RUNTIME_KILL_READY ' + json.dumps(marker) + '\n').encode()
    ledger.update(pre_kill_log_bytes=len(log), pre_kill_log_sha256=v.digest(log))
    files = {'run.log': log, 'pre-kill.log': log, 'checkpoint.json': raw,
             'harness.dart': b'review fixture harness', 'runner.py': Path(v.__file__).read_bytes(),
             'build_native.py': b'synthetic helper', 'verify_native.py': b'synthetic helper',
             'driver.dart': b'synthetic driver', 'generation-0.json': b'{"synthetic_amount":0}'}
    for name, data in files.items():
        (directory / name).write_bytes(data)
    prior = dict(c, status='expected-interrupted', passed=False,
                 production_input_differences_after_run=[], source_snapshot_unchanged=True,
                 verification_errors=[], checkpoint_sha256=v.digest(raw), native_process_id=801,
                 kill_marker=marker, native_kill=ledger,
                 evidence_sha256={name: v.digest(data) for name, data in files.items()},
                 generations={'generation-0.json': {'size': len(files['generation-0.json']),
                                                    'sha256': v.digest(files['generation-0.json'])}})
    path = directory / 'verification.json'
    path.write_text(json.dumps(prior))
    successor = dict(c, scenario='runtime-save-recover-afterFlush', verification_id='independent-synthetic-recovery')
    return path, prior, successor


def active_study(directory, c):
    evidence = dict(schema_version=1, check='no_prior_game_directory_entries',
                    checked_at='2026-10-21T12:00:00Z', study_id='independent-synthetic',
                    candidate_sha256=c['candidate_fingerprint'])
    epoch = 1792584000
    registry = dict(install_id='1' * 32, first_launch=epoch, enrolled_at=epoch,
                    synthetic=True, acquisition='internal_test', study_id='independent-synthetic',
                    eligibility_evidence_sha256=v.study_adjudicate.digest(evidence),
                    baseline=dict(candidate_sha256=c['candidate_fingerprint'], economy_sha256='d' * 64,
                                  content_sha256='e' * 64, config='independent_synthetic'))
    event = dict(seq=0, event_id='2' * 32, at=epoch, process_id='3' * 32, session_id='4' * 32,
                 kind='app_start', payload={'config': registry['baseline'], 'reason': 'enrollment'},
                 previous_sha256=v.study_adjudicate.digest(registry))
    event['sha256'] = v.study_adjudicate.digest(event)
    raw = dict(schema_version=1, registry=registry, records=[event], status='active')
    (directory / 'study-raw.json').write_text(json.dumps(raw))
    (directory / 'study-eligibility.json').write_text(json.dumps(evidence))
    return raw


def artifacts(directory):
    return {name: dict(present=(directory / name).exists(),
                       size=(directory / name).stat().st_size if (directory / name).exists() else 0,
                       sha256=v.digest((directory / name).read_bytes()) if (directory / name).exists() else None)
            for name in v.STUDY_FILES}


class IndependentCurrentRuntimeReview(unittest.TestCase):
    def setUp(self):
        # Every test refuses accidental external execution at the Python API.
        for method in ('run', 'Popen'):
            guard = patch.object(v.subprocess, method, side_effect=AssertionError('No external commands in review'))
            guard.start(); self.addCleanup(guard.stop)
        for method in ('kill', 'killpg'):
            guard = patch.object(v.os, method, side_effect=AssertionError('No native process actions in review'))
            guard.start(); self.addCleanup(guard.stop)

    def test_pre_kill_native_failures_rejected_positive_control(self):
        c, marker, prefix, ledger = kill_fixture()
        self.assertEqual(v.interrupted_errors(prefix, c, marker, ledger), [])
        for failure in ['E/flutter ( 801): Unhandled Exception: synthetic\n',
                        'flutter: EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\n']:
            with self.subTest(failure=failure), TemporaryDirectory() as temp:
                with self.assertRaises(ValueError):
                    v.bind_pre_kill_prefix((prefix + failure).encode(), c, Path(temp), {})

    def test_expected_post_kill_driver_disconnect_is_allowed_positive_control(self):
        c, marker, prefix, ledger = kill_fixture()
        self.assertEqual(v.interrupted_errors(prefix + 'Lost connection to device.\nDriver error after externally observed termination.\n', c, marker, ledger), [])

    def test_buffered_native_error_after_prefix_must_not_qualify_interruption(self):
        c, marker, prefix, ledger = kill_fixture()
        for failure in ['E/flutter ( 801): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: buffered native failure\n',
                        'flutter: EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\n',
                        'flutter: 00:03 +0 -1: teardown [E]\n']:
            with self.subTest(failure=failure):
                self.assertTrue(v.interrupted_errors(prefix + failure, c, marker, ledger),
                                'Buffered native/framework errors must not be discarded as driver disconnect cleanup.')

    def test_prefix_tamper_and_success_after_kill_are_rejected(self):
        c, marker, prefix, ledger = kill_fixture()
        self.assertTrue(v.interrupted_errors(prefix, c, marker, dict(ledger, pre_kill_log_sha256='d' * 64)))
        self.assertTrue(v.interrupted_errors(prefix + 'All tests passed.\n', c, marker, ledger))

    def test_protected_device_and_bad_pid_reject_without_external_execution(self):
        for device in [v.PROTECTED_DEVICE, v.PROTECTED_DEVICE.lower()]:
            with self.assertRaisesRegex(ValueError, 'Protected tablet'):
                v.run(type('Args', (), dict(device=device, label='phone', scenario='runtime-study-default', run_id='review'))())
        host = v.NativeHost.__new__(v.NativeHost)
        host.context = context()
        host.command = Mock(side_effect=AssertionError('Invalid PID reached command'))
        for pid in [True, 0, 1, -9, '801']:
            with self.assertRaises(ValueError): host.identity(pid)
        host.command.assert_not_called()

    def test_actual_identity_uses_selected_app_container_and_android_cmdline(self):
        host = v.NativeHost.__new__(v.NativeHost)
        host.context = context(); host.app_container = '/selected-device/Runner.app'
        host.command = Mock(return_value=b'/selected-device/Runner.app/Runner\n')
        self.assertTrue(host.identity(801))
        host.command = Mock(return_value=b'/other-device/Runner.app/Runner\n')
        self.assertFalse(host.identity(801))
        host.context = context(platform='android', device='emulator-5556'); host.adb = 'NO-DEVICE'
        host.command = Mock(side_effect=[b'801\n', b'dev.tideglass.game\0'])
        self.assertTrue(host.identity(801))
        host.command = Mock(side_effect=[b'801\n', b'dev.tideglass.game:other\0'])
        self.assertFalse(host.identity(801))

    def test_predecessor_same_candidate_linkage_and_raw_pin_rejection(self):
        with TemporaryDirectory() as temp:
            path, prior, c = prior_files(Path(temp))
            self.assertEqual(v.validate_predecessor(path, c), prior)
            for key, value in [('candidate_fingerprint', 'f' * 64), ('harness_sha256', 'f' * 64),
                               ('device', 'emulator-5556'), ('label', 'tablet'), ('run_id', 'other'),
                               ('scenario', 'runtime-save-recover-beforeWrite')]:
                with self.subTest(key=key), self.assertRaises(ValueError):
                    v.validate_predecessor(path, dict(c, **{key: value}))
            (Path(temp) / 'generation-0.json').write_bytes(b'changed bytes')
            with self.assertRaisesRegex(ValueError, 'evidence changed'):
                v.validate_predecessor(path, c)

    def test_recovery_payload_rejects_reused_process_or_wrong_checkpoint(self):
        c = context('runtime-save-recover-beforeWrite')
        prior = dict(verification_id='previous', checkpoint_sha256='c' * 64, native_process_id=801)
        payload = dict(v.identities(c), completed=True, process_id=802,
                       fixture_kind='INTERNAL SYNTHETIC QUALIFICATION ONLY', checks=['fixture check'],
                       preparation_verification_id='previous', preparation_checkpoint_sha256='c' * 64,
                       previous_native_process_id=801, recovered_stage='beforeWrite', save_loaded_amount=0,
                       save_after_recovery_amount=2)
        self.assertEqual(v.payload_errors(payload, c, prior), [])
        for key, value in [('process_id', 801), ('preparation_checkpoint_sha256', 'f' * 64),
                           ('previous_native_process_id', 999), ('save_loaded_amount', True)]:
            with self.subTest(key=key): self.assertTrue(v.payload_errors(dict(payload, **{key: value}), c, prior))

    def android_host(self, backing):
        host = v.NativeHost.__new__(v.NativeHost)
        host.context = context('runtime-save-hold-afterFlush', platform='android', device='emulator-5556')
        host.adb = 'MOCK-ONLY'; host.observations = []; host.data_container = None
        native = '/data/user/0/dev.tideglass.game/files/native-current-verification/phone-independent-review/save-afterFlush'
        def command(args, *, allow_failure=False):
            self.assertEqual(args[:6], ['MOCK-ONLY', '-s', 'emulator-5556', 'exec-out', 'run-as', v.BUNDLE])
            # Emulates only the allowlisted host reads on synthetic local files.
            # No shell subprocess is executed. Path.read_bytes follows links,
            # like the native `head` command under review.
            parts = args[6:]
            path = backing / parts[-1].lstrip('/')
            code = 0
            if parts[0] == 'head': data = path.read_bytes()[:int(parts[-2])]
            elif parts[0] == 'test':
                mode = path.stat().st_mode if path.exists() else 0
                okay = {'-e': path.exists(), '-L': path.is_symlink(), '-f': path.is_file(), '-d': path.is_dir(),
                        '-r': bool(mode & 0o444), '-x': bool(mode & 0o111)}[parts[1]]
                code = 0 if okay else 1; data = b''
            else: raise AssertionError('Review stub needs explicit support for new native inspection: ' + str(parts))
            host.observations.append(dict(command=args, exit_code=code, stdout=data.decode(errors='replace'), stderr=''))
            if code and not allow_failure: raise ValueError('Synthetic host command failed')
            return data
        host.command = command
        return host, native, backing / native.lstrip('/')

    def test_android_regular_fixture_read_positive_control(self):
        with TemporaryDirectory() as temp:
            host, native, directory = self.android_host(Path(temp))
            directory.mkdir(parents=True); (directory / 'checkpoint.json').write_bytes(b'SYNTHETIC FIXTURE')
            self.assertEqual(host.read_fixture(native, 'checkpoint.json'), b'SYNTHETIC FIXTURE')

    def test_android_file_symlink_must_not_copy_outside_fixture(self):
        with TemporaryDirectory() as temp:
            host, native, directory = self.android_host(Path(temp))
            directory.mkdir(parents=True)
            outside = Path(temp) / 'synthetic-ordinary-game.json'; outside.write_bytes(b'SYNTHETIC OUTSIDE FIXTURE')
            (directory / 'checkpoint.json').symlink_to(outside)
            with self.assertRaises(ValueError): host.read_fixture(native, 'checkpoint.json')

    def test_android_parent_symlink_must_not_copy_outside_fixture(self):
        with TemporaryDirectory() as temp:
            host, native, directory = self.android_host(Path(temp))
            directory.parent.mkdir(parents=True)
            outside = Path(temp) / 'synthetic-other-directory'; outside.mkdir()
            (outside / 'checkpoint.json').write_bytes(b'SYNTHETIC OUTSIDE FIXTURE')
            directory.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError): host.read_fixture(native, 'checkpoint.json')

    def test_android_optional_absence_is_distinct_from_required_or_dangling(self):
        with TemporaryDirectory() as temp:
            host, native, directory = self.android_host(Path(temp))
            directory.mkdir(parents=True)
            self.assertIsNone(host.read_fixture(native, 'checkpoint.json', optional=True))
            with self.assertRaises(ValueError): host.read_fixture(native, 'checkpoint.json')
            (directory / 'checkpoint.json').symlink_to(Path(temp) / 'missing-target')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                host.read_fixture(native, 'checkpoint.json', optional=True)

    def test_android_fifo_directory_and_unreadable_component_are_not_file_absence(self):
        with TemporaryDirectory() as temp:
            host, native, directory = self.android_host(Path(temp))
            directory.mkdir(parents=True); file = directory / 'checkpoint.json'
            os.mkfifo(file)
            with self.assertRaisesRegex(ValueError, 'type'): host.read_fixture(native, 'checkpoint.json', optional=True)
            file.unlink(); file.mkdir()
            with self.assertRaisesRegex(ValueError, 'type'): host.read_fixture(native, 'checkpoint.json')
            file.rmdir(); file.write_bytes(b'SYNTHETIC')
            directory.chmod(0o000)
            try:
                with self.assertRaisesRegex(ValueError, 'unreadable'): host.read_fixture(native, 'checkpoint.json', optional=True)
            finally: directory.chmod(0o700)
            directory.chmod(0o600)
            try:
                with self.assertRaisesRegex(ValueError, 'traversable'): host.read_fixture(native, 'checkpoint.json', optional=True)
            finally: directory.chmod(0o700)

    def test_android_top_fixture_component_symlink_and_oversize_rejected(self):
        with TemporaryDirectory() as temp:
            host, native, directory = self.android_host(Path(temp))
            directory.mkdir(parents=True); file = directory / 'checkpoint.json'
            file.write_bytes(b'0123456789')
            with self.assertRaisesRegex(ValueError, 'byte limit'): host.read_fixture(native, 'checkpoint.json', limit=5)
            fixture_root = directory.parent.parent
            moved = fixture_root.with_name('outside-synthetic-fixture')
            fixture_root.rename(moved); fixture_root.symlink_to(moved, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'): host.read_fixture(native, 'checkpoint.json')

    def test_ios_fixture_symlink_rejected_positive_control(self):
        with TemporaryDirectory() as temp, TemporaryDirectory() as outside:
            c = context('runtime-study-enroll')
            directory = Path(temp) / 'Library/Application Support/native-current-verification/phone-independent-review/study'
            directory.parent.mkdir(parents=True); directory.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError): v.fixture_path(str(directory), c, temp)

    def test_native_study_decodes_and_rejects_raw_chain_or_eligibility_changes(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp); c = context('runtime-study-enroll')
            raw = active_study(directory, c)
            self.assertEqual(v.inspect_study_artifacts(directory, c, artifacts(directory))['decoded_sessions'], 1)
            raw['records'][0]['sha256'] = 'f' * 64
            (directory / 'study-raw.json').write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, 'Broken raw chain'):
                v.inspect_study_artifacts(directory, c, artifacts(directory))
            active_study(directory, c)
            (directory / 'study-eligibility.json').write_text('{}')
            with self.assertRaises(ValueError): v.inspect_study_artifacts(directory, c, artifacts(directory))

    def test_study_rejects_foreign_candidate_and_real_participant_data(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp); c = context('runtime-study-enroll')
            raw = active_study(directory, c)
            with self.assertRaisesRegex(ValueError, 'configuration differs'):
                v.inspect_study_artifacts(directory, dict(c, candidate_fingerprint='f' * 64), artifacts(directory))
            raw['registry']['synthetic'] = False
            (directory / 'study-raw.json').write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, 'non-synthetic'):
                v.inspect_study_artifacts(directory, c, artifacts(directory))

    def test_default_absence_and_full_erasure_require_actual_sidecars(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            self.assertTrue(v.inspect_study_artifacts(directory, context('runtime-study-default'), artifacts(directory))['default_files_absent'])
            c = context('runtime-study-withdraw-reopen')
            (directory / 'study-raw.json').write_text(json.dumps(dict(schema_version=1, registry=None, records=[], status='withdrawn')))
            with self.assertRaises(ValueError): v.inspect_study_artifacts(directory, c, artifacts(directory))
            # Empty marker is intentional: the production store treats presence
            # as a stop even after an interrupted marker write.
            (directory / 'study-withdrawn.marker').write_bytes(b'')
            self.assertTrue(v.inspect_study_artifacts(directory, c, artifacts(directory))['withdrawal_tombstone_verified'])
            (directory / 'study-eligibility.json').write_text('{}')
            with self.assertRaises(ValueError): v.inspect_study_artifacts(directory, c, artifacts(directory))


if __name__ == '__main__':
    unittest.main(verbosity=2)
