"""Aggregate an explicit campaign with seed-level comparisons, never tick-level SEs."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from .analyze import analyze,ratio


def request_metrics(path,start,end):
    config=Path(path)/'research-config.json'
    if not config.exists():return None
    names=json.loads(config.read_text())['eventFields'];totals=np.zeros((3,len(names)));errors=[];requests=[]
    for f in sorted(Path(path).glob('requests-*.npz')):
        a,b=map(int,f.stem.split('-')[1:]);lo=max(a,start);hi=min(b,end)
        if lo>hi:continue
        with np.load(f,allow_pickle=False) as z:
            s=slice(lo-a,hi-a+1);totals+=z['events'][s].sum(axis=0);requests.append(z['requested'][s])
            if 'forecastErrors' in z:errors.append(z['forecastErrors'][s])
    result=dict(events={tier:dict(zip(names,totals[i].tolist())) for i,tier in enumerate(('T1','T2','T3'))})
    if errors:
        e=np.concatenate(errors)
        result['forecast']={tier:dict(MAE=float(e[:,i,0].mean()),RMSE=float(np.sqrt(e[:,i,1].mean())),
            bias=float(e[:,i,2].mean()),meanPrediction=float(e[:,i,3].mean()),meanFirstIncomingRequests=float(e[:,i,4].mean()))
            for i,tier in enumerate(('T1','T2'))}
    if requests:
        r=np.concatenate(requests);schema=json.loads((Path(path)/'measurement-schema.json').read_text())
        groups={}
        for tier in ('t0','t1','t2'):
            mask=np.array([p['tier']==tier for p in schema['products']]);v=r[:,mask].sum(axis=1)
            groups[tier]=dict(mean=float(v.mean()),variance=float(v.var()),CV=ratio(v.std(),v.mean()))
        result['uniqueRequestVariability']=groups
        result['amplificationCVSquared']={tier:ratio(groups[tier]['CV']**2,groups['t2']['CV']**2)
            if groups[tier]['CV'] is not None and groups['t2']['CV'] is not None else None for tier in ('t0','t1')}
        result['variabilityCaveat']='Aggregate units have different recipe multiplicities. CV ratios normalize scale but include trends and endogenous feedback; no causal bullwhip claim follows.'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--partial',action='store_true');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);jobs=json.loads(a.plan.read_text());summary=[];annual=[];pending=[]
    for job in jobs:
        path=a.root/job['id'];mp=path/'manifest.json'
        manifest=json.loads(mp.read_text()) if mp.exists() else {'status':'not_started'}
        if manifest['status']!='complete':pending.append(dict(id=job['id'],status=manifest['status']));continue
        end=job['ticks'];full=analyze(path,1,end);last=analyze(path,max(1,end-359),end)
        for kind,data,start in (('all',full,1),('lastYear',last,max(1,end-359))):
            data['requests']=request_metrics(path,start,end)
            (a.output/(job['id']+'-'+kind+'.json')).write_text(json.dumps(data,indent=2)+'\n')
        groups={r['group']:r for r in last['groups']};dist={r['tier']+':'+r['route']:r for r in last['companyDistributions']}
        summary.append(dict(**job,sourceIdentity=manifest['sourceIdentity'],invariantGate=manifest.get('invariantGate'),
            invariants=manifest['invariants'],fullObservedTick=manifest['fullObservedTick'],peakRSSBytes=manifest['peakRSSBytes'],
            finalWindow=[last['startTick'],last['endTick']],retailPerTick=groups['t2']['retailUnits']/last['groups'][0]['ticks'],
            netPerTick={t:groups[t]['netEarnings']/groups[t]['ticks'] for t in ('t0','t1','t2')},
            netMargin={t:groups[t]['netMargin'] for t in ('t0','t1','t2')},
            utilization={t:groups[t]['utilization'] for t in ('t0','t1','t2')},
            negativeShare={k:v['negativeShare'] for k,v in dist.items()}))
        for start in range(1,end+1,360):
            stop=min(start+359,end);year=analyze(path,start,stop)
            for row in year['groups']:
                annual.append(dict(run=job['id'],treatment=job['treatment'],seed=job['seed'],start=start,end=stop,**row))
    paired=[]
    for treatment in ('local','market','hybrid'):
        rows=[]
        for seed in (811,1597,2027):
            baseline=next((x for x in summary if x['id']==f'20261011-validation-baseline-{seed}'),None)
            candidate=next((x for x in summary if x['id']==f'20261011-validation-{treatment}-{seed}'),None)
            if baseline is None or candidate is None:continue
            rows.append(dict(seed=seed,retailRatio=candidate['retailPerTick']/baseline['retailPerTick'],
                routeNegativeShareDifference={k:candidate['negativeShare'][k]-baseline['negativeShare'][k] for k in candidate['negativeShare']},
                manufacturerProfitDifference=candidate['netPerTick']['t2']-baseline['netPerTick']['t2']))
        if rows:
            x=np.array([v['retailRatio'] for v in rows]);paired.append(dict(treatment=treatment,seeds=rows,n=len(rows),
                meanRetailRatio=float(x.mean()),rangeRetailRatio=[float(x.min()),float(x.max())],
                seedLevelStandardError=float(x.std(ddof=1)/np.sqrt(len(x))) if len(x)>1 else None,
                caveat='Three held-out seeds provide a limited replication check. Correlated ticks are not independent replicates. Window is final 360 ticks of a 1080-tick run, not a complete generation.'))
    (a.output/'study.json').write_text(json.dumps(dict(runs=summary,paired=paired,pending=pending,
        status='partial' if pending else 'complete'),indent=2)+'\n')
    if annual:
        with (a.output/'annual-groups.csv').open('x',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(annual[0]));writer.writeheader();writer.writerows(annual)
    print(json.dumps(dict(complete=len(summary),pending=len(pending),output=str(a.output))))
    if pending and not a.partial:raise SystemExit('Campaign incomplete; partial aggregates retained and labeled.')


if __name__=='__main__':main()
