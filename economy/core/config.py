"""Configuration schema, defaults and normalization — the canon parameter set.

Parameters are grouped the way the dashboard presents them: global environment,
Tier 0, Tier 1, Tier 2, storage, demand, and market/pricing.  Starting *cash*
is not a parameter — it is derived from equity, license and machinery
(cash = equity − license − machinery).  See ``docs/design_canon.md`` §12.
"""
from __future__ import annotations

import math

from . import model as M


def default_cfg() -> dict:
    return {
        # Global / environment
        'seed': 137,
        'difficultyTarget': 1.0,
        'theta': 0.15,
        'sigma': 0.005,
        'difficultyMin': 0.7,
        'difficultyMax': 1.4,
        'distributorCount': M.N_DISTRIBUTORS,
        't2FirmCount': M.N2_FIRMS,

        # Tier 0 (extraction)
        't0Equity': 75_000_000.0,       # $75m per extractor = license + machinery + reserve + cash
        't0License': 22_000_000.0,      # $22m Tier 0 license (equity asset)
        't0Machinery': 12_250_000.0,    # $12.25m per extraction system (equity asset; ×4 = $49m full rig)
        't0Reserve': 1_000_000.0,       # $1m reserved for other business operations
        't0Capacity': 200_000,          # extraction throughput per tick
        't0Storage': 500_000,           # storage capacity (fill to the brim, like T1/T2)
        'baseCost': 1.0,                # $1 per raw element
        't0Markup': 0.25,                 # T0 first-guess markup
        'minWholesaleLot': 1000,

        # Tier 1 (refining) — uniform scale
        't1Equity': 1_500_000.0,
        't1License': 1_000_000.0,
        't1Machinery': 15_000.0,
        't1Capacity': 2_000.0,          # C-1/C-2 throughput per machine/tick
        't1MaterialCost': 1.25,         # $1.25 per raw element (baseCost × (1 + t0Markup): T1 pays T0's marked-up price)
        't1Markup': 0.25,               # T1 first-guess markup (flat)

        # Tier 2 (manufacturing) — per-complexity machinery/capacity
        't2Equity': 1_500_000.0,
        't2License': 1_000_000.0,
        't2Machinery': {3: 75_000.0, 4: 375_000.0, 5: 420_000.0},
        't2Capacity': {3: 30.0, 4: 20.0, 5: 10.0},
        't2MaterialCost': 1.875,        # $1.875 per T1 material item ((t1MaterialCost + conversion) × (1 + t1Markup))
        'conversionFactor': 0.25,       # conversion = 0.25 × max(1, c−1) for all tiers

        # Storage (firm-level pool, raw + finished + machinery)
        'storage': 20_000.0,
        'footprint': {1: 1_000.0, 2: 1_000.0, 3: 3_000.0, 4: 4_000.0, 5: 5_000.0},

        # Demand / distributors (T3)
        'distributorSearchOffers': 5,
        'distributorActivation': 0.2,       # fraction of distributors that activate each tick
        'chokeMin': 1.8,
        'chokeMax': 3.0,
        'elasticity': 2.0,              # eta = 2 (T3 distributor demand)
        'productionMarginBand': 0.05,   # gross-margin fraction below which producer output tapers to 0 at break-even
        't2ReservationPremium': 0.25,

        # Market / pricing / reliability
        'pricingAggressiveness': 0.35,
        'alpha': 0.15,
        'reliabilityAlpha': 0.15,
        'switchingStableBand': 0.025,
        'wholesalePriceResponse': 0.05,
        'marketAnchorBand': 0.02,        # ± fraction around the market going rate where a firm holds instead of re-pricing
        'priceObservationTicks': 30,
        'loyaltyMultiple': {1: 41.665, 2: {3: 0.605, 4: 0.325, 5: 0.13}, 3: 0.485},
        'loyaltyEmaAlpha': 0.01,         # EMA smoothing for the adaptive loyalty-multiple regime

        # Research pricing (off by default)
        'researchPriceMinimumOpportunities': 0,
        'researchPriceMinimumPotentialOrders': 0,
        'researchPriceMaxObservationTicks': 3600,
    }


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _clamp_mapping(d, key, low, high=None):
    if not isinstance(d[key], dict):
        d[key] = dict(default_cfg()[key])
    out = {}
    for k in list(d[key]):
        v = float(d[key][k])
        if not math.isfinite(v):
            v = float(default_cfg()[key][int(k)])
        v = max(low, v)
        if high is not None:
            v = min(high, v)
        out[int(k)] = v
    d[key] = out


def normalize_config(c) -> dict:
    defaults = default_cfg()
    d = dict(defaults)
    d.update(c or {})

    for key in defaults:
        if _is_number(defaults[key]) and not math.isfinite(d[key]):
            d[key] = defaults[key]

    d['seed'] = math.floor(d['seed']) & 0xFFFFFFFF
    d['researchPriceMaxObservationTicks'] = max(1, math.floor(d['researchPriceMaxObservationTicks']))
    d['researchPriceMinimumPotentialOrders'] = M.clamp(d['researchPriceMinimumPotentialOrders'], 0, 1000)
    d['researchPriceMinimumOpportunities'] = max(0, min(1000, d['researchPriceMinimumOpportunities']))

    # Environment
    d['difficultyMin'] = max(0.01, d['difficultyMin'])
    d['difficultyMax'] = max(d['difficultyMin'], d['difficultyMax'])
    d['difficultyTarget'] = M.clamp(d['difficultyTarget'], d['difficultyMin'], d['difficultyMax'])
    d['theta'] = M.clamp(d['theta'], 0, 1)
    d['sigma'] = max(0, d['sigma'])

    # Topology
    d['distributorCount'] = max(1, min(M.N_DISTRIBUTORS, math.floor(d['distributorCount'] or M.N_DISTRIBUTORS)))
    d['t2FirmCount'] = max(1, min(M.N2_FIRMS, math.floor(d['t2FirmCount'] or M.N2_FIRMS)))

    # Tier 0
    for key in ('t0Equity', 't0License', 't0Machinery', 't0Reserve', 't0Capacity', 't0Storage', 'baseCost', 'minWholesaleLot'):
        d[key] = max(1, d[key])
    d['t0Markup'] = max(0, d['t0Markup'])

    # Tier 1
    for key in ('t1Equity', 't1License', 't1Machinery', 't1Capacity', 't1MaterialCost'):
        d[key] = max(0.000001, d[key])
    d['t1Markup'] = max(0, d['t1Markup'])

    # Tier 2
    for key in ('t2Equity', 't2License', 't2MaterialCost', 'conversionFactor'):
        d[key] = max(0.000001, d[key])
    _clamp_mapping(d, 't2Machinery', 1)
    _clamp_mapping(d, 't2Capacity', 1)
    _clamp_mapping(d, 'footprint', 0)

    # Storage
    d['storage'] = max(1, d['storage'])

    # Demand
    d['distributorSearchOffers'] = max(1, min(20, math.floor(d['distributorSearchOffers'])))
    d['distributorActivation'] = M.clamp(d['distributorActivation'], 0, 1)
    d['chokeMin'] = max(0.01, d['chokeMin'])
    d['chokeMax'] = max(d['chokeMin'], d['chokeMax'])
    d['elasticity'] = max(0.05, min(10, d['elasticity']))
    d['productionMarginBand'] = M.clamp(d['productionMarginBand'], 0.001, 1.0)
    d['t2ReservationPremium'] = max(0, d['t2ReservationPremium'])

    # Market
    d['pricingAggressiveness'] = M.clamp(d['pricingAggressiveness'], 0, 1)
    d['alpha'] = M.clamp(d['alpha'], 0, 1)
    d['reliabilityAlpha'] = M.clamp(d['reliabilityAlpha'], 0, 1)
    d['switchingStableBand'] = max(1e-9, d['switchingStableBand'])
    # loyaltyMultiple: {1: scalar (C-1/C-2 raw buyer), 2: {3,4,5: scalar}, 3: scalar}
    source = d['loyaltyMultiple'] if isinstance(d['loyaltyMultiple'], dict) else {}
    def member(mapping, key, fallback):
        return mapping.get(key, mapping.get(str(key), fallback))
    def multiple(value, fallback):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return fallback
        return max(0.0, value) if math.isfinite(value) else fallback
    base = defaults['loyaltyMultiple']
    sub = member(source, 2, {})
    sub = sub if isinstance(sub, dict) else {}
    d['loyaltyMultiple'] = {
        1: multiple(member(source, 1, base[1]), base[1]),
        2: {c: multiple(member(sub, c, base[2][c]), base[2][c]) for c in (3, 4, 5)},
        3: multiple(member(source, 3, base[3]), base[3]),
    }
    d['loyaltyEmaAlpha'] = M.clamp(d['loyaltyEmaAlpha'], 0.0001, 1.0)
    d['priceObservationTicks'] = max(1, min(360, math.floor(d['priceObservationTicks'])))
    wpr = d['wholesalePriceResponse']
    wpr = float(wpr) if math.isfinite(wpr) else 0.05
    d['wholesalePriceResponse'] = M.clamp(wpr, 0.001, 1)
    mab = d['marketAnchorBand']
    mab = float(mab) if math.isfinite(mab) else 0.02
    d['marketAnchorBand'] = M.clamp(mab, 0.001, 1.0)

    return d
