"""Compiled procurement and sequential production for the continuation ledger."""
import math
import numpy as np
from .jit import njit
from .float_sum import add,finish


@njit
def dot(q,p):
    total=correction=0.
    for i in range(len(q)):total,correction=add(total,correction,q[i]*p[i])
    return finish(total,correction)


@njit
def purchase(iv,fv,allocation,cash,held,basis,finished,finished_basis,quotes,incumbents,
             slots,spaces,storage,fixed,arrears,ema,recipe,limits,yields,conversion,output_space,caps,band):
    count=iv[0];n=len(held);nl=len(finished)
    native=np.any(held!=np.floor(held)) or np.any(finished!=np.floor(finished)) or np.any(slots!=np.floor(slots))
    inventory=held.copy();values=held*basis;preferences=incumbents.copy()
    quantities=np.zeros(n,np.int64);outside=np.zeros(n,np.bool_);fees=np.zeros(n)
    outputs=np.zeros(nl,np.int64);stock=finished.copy();stock_basis=finished_basis.copy()
    order=np.arange(count);funded=4+count*4
    for j in range(1,count):
        i=order[j];k=j-1
        while k>=0:
            other=order[k]
            a=iv[4+i*4];b=iv[4+other*4]
            before=a<b or (a==b and (fv[4+i]<fv[4+other] or (fv[4+i]==fv[4+other] and iv[5+i*4]<iv[5+other*4])))
            if not before:break
            order[k+1]=other;k-=1
        order[k+1]=i
    for rank in range(count):
        i=order[rank];m=iv[4+i*4];q=allocation[i]
        if q>max(0,iv[funded+i]-quantities[m]):raise ValueError('infeasible procurement allocation')
        quantities[m]+=q
        if q>0 and iv[funded+i]>0 and q>=iv[funded+i]:preferences[m]=iv[5+i*4]
    goods=0.
    for i in range(count):
        m=iv[4+i*4];supplier=iv[5+i*4];q=allocation[i]
        if q<0 or q>iv[6+i*4] or q%iv[7+i*4]:raise ValueError('infeasible procurement allocation')
        goods+=q*fv[4+i];inventory[m]+=q;values[m]+=q*fv[4+i]
        outside[m]=outside[m] or (q>0 and supplier!=incumbents[m])
    room=storage-dot(held,spaces)-dot(finished,output_space)
    if dot(quantities,spaces)>max(0.,room):raise ValueError('infeasible procurement allocation')
    for m in range(n):
        if inventory[m]>max(held[m],slots[m]):raise ValueError('infeasible procurement allocation')
        for i in range(count):
            if iv[4+i*4]==m and iv[5+i*4]==incumbents[m]:
                bid=iv[funded+i]
                if outside[m] and incumbents[m]>=0 and bid>0 and iv[6+i*4]>=bid:
                    fees[m]=fv[1]*fv[0]*(1+min(1.,max(0.,fv[4+count+i])))
                break
    fee=dot(np.ones(n),fees)
    payment=goods+fee
    if payment>cash:raise ValueError('infeasible procurement allocation')
    purchased_cash=cash-payment
    bought_basis=np.zeros(n)
    for m in range(n):bought_basis[m]=basis[m] if native and quantities[m]==0 else (values[m]/inventory[m] if inventory[m] else 0.)
    gate_equity=cash+fixed-arrears+dot(held,basis)+dot(finished,finished_basis)
    if iv[3]==1:gate_equity=purchased_cash+fixed-arrears+dot(inventory,bought_basis)+dot(finished,finished_basis)
    overhead=fv[-1] if iv[3]==2 else ((fv[2] if gate_equity>=fv[3] else 0.)-ema)/nl
    free=max(0.,storage-dot(inventory,spaces)-dot(finished,output_space))
    cash=purchased_cash;used=0.;paid=0.
    # The reference production pass reconstitutes basis from inventory value.
    made_basis=np.zeros(n)
    for m in range(n):made_basis[m]=bought_basis[m] if native else ((inventory[m]*bought_basis[m])/inventory[m] if inventory[m] else 0.)
    for r in range(nl):
        active=False
        for j in range(iv[2]):
            if iv[funded+iv[1]+j]==r:active=True
        possible=max(0,min(limits[r],math.floor((caps[r]-finished[r])/yields[r]))) if active else 0
        for m in range(n):
            if recipe[r,m]:possible=min(possible,math.floor(inventory[m]/recipe[r,m]) if native else inventory[m]//recipe[r,m])
        possible=min(possible,math.floor(cash/max(1e-9,conversion[r]*yields[r])))
        unit=dot(recipe[r],made_basis)/yields[r]+conversion[r]
        batches=0
        if possible>0 and unit<=quotes[r]+1e-9:
            surplus=quotes[r]-unit-overhead/(possible*yields[r])
            ratio=min(1.,max(0.,(surplus/max(quotes[r],1e-9))/band))
            candidate=math.floor(possible*ratio+.5)
            if candidate>0 and (quotes[r]-unit)*candidate*yields[r]-overhead>=-1e-9:batches=candidate
        units=batches*yields[r];consumed=0.
        for m in range(n):
            inventory[m]-=recipe[r,m]*batches
            consumed+=recipe[r,m]*batches*spaces[m]
        used+=units*output_space[r]-consumed
        if used>free+1e-9:raise ValueError('production would exceed physical storage')
        expense=units*conversion[r];cash-=expense;paid+=expense;outputs[r]=units
        cost=conversion[r]+dot(recipe[r],bought_basis)/yields[r]
        stock[r]=finished[r]+units
        value=finished[r]*finished_basis[r]+units*cost
        stock_basis[r]=value/stock[r] if stock[r] else 0.
    return cash,inventory,made_basis,stock,stock_basis,preferences,goods,fees,outputs,paid,overhead,gate_equity,purchased_cash
