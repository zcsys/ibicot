"""Supplier ranking shared by the Python reference and the compiled kernel."""
import math


def select_offer(offers, stock, prices, preferred, reliability, request,
                 unit_cost, multiple, minimum=1):
    """Rank an order by its payable total, preferring suppliers able to fill it.

    Offers must be sorted by quote. All challengers owe the same fixed charge,
    waived when the incumbent cannot fill the requested order. A zero request
    is a price-only planning lookup; settlement must use the actual request.
    """
    quantity = max(minimum, request)
    best = -1
    partial = -1
    for offer in offers:
        if not math.isfinite(prices[offer]):
            continue
        if partial < 0 and stock[offer] >= minimum:
            partial = offer
        if stock[offer] >= quantity:
            best = offer
            break
    if best < 0:
        best = partial
    if best < 0:
        return offers[0] if len(offers) else -1
    if preferred < 0 or not math.isfinite(prices[preferred]):
        return best
    if stock[preferred] < quantity:
        return best
    charge = 0.0
    if request > 0:
        charge = multiple * unit_cost * (1 + min(1.0, max(0.0, reliability[preferred])))
    if prices[preferred] * quantity <= prices[best] * quantity + charge:
        return preferred
    return best


def affordable_order(supplier, preferred, request, cash, stock, prices,
                     reliability, unit_cost, multiple, lot=1, price_reference=0.0, elasticity=2.0, rounding=0.5):
    """Return seller, funded units, delivered units, and the payable fixed fee.

    Recheck the cost comparison on the actual fill: a cash/stock cap must not
    make a nominally cheaper challenger more expensive than the incumbent.
    With a positive price reference, reduce continuous feasibility by eta
    before stochastic lot rounding. Reuse the same draw for an incumbent recheck.
    """
    charge = 0.0
    if supplier != preferred and preferred >= 0 and stock[preferred] >= request:
        charge = multiple * unit_cost * (1 + min(1.0, max(0.0, reliability[preferred])))
    if price_reference > 0.0:
        # Economic feasibility first; price reduction once; legal rounding last.
        feasible = max(0.0, min(request, stock[supplier], max(0.0, cash - charge) / prices[supplier]))
        reduced = feasible / (1.0 + (prices[supplier] / price_reference) ** elasticity)
        lots = reduced / lot
        whole = math.floor(lots)
        quantity = min(whole + (rounding < lots - whole), math.floor(feasible / lot)) * lot
        if charge > 0 and quantity * (prices[preferred] - prices[supplier]) <= charge:
            supplier = preferred
            charge = 0.0
            feasible = max(0.0, min(request, stock[supplier], max(0.0, cash) / prices[supplier]))
            reduced = feasible / (1.0 + (prices[supplier] / price_reference) ** elasticity)
            lots = reduced / lot
            whole = math.floor(lots)
            quantity = min(whole + (rounding < lots - whole), math.floor(feasible / lot)) * lot
        # A stock-limited feasible plan cannot claim unplaced demand as orders.
        return supplier, quantity, quantity, charge if quantity > 0 else 0.0
    funded = math.floor(min(request, max(0.0, cash - charge) / prices[supplier]) / lot) * lot
    quantity = math.floor(min(funded, stock[supplier]) / lot) * lot
    if charge > 0 and quantity * (prices[preferred] - prices[supplier]) <= charge:
        supplier = preferred
        charge = 0.0
        funded = math.floor(min(request, max(0.0, cash) / prices[supplier]) / lot) * lot
        quantity = math.floor(min(funded, stock[supplier]) / lot) * lot
    return supplier, funded, quantity, charge if quantity > 0 else 0.0
