from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,subprocess
R=Path('/Users/csys/Desktop/ibicot/idle');Q=Path(__file__).parent;A=R/'release/qa/lead-settings-adoption-20261025T171709.890699Z'
checks=[];pins={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,n):
 assert ok,n
 checks.append(n)
def pin(p,w=None):
 got=sha(p);check(w is None or got==w,'pin '+str(p.relative_to(R)));pins[str(p.relative_to(R))]=got
 return got
pin(A/'adoption.json','b6f3e98a1586301e584625df3e992c32e8400be1d411597ca27eb857d85d6199');a=json.loads((A/'adoption.json').read_text())
for p,w in a['inputs'].items():pin(R/p,w)
pin(A/'DECISIONS.md',a['decisions_sha256'])
pin(A/'program-before.json',a['before']['program']);pin(A/'scope-before.json',a['before']['scope'])
pin(R/'implementation/program.json',a['after']['program']);pin(R/'implementation/scope_requirements.json',a['after']['scope'])
old=json.loads((A/'program-before.json').read_text());new=json.loads((R/'implementation/program.json').read_text());os=json.loads((A/'scope-before.json').read_text());ns=json.loads((R/'implementation/scope_requirements.json').read_text())
check([x['id'] for x in old['items']]==[x['id'] for x in new['items']],'all 69 program IDs/order unchanged')
allowed={'M3-05':{'status','evidence','evidence_note'}};changes={}
for x,y in zip(old['items'],new['items']):
 fields={k for k in set(x)|set(y) if x.get(k)!=y.get(k)}
 if fields:changes[x['id']]=sorted(fields)
 check(fields<=allowed.get(x['id'],set()),'only declared program fields '+x['id'])
for k in set(old)|set(new):
 if k!='items':check(old.get(k)==new.get(k),'program top-level unchanged '+k)
check(changes=={'M3-05':['evidence','evidence_note','status']},'exact sole item change')
check(next(x for x in new['items'] if x['id']=='M3-05')['status']=='accepted','M3-05 accepted')
check([x['id'] for x in os['requirements']]==[x['id'] for x in ns['requirements']],'44 original scope IDs/order unchanged')
sallowed={'S26':{'delivery_status','evidence'},'S02':{'evidence'},'S08':{'evidence'}};schanges={}
for x,y in zip(os['requirements'],ns['requirements']):
 fields={k for k in set(x)|set(y) if x.get(k)!=y.get(k)}
 if fields:schanges[x['id']]=sorted(fields)
 check(fields<=sallowed.get(x['id'],set()),'only declared scope fields '+x['id'])
for k in set(os)|set(ns):
 if k!='requirements':check(os.get(k)==ns.get(k),'scope top-level unchanged '+k)
check(schanges=={'S02':['evidence'],'S08':['evidence'],'S26':['delivery_status','evidence']},'exact scope changes')
check(next(x for x in ns['requirements'] if x['id']=='S26')['delivery_status']=='verified','S26 verified')
check(all(next(x for x in ns['requirements'] if x['id']==i)['delivery_status']=='not_verified' for i in ['S02','S08']),'S02/S08 remain unverified')
backlog=json.loads((R/'v1_backlog.json').read_text());original={x['id'] for x in backlog['items']};pin(R/'v1_backlog.json')
counts={'accepted_original':sum(x['id'] in original and x['status']=='accepted' for x in new['items']),'accepted_bootstrap':sum(x['id'].startswith('BOOT') and x['status']=='accepted' for x in new['items']),'unaccepted_production_support':sum(x['id'] in original|{'OPS-14'} and x['status']!='accepted' for x in new['items']),'verified_scope':sum(x['delivery_status']=='verified' for x in ns['requirements']),'scope_total':len(ns['requirements'])}
# Bootstrap IDs are intentionally identified by the original program records.
counts['accepted_bootstrap']=sum(x['id'] not in original|{'OPS-14'} and x['status']=='accepted' for x in new['items'])
check(counts==a['counts']=={'accepted_original':24,'accepted_bootstrap':3,'unaccepted_production_support':42,'verified_scope':20,'scope_total':44},'exact final counts')
check(new['product_release_ready'] is False,'release readiness remains false')
# Existing immutable forward audit pins bind art records without new art review.
for path in ['implementation/art/production_contract.json','implementation/art/program_status_reference.json','implementation/content/launch_manifest.json']:
 pin(R/path)
priorpins=json.loads((R/'release/qa/scope-forward-final-20261023T085127.503162Z/final-input-pins.json').read_text())
# Preserve data as a reference rather than reinterpret historical status-reference snapshot.
pin(R/'release/qa/scope-forward-final-20261023T085127.503162Z/final-input-pins.json')
for file in ['structural.log','release.log']:pin(A/file,a['checks'][file.split('.')[0]]['log_sha256'])
validation={}
for mode,argv,want in [('structural',['python3','implementation/tools/validate_program.py'],0),('release',['python3','implementation/tools/validate_program.py','--release'],1)]:
 result=subprocess.run(argv,cwd=R,text=True,capture_output=True);(Q/(mode+'.log')).write_text(result.stdout+result.stderr);check(result.returncode==want,'independent '+mode+' validator expected exit');validation[mode]={'argv':argv,'exit_code':result.returncode}
check((Q/'release.log').read_text().splitlines()==['FAIL: Unaccepted production/support work: 42 items','FAIL: Unverified product requirements: 24'],'release rejection contains exactly remaining original scope/work counts')
terminal=R/'release/native-notifications/resume-20261025-20261025T150516.353584Z/terminal-20261025T171507.949495Z/checkpoint.json';pin(terminal,'79f586f99cbc0d11702cdeab027b87311f529d0081bce35dce5bde836d5f5170');t=json.loads(terminal.read_text());check(t['qualified_target_count']==10 and t['active_native_test_processes']==[],'terminal native checkpoint records ten cases and no active test process')
for p,w in t['references_sha256'].items():pin(R/p,w)
handoff=R/'release/qa/lead-android-handoff-20261025T171508.426626Z/review.json';pin(handoff,'a4f7769d4208faf8fd71e73cf81ccf6dc537db1b376bf6c648d8af17007141de');h=json.loads(handoff.read_text());check(all(h['checks'].values()),'different-author root handoff review records all checks passing');pin(R/h['handoff'],h['handoff_sha256'])
pin(R/'release/qa/playable-phone-handoff-review-20261025T165554.784434Z/REVIEW.md','9a7d888a8222a07581b80a7f36fc98f50d698c41991b77714df808b46418cbf6')
for p,w in pins.items():check(sha(R/p)==w,'unchanged at seal '+p)
v={'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'input_pins':pins,'input_pin_count':len(pins),'program_delta':changes,'scope_delta':schanges,'counts':counts,'validators':validation,'canonical_program_sha256':a['after']['program'],'canonical_scope_sha256':a['after']['scope'],'recommendation':'Accept exact narrow metadata adoption and append to sealed forward audit; release remains unready','native_execution':False,'source_edits':False,'canonical_edits':False}
(Q/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ['check_count','input_pin_count','counts','program_delta','scope_delta']},indent=2))
