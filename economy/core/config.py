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
        'consumerCount': M.N_CONSUMERS,
        't2FirmCount': M.N2_FIRMS,

        # Tier 0 (extraction)
        't0Equity': 10_000_000.0,       # $10m per extractor (all cash)
        't0Capacity': 10000,              # extraction throughput per tick
        't0TargetInventory': 500_000,
        't0MaxInventory': 1_000_000,
        'baseCost': 1.0,                # $1 per raw element
        't0Markup': 0.25,                 # T0 first-guess markup
        'minWholesaleLot': 1000,
        'inventoryCoverageTicks': 3,

        # Tier 1 (refining) — uniform scale
        't1Equity': 1_500_000.0,
        't1License': 1_000_000.0,
        't1Machinery': 15_000.0,
        't1Capacity': 500.0,            # C-1/C-2 throughput per machine/tick
        't1MaterialCost': 1.0,          # $1 per raw element
        't1Markup': 0.25,               # T1 first-guess markup (flat)

        # Tier 2 (manufacturing) — per-complexity machinery/capacity
        't2Equity': 1_500_000.0,
        't2License': 1_000_000.0,
        't2Machinery': {3: 75_000.0, 4: 375_000.0, 5: 420_000.0},
        't2Capacity': {3: 300.0, 4: 200.0, 5: 100.0},
        't2MaterialCost': 1.25,         # $1.25 per T1 material item
        'conversionFactor': 0.25,       # conversion = 0.25 × max(1, c−1) for all tiers

        # Storage (firm-level pool, raw + finished + machinery)
        'storage': 20_000.0,
        'footprint': {1: 1_000.0, 2: 1_000.0, 3: 3_000.0, 4: 4_000.0, 5: 5_000.0},

        # Demand / consumers
        'consumerSearchOffers': 5,
        'consumerActivation': 0.1,       # fraction of buyers that activate each tick
        'chokeMin': 1.8,
        'chokeMax': 3.0,
        'elasticity': 2.0,              # eta = 2
        't2ReservationPremium': 0.0,

        # Market / pricing / reliability
        'pricingAggressiveness': 0.35,
        'alpha': 0.15,
        'reliabilityAlpha': 0.15,
        'switchingStableBand': 0.025,
        'wholesalePriceResponse': 0.05,
        'priceObservationTicks': 30,
        'loyaltyMultiple': {1: 500.0, 2: 125.0, 3: 0.5},

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
    d['consumerCount'] = max(1, min(M.N_CONSUMERS, math.floor(d['consumerCount'] or M.N_CONSUMERS)))
    d['t2FirmCount'] = max(1, min(M.N2_FIRMS, math.floor(d['t2FirmCount'] or M.N2_FIRMS)))

    # Tier 0
    for key in ('t0Equity', 't0Capacity', 't0TargetInventory', 't0MaxInventory', 'baseCost', 'minWholesaleLot'):
        d[key] = max(1, d[key])
    d['t0MaxInventory'] = max(d['t0TargetInventory'], d['t0MaxInventory'])
    d['t0Markup'] = max(0, d['t0Markup'])
    d['inventoryCoverageTicks'] = max(1, min(30, d['inventoryCoverageTicks']))

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
    d['consumerSearchOffers'] = max(1, min(20, math.floor(d['consumerSearchOffers'])))
    d['consumerActivation'] = M.clamp(d['consumerActivation'], 0, 1)
    d['chokeMin'] = max(0.01, d['chokeMin'])
    d['chokeMax'] = max(d['chokeMin'], d['chokeMax'])
    d['elasticity'] = max(0.05, min(10, d['elasticity']))
    d['t2ReservationPremium'] = max(0, d['t2ReservationPremium'])

    # Market
    d['pricingAggressiveness'] = M.clamp(d['pricingAggressiveness'], 0, 1)
    d['alpha'] = M.clamp(d['alpha'], 0, 1)
    d['reliabilityAlpha'] = M.clamp(d['reliabilityAlpha'], 0, 1)
    d['switchingStableBand'] = max(1e-9, d['switchingStableBand'])
    _clamp_mapping(d, 'loyaltyMultiple', 0)
    d['priceObservationTicks'] = max(1, min(360, math.floor(d['priceObservationTicks'])))
    wpr = d['wholesalePriceResponse']
    wpr = float(wpr) if math.isfinite(wpr) else 0.05
    d['wholesalePriceResponse'] = M.clamp(wpr, 0.001, 1)

    return d
