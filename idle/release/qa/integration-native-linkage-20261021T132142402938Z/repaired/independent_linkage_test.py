"""Independent synthetic counterexamples; no native or real-session claim."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'promoted/tool'))
import study_native_diagnostics as n
import study_adjudicate as a
from test_study_native_diagnostics import NativeDiagnosticTests
class Independent(unittest.TestCase):
 def setUp(self):
  self.f=NativeDiagnosticTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
 def test_fractional_provenance_version_rejected(self):
  self.assertEqual(self.f.run_match(proof_change={'schema_version':1.0})['status'],'unknown')
 def test_boolean_provenance_version_rejected(self):
  self.assertEqual(self.f.run_match(proof_change={'schema_version':True})['status'],'unknown')
 def test_actual_new_process_boundary_excludes_old_crash(self):
  f=self.f
  other=dict(f.context,native_pid=456,observed_start_utc_ms=105000)
  f.event('app_start',105,{'config':f.config,'reason':'process_restart','native_context':other},process='5'*32,session='6'*32)
  self.assertEqual(f.run_match()['status'],'unknown')
 def test_post_crash_activity_excludes_claimed_session(self):
  f=self.f;f.event('harbor_interactive',111,{})
  self.assertEqual(f.run_match()['status'],'unknown')
 def test_context_milliseconds_and_missing_gap_reject(self):
  f=self.f;f.raw['records'][0]['payload']['native_context']=dict(f.context,observed_start_utc_ms=106000);f.rehash()
  with self.assertRaises(ValueError):a.decode_records(f.raw,f.registry,4000)
 def test_duplicate_release_rows_fail_closed(self):
  f=self.f;f.manifest['binaries'].append(copy.deepcopy(f.manifest['binaries'][0]))
  self.assertEqual(f.run_match()['status'],'unknown')
 def test_manifest_boolean_and_wrong_role_rejected(self):
  f=self.f;f.manifest['schema_version']=True
  self.assertEqual(f.run_match()['status'],'unknown')
  f.manifest['schema_version']=1;f.manifest['binaries'][0]['binary_role']='engine'
  self.assertEqual(f.run_match()['status'],'unknown')
 def test_positive_supported_synthetic_reference_and_unknown_signal(self):
  f=self.f;self.assertEqual(f.run_match()['status'],'linked')
  f.report['exception']={'type':'EXC_CRASH','signal':'SIGTERM'}
  self.assertEqual(f.run_match()['status'],'unknown')
 def test_erased_fractional_document_rejected_by_python(self):
  for version in [1.0,2.0,True]:
   with self.subTest(version=version),self.assertRaises(ValueError):
    a.decode_records({'schema_version':version,'registry':None,'records':[],'status':'withdrawn'},self.f.registry,4000)
 def test_duplicate_json_and_missing_native_identity_rejected(self):
  with self.assertRaises(ValueError):n.json_document(b'{"version":1,"version":2}')
  f=self.f;f.report['usedImages']=[{'name':'Flutter','uuid':f.binary}]
  self.assertEqual(f.run_match()['status'],'unknown')
if __name__=='__main__':unittest.main(verbosity=2)
