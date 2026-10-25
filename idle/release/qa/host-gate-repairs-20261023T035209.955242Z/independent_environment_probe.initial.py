from pathlib import Path
import contextlib,io,json,shutil,sys,tempfile
ROOT=Path('/Users/csys/Desktop/ibicot/idle');sys.path.insert(0,str(ROOT/'tool'))
import build_native
OUT=Path(__file__).parent
results=[]
for fault in ('missing_lock','mismatched_real_package','duplicate_lock_entry'):
 with tempfile.TemporaryDirectory() as tmp:
  base=Path(tmp);(base/'tool').mkdir();(base/'services').mkdir();(base/'evidence').mkdir();(base/'tests/services/operations').mkdir(parents=True)
  shutil.copy2(ROOT/'tool/check_provider_environment.py',base/'tool/check_provider_environment.py')
  lock=(ROOT/'services/requirements-providers.lock').read_text()
  entries=[line for line in lock.splitlines() if line and not line.startswith('#')]
  if fault=='mismatched_real_package':
   name=entries[0].split('==')[0];lock=lock.replace(entries[0],name+'==0.0.0')
  if fault=='duplicate_lock_entry':lock+='\n'+entries[0]+'\n'
  if fault!='missing_lock':(base/'services/requirements-providers.lock').write_text(lock)
  (base/'tests/services/test_base.py').write_text('import unittest\nclass Base(unittest.TestCase):\n def test_ok(self):self.assertTrue(True)\n')
  (base/'tests/services/operations/test_sentinel.py').write_text('from pathlib import Path\nimport unittest\nclass Sentinel(unittest.TestCase):\n def test_never(self):\n  Path("OPERATIONS_RAN").write_text("unexpected")\n  self.fail("unqualified operations executed")\n')
  report={}
  with contextlib.redirect_stdout(io.StringIO()) as output:failed=build_native.run_service_host_checks(base,base/'evidence',report)
  assert failed==['provider-environment','operations-test'],failed
  assert report['host_checks']['services-test']['exit_code']==0
  assert report['host_checks']['provider-environment']['exit_code']!=0
  assert report['host_checks']['operations-test']['status']=='blocked'
  assert not (base/'OPERATIONS_RAN').exists()
  assert report['host_checks']['provider-environment']['command'][0]==str(ROOT/'.tooling/services-venv/bin/python')
  assert report['host_checks']['provider-environment']['command'][1]==str(base/'tool/check_provider_environment.py')
  target=OUT/('negative-'+fault);target.mkdir()
  for p in (base/'evidence').iterdir():shutil.copy2(p,target/p.name)
  (target/'result.json').write_text(json.dumps(report,indent=2)+'\n')
  results.append({'fault':fault,'failed':failed,'actual_checker':True,'actual_pinned_environment':True,'operations_executed':False,'passed':True})
(OUT/'independent-environment-probes.json').write_text(json.dumps(results,indent=2)+'\n');print('3 independent actual-checker fail-closed scenarios passed')
