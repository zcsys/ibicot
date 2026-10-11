"""Compiled experimental order submission and atomic procurement settlement."""
import math
import numpy as np
from .jit import njit
from .solvers import sample_distinct, canonical_industry, industry, retail, marginal_values, demand_quantity
from .scalar_solver import solve as scalar_industry
from economy.core.rng import random_

# Per-buyer events: samples, ingredient orders, partial alternative fills,
# preference changes, fee-bearing orders, fees, retained incumbents, submitted
# units, supplied units, unfilled units, estimated same-fill fee-free savings.
EVENT_FIELDS=('samples','orders','alternativePartial','preferenceChanges','feeOrders','fees',
              'retained','requested','supplied','unfilled','forgoneGoodsSavings','retryUnits',
              'cashLimitedUnits','unfundedUnits','feeWaivedUnavailable','canonicalUnits')


@njit
def procure(seed,tick,tier,order,phase,line_for_firm,line_product,complexity,ing_off,ing_id,ing_qty,
            input_space,capacity,footprint,storage,conversion,overhead,horizon,forecast,
            buyer_cash,buyer_raw,buyer_basis,buyer_raw2,buyer_basis2,buyer_fin,buyer_price,
            preferences,ninputs,lot,fee_multiple,fee_reference,
            supplier_ids,supplier_off,supplier_owner,stock,price,reliability,basis,supplier_cash,
            sold,revenue,cogs,demand,attempts,checks,available,switch_income,switch_expense,
            bought,last_buy,mat_spend,mat_orders,loyalty_orders,loyalty_fees,
            market_requested,market_supplied,market_value,local_requests,events,trace,
            search_count,fee_enabled,inventory_feedback,quote_first,value_scale,skip_redundant):
    held=np.empty(2);ratios=np.empty(2);lots=np.full(2,float(lot));spaces=np.empty(2);slots=np.empty(2)
    prices=np.empty((2,search_count+1));stocks=np.empty((2,search_count+1))
    ids=np.empty((2,search_count+1),dtype=np.int64);counts=np.zeros(2,dtype=np.int64)
    prefs=np.full(2,-1,dtype=np.int64);fees=np.zeros(2);quotes=np.zeros(2)
    bids=np.zeros(2,dtype=np.int64);selected=np.full(2,-1,dtype=np.int64);quantities=np.zeros(2,dtype=np.int64);charges=np.zeros(2)
    intended_selected=np.full(2,-1,dtype=np.int64);intended_quantity=np.zeros(2,dtype=np.int64)
    unlimited=np.full_like(stocks,1e15);canonical_prices=np.zeros((2,1))
    one_counts=np.ones(2,dtype=np.int64);no_prefs=np.full(2,-1,dtype=np.int64);no_fees=np.zeros(2);no_bids=np.zeros(2,dtype=np.int64)
    points=np.empty(2+2*(3*(search_count+1)+1),dtype=np.int64)
    for firm in order:
        line=line_for_firm[firm];pid=line_product[line];cx=complexity[pid]
        if phase>=0 and cx!=phase:continue
        begin=ing_off[pid];end=ing_off[pid+1];nm=end-begin
        if nm==0:continue
        if nm>2:raise ValueError('compiled research buyer requires at most two distinct ingredients')
        goods_space=storage[firm]-footprint[pid]
        used=buyer_fin[line]*cx
        for m in range(ninputs):
            used+=(buyer_raw[firm*4+m] if m<4 else buyer_raw2[firm*ninputs+m])*input_space[m]
        room=max(0.,goods_space-used)
        for k in range(nm):
            prefs[k]=-1;fees[k]=0.
            m=ing_id[begin+k];ratios[k]=ing_qty[begin+k];spaces[k]=input_space[m]
            held[k]=buyer_raw[firm*4+m] if m<4 else buyer_raw2[firm*ninputs+m]
            slots[k]=goods_space*ratios[k]/(2*cx)
            pref=preferences[firm*ninputs+m]
            if tier==1 and pref>=0:pref=pref*4+m
            candidates=sample_distinct(supplier_ids[supplier_off[m]:supplier_off[m+1]],pref,
                                       seed,tick,firm+(10000000 if tier==1 else 20000000),m,search_count)
            counts[k]=len(candidates);events[firm,0]+=len(candidates)
            for s in range(len(candidates)):
                seller=candidates[s];ids[k,s]=seller;prices[k,s]=price[seller];stocks[k,s]=math.floor(stock[seller])
                if seller==pref:prefs[k]=s
            if prefs[k]>=0:
                quotes[k]=price[pref]
                mult=fee_multiple[0] if tier==1 else fee_multiple[cx-3]
                fees[k]=mult*fee_reference*(1+min(1.,max(0.,reliability[pref]))) if fee_enabled else 0.
            elif len(candidates)>0:
                ordered=np.sort(prices[k,:len(candidates)])
                n=len(ordered);quotes[k]=(ordered[(n-1)//2]+ordered[n//2])/2
            else:quotes[k]=1e100
        bound=int(horizon*capacity[pid]);finished=buyer_fin[line] if inventory_feedback else 0.
        mean=max(0.,horizon*forecast[line]);value_price=buyer_price[line]*value_scale
        opening_cash=buyer_cash[firm]
        decision_cost=conversion[pid]+max(0.,overhead[firm])/capacity[pid]
        if tier==2:
            for k in range(nm):canonical_prices[k,0]=quotes[k]
            canonical=scalar_industry(nm,held,ratios,spaces,slots,room,canonical_prices,unlimited,one_counts,no_prefs,no_fees,no_bids,
                bound,finished,value_price,mean,decision_cost,1e100,0.,points)
            bids[0]=canonical[2];bids[1]=canonical[3]
        else:
            bids,canonical_y=canonical_industry(held[:nm],ratios[:nm],lots[:nm],spaces[:nm],slots[:nm],room,quotes[:nm],bound,
                                               finished,value_price,mean,decision_cost)
        # Availability/fees are frozen using this buyer's live stock, before solving.
        for k in range(nm):
            events[firm,15]+=bids[k]
            if prefs[k]>=0 and bids[k]>0 and stocks[k,prefs[k]]<bids[k]:events[firm,14]+=1
            if prefs[k]<0 or bids[k]<=0 or stocks[k,prefs[k]]<bids[k]:fees[k]=0.
            if quote_first:
                winner=-1;least=1e300
                for s in range(counts[k]):
                    cost=prices[k,s]+(fees[k]/max(1,bids[k]) if s!=prefs[k] else 0.)
                    if cost<least:least=cost;winner=s
                for s in range(counts[k]):
                    if s!=winner:prices[k,s]=1e100
        # An unconstrained optimum that satisfies an added constraint remains
        # optimal. Reuse it only after checking feasibility of the whole basket.
        # A conservative upper bound proves when cash cannot bind any plan.
        cash_bound=conversion[pid]*bound
        for k in range(nm):
            largest=0.
            for s in range(counts[k]):largest=max(largest,prices[k,s])
            cash_bound+=math.ceil(max(0.,ratios[k]*bound-held[k])/lot)*lot*largest+fees[k]
        if tier==2:
            intended=scalar_industry(nm,held,ratios,spaces,slots,room,prices,unlimited,counts,prefs,fees,bids,
                bound,finished,value_price,mean,decision_cost,buyer_cash[firm],conversion[pid],points)
            feasible=skip_redundant
            if intended[2]>0 and stocks[0,intended[0]]<intended[2]:feasible=False
            if nm==2 and intended[3]>0 and stocks[1,intended[1]]<intended[3]:feasible=False
            actual=intended
            if not feasible:
                actual=scalar_industry(nm,held,ratios,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
                    bound,finished,value_price,mean,decision_cost,buyer_cash[firm],conversion[pid],points)
            unfunded=intended
            if not skip_redundant or buyer_cash[firm]<cash_bound:
                unfunded=scalar_industry(nm,held,ratios,spaces,slots,room,prices,unlimited,counts,prefs,fees,bids,
                    bound,finished,value_price,mean,decision_cost,1e100,conversion[pid],points)
            events[firm,12]+=max(0,unfunded[2]-intended[2])+max(0,unfunded[3]-intended[3])
            events[firm,13]+=unfunded[2]+unfunded[3]
            selected[0]=actual[0];selected[1]=actual[1];quantities[0]=actual[2];quantities[1]=actual[3]
            charges[0]=actual[4];charges[1]=actual[5];plan=actual[6];score=actual[7];total_cost=actual[8]
            intended_selected[0]=intended[0];intended_selected[1]=intended[1]
            intended_quantity[0]=intended[2];intended_quantity[1]=intended[3]
        else:
            intended_arrays=industry(held[:nm],ratios[:nm],lots[:nm],spaces[:nm],slots[:nm],room,prices[:nm],unlimited[:nm],counts[:nm],prefs[:nm],fees[:nm],bids,
                bound,finished,value_price,mean,decision_cost,buyer_cash[firm],conversion[pid])
            feasible=skip_redundant
            for k in range(nm):
                if intended_arrays[1][k]>0 and stocks[k,intended_arrays[0][k]]<intended_arrays[1][k]:feasible=False
            actual_arrays=intended_arrays
            if not feasible:
                actual_arrays=industry(held[:nm],ratios[:nm],lots[:nm],spaces[:nm],slots[:nm],room,prices[:nm],stocks[:nm],counts[:nm],prefs[:nm],fees[:nm],bids,
                    bound,finished,value_price,mean,decision_cost,buyer_cash[firm],conversion[pid])
            unfunded_arrays=intended_arrays
            if not skip_redundant or buyer_cash[firm]<cash_bound:
                unfunded_arrays=industry(held[:nm],ratios[:nm],lots[:nm],spaces[:nm],slots[:nm],room,prices[:nm],unlimited[:nm],counts[:nm],prefs[:nm],fees[:nm],bids,
                    bound,finished,value_price,mean,decision_cost,1e100,conversion[pid])
            for k in range(nm):
                events[firm,12]+=max(0,unfunded_arrays[1][k]-intended_arrays[1][k])
                events[firm,13]+=unfunded_arrays[1][k]
            selected,quantities,charges,plan,score,total_cost=actual_arrays
            intended_selected=intended_arrays[0];intended_quantity=intended_arrays[1]
        for k in range(nm):
            m=ing_id[begin+k];q=quantities[k];seller=ids[k,selected[k]] if selected[k]>=0 else -1
            request=max(intended_quantity[k],q)
            recipient=ids[k,intended_selected[k]] if intended_selected[k]>=0 else seller
            if request>0 and recipient>=0:
                market_requested[m]+=request;local_requests[recipient]+=request
                demand[recipient]+=request;attempts[recipient]+=1;checks[recipient]+=1
                if stock[recipient]>=request:available[recipient]+=1
            events[firm,7]+=request;events[firm,8]+=q;events[firm,9]+=max(0,request-q)
            if q>0 and seller!=recipient:events[firm,11]+=q
            if firm%997==0:
                row=trace[firm//997,k]
                row[0]=tick;row[1]=m;row[2]=preferences[firm*ninputs+m];row[3]=seller
                row[4]=bids[k];row[5]=request;row[6]=q;row[7]=q*price[seller] if q else 0.
                row[8]=charges[k];row[9]=row[2];row[10]=plan;row[11]=score;row[12]=mean
                row[13]=firm;row[14]=line;row[15]=pid;row[16]=held[k];row[17]=ratios[k]
                row[18]=lot;row[19]=spaces[k];row[20]=slots[k];row[21]=room;row[22]=opening_cash
                row[23]=finished;row[24]=value_price;row[25]=decision_cost;row[26]=conversion[pid]
                row[27]=bound;row[28]=prefs[k];row[29]=fees[k];row[30]=counts[k];row[31]=quotes[k]
                row[32]=recipient;row[33]=intended_quantity[k];row[34]=nm;row[35]=total_cost
                for s in range(counts[k]):
                    row[40+3*s]=ids[k,s];row[41+3*s]=prices[k,s];row[42+3*s]=stocks[k,s]
            if q<=0:continue
            pref=preferences[firm*ninputs+m];old_pref=pref
            pref_global=pref*4+m if tier==1 and pref>=0 else pref
            payment=q*price[seller];charge=charges[k]
            raw_idx=firm*(4 if m<4 else ninputs)+m
            if m<4:
                old=buyer_raw[raw_idx]
                buyer_basis[raw_idx]=(old*buyer_basis[raw_idx]+payment)/(old+q)
                buyer_raw[raw_idx]+=q
            else:
                old=buyer_raw2[raw_idx]
                buyer_basis2[raw_idx]=(old*buyer_basis2[raw_idx]+payment)/(old+q)
                buyer_raw2[raw_idx]+=q
            buyer_cash[firm]-=payment+charge;supplier_cash[supplier_owner[seller]]+=payment
            stock[seller]-=q;sold[seller]+=q;revenue[seller]+=payment;cogs[seller]+=q*basis[seller]
            bought[firm]+=q;market_supplied[m]+=q;market_value[m]+=payment
            if tier==1:last_buy[firm*4+m]=price[seller]
            else:mat_spend[cx-3]+=payment;mat_orders[cx-3]+=1
            if charge>0:
                supplier_cash[supplier_owner[pref_global]]+=charge
                switch_income[supplier_owner[pref_global]]+=charge;switch_expense[firm]+=charge
                loyalty_orders[tier-1]+=1;loyalty_fees[tier-1]+=charge
            if bids[k]>0 and q>=bids[k]:preferences[firm*ninputs+m]=seller//4 if tier==1 else seller
            events[firm,1]+=1
            if seller!=pref_global and q<bids[k]:events[firm,2]+=1
            if preferences[firm*ninputs+m]!=old_pref:events[firm,3]+=1
            if charge>0:events[firm,4]+=1
            events[firm,5]+=charge
            if old_pref>=0 and preferences[firm*ninputs+m]==old_pref:events[firm,6]+=1
            # Same realized fill, holding availability fixed; excludes utility and future effects.
            best_goods=payment
            for s in range(counts[k]):
                if stocks[k,s]>=q:best_goods=min(best_goods,q*prices[k,s])
            events[firm,10]+=max(0.,payment-best_goods)
            if firm%997==0:
                trace[firm//997,k,0]=tick;trace[firm//997,k,1]=m;trace[firm//997,k,2]=old_pref
                trace[firm//997,k,3]=seller;trace[firm//997,k,4]=bids[k];trace[firm//997,k,5]=request
                trace[firm//997,k,6]=q;trace[firm//997,k,7]=payment;trace[firm//997,k,8]=charge
                trace[firm//997,k,9]=preferences[firm*ninputs+m];trace[firm//997,k,10]=plan
                trace[firm//997,k,11]=score;trace[firm//997,k,12]=mean


@njit
def clear_retail(seed,tick,n,activation,search_count,lm,premium,valuation,complexity,
    products,preferences,last_market,last_supplier,last_q,last_fill,qmax,choke,eta,
    potential,active,fulfilled,price_lost,stock_unmet,ids,off,owners,stock,prices,rel,
    cash,last_sale,sold,revenue,cogs,basis,demand,attempts,available,opportunities,potential_orders,
    switching_income,loyalty_orders,loyalty_fees,local_requests,events,trace,fee_enabled,reverse,market_offset,skip_redundant):
    orders=0;filled=0;activated=0;payments=0.;purchases=0
    for order in range(n):
        buyer=n-1-order if reverse else order
        if random_(seed,tick,buyer+2000000)>=activation:continue
        activated+=1;market=products[buyer]-market_offset;latent=float(qmax[buyer])
        u=random_(seed,tick,buyer+7000000);half=valuation[market]*choke[buyer]*(1+premium*(complexity[market]-1))
        values=marginal_values(latent,half,eta[buyer],u)
        pot=int(math.floor(latent)+(1 if u<latent-math.floor(latent) else 0))
        global_market=market+market_offset;potential[global_market]+=pot;potential_orders[market]+=1
        candidates=sample_distinct(ids[off[market]:off[market+1]],preferences[buyer],seed,tick,buyer+30000000,market,search_count)
        n_candidates=len(candidates)
        if n_candidates==0:continue
        quotes=np.empty(n_candidates);stocks=np.empty(n_candidates);pref=-1
        for k in range(n_candidates):
            seller=candidates[k];quotes[k]=prices[seller];stocks[k]=math.floor(stock[seller])
            if seller==preferences[buyer]:pref=k
        if pref>=0:canonical_price=quotes[pref]
        else:
            ordered=np.sort(quotes);canonical_price=(ordered[(n_candidates-1)//2]+ordered[n_candidates//2])/2
        bid=demand_quantity(latent,half,eta[buyer],canonical_price,u)
        fee=0.
        if pref>=0 and fee_enabled and bid>0 and stocks[pref]>=bid:
            fee=lm*valuation[market]*(1+min(1.,max(0.,rel[candidates[pref]])))
        intended=retail(values,quotes,np.full(n_candidates,1e15),pref,bid,fee,1e100)
        feasible=skip_redundant
        for k in range(n_candidates):
            if intended[0][k]>stocks[k]:feasible=False
        actual=intended if feasible else retail(values,quotes,stocks,pref,bid,fee,1e100)
        allocations,score,goods,charge,new_pref=actual
        quantity=int(allocations.sum());requested=max(quantity,int(intended[0].sum()))
        primary=-1;nsellers=0
        for k in range(n_candidates):
            seller=candidates[k];wanted=intended[0][k]
            if wanted>0:
                local_requests[seller]+=wanted;demand[seller]+=wanted;attempts[seller]+=1
                if stocks[k]>=wanted:available[seller]+=1
            q=allocations[k]
            if q<=0:continue
            if primary<0:primary=seller
            nsellers+=1;payment=q*quotes[k]
            stock[seller]-=q;cash[owners[seller]]+=payment;last_sale[owners[seller]]=tick
            sold[seller]+=q;revenue[seller]+=payment;cogs[seller]+=q*basis[seller]
        old=preferences[buyer]
        if new_pref>=0:preferences[buyer]=candidates[new_pref]
        if charge>0:
            incumbent=candidates[pref];cash[owners[incumbent]]+=charge;switching_income[owners[incumbent]]+=charge
            loyalty_orders[2]+=1;loyalty_fees[2]+=charge
        last_market[buyer]=global_market;last_supplier[buyer]=primary;last_q[buyer]=requested;last_fill[buyer]=quantity
        active[global_market]+=requested;fulfilled[global_market]+=quantity
        price_lost[global_market]+=max(0,pot-requested);stock_unmet[global_market]+=max(0,requested-quantity)
        if requested>0:orders+=1;opportunities[market]+=1
        if quantity>0:purchases+=1;payments+=goods+charge;filled+=int(quantity>=requested)
        e=events[market];e[0]+=n_candidates;e[1]+=int(quantity>0)
        outside=quantity-(allocations[pref] if pref>=0 else 0)
        for k in range(n_candidates):
            if k!=pref and 0<allocations[k]<bid:e[2]+=1
        e[3]+=int(old!=preferences[buyer]);e[4]+=int(charge>0);e[5]+=charge
        e[6]+=int(quantity>0 and old>=0 and old==preferences[buyer]);e[7]+=requested;e[8]+=quantity;e[9]+=max(0,requested-quantity)
        if quantity>0 and fee>0 and charge==0:
            # With no payable fee the selected quantity already has minimum
            # goods cost. Only retained-incumbent baskets can forgo a saving.
            left=quantity;minimum_goods=0.
            for k in np.argsort(quotes):
                q=min(left,int(stocks[k]));minimum_goods+=q*quotes[k];left-=q
                if left==0:break
            e[10]+=max(0.,goods-minimum_goods)
        for k in range(n_candidates):e[11]+=max(0,allocations[k]-intended[0][k])
        e[13]+=requested;e[14]+=int(pref>=0 and bid>0 and stocks[pref]<bid);e[15]+=bid
        if buyer%10007==0:
            row=buyer//10007;trace[row,0]=tick;trace[row,1]=market;trace[row,2]=old;trace[row,3]=primary
            trace[row,4]=bid;trace[row,5]=requested;trace[row,6]=quantity;trace[row,7]=goods
            trace[row,8]=charge;trace[row,9]=preferences[buyer];trace[row,10]=nsellers;trace[row,11]=score
            trace[row,12]=latent;trace[row,13]=half;trace[row,14]=eta[buyer];trace[row,15]=u
            trace[row,16]=pref;trace[row,17]=fee;trace[row,18]=n_candidates;trace[row,19]=buyer
            for k in range(n_candidates):
                trace[row,20+4*k]=candidates[k];trace[row,21+4*k]=quotes[k]
                trace[row,22+4*k]=stocks[k];trace[row,23+4*k]=allocations[k]
    return orders,filled,activated,payments,purchases
