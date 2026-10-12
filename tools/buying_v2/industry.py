"""Compiled exhaustive industrial reference, not a population-scale optimizer.

Different iteration and settlement implementation from industry_oracle. This
establishes the full finite action-space contract before optimized pruning.
Explicit work limits reject oversized cases instead of silently approximating.
"""
import math
import numpy as np
from economy.core import model as M
from .jit import njit
from .industry_oracle import validate
from .float_sum import add, finish

_gate = njit(M.production_batches)


@njit
def enumerate_allocations(held, basis, spaces, slots, free_space, cash,
                          material, supplier, price, stock, lot, incumbents, bids, fees,
                          recipe, bound, conversion, quote, overhead, output_qty,
                          output_space, output_values, terminal_values, margin_band, funded_demands, lower, upper):
    n, offers, lines = len(held), len(material), len(bound)
    q = lower.copy()
    limits = upper
    request_order = np.arange(offers)
    for j in range(1, offers):
        selected = request_order[j]
        k = j-1
        while k >= 0:
            old = request_order[k]
            if not (material[selected] < material[old] or (material[selected] == material[old] and
                    (price[selected] < price[old] or (price[selected] == price[old] and supplier[selected] < supplier[old])))):
                break
            request_order[k+1] = old
            k -= 1
        request_order[k+1] = selected
    best = np.zeros(offers, dtype=np.int64)
    best_outputs = np.zeros(lines, dtype=np.int64)
    best_remaining = np.zeros(n, dtype=np.int64)
    best_value = -np.inf
    best_payment = np.inf
    best_units = 0
    best_conversion = 0.
    while True:
        inventory = held.copy()
        purchases = np.zeros(n, dtype=np.int64)
        book = held * basis
        outside = np.zeros(n, dtype=np.bool_)
        goods = 0.
        used = 0.
        units = 0
        for i in range(offers):
            m = material[i]
            inventory[m] += q[i]
            purchases[m] += q[i]
            book[m] += q[i] * price[i]
            goods += q[i] * price[i]
            units += q[i]
            if q[i] > 0 and supplier[i] != incumbents[m]:
                outside[m] = True
        # The independent ledger charges physical room per material total,
        # not per delivery. Preserve that reduction at exact slot boundaries.
        space_correction = 0.
        for m in range(n):
            used, space_correction = add(used, space_correction, purchases[m] * spaces[m])
        used = finish(used, space_correction)
        valid = used <= free_space
        cumulative = np.zeros(n,dtype=np.int64)
        for rank in range(offers):
            i = request_order[rank]
            m = material[i]
            if funded_demands[i] >= 0 and q[i] > max(0,funded_demands[i]-cumulative[m]):
                valid = False
            cumulative[m] += q[i]
        for m in range(n):
            if inventory[m] > slots[m]:
                valid = False
        fee_total = 0.
        fee_correction = 0.
        for m in range(n):
            charge = 0.
            if outside[m] and incumbents[m] >= 0 and bids[m] > 0:
                for i in range(offers):
                    if material[i] == m and supplier[i] == incumbents[m] and stock[i] >= bids[m]:
                        charge = fees[m]
                        break
            fee_total, fee_correction = add(fee_total, fee_correction, charge)
        fee_total = finish(fee_total, fee_correction)
        # Match the ledger's goods + sum(per-material charges). Adding each fee
        # directly to goods can reject an exactly affordable basket by one ulp.
        payment = goods + fee_total
        if payment > cash:
            valid = False
        if valid:
            for m in range(n):
                book[m] = book[m] / inventory[m] if inventory[m] else 0.
            remaining_cash = cash - payment
            output_value = 0.
            paid_conversion = 0.
            outputs = np.zeros(lines, dtype=np.int64)
            for r in range(lines):
                planned = bound[r]
                cost = 0.
                cost_correction = 0.
                for m in range(n):
                    if recipe[r, m]:
                        planned = min(planned, inventory[m] // recipe[r, m])
                    cost, cost_correction = add(cost, cost_correction, recipe[r, m] * book[m])
                cost = finish(cost, cost_correction)
                cost = cost / output_qty[r] + conversion[r]
                planned = min(planned, int(math.floor(remaining_cash / max(1e-9, conversion[r] * output_qty[r]))))
                batches = _gate(planned, output_qty[r], cost, quote[r], overhead[r], margin_band)
                outputs[r] = batches * output_qty[r]
                consumed_space = 0.
                for m in range(n):
                    inventory[m] -= batches * recipe[r, m]
                    consumed_space += batches * recipe[r, m] * spaces[m]
                used += outputs[r] * output_space[r] - consumed_space
                if used > free_space + 1e-9:
                    valid = False
                expense = outputs[r] * conversion[r]
                remaining_cash -= expense
                paid_conversion += expense
                output_value += output_values[r, outputs[r]]
            terminal_value = 0.
            terminal_correction = 0.
            for m in range(n):
                terminal_value, terminal_correction = add(terminal_value, terminal_correction, terminal_values[m, inventory[m]])
            terminal_value = finish(terminal_value, terminal_correction)
            value = output_value + terminal_value - payment - paid_conversion
            # Enumeration is lexicographic; keep its earlier allocation on the
            # final exact tie after payment and total purchased units.
            tolerance = 1e-9 + 1e-12 * max(abs(value), abs(best_value)) if np.isfinite(best_value) else 0.
            cost_tolerance = 1e-9 + 1e-12 * max(abs(payment), abs(best_payment)) if np.isfinite(best_payment) else 0.
            if valid and (value > best_value + tolerance or (abs(value-best_value) <= tolerance and
                          (payment < best_payment-cost_tolerance or (abs(payment-best_payment) <= cost_tolerance and units < best_units)))):
                best[:] = q
                best_outputs[:] = outputs
                best_remaining[:] = inventory
                best_value = value
                best_payment = payment
                best_units = units
                best_conversion = paid_conversion
        position = offers - 1
        while position >= 0:
            q[position] += lot[position]
            if q[position] <= limits[position]:
                break
            q[position] = lower[position]
            position -= 1
        if position < 0:
            break
    return best, best_outputs, best_remaining, best_value, best_payment, best_conversion


def pack(p):
    """Pack a validated problem once; also used by the independent bound search."""
    validate(p)
    n = len(p.held)
    iv = lambda values: np.array(values, dtype=np.int64)
    fv = lambda values: np.array(values, dtype=np.float64)
    value_width = max((len(x.output_values) for x in p.lines), default=1)
    output_values = np.zeros((len(p.lines), value_width))
    for r, line in enumerate(p.lines):
        output_values[r, :len(line.output_values)] = line.output_values
    terminal = np.zeros((n, max((len(x) for x in p.terminal_values), default=1)))
    for m, values in enumerate(p.terminal_values):
        terminal[m, :len(values)] = values
    return (iv(p.held), fv(p.basis), fv(p.spaces), iv(p.slots), p.free_space, p.cash,
        iv([o.material for o in p.offers]), iv([o.supplier for o in p.offers]), fv([o.price for o in p.offers]),
        iv([o.stock for o in p.offers]), iv([o.lot for o in p.offers]), iv(p.incumbents), iv(p.bids), fv(p.fees),
        iv([x.recipe for x in p.lines]).reshape((len(p.lines), n)), iv([x.max_batches for x in p.lines]),
        fv([x.conversion for x in p.lines]), fv([x.quote for x in p.lines]), fv([x.overhead for x in p.lines]),
        iv([x.output_qty for x in p.lines]), fv([x.output_space for x in p.lines]), output_values, terminal, p.margin_band, iv(p.funded_demands if p.funded_demands is not None else [-1]*len(p.offers)))


def solve(p, max_allocations=1_000_000):
    args = pack(p)
    limits = np.array([min(o.stock, p.slots[o.material] - p.held[o.material]) // o.lot * o.lot for o in p.offers], dtype=np.int64)
    count = math.prod(int(limit) // o.lot + 1 for limit, o in zip(limits, p.offers))
    if count > max_allocations:
        raise ValueError(f'compiled reference needs {count} allocations; scalable optimizer required')
    return enumerate_allocations(*args, np.zeros(len(p.offers), dtype=np.int64), limits)
