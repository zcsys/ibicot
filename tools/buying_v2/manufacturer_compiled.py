"""Compiled T2 company purchase callback for the retained production kernel."""
import math
import numpy as np
from economy.core import model as M
from economy.kernel.numba import INPUT_SPACE
from .jit import njit
from .discovery import sample_distinct
from .industrial_observations import record
from .seller_exposure import record_exposure
from .decision_traces import capture
from .replenishment_compiled import fund_and_select

NE=M.NE
NI=M.NI


@njit
def buy(seed,tick,firm,firm_class,slots,room,mask,unit_cost,multiple,ids,offsets,sellers,buyer,accounts,observations=None,exposure=None,trace=None):
    owner,stock,price,reliability,cash,sold,revenue,cogs,basis,intermediate_sold,intermediate_revenue,demand,attempts,checks,available,opportunities,fee_income=sellers
    buyer_cash,raw,raw_basis,inputs,input_basis,preferred,bought_total,fee_expense=buyer
    mat_spend,mat_orders,loyalty_count,loyalty_amount=accounts
    n=0
    for m in range(NI):
        if mask & (1 << m):
            n+=1
    if not n:
        return
    if n>12:
        raise ValueError('more than twelve input fee groups requires separate scaling validation')
    materials=np.empty(n,np.int64);held=np.empty(n,np.int64);values=np.empty(n);targets=np.empty(n,np.int64)
    spaces=np.empty(n);incumbents=np.empty(n,np.int64);fees=np.zeros(n)
    om=np.empty(n*6,np.int64);supplier=np.empty(n*6,np.int64);prices=np.empty(n*6);stocks=np.empty(n*6,np.int64)
    count=0;j=0
    for m in range(NI):
        if not mask & (1 << m):
            continue
        materials[j]=m
        index=firm*(NE if m<NE else NI)+m
        held[j]=int(raw[index] if m<NE else inputs[index])
        if (raw[index] if m<NE else inputs[index])!=held[j]:
            raise ValueError('nonintegral owned input; no purchase committed')
        values[j]=held[j]*(raw_basis[index] if m<NE else input_basis[index])
        targets[j]=max(0,math.floor(slots[m])-held[j]);spaces[j]=INPUT_SPACE[m]
        incumbents[j]=preferred[firm*NI+m]
        sampled=sample_distinct(ids[offsets[m]:offsets[m+1]],incumbents[j],seed,tick,firm,m)
        for s in sampled:
            om[count]=j;supplier[count]=s;prices[count]=price[s];stocks[count]=math.floor(stock[s]);count+=1
            if s==incumbents[j]:
                fees[j]=multiple*unit_cost*(1+min(1.,max(0.,reliability[s])))
        j+=1
    om=om[:count];supplier=supplier[:count];prices=prices[:count];stocks=stocks[:count]
    bids,demands,reference,result=fund_and_select(targets,om,supplier,prices,stocks,incumbents,fees,buyer_cash[firm],1,spaces,room)
    allocation,_,_,charges=result
    bought=np.zeros(n,np.int64);goods=np.zeros(n)
    for i in range(count):
        j=om[i];q=allocation[i]
        bought[j]+=q;goods[j]+=q*prices[i];values[j]+=q*prices[i]
    total=sum(goods)+sum(charges)
    if total>buyer_cash[firm] or sum(bought*spaces)>room:
        raise ValueError('compiled T2 basket violates cash/storage; no purchase committed')
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
            raise ValueError('compiled T2 fallback exceeds remaining request')
        cumulative[j]+=q
        if demands[i]>0 and q>=demands[i]:
            preferences[j]=supplier[i]
    if trace is not None:
        if trace[0][firm] >= 0:
            opening_basis=np.empty(n)
            for j in range(n):
                m=materials[j];index=firm*(NE if m<NE else NI)+m
                opening_basis[j]=raw_basis[index] if m<NE else input_basis[index]
            capture(trace,firm,buyer_cash[firm],room,1,materials,held,opening_basis,targets,spaces,
                    incumbents,bids,fees,preferences,charges,om,supplier,prices,stocks,demands,allocation,requests)
    for i in order:
        q=allocation[i]
        if not q:
            continue
        j=om[i];m=materials[j];s=supplier[i];payment=q*prices[i]
        demand[s]+=requests[i];attempts[s]+=1;checks[s]+=1
        available[s]+=int(stock[s]>=requests[i]);opportunities[m]+=1
        stock[s]-=q;cash[owner[s]]+=payment;sold[s]+=q;revenue[s]+=payment;cogs[s]+=q*basis[s]
        intermediate_sold[m]+=q;intermediate_revenue[m]+=payment
        mat_spend[firm_class]+=payment;mat_orders[firm_class]+=1
    for j in range(n):
        m=materials[j];index=firm*(NE if m<NE else NI)+m
        if bought[j]:
            if m<NE:
                raw_basis[index]=values[j]/(held[j]+bought[j]);raw[index]+=bought[j]
            else:
                input_basis[index]=values[j]/(held[j]+bought[j]);inputs[index]+=bought[j]
            preferred[firm*NI+m]=preferences[j]
        if charges[j]:
            s=incumbents[j];cash[owner[s]]+=charges[j];fee_income[owner[s]]+=charges[j]
            fee_expense[firm]+=charges[j];loyalty_count[1]+=1;loyalty_amount[1]+=charges[j]
    buyer_cash[firm]-=total;bought_total[firm]+=sum(bought)
    if exposure is not None:
        record_exposure(exposure,supplier,stocks,demands,1)
    if observations is not None:
        record(observations,NE,materials,targets,1,om,supplier,prices,stocks,demands,incumbents,bids,allocation,requests,preferences,charges)


# Recompile the shared production loop under the experiment's source-aware
# cache namespace: changing imported experimental helpers invalidates callers.
from economy.kernel import numba as _production
phase_kernel = njit(_production._operate_tier2_nb.py_func)
