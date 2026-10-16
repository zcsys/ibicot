"""Benchmark subscription: shared exemption, operation stop, decisions, and reporting."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.core.accounting import company_earnings
from economy.kernel import tick as K, numba as NB
from economy.server.runtime import KernelRuntime, stats_row
from economy.server.persistence import save_checkpoint, load_checkpoint
from economy.server.recording import profitability_rows, company_financials


class IntelligenceTests(unittest.TestCase):
    def test_shared_boundary_and_cash_sink(self):
        cfg,w=reset_world({'t2FirmCount':3,'distributorCount':1})
        w.t2Cash[:3] += np.array([-1,0,1])
        before=K.storage_rent_equity(w,cfg,'t2').copy()
        cash=w.t2Cash[:3].copy()
        out=K.settle_period_costs(w,cfg,1)
        np.testing.assert_array_equal(w.t2RentCharge[:3],[0,56,56])
        np.testing.assert_array_equal(w.t2IntelligenceCharge[:3],[0,20,20])
        np.testing.assert_array_equal(cash-w.t2Cash[:3],[0,76,76])
        np.testing.assert_array_equal(before-K.storage_rent_equity(w,cfg,'t2'),[0,76,76])
        self.assertEqual(out['t1IntelligenceExpense'],2000*M.N1)
        self.assertEqual(w.costSinks,2140*M.N1+152)
        np.testing.assert_array_equal(company_earnings(w,cfg,'t2'),[0,-76,-76])
        self.assertEqual(w.t0IntelligenceCharge.sum(),0)

    def test_no_partial_payment_and_resume(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1})
        w.t2Cash[0]=75; w.t2EqBook[0]=500000
        K.settle_period_costs(w,cfg,1)
        self.assertEqual(w.t2Cash[0],75)
        self.assertEqual(w.t2Operating[0],0)
        self.assertEqual(w.t2IntelligenceCharge[0],0)
        self.assertEqual(w.t2RentCharge[0],0)
        self.assertEqual(w.t2RentArrears[0],0)
        w.t2Cash[0]=76
        K.settle_period_costs(w,cfg,2)
        self.assertEqual(w.t2Operating[0],1)
        self.assertEqual(w.t2Cash[0],0)
        self.assertEqual(w.t2IntelligencePaid[0],20)
        # Payment crossing the threshold must not erase this tick's overhead.
        self.assertEqual(K.production_line_overhead(w,cfg,'t2')[0],76)
        w.t2EqBook[0]=499999
        K.settle_period_costs(w,cfg,3)
        self.assertEqual(w.t2Operating[0],1)
        self.assertEqual(w.t2IntelligenceCharge[0],0)

    def test_stopped_companies_cannot_trade_produce_or_reprice(self):
        for fast in (False,True):
            if fast and not NB._HAVE_NUMBA:continue
            cfg,w=reset_world({'t2FirmCount':4,'distributorCount':10,'distributorActivation':1})
            for tier in ('t1','t2'):
                getattr(w,tier+'Cash').fill(1)
                getattr(w,tier+'EqBook').fill(2000000)
                getattr(w,tier+'Fin').fill(100)
                getattr(w,tier+'LearnTicks').fill(60)
                getattr(w,tier+'LearnDemand').fill(1000)
            w.distributorPreferredSupplier[:10]=0
            prices=[w.t1Price.copy(),w.t2Price.copy()]
            stocks=[w.t1Fin.copy(),w.t2Fin.copy()]
            with patch.object(NB,'_HAVE_NUMBA',fast): K.tick(w,cfg,30)
            for tier,price,stock in zip(('t1','t2'),prices,stocks):
                self.assertEqual(getattr(w,tier+'Operating')[:(M.N1 if tier=='t1' else 4)].sum(),0)
                self.assertEqual(getattr(w,tier+'Sold').sum(),0)
                self.assertEqual(getattr(w,tier+'Bought').sum(),0)
                np.testing.assert_array_equal(getattr(w,tier+'Price'),price)
                np.testing.assert_array_equal(getattr(w,tier+'Fin'),stock)
            self.assertEqual(w.t2Made.sum(),0)

    def test_decision_gate_and_multiline_allocation(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1})
        np.testing.assert_array_equal(K.production_line_overhead(w,cfg,'t1'),2140)
        self.assertEqual(K.production_line_overhead(w,cfg,'t2')[0],76)
        self.assertEqual(M.production_batches(32,1,5.82,8,56,.05),32)
        self.assertEqual(M.production_batches(32,1,5.82,8,76,.05),0)
        w.t1Operates[1]=1
        self.assertEqual(K.production_line_overhead(w,cfg,'t1')[0],1070)
        w.t1Cash[0]-=1
        self.assertEqual(K.production_line_overhead(w,cfg,'t1')[0],0)
        w.t2LearnProfit[:]=123
        K.settle_period_costs(w,cfg,1)
        np.testing.assert_array_equal(w.t2LearnProfit,123)

    def test_reports_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp, patch('economy.server.runtime._STATS_DIR',Path(tmp)):
            rt=KernelRuntime({'t2FirmCount':2,'distributorCount':1})
            w,cfg=rt.world,rt.cfg
            rt.state.update(K.settle_period_costs(w,cfg,1))
            from economy.core.accounting import finalize_net_earnings
            finalize_net_earnings(w,cfg)
            rows=profitability_rows(w,cfg)
            self.assertEqual(sum(r['intelligence'] for r in rows if r['tier']=='t2'),40)
            self.assertEqual(company_financials(w,cfg,'t2')['intelligence'].sum(),40)
            snap=rt.publish()
            self.assertEqual(snap['tiers']['t2']['intelligenceExpense'],40)
            self.assertEqual(sum(r['intelligenceExpense'] for r in snap['tier2Products']),40)
            stem=str(Path(tmp)/'state')
            save_checkpoint(stem,cfg,1,w)
            _,_,loaded,_=load_checkpoint(stem)
            np.testing.assert_array_equal(loaded.t2IntelligencePaid,w.t2IntelligencePaid)
            # Legacy saved worlds retain their original zero subscription rate.
            meta=json.loads(Path(stem+'.json').read_text());meta['version']=9
            for key in ['t1IntelligencePerTick','t2IntelligencePerTick']:meta['cfg'].pop(key)
            Path(stem+'.json').write_text(json.dumps(meta))
            legacy,_,_,_=load_checkpoint(stem)
            self.assertEqual(legacy['t1IntelligencePerTick'],0)

    def test_equity_and_cash_reconcile_both_engines(self):
        for fast in (False,True):
            if fast and not NB._HAVE_NUMBA:continue
            cfg,w=reset_world({'t2FirmCount':4,'distributorCount':10})
            w.t1Cash+=100000;w.t2Cash[:4]+=100000
            before={t:K.storage_rent_equity(w,cfg,t).copy() for t in ('t1','t2')}
            cash=w.t0Cash.sum()+w.t1Cash.sum()+w.t2Cash[:4].sum()
            with patch.object(NB,'_HAVE_NUMBA',fast): result=K.tick(w,cfg,1)
            for tier in before:
                np.testing.assert_allclose(K.storage_rent_equity(w,cfg,tier)-before[tier],company_earnings(w,cfg,tier),atol=1e-6)
            after=w.t0Cash.sum()+w.t1Cash.sum()+w.t2Cash[:4].sum()
            self.assertAlmostEqual(after-cash,result['distributorPayments']-w.costSinks,places=5)
