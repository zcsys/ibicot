"""Vectorized P&L history. Margins are ratios of posted totals, never averages.

Per-tick product rows retain the evidence for arbitrary period/complexity/sector
queries. Annual company archives retain period totals and ending balance sheets
so distributions can be calculated after the process exits.
"""
import json
import time
from pathlib import Path

import numpy as np

from ..core import model as M
from ..core.accounting import allocate_to_lines, company_earnings, firm_count


def company_financials(world, cfg, tier):
    n = firm_count(cfg, tier)
    lc = int(world.t2LineCount)
    def aggregate(name):
        values = getattr(world, tier + name)
        if tier == 't2':
            return np.bincount(world.t2LineFirm[:lc], weights=values[:lc], minlength=n)
        return values.reshape(n, -1).sum(axis=1)
    return dict(revenue=aggregate('Revenue'), cogs=aggregate('COGS'),
                sold=aggregate('Sold'), netEarnings=company_earnings(world, cfg, tier),
                rent=np.zeros(n) if tier == 't0' else getattr(world, tier+'RentCharge')[:n].copy(),
                operating=getattr(world, tier+'Operating')[:n].copy(),
                intelligence=getattr(world, tier+'IntelligenceCharge')[:n].copy(),
                switchingIncome=getattr(world, tier+'SwitchingIncome')[:n].copy(),
                switchingExpense=getattr(world, tier+'SwitchingExpense')[:n].copy())


def profitability_rows(world, cfg):
    """One row per product, aggregated with bincount rather than company loops."""
    rows = []
    for tier, products in [('t0', M.ELEMENTS), ('t1', M.PRODUCTS), ('t2', M.T2_PRODUCTS)]:
        n = firm_count(cfg, tier)
        length = int(world.t2LineCount) if tier == 't2' else n*len(products)
        ids = world.t2LineProduct[:length] if tier == 't2' else np.tile(np.arange(len(products)), n)
        fields = {key: getattr(world, tier+suffix)[:length] for key, suffix in
                  [('revenue','Revenue'), ('cogs','COGS'), ('sold','Sold')]}
        for key, suffix in [('intelligence','IntelligenceCharge'), ('rent','RentCharge'), ('switchingIncome','SwitchingIncome'), ('switchingExpense','SwitchingExpense')]:
            amounts = np.zeros(n) if tier == 't0' and key == 'rent' else getattr(world,tier+suffix)[:n]
            fields[key] = allocate_to_lines(world,cfg,tier,amounts)
        totals = {key: np.bincount(ids, weights=value, minlength=len(products)) for key,value in fields.items()}
        for i,p in enumerate(products):
            row = {key:float(value[i]) for key,value in totals.items()}
            row.update(tier=tier, product=str(p) if tier=='t0' else p['catalogId'],
                       complexity=0 if tier=='t0' else p['complexity'],
                       sector=str(p) if tier=='t0' else p['sector'])
            row['grossProfit'] = row['revenue']-row['cogs']
            row['netEarnings'] = (row['grossProfit']+row['switchingIncome']-row['switchingExpense']-row['rent']-row['intelligence']) if world.netEarningsAvailable else None
            row['grossMargin'] = row['grossProfit']/row['revenue'] if row['revenue'] else None
            row['netMargin'] = row['netEarnings']/row['revenue'] if row['revenue'] and row['netEarnings'] is not None else None
            rows.append(row)
    return rows


class CompanyHistory:
    """Yearly period totals by company plus balances; flush partial years on pause.

    Files carry explicit start/end ticks. Partial intervals can be summed to any
    requested year; accumulated P&L is never replaced by an equity difference.
    """
    def __init__(self, directory, cfg):
        self.path = Path(directory)/('company-history-'+str(time.time_ns()))
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
        (self.path/'catalog.json').write_text(json.dumps({
            'revision':M.CATALOG_REVISION, 'companyNumbering':M.COMPANY_NUMBERING,
            'refinedProducts':M.PRODUCTS, 'manufacturedProducts':M.T2_PRODUCTS},indent=2)+'\n')
        self.totals = {}; self.start = None; self.end = None

    def record(self, world, cfg, tick):
        if self.start is None: self.start = tick
        self.end = tick
        for tier in ('t0','t1','t2'):
            for name,values in company_financials(world,cfg,tier).items():
                key = tier+'_'+name
                if key not in self.totals: self.totals[key] = values.copy()
                else: self.totals[key] += values
        if tick % M.TIME['ticksPerYear'] == 0: self.flush(world,cfg)

    def flush(self, world, cfg):
        if self.start is None: return
        from ..kernel.tick import storage_rent_equity
        data = dict(self.totals, startTick=self.start, endTick=self.end,
                    netEarningsAvailable=world.netEarningsAvailable)
        for tier in ('t0','t1','t2'):
            n=firm_count(cfg,tier)
            data[tier+'_cash'] = getattr(world,tier+'Cash')[:n]
            data[tier+'_equity'] = (world.t0Cash+cfg['t0License']+cfg['t0Reserve']
                +np.isfinite(world.t0Price.reshape(n,M.NE)).sum(axis=1)*cfg['t0Machinery']
                +(world.t0Inv*world.t0InvBasis).reshape(n,M.NE).sum(axis=1)) if tier=='t0' else storage_rent_equity(world,cfg,tier)
        for tier in ('t1', 't2'):
            n = firm_count(cfg, tier)
            for suffix in ('RentPaid', 'RentArrears', 'IntelligencePaid'):
                data[tier + '_' + suffix] = getattr(world, tier + suffix)[:n]
        data['t1Operates'] = world.t1Operates
        lc=int(world.t2LineCount)
        data['t2LineFirm'] = world.t2LineFirm[:lc]
        data['t2LineProduct'] = world.t2LineProduct[:lc]
        data['t2Sector'] = world.t2Sector[:cfg['t2FirmCount']]
        np.savez_compressed(self.path/f'companies-{self.start:06}-{self.end:06}.npz',**data)
        self.totals = {}; self.start = None
