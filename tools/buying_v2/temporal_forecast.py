"""Explicit finite temporal coupling of supplied joint sales forecasts.

Transition probabilities are assumptions supplied by the experiment, never
estimated here. No historical sales are reinterpreted as uncensored demand.
"""
from dataclasses import dataclass
import math
from .joint_forecast import JointForecast


@dataclass(frozen=True)
class TemporalForecast:
    periods: tuple
    tick_offsets: tuple
    dependence: str
    transitions: tuple
    quantities: tuple
    probabilities: tuple


def _integer(x):
    return isinstance(x,int) and not isinstance(x,bool) and x>=0


def _distribution(values):
    if not values or any(isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or p<0 or p>1 for p in values):
        raise ValueError('finite nonnegative temporal probabilities required')
    mass=math.fsum(values)
    if not math.isfinite(mass) or abs(mass-1.)>1e-12:
        raise ValueError('temporal probabilities must sum to one')
    return tuple(p/mass for p in values)


def _validate_period(period):
    if not isinstance(period,JointForecast):raise ValueError('joint forecast periods required')
    if (any(not isinstance(v,tuple) for v in (period.product_ids,period.quotes,period.payoff_caps,period.quantities,period.probabilities))
            or any(not isinstance(row,tuple) for row in period.quantities)):
        raise ValueError('immutable joint forecast metadata and states required')
    n=len(period.product_ids)
    if (not n or any(not _integer(i) for i in period.product_ids) or len(set(period.product_ids))!=n
            or len(period.quotes)!=n or len(period.payoff_caps)!=n
            or any(not _integer(q) for q in period.payoff_caps)
            or any(isinstance(q,bool) or not isinstance(q,(int,float)) or not math.isfinite(q) or q<=0 for q in period.quotes)
            or not _integer(period.decision_tick) or period.decision_tick<1
            or not isinstance(period.channel,str) or not period.channel):
        raise ValueError('invalid temporal identity, quote, cap or publication metadata')
    if (not period.quantities or len(period.quantities)!=len(period.probabilities)
            or any(len(row)!=n or any(not _integer(q) or q>cap for q,cap in zip(row,period.payoff_caps)) for row in period.quantities)
            or len(set(period.quantities))!=len(period.quantities)):
        raise ValueError('invalid or duplicate temporal quantity states')
    return _distribution(period.probabilities)


def couple_periods(periods,*,tick_offsets,transitions,max_scenarios):
    """Construct paths under explicit independence or supplied Markov kernels.

    All forecasts must be made at the same decision tick and in installed-product
    order. Offsets describe target time; they never grant future observations.
    Every transition row corresponds to the supplied preceding atom order.
    """
    periods=tuple(periods);tick_offsets=tuple(tick_offsets)
    if not periods or not _integer(max_scenarios) or max_scenarios<1:
        raise ValueError('nonempty periods and positive temporal scenario budget required')
    marginals=tuple(_validate_period(p) for p in periods)
    if any(p.product_ids!=periods[0].product_ids or p.decision_tick!=periods[0].decision_tick for p in periods):
        raise ValueError('temporal forecasts must share product order and decision tick')
    if (len(tick_offsets)!=len(periods) or any(not _integer(t) for t in tick_offsets)
            or any(b<a for a,b in zip(tick_offsets,tick_offsets[1:]))):
        raise ValueError('nondecreasing whole target tick offsets required')
    if isinstance(transitions,str):
        if transitions!='independent':raise ValueError('explicit supported temporal dependence required')
        dependence='independent'
        kernels=tuple(tuple(marginals[i+1] for _ in marginals[i]) for i in range(len(periods)-1))
    else:
        dependence='supplied-markov'
        try:
            kernels=tuple(tuple(tuple(row) for row in matrix) for matrix in transitions)
        except TypeError as exc:
            raise ValueError('explicit transition matrices required') from exc
        if len(kernels)!=len(periods)-1:raise ValueError('one transition matrix per adjacent period required')
        for i,matrix in enumerate(kernels):
            if len(matrix)!=len(marginals[i]) or any(len(row)!=len(marginals[i+1]) for row in matrix):
                raise ValueError('transition dimensions differ from joint atom order')
        kernels=tuple(tuple(_distribution(row) for row in matrix) for matrix in kernels)
    actual=marginals[0]
    counts=tuple(int(p>0) for p in actual)
    if sum(counts)>max_scenarios:raise ValueError('temporal scenario limit; no sampled approximation returned')
    # Count all positive paths before allocating them. A stochastic row always
    # continues each path; histories are never merged because endpoints match.
    for i,matrix in enumerate(kernels):
        actual=tuple(math.fsum(p*row[j] for p,row in zip(actual,matrix)) for j in range(len(marginals[i+1])))
        if any(abs(a-b)>1e-12 for a,b in zip(actual,marginals[i+1])):
            raise ValueError('transition kernel does not preserve supplied period marginal')
        counts=tuple(sum(count for count,row in zip(counts,matrix) if row[j]>0) for j in range(len(marginals[i+1])))
        if sum(counts)>max_scenarios:raise ValueError('temporal scenario limit; no sampled approximation returned')
    paths=[((j,),p) for j,p in enumerate(marginals[0]) if p>0]
    for matrix in kernels:
        following=[]
        for indices,p in paths:
            for j,conditional in enumerate(matrix[indices[-1]]):
                if conditional==0:continue
                probability=p*conditional
                if probability==0:raise ValueError('temporal probability underflow; no dropped outcome permitted')
                following.append((indices+(j,),probability))
        paths=following
    quantities=tuple(tuple(period.quantities[j] for period,j in zip(periods,indices)) for indices,_ in paths)
    probabilities=tuple(p for _,p in paths)
    return TemporalForecast(periods,tick_offsets,dependence,kernels,quantities,probabilities)


def sales_scenarios(temporal,*,prefixes,labels,suffix,opening_quotes,input_values,finished_values):
    """Insert each hidden sales outcome into an explicit common event calendar.

    Quotes must already be supplied by initial state or explicit SetQuotes events.
    This adapter never changes prices. Offsets must match the number of EndTick
    events before each generated book. Labels and prefixes are common to all paths.
    """
    from .phase_ledger import OpenBook,SettleBook,SetQuotes,EndTick
    from .phase_oracle import Scenario
    if not isinstance(temporal,TemporalForecast):raise ValueError('temporal forecast required')
    if temporal.dependence not in ('independent','supplied-markov') or not temporal.quantities:
        raise ValueError('invalid temporal dependence or empty path distribution')
    checked=couple_periods(temporal.periods,tick_offsets=temporal.tick_offsets,
                           transitions='independent' if temporal.dependence=='independent' else temporal.transitions,
                           max_scenarios=len(temporal.quantities))
    if (checked.quantities!=temporal.quantities or len(checked.probabilities)!=len(temporal.probabilities)
            or any(not isinstance(p,(int,float)) or isinstance(p,bool) or not math.isfinite(p) or p<=0 for p in temporal.probabilities)
            or any(abs(a-b)>1e-12 for a,b in zip(checked.probabilities,temporal.probabilities))):
        raise ValueError('temporal paths disagree with supplied distributions and dependence')
    prefixes=tuple(tuple(p) for p in prefixes);labels=tuple(labels);suffix=tuple(suffix)
    if (len(prefixes)!=len(temporal.periods) or len(labels)!=len(prefixes)
            or any(not isinstance(label,str) or not label for label in labels) or len(set(labels))!=len(labels)
            or len(finished_values)!=len(temporal.periods[0].product_ids)):
        raise ValueError('period calendars, unique labels and terminal product order required')
    quotes=tuple(opening_quotes);offset=0
    for prefix,period,target in zip(prefixes,temporal.periods,temporal.tick_offsets):
        for event in prefix:
            if isinstance(event,SetQuotes):quotes=event.quotes
            if isinstance(event,EndTick):offset+=1
        if offset!=target:raise ValueError('forecast target offset differs from supplied calendar')
        if quotes!=period.quotes:raise ValueError('calendar quote differs from temporal forecast quote')
    scenarios=[]
    for path,probability in zip(temporal.quantities,temporal.probabilities):
        events=[]
        for prefix,label,quantities in zip(prefixes,labels,path):
            events.extend(prefix);events.extend((OpenBook(label),SettleBook(label,quantities)))
        scenarios.append(Scenario(probability,tuple(events)+suffix,tuple(input_values),tuple(finished_values)))
    return tuple(scenarios)
