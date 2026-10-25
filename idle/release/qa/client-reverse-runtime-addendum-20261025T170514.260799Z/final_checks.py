from pathlib import Path
import hashlib,json
base=Path(__file__).resolve().parent;root=base.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
known=json.loads((base/'known-inputs.json').read_bytes());pins={};checks=[]
def check(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def pin(rel,want=None):
 p=Path(rel) if Path(rel).is_absolute() else root/rel
 h=sha(p);key=str(p.relative_to(root));pins[key]=h
 if want:check(h==want,'exact pin: '+key)
 return p
def read(rel,want=None):return json.loads(pin(rel,want).read_bytes())
for rel,want in known['pins'].items():
 if rel not in ('implementation/program.json','implementation/scope_requirements.json'):pin(rel,want)
program=read('implementation/program.json','46232c53bb334025be9163920b443d43a483821fc1222dcbadd5f9c115346f6d')
scope=read('implementation/scope_requirements.json','9824c7d16f3134b90c23a37be484b048fe8f9b12512ffb3a64299476e2de7bdd')
delta=json.loads((base/'metadata-delta.json').read_bytes());check(len(delta['changes'])==7,'exactly7 approved canonical field changes')
for name in ['program.json','scope_requirements.json']:pin(str(base/'baseline'/name))
adopt_dir='release/qa/lead-settings-adoption-20261025T171709.890699Z'
adopt=read(adopt_dir+'/adoption.json','b6f3e98a1586301e584625df3e992c32e8400be1d411597ca27eb857d85d6199')
check(adopt['before']['program']==sha(base/'baseline/program.json') and adopt['before']['scope']==sha(base/'baseline/scope_requirements.json'),'adoption begins at captured reverse cutoff')
check(pin(adopt_dir+'/program-before.json').read_bytes()==(base/'baseline/program.json').read_bytes(),'lead program before equals independent baseline')
check(pin(adopt_dir+'/scope-before.json').read_bytes()==(base/'baseline/scope_requirements.json').read_bytes(),'lead scope before equals independent baseline')
for rel,want in adopt['inputs'].items():pin(rel,want)
pin(adopt_dir+'/DECISIONS.md',adopt['decisions_sha256'])
for kind in ('structural','release'):pin(adopt_dir+'/'+kind+'.log',adopt['checks'][kind]['log_sha256'])
check(adopt['checks']['structural']['exit_code']==0 and adopt['checks']['release']['exit_code']==1,'structural pass and deliberately unready release gate preserved')
review='release/qa/settings-notifications-final-20261025T171045.565766Z'
ready=read(review+'/verification.json','0c064be69e7500346d3175efe4161a886913753c71cb4f53fea69a69e83945cd')
pin(review+'/READINESS_REVIEW.md','56b0e95862d49b334200a24abd0dcbdeb895fe65fc84d85324d3928f585ff3c5')
pin('release/qa/revoked-preparation-final-20261025T170915.130390Z/REVIEW.md')
pin('release/qa/revoked-preparation-final-20261025T170915.130390Z/verification.json')
folder='release/native-notifications/integration-android-20261025T171117719776Z'
r=read(folder+'/verification.json','a0842c611142eea6a1c6afa0954e0ca06dbc0d0290b1b7f39e62370081efb3c2')
p=read(folder+'/result.json',r['evidence_sha256']['result.json'])
check(r['passed'] is True and r['status']=='passed' and r['exit_code']==0 and r['errors']==[],'fresh recovery strict success')
check(r['production_differences_after']==[] and r['source_differences_during_run']==[] and r['frozen_source_unchanged'],'recovery source integrity')
check(r['candidate_fingerprint']==known['production_fingerprint'],'recovery unchanged3b00 production')
prior=read(r['predecessor']['path'],r['predecessor']['sha256'])
check(prior['passed'] is False and prior['status']=='os-interrupted-awaiting-ui-evidence' and prior['errors']==[],'expected-interrupted predecessor not relabeled pass')
for path,want in r['operator_input_pins'].items():pin(path,want)
check((p['previous_process_id'],p['process_id'])==(10787,11142),'actual new-PID recovery')
check(p['completed'] is True and p['permission_before_initialize']==p['permission_after_initialize']==p['permission_after_reoptin']=='denied','actual denied permission before/after initialization and re-opt-in')
check(p['remembered_opt_in_after_initialize'] is True and p['preferences_after_reoptin']['enabled'] is False,'remembered opt-in valid; denied re-opt-in persists false')
check(p['pending_before_initialize']==[77101] and p['active_before_initialize']==[],'actual pre-initialization pending and active observations distinct')
for field in ['pending_after_initialize','active_after_initialize','denied_schedule_pending_ids','denied_schedule_active_ids','return_pending_ids','return_active_ids']:check(p[field]==[],'actual recovery cleared/blocked '+field)
files=prior['restart_preparation']['files_sha256']
check(p['recovery_files_before']==p['recovery_files_before_reoptin']==files,'exact predecessor save/preferences retained before re-opt-in')
check(p['recovery_save_files_after']=={k:v for k,v in files.items() if k.startswith('save/')},'both exact save generations retained afterward')
clock=prior['restart_death']['clock_model'];check(len(clock['samples'])==6,'fresh prospective pre/post samples retained')
old=read('release/native-notifications/integration-android-20261025T164440025420Z/verification.json','f8d460bebd26e7bb63c61ae609f6dc57606a1b3a22442572c1f9c180eb3a2413')
check('clock_model' not in old['restart_death'] and old['passed'] is False,'old uncalibrated failed-admission packet remains distinct')
android=read('release/qa/lead-android-handoff-20261025T171508.426626Z/review.json')
check(all(android['checks'].values()),'independent Android handoff checks supported')
hand=read(android['handoff'],android['handoff_sha256'])
pin('release/native-proof/playable-android-handoff-20261025T171303.587519Z/playable.png',hand['evidence_sha256']['playable.png'])
terminal=read('release/native-notifications/resume-20261025-20261025T150516.353584Z/terminal-20261025T171507.949495Z/checkpoint.json')
check(terminal['active_native_test_processes']==[] and terminal['qualified_target_count']==10,'native target ledger terminal, no running native test')
for rel,want in terminal['source_sha256'].items():pin(rel,want)
for rel,want in terminal['references_sha256'].items():pin(rel,want)
check(terminal['final_android']['airplane']==0 and terminal['final_android']['wifi']==1 and terminal['final_android']['data']==1 and terminal['final_android']['notifications']=='denied','restored Android radio baseline and honest denied permission')
original=[x for x in program['items'] if x['source']=='v1_backlog.json'];accepted=[x for x in program['items'] if x['status']=='accepted']
check(len(original)==65 and len(program['items'])==69 and len(scope['requirements'])==44,'original65/44 and69 program cardinality unchanged')
check(len([x for x in original if x['status']=='accepted'])==24 and len(accepted)==27,'24 original plus3 bootstrap accepted')
check(len(program['items'])-len(accepted)==42 and len([x for x in scope['requirements'] if x['delivery_status']=='verified'])==20,'42 unaccepted and20of44 verified')
check(program['product_release_ready'] is False,'not a finished release')
(base/'final-input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(base/'final-checks.json').write_text(json.dumps({'checks':checks,'check_count':len(checks),'pins':len(pins),'metadata_delta_fields':len(delta['changes']),'candidate':known['production_fingerprint'],'program':pins['implementation/program.json'],'scope':pins['implementation/scope_requirements.json'],'counts':{'original_packages':65,'original_accepted':24,'bootstrap_accepted':3,'unaccepted_production_support':42,'scope_verified':20,'scope_total':44},'no_runtime_or_broad_retests':True,'no_live_edits':True,'release_ready':False},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'pins':len(pins),'metadata_changes':len(delta['changes']),'passed':True}))
