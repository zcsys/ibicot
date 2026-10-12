"""Isolated T1 joint replenishment and atomic wholesale settlement.

Raw suppliers are T0 companies, unlike the line IDs used in the T2 input book.
No production, sell-side pricing, or annual loyalty calibration is replaced.
"""
import math
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K
from .discovery import sample_distinct
from .industry_oracle import Problem, Offer, validate
from .funding import replenishment_plan


def company_problem(w,cfg,tick,firm,profiles):
    slots,_,used=K.tier1_storage_layout(w,cfg,firm)
    materials=sorted(used)
    held=tuple(int(w.raw[firm*M.NE+m]) for m in materials)
    caps=tuple(max(h,math.floor(slots[m])) for m,h in zip(materials,held))
    incumbents=tuple(int(w.preferredWholesale[firm*M.NE+m]) for m in materials)
    offers=[];fees=[]
    for j,m in enumerate(materials):
        ids=np.array([s for s in range(M.N0) if M.ELEMENTS[m] in profiles[s]['elements']
                      and math.isfinite(w.t0Price[s*M.NE+m])],dtype=np.int64)
        for s in sample_distinct(ids,incumbents[j],cfg['seed'],tick,firm,m+M.NI):
            index=int(s)*M.NE+m
            offers.append(Offer(j,int(s),float(w.t0Price[index]),math.floor(w.t0Inv[index]),int(cfg['minWholesaleLot'])))
        fees.append(M.loyalty_charge(cfg['baseCost'],w.t0Rel[incumbents[j]*M.NE+m],w.lm1)
                    if incumbents[j] in ids else 0.)
    occupied=sum(w.raw[firm*M.NE:(firm+1)*M.NE])+sum(w.t1Fin[firm*M.NP+p]*M.PRODUCTS[p]['complexity'] for p in range(M.NP))
    return Problem(held,tuple(float(w.rawBasis[firm*M.NE+m]) for m in materials),(1.,)*len(materials),caps,
                   max(0.,K.tier1_goods_space(w,cfg,firm)-occupied),float(w.t1Cash[firm]),tuple(offers),incumbents,
                   (0,)*len(materials),tuple(fees),(),tuple((0.,)*(cap+1) for cap in caps)),materials


def settle(w,cfg,firm,profiles,p,allocation,materials,observations=None,exposure=None,trace=None):
    validate(p)
    if not 0<=firm<M.N1 or len(materials)!=len(p.held) or len(set(materials))!=len(materials):
        raise ValueError('invalid refinery identity/material map')
    if p.funded_demands is None or len(allocation)!=len(p.offers):
        raise ValueError('missing funded quantities')
    slots,_,used=K.tier1_storage_layout(w,cfg,firm)
    if any(m not in used for m in materials) or p.spaces!=(1.,)*len(materials):
        raise ValueError('unsupported refinery input')
    if w.t1Cash[firm]!=p.cash:
        raise ValueError('cash changed; replan')
    for j,m in enumerate(materials):
        index=firm*M.NE+m
        if w.raw[index]!=p.held[j] or w.rawBasis[index]!=p.basis[j] or w.preferredWholesale[index]!=p.incumbents[j]:
            raise ValueError('buyer changed; replan')
    bought=[0]*len(materials);values=[h*b for h,b in zip(p.held,p.basis)]
    outside=[False]*len(materials);goods=0.
    for o,q in zip(p.offers,allocation):
        if not math.isfinite(q) or q<0 or q!=int(q) or q%cfg['minWholesaleLot'] or o.lot!=cfg['minWholesaleLot'] or q>o.stock:
            raise ValueError('invalid wholesale quantity')
        m=materials[o.material];index=o.supplier*M.NE+m
        if o.supplier>=M.N0 or M.ELEMENTS[m] not in profiles[o.supplier]['elements']:
            raise ValueError('invalid raw supplier')
        if w.t0Price[index]!=o.price or math.floor(w.t0Inv[index])!=o.stock:
            raise ValueError('supplier changed; replan')
        bought[o.material]+=q;values[o.material]+=q*o.price;goods+=q*o.price
        outside[o.material]|=q>0 and o.supplier!=p.incumbents[o.material]
    fees=[0.]*len(materials)
    for j,m in enumerate(materials):
        if bought[j] and p.held[j]+bought[j]>min(p.slots[j],math.floor(slots[m])):
            raise ValueError('input slot overflow')
        incumbent=p.incumbents[j]
        valid=0<=incumbent<M.N0 and M.ELEMENTS[m] in profiles[incumbent]['elements'] and math.isfinite(w.t0Price[incumbent*M.NE+m])
        inc=next((i for i,o in enumerate(p.offers) if o.material==j and o.supplier==incumbent),None)
        if valid and inc is None:
            raise ValueError('incumbent snapshot missing')
        if inc is not None and p.funded_demands[inc]!=p.bids[j]:
            raise ValueError('incumbent funded bid mismatch')
        if outside[j] and inc is not None and p.bids[j]>0 and p.offers[inc].stock>=p.bids[j]:
            fee=M.loyalty_charge(cfg['baseCost'],w.t0Rel[incumbent*M.NE+m],w.lm1)
            if abs(fee-p.fees[j])>1e-12*max(1.,fee):
                raise ValueError('loyalty formula mismatch')
            fees[j]=fee
    occupied=sum(w.raw[firm*M.NE:(firm+1)*M.NE])+sum(w.t1Fin[firm*M.NP+i]*M.PRODUCTS[i]['complexity'] for i in range(M.NP))
    if sum(bought)>max(0.,min(p.free_space,K.tier1_goods_space(w,cfg,firm)-occupied)):
        raise ValueError('total storage overflow')
    payment=goods+sum(fees)
    if payment>p.cash:
        raise ValueError('cash exhausted')
    order=sorted(range(len(p.offers)),key=lambda i:(p.offers[i].material,p.offers[i].price,p.offers[i].supplier))
    cumulative=[0]*len(materials);requests=[0]*len(p.offers);preferences=list(p.incumbents)
    for i in order:
        o,q=p.offers[i],allocation[i]
        if not q:
            continue
        requests[i]=max(0,p.funded_demands[i]-cumulative[o.material])
        if q>requests[i]:
            raise ValueError('remaining request exceeded')
        cumulative[o.material]+=q
        if p.funded_demands[i]>0 and q>=p.funded_demands[i]:
            preferences[o.material]=o.supplier
    if trace is not None:
        from .decision_traces import capture_problem
        capture_problem(trace,firm,p,materials,allocation,requests,preferences,fees,int(cfg['minWholesaleLot']))
    # Everything above is read-only. Post only actual supplier requests below.
    for i in order:
        o,q=p.offers[i],allocation[i]
        if not q:
            continue
        m=materials[o.material];index=o.supplier*M.NE+m
        w.t0Demand[index]+=requests[i]
        w.t0RelAttempts[index]+=1;w.t0RelChecks[index]+=1
        w.t0RelAvailable[index]+=int(w.t0Inv[index]>=requests[i])
        w.t0Opportunities[m]+=1
        w.t0Inv[index]-=q;w.t0Cash[o.supplier]+=q*o.price
        w.t0Sold[index]+=q;w.t0Revenue[index]+=q*o.price;w.t0COGS[index]+=q*w.t0InvBasis[index]
        w.t0Fulfilled[m]+=q
        w.t1LastBuy[firm*M.NE+m]=o.price
    for j,m in enumerate(materials):
        index=firm*M.NE+m
        if bought[j]:
            w.raw[index]+=bought[j];w.rawBasis[index]=values[j]/(p.held[j]+bought[j])
            w.preferredWholesale[index]=preferences[j]
        if fees[j]:
            w.t0Cash[p.incumbents[j]]+=fees[j]
            w.t0SwitchingIncome[p.incumbents[j]]+=fees[j];w.t1SwitchingExpense[firm]+=fees[j]
            w.loyaltySwitches[0]+=1;w.loyaltyPenalties[0]+=fees[j]
    w.t1Cash[firm]-=payment;w.t1Bought[firm]+=sum(bought)
    if exposure is not None:
        from .seller_exposure import record_exposure
        record_exposure(exposure,np.asarray([o.supplier*M.NE+materials[o.material] for o in p.offers],dtype=np.int64),
                        np.asarray([o.stock for o in p.offers]),np.asarray(p.funded_demands),int(cfg['minWholesaleLot']))
    if observations is not None:
        from .industrial_observations import record_problem
        record_problem(observations,0,materials,p,allocation,requests,preferences,fees,lot=int(cfg['minWholesaleLot']))
    return dict(goods=goods,fees=sum(fees),quantities=bought,preferences=preferences,
                productOrders=sum(q>0 for q in bought),positiveLegs=sum(q>0 for q in allocation))


def buy_reference(w,cfg,tick,firm,profiles,observations=None,exposure=None,trace=None):
    p,materials=company_problem(w,cfg,tick,firm,profiles)
    if not materials:
        return None
    funded,result=replenishment_plan(p)
    postings=settle(w,cfg,firm,profiles,funded,result[0],materials,observations,exposure,trace)
    # Explicit legacy projections, distinct from supplier request legs: targets
    # are slot deficits, funded quantities are the stock-unconstrained joint
    # reference plan, including cheapest-reference inputs without an incumbent.
    for j,m in enumerate(materials):
        index=firm*M.NE+m
        target=max(0,p.slots[j]-p.held[j])
        w.t1InputNeed[index]=target
        w.t1PurchaseReq[index]=target//cfg['minWholesaleLot']*cfg['minWholesaleLot']
        w.t0Req[m]+=w.t1PurchaseReq[index]
        choices=[i for i,o in enumerate(p.offers) if o.material==j]
        incumbent=next((i for i in choices if p.offers[i].supplier==p.incumbents[j]),None)
        reference=incumbent if incumbent is not None else min(choices,key=lambda i:(p.offers[i].price,p.offers[i].supplier),default=None)
        if reference is not None:
            w.t0FundedReq[m]+=funded.funded_demands[reference]
    return dict(problem=funded,allocation=result[0],materials=materials,postings=postings)
