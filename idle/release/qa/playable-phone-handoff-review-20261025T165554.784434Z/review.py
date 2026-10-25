from pathlib import Path
import json,hashlib,zipfile,plistlib
R=Path(__file__).resolve().parents[3];O=Path(__file__).parent;pins={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p)]=sha(b);return b
def j(p):return json.loads(read(p))
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
P=R/'release/native-proof/playable-phone-handoff-20261025T165004.928296Z';s=j(P/'handoff-seal.json');i=j(P/'installation.json');d=j(P/'data-reconciliation.json');before=j(P/'data-before.json');after=j(P/'data-after.json');expected=j(P/'expected-bundle.json');installed=j(P/'installed-bundle.json')
check('exact terminal handoff seal',sha(read(P/'handoff-seal.json'))=='d3c8374f02542d0848bf1603b8f0818a01a5adef307f0d84d52fa008e128ba6d')
for n,h in s['evidence_sha256'].items():check('sealed '+n,Path(n).name==n and sha(read(P/n))==h)
check('archive exact preserved export',sha(read(i['archive']))==i['archive_sha256']==s['archive_sha256']=='53c296abed7f7906a73a11e028852133b6860e449599f4c3dd5763099a62aa07')
with zipfile.ZipFile(i['archive']) as z:
 files={x.filename.removeprefix('Runner.app/'):sha(z.read(x.filename)) for x in z.infolist() if not x.is_dir()}
 check('archive124 complete identity',files==expected==installed and len(files)==124)
 for name,want in files.items():check('actual installed file '+name,sha(read(Path(i['installed_app'])/name))==want and sha(read(P/'extracted/Runner.app'/name))==want)
 info=plistlib.loads(z.read('Runner.app/Info.plist'));check('bundle exact',info['CFBundleIdentifier']==i['bundle']=='dev.tideglass.game')
changed=[k for k in before if k in after and before[k]!=after[k]];removed=sorted(set(before)-set(after));new=sorted(set(after)-set(before));preserved=sorted(k for k in before if after.get(k)==before[k])
check('exact bounded data-map reconciliation',len(before)==288 and len(after)==284 and len(preserved)==284 and changed==[] and new==[] and removed==sorted(d['removed_files']) and preserved==sorted(d['preserved_existing_files']))
check('four removed OS snapshot caches only',len(removed)==4 and all(k.startswith('Library/SplashBoard/Snapshots/') and k.endswith('.ktx') for k in removed))
check('normal game save slots preserved across install',all(before[k]==after[k] for k in ['Library/Application Support/tideglass/progress.0.json','Library/Application Support/tideglass/progress.1.json']))
check('initial false container result retained',i['data_container_preserved'] is False and d['before_container']!=d['after_container'] and d['installation_report_sha256']==sha(read(P/'installation.json')) and i['existing_data_differences']==removed)
check('recorded installation only no reset',all(x['exit_code']==0 and not any(t in x['argv'] for t in ['erase','uninstall']) for x in j(P/'commands.json')))
ui=j(P/'cua-operator.json');check('observed regular game action receipt',ui['dismissAction']=='clicked actual AX68 Welcome the light' and '129.6K' in ui['observedOfflineReceipt'] and 'Regular Tideglass Harbor visible' in ui['final'])
read('release/qa/current-exports-20261023T043341.519824Z/EXPORT_REVIEW.md');read('implementation/program.json');read('implementation/scope_requirements.json')
check('all review input bytes remain unchanged',all(sha(Path(k).read_bytes())==h for k,h in pins.items()))
v={'checks':checks,'check_count':len(checks),'pins':pins,'handoff_supported':True,'new_acceptance_gate':False,'new_native_execution':False,'data_preservation_limit':'Before/after digest inventories show 284 retained files equal and four OS snapshots removed; original container path changed. No claim that data remained static after actual regular gameplay resumed.','visual_review':['Actual CUA offline summary +129.6K R; 4d6h away, 1d full,2d quarter,1d6h beyond cap','Actual CUA and raw native regular Harbor:272.7K Radiance,+1R/s,1 lightkeeper; first-light onboarding'],'physical_or_store_claim':False};(O/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification':sha((O/'verification.json').read_bytes())}))
