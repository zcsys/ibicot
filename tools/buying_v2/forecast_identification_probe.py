"""Paired-world nonidentification fixture for stock-censored seller histories.

Private buyer curves are evaluator inputs. Equal published inputs imply equal
forecasts, while replenishment may reveal different sales. No new demand model.
"""
import hashlib
import numpy as np
from .forecast_probe import world, phase
from .forecast_response_stress import install_profile, expected_focal_sales
from .forecast import PublishedChannel, ForecastParameters
from .validated_response_forecast import forecast
from .seller_history import SellerHistory


def evaluate(spec, *, compiled=True):
    if len(spec['buyerProfiles']) != 2:
        raise ValueError('exactly two named private profiles required')
    if not spec['trainingQuotes'] or not spec['targetQuotes'] or not spec['seeds']:
        raise ValueError('nonempty training, targets and seeds required')
    stock = spec['trainingStock']
    if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
        raise ValueError('whole nonnegative training stock required')
    parameters = ForecastParameters(**spec['fallbackParameters'])
    rows = []
    history_evidence = []
    for seed in spec['seeds']:
        pairs = []
        for name, groups in spec['buyerProfiles'].items():
            cfg, w = world(spec, seed)
            install_profile(w, cfg, groups)
            history = SellerHistory(len(spec['trainingQuotes']))
            for tick, quote in enumerate(spec['trainingQuotes'], 1):
                obs = phase(w, cfg, tick, (stock,)*3, (quote, *spec['rivalQuotes']), compiled)
                history.record('retail', tick, np.zeros(3, dtype=np.int64), np.arange(3), np.ones(3),
                               obs['opening'], obs['closing'], obs['quote'], obs['sold'], obs['exposure'])
            tick = len(spec['trainingQuotes'])+1
            publication = PublishedChannel(history, 'retail', tick)
            predictions = []
            # Freeze every prediction before running any replenished target.
            for quote in spec['targetQuotes']:
                fallback = publication.forecast('local', seller=0, product=0, quote=quote,
                    payoff_cap=spec['ampleStock'], market_size=3, parameters=parameters)
                f = forecast(publication, seller=0, product=0, quote=quote, payoff_cap=spec['ampleStock'],
                    decay=spec['decay'], peer_elasticity=spec['peerElasticity'],
                    peer_max_log_quote_distance=spec['peerMaxLogQuoteDistance'],
                    max_log_extrapolation=spec['maxLogExtrapolation'], max_quote_folds=spec['maxQuoteFolds'], fallback=fallback)
                predictions.append(dict(quote=quote, quantities=f.quantities, probabilities=f.probabilities,
                                        mean=f.mean, diagnostics=f.diagnostics))
            outcomes = []
            for quote in spec['targetQuotes']:
                actual = phase(w, cfg, tick, (spec['ampleStock'],)*3, (quote, *spec['rivalQuotes']), compiled)
                expected = expected_focal_sales(groups, seed, tick, quote, spec['rivalQuotes'])
                if actual['sold'][0] != expected:
                    raise AssertionError('target must satisfy ample-stock independent demand calculation')
                outcomes.append(actual['sold'].tolist())
            pairs.append(dict(profile=name, history=history.view('retail'), predictions=predictions, actualSales=outcomes))
        a,b = pairs
        for key in a['history']:
            np.testing.assert_array_equal(a['history'][key], b['history'][key], err_msg=key)
        digest = hashlib.sha256()
        for key in sorted(a['history']):
            value = np.asarray(a['history'][key])
            digest.update(key.encode());digest.update(str(value.dtype).encode())
            digest.update(str(value.shape).encode());digest.update(value.tobytes())
        history_evidence.append(dict(seed=seed, sharedHistorySha256=digest.hexdigest(),
            trainingTicks=len(spec['trainingQuotes']), soldBySeller=a['history']['sold'].sum(axis=0).tolist(),
            discoveriesBySeller=a['history']['discoveries'].sum(axis=0).tolist(),
            shortChecksBySeller=a['history']['shortChecks'].sum(axis=0).tolist()))
        if a['predictions'] != b['predictions']:
            raise AssertionError('identical observed inputs produced different forecasts')
        for i, quote in enumerate(spec['targetQuotes']):
            y = [x['actualSales'][i][0] for x in pairs]
            rows.append(dict(seed=seed, quote=quote, profiles=[x['profile'] for x in pairs],
                actualSales=y, forecast=a['predictions'][i],
                unavoidableWorstAbsoluteError=abs(y[0]-y[1])/2))
    return dict(specification=spec, rows=rows, historyEvidence=history_evidence, publishedHistoriesIdentical=True,
        scope='Paired controlled private populations with exactly equal retained seller histories. Half the target-sales gap lower-bounds the worst error of any common point prediction for this pair. It is not a population risk estimate, calibrated interval, or a claim about additional unrecorded information.')
