"""One-sales-phase demand-informed target comparator, not willingness to pay.

Forecast assumptions are explicit inputs. This changes only input targets;
conversion liquidity, margin gates and future buffers remain separate problems.
"""
from dataclasses import replace
import math
from .forecast import Forecast
from .industry_oracle import validate,evaluate
from .funding import replenishment_plan


def plan(problem,forecasts,finished,*,max_nodes=100000):
    validate(problem)
    if len(forecasts)!=len(problem.lines) or len(finished)!=len(problem.lines):
        raise ValueError('one forecast and finished quantity required per installed line')
    required=[0]*len(problem.held);batches=[];expected=[]
    for line,forecast,held in zip(problem.lines,forecasts,finished):
        if not isinstance(forecast,Forecast) or isinstance(held,bool) or not isinstance(held,int) or held<0:
            raise ValueError('invalid forecast or finished quantity')
        if forecast.diagnostics.get('contemplatedQuote')!=line.quote:
            raise ValueError('forecast quote differs from installed line quote')
        if isinstance(forecast.payoff_cap,bool) or not isinstance(forecast.payoff_cap,int) or forecast.payoff_cap<0:
            raise ValueError('invalid fixed payoff cap')
        maximum=line.max_batches*line.output_qty
        if held+maximum>forecast.payoff_cap:
            raise ValueError('forecast cap does not cover existing and feasible new output')
        if (len(forecast.quantities)!=len(forecast.probabilities) or not forecast.quantities
                or any(not math.isfinite(p) or p<0 for p in forecast.probabilities)
                or abs(math.fsum(forecast.probabilities)-1)>1e-12
                or any(isinstance(q,bool) or not isinstance(q,int) or q<0 or q>forecast.payoff_cap for q in forecast.quantities)):
            raise ValueError('invalid forecast distribution')
        # Old finished stock meets each realized demand first. Taking a mean
        # before subtracting old stock would discard useful high-demand states.
        need=math.fsum(prob*min(maximum,max(0,q-held)) for q,prob in zip(forecast.quantities,forecast.probabilities))
        count=min(line.max_batches,math.ceil(need/line.output_qty))
        expected.append(need);batches.append(count)
        for m,q in enumerate(line.recipe):required[m]+=count*q
    slots=tuple(max(held,min(cap,target)) for held,cap,target in zip(problem.held,problem.slots,required))
    targeted=replace(problem,slots=slots)
    funded,allocation=replenishment_plan(targeted,max_nodes)
    outcome=evaluate(funded,tuple(int(q) for q in allocation[0]))
    if outcome is None:raise AssertionError('target comparator returned an infeasible allocation')
    return dict(problem=funded,result=outcome,expectedResidualSales=tuple(expected),
                targetBatches=tuple(batches),inputHoldingTargets=slots,
                fundingBids=funded.bids,quoteQuantities=funded.funded_demands,
                scope='One-phase expected residual sales rounded up to batches, shared recipe inputs summed then clipped to slots. Existing replenishment funding/allocation and actual production gate retained. No conversion reserve, continuation valuation or expected-profit optimality claim.')
