"""Exhaustive non-anticipating event-tree planner for small company fixtures.

An explicit funding callback remains supported for mechanics comparisons.
funding='continuation' instead derives joint intentions from the same conditional
continuation objective. Neither mode is a calibrated population purchasing model.
"""
from dataclasses import dataclass, replace
from collections import OrderedDict
from itertools import product
import math
from .phase_ledger import Purchase, SettleBook, apply, horizon_value, validate_state


class PhaseSearchLimit(ValueError):
    """Incomplete exact search with diagnostic work counters; never a policy."""
    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = diagnostics


@dataclass(frozen=True)
class Scenario:
    probability: float
    events: tuple
    input_values: tuple
    finished_values: tuple



def _native_quote_cap(held,slot,lot):
    # Independent Python bracket/search of whole lots under the ledger predicate.
    ceiling=(2**63-1-lot)//lot
    fits=lambda lots: held+lots*lot<=max(held,slot)
    if fits(ceiling):raise ValueError('native query range exceeds signed int64 frame')
    lower=0;upper=1
    while upper<ceiling and fits(upper):
        lower=upper;upper=min(ceiling,upper*2)
    while upper-lower>1:
        middle=(lower+upper)//2
        if fits(middle):lower=middle
        else:upper=middle
    return lower*lot


def solve(company, initial, scenarios, *, funding, max_nodes=100000, supply='independent-snapshots', transition_cache_size=4096, allocation_search='exhaustive', max_prefix_nodes=100000, funding_memo_size=0, audit_continuation_bound=False, continuation_bound_costs=False, prune_continuation=False, audit_closing_allocation=False, closing_search='event-tree', closing_memo_size=0, prune_prefix=False, shared_first_batches=0, shared_bound_memo_size=0, closing_proposal_memo_size=0, joint_bound_memo_size=0, shared_first_joint_states=0, cash_relaxed_joint_bound=False):
    native=any(q!=int(q) for q in (*initial.held,*initial.finished,*company.slots,*(initial.book.quantity if initial.book else ())))
    if native and ((not callable(funding) and funding not in ('continuation','continuation-reference-v1','continuation-transfer-neutral')) or allocation_search!='exhaustive' or closing_search!='event-tree'):
        raise ValueError('native fractional search requires explicit/continuation funding and exhaustive event-tree traversal')
    if closing_search not in ('event-tree', 'compiled-exhaustive', 'compiled-boxes', 'compiled-cost-boxes', 'compiled-fast-cost-boxes', 'compiled-certified-boxes', 'compiled-joint-certified-boxes'):
        raise ValueError('unknown closing search mode')
    if not isinstance(closing_memo_size, int) or isinstance(closing_memo_size, bool) or closing_memo_size < 0:
        raise ValueError('closing memo size must be a nonnegative integer')
    if not isinstance(closing_proposal_memo_size,int) or isinstance(closing_proposal_memo_size,bool) or closing_proposal_memo_size<0:
        raise ValueError('closing proposal memo size must be a nonnegative integer')
    if closing_proposal_memo_size and closing_search not in ('compiled-certified-boxes','compiled-joint-certified-boxes'):
        raise ValueError('proposal memo requires certified closing search')
    if not isinstance(joint_bound_memo_size,int) or isinstance(joint_bound_memo_size,bool) or joint_bound_memo_size<0:
        raise ValueError('joint-bound memo size must be a nonnegative integer')
    if joint_bound_memo_size and closing_search!='compiled-joint-certified-boxes':
        raise ValueError('joint-bound memo requires joint certified closing search')
    if not isinstance(cash_relaxed_joint_bound,bool):raise ValueError('cash-relaxed joint bound flag must be boolean')
    if cash_relaxed_joint_bound and closing_search!='compiled-joint-certified-boxes':
        raise ValueError('cash-relaxed bound requires joint certified closing search')
    joint_memo=None
    if joint_bound_memo_size:
        if cash_relaxed_joint_bound:
            from .closing_cash_relaxed_bound import ProfitMemo as BoundMemo
        else:
            from .closing_joint_compiled import BoundMemo
        joint_memo=BoundMemo(joint_bound_memo_size)
    proposal_memo=None
    if closing_proposal_memo_size:
        from .closing_certificate import ProposalMemo
        proposal_memo=ProposalMemo(closing_proposal_memo_size)
    closing_memo = OrderedDict()
    closing_memo_stats = dict(capacity=closing_memo_size, hits=0, misses=0, peakEntries=0,
                              savedAllocations=0, savedBoxes=0, savedProposalStates=0)
    closing_solver_stats = dict(memo=closing_memo_stats, mode=closing_search, solves=0, unsupported=0, allocations=0, boxes=0, skippedAllocations=0, proposalStates=0, certificates=0)
    if cash_relaxed_joint_bound:closing_solver_stats['cashRelaxedJointBound']=True
    if not isinstance(audit_closing_allocation, bool):
        raise ValueError('closing allocation audit flag must be boolean')
    closing_stats = dict(checked=0, unsupported=0)
    if not isinstance(shared_bound_memo_size,int) or isinstance(shared_bound_memo_size,bool) or shared_bound_memo_size<0:
        raise ValueError('shared-bound memo size must be a nonnegative integer')
    if shared_bound_memo_size and not (shared_first_batches or shared_first_joint_states):
        raise ValueError('shared-bound memo requires shared first bound')
    shared_bound_memo=None
    if shared_bound_memo_size:
        from .shared_first_bound import BoundMemo
        shared_bound_memo=BoundMemo(shared_bound_memo_size)
    if not isinstance(shared_first_batches,int) or isinstance(shared_first_batches,bool) or shared_first_batches<0:
        raise ValueError('shared first-batch limit must be a nonnegative integer')
    if not isinstance(shared_first_joint_states,int) or isinstance(shared_first_joint_states,bool) or shared_first_joint_states<0:
        raise ValueError('shared joint first-state limit must be a nonnegative integer')
    if (shared_first_batches or shared_first_joint_states) and not prune_prefix:
        raise ValueError('shared first bound requires prefix pruning')
    if not isinstance(prune_prefix,bool):
        raise ValueError('prefix pruning flag must be boolean')
    if prune_prefix and allocation_search!='feasible-prefix':
        raise ValueError('prefix pruning requires feasible-prefix traversal')
    if not isinstance(prune_continuation,bool):
        raise ValueError('continuation pruning flag must be boolean')
    if not isinstance(continuation_bound_costs,bool):
        raise ValueError('cost envelope flag must be boolean')
    if not isinstance(audit_continuation_bound,bool):
        raise ValueError('bound audit must be boolean')
    bound_stats=dict(pruned=0,checked=0,unavailable=0,wouldPrune=0,wouldPruneWithFuturePurchase=0,minSlack=None,maxSlack=None)
    if not isinstance(funding_memo_size,int) or isinstance(funding_memo_size,bool) or funding_memo_size<0:
        raise ValueError('funding memo size must be a nonnegative integer')
    funding_memo=OrderedDict();memo_stats=dict(hits=0,misses=0,peakEntries=0)
    if allocation_search not in ('exhaustive','feasible-prefix'):
        raise ValueError('unknown allocation search mode')
    if not isinstance(max_prefix_nodes,int) or isinstance(max_prefix_nodes,bool) or max_prefix_nodes<1:
        raise ValueError('positive prefix work budget required')
    prefix_stats=dict(visitedPrefixes=0,prunedLeaves=0)
    if prune_prefix:prefix_stats.update(boundEvaluations=0,boundPrunedLeaves=0,boundPrunedPrefixes=0)
    if shared_first_batches or shared_first_joint_states:prefix_stats.update(sharedBoundWork=0,sharedBoundCalls=0,sharedBoundPruned=0,sharedBoundSkipped=0)
    if supply not in ('independent-snapshots', 'persistent-arrivals'):
        raise ValueError('unknown scenario supply mode')
    if not isinstance(transition_cache_size,int) or isinstance(transition_cache_size,bool) or transition_cache_size<0:
        raise ValueError('transition cache size must be a nonnegative integer')
    validate_state(company,initial)
    slot_funding = funding == 'slot-deficit-v1'
    endogenous = funding in ('continuation','continuation-reference-v1','continuation-transfer-neutral')
    transfer_neutral = funding == 'continuation-transfer-neutral'
    reference_only = funding == 'continuation-reference-v1'
    rule = ('continuation-reference-v1' if reference_only else
            'continuation-transfer-neutral-v1' if transfer_neutral else 'continuation-v2')
    if (not endogenous and not slot_funding and not callable(funding)) or not isinstance(max_nodes,int) or isinstance(max_nodes,bool) or max_nodes<1:
        raise ValueError('explicit funding rule and positive enumeration limit required')
    if not scenarios or any(not math.isfinite(s.probability) or s.probability<0 for s in scenarios) or abs(math.fsum(s.probability for s in scenarios)-1)>1e-12:
        raise ValueError('invalid scenario probabilities')
    scenarios=tuple(s for s in scenarios if s.probability>0)
    if prune_continuation or prune_prefix:
        if not endogenous and not slot_funding:
            raise ValueError('continuation pruning requires known funding; arbitrary callbacks remain exhaustive')
        from .scenario_validation import validate_calendar
        for scenario in scenarios:validate_calendar(company,initial,scenario)
    structure=tuple((type(e),e.label) for e in scenarios[0].events)
    if any(tuple((type(e),e.label) for e in s.events)!=structure for s in scenarios):
        raise ValueError('scenario calendars/labels differ; labels cannot reveal hidden outcomes')
    if supply == 'persistent-arrivals':
        # Stock specifies cumulative initial inventory plus external arrivals,
        # before this buyer's own purchases. Outside withdrawals require a
        # different explicitly conditional model, not decreasing this total.
        for scenario in scenarios:
            previous={}
            for event in scenario.events:
                if not isinstance(event,Purchase):
                    continue
                seen=set()
                for offer in event.offers:
                    key=(offer.material,offer.supplier)
                    if (key in seen or not isinstance(offer.stock,int) or isinstance(offer.stock,bool)
                            or offer.stock<previous.get(key,0)):
                        raise ValueError('persistent supply requires unique nondecreasing whole stock totals')
                    seen.add(key);previous[key]=offer.stock
    nodes=0;funding_cache={};funding_queries=0;funding_decisions=0
    decision_stack=[]

    transitions=OrderedDict();transition_hits=0;transition_misses=0;transition_peak=0

    def transition(state,event,allocation=None):
        nonlocal transition_hits,transition_misses,transition_peak
        # Pure ledger transitions depend on complete state and event, not on the
        # posterior, observed history or continuation values. Cache only these
        # transitions; never reuse a policy/value across information groups.
        key=(state,event,allocation)
        if transition_cache_size and key in transitions:
            transition_hits+=1
            result,detail,error=transitions[key]
        else:
            transition_misses+=1
            try:
                result,detail=apply(company,state,event,allocation)
                error=None
            except ValueError as exc:
                if str(exc) not in ('infeasible procurement allocation','production would exceed physical storage'):
                    raise
                result=detail=None;error=str(exc)
            if transition_cache_size:
                if len(transitions)==transition_cache_size:
                    transitions.popitem(last=False)
                transitions[key]=(result,detail,error)
                transition_peak=max(transition_peak,len(transitions))
        if error is not None:
            raise ValueError(error)
        # Trace annotations are caller-owned. Ledger details currently contain
        # immutable scalars/tuples; copy their mapping before exposing it.
        return result,dict(detail)

    def consume_supply(scenario,index,event,allocation):
        if supply == 'independent-snapshots':
            return scenario
        physical={(o.material,o.supplier):o.stock for o in scenario.events[index].offers}
        # Funding may add hypothetical current inventory. Its added units are
        # consumed now; only real opening stock is removed from future supply.
        consumed={(o.material,o.supplier):min(q,physical[(o.material,o.supplier)])
                  for o,q in zip(event.offers,allocation)}
        events=list(scenario.events)
        for j in range(index+1,len(events)):
            future=events[j]
            if isinstance(future,Purchase):
                offers=tuple(replace(o,stock=o.stock-consumed.get((o.material,o.supplier),0)) for o in future.offers)
                if any(o.stock<0 for o in offers):
                    raise AssertionError('persistent supply ledger became negative')
                events[j]=replace(future,offers=offers)
        return replace(scenario,events=tuple(events))

    def observed_event(event):
        order=sorted(range(len(event.offers)),key=lambda i:(event.offers[i].material,event.offers[i].supplier))
        if len(event.reliability)!=len(order):
            raise ValueError('supplier reliability dimensions differ')
        return replace(event,offers=tuple(event.offers[i] for i in order),
                       reliability=tuple(event.reliability[i] for i in order),funded_demands=())

    def observed_history(trace):
        # Remember only realized own outcomes and previously inspected offers.
        # In particular, SharedSettleBook's quoteDemands are scenario inputs,
        # not observed unmet demand when this company had insufficient stock.
        fields=('cash','equity','postedEarnings','sold','sales','cogs','feeIncome',
                'openingStock','openingBasis','openingQuote','quotes','eligible',
                'charge','paid','arrears','netTransfers','nextTransferEMA',
                'allocation','observedPurchase','fundedDemands','preferences',
                'fees','goods','outputs','conversion')
        return tuple((d['event'],d['label'],tuple((name,d[name]) for name in fields if name in d)) for d in trace)

    def optimize_group(group,index,event,*,hypothetical=False,funding_detail=None,neutral=False):
        nonlocal nodes
        state=group[0][1]
        decision_stack.append(dict(eventIndex=index,label=event.label,hypothetical=hypothetical,
                                   offers=len(event.offers),stage='starting'))
        mass=math.fsum(branch[0] for branch in group)
        ranges=[]
        for offer in event.offers:
            if not 0<=offer.material<len(company.slots) or offer.lot<1 or offer.lot!=int(offer.lot):
                raise ValueError('invalid observed offer')
            cap=offer.stock if native else max(0,company.slots[offer.material]-state.held[offer.material])
            ranges.append(range(0,min(offer.stock,cap)+1,offer.lot))
        best=None;best_allocation=None;best_payment=None
        candidates=product(*ranges)
        compiled_closing = None
        if closing_search != 'event-tree':
            if closing_search in ('compiled-certified-boxes','compiled-joint-certified-boxes'):
                from .closing_certificate import solve as closing_solve
            elif closing_search in ('compiled-boxes', 'compiled-cost-boxes', 'compiled-fast-cost-boxes', 'compiled-certified-boxes', 'compiled-joint-certified-boxes'):
                from .closing_boxes import solve as closing_solve
            else:
                from .closing_values import solve as closing_solve
            if nodes >= max_nodes:
                raise ValueError('event-tree exhaustive node limit; no approximate result returned')
            posterior = tuple((weight, replace(scenario, events=scenario.events[index+1:]))
                              for weight, _, scenario, _ in group)
            # Reuse only an exact immutable input match within this solve.
            # This caches selection, never branch state, accounts or traces.
            memo_key = (state, event, posterior, neutral, hypothetical)
            cached = closing_memo.get(memo_key) if closing_memo_size else None
            if cached is not None:
                closing_memo.move_to_end(memo_key)
                closing_memo_stats['hits'] += 1
                closing_memo_stats['savedAllocations'] += cached['enumeratedAllocations']-1
                closing_memo_stats['savedBoxes'] += cached.get('boxes', 0)
                closing_memo_stats['savedProposalStates'] += cached.get('proposalStates', 0)
                # One ordinary chosen-basket replay is still charged below.
                compiled_closing = dict(cached, enumeratedAllocations=1, boxes=0, skippedAllocations=0, proposalStates=0, certificates=0)
                if 'jointBoundWork' in compiled_closing:compiled_closing['jointBoundWork']=0
            else:
                closing_memo_stats['misses'] += 1
                extra = {}
                if closing_search in ('compiled-boxes', 'compiled-cost-boxes', 'compiled-fast-cost-boxes', 'compiled-certified-boxes', 'compiled-joint-certified-boxes'):
                    remaining = max_prefix_nodes-prefix_stats['visitedPrefixes']-prefix_stats.get('boundEvaluations',0)-prefix_stats.get('sharedBoundWork',0)-closing_solver_stats['boxes']-closing_solver_stats['proposalStates']-closing_solver_stats.get('jointBoundWork',0)
                    if remaining < 1:
                        raise ValueError('closing box node limit; no approximate result returned')
                    extra['max_boxes'] = remaining
                    if closing_search not in ('compiled-certified-boxes','compiled-joint-certified-boxes'):
                        extra['include_costs'] = closing_search in ('compiled-cost-boxes', 'compiled-fast-cost-boxes')
                        extra['compiled_costs'] = closing_search == 'compiled-fast-cost-boxes'
                if closing_search=='compiled-joint-certified-boxes':extra['joint_proposals']=True
                if cash_relaxed_joint_bound:extra['cash_relaxed_joint_bound']=True
                if joint_memo is not None:extra['joint_memo']=joint_memo
                if proposal_memo is not None:extra['proposal_memo']=proposal_memo
                decision_stack[-1]['stage'] = 'closing-search'
                compiled_closing = closing_solve(company, initial, state, event, posterior, neutral=neutral,
                                                max_allocations=max_nodes-nodes, **extra)
                if joint_memo is not None:
                    closing_solver_stats['jointBoundMemo']=dict(capacity=joint_bound_memo_size,hits=joint_memo.hits,misses=joint_memo.misses,peakEntries=joint_memo.peak_entries)
                if proposal_memo is not None:
                    closing_solver_stats['proposalMemo']=dict(capacity=closing_proposal_memo_size,hits=proposal_memo.hits,misses=proposal_memo.misses,peakEntries=proposal_memo.peak_entries)
                if closing_memo_size and compiled_closing is not None:
                    closing_memo[memo_key] = dict(compiled_closing)
                    if len(closing_memo) > closing_memo_size:
                        closing_memo.popitem(last=False)
                    closing_memo_stats['peakEntries'] = max(closing_memo_stats['peakEntries'], len(closing_memo))
            if compiled_closing is None:
                closing_solver_stats['unsupported'] += 1
            else:
                count = compiled_closing['enumeratedAllocations']
                closing_solver_stats['solves'] += 1
                closing_solver_stats['allocations'] += count
                closing_solver_stats['boxes'] += compiled_closing.get('boxes', 0)
                closing_solver_stats['proposalStates'] += compiled_closing.get('proposalStates', 0)
                if 'jointBoundWork' in compiled_closing:
                    closing_solver_stats['jointBoundWork']=closing_solver_stats.get('jointBoundWork',0)+compiled_closing['jointBoundWork']
                closing_solver_stats['certificates'] += compiled_closing.get('certificates', 0)
                closing_solver_stats['skippedAllocations'] += compiled_closing.get('skippedAllocations', 0)
                nodes += count-1  # The chosen basket is charged by the loop below.
                candidates = (compiled_closing['allocation'],)
        if compiled_closing is None and allocation_search=='feasible-prefix':
            from .feasible_prefix import allocations
            def prefix_budget():
                return max_prefix_nodes-closing_solver_stats['boxes']-closing_solver_stats['proposalStates']-closing_solver_stats.get('jointBoundWork',0)-prefix_stats.get('boundEvaluations',0)-prefix_stats.get('sharedBoundWork',0)
            def prune_branch(prefix):
                # Complete baskets already have the ordinary continuation
                # bound; reserve prefix work for groups of multiple leaves.
                if best is None or len(prefix)==len(event.offers):return False
                prior=best[0]/mass
                def try_shared():
                    if not (shared_first_batches or shared_first_joint_states):return False
                    # Reserve worst-case enumeration work before calling; if it
                    # does not fit, keep the ordinary bound without spending it.
                    nlines=len(company.lines)
                    if nlines==1:
                        from .shared_first_bound import bound as shared_bound
                        states=company.lines[0].max_batches+1
                        supported=shared_first_batches>0 and states<=shared_first_batches+1
                        options=dict(max_first_batches=shared_first_batches)
                        scenario_work=len(group)
                    else:
                        from .shared_joint_first_bound import bound as shared_bound
                        states=math.prod(line.max_batches+1 for line in company.lines)
                        supported=shared_first_joint_states>0 and states<=shared_first_joint_states
                        options=dict(max_first_states=shared_first_joint_states)
                        scenario_work=len(group)*(nlines+1)
                    reservation=1+states*(scenario_work+1)
                    available=prefix_budget()-prefix_stats['visitedPrefixes']
                    if supported and reservation<=available:
                        posterior=tuple((weight,replace(scenario,events=scenario.events[index+1:])) for weight,_,scenario,_ in group)
                        shared=shared_bound(company,initial,state,event,prefix,posterior,
                                            **options,neutral=neutral,memo=shared_bound_memo)
                        if shared_bound_memo is not None:
                            prefix_stats['sharedBoundMemo']=dict(capacity=shared_bound_memo_size,hits=shared_bound_memo.hits,misses=shared_bound_memo.misses,peakEntries=shared_bound_memo.peak_entries)
                        work=1+shared['firstBatchStates']+shared['scenarioEvaluations']
                        if work>reservation:raise AssertionError('shared bound exceeded reserved work')
                        prefix_stats['sharedBoundCalls']+=1;prefix_stats['sharedBoundWork']+=work
                        value=shared['value']
                        if math.isfinite(value) and value<prior-(1e-9+1e-12*max(abs(value),abs(prior))):
                            prefix_stats['sharedBoundPruned']+=1
                            return True
                    else:prefix_stats['sharedBoundSkipped']+=1
                    return False
                if (len(company.lines)==1 or not shared_first_joint_states) and try_shared():return True
                from .prefix_continuation_bound import upper_value
                values=[]
                for weight,_,scenario,_ in group:
                    prefix_stats['boundEvaluations']+=1
                    if prefix_stats['visitedPrefixes']>prefix_budget():
                        raise ValueError('event-tree prefix bound node limit; no approximate result returned')
                    bound=upper_value(company,initial,state,event,prefix,scenario.events[index+1:],
                                      scenario.input_values,scenario.finished_values,neutral=neutral)
                    if not math.isfinite(bound):return False
                    values.append(weight*bound)
                envelope=math.fsum(values)/mass
                tolerance=1e-9+1e-12*max(abs(envelope),abs(prior))
                if envelope<prior-tolerance:return True
                return try_shared() if len(company.lines)>1 and shared_first_joint_states else False
            candidates=allocations(ranges,event.offers,state.held,company.slots,state.cash,prefix_stats,prefix_budget,
                                   prune=prune_branch if prune_prefix else None)
        decision_stack[-1]['stage'] = 'allocation-search'
        for allocation in candidates:
            nodes+=1
            if nodes>max_nodes:
                raise ValueError('event-tree exhaustive node limit; no approximate result returned')
            try:
                new,detail=transition(state,event,allocation)
            except ValueError as exc:
                if str(exc) in ('infeasible procurement allocation','production would exceed physical storage'):
                    continue
                raise
            if hypothetical:
                # Funding asks what goods are economically useful at the quote,
                # before current switching charges/relationship acquisition.
                # Holding this hypothetical preference fixed avoids a circular
                # demand -> qualification -> future fee -> demand definition.
                new=replace(new,incumbents=state.incumbents)
                detail={**detail,'preferences':state.incumbents}
            observed=observed_event(event)
            purchase_observation=(tuple((o.material,o.supplier,o.price,o.stock,o.lot) for o in observed.offers),
                observed.reliability,observed.fee_unit_cost,observed.fee_multiple,
                observed.active_lines,observed.rent_bill,observed.rent_threshold,observed.overhead_timing)
            if observed.frozen_overhead is not None:
                purchase_observation += (observed.frozen_overhead,)
            detail={**detail,'observedPurchase':purchase_observation,'allocation':allocation,
                    'offerIdentities':tuple((o.material,o.supplier) for o in event.offers),
                    'fundedDemands':event.funded_demands}
            if funding_detail is not None:
                detail['funding']=funding_detail
            if supply == 'persistent-arrivals':
                detail['observedStocks']=tuple(o.stock for o in event.offers)
            following=[(weight,new,consume_supply(scenario,index,event,allocation),trace+(detail,))
                       for weight,_,scenario,trace in group]
            envelope=None
            if audit_continuation_bound or prune_continuation:
                from .continuation_bound import upper_value
                envelope=math.fsum(weight*upper_value(company,initial,branch_state,scenario.events[index+1:],
                    scenario.input_values,scenario.finished_values,neutral=neutral,include_costs=continuation_bound_costs)
                    for weight,branch_state,scenario,_ in following)/mass
                if math.isfinite(envelope):
                    if best is not None:
                        prior=best[0]/mass
                        tol=1e-9+1e-12*max(abs(envelope),abs(prior))
                        if envelope<prior-tol:
                            bound_stats['wouldPrune']+=1
                            if any(isinstance(e,Purchase) for _,_,p,_ in following for e in p.events[index+1:]):
                                bound_stats['wouldPruneWithFuturePurchase']+=1
                            if prune_continuation:
                                bound_stats['pruned']+=1
                                continue
                else:
                    bound_stats['unavailable']+=1
            decision_stack[-1]['stage'] = 'continuation'
            result=walk(following,index+1,neutral=neutral)
            decision_stack[-1]['stage'] = 'allocation-search'
            if envelope is not None and math.isfinite(envelope):
                actual=result[0]/mass;slack=envelope-actual
                if slack<0:
                    raise AssertionError('continuation envelope is below exact candidate return')
                bound_stats['checked']+=1
                for field,func in (('minSlack',min),('maxSlack',max)):
                    old=bound_stats[field];bound_stats[field]=slack if old is None else func(old,slack)
            payment=detail['goods']+sum(detail['fees'])
            better=best is None
            if best is not None:
                value,old=result[0]/mass,best[0]/mass
                tolerance=1e-9+1e-12*max(abs(value),abs(old))
                cost_tolerance=1e-9+1e-12*max(abs(payment),abs(best_payment))
                better=value>old+tolerance or (abs(value-old)<=tolerance and (
                    payment<best_payment-cost_tolerance or (abs(payment-best_payment)<=cost_tolerance
                    and (sum(allocation),allocation)<(sum(best_allocation),best_allocation))))
            if better:
                best,best_allocation,best_payment=result,allocation,payment
        if best is None:
            raise ValueError('no feasible action at observed decision')
        if compiled_closing is not None and best[0]/mass != compiled_closing['value']:
            raise AssertionError('compiled closing value differs from actual ledger replay')
        if audit_closing_allocation:
            from .closing_allocation import candidate
            posterior = tuple((weight, replace(scenario, events=scenario.events[index+1:]))
                              for weight, _, scenario, _ in group)
            shadow = candidate(company, initial, state, event, posterior, neutral=neutral,
                               hold_incumbents=hypothetical, max_nodes=max_nodes)
            if shadow is None:
                closing_stats['unsupported'] += 1
            else:
                expected = best[0]/mass
                tolerance = 1e-9+1e-12*max(abs(expected), abs(shadow['expectedValue']))
                if shadow['allocation'] != best_allocation or abs(shadow['expectedValue']-expected) > tolerance:
                    raise AssertionError('closing allocation differs from exhaustive phase policy')
                if len(shadow['leaves']) != len(best[1]) or any(
                        a['state'] != b['state'] for a, b in zip(shadow['leaves'], best[1])):
                    raise AssertionError('closing allocation differs from exhaustive final states')
                closing_stats['checked'] += 1
        decision_stack.pop()
        return best,best_allocation,best_payment

    def continuation_funding(group,index,event,neutral=False):
        nonlocal funding_queries,funding_decisions
        funding_decisions+=1
        state=group[0][1];n=len(state.held)
        references=[]
        for material in range(n):
            candidates=[i for i,o in enumerate(event.offers) if o.material==material]
            incumbent=next((i for i in candidates if event.offers[i].supplier==state.incumbents[material]),None)
            references.append(incumbent if incumbent is not None else min(candidates,
                key=lambda i:(event.offers[i].price,event.offers[i].supplier),default=None))
        cache={}

        def query(replaced_material=-1,replacement=None):
            nonlocal funding_queries
            if reference_only:
                selected=[replacement if m==replaced_material else i for m,i in enumerate(references)]
            else:
                selected=[i for i,offer in enumerate(event.offers)
                          if offer.material!=replaced_material or i==replacement]
            # This local cache only deduplicates identical selected-offer sets.
            # Cross-group reuse below additionally requires the complete future distribution.
            key=tuple(selected)
            if key in cache:
                return cache[key]
            offers=[];reliability=[];caps=[]
            for i in selected:
                if i is not None:
                    old=event.offers[i]
                    m=old.material
                    cap=(_native_quote_cap(state.held[m],company.slots[m],old.lot) if native else
                         max(0,company.slots[m]-state.held[m])//old.lot*old.lot)
                    offers.append(replace(old,stock=cap));reliability.append(event.reliability[i]);caps.append(cap)
            hypothetical_event=replace(event,offers=tuple(offers),reliability=tuple(reliability),
                                       funded_demands=tuple(caps),fee_multiple=0.)
            memo_key=None
            if funding_memo_size:
                # Every branch in this group has identical observed history.
                # Its common prefix cannot split later information groups. The
                # ordered weighted future paths completely specify the remaining
                # conditional problem. Include CURRENT physical offers as well:
                # persistent-supply funding distinguishes real and phantom stock.
                posterior=tuple((weight,scenario.events[index:],scenario.input_values,scenario.finished_values)
                                for weight,_,scenario,_ in group)
                memo_key=(index,state,hypothetical_event,neutral or transfer_neutral,posterior)
                if memo_key in funding_memo:
                    memo_stats['hits']+=1
                    answer=dict(funding_memo[memo_key]);cache[key]=answer
                    return answer
                memo_stats['misses']+=1
            funding_queries+=1
            result,allocation,payment=optimize_group(group,index,hypothetical_event,hypothetical=True,neutral=neutral or transfer_neutral)
            quantities=[0]*n
            for offer,q in zip(offers,allocation):
                quantities[offer.material]+=q
            answer=dict(quantities=tuple(quantities),goods=payment,
                        conditionalValue=result[0]/math.fsum(b[0] for b in group))
            if funding_memo_size:
                if len(funding_memo)==funding_memo_size:
                    funding_memo.popitem(last=False)
                funding_memo[memo_key]=dict(answer)
                memo_stats['peakEntries']=max(memo_stats['peakEntries'],len(funding_memo))
            cache[key]=answer
            return answer

        reference=query()
        demands=[];quote_vectors=[]
        for i,offer in enumerate(event.offers):
            answer=query(offer.material,i)
            demands.append(answer['quantities'][offer.material])
            quote_vectors.append(dict(material=offer.material,supplier=offer.supplier,**answer))
        detail=dict(rule=rule,referenceSuppliers=tuple(event.offers[i].supplier if i is not None else -1 for i in references),
                    referenceDemands=tuple(demands[i] if i is not None else 0 for i in references),
                    jointQuantities=reference['quantities'],jointGoods=reference['goods'],quoteVectors=tuple(quote_vectors),
                    boundary=('Only the queried input is fixed to its quote; other inputs retain every discovered quote. ' if not reference_only else 'All other inputs are pinned to reference quotes (rejected comparison). ')
                        +'Current hypothetical supplier stocks are relaxed; current fees are zero and incumbent identities are held fixed. '
                        +('All subsequent switching transfers are omitted only inside the funding counterfactual.' if neutral or transfer_neutral else 'Future orders retain actual fees/preferences and their own joint funding.'))
        return replace(event,funded_demands=tuple(demands)),detail

    def walk(branches,index,neutral=False):
        if index==len(structure):
            leaves=[];values=[]
            for probability,state,scenario,trace in branches:
                outcome=horizon_value(initial,state,scenario.input_values,scenario.finished_values)
                values.append(probability*outcome)
                leaves.append(dict(probability=probability,value=outcome,state=state,trace=trace))
            return math.fsum(values),leaves
        if structure[index][0] is not Purchase:
            following=[]
            for probability,state,scenario,trace in branches:
                event=scenario.events[index]
                if neutral and isinstance(event,SettleBook):
                    event=replace(event,fee_income=0.)
                new,detail=transition(state,event)
                following.append((probability,new,scenario,trace+(detail,)))
            return walk(following,index+1,neutral=neutral)
        groups={}
        for branch in branches:
            event=observed_event(branch[2].events[index])
            if neutral:
                event=replace(event,fee_multiple=0.)
            groups.setdefault((branch[1],event,observed_history(branch[3])),[]).append(branch)
        totals=[];leaves=[]
        for (state,event,history),group in groups.items():
            if endogenous:
                event,detail=continuation_funding(group,index,event,neutral=neutral)
            else:
                key=(state,event)
                if key not in funding_cache:
                    funded=(tuple(max(0,company.slots[o.material]-state.held[o.material]) for o in event.offers)
                            if slot_funding else tuple(funding(company,state,event)))
                    if len(funded)!=len(event.offers):
                        raise ValueError('funding rule returned wrong dimensions')
                    funding_cache[key]=replace(event,funded_demands=funded)
                event=funding_cache[key];detail=None
            best,_,_=optimize_group(group,index,event,funding_detail=detail,neutral=neutral)
            totals.append(best[0]);leaves.extend(best[1])
        return math.fsum(totals),leaves

    try:
        value,leaves=walk([(s.probability,initial,s,()) for s in scenarios],0)
    except ValueError as exc:
        if 'node limit; no approximate result returned' not in str(exc):
            raise
        import copy
        diagnostics=copy.deepcopy(dict(enumeratedNodes=nodes,maxNodes=max_nodes,
            maxPrefixNodes=max_prefix_nodes,activeDecisions=decision_stack,
            fundingQueries=funding_queries,fundingObservations=funding_decisions if endogenous else len(funding_cache),
            closingSolver=closing_solver_stats,fundingMemo=dict(capacity=funding_memo_size,**memo_stats),
            prefixSearch=prefix_stats,boundAudit=bound_stats,
            transitionCache=dict(capacity=transition_cache_size,hits=transition_hits,misses=transition_misses,peakEntries=transition_peak),
            counterScope='Counters include completed subsolves and charged outer work. Work inside a closing solver that raises before returning is not included. No feasible policy or optimal value is returned.'))
        raise PhaseSearchLimit(str(exc),diagnostics) from exc
    return dict(expectedValue=value,leaves=leaves,enumeratedNodes=nodes,
                fundingObservations=funding_decisions if endogenous else len(funding_cache),
                fundingQueries=funding_queries,fundingRule=rule if endogenous else ('slot-deficit-v1' if slot_funding else 'explicit-callback'),
                supplyMode=supply,
                boundAudit=bound_stats,
                closingAudit=closing_stats,
                closingSolver=closing_solver_stats,
                fundingMemo=dict(capacity=funding_memo_size,**memo_stats),
                allocationSearch=allocation_search,prefixSearch=prefix_stats,
                transitionCache=dict(capacity=transition_cache_size,hits=transition_hits,misses=transition_misses,peakEntries=transition_peak),
                scope='Exact small event tree under the declared funding boundary and supplied scenarios. No population model or calibrated demand claim.')
