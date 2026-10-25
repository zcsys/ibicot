"""Exact Android socket transport; owned host fixtures only, no device calls."""
import importlib.util
from pathlib import Path
import shlex
import subprocess
import time
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('socket_transport',HERE/'runtime_observation.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
EMPTY=b'TABLE|tcp\nTABLE|tcp6\nTABLE|udp\nTABLE|udp6\n'
VALID=b'FD|1234\nTABLE|tcp\nSOCKET|tcp|10209|1234|0100007F:0010|00000000:0000|0A\nTABLE|tcp6\nTABLE|udp\nTABLE|udp6\n'
class SocketTransportTests(unittest.TestCase):
    def host(self,stdout=EMPTY,code=0,stderr=b''):
        h=o.Host.__new__(o.Host);h.platform='android';h.adb=Path('/owned/adb');h.device='emulator-5556';h.marker={'process_id':7435};h.app_uid=10209;h.commands=[];h.deadline=time.monotonic()+15
        h.runner=lambda argv,**kw:subprocess.CompletedProcess(argv,code,stdout,stderr)
        return h
    def test_exact_socket_argv_only_uses_shell(self):
        h=self.host();self.assertEqual(h.sockets(),[])
        self.assertEqual(h.commands[0]['argv'],['/owned/adb','-s','emulator-5556','shell','run-as','dev.tideglass.game','sh','-c',shlex.quote(o.ANDROID_SOCKETS),'observer','7435','10209'])
    def test_remote_identity_stays_binary_exec_out(self):
        h=self.host();self.assertEqual(h.remote('cat','/proc/7435/cmdline'),['/owned/adb','-s','emulator-5556','exec-out','run-as','dev.tideglass.game','cat','/proc/7435/cmdline'])
    def test_shell_roundtrip_script_is_single_unquoted_child_argument(self):
        h=self.host();h.sockets();argv=h.commands[0]['argv'];remote=shlex.split(' '.join(argv[4:]))
        self.assertEqual(remote,['run-as','dev.tideglass.game','sh','-c',o.ANDROID_SOCKETS,'observer','7435','10209'])
    def test_actual_read_failure_retains_status_and_rejects(self):
        h=self.host(code=72,stderr=b'Permission denied\n')
        with self.assertRaisesRegex(ValueError,'command unavailable'):h.sockets()
        self.assertEqual(h.commands[0]['exit_code'],72);self.assertEqual(h.commands[0]['stderr'],'Permission denied\n')
    def test_nonzero_even_with_complete_looking_tables_rejected(self):
        h=self.host(stdout=EMPTY,code=1)
        with self.assertRaises(ValueError):h.sockets()
    def test_legacy_zero_status_wrapper_prose_rejected(self):
        h=self.host(stdout=b'observer: script : inaccessible or not found\n')
        with self.assertRaisesRegex(ValueError,'Unexpected socket output'):h.sockets()
    def test_exact_uid_inode_record_parses(self):
        rows=self.host(VALID).sockets();self.assertEqual((rows[0]['uid'],rows[0]['inode']),(10209,1234))
    def test_other_uid_rejected(self):
        with self.assertRaisesRegex(ValueError,'another UID'):self.host(VALID.replace(b'|10209|',b'|10210|')).sockets()
    def test_other_process_inode_rejected(self):
        with self.assertRaisesRegex(ValueError,'selected PID'):self.host(VALID.replace(b'FD|1234',b'FD|9999')).sockets()
    def test_incomplete_tables_never_empty_success(self):
        with self.assertRaisesRegex(ValueError,'access incomplete'):self.host(EMPTY.replace(b'TABLE|udp6\n',b'')).sockets()
    def test_non_protocol_output_rejected(self):
        with self.assertRaises(ValueError):self.host(VALID+b'GLOBAL|another_uid_endpoint\n').sockets()
    def test_size_limit_unchanged(self):
        with self.assertRaisesRegex(ValueError,'output exceeds bound'):self.host(b'x'*65537).sockets()
    def test_timeout_and_budget_unchanged(self):
        h=self.host();h.deadline=time.monotonic()-1
        with self.assertRaisesRegex(ValueError,'budget exhausted'):h.sockets()
        self.assertEqual(h.commands,[])
    def test_android_storage_stays_unavailable_no_command(self):
        h=self.host()
        with self.assertRaisesRegex(ValueError,'descriptor-anchored'):h.storage()
        self.assertEqual(h.commands,[])
    def test_android_identity_uses_four_binary_scoped_reads(self):
        h=self.host();pid=7435;stat=f'{pid} (tideglass) S '+' '.join(['0']*18+['99']+['0']*10)
        data=[b'dev.tideglass.game\0unused\0',stat.encode(),b'Uid:\t10209\t10209\t10209\t10209\n',b'12345678-1234-1234-1234-123456789abc\n'];calls=[]
        def run(argv,**kw):calls.append(argv);return subprocess.CompletedProcess(argv,0,data[len(calls)-1],b'')
        h.runner=run;identity=h.identity();self.assertEqual(identity['start_ticks'],99)
        self.assertEqual([c[3] for c in calls],['exec-out']*4)
        self.assertEqual([c[-1] for c in calls],['/proc/7435/cmdline','/proc/7435/stat','/proc/7435/status','/proc/sys/kernel/random/boot_id'])
    def test_identity_reuse_and_uid_change_still_reject(self):
        before={'pid':7435,'uid':10209,'start_ticks':99};sample={'started_ns':2,'finished_ns':3}
        for after in [dict(before,start_ticks=100),dict(before,uid=10210),dict(before,pid=7436)]:
            with self.subTest(after=after),self.assertRaises(ValueError):o.attributed_sample(before,after,sample,1,4)
    def test_unchanged_socket_script_filters_on_device(self):
        before=importlib.util.spec_from_file_location('previous',HERE/'before-runtime_observation.py');old=importlib.util.module_from_spec(before);before.loader.exec_module(old)
        self.assertEqual(o.ANDROID_SOCKETS,old.ANDROID_SOCKETS);self.assertEqual(o.FILES,old.FILES);self.assertEqual(o.LIMITATIONS,old.LIMITATIONS)
    def test_ios_path_unchanged(self):
        h=self.host(b'');h.platform='ios';self.assertEqual(h.sockets(),[])
        self.assertEqual(h.commands[0]['argv'],['/usr/sbin/lsof','-a','-p','7435','-i','-nP','-FpcufPtnT'])
if __name__=='__main__':unittest.main(verbosity=2)
