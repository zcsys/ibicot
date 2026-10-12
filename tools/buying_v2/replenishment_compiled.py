"""Typed-array exact replenishment funding and storage-constrained search.

No world mutation. Search limits fail explicitly; there is no approximate basket.
"""
import math
import numpy as np
from .jit import njit
from .replenishment import solve_uniform


@njit
def space_bound(lo,hi,targets,material,prices,spaces,payable,supplier,incumbents,cash,room,lot):
    n=len(targets)
    minimum=np.zeros(n,np.int64);maximum=np.zeros(n,np.int64);outside=np.zeros(n,np.bool_)
    goods=used=0.
    cheapest=smallest=np.inf
    for i in range(len(lo)):
        m=material[i]
        minimum[m]+=lo[i];maximum[m]+=hi[i]
        goods+=lo[i]*prices[i];used+=lo[i]*spaces[m]
        outside[m]|=lo[i]>0 and supplier[i]!=incumbents[m]
        if hi[i]>lo[i]:
            cheapest=min(cheapest,prices[i]);smallest=min(smallest,spaces[m])
    charges=np.zeros(n)
    for m in range(n):
        if outside[m]:
            charges[m]=payable[m]
    payment=goods+sum(charges)
    epsilon=1e-9+1e-12*max(1.,cash,room,payment,used)
    if payment>cash+epsilon or used>room+epsilon:
        return -1,payment,used,charges
    potential=0
    for m in range(n):
        if minimum[m]>targets[m]:
            return -1,payment,used,charges
        potential+=min(targets[m],maximum[m])-minimum[m]
    if math.isfinite(cheapest):
        potential=min(potential,max(0,math.floor((cash-payment+epsilon)/cheapest/lot))*lot,
                      max(0,math.floor((room-used+epsilon)/smallest/lot))*lot)
    return sum(lo)+potential,payment,used,charges


@njit
def solve_space(targets,material,supplier,prices,stocks,incumbents,bids,fees,cash,lot,demands,spaces,room,max_nodes):
    n,count=len(targets),len(prices)
    payable=np.zeros(n)
    for i in range(count):
        m=material[i]
        if supplier[i]==incumbents[m] and bids[m]>0 and stocks[i]>=bids[m]:
            payable[m]=fees[m]
    upper=np.empty(count,np.int64)
    depth=2
    for i in range(count):
        upper[i]=min(stocks[i],targets[material[i]])//lot*lot
        width=upper[i]//lot
        while width:
            depth+=1;width//=2
    low_stack=np.zeros((depth,count),np.int64);high_stack=np.zeros((depth,count),np.int64)
    high_stack[0]=upper
    top=1;nodes=0
    best=np.zeros(count,np.int64);best_units=0;best_payment=0.;best_fees=np.zeros(n)
    order=np.arange(count)
    for j in range(1,count):
        i=order[j];k=j-1
        while k>=0:
            a=order[k]
            before=material[i]<material[a] or (material[i]==material[a] and (prices[i]<prices[a] or (prices[i]==prices[a] and supplier[i]<supplier[a])))
            if not before:
                break
            order[k+1]=a;k-=1
        order[k+1]=i
    while top:
        if nodes>=max_nodes:
            raise ValueError('space-constrained replenishment search limit; no exact result returned')
        nodes+=1;top-=1
        lo=low_stack[top].copy();hi=high_stack[top].copy()
        units,payment,used,charges=space_bound(lo,hi,targets,material,prices,spaces,payable,supplier,incumbents,cash,room,lot)
        tol=1e-9+1e-12*max(abs(payment),abs(best_payment))
        if units<best_units or (units==best_units and payment>best_payment+tol):
            continue
        axis=-1;width=0
        for i in range(count):
            w=(hi[i]-lo[i])//lot
            if w>width:
                width=w;axis=i
        if axis<0:
            cumulative=np.zeros(n,np.int64);valid=True
            for i in order:
                m=material[i]
                if demands[i]>=0 and lo[i]>max(0,demands[i]-cumulative[m]):
                    valid=False
                cumulative[m]+=lo[i]
            if not valid or payment>cash or used>room:
                continue
            lex=False
            for i in range(count):
                if lo[i]!=best[i]:
                    lex=lo[i]<best[i];break
            if units>best_units or (units==best_units and (payment<best_payment-tol or (abs(payment-best_payment)<=tol and lex))):
                best[:]=lo;best_units=units;best_payment=payment;best_fees[:]=charges
            continue
        middle=lo[axis]+width//2*lot
        # High allocation branch first; low branch remains on the bounded stack.
        low_stack[top]=lo;high_stack[top]=hi;high_stack[top,axis]=middle;top+=1
        low_stack[top]=lo;low_stack[top,axis]=middle+lot;high_stack[top]=hi;top+=1
    return best,best_units,best_payment,best_fees


@njit
def select(targets,material,supplier,prices,stocks,incumbents,bids,fees,cash,lot,demands,spaces,room,max_nodes):
    required=0.
    heterogeneous=False
    for m in range(len(targets)):
        required+=targets[m]*spaces[m]
    # With no physically purchasable lot, the only feasible allocation is
    # zero. Preserve the explicit zero-node failure of the general search.
    any_lot=False
    for i in range(len(prices)):
        if min(stocks[i],targets[material[i]])>=lot:
            any_lot=True
            break
    if not any_lot and max_nodes>=1:
        return np.zeros(len(prices),np.int64),0,0.,np.zeros(len(targets))
    for i in range(len(prices)):
        for j in range(i):
            if material[i]==material[j] and prices[i]==prices[j] and demands[i]!=demands[j]:
                heterogeneous=True
    if required>room or heterogeneous:
        return solve_space(targets,material,supplier,prices,stocks,incumbents,bids,fees,cash,lot,demands,spaces,room,max_nodes)
    return solve_uniform(targets,material,supplier,prices,stocks,incumbents,bids,fees,cash,lot,demands)


@njit
def reference_quantities(targets,rm,rs,rp,rq,noinc,zero,nofees,cash,lot,unlimited,spaces,room,max_nodes):
    required=0.
    for m in range(len(targets)):
        required+=targets[m]*spaces[m]
    if required>room:
        return select(targets,rm,rs,rp,rq,noinc,zero,nofees,cash,lot,unlimited,spaces,room,max_nodes)[0]
    # Exactly the zero-fee, one-offer-per-material solve_uniform traversal.
    # Keep its reverse-index quote ties and sequential budget subtraction;
    # a total-cost affordability shortcut would change rounding boundaries.
    count=len(rp);order=np.arange(count);answer=np.zeros(count,np.int64)
    for j in range(1,count):
        i=order[j];k=j-1
        while k>=0 and (rp[i]<rp[order[k]] or (rp[i]==rp[order[k]] and i>order[k])):
            order[k+1]=order[k];k-=1
        order[k+1]=i
    budget=cash
    for i in order:
        q=min(targets[rm[i]],rq[i])//lot*lot
        q=min(q,int(np.floor(max(0.,budget)/rp[i]/lot))*lot)
        answer[i]=q;budget-=q*rp[i]
    return answer


@njit
def quoted_quantity(targets,rm,rp,rq,order,cash,lot,k,quote):
    # Only preceding offers can affect the queried material's funded quantity.
    # Preserve the full traversal's reverse-index ties and cash subtractions.
    budget=cash
    for i in order:
        if i==k:
            continue
        if rp[i]>quote or (rp[i]==quote and i<k):
            break
        q=min(targets[rm[i]],rq[i])//lot*lot
        q=min(q,int(np.floor(max(0.,budget)/rp[i]/lot))*lot)
        budget-=q*rp[i]
    q=min(targets[rm[k]],rq[k])//lot*lot
    return min(q,int(np.floor(max(0.,budget)/quote/lot))*lot)


@njit
def fund_and_select(targets,material,supplier,prices,stocks,incumbents,fees,cash,lot,spaces,room,max_nodes=100000):
    n,count=len(targets),len(prices)
    rounded=targets//lot*lot
    reference=np.full(n,-1,np.int64)
    for i in range(count):
        m=material[i];old=reference[m]
        if old<0 or (supplier[old]!=incumbents[m] and (supplier[i]==incumbents[m] or prices[i]<prices[old] or (prices[i]==prices[old] and supplier[i]<supplier[old]))):
            reference[m]=i
    refs_count=sum(reference>=0)
    rm=np.empty(refs_count,np.int64);rs=np.empty(refs_count,np.int64);rp=np.empty(refs_count);rq=np.empty(refs_count,np.int64)
    positions=np.full(n,-1,np.int64)
    pos=0
    for m in range(n):
        i=reference[m]
        if i>=0:
            rm[pos]=m;rs[pos]=supplier[i];rp[pos]=prices[i];rq[pos]=targets[m];positions[m]=pos;pos+=1
    noinc=np.full(n,-1,np.int64);zero=np.zeros(n,np.int64);nofees=np.zeros(n);unlimited=np.full(refs_count,-1,np.int64)
    original=reference_quantities(rounded,rm,rs,rp,rq,noinc,zero,nofees,cash,lot,unlimited,spaces,room,max_nodes)
    bids=np.zeros(n,np.int64);quantities=np.zeros(n,np.int64)
    for k in range(refs_count):
        m=rm[k];quantities[m]=original[k]
        if rs[k]==incumbents[m]:
            bids[m]=original[k]
    required=0.
    for m in range(n):
        required+=rounded[m]*spaces[m]
    order=np.arange(refs_count)
    for j in range(1,refs_count):
        i=order[j];k=j-1
        while k>=0 and (rp[i]<rp[order[k]] or (rp[i]==rp[order[k]] and i>order[k])):
            order[k+1]=order[k];k-=1
        order[k+1]=i
    demands=np.empty(count,np.int64)
    for i in range(count):
        m=material[i];cached=-1
        # One fee-free reference offer per material: changing only its supplier
        # identity at the same quote cannot change this hypothetical basket.
        # Reuse the independently computed original quantity, including when
        # total storage binds; do not replace its sequential cash arithmetic.
        if prices[i]==rp[positions[m]]:
            demands[i]=original[positions[m]]
            continue
        for j in range(i):
            if material[j]==m and prices[j]==prices[i]:
                cached=j;break
        if cached>=0:
            demands[i]=demands[cached];continue
        k=positions[m]
        if required<=room:
            demands[i]=quoted_quantity(rounded,rm,rp,rq,order,cash,lot,k,prices[i])
            continue
        old_price=rp[k];old_supplier=rs[k]
        rp[k]=prices[i];rs[k]=supplier[i]
        hypothetical=reference_quantities(rounded,rm,rs,rp,rq,noinc,zero,nofees,cash,lot,unlimited,spaces,room,max_nodes)
        demands[i]=hypothetical[k]
        rp[k]=old_price;rs[k]=old_supplier
    result=select(rounded,material,supplier,prices,stocks,incumbents,bids,fees,cash,lot,demands,spaces,room,max_nodes)
    return bids,demands,quantities,result
