"""Full kernel runtime: owns the WorldState, applies the JS worker's command
surface, and publishes the exact ``lastSnapshot`` projection the browser UI
expects.  This is the Python analogue of ``the canon machine contract (spec/design_canon.md §12)``
closure + ``publish()``/``companyDetail()``/``tier2Page()``/``buildAnalytics()``.

The snapshot is a read projection (display-only); aggregate sums use NumPy so
they are fast and need not match the JS sequential-summation order bit-for-bit.
"""
from __future__ import annotations

import math
import time

import numpy as np

from ..core import model as M
from ..core.config import normalize_config
from ..core.rng import hash_seed
from ..core.state import (T0P, T1P, WorldState, _has_tier2_product, add_tier2_line,
                          quant_r, quant_w, reset_world)
from ..kernel.tick import tick as run_tick

NE, NP, N0, N1 = M.NE, M.NP, M.N0, M.N1
M4 = M.T2_MAX_PRODUCTS_PER_FIRM
MONTH = M.MONTH
N2_FIRMS = M.N2_FIRMS
N_END_USERS = M.N_END_USERS

_EI = {e: i for i, e in enumerate(M.ELEMENTS)}
_PI = {p['code']: i for i, p in enumerate(M.PRODUCTS)}

T2_COMPANY_NAMES = [
    'Helion Power Industries', 'Vector Drive Systems', 'Keel Spacecraft Works',
    'Haven Habitat Systems', 'Forge Automation', 'Relay Computing and Communications',
    'Prism Scientific Instruments', 'Stratum Industrial Machinery',
    'Waypoint Supply Industries', 'Sentinel Defence and Rescue Systems',
]


def _markup_code(code, cfg):
    comp = next(p['complexity'] for p in M.PRODUCTS if p['code'] == code)
    return M.t2_markup(comp, cfg)


def _sum(arr, n=None):
    a = arr if n is None else arr[:n]
    return float(np.sum(a))


def _hhi(vols):
    arr = np.asarray([float(v) for v in vols], dtype=np.float64)
    total = arr.sum()
    if total <= 0:
        return 0.0
    sh = arr / total
    return float((sh * sh).sum())


def _market_reliability(values, volumes):
    vals = np.asarray([float(v) for v in values], dtype=np.float64)
    vols = np.asarray([float(v) if v is not None else 0.0 for v in volumes], dtype=np.float64)
    active = np.isfinite(vals)
    n = int(active.sum())
    if not n:
        return 0.0
    v = np.maximum(0.0, vols)
    total = float(v[active].sum())
    if total > 0:
        return float((v[active] * vals[active]).sum() / total)
    return float(vals[active].sum() / n)


class KernelRuntime:
    def __init__(self, cfg=None):
        cfg = cfg or {}
        self.tick = 0
        self.month = 0
        self.running = False
        self.mode = 'fixed'
        self.targetTPS = 30
        self.state = {'activeOrders': 0, 'fulfilledOrders': 0}
        self.selectedTierControl = 'T1'
        self.selectedT2Id = 0
        self.selectedId = 0
        self.lastSnapshot = None
        self.lastReportAt = time.monotonic()
        self.lastReportTick = 0
        self.analyticsHistory = []
        self.tier2CompanyHistory = []
        self.tier2HistoryCompany = -1
        self.watchedCompanies = {'T0': set(), 'T1': set()}
        self.watchedCompanyHistory = {}
        self.workerStats = {'steps': 0, 'lastTickMs': 0.0, 'totalTickMs': 0.0}
        self.adminAccounting = {'equipmentSinks': 0, 'sequence': 0, 'lastEquipmentReceipt': None}
        self.playerLicenses = set(M.PROGRESSION_DEFAULTS['startingLicenses'])
        self.playerHouse = None
        self.ownershipAccounting = {'licensesSpent': 0, 'houseSpent': 0}
        self.ownershipEnforced = True
        self.tier2Query = {'page': 0, 'pageSize': 50, 'search': '', 'sector': '',
                           'controller': '', 'sort': 'id', 'descending': False}

        self.cfg, self.W = reset_world(cfg)
        self._init_admin()
        self._init_analytics_scratch()
        self.publish()

    def _init_admin(self):
        self.equipment = [[T1P[i // 100]['product']] for i in range(N1)]
        self.controller = np.zeros(N1, dtype=np.uint8)
        self.online = np.zeros(N1, dtype=np.uint8)
        self.playerPrices = [{} for _ in range(N1)]

    def _init_analytics_scratch(self):
        self.prevT0Inventory = np.zeros(N0 * NE, dtype=np.float64)
        self.prevT1Finished = np.zeros(N1 * NP, dtype=np.float64)
        self.prevT1FinishedCohort = np.zeros(N1 * NP, dtype=np.float64)
        self.tickStartT0Inventory = np.zeros(N0 * NE, dtype=np.float64)
        self.tickStartT1Finished = np.zeros(N1 * NP, dtype=np.float64)
        self.lastTickT0Produced = np.zeros(N0 * NE, dtype=np.float64)
        self.lastTickT1Made = np.zeros(N1 * NP, dtype=np.float64)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def reset(self, cfg=None):
        self.tick = 0
        self.month = 0
        self.running = False
        self.playerLicenses = set(M.PROGRESSION_DEFAULTS['startingLicenses'])
        self.playerHouse = None
        self.ownershipAccounting = {'licensesSpent': 0, 'houseSpent': 0}
        self.ownershipEnforced = True
        self.analyticsHistory = []
        self.watchedCompanyHistory = {}
        self.tier2CompanyHistory = []
        self.tier2HistoryCompany = -1
        self._init_analytics_scratch()
        self.cfg, self.W = reset_world(cfg if cfg is not None else self.cfg)
        self._init_admin()
        self.workerStats = {'steps': 0, 'lastTickMs': 0.0, 'totalTickMs': 0.0}
        self.adminAccounting = {'equipmentSinks': 0, 'sequence': 0, 'lastEquipmentReceipt': None}
        self.state = {'activeOrders': 0, 'fulfilledOrders': 0, 'activatedConsumers': 0, 'consumerPayments': 0}
        self.lastReportAt = time.monotonic()
        self.lastReportTick = 0
        return self.publish()

    def step(self):
        started = time.monotonic()
        t = self.tick + 1
        np.copyto(self.tickStartT0Inventory, self.W.t0Inv)
        np.copyto(self.tickStartT1Finished, self.W.t1Fin)
        run_tick(self.W, self.cfg, t, state=self.state)
        for i in range(N0):
            for e in range(NE):
                idx = i * NE + e
                self.lastTickT0Produced[idx] = max(0.0, self.W.t0Inv[idx] - self.tickStartT0Inventory[idx] + self.W.t0Sold[idx])
        for cid in range(N1):
            for p in range(NP):
                idx = cid * NP + p
                self.lastTickT1Made[idx] = max(0.0, self.W.t1Fin[idx] - self.tickStartT1Finished[idx] + self.W.t1Sold[idx])
        self.tick = t
        self.month = t // MONTH
        self.workerStats['steps'] += 1
        self.workerStats['lastTickMs'] = (time.monotonic() - started) * 1000
        self.workerStats['totalTickMs'] += self.workerStats['lastTickMs']

    def run(self, mode='fixed'):
        self.mode = mode
        self.running = True

    def pause(self):
        self.running = False

    # ------------------------------------------------------------------
    # Live config
    # ------------------------------------------------------------------
    def apply_config(self, patch):
        if patch is None:
            return self.publish()
        for key in ('endUserCount', 't2FirmCount'):
            if key in patch and patch[key] != self.cfg[key]:
                raise ValueError('Population changes require Reset.')
        merged = dict(self.cfg)
        merged.update(patch)
        self.cfg = normalize_config(merged)
        for cid in range(self.cfg['endUserCount']):
            a = hash_seed(self.cfg['seed'], 8000000 + cid)
            b = hash_seed(self.cfg['seed'], 9000000 + cid)
            self.W.endQMax[cid] = self.cfg['demandQtyMin'] + a % (self.cfg['demandQtyMax'] - self.cfg['demandQtyMin'] + 1)
            self.W.endChoke[cid] = self.cfg['vmin'] + b / 4294967296 * (self.cfg['vmax'] - self.cfg['vmin'])
            self.W.endEta[cid] = self.cfg['elasticity']
        return self.publish()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    def select(self, tier, id_):
        if tier == 'T2':
            self.selectedTierControl = 'T2'
            self.selectedT2Id = max(0, min(self.cfg['t2FirmCount'] - 1, int(id_)))
        else:
            self.selectedTierControl = 'T1'
            self.selectedId = max(0, min(N1 - 1, int(id_)))
        return self.publish()

    def watch_companies(self, watches):
        self.watchedCompanies['T0'] = {int(x) for x in (watches or {}).get('T0', []) if 0 <= int(x) < N0}
        self.watchedCompanies['T1'] = {int(x) for x in (watches or {}).get('T1', []) if 0 <= int(x) < N1}
        return self.publish()

    def set_ownership_enforcement(self, enforced):
        self.ownershipEnforced = bool(enforced)
        return self.publish()

    def buy_license(self, tier):
        costs = M.PROGRESSION_DEFAULTS['licenseCosts']
        if tier not in costs:
            return {'type': 'licenseResult', 'ok': False, 'tier': tier, 'cost': None,
                    'msg': 'Unknown tier.', 'licenses': list(self.playerLicenses)}
        cost = costs[tier]
        if cost is None:
            return {'type': 'licenseResult', 'ok': False, 'tier': tier, 'cost': None,
                    'msg': 'This license is not for sale.', 'licenses': list(self.playerLicenses)}
        if tier in self.playerLicenses:
            return {'type': 'licenseResult', 'ok': False, 'tier': tier, 'cost': None,
                    'msg': 'License already held.', 'licenses': list(self.playerLicenses)}
        self.playerLicenses.add(tier)
        self.ownershipAccounting['licensesSpent'] += cost
        self.publish()
        return {'type': 'licenseResult', 'ok': True, 'tier': tier, 'cost': cost,
                'msg': None, 'licenses': list(self.playerLicenses)}

    def found_house(self, name):
        name = str(name or '').strip()[:80]
        if self.playerHouse:
            return {'type': 'houseResult', 'ok': False, 'name': None,
                    'msg': 'A house is already founded.', 'house': self.playerHouse}
        if not name:
            return {'type': 'houseResult', 'ok': False, 'name': None,
                    'msg': 'A house name is required.', 'house': None}
        self.playerHouse = {'name': name}
        self.ownershipAccounting['houseSpent'] += M.PROGRESSION_DEFAULTS['houseFoundingCost']
        self.publish()
        return {'type': 'houseResult', 'ok': True, 'name': name, 'msg': None,
                'house': dict(self.playerHouse)}

    def player(self, tier, id_, code, price, online, controller):
        if tier == 'T2':
            id_ = int(id_)
            if not (0 <= id_ < self.cfg['t2FirmCount']):
                raise ValueError('Invalid Tier 2 company.')
            product = M.T2_PRODUCT_BY_CODE.get(code)
            if controller == 'PLAYER' and (product is None
                                           or not _has_tier2_product(self.W, id_, product['id'])
                                           or not math.isfinite(price) or price < 0):
                raise ValueError('Select an installed product and a valid non-negative price.')
            self.W.t2Controller[id_] = 1 if controller == 'PLAYER' else 0
            self.W.t2Online[id_] = 1 if online else 0
            if self.W.t2Controller[id_]:
                for slot in range(int(self.W.t2FirmLineCount[id_])):
                    line = int(self.W.t2FirmLines[id_ * M4 + slot])
                    if self.W.t2LineProduct[line] == product['id']:
                        self.W.t2PlayerPrice[line] = max(price, self.W.t2FinBasis[line] or self.W.t2UnitCost[line], M.MIN_UNIT_PRICE)
                        self.W.t2Price[line] = self.W.t2PlayerPrice[line]
                        self.W.t2LearnOpportunity[line] = self.W.t2LearnPotentialOpportunity[line] = 0
                        self.W.t2LearnProfit[line] = self.W.t2LearnSales[line] = self.W.t2LearnDemand[line] = self.W.t2LearnTicks[line] = 0
                        self.W.t2LearnStep[line] = 1
                        self.W.t2LearnPrevious[line] = float('nan')
            self.selectedTierControl = 'T2'
            self.selectedT2Id = id_
            return self.publish()
        id_ = int(id_)
        pi = _PI.get(code)
        if not (0 <= id_ < N1) or pi is None or code not in self.equipment[id_]:
            raise ValueError('Invalid Tier 1 company or product.')
        self.selectedTierControl = 'T1'
        self.selectedId = id_
        self.controller[id_] = 1 if controller == 'PLAYER' else 0
        self.online[id_] = 1 if online else 0
        self.W.t1Controller[id_] = self.controller[id_]
        index = id_ * NP + pi
        if self.controller[id_] and math.isfinite(price):
            self.playerPrices[id_][code] = quant_r(price)
            self.W.playerPrice[index] = self.playerPrices[id_][code]
            self.W.t1LearnOpportunity[index] = self.W.t1LearnPotentialOpportunity[index] = 0
            self.W.t1LearnProfit[index] = self.W.t1LearnSales[index] = self.W.t1LearnDemand[index] = self.W.t1LearnTicks[index] = 0
            self.W.t1LearnStep[index] = 1
            self.W.t1LearnPrevious[index] = float('nan')
        return self.publish()

    def buy_equipment(self, tier, id_, code):
        if tier == 'T2':
            id_ = int(id_)
            if not (0 <= id_ < self.cfg['t2FirmCount']) or not self.W.t2Controller[id_]:
                raise ValueError('Only player-controlled Tier 2 companies can buy machinery.')
            product = M.T2_PRODUCT_BY_CODE.get(code)
            if product is None:
                raise ValueError('Unknown product.')
            add_tier2_line(self.W, self.cfg, id_, product)
            return self.publish()
        id_ = int(id_)
        product = M.PRODUCTS[_PI[code]] if code in _PI else None
        if self.controller[id_] != 1 or product is None or code in self.equipment[id_]:
            raise ValueError('Only PLAYER-controlled companies can buy new equipment.')
        if self.W.t1Cash[id_] + 1e-9 < self.cfg['t1Machinery']:
            raise ValueError('Insufficient cash.')
        self.W.t1Cash[id_] -= self.cfg['t1Machinery']
        self.W.t1EqBook[id_] += self.cfg['t1Machinery']
        self.equipment[id_].append(code)
        index = id_ * NP + _PI[code]
        input_cost = sum(self._last_finite_wholesale(_EI[e]) * r for e, r in product['inputs'].items())
        uc = input_cost + M.conversion_cost(product['complexity'], self.cfg)
        self.W.t1Operates[index] = 1
        self.W.t1UnitCost[index] = uc
        self.W.t1Rel[index] = 0.5
        self.W.t1Price[index] = quant_r(uc * (1 + _markup_code(code, self.cfg)), uc)
        self.W.t1PrevPrice[index] = self.W.t1Price[index]
        return self.publish()

    def _last_finite_wholesale(self, e):
        best = float('inf')
        for i in range(N0):
            if M.ELEMENTS[e] in T0P[i]['elements']:
                best = min(best, float(self.W.t0Price[i * NE + e]))
        return best if math.isfinite(best) else self.cfg['baseCost']

    def company_detail(self, tier, id_):
        return self._company_detail(tier, int(id_))

    # ------------------------------------------------------------------
    # Projections (ports of worker publish() + helpers)
    # ------------------------------------------------------------------
    def _book_t0_equity(self):
        v = float(self.W.t0Cash.sum())
        for i in range(N0):
            b = i * NE
            for e in range(NE):
                v += float(self.W.t0Inv[b + e] * self.W.t0InvBasis[b + e])
        return v

    def _market_averages(self):
        W = self.W
        wVol = np.zeros(NE)
        wRev = np.zeros(NE)
        rVol = np.zeros(NP)
        rRev = np.zeros(NP)
        rCounts = np.zeros(NP, dtype=np.int64)
        for i in range(N0):
            for e in range(NE):
                if M.ELEMENTS[e] in T0P[i]['elements']:
                    idx = i * NE + e
                    wVol[e] += W.t0Sold[idx]
                    wRev[e] += W.t0Revenue[idx]
        for cid in range(N1):
            for p in range(NP):
                if W.t1Operates[cid * NP + p]:
                    rVol[p] += W.t1Sold[cid * NP + p]
                    rRev[p] += W.t1Rev[cid * NP + p]
                    rCounts[p] += 1
        wP = np.zeros(NE)
        for e in range(NE):
            if wVol[e]:
                wP[e] = wRev[e] / wVol[e]
            else:
                s = 0.0
                n = 0
                for i in range(N0):
                    if M.ELEMENTS[e] in T0P[i]['elements']:
                        s += W.t0Price[i * NE + e]
                        n += 1
                wP[e] = s / n if n else float('nan')
        rP = np.zeros(NP)
        for p in range(NP):
            if rVol[p]:
                rP[p] = rRev[p] / rVol[p]
            else:
                s = 0.0
                n = 0
                for cid in range(N1):
                    if W.t1Operates[cid * NP + p] and math.isfinite(W.t1Price[cid * NP + p]):
                        s += W.t1Price[cid * NP + p]
                        n += 1
                rP[p] = s / n if n else float('nan')
        wv = float(wVol.sum())
        wr = float(wRev.sum())
        rv = float(rVol.sum())
        rr = float(rRev.sum())
        return {'wVol': wVol, 'wRev': wRev, 'rVol': rVol, 'rRev': rRev, 'wP': wP, 'rP': rP,
                'wAvg': wr / wv if wv else float(np.nansum(wP) / NE),
                'rAvg': rr / rv if rv else float(np.nansum(rP) / NP),
                'wVolume': wv, 'rVolume': rv}

    def _cohort_analytics(self, m):
        W = self.W
        cohorts = []
        for cidx in range(NP):
            start = cidx * 100
            end = start + 100
            pIdx = _PI[T1P[cidx]['product']]
            product = T1P[cidx]['product']
            price = 0.0
            uc = 0.0
            finished = 0.0
            raw = 0.0
            cash = 0.0
            equity = 0.0
            made = 0.0
            sold = 0.0
            revenue = 0.0
            cogs = 0.0
            rel = 0.0
            stability = 0.0
            eqCount = 0
            players = 0
            for cid in range(start, end):
                b = cid * NP + pIdx
                rb = cid * NE
                stock = W.t1Fin[b]
                p = W.t1Price[b]
                if math.isfinite(p):
                    price += p
                    eqCount += 1
                uc += W.t1UnitCost[b]
                finished += stock
                for e in range(NE):
                    raw += W.raw[rb + e]
                cash += W.t1Cash[cid]
                inv_val = 0.0
                for e in range(NE):
                    inv_val += W.raw[rb + e] * W.rawBasis[rb + e]
                for p2 in range(NP):
                    if W.t1Operates[cid * NP + p2]:
                        inv_val += W.t1Fin[cid * NP + p2] * W.t1FinBasis[cid * NP + p2]
                equity += W.t1Cash[cid] + W.t1EqBook[cid] + inv_val + self.cfg['t1License']
                for p in range(NP):
                    if not W.t1Operates[cid * NP + p]:
                        continue
                    index = cid * NP + p
                    made += self.lastTickT1Made[index]
                    sold += W.t1Sold[index]
                    revenue += W.t1Rev[index]
                    cogs += W.t1COGS[index]
                    if p != pIdx:
                        finished += W.t1Fin[index]
                rel += W.t1Rel[b]
                stability += W.t1PriceStability[b]
                if self.controller[cid]:
                    players += 1
                self.prevT1FinishedCohort[b] = W.t1Fin[b]
            marketVol = m['rVol'][pIdx]
            cohorts.append({
                'code': product, 'displayName': M.PRODUCTS[pIdx]['name'], 'name': T1P[cidx]['name'],
                'sector': M.t1_sector(product),
                'firms': end - start,
                'equipment': 'Basic' if M.PRODUCTS[pIdx]['complexity'] == 1 else 'Compound',
                'avgPrice': price / eqCount if eqCount else float('nan'),
                'avgUnitCost': uc / (end - start),
                'finished': float(finished), 'raw': float(raw), 'inventory': float(finished + raw),
                'cash': float(cash), 'equity': float(equity), 'made': float(made),
                'sold': float(sold), 'revenue': float(revenue), 'cogs': float(cogs),
                'grossProfit': float(revenue - cogs),
                'margin': float((revenue - cogs) / revenue) if revenue else 0.0,
                'reliability': float(rel / (end - start)),
                'priceStability': float(stability / (end - start)),
                'marketShare': (float(W.t1Sold[start * NP + pIdx:end * NP + pIdx][::NP].sum()) / marketVol) if marketVol else 0.0,
                'players': players,
            })
        return cohorts

    def _build_analytics(self, m):
        W = self.W
        t0Inventory = _sum(W.t0Inv)
        t0Cash = _sum(W.t0Cash)
        t0Sold = _sum(W.t0Sold)
        t0Revenue = _sum(W.t0Revenue)
        t0Produced = np.zeros(NE)
        t0Vol = np.zeros(NE)
        t0HHI = [0.0] * NE
        t0Rel = [[] for _ in range(NE)]
        for i in range(N0):
            for e in range(NE):
                if M.ELEMENTS[e] in T0P[i]['elements']:
                    idx = i * NE + e
                    t0Produced[e] += self.lastTickT0Produced[idx]
                    t0Vol[e] += W.t0Sold[idx]
                    t0Rel[e].append(W.t0Rel[idx])
                    self.prevT0Inventory[idx] = W.t0Inv[idx]
        for e in range(NE):
            vols = [W.t0Sold[i * NE + e] for i in range(N0) if M.ELEMENTS[e] in T0P[i]['elements']]
            t0HHI[e] = _hhi(vols)
        t1Raw = t1Finished = t1Cash = t1Sold = t1Revenue = t1COGS = t1Made = t1Equity = 0.0
        activeFirms = players = relWeighted = relN = 0
        for cid in range(N1):
            rb = cid * NE
            raw = 0.0
            finished = 0.0
            eqv = W.t1Cash[cid] + W.t1EqBook[cid]
            for e in range(NE):
                raw += W.raw[rb + e]
                eqv += W.raw[rb + e] * W.rawBasis[rb + e]
            t1Raw += raw
            t1Cash += W.t1Cash[cid]
            if self.controller[cid]:
                players += 1
            any_ = False
            for p in range(NP):
                if W.t1Operates[cid * NP + p]:
                    idx = cid * NP + p
                    fin = W.t1Fin[idx]
                    finished += fin
                    eqv += fin * W.t1FinBasis[idx]
                    t1Sold += W.t1Sold[idx]
                    t1Revenue += W.t1Rev[idx]
                    t1COGS += W.t1COGS[idx]
                    t1Made += self.lastTickT1Made[idx]
                    self.prevT1Finished[idx] = fin
                    relWeighted += W.t1Rel[idx]
                    relN += 1
                    any_ = True
            if any_:
                activeFirms += 1
            t1Finished += finished
            t1Equity += eqv + self.cfg['t1License']
        n2 = self.cfg['t2FirmCount']
        lc = int(W.t2LineCount)
        t2Cash = _sum(W.t2Cash, n2)
        t2Equity = _sum(W.t2Cash, n2) + _sum(W.t2EqBook, n2) + n2 * self.cfg['t2License']
        t2Inventory = _sum(W.t2Fin, lc)
        t2Made = _sum(W.t2Made, lc)
        t2Sold = _sum(W.t2Sold, lc)
        t2Revenue = _sum(W.t2Revenue, lc)
        t2COGS = _sum(W.t2COGS, lc)
        t2Equity += float((W.t2Fin[:lc] * W.t2FinBasis[:lc]).sum())
        t2Inventory += _sum(W.t2Raw, n2 * NE) + _sum(W.t2T1Raw, n2 * NP)
        t2Equity += float((W.t2Raw[:n2 * NE] * W.t2RawBasis[:n2 * NE]).sum())
        t2Equity += float((W.t2T1Raw[:n2 * NP] * W.t2T1Basis[:n2 * NP]).sum())
        potential = _sum(W.endPotential)
        active = _sum(W.endActive)
        fulfilled = _sum(W.endFulfilled)
        priceLost = _sum(W.endPriceLost)
        stockUnmet = _sum(W.endStockUnmet)
        orderTotal = self.state.get('activeOrders', 0)
        fulfilledOrders = self.state.get('fulfilledOrders', 0)
        cohort = self._cohort_analytics(m)
        latest = {
            'tick': self.tick, 'wholesaleAvg': m['wAvg'], 'retailAvg': m['rAvg'],
            'wVolume': m['wVolume'], 'rVolume': m['rVolume'],
            't0Inventory': t0Inventory, 't1Inventory': t1Raw + t1Finished,
            't0Equity': self._book_t0_equity(), 't1Equity': t1Equity,
            't2Cash': t2Cash, 't2Equity': t2Equity, 't2Made': t2Made,
            't2Inventory': t2Inventory, 't2Sold': t2Sold, 't2Revenue': t2Revenue, 't2COGS': t2COGS,
            't0Cash': t0Cash, 't1Cash': t1Cash,
            'retailPotential': potential, 'retailActive': active, 'retailFulfilled': fulfilled,
            'priceLost': priceLost, 'stockUnmet': stockUnmet,
            't1GrossProfit': t1Revenue - t1COGS,
            'avgT0Reliability': float(np.nanmean(np.concatenate(t0Rel))) if any(len(x) for x in t0Rel) else 0.0,
            'avgT1Reliability': relWeighted / relN if relN else 0.0,
        }
        if self.analyticsHistory and self.analyticsHistory[-1].get('tick') == self.tick:
            self.analyticsHistory[-1] = latest
        else:
            self.analyticsHistory.append(latest)
        if len(self.analyticsHistory) > 240:
            self.analyticsHistory.pop(0)
        return {
            'cohort': cohort, 'latest': latest, 't0Inventory': t0Inventory, 't0Cash': t0Cash,
            't0Sold': t0Sold, 't0Revenue': t0Revenue, 't0Equity': self._book_t0_equity(),
            't0Produced': t0Produced, 't0Vol': t0Vol, 't0HHI': t0HHI,
            't1Raw': t1Raw, 't1Finished': t1Finished, 't1Cash': t1Cash,
            'activeFirms': activeFirms, 'players': players, 't1Made': t1Made, 't1Sold': t1Sold,
            't1Revenue': t1Revenue, 't1COGS': t1COGS, 't1Equity': t1Equity,
            't2Cash': t2Cash, 't2Equity': t2Equity, 't2Made': t2Made, 't2Inventory': t2Inventory,
            't2Sold': t2Sold, 't2Revenue': t2Revenue, 't2COGS': t2COGS, 't2Lines': lc,
            'potential': potential, 'active': active, 'fulfilled': fulfilled,
            'priceLost': priceLost, 'stockUnmet': stockUnmet,
            'orderTotal': orderTotal, 'fulfilledOrders': fulfilledOrders,
            'unitFillRate': fulfilled / active if active else 0.0,
            'orderFillRate': fulfilledOrders / orderTotal if orderTotal else 0.0,
            'priceLossShare': priceLost / potential if potential else 0.0,
            'stockUnmetShare': stockUnmet / active if active else 0.0,
            'retailRevenue': self.state.get('consumerPayments', 0),
            'difficultyMean': float(W.difficulty.mean()),
            'difficultyMin': float(W.difficulty.min()),
            'difficultyMax': float(W.difficulty.max()),
        }

    def _tier2_company(self, id_, detailed=True):
        W = self.W
        if not (0 <= id_ < self.cfg['t2FirmCount']):
            return None
        products = []
        finished = made = sold = revenue = cogs = raw = value = capacity = 0.0
        for slot in range(int(W.t2FirmLineCount[id_])):
            line = int(W.t2FirmLines[id_ * M4 + slot])
            product = M.T2_PRODUCTS[int(W.t2LineProduct[line])]
            products.append({
                'line': line, 'code': product['code'], 'name': product['name'],
                'primaryMaterial': next(p['name'] for p in M.PRODUCTS if p['code'] == product['primaryMaterial']),
                'complexity': product['complexity'],
                'recipe': ' + '.join(f'{q} {M.PRODUCTS[m]["name"]}' for m, q in product['ingredients']),
                'price': float(W.t2Price[line]),
                'unitCost': float(W.t2FinBasis[line] or W.t2UnitCost[line]),
                'capacity': self.cfg['t2Capacity'][product['complexity']],
                'finished': float(W.t2Fin[line]), 'made': float(W.t2Made[line]),
                'sold': float(W.t2Sold[line]), 'revenue': float(W.t2Revenue[line]),
                'cogs': float(W.t2COGS[line]),
                'grossProfit': float(W.t2Revenue[line] - W.t2COGS[line]),
                'margin': float((W.t2Revenue[line] - W.t2COGS[line]) / W.t2Revenue[line]) if W.t2Revenue[line] else 0.0,
                'utilization': float(W.t2Made[line] / self.cfg['t2Capacity'][product['complexity']]),
                'demandEMA': float(W.t2DemandEMA[line]), 'salesEMA': float(W.t2SalesEMA[line]),
                'stockCoverage': float(W.t2Fin[line] / W.t2SalesEMA[line]) if W.t2SalesEMA[line] > 0 else None,
                'reliability': float(W.t2Rel[line]),
            })
            capacity += self.cfg['t2Capacity'][product['complexity']]
            finished += W.t2Fin[line]
            made += W.t2Made[line]
            sold += W.t2Sold[line]
            revenue += W.t2Revenue[line]
            cogs += W.t2COGS[line]
            value += W.t2Fin[line] * W.t2FinBasis[line]
        inputs = []
        for material in range(NP):
            basic = material < NE
            index = id_ * (NE if basic else NP) + material
            q = (W.t2Raw if basic else W.t2T1Raw)[index]
            b = (W.t2RawBasis if basic else W.t2T1Basis)[index]
            raw += q
            value += q * b
            if detailed:
                supplier = int(W.t2Preferred[id_ * NP + material])
                seller = supplier // NP if supplier >= 0 else -1
                inputs.append({
                    'name': M.PRODUCTS[material]['name'], 'sourceTier': 'T1',
                    'stock': float(q), 'basis': float(b), 'value': float(q * b),
                    'supplier': supplier, 'supplierId': seller,
                    'supplierName': (T1P[seller // 100]['name'] + ' ' + str(seller % 100 + 1).zfill(3)) if seller >= 0 else None,
                    'supplierPrice': float(W.t1Price[supplier]) if supplier >= 0 else None,
                    'supplierReliability': float(W.t1Rel[supplier]) if supplier >= 0 else None,
                })
        eligible = []
        if detailed:
            eligible = [{'code': p['code'], 'name': p['name'], 'price': self.cfg['t2Machinery'][p['complexity']],
                         'complexity': p['complexity']}
                        for p in M.T2_PRODUCTS
                        if p['complexity'] <= W.t2Capability[id_] and W.t2Sector[id_] == p['sectorIndex']
                        and not _has_tier2_product(W, id_, p['id'])]
        return {'tier': 'T2', 'id': id_,
                'name': T2_COMPANY_NAMES[int(W.t2Sector[id_])] + ' ' + str(id_ + 1).zfill(5),
                'sector': M.T2_SECTORS[int(W.t2Sector[id_])], 'capability': int(W.t2Capability[id_]),
                'controller': 'PLAYER' if W.t2Controller[id_] else 'BOT',
                'online': bool(W.t2Online[id_]),
                'cash': float(W.t2Cash[id_]), 'eqBook': float(W.t2EqBook[id_]),
                'equipmentBookValue': float(W.t2EqBook[id_]),
                'equity': float(W.t2Cash[id_] + W.t2EqBook[id_] + value + self.cfg['t2License']),
                'inventory': float(raw + finished), 'inventoryCapacity': self.cfg['storage'],
                'raw': float(raw), 'finished': float(finished), 'made': float(made), 'sold': float(sold),
                'revenue': float(revenue), 'cogs': float(cogs),
                'grossProfit': float(revenue - cogs), 'capacity': float(capacity),
                'utilization': float(made / capacity) if capacity else 0.0,
                'margin': float((revenue - cogs) / revenue) if revenue else 0.0,
                'lineCount': len(products),
                'sellThrough': float(sold / (finished + sold)) if (finished + sold) else 0.0,
                'reliability': float(np.mean([p['reliability'] for p in products])) if products else 0.0,
                'native': products[0]['code'] if products else None,
                'price': products[0]['price'] if products else None,
                'equipment': [p['code'] for p in products],
                'products': products, 'inputs': inputs, 'eligibleEquipment': eligible}

    def _tier2_page(self):
        W = self.W
        q = self.tier2Query
        search = q['search'].lower()
        n = self.cfg['t2FirmCount']
        # Fast path: no filters, default id order — the match set is the whole
        # population, so skip the per-firm scan entirely.
        if not search and not q['sector'] and not q['controller'] and q['sort'] == 'id' and not q['descending']:
            page = min(max(0, q['page']), max(0, math.ceil(n / q['pageSize']) - 1))
            start = page * q['pageSize']
            rows = [self._tier2_company(i, False) for i in range(start, min(n, start + q['pageSize']))]
            return {'page': page, 'pageSize': q['pageSize'], 'total': n, 'rows': rows}
        matches = []
        for id_ in range(n):
            sector = M.T2_SECTORS[int(W.t2Sector[id_])]
            control = 'PLAYER' if W.t2Controller[id_] else 'BOT'
            if q['sector'] and q['sector'] != sector:
                continue
            if q['controller'] and q['controller'] != control:
                continue
            if search:
                text = T2_COMPANY_NAMES[int(W.t2Sector[id_])] + ' ' + str(id_ + 1).zfill(5) + ' ' + sector + ' ' + control
                for slot in range(int(W.t2FirmLineCount[id_])):
                    text += ' ' + M.T2_PRODUCTS[int(W.t2LineProduct[int(W.t2FirmLines[id_ * M4 + slot])])]['name']
                if search not in text.lower():
                    continue
            matches.append(id_)
        if q['sort'] != 'id':
            vals = {x: self._tier2_company(x, False)[q['sort']] for x in matches}
            first = vals[matches[0]] if matches else None
            if isinstance(first, str):
                matches.sort(key=lambda x: (vals[x].lower(), x))
            else:
                matches.sort(key=lambda x: (vals[x] if vals[x] is not None else 0.0, x))
        if q['descending']:
            matches.reverse()
        page = min(max(0, q['page']), max(0, math.ceil(len(matches) / q['pageSize']) - 1))
        rows = [self._tier2_company(i, False) for i in matches[page * q['pageSize']:(page + 1) * q['pageSize']]]
        return {'page': page, 'pageSize': q['pageSize'], 'total': len(matches), 'rows': rows}

    def _company_detail(self, tier, id_):
        W = self.W
        if tier == 'T2':
            return self._tier2_company(id_)
        id_ = max(0, id_)
        if tier == 'T0':
            co = T0P[id_] if id_ < N0 else None
            if not co:
                return None
            elements = []
            inventory = prod = sold = revenue = equity = 0.0
            equity = W.t0Cash[id_]
            for e in M.ELEMENTS:
                if e not in co['elements']:
                    continue
                i = _EI[e]
                idx = id_ * NE + i
                stock = W.t0Inv[idx]
                invVal = stock * W.t0InvBasis[idx]
                inventory += stock
                prod += self.lastTickT0Produced[idx]
                sold += W.t0Sold[idx]
                revenue += W.t0Revenue[idx]
                equity += invVal
                elements.append({
                    'element': e, 'stock': float(stock), 'cost': float(W.t0Cost[idx]),
                    'price': float(W.t0Price[idx]), 'production': float(self.lastTickT0Produced[idx]),
                    'sold': float(W.t0Sold[idx]), 'revenue': float(W.t0Revenue[idx]),
                    'cogs': float(W.t0COGS[idx]),
                    'grossProfit': float(W.t0Revenue[idx] - W.t0COGS[idx]),
                    'reliability': float(W.t0Rel[idx]), 'stability': float(W.t0Stability[idx]),
                    'reliabilityAttempts': int(W.t0RelAttempts[idx]),
                })
            return {'tier': 'T0', 'id': id_, 'name': co['name'], 'elements': list(co['elements']),
                    'cash': float(W.t0Cash[id_]), 'inventory': float(inventory), 'equity': float(equity),
                    'made': float(prod), 'sold': float(sold), 'revenue': float(revenue),
                    'cogs': float(sum(x['cogs'] for x in elements)),
                    'grossProfit': float(revenue - sum(x['cogs'] for x in elements)),
                    'capacity': self.cfg['capacity'], 'targetInventory': self.cfg['targetInventory'],
                    'maxInventory': self.cfg['maxInventory'], 'status': 'ACTIVE', 'elementData': elements}
        if id_ >= N1:
            return None
        piBase = T1P[id_ // 100]
        raw = []
        for e in M.ELEMENTS:
            i = _EI[e]
            idx = id_ * NE + i
            raw.append({'element': e, 'stock': float(W.raw[idx]), 'basis': float(W.rawBasis[idx]),
                        'lastBuy': float(W.t1LastBuy[idx]) if math.isfinite(W.t1LastBuy[idx]) else None,
                        'inputNeed': float(W.t1InputNeed[idx]), 'purchaseRequest': float(W.t1PurchaseReq[idx]),
                        'preferredSupplier': int(W.preferredWholesale[idx])})
        products = []
        inv = eqv = made = sold = revenue = cogs = 0.0
        eqv = W.t1Cash[id_] + W.t1EqBook[id_] + self.cfg['t1License']
        for p in range(NP):
            if W.t1Operates[id_ * NP + p]:
                idx = id_ * NP + p
                fin = W.t1Fin[idx]
                inv += fin
                eqv += fin * W.t1FinBasis[idx]
                made += self.lastTickT1Made[idx]
                sold += W.t1Sold[idx]
                revenue += W.t1Rev[idx]
                cogs += W.t1COGS[idx]
                products.append({
                    'product': M.PRODUCTS[p]['code'], 'price': float(W.t1Price[idx]),
                    'unitCost': float(W.t1UnitCost[idx]), 'finished': float(fin),
                    'finishedBasis': float(W.t1FinBasis[idx]),
                    'salesEMA': float(W.t1SalesEMA[idx]), 'demandEMA': float(W.t1DemandEMA[idx]),
                    'active': float(W.t1Demand[idx]), 'fulfilled': float(W.t1Sold[idx]),
                    'stockUnmet': float(max(0.0, W.t1Demand[idx] - W.t1Sold[idx])),
                    'made': float(self.lastTickT1Made[idx]), 'sold': float(W.t1Sold[idx]),
                    'revenue': float(W.t1Rev[idx]), 'cogs': float(W.t1COGS[idx]),
                    'reliability': float(W.t1Rel[idx]), 'priceStability': float(W.t1PriceStability[idx]),
                    'reliabilityAttempts': int(W.t1RelAttempts[idx]),
                })
        for x in raw:
            inv += x['stock']
        for e in M.ELEMENTS:
            eqv += W.raw[id_ * NE + _EI[e]] * W.rawBasis[id_ * NE + _EI[e]]
        return {'tier': 'T1', 'id': id_, 'name': piBase['name'] + ' ' + str((id_ % 100) + 1).zfill(3),
                'sector': M.t1_sector(piBase['product']),
                'controller': 'PLAYER' if self.controller[id_] else 'BOT',
                'online': bool(self.online[id_]), 'cash': float(W.t1Cash[id_]),
                'equipment': list(self.equipment[id_]), 'equipmentBookValue': float(W.t1EqBook[id_]),
                'inventory': float(inv), 'equity': float(eqv), 'raw': raw, 'products': products,
                'made': float(made), 'sold': float(sold), 'revenue': float(revenue), 'cogs': float(cogs),
                'grossProfit': float(revenue - cogs),
                'reliability': float(np.mean([p['reliability'] for p in products])) if products else 0.0}

    def _watched_details(self):
        out = {}
        for id_ in self.watchedCompanies['T0']:
            if 0 <= id_ < N0:
                out['T0:' + str(id_)] = self._company_detail('T0', id_)
        for id_ in self.watchedCompanies['T1']:
            if 0 <= id_ < N1:
                out['T1:' + str(id_)] = self._company_detail('T1', id_)
        for key in list(self.watchedCompanyHistory):
            if key not in out:
                del self.watchedCompanyHistory[key]
        for key, detail in out.items():
            history = self.watchedCompanyHistory.get(key) or []
            point = {'tick': self.tick}
            for field in ('cash', 'equity', 'made', 'sold', 'revenue', 'cogs', 'grossProfit'):
                if field in detail and math.isfinite(detail[field]):
                    point[field] = detail[field]
            if history and history[-1].get('tick') == self.tick:
                history[-1] = point
            else:
                history.append(point)
            if len(history) > 240:
                history.pop(0)
            self.watchedCompanyHistory[key] = history
            detail['history'] = history
        return out

    def _company_summaries_t0(self):
        W = self.W
        out = []
        for id_ in range(N0):
            prof = T0P[id_]
            inv = prod = cogs = sold = rev = rel = 0.0
            n = 0
            eq = W.t0Cash[id_]
            for e in range(NE):
                if M.ELEMENTS[e] in prof['elements']:
                    idx = id_ * NE + e
                    inv += W.t0Inv[idx]
                    prod += self.lastTickT0Produced[idx]
                    cogs += W.t0COGS[idx]
                    sold += W.t0Sold[idx]
                    rev += W.t0Revenue[idx]
                    rel += W.t0Rel[idx]
                    n += 1
                    eq += W.t0Inv[idx] * W.t0InvBasis[idx]
            out.append({'id': id_, 'name': prof['name'], 'elements': list(prof['elements']),
                        'cash': float(W.t0Cash[id_]), 'inventory': float(inv), 'equity': float(eq),
                        'production': float(prod), 'sold': float(sold), 'revenue': float(rev),
                        'cogs': float(cogs), 'grossProfit': float(rev - cogs),
                        'avgPrice': float(np.mean([W.t0Price[id_ * NE + _EI[e]] for e in prof['elements']])) if n else float('nan'),
                        'reliability': float(rel / n) if n else 0.0})
        return out

    def _product_ready_stock(self, pi):
        return float(self.W.t1Fin[pi::NP].sum())

    def _product_supply_capacity(self, pi):
        cap = self.cfg['t1Capacity']
        return float(np.count_nonzero(self.W.t1Operates[pi::NP])) * cap

    def publish(self):
        W = self.W
        cfg = self.cfg
        m = self._market_averages()
        now = time.monotonic()
        elapsed = max(0.001, now - self.lastReportAt)
        intervalTicks = self.tick - self.lastReportTick
        tps = intervalTicks / elapsed
        self.lastReportAt = now
        self.lastReportTick = self.tick
        analytics = self._build_analytics(m)

        sid = max(0, min(N1 - 1, self.selectedId))
        scode = T1P[sid // 100]['product']
        spi = _PI[scode]

        companies = []
        for cid in range(N1):
            pi = _PI[T1P[cid // 100]['product']]
            b = cid * NP
            raw = fin = totalSold = totalRevenue = totalCOGS = totalMade = rel = 0.0
            relN = 0
            for e in range(NE):
                raw += W.raw[cid * NE + e]
            for p in range(NP):
                if W.t1Operates[cid * NP + p]:
                    fin += W.t1Fin[cid * NP + p]
                    totalSold += W.t1Sold[cid * NP + p]
                    totalRevenue += W.t1Rev[cid * NP + p]
                    totalCOGS += W.t1COGS[cid * NP + p]
                    totalMade += self.lastTickT1Made[cid * NP + p]
                    rel += W.t1Rel[cid * NP + p]
                    relN += 1
            inv_val = 0.0
            for e in range(NE):
                inv_val += W.raw[cid * NE + e] * W.rawBasis[cid * NE + e]
            for p in range(NP):
                if W.t1Operates[cid * NP + p]:
                    inv_val += W.t1Fin[cid * NP + p] * W.t1FinBasis[cid * NP + p]
            companies.append({
                'id': cid, 'name': T1P[cid // 100]['name'] + ' ' + str((cid % 100) + 1).zfill(3),
                'sector': M.t1_sector(T1P[cid // 100]['product']),
                'controller': 'PLAYER' if self.controller[cid] else 'BOT',
                'equipment': list(self.equipment[cid]), 'price': float(W.t1Price[b + pi]),
                'raw': float(raw), 'finished': float(fin), 'inventory': float(raw + fin),
                'cash': float(W.t1Cash[cid]),
                'equity': float(W.t1Cash[cid] + W.t1EqBook[cid] + inv_val + self.cfg['t1License']),
                'made': float(totalMade), 'sold': float(totalSold), 'revenue': float(totalRevenue),
                'grossProfit': float(totalRevenue - totalCOGS),
                'reliability': float(rel / relN) if relN else 0.0})

        productStats = []
        _op = W.t1Operates.reshape(N1, NP)
        _sold = W.t1Sold.reshape(N1, NP)
        _rel = W.t1Rel.reshape(N1, NP)
        _price = W.t1Price.reshape(N1, NP)
        _uc = W.t1UnitCost.reshape(N1, NP)
        _made = self.lastTickT1Made.reshape(N1, NP)
        _cogs = W.t1COGS.reshape(N1, NP)
        _demand = W.t1Demand.reshape(N1, NP)
        for p in range(NP):
            prod = M.PRODUCTS[p]
            mask = _op[:, p] != 0
            firms = int(mask.sum())
            if firms:
                vol = _sold[:, p][mask]
                rel = _rel[:, p][mask]
                made = float(_made[:, p][mask].sum())
                cogs = float(_cogs[:, p][mask].sum())
                demand = float(_demand[:, p][mask].sum())
                avg_price = float(_price[:, p][mask].mean())
                avg_uc = float(_uc[:, p][mask].mean())
                hhi = _hhi(vol)
                reliability = _market_reliability(rel, vol)
            else:
                made = cogs = demand = avg_price = avg_uc = hhi = reliability = 0.0
            productStats.append({
                'code': prod['code'], 'name': prod['name'], 'complexity': prod['complexity'],
                'role': prod['role'], 'firms': firms, 'machineryPrice': self.cfg['t1Machinery'],
                'capacity': cfg['t1Capacity'],
                'productionCapacity': self._product_supply_capacity(p),
                'made': made, 'sold': float(m['rVol'][p]), 'cogs': cogs,
                'avgPrice': avg_price, 'avgUnitCost': avg_uc,
                'retailPrice': float(m['rP'][p]), 'volume': float(m['rVol'][p]),
                'consumerVolume': float(W.endFulfilled[p]),
                'intermediateVolume': float(W.t1IntermediateSold[p]),
                'intermediateRevenue': float(W.t1IntermediateRevenue[p]),
                'revenue': float(m['rRev'][p]), 'supplyCapacity': self._product_supply_capacity(p),
                'readyStock': self._product_ready_stock(p), 'customerType': 'Companies',
                'potential': None, 'active': demand, 'fulfilled': float(W.t1IntermediateSold[p]),
                'priceLost': None, 'stockUnmet': float(max(0.0, demand - W.t1IntermediateSold[p])),
                'hhi': hhi, 'reliability': reliability,
                'fillRate': float(W.t1IntermediateSold[p] / demand) if demand > 0 else None})

        t2ProductStats = []
        for p in M.T2_PRODUCTS:
            t2ProductStats.append({'customerType': 'External galactic buyers', 'code': p['code'], 'name': p['name'],
                                   'needType': p['needType'], 'kind': p['kind'], 'sector': p['sector'],
                                   'complexity': p['complexity'],
                                   'primaryMaterial': next(x['name'] for x in M.PRODUCTS if x['code'] == p['primaryMaterial']),
                                   'machineryPrice': self.cfg['t2Machinery'][p['complexity']],
                                   'capacity': self.cfg['t2Capacity'][p['complexity']],
                                   'recipe': ' + '.join(f'{q} {M.PRODUCTS[m]["name"]}' for m, q in p['ingredients']),
                                   'firms': 0, 'avgPrice': 0.0, 'avgUnitCost': 0.0, 'productionCapacity': 0.0,
                                   'readyStock': 0.0, 'made': 0.0, 'sold': 0.0, 'revenue': 0.0, 'cogs': 0.0,
                                   'reliability': 0.0, 'hhi': 0.0,
                                   'potential': float(W.endPotential[NP + p['id']]),
                                   'active': float(W.endActive[NP + p['id']]),
                                   'fulfilled': float(W.endFulfilled[NP + p['id']]),
                                   'stockUnmet': float(W.endStockUnmet[NP + p['id']]),
                                   'fillRate': float(W.endFulfilled[NP + p['id']] / W.endActive[NP + p['id']]) if W.endActive[NP + p['id']] else 0.0})
        lc = int(W.t2LineCount)
        t2_cap = np.array([p['capacity'] for p in M.T2_PRODUCTS], dtype=np.float64)
        if lc:
            pid = W.t2LineProduct[:lc].astype(np.int64)
            sold = W.t2Sold[:lc]
            finb = W.t2FinBasis[:lc]
            ucost = np.where(finb != 0.0, finb, W.t2UnitCost[:lc])
            firms = np.bincount(pid, minlength=200).astype(np.float64)
            avg_price = np.bincount(pid, weights=W.t2Price[:lc], minlength=200)
            ready_stock = np.bincount(pid, weights=W.t2Fin[:lc], minlength=200)
            made_s = np.bincount(pid, weights=W.t2Made[:lc], minlength=200)
            avg_uc = np.bincount(pid, weights=ucost, minlength=200)
            prod_cap = np.bincount(pid, weights=t2_cap[pid], minlength=200)
            sold_s = np.bincount(pid, weights=sold, minlength=200)
            rev_s = np.bincount(pid, weights=W.t2Revenue[:lc], minlength=200)
            cogs_s = np.bincount(pid, weights=W.t2COGS[:lc], minlength=200)
            rel_s = np.bincount(pid, weights=W.t2Rel[:lc], minlength=200)
            hhi_s = np.bincount(pid, weights=sold * sold, minlength=200)
            for i, st in enumerate(t2ProductStats):
                f = firms[i]
                st['firms'] = int(f)
                st['avgPrice'] = float(avg_price[i] / f) if f else 0.0
                st['readyStock'] = float(ready_stock[i])
                st['made'] = float(made_s[i])
                st['avgUnitCost'] = float(avg_uc[i] / f) if f else 0.0
                st['productionCapacity'] = float(prod_cap[i])
                st['sold'] = float(sold_s[i])
                st['revenue'] = float(rev_s[i])
                st['cogs'] = float(cogs_s[i])
                st['reliability'] = float(rel_s[i] / f) if f else 0.0
                st['hhi'] = float(hhi_s[i] / (sold_s[i] ** 2)) if sold_s[i] else 0.0
                st['grossProfit'] = st['revenue'] - st['cogs']
                st['margin'] = st['grossProfit'] / st['revenue'] if st['revenue'] else 0.0
                st['utilization'] = st['made'] / st['productionCapacity'] if st['productionCapacity'] else 0.0

        n2 = cfg['t2FirmCount']
        sector = W.t2Sector[:n2].astype(np.int64)
        firms = np.bincount(sector, minlength=10).astype(np.float64)
        players = np.bincount(sector, weights=W.t2Controller[:n2].astype(np.float64), minlength=10)
        online = np.bincount(sector, weights=(W.t2Controller[:n2] & W.t2Online[:n2]).astype(np.float64), minlength=10)
        cash = np.bincount(sector, weights=W.t2Cash[:n2], minlength=10)
        eqbook = np.bincount(sector, weights=W.t2EqBook[:n2], minlength=10)
        raw = np.zeros(10)
        eq_raw = np.zeros(10)
        for mat in range(NP):
            if mat < NE:
                q = W.t2Raw[mat::NE][:n2]
                b = W.t2RawBasis[mat::NE][:n2]
            else:
                q = W.t2T1Raw[mat::NP][:n2]
                b = W.t2T1Basis[mat::NP][:n2]
            raw += np.bincount(sector, weights=q, minlength=10)
            eq_raw += np.bincount(sector, weights=q * b, minlength=10)
        line_firm = W.t2LineFirm[:lc].astype(np.int64)
        line_sector = sector[line_firm]
        lines = np.bincount(line_sector, minlength=10).astype(np.float64)
        inventory = np.bincount(line_sector, weights=W.t2Fin[:lc], minlength=10)
        made = np.bincount(line_sector, weights=W.t2Made[:lc], minlength=10)
        sold = np.bincount(line_sector, weights=W.t2Sold[:lc], minlength=10)
        rev = np.bincount(line_sector, weights=W.t2Revenue[:lc], minlength=10)
        cogs = np.bincount(line_sector, weights=W.t2COGS[:lc], minlength=10)
        gross = rev - cogs
        capacity = np.bincount(line_sector, weights=t2_cap[W.t2LineProduct[:lc].astype(np.int64)], minlength=10)
        eq_fin = np.bincount(line_sector, weights=W.t2Fin[:lc] * W.t2FinBasis[:lc], minlength=10)
        equity = cash + eqbook + eq_raw + eq_fin + firms * self.cfg['t2License']

        t2Cohorts = []
        for s in range(10):
            t2Cohorts.append({
                'name': M.T2_SECTORS[s], 'firms': int(firms[s]), 'lines': int(lines[s]),
                'players': int(players[s]), 'online': int(online[s]), 'cash': float(cash[s]),
                'equity': float(equity[s]), 'equipmentBookValue': float(eqbook[s]),
                'raw': float(raw[s]), 'inventory': float(inventory[s]), 'capacity': float(capacity[s]),
                'made': float(made[s]), 'sold': float(sold[s]), 'revenue': float(rev[s]),
                'cogs': float(cogs[s]), 'grossProfit': float(gross[s]),
                'utilization': float(made[s] / capacity[s]) if capacity[s] else 0.0,
                'margin': float(gross[s] / rev[s]) if rev[s] else 0.0})

        def summarize_markets(products, name):
            s = {'name': name, 'products': len(products), 'lines': 0, 'capacity': 0.0, 'readyStock': 0.0,
                 'made': 0.0, 'sold': 0.0, 'revenue': 0.0, 'cogs': 0.0, 'active': 0.0, 'fulfilled': 0.0,
                 'stockUnmet': 0.0, 'reliability': 0.0}
            for p in products:
                for k in ('made', 'sold', 'revenue', 'cogs', 'active', 'fulfilled', 'stockUnmet', 'readyStock'):
                    s[k] += p[k]
                s['lines'] += p['firms']
                s['capacity'] += p['productionCapacity']
                s['reliability'] += p['reliability'] * p['firms']
            s['reliability'] /= max(1, s['lines'])
            s['grossProfit'] = s['revenue'] - s['cogs']
            s['margin'] = s['grossProfit'] / s['revenue'] if s['revenue'] else 0.0
            s['utilization'] = s['made'] / s['capacity'] if s['capacity'] else 0.0
            s['fillRate'] = s['fulfilled'] / s['active'] if s['active'] else 0.0
            s['volumeShare'] = s['sold'] / analytics['t2Sold'] if analytics['t2Sold'] else 0.0
            return s

        t2Industries = []
        for i, name in enumerate(M.T2_SECTORS):
            d = summarize_markets([p for p in t2ProductStats if p['sector'] == name], name)
            d['description'] = M.T2_SECTOR_DEFINITIONS[i]['description']
            t2Industries.append(d)
        t2Complexity = []
        for c in M.TIER_BOUNDARIES['T2']:
            d = summarize_markets([p for p in t2ProductStats if p['complexity'] == c], 'Complexity ' + str(c))
            d['complexity'] = c
            t2Complexity.append(d)
        t2Totals = summarize_markets(t2ProductStats, 'All Tier 2 industries')
        productCategories = []
        for c in [1, 2, 3, 4, 5]:
            products = [p for p in (productStats if c < 3 else t2ProductStats) if p['complexity'] == c]
            s = summarize_markets(products, 'C-' + str(c))
            s['complexity'] = c
            s['tier'] = 'Tier 1' if c < 3 else 'Tier 2'
            s['role'] = 'Business inputs' if c < 3 else 'Galactic end-use goods'
            s['machineryPrice'] = products[0]['machineryPrice'] if products else 0
            s['unitCapacity'] = s['capacity'] / s['lines'] if s['lines'] else 0.0
            s['avgPrice'] = float(sum(p['avgPrice'] * p['firms'] for p in products) / max(1, s['lines']))
            s['avgUnitCost'] = float(sum(p['avgUnitCost'] * p['firms'] for p in products) / max(1, s['lines']))
            s['soldPerLine'] = s['sold'] / s['lines'] if s['lines'] else float('nan')
            s['profitPerLine'] = s['grossProfit'] / s['lines'] if s['lines'] else float('nan')
            productCategories.append(s)
        analytics['latest']['t2Industries'] = [{'name': x['name'], 'made': x['made'], 'sold': x['sold'],
                                                'active': x['active'], 'fulfilled': x['fulfilled'],
                                                'revenue': x['revenue'], 'cogs': x['cogs'],
                                                'grossProfit': x['grossProfit'], 'utilization': x['utilization'],
                                                'fillRate': x['fillRate']} for x in t2Industries]
        analytics['latest'].update({'t2GrossProfit': t2Totals['grossProfit'], 't2Capacity': t2Totals['capacity'],
                                    't2Utilization': t2Totals['utilization'], 't2Desired': t2Totals['active'],
                                    't2Fulfilled': t2Totals['fulfilled'], 't2FillRate': t2Totals['fillRate']})

        selectedT2 = self._tier2_company(self.selectedT2Id) if self.selectedTierControl == 'T2' else None
        if not selectedT2 or self.tier2HistoryCompany != self.selectedT2Id:
            self.tier2CompanyHistory = []
            self.tier2HistoryCompany = self.selectedT2Id if selectedT2 else -1
        if selectedT2:
            c = selectedT2
            point = {'tick': self.tick, 'id': c['id'], 'cash': c['cash'], 'equity': c['equity'],
                     'made': c['made'], 'sold': c['sold'], 'revenue': c['revenue'], 'cogs': c['cogs'],
                     'grossProfit': c['grossProfit'], 'utilization': c['utilization']}
            if self.tier2CompanyHistory and self.tier2CompanyHistory[-1].get('tick') == self.tick:
                self.tier2CompanyHistory[-1] = point
            else:
                self.tier2CompanyHistory.append(point)
            if len(self.tier2CompanyHistory) > 240:
                self.tier2CompanyHistory.pop(0)

        elementStats = []
        for i, e in enumerate(M.ELEMENTS):
            elementStats.append({
                'name': e, 'code': ['W', 'E', 'F', 'A'][i], 'price': float(m['wP'][i]),
                'volume': float(m['wVol'][i]),
                'revenue': float(W.t0Revenue[i::NE].sum()),
                'cogs': float(W.t0COGS[i::NE].sum()),
                'grossProfit': float((W.t0Revenue[i::NE] - W.t0COGS[i::NE]).sum()),
                'difficulty': float(W.difficulty[i]), 'hhi': analytics['t0HHI'][i],
                'reliability': _market_reliability([W.t0Rel[j * NE + i] for j in range(N0) if M.ELEMENTS[i] in T0P[j]['elements']],
                                                   [W.t0Sold[j * NE + i] for j in range(N0) if M.ELEMENTS[i] in T0P[j]['elements']])})

        lastSnapshot = {
            'world': dict(M.WORLD_STORY, population=cfg['endUserCount']),
            'tick': self.tick, 'month': self.month, 'calendar': M.calendar_at(self.tick),
            'invention': {'possible': M.T2_CATALOGUE_COUNT, 'invented': len(M.T2_PRODUCTS),
                          'reserved': len(M.T2_UNINVENTED_PRODUCTS)},
            'tps': tps, 'mode': self.mode, 'targetTPS': self.targetTPS,
            'adminAccounting': dict(self.adminAccounting, lastEquipmentReceipt=(
                dict(self.adminAccounting['lastEquipmentReceipt']) if self.adminAccounting['lastEquipmentReceipt'] else None)),
            'ownership': {'licenses': list(self.playerLicenses),
                          'licenseCosts': dict(M.PROGRESSION_DEFAULTS['licenseCosts']),
                          'house': dict(self.playerHouse) if self.playerHouse else None,
                          'houseFoundingCost': M.PROGRESSION_DEFAULTS['houseFoundingCost'],
                          'accounting': dict(self.ownershipAccounting)},
            'difficulty': {M.ELEMENTS[e]: float(W.difficulty[e]) for e in range(NE)},
            'wholesaleAvg': m['wAvg'], 'retailAvg': m['rAvg'],
            'wholesaleVolume': m['wVolume'], 'retailVolume': m['rVolume'],
            'retailOrders': analytics['orderTotal'], 'fulfilledOrders': analytics['fulfilledOrders'],
            'elements': elementStats, 'products': productStats, 'tier2Products': t2ProductStats,
            'productCategories': productCategories, 'tier2Cohorts': t2Cohorts,
            'tier2Industries': t2Industries, 'tier2Complexity': t2Complexity,
            'tier2CompanyHistory': self.tier2CompanyHistory, 'tier2Companies': self._tier2_page(),
            'performance': {'lastTickMs': self.workerStats['lastTickMs'],
                            'averageTickMs': self.workerStats['totalTickMs'] / max(1, self.workerStats['steps']),
                            'stateBytes': int(sum(a.nbytes for a in (getattr(W, n) for n in W.array_names))),
                            'activeLines': int(W.t2LineCount),
                            'activatedConsumers': self.state.get('activatedConsumers', 0),
                            'orders': self.state.get('activeOrders', 0)},
            'cohorts': analytics['cohort'], 't0Companies': self._company_summaries_t0(),
            'analyticsHistory': self.analyticsHistory,
            'tiers': {
                't0': {'firms': N0, 'bought': 0, 'made': float(analytics['t0Produced'].sum()),
                       'cogs': _sum(W.t0COGS), 'grossProfit': analytics['t0Revenue'] - _sum(W.t0COGS),
                       'inventory': analytics['t0Inventory'], 'cash': analytics['t0Cash'],
                       'equity': analytics['t0Equity'], 'sold': analytics['t0Sold'],
                       'revenue': analytics['t0Revenue'], 'productionByElement': list(analytics['t0Produced']),
                       'hhi': analytics['t0HHI'], 'reliability': analytics['latest']['avgT0Reliability']},
                't1': {'firms': N1, 'inventory': analytics['latest']['t1Inventory'],
                       'raw': analytics['t1Raw'], 'finished': analytics['t1Finished'],
                       'cash': analytics['t1Cash'], 'equity': analytics['t1Equity'],
                       'bought': _sum(W.t1Bought), 'made': analytics['t1Made'],
                       'sold': analytics['t1Sold'], 'revenue': analytics['t1Revenue'],
                       'cogs': analytics['t1COGS'], 'grossProfit': analytics['t1Revenue'] - analytics['t1COGS'],
                       'desired': float(sum(p['active'] for p in productStats)),
                       'fulfilled': float(sum(p['fulfilled'] for p in productStats)),
                       'stockUnmet': float(sum(p['stockUnmet'] for p in productStats)),
                       'activeFirms': analytics['activeFirms'], 'players': analytics['players'],
                       'reliability': analytics['latest']['avgT1Reliability']},
                't2': {'firms': cfg['t2FirmCount'], 'activeLines': analytics['t2Lines'],
                       'inventory': analytics['t2Inventory'], 'finished': _sum(W.t2Fin, lc),
                       'stockCoverage': (float(W.t2Fin[:lc].sum() / W.t2SalesEMA[:lc].sum()) if W.t2SalesEMA[:lc].sum() > 0 else None),
                       'tradingFirms360': int((W.t2LastSaleTick[:cfg['t2FirmCount']] > 0).sum()) if self.tick > 0 else 0,
                       'cash': analytics['t2Cash'], 'equity': analytics['t2Equity'],
                       'bought': _sum(W.t2Bought, cfg['t2FirmCount']), 'made': analytics['t2Made'],
                       'sold': analytics['t2Sold'], 'revenue': analytics['t2Revenue'],
                       'cogs': analytics['t2COGS'], 'grossProfit': analytics['t2Revenue'] - analytics['t2COGS'],
                       'capacity': t2Totals['capacity'], 'utilization': t2Totals['utilization'],
                       'margin': t2Totals['margin'], 'desired': t2Totals['active'],
                       'fulfilled': t2Totals['fulfilled'], 'fillRate': t2Totals['fillRate']},
                'endUsers': {'population': cfg['endUserCount'], 'potential': analytics['potential'],
                             'active': analytics['active'], 'fulfilled': analytics['fulfilled'],
                             'priceLost': analytics['priceLost'], 'stockUnmet': analytics['stockUnmet'],
                             'orders': analytics['orderTotal'], 'fulfilledOrders': analytics['fulfilledOrders'],
                             'unitFillRate': analytics['unitFillRate'], 'orderFillRate': analytics['orderFillRate'],
                             'priceLossShare': analytics['priceLossShare'],
                             'stockUnmetShare': analytics['stockUnmetShare'],
                             'revenue': analytics['retailRevenue']},
            },
            'companies': companies,
            'selected': selectedT2 or {
                'tier': 'T1', 'products': self._company_detail('T1', sid)['products'], 'id': sid,
                'name': T1P[sid // 100]['name'] + ' ' + str((sid % 100) + 1).zfill(3),
                'sector': M.t1_sector(scode), 'controller': 'PLAYER' if self.controller[sid] else 'BOT',
                'online': bool(self.online[sid]), 'price': float(W.t1Price[sid * NP + spi]),
                'cash': float(W.t1Cash[sid]), 'finished': float(W.t1Fin[sid * NP + spi]),
                'inventory': float(W.raw[sid * NE:(sid + 1) * NE].sum() + W.t1Fin[sid * NP + spi]),
                'eqBook': float(W.t1EqBook[sid]), 'equipment': list(self.equipment[sid]),
                'reliability': float(W.t1Rel[sid * NP + spi])},
            'engine': 'python', 'expandedDetails': self._watched_details(),
        }
        lastSnapshot['endUsers'] = lastSnapshot['tiers']['endUsers']
        lastSnapshot['tiers']['t3'] = lastSnapshot['endUsers']
        analytics['latest']['tiers'] = {t: {k: (list(v) if isinstance(v, (list, np.ndarray)) else v)
                                             for k, v in s.items()}
                                        for t, s in lastSnapshot['tiers'].items()}
        analytics['latest']['difficulty'] = list(W.difficulty)
        analytics['latest']['elementPrices'] = list(m['wP'])
        analytics['latest']['materialPrices'] = list(m['rP'])
        self.lastSnapshot = lastSnapshot
        return lastSnapshot
