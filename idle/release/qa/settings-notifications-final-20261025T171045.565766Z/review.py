from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,re
R=Path('/Users/csys/Desktop/ibicot/idle');Q=Path(__file__).parent
B=R/'release/native-notifications/integration-android-20261025T171117719776Z'
CHECKPOINT=R/'release/native-notifications/resume-20261025-20261025T150516.353584Z/android-revoked-recovery-final-checkpoint.json'
checks=[];pins={};negative=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,name):
 assert ok,name
 checks.append(name)
def pin(p,want=None):
 got=sha(p);check(want is None or got==want,'pin '+str(p.relative_to(R)));pins[str(p.relative_to(R))]=got
 return got
for name,want in json.loads((Q/'intake-pins.json').read_text()).items():pin(R/name,want)
pin(B/'verification.json','a0842c611142eea6a1c6afa0954e0ca06dbc0d0290b1b7f39e62370081efb3c2')
pin(CHECKPOINT,'7c3d066739439ae89038d4c34ae2fa53a8472bcedb5fcaffd2aa860bf2ba176b')
v=json.loads((B/'verification.json').read_text());d=json.loads((B/'result.json').read_text());log=(B/'run.log').read_text();ledger=json.loads(CHECKPOINT.read_text())
check(v['evidence_sha256']==ledger['native_evidence_sha256'],'sealed checkpoint exactly matches native evidence dictionary')
for name,want in v['evidence_sha256'].items():
 check(Path(name).name==name and not (B/name).is_symlink(),'contained actual evidence '+name)
 pin(B/name,want)
for name,want in v['operator_input_pins'].items():pin(Path(name),want)
pin(Path(v['predecessor']['path']),v['predecessor']['sha256'])
module={};exec(compile((B/'reminder_restart.py').read_text(),str(B/'reminder_restart.py'),'exec'),module)
t=ast.parse((B/'verify_native.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='native_log_errors');ns={'re':re};exec(compile(ast.Module(body=[f],type_ignores=[]),'<archived native_log_errors>','exec'),ns)
prior,c=module['validate_predecessor'](v['predecessor']['path'],v,v['source_pins'],next(iter(v['operator_input_pins'])),ns['native_log_errors']);check(True,'full exact reviewed predecessor replay')
check(module['recovery_errors'](d,v,prior,c,log,module['MARKER'],ns['native_log_errors'])==[],'full exact archived recovery validator replay')
check(v['passed'] is True and v['exit_code']==0 and v['errors']==[],'actual strict native report success')
check(ns['native_log_errors'](log)==[],'native framework and driver completion with no late failure')
check(v['production_differences_after']==[] and v['source_differences_during_run']==[] and v['frozen_source_unchanged'] and v['generated_harness_matches'],'actual reported source/frozen/harness integrity')
check(v['production_inputs_before']==prior['production_inputs_before'],'same complete recorded production map as admitted preparation')
check(v['installed_artifact']['matches_host_artifact'] and v['installed_artifact']['sha256'] in v['artifact_after'].values(),'actual installed archive binds built recovery artifact')
for name in ['game/mobile/lib/app.dart','game/mobile/lib/audio_bus.dart','game/mobile/lib/audio_settings.dart','game/mobile/lib/notification_service.dart','game/mobile/lib/notification_settings.dart','game/mobile/lib/notification_copy.dart','game/mobile/lib/reminder_lifecycle.dart','game/mobile/lib/number_format.dart','game/mobile/lib/strings.dart','game/mobile/lib/help_screen.dart','game/mobile/lib/harbor_art.dart','game/persistence/lib/tideglass_persistence.dart']:
 if name in v['production_inputs_before']:pin(R/name,v['production_inputs_before'][name])
check((prior['restart_preparation']['native_pid'],d['process_id'])==(10787,11142),'actual distinct preparation/recovery process IDs')
check(d['pending_before_initialize']==[77101] and d['pending_after_initialize']==[],'actual plugin pending record is canceled by initialization')
check(d['active_before_initialize']==[] and d['active_after_initialize']==[],'actual active records separately observed empty')
check(d['permission_before_initialize']==d['permission_after_initialize']==d['permission_after_reoptin']=='denied','denied before initialization, after initialization, and after re-opt-in')
check(d['remembered_opt_in_after_initialize'] is True and d['preferences_after_reoptin']['enabled'] is False,'remembered preference retained until explicit denied re-opt-in persists disabled')
check(d['recovery_files_before']==c['files_sha256']==d['recovery_files_before_reoptin'],'all prior durable bytes retained through initialization/refused schedule/return')
check(d['recovery_save_files_after']=={k:w for k,w in c['files_sha256'].items() if k.startswith('save/')},'both saved generations retained after denied re-opt-in')
a=json.loads((B/'operator-deny-after-action.json').read_text());node=a['observed_node']
check(node['text']=='Don’t allow' and node['clickable']=='true' and node['enabled']=='true','actual observed OS denial control')
bounds=[int(x) for x in re.findall(r'\d+',node['bounds'])];x,y=map(int,a['argv'][-2:]);check(bounds[0]<=x<=bounds[2] and bounds[1]<=y<=bounds[3],'one tap inside observed OS control')
check(a['pre_image_sha256']==v['evidence_sha256']['operator-deny-before.png'] and a['pre_hierarchy_sha256']==v['evidence_sha256']['operator-deny-before-hierarchy.txt'],'actual pre-action image and hierarchy binding')
check((B/'operator-deny-before-pid.txt').read_text().strip()=='11142','operator prompt binds new recovery PID')
post=json.loads((B/'operator-deny-after-receipts.json').read_text())
check('uiautomator' not in json.dumps(post).lower(),'no post-action accessibility dump in recorded post-action receipts')
for name,(key,value) in {'old_pid':('process_id',10787),'wrong_checkpoint':('predecessor_checkpoint_sha256','0'*64),'permission_allowed':('permission_after_initialize','allowed'),'pending_survives':('pending_after_initialize',[77101]),'save_replaced':('recovery_save_files_after',{}),'fresh_default_substitution':('remembered_opt_in_after_initialize',False),'reoptin_allowed':('permission_after_reoptin','allowed')}.items():
 bad=copy.deepcopy(d);bad[key]=value;errors=module['recovery_errors'](bad,v,prior,c,log,module['MARKER'],ns['native_log_errors']);check(bool(errors),'negative '+name);negative.append({'mutation':name,'errors':errors})
check(bool(ns['native_log_errors'](log+'\nEXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\n')),'late framework failure still rejects')
p=json.loads((Q/'before/program.json').read_text());s=json.loads((Q/'before/scope_requirements.json').read_text());backlog=json.loads((R/'v1_backlog.json').read_text());item=next(x for x in p['items'] if x['id']=='M3-05');original=next(x for x in backlog['items'] if x['id']=='M3-05')
check(item['source_acceptance']==original['acceptance'],'exact original M3-05 acceptance preserved')
check(item['reviewer']=='qa_release' and item['source_acceptance_dependencies']==['M1-05','M3-01'],'named reviewer and original dependencies preserved')
check(all(next(x for x in p['items'] if x['id']==dep)['status']=='accepted' for dep in item['source_acceptance_dependencies']),'both original prerequisites accepted')
check(len(s['requirements'])==44 and len([x for x in p['items'] if x['id'].startswith('M')])==65,'original 65 package and 44 scope records retained')
check(p['product_release_ready'] is False,'release readiness remains false')
for name,want in pins.items():check(sha(R/name)==want,'unchanged at close '+name)
summary={'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'input_pins':pins,'input_pin_count':len(pins),'negative_controls':negative,'recovery_passed':True,'actual_pid_pair':[10787,11142],'predecessor_checkpoint_sha256':d['predecessor_checkpoint_sha256'],'restored_payload_sha256':d['restored_payload_sha256'],'pending_before_after':[d['pending_before_initialize'],d['pending_after_initialize']],'recommendation':{'M3-05':'accept at unchanged original implementation criterion','S26':'verified at unchanged original scope criterion','S02':'retain not_verified; Android actual isolation proven, iOS isolation unproven','S08':'retain not_verified; mandatory physical p95 return performance unproven'},'native_commands_run':False,'flutter_run':False,'production_edits':False,'canonical_edits':False,'whole_release_acceptance':False}
(Q/'verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'negative_controls':len(negative),'recommendation':summary['recommendation']},indent=2))
