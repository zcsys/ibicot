"""Experimental retail-only treatment; industrial buying stays baseline.

Keep this treatment distinct from the future corrected industrial baseline.
Production defaults and import graph remain unchanged.
"""
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K, numba as N
from .observations import empty_totals
from .retail_world import clear_distributors


class RetailEngine:
    policy = 'v2-retail-only-v2'
    industrial_coverage = ()

    def __init__(self, runtime, compiled=True, industrial_observations=True, history_window=0, trace_sample=0):
        from .industrial_observations import empty_totals as empty_industrial
        self.industrial_observations = empty_industrial() if industrial_observations else None
        from .seller_history import SellerHistory
        if history_window and self.industrial_coverage != ('t1','t2'):
            raise ValueError('seller history currently requires both industrial tiers')
        self.seller_history = SellerHistory(history_window) if history_window else None
        if isinstance(trace_sample, bool) or int(trace_sample) != trace_sample or trace_sample < 0:
            raise ValueError('trace sample must be a nonnegative integer')
        if trace_sample and self.industrial_coverage != ('t1','t2'):
            raise ValueError('decision traces require both industrial tiers')
        self.trace_sample = trace_sample
        self.decision_traces = {}
        self.retail_trace = None
        self.purchase_trace = None
        self.purchase_exposure = None
        self.runtime = runtime
        self.compiled = compiled
        self.observations = empty_totals(M.NP + len(M.T2_PRODUCTS))

    def step(self, tick):
        rt = self.runtime
        w, cfg, state = rt.world, rt.cfg, rt.state
        if self.industrial_observations is not None:
            self.industrial_observations.fill(0)
        if self.seller_history is not None and any(
                channel['lastTick'] != tick - 1 for channel in self.seller_history.channels.values()):
            raise ValueError('seller history tick does not precede engine step')
        self.decision_traces = {}
        self.retail_trace = None
        self.purchase_trace = None
        K.reset_tick(w)
        w.costSinks = 0
        w.equipmentSinks = 0
        K.update_environment(w, cfg, tick)
        K.operate_tier0(w, cfg, K.T0P, tick)
        if self.seller_history is not None:
            opening = w.t0Inv.copy()
            sold_before = w.t0Sold.copy()
            quotes = w.t0Price.copy()
            self.purchase_exposure = np.zeros((3, len(opening)), dtype=np.uint64)
        self.prepare_trace(M.N1, cfg, tick, 1, 1)
        self.buy_refinery_inputs(w, cfg, tick)
        if self.seller_history is not None:
            self.seller_history.record('t0-wholesale', tick,
                np.tile(np.arange(M.NE), M.N0), np.repeat(np.arange(M.N0), M.NE),
                N.PROF_HAS.ravel().astype(bool) & np.isfinite(quotes),
                opening, w.t0Inv, quotes, w.t0Sold - sold_before,
                self.purchase_exposure, lot=int(cfg['minWholesaleLot']))
        N.operate_tier1(w, cfg)
        K.price_markets(w, cfg, K.T0P, M.PRODUCTS, tick)
        if self.seller_history is not None:
            lc = int(w.t2LineCount)
            opening = w.t2Fin[:lc].copy()
            sold_before = w.t2Sold[:lc].copy()
            quotes = w.t2Price[:lc].copy()
            self.purchase_exposure = np.zeros((3, lc), dtype=np.uint64)
        if self.trace_sample:
            from .retail_traces import RetailTrace
            self.retail_trace = RetailTrace(int(cfg['distributorCount']),self.trace_sample,cfg['seed'],tick,cfg['distributorActivation'])
        o, f, a, payment, purchases = clear_distributors(w, cfg, tick, self.observations, self.compiled,
            self.purchase_exposure,self.retail_trace.arrays if self.retail_trace is not None else None)
        if self.seller_history is not None:
            self.seller_history.record('retail', tick,
                M.NP + w.t2LineProduct[:lc], w.t2LineFirm[:lc], np.isfinite(quotes),
                opening, w.t2Fin[:lc], quotes, w.t2Sold[:lc] - sold_before, self.purchase_exposure)
        self.operate_manufacturers(w, cfg, tick)
        counts = dict(orders=o, filledOrders=f, activated=a, distributorPayments=payment, purchaseOrders=purchases)
        N.observe_markets(w, cfg, K.T0P)
        K.update_reliability(w, cfg, tick)
        K.expand_tier2_bots(w, cfg, M.T2_PRODUCTS, tick)
        K.update_loyalty_regime(w, cfg, counts, tick)
        state.update(K.settle_storage_rent(w, cfg, tick))
        state.update(K.finalize_net_earnings(w, cfg))
        state.update(activatedDistributors=a, distributorPayments=payment,
                     costSinks=w.costSinks, equipmentSinks=w.equipmentSinks,
                     activeOrders=o, fulfilledOrders=f)
        return state

    def prepare_trace(self, population, cfg, tick, tier, phase):
        self.purchase_trace = None
        if self.trace_sample:
            from .decision_traces import DecisionTrace
            trace = DecisionTrace(population, self.trace_sample, cfg['seed'], tick, tier, phase)
            self.decision_traces[(tier, phase)] = trace
            self.purchase_trace = trace.arrays

    def phase_history_observer(self, world, tick, phase):
        if self.seller_history is None:
            self.purchase_exposure = None
            return None
        self.purchase_exposure = np.zeros((3, M.N1 * M.NP + int(world.t2LineCount)), dtype=np.uint64)
        exposure = self.purchase_exposure
        def observe(book):
            offered = np.zeros(len(book.fin), dtype=bool)
            offered[book.flat] = True
            self.seller_history.record(f'input-C{phase}', tick,
                np.concatenate((np.tile(np.arange(M.NP), M.N1), M.NP + world.t2LineProduct[:book.lc])),
                book.owner, offered, book._initial['fin'], book.fin, book._initial['price'],
                book.sold - book._initial['sold'], exposure)
        return observe

    def operate_manufacturers(self, world, cfg, tick):
        N.operate_tier2(world, cfg, tick)

    def buy_refinery_inputs(self, world, cfg, tick):
        N.plan_and_buy_inputs(world, cfg, tick)


class ReplenishmentReferenceEngine(RetailEngine):
    """D3 T2 comparison only; T1 remains baseline, no deployment claim."""
    policy = 'v2-t2-replenishment-reference-v1'
    industrial_coverage = ('t2',)

    def operate_manufacturers(self, world, cfg, tick):
        from .industrial_adapter import buy_t2_reference
        def purchase(w,c,t,f,p,b):
            return buy_t2_reference(w,c,t,f,p,b,observations=self.industrial_observations,exposure=self.purchase_exposure,trace=self.purchase_trace)
        for phase in M.TIER_BOUNDARIES['T2']:
            self.prepare_trace(int(cfg['t2FirmCount']), cfg, tick, 2, phase)
            observer = self.phase_history_observer(world, tick, phase)
            K._operate_tier2_phase(world,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,tick,phase,
                                  purchase_company=purchase,phase_observer=observer)


class IndustrialReferenceEngine(ReplenishmentReferenceEngine):
    """Both industrial tiers use D3 replenishment; isolated reference policy."""
    policy = 'v2-industrial-replenishment-reference-v1'
    industrial_coverage = ('t1','t2')

    def buy_refinery_inputs(self, world, cfg, tick):
        from .refinery import buy_reference
        def purchase(w,c,t,f,p):
            return buy_reference(w,c,t,f,p,observations=self.industrial_observations,exposure=self.purchase_exposure,trace=self.purchase_trace)
        K.plan_and_buy_inputs(world,cfg,M.PRODUCTS,K.T0P,tick,purchase_company=purchase)


class ManufacturerCompiledEngine(IndustrialReferenceEngine):
    """Same D3 policy; T2 population compiled, T1 reference pending parity."""
    def operate_manufacturers(self, world, cfg, tick):
        from .manufacturer_compiled import buy, phase_kernel
        for phase in M.TIER_BOUNDARIES['T2']:
            self.prepare_trace(int(cfg['t2FirmCount']), cfg, tick, 2, phase)
            observer = self.phase_history_observer(world, tick, phase)
            N._operate_tier2_phase(world,cfg,tick,phase,purchase_company=buy,execution_kernel=phase_kernel,purchase_observations=self.industrial_observations,purchase_exposure=self.purchase_exposure,purchase_trace=self.purchase_trace,phase_observer=observer)


class IndustrialCompiledEngine(ManufacturerCompiledEngine):
    """Same D3 policy with both company populations executing compiled loops."""
    def buy_refinery_inputs(self, world, cfg, tick):
        from .refinery_compiled import buy, phase_kernel
        N.plan_and_buy_inputs(world,cfg,tick,purchase_company=buy,execution_kernel=phase_kernel,purchase_observations=self.industrial_observations,purchase_exposure=self.purchase_exposure,purchase_trace=self.purchase_trace)
