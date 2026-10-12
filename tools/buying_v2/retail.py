"""Exact single-product basket solver for the accepted one-fee contract.

Search scope is supplied by the caller. Values are descending marginal values
consistent with the buyer's price-sensitive quantity curve. This is retail
surplus, not a manufacturer's expected-profit model. The incumbent availability
bid and per-quote funded demands are computed before calling this function.
"""
import numpy as np
from .jit import njit


@njit
def solve_retail_into(values, value_count, prices, stock, supplier_ids, n, incumbent, bid, fee, cash,
                      funded_demands, best, order):
    """Return allocation, net surplus, goods cost, fee and final preference.

    Enumerate every quantity along the cheapest feasible goods prefix, plus
    the incumbent-only family. For a fixed quantity, a uniform one-time outside
    fee cannot distinguish two outside baskets, so their cheapest goods prefix
    suffices; the no-fee incumbent-only family must be compared separately.
    Exact-surplus ties retain the incumbent-only family when available, then
    the earlier quantity within a family; equal quotes prefer incumbent then
    stable ID. Stable-ID fairness remains a separate validation requirement. Mutates only the best/order workspace arrays.
    """
    for i in range(n):
        order[i] = i
        best[i] = 0
    for i in range(1, n):
        k = order[i]
        j = i - 1
        while j >= 0:
            a = order[j]
            better = prices[k] < prices[a]
            if prices[k] == prices[a]:
                better = ((supplier_ids[k] == incumbent and supplier_ids[a] != incumbent)
                          or ((supplier_ids[k] == incumbent) == (supplier_ids[a] == incumbent)
                              and supplier_ids[k] < supplier_ids[a]))
            if not better:
                break
            order[j + 1] = a
            j -= 1
        order[j + 1] = k
    inc = -1
    for i in range(n):
        if supplier_ids[i] == incumbent:
            inc = i
    payable = fee if inc >= 0 and bid > 0 and stock[inc] >= bid else 0.
    best_value = 0.
    best_cost = 0.
    best_fee = 0.
    best_family = 0
    best_units = 0
    # Incumbent-only first gives relationship retention in exact-surplus ties.
    for family in range(2):
        units = 0
        benefit = 0.
        cost = 0.
        external = False
        for rank in range(n):
            i = order[rank]
            if family == 0 and i != inc:
                continue
            for _ in range(min(int(stock[i]), value_count - units)):
                cost += prices[i]
                benefit += values[units]
                units += 1
                external = external or supplier_ids[i] != incumbent
                charge = payable if external else 0.
                objective = benefit - cost - charge
                if cost + charge <= cash and objective > best_value:
                    best_family = family
                    best_units = units
                    best_value = objective
                    best_cost = cost
                    best_fee = charge
    remaining = best_units
    for rank in range(n):
        i = order[rank]
        if best_family == 0 and i != inc:
            continue
        take = min(int(stock[i]), remaining)
        best[i] = take
        remaining -= take
        if remaining == 0:
            break
    preference = incumbent
    for rank in range(n):
        i = order[rank]
        if best[i] > 0 and best[i] >= funded_demands[i]:
            preference = supplier_ids[i]
            break
    return best_value, best_cost, best_fee, preference


@njit
def solve_retail(values, prices, stock, supplier_ids, incumbent, bid, fee, cash, funded_demands):
    """Allocating reference interface; hot callers supply reusable workspaces."""
    n = len(prices)
    best = np.zeros(n, dtype=np.int64)
    order = np.empty(n, dtype=np.int64)
    score, goods, charge, preference = solve_retail_into(values, len(values), prices, stock,
        supplier_ids, n, incumbent, bid, fee, cash, funded_demands, best, order)
    return best, score, goods, charge, preference
