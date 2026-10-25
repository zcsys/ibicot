"""Independent replay against an immutable, explicitly supplied collector author pin."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 author=ROOT/sys.argv[1]; meta=json.loads(author.read_text()); files=meta['source_sha256']
 assert len(files)==48
 assert hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()==meta['source_fingerprint']
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'); name='integration-study-collection-final-'+stamp
 out=ROOT/'release/qa'/name; work=ROOT/'game/qa/workspaces'/name
 out.mkdir(); work.mkdir()
 for rel,h in files.items():
  assert sha(ROOT/rel)==h,rel
  p=work/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,p);assert sha(p)==h
 shutil.copyfile(author,out/'author-verification.json')
 qa={}
 for rel in ['game/qa/integration_study_collection_test.dart','game/qa/integration_study_collection_test.py','game/qa/integration_study_collection_review.py']:
  qa[rel]=sha(ROOT/rel);shutil.copyfile(ROOT/rel,out/Path(rel).name)
 shutil.copyfile(ROOT/'game/qa/integration_study_collection_test.dart',work/'game/platform/test/qa_independent_test.dart')
 (out/'snapshot.json').write_text(json.dumps({'source_fingerprint':meta['source_fingerprint'],'files':files,'qa_inputs':qa,'author_verification_sha256':sha(author)},indent=2)+'\n')
 (ROOT/'game/qa/current_study_collection_final_review.json').write_text(json.dumps({'evidence':str(out),'workspace':str(work)},indent=2)+'\n')
 dart=str(ROOT/'tool/dart'); checks=[]
 def run(name,args,cwd=work,env=None):
  r=subprocess.run(args,cwd=cwd,env=env,text=True,capture_output=True,timeout=120)
  p=out/(name+'.log');p.write_text(r.stdout+r.stderr)
  checks.append({'name':name,'command':args,'cwd':str(cwd),'exit_code':r.returncode,'log_sha256':sha(p)})
  return r
 run('pub-get',[dart,'pub','get','--offline'],work/'game/platform')
 run('dart-30',[dart,'test','test/study_recorder_test.dart','test/qa_independent_test.dart','--reporter=json'],work/'game/platform')
 run('dart-analysis',[dart,'analyze','lib/study_recorder.dart','test/study_recorder_test.dart','test/study_fixture_export.dart'],work/'game/platform')
 run('python-author-30',[sys.executable,'-m','unittest','discover','-s','tool','-p','test_study*.py','-v'])
 run('python-independent-5',[sys.executable,str(out/'integration_study_collection_test.py'),'-v'],env={**os.environ,'STUDY_COLLECTION_SOURCE':str(work)})
 run('actual-dart-export',[dart,'run','test/study_fixture_export.dart',str(out/'regenerated')],work/'game/platform')
 fixture=work/'release/study/fixtures/collection-v1'; generated=out/'regenerated'
 parity={rel:sha(fixture/rel)==sha(generated/rel) for rel in ['protocol.json','registry.json','raw.json','labels.json']}
 for p in (fixture/'evidence').iterdir():
  target=generated/'evidence'/p.name
  if target.exists(): assert sha(p)==sha(target)
  else: shutil.copyfile(p,target)
 run('adjudicate-generated',[sys.executable,'tool/study_adjudicate.py','--protocol',str(generated/'protocol.json'),'--registry',str(generated/'registry.json'),'--raw',str(generated/'raw.json'),'--review',str(fixture/'review.json'),'--evidence-dir',str(generated/'evidence'),'--output-dir',str(out/'qualified')])
 report=run('analyze-generated',[sys.executable,'tool/study_report.py','--protocol',str(generated/'protocol.json'),'--data',str(out/'qualified/data.json')])
 qualified_parity=sha(out/'qualified/data.json')==sha(fixture/'qualified/data.json')
 report_parity=json.loads(report.stdout)==json.loads((fixture/'qualified/report.json').read_text())
 drift=[rel for rel,h in files.items() if sha(work/rel)!=h]; live=[rel for rel,h in files.items() if sha(ROOT/rel)!=h]
 verification={'format':'independent-study-collection-final-v1','source_fingerprint':meta['source_fingerprint'],'source_count':len(files),'checks':checks,'dart_fixture_byte_parity':parity,'qualified_data_byte_parity':qualified_parity,'report_semantic_parity':report_parity,'frozen_drift':drift,'live_drift':live,'participants_observed':0,'native_or_ui_claim':False,'packages_accepted':False}
 (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
 print(json.dumps({'evidence':str(out),'source_fingerprint':meta['source_fingerprint'],'checks':[{k:r[k] for k in ('name','exit_code')} for r in checks],'fixture':parity,'data_parity':qualified_parity,'report_parity':report_parity,'drift':drift,'live':live},indent=2))
 return int(any(r['exit_code'] for r in checks) or not all(parity.values()) or not qualified_parity or not report_parity or bool(drift))
if __name__=='__main__': raise SystemExit(main())
