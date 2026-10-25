"""Transport-faithful counterexamples; no device mutation or native execution."""
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import verify_current_runtime as v

C=dict(verification_id='probe-only',candidate_fingerprint='a'*64,harness_sha256='b'*64,
       device='emulator-5556',label='android',platform='android',scenario='runtime-save-hold-beforeWrite',run_id='probe-fixture')
DIR='/data/user/0/dev.tideglass.game/files/native-current-verification/android-probe-fixture/save-beforeWrite'
FILE=DIR+'/checkpoint.json'

class ProbeTests(unittest.TestCase):
    def host(self):
        h=v.NativeHost(C);h.calls=[];return h
    def transport(self,host,properties=None,data=b'{}',fault=None):
        properties=properties or {}
        def run(command,**kwargs):
            host.calls.append(command)
            if 'test' in command:
                i=command.index('test');flag,target=command[i+1:]
                truth=properties.get((flag,target),flag!='-L')
                # Actual observed adb semantics: exec-out loses false status.
                code=0 if 'exec-out' in command else (0 if truth else 1)
                stdout,stderr=b'',b''
                if fault and (flag,target)==fault[0]:code,stdout,stderr=fault[1:]
                return SimpleNamespace(returncode=code,stdout=stdout,stderr=stderr)
            if 'head' in command:
                self.assertIn('exec-out',command)
                return SimpleNamespace(returncode=0,stdout=data,stderr=b'')
            raise AssertionError(command)
        return patch.object(v.subprocess,'run',side_effect=run)
    def read(self,h,**kw):return h.read_fixture(DIR,'checkpoint.json',**kw)
    def no_head(self,h):self.assertFalse(any('head' in c for c in h.calls))
    def test_directory_not_link_remote_false_status_survives_transport(self):
        h=self.host()
        with self.transport(h):self.assertEqual(self.read(h),b'{}')
        self.assertTrue(all('shell' in c for c in h.calls if 'test' in c))
    def test_binary_bytes_keep_exec_out_transfer(self):
        h=self.host();data=b'\x00\xff\r\n\x1a'
        with self.transport(h,data=data):self.assertEqual(self.read(h),data)
        self.assertEqual(sum('head' in c for c in h.calls),1)
    def test_symlink_ancestor_refused_before_read(self):
        h=self.host()
        with self.transport(h,{('-L','/data/user/0/dev.tideglass.game/files'):True}),self.assertRaisesRegex(ValueError,'symlink'):self.read(h)
        self.no_head(h)
    def test_symlink_final_file_refused_before_read(self):
        h=self.host()
        with self.transport(h,{('-L',FILE):True}),self.assertRaisesRegex(ValueError,'symlink'):self.read(h)
        self.no_head(h)
    def test_optional_missing_file_is_explicit_absence(self):
        h=self.host()
        with self.transport(h,{('-e',FILE):False}):self.assertIsNone(self.read(h,optional=True))
        self.no_head(h)
    def test_required_missing_file_refused(self):
        h=self.host()
        with self.transport(h,{('-e',FILE):False}),self.assertRaisesRegex(ValueError,'absent'):self.read(h)
        self.no_head(h)
    def test_fifo_or_nonregular_terminal_refused(self):
        h=self.host()
        with self.transport(h,{('-f',FILE):False}),self.assertRaisesRegex(ValueError,'unexpected type'):self.read(h)
        self.no_head(h)
    def test_parent_not_directory_refused(self):
        h=self.host()
        with self.transport(h,{('-d',DIR):False}),self.assertRaisesRegex(ValueError,'unexpected type'):self.read(h)
        self.no_head(h)
    def test_unreadable_file_refused(self):
        h=self.host()
        with self.transport(h,{('-r',FILE):False}),self.assertRaisesRegex(ValueError,'unreadable'):self.read(h)
        self.no_head(h)
    def test_untraversable_parent_refused(self):
        h=self.host()
        with self.transport(h,{('-x',DIR):False}),self.assertRaisesRegex(ValueError,'traversable'):self.read(h)
        self.no_head(h)
    def test_probe_error_and_output_are_not_boolean_success(self):
        for code,out,err in [(2,b'',b''),(0,b'noise',b''),(1,b'',b'error')]:
            h=self.host()
            with self.subTest(code=code,out=out,err=err),self.transport(h,fault=(('-L','/data/user/0/dev.tideglass.game/files'),code,out,err)),self.assertRaisesRegex(ValueError,'type/access'):self.read(h)
            self.no_head(h)
    def test_transport_timeout_refused_before_read(self):
        h=self.host()
        with patch.object(v.subprocess,'run',side_effect=subprocess.TimeoutExpired('adb',20)),self.assertRaises(subprocess.TimeoutExpired):self.read(h)
    def test_size_bound_remains_enforced(self):
        h=self.host()
        with self.transport(h,data=b'12345'),self.assertRaisesRegex(ValueError,'byte limit'):self.read(h,limit=4)
        self.assertEqual(h.calls[-1][-3:],['-c','5',FILE])
    def test_escape_or_unlisted_file_never_reaches_transport(self):
        for directory,relative in [(DIR+'/../other','checkpoint.json'),(DIR,'../outside'),('/data/user/0/other/files','checkpoint.json')]:
            h=self.host()
            with self.subTest(directory=directory,relative=relative),self.transport(h),self.assertRaises(ValueError):h.read_fixture(directory,relative)
            self.assertEqual(h.calls,[])
