"""Coverage audit for temporal sales evidence, not a fitted demand kernel.

Counts refer to seller-phase pairs. Even selected pairs need not measure latent
or stationary demand: competitors, discovery and buyer resources can change.
"""
import math
import numpy as np
from .seller_history import SellerHistory


def audit(history,*,decision_tick):
    if not isinstance(history,SellerHistory) or not isinstance(decision_tick,int) or isinstance(decision_tick,bool) or decision_tick<1:
        raise ValueError('validated seller history and positive decision tick required')
    channels=[]
    for name in sorted(history.channels):
        history._validate_state(name,history.channels[name])
        full=history.view(name)
        available=full['ticks']<decision_tick
        ticks=full['ticks'][available]
        # A future-added or never-observed column must not enter the historical
        # seller universe merely because it exists in the supplied final file.
        known=np.any(full['offered'][available]!=0,axis=0)
        if not np.any(known):continue
        fields={k:full[k][available][:,known] for k in ('offered','sold','closingStock','quote','shortChecks','discoveries')}
        product=full['product'][known]
        products,inverse=np.unique(product,return_inverse=True)
        n=len(product);shape=(max(0,len(ticks)-1),n)
        remaining=np.ones(shape,dtype=bool)
        masks={}
        def exclude(label,flag):
            masks[label]=remaining & flag
            remaining[masks[label]]=False
        exclude('nonconsecutive',np.broadcast_to((np.diff(ticks)!=1)[:,None],shape))
        offered=fields['offered']!=0
        opening=fields['sold']+fields['closingStock']
        exclude('unoffered',~(offered[:-1]&offered[1:]))
        exclude('emptyOpening',(opening[:-1]<full['lot'])|(opening[1:]<full['lot']))
        constrained=(fields['shortChecks']>0)|(fields['closingStock']<full['lot'])
        exclude('recordedStockConstraint',constrained[:-1]|constrained[1:])
        exclude('changedQuote',fields['quote'][:-1]!=fields['quote'][1:])
        masks['comparable']=remaining.copy()
        positive=fields['sold']>0
        for a in range(2):
            for b in range(2):masks[f'transition{a}{b}']=remaining&(positive[:-1]==bool(a))&(positive[1:]==bool(b))
        masks['sameOpeningStock']=remaining&(opening[:-1]==opening[1:])
        masks['bothDiscovered']=remaining&(fields['discoveries'][:-1]>0)&(fields['discoveries'][1:]>0)
        by_seller={k:v.sum(axis=0,dtype=np.int64) for k,v in masks.items()}
        origin_zero=by_seller['transition00']+by_seller['transition01']
        origin_positive=by_seller['transition10']+by_seller['transition11']
        def summarize(selection):
            counts={k:int(v[selection].sum()) for k,v in by_seller.items()}
            matrix=[[counts[f'transition{a}{b}'] for b in range(2)] for a in range(2)]
            rows=[sum(row) for row in matrix]
            cols=[sum(matrix[i][j] for i in range(2)) for j in range(2)]
            denominator=math.prod(rows+cols)
            return dict(sellers=int(np.count_nonzero(selection)),candidatePairs=shape[0]*int(np.count_nonzero(selection)),
                exclusions={k:counts[k] for k in ('nonconsecutive','unoffered','emptyOpening','recordedStockConstraint','changedQuote')},
                comparablePairs=counts['comparable'],sameOpeningStockPairs=counts['sameOpeningStock'],bothDiscoveredPairs=counts['bothDiscovered'],
                sellersWithComparablePairs=int(np.count_nonzero(by_seller['comparable'][selection])),
                sellersWithBothOriginStates=int(np.count_nonzero((origin_zero[selection]>0)&(origin_positive[selection]>0))),
                transitionCounts=matrix,conditionalPositiveSaleProbability=[matrix[i][1]/rows[i] if rows[i] else None for i in range(2)],
                pooledBinaryCorrelation=(matrix[0][0]*matrix[1][1]-matrix[0][1]*matrix[1][0])/math.sqrt(denominator) if denominator else None)
        totals=summarize(np.ones(n,dtype=bool))
        assert sum(totals['exclusions'].values())+totals['comparablePairs']==totals['candidatePairs']
        channels.append(dict(channel=name,firstTick=int(ticks[0]) if len(ticks) else None,lastTick=int(ticks[-1]) if len(ticks) else None,
                             lot=full['lot'],totals=totals,products=[dict(product=int(p),**summarize(inverse==i)) for i,p in enumerate(products)]))
    return dict(version=1,decisionTick=decision_tick,channels=channels,
                scope='Descriptive consecutive seller-phase sales at unchanged own quote, with no recorded stock constraint. Exclusions are disjoint in reported order. Universe: sellers offered at least once before decision tick in retained history. Binary states are zero/positive sales, not latent demand. Pooled transitions can reflect seller heterogeneity; no calibrated temporal kernel or causal claim.')
