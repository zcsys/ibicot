"""Controlled retail-phase stock/quote probes; never a whole-economy run."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import tarfile
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, validate_storage
from tools.buying_research.provenance import provenance, ROOT, sha
from .forecast import ForecastParameters, PublishedChannel
from .retail_world import clear_distributors
from .observations import empty_totals
from .seller_history import SellerHistory


def world(spec,seed):
    cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=spec['buyers'],distributorActivation=1.,
                          t2ReservationPremium=0.,storage=spec['sellerStorage'],seed=seed))
    w.t2LineProduct[:3]=0
    w.t2Raw.fill(0);w.t2T1Raw.fill(0)
    w.distributorProduct[:]=M.NP;w.distributorPreferredMarket[:]=M.NP
    n=cfg['distributorCount']
    w.distributorQMax[:n]=spec['latentQuantity'];w.distributorEta[:n]=spec['elasticity']
    valuation=M.procurement_profile(M.T2_PRODUCTS[0],cfg,M.reference_tier2_cost(M.T2_PRODUCTS[0],cfg))['valuation']
    w.distributorChoke[:n]=spec['halfPrice']/valuation
    w.lm3=0.
    return cfg,w


def phase(w,cfg,tick,stocks,quotes,compiled=True):
    opening=np.array(stocks,dtype=float);quotes=np.array(quotes,dtype=float)
    w.t2Fin[:3]=opening;w.t2Price[:3]=quotes;w.t2FinBasis[:3]=1.
    validate_storage(w,cfg)
    w.distributorPreferredSupplier[:cfg['distributorCount']]=-1
    before=[getattr(w,name)[:3].copy() for name in ('t2Sold','t2Cash','t2Revenue','t2COGS')]
    exposure=np.zeros((3,3),dtype=np.uint64)
    counts=clear_distributors(w,cfg,tick,empty_totals(M.NP+len(M.T2_PRODUCTS)),compiled=compiled,exposure=exposure)
    sold=w.t2Sold[:3]-before[0];closing=w.t2Fin[:3].copy()
    np.testing.assert_array_equal(opening-closing,sold)
    np.testing.assert_allclose(w.t2Revenue[:3]-before[2],sold*quotes,rtol=0,atol=1e-7)
    np.testing.assert_allclose(w.t2COGS[:3]-before[3],sold,rtol=0,atol=1e-7)
    np.testing.assert_allclose(w.t2Cash[:3]-before[1],sold*quotes,rtol=0,atol=1e-7)
    assert abs(counts[3]-float(sold@quotes))<1e-7
    return dict(opening=opening,closing=closing,sold=sold,quote=quotes,exposure=exposure)


def evaluate(spec,output=None,compiled=True):
    if (not isinstance(spec['buyers'],int) or spec['buyers']<1 or not isinstance(spec['trainingTicks'],int)
            or spec['trainingTicks']<1 or len(spec['trainingQuotes'])!=3 or not spec['seeds']):
        raise ValueError('invalid controlled probe dimensions')
    if any(not math.isfinite(x) or x<=0 for x in (spec['latentQuantity'],spec['elasticity'],spec['halfPrice'],
            spec['ampleStock'],*spec['trainingQuotes'],*spec['targetQuotes'])):
        raise ValueError('invalid probe resources/quotes')
    if any(not isinstance(x,int) or x<0 for x in (spec['ampleStock'],*spec['trainingStocks'].values())):
        raise ValueError('probe stocks must be whole items')
    parameters={k:ForecastParameters(**v) for k,v in spec['profiles'].items()}
    rows=[]
    for seed in spec['seeds']:
        for treatment,stock in spec['trainingStocks'].items():
            cfg,w=world(spec,seed);h=SellerHistory(spec['trainingTicks'])
            for tick in range(1,spec['trainingTicks']+1):
                observed=phase(w,cfg,tick,(stock,spec['ampleStock'],spec['ampleStock']),spec['trainingQuotes'],compiled)
                h.record('retail',tick,np.zeros(3,dtype=np.int64),np.arange(3),np.ones(3),
                         observed['opening'],observed['closing'],observed['quote'],observed['sold'],observed['exposure'])
            if output is not None:
                h.save(output/f'history-{seed}-{treatment}.npz')
                (output/f'config-{seed}-{treatment}.json').write_text(json.dumps(cfg,indent=2)+'\n')
            tick=spec['trainingTicks']+1
            publications={mode:PublishedChannel(h,'retail',tick,feedback=mode) for mode in ('inquiries','transactions')}
            for quote in spec['targetQuotes']:
                predictions=[]
                # Compute all forecasts before measuring target-phase outcomes.
                for feedback,publication in publications.items():
                    for profile,params in parameters.items():
                        for regime in ('local','market','hybrid'):
                            f=publication.forecast(regime,seller=0,product=0,quote=quote,
                                payoff_cap=spec['ampleStock'],market_size=3,parameters=params)
                            predictions.append(dict(feedback=feedback,profile=profile,regime=regime,
                                predicted=f.expected_sales(spec['ampleStock']),diagnostics=f.diagnostics))
                target_quotes=[quote,*spec['trainingQuotes'][1:]]
                target=phase(w,cfg,tick,(spec['ampleStock'],)*3,target_quotes,compiled)
                actual=float(target['sold'][0])
                for p in predictions:p.update(error=p['predicted']-actual)
                rows.append(dict(seed=seed,training=treatment,targetTick=tick,targetQuotes=target_quotes,
                                 actualSales=target['sold'].tolist(),targetExposure=target['exposure'].tolist(),predictions=predictions))
    return dict(scope='Controlled retail-phase fixtures with replenished stock, fixed valuations/quotes, no loyalty fee and reset preferences. Not a closed-loop world, industrial forecast validation or adopted calibration.',specification=spec,rows=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();spec=json.loads(a.spec.read_text());manifest=provenance(a.output,spec)
    paths=set(manifest['sourceHashes'])|{str(x.relative_to(ROOT)) for x in (ROOT/'tools/buying_v2').glob('*.py')}
    manifest['sourceHashes']={name:sha(ROOT/name) for name in sorted(paths)}
    manifest['sourceIdentity']=hashlib.sha256(json.dumps(manifest['sourceHashes'],sort_keys=True).encode()).hexdigest()
    manifest['specificationSha256']=sha(a.spec)
    with tarfile.open(a.output/'source.tar.gz','w:gz') as archive:
        for name in manifest['sourceHashes']:archive.add(ROOT/name,arcname=name)
    (a.output/'specification.json').write_bytes(a.spec.read_bytes())
    try:
        result=evaluate(spec,a.output)
        (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        manifest.update(status='complete',targetPhases=len(result['rows']))
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc));raise
    finally:
        (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
