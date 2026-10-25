from pathlib import Path
import ast,json,hashlib,re,types,xml.etree.ElementTree as ET
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;pins={};checks=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
node=next(n for n in ast.parse(read('release/qa/settings-native-20261023T081631.942859Z/replay_reminder_initial.py')).body if isinstance(n,ast.FunctionDef) and n.name=='pure');exec(compile(ast.Module(body=[node],type_ignores=[]),'preserved-pure-extractor','exec'))
P=R/'release/native-notifications/integration-android-20261025T154824471008Z';CP='release/native-notifications/resume-20261025-20261025T150516.353584Z/android-delivery-checkpoint.json';cp=j(CP);r=j(P/'verification.json');p=j(P/'result.json');log=read(P/'run.log').decode();ns=pure(P)
check('exact failed checkpoint',sha(read(CP))=='e21f62739c0e3f3ea2f6de7b4100282ccd101e6029490d7d5534d874fa13caaf')
check('exact failed report',sha(read(P/'verification.json'))==cp['verification_sha256']=='38a60e7e39295b9afec213dcbf4808cfa5d599d65f1ca2365049d4ec3382bca7')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(P/n))==h==cp['native_evidence_sha256'][n])
for n,h in cp['late_operator_files_sha256'].items():check('late archive '+n,Path(n).name==n and sha(read(P/n))==h)
errors=ns['payload_errors'](p,r,log);check('failure reproduced without relabeling',bool(errors) and set(errors)<=set(r['errors']) and r['passed'] is False and r['exit_code']==1 and p['completed'] is False)
check('specific actual delivery missing',p['delivered_records']==[] and 'Scheduled requests are not delivered OS notifications' in errors and 'A scheduled request alone is not actual delivery.' in log)
check('unchanged actual source and built artifact',r['frozen_source_unchanged'] and r['generated_harness_matches'] and not r['production_differences_after'] and not r['source_differences_during_run'] and r['installed_artifact']['matches_host_artifact'] and r['installed_artifact']['sha256'] in r['artifact_after'].values())
plan=p['plan'];obs=p['plan_observation'];check('actual same saved/game state and digest',obs['saved_payload']==obs['game_payload'] and sha(json.dumps(obs['saved_payload'],separators=(',',':'),ensure_ascii=False).encode())==plan['saved_payload_sha256'])
check('actual pause and resumed callback after due',ns['actual_departure_return'](p['lifecycle_events'],p['actions'],'background_app_now_using_os_home',plan['due_utc_ms']))
elapsed=p['returned_elapsed_ms']-p['scheduled_elapsed_ms'];check('actual monotonic interval retained',elapsed==360267 and p['returned_utc_ms']>=plan['due_utc_ms'] and plan['due_utc_ms']-plan['background_call_utc_ms']>=300000)
check('same observed native process before Home and at due',read(P/'operator-home-before-pid.txt').decode().strip()==read(P/'operator-due-home-pid.txt').decode().strip()==str(p['process_id'])=='5708')
home=j(P/'operator-home-after-action.json');ret=j(P/'operator-return-after-action.json')
check('actual Home on selected emulator',home['argv'][1:]==['-s','emulator-5556','shell','input','keyevent','KEYCODE_HOME'] and home['exit_code']==0)
s=read(P/'operator-return-drawer-hierarchy.txt').decode();root=ET.fromstring(s[s.index('<?xml'):s.index('</hierarchy>')+len('</hierarchy>')]);nodes=[x for x in root.iter('node') if x.attrib==ret['observed_node']]
check('return through uniquely observed current uppercase icon',len(nodes)==1 and nodes[0].get('text')=='Tideglass' and nodes[0].get('enabled')=='true' and nodes[0].get('clickable')=='true')
coords=list(map(int,ret['argv'][-2:]));b=list(map(int,re.findall(r'\d+',ret['observed_node']['bounds'])));check('actual return tap in observed bounds after due',ret['argv'][1:7]==['-s','emulator-5556','shell','input','touchscreen','tap'] and b[0]<coords[0]<b[2] and b[1]<coords[1]<b[3] and datetime.fromisoformat(ret['utc']).timestamp()*1000>=plan['due_utc_ms'])
check('return identity screenshot and hierarchy',ret['pre_image_sha256']==sha(read(P/'operator-return-drawer.png')) and ret['pre_hierarchy_sha256']==sha(read(P/'operator-return-drawer-hierarchy.txt')))
check('post-return cancellation separately observed',p['return_pending_ids']==[] and p['return_active_ids']==[])
D=R/'release/native-notifications/android-delivery-diagnostics-20261025T155621.067878Z';diag=j(D/'verification.json');check('diagnostic report binds failed actual run',diag['native_report_sha256']==sha(read(P/'verification.json')))
for n,h in diag['evidence_sha256'].items():check('diagnostic archive '+n,Path(n).name==n and sha(read(D/n))==h)
check('native granted permission retained', 'android.permission.POST_NOTIFICATIONS: granted=true' in read(D/'package.txt').decode())
source=read(R/'game/mobile/lib/notification_service.dart').decode();check('production uses stated inexact mode','AndroidScheduleMode.inexactAllowWhileIdle' in source)
check('no premature causal claim', 'not proven' in diag['inference'] and 'no production defect' in diag['inference'])
check('all reviewed pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
out={'utc':datetime.now(timezone.utc).isoformat(),'result':'strict_failure_confirmed_delivery_unqualified','checks':checks,'checks_passed':len(checks),'pins':pins,'pure_verifier_errors':errors,'actual_scheduled_to_return_ms':elapsed,'actual_due_utc_ms':plan['due_utc_ms'],'actual_returned_utc_ms':p['returned_utc_ms'],'observed_delivered_records':[],'cause':'not established; diagnostic inexact-scheduling explanation remains an inference','new_native_device_or_runtime_execution':False,'M3_05_S26_acceptance':False}
(O/'delivery-failure-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification_sha256':sha((O/'delivery-failure-verification.json').read_bytes())}))
