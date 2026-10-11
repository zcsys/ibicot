"""Measure a mature saved world in isolation, preserving its original evidence.

Run only after competing simulation/test processes finish. Compilation/loading is
reported separately. This runner writes new observations and cannot replace its
source checkpoint. It supports baseline and the unmodified R1 information regimes.
"""
import argparse
import json
import resource
import os
import re
import subprocess
import time
from pathlib import Path
import numpy as np
from economy.kernel.tick import tick as run_tick
from economy.server.runtime import KernelRuntime
from economy.server.persistence import load_checkpoint,save_checkpoint
from economy.core.state import validate_storage
from .engine import ResearchEngine
from .provenance import provenance,sha
from .recording import Recorder
from .run import summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--tick',type=int,required=True);p.add_argument('--ticks',type=int,default=360)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();meta=json.loads((source/'manifest.json').read_text());spec=meta['specification']
    # The first preserved baseline predates explicit scenario/options fields.
    if spec.get('scenario','none')!='none' or spec.get('researchOptions',{}):
        raise ValueError('benchmark requires ordinary matched regime')
    rc=source/'research-config.json'
    if rc.exists() and json.loads(rc.read_text())['options'].get('salesFloor',False):
        raise ValueError('This benchmark runner does not restore the sales-floor subclass')
    # Queued measurements must not accidentally start alongside a later-added
    # campaign. Wait for other research workers; never interrupt their evidence.
    pattern=re.compile(r'-m tools\.buying_research\.(run|campaign|local_floor|supply_outage|anchor)(?:\s|$)')
    announced=False
    while True:
        processes=subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines()
        busy=[line.strip() for line in processes if pattern.search(line) and int(line.split()[0])!=os.getpid()]
        if not busy:break
        if not announced:print(json.dumps(dict(status='waiting_for_other_research_workers',processes=busy)),flush=True);announced=True
        time.sleep(30)
    checkpoint=source/f'checkpoint-{a.tick:06}';sidecar=source/f'research-{a.tick:06}.npz'
    sources={str(checkpoint)+suffix:sha(str(checkpoint)+suffix) for suffix in ('.json','.npz')}
    if spec['treatment']!='baseline':sources[str(sidecar)]=sha(sidecar)
    manifest=provenance(a.output,dict(treatment=spec['treatment'],seed=spec['seed'],startCheckpoint=str(checkpoint),
        sourceHashes=sources,ticks=a.ticks,window=[a.tick+1,a.tick+a.ticks],publishEvery=30,
        scenario='none',researchOptions={},benchmarkOnly=True,requiresIsolatedExecution=True))
    try:
        began=time.perf_counter();cfg,t,w,state=load_checkpoint(str(checkpoint))
        if t!=a.tick:raise ValueError('checkpoint tick mismatch')
        rt=KernelRuntime(cfg);rt.world=w;rt.state=state;rt.tick=t;rt.month=t//30
        (a.output/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
        engine=None
        if spec['treatment']!='baseline':
            options=json.loads((source/'research-config.json').read_text())['options']
            engine=ResearchEngine(rt,spec['treatment'],a.output,options);engine.restore(sidecar)
            if engine.last_tick!=t:raise ValueError('world/information checkpoint tick mismatch')
        recorder=Recorder(a.output,w,cfg);recorder.period_start=t+1
        initialized=time.perf_counter()-began;step=[];observe=[];publish=[];encode=[];total=[]
        series=(a.output/'ticks.jsonl').open('x');begin=time.perf_counter()
        for tick in range(t+1,t+a.ticks+1):
            started=time.perf_counter();old0=w.t0Inv.copy();old1=w.t1Fin.copy();now=time.perf_counter()
            if engine is None:run_tick(w,cfg,tick,state=state)
            else:engine.step(tick,state)
            step.append(time.perf_counter()-now);rt.tick=tick;rt.month=tick//30
            rt.lastTickT0Produced[:]=w.t0Inv-old0+w.t0Sold;rt.lastTickT1Made[:]=w.t1Fin-old1+w.t1Sold
            now=time.perf_counter();recorder.record(w,tick,state,old0,old1);observe.append(time.perf_counter()-now)
            if tick%30==0 or tick==t+a.ticks:
                now=time.perf_counter();snap=rt.publish();publish.append(time.perf_counter()-now)
                now=time.perf_counter();encoded=json.dumps(snap);encode.append(time.perf_counter()-now)
                if tick==t+a.ticks:(a.output/'final-snapshot.json').write_text(encoded+'\n')
            series.write(json.dumps(dict(tick=tick,stepMs=step[-1]*1000,lm1=w.lm1,lm2=w.lm2.tolist(),lm3=w.lm3,
                aov1=w.aov1,aov2=w.aov2.tolist(),aov3=w.aov3,**recorder.invariants()))+'\n')
            total.append(time.perf_counter()-started)
            if tick%30==0:series.flush()
            if tick%120==0:print(json.dumps(dict(tick=tick,elapsedSeconds=time.perf_counter()-begin)),flush=True)
        series.close();recorder.flush(w,tick)
        if engine is not None:engine.flush(tick);engine.save(a.output/f'research-{tick:06}.npz')
        validate_storage(w,cfg);save_checkpoint(str(a.output/f'checkpoint-{tick:06}'),cfg,tick,w,state,rt.checkpoint_metadata())
        inv=recorder.invariants();valid=all(inv[k]<=1 for k in ('maxCompanyToleranceRatio','maxMoneyToleranceRatio','maxGoodsToleranceRatio')) and inv['minCash']>=0 and inv['minStock']>=0
        manifest.update(status='complete',invariantGate=bool(valid),initializationMs=initialized*1000,
            runtimeSeconds=time.perf_counter()-begin,firstTickMs=step[0]*1000,warmTick=summary(step[1:]),recording=summary(observe),
            publish=summary(publish),encoding=summary(encode),fullObservedTick=summary(total[1:]),
            peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,invariants=inv)
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc));raise
    finally:(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(output=str(a.output),fullObservedTick=manifest['fullObservedTick'],invariantGate=manifest['invariantGate'])))


if __name__=='__main__':main()
