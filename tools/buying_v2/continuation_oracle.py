"""Small exact two-period counterfactual for buffer-value validation.

This is a perfect-information scenario benchmark, not a production forecast.
No sales receipts arrive between purchase decisions. Closing demand buys goods
at the specified future quote; remaining finished goods have zero terminal value.
Both periods retain cash, lots, stock, storage, basis and ordered production gates.
Loyalty fees are excluded explicitly rather than pretending preferences persist
through arbitrary future decisions. Real fee behavior is tested separately.
"""
from dataclasses import replace
from itertools import product
import math
from .industry_oracle import evaluate,solve,validate


def continuation(initial,future,finished_caps,closing_demand,allocation,max_allocations=1000000,demand_scenarios=None):
    if len(initial.lines)!=len(future.lines) or len(finished_caps)!=len(initial.lines) or len(closing_demand)!=len(initial.lines):
        raise ValueError('line/scenario dimensions differ')
    if any(initial.fees) or any(future.fees):
        raise ValueError('this continuation benchmark excludes loyalty fees')
    if initial.spaces!=future.spaces or initial.slots!=future.slots:
        raise ValueError('input technology/storage cannot change between periods')
    if any(q<0 or q!=int(q) for q in (*finished_caps,*closing_demand)):
        raise ValueError('invalid final demand or finished slots')
    scenarios=((1.,tuple(closing_demand)),) if demand_scenarios is None else tuple(demand_scenarios)
    if not scenarios or any(not math.isfinite(weight) or weight<0 or len(d)!=len(initial.lines)
            or any(not math.isfinite(q) or q<0 or q!=int(q) for q in d) for weight,d in scenarios) \
            or abs(sum(weight for weight,d in scenarios)-1.)>1e-12:
        raise ValueError('invalid closing-demand distribution')
    # First-period output remains inventory; assigning it current revenue as
    # well as closing sale proceeds would double count it.
    first=replace(initial,lines=tuple(replace(line,output_values=(0.,)*len(line.output_values)) for line in initial.lines),
                  terminal_values=tuple((0.,)*len(row) for row in initial.terminal_values))
    validate(first);validate(future)
    now=evaluate(first,allocation)
    if now is None:
        return None
    lines=[]
    for i,(old,new) in enumerate(zip(initial.lines,future.lines)):
        if old.recipe!=new.recipe or old.output_qty!=new.output_qty or old.output_space!=new.output_space:
            raise ValueError('recipe technology cannot change between periods')
        existing=now['outputs'][i]
        if existing>finished_caps[i]:
            return None
        bounds=min(new.max_batches,(finished_caps[i]-existing)//new.output_qty)
        values=tuple(new.quote*sum(weight*min(d[i],existing+q) for weight,d in scenarios) for q in range(bounds*new.output_qty+1))
        lines.append(replace(new,max_batches=bounds,output_values=values))
    occupied_change=sum((q-h)*s for q,h,s in zip(now['remaining'],initial.held,initial.spaces))
    occupied_change+=sum(q*line.output_space for q,line in zip(now['outputs'],initial.lines))
    remaining_room=initial.free_space-occupied_change
    next_problem=replace(future,held=now['remaining'],basis=now['basis'],cash=now['cash'],
                         free_space=remaining_room,lines=tuple(lines))
    later=solve(next_problem,max_allocations=max_allocations)
    sale_quantities=tuple(sum(weight*min(d[i],a+b) for weight,d in scenarios) for i,(a,b) in enumerate(zip(now['outputs'],later['outputs'])))
    revenue=sum(q*line.quote for q,line in zip(sale_quantities,future.lines))
    initial_outlay=initial.cash-now['cash']
    return dict(first=now,second=later,closingSales=sale_quantities,closingRevenue=revenue,
                cashAtSecondDecision=now['cash'],closingCash=later['cash']+revenue,
                scenarioValue=later['value']-initial_outlay,
                continuationValue=later['value'],remainingRoomAtSecondDecision=remaining_room)


def optimize(initial,future,finished_caps,closing_demand,max_allocations=1000000):
    validate(initial)
    ranges=[range(0,min(o.stock,initial.slots[o.material]-initial.held[o.material])+1,o.lot) for o in initial.offers]
    count=math.prod(len(r) for r in ranges)
    if count>max_allocations:
        raise ValueError('first-period exhaustive allocation limit')
    best=None;key=None
    for allocation in product(*ranges):
        result=continuation(initial,future,finished_caps,closing_demand,allocation,max_allocations)
        if result is None:
            continue
        spent=initial.cash-result['first']['cash']+result['first']['cash']-result['second']['cash']
        candidate=(-result['scenarioValue'],spent,sum(allocation),allocation)
        if key is None or candidate<key:
            best,key=result,candidate
    return best



def merge_observationally_equal_states(initial,scenarios):
    """Scenario labels are not information. Merge branches with the same
    observed supply/technology before optimizing their hidden demand/value.
    """
    groups={}
    for weight,future,demands in scenarios:
        if weight==0:
            continue
        if not demands or any(not math.isfinite(w) or w<0 for w,_ in demands) or abs(sum(w for w,_ in demands)-1)>1e-12:
            raise ValueError('invalid closing-demand distribution')
        validate(future)
        n=len(future.held)
        indices=sorted(range(len(future.offers)),key=lambda i:(future.offers[i].material,future.offers[i].supplier))
        key=replace(future,offers=tuple(future.offers[i] for i in indices),
                    funded_demands=None if future.funded_demands is None else tuple(future.funded_demands[i] for i in indices),
                    incumbents=(-1,)*n,bids=(0,)*n,held=(0,)*n,basis=(0.,)*n,cash=0.,free_space=0.,
                    lines=tuple(replace(line,output_values=(0.,)*(line.max_batches*line.output_qty+1)) for line in future.lines),
                    terminal_values=tuple((0.,)*(cap+1) for cap in future.slots))
        groups.setdefault(key,[]).append((weight,future,demands))
    merged=[]
    for key,states in groups.items():
        probability=sum(w for w,_,_ in states)
        future=states[0][1]
        demands=tuple((w*conditional/probability,tuple(d)) for w,_,distribution in states for conditional,d in distribution)
        terminal=tuple(tuple(sum(w*p.terminal_values[m][q] for w,p,_ in states)/probability
                             for q in range(cap+1)) for m,cap in enumerate(future.slots))
        merged.append((probability,replace(future,terminal_values=terminal),demands))
    return merged


def optimize_uncertain(initial,supply_scenarios,finished_caps,max_allocations=1000000):
    """One first purchase across all future supply states. At the next decision,
    only supply/quotes are revealed; closing demand remains a distribution.
    Each entry is (probability, future Problem, demand distribution).
    This enforces the information boundary rather than averaging clairvoyant
    first-stage optima or letting second-stage buyers see future final demand.
    """
    validate(initial)
    if not supply_scenarios or any(not math.isfinite(weight) or weight<0 for weight,_,_ in supply_scenarios) or abs(sum(w for w,_,_ in supply_scenarios)-1)>1e-12:
        raise ValueError('invalid supply-state probabilities')
    supply_scenarios=merge_observationally_equal_states(initial,supply_scenarios)
    ranges=[range(0,min(o.stock,initial.slots[o.material]-initial.held[o.material])+1,o.lot) for o in initial.offers]
    if math.prod(len(r) for r in ranges)>max_allocations:
        raise ValueError('first-period exhaustive allocation limit')
    best=None;best_key=None
    for allocation in product(*ranges):
        results=[];value=0.;cash_spend=0.;valid=True
        for weight,future,demands in supply_scenarios:
            if weight==0:
                continue
            if not demands:
                raise ValueError('missing closing-demand distribution')
            result=continuation(initial,future,finished_caps,demands[0][1],allocation,max_allocations,demands)
            if result is None:
                valid=False;break
            results.append(dict(probability=weight,result=result))
            value+=weight*result['scenarioValue']
            cash_spend+=weight*(initial.cash-result['second']['cash'])
        if not valid:
            continue
        key=(-value,cash_spend,sum(allocation),allocation)
        if best_key is None or key<best_key:
            best=dict(firstAllocation=allocation,expectedValue=value,states=results)
            best_key=key
    return best
