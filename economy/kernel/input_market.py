"""Supplier book for one manufacturing complexity phase.

Distributors clear opening finished inventory before manufacturing. Manufacturing
runs in ascending complexity order, rebuilding this book between phases: C4
buyers can purchase freshly produced C3 goods plus unsold opening inventory.
Within a phase stock only decreases, preserving the compiled stock index and
avoiding company-iteration priority over newly produced inputs. All new goods
enter inventory first; settlement preserves cash, book value and inventory basis.
"""
import numpy as np
from ..core import model as M


class InputMarket:
    def __init__(self, world, tick):
        from .tick import market_offers
        self.world = world
        self.tick = tick
        self.n1 = M.N1 * M.NP
        self.lc = int(world.t2LineCount)
        self.owner = np.concatenate((np.arange(self.n1, dtype=np.int64)//M.NP,
                                     M.N1 + world.t2LineFirm[:self.lc].astype(np.int64)))
        self._initial = {}
        # T2 arrays are snapshots: production continues against the live arrays.
        for key, suffix in [('fin','Fin'), ('price','Price'), ('rel','Rel'),
                            ('sold','Sold'), ('revenue','Revenue'), ('cogs','COGS'),
                            ('basis','FinBasis'), ('demand','Demand'),
                            ('attempts','RelAttempts'), ('available','RelAvailable')]:
            values = np.concatenate((getattr(world,'t1'+suffix), getattr(world,'t2'+suffix)[:self.lc])).astype(np.float64)
            setattr(self,key,values)
            self._initial[key] = values.copy()
        self.checks = np.concatenate((world.t1RelAvailChecks, np.zeros(self.lc)))
        self.cash = np.concatenate((world.t1Cash,world.t2Cash))
        self._cash_initial = self.cash.copy()
        self.switch_income = np.concatenate((world.t1SwitchingIncome,world.t2SwitchingIncome))
        self._income_initial = self.switch_income.copy()
        self.opportunities = np.zeros(M.NI)
        self.intermediate_sold = np.zeros(M.NI)
        self.intermediate_revenue = np.zeros(M.NI)
        t1 = market_offers(world,1,tick)
        t2 = market_offers(world,2,tick)
        self.offers = t1 + [[self.n1 + i for i in t2[p['id']]] for p in M.T2_INPUT_PRODUCTS[M.NP:]]
        self.off = np.zeros(M.NI+1,dtype=np.int64)
        self.off[1:] = np.cumsum([len(x) for x in self.offers])
        self.flat = np.asarray([i for market in self.offers for i in market],dtype=np.int64)

    def settle(self):
        w = self.world
        for key, suffix in [('fin','Fin'), ('sold','Sold'), ('revenue','Revenue'),
                            ('cogs','COGS'), ('demand','Demand'), ('attempts','RelAttempts'),
                            ('available','RelAvailable')]:
            delta = getattr(self,key) - self._initial[key]
            a,b = getattr(w,'t1'+suffix),getattr(w,'t2'+suffix)
            a[:] += delta[:self.n1].astype(a.dtype)
            b[:self.lc] += delta[self.n1:].astype(b.dtype)
        w.t1RelAvailChecks[:] = self.checks[:self.n1]
        cash_delta = self.cash - self._cash_initial
        w.t1Cash[:] += cash_delta[:M.N1]
        w.t2Cash[:] += cash_delta[M.N1:]
        income_delta = self.switch_income - self._income_initial
        w.t1SwitchingIncome[:] += income_delta[:M.N1]
        w.t2SwitchingIncome[:] += income_delta[M.N1:]
        w.t1Opportunities[:] += self.opportunities[:M.NP].astype(w.t1Opportunities.dtype)
        w.t1IntermediateSold[:] += self.intermediate_sold[:M.NP]
        w.t1IntermediateRevenue[:] += self.intermediate_revenue[:M.NP]
        ids = np.array([p['id'] for p in M.T2_INPUT_PRODUCTS[M.NP:]],dtype=np.int64)
        w.t2Opportunities[ids] += self.opportunities[M.NP:].astype(w.t2Opportunities.dtype)
        w.t2IntermediateSold[ids] += self.intermediate_sold[M.NP:]
        w.t2IntermediateRevenue[ids] += self.intermediate_revenue[M.NP:]
        # Remaining stock and newly made stock have different cost bases.
        # Production has already averaged the original stock with new output;
        # remove the sold units at their original book cost, not that new mean.
        sold = - (self.fin - self._initial['fin'])[self.n1:]
        moved = sold > 0
        w.t2LastSaleTick[w.t2LineFirm[:self.lc][moved]] = self.tick
        remaining = w.t2Fin[:self.lc]
        before_settlement_units = remaining + sold
        value = before_settlement_units * w.t2FinBasis[:self.lc] - sold * self.basis[self.n1:]
        np.divide(value, remaining, out=w.t2FinBasis[:self.lc], where=moved & (remaining > 0))
        w.t2FinBasis[:self.lc][moved & (remaining <= 0)] = 0
