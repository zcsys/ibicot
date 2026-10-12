"""Retrospective calibration-only scoring, conditional on actual offered stock.

The input specification must exist before evaluation. This does not run a new
buying policy or score latent demand against censored sales.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from .forecast import ForecastParameters, PublishedChannel, VERSION
from .seller_history import SellerHistory


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate(spec):
    source=Path(spec['history'])
    if sha(source)!=spec['historySha256']:
        raise ValueError('history identity changed after calibration specification')
    history=SellerHistory.load(source,expected_tick=spec['historyEndTick'])
    if not spec['channels'] or len(set(spec['channels']))!=len(spec['channels']) or not set(spec['channels'])<=set(history.channels):
        raise ValueError('invalid selected history channels')
    if not isinstance(spec['sellersPerProduct'],int) or spec['sellersPerProduct']<1:
        raise ValueError('seller sample size must be positive')
    first,last=spec['evaluationTicks']
    if first<2 or last>spec['historyEndTick'] or last<first:
        raise ValueError('invalid retrospective calibration window')
    feedback_modes=spec.get('feedbackModes',['inquiries'])
    if not feedback_modes or len(set(feedback_modes))!=len(feedback_modes) or not set(feedback_modes)<= {'inquiries','transactions'}:
        raise ValueError('invalid forecast feedback modes')
    profiles={name:ForecastParameters(**values) for name,values in spec['profiles'].items()}
    rng=np.random.default_rng(spec['samplingSeed'])
    results=[]
    for channel in spec['channels']:
        view=history.view(channel)
        if not np.array_equal(view['ticks'],np.arange(1,spec['historyEndTick']+1)):
            raise ValueError('calibration screen requires complete history from tick 1')
        # Fixed tick-1 sample by product, independent of future sales or errors.
        samples=[]
        for product in np.unique(view['product']):
            ids=np.flatnonzero((view['product']==product)&view['offered'][0].astype(bool))
            count=min(len(ids),spec['sellersPerProduct'])
            if count:
                samples.extend(sorted(rng.choice(ids,size=count,replace=False).tolist()))
        samples=sorted(samples)
        metrics={(feedback,profile,regime):dict(n=0,absoluteError=0.,squaredError=0.,error=0.,actual=0.,predicted=0.,
                    targetConstrained=0,targetNoDiscovery=0,emptyStockExcluded=0,unofferedExcluded=0)
                 for feedback in feedback_modes for profile in profiles for regime in ('local','market','hybrid')}
        for tick in range(first,last+1):
            publications={feedback:PublishedChannel(history,channel,tick,feedback=feedback) for feedback in feedback_modes}
            index=tick-1
            current_offered=view['offered'][index].astype(bool)
            market_sizes=np.bincount(view['product'][current_offered])
            for seller in samples:
                if not current_offered[seller]:
                    for metric in metrics.values():metric['unofferedExcluded']+=1
                    continue
                # Opening stock is recovered by the collector's verified stock
                # identity, and was available at the target phase's entry. This
                # conditions the score on an actual inventory policy; it is not
                # a prediction of counterfactual inventory chosen by a new policy.
                sold=float(view['sold'][index,seller])
                opening=sold+float(view['closingStock'][index,seller])
                cap=int(opening//view['lot']*view['lot'])
                if cap==0:
                    for metric in metrics.values():metric['emptyStockExcluded']+=1
                    continue
                if sold>cap+1e-6:
                    raise ValueError('recorded sales exceed phase stock cap')
                product=int(view['product'][seller])
                for (feedback,profile,regime),metric in metrics.items():
                    forecast=publications[feedback].forecast(regime,seller=seller,product=product,
                        quote=float(view['quote'][index,seller]),payoff_cap=cap,
                        market_size=int(market_sizes[product]),parameters=profiles[profile])
                    predicted=forecast.expected_sales(cap)
                    error=predicted-sold
                    metric['n']+=1;metric['error']+=error;metric['absoluteError']+=abs(error)
                    metric['squaredError']+=error*error;metric['actual']+=sold;metric['predicted']+=predicted
                    metric['targetNoDiscovery']+=int(view['discoveries'][index,seller]==0)
                    metric['targetConstrained']+=int(view['fundedChecks'][index,seller]>0 and
                        (view['shortChecks'][index,seller]>0 or view['closingStock'][index,seller]<view['lot']))
        rows=[]
        for (feedback,profile,regime),metric in metrics.items():
            n=metric['n']
            rows.append(dict(feedback=feedback,profile=profile,regime=regime,observations=n,
                MAE=metric['absoluteError']/n if n else None,RMSE=(metric['squaredError']/n)**.5 if n else None,
                bias=metric['error']/n if n else None,actualItems=metric['actual'],forecastItems=metric['predicted'],
                targetConstrainedObservations=metric['targetConstrained'],targetNoDiscoveryObservations=metric['targetNoDiscovery'],
                emptyStockExcluded=metric['emptyStockExcluded'],unofferedExcluded=metric['unofferedExcluded']))
        results.append(dict(channel=channel,sampledSellerIds=samples,sampledSellerCount=len(samples),scores=rows))
    return dict(forecastVersion=VERSION,results=results,
        scope='Calibration-only sampled seller-phase sales conditional on actual phase-entry stock and quotes. No counterfactual policy, latent-demand accuracy, independent test set or population-weighted claim.',
        specification=spec)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    spec=json.loads(a.spec.read_text())
    # Reserve an exclusive result directory and archive inputs before evaluation.
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'specification.json').write_text(json.dumps(spec,indent=2)+'\n')
    sources={name:Path(__file__).with_name(name) for name in ('forecast.py','forecast_screen.py','seller_history.py')}
    for name,path in sources.items(): (a.output/name).write_bytes(path.read_bytes())
    manifest=dict(status='running',specificationSha256=sha(a.spec),sourceHashes={name:sha(path) for name,path in sources.items()})
    manifest_path=a.output/'manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    start=time.perf_counter()
    try:
        result=evaluate(spec)
        (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        manifest.update(status='complete',runtimeSeconds=time.perf_counter()-start)
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc))
        raise
    finally:
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
