"""WorldState: NumPy typed arrays + the JS worker's initialization sequence.

The array names, dtypes and shapes mirror ``the canon machine contract (docs/design_canon.md §12)``
``sourceViews()`` / ``reset()`` exactly, so the Python port is a mechanical
transcription.  See ``docs/design_canon.md`` §6.
"""
from __future__ import annotations

import numpy as np

from . import model as M
from .config import normalize_config
from .rng import hash_seed_vec

# --------------------------------------------------------------------------
# Tier 0 profiles (worker `T0P`): the 20 extraction companies, in fixed order.
# Names follow the Star Business naming catalog §4.  Coverage is 2 four-market,
# 4 three-market, 6 two-market and 8 single-market companies.
#
# Special duties (two-market companies):
#   Mudrock Machinery Co.                     -> machinery manufacturing
#   Steam Ridge Financial Inc.                -> financial services
#   Dustline Spatial Solutions Corp.          -> warehouses, land, industrial space
#   Flare Basin Advertising Incorporated      -> advertising
#   Cloudline Games & Entertainment Corp.     -> games & entertainment
#   Hotrock Utility Company                   -> utilities
#
# Civic duties (three-market corporations):
#   Baseline Resource Corporation  -> Colony Policy
#   Union Charter Resources Inc.   -> Business Registry
#   Signal Point Resources Corp.   -> Market Intelligence
#   Commonline Resources Company   -> Community Hub
#
# Single-market companies (pure extractors, two per element):
#   Water: Bluegate Water Co. / Coldwell Ice Resources Inc.
#   Earth: Bedrock Mining Corp. / Iron County Minerals Company
#   Fire:  Furnace Creek Energy Inc. / Sunbelt Energy Corporation
#   Air:   Skyline Gas Co. / Highband Atmospherics Inc.
# --------------------------------------------------------------------------
_T0P_RAW = [
    ['Raw Materials Corp.', ['Water', 'Earth', 'Fire', 'Air']],
    ['Elements Inc.', ['Water', 'Earth', 'Fire', 'Air']],
    ['Baseline Resource Corporation', ['Water', 'Earth', 'Fire']],
    ['Union Charter Resources Inc.', ['Water', 'Earth', 'Air']],
    ['Signal Point Resources Corp.', ['Water', 'Fire', 'Air']],
    ['Commonline Resources Company', ['Earth', 'Fire', 'Air']],
    ['Mudrock Machinery Co.', ['Water', 'Earth']],
    ['Steam Ridge Financial Inc.', ['Water', 'Fire']],
    ['Cloudline Games & Entertainment Corporation', ['Water', 'Air']],
    ['Hotrock Utility Company', ['Earth', 'Fire']],
    ['Dustline Spatial Solutions Corp.', ['Earth', 'Air']],
    ['Flare Basin Advertising Incorporated', ['Fire', 'Air']],
    ['Bluegate Water Co.', ['Water']],
    ['Coldwell Ice Resources Inc.', ['Water']],
    ['Bedrock Mining Corp.', ['Earth']],
    ['Iron County Minerals Company', ['Earth']],
    ['Furnace Creek Energy Inc.', ['Fire']],
    ['Sunbelt Energy Corporation', ['Fire']],
    ['Skyline Gas Co.', ['Air']],
    ['Highband Atmospherics Inc.', ['Air']],
]
_EI = {element: i for i, element in enumerate(M.ELEMENTS)}
T0P = [{'id': i, 'name': name, 'elements': elements,
        'element_indices': sorted(_EI[element] for element in elements)}
       for i, (name, elements) in enumerate(_T0P_RAW)]

# Tier 1 cohort -> native product code (worker `T1P`).
T1P = [{'name': p['companyName'], 'product': p['code']} for p in M.PRODUCTS]


def quantize_whole(x: float, floor: float = 0.0) -> float:
    return M.round_to_cent(x)


def quantize_round(x: float, floor: float = 0.0) -> float:
    return M.round_to_cent(x)


# --------------------------------------------------------------------------
# Array schema (name -> (dtype, length)).  ML = min(MAX_T2_LINES, N2 * M4).
# --------------------------------------------------------------------------
_DTYPES = {
    'f64': np.float64, 'f32': np.float32,
    'u8': np.uint8, 'u16': np.uint16, 'u32': np.uint32,
    'i8': np.int8, 'i16': np.int16, 'i32': np.int32,
}


def _learn(prefix, n):
    return [
        (f'{prefix}LearnOpportunity', 'f64', n),
        (f'{prefix}LearnPotentialOpportunity', 'f64', n),
        (f'{prefix}LearnProfit', 'f64', n),
        (f'{prefix}LearnSales', 'f64', n),
        (f'{prefix}LearnTicks', 'u32', n),
        (f'{prefix}LearnPrevious', 'f64', n),
        (f'{prefix}LearnDemand', 'f64', n),
        (f'{prefix}LearnStep', 'f64', n),
        (f'{prefix}LearnDirection', 'i8', n),
        (f'{prefix}Demand', 'f64', n),
        (f'{prefix}DemandEMA', 'f64', n),
    ]


def _array_spec(cfg):
    NE, NP, N0, N1 = M.NE, M.NP, M.N0, M.N1
    # Firm-level and end-user arrays are ALWAYS allocated at full population
    # (mirrors sourceViews()); only the sparse line arrays scale with
    # cfg.t2FirmCount.  cfg.consumerCount / cfg.t2FirmCount merely limit how
    # many entries are initialized and processed.
    N2F = M.N2_FIRMS
    NUF = M.N_CONSUMERS
    ML = min(M.MAX_T2_LINES, cfg['t2FirmCount'])  # single-machine: one line per firm
    n_t2 = len(M.T2_PRODUCTS)  # 200

    spec = [
        ('t0Opportunities', 'u32', NE),
        ('t1Opportunities', 'u32', NP),
        ('t2Opportunities', 'u32', n_t2),
        ('t2PotentialOrders', 'u32', n_t2),
    ]
    spec += _learn('t0', N0 * NE)
    spec += _learn('t1', N1 * NP)
    # t2 learner/demand arrays are MAX_T2_LINES (sourceViews passes MAX_T2_LINES
    # to priceLearningViews), NOT the cfg-scaled ML used by the line arrays.
    spec += _learn('t2', M.MAX_T2_LINES)
    spec += [
        ('difficulty', 'f64', NE),
        ('t0Inv', 'f64', N0 * NE),
        ('t0Cash', 'f64', N0),
        ('t0Controller', 'u8', N0),
        ('t0Price', 'f64', N0 * NE),
        ('t0PlayerPrice', 'f64', N0 * NE),
        ('t0Cost', 'f64', N0 * NE),
        ('t0InvBasis', 'f64', N0 * NE),
        ('t0COGS', 'f64', N0 * NE),
        ('t0SalesEMA', 'f64', N0 * NE),
        ('t0PrevPrice', 'f64', N0 * NE),
        ('t0Rel', 'f64', N0 * NE),
        ('t0Stability', 'f64', N0 * NE),
        ('t0Req', 'f64', NE),
        ('t0FundedReq', 'f64', NE),
        ('t0Fulfilled', 'f64', NE),
        ('t0Sold', 'f64', N0 * NE),
        ('t0Revenue', 'f64', N0 * NE),
        ('raw', 'f64', N1 * NE),
        ('rawBasis', 'f64', N1 * NE),
        ('t1Cash', 'f64', N1),
        ('t1EqBook', 'f64', N1),
        ('t1Controller', 'u8', N1),
        ('t1Operates', 'u8', N1 * NP),
        ('t1Price', 'f64', N1 * NP),
        ('t1PrevPrice', 'f64', N1 * NP),
        ('t1PriceStability', 'f64', N1 * NP),
        ('t1Rel', 'f64', N1 * NP),
        ('t1UnitCost', 'f64', N1 * NP),
        ('t1ReplacementCost', 'f64', N1 * NP),
        ('t1Fin', 'f64', N1 * NP),
        ('t1FinBasis', 'f64', N1 * NP),
        ('t1SalesEMA', 'f64', N1 * NP),
        ('t1Sold', 'f64', N1 * NP),
        ('t1Revenue', 'f64', N1 * NP),
        ('t1COGS', 'f64', N1 * NP),
        ('t1IntermediateSold', 'f64', NP),
        ('t1IntermediateRevenue', 'f64', NP),
        ('t1InputNeed', 'f64', N1 * NE),
        ('t1PurchaseReq', 'f64', N1 * NE),
        ('t1LastBuy', 'f64', N1 * NE),
        ('t1Bought', 'f64', N1),
        ('preferredWholesale', 'i32', N1 * NE),
        ('playerPrice', 'f64', N1 * NP),
        ('active', 'f64', NP),
        ('potential', 'f64', NP),
        ('fulfilled', 'f64', NP),
        ('priceLost', 'f64', NP),
        ('stockUnmet', 'f64', NP),
        ('t0RelAttempts', 'f64', N0 * NE),
        ('t0RelChecks', 'f64', N0 * NE),
        ('t0RelAvailable', 'f64', N0 * NE),
        ('t0RelPriceSum', 'f64', N0 * NE),
        ('t0RelPriceSamples', 'u32', N0 * NE),
        ('t1RelAttempts', 'f64', N1 * NP),
        ('t1RelAvailChecks', 'f64', N1 * NP),
        ('t1RelAvailable', 'f64', N1 * NP),
        ('t1RelPriceSum', 'f64', N1 * NP),
        ('t1RelPriceSamples', 'u32', N1 * NP),
        ('t2Cash', 'f64', N2F),
        ('t2Bought', 'f64', N2F),
        ('t2EqBook', 'f64', N2F),
        ('t2LastSaleTick', 'u32', N2F),
        ('t2Raw', 'f64', N2F * NE),
        ('t2RawBasis', 'f64', N2F * NE),
        ('t2T1Raw', 'f64', N2F * NP),
        ('t2T1Basis', 'f64', N2F * NP),
        ('t2Controller', 'u8', N2F),
        ('t2Capability', 'u8', N2F),
        ('t2Sector', 'u8', N2F),
        ('t2LineFirm', 'u16', ML),
        ('t2LineProduct', 'u16', ML),
        ('t2Fin', 'f64', ML),
        ('t2FinBasis', 'f64', ML),
        ('t2UnitCost', 'f64', ML),
        ('t2ReplacementCost', 'f64', ML),
        ('t2Price', 'f64', ML),
        ('t2PlayerPrice', 'f64', ML),
        ('t2SalesEMA', 'f64', ML),
        ('t2Sold', 'f64', ML),
        ('t2Revenue', 'f64', ML),
        ('t2COGS', 'f64', ML),
        ('t2ReferenceCost', 'f64', M.T2_Catalog_COUNT),
        ('t2SectorProducts', 'u16', len(M.T2_SECTORS) * n_t2),
        ('t2SectorProductWeight', 'f64', len(M.T2_SECTORS) * n_t2),
        ('t2SectorCount', 'u8', len(M.T2_SECTORS)),
        ('t2Online', 'u8', N2F),
        ('t2FirmLines', 'i32', N2F * M.T2_MAX_PRODUCTS_PER_FIRM),
        ('t2FirmLineCount', 'u8', N2F),
        ('t2Preferred', 'i32', N2F * NP),
        ('t2Made', 'f64', ML),
        ('t2Rel', 'f64', ML),
        ('t2RelAttempts', 'u32', ML),
        ('t2RelAvailable', 'u32', ML),
        ('t2RelPriceSum', 'f64', ML),
        ('t2RelPriceSamples', 'u32', ML),
        ('t2MonthSold', 'f64', ML),
        ('t2MonthlyCapacity', 'f64', ML),
        ('consumerProduct', 'i16', NUF),
        ('consumerPreferredSupplier', 'i32', NUF),
        ('consumerLastMarket', 'i16', NUF),
        ('consumerLastSupplier', 'i32', NUF),
        ('consumerLastQ', 'u16', NUF),
        ('consumerLastFulfilled', 'u16', NUF),
        ('consumerQMax', 'f32', NUF),
        ('consumerChoke', 'f32', NUF),
        ('consumerEta', 'f32', NUF),
        ('marketPotential', 'f64', NP + n_t2),
        ('marketActive', 'f64', NP + n_t2),
        ('marketFulfilled', 'f64', NP + n_t2),
        ('marketPriceLost', 'f64', NP + n_t2),
        ('marketStockUnmet', 'f64', NP + n_t2),
    ]
    return spec


class WorldState:
    """Flat record of NumPy typed arrays + scalars, mirroring the JS ``world``."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._names = []
        for name, dt, n in _array_spec(cfg):
            setattr(self, name, np.zeros(n, dtype=_DTYPES[dt]))
            self._names.append(name)
        self.t2LineCount = 0
        self.costSinks = 0.0
        self.equipmentSinks = 0.0
        self._init_loyalty_regime(cfg)

    def _init_loyalty_regime(self, cfg):
        # Adaptive loyalty-multiple regime (§12.6): an EMA of the average order
        # value per buyer class drives the switching-charge multiple M, so the
        # charge tracks ~10% of a typical order as prices/margins drift.
        self.lmUnitCost1 = float(cfg['baseCost'])                                 # raw
        self.lmUnitCost2 = float(cfg['t1MaterialCost'] + cfg['conversionFactor'])  # material
        self.lmUnitCost3 = self._mean_t2_unit_cost(cfg)                            # good (mean)
        self.lm1 = float(cfg['loyaltyMultiple'][1])
        self.lm2 = np.array([cfg['loyaltyMultiple'][2][c] for c in (3, 4, 5)], dtype=np.float64)
        self.lm3 = float(cfg['loyaltyMultiple'][3])
        self.aov1 = self.lm1 * self.lmUnitCost1 * 1.5 / 0.10
        self.aov2 = self.lm2 * self.lmUnitCost2 * 1.5 / 0.10
        self.aov3 = self.lm3 * self.lmUnitCost3 * 1.5 / 0.10
        # per-tick accumulators for the T2 material AOV (split by complexity)
        self.t2MatSpend = np.zeros(3, dtype=np.float64)
        self.t2MatOrders = np.zeros(3, dtype=np.float64)
        # per-tick loyalty accounting: disloyal supplier switches and charge paid,
        # indexed by buyer tier [T1, T2, T3]
        self.loyaltySwitches = np.zeros(3, dtype=np.float64)
        self.loyaltyPenalties = np.zeros(3, dtype=np.float64)

    @staticmethod
    def _mean_t2_unit_cost(cfg):
        return sum(cfg['t2MaterialCost'] + cfg['conversionFactor'] * max(1, p['complexity'] - 1)
                   for p in M.T2_PRODUCTS) / len(M.T2_PRODUCTS)

    @property
    def array_names(self):
        return list(self._names)

    def arrays(self):
        for name in self._names:
            yield name, getattr(self, name)


def zero(world: WorldState) -> None:
    for name in world.array_names:
        getattr(world, name).fill(0)


# --------------------------------------------------------------------------
# Tier 2 line installation (worker `addTier2Line`).
# --------------------------------------------------------------------------
def _has_tier2_product(world, firm, product_id):
    for slot in range(int(world.t2FirmLineCount[firm])):
        if world.t2LineProduct[world.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot]] == product_id:
            return True
    return False


def add_tier2_line(world, cfg, firm, product, paid=True):
    firm = int(firm)
    if not (0 <= firm < cfg['t2FirmCount']) or product is None:
        raise ValueError('Invalid Tier 2 company or product.')
    if product['complexity'] not in M.TIER_BOUNDARIES['T2']:
        raise ValueError('Tier 2 firms can only manufacture C-3 through C-5 products.')
    if world.t2FirmLineCount[firm] >= M.T2_MAX_PRODUCTS_PER_FIRM or world.t2LineCount >= len(world.t2Fin):
        raise ValueError('Company or economy product-line limit reached.')
    if _has_tier2_product(world, firm, product['id']):
        raise ValueError('This product line is already installed.')
    if product['complexity'] > world.t2Capability[firm] or world.t2Sector[firm] != product['sectorIndex']:
        raise ValueError('Machinery requires an eligible sector and capability.')
    if paid and world.t2Cash[firm] < cfg['t2Machinery'][product['complexity']]:
        raise ValueError('Insufficient cash.')
    line = world.t2LineCount
    world.t2LineCount += 1
    world.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + int(world.t2FirmLineCount[firm])] = line
    world.t2FirmLineCount[firm] = int(world.t2FirmLineCount[firm]) + 1
    world.t2LineFirm[line] = firm
    world.t2LineProduct[line] = product['id']
    world.t2UnitCost[line] = M.initial_tier2_cost(product, cfg)
    world.t2LearnStep[line] = 1
    world.t2Price[line] = M.round_to_cent(max(M.MIN_UNIT_PRICE, world.t2UnitCost[line] * (1 + M.tier2_starting_markup(product, cfg))))
    world.t2LearnPrevious[line] = float('nan')
    world.t2LearnDirection[line] = 1 if ((firm + cfg['seed']) % 2) else -1
    world.t2PlayerPrice[line] = float('nan')
    world.t2Rel[line] = 0.5
    world.t2SalesEMA[line] = 0
    world.t2DemandEMA[line] = 0
    if paid:
        mach = cfg['t2Machinery'][product['complexity']]
        world.t2Cash[firm] -= mach
        world.equipmentSinks += mach
        world.t2EqBook[firm] += mach
    return line


def initialize_tier2(world, cfg):
    world.t2LineCount = 0
    prod_id = np.array([p['id'] for p in M.T2_PRODUCTS], dtype=np.int64)
    prod_comp = np.array([p['complexity'] for p in M.T2_PRODUCTS], dtype=np.int64)
    prod_sector = np.array([p['sectorIndex'] for p in M.T2_PRODUCTS], dtype=np.int64)
    world.t2ReferenceCost[prod_id] = cfg['t2MaterialCost'] + cfg['conversionFactor'] * np.maximum(1, prod_comp - 1)
    world.t2FirmLines.fill(-1)
    world.t2Preferred.fill(-1)
    world.t2PlayerPrice.fill(float('nan'))
    world.t2Rel.fill(0.5)
    world.t2SectorCount.fill(0)
    n_t2 = len(M.T2_PRODUCTS)
    for product in M.T2_PRODUCTS:
        count = int(world.t2SectorCount[product['sectorIndex']])
        world.t2SectorCount[product['sectorIndex']] = count + 1
        index = product['sectorIndex'] * n_t2 + count
        world.t2SectorProducts[index] = product['id']
        # Demand routing weight ∝ supply (firms × capacity, the 108:12:1 ratio):
        # more consumers are routed to higher-supply products, so total demand
        # scales with supply while the per-consumer quantity stays small.
        supply = M.T2_FIRMS_PER_PRODUCT[product['complexity']] * cfg['t2Capacity'][product['complexity']]
        world.t2SectorProductWeight[index] = (world.t2SectorProductWeight[index - 1] if count else 0) + supply

    # Canon topology (§3): 60,000 single-machine firms — 1,800 C-3 / 300 C-4 /
    # 50 C-5 per product (reverse 6:3:1 ratio).  Each firm owns exactly one line.
    # A reduced cfg['t2FirmCount'] takes a stratified prefix (C-3 first, then
    # C-4, then C-5) so small regression fixtures stay representative.
    target_firms = cfg['t2FirmCount']
    per_product = M.T2_FIRMS_PER_PRODUCT
    assigned = []
    for product in M.T2_PRODUCTS:
        cnt = min(per_product[product['complexity']], target_firms - len(assigned))
        if cnt <= 0:
            break
        assigned.extend([product['id']] * cnt)
    pid = np.array(assigned, dtype=np.int64)
    n = pid.size
    firms = np.arange(n)
    comp = prod_comp[pid]
    sector = prod_sector[pid]
    mach = np.array([cfg['t2Machinery'][int(c)] for c in comp], dtype=np.float64)
    unit_cost = cfg['t2MaterialCost'] + cfg['conversionFactor'] * np.maximum(1, comp - 1)
    price = np.floor(np.maximum(M.MIN_UNIT_PRICE, unit_cost * (1.0 + cfg['t1Markup'])) * 100.0 + 0.5) / 100.0

    world.t2Capability[:n] = 5
    world.t2Sector[:n] = sector
    world.t2FirmLines[firms * M.T2_MAX_PRODUCTS_PER_FIRM] = firms
    world.t2FirmLineCount[:n] = 1
    world.t2LineFirm[:n] = firms
    world.t2LineProduct[:n] = pid
    world.t2UnitCost[:n] = unit_cost
    world.t2LearnStep[:n] = 1
    world.t2Price[:n] = price
    world.t2LearnPrevious[:n] = float('nan')
    world.t2LearnDirection[:n] = np.where(((firms + cfg['seed']) % 2) == 1, np.int8(1), np.int8(-1))
    world.t2PlayerPrice[:n] = float('nan')
    world.t2Rel[:n] = 0.5
    world.t2SalesEMA[:n] = 0
    world.t2DemandEMA[:n] = 0
    world.t2Cash[:n] = cfg['t2Equity'] - cfg['t2License'] - mach
    world.t2EqBook[:n] = mach
    world.t2LineCount = n


def initialize_consumers(world, cfg):
    world.consumerPreferredSupplier.fill(-1)
    world.consumerLastMarket.fill(-1)
    world.consumerLastSupplier.fill(-1)
    seed = cfg['seed']
    n_t2 = len(M.T2_PRODUCTS)
    # Per-product supply weight = firms × capacity (canon §5: the 108:12:1 ratio across
    # C-3 / C-4 / C-5), so the number of consumers interested in a product scales with
    # its supply rather than being spread evenly.
    supply = np.array([M.T2_FIRMS_PER_PRODUCT[p['complexity']] * cfg['t2Capacity'][p['complexity']]
                       for p in M.T2_PRODUCTS], dtype=np.float64)
    cum = np.cumsum(supply)
    total = cum[-1]
    world.consumerQMax.fill(M.CONSUMER_QMAX)
    n = cfg['consumerCount']
    cids = np.arange(n)
    b = hash_seed_vec(seed, 9000000 + cids)
    draw = hash_seed_vec(seed, 7000000 + cids).astype(np.float64) / 4294967296.0 * total
    offset = np.searchsorted(cum, draw, side='left')
    np.minimum(offset, n_t2 - 1, out=offset)
    world.consumerProduct[:n] = (M.NP + offset).astype(np.int16)
    world.consumerChoke[:n] = (cfg['chokeMin'] + b.astype(np.float64) / 4294967296.0
                               * (cfg['chokeMax'] - cfg['chokeMin'])).astype(np.float32)
    world.consumerEta[:n] = cfg['elasticity']


def reset_world(cfg):
    """Normalize config, allocate and initialize the world (JS worker ``reset``)."""
    cfg = normalize_config(cfg)
    world = WorldState(cfg)
    seed = cfg['seed']
    NE, NP, N0, N1 = M.NE, M.NP, M.N0, M.N1

    zero(world)
    for tier, width in (('t0', NE), ('t1', NP), ('t2', None)):
        learn_dir = getattr(world, f'{tier}LearnDirection')
        getattr(world, f'{tier}LearnPrevious').fill(float('nan'))
        getattr(world, f'{tier}LearnStep').fill(1)
        n = len(learn_dir)
        if tier == 't0':
            firms = np.arange(n) // NE
        elif tier == 't1':
            firms = np.arange(n) // NP
        else:
            firms = np.arange(n)
        learn_dir[:] = np.where(((firms + seed) % 2) == 1, np.int8(1), np.int8(-1))

    world.difficulty.fill(cfg['difficultyTarget'])
    for i in range(N0):
        n_el = len(T0P[i]['element_indices'])
        world.t0Cash[i] = cfg['t0Equity'] - cfg['t0License'] - n_el * cfg['t0Machinery'] - cfg['t0Reserve']
    world.t0Controller.fill(0)
    world.t0PlayerPrice.fill(float('nan'))
    world.t0Rel.fill(0.5)
    world.t0Stability.fill(1)
    world.t0Req.fill(0)
    world.t0Fulfilled.fill(0)
    world.t0PrevPrice.fill(float('nan'))
    world.t0Price.fill(float('nan'))
    world.t0Cost.fill(0)
    for i in range(N0):
        for element in range(NE):
            if M.ELEMENTS[element] in T0P[i]['elements']:
                idx = i * NE + element
                cost = cfg['baseCost'] * cfg['difficultyTarget']
                world.t0Cost[idx] = cost
                world.t0Price[idx] = quantize_whole(cost * (1 + cfg['t0Markup']))
                world.t0PrevPrice[idx] = world.t0Price[idx]

    world.t1Cash.fill(cfg['t1Equity'] - cfg['t1License'] - cfg['t1Machinery'])
    world.t1EqBook.fill(0)
    world.t1Controller.fill(0)
    world.t1Operates.fill(0)
    world.t1Price.fill(float('nan'))
    world.t1PrevPrice.fill(float('nan'))
    world.t1PriceStability.fill(1)
    world.t1Rel.fill(0)
    world.t1UnitCost.fill(0)
    world.t1Fin.fill(0)
    world.t1FinBasis.fill(0)
    world.t1SalesEMA.fill(0)
    world.t1LastBuy.fill(float('nan'))
    world.preferredWholesale.fill(-1)
    world.playerPrice.fill(float('nan'))

    for cid in range(N1):
        code = T1P[cid // 100]['product']
        pi = next(i for i, p in enumerate(M.PRODUCTS) if p['code'] == code)
        p = M.PRODUCTS[pi]
        eq = cfg['t1Machinery']                        # canon $15k flat
        uc = M.unit_cost(p['complexity'], cfg)         # canon $1.25 reference unit cost
        price = quantize_round(uc * (1 + M.t2_markup(p['complexity'], cfg)), uc)  # first-guess markup 0.25
        world.t1EqBook[cid] = eq
        world.t1Operates[cid * NP + pi] = 1
        world.t1Rel[cid * NP + pi] = 0.5
        world.t1UnitCost[cid * NP + pi] = uc
        world.t1Price[cid * NP + pi] = price
        world.t1PrevPrice[cid * NP + pi] = price

    initialize_tier2(world, cfg)
    initialize_consumers(world, cfg)

    return cfg, world
