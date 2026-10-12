"""Reference model selection by leaving each published quote level out.

This is retrospective quote validation, not held-out future validation. Incomplete
folds or ties retain the supplied peer path. No private buyer inputs are read.
"""
import copy
import math
import numpy as np
from .forecast import Forecast
from .competitive_forecast import forecast as peer_forecast
from .bounded_response_forecast import forecast as bounded_forecast


def forecast(publication,*,seller,product,quote,payoff_cap,decay,peer_elasticity,
             peer_max_log_quote_distance,max_log_extrapolation,max_quote_folds,fallback):
    if not isinstance(max_quote_folds,int) or isinstance(max_quote_folds,bool) or max_quote_folds<1:
        raise ValueError('positive quote-validation fold budget required')
    common=dict(seller=seller,product=product,quote=quote,payoff_cap=payoff_cap,decay=decay)
    peer=peer_forecast(publication,**common,elasticity=peer_elasticity,
                       max_log_quote_distance=peer_max_log_quote_distance,fallback=fallback)
    bounded=bounded_forecast(publication,**common,max_log_extrapolation=max_log_extrapolation,fallback=peer)
    folds=[]
    def result(chosen,name,reason,losses=None):
        diagnostics=copy.deepcopy(chosen.diagnostics)
        diagnostics.update(regime='validated-quote-response',version=1,modelDiagnostics=copy.deepcopy(chosen.diagnostics),
            validation=dict(selected=name,reason=reason,losses=losses,folds=folds,maxQuoteFolds=max_quote_folds,
                            criterion='Time-weighted absolute item error, withholding whole books at each distinct eligible quote. Strict improvement required; incomplete folds and numerical ties retain peer.',
                            semantics='Past quote-level validation conditional on observed eligibility. Not future holdout, calibrated uncertainty or a production default.'))
        return Forecast(chosen.quantities,chosen.probabilities,chosen.payoff_cap,diagnostics)
    if bounded.diagnostics['fallbackUsed']:
        return result(peer,'peer','bounded-unsupported:'+bounded.diagnostics['fallbackReason'])
    observations=bounded.diagnostics['observations']
    prices=sorted({o['quote'] for o in observations})
    if len(prices)<3:return result(peer,'peer','insufficient-quotes-for-validation')
    if len(prices)>max_quote_folds:return result(peer,'peer','validation-fold-limit')
    errors={'peer':[],'bounded':[]};weights=[]
    for held_quote in prices:
        held=[o for o in observations if o['quote']==held_quote]
        ticks={o['tick'] for o in held}
        # Clone only the eligibility mask: fitting functions read frozen rows,
        # while the caller's publication and all other decisions remain intact.
        training=copy.copy(publication)
        training.local_informed=publication.local_informed.copy()
        withheld=np.isin(publication.rows['ticks'],tuple(ticks))
        training.local_informed[withheld,:]=False
        sentinel=Forecast((0,),(1.,),payoff_cap,dict(seller=seller,product=product,contemplatedQuote=held_quote,
                                                  decisionTick=publication.decision_tick,channel=publication.channel))
        arguments={**common,'quote':held_quote}
        p=peer_forecast(training,**arguments,elasticity=peer_elasticity,
                        max_log_quote_distance=peer_max_log_quote_distance,fallback=sentinel)
        b=bounded_forecast(training,**arguments,max_log_extrapolation=max_log_extrapolation,fallback=sentinel)
        fold=dict(quote=held_quote,withheldTicks=sorted(ticks),observations=len(held),
                  peerFallback=p.diagnostics['fallbackUsed'],boundedFallback=b.diagnostics['fallbackUsed'])
        folds.append(fold)
        if p.diagnostics['rankSignature']!=bounded.diagnostics['rankSignature'] or b.diagnostics['rankSignature']!=bounded.diagnostics['rankSignature']:
            return result(peer,'peer','validation-rank-shift')
        if p.diagnostics['fallbackUsed'] or b.diagnostics['fallbackUsed']:
            fold['boundedFallbackReason']=b.diagnostics.get('fallbackReason')
            return result(peer,'peer','incomplete-validation')
        # Assert the withheld response observations cannot enter either fit.
        assert not any(o['tick'] in ticks for o in p.diagnostics['selectedObservations'])
        assert not any(o['tick'] in ticks for o in b.diagnostics['observations'])
        fold.update(peerMean=p.mean,boundedMean=b.mean)
        for observation in held:
            weight=decay**(publication.decision_tick-1-observation['tick'])
            if weight==0:return result(peer,'peer','validation-weight-underflow')
            truth=min(payoff_cap,observation['sold'])
            weights.append(weight)
            errors['peer'].append(weight*abs(p.mean-truth));errors['bounded'].append(weight*abs(b.mean-truth))
    mass=math.fsum(weights)
    losses={name:math.fsum(values)/mass for name,values in errors.items()}
    tolerance=1e-12*max(1.,*losses.values())
    if losses['bounded']+tolerance<losses['peer']:
        return result(bounded,'bounded','lower-validation-error',losses)
    return result(peer,'peer','peer-retained-by-validation',losses)
