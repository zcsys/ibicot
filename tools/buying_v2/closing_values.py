"""Batch closing values and bounded exhaustive selection in ledger arithmetic.

Python math.fsum preserves the event tree's posterior reduction; it is
deliberately outside compiled code. This is still an exponential oracle path.
"""
import math
import numpy as np
from .jit import njit
from .industry import pack, enumerate_allocations
from .closing_allocation import prepare
from .float_sum import add, finish


@njit
def _values(args, allocations, initial_cash, liability_change, old_finished,
            quotes, demand, fee_income, input_values, finished_values):
    values = np.full((len(allocations), len(demand)), -np.inf)
    payments = np.full(len(allocations), np.inf)
    for row in range(len(allocations)):
        allocation = allocations[row]
        result = enumerate_allocations(*args, allocation, allocation)
        if not np.isfinite(result[3]):
            continue
        payments[row] = result[4]
        cash = args[5]-result[4]
        for r in range(len(old_finished)):
            cash -= result[1][r]*args[16][r]
        for scenario in range(len(demand)):
            revenue = 0.
            revenue_correction = 0.
            terminal = 0.
            for m in range(len(result[2])):
                terminal += input_values[scenario, m, result[2][m]]
            for r in range(len(old_finished)):
                stock = old_finished[r]+result[1][r]
                sold = min(stock, demand[scenario, r])
                revenue, revenue_correction = add(revenue, revenue_correction, sold*quotes[r])
                terminal += finished_values[scenario, r, stock-sold]
            final_cash = cash+finish(revenue, revenue_correction)+fee_income[scenario]
            values[row, scenario] = final_cash-initial_cash-liability_change+terminal
    return values, payments


def evaluator(company, initial, state, event, posterior, *, neutral=False):
    """Pack one conditional closing problem; return a reusable basket evaluator."""
    problem = prepare(company, initial, state, event, posterior, neutral=neutral)
    if problem is None:
        return None
    return _prepared_evaluator(problem, initial, state, event, posterior, neutral=neutral)


def _prepared_evaluator(problem, initial, state, event, posterior, *, neutral=False):
    """Internal reuse of prepare's validated problem for this exact solve only."""
    # The combined solver's objective is irrelevant here. Zero it to avoid
    # overflow or cancellation in unused value-table calculations.
    from dataclasses import replace
    problem = replace(problem, lines=tuple(replace(line, output_values=(0.,)*len(line.output_values)) for line in problem.lines),
                      terminal_values=tuple((0.,)*len(table) for table in problem.terminal_values))
    args = pack(problem)
    count = len(posterior)
    iv = np.zeros((count, len(state.held), max(len(t) for _, s in posterior for t in s.input_values)))
    fv = np.zeros((count, len(state.finished), max(len(t) for _, s in posterior for t in s.finished_values)))
    for i, (_, scenario) in enumerate(posterior):
        for m, table in enumerate(scenario.input_values):iv[i, m, :len(table)] = table
        for r, table in enumerate(scenario.finished_values):fv[i, r, :len(table)] = table
    old_finished = np.asarray(state.finished, dtype=np.int64)
    quotes = np.asarray(state.quotes)
    demand = np.asarray([s.events[1].demand for _, s in posterior], dtype=np.int64)
    fee_income = np.asarray([0. if neutral else s.events[1].fee_income for _, s in posterior])
    mass = math.fsum(w for w, _ in posterior)
    def run(allocations):
        rows = tuple(tuple(q) for q in allocations)
        for allocation in rows:
            if len(allocation) != len(event.offers):
                raise ValueError('allocation length differs from offers')
            if any(not isinstance(q, int) or isinstance(q, bool) or q < 0 or q > o.stock or q % o.lot
                   for q, o in zip(allocation, event.offers)):
                raise ValueError('allocation must respect whole offer lots and stock')
        values, payments = _values(args, np.asarray(rows, dtype=np.int64).reshape((len(rows), len(event.offers))),
            initial.cash, state.arrears-initial.arrears, old_finished, quotes,
            demand, fee_income, iv, fv)
        answer = []
        for row in range(len(rows)):
            if np.isneginf(values[row]).all():
                answer.append(None)
                continue
            if not np.isfinite(values[row]).all():
                raise ValueError('nonfinite closing payoff')
            weighted = math.fsum(w*float(v) for (w, _), v in zip(posterior, values[row]))
            answer.append(dict(allocation=rows[row], value=weighted/mass, weightedValue=weighted,
                               scenarioValues=tuple(float(v) for v in values[row]), payment=float(payments[row])))
        return answer
    return run


def evaluate(company, initial, state, event, posterior, allocations, *, neutral=False):
    """Return ledger-order values, None for unsupported scope/infeasible rows."""
    run = evaluator(company, initial, state, event, posterior, neutral=neutral)
    return None if run is None else run(allocations)


def solve(company, initial, state, event, posterior, *, neutral=False, max_allocations=100000):
    """Exhaustive closing optimizer preserving the event tree's lexicographic scan.

    This accelerates evaluation only; it does not solve combinatorial scaling.
    Explicit limits count the full Cartesian action space, including infeasibility.
    """
    from itertools import product
    if not isinstance(max_allocations, int) or isinstance(max_allocations, bool) or max_allocations < 1:
        raise ValueError('positive closing enumeration budget required')
    problem = prepare(company, initial, state, event, posterior, neutral=neutral)
    if problem is None:
        return None
    ranges = tuple(range(0, min(o.stock, max(0, company.slots[o.material]-state.held[o.material]))+1, o.lot)
                   for o in event.offers)
    count = math.prod(len(r) for r in ranges)
    if count > max_allocations:
        raise ValueError('closing exhaustive node limit; no approximate result returned')
    run = _prepared_evaluator(problem, initial, state, event, posterior, neutral=neutral)
    rows = run(product(*ranges))
    best = None
    for row in rows:
        if row is None:
            continue
        better = best is None
        if best is not None:
            tolerance = 1e-9+1e-12*max(abs(row['value']), abs(best['value']))
            cost_tolerance = 1e-9+1e-12*max(abs(row['payment']), abs(best['payment']))
            better = row['value'] > best['value']+tolerance or (abs(row['value']-best['value']) <= tolerance and (
                row['payment'] < best['payment']-cost_tolerance or (abs(row['payment']-best['payment']) <= cost_tolerance
                and (sum(row['allocation']), row['allocation']) < (sum(best['allocation']), best['allocation']))))
        if better:
            best = row
    if best is None:
        raise ValueError('no feasible closing allocation')
    return dict(best, enumeratedAllocations=count)
