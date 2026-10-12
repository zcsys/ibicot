"""Isolated raw-state sampling with independent phase-settlement reconciliation."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K
from economy.server.runtime import KernelRuntime
from tools.buying_research.provenance import provenance, ROOT, sha
from .engine import IndustrialReferenceEngine
from .industrial_adapter import buy_t2_reference
from .decision_traces import DecisionTrace
from .prepurchase_state import capture_t2


class CaptureEngine(IndustrialReferenceEngine):
    def __init__(self, runtime, sample_size, sink):
        super().__init__(runtime)
        self.sample_size, self.sink = sample_size, sink

    def operate_manufacturers(self, w, cfg, tick):
        for phase in M.TIER_BOUNDARIES['T2']:
            sample = DecisionTrace(cfg['t2FirmCount'],self.sample_size,cfg['seed'],tick,2,phase)
            chosen = set(map(int,sample.firms))
            overhead = K.production_line_overhead(w,cfg,'t2')
            records, settlement, sellers = {}, [], []
            def purchase(w,c,t,f,p,b):
                if f in chosen:
                    records[f] = capture_t2(w,c,t,f,p,b,overhead)
                return buy_t2_reference(w,c,t,f,p,b,observations=self.industrial_observations)
            def observe(book):
                supplier_ids=sorted({o['supplier'] for r in records.values() for m in r['offers'] for o in m['suppliers']})
                for supplier in supplier_ids:
                    tier='t1' if supplier<book.n1 else 't2'
                    line=supplier if tier=='t1' else supplier-book.n1
                    owner=int(book.owner[supplier]);firm=owner if tier=='t1' else owner-M.N1
                    sellers.append(dict(supplier=supplier,tier=tier,line=line,firm=firm,
                        cashBefore=float(getattr(w,tier+'Cash')[firm]),
                        cashDelta=float(book.cash[owner]-book._cash_initial[owner]),
                        unitsBefore=float(getattr(w,tier+'Fin')[line]),
                        basisBefore=float(getattr(w,tier+'FinBasis')[line]),
                        sold=float(book._initial['fin'][supplier]-book.fin[supplier]),
                        soldBasis=float(book.basis[supplier])))
                # Independently reconcile sampled sellers, including newly produced
                # goods at their live averaged basis. This is before book.settle().
                for f in sorted(records):
                    owner=M.N1+f
                    row=dict(firm=f,cashBefore=float(w.t2Cash[f]),
                             cashDelta=float(book.cash[owner]-book._cash_initial[owner]),lines=[])
                    for line in records[f]['installedLines']:
                        supplier=book.n1+line
                        sold=float(book._initial['fin'][supplier]-book.fin[supplier])
                        row['lines'].append(dict(line=line,unitsBefore=float(w.t2Fin[line]),
                            basisBefore=float(w.t2FinBasis[line]),sold=sold,
                            soldBasis=float(book.basis[supplier])))
                    settlement.append(row)
            K._operate_tier2_phase(w,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,tick,phase,
                                  purchase_company=purchase,phase_observer=observe)
            for row in settlement:
                f=row['firm'];row['cashAfter']=float(w.t2Cash[f])
                np.testing.assert_allclose(row['cashAfter'],row['cashBefore']+row['cashDelta'],rtol=1e-12,atol=1e-9)
                for item in row['lines']:
                    line=item['line'];item['unitsAfter']=float(w.t2Fin[line]);item['basisAfter']=float(w.t2FinBasis[line])
                    expected_units=item['unitsBefore']-item['sold']
                    expected_value=item['unitsBefore']*item['basisBefore']-item['sold']*item['soldBasis']
                    np.testing.assert_allclose(item['unitsAfter'],expected_units,rtol=1e-12,atol=1e-9)
                    np.testing.assert_allclose(item['unitsAfter']*item['basisAfter'],expected_value,rtol=1e-12,atol=1e-8)
            for item in sellers:
                tier=item['tier'];line=item['line'];firm=item['firm']
                item['cashAfter']=float(getattr(w,tier+'Cash')[firm])
                item['unitsAfter']=float(getattr(w,tier+'Fin')[line])
                item['basisAfter']=float(getattr(w,tier+'FinBasis')[line])
                np.testing.assert_allclose(item['cashAfter'],item['cashBefore']+item['cashDelta'],rtol=1e-12,atol=1e-9)
                np.testing.assert_allclose(item['unitsAfter'],item['unitsBefore']-item['sold'],rtol=1e-12,atol=1e-9)
                np.testing.assert_allclose(item['unitsAfter']*item['basisAfter'],item['unitsBefore']*item['basisBefore']-item['sold']*item['soldBasis'],rtol=1e-12,atol=1e-8)
            self.sink(dict(tick=tick,phase=phase,sampling='systematic-hash-rotation-v1',
                           requested=sorted(chosen),missing=sorted(chosen-records.keys()),
                           records=list(records.values()),settlement=settlement,sellerSettlement=sellers,reconciled=True))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ticks',type=int,required=True)
    parser.add_argument('--sample',type=int,default=8)
    parser.add_argument('--cfg',default='{}')
    args=parser.parse_args()
    if args.ticks<1 or args.sample<1: parser.error('positive ticks/sample required')
    overrides=json.loads(args.cfg)
    spec=dict(treatment=IndustrialReferenceEngine.policy,configOverrides=overrides,
              ticks=args.ticks,sample=args.sample,startCheckpoint=None,window=[1,args.ticks])
    manifest=provenance(args.output,spec)
    paths=set(manifest['sourceHashes'])
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'tools/buying_v2').glob('*.py'))
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'tests/py').glob('test_buying*.py'))
    hashes={p:sha(ROOT/p) for p in sorted(paths)}
    manifest.update(sourceHashes=hashes,sourceIdentity=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest())
    with tarfile.open(args.output/'source.tar.gz','w:gz') as archive:
        for p in hashes: archive.add(ROOT/p,arcname=p)
    try:
        rt=KernelRuntime(overrides)
        (args.output/'config.json').write_text(json.dumps(rt.cfg,indent=2)+'\n')
        count=0
        with (args.output/'captures.jsonl').open('x') as stream:
            def sink(row):
                nonlocal count
                stream.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\n');stream.flush()
                count+=len(row['records'])
            engine=CaptureEngine(rt,args.sample,sink)
            for tick in range(1,args.ticks+1):
                engine.step(tick)
                print(json.dumps(dict(tick=tick,captured=count)),flush=True)
        manifest.update(status='complete',captured=count,allSampledSettlementsReconciled=True,
                        captureHash=sha(args.output/'captures.jsonl'),
                        caveat='Raw sampled startup states under isolated D3. Not population inference, adopted forecast or solver execution.')
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc));raise
    finally:
        (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__': main()
