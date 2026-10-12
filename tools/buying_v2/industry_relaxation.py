"""Single-line cost relaxation, accepted only after actual execution verifies it.

The complete solver remains the fallback. No useful-buffer, multiple-line, fee,
lot or gate action is removed from that fallback's supported space.
"""
import numpy as np
from .jit import njit
from .industry import enumerate_allocations


@njit
def certified_candidate(args):
    held, basis, spaces, slots, room, cash, material, supplier, price, stock, lot, incumbents, bids, fees, recipe, bounds, conversion, quote, overhead, output_qty, output_space, output_values, terminal_values, band, funded_demands = args
    n, offers = len(held), len(material)
    zeros = np.zeros(offers, dtype=np.int64)
    baseline = enumerate_allocations(*args, zeros, zeros)
    if len(bounds) != 1 or np.any(terminal_values != 0):
        return baseline, False
    for m in range(n):
        if incumbents[m] >= 0 and bids[m] > 0 and fees[m] > 0:
            for i in range(offers):
                if material[i] == m and supplier[i] == incumbents[m] and stock[i] >= bids[m]:
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
    for batches in range(bounds[0]+1):
        q = np.zeros(offers, dtype=np.int64)
        needed = np.zeros(n, dtype=np.int64)
        used = 0.
        valid = True
        for m in range(n):
            deficit = max(0, recipe[0,m]*batches-held[m])
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
        expense = batches*output_qty[0]*conversion[0]
        if goods+expense > cash:
            continue
        score = output_values[0,batches*output_qty[0]]-goods-expense
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
    tol = 1e-9+1e-12*max(abs(best_score),abs(actual[3])) if np.isfinite(best_score) else 0.
    certified = np.isfinite(best_score) and np.isfinite(actual[3]) and abs(actual[3]-best_score) <= tol
    return actual, certified
