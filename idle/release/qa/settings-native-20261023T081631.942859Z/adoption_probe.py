import copy, hashlib, json
from pathlib import Path
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).resolve().parent
pins={};checks=[]
def read(p):
    p=R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def js(p):return json.loads(read(p))
def sha(p):return hashlib.sha256(read(p)).hexdigest()
def ck(n,v):checks.append({'name':n,'pass':bool(v)})
def out(n,v):(O/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
A='release/qa/lead-daily-challenge-adoption-20261023T080939.226834Z'
d=js(A+'/adoption.json');ck('exact supplied adoption hash',sha(A+'/adoption.json')=='a9b31284f59419a98c7ca6aedb5da4de6a2cb35888ebd733e015080c271da6ab')
beforep=js(A+'/program-before.json');befores=js(A+'/scope-before.json');p=js('implementation/program.json');s=js('implementation/scope_requirements.json');b=js('v1_backlog.json')
out('program-intake.json',p);out('scope-intake.json',s)
for kind,before,after,key,ids,fields in [('program',beforep,p,'items',['M3-01','M3-02','M3-04'],['evidence','evidence_note','status']),('scope',befores,s,'requirements',['S16'],['delivery_status','evidence','verification_note'])]:
    ck(kind+' before hash',sha(A+'/'+kind+'-before.json')==d[kind+'_before_sha256'])
    ck(kind+' after hash',sha('implementation/'+('program.json' if kind=='program' else 'scope_requirements.json'))==d[kind+'_after_sha256'])
    bm={x['id']:x for x in before[key]};am={x['id']:x for x in after[key]}
    delta={i:sorted(k for k in set(bm[i])|set(am[i]) if bm[i].get(k)!=am[i].get(k)) for i in bm if bm[i]!=am[i]}
    ck(kind+' exact field delta',delta=={i:fields for i in ids})
    restored=copy.deepcopy(after)
    for i,x in enumerate(restored[key]):
        if x['id'] in ids: restored[key][i]=bm[x['id']]
    ck(kind+' reverse equality retains all other fields/order',restored==before)
items={x['id']:x for x in p['items']};accepted={x['id'] for x in beforep['items'] if x['status']=='accepted'}
for i in d['accepted_in_order']:
    ck('original dependency order '+i,set(items[i]['source_acceptance_dependencies'])<=accepted)
    accepted.add(i)
for x in b['items']:ck('original clause/deps '+x['id'],items[x['id']]['source_acceptance']==x['acceptance'] and items[x['id']]['source_acceptance_dependencies']==x['dependencies'])
counts={'original_accepted':sum(items[x['id']]['status']=='accepted' for x in b['items']), 'bootstrap_accepted':sum(x['id'].startswith('BOOT-') and x['status']=='accepted' for x in p['items']), 'scope_verified':sum(x['delivery_status']=='verified' for x in s['requirements'])}
ck('expected counts',counts=={'original_accepted':23,'bootstrap_accepted':3,'scope_verified':19})
drifts={}
for name,desc in d['source_reviews'].items():
    folder='release/qa/'+name;seal=js(folder+'/seal.json');ck('source seal '+name,sha(folder+'/seal.json')==desc['seal_sha256']);ck('source output count '+name,len(seal['output_sha256'])==desc['output_count'])
    for path,h in seal['output_sha256'].items():ck('sealed output '+name+'/'+path,sha(folder+'/'+path)==h)
    inputfile='input-sha256.json' if name.startswith('platform') else 'inputs-before.json';ip=js(folder+'/'+inputfile)
    ck('source input count '+name,len(ip)==desc['input_count']);drifts[name]={}
    for path,h in ip.items():
        actual=sha(path)
        if actual!=h:drifts[name][path]={'before':h,'after':actual}
    ck('only adopted metadata drift '+name,set(drifts[name])==({'implementation/program.json'} if name.startswith('platform') else {'implementation/program.json','implementation/scope_requirements.json'}))
    for path,delta in drifts[name].items():
        ck('exact before metadata '+name+' '+path,delta['before']==d['program_before_sha256' if path.endswith('program.json') else 'scope_before_sha256'])
    read(folder+('/REVIEW.md' if name.startswith('platform') else '/READINESS_REVIEW.md'))
read(A+'/DECISIONS.md');v=js(A+'/verification.json');ck('root completed platform reproduction',v['checks_passed']==298 and v['checks_failed']==0 and v['input_drift']==[])
read(A+'/replay.stdout');read(A+'/replay.stderr');read(A+'/checks.json')
out('adoption-current-input-drift.json',drifts);out('adoption-inputs-before.json',pins)
after={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in pins};out('adoption-inputs-after.json',after);ck('all current pins unchanged',pins==after)
out('adoption-verification.json',{'checks':checks,'all_passed':all(x['pass'] for x in checks),'check_count':len(checks),'input_count':len(pins),'counts':counts,'production_or_status_edits':False,'failed':[x['name'] for x in checks if not x['pass']]})
print(json.dumps({'checks':len(checks),'inputs':len(pins),'failed':[x['name'] for x in checks if not x['pass']]},indent=2))
