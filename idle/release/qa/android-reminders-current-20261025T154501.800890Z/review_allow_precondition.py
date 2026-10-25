from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;P=R/'release/native-notifications/android-enable-preflight-20261025T154330.157706Z';pins={};checks=[]
def read(p):
 p=Path(p);b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(n):return json.loads(read(P/n))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
def xml(n):
 s=read(P/n).decode();return ET.fromstring(s[s.index('<?xml'):s.index('</hierarchy>')+len('</hierarchy>')])
r=j('verification.json');check('exact precondition report',sha(read(P/'verification.json'))=='4075f05717a4f54d206cc62adeff3e550c62015526728690600348d178644584')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(P/n))==h)
identity=j('current-apk-identity.json');denial=R/'release/native-notifications/integration-android-20261025T154133598181Z/verification.json';d=json.loads(read(denial))
check('installed APK binds immediate preceding actual current run',identity['native_verification_sha256']==sha(read(denial)) and identity['apk_sha256']==d['installed_artifact']['sha256']==identity['installed_artifact']['sha256'] and identity['installed_artifact']['matches_host_artifact'])
badging=read(P/'current-apk-badging.txt').decode();check('current APK package and label',"package: name='dev.tideglass.game'" in badging and "application-label:'Tideglass'" in badging and identity['badging_sha256']==sha(read(P/'current-apk-badging.txt')))
drawer=xml('drawer-hierarchy.txt');icons=[x for x in drawer.iter('node') if x.get('text')=='Tideglass'];lower=[x for x in drawer.iter('node') if x.get('text')=='tideglass'];check('unique intended case-sensitive icon distinct from older lowercase app',len(icons)==1 and len(lower)==1 and icons[0].get('bounds')!=lower[0].get('bounds'))
for action,pre in [('icon-menu-action.json','drawer'),('app-info-action.json','icon-menu'),('notifications-action.json','app-info'),('enabled-action.json','notifications')]:
 a=j(action);root=xml(pre+'-hierarchy.txt');matches=[x for x in root.iter('node') if x.attrib==a['observed_node']];check('unique observed action node '+action,len(matches)==1 and matches[0].get('enabled')=='true' and matches[0].get('clickable')=='true')
 check('actual input on owned emulator '+action,a['argv'][1:6]==['-s','emulator-5556','shell','input','touchscreen'] and a['argv'][6] in ['tap','swipe'] and a['exit_code']==0)
 coords=list(map(int,a['argv'][7:]));bounds=list(map(int,re.findall(r'\d+',a['observed_node']['bounds'])));check('action targets recorded current bounds '+action,bounds[0]<coords[0]<bounds[2] and bounds[1]<coords[1]<bounds[3])
 if a['argv'][6]=='swipe':check('long press at same observed point',coords[:2]==coords[2:4] and coords[4]==800 and a['observed_node']==icons[0].attrib)
 check('pre-action screenshot/hierarchy identity '+action,a['pre_image_sha256']==sha(read(P/(pre+'.png'))) and a['pre_hierarchy_sha256']==sha(read(P/(pre+'-hierarchy.txt'))))
 check('approved method '+action,a['lead_method_sha256']=='4b841ade92aee43a7292c07bbaa0e0d1306a9468c840e2318eaf0a43fc0e796a')
before=[x for x in xml('notifications-hierarchy.txt').iter('node') if x.get('resource-id')=='android:id/switch_widget'];after=[x for x in xml('enabled-hierarchy.txt').iter('node') if x.get('resource-id')=='android:id/switch_widget'];check('actual Settings switch false to true',len(before)==len(after)==1 and before[0].get('checked')=='false' and after[0].get('checked')=='true')
beforepackage=read(P/'package.txt').decode();afterpackage=read(P/'package-after.txt').decode();check('exact package actual OS permission denied fixed to allowed', 'android.permission.POST_NOTIFICATIONS: granted=false' in beforepackage and 'USER_FIXED' in beforepackage and 'android.permission.POST_NOTIFICATIONS: granted=true' in afterpackage and 'Package [dev.tideglass.game]' in beforepackage and 'Package [dev.tideglass.game]' in afterpackage)
receipt=j('package-after-receipt.json');check('permission observation is read-only exact package',receipt['argv'][1:]==['-s','emulator-5556','shell','dumpsys','package','dev.tideglass.game'] and receipt['exit_code']==0 and receipt['sha256']==sha(read(P/'package-after.txt')))
check('no inferred visible package URI','no visible package URI claimed' in r['binding'])
check('pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
report={'utc':datetime.now(timezone.utc).isoformat(),'result':'separate_actual_Settings_allow_precondition_supported','checks':checks,'checks_passed':len(checks),'pins':pins,'visual_review':'All five observed screens inspected: unique uppercase Tideglass lighthouse icon (distinct lowercase Flutter app), its App info menu, Tideglass App info with Notifications Off, All Tideglass notifications switch off, then same switch on.','boundary':'Actual Settings precondition after USER_FIXED denial, not a new opt-in prompt or standalone quiet/delivery qualification. Compose Settings extras hide package URI; identity comes from continuous UI chain, exact current APK label/package and exact-package OS permission change.','new_device_or_runtime_execution':False}
(O/'allow-precondition-verification.json').write_text(json.dumps(report,indent=2)+'\n')
(O/'allow-precondition-seal.json').write_text(json.dumps({'files':{n:sha((O/n).read_bytes()) for n in ['review_allow_precondition.py','allow-precondition-verification.json']}},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'pins':len(pins),'verification_sha256':sha((O/'allow-precondition-verification.json').read_bytes()),'seal_sha256':sha((O/'allow-precondition-seal.json').read_bytes())}))
