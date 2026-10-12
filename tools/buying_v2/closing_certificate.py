"""Strict ledger-value dominance certificate for a supplied closing proposal.

Failure is inconclusive. It must never replace the lexicographic exact solver.
The complement partition covers every whole-lot basket other than the proposal.
"""
import math
from dataclasses import replace
from collections import OrderedDict
from .closing_allocation import prepare
from .closing_values import _prepared_evaluator
from .closing_boxes import upper_value
from .closing_cost_compiled import bounder


def complement_boxes(lo, hi, point, lots):
    """Disjoint boxes, classified by first coordinate differing from point."""
    for i, (left, right, q, lot) in enumerate(zip(lo, hi, point, lots)):
        prefix = point[:i]
        if q > left:
            yield prefix+lo[i:], prefix+(q-lot,)+hi[i+1:]
        if q < right:
            yield prefix+(q+lot,)+lo[i+1:], prefix+hi[i:]


def certify(company, initial, state, event, posterior, allocation, *, neutral=False, max_boxes=100000, joint_bound=False, joint_memo=None, cash_relaxed_joint_bound=False):
    """Return proof status and work; never claim a result after an incomplete proof."""
    if not isinstance(max_boxes, int) or isinstance(max_boxes, bool) or max_boxes < 1:
        raise ValueError('positive closing certificate box budget required')
    problem = prepare(company, initial, state, event, posterior, neutral=neutral)
    if problem is None:
        return dict(certified=False, reason='unsupported', boxes=0, allocations=0)
    run = _prepared_evaluator(problem, initial, state, event, posterior, neutral=neutral)
    point = tuple(allocation)
    if len(point)!=len(event.offers) or any(not isinstance(q,int) or isinstance(q,bool) or q<0 or q>o.stock or q%o.lot for q,o in zip(point,event.offers)):
        return dict(certified=False,reason='invalid-proposal',boxes=0,allocations=0)
    row = run((point,))[0]
    if row is None:
        return dict(certified=False, reason='infeasible-proposal', boxes=0, allocations=1)
    lo = (0,)*len(event.offers)
    lots = tuple(o.lot for o in event.offers)
    hi = tuple(min(o.stock,max(0,company.slots[o.material]-state.held[o.material]))//o.lot*o.lot for o in event.offers)
    # Feasible input slots guarantee the proposal lies in the box.
    assert all(a <= q <= b for a,q,b in zip(lo,point,hi))
    cost_bound = bounder(problem, initial, state, posterior, neutral=neutral)
    stack = list(complement_boxes(lo,hi,point,lots))
    boxes = joint_work = 0
    joint = None
    if joint_bound and len(problem.lines)>1:
        options={}
        if cash_relaxed_joint_bound:
            from .closing_cash_relaxed_bound import bounder as joint_bounder
            options['compiled']=True
        else:
            from .closing_joint_compiled import bounder as joint_bounder
        states = math.prod(line.max_batches+1 for line in problem.lines)
        joint = joint_bounder(problem,initial,state,posterior,neutral=neutral,max_states=min(states,max_boxes),memo=joint_memo,**options)
    def result(**kwargs):
        if joint_bound:kwargs['jointBoundWork']=joint_work
        return kwargs
    while stack:
        if boxes+joint_work >= max_boxes:
            return result(certified=False, reason='proof-limit', boxes=boxes, allocations=1, proposal=row)
        left,right = stack.pop();boxes += 1
        upper = upper_value(problem,initial,state,posterior,left,right,neutral=neutral)
        if upper != -math.inf:
            upper = min(upper,cost_bound(left,right))
        if upper == -math.inf:
            continue
        tolerance = 1e-9+1e-12*max(abs(upper),abs(row['value']))
        # Strict gap rules out every value tie, so original traversal order,
        # payment/units/lex ties and a chain of near ties cannot alter the winner.
        if math.isfinite(upper) and row['value'] > math.nextafter(upper+tolerance,math.inf):
            continue
        if joint is not None and boxes+joint_work < max_boxes:
            remaining = max_boxes-boxes-joint_work
            bounded = joint(left,right,work_budget=remaining)
            charged = 1+bounded['batchStates']*(1+len(posterior))
            assert charged <= remaining
            joint_work += charged
            upper = min(upper,bounded['upperValue'])
            tolerance = 1e-9+1e-12*max(abs(upper),abs(row['value']))
            if upper == -math.inf or (math.isfinite(upper) and row['value'] > math.nextafter(upper+tolerance,math.inf)):
                continue
        axis = next((i for i,(a,b) in enumerate(zip(left,right)) if a!=b),None)
        if axis is None:
            return result(certified=False, reason='not-strictly-dominated', boxes=boxes, allocations=1, proposal=row)
        middle = left[axis]+((right[axis]-left[axis])//lots[axis]//2)*lots[axis]
        low_hi = list(right);low_hi[axis]=middle
        high_lo = list(left);high_lo[axis]=middle+lots[axis]
        stack.append((tuple(high_lo),right));stack.append((left,tuple(low_hi)))
    return result(certified=True, reason='strict-ledger-value-dominance', boxes=boxes, allocations=1, proposal=row)


class ProposalMemo:
    """Bounded hints only: every hit still requires a fresh strict proof."""
    def __init__(self,capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:
            raise ValueError('positive proposal memo capacity required')
        self.capacity=capacity;self.data=OrderedDict();self.hits=self.misses=self.peak_entries=0

    def key(self,problem):
        lines=tuple(replace(line,output_values=tuple(v-line.output_values[0] for v in line.output_values)) for line in problem.lines)
        n=len(problem.held)
        # This is intentionally a hint key, not a value/policy equivalence key.
        # Basis, loyalty and funded caps are rechecked by the strict proof and
        # complete fallback; they may change which hint is useful.
        return replace(problem,cash=0.,lines=lines,basis=(0.,)*n,incumbents=(-1,)*n,
                       bids=(0,)*n,fees=(0.,)*n,funded_demands=None)

    def get(self,key):
        if key in self.data:
            self.hits+=1;self.data.move_to_end(key);return self.data[key]
        self.misses+=1;return None

    def put(self,key,allocation):
        self.data[key]=tuple(allocation)
        if len(self.data)>self.capacity:self.data.popitem(last=False)
        self.peak_entries=max(self.peak_entries,len(self.data))


def solve(company, initial, state, event, posterior, *, neutral=False, max_allocations=100000, max_boxes=100000, proposal_memo=None, joint_proposals=False, joint_memo=None, cash_relaxed_joint_bound=False,joint_fallback=False):
    """Try a bounded strict proof, then retain the full lexicographic fallback.

    Proposal generation is only a hint. Its algebraic certificate is never used
    as a ledger certificate. Charge its two evaluations and batch-count scan.
    """
    from .industry import pack
    from .industry_relaxation import certified_candidate
    from .joint_line_proposal import candidate as joint_candidate
    from .closing_boxes import solve as fallback
    if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (max_allocations,max_boxes)):
        raise ValueError('positive closing leaf and box budgets required')
    problem=prepare(company,initial,state,event,posterior,neutral=neutral)
    if problem is None:return None
    proposal_states=proof_boxes=proposal_evaluations=joint_work=0
    eligible=(len(problem.lines)==1 or joint_proposals) and all(v==0. for table in problem.terminal_values for v in table)
    if proposal_memo is not None and not isinstance(proposal_memo,ProposalMemo):
        raise ValueError('proposal memo type required')
    states=math.prod(line.max_batches+1 for line in problem.lines) if eligible else 0
    allocation=None;memo_key=None
    if eligible and proposal_memo is not None and max_boxes>4:
        memo_key=proposal_memo.key(problem);allocation=proposal_memo.get(memo_key)
        proposal_states=1  # Charge lookup/key work even when no proof follows.
    generation_states=0 if allocation is not None else states
    # Engineering work split only: keep at least three quarters of the original
    # box budget for fallback, and cap the speculative proof at 256 boxes.
    proof_budget=min(max_boxes if joint_proposals else 256,max_boxes//4-proposal_states-generation_states)
    required_allocations=1 if allocation is not None else 3
    if eligible and proof_budget>0 and max_allocations>=required_allocations:
        proposal_states+=generation_states
        generation_evaluations=0
        if allocation is None:
            generator=certified_candidate if len(problem.lines)==1 else joint_candidate
            candidate,_=generator(pack(problem))
            allocation=tuple(int(q) for q in candidate[0]);generation_evaluations=2
            if memo_key is not None:proposal_memo.put(memo_key,allocation)
        proof=certify(company,initial,state,event,posterior,allocation,neutral=neutral,max_boxes=proof_budget,joint_bound=joint_proposals,joint_memo=joint_memo,cash_relaxed_joint_bound=cash_relaxed_joint_bound)
        proposal_evaluations=generation_evaluations+proof['allocations']
        proof_boxes=proof['boxes']
        joint_work=proof.get('jointBoundWork',0)
        if proof['certified']:
            cardinality=math.prod(min(o.stock,max(0,company.slots[o.material]-state.held[o.material]))//o.lot+1 for o in event.offers)
            return dict(proof['proposal'],enumeratedAllocations=proposal_evaluations,boxes=proof_boxes,
                        prunedBoxes=0,skippedAllocations=cardinality-1,cartesianAllocations=cardinality,
                        proposalStates=proposal_states,certificates=1,**({'jointBoundWork':joint_work} if joint_proposals else {}))
    remaining_allocations=max_allocations-proposal_evaluations
    if remaining_allocations<1:
        raise ValueError('closing allocation node limit; no approximate result returned')
    result=fallback(company,initial,state,event,posterior,neutral=neutral,
                    max_allocations=remaining_allocations,max_boxes=max_boxes-proposal_states-proof_boxes-joint_work,
                    include_costs=True,compiled_costs=True,joint_bound=joint_fallback,joint_memo=joint_memo,cash_relaxed_joint_bound=cash_relaxed_joint_bound)
    result=dict(result,enumeratedAllocations=result['enumeratedAllocations']+proposal_evaluations,
                boxes=result['boxes']+proof_boxes,proposalStates=proposal_states,certificates=0)
    if joint_proposals or joint_fallback:result['jointBoundWork']=joint_work+result.get('jointBoundWork',0)
    return result
