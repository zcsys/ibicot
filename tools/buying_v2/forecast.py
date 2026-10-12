"""Experimental one-phase payoff scenarios from lagged seller observations.

This is an explicit empirical scenario model, not identified latent demand.
Parameters have no defaults or production adoption. The payoff cap is fixed for
all actions in a decision, not the amount a candidate basket happens to produce.
"""
from dataclasses import asdict, dataclass
import math
import numpy as np

VERSION = 2


@dataclass(frozen=True)
class ForecastParameters:
    decay: float
    elasticity: float
    censored_tail_weight: float
    cold_start_positive_weight: float
    cold_start_quantity: float
    cold_start_quote: float
    prior_weight: float
    hybrid_local_weight: float

    def __post_init__(self):
        if any(not math.isfinite(v) for v in asdict(self).values()):
            raise ValueError('forecast parameters must be finite')
        if not 0 < self.decay <= 1 or self.elasticity < 0 or self.prior_weight < 0:
            raise ValueError('invalid decay, elasticity or prior weight')
        if self.cold_start_quantity < 0 or self.cold_start_quote <= 0:
            raise ValueError('invalid cold-start quantity or reference quote')
        if any(not 0 <= v <= 1 for v in (self.censored_tail_weight,
                self.cold_start_positive_weight, self.hybrid_local_weight)):
            raise ValueError('forecast mixture weights must be in [0,1]')


def _positive_integer(value, allow_zero=False):
    return not isinstance(value, (bool, np.bool_)) and isinstance(value, (int, np.integer)) and value >= (0 if allow_zero else 1)


@dataclass(frozen=True)
class Forecast:
    quantities: tuple
    probabilities: tuple
    payoff_cap: int
    diagnostics: dict

    @property
    def mean(self):
        return sum(q * p for q, p in zip(self.quantities, self.probabilities))

    def expected_sales(self, stock):
        if not _positive_integer(stock, allow_zero=True) or stock > self.payoff_cap:
            raise ValueError('stock must be integral and within the fixed payoff cap')
        return sum(min(stock, q) * p for q, p in zip(self.quantities, self.probabilities))

    def incremental_values(self, existing, max_new, quote):
        if not _positive_integer(max_new, allow_zero=True) or not math.isfinite(quote) or quote <= 0:
            raise ValueError('invalid output bound or quote')
        if quote != self.diagnostics.get('contemplatedQuote'):
            raise ValueError('value quote differs from forecast contemplated quote')
        base = self.expected_sales(existing)
        if existing + max_new > self.payoff_cap:
            raise ValueError('output exceeds the fixed payoff cap')
        return tuple(quote * (self.expected_sales(existing + q) - base) for q in range(max_new + 1))


def _distribution(atoms, cap, diagnostics):
    merged = {}
    for quantity, probability in atoms:
        if probability <= 0:
            continue
        # Adjacent-integer mixtures preserve an explicitly assumed fractional
        # expectation while all realizable scenario quantities remain integral.
        quantity = min(float(cap), max(0., float(quantity)))
        lo = int(math.floor(quantity))
        fraction = quantity - lo
        merged[lo] = merged.get(lo, 0.) + probability * (1 - fraction)
        if fraction:
            merged[lo + 1] = merged.get(lo + 1, 0.) + probability * fraction
    total = math.fsum(merged.values())
    if not total > 0 or not math.isfinite(total):
        raise ValueError('forecast has no finite probability mass')
    keys = tuple(sorted(q for q, p in merged.items() if p > 0))
    return Forecast(keys, tuple(merged[q] / total for q in keys), int(cap), diagnostics)


def _adjust(sold, old_quote, new_quote, elasticity, cap):
    if sold <= 0 or cap == 0:
        return 0.
    # Log-space adjustment avoids overflow under large quote shocks. This is
    # a sensitivity assumption, not an elasticity estimated from one sample.
    log_q = math.log(sold) + elasticity * (math.log(old_quote) - math.log(new_quote))
    if log_q >= math.log(cap):
        return float(cap)
    return math.exp(log_q)


class PublishedChannel:
    """One publication view, built once per channel/decision tick.

    All retained rows strictly precede the decision tick. Product summaries are
    computed once and contain no current-tick supplier transactions. Forecasts
    are reference implementations; no per-company Python path is deployed.
    """
    def __init__(self, history, channel, decision_tick, *, feedback='inquiries'):
        if feedback not in ('inquiries', 'transactions'):
            raise ValueError('unknown forecast feedback mode')
        self.feedback = feedback
        if not _positive_integer(decision_tick):
            raise ValueError('decision tick must be positive integer')
        self.decision_tick = int(decision_tick)
        self.channel = channel
        self.catalog = history.catalog
        self.window = history.window
        if channel not in history.channels:
            self.rows = None
            self.products = np.empty(0, dtype=np.int64)
            self.market = {}
            return
        view = history.view(channel)
        keep = view['ticks'] < decision_tick
        self.rows = {key: value[keep].copy() for key, value in view.items()
                     if key not in ('product', 'owner', 'lot')
                     and (feedback == 'inquiries' or key not in ('discoveries', 'fundedChecks', 'shortChecks'))}
        if len(self.rows['ticks']) and self.rows['ticks'][-1] != decision_tick - 1:
            raise ValueError('latest completed phase observation is missing')
        self.products = view['product'].copy()
        self.market = {}
        offered = self.rows['offered'].astype(bool)
        if feedback == 'inquiries':
            informed = offered & (self.rows['discoveries'] > 0)
            constrained = informed & (self.rows['fundedChecks'] > 0) & ((self.rows['shortChecks'] > 0) | (self.rows['closingStock'] < view['lot']))
        else:
            # The collector verifies opening = sold + closing. An offered,
            # stocked phase supplies a realized-sales observation even without
            # a discovery. Empty opening stock supplies no demand observation.
            # This mode cannot detect rejected large orders from inquiry data.
            opening = self.rows['sold'] + self.rows['closingStock']
            informed = offered & (opening >= view['lot'])
            constrained = informed & (self.rows['closingStock'] < view['lot'])
        self.local_informed = informed
        self.local_constrained = constrained
        # Summaries deliberately use equal-share product aggregation, not a
        # company's own past market share. A pure market forecast cannot quietly
        # inherit local outcomes through an estimated individual-share weight.
        for product in np.unique(self.products):
            mask = self.products == product
            counts = offered[:, mask].sum(axis=1)
            quotes = np.where(offered[:, mask], self.rows['quote'][:, mask], 0.).sum(axis=1)
            reference = np.divide(quotes, counts, out=np.zeros_like(quotes), where=counts > 0)
            self.market[int(product)] = dict(sold=self.rows['sold'][:, mask].sum(axis=1),
                quote=reference, informed=informed[:, mask].any(axis=1),
                constrained=constrained[:, mask].any(axis=1), offered_count=counts)
        # Views are detached from the mutable history; publication cannot change
        # underneath a set of company decisions.
        for value in self.rows.values():
            value.flags.writeable = False

    def forecast(self, regime, *, seller, product, quote, payoff_cap, market_size, parameters):
        if regime not in ('local', 'market', 'hybrid'):
            raise ValueError('unknown forecast information regime')
        if not isinstance(parameters, ForecastParameters):
            raise ValueError('explicit forecast parameters required')
        if not _positive_integer(seller, True) or not _positive_integer(product, True):
            raise ValueError('invalid seller/product identity')
        if not _positive_integer(payoff_cap, True) or not _positive_integer(market_size):
            raise ValueError('payoff cap and current market size must be integers')
        if not math.isfinite(quote) or quote <= 0:
            raise ValueError('contemplated quote must be finite and positive')
        if seller < len(self.products) and self.products[seller] != product:
            raise ValueError('seller/product identity mismatch')
        params = parameters
        prior = [(0., 1 - params.cold_start_positive_weight),
                 (_adjust(params.cold_start_quantity, params.cold_start_quote, quote, params.elasticity, payoff_cap),
                  params.cold_start_positive_weight)]

        def estimate(kind):
            atoms = []
            observed = censored = 0
            weight_sum = 0.
            if self.rows is not None:
                if kind == 'local' and seller < len(self.products):
                    series = dict(sold=self.rows['sold'][:, seller], quote=self.rows['quote'][:, seller],
                                  informed=self.local_informed[:, seller], constrained=self.local_constrained[:, seller])
                    share = 1.
                elif kind == 'market' and product in self.market:
                    series = self.market[product]
                    share = 1. / market_size
                else:
                    series = None
                if series is not None:
                    for i, tick in enumerate(self.rows['ticks']):
                        if not series['informed'][i]:
                            continue
                        weight = params.decay ** (self.decision_tick - 1 - int(tick))
                        observed += 1
                        constrained = bool(series['constrained'][i])
                        censored += int(constrained)
                        weight_sum += weight
                        quantity = _adjust(series['sold'][i] * share, series['quote'][i], quote, params.elasticity, payoff_cap)
                        tail = params.censored_tail_weight if constrained else 0.
                        atoms.append((quantity, weight * (1 - tail)))
                        tail_quantity = _adjust(max(series['sold'][i] * share, payoff_cap), series['quote'][i], quote, params.elasticity, payoff_cap)
                        atoms.append((tail_quantity, weight * tail))
            if weight_sum == 0:
                atoms = prior.copy()
                used_prior = 1.
            else:
                atoms.extend((q, p * params.prior_weight) for q, p in prior)
                used_prior = params.prior_weight / (weight_sum + params.prior_weight)
            diagnostics = dict(observedRows=observed, constrainedRows=censored,
                               missingRows=(len(self.rows['ticks']) if self.rows is not None else 0)-observed,
                               observationWeight=weight_sum, priorProbability=used_prior,
                               share=1. / market_size if kind == 'market' else None)
            return _distribution(atoms, payoff_cap, diagnostics)

        if regime == 'hybrid':
            local, market = estimate('local'), estimate('market')
            alpha = params.hybrid_local_weight
            atoms = list(zip(local.quantities, (alpha * p for p in local.probabilities)))
            atoms.extend(zip(market.quantities, ((1-alpha) * p for p in market.probabilities)))
            result = _distribution(atoms, payoff_cap, dict(local=local.diagnostics, market=market.diagnostics))
        else:
            result = estimate(regime)
        result.diagnostics.update(version=VERSION, regime=regime, feedback=self.feedback, channel=self.channel,
            decisionTick=self.decision_tick, latestPublishedTick=int(self.rows['ticks'][-1]) if self.rows is not None and len(self.rows['ticks']) else None,
            seller=int(seller), product=int(product), marketSize=int(market_size),
            contemplatedQuote=float(quote), parameters=asdict(params), catalog=self.catalog,
            semantics='One-phase capped payoff opportunities; stock constraints and quote response are scenario assumptions, not identified latent demand.')
        return result
