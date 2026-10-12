"""Bounded phase-planner scaling screen with complete synthetic inputs."""
import argparse
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
import time
import sys
from .industry_oracle import Line,Offer
from .phase_ledger import Company,State,Purchase,OpenBook,SettleBook,EndTick
from .phase_oracle import Scenario,solve,PhaseSearchLimit


def case(capacity,suppliers,periods,outcomes,lines=1):
    if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (capacity,suppliers,periods,outcomes)) or outcomes not in (1,2):
        raise ValueError('positive case dimensions and one/two outcomes required')
    if not isinstance(lines,int) or isinstance(lines,bool) or lines not in (1,2):
        raise ValueError('one or two installed lines required in this screen')
    if lines==2:
        company,initial,paths=case(capacity,suppliers,periods,outcomes)
        slots=(3*capacity,capacity)
        second=Line((2,0),capacity,.5,12.,0.,(0.,)*(capacity+1),2.)
        company=replace(company,slots=slots,storage=12.*capacity,lines=company.lines+(second,),finished_caps=(2*capacity,)*2)
        initial=replace(initial,finished=(0,0),finished_basis=(0.,0.),quotes=(10.,12.))
        extended=[]
        for path in paths:
            events=[]
            for event in path.events:
                if isinstance(event,Purchase):
                    event=replace(event,offers=tuple(replace(o,stock=slots[o.material]) for o in event.offers),active_lines=(0,1))
                elif isinstance(event,SettleBook):event=replace(event,demand=event.demand*2)
                events.append(event)
            extended.append(replace(path,events=tuple(events),input_values=tuple((0.,)*(q+1) for q in slots),finished_values=((0.,)*(2*capacity+1),)*2))
        return company,initial,tuple(extended)
    line=Line((1,1),capacity,.5,10.,0.,(0.,)*(capacity+1),2.)
    company=Company((1.,1.),(capacity,capacity),6.*capacity,(line,),(2*capacity,),0.)
    initial=State(100.*capacity,(0,0),(0.,0.),(0,),(0.,),(10.,),(-1,-1))
    paths=[]
    for outcome in range(outcomes):
        demand=capacity if outcomes==1 or outcome else 0
        events=[]
        for period in range(periods):
            label=f'buy-{period}'
            offers=tuple(Offer(m,s,2.+s,capacity) for m in range(2) for s in range(suppliers))
            events.extend((Purchase(label,offers,(),(0.,)*len(offers),1.,0.,(0,),0.),
                           OpenBook(f'sales-{period}'),SettleBook(f'sales-{period}',(demand,))))
            if period+1<periods:events.append(EndTick(f'end-{period}',.15))
        paths.append(Scenario(1./outcomes,tuple(events),((0.,)*(capacity+1),)*2,((0.,)*(2*capacity+1),)))
    return company,initial,tuple(paths)


def frozen_funding(company,state,event):
    return tuple(max(0,company.slots[o.material]-state.held[o.material]) for o in event.offers)


def evaluate(spec,out):
    trusted_frozen=spec.get('trustedFrozenFunding',False)
    if not isinstance(trusted_frozen,bool):raise ValueError('trusted frozen flag must be boolean')
    rows=[]
    for dimensions in spec['cases']:
        args=case(**dimensions)
        identity='-'.join(str(dimensions[k]) for k in ('capacity','suppliers','periods','outcomes'))
        if dimensions.get('lines',1)!=1:identity+=f"-lines{dimensions['lines']}"
        (out/f'case-{identity}.json').write_text(json.dumps(dict(company=asdict(args[0]),initial=asdict(args[1]),scenarios=[asdict(s) for s in args[2]]),indent=2)+'\n')
        for funding in spec['funding']:
            completed=[]
            for search in spec['search']:
                start=time.perf_counter();row=dict(**dimensions,funding=funding,search=search)
                try:
                    result=solve(*args,funding=('slot-deficit-v1' if trusted_frozen else frozen_funding) if funding=='frozen' else funding,
                                 closing_proposal_memo_size=spec.get('closingProposalMemoSize',0),
                                 joint_bound_memo_size=spec.get('jointBoundMemoSize',0),
                                 cash_relaxed_joint_bound=spec.get('cashRelaxedJointBound',False),
                                 shared_first_joint_states=spec.get('sharedFirstJointStates',0) if search=='feasible-prefix' else 0,
                                 shared_bound_memo_size=spec.get('sharedBoundMemoSize',0) if (funding!='frozen' or trusted_frozen) and search=='feasible-prefix' else 0,
                                 shared_first_batches=spec.get('sharedFirstBatches',0) if (funding!='frozen' or trusted_frozen) and search=='feasible-prefix' else 0,
                                 allocation_search=search,prune_prefix=spec.get('prunePrefix',False) and (funding!='frozen' or trusted_frozen) and search=='feasible-prefix',max_nodes=spec['maxNodes'],max_prefix_nodes=spec['maxPrefixNodes'],funding_memo_size=spec.get('fundingMemoSize',0),
                                 prune_continuation=spec.get('pruneContinuation',False) and (funding!='frozen' or trusted_frozen),
                                 continuation_bound_costs=spec.get('continuationBoundCosts',False), closing_search=spec.get('closingSearch','event-tree'), closing_memo_size=spec.get('closingMemoSize',0))
                    semantic={k:v for k,v in result.items() if k not in ('enumeratedNodes','allocationSearch','prefixSearch','transitionCache','boundAudit','fundingMemo','fundingQueries','fundingObservations','closingSolver')}
                    if completed:assert semantic==completed[0]
                    completed.append(semantic)
                    row.update(status='exact',value=result['expectedValue'],nodes=result['enumeratedNodes'],
                               prefix=result['prefixSearch'],cache=result['transitionCache'],memo=result['fundingMemo'],bound=result['boundAudit'],
                               closing=result['closingSolver'],
                               firstAllocation=result['leaves'][0]['trace'][0]['allocation'])
                    # Certain one/two-period trade has c receipts at $10 per
                    # period and cheapest inputs 2+2 plus .5 conversion per unit.
                    if dimensions['outcomes']==1:
                        unit_profit=13. if dimensions.get('lines',1)==2 else 5.5
                        assert abs(result['expectedValue']-unit_profit*dimensions['capacity']*dimensions['periods'])<1e-8
                except ValueError as exc:
                    if 'node limit; no approximate result returned' not in str(exc):raise
                    row.update(status='limit',reason=str(exc))
                    if isinstance(exc,PhaseSearchLimit):row['limitDiagnostics']=exc.diagnostics
                row['elapsedMs']=(time.perf_counter()-start)*1000;rows.append(row)
                with (out/'rows.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
                print(json.dumps(row),flush=True)
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();spec=json.loads(args.spec.read_text());args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'specification.json').write_bytes(args.spec.read_bytes())
    source=args.output/'source/tools/buying_v2';source.mkdir(parents=True)
    hashes={}
    for name in ('__init__.py','benchmark_phase_search.py','phase_oracle.py','phase_ledger.py','industry_oracle.py','feasible_prefix.py','continuation_bound.py','scenario_validation.py'):
        data=Path(__file__).with_name(name).read_bytes();(source/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    if spec.get('closingSearch','event-tree') != 'event-tree':
        root=Path(__file__).resolve().parents[2]
        dependencies=sorted((root/'tools/buying_v2').glob('*.py'))+sorted((root/'economy').rglob('*.py'))
        dependencies += [root/'economy/core/catalog.json']+[root/'catalogs/midbridge-4259-recursive'/name for name in ('catalog.json','starting-selection.json','naming.json')]
        for path in dependencies:
            relative=path.relative_to(root);target=args.output/'source'/relative
            target.parent.mkdir(parents=True,exist_ok=True);data=path.read_bytes();target.write_bytes(data)
            hashes[str(relative)]=hashlib.sha256(data).hexdigest()
    runtime=dict(python=sys.version)
    if spec.get('closingSearch','event-tree') != 'event-tree':
        import numpy, numba
        runtime.update(numpy=numpy.__version__,numba=numba.__version__)
    manifest=dict(status='running',sourceHashes=hashes,runtime=runtime,specificationSha256=hashlib.sha256(args.spec.read_bytes()).hexdigest())
    try:
        rows=evaluate(spec,args.output);(args.output/'result.json').write_text(json.dumps(rows,indent=2)+'\n');manifest['status']='complete'
    except BaseException as exc:manifest.update(status='failed',error=repr(exc));raise
    finally:(args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
