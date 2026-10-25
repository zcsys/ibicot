from pathlib import Path
import json,hashlib,subprocess,copy
ROOT=Path('/Users/csys/Desktop/ibicot/idle');OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
checks=[];pins={}
def check(name,ok):
 checks.append({'name':name,'pass':bool(ok)})
 if not ok:raise AssertionError(name)
def pin(p):pins[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=sha(p)
def diff(a,b,p=''):
 if a==b:return []
 if isinstance(a,dict) and isinstance(b,dict):return sum((diff(a.get(k),b.get(k),p+'/'+k) for k in sorted(a.keys()|b.keys())),[])
 if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [p]
lead=ROOT/'release/qa/lead-onboarding-acceptance-20261023T041409.400628Z';prior=ROOT/'release/qa/onboarding-clause-20261023T040451.613635Z';adoption=read(lead/'adoption.json');before=read(lead/'before/program.json');after=read(ROOT/'implementation/program.json');oldref=read(lead/'before/program_status_reference.json');newref=read(ROOT/'implementation/art/program_status_reference.json');original=read(ROOT/'v1_backlog.json')
for p in lead.rglob('*'):
 if p.is_file():pin(p)
for f in ['implementation/program.json','implementation/art/program_status_reference.json','implementation/scope_requirements.json','implementation/content/launch_manifest.json','implementation/art/production_contract.json','v1_backlog.json','implementation/tools/validate_program.py']:pin(ROOT/f)
for f,record in adoption['mutations'].items():
 b=lead/'before'/Path(f).name;p=ROOT/f
 check('recorded before hash '+f,sha(b)==record['before']);check('recorded live after hash '+f,sha(p)==record['after'])
idx=next(i for i,x in enumerate(after['items']) if x['id']=='M2-02');expected=[f'/items/{idx}/evidence',f'/items/{idx}/evidence_note',f'/items/{idx}/status']
check('exact program structural delta',diff(before,after)==expected)
check('exact artist reference structural delta',diff(oldref,newref)==['/program_sha256'])
check('artist authoritative program hash',newref['program_sha256']==sha(ROOT/'implementation/program.json'))
check('original artifact contract hash',newref['production_contract_sha256']==sha(ROOT/'implementation/art/production_contract.json'))
check('M2-02 status transition',before['items'][idx]['status']=='in_progress' and after['items'][idx]['status']=='accepted')
for x,y in zip(before['items'],after['items']):
 check(x['id']+' immutable identity/criterion/dependencies/reviewer',all(x[k]==y[k] for k in ['id','source_acceptance','source_acceptance_dependencies','reviewer','owner','scope_ids','source']))
 if x['id']!='M2-02':check(x['id']+' entire unrelated item unchanged',x==y)
items={x['id']:x for x in after['items']}
for x in original['items']:
 check('original clause '+x['id'],items[x['id']]['source_acceptance']==x['acceptance'])
 check('original dependencies '+x['id'],items[x['id']]['source_acceptance_dependencies']==x['dependencies'])
check('original package count',len(original['items'])==65)
for x in ['M1-05','M2-01']:check('accepted prerequisite '+x,items[x]['status']=='accepted')
check('named independent reviewer retained',items['M2-02']['reviewer']=='qa_release')
check('lead uses sealed review',adoption['review_verification_sha256']==sha(prior/'verification.json'))
for f,h in read(prior/'evidence-index.json').items():
 check('sealed independent output '+f,sha(prior/f)==h)
for f,h in read(prior/'inspected-file-pins.json').items():
 p=ROOT/f
 expected_hash=adoption['mutations']['implementation/program.json']['after'] if f=='implementation/program.json' else h
 check('preserved inspected pin '+f,sha(p)==expected_hash)
metadata=read(ROOT/'release/qa/host-gate-repairs-20261023T035209.955242Z/metadata-verification.json')
for f in ['implementation/scope_requirements.json','implementation/content/launch_manifest.json']:
 check('whole prior reviewed file unchanged '+f,sha(ROOT/f)==metadata['changes'][f]['after'])
scope=read(ROOT/'implementation/scope_requirements.json');assets=read(ROOT/'implementation/content/launch_manifest.json')['assets']
check('all44 scope entries remain exact',len(scope['requirements'])==44)
check('all164 asset records remain exact',len(assets)==164)
ids={x['id'] for x in original['items']};counts={'accepted_original':sum(x['id'] in ids and x['status']=='accepted' for x in after['items']),'accepted_bootstrap':sum(x['id'].startswith('BOOT-') and x['status']=='accepted' for x in after['items']),'unaccepted_production_support':sum(x['id'] in ids|{'OPS-14'} and x['status']!='accepted' for x in after['items'])}
check('counts exactly match lead decision',counts==adoption['counts']=={'accepted_original':18,'accepted_bootstrap':3,'unaccepted_production_support':48})
scopecounts={'verified':sum(x['delivery_status']=='verified' for x in scope['requirements']),'unverified':sum(x['delivery_status']=='not_verified' for x in scope['requirements'])};check('unchanged scope counts',scopecounts=={'verified':9,'unverified':35})
# Exactly one requested validator invocation; no Flutter or native execution.
cmd=['python3','implementation/tools/validate_program.py','--self-test'];result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True);(OUT/'program-validation.log').write_text(result.stdout+result.stderr);check('single independent validator exits0',result.returncode==0);check('six mutation rejection tests executed','Rejection tests: 6 checked' in result.stdout)
for f,h in pins.items():check('read-only review preserved '+f,sha(ROOT/f)==h)
(OUT/'structural-delta.json').write_text(json.dumps({'implementation/program.json':diff(before,after),'implementation/art/program_status_reference.json':diff(oldref,newref)},indent=2)+'\n')
(OUT/'inspected-file-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(OUT/'verification.json').write_text(json.dumps({'reviewer':'qa_release','recommendation':'accept bounded metadata adoption','status_edits_by_reviewer':False,'flutter_or_device_commands':False,'checks':checks,'all_passed':True,'counts':counts,'scope_counts':scopecounts,'original_packages':65,'scope_requirements':44,'unchanged_asset_records':164,'validator':{'command':cmd,'exit_code':result.returncode,'log_sha256':sha(OUT/'program-validation.log')}},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'counts':counts,'scope_counts':scopecounts,'verification_sha256':sha(OUT/'verification.json')},indent=2))
