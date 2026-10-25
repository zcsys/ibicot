from pathlib import Path
import ast,json,hashlib,re,types,copy
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;pins={};checks=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
node=next(n for n in ast.parse(read('release/qa/settings-native-20261023T081631.942859Z/replay_reminder_initial.py')).body if isinstance(n,ast.FunctionDef) and n.name=='pure');exec(compile(ast.Module(body=[node],type_ignores=[]),'preserved-pure-extractor','exec'))
P=R/'release/native-notifications/integration-android-20261025T154733176679Z';CP='release/native-notifications/resume-20261025-20261025T150516.353584Z/android-quiet-cancel-checkpoint.json';cp=j(CP);r=j(P/'verification.json');p=j(P/'result.json');log=read(P/'run.log').decode();ns=pure(P)
check('exact checkpoint',sha(read(CP))=='00e08cdb778f1252e457da9feb77feaa2be0b4e012f828ebfc6605953475a069')
check('exact report',sha(read(P/'verification.json'))==cp['verification_sha256']=='a8f362dcfe4b9cc96ee5d970ca3d7ae6a9407d845086ca443e0e8e67c510552b')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(P/n))==h==cp['native_evidence_sha256'][n])
check('strict real native and driver completion',ns['payload_errors'](p,r,log)==[] and r['passed'] and r['exit_code']==0 and not r['errors'])
check('exact current target and source',r['device']=='emulator-5556' and r['platform']=='android' and r['harness_sha256']=='330ab6428203ec80e4de19e4eb727ad8dcfc6f63572e9ea1b0ef3ff7dc7a71da' and all(r['source_pins'][n]==r['evidence_sha256'][n] for n in r['source_pins']))
check('production unchanged and installed artifact exact',r['frozen_source_unchanged'] and r['generated_harness_matches'] and not r['production_differences_after'] and not r['source_differences_during_run'] and r['installed_artifact']['matches_host_artifact'] and r['installed_artifact']['sha256'] in r['artifact_after'].values())
binding=j(P/'operator-allow-precondition.json')
# The native packet explicitly references the independently reviewed real Settings precondition.
serialized=json.dumps(binding);check('actual allowed-state precondition referenced','4075f05717a4f54d206cc62adeff3e550c62015526728690600348d178644584' in serialized and 'android-enable-preflight-20261025T154330.157706Z' in serialized)
check('previous independent precondition remains pinned',sha(read(O/'allow-precondition-verification.json'))=='9131872ad3fa3da654062446867c33df251e2547c3006b3f0bb413d943ee5310')
check('no invented new permission dialog',p['permission_before_initialize']==p['permission_after_initialize']==p['permission_after_opt_in']=='allowed' and p['lifecycle_events']==[])
plan=p['plan'];obs=p['plan_observation'];q=p['quiet_window'];bg=datetime.fromtimestamp(plan['background_call_utc_ms']/1000,timezone.utc).astimezone(ZoneInfo(q['zone']));due=datetime.fromtimestamp(plan['due_utc_ms']/1000,timezone.utc).astimezone(ZoneInfo(q['zone']));expected=bg.replace(hour=q['end_minute']//60,minute=q['end_minute']%60,second=0,microsecond=0)
if expected<=bg:expected+=timedelta(days=1)
check('independent exact next quiet-end conversion',due==expected and due.hour*60+due.minute==p['quiet_due_local_minute']==q['end_minute'] and bg.hour*60+bg.minute==q['start_minute'])
check('minimum five-minute delay retained',300000<=plan['due_utc_ms']-plan['background_call_utc_ms']<3600000)
check('actual durable game and save states match',obs['saved_payload']==obs['game_payload'] and obs['saved_snapshot_id']==plan['saved_snapshot_id'] and obs['saved_settled_through_utc_micros']==obs['game_settled_through_utc_micros'])
check('actual durable payload digest',sha(json.dumps(obs['saved_payload'],separators=(',',':'),ensure_ascii=False).encode())==plan['saved_payload_sha256'])
check('exact native plan queued and cancelled',obs['pending_ids']==plan['ids']==[77101] and p['return_pending_ids']==[] and plan['production_lifecycle'] is True)
negative=[]
for label,fn in [('wrong-run',lambda x:x.update(run_id='wrong')),('incomplete',lambda x:x.update(completed=False)),('too-early',lambda x:x['plan'].update(due_utc_ms=x['plan']['background_call_utc_ms']+299999)),('wrong-quiet-end',lambda x:x.update(quiet_due_local_minute=(x['quiet_due_local_minute']+1)%1440)),('pending-after-return',lambda x:x.update(return_pending_ids=[77101]))]:
 bad=copy.deepcopy(p);fn(bad);errors=ns['payload_errors'](bad,r,log);check('reject '+label,bool(errors));negative.append({'mutation':label,'errors':errors})
check('reject late native exception',bool(ns['payload_errors'](p,r,log+'\nI/flutter (5391): Unhandled Exception: independent negative control\n')))
check('all pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
out={'utc':datetime.now(timezone.utc).isoformat(),'result':'Android_quiet_plan_and_cancellation_supported','checks':checks,'checks_passed':len(checks),'negative_controls':negative,'late_error_control':True,'pins':pins,'actual_due_local':due.isoformat(),'delay_from_background_ms':plan['due_utc_ms']-plan['background_call_utc_ms'],'boundary':'Synthetic Focus/quiet window and direct production lifecycle calls exercise real OS scheduling/cancellation. This quiet case has no native pause/resume and does not claim actual Home departure, a new permission prompt or delivery. Those are separately tested by delivery/revocation.','new_device_or_runtime_execution':False,'remaining':['delivery','revoked']}
(O/'quiet-verification.json').write_text(json.dumps(out,indent=2)+'\n');(O/'quiet-seal.json').write_text(json.dumps({'files':{n:sha((O/n).read_bytes()) for n in ['review_quiet.py','quiet-verification.json']}},indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification_sha256':sha((O/'quiet-verification.json').read_bytes()),'seal_sha256':sha((O/'quiet-seal.json').read_bytes())}))
