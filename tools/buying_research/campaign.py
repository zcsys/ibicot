"""Execute a frozen list of isolated research runs; concurrency is not a benchmark.

Each job supplies id, treatment, seed, ticks and optional options/cfg/scenario.
Use workers=1 for matched performance measurements. Outputs are never replaced.
"""
import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path)
    p.add_argument('--workers',type=int,default=3);p.add_argument('--root',type=Path,default=Path('stats/buying-behavior-research'))
    a=p.parse_args();jobs=json.loads(a.plan.read_text())
    def run(job):
        output=(a.root/job['id']).resolve();log=a.root/(job['id']+'.log')
        module=job.get('module','tools.buying_research.run')
        if module not in ('tools.buying_research.run','tools.buying_research.supply_outage','tools.buying_research.local_floor','tools.buying_research.anchor'):
            raise ValueError('unsupported campaign module')
        cmd=[sys.executable,'-m',module,'--output',str(output),'--ticks',str(job['ticks']),
             '--seed',str(job['seed']),'--treatment',job['treatment'],'--scenario',job.get('scenario','none'),
             '--options',json.dumps(job.get('options',{})),'--cfg',json.dumps(job.get('cfg',{}))]
        begin=time.time()
        env=os.environ.copy()
        if 'workspace' in job:env['PYTHONPATH']=str(Path('.pydeps').resolve())+':.'
        with log.open('x') as f:code=subprocess.call(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,cwd=job.get('workspace'))
        result=dict(id=job['id'],returncode=code,elapsedSeconds=time.time()-begin)
        print(json.dumps(result),flush=True);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as executor:
        results=list(executor.map(run,jobs))
    with (a.root/(a.plan.stem+'-results.json')).open('x') as f:json.dump(results,f,indent=2)
    if any(x['returncode'] for x in results):raise SystemExit(1)


if __name__=='__main__':main()
