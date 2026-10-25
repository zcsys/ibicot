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
P=R/'release/native-notifications/integration-android-20261025T155657188665Z';CP='release/native-notifications/resume-20261025-20261025T150516.353584Z/android-revoked-checkpoint.json';cp=j(CP);r=j(P/'verification.json');p=j(P/'result.json');log=read(P/'run.log').decode();ns=pure(P)
check('exact failed checkpoint',sha(read(CP))=='a3d1c3fcf480d57114e503ccd670cbd58f32b8d1361183e6b42cff015a1fbcd3')
check('exact failed report',sha(read(P/'verification.json'))==cp['verification_sha256']=='3526106ff508ffe8535a0152a5e22bc756acfcfe57527cc15db8be85f0222ca4')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(P/n))==h==cp['native_evidence_sha256'][n])
for n,h in cp['late_operator_files_sha256'].items():check('late archive '+n,Path(n).name==n and sha(read(P/n))==h)
errors=ns['payload_errors'](p,r,log);check('strict failed classification reproduced',bool(errors) and set(errors)<=set(r['errors']) and r['passed'] is False and r['exit_code']==1 and p['completed'] is False)
check('assertion saw allowed instead of denied','Expected: ReminderPermission:<ReminderPermission.denied>' in log and 'Actual: ReminderPermission:<ReminderPermission.allowed>' in log)
check('actual Settings departure and resumed callback recorded',ns['actual_departure_return'](p['lifecycle_events'],p['actions'],'revoke_in_os_settings_then_return_via_app_icon',0))
check('no successful revocation or retry evidence','permission_after_revoke' not in p and 'revoked_opt_in_stays_disabled' not in p and 'revoke_pending_ids' not in p)
check('source and installed artifact unchanged',r['frozen_source_unchanged'] and r['generated_harness_matches'] and not r['production_differences_after'] and not r['source_differences_during_run'] and r['installed_artifact']['matches_host_artifact'] and r['installed_artifact']['sha256'] in r['artifact_after'].values())
D=R/'release/native-notifications/android-revoked-diagnostics-20261025T155831.658109Z';diag=j(D/'verification.json');check('exact read-only diagnostic',sha(read(D/'verification.json'))=='859ab8e4ac74969ee2158682da836b3697b5e2d88f4cf91e675ce12a79cf0550' and diag['native_report_sha256']==sha(read(P/'verification.json')))
for n,h in diag['files_sha256'].items():check('diagnostic archive '+n,Path(n).name==n and sha(read(D/n))==h)
raw=read(D/'logcat.txt').decode();check('actual Settings opened and drawn','android.settings.APP_NOTIFICATION_SETTINGS' in raw and 'Fully drawn com.android.settings/.Settings$AppNotificationSettingsActivity' in raw)
check('back-preview then close recorded','18:57:45.939' in raw and 'Finishing gesture with event action: 1' in raw and 't=CLOSE' in raw)
check('no diagnosed gesture origin','Origin of that gesture is not established' in ' '.join(diag['facts']))
check('permission remained granted','android.permission.POST_NOTIFICATIONS: granted=true' in read(D/'package.txt').decode())
check('post-failure read has no current PID',read(P/'operator-settings-before-pid.txt')==b'')
check('no recorded test operator input file',not any('action.json' in n for n in list(r['evidence_sha256'])+list(cp['late_operator_files_sha256'])))
check('all pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
out={'utc':datetime.now(timezone.utc).isoformat(),'result':'revocation_failure_preserved_actual_change_unqualified','checks':checks,'checks_passed':len(checks),'pins':pins,'pure_verifier_errors':errors,'visual_inspection':'Late first operator screenshot shows the launcher after terminal failure, not an active Settings switch; empty PID is retained.','cause':'origin of Back/Settings close unestablished; no new Settings crash or production defect concluded','M3_05_S26_acceptance':False,'new_native_device_or_runtime_execution':False};(O/'revoked-failure-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification_sha256':sha((O/'revoked-failure-verification.json').read_bytes())}))
