from pathlib import Path
import ast,json,hashlib,re,types
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;pins={};checks=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
node=next(n for n in ast.parse(read('release/qa/settings-native-20261023T081631.942859Z/replay_reminder_initial.py')).body if isinstance(n,ast.FunctionDef) and n.name=='pure');exec(compile(ast.Module(body=[node],type_ignores=[]),'preserved-pure-extractor','exec'))
from copy import deepcopy
P=R/'release/native-notifications/integration-android-20261025T162843581392Z';CP='release/native-notifications/resume-20261025-20261025T150516.353584Z/android-delivery-observed3-checkpoint.json';cp=j(CP);r=j(P/'verification.json');p=j(P/'result.json');log=read(P/'run.log').decode();ns=pure(P)
check('exact terminal checkpoint',sha(read(CP))=='932afa59293bd3409cd94fba521c09137231d033ce3686c2d04769460f066249')
check('exact terminal report',sha(read(P/'verification.json'))==cp['verification_sha256']=='0f4f530c677cb4bb1cb9293c23878e3a046e75af68183091181544a68a5c9758')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(P/n))==h==cp['native_evidence_sha256'][n])
for n,h in cp['late_operator_files_sha256'].items():check('late archive '+n,Path(n).name==n and sha(read(P/n))==h)
check('original strict complete validator passes',ns['payload_errors'](p,r,log)==[] and r['passed'] is True and r['exit_code']==0 and r['errors']==[])
check('real delivered ID and body before scoped cancellation',p['delivered_records']==[{'id':77101,'title':'A light in the harbor','body':'Focus is available for your next constellation. Return whenever you like.'}] and p['return_pending_ids']==[] and p['return_active_ids']==[])
check('actual callbacks and lifetime',p['lifecycle_callback_failures']==[] and p['completed'] is True and p['returned_elapsed_ms']-p['scheduled_elapsed_ms']==511811 and ns['actual_departure_return'](p['lifecycle_events'],p['actions'],'background_app_now_using_os_home',0))
check('original minimum and watch bound',p['plan']['due_utc_ms']-p['plan']['background_call_utc_ms']>=300000 and p['returned_elapsed_ms']<720000)
check('native and driver completion preserved','All tests passed!' in log and 'All tests passed.' in log and 'SemanticsHandle was active' not in log and 'EXCEPTION CAUGHT' not in log)
check('frozen source and artifacts exact',r['frozen_source_unchanged'] and not r['production_differences_after'] and not r['source_differences_during_run'] and r['generated_harness_matches'] and r['installed_artifact']['matches_host_artifact'])
check('unchanged original harness and gate',r['source_pins']['harness.dart']=='330ab6428203ec80e4de19e4eb727ad8dcfc6f63572e9ea1b0ef3ff7dc7a71da' and r['source_pins']['verify_native_reminders.py']=='2ff5ce93795e3ed4584ce08fc2976e6c268582c26b995aadae9c7e3b337df1ed')
tap=j(P/'operator-return-action.json');before=j(P/'operator-before-return-receipts.json');after=j(P/'operator-return-receipts.json');stamp=lambda text:datetime.fromisoformat(text).timestamp()*1000
check('observed current-icon tap bound',tap['observed_node']['text']=='Tideglass' and tap['pre_image_sha256']==sha(read(P/'operator-before-return.png')) and tap['pre_hierarchy_sha256']==sha(read(P/'operator-before-return-hierarchy.txt')) and tap['argv'][-4:]==['input','tap','910','1970'])
check('hierarchy session finished before icon tap',before[0]['argv'][-3:]==['uiautomator','dump','/dev/tty'] and stamp(before[1]['utc'])<stamp(tap['utc']))
all_receipts=[]
for name in r['evidence_sha256']:
 if name.endswith('receipts.json'):
  value=j(P/name)
  if isinstance(value,list):all_receipts+=value
check('no recorded post-return UiAutomation session',all('uiautomator' not in row.get('argv',[]) or stamp(row['utc'])<stamp(tap['utc']) for row in all_receipts))
check('post-return observations are screenshot and activity only',len(after)==2 and after[0]['argv'][-3:]==['exec-out','screencap','-p'] and after[1]['argv'][-3:]==['dumpsys','activity','activities'])
raw=read(P/'due-observation4-notifications.txt').decode();blocks=re.split(r'(?=    NotificationRecord\()',raw);matches=[x for x in blocks if x.startswith('    NotificationRecord(') and 'pkg=dev.tideglass.game ' in x.splitlines()[0]]
check('unique raw active actual notification',len(matches)==1 and 'id=77101 ' in matches[0].splitlines()[0] and 'android.text=String (Focus is available for your next constellation. Return whenever you like.)' in matches[0])
creation=int(re.search(r'mCreationTimeMs=(\d+)',matches[0])[1]);check('raw OS creation after due before return',creation==1792946249420 and p['plan']['due_utc_ms']<=creation<p['returned_utc_ms'])
neg=[]
for name,change in [('missing-delivery',lambda q:q.update(delivered_records=[])),('wrong-body',lambda q:q['delivered_records'][0].update(body='wrong')),('uncancelled',lambda q:q.update(return_pending_ids=[77101])),('callback-failure',lambda q:q.update(lifecycle_callback_failures=[{'error':'synthetic'}])),('short-duration',lambda q:q.update(returned_elapsed_ms=q['scheduled_elapsed_ms']+299999))]:
 q=deepcopy(p);change(q);errors=ns['payload_errors'](q,r,log);check('negative '+name,bool(errors));neg.append({'mutation':name,'errors':errors})
check('late framework semantics error still rejected',bool(ns['payload_errors'](p,r,log+'\nEXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\nA SemanticsHandle was active at the end of the test.\n')))
old=R/'release/native-notifications/integration-android-20261025T161006684764Z/verification.json';check('prior semantics failure unchanged',sha(read(old))=='96e56315397749e294f1c03e7c0fb2c61a978118c8d5648b2566fad6a03da9fb' and j(old)['passed'] is False)
read('release/qa/quiet-hours-contract-clarification-20261025T161119.038568Z/REVIEW.md');read('implementation/program.json');read('implementation/scope_requirements.json')
check('all inputs stable',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
result={'checks':checks,'check_count':len(checks),'pins':pins,'synthetic_negative_controls':neg,'actual_native_delivery_supported':True,'native_creation_utc_ms':creation,'background_elapsed_ms':511811,'strict_framework_and_driver_pass':True,'new_native_execution':False,'M3_05_S26':'Remain open until independent Android revoked restart proof','visual_limit':'Pre-return screenshot shows actual current lighthouse launcher icon. Immediate post-tap screenshot still shows launcher transition; actual resume is established by native lifecycle/result, not claimed from that screenshot.'}
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'sha':sha((O/'verification.json').read_bytes())}))
