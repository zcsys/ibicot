"""Real host POSIX-shell publication checks; no adb, Flutter or device process."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,importlib.util,json,os,shlex,signal,subprocess,time,unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ack_recorder',HERE/'staged/native_recording.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class AckPublication(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.folder=Path(self.tmp.name)/"private fixture's directory";self.folder.mkdir()
  self.payload=self.folder/'screenshot-1-ready.json';self.marker=Path(str(self.payload)+'.complete')
  self.receipt={'candidate_fingerprint':'a'*64,'verification_id':'unit','sha256':'b'*64,'bytes':123,'quoted':'test $HOME `false` $(false)'}
  self.r=m.GalleryRecorder(Path(self.tmp.name),self.folder,'android','not-a-device','unit','unit')
  self.r.capture_directory=str(self.folder)
 def command(self,receipt=None):
  with patch.object(self.r,'run') as call:
   self.r.acknowledge(self.payload.name,self.receipt if receipt is None else receipt)
  args,kw=call.call_args
  shell=shlex.split(args[0][-1]);self.assertEqual(len(shell),1)
  self.assertEqual(args[0][-5:-1],['run-as',m.APP_ID,'sh','-c'])
  return ['/bin/sh','-c',shell[0]],kw['input_text'].encode()
 def execute(self,receipt=None,env=None):
  cmd,body=self.command(receipt);return subprocess.run(cmd,input=body,capture_output=True,timeout=3,env=env)
 def assert_no_publication(self):self.assertFalse(self.marker.exists());self.assertFalse(self.marker.is_symlink())
 def test_complete_payload_then_empty_directory_publishes_exact_bytes(self):
  result=self.execute();self.assertEqual(result.returncode,0,result.stderr)
  self.assertEqual(self.payload.read_bytes(),(json.dumps(self.receipt,sort_keys=True)+'\n').encode())
  self.assertTrue(self.marker.is_dir());self.assertFalse(self.marker.is_symlink());self.assertEqual(list(self.marker.iterdir()),[])
 def test_second_publisher_refuses_without_changing_completed_payload(self):
  self.assertEqual(self.execute().returncode,0);before=self.payload.read_bytes()
  self.assertNotEqual(self.execute({'other':'receipt'}).returncode,0);self.assertEqual(self.payload.read_bytes(),before)
 def test_existing_partial_payload_is_preserved_without_completion(self):
  self.payload.write_bytes(b'{"partial":');self.assertNotEqual(self.execute().returncode,0)
  self.assertEqual(self.payload.read_bytes(),b'{"partial":');self.assert_no_publication()
 def test_existing_payload_directory_or_fifo_is_not_opened(self):
  self.payload.mkdir();self.assertNotEqual(self.execute().returncode,0);self.assert_no_publication();self.payload.rmdir()
  os.mkfifo(self.payload);self.assertNotEqual(self.execute().returncode,0);self.assert_no_publication();self.assertTrue(self.payload.exists())
 def test_payload_symlinks_existing_and_dangling_are_refused(self):
  target=self.folder/'unrelated';target.write_bytes(b'preserve');self.payload.symlink_to(target)
  self.assertNotEqual(self.execute().returncode,0);self.assertEqual(target.read_bytes(),b'preserve');self.assert_no_publication()
  self.payload.unlink();target.unlink();self.payload.symlink_to(target)
  self.assertNotEqual(self.execute().returncode,0);self.assertFalse(target.exists());self.assert_no_publication()
 def test_preexisting_completion_directory_or_file_prevents_payload_write(self):
  self.marker.mkdir();self.assertNotEqual(self.execute().returncode,0);self.assertFalse(self.payload.exists());self.marker.rmdir()
  self.marker.write_bytes(b'preserve');self.assertNotEqual(self.execute().returncode,0);self.assertFalse(self.payload.exists());self.assertEqual(self.marker.read_bytes(),b'preserve')
 def test_completion_symlinks_existing_and_dangling_prevent_payload_write(self):
  target=self.folder/'other';target.mkdir();self.marker.symlink_to(target,target_is_directory=True)
  self.assertNotEqual(self.execute().returncode,0);self.assertFalse(self.payload.exists());self.assertEqual(list(target.iterdir()),[])
  self.marker.unlink();target.rmdir();self.marker.symlink_to(target,target_is_directory=True)
  self.assertNotEqual(self.execute().returncode,0);self.assertFalse(self.payload.exists());self.assertFalse(target.exists())
 def wait_partial(self,count):
  deadline=time.monotonic()+2
  while time.monotonic()<deadline:
   if self.payload.exists() and self.payload.stat().st_size==count:return
   time.sleep(.005)
  self.fail('Host cat did not write supplied partial payload')
 def test_partial_open_writer_never_publishes_then_completion_is_exact(self):
  cmd,body=self.command();p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  try:
   half=len(body)//2;p.stdin.write(body[:half]);p.stdin.flush();self.wait_partial(half);self.assert_no_publication()
   p.stdin.write(body[half:]);p.stdin.close();p.stdin=None;_,err=p.communicate(timeout=3)
   self.assertEqual(p.returncode,0,err);self.assertTrue(self.marker.is_dir());self.assertEqual(self.payload.read_bytes(),body)
  finally:
   if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.communicate()
 def test_interrupted_partial_writer_leaves_unpublished_evidence(self):
  cmd,body=self.command();p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  try:
   half=len(body)//2;p.stdin.write(body[:half]);p.stdin.flush();self.wait_partial(half)
   os.killpg(p.pid,signal.SIGKILL);p.communicate(timeout=3)
   self.assertLess(p.returncode,0);self.assertEqual(self.payload.read_bytes(),body[:half]);self.assert_no_publication()
   self.assertNotEqual(self.execute().returncode,0);self.assertEqual(self.payload.read_bytes(),body[:half]);self.assert_no_publication()
  finally:
   if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.communicate()
 def fault_environment(self,utility,script):
  bindir=self.folder/'bin';bindir.mkdir();p=bindir/utility;p.write_text('#!/bin/sh\n'+script+'\n');p.chmod(0o700)
  return {**os.environ,'PATH':str(bindir)+':/bin:/usr/bin'}
 def test_writer_nonzero_exit_never_publishes_even_if_bytes_are_complete(self):
  result=self.execute(env=self.fault_environment('cat','/bin/cat\nexit 7'))
  self.assertEqual(result.returncode,7);self.assertEqual(json.loads(self.payload.read_text()),self.receipt);self.assert_no_publication()
 def test_marker_creation_failure_preserves_complete_payload_unpublished(self):
  result=self.execute(env=self.fault_environment('mkdir','exit 9'))
  self.assertEqual(result.returncode,9);self.assertEqual(json.loads(self.payload.read_text()),self.receipt);self.assert_no_publication()
 def test_concurrent_publishers_have_one_unchanged_winner(self):
  cmd,a=self.command({'publisher':'A'});_,b=self.command({'publisher':'B'})
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  q=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  p.communicate(a,timeout=3);q.communicate(b,timeout=3)
  self.assertEqual(sum(x.returncode==0 for x in [p,q]),1);self.assertEqual(self.payload.read_bytes(),a if p.returncode==0 else b);self.assertTrue(self.marker.is_dir())
 def test_unsafe_acknowledgement_name_never_reaches_shell(self):
  for filename in ['../outside','recording-started','screenshot-5-ready.json','screenshot-1-ready.json.complete']:
   with self.subTest(filename=filename),patch.object(self.r,'run') as call,self.assertRaises(ValueError):self.r.acknowledge(filename,{})
   call.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
