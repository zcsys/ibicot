"""Synthetic host orchestration tests only. No adb, Flutter or native command runs."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,importlib.util,json,struct,subprocess,unittest,zlib
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('staged_recording',HERE/'staged/native_recording.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def png(w=2,h=3):
 def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x12\x34\x56\xff'*w)*h))+chunk(b'IEND',b'')
def stat(pid=4321,tick=99):return f'{pid} (screenrecord) S '+ ' '.join(['0']*18+[str(tick)]+['0']*20)
class FakeProcess:
 def __init__(self):self.code=None;self.signals=[]
 def poll(self):return self.code
 def wait(self,timeout=None):self.code=0;return self.code
 def send_signal(self,s):self.signals.append(s)
 def terminate(self):self.code=-15
class GalleryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.ev=self.root/'integration-android-20261023T000000.000000Z';self.ev.mkdir();(self.ev/'harness.dart').write_text('synthetic unit harness')
  self.r=m.GalleryRecorder(self.root,self.ev,'android','emulator-test-only','android','unit-run')
  self.command=['flutter-not-executed','drive']+[f'--dart-define={k}={v}' for k,v in {'TIDEGLASS_VERIFICATION_ID':self.ev.name,'TIDEGLASS_CANDIDATE_FINGERPRINT':'a'*64,'TIDEGLASS_HARNESS_SHA256':hashlib.sha256((self.ev/'harness.dart').read_bytes()).hexdigest(),'TIDEGLASS_DEVICE_LABEL':'android','TIDEGLASS_RUN_ID':'unit-run','TIDEGLASS_SCENARIO':'capture-gallery'}.items()]
  self.r.bind_command(self.command);self.directory='/data/user/0/dev.tideglass.game/files/native-verification/capture-android-unit-run';self.identity={**self.r.capture_identity,'directory':self.directory};self.data=png();self.calls=[];self.acks=[];self.proc=FakeProcess();self.argv=['screenrecord','--time-limit','27',self.r.remote];self.tick=99;self.screencap_code=0;self.stat_calls=0
  self.runpatch=patch.object(m.subprocess,'run',side_effect=self.run);self.runpatch.start();self.addCleanup(self.runpatch.stop)
  self.popatch=patch.object(m.subprocess,'Popen',side_effect=self.popen);self.popatch.start();self.addCleanup(self.popatch.stop)
  self.sleep=patch.object(m.time,'sleep');self.sleep.start();self.addCleanup(self.sleep.stop)
 def run(self,cmd,**kw):
  self.calls.append((cmd,kw))
  if cmd[-3:]==['exec-out','screencap','-p']:return subprocess.CompletedProcess(cmd,self.screencap_code,self.data,b'')
  if '/proc/4321/stat' in cmd:self.stat_calls+=1;return subprocess.CompletedProcess(cmd,0,stat(tick=self.tick),'')
  if '/proc/4321/cmdline' in cmd:return subprocess.CompletedProcess(cmd,0,'\0'.join(self.argv)+'\0','')
  if 'run-as' in cmd and 'sh' in cmd:self.acks.append((cmd,json.loads(kw['input'])));return subprocess.CompletedProcess(cmd,0,'','')
  if 'pull' in cmd:Path(cmd[-1]).write_bytes(b'unit-video-placeholder');return subprocess.CompletedProcess(cmd,0,'','')
  if cmd[:2]==['xcrun','swift']:return subprocess.CompletedProcess(cmd,0,json.dumps({'duration_seconds':getattr(self,'duration',26.1),'width':2,'height':3,'audio_track_count':0,'video_track_count':1}),'')
  return subprocess.CompletedProcess(cmd,0,'','')
 def popen(self,cmd,**kw):
  self.calls.append((cmd,kw));(self.ev/'recorder.log').write_text('TIDEGLASS_SCREENRECORD_PID=4321\n');return self.proc
 def request(self,i=1,**changes):
  d={**self.identity,'sequence':i,'file':f'android-capture-{m.SCREENS[i-1]}.png','width':2,'height':3,'gameplay_elapsed_ms':[0,9000,15000,22000][i-1]};d.update(changes);return json.dumps(d,separators=(',',':'))
 def line(self,marker,value):return 'I/flutter ( 44): '+marker+value+'\n'
 def start(self):
  self.log=self.line(m.SCREENSHOT,self.request())
  self.r.observe(self.log);self.log+=self.line(m.READY,json.dumps(self.identity));self.r.observe(self.log)
 def complete(self):
  self.start()
  for i in range(2,5):self.log+=self.line(m.SCREENSHOT,self.request(i));self.r.observe(self.log)
  self.log+=self.line(m.DONE+' ',json.dumps({**self.identity,'gameplay_elapsed_ms':25001}));self.r.observe(self.log)
 def test_complete_flow_preserves_raw_bytes_order_identity_and_targeted_stop(self):
  self.complete();self.assertTrue(self.r.done);self.assertEqual(len(self.r.report['android_screenshots']),4)
  for row in self.r.report['android_screenshots']:
   self.assertEqual((self.ev/row['file']).read_bytes(),self.data);self.assertEqual(row['sha256'],hashlib.sha256(self.data).hexdigest());self.assertLessEqual(row['host_capture_start_monotonic_ns'],row['host_capture_end_monotonic_ns'])
  self.assertEqual(len(self.acks),5);self.assertTrue(self.r.report['android_recording_stop']['recorder_stopped']);self.assertEqual(self.r.report['android_recorder_start']['identity'],self.r.report['android_recorder_stop']['identity'])
  kills=[c for c,k in self.calls if 'kill' in c];self.assertEqual(kills,[self.r.adb('shell','kill','-2','4321')]);self.assertFalse(any('pkill' in c or 'pidof' in c for c,k in self.calls))
  for command,receipt in self.acks:
   self.assertIn('set -C;',command[-1]);self.assertIn('ln ',command[-1]);self.assertIn(self.directory,command[-1])
  self.assertTrue(self.r.finish()['passed'])
 def test_cumulative_log_poll_does_not_repeat_screenshots(self):
  log=self.line(m.SCREENSHOT,self.request());self.r.observe(log);self.r.observe(log);self.assertEqual(len(self.acks),1)
 def test_duplicate_request_marker_rejected(self):
  line=self.line(m.SCREENSHOT,self.request());self.r.observe(line)
  with self.assertRaisesRegex(ValueError,'sequence'):self.r.observe(line+line)
 def test_changed_previous_marker_rejected(self):
  self.r.observe(self.line(m.SCREENSHOT,self.request()))
  with self.assertRaisesRegex(ValueError,'history'):self.r.observe(self.line(m.SCREENSHOT,self.request(width=3)))
 def test_all_bound_identity_fields_reject_mismatch(self):
  for key in m.IDENTITY_KEYS:
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'identity'):self.r.capture_android_screenshot(self.request(**{key:'wrong'}))
  self.assertFalse(self.calls)
 def test_missing_or_duplicate_command_identity_rejected(self):
  for cmd in [self.command[:-1],self.command+[self.command[-1]],self.command[:-2]]:
   with self.subTest(cmd=cmd),self.assertRaises(ValueError):self.r.bind_command(cmd)
 def test_harness_file_mismatch_rejected(self):
  (self.ev/'harness.dart').write_text('changed')
  with self.assertRaisesRegex(ValueError,'identity'):self.r.bind_command(self.command)
 def test_unsafe_wrong_or_changed_private_directory_rejected(self):
  for d in ['/sdcard/x',self.directory+'/../other',self.directory+'x','/data/user/0/other/files/native-verification/capture-android-unit-run']:
   with self.subTest(d=d),self.assertRaises(ValueError):self.r.capture_android_screenshot(self.request(directory=d))
  self.r.checked_request(json.dumps(self.identity))
  with self.assertRaisesRegex(ValueError,'directory changed'):self.r.checked_request(json.dumps({**self.identity,'directory':self.directory.replace('/data/user/0/','/data/data/')}))
 def test_wrong_names_sequence_and_elapsed_rejected(self):
  for changes in [{'file':'../outside.png'},{'file':'android-capture-chapter.png'},{'sequence':2},{'sequence':True},{'gameplay_elapsed_ms':1},{'gameplay_elapsed_ms':-1},{'gameplay_elapsed_ms':1.5},{'width':0},{'width':True},{'height':100000}]:
   with self.subTest(changes=changes),self.assertRaises(ValueError):self.r.capture_android_screenshot(self.request(**changes))
  self.assertFalse(self.calls)
 def test_existing_output_never_overwritten(self):
  p=self.ev/'android-capture-main.png';p.write_bytes(b'preserve')
  with self.assertRaisesRegex(ValueError,'replace'):self.r.capture_android_screenshot(self.request())
  self.assertEqual(p.read_bytes(),b'preserve');self.assertFalse(self.calls)
 def test_symlink_output_refused_without_touching_target(self):
  target=self.root/'outside';target.write_bytes(b'preserve');(self.ev/'android-capture-main.png').symlink_to(target)
  with self.assertRaisesRegex(ValueError,'replace'):self.r.capture_android_screenshot(self.request())
  self.assertEqual(target.read_bytes(),b'preserve')
 def test_screencap_error_never_acknowledged(self):
  self.screencap_code=1
  with self.assertRaisesRegex(RuntimeError,'screencap'):self.r.capture_android_screenshot(self.request())
  self.assertFalse(self.acks);self.assertFalse((self.ev/'android-capture-main.png').exists())
 def test_screencap_timeout_never_acknowledged(self):
  with patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired('unit',5)),self.assertRaises(subprocess.TimeoutExpired):self.r.capture_android_screenshot(self.request())
  self.assertFalse(self.acks)
 def test_invalid_png_bytes_preserved_but_not_acknowledged(self):
  self.data=b'not a native PNG'
  with self.assertRaises(ValueError):self.r.capture_android_screenshot(self.request())
  self.assertEqual((self.ev/'android-capture-main.png').read_bytes(),self.data);self.assertFalse(self.acks)
 def test_wrong_geometry_bytes_preserved_but_not_acknowledged(self):
  self.data=png(3,3)
  with self.assertRaisesRegex(ValueError,'geometry'):self.r.capture_android_screenshot(self.request())
  self.assertEqual((self.ev/'android-capture-main.png').read_bytes(),self.data);self.assertFalse(self.acks)
 def test_png_bad_crc_truncation_and_trailing_data_rejected(self):
  for blob in [self.data[:-1],self.data+b'extra',self.data[:40]+bytes([self.data[40]^1])+self.data[41:],self.data[:8]]:
   with self.subTest(size=len(blob)),self.assertRaises(ValueError):m.raw_png_size(blob)
 def test_duplicate_or_missing_ready_marker_rejected(self):
  ready=self.line(m.READY,json.dumps(self.identity))
  with self.assertRaises(ValueError):self.r.observe(ready)
  self.r.observe(self.line(m.SCREENSHOT,self.request()))
  with self.assertRaises(ValueError):self.r.observe(self.line(m.SCREENSHOT,self.request())+ready+ready)
 def test_done_requires_four_screens_and_same_identity(self):
  self.start()
  with self.assertRaisesRegex(ValueError,'four'):self.r.observe(self.log+self.line(m.DONE+' ',json.dumps({**self.identity,'gameplay_elapsed_ms':25000})))
 def test_wrong_endpoint_identity_rejected(self):
  self.start()
  for i in range(2,5):self.log+=self.line(m.SCREENSHOT,self.request(i));self.r.observe(self.log)
  with self.assertRaisesRegex(ValueError,'identity'):self.r.observe(self.log+self.line(m.DONE+' ',json.dumps({**self.identity,'run_id':'other','gameplay_elapsed_ms':25000})))
 def test_backward_screenshot_elapsed_rejected(self):
  self.start();self.log+=self.line(m.SCREENSHOT,self.request(2));self.r.observe(self.log)
  with self.assertRaisesRegex(ValueError,'backward'):self.r.capture_android_screenshot(self.request(3,gameplay_elapsed_ms=8000))
 def test_screenrecord_wrapper_pins_unique_remote_path(self):
  self.start();cmd=next(c for c,k in self.calls if any('capture_pid=$!' in a for a in c));self.assertIn(self.r.remote,cmd[-1]);self.assertIn('--time-limit 27',cmd[-1]);self.assertIn('wait "$capture_pid"',cmd[-1])
 def test_other_process_or_other_remote_path_never_signalled(self):
  self.start()
  for argv in [['not-screenrecord','--time-limit','27',self.r.remote],['screenrecord','--time-limit','27','/sdcard/someone-else.mp4'],['screenrecord','--time-limit','27',self.r.remote,'extra']]:
   self.argv=argv
   with self.subTest(argv=argv),self.assertRaisesRegex(ValueError,'exact owned'):self.r.stop_android_recorder()
  self.assertFalse(any('kill' in c for c,k in self.calls))
 def test_reused_pid_start_ticks_never_signalled(self):
  self.start();self.tick=100
  with self.assertRaisesRegex(ValueError,'changed'):self.r.stop_android_recorder()
  self.assertFalse(any('kill' in c for c,k in self.calls))
 def test_identity_changed_between_stat_reads_rejected(self):
  n=0
  def changes(cmd,**kw):
   nonlocal n
   if '/proc/4321/stat' in cmd:n+=1;return subprocess.CompletedProcess(cmd,0,stat(tick=n),'')
   return self.run(cmd,**kw)
  with patch.object(m.subprocess,'run',side_effect=changes),self.assertRaisesRegex(ValueError,'during observation'):self.r.recorder_identity(4321)
 def test_malformed_pid_stat_is_rejected(self):
  for text,pid in [('bad',4321),(stat(),2),(stat(tick=0),4321)]:
   with self.subTest(text=text),self.assertRaises(ValueError):m.process_start_ticks(text,pid)
  self.assertEqual(m.process_start_ticks(stat().replace('(screenrecord)','(screen record (worker))'),4321),99)
 def test_early_recorder_exit_rejects_next_screen(self):
  self.start();self.proc.code=0
  with self.assertRaisesRegex(RuntimeError,'exited'):self.r.capture_android_screenshot(self.request(2))
 def test_existing_video_cannot_be_replaced(self):
  self.complete();self.r.video.write_bytes(b'old video');result=self.r.finish();self.assertFalse(result['passed']);self.assertEqual(self.r.video.read_bytes(),b'old video')
 def test_duration_gate_stays_15_to_30(self):
  self.complete();self.duration=30.474355555555555;result=self.r.finish();self.assertFalse(result['passed']);self.assertIn('Footage duration is outside the requested 15–30 seconds',result['errors'])
 def test_manifest_receipts_bind_every_saved_raw_byte(self):
  self.complete();recording=self.r.finish();payload={**self.identity,'os_version':'unit','platform_locale':'unit','provenance':'synthetic unit only','seeded_core':{},'seeded_story':{},'actual_purchase_count_delta':1,'real_gameplay_elapsed_ms':25001,'android_screencaps':self.r.report['android_screenshots'],'android_recording_stop':self.r.report['android_recording_stop'],'screenshots':[str(self.ev/r['file']) for r in self.r.report['android_screenshots']]}
  self.assertEqual(len(m.capture_manifest(self.ev,payload,recording,'unit-device')['screenshots']),4)
  file=Path(payload['screenshots'][0]);file.write_bytes(png(3,3))
  with self.assertRaisesRegex(ValueError,'differs from receipt'):m.capture_manifest(self.ev,payload,recording,'unit-device')
 def test_manifest_rejects_missing_or_changed_receipts(self):
  self.complete();recording=self.r.finish();payload={**self.identity,'screenshots':[str(self.ev/r['file']) for r in self.r.report['android_screenshots']]}
  with self.assertRaisesRegex(ValueError,'receipts'):m.capture_manifest(self.ev,payload,recording,'unit')
 def test_ios_binding_identity_is_noop(self):
  r=m.GalleryRecorder(self.root,self.ev,'ios','unit','ios','run');r.bind_command([]);self.assertIsNone(r.capture_identity)
if __name__=='__main__':unittest.main(verbosity=2)
