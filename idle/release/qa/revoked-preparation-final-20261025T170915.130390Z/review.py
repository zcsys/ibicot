from pathlib import Path
import ast,re,json,hashlib
from datetime import datetime,timezone
R=Path('/Users/csys/Desktop/ibicot/idle');Q=Path(__file__).parent
B=R/'release/native-notifications/integration-android-20261025T170413580881Z'
P=R/'release/native-notifications/revoked-restart2-operator-20261025T170413580881Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];pins={}
def check(v,n):
 assert v,n
 checks.append(n)
def pin(p,want=None):
 got=sha(p);check(want is None or got==want,'pin '+str(p.relative_to(R)));pins[str(p.relative_to(R))]=got
 return got
v=json.loads((B/'verification.json').read_text());cp=json.loads((P/'checkpoint.json').read_text())
for p,w in [(B/'verification.json','a3deed28c60fc116e99bcec42b3654e062f90af74587fcd217fc84a7ba9925ea'),(P/'operator.json','fbfd8618b4175814cc750bcf78c08c8af6e47ce564e32a7d1f8937a730817f6e'),(P/'checkpoint.json','18d0d6908522b4e09d7a110633a64b9874c4dad136f179f4366b10e30c498301')]:pin(p,w)
for base,key in [(B,'native_evidence_sha256'),(P,'operator_files_sha256')]:
 for n,w in cp[key].items():pin(base/n,w)
for path in ['implementation/program.json','implementation/scope_requirements.json','release/qa/revoked-clock-independent-20261025T170122.048749Z/verification.json','release/qa/revoked-clock-independent-20261025T170122.048749Z/REVIEW.md','release/qa/lead-clock-integration-20261025T170309.688305Z/decision.json','release/native-notifications/integration-android-20261025T164440025420Z/verification.json']:
 pin(R/path)
g={};exec(compile((B/'reminder_restart.py').read_text(),str(B/'reminder_restart.py'),'exec'),g)
t=ast.parse((B/'verify_native.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='native_log_errors');ns={'re':re};exec(compile(ast.Module(body=[f],type_ignores=[]),'<archived native_log_errors>','exec'),ns)
prior,c=g['validate_predecessor'](B/'verification.json',{**v,'scenario':'revoked-recover','verification_id':'qa-readonly-current-predecessor'},v['source_pins'],P/'operator.json',ns['native_log_errors']);check(True,'exact archived full predecessor validation')
op=json.loads((P/'operator.json').read_text());timing=g['validate_operator_timing'](op,prior,json.loads((P/'pid-observations.json').read_text()));check(True,'exact operator timing and PID validation')
check(prior['restart_preparation']['native_pid']==10787,'fresh expected actual PID')
check(prior['restart_preparation']['checkpoint_sha256']=='817acff3bbd7e70a4fda1325d3d48b79b684f18066ef6cd10859faf0df0b5e44','fresh durable checkpoint')
check(prior['passed'] is False and prior['errors']==[],'expected interruption remains not pass')
check(len(prior['restart_death']['clock_model']['samples'])==6,'six prospective/post-death samples')
check(timing['kill_host_interval_ns']==[1792947909728535640,1792947909762204962],'independent exact measured host interval')
for path,w in pins.items():assert sha(R/path)==w,path
result={'utc':datetime.now(timezone.utc).isoformat(),'admission':'eligible exact expected-interrupted predecessor for fresh recovery','checks':checks,'check_count':len(checks),'input_pins':pins,'input_pin_count':len(pins),'timing':timing,'native_pid':10787,'checkpoint_sha256':prior['restart_preparation']['checkpoint_sha256'],'visual_inspection':'Reviewer directly viewed before.png and after.png. Current Tideglass lighthouse identity, All Tideglass notifications ON then OFF and denial copy are visible.','limits':['Preparation is not a passed integration test.','Measured interval consistency plus independent causal UI/PID/reason evidence is not proof the kill occurred during the adb command.','Old uncalibrated predecessor remains ineligible.','No recovery, package, scope or release acceptance is inferred.'],'source_edits':False,'runtime_commands':False}
(Q/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'admission':result['admission']}))
