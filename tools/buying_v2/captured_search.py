"""Bounded solver diagnostics on unchanged captured company states.

No forecast calibration or policy adoption. Explicit zero-sale and full-clearance
scenarios bracket illustrative sales assumptions; neither is a prediction.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import shutil
import time
from .prepurchase_projection import project
from .phase_ledger import OpenBook,SettleBook
from .phase_oracle import Scenario
from .quantity_value import LinearQuantityValue
from .continuation_search import solve,SearchLimit
from .benchmark_continuation import encode


def geometry(record):
    p=project(record)
    # Stock/lot Cartesian grid, deliberately before cash/slot/fee constraints.
    return math.prod(o.stock//o.lot+1 for o in p.purchase.offers)


def select(records):
    groups={}
    for record in records:groups.setdefault(record['phase'],[]).append(record)
    selected=[]
    for phase,rows in sorted(groups.items()):
        ordered=sorted(rows,key=lambda r:(geometry(r),r['tick'],r['firm']))
        for role,record in (('minimum-stock-grid',ordered[0]),('maximum-stock-grid',ordered[-1])):
            if any(r['tick']==record['tick'] and r['phase']==phase and r['firm']==record['firm'] for _,r in selected):continue
            selected.append((role,record))
    return selected


def scenario(projection,mode):
    if mode not in ('zero-sales','full-clearance'):raise ValueError('explicit diagnostic sales mode required')
    p=projection;c=p.company;s=p.state
    # Prior committed sales settle once. Later diagnostic sales see fresh output.
    events=(p.purchase,p.settlement((0,)*len(c.lines)),OpenBook('diagnostic-next-book'),
            SettleBook('diagnostic-next-book',tuple(math.ceil(q)+line.max_batches*line.output_qty if mode=='full-clearance' else 0 for q,line in zip(s.finished,c.lines))))
    upper=max(1.,c.storage,*c.slots,*s.held,*s.finished,*c.finished_caps)*2+1
    zero=LinearQuantityValue((0.,upper),(0.,0.))
    return Scenario(1.,events,(zero,)*len(s.held),(zero,)*len(s.finished))


def run(selected,out,*,allocations=4000,work=16000,prune_prefix=False,prune_ranges=False):
    rows=[]
    for index,(role,record) in enumerate(selected):
        (out/f'capture-{index}.json').write_text(json.dumps(record,sort_keys=True)+'\n')
        p=project(record)
        for mode in ('zero-sales','full-clearance'):
            path=scenario(p,mode)
            start=time.perf_counter()
            try:
                result=solve(p.company,p.state,(path,),funding='continuation',storage='arena',max_allocations=allocations,max_prefixes=work,prune_prefix=prune_prefix,prune_ranges=prune_ranges)
                status='exact'
            except SearchLimit as exc:
                result=dict(reason=str(exc),diagnostics=exc.diagnostics);status='limit'
            except (ValueError,OverflowError) as exc:
                result=dict(reason=str(exc),errorType=type(exc).__name__);status='unsupported-or-error'
            elapsed=time.perf_counter()-start
            payload=json.dumps(dict(status=status,result=result),default=encode,sort_keys=True)
            (out/f'result-{index}-{mode}.json').write_text(payload+'\n')
            row=dict(case=index,selection=role,tick=record['tick'],phase=record['phase'],firm=record['firm'],mode=mode,
                     status=status,seconds=elapsed,stockGrid=str(geometry(record)),offers=len(p.purchase.offers),
                     lines=len(p.company.lines),fingerprint=hashlib.sha256(payload.encode()).hexdigest(),
                     diagnostics=result.get('diagnostics'),reason=result.get('reason'))
            rows.append(row)
            with (out/'rows.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            print(json.dumps(row),flush=True)
    (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--allocations',type=int,default=4000);parser.add_argument('--work',type=int,default=16000)
    parser.add_argument('--prune-prefix',action='store_true')
    parser.add_argument('--prune-ranges',action='store_true')
    args=parser.parse_args()
    if args.allocations<1 or args.work<1:parser.error('positive work limits required')
    raw=args.captures.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    manifest=json.loads(args.captures.with_name('manifest.json').read_text())
    if manifest['captureHash']!=digest:raise ValueError('capture hash mismatch')
    records=[r for row in map(json.loads,raw.splitlines()) for r in row['records']]
    chosen=select(records);args.output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[2];hashes={}
    for pattern in ('economy/**/*.py','tools/buying_v2/*.py','tools/buying_research/*.py','tests/py/test_buying*.py','catalogs/midbridge-4259-recursive/*.json','economy/core/catalog.json'):
        for path in root.glob(pattern):
            relative=path.relative_to(root);dest=args.output/'source'/relative
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
            hashes[str(relative)]=hashlib.sha256(path.read_bytes()).hexdigest()
    spec=dict(capturePath=str(args.captures.resolve()),captureHash=digest,records=len(records),selected=len(chosen),
              allocations=args.allocations,work=args.work,prunePrefix=args.prune_prefix,pruneRanges=args.prune_ranges,selection='minimum and maximum stock-grid per phase; not population representative',
              assumptions='One purchase phase; committed settlement; later zero/full-clearance sales at captured quotes; zero terminal values; no new arrivals. Diagnostic only.',
              timing='Single execution per case; includes specialization/compilation where encountered; not warm latency or p95.')
    (args.output/'specification.json').write_text(json.dumps(spec,indent=2)+'\n')
    (args.output/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    run(chosen,args.output,allocations=args.allocations,work=args.work,prune_prefix=args.prune_prefix,prune_ranges=args.prune_ranges)


if __name__=='__main__':main()
