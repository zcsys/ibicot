"""Research observations without changing world state or inferring P&L from equity."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from economy.core import model as M
from economy.core.accounting import allocate_to_lines, company_earnings, firm_count
from economy.core.state import tier1_storage_capacities
from economy.kernel.tick import storage_rent_equity
from economy.server.recording import company_financials

FIELDS = ('revenue', 'cogs', 'sold', 'attempted', 'made', 'capacity', 'finished',
          'quoteSum', 'lines', 'switchIncome', 'switchExpense', 'rent', 'net',
          'attempts', 'available', 'intermediateSold', 'retailRequested', 'retailSold',
          'retailPotential', 'rawSpace', 'cash', 'equity', 'companies',
          'recordedUnitCostSum','initialReferenceCostSum')


def equity(world, cfg, tier):
    if tier != 't0':
        return storage_rent_equity(world, cfg, tier)
    return (world.t0Cash + cfg['t0License'] + cfg['t0Reserve']
            + np.isfinite(world.t0Price.reshape(M.N0, M.NE)).sum(axis=1)*cfg['t0Machinery']
            + (world.t0Inv*world.t0InvBasis).reshape(M.N0,M.NE).sum(axis=1))


def goods(world, cfg):
    """Embodied raw-element count: conserved by every current recipe."""
    n = cfg['t2FirmCount']; lc = int(world.t2LineCount)
    c1 = np.array([p['complexity'] for p in M.PRODUCTS])
    ci = np.array([p['complexity'] for p in M.T2_INPUT_PRODUCTS])
    c2 = np.array([p['complexity'] for p in M.T2_PRODUCTS])
    return float(world.t0Inv.sum()+world.raw.sum()
        +(world.t1Fin.reshape(M.N1,M.NP)*c1).sum()+world.t2Raw[:n*M.NE].sum()
        +(world.t2T1Raw[:n*M.NI].reshape(n,M.NI)*ci).sum()
        +(world.t2Fin[:lc]*c2[world.t2LineProduct[:lc]]).sum())


class Recorder:
    def __init__(self, path, world, cfg):
        self.path=Path(path); self.cfg=cfg
        self.products=([dict(tier='t0',id=p,complexity=0,route='extraction') for p in M.ELEMENTS]
            +[dict(tier='t1',id=p['catalogId'],complexity=p['complexity'],route='c'+str(p['complexity'])) for p in M.PRODUCTS]
            +[dict(tier='t2',id=p['catalogId'],complexity=p['complexity'],route=p['demandGroup']) for p in M.T2_PRODUCTS])
        (self.path/'measurement-schema.json').write_text(json.dumps(dict(version=2,fields=FIELDS,products=self.products,
            notes={'attempted':'Supplier first-request quantities in R1; retry attempts can duplicate intentions in baseline. Not interchangeable.',
                   'retailRequested':'One last price-dependent request per activated buyer in baseline; not latent demand.',
                   'rawSpace':'Company input inventory apportioned equally across installed lines.',
                   'companies':'Fractional allocation across installed lines; sums to tier company count.',
                   'quoteSum':'Sum of finite current quotes; divide by lines for unweighted mean. Realized price = revenue/sold.',
                   'made':'T0/T1 stock-flow identity, T2 posted production. T0 extraction may be fractional.',
                   'net':'Line revenue minus line COGS plus allocated company fees minus allocated expenses/rent.'}),indent=2)+'\n')
        self.buffer=[]; self.ticks=[]; self.company={}; self.period_start=1
        self.structure={}
        for ti,tier in enumerate(('t0','t1','t2')):
            count=firm_count(cfg,tier);size=(M.NE,M.NP,len(M.T2_PRODUCTS))[ti]
            lc=int(world.t2LineCount);length=(M.N0*M.NE,M.N1*M.NP,lc)[ti]
            ids=world.t2LineProduct[:lc].astype(int) if ti==2 else np.tile(np.arange(size),count)
            mask=(np.isfinite(world.t0Price) if ti==0 else world.t1Operates.astype(bool) if ti==1 else np.ones(lc,dtype=bool))
            cap=(np.full(length,cfg['t0Capacity']) if ti==0 else
                 np.tile([M.refinery_capacity(p,cfg) for p in M.PRODUCTS],count) if ti==1 else
                 np.array([cfg['t2Capacity'][p['complexity']] for p in M.T2_PRODUCTS])[ids])
            self.structure[tier]=(count,size,length,ids,mask,cap)
        self.input_space=np.array([p['complexity'] for p in M.T2_INPUT_PRODUCTS])
        self.reference_costs={
            't0':np.full(M.N0*M.NE,cfg['baseCost']*cfg['difficultyTarget']),
            't1':np.tile([M.refinery_unit_cost(p,cfg) for p in M.PRODUCTS],M.N1),
            't2':np.array([M.initial_tier2_cost(p,cfg) for p in M.T2_PRODUCTS])[world.t2LineProduct[:int(world.t2LineCount)]]}
        self.previous_equity={t:equity(world,cfg,t) for t in ('t0','t1','t2')}
        np.savez_compressed(self.path/'opening-company-accounts.npz',
            **{t+'_equity':v for t,v in self.previous_equity.items()},
            **{t+'_cash':getattr(world,t+'Cash')[:firm_count(cfg,t)] for t in ('t0','t1','t2')})
        self.previous_cash=sum(getattr(world,t+'Cash')[:firm_count(cfg,t)].sum() for t in ('t0','t1','t2'))
        self.previous_goods=goods(world,cfg)
        self.max_equity_residual=0.; self.max_money_residual=0.; self.max_goods_residual=0.
        self.max_equity_ratio=0.;self.max_money_ratio=0.;self.max_goods_ratio=0.
        self.min_cash=float('inf'); self.min_stock=float('inf')
        self.price_floor_contacts=0;self.price_ceiling_contacts=0

    def record(self, w, tick, state, old0, old1):
        cfg=self.cfg; lc=int(w.t2LineCount); n=cfg['t2FirmCount']
        production=[w.t0Inv-old0+w.t0Sold,w.t1Fin-old1+w.t1Sold,w.t2Made[:lc]]
        rows=[]; current_cash=0.; earnings=[]
        for ti,tier in enumerate(('t0','t1','t2')):
            count,size,length,ids,mask,cap=self.structure[tier]
            prices=getattr(w,tier+'Price')[:length]
            self.price_floor_contacts+=int(np.count_nonzero(mask&(prices<=M.MIN_UNIT_PRICE)))
            self.price_ceiling_contacts+=int(np.count_nonzero(mask&(prices>=M.MAX_UNIT_PRICE)))
            stock=(w.t0Inv if ti==0 else getattr(w,tier+'Fin')[:length])
            raw=(np.zeros(count) if ti==0 else w.raw.reshape(count,M.NE).sum(axis=1) if ti==1 else
                 w.t2Raw[:n*M.NE].reshape(n,M.NE).sum(axis=1)+(w.t2T1Raw[:n*M.NI].reshape(n,M.NI)
                 *self.input_space).sum(axis=1))
            eq=equity(w,cfg,tier); net=company_earnings(w,cfg,tier)
            residual=eq-self.previous_equity[tier]-net
            self.max_equity_residual=max(self.max_equity_residual,float(np.abs(residual).max()))
            tolerance=1e-6+1e-12*np.maximum(np.abs(eq),np.abs(self.previous_equity[tier]))
            self.max_equity_ratio=max(self.max_equity_ratio,float(np.max(np.abs(residual)/tolerance)))
            self.previous_equity[tier]=eq
            cash=getattr(w,tier+'Cash')[:count]; current_cash+=float(cash.sum()); earnings.append(float(net.sum()))
            self.min_cash=min(self.min_cash,float(cash.min())); self.min_stock=min(self.min_stock,float(stock.min()),float(raw.min()))
            line=dict(revenue=getattr(w,tier+'Revenue')[:length],cogs=getattr(w,tier+'COGS')[:length],
                sold=getattr(w,tier+'Sold')[:length],attempted=getattr(w,tier+'Demand')[:length],
                made=production[ti],capacity=cap*mask,finished=stock,quoteSum=np.where(mask,prices,0),lines=mask.astype(float),
                attempts=getattr(w,tier+'RelAttempts')[:length],available=getattr(w,tier+'RelAvailable')[:length])
            line['recordedUnitCostSum']=(w.t0Cost if ti==0 else getattr(w,tier+'UnitCost')[:length])*mask
            line['initialReferenceCostSum']=self.reference_costs[tier]*mask
            for key,amount in [('switchIncome',getattr(w,tier+'SwitchingIncome')[:count]),
                    ('switchExpense',getattr(w,tier+'SwitchingExpense')[:count]),
                    ('rent',np.zeros(count) if ti==0 else getattr(w,tier+'RentCharge')[:count]),
                    ('net',net),('rawSpace',raw),('cash',cash),('equity',eq),('companies',np.ones(count))]:
                line[key]=allocate_to_lines(w,cfg,tier,amount)
            # Merchandise profit belongs to the actual selling line. Only
            # company-level charges/receipts require allocation across lines.
            line['net']=line['revenue']-line['cogs']+line['switchIncome']-line['switchExpense']-line['rent']
            data={key:np.bincount(ids,weights=val,minlength=size) for key,val in line.items()}
            for key in FIELDS:
                if key not in data: data[key]=np.zeros(size)
            if ti>0: data['intermediateSold']=getattr(w,tier+'IntermediateSold').copy()
            if ti==2:
                for key,src in [('retailRequested','marketActive'),('retailSold','marketFulfilled'),('retailPotential','marketPotential')]:
                    data[key]=getattr(w,src)[M.NP:].copy()
            rows.append(np.column_stack([data[key] for key in FIELDS]))
            for key,val in company_financials(w,cfg,tier).items():
                name=tier+'_'+key
                if name not in self.company: self.company[name]=val.copy()
                else: self.company[name]+=val
        external=state['distributorPayments']-w.costSinks-w.equipmentSinks
        money_error=abs(current_cash-self.previous_cash-external)
        self.max_money_residual=max(self.max_money_residual,money_error)
        self.max_money_ratio=max(self.max_money_ratio,money_error/(1e-4+1e-12*max(abs(current_cash),abs(self.previous_cash))))
        self.previous_cash=current_cash
        current_goods=goods(w,cfg)
        retail_removed=float(np.dot(w.marketFulfilled[M.NP:],[p['complexity'] for p in M.T2_PRODUCTS]))
        goods_error=abs(current_goods-self.previous_goods-production[0].sum()+retail_removed)
        self.max_goods_residual=max(self.max_goods_residual,goods_error)
        self.max_goods_ratio=max(self.max_goods_ratio,goods_error/(32*np.spacing(max(abs(current_goods),abs(self.previous_goods),1.))))
        self.previous_goods=current_goods
        for arr in (w.raw,w.t2Raw[:n*M.NE],w.t2T1Raw[:n*M.NI]):
            self.min_stock=min(self.min_stock,float(arr.min()))
        self.buffer.append(np.vstack(rows)); self.ticks.append(tick)
        if tick%360==0: self.flush(w,tick)

    def flush(self,w,tick):
        if not self.ticks:return
        np.savez_compressed(self.path/f'products-{self.ticks[0]:06}-{self.ticks[-1]:06}.npz',
                            ticks=self.ticks,data=np.stack(self.buffer))
        for tier in ('t0','t1','t2'):
            count=firm_count(self.cfg,tier)
            self.company[tier+'_cash']=getattr(w,tier+'Cash')[:count].copy()
            self.company[tier+'_equity']=self.previous_equity[tier]
        np.savez_compressed(self.path/f'companies-{self.period_start:06}-{tick:06}.npz',
            startTick=self.period_start,endTick=tick,t2LineFirm=w.t2LineFirm[:int(w.t2LineCount)],
            t2LineProduct=w.t2LineProduct[:int(w.t2LineCount)],t1Operates=w.t1Operates,**self.company)
        self.buffer=[];self.ticks=[];self.company={};self.period_start=tick+1

    def invariants(self):
        return dict(maxCompanyEquityResidual=self.max_equity_residual,maxMoneyResidual=self.max_money_residual,
                    maxEmbodiedGoodsResidual=self.max_goods_residual,minCash=self.min_cash,minStock=self.min_stock,
                    maxCompanyToleranceRatio=self.max_equity_ratio,maxMoneyToleranceRatio=self.max_money_ratio,
                    maxGoodsToleranceRatio=self.max_goods_ratio,
                    priceFloorLineTicks=self.price_floor_contacts,priceCeilingLineTicks=self.price_ceiling_contacts)
