"""Read-only revalidation of immutable152 and archived native evidence."""
from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tool'))
import build_native,verify_native
base=ROOT/'release/native-proof'
candidate=ROOT/'.tooling/build-candidates/20261021T101953.650199Z-152805bf9e26'
manifest=json.loads((candidate/'manifest.json').read_text())
fp=manifest['source_fingerprint']
out=base/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-152-final-verification')
out.mkdir()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data): (out/name).write_text(json.dumps(data,indent=2)+'\n')
checks={}
checks['frozen_source_matches_manifest']=build_native.source_hashes(candidate/'source')==manifest['source_sha256']
checks['fingerprint_matches_manifest']=build_native.fingerprint(build_native.source_hashes(candidate/'source'))==fp
workspaces={}
for ws in ['workspace','workspace-release']:
 diffs=[p for p,h in manifest['source_sha256'].items() if not(candidate/ws/p).is_file() or sha(candidate/ws/p)!=h]
 prod=verify_native.production_inputs(manifest['source_sha256'])
 pd=[p for p,h in prod.items() if not(candidate/ws/p).is_file() or sha(candidate/ws/p)!=h]
 locks=[p for p,h in manifest['source_sha256'].items() if Path(p).name in ['pubspec.lock','Package.resolved'] and (not(candidate/ws/p).is_file() or sha(candidate/ws/p)!=h)]
 workspaces[ws]={'captured_file_differences':diffs,'production_differences':pd,'dependency_lock_differences':locks}
 checks[ws+'_production_and_locks_match']=not(pd or locks)
artifacts=[]
for folder in ['20261021T102112.746555Z','20261021T103632.486357Z']:
 report=json.loads((base/folder/'build-report.json').read_text())
 for target,row in report['results'].items():
  p=ROOT/row['artifact']; current=sha(p)
  artifacts.append({'target':target,'mode':report['mode'],'path':row['artifact'],'expected_sha256':row['artifact_sha256'],'actual_sha256':current,'bytes':p.stat().st_size,'matches':current==row['artifact_sha256'] and p.stat().st_size==row['artifact_bytes']})
checks['five_artifacts_match']=len(artifacts)==5 and all(x['matches'] for x in artifacts)
audit=[];accepted=[];failed=[]
oldfp='d85bdf74433d96d2f6ea6a58a8481290942d526a7cdb8ec14b55e57537e9dced'
for p in sorted(base.glob('integration-*/verification.json')):
 r=json.loads(p.read_text())
 if r.get('candidate_fingerprint') not in [fp,oldfp]:continue
 log=p.parent/'run.log';errors=verify_native.native_log_errors(log.read_text())
 evidence_diffs=[name for name,h in r.get('evidence_sha256',{}).items() if not(p.parent/name).is_file() or sha(p.parent/name)!=h]
 payload=json.loads((p.parent/'result.json').read_text()) if (p.parent/'result.json').is_file() else {}
 identity_diffs=[]
 for key,expected in [('candidate_fingerprint',r['candidate_fingerprint']),('verification_id',p.parent.name),('scenario',r['scenario']),('run_id',r['run_id']),('device_label',r['label']),('platform',r.get('platform',verify_native.native_platform(r['device'],None))),('harness_sha256',r['harness_sha256']['harness.dart'])]:
  if payload.get(key)!=expected:identity_diffs.append(key)
 # Legacy d85 harness predates candidate/verification identity fields; retain the historical binding limit.
 required_identity_diffs=identity_diffs if r['candidate_fingerprint']==fp else []
 # Preserve original report outcomes; this is an explicit superseding audit.
 strict_pass=bool(r.get('passed')) and r.get('exit_code')==0 and not errors and not evidence_diffs and not required_identity_diffs
 row={'path':str(p.relative_to(ROOT)),'candidate_fingerprint':r['candidate_fingerprint'],'label':r['label'],'device':r['device'],'scenario':r['scenario'],'run_id':r['run_id'],'verification_sha256':sha(p),'log_sha256':sha(log),'reported_passed':r['passed'],'strict_passed':strict_pass,'strict_log_errors':errors,'evidence_hash_differences':evidence_diffs,'payload_identity_differences':identity_diffs,'harness_sha256':r['harness_sha256']}
 audit.append(row)
 if r['candidate_fingerprint']==fp:(accepted if strict_pass else failed).append(row)
plan=json.loads((base/'20261021T101953.650199Z/runtime-plan.json').read_text())
required={(r['label'],r['device'],r['scenario']) for r in plan['rows']}
actual={(r['label'],r['device'],r['scenario']) for r in accepted}
checks['all_22_runtime_cells']=len(accepted)==22 and required==actual
checks['protected_device_not_used']=all(r['device']!=plan['protected_device_excluded'] for r in accepted+failed)
checks['native_evidence_hashes_match']=all(not r['evidence_hash_differences'] for r in audit)
write('native-log-audit.json',{'verifier_sha256':sha(ROOT/'tool/verify_native.py'),'reports':audit,'original_reports_unchanged':True,'false_passes_superseded':[r['path'] for r in audit if r['reported_passed'] and not r['strict_passed']]})
write('runtime-matrix.json',{'candidate_fingerprint':fp,'accepted':accepted,'failed_or_invalid':failed,'expected_cells':len(required),'accepted_cells':len(actual),'missing':[list(x) for x in sorted(required-actual)],'supersedes_only_false_pass_classification':True})
for name in ['verify_native.py','build_native.py','native_recording.py','native_integration_driver.dart','native_video_metadata.swift','test_native_candidates.py']:(out/name).write_bytes((ROOT/'tool'/name).read_bytes())
(out/'platform_smoke_test.dart').write_bytes((ROOT/'game/mobile/integration_test/platform_smoke_test.dart').read_bytes())
write('final-verification.json',{'candidate_fingerprint':fp,'candidate_directory':str(candidate),'source_manifest_sha256':sha(candidate/'manifest.json'),'checks':checks,'workspaces':workspaces,'artifacts':artifacts,'passed':all(checks.values()),'runtime_matrix':'runtime-matrix.json','native_log_audit':'native-log-audit.json','tooling_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ['.py','.swift','.dart']},'limitations':['Same-host source, recipe, lock and artifact identity checks only. No second-host or byte-identical rebuild.','Original candidate reports preserved; newer working-tree source is excluded.','No physical device, human playtest, paid store transaction, hosted provider, signed distribution or public-release acceptance.']})
print(out)
print(json.dumps(checks,indent=2))
if not all(checks.values()):raise SystemExit(1)
