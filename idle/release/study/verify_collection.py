"""Freeze collection source and run bounded author checks; never enroll players."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out=ROOT/'release/study'/('collection-author-'+stamp);source=out/'source';source.mkdir(parents=True)
 paths=[ROOT/p for p in ['game/platform/lib/study_recorder.dart','game/platform/test/study_recorder_test.dart','game/platform/test/study_fixture_export.dart','game/platform/pubspec.yaml','game/platform/pubspec.lock','tool/study_adjudicate.py','tool/test_study_adjudicate.py','tool/study_report.py','tool/test_study_report.py','release/study/COLLECTION.md','release/study/README.md','release/study/verify_collection.py','docs/quality/PLAYER_STUDY_PROTOCOL.md','release/qa/integration-study-20261021T102508755253Z/STUDY_REVIEW.md']]
 for package in ('core','events','persistence'):
  paths += list((ROOT/'game'/package/'lib').rglob('*.dart'))
  paths += [ROOT/'game'/package/name for name in ('pubspec.yaml','pubspec.lock') if (ROOT/'game'/package/name).exists()]
 paths += [p for p in (ROOT/'release/study/fixtures').rglob('*') if p.is_file()]
 entries={}
 for path in sorted(set(paths)):
  relative=path.relative_to(ROOT);target=source/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);entries[str(relative)]=sha(target)
 fingerprint=hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 dart=str(ROOT/'tool/dart');records=[]
 commands=[('offline-dependencies',[dart,'pub','get','--offline'],source/'game/platform'),('recorder-tests',[dart,'test','test/study_recorder_test.dart'],source/'game/platform'),('recorder-analysis',[dart,'analyze','lib/study_recorder.dart','test/study_recorder_test.dart','test/study_fixture_export.dart'],source/'game/platform'),('python-tests',[sys.executable,'-m','unittest','discover','-s','tool','-p','test_study*.py','-v'],source),('dart-fixture',[dart,'run','test/study_fixture_export.dart',str(out/'regenerated-fixture')],source/'game/platform')]
 fixture=source/'release/study/fixtures/collection-v1'
 commands += [('adjudicate-cli',[sys.executable,'tool/study_adjudicate.py','--protocol',str(fixture/'protocol.json'),'--registry',str(fixture/'registry.json'),'--raw',str(fixture/'raw.json'),'--review',str(fixture/'review.json'),'--evidence-dir',str(fixture/'evidence'),'--output-dir',str(out/'qualified')],source),('analysis-cli',[sys.executable,'tool/study_report.py','--protocol',str(fixture/'protocol.json'),'--data',str(out/'qualified/data.json')],source)]
 for name,command,cwd in commands:
  result=subprocess.run(command,cwd=cwd,text=True,capture_output=True,timeout=120)
  log=out/(name+'.log');log.write_text(result.stdout+result.stderr)
  records.append({'name':name,'command':command,'cwd':str(cwd.relative_to(out)),'exit_code':result.returncode,'log':log.name,'log_sha256':sha(log)})
  if result.returncode:break
 drift=[name for name,digest in entries.items() if sha(source/name)!=digest]
 live=[name for name,digest in entries.items() if sha(ROOT/name)!=digest]
 regenerated={}
 if (out/'regenerated-fixture').exists():
  for name in ('protocol.json','registry.json','raw.json','labels.json'):
   regenerated[name]=sha(out/'regenerated-fixture'/name)==sha(fixture/name)
 comparison=False
 if (out/'qualified/data.json').exists():comparison=json.loads((out/'qualified/data.json').read_text())==json.loads((fixture/'qualified/data.json').read_text())
 report={'format':'tideglass-study-collection-author-v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':entries,'source_fingerprint':fingerprint,'fingerprint_recipe':'SHA256 of UTF8 json.dumps(source_sha256,sort_keys=True,separators=(comma,colon))','checks':records,'source_drift':drift,'live_source_drift':live,'dart_fixture_byte_parity':regenerated,'schema2_data_parity':comparison,'participants_observed':0,'production_packages_accepted':False,'independent_review':'pending','flutter_integration_covered':False,'pre_dart_crashes_observed':False,'outbound_collection_enabled':False,'scope_mapping':{'recorder':['M5-04','M6-01','S30','S39'],'adjudicator':['M5-05','M6-01','S30','S34'],'withdrawal_and_docs':['S39']},'limitations':['Hash chains do not prove truthful clocks, devices, enrollment completeness or actual human observation.','External crash and terminal fixtures are synthetic; real linkage requires qualified independent review.','Root-owned Flutter wrapper/native qualification has separate evidence.','Default local withdrawal cannot recall already exported copies.']}
 (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'evidence':str(out.relative_to(ROOT)),'source_fingerprint':fingerprint,'checks':[{k:v for k,v in row.items() if k in ('name','exit_code')} for row in records],'source_drift':drift,'live_source_drift':live,'fixture_parity':regenerated,'schema2_data_parity':comparison},indent=2))
 return int(any(x['exit_code'] for x in records) or bool(drift) or bool(live) or not all(regenerated.values()) or not comparison)
if __name__=='__main__':raise SystemExit(main())
