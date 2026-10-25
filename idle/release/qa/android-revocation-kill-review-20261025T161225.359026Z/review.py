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
P=R/'release/native-notifications/integration-android-20261025T160721674439Z';CP='release/native-notifications/resume-20261025-20261025T150516.353584Z/android-revoked-ready2-checkpoint.json';cp=j(CP);r=j(P/'verification.json');log=read(P/'run.log').decode();ns=pure(P)
check('exact failed checkpoint',sha(read(CP))=='80124ef37b6d5f2418a115701178f15fdbb31a81d9cf8c2c2901aea33d14471a')
check('exact failed report',sha(read(P/'verification.json'))==cp['verification_sha256']=='ed7162a54d8171b93c8c21098a2ffee12c8d04bee93abc1252f5d9b7e302ac8b')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(P/n))==h==cp['native_evidence_sha256'][n])
for n,h in cp['late_operator_files_sha256'].items():check('late archive '+n,Path(n).name==n and sha(read(P/n))==h)
check('native payload absent',not (P/'result.json').exists())
errors=ns['payload_errors']({},r,log);check('strict failure reproduced',bool(errors) and set(errors)<=set(r['errors']) and r['passed'] is False and r['exit_code']==1)
check('driver failed after remote loss','DriverError: Failed to fulfill RequestData due to remote error' in log)
check('source and installed artifact binding retained',r['frozen_source_unchanged'] and r['generated_harness_matches'] and not r['production_differences_after'] and not r['source_differences_during_run'] and r['installed_artifact']['matches_host_artifact'] and r['installed_artifact']['sha256'] in r['artifact_after'].values())
D=R/'release/native-notifications/android-revoked-kill-20261025T160855.867422Z';diag=j(D/'verification.json');check('diagnostic binds exact failure',sha(read(D/'verification.json'))=='c3d3f6524721616b48634a2c89ed215880f48c88ff4df3f196431081b95e3fd2' and diag['native_report_sha256']==sha(read(P/'verification.json')))
for n,h in diag['files_sha256'].items():check('diagnostic archive '+n,Path(n).name==n and sha(read(D/n))==h)
action=j(P/'operator-settings-off-action.json');check('observed current run PID',read(P/'operator-settings-before-pid.txt').strip()==b'7256')
check('actual bounded switch tap',action['argv'][-4:]==['touchscreen','tap','916','1061'] and action['observed_node']['bounds']=='[848,998][985,1124]' and action['observed_node']['checked']=='true' and action['observed_node']['enabled']=='true')
check('tap binds observed hierarchy and image',action['pre_image_sha256']==sha(read(P/'operator-settings-before.png')) and action['pre_hierarchy_sha256']==sha(read(P/'operator-settings-before-hierarchy.txt')))
# Actual UI hierarchy plus screenshot, not command exit, establishes switch state.
import xml.etree.ElementTree as ET
getxml=lambda name:ET.fromstring(re.search(r'(<hierarchy.*</hierarchy>)',read(P/name).decode(),re.S).group(1))
before=[n for n in getxml('operator-settings-before-hierarchy.txt').iter('node') if n.get('resource-id')=='android:id/switch_widget']
after=[n for n in getxml('operator-settings-off-hierarchy.txt').iter('node') if n.get('resource-id')=='android:id/switch_widget']
check('actual settings switch true to false',len(before)==len(after)==1 and before[0].get('checked')=='true' and after[0].get('checked')=='false')
check('actual exact-package permission denied','android.permission.POST_NOTIFICATIONS: granted=false' in read(D/'package.txt').decode())
exitinfo=read(D/'app-exit.txt').decode();raw=read(D/'logcat.txt').decode()
check('OS records permission-change kill on exact PID',bool(re.search(r'timestamp=2026-10-25 19:08:13[.]889 pid=7256.*?process=dev.tideglass.game reason=8 \(PERMISSION CHANGE\).*?description=PermissionHelper',exitinfo,re.S)) and 'Killing 7256:dev.tideglass.game' in raw and 'PermissionHelper' in raw)
check('return shows Settings rather than resumed app',sha(read(P/'operator-return.png'))==sha(read(P/'operator-settings-off.png')) and 'AppNotificationSettingsActivity' in read(P/'operator-return-activities.txt').decode())
check('all pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
output={'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'pins':pins,'pure_failure_errors':errors,'actual_switch_off':True,'OS_permission_change_killed_bound_process':True,'same_process_return_or_cancellation_proven':False,'native_classification':'failed_preserved','product_defect_inferred':False,'production_or_status_writes':False,'new_native_execution':False,'recommendation':'Retain Android revoked unqualified; separately reviewed restart-aware proof needed.'}
(O/'verification.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'sha':sha((O/'verification.json').read_bytes())}))
