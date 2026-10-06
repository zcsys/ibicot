"""WorldState: NumPy typed arrays + the JS worker's initialization sequence.

The array names, dtypes and shapes mirror ``the canon machine contract (spec/design_canon.md §12)``
``sourceViews()`` / ``reset()`` exactly, so the Python port is a mechanical
transcription.  See ``spec/design_canon.md`` §6.
"""
from __future__ import annotations

import numpy as np

from . import model as M
from .config import normalize_config
from .rng import hash_seed

# --------------------------------------------------------------------------
# Tier 0 profiles (worker `T0P`): name + element names, in fixed order.
# --------------------------------------------------------------------------
_T0P_RAW = [
    ['Atlas Resources', ['Water', 'Earth', 'Fire', 'Air']],
    ['Axiom Extraction Systems', ['Water', 'Earth', 'Fire', 'Air']],
    ['Orbital Materials Network', ['Water', 'Earth', 'Fire']],
    ['Galactic Resource Consortium', ['Water', 'Earth', 'Air']],
    ['Gaia Extraction Works', ['Water', 'Fire', 'Air']],
    ['Confluence Resources', ['Earth', 'Fire', 'Air']],
    ['Hydro Mineral Works', ['Water', 'Earth']],
    ['Solar Resource Works', ['Water', 'Fire']],
    ['Atmospheric Resource Works', ['Water', 'Air']],
    ['Thermal Mineral Works', ['Earth', 'Fire']],
    ['Mineral and Gas Works', ['Earth', 'Air']],
    ['Thermal and Gas Works', ['Fire', 'Air']],
    ['Deepwell Ice Extraction', ['Water']],
    ['Comet Ice Harvesting', ['Water']],
    ['Bedrock Mineral Extraction', ['Earth']],
    ['Stratum Mining', ['Earth']],
    ['Helios Solar Collection', ['Fire']],
    ['Mantle Geothermal Works', ['Fire']],
    ['Cirrus Atmospheric Capture', ['Air']],
    ['Zephyr Gas Separation', ['Air']],
]
_EI = {e: i for i, e in enumerate(M.ELEMENTS)}
T0P = [{'id': i, 'name': name, 'elements': elements,
        'element_indices': sorted(_EI[e] for e in elements)}
       for i, (name, elements) in enumerate(_T0P_RAW)]

# Tier 1 cohort -> native product code (worker `T1P`).
T1P = [{'name': p['companyName'], 'product': p['code']} for p in M.PRODUCTS]


def quant_w(x: float, floor: float = 0.0) -> float:
    return M.round_to_cent(x)


def quant_r(x: float, floor: float = 0.0) -> float:
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
        (f'{prefix}LearnStock', 'f64', n),
        (f'{prefix}LearnStep', 'f64', n),
        (f'{prefix}LearnDirection', 'i8', n),
        (f'{prefix}Demand', 'f64', n),
        (f'{prefix}DemandEMA', 'f64', n),
    ]


def _array_spec(cfg):
    NE, NP, N0, N1 = M.NE, M.NP, M.N0, M.N1
    # Firm-level and end-user arrays are ALWAYS allocated at full population
    # (mirrors sourceViews()); only the sparse line arrays scale with
    # cfg.t2FirmCount.  cfg.endUserCount / cfg.t2FirmCount merely limit how
    # many entries are initialized and processed.
    N2F = M.N2_FIRMS
    NUF = M.N_END_USERS
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
        ('t0Ful', 'f64', NE),
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
        ('t1Rev', 'f64', N1 * NP),
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
        ('t0RelFulfilled', 'f64', N0 * NE),
        ('t0RelChecks', 'f64', N0 * NE),
        ('t0RelAvailable', 'f64', N0 * NE),
        ('t0RelPriceSum', 'f64', N0 * NE),
        ('t0RelPriceSamples', 'u32', N0 * NE),
        ('t1RelAttempts', 'f64', N1 * NP),
        ('t1RelFulfilled', 'f64', N1 * NP),
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
        ('t2ReferenceCost', 'f64', M.T2_CATALOGUE_COUNT),
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
        ('t2RelFulfilled', 'u32', ML),
        ('t2RelAvailable', 'u32', ML),
        ('t2RelPriceSum', 'f64', ML),
        ('t2RelPriceSamples', 'u32', ML),
        ('t2MonthSold', 'f64', ML),
        ('t2MonthlyCapacity', 'f64', ML),
        ('endBasketCount', 'u8', NUF),
        ('endBasket', 'u8', NUF * 5),
        ('endNeedProduct', 'i16', NUF * 5),
        ('endPreferredProduct', 'i16', NUF * 5),
        ('endPreferredSupplier', 'i32', NUF * 5),
        ('endLastMarket', 'i16', NUF),
        ('endLastSupplier', 'i32', NUF),
        ('endLastQ', 'u16', NUF),
        ('endLastFulfilled', 'u16', NUF),
        ('endPrimarySector', 'u8', NUF),
        ('endSecondarySector', 'u8', NUF),
        ('endQMax', 'f32', NUF),
        ('endChoke', 'f32', NUF),
        ('endEta', 'f32', NUF),
        ('endPotential', 'f64', NP + n_t2),
        ('endActive', 'f64', NP + n_t2),
        ('endFulfilled', 'f64', NP + n_t2),
        ('endPriceLost', 'f64', NP + n_t2),
        ('endStockUnmet', 'f64', NP + n_t2),
    ]
    return spec


class WorldState:
    """Flat record of NumPy typed arrays + scalars, mirroring the JS ``W``."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._names = []
        for name, dt, n in _array_spec(cfg):
            setattr(self, name, np.zeros(n, dtype=_DTYPES[dt]))
            self._names.append(name)
        self.t2LineCount = 0
        self.costSinks = 0.0
        self.equipmentSinks = 0.0

    @property
    def array_names(self):
        return list(self._names)

    def arrays(self):
        for name in self._names:
            yield name, getattr(self, name)


def zero(W: WorldState) -> None:
    for name in W.array_names:
        getattr(W, name).fill(0)


# --------------------------------------------------------------------------
# Tier 2 line installation (worker `addTier2Line`).
# --------------------------------------------------------------------------
def _has_tier2_product(W, firm, product_id):
    for slot in range(int(W.t2FirmLineCount[firm])):
        if W.t2LineProduct[W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot]] == product_id:
            return True
    return False


def add_tier2_line(W, cfg, firm, product, paid=True):
    firm = int(firm)
    if not (0 <= firm < cfg['t2FirmCount']) or product is None:
        raise ValueError('Invalid Tier 2 company or product.')
    if product['complexity'] not in M.TIER_BOUNDARIES['T2']:
        raise ValueError('Tier 2 firms can only manufacture C-3 through C-5 products.')
    if W.t2FirmLineCount[firm] >= M.T2_MAX_PRODUCTS_PER_FIRM or W.t2LineCount >= len(W.t2Fin):
        raise ValueError('Company or economy product-line limit reached.')
    if _has_tier2_product(W, firm, product['id']):
        raise ValueError('This product line is already installed.')
    if product['complexity'] > W.t2Capability[firm] or W.t2Sector[firm] != product['sectorIndex']:
        raise ValueError('Machinery requires an eligible sector and capability.')
    if paid and W.t2Cash[firm] < cfg['t2Machinery'][product['complexity']]:
        raise ValueError('Insufficient cash.')
    line = W.t2LineCount
    W.t2LineCount += 1
    W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + int(W.t2FirmLineCount[firm])] = line
    W.t2FirmLineCount[firm] = int(W.t2FirmLineCount[firm]) + 1
    W.t2LineFirm[line] = firm
    W.t2LineProduct[line] = product['id']
    W.t2UnitCost[line] = M.initial_tier2_cost(product, cfg)
    W.t2LearnStep[line] = 1
    W.t2Price[line] = M.round_to_cent(max(M.MIN_UNIT_PRICE, W.t2UnitCost[line] * (1 + M.tier2_starting_markup(product, cfg))))
    W.t2LearnPrevious[line] = float('nan')
    W.t2LearnDirection[line] = 1 if ((firm + cfg['seed']) % 2) else -1
    W.t2PlayerPrice[line] = float('nan')
    W.t2Rel[line] = 0.5
    W.t2SalesEMA[line] = 0
    W.t2DemandEMA[line] = 0
    if paid:
        mach = cfg['t2Machinery'][product['complexity']]
        W.t2Cash[firm] -= mach
        W.equipmentSinks += mach
        W.t2EqBook[firm] += mach
    return line


def initialize_tier2(W, cfg):
    W.t2LineCount = 0
    for p in M.T2_PRODUCTS:
        W.t2ReferenceCost[p['id']] = M.reference_tier2_cost(p, cfg)
    W.t2FirmLines.fill(-1)
    W.t2Preferred.fill(-1)
    W.t2PlayerPrice.fill(float('nan'))
    W.t2Rel.fill(0.5)
    W.t2SectorCount.fill(0)
    n_t2 = len(M.T2_PRODUCTS)
    for product in M.T2_PRODUCTS:
        count = int(W.t2SectorCount[product['sectorIndex']])
        W.t2SectorCount[product['sectorIndex']] = count + 1
        index = product['sectorIndex'] * n_t2 + count
        W.t2SectorProducts[index] = product['id']
        # Demand routing weight ∝ supply (firms × capacity, the 108:12:1 ratio):
        # more consumers are routed to higher-supply products, so total demand
        # scales with supply while the per-consumer quantity stays small.
        supply = M.T2_FIRMS_PER_PRODUCT[product['complexity']] * cfg['t2Capacity'][product['complexity']]
        W.t2SectorProductWeight[index] = (W.t2SectorProductWeight[index - 1] if count else 0) + supply

    # Canon topology (§3): 60,000 single-machine firms — 1,800 C-3 / 300 C-4 /
    # 50 C-5 per product (reverse 6:3:1 ratio).  Each firm owns exactly one line.
    # A reduced cfg['t2FirmCount'] takes a stratified prefix (C-3 first, then
    # C-4, then C-5) so small regression fixtures stay representative.
    firm = 0
    target_firms = cfg['t2FirmCount']
    per_product = M.T2_FIRMS_PER_PRODUCT
    for product in M.T2_PRODUCTS:
        for _ in range(per_product[product['complexity']]):
            if firm >= target_firms:
                break
            W.t2Capability[firm] = 5
            W.t2Sector[firm] = product['sectorIndex']
            add_tier2_line(W, cfg, firm, product, False)
            mach = cfg['t2Machinery'][product['complexity']]
            W.t2Cash[firm] = cfg['t2Equity'] - cfg['t2License'] - mach
            W.t2EqBook[firm] = mach
            firm += 1
        if firm >= target_firms:
            break


def initialize_consumers(W, cfg):
    W.endNeedProduct.fill(-1)
    W.endPreferredProduct.fill(-1)
    W.endPreferredSupplier.fill(-1)
    W.endLastMarket.fill(-1)
    W.endLastSupplier.fill(-1)
    seed = cfg['seed']
    total_weight = sum(M.T2_SECTOR_WEIGHTS)
    nsector = len(M.T2_SECTORS)
    for cid in range(cfg['endUserCount']):
        a = hash_seed(seed, 8000000 + cid)
        b = hash_seed(seed, 9000000 + cid)
        count = 2 + a % 4
        draw = hash_seed(seed, 10000000 + cid) / 4294967296 * total_weight
        primary = nsector - 1
        for sector in range(nsector):
            draw -= M.T2_SECTOR_WEIGHTS[sector]
            if draw < 0:
                primary = sector
                break
        W.endBasketCount[cid] = count
        W.endPrimarySector[cid] = primary
        W.endBasket[cid * 5] = primary
        sectors = M.T2_ADJACENCY[primary]
        for slot in range(1, count):
            if slot == 1:
                sector = sectors[b % len(sectors)]
            else:
                sector = (primary + 1 + ((b >> (slot * 3)) % (nsector - 1))) % nsector
            duplicate = True
            while duplicate:
                duplicate = False
                for previous in range(slot):
                    if W.endBasket[cid * 5 + previous] == sector:
                        duplicate = True
                if duplicate:
                    sector = (sector + 1) % nsector
            W.endBasket[cid * 5 + slot] = sector
        W.endSecondarySector[cid] = W.endBasket[cid * 5 + 1]
        W.endQMax[cid] = cfg['demandQtyMin'] + a % (cfg['demandQtyMax'] - cfg['demandQtyMin'] + 1)
        W.endChoke[cid] = cfg['vmin'] + b / 4294967296 * (cfg['vmax'] - cfg['vmin'])
        W.endEta[cid] = cfg['elasticity']


def reset_world(cfg):
    """Normalize config, allocate and initialize the world (JS worker ``reset``)."""
    cfg = normalize_config(cfg)
    W = WorldState(cfg)
    seed = cfg['seed']
    NE, NP, N0, N1 = M.NE, M.NP, M.N0, M.N1

    zero(W)
    for tier, width in (('t0', NE), ('t1', NP), ('t2', None)):
        learn_dir = getattr(W, f'{tier}LearnDirection')
        getattr(W, f'{tier}LearnPrevious').fill(float('nan'))
        getattr(W, f'{tier}LearnStep').fill(1)
        for i in range(len(learn_dir)):
            if tier == 't0':
                firm = i // NE
            elif tier == 't1':
                firm = i // NP
            else:
                firm = i
            learn_dir[i] = 1 if ((firm + seed) % 2) else -1

    W.difficulty.fill(cfg['dbar'])
    W.t0Cash.fill(cfg['t0Equity'])
    W.t0Controller.fill(0)
    W.t0PlayerPrice.fill(float('nan'))
    W.t0Rel.fill(0.5)
    W.t0Stability.fill(1)
    W.t0Req.fill(0)
    W.t0Ful.fill(0)
    W.t0PrevPrice.fill(float('nan'))
    W.t0Price.fill(float('nan'))
    W.t0Cost.fill(0)
    for i in range(N0):
        for e in range(NE):
            if M.ELEMENTS[e] in T0P[i]['elements']:
                idx = i * NE + e
                cost = cfg['baseCost'] * cfg['dbar']
                W.t0Cost[idx] = cost
                W.t0DemandEMA[idx] = cfg['targetInventory'] / len(T0P[i]['elements']) / cfg['inventoryCoverageTicks']
                W.t0Price[idx] = quant_w(cost * (1 + cfg['markup']))
                W.t0PrevPrice[idx] = W.t0Price[idx]

    W.t1Cash.fill(cfg['t1Equity'] - cfg['t1License'] - cfg['t1Machinery'])
    W.t1EqBook.fill(0)
    W.t1Controller.fill(0)
    W.t1Operates.fill(0)
    W.t1Price.fill(float('nan'))
    W.t1PrevPrice.fill(float('nan'))
    W.t1PriceStability.fill(1)
    W.t1Rel.fill(0)
    W.t1UnitCost.fill(0)
    W.t1Fin.fill(0)
    W.t1FinBasis.fill(0)
    W.t1SalesEMA.fill(0)
    W.t1LastBuy.fill(float('nan'))
    W.preferredWholesale.fill(-1)
    W.playerPrice.fill(float('nan'))

    for cid in range(N1):
        code = T1P[cid // 100]['product']
        pi = next(i for i, p in enumerate(M.PRODUCTS) if p['code'] == code)
        p = M.PRODUCTS[pi]
        eq = cfg['t1Machinery']                        # canon $15k flat
        uc = M.unit_cost(p['complexity'], cfg)         # canon $1.25 reference unit cost
        price = quant_r(uc * (1 + M.t2_markup(p['complexity'], cfg)), uc)  # first-guess markup 0.25
        W.t1EqBook[cid] = eq
        W.t1Operates[cid * NP + pi] = 1
        W.t1Rel[cid * NP + pi] = 0.5
        W.t1UnitCost[cid * NP + pi] = uc
        W.t1Price[cid * NP + pi] = price
        W.t1PrevPrice[cid * NP + pi] = price

    initialize_tier2(W, cfg)
    initialize_consumers(W, cfg)

    return cfg, W
