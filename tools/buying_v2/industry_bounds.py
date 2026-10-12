"""Exact branch-and-bound prototype for the full industrial allocation space.

No cost-basis dominance or minimal-kit restriction. Bounds relax competition
between lines, production gates and conversion expenditure, so they can only
OVERestimate attainable value. Still a Python prototype, not a hot-path policy.
"""
import heapq
import math
import numpy as np
from .industry import pack, enumerate_allocations


class SearchLimit(RuntimeError):
    """No optimality certificate was obtained; never return an approximate policy."""


def solve(p, max_nodes=100_000):
    args = pack(p)
    n = len(p.held)
    count = len(p.offers)
    lots = np.array([o.lot for o in p.offers], dtype=np.int64)
    lower = np.zeros(count, dtype=np.int64)
    upper = np.array([min(o.stock, p.slots[o.material] - p.held[o.material]) // o.lot * o.lot for o in p.offers], dtype=np.int64)
    forced_fee = []
    for m in range(n):
        inc_stock = next((o.stock for o in p.offers if o.material == m and o.supplier == p.incumbents[m]), 0)
        forced_fee.append(p.fees[m] if p.incumbents[m] >= 0 and p.bids[m] > 0 and inc_stock >= p.bids[m] else 0.)

    def bound(lo, hi):
        minimum = list(p.held)
        maximum = list(p.held)
        goods = 0.
        space = 0.
        outside = [False] * n
        for i, o in enumerate(p.offers):
            minimum[o.material] += int(lo[i])
            maximum[o.material] += int(hi[i])
            goods += lo[i] * o.price
            outside[o.material] |= lo[i] > 0 and o.supplier != p.incumbents[o.material]
        space = sum((minimum[m] - p.held[m]) * p.spaces[m] for m in range(n))
        # Outward allowance protects pruning at floating-point boundaries.
        scale = max(1., abs(goods), abs(space), abs(p.cash), abs(p.free_space))
        epsilon = 64 * math.ulp(scale)
        payment = goods + sum(forced_fee[m] for m in range(n) if outside[m])
        if payment > p.cash + epsilon or space > p.free_space + epsilon or any(minimum[m] > p.slots[m] for m in range(n)):
            return -math.inf
        maximum = [min(maximum[m], p.slots[m]) for m in range(n)]
        optimistic = 0.
        for line in p.lines:
            batches = min([line.max_batches] + [maximum[m] // q for m, q in enumerate(line.recipe) if q])
            optimistic += max(line.output_values[q * line.output_qty] for q in range(batches + 1))
        # All inputs can hypothetically remain AND all output can be made. This
        # intentional double counting is solely an upper bound, never earnings.
        for m in range(n):
            optimistic += max(p.terminal_values[m][:maximum[m] + 1])
        raw = optimistic - payment
        return raw + 64 * math.ulp(max(1., abs(optimistic), abs(payment)))

    best = enumerate_allocations(*args, lower, lower)
    def key(result):
        return (result[4], int(result[0].sum()), tuple(result[0]))
    queue = []
    serial = 0
    initial = bound(lower, upper)
    heapq.heappush(queue, (-initial, serial, lower, upper))
    visited = evaluated = pruned = 0
    while queue:
        if visited >= max_nodes:
            raise SearchLimit(f'industrial search exceeded {max_nodes} nodes; no exact result returned')
        negative, _, lo, hi = heapq.heappop(queue)
        visited += 1
        if -negative < best[3] - (1e-9+1e-12*max(abs(negative),abs(best[3]))):
            pruned += 1
            continue
        widths = (hi - lo) // lots
        if len(widths) == 0 or widths.max() == 0:
            result = enumerate_allocations(*args, lo, hi)
            evaluated += 1
            tol = 1e-9+1e-12*max(abs(result[3]),abs(best[3])) if math.isfinite(best[3]) else 0.
            ct = 1e-9+1e-12*max(abs(result[4]),abs(best[4])) if math.isfinite(best[4]) else 0.
            cheaper = result[4] < best[4]-ct or (abs(result[4]-best[4]) <= ct and key(result)[1:] < key(best)[1:])
            if result[3] > best[3]+tol or (abs(result[3]-best[3]) <= tol and cheaper):
                best = result
            continue
        axis = int(np.argmax(widths))
        middle = lo[axis] + (widths[axis] // 2) * lots[axis]
        low_hi, high_lo = hi.copy(), lo.copy()
        low_hi[axis] = middle
        high_lo[axis] = middle + lots[axis]
        for child_lo, child_hi in ((lo, low_hi), (high_lo, hi)):
            optimistic = bound(child_lo, child_hi)
            if optimistic == -math.inf or optimistic < best[3] - (1e-9+1e-12*max(abs(optimistic),abs(best[3]))):
                pruned += 1
                continue
            serial += 1
            heapq.heappush(queue, (-optimistic, serial, child_lo, child_hi))
    return best, dict(nodes=visited, leaves=evaluated, pruned=pruned,
                      exhaustiveAllocations=math.prod(int(x) // o.lot + 1 for x, o in zip(upper, p.offers)),
                      certificate='exact search exhausted all unpruned boxes')
