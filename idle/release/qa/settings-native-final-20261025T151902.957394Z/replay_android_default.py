from pathlib import Path
import ast,json,hashlib,re,types,copy
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;pins={};checks=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def check(name,ok):checks.append({'name':name,'passed':bool(ok)});assert ok,name
def sha(b):return hashlib.sha256(b).hexdigest()
old='release/qa/settings-native-20261023T081631.942859Z/replay_reminder_initial.py'
node=next(n for n in ast.parse(read(old)).body if isinstance(n,ast.FunctionDef) and n.name=='pure');exec(compile(ast.Module(body=[node],type_ignores=[]),'preserved-pure-extractor','exec'))
folder=R/'release/native-notifications/integration-android-20261025T151153756482Z';report=j(folder/'verification.json');payload=j(folder/'result.json');log=read(folder/'run.log').decode();ns=pure(folder)
check('exact report',sha(read(folder/'verification.json'))=='3c5e1c53eb0dcafb7555fb3d204d9ed5bf6f5232257f4f52135b8a7a0b977044')
for name,h in report['evidence_sha256'].items():check('actual archive '+name,Path(name).name==name and sha(read(folder/name))==h)
check('strict native default completion',ns['payload_errors'](payload,report,log)==[] and report['passed'] and report['exit_code']==0)
check('actual owned Android target',report['device']=='emulator-5556' and report['platform']=='android')
check('default stays opted out',payload['default_opted_out'] is True and payload['default_preferences_file_absent'] is True and payload['default_pending_ids']==[])
check('no actual permission action',payload['actions']==[] and payload['initialization_lifecycle_events']==[] and payload['permission_before_initialize']==payload['permission_after_initialize'])
check('unchanged production',report['frozen_source_unchanged'] and not report['production_differences_after'] and not report['source_differences_during_run'])
for field,value in [('default_opted_out',False),('default_pending_ids',[77101]),('completed',False)]:
 bad=copy.deepcopy(payload);bad[field]=value;check('reject '+field,bool(ns['payload_errors'](bad,report,log)))
check('reject late native failure',bool(ns['payload_errors'](payload,report,log+'\nI/flutter (123): Unhandled Exception: negative control\n')))
check('pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
(O/'android-default-review-verification.json').write_text(json.dumps({'checks_passed':len(checks),'checks':checks,'pins':pins,'actual_default_only':True,'remaining_four':'not implied by this default result; actual UI-dependent runs require their own sealed reports','native_or_device_commands':False},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'pins':len(pins)}))
