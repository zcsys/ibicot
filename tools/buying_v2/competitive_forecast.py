"""Experimental market-publication comparator with explicit peer exchangeability.

Match price rank in fully observed, unconstrained product books, then use the
nearest observed absolute quote. This is not an identified demand curve, a
stockout model, or a production policy. Rival quotes persist from publication.
"""
import math
import numpy as np
from .forecast import Forecast, PublishedChannel, _adjust, _distribution, _positive_integer


def forecast(publication, *, seller, product, quote, payoff_cap, decay, elasticity,
             max_log_quote_distance, fallback):
    if not isinstance(publication, PublishedChannel) or publication.feedback != 'inquiries':
        raise ValueError('inquiry publication required to exclude constrained books')
    if (not _positive_integer(seller, True) or not _positive_integer(product, True)
            or not _positive_integer(payoff_cap, True) or not math.isfinite(quote) or quote <= 0
            or not math.isfinite(decay) or not 0 < decay <= 1
            or not math.isfinite(elasticity) or elasticity < 0
            or not math.isfinite(max_log_quote_distance) or max_log_quote_distance < 0):
        raise ValueError('invalid identity, quote or explicit comparator parameters')
    if seller < len(publication.products) and publication.products[seller] != product:
        raise ValueError('seller/product identity mismatch')
    expected = dict(seller=int(seller), product=int(product), contemplatedQuote=float(quote),
                    decisionTick=publication.decision_tick, channel=publication.channel)
    if (not isinstance(fallback, Forecast) or fallback.payoff_cap != payoff_cap
            or any(fallback.diagnostics.get(k) != v for k,v in expected.items())):
        raise ValueError('fallback must describe the same decision and payoff cap')
    rows=publication.rows
    candidates=[];eligible_books=0;signature=None
    if rows is not None and len(rows['ticks']):
        # The contemplated seller replaces its last offer, or enters as a new
        # seller. No current/future rival quotes or transactions are inspected.
        rivals=np.flatnonzero((publication.products == product) & rows['offered'][-1].astype(bool))
        rivals=rivals[rivals != seller]
        rival_quotes=rows['quote'][-1,rivals]
        signature=(len(rivals)+1,int(np.sum(rival_quotes < quote)),int(np.sum(rival_quotes == quote)))
        for i,tick in enumerate(rows['ticks']):
            ids=np.flatnonzero((publication.products == product) & rows['offered'][i].astype(bool))
            if len(ids) != signature[0]:continue
            # Even a peer's sold quantity can include fallback from an exhausted
            # rival. Exclude the whole book if any offer is missing information
            # or supply constrained, rather than labeling fallback as rank demand.
            if (not np.all(publication.local_informed[i,ids])
                    or np.any(publication.local_constrained[i,ids])
                    or np.any(rows['sold'][i,ids]+rows['closingStock'][i,ids] <= 0)):
                continue
            eligible_books+=1
            quotes=rows['quote'][i,ids]
            for j,peer in enumerate(ids):
                old=float(quotes[j])
                rank=(len(ids),int(np.sum(quotes < old)),int(np.sum(quotes == old))-1)
                distance=abs(math.log(old)-math.log(quote))
                if rank == signature and distance <= max_log_quote_distance:
                    candidates.append((distance,int(tick),int(peer),old,float(rows['sold'][i,peer])))
    selected=[]
    if candidates:
        nearest=min(x[0] for x in candidates)
        selected=[x for x in candidates if x[0] == nearest]
    diagnostics=dict(expected, version=1, regime='competitive-peer-rank', feedback='inquiries',
        latestPublishedTick=int(rows['ticks'][-1]) if rows is not None and len(rows['ticks']) else None,
        catalog=publication.catalog, eligibleBooks=eligible_books, rankSignature=signature,
        selectedObservations=[dict(tick=t,seller=s,quote=q,sold=y) for _,t,s,q,y in selected],
        parameters=dict(decay=decay,elasticity=elasticity,maxLogQuoteDistance=max_log_quote_distance),
        fallbackUsed=not bool(selected),
        semantics='Peer exchangeability by price rank; nearest quote; lagged rivals held fixed. No guaranteed market share.')
    if not selected:
        diagnostics['fallbackDiagnostics']=fallback.diagnostics.copy()
        return Forecast(fallback.quantities,fallback.probabilities,payoff_cap,diagnostics)
    atoms=[(_adjust(y,q,quote,elasticity,payoff_cap),decay**(publication.decision_tick-1-t))
           for _,t,s,q,y in selected]
    return _distribution(atoms,payoff_cap,diagnostics)
