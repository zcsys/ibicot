from pathlib import Path
from datetime import datetime
from copy import deepcopy
import ast,json,hashlib,re,types
R=Path(__file__).resolve().parents[3];O=Path(__file__).parent;pins={};checks=[];neg=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=sha(b);return b
def j(p):return json.loads(read(p))
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
P=R/'release/native-proof/offline-operator-20261025T163838.795705Z';cp=j(P/'checkpoint.json');ctx=j(P/'context.json')
check('exact sealed terminal pair',sha(read(P/'checkpoint.json'))=='d7cb2c58a36f6e519f6ff5ad62040b1e6042dbafebb2d6905cc0b7d926648eb1')
for n,h in cp['operator_files_sha256'].items():check('operator archive '+n,Path(n).name==n and sha(read(P/n))==h)
L=Path(ctx['listener'])
for n,h in cp['listener_files_sha256'].items():check('listener archive '+n,sha(read(L/n))==h)
full=read(L/'listener.jsonl');journal=[json.loads(x) for x in full.splitlines()];check('contiguous complete journal',list(range(1,len(journal)+1))==[x['sequence'] for x in journal]);check('listener stopped',journal[-1]['type']=='stopped')
rows=[]
for row in cp['rows']:
 B=Path(row['report']).parent;r=j(B/'verification.json');p=j(B/'result.json');s=j(B/'os-snapshots.json');profile=j(B/'network-profile.json');log=read(B/'run.log').decode();prefix=read(B/'listener-prefix.jsonl');jr=[json.loads(x) for x in prefix.splitlines()]
 check('report pin '+row['scenario'],sha(read(B/'verification.json'))==row['sha256'])
 for n,h in r['evidence_sha256'].items():check(row['scenario']+' archive '+n,Path(n).name==n and sha(read(B/n))==h==row['evidence_sha256'][n])
 check(row['scenario']+' strict result',r['passed'] is True and r['exit_code']==0 and r['verification_errors']==[])
 check(row['scenario']+' pinned source',r['source_snapshot_unchanged'] and r['production_inputs_match_snapshot'] and r['production_input_differences_after_run']==[] and r['harness_source_differences_during_run']==[] and r['harness_sha256']['harness.dart']==ctx['source_pins']['platform_smoke_offline_test.dart'] and r['harness_sha256']['offline_support.py']==ctx['source_pins']['offline_support.py'] and r['runner_sha256']==ctx['source_pins']['verify_offline_native.py'])
 ns={'__name__':'qa_readonly_offline','__file__':str(B/'offline_support.py')};exec(compile(read(B/'offline_support.py'),str(B/'offline_support.py'),'exec'),ns)
 runner=ast.parse(read(B/'verify_native.py'));node=next(x for x in runner.body if isinstance(x,ast.FunctionDef) and x.name=='native_log_errors');ln={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'archived-log-validator','exec'),ln)
 check(row['scenario']+' independent framework verifier',ln['native_log_errors'](log)==[])
 check(row['scenario']+' immutable prefix of actual healthy listener',full.startswith(prefix))
 prior=rows[0]['payload'] if rows else None
 q=ns['qualify'](p,profile,jr,s,prior);check(row['scenario']+' actual pure qualification replay',q==r['offline_qualification'])
 check(row['scenario']+' checkpoint actual bytes',sha(read(B/'native-checkpoint.json'))==p['offline_network']['checkpoint_sha256'])
 check(row['scenario']+' only local endpoint',p['offline_network']['endpoint']=='10.0.2.2:'+str(profile['port']) and all(x.get('error_type') in ('SocketException','TimeoutException') for x in p['offline_network']['samples'] if x.get('reachable') is False))
 check(row['scenario']+' late framework failure rejected',bool(ln['native_log_errors'](log+'\nEXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK\n')))
 rows.append({'dir':B,'report':r,'payload':p,'snapshots':s,'profile':profile,'journal':jr,'ns':ns,'qualification':q})
a,b=rows;pa,pb=a['payload'],b['payload'];states=[a['qualification']['states'],b['qualification']['states']]
check('new actual native process',pa['process_id']==9280 and pb['process_id']==9798 and pa['process_id']!=pb['process_id'])
check('exact successful predecessor link',j(b['dir']/'predecessor.json')=={'path':str(a['dir']/'verification.json'),'sha256':sha(read(a['dir']/'verification.json'))})
check('same guest directory profile and checkpoint',pa['save_directory']==pb['save_directory'] and a['profile']==b['profile'] and read(a['dir']/'native-checkpoint.json')==read(b['dir']/'native-checkpoint.json'))
c=j(a['dir']/'native-checkpoint.json');check('actual purchase and price deduction',pa['before_core']['counts']==[1,0,0,0,0] and pa['after_core']['counts']==[2,0,0,0,0] and int(pa['after_core']['lifetime_micros'])-int(pa['after_core']['wallet_micros'])==33600000 and pa['elapsed_milliseconds']>=35000)
check('checkpoint recovered with allowed elapsed earnings',pb['before_core']['counts']==c['core']['counts'] and all(int(pb['before_core'][k])>=int(c['core'][k]) for k in ['lifetime_micros','wallet_micros']))
check('radio baseline exact restoration',all(states[0]['before-online'][k]==states[1]['after-restored'][k] for k in ['airplane','wifi','data']) and states[1]['after-restored']['default']!='none')
check('actual offline raw three retained',all(states[i][k]=={'airplane':'1','wifi':'3','data':'1','default':'none'} for i in [0,1] for k in ['offline-ready','offline-complete']))
for prefix,wanted in [('disable','false'),('restore','true')]:
 action=j(P/(prefix+'-airplane-action.json'));node=action['observed_node'];nums=list(map(int,re.findall(r'\d+',node['bounds'])));x,y=map(int,action['argv'][-2:]);check(prefix+' actual observed tile action',node['package']=='com.android.systemui' and node['checked']==wanted and nums[0]<=x<=nums[2] and nums[1]<=y<=nums[3] and action['pre_image_sha256']==sha(read(P/(prefix+'-expanded.png'))) and action['pre_hierarchy_sha256']==sha(read(P/(prefix+'-expanded-hierarchy.txt'))))
 ret=j(P/(prefix+'-return-action.json'));check(prefix+' current icon observed before return',ret['observed_node']['text']=='Tideglass' and ret['pre_image_sha256']==sha(read(P/(prefix+'-home.png'))) and ret['pre_hierarchy_sha256']==sha(read(P/(prefix+'-home-hierarchy.txt'))))
 receipt_rows=[]
 for f in P.glob(prefix+'-*-receipts.json'):receipt_rows+=j(f)
 check(prefix+' no post-return UiAutomation',all('uiautomator' not in x.get('argv',[]) or datetime.fromisoformat(x['utc'])<datetime.fromisoformat(ret['utc']) for x in receipt_rows))
# Bounded synthetic mutations of the actual successful pair; no native commands.
def reject(name,payload=None,snapshots=None,journal=None,predecessor=None):
 try:b['ns']['qualify'](payload or pb,b['profile'],b['journal'] if journal is None else journal,snapshots or b['snapshots'],pa if predecessor is None else predecessor)
 except (ValueError,KeyError,AssertionError) as e:neg.append({'name':name,'error':str(e)});check('negative '+name,True)
 else:check('negative '+name,False)
p=deepcopy(pb);p['process_id']=pa['process_id'];p['offline_network']['process_id']=pa['process_id'];reject('same PID',payload=p)
p=deepcopy(pb);p['offline_network']['checkpoint_sha256']='0'*64;reject('wrong checkpoint',payload=p)
p=deepcopy(pb);next(x for x in p['offline_network']['samples'] if x['phase']=='bootstrap')['reachable']=True;reject('reachable during actual bootstrap',payload=p)
reject('missing independent listener health',journal=[x for x in b['journal'] if x['type']!='health'])
p=deepcopy(pb)
for x in p['offline_network']['samples']:
 if x['phase']=='after-restored' and x['reachable'] is True:x['reachable']=False;x['error_type']='SocketException'
reject('no actual restored reachability',payload=p)
for path,want in [('release/native-proof/integration-android-offline-20261025T160235.910710Z/verification.json','db58df8f44328ee257b34f97970133dc7ac9f96ead1a0753db9f90a337efa8c8'),('release/native-proof/integration-android-offline-20261025T162255.665708Z/verification.json','5b1e4511de154bc04e266f4ab5fd286ed2e18e749986a5836a75cccb3dd21284')]:check('prior failure preserved '+path,sha(read(path))==want and j(path)['passed'] is False)
for f in ['implementation/program.json','implementation/scope_requirements.json','V1_ROADMAP.md','release/qa/lead-offline-wifi-review-20261025T161131.010939Z/decision.json','release/qa/scope-forward-final-20261023T085127.503162Z/scope-matrix.json']:read(f)
check('inputs unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
result={'checks':checks,'check_count':len(checks),'pins':pins,'negative_controls':neg,'actual_android_offline_pair_supported':True,'S02_recommendation':'Keep not_verified: bounded Android airplane-mode guest flow is proven; iOS actual network isolation remains unproven. Existing unchanged localization/optional-cloud separation proofs are retained, not re-executed.','authorship':'QA authored staged offline harness/helper; root independently reviewed/reproduced them before execution. This packet independently audits native_verifier actual execution and raw operator evidence; no self-approval of staged implementation.','new_native_execution':False,'source_changes':False}
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification_sha256':sha((O/'verification.json').read_bytes())}))
