"""Explicit finite dependence scenarios for distinct products in one sales phase.

Neither independence nor common-quantile dependence is an adopted forecast.
No scenario sampling or truncation silently replaces the supplied marginals.
"""
from bisect import bisect_right
from dataclasses import dataclass
from itertools import product
import math
from .forecast import Forecast


@dataclass(frozen=True)
class JointForecast:
    product_ids: tuple
    quotes: tuple
    payoff_caps: tuple
    decision_tick: int
    channel: str
    dependence: str
    quantities: tuple
    probabilities: tuple


def couple(forecasts,*,dependence,max_scenarios):
    if dependence not in ('independent','common-quantile'):
        raise ValueError('explicit supported dependence assumption required')
    if not isinstance(max_scenarios,int) or isinstance(max_scenarios,bool) or max_scenarios<1 or not forecasts:
        raise ValueError('positive scenario budget and nonempty forecasts required')
    marginals=[];ids=[];quotes=[];caps=[];ticks=[];channels=[]
    for f in forecasts:
        if not isinstance(f,Forecast):raise ValueError('forecast required')
        d=f.diagnostics
        identity=d.get('product');tick=d.get('decisionTick');channel=d.get('channel');quote=d.get('contemplatedQuote')
        if (not isinstance(identity,int) or isinstance(identity,bool) or identity<0
                or not isinstance(tick,int) or isinstance(tick,bool) or tick<1 or not isinstance(channel,str) or not channel
                or not isinstance(quote,(float,int)) or not math.isfinite(quote) or quote<=0):
            raise ValueError('invalid forecast identity, quote or publication metadata')
        last=d.get('latestPublishedTick')
        if last is not None and (not isinstance(last,int) or last>=tick):raise ValueError('forecast includes unpublished history')
        if (not isinstance(f.payoff_cap,int) or isinstance(f.payoff_cap,bool) or f.payoff_cap<0
                or len(f.quantities)!=len(f.probabilities) or not f.quantities
                or any(not isinstance(q,int) or isinstance(q,bool) or q<0 or q>f.payoff_cap for q in f.quantities)
                or tuple(sorted(set(f.quantities)))!=tuple(f.quantities)
                or any(not math.isfinite(p) or p<0 for p in f.probabilities)):
            raise ValueError('invalid marginal distribution')
        total=math.fsum(f.probabilities)
        if abs(total-1)>1e-12:raise ValueError('marginal probabilities must sum to one')
        marginals.append(tuple((q,p/total) for q,p in zip(f.quantities,f.probabilities) if p>0))
        ids.append(identity);quotes.append(float(quote));caps.append(f.payoff_cap);ticks.append(tick);channels.append(channel)
    if len(set(ids))!=len(ids):raise ValueError('distinct owned product forecasts required')
    if len(set(ticks))!=1 or len(set(channels))!=1:raise ValueError('joint forecasts must share decision tick and sales channel')
    quantities=[];probabilities=[]
    if dependence=='independent':
        if math.prod(len(m) for m in marginals)>max_scenarios:
            raise ValueError('joint scenario limit; no sampled approximation returned')
        for atoms in product(*marginals):
            probability=math.prod(p for q,p in atoms)
            if probability==0:raise ValueError('joint probability underflow; no dropped outcome permitted')
            quantities.append(tuple(q for q,p in atoms));probabilities.append(probability)
    else:
        cumulative=[];cuts={0.,1.}
        for marginal in marginals:
            bounds=[min(1.,math.fsum(p for q,p in marginal[:i])) for i in range(1,len(marginal))]
            if any(right<=left for left,right in zip([0.]+bounds,bounds+[1.])):
                raise ValueError('joint cumulative precision loss; no dropped outcome permitted')
            cumulative.append(bounds);cuts.update(bounds)
        cuts=sorted(cuts)
        if len(cuts)-1>max_scenarios:raise ValueError('joint scenario limit; no sampled approximation returned')
        for left,right in zip(cuts,cuts[1:]):
            quantities.append(tuple(m[bisect_right(bounds,left)][0] for m,bounds in zip(marginals,cumulative)))
            probabilities.append(right-left)
    return JointForecast(tuple(ids),tuple(quotes),tuple(caps),ticks[0],channels[0],dependence,
                         tuple(quantities),tuple(probabilities))


def sales_scenarios(joint,*,prefix,label,suffix,input_values,finished_values):
    """One uncertain sales event between an explicit shared calendar prefix/suffix.

    Product order must match company installed-line order. Quotes remain supplied
    company-state inputs; this helper neither sets prices nor reveals outcomes.
    """
    from .phase_ledger import OpenBook,SettleBook
    from .phase_oracle import Scenario
    if not isinstance(joint,JointForecast) or len(finished_values)!=len(joint.product_ids):
        raise ValueError('joint product order must match terminal finished tables')
    return tuple(Scenario(prob,tuple(prefix)+(OpenBook(label),SettleBook(label,q))+tuple(suffix),
                          tuple(input_values),tuple(finished_values)) for q,prob in zip(joint.quantities,joint.probabilities))
