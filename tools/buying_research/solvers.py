"""Exact finite-action basket solvers. No world mutations or sampled evaluation draws.

Input arrays are in ascending stable supplier ID order. Monetary ties prefer lower
cost, then incumbent use, then more units at the lower stable supplier ID.
"""
import math
import numpy as np
from .jit import njit
from economy.core.rng import random_


@njit
def sample_distinct(ids, preferred, seed, tick, buyer, market, count=5):
    """Floyd sampling from non-incumbent indices, uniform without replacement."""
    # Books are sorted by stable ID, so finding the incumbent is logarithmic.
    location=np.searchsorted(ids,preferred)
    pref_pos=location if location<len(ids) and ids[location]==preferred else -1
    n=len(ids)-(1 if pref_pos>=0 else 0)
    k=min(count,n);draws=np.empty(k,dtype=np.int64)
    for step in range(k):
        j=n-k+step
        stream=(buyer*1009+market*1000003+step*10000019+43000001)&0xffffffff
        v=int(random_(seed,tick,stream)*(j+1))
        for prev in range(step):
            if draws[prev]==v:v=j;break
        draws[step]=v
    answer=np.empty(k+(1 if pref_pos>=0 else 0),dtype=np.int64)
    for i in range(k):
        idx=draws[i]
        if pref_pos>=0 and idx>=pref_pos:idx+=1
        answer[i]=ids[idx]
    if pref_pos>=0:answer[k]=preferred
    return np.sort(answer)


@njit
def demand_quantity(latent,half,eta,price,u):
    u=max(u,1e-12)
    q=latent/(1+(price/half)**eta) if latent>0 and half>0 else 0.
    return int(math.floor(q)+(1 if u<q-math.floor(q) else 0))


@njit
def marginal_values(latent,half,eta,u):
    n=int(math.ceil(latent));v=np.zeros(n);u=max(u,1e-12)
    for k in range(n):
        quantile=k+u
        if quantile<latent:
            v[k]=half*(max(0.,latent/max(quantile,1e-12)-1))**(1/eta)
    return v


@njit
def better(score,cost,allocation,best_score,best_cost,best,preferred):
    tol=1e-9+1e-12*max(abs(score),abs(best_score))
    if score>best_score+tol:return True
    if score<best_score-tol:return False
    if cost<best_cost-1e-9:return True
    if cost>best_cost+1e-9:return False
    if preferred>=0 and allocation[preferred]!=best[preferred]:
        return allocation[preferred]>best[preferred]
    for i in range(len(best)):
        if allocation[i]!=best[i]:return allocation[i]>best[i]
    return False


@njit
def retail(values,prices,stock,preferred,bid,fixed_fee,cash):
    """Incumbent-only vs outside-bearing schedules; fee availability is frozen.

    preferred is an index into the local candidate arrays (or -1).
    Returns allocations, utility net of total payment, goods, fee, preference.
    """
    n=len(prices);limit=len(values)
    fee=fixed_fee if preferred>=0 and bid>0 and stock[preferred]>=bid else 0.
    same_price=n>0
    for i in range(1,n):
        if prices[i]!=prices[0]:same_price=False;break
    if same_price:
        # The general comparator groups near-equal objectives into monetary
        # ties. Use it at ambiguous marginal gains instead of silently adopting
        # a stricter positive-gain convention in this optimization.
        scale=0.
        for v in values:scale+=abs(v)+abs(prices[0])
        threshold=1e-9+1e-12*scale
        for v in values:
            if 0<abs(v-prices[0])<=threshold:same_price=False;break
    if same_price:
        desired=0;utility=0.
        for v in values:
            if v>prices[0] and (desired+1)*prices[0]<=cash:desired+=1;utility+=v
            else:break
        # All equal prices with free outside access, or adequate incumbent stock:
        # all marginally worthwhile units form the optimum with the tie allocator.
        if fee==0 or (preferred>=0 and stock[preferred]>=desired):
            best=np.zeros(n,dtype=np.int64);left=desired
            if preferred>=0:
                best[preferred]=min(left,int(stock[preferred]));left-=best[preferred]
            for i in range(n):
                if i==preferred:continue
                best[i]=min(left,int(stock[i]));left-=best[i]
            q=desired-left;utility=0.
            for i in range(q):utility+=values[i]
            new_pref=preferred;only=-1;sellers=0
            for i in range(n):
                if best[i]>0:only=i;sellers+=1
            if bid>0 and sellers==1 and best[only]>=bid:new_pref=only
            return best,utility-q*prices[0],q*prices[0],0.,new_pref
    order=np.arange(n)
    # Stable insertion sort; equal quotes favor incumbent then stable input index.
    for i in range(1,n):
        item=order[i];j=i-1
        while j>=0:
            prev=order[j]
            move=(prices[item]<prices[prev] or (prices[item]==prices[prev] and item==preferred and prev!=preferred))
            if not move:break
            order[j+1]=prev;j-=1
        order[j+1]=item
    cheapest_out=-1
    for idx in order:
        if idx!=preferred and stock[idx]>=1:
            cheapest_out=idx;break
    best=np.zeros(n,dtype=np.int64);best_score=0.;best_payment=0.;best_goods=0.;best_fee=0.
    prefix=np.zeros(n,dtype=np.int64);incumbent=np.zeros(n,dtype=np.int64)
    prefix_cost=0.;outside=0;head=0;utility=0.
    for q in range(1,limit+1):
        utility+=values[q-1]
        # Incumbent-only option.
        if preferred>=0 and q<=stock[preferred]:
            goods=q*prices[preferred]
            incumbent[preferred]=q
            if goods<=cash and better(utility-goods,goods,incumbent,best_score,best_payment,best,preferred):
                for i in range(n):best[i]=incumbent[i]
                best_score=utility-goods;best_payment=goods;best_goods=goods;best_fee=0.
        while head<n and prefix[order[head]]>=int(stock[order[head]]):head+=1
        if head>=n:continue
        idx=order[head];prefix[idx]+=1;prefix_cost+=prices[idx]
        if idx!=preferred:outside+=1
        if cheapest_out<0:continue
        goods=prefix_cost
        if outside==0:
            # Cheapest q units were all incumbent. Force one outside unit.
            prefix[preferred]-=1;prefix[cheapest_out]+=1
            goods+=prices[cheapest_out]-prices[preferred]
        payment=goods+fee
        if payment<=cash and better(utility-payment,payment,prefix,best_score,best_payment,best,preferred):
            for i in range(n):best[i]=prefix[i]
            best_score=utility-payment;best_payment=payment;best_goods=goods;best_fee=fee
        if outside==0:
            prefix[preferred]+=1;prefix[cheapest_out]-=1
    new_preferred=preferred
    if bid>0:
        sellers=0;only=-1
        for i in range(n):
            if best[i]>0:sellers+=1;only=i
        if sellers==1 and best[only]>=bid:new_preferred=only
    return best,best_score,best_goods,best_fee,new_preferred


@njit
def industrial_value(y,finished,price,mean,conversion):
    if mean<=0:return -conversion*y
    return price*mean*math.exp(-finished/mean)*(-math.expm1(-y/mean))-conversion*y


@njit
def plan_points(bound,held,ratios,lots,finished,price,mean,conversion):
    """Exact candidates at purchase-cost steps and the free-value stationary point.

    A fixed purchase vector applies between consecutive lot boundaries. Value is
    concave there; include both integer neighbors of its stationary point. The
    final buy vector's physical and cash constraints are constant within each
    interval except conversion reserve, handled by the caller's bound.
    """
    # For unit lots every integer is a boundary; at T1 only O(B/lot) are needed.
    points=np.zeros(bound+1,dtype=np.uint8);points[0]=1;points[bound]=1
    for m in range(len(held)):
        if ratios[m]<=0:continue
        for y in range(1,bound+1):
            q0=int(math.ceil(max(0.,ratios[m]*(y-1)-held[m])/lots[m]))
            q1=int(math.ceil(max(0.,ratios[m]*y-held[m])/lots[m]))
            if q1!=q0:points[y]=1;points[y-1]=1
    if conversion>0 and mean>0 and price>0:
        root=mean*math.log(price/conversion)-finished
        if root>=0 and root<=bound:
            points[int(math.floor(root))]=1;points[int(math.ceil(root))]=1
    return np.flatnonzero(points)


@njit
def industry_enumerate(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
             bound,finished,output_price,mean,conversion,cash,reserve_per_output):
    """Exact single-route enumeration, one supplier per ingredient.

    Matrices have one row per unique ingredient and up to six sellers. Prices
    and stocks are local copies read at this buyer's decision point. This simple
    version enumerates all output units, including lot boundaries; optimize only
    after oracle validation. Fees use canonical bids, never search quantities.
    """
    nm=len(held);best_sel=np.full(nm,-1,dtype=np.int64);best_q=np.zeros(nm,dtype=np.int64)
    best_cost=0.;best_score=-1e300;best_y=0;best_fees=np.zeros(nm)
    for y in range(bound+1):
        cost=0.;space=0.;valid=True
        selected=np.full(nm,-1,dtype=np.int64);quantities=np.zeros(nm,dtype=np.int64);charges=np.zeros(nm)
        for m in range(nm):
            q=int(math.ceil(max(0.,ratios[m]*y-held[m])/lots[m]))*int(lots[m])
            quantities[m]=q;space+=q*spaces[m]
            if q>0 and q+held[m]>slots[m]:valid=False;break
            if q==0:continue
            pf=prefs[m];charge=0.
            if pf>=0 and bids[m]>0 and stocks[m,pf]>=bids[m]:charge=fees[m]
            lowest=1e300;winner=-1
            for s in range(counts[m]):
                if stocks[m,s]<q:continue
                payment=q*prices[m,s]+(charge if s!=pf else 0.)
                if payment<lowest-1e-9 or (abs(payment-lowest)<=1e-9 and s==pf):
                    lowest=payment;winner=s
            if winner<0:valid=False;break
            selected[m]=winner;cost+=lowest;charges[m]=charge if winner!=pf else 0.
        if not valid or space>room or cost+reserve_per_output*y>cash:continue
        score=industrial_value(y,finished,output_price,mean,conversion)-cost
        tol=1e-9+1e-12*max(abs(score),abs(best_score))
        choose=best_score==-1e300 or score>best_score+tol
        if abs(score-best_score)<=tol:
            if cost<best_cost-1e-9:choose=True
            elif abs(cost-best_cost)<=1e-9 and y<best_y:choose=True
        if choose:
            best_score=score;best_cost=cost;best_sel=selected;best_q=quantities;best_fees=charges;best_y=y
    return best_sel,best_q,best_fees,best_y,best_score,best_cost


@njit
def industry_steps(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
             bound,finished,output_price,mean,conversion,cash,reserve_per_output):
    """Exact cost-step interval solver, including cash-boundary interior points."""
    nm=len(held);selected=np.full(nm,-1,dtype=np.int64);quantities=np.zeros(nm,dtype=np.int64);charges=np.zeros(nm)
    best_sel=selected.copy();best_q=quantities.copy();best_fees=charges.copy()
    best_cost=0.;best_score=-1e300;best_y=0
    root=(mean*math.log(output_price/conversion)-finished if mean>0 and output_price>0 and conversion>0
          else float(bound) if conversion<=0 and mean>0 else 0.)
    low=0
    while low<=bound:
        high=bound;cost=0.;space=0.;valid=True
        for m in range(nm):
            q=int(math.ceil(max(0.,ratios[m]*low-held[m])/lots[m]))*int(lots[m])
            quantities[m]=q;selected[m]=-1;charges[m]=0.;space+=q*spaces[m]
            high=min(high,int(math.floor((held[m]+q)/ratios[m])))
            if q>0 and q+held[m]>slots[m]:valid=False
            if q==0:continue
            pref=prefs[m];charge=0.
            if pref>=0 and bids[m]>0 and stocks[m,pref]>=bids[m]:charge=fees[m]
            cheapest=1e300;winner=-1
            for s in range(counts[m]):
                if stocks[m,s]<q:continue
                payment=q*prices[m,s]+(charge if s!=pref else 0.)
                if payment<cheapest-1e-9 or (abs(payment-cheapest)<=1e-9 and s==pref):
                    cheapest=payment;winner=s
            if winner<0:valid=False
            else:
                selected[m]=winner;cost+=cheapest;charges[m]=charge if winner!=pref else 0.
        cash_high=high
        if reserve_per_output>0:cash_high=int(math.floor(max(-1.,min(float(cash_high),(cash-cost)/reserve_per_output))))
        if valid and space<=room and cost<=cash and cash_high>=low:
            for side in range(2):
                y=max(low,min(cash_high,int(math.floor(root)) if side==0 else int(math.ceil(root))))
                score=industrial_value(y,finished,output_price,mean,conversion)-cost
                tol=1e-9+1e-12*max(abs(score),abs(best_score))
                choose=best_score==-1e300 or score>best_score+tol
                if abs(score-best_score)<=tol:
                    if cost<best_cost-1e-9:choose=True
                    elif abs(cost-best_cost)<=1e-9 and y<best_y:choose=True
                if choose:
                    best_score=score;best_cost=cost;best_sel=selected.copy();best_q=quantities.copy();best_fees=charges.copy();best_y=y
        low=max(low+1,high+1)
    return best_sel,best_q,best_fees,best_y,best_score,best_cost


@njit
def industry_unit(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
                  bound,finished,output_price,mean,conversion,cash,reserve_per_output):
    """Exact <=2-input, integer-owned-stock, unit-lot supplier/quantity solver.

    For fixed sellers, at most three intervals have constant purchased-input
    slope. All hard constraints become affine, fixed fees are constant, and V is
    concave. Test endpoints and integer neighbors of its stationary point. At
    most 36 seller pairs; quantities are solved jointly, not fixed beforehand.
    """
    nm=len(held);best_sel=np.full(nm,-1,dtype=np.int64);best_q=np.zeros(nm,dtype=np.int64)
    best_fees=np.zeros(nm);best_y=0;best_score=-1e300;best_cost=0.
    cuts=np.empty(nm+2,dtype=np.int64);cuts[0]=0;cuts[nm+1]=bound+1
    for m in range(nm):cuts[m+1]=min(bound+1,int(math.floor(held[m]/ratios[m]))+1)
    cuts=np.sort(cuts)
    # Dominance respects both feasible quantities and the specified tie rule.
    allowed=np.ones_like(stocks,dtype=np.uint8)
    for m in range(nm):
        pf=prefs[m];eligible=pf>=0 and bids[m]>0 and stocks[m,pf]>=bids[m]
        max_need=max(0.,ratios[m]*bound-held[m])
        for s in range(counts[m]):
            fs=fees[m] if eligible and s!=pf else 0.
            for a in range(counts[m]):
                if a==s:continue
                fa=fees[m] if eligible and a!=pf else 0.
                tie_wins=(a==pf or (s!=pf and a<s))
                if (min(stocks[m,a],max_need)>=min(stocks[m,s],max_need) and prices[m,a]<=prices[m,s]
                        and fa<=fs and (prices[m,a]<prices[m,s] or fa<fs or tie_wins)):
                    allowed[m,s]=0;break
    count_b=max(1,counts[1]) if nm==2 else 1
    for a in range(max(1,counts[0])):
        if counts[0]>0 and not allowed[0,a]:continue
        for b in range(count_b):
            if nm==2 and counts[1]>0 and not allowed[1,b]:continue
            chosen=np.array([a,b],dtype=np.int64)
            for section in range(nm+1):
                low=cuts[section];high=cuts[section+1]-1
                if high<low:continue
                coeff=0.;constant=0.;space_coeff=0.;space_constant=0.;valid=True
                charges=np.zeros(nm)
                for m in range(nm):
                    if ratios[m]*low<=held[m]:continue
                    s=chosen[m]
                    if counts[m]<=s:valid=False;break
                    high=min(high,int(math.floor((held[m]+min(stocks[m,s],ratios[m]*bound))/ratios[m])),int(math.floor(slots[m]/ratios[m])))
                    pf=prefs[m]
                    if pf>=0 and bids[m]>0 and stocks[m,pf]>=bids[m] and s!=pf:charges[m]=fees[m]
                    coeff+=ratios[m]*prices[m,s];constant+=charges[m]-held[m]*prices[m,s]
                    space_coeff+=ratios[m]*spaces[m];space_constant-=held[m]*spaces[m]
                if not valid:continue
                if space_coeff>0:high=min(high,int(math.floor((room-space_constant)/space_coeff)))
                if coeff+reserve_per_output>0:high=int(math.floor(max(-1.,min(float(high),(cash-constant)/(coeff+reserve_per_output)))))
                if high<low:continue
                marginal_cost=conversion+coeff
                root=(mean*math.log(output_price/marginal_cost)-finished if mean>0 and output_price>0 and marginal_cost>0
                      else float(high) if marginal_cost<=0 and mean>0 else 0.)
                for side in range(2):
                    y=max(low,min(high,int(math.floor(root)) if side==0 else int(math.ceil(root))))
                    quantities=np.zeros(nm,dtype=np.int64);selected=np.full(nm,-1,dtype=np.int64);cost=0.;used=0.
                    for m in range(nm):
                        q=int(max(0.,ratios[m]*y-held[m]));quantities[m]=q;used+=q*spaces[m]
                        if q>0:selected[m]=chosen[m];cost+=q*prices[m,chosen[m]]+charges[m]
                    if cost+reserve_per_output*y>cash or used>room:continue
                    score=industrial_value(y,finished,output_price,mean,conversion)-cost
                    tol=1e-9+1e-12*max(abs(score),abs(best_score))
                    choose=best_score==-1e300 or score>best_score+tol
                    if abs(score-best_score)<=tol:
                        if cost<best_cost-1e-9:choose=True
                        elif abs(cost-best_cost)<=1e-9:
                            if y<best_y:choose=True
                            elif y==best_y:
                                for m in range(nm):
                                    if selected[m]==best_sel[m]:continue
                                    choose=(selected[m]==prefs[m] or (best_sel[m]!=prefs[m] and selected[m]<best_sel[m]));break
                    if choose:
                        best_sel=selected;best_q=quantities;best_fees=charges.copy();best_y=y;best_cost=cost;best_score=score
    return best_sel,best_q,best_fees,best_y,best_score,best_cost


@njit
def industry_envelope(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
                      bound,finished,output_price,mean,conversion,cash,reserve_per_output):
    """Exact unit-lot lower envelope. All alternatives share one product fee.

    The cheapest stocked alternative changes only at stock boundaries. Its cost
    can cross incumbent cost only at q*(p_inc-p_alt)=fee. Partition at those
    boundaries, select costs once per interval, and solve concave value inside.
    """
    nm=len(held);width=prices.shape[1]
    points=np.empty(2+nm*(3*width+1),dtype=np.int64);npnt=2;points[0]=0;points[1]=bound+1
    for m in range(nm):
        point=int(math.floor(held[m]/ratios[m]))+1
        if 0<point<bound+1:points[npnt]=point;npnt+=1
        pf=prefs[m];eligible=pf>=0 and bids[m]>0 and stocks[m,pf]>=bids[m]
        fee=fees[m] if eligible else 0.
        for s in range(counts[m]):
            point=int(math.floor((held[m]+min(stocks[m,s],ratios[m]*bound))/ratios[m]))+1
            if 0<point<bound+1:points[npnt]=point;npnt+=1
            if pf>=0 and s!=pf and prices[m,pf]>prices[m,s]:
                root=(held[m]+fee/(prices[m,pf]-prices[m,s]))/ratios[m]
                if root>bound+1:continue
                low=int(math.floor(root))
                for point in (low,low+1):
                    if 0<point<bound+1:points[npnt]=point;npnt+=1
    points=np.sort(points[:npnt])
    selected=np.full(nm,-1,dtype=np.int64);quantities=np.zeros(nm,dtype=np.int64);charges=np.zeros(nm)
    best_sel=selected.copy();best_q=quantities.copy();best_fees=charges.copy()
    best_y=0;best_cost=0.;best_score=-1e300
    for section in range(len(points)-1):
        low=points[section];high=points[section+1]-1
        if high<low:continue
        coeff=0.;constant=0.;sp_coeff=0.;sp_constant=0.;valid=True
        for m in range(nm):
            q=int(max(0.,ratios[m]*low-held[m]));selected[m]=-1;charges[m]=0.
            if q==0:continue
            pf=prefs[m];fee=0.
            if pf>=0 and bids[m]>0 and stocks[m,pf]>=bids[m]:fee=fees[m]
            cheapest=1e300;winner=-1
            for s in range(counts[m]):
                if stocks[m,s]<q:continue
                cost=q*prices[m,s]+(fee if s!=pf else 0.)
                if cost<cheapest-1e-9 or (abs(cost-cheapest)<=1e-9 and s==pf):cheapest=cost;winner=s
            if winner<0:valid=False;break
            selected[m]=winner;charges[m]=fee if winner!=pf else 0.
            high=min(high,int(math.floor(slots[m]/ratios[m])))
            coeff+=ratios[m]*prices[m,winner];constant+=charges[m]-held[m]*prices[m,winner]
            sp_coeff+=ratios[m]*spaces[m];sp_constant-=held[m]*spaces[m]
        if not valid:continue
        if sp_coeff>0:high=min(high,int(math.floor((room-sp_constant)/sp_coeff)))
        if coeff+reserve_per_output>0:high=int(math.floor(max(-1.,min(float(high),(cash-constant)/(coeff+reserve_per_output)))))
        if high<low:continue
        marginal=conversion+coeff
        root=(mean*math.log(output_price/marginal)-finished if mean>0 and output_price>0 and marginal>0
              else float(high) if marginal<=0 and mean>0 else 0.)
        for side in range(2):
            y=max(low,min(high,int(math.floor(root)) if side==0 else int(math.ceil(root))))
            cost=0.;space=0.
            for m in range(nm):
                q=int(max(0.,ratios[m]*y-held[m]));quantities[m]=q;space+=q*spaces[m]
                if q>0:cost+=q*prices[m,selected[m]]+charges[m]
            if cost+reserve_per_output*y>cash or space>room:continue
            score=industrial_value(y,finished,output_price,mean,conversion)-cost
            tol=1e-9+1e-12*max(abs(score),abs(best_score))
            choose=best_score==-1e300 or score>best_score+tol
            if abs(score-best_score)<=tol:
                if cost<best_cost-1e-9:choose=True
                elif abs(cost-best_cost)<=1e-9 and y<best_y:choose=True
            if choose:
                best_sel=selected.copy();best_q=quantities.copy();best_fees=charges.copy()
                best_y=y;best_cost=cost;best_score=score
    return best_sel,best_q,best_fees,best_y,best_score,best_cost


@njit
def industry(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
             bound,finished,output_price,mean,conversion,cash,reserve_per_output):
    fast=len(held)<=2 and len(held)>0
    for m in range(len(held)):
        if lots[m]!=1 or held[m]!=math.floor(held[m]) or ratios[m]!=math.floor(ratios[m]):fast=False
    if fast:
        return industry_envelope(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
                             bound,finished,output_price,mean,conversion,cash,reserve_per_output)
    return industry_steps(held,ratios,lots,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
                          bound,finished,output_price,mean,conversion,cash,reserve_per_output)


@njit
def canonical_industry(held,ratios,lots,spaces,slots,room,quotes,bound,finished,price,mean,conversion):
    n=len(held)
    stock=np.empty((n,1))
    for m in range(n):stock[m,0]=ratios[m]*bound+lots[m]
    result=industry(held,ratios,lots,spaces,slots,room,quotes.reshape((n,1)),stock,
        np.ones(n,dtype=np.int64),np.full(n,-1,dtype=np.int64),np.zeros(n),np.zeros(n,dtype=np.int64),
        bound,finished,price,mean,conversion,1e100,0.)
    return result[1],result[3]
