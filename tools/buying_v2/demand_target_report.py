"""Compare explicit one-phase forecast targets against retained objectives."""
import argparse
from dataclasses import asdict
import hashlib,json,tarfile
from pathlib import Path
from tools.buying_research.provenance import provenance,ROOT,sha
from .forecast import Forecast
from .policy_comparison import cases,compare
from .demand_replenishment import plan


def examples():
    demand={'complementary_inputs_scarce_cash':8,'conversion_cash_reservation':10,
            'weak_realizable_sales':1,'owned_input_history_gate':2,'useful_future_buffer_assumption':0}
    rows={}
    for name,p in cases().items():
        forecasts=tuple(Forecast((demand[name],),(1.,),line.max_batches*line.output_qty,
                                {'contemplatedQuote':line.quote}) for line in p.lines)
        d=plan(p,forecasts,(0,)*len(p.lines))
        policies=compare(p)
        policies['demand_targets']=dict(d['result'],fundedBids=d['fundingBids'],quoteQuantities=d['quoteQuantities'],
            inputHoldingTargets=d['inputHoldingTargets'],targetBatches=d['targetBatches'],expectedResidualSales=d['expectedResidualSales'])
        rows[name]=dict(problem=asdict(p),forecasts=[asdict(f) for f in forecasts],existingFinished=[0]*len(p.lines),policies=policies)
    return dict(scope='Small explicit assumptions, not calibrated forecasts. All outcomes scored with the same original fixture output/terminal tables. Demand targets use only the declared next sales phase and ignore later buffer value.',cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    manifest=provenance(a.output,dict(treatment='demand-target-comparator',calibration='none; supplied analytical cases'))
    paths=set(manifest['sourceHashes'])|{str(x.relative_to(ROOT)) for x in (ROOT/'tools/buying_v2').glob('*.py')}
    manifest['sourceHashes']={name:sha(ROOT/name) for name in sorted(paths)}
    manifest['sourceIdentity']=hashlib.sha256(json.dumps(manifest['sourceHashes'],sort_keys=True).encode()).hexdigest()
    with tarfile.open(a.output/'source.tar.gz','w:gz') as archive:
        for name in manifest['sourceHashes']:archive.add(ROOT/name,arcname=name)
    try:
        result=examples();(a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        manifest['status']='complete'
        for name,row in result['cases'].items():
            print(name,{k:dict(quantities=v['quantities'],outputs=v['outputs'],value=v['value']) for k,v in row['policies'].items()})
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc));raise
    finally:(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
