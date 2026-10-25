import copy
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('runtime_observation', HERE / 'runtime_observation.py')
o = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o)


def context():
    return dict(verification_id='proof-1', candidate_fingerprint='a'*64,
                harness_sha256='b'*64, scenario='runtime-study-default', run_id='run1',
                device_label='ios-phone', platform='ios')


def marker():
    return dict(context(), process_id=123, fixture_directory='/synthetic/study',
                mode='default-unprovisioned', window_id='proof-1-privacy',
                maximum_ms=20000, native_elapsed_us=2, native_utc_ms=100000)


class IdentityTests(unittest.TestCase):
    def test_protected_and_unapproved_refused_before_command(self):
        for device in [o.PROTECTED, o.PROTECTED.lower(), 'emulator-5554', 'anything', '']:
            with self.subTest(device=device), self.assertRaises(ValueError):
                o.Host('/nonexistent', device, marker(), run=lambda *a, **k: self.fail('external command'))

    def test_ios_exact_pid_executable_and_start(self):
        raw = b'123 501 Wed Oct 21 15:12:01 2026 /fixture/Runner.app/Runner\n'
        identity = o.parse_ios_identity(raw, 123, Path('/fixture/Runner.app/Runner'))
        self.assertEqual(identity['start'], 'Wed Oct 21 15:12:01 2026')
        for pid, path in [(124, '/fixture/Runner.app/Runner'), (123, '/other/Runner')]:
            with self.assertRaises(ValueError):
                o.parse_ios_identity(raw, pid, Path(path))

    def android(self, uid=10231, pid=123, ticks=99):
        stat = f'{pid} (tideglass) S ' + ' '.join(['0']*18 + [str(ticks)] + ['0']*10)
        status = f'Name:\ttideglass\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n'.encode()
        return [b'dev.tideglass.game\0', stat.encode(), status, pid, uid, '12345678-1234-1234-1234-123456789abc']

    def test_android_uid_package_pid_start_and_boot(self):
        args = self.android()
        parsed = o.parse_android_identity(*args)
        self.assertEqual(parsed['start_ticks'], 99)
        for index, value in [(0, b'other.app\0'), (3, 124), (4, 10232), (5, 'bad')]:
            altered = args[:]; altered[index] = value
            with self.subTest(index=index), self.assertRaises(ValueError):
                o.parse_android_identity(*altered)

    def test_reused_pid_changed_start_is_not_same_process(self):
        before = o.parse_android_identity(*self.android(ticks=99))
        after = o.parse_android_identity(*self.android(ticks=100))
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            o.attributed_sample(before, after, {'started_ns': 2, 'finished_ns': 3}, 1, 4)

    def test_changed_uid_or_boot_rejects_sample(self):
        baseline = o.parse_android_identity(*self.android())
        for key, value in [('uid', 10111), ('boot_id', 'another-boot')]:
            after = dict(baseline, **{key: value})
            with self.assertRaises(ValueError):
                o.attributed_sample(baseline, after, {'started_ns': 2, 'finished_ns': 3}, 1, 4)


class SocketTests(unittest.TestCase):
    def test_lsof_requires_exact_selected_pid(self):
        raw = b'p123\ncRunner\nu501\nf7\ntIPv4\nPTCP\nn127.0.0.1:3210\nTST=LISTEN\n'
        rows = o.parse_lsof(raw, 123)
        self.assertEqual(rows[0]['n'], ['127.0.0.1:3210'])
        with self.assertRaises(ValueError):
            o.parse_lsof(raw.replace(b'p123', b'p124'), 123)
        with self.assertRaises(ValueError):
            o.parse_lsof(b'f7\nnexample:443\n', 123)

    def test_android_requires_both_uid_and_pid_fd_inode(self):
        data = 'FD|1234\nTABLE|tcp\nSOCKET|tcp|10231|1234|0100007F:0010|00000000:0000|0A\nTABLE|tcp6\nTABLE|udp\nTABLE|udp6\n'
        self.assertEqual(len(o.parse_android_sockets(data.encode(), 10231)), 1)
        for bad in [data.replace('|10231|', '|10232|'), data.replace('FD|1234', 'FD|1235'), data.replace('TABLE|udp6\n', '')]:
            with self.assertRaises(ValueError):
                o.parse_android_sockets(bad.encode(), 10231)

    def test_complete_empty_snapshot_is_only_empty_rows(self):
        self.assertEqual(o.parse_android_sockets(b'TABLE|tcp\nTABLE|tcp6\nTABLE|udp\nTABLE|udp6\n', 10123), [])
        self.assertEqual(o.parse_lsof(b'', 123), [])
        self.assertIn('not packets', o.LIMITATIONS[0])

    @unittest.skipUnless(sys.platform == 'darwin', 'actual host lsof qualification requires macOS')
    def test_actual_owned_loopback_child_pid_socket(self):
        # This test creates its OWN short-lived child and loopback listener. It
        # does not select or inspect another user's process, devices or network.
        code = "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(); print(s.getsockname()[1],flush=True); time.sleep(10)"
        child = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE, text=True)
        try:
            port = int(child.stdout.readline())
            result = subprocess.run(['/usr/sbin/lsof', '-a', '-p', str(child.pid), '-i', '-nP', '-FpcufPtnT'], capture_output=True, timeout=2)
            self.assertEqual(result.returncode, 0)
            rows = o.parse_lsof(result.stdout, child.pid)
            self.assertTrue(any(f'127.0.0.1:{port}' in row.get('n', []) for row in rows))
            raw = subprocess.run(['/bin/ps', '-p', str(child.pid), '-o', 'pid=,uid=,lstart=,comm='], capture_output=True, timeout=2).stdout
            exe = raw.decode().strip().split(maxsplit=7)[7]
            self.assertEqual(o.parse_ios_identity(raw, child.pid, Path(exe))['pid'], child.pid)
        finally:
            child.terminate(); child.wait(timeout=2); child.stdout.close()


class WindowTests(unittest.TestCase):
    def test_marker_schema_and_scenario_guard(self):
        o.validate_window(marker(), context())
        for key, value in [('process_id', True), ('maximum_ms', 20001), ('mode', 'consented'), ('scenario', 'runtime-cache-grace'), ('harness_sha256', 'c'*64)]:
            value_marker = dict(marker(), **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                o.validate_window(value_marker, context())
        with self.assertRaises(ValueError):
            o.validate_window(dict(marker(), unapproved=True), context())

    def pair(self, opened, closed):
        return 'flutter: TIDEGLASS_PRIVACY_WINDOW_OPEN ' + json.dumps(opened) + '\nflutter: TIDEGLASS_PRIVACY_WINDOW_CLOSE ' + json.dumps(closed) + '\n'

    def test_order_complete_and_twenty_second_ceiling(self):
        opened = marker(); closed = dict(opened, native_elapsed_us=15000002, native_utc_ms=115000)
        self.assertEqual(o.window_pair(self.pair(opened, closed), context()), (opened, closed))
        for log in [self.pair(opened, closed).splitlines()[0], self.pair(opened, closed)*2,
                    self.pair(opened, dict(closed, native_elapsed_us=20000003)),
                    self.pair(opened, dict(closed, process_id=125))]:
            with self.assertRaises(ValueError):
                o.window_pair(log, context())

    def test_host_and_native_interval_attribution_fail_closed(self):
        opened=marker(); closed=dict(opened, native_utc_ms=115000)
        sample={'process_identity': {'pid': 123}, 'started_ns': 11, 'finished_ns': 20,
                'started_utc_ms': 100001, 'finished_utc_ms': 114999}
        o.validate_sample_window(sample, opened, closed, 10, {'pid':123})
        for key, value in [('started_ns', 9), ('finished_ns', 17000000011), ('started_utc_ms', 99999), ('finished_utc_ms', 115001), ('process_identity', {'pid':124})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                o.validate_sample_window(dict(sample, **{key:value}), opened, closed, 10, {'pid':123})

    def test_waiting_or_failed_capture_never_finalizes(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            for status in ['incomplete', 'failed', 'expected-interrupted']:
                (output/'observation.json').write_text(json.dumps({'status':status,'errors':[]}))
                with self.assertRaises(ValueError):
                    o.finalize(output, output)


class StorageTests(unittest.TestCase):
    def test_only_seven_fixed_fixture_files_are_read(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            (base/'support').mkdir()
            (base/'support/tideglass-study.json').write_text('{"synthetic":true}')
            (base/'unrelated-secret').write_text('not read')
            result=o.local_storage(base)
            self.assertEqual(set(result), set(o.FILES))
            self.assertEqual(result['support/tideglass-study.json']['sha256'], o.sha(b'{"synthetic":true}'))
            self.assertFalse(result['game/progress.0.json']['present'])
            self.assertNotIn('not read', json.dumps(result))

    def test_symlink_fifo_and_oversize_refused(self):
        for kind in ['link', 'fifo', 'oversize']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                base=Path(directory); (base/'support').mkdir()
                file=base/'support/tideglass-study.json'
                if kind=='link': file.symlink_to(base/'elsewhere')
                if kind=='fifo': os.mkfifo(file)
                if kind=='oversize':
                    with file.open('wb') as stream: stream.truncate(2097153)
                with self.assertRaises(ValueError): o.local_storage(base)

    def test_root_exact_device_and_synthetic_namespace(self):
        device='F05BE4B0-52C1-4CA1-B721-BD64AE559E3F'
        container=f'/tmp/Devices/{device}/data/Containers/Data/Application/container'
        m=marker(); m['fixture_directory']=container+'/Library/Application Support/native-current-verification/ios-phone-run1/study'
        self.assertEqual(str(o.fixture_root(m, device, container)), m['fixture_directory'])
        for bad in [m['fixture_directory'].replace('native-current-verification','tideglass'), m['fixture_directory']+'/../study']:
            with self.assertRaises(ValueError): o.fixture_root(dict(m,fixture_directory=bad), device,container)


class StagingTests(unittest.TestCase):
    def test_harness_opt_in_default_unchanged_and_post_assertion(self):
        source=(HERE/'source/game/mobile/integration_test/current_runtime_test.dart').read_text()
        self.assertRegex(source, r"const privacyObservation = bool.fromEnvironment\(\s*'TIDEGLASS_PRIVACY_OBSERVATION',?\s*\);")
        self.assertIn('if (privacyObservation) await privacyWindow(tester);', source)
        self.assertLess(source.index('await privacyWindow(tester);'), source.index("report['completed'] = true"))
        self.assertIn('const Duration(seconds: 20)',source)
        self.assertIn('const Duration(seconds: 15)',source)
        self.assertIn("'maximum_ms': 20000",source)
        self.assertIn('if (privacyObservation) {\n      await guardEmptySharedCache();',source)

    def test_runner_opt_in_archive_and_allowlist(self):
        source=(HERE/'source/tool/verify_current_runtime.py').read_text()
        self.assertIn("require(not observe_privacy or args.scenario in ('runtime-study-default', 'runtime-study-enroll')",source)
        self.assertIn("privacy_observation_enabled=observe_privacy",source)
        self.assertIn("'--dart-define=TIDEGLASS_PRIVACY_OBSERVATION=true'",source)
        self.assertIn("'--observe-privacy', action='store_true'",source)

    def test_android_command_filters_on_device_without_global_capture(self):
        self.assertIn('test "$8" = "$uid" || continue',o.ANDROID_SOCKETS)
        self.assertIn('case "$nodes" in',o.ANDROID_SOCKETS)
        self.assertNotIn('tcpdump',o.ANDROID_SOCKETS)
        self.assertNotIn('su ',o.ANDROID_SOCKETS)


class FinalizationTests(unittest.TestCase):
    def prepare(self, base):
        evidence=base/'proof-1'; evidence.mkdir()
        output=base/'observation'; output.mkdir()
        harness=b'SYNTHETIC HARNESS BYTES'
        ctx=dict(context(),harness_sha256=o.sha(harness))
        opened=dict(marker(),harness_sha256=o.sha(harness))
        closed=dict(opened,native_elapsed_us=15000002,native_utc_ms=115000)
        prefix='flutter: TIDEGLASS_PRIVACY_WINDOW_OPEN '+json.dumps(opened)+'\n'
        log=prefix+'flutter: TIDEGLASS_PRIVACY_WINDOW_CLOSE '+json.dumps(closed)+'\nflutter: 00:20 +1: All tests passed!\nAll tests passed.\n'
        payload=dict(ctx,process_id=123,completed=True,privacy_observation_window={'opened':opened,'closed':closed})
        payload_raw=json.dumps(payload).encode()
        for name, data in [('harness.dart',harness),('run.log',log.encode()),('result.json',payload_raw)]: (evidence/name).write_bytes(data)
        verification=dict(ctx,label=ctx['device_label'],device='F05BE4B0-52C1-4CA1-B721-BD64AE559E3F',
            passed=True,status='passed',exit_code=0,verification_errors=[],native_process_id=123,
            source_snapshot_unchanged=True,source_changes_during_run=[],production_input_differences_after_run=[],
            privacy_observation_enabled=True,command=['--dart-define=TIDEGLASS_PRIVACY_OBSERVATION=true'],
            evidence_sha256={p.name:o.sha(p.read_bytes()) for p in evidence.iterdir()})
        (evidence/'verification.json').write_text(json.dumps(verification))
        (output/'open-prefix.log').write_text(prefix)
        report=dict(status='collected-pending-native-completion',errors=[],native_evidence=str(evidence),context=ctx,
            device=verification['device'],opened=opened,open_prefix_sha256=o.sha(prefix.encode()),
            process_identity={'pid':123},opened_observed_ns=1,collector_sha256=o.sha((HERE/'runtime_observation.py').read_bytes()),
            samples=[dict(process_identity={'pid':123},started_ns=2,finished_ns=3,
                started_utc_ms=100001,finished_utc_ms=114999,sockets={'status':'observed','rows':[]},storage={'status':'observed','files':{}})])
        (output/'observation.json').write_text(json.dumps(report))
        return evidence, output, verification

    def test_finalization_requires_both_normal_successes_and_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            _,output,_=self.prepare(Path(directory))
            result=o.finalize(output,Path(__file__).resolve().parents[3])
            self.assertEqual(result['status'],'finalized-sampled-observation')
            self.assertFalse(result['traffic_absence_claim'])
            self.assertFalse(result['release_acceptance'])
            with self.assertRaises(ValueError): o.finalize(output,Path(__file__).resolve().parents[3])

    def test_native_failure_zero_count_source_drift_and_false_pass_refused(self):
        for defect in ['negative-native','zero-count','wrong-device','wrong-pid','drift','no-flag','pin','late-sample','no-close']:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                evidence,output,verification=self.prepare(Path(directory))
                if defect in ('negative-native','zero-count','no-close'):
                    text=(evidence/'run.log').read_text()
                    if defect=='negative-native': text+='E/flutter ( 123): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: late failure\n'
                    if defect=='zero-count': text=text.replace('+1:', '+0:')
                    if defect=='no-close': text='\n'.join(line for line in text.splitlines() if 'WINDOW_CLOSE' not in line)+'\n'
                    (evidence/'run.log').write_text(text)
                    verification['evidence_sha256']['run.log']=o.sha(text.encode())
                if defect=='wrong-device': verification['device']='other'
                if defect=='wrong-pid': verification['native_process_id']=124
                if defect=='drift': verification['source_snapshot_unchanged']=False
                if defect=='no-flag': verification['privacy_observation_enabled']=False
                if defect=='pin': verification['evidence_sha256']['result.json']='0'*64
                if defect=='late-sample':
                    report=json.loads((output/'observation.json').read_text()); report['samples'][0]['finished_utc_ms']=115001
                    (output/'observation.json').write_text(json.dumps(report))
                (evidence/'verification.json').write_text(json.dumps(verification))
                with self.assertRaises(ValueError): o.finalize(output,Path(__file__).resolve().parents[3])


if __name__=='__main__': unittest.main(verbosity=2)
