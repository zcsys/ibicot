"""Compiled exact box search with explicit incomplete-search reporting."""
import math
import numpy as np
from .jit import njit
from .industry import pack, enumerate_allocations
from .industry_bounds import SearchLimit
from .industry_relaxation import certified_candidate


@njit
def anchored_value(values, y, output_qty, conversion, recipe, minimum, cheapest):
    needed = 0.
    for m in range(len(minimum)):
        missing = max(0, recipe[m] * y - minimum[m])
        if missing:
            needed += missing * cheapest[m]
    return values[y * output_qty] - needed - y * output_qty * conversion


@njit
def upper_bound(args, lo, hi, output_prefix, terminal_prefix, concave):
    held, basis, spaces, slots, room, cash, material, supplier, price, stock, lot, incumbents, bids, fees, recipe, bounds, conversion, quote, overhead, output_qty, output_space, output_values, terminal_values, band, funded_demands = args
    n = len(held)
    minimum = held.copy()
    maximum = held.copy()
    outside = np.zeros(n, dtype=np.bool_)
    goods = 0.
    used = 0.
    for i in range(len(lo)):
        m = material[i]
        minimum[m] += lo[i]
        maximum[m] += hi[i]
        goods += lo[i] * price[i]
        if lo[i] > 0 and supplier[i] != incumbents[m]:
            outside[m] = True
    fee_total = 0.
    for m in range(n):
        used += (minimum[m] - held[m]) * spaces[m]
        if outside[m] and incumbents[m] >= 0 and bids[m] > 0:
            for i in range(len(lo)):
                if material[i] == m and supplier[i] == incumbents[m] and stock[i] >= bids[m]:
                    fee_total += fees[m]
                    break
    payment = goods + fee_total
    # 128 eps is conservative relative to the corresponding short reductions.
    eps = 128 * np.finfo(np.float64).eps * max(1., abs(goods), abs(used), abs(cash), abs(room))
    if payment > cash + eps or used > room + eps:
        return -np.inf
    for m in range(n):
        if minimum[m] > slots[m]:
            return -np.inf
        maximum[m] = min(maximum[m], slots[m])
    maxima = np.empty(len(bounds))
    all_output = 0.
    for r in range(len(bounds)):
        batches = bounds[r]
        for m in range(n):
            if recipe[r, m]:
                batches = min(batches, maximum[m] // recipe[r, m])
        best = output_prefix[r, batches * output_qty[r]]
        maxima[r] = best
        all_output += best
    terminal_max = 0.
    for m in range(n):
        terminal_max += terminal_prefix[m, maximum[m]]
    optimistic = all_output + terminal_max
    # Each actual line output requires at least its own missing inputs. Allow
    # every missing unit the cheapest remaining quote, ignoring lots and stock
    # competition. This lower-bounds extra cost WITHOUT assuming that cheapest
    # actual procurement dominates cost-basis-sensitive alternatives.
    cheapest = np.full(n, np.inf)
    for i in range(len(lo)):
        if hi[i] > lo[i]:
            cheapest[material[i]] = min(cheapest[material[i]], price[i])
    for r in range(len(bounds)):
        batches = bounds[r]
        for m in range(n):
            if recipe[r, m]:
                batches = min(batches, maximum[m] // recipe[r, m])
        anchored = -np.inf
        if concave[r]:
            left, right = 0, batches
            while left < right:
                middle = (left + right) // 2
                v0 = anchored_value(output_values[r], middle, output_qty[r], conversion[r], recipe[r], minimum, cheapest)
                v1 = anchored_value(output_values[r], middle + 1, output_qty[r], conversion[r], recipe[r], minimum, cheapest)
                if v1 > v0:
                    left = middle + 1
                else:
                    right = middle
            anchored = anchored_value(output_values[r], left, output_qty[r], conversion[r], recipe[r], minimum, cheapest)
        else:
            for y in range(batches + 1):
                anchored = max(anchored, anchored_value(output_values[r], y, output_qty[r], conversion[r], recipe[r], minimum, cheapest))
        optimistic = min(optimistic, all_output - maxima[r] + anchored + terminal_max)
    return optimistic - payment + 256 * np.finfo(np.float64).eps * max(1., abs(all_output), abs(terminal_max), abs(payment))


@njit
def search(args, upper, stack_size, max_nodes, output_prefix, terminal_prefix, concave):
    n = len(upper)
    lot = args[10]
    zeros = np.zeros(n, dtype=np.int64)
    best = enumerate_allocations(*args, zeros, zeros)
    lows = np.zeros((stack_size, n), dtype=np.int64)
    highs = np.zeros((stack_size, n), dtype=np.int64)
    scores = np.empty(stack_size)
    highs[0] = upper
    scores[0] = upper_bound(args, zeros, upper, output_prefix, terminal_prefix, concave)
    pending = 1
    nodes = leaves = pruned = 0
    while pending:
        if nodes >= max_nodes:
            return best, nodes, leaves, pruned, False
        pending -= 1
        lo = lows[pending].copy()
        hi = highs[pending].copy()
        optimistic = scores[pending]
        nodes += 1
        if optimistic < best[3] - (1e-9 + 1e-12*max(abs(optimistic), abs(best[3]))):
            pruned += 1
            continue
        axis = -1
        width = 0
        for i in range(n):
            candidate = (hi[i] - lo[i]) // lot[i]
            if candidate > width:
                axis, width = i, candidate
        if axis < 0:
            result = enumerate_allocations(*args, lo, hi)
            leaves += 1
            better_tie = False
            cost_tol = 1e-9+1e-12*max(abs(result[4]),abs(best[4]))
            if result[4] < best[4]-cost_tol:
                better_tie = True
            elif abs(result[4]-best[4]) <= cost_tol:
                total = result[0].sum()
                old_total = best[0].sum()
                if total < old_total:
                    better_tie = True
                elif total == old_total:
                    for i in range(n):
                        if result[0][i] != best[0][i]:
                            better_tie = result[0][i] < best[0][i]
                            break
            tol = 1e-9+1e-12*max(abs(result[3]),abs(best[3])) if np.isfinite(best[3]) else 0.
            if result[3] > best[3]+tol or (abs(result[3]-best[3]) <= tol and better_tie):
                best = result
            continue
        middle = lo[axis] + (width // 2) * lot[axis]
        low_hi = hi.copy()
        high_lo = lo.copy()
        low_hi[axis] = middle
        high_lo[axis] = middle + lot[axis]
        low_score = upper_bound(args, lo, low_hi, output_prefix, terminal_prefix, concave)
        high_score = upper_bound(args, high_lo, hi, output_prefix, terminal_prefix, concave)
        # Push lower bound first so the more promising box is popped next.
        for step in range(2):
            take_low = (step == 0) == (low_score <= high_score)
            score = low_score if take_low else high_score
            if score == -np.inf or score < best[3] - (1e-9+1e-12*max(abs(score),abs(best[3]))):
                pruned += 1
                continue
            lows[pending] = lo if take_low else high_lo
            highs[pending] = low_hi if take_low else hi
            scores[pending] = score
            pending += 1
    return best, nodes, leaves, pruned, True


def solve(p, max_nodes=100_000):
    if max_nodes <= 0:
        raise SearchLimit('compiled industrial search has no work budget')
    args = pack(p)
    upper = np.array([min(o.stock, p.slots[o.material] - p.held[o.material]) // o.lot * o.lot for o in p.offers], dtype=np.int64)
    relaxed, certified = certified_candidate(args)
    if certified:
        return relaxed, dict(nodes=0, leaves=1, pruned=0,
            exhaustiveAllocations=math.prod(int(x) // o.lot + 1 for x, o in zip(upper, p.offers)),
            certificate='single-line fee-free zero-terminal relaxation verified by actual production')
    depth = sum((int(x) // o.lot + 1).bit_length() for x, o in zip(upper, p.offers)) + 2
    output_prefix = np.maximum.accumulate(args[21], axis=1)
    terminal_prefix = np.maximum.accumulate(args[22], axis=1)
    concave = np.array([bool(np.all(np.diff(np.asarray(line.output_values)[::line.output_qty], n=2) <= 0)) for line in p.lines])
    result, nodes, leaves, pruned, complete = search(args, upper, depth, max_nodes, output_prefix, terminal_prefix, concave)
    if not complete:
        raise SearchLimit(f'compiled industrial search exhausted {nodes} nodes; no optimum returned')
    return result, dict(nodes=nodes, leaves=leaves, pruned=pruned,
                        exhaustiveAllocations=math.prod(int(x) // o.lot + 1 for x, o in zip(upper, p.offers)),
                        certificate='exact compiled search exhausted all unpruned boxes')
