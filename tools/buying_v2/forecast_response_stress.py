"""Controlled response-family stress fixtures; not a whole-economy forecast test."""
import math
import numpy as np
from economy.core import model as M
from economy.core.rng import random_
from .forecast_probe import world,phase
from .forecast import PublishedChannel,ForecastParameters
from .seller_history import SellerHistory
from .competitive_forecast import forecast as peer
from .bounded_response_forecast import forecast


def install_profile(w,cfg,groups):
    """Evaluator-only private buyer parameters; never passed to a forecast."""
    if not groups or any(not isinstance(g['count'],int) or isinstance(g['count'],bool) or g['count']<1 for g in groups):
        raise ValueError('positive whole buyer-group sizes required')
    if sum(g['count'] for g in groups)!=cfg['distributorCount']:raise ValueError('buyer groups must cover active population exactly')
    if any(not math.isfinite(g[k]) or g[k]<=0 for g in groups for k in ('quantity','halfPrice','elasticity')):
        raise ValueError('positive finite buyer profile parameters required')
    valuation=M.procurement_profile(M.T2_PRODUCTS[0],cfg,M.reference_tier2_cost(M.T2_PRODUCTS[0],cfg))['valuation']
    start=0
    for g in groups:
        end=start+g['count']
        w.distributorQMax[start:end]=g['quantity'];w.distributorEta[start:end]=g['elasticity']
        w.distributorChoke[start:end]=g['halfPrice']/valuation
        start=end


def expected_focal_sales(groups,seed,tick,quote,rivals):
    """Independent declared-curve calculation in this all-discovered, no-fee fixture."""
    if quote==min(rivals):raise ValueError('tie allocation is outside this analytical check')
    if quote>min(rivals):return 0
    total=0;buyer=0
    for g in groups:
        q=g['quantity']/(1+(quote/g['halfPrice'])**g['elasticity'])
        for _ in range(g['count']):
            total+=math.floor(q)+int(random_(seed,tick,buyer+7000000)<q%1);buyer+=1
    return total


def evaluate(spec,*,compiled=True):
    parameters=ForecastParameters(**spec['fallbackParameters']);rows=[]
    validate_response=spec.get('validateResponse',False)
    if not isinstance(validate_response,bool):raise ValueError('response validation flag must be boolean')
    # Ample inventory must cover all potential demand, even before price reduces it.
    if any(sum(g['count']*math.ceil(g['quantity']) for g in groups)>spec['ampleStock'] for groups in spec['buyerProfiles'].values()):
        raise ValueError('stress fixture requires ample stock for aggregate potential demand')
    for name,groups in spec['buyerProfiles'].items():
        for seed in spec['seeds']:
            cfg,w=world(spec,seed);install_profile(w,cfg,groups);history=SellerHistory(len(spec['trainingQuotes']))
            for tick,quote in enumerate(spec['trainingQuotes'],1):
                obs=phase(w,cfg,tick,(spec['ampleStock'],)*3,(quote,*spec['rivalQuotes']),compiled)
                assert obs['sold'][0]==expected_focal_sales(groups,seed,tick,quote,spec['rivalQuotes'])
                history.record('retail',tick,np.zeros(3,dtype=np.int64),np.arange(3),np.ones(3),obs['opening'],obs['closing'],obs['quote'],obs['sold'],obs['exposure'])
            tick=len(spec['trainingQuotes'])+1;publication=PublishedChannel(history,'retail',tick)
            for quote in spec['targetQuotes']:
                local=publication.forecast('local',seller=0,product=0,quote=quote,payoff_cap=spec['ampleStock'],market_size=3,parameters=parameters)
                previous=peer(publication,seller=0,product=0,quote=quote,payoff_cap=spec['ampleStock'],decay=spec['decay'],elasticity=spec['peerElasticity'],max_log_quote_distance=spec['peerMaxLogQuoteDistance'],fallback=local)
                fitted=forecast(publication,seller=0,product=0,quote=quote,payoff_cap=spec['ampleStock'],decay=spec['decay'],max_log_extrapolation=spec['maxLogExtrapolation'],fallback=previous)
                validated=None
                if validate_response:
                    from .validated_response_forecast import forecast as select_forecast
                    validated=select_forecast(publication,seller=0,product=0,quote=quote,payoff_cap=spec['ampleStock'],
                        decay=spec['decay'],peer_elasticity=spec['peerElasticity'],peer_max_log_quote_distance=spec['peerMaxLogQuoteDistance'],
                        max_log_extrapolation=spec['maxLogExtrapolation'],max_quote_folds=spec['maxQuoteFolds'],fallback=local)
                actual=phase(w,cfg,tick,(spec['ampleStock'],)*3,(quote,*spec['rivalQuotes']),compiled)
                expected=expected_focal_sales(groups,seed,tick,quote,spec['rivalQuotes'])
                assert actual['sold'][0]==expected
                rows.append(dict(profile=name,seed=seed,quote=quote,actualSales=actual['sold'].tolist(),analyticalFocalSales=expected,
                                 peerMean=previous.mean,boundedMean=fitted.mean,diagnostics=fitted.diagnostics))
                if validated is not None:
                    rows[-1].update(validatedMean=validated.mean,validationDiagnostics=validated.diagnostics)
    summaries=[]
    for name in spec['buyerProfiles']:
        subset=[r for r in rows if r['profile']==name];actual=sum(r['actualSales'][0] for r in subset)
        metrics={}
        for key in (('peerMean','boundedMean','validatedMean') if validate_response else ('peerMean','boundedMean')):
            errors=[r[key]-r['actualSales'][0] for r in subset]
            metrics[key]=dict(MAE=sum(abs(e) for e in errors)/len(errors),bias=sum(errors)/len(errors),maxAbsoluteError=max(abs(e) for e in errors),
                              summedActualItems=actual,WAPE=sum(abs(e) for e in errors)/actual if actual else None)
        summaries.append(dict(profile=name,targetPhases=len(subset),fallbacks=sum(r['diagnostics']['fallbackUsed'] for r in subset),metrics=metrics))
    return dict(scope='Calibration-only homogeneous/control and heterogeneous buyer response fixtures; no price adaptation, loyalty, scarce stock or production. Private profile parameters are evaluator-only. No parameter retuning or held-out population claim.',specification=spec,rows=rows,summaries=summaries)
