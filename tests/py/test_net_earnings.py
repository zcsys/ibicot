"""Net decision signals must reconcile independently to company book equity."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from economy.core import model as M
from economy.core.accounting import allocate_to_lines, company_earnings, finalize_net_earnings
from economy.core.state import reset_world, T0P
from economy.kernel import tick as K, numba as NB
from economy.server.persistence import save_checkpoint, load_checkpoint
from economy.server.runtime import KernelRuntime


def equity(w, cfg, tier):
    if tier != 't0':
        return K.storage_rent_equity(w, cfg, tier)
    machines = np.array([len(p['element_indices']) for p in T0P]) * cfg['t0Machinery']
    return w.t0Cash + cfg['t0License'] + cfg['t0Reserve'] + machines + (w.t0Inv * w.t0InvBasis).reshape(M.N0, M.NE).sum(1)


class NetEarningsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = patch('economy.server.runtime._STATS_DIR', Path(self.tmp.name))
        p.start(); self.addCleanup(p.stop)

    def test_signed_profit_learning_in_both_engines(self):
        for previous, profit, sign in [(-100,-90,1),(-100,-110,-1),(-100,-101,0),
                                       (0,0,0),(0,10,1),(0,-10,-1),(10,-1,-1)]:
            args = dict(old_price=100.,profit=profit,previous_profit=previous,direction=1,
                        sales=0.,stock=0.,demand=0.,available=0.,step_scale=1.,
                        market_price=100.,band=.02,pricing_aggressiveness=.35,response=.05)
            r=M.adaptive_price(**args)
            self.assertEqual(np.sign(r['price']-100),sign)
            if NB._HAVE_NUMBA:
                self.assertEqual(NB._adaptive_price(**args),(r['price'],r['direction'],r['stepScale']))

    def test_postings_preserve_gross_learning_forecast_applies_even_when_exempt(self):
        cfg,w=reset_world({'t2FirmCount':12,'distributorCount':30})
        w.t1Operates[1]=1
        w.t0SwitchingIncome[0]=30
        w.t1SwitchingIncome[0]=20
        w.t1SwitchingExpense[0]=30
        w.t2SwitchingIncome[0]=4
        w.t2SwitchingExpense[0]=20
        w.t1RentCharge[0]=100
        w.t2RentCharge[0]=40
        # Nonzero gross observations must survive all period postings unchanged.
        for t in ['t0','t1','t2']:getattr(w,t+'LearnProfit').fill(123)
        finalize_net_earnings(w,cfg)
        np.testing.assert_array_equal(w.t0LearnProfit,123)
        np.testing.assert_array_equal(w.t1LearnProfit,123)
        np.testing.assert_array_equal(w.t2LearnProfit,123)
        K.reset_tick(w)
        self.assertEqual(w.t1SwitchingExpense.sum(),0)
        # Rent exemption must not waive switching costs; expense estimate is
        # prior posted net transfers × alpha, shared by the two refinery lines.
        self.assertEqual(K.production_line_overhead(w,cfg,'t1')[0],.75)
        self.assertAlmostEqual(K.production_line_overhead(w,cfg,'t2')[0],2.4)
        self.assertLess(K.production_line_overhead(w,cfg,'t0')[0],0)

    def test_transaction_ledgers_and_equity_reconcile_in_both_engines(self):
        for fast in [False,True]:
            if fast and not NB._HAVE_NUMBA:continue
            cfg,w=reset_world({'t2FirmCount':400,'distributorCount':800,'storageRentPerUnitYear':.072})
            w.t0Inv[:]=np.isfinite(w.t0Price)*50000.
            w.t0InvBasis[:]=1
            w.t0Price[np.isfinite(w.t0Price)]=1.25
            for e in range(M.NE):
                sellers=[i for i,p in enumerate(T0P) if e in p['element_indices']]
                w.preferredWholesale[e::M.NE]=sellers[0]
                w.t0Price[sellers[0]*M.NE+e]=3
            w.t1Fin[:]=5000.*w.t1Operates
            w.t1FinBasis[:]=1.5
            w.t1Price[np.isfinite(w.t1Price)]=3
            for m in range(M.NP):
                sellers=np.flatnonzero(w.t1Operates[m::M.NP])*M.NP+m
                w.t2Preferred[m::M.NP]=sellers[0]
                w.t1Price[sellers[0]]=5
            for i in range(400):
                pid=i%len(M.T2_PRODUCTS)
                w.t2LineProduct[i]=pid
                w.t2Sector[i]=M.T2_PRODUCTS[pid]['sectorIndex']
                w.t2Price[i]=12 if i<200 else 10
                w.t2Fin[i]=100
                w.t2FinBasis[i]=2
            w.t1Cash[:]+=1000000
            w.t2Cash[:400]+=1000000
            w.distributorProduct[:800]=np.arange(800)%200+M.NP
            w.distributorPreferredSupplier[:800]=np.arange(800)%200
            seen=np.zeros(3)
            for tick in range(1,5):
                before={t:equity(w,cfg,t).copy() for t in ['t0','t1','t2']}
                with patch.object(NB,'_HAVE_NUMBA',fast):K.tick(w,cfg,tick)
                for tier in before:
                    np.testing.assert_allclose(equity(w,cfg,tier)-before[tier],company_earnings(w,cfg,tier),rtol=0,atol=1e-6)
                self.assertAlmostEqual(w.t0SwitchingIncome.sum(),w.t1SwitchingExpense.sum(),delta=1e-7)
                self.assertAlmostEqual(w.t1SwitchingIncome.sum(),w.t2SwitchingExpense.sum(),delta=1e-7)
                self.assertAlmostEqual(w.t2SwitchingIncome.sum(),w.loyaltyPenalties[2],delta=1e-7)
                seen+=w.loyaltyPenalties
            self.assertTrue((seen>0).all(),(fast,seen))

    def test_snapshot_groups_publish_complete_net_earnings(self):
        rt=KernelRuntime({'t2FirmCount':12,'distributorCount':30})
        w=rt.world
        w.t0SwitchingIncome[0]=7
        w.t1SwitchingIncome[0]=10
        w.t1SwitchingExpense[0]=7
        w.t2SwitchingExpense[0]=10
        w.t2SwitchingIncome[0]=3
        s=rt.publish()
        for tier,expected in [('t0',7),('t1',3),('t2',-7)]:
            self.assertEqual(s['tiers'][tier]['netEarnings'],expected)
        self.assertEqual(sum(x['switchingIncome'] for x in s['elements']),7)
        self.assertEqual(sum(x['switchingExpense'] for x in s['tier2Products']),10)
        self.assertEqual(rt.company_detail('T0',0)['switchingIncome'],7)
        self.assertEqual(rt.company_detail('T1',0)['switchingExpense'],7)
        np.testing.assert_array_equal(rt._tier2_sort_values(np.array([0,1]),'netProfit'),[-7,0])

    def test_checkpoint_preserves_postings_and_migrates_old_windows(self):
        cfg,w=reset_world({'t2FirmCount':12,'distributorCount':30})
        w.t1SwitchingIncome[0]=12;w.t1SwitchingNetEMA[0]=3
        w.t1LearnProfit[0]=99;w.t1LearnPrevious[0]=88;w.t1LearnTicks[0]=10
        stem=str(Path(self.tmp.name)/'accounting')
        save_checkpoint(stem,cfg,1,w)
        _,_,loaded,_=load_checkpoint(stem)
        self.assertEqual(loaded.t1SwitchingIncome[0],12)
        self.assertEqual(loaded.t1SwitchingNetEMA[0],3)
        self.assertEqual(loaded.t1LearnProfit[0],99)
        meta=json.loads(Path(stem+'.json').read_text());meta['version']=4
        Path(stem+'.json').write_text(json.dumps(meta))
        _,_,loaded,_=load_checkpoint(stem)
        self.assertTrue(loaded.netEarningsAvailable)
        self.assertEqual(loaded.t1SwitchingIncome[0],12)
        self.assertEqual(loaded.t1SwitchingNetEMA[0],3)
        self.assertEqual(loaded.t1LearnProfit[0],0)
        self.assertTrue(np.isnan(loaded.t1LearnPrevious[0]))
        meta['version']=3
        Path(stem+'.json').write_text(json.dumps(meta))
        np.savez(stem+'.npz',**{name:getattr(w,name) for name in w.array_names if 'Switching' not in name})
        _,_,loaded,_=load_checkpoint(stem)
        self.assertFalse(loaded.netEarningsAvailable)
        self.assertEqual(loaded.t1LearnProfit[0],0)
        self.assertTrue(np.isnan(loaded.t1LearnPrevious[0]))
        self.assertEqual(loaded.t1SwitchingNetEMA[0],0)
