"""Forecast-to-value adapter for an explicit single closing-sales decision.

This is a separable one-phase comparator, not the multi-phase continuation model.
Funding bids and per-offer caps must already be supplied; none are inferred here.
"""
from dataclasses import replace
import math
from .forecast import Forecast
from .industry_oracle import validate
from .industry_search import solve


def prepare(problem, forecasts, finished, *, product_ids, decision_tick, channel, finished_terminal):
    validate(problem)
    n=len(problem.lines)
    if (not n or any(len(x)!=n for x in (forecasts,finished,product_ids,finished_terminal))
            or len(set(product_ids))!=n):
        raise ValueError('distinct product identities and one forecast per installed line required')
    if problem.funded_demands is None:
        raise ValueError('explicit frozen funded-demand caps required; adapter does not derive funding')
    if not isinstance(decision_tick,int) or isinstance(decision_tick,bool) or decision_tick<1 or not isinstance(channel,str) or not channel:
        raise ValueError('explicit decision timing and channel required')
    lines=[];baselines=[];catalogs=[]
    for line,f,old,pid,terminal in zip(problem.lines,forecasts,finished,product_ids,finished_terminal):
        if (not isinstance(f,Forecast) or not isinstance(old,int) or isinstance(old,bool) or old<0
                or not isinstance(pid,int) or isinstance(pid,bool) or pid<0):
            raise ValueError('invalid forecast or installed product/stock')
        d=f.diagnostics
        if any(d.get(k)!=v for k,v in dict(product=pid,decisionTick=decision_tick,channel=channel,contemplatedQuote=line.quote).items()):
            raise ValueError('forecast does not match installed product, quote or decision')
        latest=d.get('latestPublishedTick')
        if latest is not None and (not isinstance(latest,int) or isinstance(latest,bool) or latest>=decision_tick):
            raise ValueError('unpublished history in forecast')
        catalogs.append(d.get('catalog'))
        maximum=line.max_batches*line.output_qty
        if (not isinstance(f.payoff_cap,int) or isinstance(f.payoff_cap,bool) or f.payoff_cap<old+maximum
                or len(f.quantities)!=len(f.probabilities) or not f.quantities
                or tuple(sorted(set(f.quantities)))!=tuple(f.quantities)
                or any(not isinstance(q,int) or isinstance(q,bool) or q<0 or q>f.payoff_cap for q in f.quantities)
                or any(not math.isfinite(p) or p<0 for p in f.probabilities)
                or abs(math.fsum(f.probabilities)-1)>1e-12):
            raise ValueError('invalid or incomplete fixed forecast distribution')
        if len(terminal)<=old+maximum or any(not math.isfinite(v) for v in terminal):
            raise ValueError('explicit finite terminal values for all remaining finished quantities required')
        def payoff(stock):
            return math.fsum(p*(line.quote*min(stock,q)+terminal[max(0,stock-q)])
                             for q,p in zip(f.quantities,f.probabilities))
        base=payoff(old);baselines.append(base)
        lines.append(replace(line,output_values=tuple(payoff(old+q)-base for q in range(maximum+1))))
    if any(x!=catalogs[0] for x in catalogs):
        raise ValueError('mixed catalog publications')
    valued=replace(problem,lines=tuple(lines));validate(valued)
    return valued,tuple(baselines)


def plan(problem, forecasts, finished, *, product_ids, decision_tick, channel, finished_terminal, max_nodes=100000):
    valued,baseline=prepare(problem,forecasts,finished,product_ids=product_ids,decision_tick=decision_tick,
                           channel=channel,finished_terminal=finished_terminal)
    result,certificate=solve(valued,max_nodes=max_nodes)
    return dict(problem=valued,result=result,certificate=certificate,existingFinishedPayoff=baseline,
        scope='One purchase/production decision then closing sales; explicit frozen funding and terminal values. Marginal expectations suffice only because there is no sales-dependent recourse or shared sales capacity. No multi-phase or world-policy claim.')
