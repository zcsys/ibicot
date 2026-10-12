"""Exact reference fallback when total space couples replenishment targets."""
import heapq
import math
import numpy as np
from .industry_bounds import SearchLimit


def solve(targets, offers, incumbents, bids, fees, cash, spaces, room, lot, max_nodes, funded_demands=None):
    n=len(targets)
    payable=[]
    for m in range(n):
        inc_stock=next((o.stock for o in offers if o.material==m and o.supplier==incumbents[m]),0)
        payable.append(fees[m] if incumbents[m]>=0 and bids[m]>0 and inc_stock>=bids[m] else 0.)
    upper=tuple(min(o.stock,targets[o.material])//lot*lot for o in offers)
    zero=(0,)*len(offers)
    best_q=zero;best_units=0;best_payment=0.;best_fees=[0.]*n

    def bound(lo,hi):
        minimum=[0]*n;maximum=[0]*n;outside=[False]*n
        goods=used=0.
        for i,o in enumerate(offers):
            minimum[o.material]+=lo[i];maximum[o.material]+=hi[i]
            goods+=lo[i]*o.price;used+=lo[i]*spaces[o.material]
            outside[o.material]|=lo[i]>0 and o.supplier!=incumbents[o.material]
        charges=[payable[m] if outside[m] else 0. for m in range(n)]
        payment=goods+sum(charges)
        epsilon=1e-9+1e-12*max(1.,cash,room,payment,used)
        if any(a>b for a,b in zip(minimum,targets)) or payment>cash+epsilon or used>room+epsilon:
            return None
        units=sum(lo)
        potential=sum(min(targets[m],maximum[m])-minimum[m] for m in range(n))
        remaining=[o for i,o in enumerate(offers) if hi[i]>lo[i]]
        if remaining:
            cheapest=min(o.price for o in remaining)
            smallest=min(spaces[o.material] for o in remaining)
            potential=min(potential,max(0,math.floor((cash-payment+epsilon)/cheapest/lot))*lot,
                          max(0,math.floor((room-used+epsilon)/smallest/lot))*lot)
        return units+potential,payment,used,charges

    queue=[];serial=0;nodes=0
    first=bound(zero,upper)
    heapq.heappush(queue,(-first[0],first[1],serial,zero,upper))
    while queue:
        if nodes>=max_nodes:
            raise SearchLimit('space-constrained replenishment search limit; no exact result returned')
        neg_units,low_cost,_,lo,hi=heapq.heappop(queue);nodes+=1
        tol=1e-9+1e-12*max(abs(low_cost),abs(best_payment))
        if -neg_units<best_units or (-neg_units==best_units and low_cost>best_payment+tol):
            continue
        widths=[(b-a)//lot for a,b in zip(lo,hi)]
        if not widths or max(widths)==0:
            if funded_demands is not None:
                cumulative=[0]*n
                valid=True
                for i in sorted(range(len(offers)),key=lambda i:(offers[i].material,offers[i].price,offers[i].supplier)):
                    m=offers[i].material
                    if lo[i]>max(0,funded_demands[i]-cumulative[m]):
                        valid=False
                    cumulative[m]+=lo[i]
                if not valid:
                    continue
            total,payment,used,charges=bound(lo,hi)
            if payment>cash or used>room:
                continue
            if total>best_units or (total==best_units and (payment<best_payment-tol or (abs(payment-best_payment)<=tol and lo<best_q))):
                best_q,best_units,best_payment,best_fees=lo,total,payment,charges
            continue
        axis=widths.index(max(widths));middle=lo[axis]+widths[axis]//2*lot
        low_hi=list(hi);low_hi[axis]=middle
        high_lo=list(lo);high_lo[axis]=middle+lot
        for a,b in ((lo,tuple(low_hi)),(tuple(high_lo),hi)):
            estimate=bound(a,b)
            if estimate is None or estimate[0]<best_units:
                continue
            serial+=1
            heapq.heappush(queue,(-estimate[0],estimate[1],serial,a,b))
    return np.array(best_q,dtype=np.int64),best_units,best_payment,np.array(best_fees)
