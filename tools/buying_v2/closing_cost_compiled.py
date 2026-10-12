"""Directed-rounding compiled counterpart to the rational closing-cost bound.

Minimum goods cost rounds down; its arithmetic-error allowance rounds up.
The posterior sum also rounds upward instead of requiring compiled math.fsum.
"""
import math
import numpy as np
from .jit import njit


@njit
def up(value):
    return np.nextafter(value, np.inf)


@njit
def down(value):
    return np.nextafter(value, -np.inf)


@njit
def _bound(args, lo, hi):
    held, slots, material, price, order, recipe, capacity, yield_qty, conversion, old, quote, opening_cash, initial_cash, liabilities, weights, mass, demand, fee_income, inputs, terminal, finished_prefix = args
    minimum = held.copy();maximum = held.copy()
    base = error = prefix = 0.
    for i in range(len(material)):
        m = material[i]
        minimum[m] += lo[i];maximum[m] += hi[i]
        base = down(base+down(lo[i]*price[i]))
        top = hi[i]*price[i]
        prefix = up(prefix+up(top))
        if not np.isfinite(prefix):
            error = np.inf
        elif np.isfinite(error):
            # For finite positive values, this equals ulp except at the
            # greatest finite float, where infinity safely weakens the bound.
            allowance = up((up(top)-top)+(up(prefix)-prefix))
            error = up(error+allowance)
    for m in range(len(held)):
        if minimum[m] > slots[m]:return -np.inf
        maximum[m] = min(maximum[m], slots[m])
    limits = capacity.copy()
    finished = old.copy()
    for r in range(len(capacity)):
        for m in range(len(held)):
            if recipe[r, m]:limits[r] = min(limits[r], maximum[m]//recipe[r, m])
        finished[r] += limits[r]*yield_qty[r]
    result = np.inf
    for anchor in range(len(capacity)):
        best = -np.inf
        for batches in range(limits[anchor]+1):
            lower = base
            for m in range(len(held)):
                missing = max(0, recipe[anchor, m]*batches-minimum[m])
                for rank in range(len(order)):
                    if missing == 0:break
                    i = order[rank]
                    if material[i] != m:continue
                    take = min(missing, hi[i]-lo[i])
                    lower = down(lower+down(take*price[i]));missing -= take
                if missing:raise AssertionError('output cap exceeds relaxed input supply')
            goods = max(0., down(lower-error)) if np.isfinite(error) else 0.
            if goods > opening_cash:continue
            units = batches*yield_qty[anchor]
            expense = units*conversion[anchor]
            if not np.isfinite(expense):continue
            cash = up(up(opening_cash-goods)-expense)
            weighted = 0.
            for s in range(len(weights)):
                sales = remaining_value = 0.
                for m in range(len(held)):
                    remaining_value = up(remaining_value+inputs[s, m, maximum[m]-recipe[anchor, m]*batches])
                for r in range(len(capacity)):
                    stock = old[r]+units if r == anchor else finished[r]
                    sold = min(stock, demand[s, r])
                    sales = up(sales+up(sold*quote[r]))
                    remaining = stock-sold
                    value = terminal[s, r, remaining] if r == anchor else finished_prefix[s, r, remaining]
                    remaining_value = up(remaining_value+value)
                closing = up(up(cash+sales)+fee_income[s])
                value = up(up(up(closing-initial_cash)-liabilities)+remaining_value)
                term = up(weights[s]*value)
                weighted = up(weighted+term)
                if not np.isfinite(term) or not np.isfinite(weighted):
                    weighted = np.inf;break
            value = up(up(weighted)/mass)
            best = max(best, value)
        result = min(result, best)
    return result


def _pack(problem, initial, state, posterior, *, neutral=False):
    """Pack a validated closing problem once; produce a reusable box bound."""
    iv = lambda values: np.asarray(values, dtype=np.int64)
    fv = lambda values: np.asarray(values, dtype=np.float64)
    n = len(state.held);lines = len(state.finished);scenarios = len(posterior)
    inputs = np.zeros((scenarios, n, max(len(t) for _, s in posterior for t in s.input_values)))
    terminal = np.zeros((scenarios, lines, max(len(t) for _, s in posterior for t in s.finished_values)))
    finished_prefix = np.zeros_like(terminal)
    for s, (_, scenario) in enumerate(posterior):
        for m, table in enumerate(scenario.input_values):inputs[s, m, :len(table)] = np.maximum.accumulate(table)
        for r, table in enumerate(scenario.finished_values):
            terminal[s, r, :len(table)] = table
            finished_prefix[s, r, :len(table)] = np.maximum.accumulate(table)
    order = sorted(range(len(problem.offers)), key=lambda i: problem.offers[i].price)
    args = (iv(state.held), iv(problem.slots), iv([o.material for o in problem.offers]), fv([o.price for o in problem.offers]),
        iv(order), iv([line.recipe for line in problem.lines]), iv([line.max_batches for line in problem.lines]),
        iv([line.output_qty for line in problem.lines]), fv([line.conversion for line in problem.lines]),
        iv(state.finished), fv(state.quotes), state.cash, initial.cash, state.arrears-initial.arrears,
        fv([w for w, _ in posterior]), math.fsum(w for w, _ in posterior), iv([s.events[1].demand for _, s in posterior]),
        fv([0. if neutral else s.events[1].fee_income for _, s in posterior]), inputs, terminal, finished_prefix)
    return args


def bounder(problem, initial, state, posterior, *, neutral=False):
    args = _pack(problem, initial, state, posterior, neutral=neutral)
    return lambda lo, hi: float(_bound(args, np.asarray(lo,dtype=np.int64), np.asarray(hi,dtype=np.int64)))
