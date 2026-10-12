"""Joint-line closing hint; never an optimality certificate.

Enumerate joint batch targets, buy their aggregate deficits at cheapest quotes,
and score the relaxed targets. Actual sequential production may differ. Callers
must prove strict ledger dominance or fall back to complete lexicographic search.
The caller reserves the Cartesian batch-state count before invoking this helper.
"""
import numpy as np
from .jit import njit
from .industry import enumerate_allocations


@njit
def candidate(args):
    held, basis, spaces, slots, room, cash, material, supplier, price, stock, lot, incumbents, bids, fees, recipe, bounds, conversion, quote, overhead, output_qty, output_space, output_values, terminal_values, band, funded_demands = args
    n, offers = len(held), len(material)
    zeros = np.zeros(offers, dtype=np.int64)
    baseline = enumerate_allocations(*args, zeros, zeros)
    if len(bounds) < 2 or np.any(terminal_values != 0):
        return baseline, False
    lots = np.ones(n, dtype=np.int64)
    for m in range(n):
        seen = 0
        for i in range(offers):
            if material[i] == m:
                if seen and lot[i] != seen:
                    return baseline, False
                seen = lot[i]
        if seen:
            lots[m] = seen
    order = np.arange(offers)
    for j in range(1, offers):
        i = order[j]
        k = j-1
        # Lexicographically smaller allocations fill later equal-price offers.
        while k >= 0 and (price[i] < price[order[k]] or (price[i] == price[order[k]] and i > order[k])):
            order[k+1] = order[k]
            k -= 1
        order[k+1] = i
    best = zeros.copy()
    best_score = -np.inf
    best_goods = np.inf
    best_units = 0
    count = 1
    for bound in bounds:
        count *= bound+1
    batches = np.zeros(len(bounds), dtype=np.int64)
    for ordinal in range(count):
        remainder = ordinal
        for r in range(len(bounds)-1, -1, -1):
            batches[r] = remainder % (bounds[r]+1)
            remainder //= bounds[r]+1
        q = np.zeros(offers, dtype=np.int64)
        needed = np.zeros(n, dtype=np.int64)
        used = 0.
        valid = True
        for m in range(n):
            required = 0
            for r in range(len(bounds)):
                required += recipe[r,m]*batches[r]
            deficit = max(0, required-held[m])
            needed[m] = (deficit+lots[m]-1)//lots[m]*lots[m]
            used += needed[m]*spaces[m]
            if held[m]+needed[m] > slots[m]:
                valid = False
        if not valid or used > room:
            continue
        for rank in range(offers):
            i = order[rank]
            m = material[i]
            take = min(needed[m], stock[i]//lot[i]*lot[i])
            q[i] = take
            needed[m] -= take
        if np.any(needed > 0):
            continue
        goods = 0.
        for i in range(offers):
            goods += q[i]*price[i]
        expense = 0.
        value = 0.
        for r in range(len(bounds)):
            units = batches[r]*output_qty[r]
            expense += units*conversion[r]
            value += output_values[r,units]
        if goods+expense > cash:
            continue
        score = value-goods-expense
        total = q.sum()
        tol = 1e-9+1e-12*max(abs(score),abs(best_score)) if np.isfinite(best_score) else 0.
        lex = False
        for i in range(offers):
            if q[i] != best[i]:
                lex = q[i] < best[i]
                break
        cost_tol = 1e-9+1e-12*max(abs(goods),abs(best_goods)) if np.isfinite(best_goods) else 0.
        cheaper = goods < best_goods-cost_tol or (abs(goods-best_goods) <= cost_tol and (total < best_units or (total == best_units and lex)))
        if score > best_score+tol or (abs(score-best_score) <= tol and cheaper):
            best[:] = q
            best_score, best_goods, best_units = score, goods, total
    actual = enumerate_allocations(*args, best, best)
    # Even a matching relaxed score cannot certify ledger arithmetic or ties.
    return actual, False
