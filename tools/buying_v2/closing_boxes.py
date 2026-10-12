"""Conservative ledger-order range bounds and lexicographic closing search."""
import math
from .closing_allocation import prepare
from .closing_values import _prepared_evaluator


def _up(x):
    return math.nextafter(x, math.inf)


def _down(x):
    return math.nextafter(x, -math.inf)


def upper_value(problem, initial, state, posterior, lo, hi, *, neutral=False):
    """Bound validated whole-lot boxes. Costs/gates/shared inputs are relaxed.

    Each arithmetic operation rounds outward. No algebraic cancellation with
    initial cash is used: the bound follows actual ledger cash/terminal order.
    """
    n = len(state.held)
    minimum = list(state.held)
    maximum = list(state.held)
    outside = [False]*n
    goods = 0.
    for offer, left, right in zip(problem.offers, lo, hi):
        minimum[offer.material] += left
        maximum[offer.material] += right
        goods = _down(goods+_down(left*offer.price))
        outside[offer.material] |= left > 0 and offer.supplier != state.incumbents[offer.material]
    if any(q > cap for q, cap in zip(minimum, problem.slots)):
        return -math.inf
    # Eligibility restricts all physical dimensions and sums to exact integers.
    used = sum((q-h)*int(s) for q, h, s in zip(minimum, state.held, problem.spaces))
    if used > problem.free_space:
        return -math.inf
    fees = 0.
    for m in range(n):
        if outside[m] and problem.incumbents[m] >= 0 and problem.bids[m] > 0:
            if any(o.material == m and o.supplier == problem.incumbents[m] and o.stock >= problem.bids[m]
                   for o in problem.offers):
                fees = _down(fees+problem.fees[m])
    payment = _down(goods+fees)
    if payment > state.cash:
        return -math.inf
    maximum = [min(q, cap) for q, cap in zip(maximum, problem.slots)]
    finished = []
    for old, line in zip(state.finished, problem.lines):
        batches = min([line.max_batches]+[maximum[m]//q for m, q in enumerate(line.recipe) if q])
        finished.append(old+batches*line.output_qty)
    cash = _up(state.cash-payment)  # Zero conversion is an optimistic relaxation.
    weighted = []
    for weight, scenario in posterior:
        sales = 0.
        terminal = 0.
        for m, table in enumerate(scenario.input_values):
            terminal = _up(terminal+max(table[:maximum[m]+1]))
        for r, table in enumerate(scenario.finished_values):
            sales = _up(sales+_up(min(finished[r], scenario.events[1].demand[r])*state.quotes[r]))
            terminal = _up(terminal+max(table[:finished[r]+1]))
        closing = _up(_up(cash+sales)+(0. if neutral else scenario.events[1].fee_income))
        value = _up(_up(_up(closing-initial.cash)-(state.arrears-initial.arrears))+terminal)
        term = _up(weight*value)
        if not math.isfinite(term):
            return math.inf
        weighted.append(term)
    try:
        return _up(_up(math.fsum(weighted))/math.fsum(w for w, _ in posterior))
    except OverflowError:
        return math.inf


def solve(company, initial, state, event, posterior, *, neutral=False, max_allocations=100000, max_boxes=100000, include_costs=False, compiled_costs=False,joint_bound=False,joint_memo=None,cash_relaxed_joint_bound=False):
    """Skip only provably inferior/infeasible contiguous lexicographic ranges."""
    if not isinstance(joint_bound,bool):raise ValueError('joint fallback flag must be boolean')
    if any(not isinstance(x, int) or isinstance(x, bool) or x < 1 for x in (max_allocations, max_boxes)):
        raise ValueError('positive closing leaf and box budgets required')
    problem = prepare(company, initial, state, event, posterior, neutral=neutral)
    if problem is None:
        return None
    run = _prepared_evaluator(problem, initial, state, event, posterior, neutral=neutral)
    cost_bound = None
    if include_costs:
        if compiled_costs:
            from .closing_cost_compiled import bounder
        else:
            from .closing_cost_bound import bounder
        cost_bound = bounder(problem, initial, state, posterior, neutral=neutral)
    joint=None;joint_work=0
    if joint_bound and len(problem.lines)>1:
        if cash_relaxed_joint_bound:
            from .closing_cash_relaxed_bound import bounder as joint_bounder
            options=dict(compiled=True)
        else:
            from .closing_joint_compiled import bounder as joint_bounder
            options={}
        joint=joint_bounder(problem,initial,state,posterior,neutral=neutral,
            max_states=math.prod(line.max_batches+1 for line in problem.lines),memo=joint_memo,**options)
    lo = (0,)*len(event.offers)
    hi = tuple(min(o.stock, max(0, company.slots[o.material]-state.held[o.material]))//o.lot*o.lot for o in event.offers)
    stack = [(lo, hi)]
    best = None
    boxes = leaves = skipped = pruned = 0
    while stack:
        if boxes+joint_work >= max_boxes:
            raise ValueError('closing box node limit; no approximate result returned')
        left, right = stack.pop()
        boxes += 1
        bound = upper_value(problem, initial, state, posterior, left, right, neutral=neutral)
        if bound != -math.inf and cost_bound is not None:
            bound = min(bound, cost_bound(left, right))
        discard = bound == -math.inf
        if best is not None and math.isfinite(bound):
            tolerance = 1e-9+1e-12*max(abs(bound), abs(best['value']))
            discard |= bound < best['value']-tolerance
        if not discard and best is not None and joint is not None and any(a!=b for a,b in zip(left,right)):
            remaining=max_boxes-boxes-joint_work
            if remaining>0:
                bounded=joint(left,right,work_budget=remaining)
                charged=1+bounded['batchStates']*(1+len(posterior))
                if charged>remaining:raise AssertionError('joint fallback exceeded reserved work')
                joint_work+=charged
                bound=min(bound,bounded['upperValue'])
                tolerance=1e-9+1e-12*max(abs(bound),abs(best['value']))
                discard=bound==-math.inf or (math.isfinite(bound) and bound<best['value']-tolerance)
        if discard:
            skipped += math.prod((b-a)//o.lot+1 for a, b, o in zip(left, right, event.offers))
            pruned += 1
            continue
        axis = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), None)
        if axis is not None:
            lot = event.offers[axis].lot
            middle = left[axis]+((right[axis]-left[axis])//lot//2)*lot
            low_hi = list(right);low_hi[axis] = middle
            high_lo = list(left);high_lo[axis] = middle+lot
            # First varying coordinate, low half first: identical leaf order to
            # itertools.product. Value-guided reordering would alter near ties.
            stack.append((tuple(high_lo), right))
            stack.append((left, tuple(low_hi)))
            continue
        if leaves >= max_allocations:
            raise ValueError('closing allocation node limit; no approximate result returned')
        leaves += 1
        row = run((left,))[0]
        if row is None:
            continue
        better = best is None
        if best is not None:
            tolerance = 1e-9+1e-12*max(abs(row['value']), abs(best['value']))
            cost_tolerance = 1e-9+1e-12*max(abs(row['payment']), abs(best['payment']))
            better = row['value'] > best['value']+tolerance or (abs(row['value']-best['value']) <= tolerance and (
                row['payment'] < best['payment']-cost_tolerance or (abs(row['payment']-best['payment']) <= cost_tolerance
                and (sum(row['allocation']), row['allocation']) < (sum(best['allocation']), best['allocation']))))
        if better:best = row
    if best is None:
        raise ValueError('no feasible closing allocation')
    return dict(best, enumeratedAllocations=leaves, boxes=boxes, prunedBoxes=pruned, skippedAllocations=skipped,
                cartesianAllocations=math.prod(q//o.lot+1 for q, o in zip(hi, event.offers)),**({'jointBoundWork':joint_work} if joint_bound else {}))
