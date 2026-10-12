"""Independent exhaustive industrial oracle, intentionally limited to small cases.

Enumerates EVERY offer allocation, including industrial splits and unmatched
buffers. Production is simulated in the declared actual line order; output is
not an independently selectable vector that the real production gate can veto.
No R1 solver or production-gate implementation is imported.
"""
from dataclasses import dataclass
from itertools import product
import math


@dataclass(frozen=True)
class Offer:
    material: int
    supplier: int
    price: float
    stock: int
    lot: int = 1


@dataclass(frozen=True)
class Line:
    recipe: tuple[int, ...]
    max_batches: int
    conversion: float
    quote: float
    overhead: float
    output_values: tuple[float, ...]
    output_space: float
    output_qty: int = 1


@dataclass(frozen=True)
class Problem:
    held: tuple[int, ...]
    basis: tuple[float, ...]
    spaces: tuple[float, ...]
    slots: tuple[int, ...]
    free_space: float
    cash: float
    offers: tuple[Offer, ...]
    incumbents: tuple[int, ...]
    bids: tuple[int, ...]
    fees: tuple[float, ...]
    lines: tuple[Line, ...]
    # Total terminal input values at each remaining quantity; these are explicit
    # scenario assumptions, NOT adopted production willingness-to-pay defaults.
    terminal_values: tuple[tuple[float, ...], ...]
    margin_band: float = .05
    funded_demands: tuple[int, ...] | None = None


def validate(p):
    n = len(p.held)
    def integer(x):
        return math.isfinite(x) and x == int(x)
    numeric = (p.free_space, p.cash, p.margin_band, *p.basis, *p.spaces, *p.fees)
    if not n or not all(math.isfinite(x) for x in numeric):
        raise ValueError('nonfinite or empty company state')
    if not all(integer(x) for x in (*p.held, *p.slots, *p.bids, *p.incumbents)):
        raise ValueError('inventory quantities and identities must be integral')
    if any(len(x) != n for x in (p.basis, p.spaces, p.slots, p.incumbents, p.bids, p.fees, p.terminal_values)):
        raise ValueError('material dimensions differ')
    if p.cash < 0 or p.free_space < 0 or p.margin_band <= 0:
        raise ValueError('invalid company resources or margin band')
    for m in range(n):
        if not 0 <= p.held[m] <= p.slots[m] or p.basis[m] < 0 or p.spaces[m] <= 0:
            raise ValueError('invalid inventory')
        if not all(math.isfinite(v) for v in p.terminal_values[m]):
            raise ValueError('nonfinite terminal values')
        if len(p.terminal_values[m]) <= p.slots[m] or p.bids[m] < 0 or p.fees[m] < 0:
            raise ValueError('invalid terminal values or fee data')
    if p.funded_demands is not None and (len(p.funded_demands) != len(p.offers) or any(not integer(x) or x < 0 for x in p.funded_demands)):
        raise ValueError('invalid funded-demand vector')
    seen = set()
    for o in p.offers:
        if not all(integer(x) for x in (o.material, o.supplier, o.stock, o.lot)):
            raise ValueError('offer quantities and identities must be integral')
        if not 0 <= o.material < n or o.supplier < 0 or o.stock < 0 or o.price <= 0 or not math.isfinite(o.price) or o.lot < 1:
            raise ValueError('invalid offer')
        key = (o.material, o.supplier)
        if key in seen:
            raise ValueError('duplicate supplier stock for one input')
        seen.add(key)
    for line in p.lines:
        if not all(integer(x) for x in (*line.recipe, line.max_batches, line.output_qty)):
            raise ValueError('recipe quantities must be integral')
        if not all(math.isfinite(x) for x in (line.conversion, line.quote, line.overhead, line.output_space, *line.output_values)) or line.output_space < 0:
            raise ValueError('nonfinite or invalid line values')
        if len(line.recipe) != n or min(line.recipe) < 0 or not any(line.recipe):
            raise ValueError('invalid recipe')
        if line.max_batches < 0 or line.conversion < 0 or line.quote <= 0 or line.output_qty < 1:
            raise ValueError('invalid line')
        if len(line.output_values) <= line.max_batches * line.output_qty:
            raise ValueError('missing output values')


def evaluate(p, allocation, *, terminal_lookup=None, native_resources=False):
    """Simulate deterministic procurement/production for one complete allocation."""
    if len(allocation) != len(p.offers):
        raise ValueError('allocation length differs from offers')
    n = len(p.held)
    if p.funded_demands is not None:
        cumulative = [0]*n
        for i in sorted(range(len(p.offers)), key=lambda i:(p.offers[i].material,p.offers[i].price,p.offers[i].supplier)):
            m = p.offers[i].material
            if allocation[i] > max(0,p.funded_demands[i]-cumulative[m]):
                return None
            cumulative[m] += allocation[i]
    inventory = list(p.held)
    values = [h * b for h, b in zip(p.held, p.basis)]
    purchases = [0] * n
    goods = 0.
    outside = [False] * n
    for o, q in zip(p.offers, allocation):
        if q < 0 or q > o.stock or q % o.lot:
            return None
        purchases[o.material] += q
        goods += q * o.price
        inventory[o.material] += q
        values[o.material] += q * o.price
        outside[o.material] |= q > 0 and o.supplier != p.incumbents[o.material]
    if any(inventory[m] > p.slots[m] for m in range(n)):
        return None
    used_space = sum(q * s for q, s in zip(purchases, p.spaces))
    if used_space > p.free_space:
        return None
    charges = []
    for m in range(n):
        inc_stock = next((o.stock for o in p.offers if o.material == m and o.supplier == p.incumbents[m]), 0)
        charges.append(p.fees[m] if outside[m] and p.incumbents[m] >= 0 and p.bids[m] > 0 and inc_stock >= p.bids[m] else 0.)
    payment = goods + sum(charges)
    if payment > p.cash:
        return None
    cash = p.cash - payment
    basis = [p.basis[m] if native_resources and purchases[m]==0 else (v/q if q else 0.)
             for m,(v,q) in enumerate(zip(values,inventory))]
    produced = []
    conversion_paid = 0.
    output_value = 0.
    for line in p.lines:
        possible = min([line.max_batches] + [(math.floor(inventory[m]/q) if isinstance(inventory[m],float) else inventory[m]//q) for m, q in enumerate(line.recipe) if q])
        possible = min(possible, math.floor(cash / max(1e-9, line.conversion * line.output_qty)))
        unit_cost = sum(q * basis[m] for m, q in enumerate(line.recipe)) / line.output_qty + line.conversion
        # Independent statement of the retained ramp and reduced-batch check.
        batches = 0
        if possible > 0 and unit_cost <= line.quote + 1e-9:
            surplus = line.quote - unit_cost - line.overhead / (possible * line.output_qty)
            ratio = min(1., max(0., (surplus / max(line.quote, 1e-9)) / p.margin_band))
            candidate = math.floor(possible * ratio + .5)
            if candidate > 0 and (line.quote - unit_cost) * candidate * line.output_qty - line.overhead >= -1e-9:
                batches = candidate
        units = batches * line.output_qty
        consumed_space = 0.
        for m, q in enumerate(line.recipe):
            inventory[m] -= q * batches
            consumed_space += q * batches * p.spaces[m]
        used_space += units * line.output_space - consumed_space
        if used_space > p.free_space + 1e-9:
            return None
        expense = units * line.conversion
        cash -= expense
        conversion_paid += expense
        output_value += line.output_values[units]
        produced.append(units)
    terminal = sum((p.terminal_values[m][inventory[m]] if terminal_lookup is None
                    else terminal_lookup(p.terminal_values[m],inventory[m])) for m in range(n))
    return dict(allocation=tuple(allocation), quantities=tuple(purchases), outputs=tuple(produced),
                remaining=tuple(inventory), basis=tuple(basis), goods=goods, fees=tuple(charges),
                conversion=conversion_paid, cash=cash,
                value=output_value + terminal - payment - conversion_paid)


def solve(p, max_allocations=1_000_000):
    validate(p)
    ranges = [range(0, min(o.stock, p.slots[o.material] - p.held[o.material]) + 1, o.lot) for o in p.offers]
    count = math.prod(len(x) for x in ranges)
    if count > max_allocations:
        raise ValueError(f'exhaustive oracle needs {count} allocations; use a small fixture')
    best = None
    for allocation in product(*ranges):
        result = evaluate(p, allocation)
        if result is None:
            continue
        payment = result['goods'] + sum(result['fees'])
        key = (sum(allocation), allocation)
        better = best is None
        if best is not None:
            tol = 1e-9 + 1e-12 * max(abs(result['value']), abs(best['value']))
            old_payment = best['goods'] + sum(best['fees'])
            cost_tol = 1e-9 + 1e-12 * max(abs(payment), abs(old_payment))
            better = result['value'] > best['value'] + tol or (
                abs(result['value'] - best['value']) <= tol and (
                    payment < old_payment - cost_tol or
                    (abs(payment - old_payment) <= cost_tol and key < best_key)))
        if better:
            best, best_key = result, key
    if best is None:
        raise ValueError('no feasible allocation, including no purchase')
    best['enumeratedAllocations'] = count
    return best
