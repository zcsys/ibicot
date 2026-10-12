"""Reproducible synthetic screen of the connected continuation candidate."""
import argparse
from dataclasses import asdict,is_dataclass
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
import numpy as np
from .benchmark_phase_search import case
from .continuation_search import solve,SearchLimit


def encode(value):
    if is_dataclass(value):return asdict(value)
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)


def run(spec,out):
    knobs=dict(funding='continuation',storage='arena',max_allocations=spec['maxAllocations'],max_prefixes=spec['maxPrefixes'])
    if spec.get('closingJointFallback',False):knobs['closing_joint_fallback']=True
    if spec.get('sharedRecourseMemoEntries',0):knobs['shared_recourse_memo_entries']=spec['sharedRecourseMemoEntries']
    if spec.get('proofMemoEntries',0):knobs['proof_memo_entries']=spec['proofMemoEntries']
    if spec.get('closingCashRelaxed',False):knobs['closing_cash_relaxed']=True
    if spec.get('prunePrefix',False):knobs.update(prune_prefix=True,shared_first_states=spec.get('sharedFirstStates',0))
    if spec.get('pruneContinuation',False):knobs['prune_continuation']=True
    if spec.get('closing',False):knobs['closing']=True
    if spec.get('closingMemoEntries',0):knobs['closing_memo_entries']=spec['closingMemoEntries']
    if spec.get('fundingMemoEntries',0):knobs['funding_memo_entries']=spec['fundingMemoEntries']
    start=time.perf_counter();solve(*case(1,1,1,1),**knobs)
    (out/'warmup.json').write_text(json.dumps(dict(elapsedSeconds=time.perf_counter()-start,case=[1,1,1,1],scope='Compilation and first solve; excluded from sample timings.'))+'\n')
    rows=[]
    for number,dimensions in enumerate(spec['cases']):
        args=case(**dimensions)
        (out/f'case-{number:02}.json').write_text(json.dumps(dict(company=asdict(args[0]),initial=asdict(args[1]),scenarios=[asdict(p) for p in args[2]]),indent=2)+'\n')
        samples=[];fingerprints=[];last=None
        for repeat in range(spec['repeats']):
            start=time.perf_counter()
            try:
                result=solve(*args,**knobs);status='exact'
            except SearchLimit as exc:
                status='limit';result=dict(reason=str(exc),diagnostics=exc.diagnostics)
            elapsed=(time.perf_counter()-start)*1000
            payload=json.dumps(dict(status=status,result=result),default=encode,sort_keys=True)
            digest=hashlib.sha256(payload.encode()).hexdigest()
            if fingerprints and digest!=fingerprints[0]:raise AssertionError('repeated solve differs')
            samples.append(elapsed);fingerprints.append(digest);last=result
            if repeat==0:(out/f'result-{number:02}.json').write_text(payload+'\n')
        row=dict(case=number,dimensions=dimensions,status=status,samplesMs=samples,medianMs=statistics.median(samples),
            empiricalP95Ms=sorted(samples)[math.ceil(.95*len(samples))-1],fingerprint=fingerprints[0],diagnostics=last['diagnostics'])
        if status=='exact':
            row['value']=last['expectedValue']
            if dimensions['outcomes']==1:
                expected=(13. if dimensions.get('lines',1)==2 else 5.5)*dimensions['capacity']*dimensions['periods']
                if abs(row['value']-expected)>1e-8:raise AssertionError('certain-demand analytical value differs')
        else:row['reason']=last['reason']
        rows.append(row)
        with (out/'rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        print(json.dumps({k:row[k] for k in ('case','dimensions','status','medianMs')}),flush=True)
    (out/'result.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    spec=json.loads(args.spec.read_text());args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'specification.json').write_bytes(args.spec.read_bytes())
    run(spec,args.output)


if __name__=='__main__':main()
