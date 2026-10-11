"""Unchanged production/price gates, separated from experimental procurement.

Derived from f2b9b47 economy/kernel/numba.py _operate_tier2_nb production block.
Only procurement is moved out; a differential test exercises this block alone.
"""
import math
import numpy as np
from .jit import njit
from economy.kernel import numba as N
from economy.core import model as M


@njit
def manufacture(tick,nfirms,phase,storage,footprint,capacity,conversion,margin_band,overhead,
    line_count,firm_lines,line_product,raw,raw_basis,raw2,basis2,cash,fin,fin_basis,price,unit_cost,
    replacement,made,input_consumed,controller,player_price,rel_price_sum,rel_price_samples,monthly_capacity,
    learn_ticks,learn_profit,learn_sales,learn_previous,learn_direction,learn_demand,learn_step,
    learn_opportunity,learn_potential,obs,min_potential,max_obs,min_opp,aggressiveness,response,going,band,stable_band):
    sinks=0.
    for order in range(nfirms):
        firm=(order+tick*137)%nfirms;nl=line_count[firm];goods_space=storage
        for s in range(nl):goods_space-=footprint[line_product[firm_lines[firm*M.T2_MAX_PRODUCTS_PER_FIRM+s]]]
        for s in range(nl):
            line=firm_lines[firm*M.T2_MAX_PRODUCTS_PER_FIRM+s];pid=line_product[line]
            if N.T2_COMPLEXITY[pid]!=phase:continue
            target=math.floor(goods_space/(2*max(1,nl)*N.T2_COMPLEXITY[pid]))
            planned=max(0,math.floor(min(capacity[pid],target-fin[line])/N.T2_OUTPUT[pid]))
            input_cost=0.
            for gi in range(N.T2_ING_OFF[pid],N.T2_ING_OFF[pid+1]):
                m=N.T2_ING_M[gi];ratio=N.T2_ING_Q[gi]
                if m<4:
                    have=raw[firm*4+m];cost=raw_basis[firm*4+m]
                else:
                    have=raw2[firm*M.NI+m];cost=basis2[firm*M.NI+m]
                planned=min(planned,math.floor(have/ratio));input_cost+=ratio*cost
            planned=min(planned,math.floor(cash[firm]/(conversion[pid]*N.T2_OUTPUT[pid])))
            replacement[line]=input_cost/N.T2_OUTPUT[pid]+conversion[pid]
            planned=N._production_batches(planned,N.T2_OUTPUT[pid],replacement[line],price[line],overhead[firm],margin_band)
            if planned>0:
                for gi in range(N.T2_ING_OFF[pid],N.T2_ING_OFF[pid+1]):
                    m=N.T2_ING_M[gi];q=planned*N.T2_ING_Q[gi];input_consumed[m]+=q
                    if m<4:raw[firm*4+m]-=q
                    else:raw2[firm*M.NI+m]-=q
                quantity=planned*N.T2_OUTPUT[pid];cost=input_cost/N.T2_OUTPUT[pid]+conversion[pid]
                cash[firm]-=quantity*conversion[pid];sinks+=quantity*conversion[pid]
                fin_basis[line]=(fin[line]*fin_basis[line]+quantity*cost)/(fin[line]+quantity)
                fin[line]+=quantity;unit_cost[line]=cost;made[line]=quantity
            previous=price[line]
            if controller[firm] and math.isfinite(player_price[line]):
                price[line]=N._round_cent(min(M.MAX_UNIT_PRICE,max(M.MIN_UNIT_PRICE,player_price[line])))
            else:
                price[line]=N._learned_quote(2,price,learn_ticks,learn_profit,learn_sales,learn_previous,
                    learn_direction,learn_demand,learn_step,learn_opportunity,learn_potential,line,fin[line],tick,
                    obs,min_potential,max_obs,min_opp,going[pid],band,aggressiveness,response)
            rel_price_sum[line]+=1-min(1.,max(0.,price[line]-previous)/max(1e-9,previous*stable_band))
            rel_price_samples[line]+=1;monthly_capacity[line]+=capacity[pid]
    return sinks
