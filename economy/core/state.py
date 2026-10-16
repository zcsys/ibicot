"""WorldState: NumPy typed arrays + the world's initialization sequence.

The array names, dtypes and shapes mirror ``the canon machine contract (docs/design_canon.md §12)``
``sourceViews()`` / ``reset()`` exactly, so the Python port is a mechanical
transcription.  See ``docs/design_canon.md`` §6.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from . import model as M
from .config import normalize_config
from .rng import hash_seed_vec

# Designated roles are inactive metadata; extraction coverage and ordering remain unchanged.
_T0P_RAW = [(p['name'],p['elements_extracted']) for p in M.NAMING_CATALOG['t0_companies']]
_EI = {element: i for i, element in enumerate(M.ELEMENTS)}
T0P = [{'id': i, 'companyNumber': M.company_number('T0',i), 'name': M._DATA['MIDBRIDGE']['tier0Companies'][i]['name'], 'elements': elements,
        'designated_role': M.NAMING_CATALOG['t0_companies'][i]['designated_role'],
        'element_indices': sorted(_EI[element] for element in elements)}
       for i, (name, elements) in enumerate(_T0P_RAW)]

# Tier 1 cohort -> native product code (the product table).
T1P = [{'name': p['companyName'], 'product': p['code']} for p in M.PRODUCTS]


def quantize_whole(x: float, floor: float = 0.0) -> float:
    return M.round_to_cent(M.clamp(x, M.MIN_UNIT_PRICE, M.MAX_UNIT_PRICE))


def quantize_round(x: float, floor: float = 0.0) -> float:
    return M.round_to_cent(M.clamp(x, M.MIN_UNIT_PRICE, M.MAX_UNIT_PRICE))


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
        (f'{prefix}LearnRevenue', 'f64', n),
        (f'{prefix}LearnPreviousRevenue', 'f64', n),
        (f'{prefix}LearnPreviousSales', 'f64', n),
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
    # cfg.t2FirmCount.  cfg.distributorCount / cfg.t2FirmCount merely limit how
    # many entries are initialized and processed.
    N2F = M.N2_FIRMS
    NUF = M.N_DISTRIBUTORS
    ML = min(M.MAX_T2_LINES, cfg['t2FirmCount'] * M.T2_MAX_PRODUCTS_PER_FIRM)
    n_t2 = len(M.T2_PRODUCTS)  # 105 invented

    spec = [
        ('t0Opportunities', 'u32', NE),
        ('t1Opportunities', 'u32', NP),
        ('t2Opportunities', 'u32', n_t2),
        ('t2PotentialOrders', 'u32', n_t2),
        ('t2IntermediateSold', 'f64', n_t2),
        ('t2InputConsumed', 'f64', M.NI),
        ('t2IntermediateRevenue', 'f64', n_t2),
    ]
    spec += _learn('t0', N0 * NE)
    spec += _learn('t1', N1 * NP)
    spec += _learn('t2', ML)
    for tier, n in (('t0', N0), ('t1', N1), ('t2', N2F)):
        spec += [(tier + name, 'f64', n) for name in
                 ('SwitchingIncome', 'SwitchingExpense', 'SwitchingNetEMA',
                  'IntelligenceCharge', 'IntelligencePaid', 'Operating')]
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
        ('t1RentArrears', 'f64', N1),
        ('t1RentPaid', 'f64', N1),
        ('t1RentCharge', 'f64', N1),
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
        ('potential', 'f64', NP),  # T1 whole-unit input needs before cash/stock/price limits
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
        ('t2RentArrears', 'f64', N2F),
        ('t2RentPaid', 'f64', N2F),
        ('t2RentCharge', 'f64', N2F),
        ('t2Bought', 'f64', N2F),
        ('t2EqBook', 'f64', N2F),
        ('t2LastSaleTick', 'u32', N2F),
        ('t2Raw', 'f64', N2F * NE),
        ('t2RawBasis', 'f64', N2F * NE),
        ('t2T1Raw', 'f64', N2F * M.NI),
        ('t2T1Basis', 'f64', N2F * M.NI),
        ('t2Controller', 'u8', N2F),
        ('t2Capability', 'u8', N2F),
        ('t2Sector', 'u8', N2F),
        ('t2LineFirm', 'u32', ML),
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
        ('t2Preferred', 'i32', N2F * M.NI),
        ('t2Made', 'f64', ML),
        ('t2Rel', 'f64', ML),
        ('t2RelAttempts', 'u32', ML),
        ('t2RelAvailable', 'u32', ML),
        ('t2RelPriceSum', 'f64', ML),
        ('t2RelPriceSamples', 'u32', ML),
        ('t2MonthSold', 'f64', ML),
        ('t2MonthlyCapacity', 'f64', ML),
        ('distributorProduct', 'i16', NUF),
        ('distributorPreferredSupplier', 'i32', NUF),
        ('distributorPreferredMarket', 'i16', NUF),
        ('distributorLastMarket', 'i16', NUF),
        ('distributorLastSupplier', 'i32', NUF),
        ('distributorLastQ', 'u16', NUF),
        ('distributorLastFulfilled', 'u16', NUF),
        ('distributorQMax', 'f32', NUF),
        ('distributorChoke', 'f32', NUF),
        ('distributorEta', 'f32', NUF),
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
        self.distributorPreferredMarket.fill(-1)
        self.distributorSupplierHistory = {}
        self.t2LineCount = 0
        self.costSinks = 0.0
        self.equipmentSinks = 0.0
        self.netEarningsAvailable = True
        self.operatingCostsSettled = False
        for tier in ('t0', 't1', 't2'):
            getattr(self, tier + 'Operating').fill(1)
        self._init_loyalty_regime(cfg)

    def sync_distributor_preferences(self):
        """Bind the hot supplier cache to its product; retain other products sparsely.

        Only reassigned buyers enter Python. The fixed-product million-buyer case
        uses one vectorized comparison and leaves the compiled purchase loop intact.
        Keys are (buyer, market); values are production-line IDs, not firm IDs.
        """
        markets = self.distributorProduct
        cached = self.distributorPreferredMarket
        unbound = cached < 0
        cached[unbound] = markets[unbound]
        for buyer in np.flatnonzero(cached != markets):
            old_key = (int(buyer), int(cached[buyer]))
            supplier = int(self.distributorPreferredSupplier[buyer])
            if supplier >= 0:
                self.distributorSupplierHistory[old_key] = supplier
            else:
                self.distributorSupplierHistory.pop(old_key, None)
            new_key = (int(buyer), int(markets[buyer]))
            self.distributorPreferredSupplier[buyer] = self.distributorSupplierHistory.pop(new_key, -1)
            cached[buyer] = markets[buyer]

    def _init_loyalty_regime(self, cfg):
        # Adaptive loyalty-multiple regime (§12.6): an EMA of the average order
        # value per buyer class drives the switching-charge multiple M, so the
        # charge tracks ~5% of a typical order as prices/margins drift.
        self.lmUnitCost1 = float(cfg['baseCost'])                                 # raw
        self.lmUnitCost2 = M.material_switching_reference(cfg)  # material
        self.lmUnitCost3 = self._mean_t2_unit_cost(cfg)                            # good (mean)
        self.lm1 = float(cfg['loyaltyMultiple'][1])
        self.lm2 = np.array([cfg['loyaltyMultiple'][2][c] for c in (3, 4, 5)], dtype=np.float64)
        self.lm3 = float(cfg['loyaltyMultiple'][3])
        self.aov1 = self.lm1 * self.lmUnitCost1 * 1.5 / M.LOYALTY_ORDER_SHARE
        self.aov2 = self.lm2 * self.lmUnitCost2 * 1.5 / M.LOYALTY_ORDER_SHARE
        self.aov3 = self.lm3 * self.lmUnitCost3 * 1.5 / M.LOYALTY_ORDER_SHARE
        # per-tick accumulators for the T2 material AOV (split by complexity)
        self.t2MatSpend = np.zeros(3, dtype=np.float64)
        self.t2MatOrders = np.zeros(3, dtype=np.float64)
        # per-tick loyalty accounting: disloyal supplier switches and charge paid,
        # indexed by buyer tier [T1, T2, T3]
        self.loyaltySwitches = np.zeros(3, dtype=np.float64)
        self.loyaltyPenalties = np.zeros(3, dtype=np.float64)

    @staticmethod
    def _mean_t2_unit_cost(cfg):
        return M.distributor_switching_reference(cfg)

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
# Tier 2 line installation (line installation).
# --------------------------------------------------------------------------
def _has_tier2_product(world, firm, product_id):
    for slot in range(int(world.t2FirmLineCount[firm])):
        if world.t2LineProduct[world.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot]] == product_id:
            return True
    return False


@lru_cache(maxsize=64)
def _tier1_storage_cached(base, c2):
    # Fixed cohort identity; vectorized once per configuration, reused in hot paths.
    capacities = np.repeat(np.where(np.array([p['complexity'] for p in M.PRODUCTS]) == 2,
                                    c2, base), M.T1_PRODUCT_FIRM_COUNTS).astype(np.float64)
    capacities.flags.writeable = False
    return capacities


def tier1_storage_capacities(cfg):
    return _tier1_storage_cached(float(cfg.get('t1C1Storage', cfg['storage'])), float(cfg.get('t1C2Storage', cfg['storage'])))


def tier1_goods_space(world, cfg, firm):
    footprint = sum(cfg['footprint'][M.complexity(p)] for i, p in enumerate(M.PRODUCTS)
                    if world.t1Operates[firm * M.NP + i])
    return M.refinery_storage(cfg, firm) - footprint


def tier2_goods_space(world, cfg, firm):
    lines = world.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM:
                              firm * M.T2_MAX_PRODUCTS_PER_FIRM + int(world.t2FirmLineCount[firm])]
    footprint = sum(cfg['footprint'][M.T2_PRODUCTS[int(world.t2LineProduct[line])]['complexity']]
                    for line in lines)
    return cfg['storage'] - footprint


def tier2_occupied_space(world, cfg, firm):
    lines = world.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM:
                              firm * M.T2_MAX_PRODUCTS_PER_FIRM + int(world.t2FirmLineCount[firm])]
    return (cfg['storage'] - tier2_goods_space(world, cfg, firm)
            + world.t2Raw[firm * M.NE:(firm + 1) * M.NE].sum()
            + world.t2T1Raw[firm * M.NI:(firm + 1) * M.NI] @ np.array([p['complexity'] for p in M.T2_INPUT_PRODUCTS])
            + world.t2Fin[lines] @ np.array([M.T2_PRODUCTS[int(world.t2LineProduct[l])]['complexity'] for l in lines]))


def validate_storage(world, cfg):
    """Reject a configuration that would put installed assets outside storage."""
    footprint1 = np.array([cfg['footprint'][M.complexity(p)] for p in M.PRODUCTS])
    occupied1 = (world.t1Operates.reshape(M.N1, M.NP) @ footprint1
                 + world.raw.reshape(M.N1, M.NE).sum(axis=1)
                 + world.t1Fin.reshape(M.N1, M.NP) @ np.array([p['complexity'] for p in M.PRODUCTS]))
    n, lc = cfg['t2FirmCount'], int(world.t2LineCount)
    footprint2 = np.array([cfg['footprint'][p['complexity']] for p in M.T2_PRODUCTS])
    occupied2 = (world.t2Raw.reshape(M.N2_FIRMS, M.NE)[:n].sum(axis=1)
                 + world.t2T1Raw.reshape(M.N2_FIRMS, M.NI)[:n] @ np.array([p['complexity'] for p in M.T2_INPUT_PRODUCTS])
                 + np.bincount(world.t2LineFirm[:lc], minlength=n,
                               weights=world.t2Fin[:lc] * np.array([p['complexity'] for p in M.T2_PRODUCTS])[world.t2LineProduct[:lc]] + footprint2[world.t2LineProduct[:lc]]))
    if (occupied1 > tier1_storage_capacities(cfg) + 1e-9).any() or (occupied2 > cfg['storage'] + 1e-9).any():
        raise ValueError('Storage must accommodate installed machinery and existing goods.')


def add_tier2_line(world, cfg, firm, product, paid=True):
    firm = int(firm)
    if not (0 <= firm < cfg['t2FirmCount']) or product is None or not product.get('invented',False):
        raise ValueError('Invalid Tier 2 company or product.')
    if product['complexity'] not in M.TIER_BOUNDARIES['T2']:
        raise ValueError('Tier 2 firms can only manufacture C-3 through C-4 products.')
    if world.t2FirmLineCount[firm] >= M.T2_MAX_PRODUCTS_PER_FIRM or world.t2LineCount >= len(world.t2Fin):
        raise ValueError('Company or economy product-line limit reached.')
    if _has_tier2_product(world, firm, product['id']):
        raise ValueError('This product line is already installed.')
    if product['complexity'] > world.t2Capability[firm] or world.t2Sector[firm] != product['sectorIndex']:
        raise ValueError('Machinery requires an eligible sector and capability.')
    if paid and world.t2Cash[firm] < cfg['t2Machinery'][product['complexity']]:
        raise ValueError('Insufficient cash.')
    if tier2_occupied_space(world, cfg, firm) + cfg['footprint'][product['complexity']] > cfg['storage'] + 1e-9:
        raise ValueError('Insufficient storage space for machinery.')
    line = world.t2LineCount
    world.t2LineCount += 1
    world.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + int(world.t2FirmLineCount[firm])] = line
    world.t2FirmLineCount[firm] = int(world.t2FirmLineCount[firm]) + 1
    world.t2LineFirm[line] = firm
    world.t2LineProduct[line] = product['id']
    world.t2UnitCost[line] = M.initial_tier2_cost(product, cfg)
    world.t2LearnStep[line] = 1
    world.t2Price[line] = M.round_to_cent(max(M.MIN_UNIT_PRICE, M.reference_tier2_cost(product, cfg) * (1 + M.tier2_starting_markup(product, cfg))))
    world.t2LearnPrevious[line] = float('nan')
    world.t2LearnPreviousRevenue[line] = float('nan')
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
    world.t2ReferenceCost[prod_id] = np.array([M.reference_tier2_cost(p, cfg) for p in M.T2_PRODUCTS])
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
        # Retained sector-option capacity weights. Distributor allocation uses
        # its own demand weights below and does not consume this option table.
        supply = M.T2_PRODUCT_FIRM_COUNTS[product['id']] * cfg['t2Capacity'][product['complexity']]
        world.t2SectorProductWeight[index] = (world.t2SectorProductWeight[index - 1] if count else 0) + supply

    # Route-balanced allocation; one line per firm. Counts differ by at most
    # one within each recipe route because companies are indivisible.
    # A reduced cfg['t2FirmCount'] takes a product prefix; small regression
    # fixtures must explicitly assign products to cover every complexity.
    target_firms = cfg['t2FirmCount']
    per_product = M.T2_PRODUCT_FIRM_COUNTS
    assigned = []
    for product in M.T2_PRODUCTS:
        cnt = min(per_product[product['id']], target_firms - len(assigned))
        if cnt <= 0:
            break
        assigned.extend([product['id']] * cnt)
    pid = np.array(assigned, dtype=np.int64)
    n = pid.size
    firms = np.arange(n)
    comp = prod_comp[pid]
    sector = prod_sector[pid]
    mach = np.array([cfg['t2Machinery'][int(c)] for c in comp], dtype=np.float64)
    unit_cost = world.t2ReferenceCost[pid]
    price = np.floor(np.maximum(M.MIN_UNIT_PRICE, unit_cost * (1.0 + cfg['t1Markup'])) * 100.0 + 0.5) / 100.0

    world.t2Capability[:n] = 5
    world.t2Sector[:n] = sector
    world.t2FirmLines[firms * M.T2_MAX_PRODUCTS_PER_FIRM] = firms
    world.t2FirmLineCount[:n] = 1
    world.t2LineFirm[:n] = firms
    world.t2LineProduct[:n] = pid
    world.t2UnitCost[:n] = np.array([M.initial_tier2_cost(p, cfg) for p in M.T2_PRODUCTS])[pid]
    world.t2LearnStep[:n] = 1
    world.t2Price[:n] = price
    world.t2LearnPrevious[:n] = float('nan')
    world.t2LearnPreviousRevenue[:n] = float('nan')
    world.t2LearnDirection[:n] = np.where(((firms + cfg['seed']) % 2) == 1, np.int8(1), np.int8(-1))
    world.t2PlayerPrice[:n] = float('nan')
    world.t2Rel[:n] = 0.5
    world.t2SalesEMA[:n] = 0
    world.t2DemandEMA[:n] = 0
    world.t2Cash[:n] = cfg['t2Equity'] - cfg['t2License'] - mach
    world.t2EqBook[:n] = mach
    world.t2LineCount = n


def initialize_distributors(world, cfg):
    world.distributorPreferredSupplier.fill(-1)
    world.distributorPreferredMarket.fill(-1)
    world.distributorSupplierHistory.clear()
    world.distributorLastMarket.fill(-1)
    world.distributorLastSupplier.fill(-1)
    seed = cfg['seed']
    n_t2 = len(M.T2_PRODUCTS)
    # Final routing uses net default capacity times the static complexity calibration.
    # Routing is fixed at initialization; live shortages do not reassign buyers.
    supply = np.array([p['distributorWeight'] for p in M.T2_PRODUCTS], dtype=np.float64)
    cum = np.cumsum(supply)
    total = cum[-1]
    world.distributorQMax.fill(M.DISTRIBUTOR_QMAX)
    n = cfg['distributorCount']
    cids = np.arange(n)
    b = hash_seed_vec(seed, 9000000 + cids)
    # Stratification keeps each product's assigned count within one of its
    # exact share. Seeded hash order spreads buckets across distributor IDs.
    order = np.argsort(hash_seed_vec(seed, 7000000 + cids), kind='stable')
    draw = (np.arange(n, dtype=np.float64) + 0.5) * total / max(1, n)
    offset = np.empty(n, dtype=np.int64)
    offset[order] = np.searchsorted(cum, draw, side='right')
    np.minimum(offset, n_t2 - 1, out=offset)
    world.distributorProduct[:n] = (M.NP + offset).astype(np.int16)
    world.distributorChoke[:n] = (cfg['chokeMin'] + b.astype(np.float64) / 4294967296.0
                               * (cfg['chokeMax'] - cfg['chokeMin'])).astype(np.float32)
    world.distributorEta[:n] = cfg['elasticity']


def reset_world(cfg):
    """Normalize config, allocate and initialize the world (reset)."""
    cfg = normalize_config(cfg)
    world = WorldState(cfg)
    seed = cfg['seed']
    NE, NP, N0, N1 = M.NE, M.NP, M.N0, M.N1

    # WorldState already allocates zeroed arrays. Re-filling every array here
    # needlessly writes the entire state a second time (including spare lines).
    for tier, width in (('t0', NE), ('t1', NP), ('t2', None)):
        learn_dir = getattr(world, f'{tier}LearnDirection')
        getattr(world, f'{tier}LearnPrevious').fill(float('nan'))
        getattr(world, f'{tier}LearnPreviousRevenue').fill(float('nan'))
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
        code = T1P[M.T1_FIRM_PRODUCT[cid]]['product']
        pi = next(i for i, p in enumerate(M.PRODUCTS) if p['code'] == code)
        p = M.PRODUCTS[pi]
        eq = cfg['t1Machinery']                        # canon $15k flat
        uc = M.refinery_unit_cost(p, cfg)         # canon $1.25 reference unit cost
        price = quantize_round(M.reference_refinery_cost(p, cfg) * (1 + M.t2_markup(p['complexity'], cfg)), uc)  # first-guess markup 0.25
        world.t1EqBook[cid] = eq
        world.t1Operates[cid * NP + pi] = 1
        world.t1Rel[cid * NP + pi] = 0.5
        world.t1UnitCost[cid * NP + pi] = uc
        world.t1Price[cid * NP + pi] = price
        world.t1PrevPrice[cid * NP + pi] = price

    initialize_tier2(world, cfg)
    initialize_distributors(world, cfg)

    validate_storage(world, cfg)
    return cfg, world
