"""Opt-in experimental world engine, never imported by the application.

R1 full-world runs explicitly require one line per company. The general oracle
covers small multi-route cases; failure of that rollout scope is recorded rather
than silently falling back to sequential or heuristic procurement.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
import numpy as np

from economy.core import model as M
from economy.core.state import T0P,tier1_storage_capacities
from economy.core.accounting import finalize_net_earnings
from economy.kernel import numba as N
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket
from .settlement import procure,clear_retail,EVENT_FIELDS
from .production import manufacture


def book_ids(markets,nmarkets,eligible):
    ids=np.flatnonzero(eligible)
    ids=ids[np.argsort(markets[ids],kind='stable')]
    off=np.zeros(nmarkets+1,dtype=np.int64)
    off[1:]=np.cumsum(np.bincount(markets[ids],minlength=nmarkets))
    return ids.astype(np.int64),off


class ResearchEngine:
    def __init__(self,rt,treatment,path,options=None):
        self.rt=rt;self.w=rt.world;self.cfg=rt.cfg;self.path=Path(path);self.treatment=treatment
        cfg=self.cfg;w=self.w;self.options=dict(window=30,horizon=3.,hybridWeight=.5,
            coldStartCapacityFraction=.5,searchCount=5,fees=True,inventoryFeedback=True,
            reverseRetail=False,reverseIndustry=False,marketCapacityShare=False,anchor=True,
            quoteFirst=False,valueScale=1.,skipRedundantSolves=True)
        self.options.update(options or {})
        if treatment not in ('local','market','hybrid','sales','capacity'):
            raise ValueError('unknown experimental treatment '+treatment)
        self.n=cfg['t2FirmCount'];self.lc=int(w.t2LineCount)
        if np.any(w.t2FirmLineCount[:self.n]!=1) or np.any(w.t1Operates.reshape(M.N1,M.NP).sum(axis=1)!=1):
            raise ValueError('R1 full-world experimental scope requires one line per company; use multi-route oracle for general fixtures')
        self.t1_lines=np.argmax(w.t1Operates.reshape(M.N1,M.NP),axis=1)+np.arange(M.N1)*M.NP
        self.t2_lines=w.t2FirmLines[:self.n*M.T2_MAX_PRODUCTS_PER_FIRM:M.T2_MAX_PRODUCTS_PER_FIRM].astype(np.int64)
        self.t1_pids=np.tile(np.arange(M.NP,dtype=np.int64),M.N1)
        self.t0_ids,self.t0_off=book_ids(np.tile(np.arange(4),M.N0),4,np.isfinite(w.t0Price))
        self.retail_ids,self.retail_off=book_ids(w.t2LineProduct[:self.lc],len(M.T2_PRODUCTS),np.isfinite(w.t2Price[:self.lc]))
        self.t1_cap=np.array([M.refinery_capacity(p,cfg) for p in M.PRODUCTS])
        self.t1_cx=np.array([p['complexity'] for p in M.PRODUCTS],dtype=np.int64)
        self.t1_foot=np.array([cfg['footprint'][p['complexity']] for p in M.PRODUCTS])
        self.t1_conv=np.array([M.conversion_cost(p['complexity'],cfg) for p in M.PRODUCTS])
        self.t2_conv,_,self.t2_cap,self.t2_foot=N.t2_scale_arrays(cfg)
        self.local1=self.t1_cap[self.t1_pids]*self.options['coldStartCapacityFraction']*w.t1Operates
        self.local2=self.t2_cap[w.t2LineProduct[:self.lc]]*self.options['coldStartCapacityFraction']
        self.market1=self.t1_cap*M.T1_FIRMS_PER_MATERIAL*self.options['coldStartCapacityFraction']
        counts=np.bincount(w.t2LineProduct[:self.lc],minlength=len(M.T2_PRODUCTS))
        self.market2=self.t2_cap*counts*self.options['coldStartCapacityFraction']
        self.count1=np.bincount(self.t1_pids,weights=w.t1Operates,minlength=M.NP)
        self.count2=counts
        self.local_requests0=np.zeros(M.N0*4);self.local_requests1=np.zeros(M.N1*M.NP);self.local_requests2=np.zeros(self.lc)
        self.events1=np.zeros((M.N1,len(EVENT_FIELDS)));self.events2=np.zeros((self.n,len(EVENT_FIELDS)))
        self.events3=np.zeros((len(M.T2_PRODUCTS),len(EVENT_FIELDS)))
        self.trace1=np.full(((M.N1-1)//997+1,2,40+3*(self.options['searchCount']+1)),np.nan)
        self.trace2=np.full(((self.n-1)//997+1,2,40+3*(self.options['searchCount']+1)),np.nan)
        self.trace3=np.full(((cfg['distributorCount']-1)//10007+1,20+4*(self.options['searchCount']+1)),np.nan)
        self.requested0=np.zeros(4);self.requested1=np.zeros(M.NI);self.requested2=np.zeros(len(M.T2_PRODUCTS))
        self.supplied0=np.zeros(4);self.value0=np.zeros(4)
        self.history=[];self.event_history=[];self.trace_history=[];self.forecast_history=[]
        self.period_events1=np.zeros_like(self.events1);self.period_events2=np.zeros_like(self.events2)
        self.period_events3=np.zeros_like(self.events3)
        self.last_tick=0
        (self.path/'research-config.json').write_text(json.dumps(dict(treatment=treatment,options=self.options,
            schema=1,telemetrySchema=3,eventFields=EVENT_FIELDS,scope='single installed route per industry company',
            industryTraceColumns=['tick','inputMarket','oldPreference','seller','canonicalBid','uniqueRequested',
                'quantity','goodsPayment','fee','newPreference','plannedOutput','objective','horizonMean',
                'firm','line','product','heldInput','recipeQuantity','lot','inputSpace','inputSlot','freeStorage',
                'openingCash','finished','valuationOutputPrice','decisionCost','conversionReservePerOutput',
                'outputBound','incumbentSampleIndex','payableFee','sampleCount','canonicalQuote',
                'firstRequestRecipient','firstRequestQuantity','ingredientCount','basketCost',
                'reserved36','reserved37','reserved38','reserved39'],
            industryTraceOffers='From column 40: repeated stable supplier ID, solver quote, opening offered stock.',
            retailTraceColumns=['tick','market','oldPreference','firstSeller','canonicalBid','uniqueRequested',
                'quantity','goodsPayment','fee','newPreference','sellerCount','objective','latentL','halfPrice',
                'eta','roundingDraw','incumbentSampleIndex','payableFee','sampleCount','buyer'],
            retailTraceOffers='From column 20: repeated stable supplier ID, quote, opening stock, purchased quantity.',
            forecastErrors='tick x buyer tier (T1,T2) x (MAE,MSE,bias,mean forecast,mean first incoming requests); forecast uses prior completed tick.'),indent=2)+'\n')

    def forecast(self,local,market,pids,counts,cap):
        prior=market[pids]/np.maximum(1,counts[pids])
        # All installed routes for a product currently share one nominal capacity;
        # equal and capacity-weighted shares are algebraically identical here.
        if self.treatment in ('local','sales'):return local.copy()
        if self.treatment=='capacity':return cap[pids]*self.options['coldStartCapacityFraction']
        if self.treatment=='market':return prior
        weight=self.options['hybridWeight']
        return (1-weight)*local+weight*prior

    def step(self,tick,state):
        w=self.w;cfg=self.cfg;o=self.options;self.last_tick=tick
        started=time.perf_counter();self.stages={}
        forecast1=self.forecast(self.local1,self.market1,self.t1_pids,self.count1,self.t1_cap)
        forecast2=self.forecast(self.local2,self.market2,w.t2LineProduct[:self.lc],self.count2,self.t2_cap)
        for arr in (self.local_requests0,self.local_requests1,self.local_requests2,self.events1,self.events2,self.events3,
                    self.requested0,self.requested1,self.requested2,self.supplied0,self.value0):arr.fill(0)
        for arr in (self.trace1,self.trace2,self.trace3):arr.fill(np.nan)
        K.reset_tick(w);w.costSinks=0.;w.equipmentSinks=0.
        K.update_environment(w,cfg,tick);K.operate_tier0(w,cfg,T0P,tick)
        self.stages['prepareT0']=time.perf_counter()-started;started=time.perf_counter()
        # Preserve the baseline refinery cohort/firm rotation.
        orders=np.array([((tick%M.NP+c)%M.NP)*M.T1_FIRMS_PER_MATERIAL+
            ((tick*37)%M.T1_FIRMS_PER_MATERIAL+r)%M.T1_FIRMS_PER_MATERIAL
            for r in range(M.T1_FIRMS_PER_MATERIAL) for c in range(M.NP)],dtype=np.int64)
        if o['reverseIndustry']:orders=orders[::-1].copy()
        dummy=np.zeros(1)
        procure(cfg['seed'],tick,1,orders,-1,self.t1_lines,self.t1_pids,self.t1_cx,N.T1_ING_OFF,N.T1_ING_E,N.T1_ING_Q,
            np.ones(4),self.t1_cap,self.t1_foot,tier1_storage_capacities(cfg),self.t1_conv,K.production_line_overhead(w,cfg,'t1'),o['horizon'],forecast1,
            w.t1Cash,w.raw,w.rawBasis,dummy,dummy,w.t1Fin,w.t1Price,w.preferredWholesale,4,int(cfg['minWholesaleLot']),
            np.array([w.lm1]),cfg['baseCost'],self.t0_ids,self.t0_off,np.repeat(np.arange(M.N0),4),
            w.t0Inv,w.t0Price,w.t0Rel,w.t0InvBasis,w.t0Cash,w.t0Sold,w.t0Revenue,w.t0COGS,w.t0Demand,
            w.t0RelAttempts,w.t0RelChecks,w.t0RelAvailable,w.t0SwitchingIncome,w.t1SwitchingExpense,w.t1Bought,
            w.t1LastBuy,dummy,dummy,w.loyaltySwitches,w.loyaltyPenalties,self.requested0,self.supplied0,self.value0,
            self.local_requests0,self.events1,self.trace1,o['searchCount'],o['fees'],o['inventoryFeedback'],o['quoteFirst'],o['valueScale'],o['skipRedundantSolves'])
        self.stages['procureT1']=time.perf_counter()-started;started=time.perf_counter()
        w.t0Req[:]=self.requested0;w.t0FundedReq[:]=self.requested0;w.t0Fulfilled[:]=self.supplied0
        N.operate_tier1(w,cfg);K.price_markets(w,cfg,T0P,M.PRODUCTS,tick)
        self.stages['makePriceT1']=time.perf_counter()-started;started=time.perf_counter()
        w.sync_distributor_preferences()
        for name in ('marketPotential','marketActive','marketFulfilled','marketPriceLost','marketStockUnmet',
                     'distributorLastQ','distributorLastFulfilled'):getattr(w,name).fill(0)
        w.distributorLastMarket.fill(-1);w.distributorLastSupplier.fill(-1)
        retail_counts=clear_retail(cfg['seed'],tick,cfg['distributorCount'],cfg['distributorActivation'],o['searchCount'],w.lm3,
            cfg['t2ReservationPremium'],N.procurement_arrays(cfg),N.T2_COMPLEXITY,w.distributorProduct,
            w.distributorPreferredSupplier,w.distributorLastMarket,w.distributorLastSupplier,w.distributorLastQ,w.distributorLastFulfilled,
            w.distributorQMax,w.distributorChoke,w.distributorEta,w.marketPotential,w.marketActive,w.marketFulfilled,
            w.marketPriceLost,w.marketStockUnmet,self.retail_ids,self.retail_off,w.t2LineFirm,w.t2Fin,w.t2Price,w.t2Rel,
            w.t2Cash,w.t2LastSaleTick,w.t2Sold,w.t2Revenue,w.t2COGS,w.t2FinBasis,w.t2Demand,w.t2RelAttempts,w.t2RelAvailable,
            w.t2Opportunities,w.t2PotentialOrders,w.t2SwitchingIncome,w.loyaltySwitches,w.loyaltyPenalties,self.local_requests2,
            self.events3,self.trace3,o['fees'],o['reverseRetail'],M.NP,o['skipRedundantSolves'])
        counts=dict(zip(('orders','filledOrders','activated','distributorPayments','purchaseOrders'),retail_counts))
        self.stages['retail']=time.perf_counter()-started;started=time.perf_counter()
        self.requested2[:]=w.marketActive[M.NP:]
        for phase in M.TIER_BOUNDARIES['T2']:
            self.buy_make_phase(tick,phase,forecast2)
        self.stages['procureMakeT2']=time.perf_counter()-started;started=time.perf_counter()
        N.observe_markets(w,cfg,T0P);K.update_reliability(w,cfg,tick);K.expand_tier2_bots(w,cfg,M.T2_PRODUCTS,tick)
        K.update_loyalty_regime(w,cfg,counts,tick);state.update(K.settle_storage_rent(w,cfg,tick));state.update(finalize_net_earnings(w,cfg))
        state.update(activatedDistributors=counts['activated'],distributorPayments=counts['distributorPayments'],
            costSinks=w.costSinks,equipmentSinks=w.equipmentSinks,activeOrders=counts['orders'],fulfilledOrders=counts['filledOrders'])
        # One-tick publication lag; no same-tick forecast inflation.
        alpha=2/(o['window']+1)
        self.local1+=alpha*((w.t1Sold if self.treatment=='sales' else self.local_requests1)-self.local1)
        self.local2+=alpha*((w.t2Sold[:self.lc] if self.treatment=='sales' else self.local_requests2)-self.local2)
        self.market1+=alpha*(self.requested1[:M.NP]-self.market1)
        intermediate_ids=np.array([p['id'] for p in M.T2_INPUT_PRODUCTS[M.NP:]])
        self.requested2[intermediate_ids]+=self.requested1[M.NP:]
        self.market2+=alpha*(self.requested2-self.market2)
        self.record(tick,forecast1,forecast2)
        self.stages['observeRecord']=time.perf_counter()-started

    def buy_make_phase(self,tick,phase,forecast):
        w=self.w;cfg=self.cfg;o=self.options;book=InputMarket(w,tick)
        # Structural stable-ID book: available stock never affects sampling.
        markets=np.concatenate((self.t1_pids,np.full(self.lc,-1,dtype=np.int64)))
        for m,p in enumerate(M.T2_INPUT_PRODUCTS[M.NP:],M.NP):markets[M.N1*M.NP:][w.t2LineProduct[:self.lc]==p['id']]=m
        ids,off=book_ids(markets,M.NI,(markets>=0)&np.isfinite(book.price))
        local=np.concatenate((self.local_requests1,self.local_requests2))
        check=np.zeros_like(book.attempts);dummy=np.zeros(1)
        orders=(np.arange(self.n,dtype=np.int64)+tick*137)%self.n
        if o['reverseIndustry']:orders=orders[::-1].copy()
        procure(cfg['seed'],tick,2,orders,phase,self.t2_lines,w.t2LineProduct,N.T2_COMPLEXITY,N.T2_ING_OFF,N.T2_ING_M,N.T2_ING_Q,
            N.INPUT_SPACE,self.t2_cap,self.t2_foot,np.full(self.n,cfg['storage']),self.t2_conv,K.production_line_overhead(w,cfg,'t2'),o['horizon'],forecast,
            w.t2Cash,w.t2Raw,w.t2RawBasis,w.t2T1Raw,w.t2T1Basis,w.t2Fin,w.t2Price,w.t2Preferred,M.NI,1,w.lm2,
            M.material_switching_reference(cfg),ids,off,book.owner,book.fin,book.price,book.rel,book.basis,book.cash,
            book.sold,book.revenue,book.cogs,book.demand,book.attempts,check,book.available,book.switch_income,w.t2SwitchingExpense,
            w.t2Bought,dummy,w.t2MatSpend,w.t2MatOrders,w.loyaltySwitches,w.loyaltyPenalties,self.requested1,
            book.intermediate_sold,book.intermediate_revenue,local,self.events2,self.trace2,o['searchCount'],o['fees'],o['inventoryFeedback'],o['quoteFirst'],o['valueScale'],o['skipRedundantSolves'])
        book.checks+=check
        self.local_requests1[:]=local[:M.N1*M.NP];self.local_requests2[:]=local[M.N1*M.NP:]
        book.settle()
        going=K._market_going_rate(w.t2Price[:self.lc],w.t2LearnSales[:self.lc],w.t2LineProduct[:self.lc].astype(np.int64),len(M.T2_PRODUCTS))
        if not o['anchor']:going[:]=0
        w.costSinks+=manufacture(tick,self.n,phase,cfg['storage'],self.t2_foot,self.t2_cap,self.t2_conv,
            cfg['productionMarginBand'],K.production_line_overhead(w,cfg,'t2'),w.t2FirmLineCount,w.t2FirmLines,w.t2LineProduct,
            w.t2Raw,w.t2RawBasis,w.t2T1Raw,w.t2T1Basis,w.t2Cash,w.t2Fin,w.t2FinBasis,w.t2Price,w.t2UnitCost,
            w.t2ReplacementCost,w.t2Made,w.t2InputConsumed,w.t2Controller,w.t2PlayerPrice,w.t2RelPriceSum,w.t2RelPriceSamples,
            w.t2MonthlyCapacity,w.t2LearnTicks,w.t2LearnProfit,w.t2LearnSales,w.t2LearnPrevious,w.t2LearnDirection,
            w.t2LearnDemand,w.t2LearnStep,w.t2LearnOpportunity,w.t2LearnPotentialOpportunity,cfg['priceObservationTicks'],
            cfg['researchPriceMinimumPotentialOrders'],cfg['researchPriceMaxObservationTicks'],cfg['researchPriceMinimumOpportunities'],
            cfg['pricingAggressiveness'],cfg['wholesalePriceResponse'],going,cfg['marketAnchorBand'],cfg['switchingStableBand'])

    def record(self,tick,forecast1,forecast2):
        w=self.w
        self.last_forecast1=forecast1;self.last_forecast2=forecast2
        errors=[]
        for predicted,observed,mask in ((forecast1,self.local_requests1,w.t1Operates.astype(bool)),
                                        (forecast2,self.local_requests2,np.ones(self.lc,dtype=bool))):
            delta=predicted[mask]-observed[mask]
            errors.append([float(np.mean(abs(delta))),float(np.mean(delta*delta)),float(np.mean(delta)),
                           float(predicted[mask].mean()),float(observed[mask].mean())])
        self.forecast_history.append(errors)
        self.history.append(np.concatenate((self.requested0,self.requested1[:M.NP],self.requested2)))
        self.event_history.append(np.vstack((self.events1.sum(axis=0),self.events2.sum(axis=0),self.events3.sum(axis=0))))
        self.period_events1+=self.events1;self.period_events2+=self.events2;self.period_events3+=self.events3
        if tick%30==0:
            self.trace_history.append((tick,self.trace1.copy(),self.trace2.copy(),self.trace3.copy()))
        if tick%360==0:
            self.flush(tick,forecast1,forecast2)

    def flush(self,tick,forecast1=None,forecast2=None):
        if self.history:
            np.savez_compressed(self.path/f'requests-{tick-len(self.history)+1:06}-{tick:06}.npz',requested=np.array(self.history),
                events=np.array(self.event_history),forecastErrors=np.array(self.forecast_history),
                localForecast1=self.last_forecast1,localForecast2=self.last_forecast2,
                localRequests1=self.local_requests1,localRequests2=self.local_requests2,
                companyEvents1=self.period_events1,companyEvents2=self.period_events2,retailProductEvents=self.period_events3,
                **{f'{kind}_{t}':array for t,a,b,c in self.trace_history for kind,array in [('t1',a),('t2',b),('t3',c)]})
            self.history=[];self.event_history=[];self.trace_history=[];self.forecast_history=[]
            for a in (self.period_events1,self.period_events2,self.period_events3):a.fill(0)

    def save(self,path):
        np.savez_compressed(path,schema=1,lastTick=self.last_tick,local1=self.local1,local2=self.local2,
            market1=self.market1,market2=self.market2,options=json.dumps(self.options),treatment=self.treatment)

    def restore(self,path):
        with np.load(path,allow_pickle=False) as data:
            if int(data['schema'])!=1 or str(data['treatment'])!=self.treatment:raise ValueError('research checkpoint mismatch')
            if json.loads(str(data['options']))!=self.options:raise ValueError('research options mismatch')
            self.last_tick=int(data['lastTick'])
            for name in ('local1','local2','market1','market2'):getattr(self,name)[:]=data[name]
