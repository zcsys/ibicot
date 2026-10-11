"""Slow independent purchase-allocation enumeration. No optimized solver imports.

This is deliberately quantity-first rather than output-plan-first. Use only small
markets. It enumerates every stock/cash-feasible purchase and every producible
route vector, then enforces the contract's minimal complete-kit action space.
"""
import itertools
import math


def retail_oracle(values, prices, stock, preferred, bid, fixed_fee, cash):
    best=None
    ranges=[range(min(int(s),len(values))+1) for s in stock]
    for allocation in itertools.product(*ranges):
        q=sum(allocation)
        if q>len(values):continue
        goods=sum(p*x for p,x in zip(prices,allocation))
        outside=any(x>0 and i!=preferred for i,x in enumerate(allocation))
        fee=fixed_fee if outside and preferred>=0 and bid>0 and stock[preferred]>=bid else 0.
        cost=goods+fee
        if cost>cash:continue
        score=sum(values[:q])-cost
        key=(cost,-allocation[preferred] if preferred>=0 else 0,tuple(-x for x in allocation))
        if best is None or score>best[0]+1e-9+1e-12*max(abs(score),abs(best[0])) or (
            abs(score-best[0])<=1e-9+1e-12*max(abs(score),abs(best[0])) and key<best[1]):
            pref=preferred
            sellers=[i for i,x in enumerate(allocation) if x>0]
            if bid>0 and len(sellers)==1 and allocation[sellers[0]]>=bid:pref=sellers[0]
            best=(score,key,allocation,goods,fee,pref)
    return best[2],best[0],best[3],best[4],best[5]


def industry_oracle(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
                    bound,finished,output_price,mean,conversion,cash,reserve_per_output):
    best=None
    ranges=[range(max(0,int((slot-old)//lot))+1) for old,slot,lot in zip(held,slots,lots)]
    for order_lots in itertools.product(*ranges):
        quantities=tuple(int(lot*k) for lot,k in zip(lots,order_lots))
        if sum(q*s for q,s in zip(quantities,spaces))>room:continue
        options=[[s for s in range(counts[m]) if stocks[m,s]>=q] if q else [-1]
                 for m,q in enumerate(quantities)]
        for sellers in itertools.product(*options):
            charges=tuple(fees[m] if quantities[m]>0 and sellers[m]!=prefs[m] and prefs[m]>=0
                and bids[m]>0 and stocks[m,prefs[m]]>=bids[m] else 0. for m in range(len(held)))
            cost=sum(quantities[m]*prices[m,s]+charges[m] for m,s in enumerate(sellers) if s>=0)
            for y in range(bound+1):
                expected=tuple(int(lots[m]*math.ceil(max(0.,ratios[m]*y-held[m])/lots[m])) for m in range(len(held)))
                if expected!=quantities or cost+reserve_per_output*y>cash:continue
                gross=output_price*mean*(math.exp(-finished/mean)-math.exp(-(finished+y)/mean)) if mean>0 else 0.
                score=gross-conversion*y-cost
                supplier_key=tuple((0 if s==prefs[m] else 1,s) for m,s in enumerate(sellers))
                key=(cost,y,supplier_key)
                if best is None or score>best[0]+1e-9+1e-12*max(abs(score),abs(best[0])) or (
                    abs(score-best[0])<=1e-9+1e-12*max(abs(score),abs(best[0])) and key<best[1]):
                    best=(score,key,sellers,quantities,charges,y,cost)
    return best[2],best[3],best[4],best[5],best[0],best[6]


def multi_route_oracle(held, recipe, bounds, route_values, offers, lots, spaces, slots, room, cash, reserve):
    """Exact small multi-route model, shared ingredients/cash, fixed payable fees.

    offers[m] lists (price, stock, fee, stable_id). Fees are already frozen by the
    protocol. route_values[r][y] is the declared route return; no input cost basis
    is subtracted. Returns objective, outputs, suppliers, quantities, total cost.
    """
    best=(0.,tuple(0 for _ in bounds),tuple(-1 for _ in held),tuple(0 for _ in held),0.)
    for ys in itertools.product(*(range(b+1) for b in bounds)):
        required=[sum(recipe[r][m]*ys[r] for r in range(len(bounds))) for m in range(len(held))]
        q=[int(lots[m]*math.ceil(max(0.,required[m]-held[m])/lots[m])) for m in range(len(held))]
        if any(x>0 and x+held[m]>slots[m] for m,x in enumerate(q)):continue
        if sum(x*s for x,s in zip(q,spaces))>room:continue
        options=[[o for o in offers[m] if o[1]>=x] if x else [(0,0,0,-1)] for m,x in enumerate(q)]
        for suppliers in itertools.product(*options):
            cost=sum(o[0]*x+(o[2] if x else 0) for o,x in zip(suppliers,q))
            if cost+sum(r*y for r,y in zip(reserve,ys))>cash:continue
            value=sum(route_values[r][y] for r,y in enumerate(ys))-cost
            ids=tuple(o[3] for o in suppliers)
            if value>best[0]+1e-9 or (abs(value-best[0])<=1e-9 and (cost,ys,ids)<(best[4],best[1],best[2])):
                best=(value,ys,ids,tuple(q),cost)
    return best
