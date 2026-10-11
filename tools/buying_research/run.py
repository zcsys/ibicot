"""Isolated full-world runner. Run with PYTHONPATH=.pydeps:. python -m tools.buying_research.run."""
from __future__ import annotations
import argparse
import json
import resource
import time
from pathlib import Path
import numpy as np

from economy.core import model as M
from economy.kernel.tick import tick as run_tick
from economy.server.runtime import KernelRuntime
from economy.server.persistence import save_checkpoint
from tools.buying_research.provenance import provenance
from tools.buying_research.recording import Recorder
from tools.buying_research.scenarios import Scenario


def summary(values):
    x=np.array(values)*1000
    return dict(medianMs=float(np.median(x)),meanMs=float(x.mean()),p95Ms=float(np.percentile(x,95)),p99Ms=float(np.percentile(x,99))) if len(x) else None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ticks',type=int,default=14400)
    p.add_argument('--seed',type=int,default=137)
    p.add_argument('--cfg',default='{}')
    p.add_argument('--treatment',default='baseline')
    p.add_argument('--options',default='{}',help='Explicit experimental options; never production configuration')
    p.add_argument('--scenario',default='none')
    p.add_argument('--publish-every',type=int,default=30)
    args=p.parse_args()
    cfg=json.loads(args.cfg);cfg['seed']=args.seed
    spec=dict(treatment=args.treatment,ticks=args.ticks,seed=args.seed,configOverrides=cfg,
              researchOptions=json.loads(args.options),scenario=args.scenario,startCheckpoint=None,publishEvery=args.publish_every,window=[1,args.ticks])
    manifest=provenance(args.output,spec)
    try:
        started=time.perf_counter();rt=KernelRuntime(cfg);init=time.perf_counter()-started
        w=rt.world;cfg=rt.cfg;spec['config']=cfg;spec['catalogRevision']=M.CATALOG_REVISION
        (args.output/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
        (args.output/'allocation.json').write_text(json.dumps(dict(
            activeCompanies=cfg['t2FirmCount'],activeLines=int(w.t2LineCount),inputMarkets=M.NI,
            products=[dict(id=p['catalogId'],complexity=p['complexity'],route=p['demandGroup'],
                actualCompanies=int(np.count_nonzero(w.t2LineProduct[:int(w.t2LineCount)]==p['id'])),
                actualDistributors=int(np.count_nonzero(w.distributorProduct[:cfg['distributorCount']]==M.NP+p['id'])))
                for p in M.T2_PRODUCTS]),indent=2)+'\n')
        scenario=Scenario(args.scenario,rt,args.output)
        (args.output/'initial-snapshot.json').write_text(json.dumps(rt.publish())+'\n')
        recorder=Recorder(args.output,w,cfg)
        engine=None
        if args.treatment!='baseline':
            from tools.buying_research.engine import ResearchEngine
            engine=ResearchEngine(rt,args.treatment,args.output,json.loads(args.options))
        steps=[];observations=[];publishes=[];encoding=[];total=[]
        series=open(args.output/'ticks.jsonl','x')
        run_started=time.perf_counter()
        for t in range(1,args.ticks+1):
            scenario.before(t,engine,recorder)
            before=time.perf_counter();old0=w.t0Inv.copy();old1=w.t1Fin.copy()
            start=time.perf_counter()
            if engine is None: run_tick(w,cfg,t,state=rt.state)
            else: engine.step(t,rt.state)
            elapsed=time.perf_counter()-start;steps.append(elapsed)
            rt.tick=t;rt.month=t//30
            rt.lastTickT0Produced[:]=w.t0Inv-old0+w.t0Sold
            rt.lastTickT1Made[:]=w.t1Fin-old1+w.t1Sold
            start=time.perf_counter();recorder.record(w,t,rt.state,old0,old1)
            observations.append(time.perf_counter()-start)
            if t%args.publish_every==0 or t==args.ticks:
                start=time.perf_counter();snap=rt.publish();publishes.append(time.perf_counter()-start)
                start=time.perf_counter();encoded=json.dumps(snap);encoding.append(time.perf_counter()-start)
                if t==args.ticks:(args.output/'final-snapshot.json').write_text(encoded+'\n')
            row=dict(tick=t,stepMs=elapsed*1000,lm1=w.lm1,lm2=w.lm2.tolist(),lm3=w.lm3,
                     aov1=w.aov1,aov2=w.aov2.tolist(),aov3=w.aov3,feeOrders=w.loyaltySwitches.tolist(),
                     fees=w.loyaltyPenalties.tolist(),**recorder.invariants())
            if engine is not None:row['stagesMs']={k:v*1000 for k,v in engine.stages.items()}
            series.write(json.dumps(row)+'\n');total.append(time.perf_counter()-before)
            if t%30==0:
                series.flush()
            if t%360==0 or t==args.ticks or (args.ticks<=120 and t%30==0):
                from economy.core.state import validate_storage
                validate_storage(w,cfg)
                print(json.dumps(dict(tick=t,elapsedSeconds=time.perf_counter()-run_started,
                    medianStepMs=float(np.median(steps[-360:]))*1000,**recorder.invariants())),flush=True)
            if t in (7200,args.ticks):
                save_checkpoint(str(args.output/f'checkpoint-{t:06}'),cfg,t,w,rt.state,rt.checkpoint_metadata())
                if engine is not None:engine.save(args.output/f'research-{t:06}.npz')
        series.close();recorder.flush(w,args.ticks)
        if engine is not None:engine.flush(args.ticks)
        invariants=recorder.invariants()
        valid=all(invariants[k]<=1 for k in ('maxCompanyToleranceRatio','maxMoneyToleranceRatio','maxGoodsToleranceRatio')) and invariants['minStock']>=0 and invariants['minCash']>=0
        manifest.update(status='complete',invariantGate=bool(valid),runtimeSeconds=time.perf_counter()-run_started,
            initializationMs=init*1000,firstTickMs=steps[0]*1000,
            warmTick=summary(steps[1:]),recording=summary(observations),publish=summary(publishes),
            encoding=summary(encoding),fullObservedTick=summary(total[1:]),
            peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,invariants=recorder.invariants())
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc));raise
    finally:
        (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
