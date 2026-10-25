from pathlib import Path
import ast,json,hashlib,re,types,copy,xml.etree.ElementTree as ET
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;pins={};checks=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
node=next(n for n in ast.parse(read('release/qa/settings-native-20261023T081631.942859Z/replay_reminder_initial.py')).body if isinstance(n,ast.FunctionDef) and n.name=='pure');exec(compile(ast.Module(body=[node],type_ignores=[]),'preserved-pure-extractor','exec'))
folder=R/'release/native-notifications/integration-android-20261025T154133598181Z';checkpoint='release/native-notifications/resume-20261025-20261025T150516.353584Z/android-denied-ready3-checkpoint.json';cp=j(checkpoint);r=j(folder/'verification.json');p=j(folder/'result.json');log=read(folder/'run.log').decode();ns=pure(folder)
check('exact checkpoint',sha(read(checkpoint))=='1353cde446580ea80206dbac4830c4c1c412d2e1da8750e1ca5fb5b33cfdaea0')
check('exact native report',sha(read(folder/'verification.json'))==cp['verification_sha256']=='8888701c7606b6e8afc14547fa1ea05050c92fbdab153d567f1385e96cfec504')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(folder/n))==h==cp['native_evidence_sha256'][n])
for n,h in cp['late_operator_files_sha256'].items():check('late operator archive '+n,Path(n).name==n and sha(read(folder/n))==h)
check('source identity',all(r['source_pins'][n]==r['evidence_sha256'][n] for n in r['source_pins']))
check('strict native and driver completion',ns['payload_errors'](p,r,log)==[] and r['passed'] and r['exit_code']==0 and not r['errors'])
check('actual owned platform',r['device']=='emulator-5556' and r['platform']=='android' and p['process_id']==4797)
check('production unchanged',r['frozen_source_unchanged'] and r['generated_harness_matches'] and not r['production_differences_after'] and not r['source_differences_during_run'])
m=j(folder/'candidate-manifest.json');check('production before exact frozen candidate',len(r['production_inputs_before'])==482 and all(m['source_sha256'][f]==h for f,h in r['production_inputs_before'].items()))
check('installed artifact is actual built APK',r['installed_artifact']['matches_host_artifact'] and r['installed_artifact']['sha256'] in r['artifact_after'].values())
check('actual denial leaves opt-out with no pending request',p['permission_after_opt_in']=='denied' and p['preferences_after_opt_in']['enabled'] is False and p['denied_pending_ids']==[])
a=j(folder/'operator-deny-action.json');marker=p['actions'][0]
check('same current marker and PID',a['native_pid']==p['process_id'] and a['marker_utc_ms']==marker['utc_ms'] and marker['action']=='deny_permission_if_prompted')
check('fresh native PID observation',read(folder/'operator-deny-before-pid.txt').decode().strip()==str(p['process_id']))
acts=read(folder/'operator-deny-before-activities.txt').decode()
check('permission dialog belongs to live task75 current PID',all(t in acts for t in ['4797:dev.tideglass.game','launchedFromPackage=dev.tideglass.game','resultTo=ActivityRecord{3b01670 u0 dev.tideglass.game/.MainActivity t75}','GrantPermissionsActivity t75']))
def hierarchy(name):
 s=read(folder/name).decode();return ET.fromstring(s[s.index('<?xml'):s.index('</hierarchy>')+len('</hierarchy>')])
before=hierarchy('operator-deny-before-hierarchy.txt');after=hierarchy('operator-deny-after-hierarchy.txt');nodes=[x for x in before.iter('node') if x.get('resource-id')==a['node']['resource-id']]
check('unique current enabled denial button',len(nodes)==1 and nodes[0].attrib==a['node'] and nodes[0].get('enabled')=='true' and nodes[0].get('clickable')=='true' and nodes[0].get('text')=='Don’t allow')
b=list(map(int,re.findall(r'\d+',a['node']['bounds'])));x,y=a['coordinates'];check('actual tap inside observed control',b[0]<x<b[2] and b[1]<y<b[3])
check('actual input event, no permission API bypass',a['argv'][1:]==['-s','emulator-5556','shell','input','touchscreen','tap',str(x),str(y)] and a['exit_code']==0 and a['operator']=='Automated actual Android OS UI tap')
check('pre-action visual identity',a['pre_hierarchy_sha256']==sha(read(folder/'operator-deny-before-hierarchy.txt')) and a['pre_image_sha256']==sha(read(folder/'operator-deny-before.png')))
check('after UI removed prompt and returned current app',not any(x.get('package')=='com.google.android.permissioncontroller' for x in after.iter('node')) and any(x.get('package')=='dev.tideglass.game' for x in after.iter('node')))
check('real lifecycle returned from permission UI',p['lifecycle_events'][0]['state']=='inactive' and p['lifecycle_events'][-1]['state']=='resumed' and not p['lifecycle_callback_failures'])
actms=datetime.fromisoformat(a['utc']).timestamp()*1000;check('actual decision within original150second window',0<actms-marker['utc_ms']<150000)
for n in ['operator-deny-before-receipts.json','operator-deny-after-receipts.json']:
 for v in j(folder/n):
  check(n+':'+v['file'],v['argv'][1:3]==['-s','emulator-5556'] and v['exit_code']==0 and sha(read(folder/v['file']))==v['sha256'])
method='docs/quality/android-ui-operator.md';review='release/qa/client-android-ui-procedure-20261025T153851.062431Z/REVIEW.md'
check('prospectively approved method',sha(read(method))==a['lead_method_sha256']=='4b841ade92aee43a7292c07bbaa0e0d1306a9468c840e2318eaf0a43fc0e796a')
check('different-author procedure approval',sha(read(review))=='f54589031e9a103cd15e1455f2ac3004dcb3d319a77c7f4ef78dbbcccb9e6067')
negative=[]
for label,mutation in [('wrong-run',lambda x:x.update(run_id='wrong-run')),('incomplete',lambda x:x.update(completed=False)),('enabled-after-denial',lambda x:x['preferences_after_opt_in'].update(enabled=True)),('pending-after-denial',lambda x:x.update(denied_pending_ids=[77101])),('allowed-instead',lambda x:x.update(permission_after_opt_in='allowed'))]:
 bad=copy.deepcopy(p);mutation(bad);errors=ns['payload_errors'](bad,r,log);check('reject '+label,bool(errors));negative.append({'mutation':label,'errors':errors})
check('reject late error',bool(ns['payload_errors'](p,r,log+'\nI/flutter (4797): Unhandled Exception: independent negative control\n')))
check('source and receipts unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
(O/'denied-verification.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'result':'denied_actual_OS_path_supported','checks':checks,'checks_passed':len(checks),'negative_controls':negative,'late_error_control':True,'pins':pins,'action_delta_from_marker_ms':actms-marker['utc_ms'],'visual_inspection':'Raw before image visibly contains Allow Tideglass to send you notifications? with Allow and Don’t allow. Raw after image has no permission sheet and displays the reminder qualification app. Actual UI tap is an automated SDK gesture, not a human or CUA event.','remaining_scenarios':['quiet-cancel','delivery','revoked'],'physical_banner_or_usability_claim':False,'new_native_device_or_runtime_execution':False},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'pins':len(pins),'action_delta_ms':actms-marker['utc_ms'],'verification_sha256':sha((O/'denied-verification.json').read_bytes())}))
