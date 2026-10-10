"""Read-only economy projections with the original sequential sum order.

These loops run once per snapshot. No fast-math or parallel reductions: even
low-order floating-point bits in the dashboard remain unchanged. Numba is
optional, with Python/NumPy fallbacks for every projection.
"""
from collections import namedtuple

import math
import numpy as np

from ..core import model as M

try:
    from ..core.jit import njit
    HAVE_NUMBA = True
except Exception:  # pragma: no cover - Numba/LLVM is optional
    HAVE_NUMBA = False
    def njit(fn):
        return fn

NE, NP, N1 = M.NE, M.NP, M.N1
PRODUCT_COUNT, SECTOR_COUNT = len(M.T2_PRODUCTS), len(M.T2_SECTORS)
_VIEW_FIELDS = ('t1Operates', 'raw', 'rawBasis', 't1Fin', 't1FinBasis', 't1Sold',
                't1Revenue', 't1COGS', 't1Rel', 't1Cash', 't1EqBook', 't1Price',
                't1UnitCost', 't1PriceStability')
RefineryView = namedtuple('RefineryView', _VIEW_FIELDS)
COMPANY_FIELDS = ('raw', 'finished', 'sold', 'revenue', 'cogs', 'made', 'reliability',
                  'equity', 'inventoryValue')
COHORT_FIELDS = ('price', 'unitCost', 'finished', 'raw', 'cash', 'equity', 'made',
                 'sold', 'revenue', 'cogs', 'reliability', 'stability', 'quotes', 'players')
TOTAL_FIELDS = ('raw', 'finished', 'cash', 'sold', 'revenue', 'cogs', 'made', 'equity',
                'activeFirms', 'players', 'reliabilitySum', 'reliabilityCount')


@njit
def _project(w, made_by_line, controller, license_cost):
    companies = np.zeros((9, N1))
    totals = np.zeros(12)
    cohorts = np.zeros((14, NP))
    volumes, revenues, quotes, quote_counts = (np.zeros(NP), np.zeros(NP), np.zeros(NP), np.zeros(NP))
    for cid in range(N1):
        raw = fin = sold = revenue = cogs = made = rel = value = 0.0
        rel_n = 0
        # Global equity historically starts from cash + machinery before
        # accumulating stock, whereas company equity adds inventory last.
        eqv = w.t1Cash[cid] + w.t1EqBook[cid]
        for e in range(NE):
            idx = cid * NE + e
            raw += w.raw[idx]
            value += w.raw[idx] * w.rawBasis[idx]
            eqv += w.raw[idx] * w.rawBasis[idx]
        for p in range(NP):
            idx = cid * NP + p
            if not w.t1Operates[idx]:
                continue
            fin += w.t1Fin[idx]
            sold += w.t1Sold[idx]
            revenue += w.t1Revenue[idx]
            cogs += w.t1COGS[idx]
            made += made_by_line[idx]
            rel += w.t1Rel[idx]
            rel_n += 1
            value += w.t1Fin[idx] * w.t1FinBasis[idx]
            eqv += w.t1Fin[idx] * w.t1FinBasis[idx]
            totals[3] += w.t1Sold[idx]
            totals[4] += w.t1Revenue[idx]
            totals[5] += w.t1COGS[idx]
            totals[6] += made_by_line[idx]
            totals[10] += w.t1Rel[idx]
            totals[11] += 1
            volumes[p] += w.t1Sold[idx]
            revenues[p] += w.t1Revenue[idx]
            if math.isfinite(w.t1Price[idx]):
                quotes[p] += w.t1Price[idx]
                quote_counts[p] += 1
        equity = w.t1Cash[cid] + w.t1EqBook[cid] + value + license_cost
        companies[:, cid] = (raw, fin, sold, revenue, cogs, made, rel / rel_n if rel_n else 0.0, equity, value)
        totals[0] += raw
        totals[1] += fin
        totals[2] += w.t1Cash[cid]
        totals[7] += eqv + license_cost
        totals[8] += int(rel_n > 0)
        totals[9] += int(controller[cid] != 0)
    for cohort in range(NP):
        for cid in range(cohort * 100, (cohort + 1) * 100):
            b = cid * NP + cohort
            if math.isfinite(w.t1Price[b]):
                cohorts[0, cohort] += w.t1Price[b]
                cohorts[12, cohort] += 1
            cohorts[1, cohort] += w.t1UnitCost[b]
            cohorts[2, cohort] += w.t1Fin[b]
            for e in range(NE):
                cohorts[3, cohort] += w.raw[cid * NE + e]
            cohorts[4, cohort] += w.t1Cash[cid]
            cohorts[5, cohort] += companies[7, cid]
            for p in range(NP):
                idx = cid * NP + p
                if w.t1Operates[idx]:
                    cohorts[6, cohort] += made_by_line[idx]
                    cohorts[7, cohort] += w.t1Sold[idx]
                    cohorts[8, cohort] += w.t1Revenue[idx]
                    cohorts[9, cohort] += w.t1COGS[idx]
                    if p != cohort:
                        cohorts[2, cohort] += w.t1Fin[idx]
            cohorts[10, cohort] += w.t1Rel[b]
            cohorts[11, cohort] += w.t1PriceStability[b]
            cohorts[13, cohort] += int(controller[cid] != 0)
    return companies, cohorts, totals, volumes, revenues, quotes, quote_counts


def project_refineries(world, made, controller, license_cost):
    result = _project(RefineryView(*(getattr(world, k) for k in _VIEW_FIELDS)), made, controller, license_cost)
    companies, cohorts, totals, *markets = result
    return (dict(zip(COMPANY_FIELDS, companies)), dict(zip(COHORT_FIELDS, cohorts)),
            dict(zip(TOTAL_FIELDS, totals)), *markets)

_T2_FIELDS = ('t2LineProduct', 't2LineFirm', 't2Price', 't2Fin', 't2FinBasis',
              't2UnitCost', 't2Made', 't2Sold', 't2Revenue', 't2COGS', 't2Rel',
              't2Sector', 't2Controller', 't2Online', 't2Cash', 't2EqBook',
              't2Raw', 't2RawBasis', 't2T1Raw', 't2T1Basis')
ManufacturingView = namedtuple('ManufacturingView', _T2_FIELDS)


@njit
def _manufacturing(w, n, line_count, capacity):
    products = np.zeros((11, PRODUCT_COUNT))
    sectors = np.zeros((15, SECTOR_COUNT))
    for firm in range(n):
        sector = w.t2Sector[firm]
        sectors[0, sector] += 1
        sectors[1, sector] += w.t2Controller[firm]
        sectors[2, sector] += w.t2Controller[firm] & w.t2Online[firm]
        sectors[3, sector] += w.t2Cash[firm]
        sectors[4, sector] += w.t2EqBook[firm]
    # Keep the original material-major reduction order: sum each material
    # across firms before adding its sector totals to the inventory value.
    for material in range(NP):
        raw = np.zeros(SECTOR_COUNT)
        value = np.zeros(SECTOR_COUNT)
        for firm in range(n):
            sector = w.t2Sector[firm]
            if material < NE:
                idx = firm * NE + material
                q, b = w.t2Raw[idx], w.t2RawBasis[idx]
            else:
                idx = firm * NP + material
                q, b = w.t2T1Raw[idx], w.t2T1Basis[idx]
            raw[sector] += q
            value[sector] += q * b
        for sector in range(SECTOR_COUNT):
            sectors[5, sector] += raw[sector]
            sectors[6, sector] += value[sector]
    for line in range(line_count):
        pid = w.t2LineProduct[line]
        sector = w.t2Sector[w.t2LineFirm[line]]
        sold = w.t2Sold[line]
        basis = w.t2FinBasis[line]
        products[0, pid] += 1
        products[1, pid] += w.t2Price[line]
        products[2, pid] += w.t2Fin[line]
        products[3, pid] += w.t2Made[line]
        products[4, pid] += basis if basis != 0 else w.t2UnitCost[line]
        products[5, pid] += capacity[pid]
        products[6, pid] += sold
        products[7, pid] += w.t2Revenue[line]
        products[8, pid] += w.t2COGS[line]
        products[9, pid] += w.t2Rel[line]
        products[10, pid] += sold * sold
        sectors[7, sector] += 1
        sectors[8, sector] += w.t2Fin[line]
        sectors[9, sector] += w.t2Made[line]
        sectors[10, sector] += sold
        sectors[11, sector] += w.t2Revenue[line]
        sectors[12, sector] += w.t2COGS[line]
        sectors[13, sector] += capacity[pid]
        sectors[14, sector] += w.t2Fin[line] * basis
    return products, sectors


def project_manufacturing(world, n, line_count, capacity):
    project = _manufacturing if HAVE_NUMBA else _manufacturing_numpy
    return project(ManufacturingView(*(getattr(world, k) for k in _T2_FIELDS)), n, line_count, capacity)


def _manufacturing_numpy(w, n, lc, capacity):
    """Vectorized fallback and independent reduction oracle for the fused loop."""
    pid = w.t2LineProduct[:lc]
    sold, basis = w.t2Sold[:lc], w.t2FinBasis[:lc]
    products = np.vstack([
        np.bincount(pid, minlength=PRODUCT_COUNT),
        *(np.bincount(pid, weights=values, minlength=PRODUCT_COUNT) for values in (
            w.t2Price[:lc], w.t2Fin[:lc], w.t2Made[:lc],
            np.where(basis != 0, basis, w.t2UnitCost[:lc]), capacity[pid], sold,
            w.t2Revenue[:lc], w.t2COGS[:lc], w.t2Rel[:lc], sold * sold))])
    sectors = np.zeros((15, SECTOR_COUNT))
    sector = w.t2Sector[:n]
    sectors[0] = np.bincount(sector, minlength=SECTOR_COUNT)
    for i, values in enumerate((w.t2Controller[:n], w.t2Controller[:n] & w.t2Online[:n],
                                 w.t2Cash[:n], w.t2EqBook[:n]), 1):
        sectors[i] = np.bincount(sector, weights=values, minlength=SECTOR_COUNT)
    for material in range(NP):
        if material < NE:
            quantity, cost = w.t2Raw[material::NE][:n], w.t2RawBasis[material::NE][:n]
        else:
            quantity, cost = w.t2T1Raw[material::NP][:n], w.t2T1Basis[material::NP][:n]
        sectors[5] += np.bincount(sector, weights=quantity, minlength=SECTOR_COUNT)
        sectors[6] += np.bincount(sector, weights=quantity * cost, minlength=SECTOR_COUNT)
    line_sector = sector[w.t2LineFirm[:lc]]
    sectors[7] = np.bincount(line_sector, minlength=SECTOR_COUNT)
    for i, values in enumerate((w.t2Fin[:lc], w.t2Made[:lc], sold, w.t2Revenue[:lc],
                                 w.t2COGS[:lc], capacity[pid], w.t2Fin[:lc] * basis), 8):
        sectors[i] = np.bincount(line_sector, weights=values, minlength=SECTOR_COUNT)
    return products, sectors
