"""Experimental bounded own-quote response, conditional on peer-rank matching.

Fits 1/mean_sales = intercept + slope*quote at distinct observed quotes. This
functional family and residual transport are hypotheses, not adopted demand.
"""
import math
import numpy as np
from .forecast import Forecast,PublishedChannel,_distribution,_positive_integer


def forecast(publication,*,seller,product,quote,payoff_cap,decay,max_log_extrapolation,fallback):
    if not isinstance(publication,PublishedChannel) or publication.feedback!='inquiries':
        raise ValueError('inquiry publication required')
    if (not _positive_integer(seller,True) or not _positive_integer(product,True) or not _positive_integer(payoff_cap,True)
            or not math.isfinite(quote) or quote<=0 or not math.isfinite(decay) or not 0<decay<=1
            or not math.isfinite(max_log_extrapolation) or max_log_extrapolation<0):
        raise ValueError('invalid explicit bounded-response parameters')
    if seller<len(publication.products) and publication.products[seller]!=product:raise ValueError('seller/product mismatch')
    expected=dict(seller=int(seller),product=int(product),contemplatedQuote=float(quote),decisionTick=publication.decision_tick,channel=publication.channel)
    if not isinstance(fallback,Forecast) or fallback.payoff_cap!=payoff_cap or any(fallback.diagnostics.get(k)!=v for k,v in expected.items()):
        raise ValueError('fallback must describe the same decision and payoff cap')
    rows=publication.rows;observations=[];eligible=0;signature=None
    if rows is not None and len(rows['ticks']):
        rivals=np.flatnonzero((publication.products==product)&rows['offered'][-1].astype(bool));rivals=rivals[rivals!=seller]
        rival_quotes=rows['quote'][-1,rivals]
        signature=(len(rivals)+1,int(np.sum(rival_quotes<quote)),int(np.sum(rival_quotes==quote)))
        for i,tick in enumerate(rows['ticks']):
            ids=np.flatnonzero((publication.products==product)&rows['offered'][i].astype(bool))
            if (len(ids)!=signature[0] or not np.all(publication.local_informed[i,ids])
                    or np.any(publication.local_constrained[i,ids])
                    or np.any(rows['sold'][i,ids]+rows['closingStock'][i,ids]<=0)):continue
            eligible+=1;quotes=rows['quote'][i,ids]
            for j,peer in enumerate(ids):
                old=float(quotes[j])
                rank=(len(ids),int(np.sum(quotes<old)),int(np.sum(quotes==old))-1)
                if rank==signature:
                    observations.append((int(tick),int(peer),old,float(rows['sold'][i,peer])))
    diagnostics=dict(expected,version=1,regime='competitive-bounded-response',feedback='inquiries',catalog=publication.catalog,
        latestPublishedTick=int(rows['ticks'][-1]) if rows is not None and len(rows['ticks']) else None,
        rankSignature=signature,eligibleBooks=eligible,
        observations=[dict(tick=t,seller=s,quote=q,sold=y) for t,s,q,y in observations],
        parameters=dict(decay=decay,maxLogExtrapolation=max_log_extrapolation),
        semantics='Fitted bounded quote-response family conditional on peer exchangeability and lagged rival quotes; empirical residual transport is not calibrated uncertainty.')
    def reject(reason):
        return Forecast(fallback.quantities,fallback.probabilities,payoff_cap,
                        dict(diagnostics,fallbackUsed=True,fallbackReason=reason,fallbackDiagnostics=fallback.diagnostics.copy()))
    if not observations:return reject('no-eligible-observations')
    if any(y<=0 for _,_,_,y in observations):return reject('nonpositive-sales-observation')
    grouped={};weighted=[]
    for tick,peer,old,sold in observations:
        weight=decay**(publication.decision_tick-1-tick)
        if weight==0:return reject('decay-weight-underflow')
        grouped.setdefault(old,[]).append((sold,weight));weighted.append((old,sold,weight))
    if len(grouped)<2:return reject('insufficient-quote-variation')
    prices=sorted(grouped)
    distance=max(0.,math.log(prices[0])-math.log(quote),math.log(quote)-math.log(prices[-1]))
    if distance>max_log_extrapolation:return reject('quote-outside-declared-support')
    levels=[(p,math.fsum(y*w for y,w in grouped[p])/math.fsum(w for _,w in grouped[p]),math.fsum(w for _,w in grouped[p])) for p in prices]
    # Scaled centered regression avoids subtracting large uncentered moments.
    xs=max(prices);ys=max(1./y for _,y,_ in levels);mass=math.fsum(w for _,_,w in levels)
    xbar=math.fsum(w*(p/xs) for p,_,w in levels)/mass
    ybar=math.fsum(w*((1./y)/ys) for _,y,w in levels)/mass
    variance=math.fsum(w*(p/xs-xbar)**2 for p,_,w in levels)
    if variance<=0 or not math.isfinite(variance):return reject('unresolved-quote-variation')
    slope_scaled=math.fsum(w*(p/xs-xbar)*((1./y)/ys-ybar) for p,y,w in levels)/variance
    intercept=(ybar-slope_scaled*xbar)*ys;slope=slope_scaled*ys/xs
    if not math.isfinite(intercept) or intercept<=0 or not math.isfinite(slope) or slope<0:return reject('inadmissible-fitted-response')
    ceiling=1./intercept
    denominator=intercept+slope*quote
    if not math.isfinite(ceiling) or not math.isfinite(denominator) or denominator<=0:return reject('nonfinite-fitted-response')
    atoms=[]
    for old,sold,weight in weighted:
        previous=intercept+slope*old
        if not math.isfinite(previous) or previous<=0:return reject('nonfinite-fitted-response')
        log_q=math.log(sold)+math.log(previous)-math.log(denominator)
        quantity=0. if payoff_cap==0 else (float(payoff_cap) if log_q>=math.log(payoff_cap) else math.exp(log_q))
        atoms.append((quantity,weight))
    diagnostics.update(fallbackUsed=False,fallbackReason=None,
                       fit=dict(intercept=intercept,slope=slope,zeroPriceMean=ceiling,
                                meanAtQuote=1./denominator,distinctQuotes=len(levels),observations=len(observations),
                                trainingMinimumQuote=prices[0],trainingMaximumQuote=prices[-1]))
    return _distribution(atoms,payoff_cap,diagnostics)
