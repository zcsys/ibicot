"""Conditional-output closing bound with relaxed minimum input spending.

One installed line is fixed at each possible output. All other lines retain
optimistic independent access to inputs. This bounds each feasible allocation;
it does not select production independently of the actual production gate.
"""
from fractions import Fraction
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


def bounder(problem, initial, state, posterior, *, neutral=False):
    prices = tuple(Fraction(o.price) for o in problem.offers)
    orders = tuple(tuple(sorted((i for i, o in enumerate(problem.offers) if o.material == m),
                               key=lambda i: problem.offers[i].price)) for m in range(len(state.held)))
    mass = math.fsum(w for w, _ in posterior)
    input_prefixes = []
    finished_prefixes = []
    for _, scenario in posterior:
        for destination, tables in ((input_prefixes, scenario.input_values), (finished_prefixes, scenario.finished_values)):
            rows = []
            for table in tables:
                top = -math.inf;row = []
                for value in table:
                    top = max(top, value);row.append(top)
                rows.append(tuple(row))
            destination.append(tuple(rows))

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
            return -math.inf
        maximum = [min(q, cap) for q, cap in zip(maximum, problem.slots)]
        limits = [min([line.max_batches]+[maximum[m]//q for m, q in enumerate(line.recipe) if q]) for line in problem.lines]
        finished = [old+limit*line.output_qty for old, limit, line in zip(state.finished, limits, problem.lines)]
        result = math.inf
        cost_cache = {}
        for anchor, line in enumerate(problem.lines):
            best = -math.inf
            for batches in range(limits[anchor]+1):
                needed = tuple(max(0, q*batches-minimum[m]) for m, q in enumerate(line.recipe))
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
                units = batches*line.output_qty
                conversion = units*line.conversion
                if not math.isfinite(conversion):
                    continue
                # Ignore all fees and other lines' conversion, retaining this
                # line's actual rounded expense and the cash operation order.
                cash = _up(_up(state.cash-goods)-conversion)
                weighted = []
                for scenario_index, (weight, scenario) in enumerate(posterior):
                    sales = terminal = 0.
                    for m, q in enumerate(line.recipe):
                        terminal = _up(terminal+input_prefixes[scenario_index][m][maximum[m]-q*batches])
                    for r, cap in enumerate(finished):
                        stock = state.finished[r]+units if r == anchor else cap
                        sold = min(stock, scenario.events[1].demand[r])
                        sales = _up(sales+_up(sold*state.quotes[r]))
                        remaining = stock-sold
                        value = scenario.finished_values[r][remaining] if r == anchor else finished_prefixes[scenario_index][r][remaining]
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
            result = min(result, best)
        return result
    return bound
