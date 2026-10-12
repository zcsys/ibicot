"""Typed-array T1 settlement, preserving the reference company sequence."""
import math
import numpy as np
from economy.core import model as M
from economy.kernel.numba import T1_SPACE
from .jit import njit
from .discovery import sample_distinct
from .industrial_observations import record
from .seller_exposure import record_exposure
from .decision_traces import capture
from .replenishment_compiled import fund_and_select

NE,NP,N0,NI=M.NE,M.NP,M.N0,M.NI


@njit
def buy(seed,tick,firm,lot,unit_cost,multiple,slots,goods_space,input_mask,profile_has,sellers,buyer,accounts,observations=None,exposure=None,trace=None):
    price,stock,basis,reliability,cash,demand,attempts,checks,available,sold,revenue,cogs,fulfilled,opportunities,fee_income=sellers
    buyer_cash,finished,raw,raw_basis,preferred,last_buy,bought_total,fee_expense,input_need,purchase_req=buyer
    target_requests,funded_requests,loyalty_count,loyalty_amount=accounts
    n=0
    for m in range(NE):
        if input_mask & (1 << m):
            n+=1
    if not n:
        return
    materials=np.empty(n,np.int64);held=np.empty(n,np.int64);values=np.empty(n);targets=np.empty(n,np.int64)
    incumbents=np.empty(n,np.int64);fees=np.zeros(n)
    om=np.empty(n*6,np.int64);supplier=np.empty(n*6,np.int64);prices=np.empty(n*6);stocks=np.empty(n*6,np.int64)
    count=j=0
    for m in range(NE):
        if not input_mask & (1 << m):
            continue
        materials[j]=m;index=firm*NE+m
        held[j]=int(raw[index]);values[j]=held[j]*raw_basis[index];targets[j]=max(0,math.floor(slots[m])-held[j])
        if raw[index]!=held[j]:
            raise ValueError('nonintegral owned input; no purchase committed')
        incumbents[j]=preferred[index]
        eligible=np.empty(N0,np.int64);length=0
        for s in range(N0):
            if profile_has[s,m] and math.isfinite(price[s*NE+m]):
                eligible[length]=s;length+=1
        sampled=sample_distinct(eligible[:length],incumbents[j],seed,tick,firm,m+NI)
        for s in sampled:
            si=s*NE+m;om[count]=j;supplier[count]=s;prices[count]=price[si];stocks[count]=math.floor(stock[si]);count+=1
            if s==incumbents[j]:
                fees[j]=multiple*unit_cost*(1+min(1.,max(0.,reliability[si])))
        j+=1
    occupied=0.
    for m in range(NE):
        occupied+=raw[firm*NE+m]
    finished_space=0.
    for p in range(NP):
        finished_space+=finished[firm*NP+p]*T1_SPACE[p]
    occupied+=finished_space
    room=max(0.,goods_space-occupied)
    om=om[:count];supplier=supplier[:count];prices=prices[:count];stocks=stocks[:count]
    bids,demands,reference,result=fund_and_select(targets,om,supplier,prices,stocks,incumbents,fees,buyer_cash[firm],lot,np.ones(n),room)
    allocation,_,_,charges=result
    bought=np.zeros(n,np.int64);goods=0.
    for i in range(count):
        j=om[i];q=allocation[i];bought[j]+=q;values[j]+=q*prices[i];goods+=q*prices[i]
    total=goods+sum(charges)
    if total>buyer_cash[firm] or sum(bought)>room:
        raise ValueError('compiled T1 basket violates cash/storage; no purchase committed')
    order=np.arange(count)
    for k in range(1,count):
        i=order[k];h=k-1
        while h>=0:
            a=order[h]
            if not (om[i]<om[a] or (om[i]==om[a] and (prices[i]<prices[a] or (prices[i]==prices[a] and supplier[i]<supplier[a])))):
                break
            order[h+1]=a;h-=1
        order[h+1]=i
    cumulative=np.zeros(n,np.int64);preferences=incumbents.copy();requests=np.zeros(count,np.int64)
    for i in order:
        q=allocation[i];j=om[i]
        if not q:
            continue
        requests[i]=max(0,demands[i]-cumulative[j])
        if q>requests[i]:
            raise ValueError('compiled T1 fallback exceeds remaining request')
        cumulative[j]+=q
        if demands[i]>0 and q>=demands[i]:
            preferences[j]=supplier[i]
    if trace is not None:
        if trace[0][firm] >= 0:
            opening_basis=np.empty(n)
            for j in range(n):
                opening_basis[j]=raw_basis[firm*NE+materials[j]]
            capture(trace,firm,buyer_cash[firm],room,lot,materials,held,opening_basis,targets,np.ones(n),
                    incumbents,bids,fees,preferences,charges,om,supplier,prices,stocks,demands,allocation,requests)
    for i in order:
        q=allocation[i]
        if not q:
            continue
        j=om[i];m=materials[j];s=supplier[i];si=s*NE+m;payment=q*prices[i]
        demand[si]+=requests[i];attempts[si]+=1;checks[si]+=1;available[si]+=int(stock[si]>=requests[i]);opportunities[m]+=1
        stock[si]-=q;cash[s]+=payment;sold[si]+=q;revenue[si]+=payment;cogs[si]+=q*basis[si];fulfilled[m]+=q
        last_buy[firm*NE+m]=prices[i]
    for j in range(n):
        m=materials[j];index=firm*NE+m
        if bought[j]:
            raw[index]+=bought[j];raw_basis[index]=values[j]/(held[j]+bought[j]);preferred[index]=preferences[j]
        if charges[j]:
            s=incumbents[j];cash[s]+=charges[j];fee_income[s]+=charges[j];fee_expense[firm]+=charges[j]
            loyalty_count[0]+=1;loyalty_amount[0]+=charges[j]
        input_need[index]=targets[j];purchase_req[index]=targets[j]//lot*lot
        target_requests[m]+=purchase_req[index];funded_requests[m]+=reference[j]
    buyer_cash[firm]-=total;bought_total[firm]+=sum(bought)
    if exposure is not None:
        record_exposure(exposure,supplier*NE+materials[om],stocks,demands,lot)
    if observations is not None:
        record(observations,0,materials,targets,lot,om,supplier,prices,stocks,demands,incumbents,bids,allocation,requests,preferences,charges)


from economy.kernel import numba as _production
phase_kernel = njit(_production._plan_and_buy_inputs_nb.py_func)
