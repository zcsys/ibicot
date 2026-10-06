"""Static catalogue and economic primitives.

The catalogue data is extracted one-for-one from ``web/catalogue.js`` into
``_catalogue.json`` (see ``tools/dump_catalogue.js``), so the counts, order,
codes, recipes and invented-market selection are bit-identical to the JS
oracle without hand transcription.  This module adds the small pure-math
primitives (``adaptivePrice``, ``finishedStockTarget``, ``procurementProfile``,
…) transcribed from the same file.
"""
from __future__ import annotations

import json
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, '_catalogue.json'), 'r', encoding='utf-8') as _f:
    _DATA = json.load(_f)

TIME = _DATA['TIME']
ELEMENTS: list[str] = _DATA['ELEMENTS']
T1_BASIC_MACHINERY = _DATA['T1_BASIC_MACHINERY']
T1_COMPOUND_MACHINERY = _DATA['T1_COMPOUND_MACHINERY']
T2_ROUTE_SETUP = _DATA['T2_ROUTE_SETUP']
MIN_UNIT_PRICE = _DATA['MIN_UNIT_PRICE']
TIER_BOUNDARIES = _DATA['TIER_BOUNDARIES']
T1_COMPANY_NAMES = _DATA['T1_COMPANY_NAMES']
PRODUCTS: list[dict] = _DATA['PRODUCTS']
T2_SECTORS: list[str] = _DATA['T2_SECTORS']
T2_SECTOR_DEFINITIONS: list[dict] = _DATA['T2_SECTOR_DEFINITIONS']
T2_SECTOR_WEIGHTS: list = _DATA['T2_SECTOR_WEIGHTS']
T2_ADJACENCY: list = _DATA['T2_ADJACENCY']
T2_NEED_TYPES: list = _DATA['T2_NEED_TYPES']
T2_MAX_PRODUCTS_PER_FIRM = _DATA['T2_MAX_PRODUCTS_PER_FIRM']
ECONOMY_DEFAULTS = _DATA['ECONOMY_DEFAULTS']
PROGRESSION_DEFAULTS = _DATA['PROGRESSION_DEFAULTS']
INVENTED_PER_COMPLEXITY = {int(k): v for k, v in _DATA['INVENTED_PER_COMPLEXITY'].items()}
T2_PRODUCTS: list[dict] = _DATA['T2_PRODUCTS']
T2_CATALOGUE: list[dict] = _DATA['T2_CATALOGUE']
T2_UNINVENTED_PRODUCTS: list[dict] = _DATA['T2_UNINVENTED_PRODUCTS']
T2_COMPLEXITY_COUNTS: list = _DATA['T2_COMPLEXITY_COUNTS']
T2_CATALOGUE_COUNT = _DATA['T2_CATALOGUE_COUNT']
WORLD_STORY = _DATA['WORLD_STORY']

# ===========================================================================
# Canon parameter pass (design_canon.md §3–§6 / handoff "settled parameters").
# These override the JS oracle's *stale* values.  The topology (§3) is settled
# canon; the supply-side numbers (§4, §6) are pinned working values; the
# demand-side (§5) structure is canon while its exact scale/markup are
# calibration (see §9).  The JS-equivalence gate is retired once this pass is
# applied — the canon deliberately diverges from the old JS kernel.
# ===========================================================================
NE = len(ELEMENTS)          # 4
NP = len(PRODUCTS)          # 10
N0 = 20
N1 = 1000
N2_FIRMS = 60000            # canon: 60,000 single-machine T2 firms (was 61,950)
N_END_USERS = WORLD_STORY['population']          # 1,000,000
MAX_T2_LINES = N2_FIRMS     # one machine/line per firm at start
MONTH = TIME['ticksPerMonth']                     # 30

# Supply-side scale values (equity, license, machinery, capacity, costs, storage)
# live in ``core/config.py``.  The model exposes cfg-driven helpers so the kernel,
# Numba fast path and snapshot layers all share one source of truth.


def conversion_cost(complexity: int, cfg) -> float:
    # canon: $0.25 × max(1, complexity−1)  → 0.25/0.25/0.50/0.75/1.00
    return cfg['conversionFactor'] * max(1, complexity - 1)


def unit_cost(complexity: int, cfg) -> float:
    # canon cost ladder: $1.25 / $1.25 / $1.75 / $2.00 / $2.25 (per output item)
    material = cfg['t1MaterialCost'] if complexity <= 2 else cfg['t2MaterialCost']
    return material + conversion_cost(complexity, cfg)


def t2_markup(complexity: int, cfg) -> float:
    # canon first-guess markup: T1 flat; T2 base × exponent^(c−3)
    if complexity <= 2:
        return cfg['t1Markup']
    return cfg['t2MarkupBase'] * (cfg['t2MarkupExponent'] ** (complexity - 3))


def goods_space(complexity: int, cfg) -> float:
    # canon: G = storage − machinery footprint (shared by raw+finished+machinery)
    return cfg['storage'] - cfg['footprint'][complexity]


def inventory_target(complexity: int, cfg) -> float:
    # canon: desired inventory = fill G, split 1:1 → finished = raw = G/2
    return goods_space(complexity, cfg) / 2.0


# Tier 1 material -> galactic sector (canon 1:1 mapping).  Each of the ten
# processed materials feeds one distinct Tier 2 application sector; this is the
# sector a Tier 1 firm is grouped under in the dashboard.
T1_SECTOR_BY_CODE: dict = {
    'W': 3,    # Purified Water      -> Habitats & Life Support
    'E': 7,    # Refined Minerals    -> Mining & Industry
    'F': 0,    # Energy Cells        -> Power & Energy
    'A': 6,    # Chemical Feedstock  -> Science & Diagnostics
    'W+E': 2,  # Ceramic Composite   -> Spacecraft & Hulls
    'W+F': 1,  # Thermal Compounds   -> Propulsion & Navigation
    'W+A': 8,  # Synthetic Fibers    -> Logistics & Provisioning
    'E+F': 5,  # Semiconductor Substrate -> Computing & Communications
    'E+A': 4,  # Structural Polymers -> Robotics & Automation
    'F+A': 9,  # Active Compounds    -> Defence & Rescue
}


def t1_sector(code: str) -> str:
    return T2_SECTORS[T1_SECTOR_BY_CODE[code]]


# Count-preserving output quantity (structural, from the recipe).
for _p in T2_PRODUCTS:
    _p['outputQty'] = sum(int(q) for _m, q in _p['ingredients'])
for _p in PRODUCTS:
    _p['outputQty'] = sum(int(q) for q in _p['inputs'].values())

# Per-product precomputed *structural* flat structure used by the hot loops.
# (Scale values — conversion, machinery, capacity, target — are cfg-driven.)
_T2_COMPLEXITY = [p['complexity'] for p in T2_PRODUCTS]
_T2_SECTOR = [p['sectorIndex'] for p in T2_PRODUCTS]
_T2_OUTPUT = [p['outputQty'] for p in T2_PRODUCTS]
# ingredients: list per product of (material_index, quantity) tuples
_T2_INGREDIENTS = [[(int(m), int(q)) for (m, q) in p['ingredients']] for p in T2_PRODUCTS]
# catalogueInputRatios: T2_PRODUCTS x PRODUCTS ratio matrix
_T2_RATIOS = [[0.0] * NP for _ in range(len(T2_PRODUCTS))]
for _pid, _ing in enumerate(_T2_INGREDIENTS):
    for _m, _q in _ing:
        _T2_RATIOS[_pid][_m] = float(_q)

# T2_PRODUCT_BY_CODE
T2_PRODUCT_BY_CODE = {p['code']: p for p in T2_PRODUCTS}

# catalogueInputRatios (T2_PRODUCTS x PRODUCTS) used by the Tier 2 buy phase.
catalogue_input_ratios = _T2_RATIOS


def calendar_at(tick: int) -> dict:
    t = int(tick)
    month = (int(t / TIME['ticksPerMonth']) % TIME['monthsPerYear']) + 1
    year = (int(t / TIME['ticksPerYear']) % TIME['yearsPerGeneration']) + 1
    generation = int(t / TIME['ticksPerGeneration'])
    age = int(t / TIME['ticksPerAge'])
    return {'tick': t, 'month': month, 'year': year, 'generation': generation,
            'generationHex': '0x' + format(generation, 'X'), 'age': age}


def clamp(value, low, high):
    return max(low, min(high, value))


def complexity(product) -> int:
    return product['complexity']


def finished_stock_target(sales_ema, coverage_ticks, bootstrap_stock, capacity,
                          target_inventory, max_inventory) -> float:
    return max(0.0, min(target_inventory, max_inventory,
                        max(min(capacity, bootstrap_stock),
                            math.ceil(max(0.0, sales_ema) * coverage_ticks))))


def switching_cost(reliability, minimum, maximum) -> float:
    return minimum + (maximum - minimum) * clamp(reliability, 0.0, 1.0)


def reliability_score(fulfillment, price_stability, availability) -> float:
    return (0.5 * clamp(fulfillment, 0.0, 1.0)
            + 0.3 * clamp(price_stability, 0.0, 1.0)
            + 0.2 * clamp(availability, 0.0, 1.0))


def next_reliability(current, score, alpha) -> float:
    return clamp(current + clamp(alpha, 0.0, 1.0) * (score - current), 0.0, 1.0)


def demand_at_price(q_max, choke_price, price, elasticity) -> float:
    if q_max > 0 and choke_price > 0 and price >= 0 and elasticity > 0:
        return q_max / (1.0 + (price / choke_price) ** elasticity)
    return 0.0


def adaptive_price(old_price, unit_cost, profit, previous_profit, direction=1,
                   sales=0.0, stock=0.0, demand=0.0, available=0.0, step_scale=1.0,
                   k=0.35, response=0.05) -> dict:
    floor = max(MIN_UNIT_PRICE, unit_cost)
    price = max(floor, old_price)
    next_direction = -1 if direction < 0 else 1
    scarce = demand > available + 1e-9
    if scarce:
        next_direction = 1
    elif sales <= 0:
        if stock <= 0:
            return {'price': price, 'direction': next_direction, 'stepScale': step_scale}
        next_direction = -1
    elif math.isfinite(previous_profit) and profit < previous_profit:
        next_direction *= -1
    scale = clamp(step_scale * (0.5 if next_direction != direction else 1.2), 0.01, 1.0)
    nxt = max(floor, price * math.exp(next_direction * clamp(k, 0.0, 1.0) * response * scale))
    if nxt == price and next_direction < 0:
        next_direction = 1
    return {'price': nxt, 'direction': next_direction, 'stepScale': scale}


def recipe_margin_factor(product, standardization=0.0, specialization=0.0, material_balance=None) -> float:
    compounds = 0
    material_tilt = 0.0
    for material, units in product['ingredients']:
        if material >= 4:
            compounds += units
        mb = material_balance[material] if material_balance is not None else 0.0
        material_tilt += units * mb
    return math.exp(specialization * (product['complexity'] - 3)
                    - standardization * compounds - material_tilt)


def tier2_starting_markup(product, cfg) -> float:
    return t2_markup(product['complexity'], cfg)


def procurement_profile(product, cfg, reference_cost) -> dict:
    # canon demand side (§5): V = 2 × unit cost; η = 2;
    # quantityFactor ∝ 1 / (cost × benchmark markup), scaled by tier2DemandFactor.
    markup = t2_markup(product['complexity'], cfg)
    return {'markup': markup,
            'quantityFactor': cfg['tier2DemandFactor'] / (reference_cost * markup),
            'valuation': 2.0 * reference_cost}


def initial_tier2_cost(product, cfg) -> float:
    return unit_cost(product['complexity'], cfg)


def reference_tier2_cost(product, cfg=None) -> float:
    return unit_cost(product['complexity'], cfg or {})


def portfolio_options(products, max_width=T2_MAX_PRODUCTS_PER_FIRM):
    """All unordered 1..max_width subsets of ``products`` in ascending index order."""
    options = []
    pick = []

    def visit(start, remaining):
        if remaining == 0:
            options.append(list(pick))
            return
        for i in range(start, len(products) - remaining + 1):
            pick.append(products[i])
            visit(i + 1, remaining - 1)
            pick.pop()

    for width in range(1, min(max_width, len(products)) + 1):
        visit(0, width)
    return options


def related_sector(core, sector):
    return core == sector or sector in T2_ADJACENCY[core]
