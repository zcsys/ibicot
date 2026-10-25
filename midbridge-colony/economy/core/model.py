"""Current catalog and economic primitives, loaded from the active catalog directory."""
from __future__ import annotations

import math

from .midbridge import load_catalog, CATALOG_REVISION
_DATA = load_catalog()

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
# The topology is defined by the current catalog. Supply-side working values
# and demand calibration below preserve the approved production behavior.
# ===========================================================================
NE = len(ELEMENTS)          # 4
NP = len(PRODUCTS)          # 14
N0 = 20
T1_DEFAULT_CAPACITY = 6_000.0
T1_C2_DEFAULT_CAPACITY = 6_000.0

def refinery_capacity(product, cfg):
    """Per-machine throughput; legacy scalar configurations cover both classes."""
    return cfg['t1Capacity'] if product['complexity'] == 1 else cfg.get('t1CapacityC2', cfg['t1Capacity'])

N1 = 1000  # 4 × 125 C1 companies + 10 × 50 C2 companies.
# Reverse product-count shares across complexities to favor simpler production.
# Exact reversed-count allocation requires multiples of 28,980:
# 36*x : 69*y = 23:12 => x:y = 529:144. Two blocks are nearest 50k.
N2_FIRMS = 57_960
T2_ALLOCATION_CAPACITIES = {3:32, 4:24}


def _apportion(total, weights):
    denominator = sum(weights.values())
    result = {key:total*weight//denominator for key,weight in weights.items()}
    order = sorted(weights, key=lambda key:(-(total*weights[key]%denominator),key))
    for key in order[:total-sum(result.values())]:
        result[key] += 1
    return result


# Main-branch principle: product shares increase with complexity, while total
# company shares use those same counts in reverse. Divide each complexity's
# population equally across its products; stable catalog IDs break integer ties.
_complexities = sorted({p['complexity'] for p in T2_PRODUCTS})
_product_counts = {c:sum(p['complexity'] == c for p in T2_PRODUCTS) for c in _complexities}
_reverse_counts = dict(zip(_complexities, reversed(list(_product_counts.values()))))
T2_COMPLEXITY_FIRM_COUNTS = _apportion(N2_FIRMS, _reverse_counts)
_capacity_multiple = math.lcm(*_product_counts.values())
T2_COMPANY_WEIGHTS = {p['catalogId']:_reverse_counts[p['complexity']]*_capacity_multiple//_product_counts[p['complexity']] for p in T2_PRODUCTS}
_allocation = {}
for _c in _complexities:
    _allocation.update(_apportion(T2_COMPLEXITY_FIRM_COUNTS[_c],
                                 {p['catalogId']:1 for p in T2_PRODUCTS if p['complexity'] == _c}))
T2_PRODUCT_FIRM_COUNTS = {p['id']:_allocation[p['catalogId']] for p in T2_PRODUCTS}
T2_PRODUCTION_WEIGHTS = {p['catalogId']:_allocation[p['catalogId']]*T2_ALLOCATION_CAPACITIES[p['complexity']] for p in T2_PRODUCTS}
# Allocate refiners by nominal T2 ingredient requirements at nominal capacity.
# Count direct ingredient use once: C3 capacity already includes C4 input supply.
T1_NOMINAL_DEMAND = {i:0 for i in range(NP)}
for _p in T2_PRODUCTS:
    for _m, _q in _p['ingredients']:
        if _m < NP:
            T1_NOMINAL_DEMAND[_m] += T2_PRODUCT_FIRM_COUNTS[_p['id']] * T2_ALLOCATION_CAPACITIES[_p['complexity']] * _q
# User-selected equal complexity populations, with exact product divisibility.
# Equal company counts per product within each complexity; no remainder weights.
T1_COMPLEXITY_FIRM_COUNTS = {1: 500, 2: 500}
_t1_allocation = {}
for _c, _count in T1_COMPLEXITY_FIRM_COUNTS.items():
    _products = [p for p in PRODUCTS if p['complexity'] == _c]
    assert _count % len(_products) == 0
    _t1_allocation.update({p['catalogId']: _count // len(_products) for p in _products})
T1_PRODUCT_FIRM_COUNTS = [_t1_allocation[p['catalogId']] for p in PRODUCTS]
T1_FIRM_OFFSETS = [sum(T1_PRODUCT_FIRM_COUNTS[:i]) for i in range(NP)]
T1_FIRM_PRODUCT = [p for p,n in enumerate(T1_PRODUCT_FIRM_COUNTS) for _ in range(n)]
T1_MAX_COHORT = max(T1_PRODUCT_FIRM_COUNTS)

# Route final demand to saleable output after reserving intermediates. At a
# common utilization, recursive final demand then exactly matches every line's
# nominal production. Gross capacity remains uniform within each complexity.
T2_FINAL_DEMAND_WEIGHTS = dict(T2_PRODUCTION_WEIGHTS)
for _p in T2_PRODUCTS:
    for _ingredient,_quantity in _p['ingredientCatalogIds'].items():
        if _ingredient in T2_FINAL_DEMAND_WEIGHTS:
            T2_FINAL_DEMAND_WEIGHTS[_ingredient] -= _quantity*T2_PRODUCTION_WEIGHTS[_p['catalogId']]
if min(T2_FINAL_DEMAND_WEIGHTS.values()) <= 0:
    raise ValueError('Manufacturer allocation leaves insufficient capacity for final demand.')
# Static trial calibration of final consumers only; upstream counts stay fixed.
T3_COMPLEXITY_DEMAND_MULTIPLIERS = _DATA['T3_COMPLEXITY_DEMAND_MULTIPLIERS']
for _p in T2_PRODUCTS:
    _p['distributorWeight'] = (T2_FINAL_DEMAND_WEIGHTS[_p['catalogId']]
                               * T3_COMPLEXITY_DEMAND_MULTIPLIERS[_p['complexity']])
T2_ROUTE_FIRM_COUNTS = {g:sum(T2_PRODUCT_FIRM_COUNTS[p['id']] for p in T2_PRODUCTS if p['demandGroup']==g) for g in ('c3','c4_basic_c3','c4_compound_pair')}
N_DISTRIBUTORS = WORLD_STORY['population']          # 1,000,000
MAX_T2_LINES = N2_FIRMS * T2_MAX_PRODUCTS_PER_FIRM
MONTH = TIME['ticksPerMonth']                     # 30
LOYALTY_ORDER_SHARE = 0.05
DISTRIBUTOR_QMAX = 20                           # canon §5: fixed per-distributor quantity

# Supply-side scale values (equity, license, machinery, capacity, costs, storage)
# live in ``core/config.py``.  The model exposes cfg-driven helpers so the kernel,
# Numba fast path and snapshot layers all share one source of truth.


def conversion_cost(complexity: int, cfg) -> float:
    # canon: $0.25 × max(1, complexity−1)  → 0.25/0.25/0.50/0.75/1.00
    return cfg['conversionFactor'] * max(1, complexity - 1)


def refinery_unit_cost(product, cfg):
    return (sum(product['inputs'].values()) * cfg['t1MaterialCost']
            / product['outputQty'] + conversion_cost(product['complexity'], cfg))


def unit_cost(complexity: int, cfg) -> float:
    """Class mean reference; use recipe-specific helpers for an actual product."""
    rows = PRODUCTS if complexity <= 2 else T2_PRODUCTS
    values = [(refinery_unit_cost(p, cfg) if complexity <= 2 else initial_tier2_cost(p, cfg))
              for p in rows if p['complexity'] == complexity]
    return sum(values) / len(values)


def material_switching_reference(cfg):
    # One common material reference matches the buyer-class AOV adaptation.
    return sum(refinery_unit_cost(p, cfg) for p in PRODUCTS) / len(PRODUCTS)


def t2_markup(complexity: int, cfg) -> float:
    # First-guess markup is uniform across tiers/complexities (flat 0.25): the
    # calibrated net final-output capacity sets routing independently of seed
    # prices. Prices then rise to their own equilibrium via the
    # derivative-following pricer.
    return cfg['t1Markup']


def refinery_storage(cfg, firm):
    """Storage belongs to the firm's native material cohort, not added machines."""
    return cfg.get('t1C2Storage', cfg['storage']) if PRODUCTS[T1_FIRM_PRODUCT[int(firm)]]['complexity'] == 2 else cfg.get('t1C1Storage', cfg['storage'])


def goods_space(complexity: int, cfg) -> float:
    # canon: G = storage − machinery footprint (shared by raw+finished+machinery)
    return (cfg.get(f't1C{complexity}Storage', cfg['storage']) if complexity <= 2 else cfg['storage']) - cfg['footprint'][complexity]


def inventory_target(complexity: int, cfg) -> float:
    # canon: desired inventory = fill G, split 1:1 → finished = raw = G/2
    return math.floor(goods_space(complexity, cfg) / (2.0 * complexity))


# Stable material indices pair the fourteen refinery and application sectors.
T1_SECTOR_BY_CODE = {p['code']: i for i, p in enumerate(PRODUCTS)}

# Market symbols (Midbridge naming catalog), keyed by the legacy recipe code.
MATERIAL_SYMBOLS: dict = {p['code']: p['symbol'] for p in PRODUCTS}

# ---------------------------------------------------------------------------
# Accepted equipment classes and recipe-specific installation names.
NAMING_CATALOG = _DATA['NAMING_CATALOG']
T1_EQUIPMENT_CLASS = {int(p['complexity'][2:]):p['name'] for p in NAMING_CATALOG['equipment_classes'] if p['complexity'] in ('C-1','C-2')}
T1_EQUIPMENT_CONFIG = dict(T1_EQUIPMENT_CLASS)
T1_EQUIPMENT_INSTALLATION: dict = {
    p['code']: p['installationName']
    for p in PRODUCTS
}
T2_EQUIPMENT_CONFIG: dict = {int(k): v for k, v in _DATA['EQUIPMENT_CONFIG'].items()}

# ---------------------------------------------------------------------------
# Numbered companies (Midbridge naming catalog).  Each T1 sector uses one
# generic stem and each T2 sector uses one facility stem; a global `0x`
# company number identifies the individual firm.  Neither tier has flagship
# names.  No house-name pool, location suffix, district, or berth is added.
# The twenty authored T0 identities stay separate and are never prepended.
# ---------------------------------------------------------------------------
T1_GENERIC_BASES = {p['code']:n['generic_stem'] for p,n in zip(PRODUCTS,NAMING_CATALOG['t1_companies'])}
T2_GENERIC_BASES = [p['facility_stem'] for p in NAMING_CATALOG['t2_companies']]

# Cohort sizes and offsets remain useful for population allocation.
T2_SECTOR_FIRM_COUNTS = [sum(T2_PRODUCT_FIRM_COUNTS[p['id']] for p in T2_PRODUCTS if p['sectorIndex'] == s) for s in range(len(T2_SECTORS))]
T2_SECTOR_FIRM_OFFSETS = [sum(T2_SECTOR_FIRM_COUNTS[:s]) for s in range(len(T2_SECTORS))]


# One namespace across the full catalog population. Reduced test worlds reserve
# the same ranges, so a company's number never depends on a run's sample size.
COMPANY_NUMBERING = {}
_next_company_number = 0
for _tier, _count in [('T-1',1),('T0',N0),('T1',N1),('T2',N2_FIRMS),('T3',N_DISTRIBUTORS)]:
    COMPANY_NUMBERING[_tier] = {'start':_next_company_number, 'count':_count}
    _next_company_number += _count


def company_number(tier, local_id=0):
    """Globally unique lower-case hexadecimal number; array IDs stay local."""
    import operator
    key = tier if isinstance(tier,str) else f'T{tier}'
    if key not in COMPANY_NUMBERING:
        raise ValueError('Unknown company tier')
    cid = operator.index(local_id)
    block = COMPANY_NUMBERING[key]
    if isinstance(local_id,bool) or not 0 <= cid < block['count']:
        raise ValueError('Company ID outside its tier range')
    return hex(block['start'] + cid)


def company_from_number(number):
    """Resolve a public hex company number to its existing (tier, local ID)."""
    import re
    if not isinstance(number,str) or not re.fullmatch(r'0[xX][0-9a-fA-F]+',number):
        raise ValueError('Company number must be hexadecimal with a 0x prefix')
    value = int(number,16)
    for tier,block in COMPANY_NUMBERING.items():
        if block['start'] <= value < block['start'] + block['count']:
            return tier,value-block['start']
    raise ValueError('Unknown company number')


def company_display_name(tier, generic_base, local_id):
    return f'{generic_base} {company_number(tier,local_id)}'


def t1_firm_name(cid):
    code = PRODUCTS[T1_FIRM_PRODUCT[int(cid)]]['code']
    base = T1_GENERIC_BASES[code]
    return company_display_name('T1',base,int(cid))


def t2_firm_name(sector, firm_id):
    base = T2_GENERIC_BASES[int(sector)]
    return company_display_name('T2',base,int(firm_id))


def company_registry(cfg):
    """Compact identities/ranges; never allocate a million display strings."""
    active = {'T-1':1,'T0':N0,'T1':N1,'T2':cfg['t2FirmCount'],'T3':cfg['distributorCount']}
    return {'format':'global-hex-v1',
            'gaia':{'tier':'T-1','id':0,'name':'Gaia','companyNumber':'0x0'},
            'ranges':{tier:{**block,'activeCount':active[tier],
                'first':hex(block['start']), 'last':hex(block['start']+block['count']-1)}
                for tier,block in COMPANY_NUMBERING.items()}}


def t1_sector(code: str) -> str:
    return PRODUCTS[T1_SECTOR_BY_CODE[code]]['sector']


# Every recipe yields one item; ancestry determines its occupied space.
for _p in T2_Catalog:
    _p['outputQty'] = 1
    _p['capacity'] = T2_ALLOCATION_CAPACITIES[_p['complexity']]
for _p in PRODUCTS:
    _p['outputQty'] = 1
    _p['capacity'] = T1_DEFAULT_CAPACITY if _p['complexity'] == 1 else T1_C2_DEFAULT_CAPACITY

# Per-product precomputed *structural* flat structure used by the hot loops.
# (Scale values — conversion, machinery, capacity, target — are cfg-driven.)
_T2_COMPLEXITY = [p['complexity'] for p in T2_PRODUCTS]
_T2_SECTOR = [p['sectorIndex'] for p in T2_PRODUCTS]
_T2_OUTPUT = [p['outputQty'] for p in T2_PRODUCTS]
# ingredients: list per product of (material_index, quantity) tuples
_T2_INGREDIENTS = [[(int(m), int(q)) for (m, q) in p['ingredients']] for p in T2_PRODUCTS]
# catalogInputRatios: T2_PRODUCTS x PRODUCTS ratio matrix
T2_INPUT_PRODUCTS = _DATA['T2_INPUT_PRODUCTS']
NI = len(T2_INPUT_PRODUCTS)
_T2_RATIOS = [[0.0] * NI for _ in range(len(T2_PRODUCTS))]
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
    return LOYALTY_ORDER_SHARE * price * (1.0 + clamp(reliability, 0.0, 1.0)) / 1.5


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
    # Demand-side valuation includes nominal overhead; eta = 2. Quantity is
    # fixed at DISTRIBUTOR_QMAX; weighted invented-product routing lives in
    # initialize_distributors, using default capacity less intermediate use.
    return {'markup': cfg['t1Markup'],
            'valuation': reference_cost,
            'switchingReference': initial_tier2_cost(product, cfg)}


def initial_tier2_cost(product, cfg) -> float:
    return (sum(q * (refinery_unit_cost(T2_INPUT_PRODUCTS[m], cfg) if m < NP else initial_tier2_cost(T2_INPUT_PRODUCTS[m], cfg)) * (1 + cfg['t1Markup'])
                for m, q in product['ingredients']) / product['outputQty']
            + conversion_cost(product['complexity'], cfg))


def reference_overhead_per_unit(product, cfg) -> float:
    """Stable own-company overhead allowance at nominal one-line capacity.

    This calibration ignores current equity, utilization and installed-line
    ownership. Actual exemption, expenses and inventory accounting are separate.
    Upstream overhead is not recursively added to the existing base-cost ladder.
    """
    c = product['complexity']
    if c <= 2:
        storage = cfg['t1C1Storage'] if c == 1 else cfg['t1C2Storage']
        capacity = cfg['t1Capacity'] if c == 1 else cfg['t1CapacityC2']
        intelligence = cfg['t1IntelligencePerTick']
    else:
        storage = cfg['storage']
        capacity = cfg['t2Capacity'][c]
        intelligence = cfg['t2IntelligencePerTick']
    return (storage / 1000 * cfg['storageRentPerThousandPerTick'] + intelligence) / capacity


def reference_refinery_cost(product, cfg) -> float:
    return refinery_unit_cost(product, cfg) + reference_overhead_per_unit(product, cfg)


def input_reference_cost(material, cfg) -> float:
    """Demand-side reference including nominal overhead for one input material.

    Serves as the halving price of the final procurement reduction:
    latent demand is the feasible purchase and the request follows the Tier 3 curve
    q = q_max / (1 + (price / V) ** t2InputElasticity). Basic elements use the raw-material cost,
    refinery products their unit cost, and T2 intermediates their initial cost.
    Each adds its own nominal-capacity rent/intelligence allowance.
    """
    p = T2_INPUT_PRODUCTS[material]
    if material < NE:
        return cfg['t1MaterialCost'] + reference_overhead_per_unit(p, cfg)
    if material < NP:
        return reference_refinery_cost(p, cfg)
    return reference_tier2_cost(p, cfg)


def distributor_switching_reference(cfg):
    """Order-routing-weighted reference, matching the Distributor buyer class."""
    weight = sum(p['distributorWeight'] for p in T2_PRODUCTS)
    return sum(p['distributorWeight'] * initial_tier2_cost(p, cfg) for p in T2_PRODUCTS) / weight


def initial_loyalty_multiples(cfg):
    """Provisional starting fees at reliability 0.5; annual 5% AOV still adapts."""
    raw = 50.0 / (cfg['baseCost'] * 1.5)
    material = 1.5 / (material_switching_reference(cfg) * 1.5)
    distributor = 1.5 / (distributor_switching_reference(cfg) * 1.5)
    return {1:raw, 2:{3:material, 4:material, 5:0.0}, 3:distributor}


def reference_tier2_cost(product, cfg=None) -> float:
    if cfg is None:
        from .config import default_cfg
        cfg = default_cfg()
    return initial_tier2_cost(product, cfg) + reference_overhead_per_unit(product, cfg)


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
