"""Configuration schema, defaults and normalization — mirror of the JS worker.

Transcribed from ``the canon machine contract (spec/design_canon.md §12)`` ``defaultCfg()`` and
``normalizeConfig()`` so that a normalized config is bit-identical to the JS
side.  See ``spec/design_canon.md`` §5.
"""
from __future__ import annotations

import math

from . import model as M


def default_cfg() -> dict:
    d = M.ECONOMY_DEFAULTS
    return {
        'seed': 12345,
        'dbar': 1,
        'theta': 0.15,
        'sigma': 0.005,
        'dmin': 0.7,
        'dmax': 1.4,
        'capacity': d['capacity'],
        'targetInventory': d['targetInventory'],
        'maxInventory': d['maxInventory'],
        'baseCost': 1,
        'retailTargetInventory': d['retailTargetInventory'],
        'retailMaxInventory': d['retailMaxInventory'],
        'retailInitialCash': M.T1_WORKING_CASH,          # canon $485k T1 working cash
        'basicEquipmentCapacity': M.T1_CAPACITY,         # canon C-1/C-2 throughput 500
        'compoundEquipmentCapacity': M.T1_CAPACITY,
        'manufacturingCostPerUnit': M.conversion_cost(1),  # canon T1 conversion $0.25
        'minWholesaleLot': d['minWholesaleLot'],
        'k': 0.35,
        'alpha': 0.15,
        'markup': 0.25,
        'compoundMarkupPremium': 0,                      # canon: T1 markup flat 0.25
        'wholesalePriceResponse': 0.05,
        'priceObservationTicks': 30,
        'researchPriceMinimumOpportunities': 0,
        'researchPriceMinimumPotentialOrders': 0,
        'researchPriceMaxObservationTicks': 3600,
        'consumerSearchOffers': 5,
        'vmin': 0.9,
        'vmax': 1.5,
        'demandQtyMin': 1,
        'demandQtyMax': 10,
        'elasticityMin': 2,                              # canon: eta = 2 (flat)
        'elasticityMax': 2,
        'taumin': 0.05,
        'taumax': 0.2,
        'reliabilityAlpha': 0.15,
        'switchingStableBand': 0.025,
        'endUserCount': M.N_END_USERS,
        't2FirmCount': M.N2_FIRMS,
        'initialCash': M.T0_INITIAL_CASH,                # canon $10m Tier 0
        'inventoryCoverageTicks': d['inventoryCoverageTicks'],
        'initialDemandForecastScale': 0,
        'procurementMaterialBalance': [0] * M.NP,
        'tier2MaterialBalance': [0] * M.NP,
        'tier2WorkingCashTicks': d['tier2WorkingCashTicks'],
        'tier2MinimumCash': d['tier2MinimumCash'],
        'tier2MarkupPremium': d['tier2MarkupPremium'],
        'tier2BaseMarkup': d['tier2BaseMarkup'],
        'procurementBaseMarkup': d['procurementBaseMarkup'],
        'procurementMarkupPremium': d['procurementMarkupPremium'],
        'procurementBasicReferenceCost': d['procurementBasicReferenceCost'],
        'procurementCompoundReferenceCost': d['procurementCompoundReferenceCost'],
        'tier2ConversionCostScale': d['tier2ConversionCostScale'],
        'procurementConversionReferenceScale': d['procurementConversionReferenceScale'],
        'tier2CompoundStandardization': d['tier2CompoundStandardization'],
        'tier2ComplexitySpecialization': d['tier2ComplexitySpecialization'],
        'procurementCompoundStandardization': d['procurementCompoundStandardization'],
        'procurementComplexitySpecialization': d['procurementComplexitySpecialization'],
        'tier2CompanyCapacity': d['tier2CompanyCapacity'],
        'tier2InventoryCapacity': M.STORAGE,             # canon 20,000 firm-level pool
        'tier1InventoryCapacity': M.STORAGE,
        'consumerActivation': 0.1,
        'tier2DemandFactor': 1,
        'tier2ReservationPremium': 0,
    }


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def normalize_config(c) -> dict:
    defaults = default_cfg()
    d = dict(defaults)
    d.update(c or {})

    for key in defaults:
        if _is_number(defaults[key]) and not math.isfinite(d[key]):
            d[key] = defaults[key]

    for key in ('procurementMaterialBalance', 'tier2MaterialBalance'):
        coefficients = d[key] if isinstance(d[key], (list, tuple)) else defaults[key]
        d[key] = [M.clamp(coefficients[material], -5, 5) if math.isfinite(coefficients[material]) else 0
                  for material in range(M.NP)]

    d['seed'] = math.floor(d['seed']) & 0xFFFFFFFF
    d['researchPriceMaxObservationTicks'] = max(1, math.floor(d['researchPriceMaxObservationTicks']))
    d['initialDemandForecastScale'] = M.clamp(d['initialDemandForecastScale'], 0, 100)
    d['researchPriceMinimumPotentialOrders'] = M.clamp(d['researchPriceMinimumPotentialOrders'], 0, 1000)
    d['researchPriceMinimumOpportunities'] = max(0, min(1000, d['researchPriceMinimumOpportunities']))

    for key in ('capacity', 'targetInventory', 'maxInventory', 'retailTargetInventory',
                'retailMaxInventory', 'retailInitialCash', 'initialCash', 'baseCost',
                'manufacturingCostPerUnit', 'tier2MinimumCash'):
        d[key] = max(0, d[key])

    for key in ('alpha', 'reliabilityAlpha', 'consumerActivation'):
        d[key] = M.clamp(d[key], 0, 1)

    d['dmin'] = max(0.01, d['dmin'])
    d['dmax'] = max(d['dmin'], d['dmax'])
    d['dbar'] = M.clamp(d['dbar'], d['dmin'], d['dmax'])
    d['theta'] = M.clamp(d['theta'], 0, 1)
    d['sigma'] = max(0, d['sigma'])

    d['tier2CompanyCapacity'] = max(1, math.floor(d['tier2CompanyCapacity']))
    d['tier2InventoryCapacity'] = max(5, math.floor(d['tier2InventoryCapacity']))

    d['taumin'] = max(0, d['taumin'])
    d['taumax'] = max(d['taumin'], d['taumax'])

    d['tier2BaseMarkup'] = max(-1, d['tier2BaseMarkup'])
    d['procurementBaseMarkup'] = max(0.000001, d['procurementBaseMarkup'])
    d['procurementMarkupPremium'] = max(0, d['procurementMarkupPremium'])
    d['procurementBasicReferenceCost'] = max(M.MIN_UNIT_PRICE, d['procurementBasicReferenceCost'])
    d['procurementCompoundReferenceCost'] = max(M.MIN_UNIT_PRICE, d['procurementCompoundReferenceCost'])
    d['tier2ConversionCostScale'] = max(1e-9, d['tier2ConversionCostScale'])
    d['procurementConversionReferenceScale'] = max(1e-9, d['procurementConversionReferenceScale'])

    for key in ('tier2CompoundStandardization', 'tier2ComplexitySpecialization',
                'procurementCompoundStandardization', 'procurementComplexitySpecialization'):
        d[key] = M.clamp(d[key], 0, 5)

    d['switchingStableBand'] = max(1e-9, d['switchingStableBand'])
    d['tier2DemandFactor'] = M.clamp(d['tier2DemandFactor'], 0.01, 10)
    d['tier2ReservationPremium'] = max(0, d['tier2ReservationPremium'])
    d['tier2MarkupPremium'] = max(0, d['tier2MarkupPremium'])
    d['markup'] = max(0, d['markup'])
    d['compoundMarkupPremium'] = max(0, d['compoundMarkupPremium'])
    d['k'] = M.clamp(d['k'], 0, 1)
    d['priceObservationTicks'] = max(1, min(360, math.floor(d['priceObservationTicks'])))
    d['consumerSearchOffers'] = max(1, min(20, math.floor(d['consumerSearchOffers'])))
    d['vmin'] = max(0.01, d['vmin'])
    d['vmax'] = max(d['vmin'], d['vmax'])
    d['maxInventory'] = max(d['targetInventory'], d['maxInventory'])
    d['retailMaxInventory'] = max(d['retailTargetInventory'], d['retailMaxInventory'])
    d['taumin'] = min(d['taumin'], d['taumax'])
    d['taumax'] = max(d['taumin'], d['taumax'])
    d['demandQtyMin'] = max(1, min(100, math.floor(d['demandQtyMin'])))
    d['demandQtyMax'] = max(d['demandQtyMin'], min(100, math.floor(d['demandQtyMax'])))
    d['elasticityMin'] = max(0.05, min(10, d['elasticityMin']))
    d['elasticityMax'] = max(d['elasticityMin'], min(10, d['elasticityMax']))
    d['minWholesaleLot'] = max(1, math.floor(d['minWholesaleLot']))
    d['tier1InventoryCapacity'] = max(2 * d['minWholesaleLot'], math.floor(d['tier1InventoryCapacity']))
    d['inventoryCoverageTicks'] = max(1, min(30, d['inventoryCoverageTicks']))
    d['tier2WorkingCashTicks'] = max(1, min(360, d['tier2WorkingCashTicks']))
    d['endUserCount'] = max(1, min(M.N_END_USERS, math.floor(d['endUserCount'] or M.N_END_USERS)))
    d['t2FirmCount'] = max(1, min(M.N2_FIRMS, math.floor(d['t2FirmCount'] or M.N2_FIRMS)))
    d['basicEquipmentCapacity'] = max(1, math.floor(d['basicEquipmentCapacity']))
    d['compoundEquipmentCapacity'] = max(1, math.floor(d['compoundEquipmentCapacity']))
    wpr = d['wholesalePriceResponse']
    wpr = float(wpr) if math.isfinite(wpr) else 0.05
    d['wholesalePriceResponse'] = M.clamp(wpr, 0.001, 1)

    return d
