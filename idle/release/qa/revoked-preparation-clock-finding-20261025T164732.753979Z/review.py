from pathlib import Path
from datetime import datetime
import hashlib,json
R=Path(__file__).resolve().parents[3];O=Path(__file__).parent;pins={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=sha(b);return b
def j(p):return json.loads(read(p))
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
P=R/'release/native-notifications/revoked-restart-operator-20261025T164440025420Z';B=R/'release/native-notifications/integration-android-20261025T164440025420Z';cp=j(P/'checkpoint.json');r=j(B/'verification.json');op=j(P/'operator.json')
check('exact terminal report',sha(read(B/'verification.json'))=='f8d460bebd26e7bb63c61ae609f6dc57606a1b3a22442572c1f9c180eb3a2413'==cp['preparation_report_sha256'])
check('exact checkpoint',sha(read(P/'checkpoint.json'))=='355eb30af3a914e09c2c9a9885b1df21a8c19ee90d15c9aaf1d2f77e9ecc74d8')
for n,h in r['evidence_sha256'].items():check('native '+n,Path(n).name==n and sha(read(B/n))==h==cp['native_evidence_sha256'][n])
for n,h in cp['operator_files_sha256'].items():check('operator '+n,Path(n).name==n and sha(read(P/n))==h)
check('properly unaccepted interruption',r['passed'] is False and r['status']=='os-interrupted-awaiting-ui-evidence' and r['errors']==[] and r['exit_code']!=0)
check('source and artifact binding',r['production_differences_after']==[] and r['frozen_source_unchanged'] is True and r['source_differences_during_run']==[] and r['generated_harness_matches'] is True and r['installed_artifact']['matches_host_artifact'])
ns={'__name__':'qa_archived_restart'};exec(compile(read(B/'reminder_restart.py'),'archived-restart','exec'),ns)
prep=r['restart_preparation'];death=r['restart_death'];c=ns['checkpoint'](read(B/'revoke-checkpoint.json'),r,prep['marker'])
check('checkpoint is real incomplete preparation',c['preparation']['completed'] is False and c['preparation']['plan']['production_lifecycle'] is True and c['preparation']['plan_observation']['pending_ids']==[77101])
kill=ns['kill_record'](read(B/'exit-info.txt').decode(),read(B/'death-logcat.txt').decode(),prep['marker'],read(B/'device-offset.txt').decode().strip(),death['observed_utc_ms']);check('actual fresh bound permission kill',kill==1792946734623==death['kill_utc_ms'] and death['process_id']==10359)
ns['validate_host_receipts'](j(B/'restart-host-receipts.json'),r,prep,death);check('current original raw export/PID verifier',True)
try:ns['validate_operator'](P/'operator.json',r)
except ValueError as e:error=str(e)
else:raise AssertionError('operator failure disappeared')
check('exact rejection reproduced',error==cp['operator_validation_error']=='UI action does not bind actual fresh permission kill')
check('raw clock mismatch arithmetic',op['action_started_utc_ms']-kill==368 and op['action_finished_utc_ms']-op['action_started_utc_ms']==60)
check('actual UI on then off',ns['switch'](read(P/'before.xml').decode(),True)==ns['switch'](read(P/'after.xml').decode(),False))
check('actual before PID and later absence',read(P/'before-pid.txt').decode().strip()=='10359' and not read(P/'after-pid.txt').strip())
D=R/'release/native-notifications/revocation-clock-diagnostic-20261025T164645.898891Z';d=j(D/'diagnostic.json');check('exact later diagnostic',sha(read(D/'diagnostic.json'))=='637eb1f3ffd56701ad3f56498656b0baf47d8bf8b2d3979917229909988bc934')
for x in d['samples']:
 check('diagnostic raw '+x['raw_file'],sha(read(D/x['raw_file']))==x['sha256'])
 expected=[(x[k]-x['device_utc_ns'])/1e6 for k in ['host_before_ns','host_after_ns']];check('reproduced later clock bound '+x['raw_file'],expected==x['host_minus_device_bounds_ms'] and x['host_before_ns']>op['after_utc_ms']*1000000)
# Explicitly no retrospective adjustment or synthetic pass of the actual packet.
for f in ['release/qa/revoked-restart-independent-20261025T162707.106411Z/REVIEW.md','release/qa/revoked-nullability-review-20261025T163020.468764Z/REVIEW.md','implementation/program.json','implementation/scope_requirements.json']:read(f)
check('all input pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
v={'checks':checks,'check_count':len(checks),'pins':pins,'operator_rejection':error,'recovery_authorized':False,'production_defect_identified':False,'finding':'Protocol directly compares host UTC epoch samples against device UTC epoch events after only timezone conversion; same-run clock relationship was not captured.','prior_review_correction':'QA earlier stage review missed this clock-domain assumption; this append-only finding corrects it without changing the original seal.','device_calls':False}
(O/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification':sha((O/'verification.json').read_bytes())}))
