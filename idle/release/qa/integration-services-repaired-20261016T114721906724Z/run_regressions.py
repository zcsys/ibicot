from pathlib import Path
import json,subprocess,datetime,concurrent.futures,hashlib
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).resolve().parent;M=json.loads((O/'snapshot.json').read_text());W=Path(M['workspace'])
def run(name,cmd,cwd):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(cmd,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(O/(name+'.log')).write_text(p.stdout)
 out={'name':name,'command':cmd,'cwd':str(cwd),'start_utc':start,'exit_code':p.returncode,'log':name+'.log'}
 if 'test' in cmd:
  events=[]
  for l in p.stdout.splitlines():
   try:events.append(json.loads(l))
   except:pass
  results=[e for e in events if e.get('type')=='testDone' and not e.get('hidden')]
  out['counts']={s:sum(e['result']==s for e in results) for s in ['success','failure','error']}
 return out
def package(area):
 cwd=W/'game'/area;tool=str(R/'tool'/('flutter' if area=='mobile' else 'dart'));commands=[('pub',[tool,'pub','get']),('test',[tool,'test','--reporter','json']),('analyze',[tool,'analyze'])];result=[]
 for phase,cmd in commands:
  result.append(run(area+'-'+phase,cmd,cwd))
  if result[-1]['exit_code']!=0 and phase=='pub':break
 return result
jobs=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 futures={pool.submit(package,a):a for a in ['core','events','persistence','progression','platform','mobile']}
 for f in concurrent.futures.as_completed(futures):
  results=f.result();jobs+=results;print(futures[f],[(r['name'],r['exit_code'],r.get('counts')) for r in results],flush=True)
python=str(R/'.tooling/services-venv/bin/python')
for name,cmd in [('base-services',[python,'-m','unittest','discover','-s','tests/services','-v']),('provider-author',[python,'-m','unittest','discover','-s','tests/services/providers','-v']),('provider-independent',[python,str(O/'test_independent_providers.py'),str(W)])]:
 jobs.append(run(name,cmd,W));print(name,jobs[-1]['exit_code'],flush=True)
changed=[p for p,h in M['files'].items() if not (W/p).exists() or hashlib.sha256((W/p).read_bytes()).hexdigest()!=h]
result={'source_fingerprint':M['source_fingerprint'],'all_passed':all(j['exit_code']==0 for j in jobs) and not changed,'runs':jobs,'frozen_input_changes':changed,'service_execution_note':'48 base executions include duplicated 22 author cases imported by director review; 26 unique base tests. Eight provider author tests and four independent provider tests are separate.'};(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('ALL_PASSED',result['all_passed'],flush=True)
