"""Exact fixed-target procurement with explicit total storage constraints.

Objective: most purchased input units, then least goods-plus-fee payment. Targets
remain the existing storage deficits; this is NOT derived industrial demand.
Uniform lot sizes are the current within-tier contract. Binding total space
uses a general exact reference search instead of a quantity-greedy shortcut.
"""
import numpy as np
from .jit import njit


@njit
def solve_uniform(targets, material, supplier, prices, stocks, incumbents,
                  bids, fees, cash, lot, funded_demands):
    n, count = len(targets), len(prices)
    payable = np.zeros(n)
    bit = np.full(n, -1, dtype=np.int64)
    bits = 0
    for m in range(n):
        for i in range(count):
            if material[i] == m and supplier[i] == incumbents[m] and bids[m] > 0 and stocks[i] >= bids[m]:
                payable[m] = fees[m]
        if payable[m] > 0:
            bit[m] = bits
            bits += 1
    order = np.arange(count)
    for j in range(1,count):
        i = order[j]
        k = j-1
        while k >= 0 and (prices[i] < prices[order[k]] or (prices[i] == prices[order[k]] and i > order[k])):
            order[k+1] = order[k]
            k -= 1
        order[k+1] = i
    best = np.zeros(count,dtype=np.int64)
    best_units = 0
    best_payment = 0.
    best_fees = np.zeros(n)
    for mask in range(1 << bits):
        reserved = 0.
        for m in range(n):
            if bit[m] >= 0 and mask & (1 << bit[m]):
                reserved += payable[m]
        if reserved > cash:
            continue
        remaining = targets.copy()
        allocation = np.zeros(count,dtype=np.int64)
        outside = np.zeros(n,dtype=np.bool_)
        budget = cash-reserved
        goods = 0.
        units = 0
        for rank in range(count):
            i = order[rank]
            m = material[i]
            if supplier[i] != incumbents[m] and bit[m] >= 0 and not(mask & (1 << bit[m])):
                continue
            limit = remaining[m]
            if funded_demands[i] >= 0:
                limit = min(limit,max(0,funded_demands[i]-(targets[m]-remaining[m])))
            quantity = min(limit, stocks[i])//lot*lot
            quantity = min(quantity, int(np.floor(max(0.,budget)/prices[i]/lot))*lot)
            allocation[i] = quantity
            remaining[m] -= quantity
            cost = quantity*prices[i]
            budget -= cost
            goods += cost
            units += quantity
            outside[m] |= quantity > 0 and supplier[i] != incumbents[m]
        valid = True
        charges = np.zeros(n)
        for m in range(n):
            if bit[m] >= 0 and mask & (1 << bit[m]):
                if not outside[m]:
                    valid = False
                charges[m] = payable[m]
        if not valid:
            continue
        payment = goods+reserved
        tolerance = 1e-9+1e-12*max(abs(payment),abs(best_payment))
        lex = False
        for i in range(count):
            if allocation[i] != best[i]:
                lex = allocation[i] < best[i]
                break
        if units > best_units or (units == best_units and
           (payment < best_payment-tolerance or (abs(payment-best_payment) <= tolerance and lex))):
            best[:] = allocation
            best_units, best_payment = units, payment
            best_fees[:] = charges
    return best, best_units, best_payment, best_fees


def solve(targets, offers, incumbents, bids, fees, cash, spaces, free_space, lot=1, max_nodes=100000, funded_demands=None):
    n = len(targets)
    if len(spaces)!=n or len(incumbents)!=n or len(bids)!=n or len(fees)!=n:
        raise ValueError('replenishment dimensions differ')
    if free_space < 0 or not np.isfinite(free_space) or any(x<0 or not np.isfinite(x) for x in fees) or any(x<0 or x!=int(x) for x in bids):
        raise ValueError('invalid storage, fees or bids')
    if funded_demands is not None and (len(funded_demands)!=len(offers) or any(q<0 or not np.isfinite(q) or q!=int(q) for q in funded_demands)):
        raise ValueError('invalid quote demands')
    if lot < 1 or lot != int(lot) or cash < 0 or not np.isfinite(cash):
        raise ValueError('invalid lot or cash')
    if any(q<0 or not np.isfinite(q) or q!=int(q) for q in targets):
        raise ValueError('invalid targets')
    if any(s<=0 or not np.isfinite(s) for s in spaces):
        raise ValueError('invalid input spaces')
    targets = np.array([int(q)//lot*lot for q in targets],dtype=np.int64)
    if n > 12:
        raise ValueError('more than twelve input fee groups requires separate scaling validation')
    if any(o.lot!=lot or any(not np.isfinite(x) or x!=int(x) for x in (o.stock,o.material,o.supplier))
           or o.stock<0 or o.supplier<0 or o.price<=0 or not np.isfinite(o.price) or not 0<=o.material<n for o in offers):
        raise ValueError('invalid offer or mixed lots')
    if len({(o.material,o.supplier) for o in offers})!=len(offers):
        raise ValueError('duplicate offer stock')
    # Reverse-index ties minimize the allocation vector only when same-price
    # sellers face the same funded demand. Otherwise actual supplier-ID order
    # matters for feasibility; use exhaustive bounded search for that case.
    quote_caps = {}
    heterogeneous_ties = False
    if funded_demands is not None:
        for o,q in zip(offers,funded_demands):
            key=(o.material,o.price)
            if key in quote_caps and quote_caps[key]!=q:
                heterogeneous_ties=True
            quote_caps[key]=q
    if float(np.dot(targets,spaces)) > free_space or heterogeneous_ties:
        from .replenishment_space import solve as constrained
        return constrained(tuple(targets),offers,incumbents,bids,fees,cash,spaces,free_space,lot,max_nodes,funded_demands)
    return solve_uniform(targets,np.array([o.material for o in offers],dtype=np.int64),
        np.array([o.supplier for o in offers],dtype=np.int64),np.array([o.price for o in offers]),
        np.array([o.stock for o in offers],dtype=np.int64),np.array(incumbents,dtype=np.int64),
        np.array(bids,dtype=np.int64),np.array(fees,dtype=float),float(cash),int(lot),np.array(funded_demands if funded_demands is not None else [-1]*len(offers),dtype=np.int64))
