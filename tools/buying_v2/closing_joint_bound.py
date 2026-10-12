"""Bounded joint-output closing relaxation, independent of planner selection.

Every actual sequential output vector appears in this Cartesian relaxation.
Aggregate inputs are conserved; gates, fees, lots and storage are relaxed.
Fractional minimum procurement costs and outward rounding bound ledger value.
"""
from fractions import Fraction
from itertools import product
import math
import sys
from .closing_boxes import _up, _down


def _floor_float(value):
    if value <= 0:
        return 0.
    try:
        result = float(value)
    except OverflowError:
        return sys.float_info.max
    return _down(result) if Fraction(result) > value else result


def bounder(problem, initial, state, posterior, *, neutral=False, max_states=4096):
    if not isinstance(max_states,int) or isinstance(max_states,bool) or max_states<1:
        raise ValueError('positive joint batch-state budget required')
    prices = tuple(Fraction(o.price) for o in problem.offers)
    orders = tuple(tuple(sorted((i for i, o in enumerate(problem.offers) if o.material == m),
                               key=lambda i: problem.offers[i].price)) for m in range(len(state.held)))
    mass = math.fsum(w for w, _ in posterior)
    input_prefixes = []
    for _, scenario in posterior:
        rows = []
        for table in scenario.input_values:
            top = -math.inf;row = []
            for value in table:
                top = max(top, value);row.append(top)
            rows.append(tuple(row))
        input_prefixes.append(tuple(rows))

    def bound(lo, hi):
        minimum = list(state.held);maximum = list(state.held)
        base = Fraction(0)
        error = Fraction(0)
        prefix = 0.
        for i, (offer, left, right) in enumerate(zip(problem.offers, lo, hi)):
            minimum[offer.material] += left;maximum[offer.material] += right
            base += left*prices[i]
            top = right*offer.price
            prefix = _up(prefix+_up(top))
            if not math.isfinite(prefix):
                error = None
            elif error is not None:
                # Actual goods uses rounded products followed by sequential
                # additions. One full ulp per product/addition is conservative
                # over this positive box, including subnormal boundaries.
                error += Fraction(math.ulp(top))+Fraction(math.ulp(prefix))
        if any(q > cap for q, cap in zip(minimum, problem.slots)):
            return dict(upperValue=-math.inf,batchStates=0)
        maximum = [min(q, cap) for q, cap in zip(maximum, problem.slots)]
        limits = [min([line.max_batches]+[maximum[m]//q for m, q in enumerate(line.recipe) if q]) for line in problem.lines]
        count = math.prod(limit+1 for limit in limits)
        if count > max_states:
            return dict(upperValue=math.inf,batchStates=0)
        best = -math.inf
        cost_cache = {}
        for batches in product(*(range(limit+1) for limit in limits)):
            required = tuple(sum(line.recipe[m]*b for line,b in zip(problem.lines,batches)) for m in range(len(state.held)))
            if any(q > cap for q,cap in zip(required,maximum)):
                continue
            needed = tuple(max(0,q-minimum[m]) for m,q in enumerate(required))
            if needed not in cost_cache:
                exact = base
                for m, missing in enumerate(needed):
                    for i in orders[m]:
                        take = min(missing, hi[i]-lo[i])
                        exact += take*prices[i];missing -= take
                        if not missing:break
                    if missing:raise AssertionError('output cap exceeds relaxed input supply')
                cost_cache[needed] = 0. if error is None else _floor_float(exact-error)
            goods = cost_cache[needed]
            if goods > state.cash:
                continue
            units = tuple(b*line.output_qty for b,line in zip(batches,problem.lines))
            expenses = tuple(q*line.conversion for q,line in zip(units,problem.lines))
            if any(not math.isfinite(x) for x in expenses):
                continue
            # Preserve installed-line cash subtraction order, with an
            # upper rounded balance and no fees, gates or room restrictions.
            cash = _up(state.cash-goods)
            for expense in expenses:
                cash = _up(cash-expense)
            weighted = []
            for scenario_index, (weight, scenario) in enumerate(posterior):
                sales = terminal = 0.
                for m, q in enumerate(required):
                    terminal = _up(terminal+input_prefixes[scenario_index][m][maximum[m]-q])
                for r, quantity in enumerate(units):
                    stock = state.finished[r]+quantity
                    sold = min(stock, scenario.events[1].demand[r])
                    sales = _up(sales+_up(sold*state.quotes[r]))
                    remaining = stock-sold
                    value = scenario.finished_values[r][remaining]
                    terminal = _up(terminal+value)
                closing = _up(_up(cash+sales)+(0. if neutral else scenario.events[1].fee_income))
                value = _up(_up(_up(closing-initial.cash)-(state.arrears-initial.arrears))+terminal)
                term = _up(weight*value)
                if not math.isfinite(term):
                    weighted = None;break
                weighted.append(term)
            try:
                value = math.inf if weighted is None else _up(_up(math.fsum(weighted))/mass)
            except OverflowError:
                value = math.inf
            best = max(best, value)
        return dict(upperValue=best,batchStates=count)
    return bound
