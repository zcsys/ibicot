"""Static catalog and economic primitives.

The catalog data is extracted one-for-one from ``web/catalog.js`` into
``catalog.json`` (see ``tools/dump_catalog.js``), so the counts, order,
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
with open(os.path.join(_HERE, 'catalog.json'), 'r', encoding='utf-8') as _f:
    _DATA = json.load(_f)

TIME = _DATA['TIME']
ELEMENTS: list[str] = _DATA['ELEMENTS']
T1_BASIC_MACHINERY = _DATA['T1_BASIC_MACHINERY']
T1_COMPOUND_MACHINERY = _DATA['T1_COMPOUND_MACHINERY']
T2_ROUTE_SETUP = _DATA['T2_ROUTE_SETUP']
# Quotes are whole cents, so the smallest representable positive quote is $0.01.
MIN_UNIT_PRICE = max(0.01, _DATA['MIN_UNIT_PRICE'])
# Numerical guardrail ceiling for prices (never an economic bound — see canon
# axiom 6: prices must settle at an interior equilibrium, not on a guardrail).
MAX_UNIT_PRICE = 1e9


def round_to_cent(x: float) -> float:
    # Prices are quoted in whole cents, rounded half away from zero.
    return (math.floor(x * 100 + 0.5) if x >= 0 else math.ceil(x * 100 - 0.5)) / 100
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
T2_Catalog: list[dict] = _DATA['T2_Catalog']
T2_UNINVENTED_PRODUCTS: list[dict] = _DATA['T2_UNINVENTED_PRODUCTS']
T2_COMPLEXITY_COUNTS: list = _DATA['T2_COMPLEXITY_COUNTS']
T2_Catalog_COUNT = _DATA['T2_Catalog_COUNT']
T2_SECTOR_MANUFACTURERS: list[dict] = _DATA['T2_SECTOR_MANUFACTURERS']
T2_MANUFACTURER_BY_SECTOR: dict = _DATA['T2_MANUFACTURER_BY_SECTOR']
EQUIPMENT_MAKERS: list[str] = _DATA['EQUIPMENT_MAKERS']
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
N_DISTRIBUTORS = WORLD_STORY['population']          # 1,000,000
MAX_T2_LINES = N2_FIRMS * T2_MAX_PRODUCTS_PER_FIRM
MONTH = TIME['ticksPerMonth']                     # 30
# Firms per product by complexity (canon §3): C-3 1,800 · C-4 300 · C-5 50.
T2_FIRMS_PER_PRODUCT = {3: 1800, 4: 300, 5: 50}
DISTRIBUTOR_QMAX = 20                           # canon §5: fixed per-distributor quantity

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
    # First-guess markup is uniform across tiers/complexities (flat 0.25): the
    # complexity gradient lives in demand *volume* (supply-scaled distributor routing,
    # 108:12:1), not in the seed price.  Prices then rise to their own equilibrium via the
    # derivative-following pricer.
    return cfg['t1Markup']


def goods_space(complexity: int, cfg) -> float:
    # canon: G = storage − machinery footprint (shared by raw+finished+machinery)
    return cfg['storage'] - cfg['footprint'][complexity]


def inventory_target(complexity: int, cfg) -> float:
    # canon: desired inventory = fill G, split 1:1 → finished = raw = G/2
    return goods_space(complexity, cfg) / 2.0


# Tier 1 material -> manufacturing sector (Star Business 1:1 mapping).  Each of
# the ten refined materials feeds one distinct Tier 2 application sector; this is
# the sector a Tier 1 firm is grouped under in the dashboard.
T1_SECTOR_BY_CODE: dict = {
    'W': 3,    # Industrial Fluid      -> Housing & Life Support
    'E': 7,    # Bulk Alloy            -> Industrial Tooling & Mining Supplies
    'F': 0,    # Energy Carrier        -> Power & Utilities
    'A': 6,    # Process Gas           -> Sensors & Medical Equipment
    'W+E': 2,  # Ceramic Stock         -> Shipbuilding & Orbital Structures
    'W+F': 1,  # Thermal Compound      -> Propulsion & Flight Systems
    'W+A': 8,  # Technical Fiber       -> Freight & Warehouse Equipment
    'E+F': 5,  # Semiconductor Crystal -> Computing & Communications
    'E+A': 4,  # Polymer Composite     -> Robotics & Field Services
    'F+A': 9,  # Active Reagent        -> Defense & Emergency Systems
}

# Market symbols (Star Business naming catalog §3), keyed by the legacy recipe code.
MATERIAL_SYMBOLS: dict = {p['code']: p['symbol'] for p in PRODUCTS}

# ---------------------------------------------------------------------------
# Tier 1 refining installations (Star Business naming catalog §7).  "Refining"
# identifies the operation; "bench" and "cell" express increasing installation
# scale.  These are equipment classes within the Machinery Market, not separate
# markets.  The maker is kept separate: Mudrock Machinery Co.
# ---------------------------------------------------------------------------
T1_EQUIPMENT_CLASS: dict = {1: 'Refining Bench', 2: 'Refining Cell'}
T1_EQUIPMENT_CONFIG: dict = {1: 'Single-Element Refining', 2: 'Paired-Element Refining'}
T1_EQUIPMENT_INSTALLATION: dict = {
    p['code']: f"{p['name']} {T1_EQUIPMENT_CLASS[p['complexity']]}"
    for p in PRODUCTS
}
T2_EQUIPMENT_CONFIG: dict = {int(k): v for k, v in _DATA['EQUIPMENT_CONFIG'].items()}

# ---------------------------------------------------------------------------
# Numbered companies (Star Business naming catalog §9).  Each sector has one
# recognizable generic business name; a `0x`-prefixed hex sector serial identifies
# the individual firm.  No house-name pool, location suffix, district, or berth is
# added.  The twenty authored identities stay separate and are never prepended.
# ---------------------------------------------------------------------------
T1_GENERIC_BASES: dict = {
    'W': 'Industrial Fluids', 'E': 'Alloy Refining', 'F': 'Energy Materials',
    'A': 'Process Gases', 'W+E': 'Ceramic Materials', 'W+F': 'Thermal Materials',
    'W+A': 'Technical Fibers', 'E+F': 'Semiconductor Materials', 'E+A': 'Composite Materials',
    'F+A': 'Active Chemicals',
}
T2_GENERIC_BASES: list[str] = [
    'Power Equipment', 'Propulsion Systems', 'Shipbuilding Works', 'Habitat Systems',
    'Service Robotics', 'Computing Systems', 'Scientific Instruments', 'Industrial Tooling',
    'Freight Equipment', 'Defense Systems',
]

# Cohort sizes used to derive a firm's 1-based sector serial for the display name.
T1_FIRMS_PER_MATERIAL: int = N1 // len(PRODUCTS)          # 100
T2_FIRMS_PER_SECTOR: int = N2_FIRMS // len(T2_SECTORS)    # 6000


def company_display_name(tier: int, generic_base: str, sector_serial: int) -> str:
    if tier not in (1, 2) or sector_serial < 1:
        raise ValueError("Invalid tier or sector serial")
    return f"{generic_base} 0x{sector_serial:x}"


def t1_firm_name(cid: int) -> str:
    """Display name for a Tier 1 refinery: generic base + hex sector serial."""
    code = PRODUCTS[int(cid) // 100]['code']
    serial = int(cid) % T1_FIRMS_PER_MATERIAL + 1
    return company_display_name(1, T1_GENERIC_BASES[code], serial)


def t2_firm_name(sector: int, firm_id: int) -> str:
    """Display name for a Tier 2 manufacturer: generic base + hex sector serial."""
    sector = int(sector)
    serial = int(firm_id) - sector * T2_FIRMS_PER_SECTOR + 1
    return company_display_name(2, T2_GENERIC_BASES[sector], serial)


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
# catalogInputRatios: T2_PRODUCTS x PRODUCTS ratio matrix
_T2_RATIOS = [[0.0] * NP for _ in range(len(T2_PRODUCTS))]
for _pid, _ing in enumerate(_T2_INGREDIENTS):
    for _m, _q in _ing:
        _T2_RATIOS[_pid][_m] = float(_q)

# T2_PRODUCT_BY_CODE
T2_PRODUCT_BY_CODE = {p['code']: p for p in T2_PRODUCTS}

# catalogInputRatios (T2_PRODUCTS x PRODUCTS) used by the Tier 2 buy phase.
catalog_input_ratios = _T2_RATIOS


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


def loyalty_surcharge(price, reliability) -> float:
    # Per-unit surcharge used in supplier ranking: the fixed switching charge spread
    # over one typical order ≈ 5 % of price at reliability 0.5 (the charge ≈ 5 % of
    # a typical order's value, so a challenger must undercut by ~5 % to win).
    return 0.05 * price * (1.0 + clamp(reliability, 0.0, 1.0)) / 1.5


def loyalty_charge(unit_cost, reliability, multiple) -> float:
    # Fixed charge paid once per disloyal purchase, to the incumbent (see canon §12.6).
    return multiple * unit_cost * (1.0 + clamp(reliability, 0.0, 1.0))


def reliability_score(price_stability, availability) -> float:
    return (0.5 * clamp(price_stability, 0.0, 1.0)
            + 0.5 * clamp(availability, 0.0, 1.0))


def next_reliability(current, score, alpha) -> float:
    return clamp(current + clamp(alpha, 0.0, 1.0) * (score - current), 0.0, 1.0)


def demand_at_price(q_max, choke_price, price, elasticity) -> float:
    if q_max > 0 and choke_price > 0 and price >= 0 and elasticity > 0:
        return q_max / (1.0 + (price / choke_price) ** elasticity)
    return 0.0


def adaptive_price(old_price, profit, previous_profit, direction=1,
                   sales=0.0, stock=0.0, demand=0.0, available=0.0, step_scale=1.0,
                   market_price=None, band=0.02,
                   pricing_aggressiveness=0.35, response=0.05) -> dict:
    # Guardrails only: the price may go below unit cost (sell at a loss) and is
    # never pinned to an economic floor/ceiling.
    floor = MIN_UNIT_PRICE
    price = round_to_cent(min(MAX_UNIT_PRICE, max(floor, old_price)))
    next_direction = -1 if direction < 0 else 1
    moved = False
    # Derivative-following pricing (canon §12.2): unmet demand raises; a firm priced
    # above its market's going rate lowers (expensive → contest) and one priced
    # below raises (cheap → capture value); otherwise it follows the sign of the
    # realised profit change with a 2 % dead band, holding once profit flattens.
    if demand > available + 1e-9:
        # Scarce: unmet demand (demand exceeds what we supplied) → raise, even once
        # a profit baseline exists, so upstream tiers capture a lively market.
        next_direction = 1
        moved = True
    elif market_price is not None and market_price > 0:
        if price > market_price * (1 + band):
            next_direction = -1   # expensive → contest
            moved = True
        elif price < market_price * (1 - band):
            next_direction = 1    # cheap → capture value
            moved = True
    if not moved and math.isfinite(previous_profit):
        # A loss shrinking is an improvement; zero is also a valid baseline.
        change = (profit - previous_profit) / max(abs(previous_profit), 1e-9)
        if change < -0.02:
            next_direction = -next_direction
        elif change > 0.02:
            pass
        else:
            return {'price': price, 'direction': next_direction, 'stepScale': step_scale}
    scale = clamp(step_scale * (1.0 if next_direction != direction else 1.2), 0.01, 1.0)
    nxt = round_to_cent(min(MAX_UNIT_PRICE, max(floor, price * math.exp(next_direction * clamp(pricing_aggressiveness, 0.0, 1.0) * response * scale))))
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
    # canon demand side (§5): V = unit cost; η = 2. Per-distributor quantity is
    # fixed at DISTRIBUTOR_QMAX; the complexity gradient (demand ∝ supply = firms ×
    # capacity, 108:12:1) lives in *distributor routing* (initialize_distributors).
    return {'markup': cfg['t1Markup'],
            'valuation': reference_cost}


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


def production_batches(batches, output_qty, unit_cost, price, overhead, margin_band):
    """Gate feasible whole batches using inventory cost plus forecast period cost.

    Period overhead stays outside inventory basis. Recheck the reduced output:
    spreading a fixed bill over fewer units must not create a loss-making plan.
    """
    if batches <= 0 or unit_cost > price + 1e-9:
        return 0
    margin = (price - unit_cost - overhead / (batches * output_qty)) / max(price, 1e-9)
    factor = min(1.0, max(0.0, margin / margin_band))
    result = math.floor(batches * factor + 0.5)
    if result <= 0 or (price - unit_cost) * result * output_qty - overhead < -1e-9:
        return 0
    return result
