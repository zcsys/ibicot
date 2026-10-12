import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from tools.buying_v2.retail_world import clear_distributors
from tools.buying_v2.observations import empty_totals, FIELDS
from tools.buying_v2.discovery import sample_distinct


class RetailWorldTests(unittest.TestCase):
    def test_distinct_bounded_discovery(self):
        for n in range(12):
            ids = np.arange(n, dtype=np.int64)
            for incumbent in (-1, 0, n + 1):
                for tick in range(20):
                    result = sample_distinct(ids, incumbent, 137, tick, 40, 12)
                    np.testing.assert_array_equal(result, sample_distinct.py_func(ids, incumbent, 137, tick, 40, 12))
                    self.assertEqual(list(result), sorted(result))
                    self.assertEqual(len(result), len(set(result)))
                    self.assertTrue(set(result).issubset(set(ids)))
                    self.assertEqual(len(result), min(5, n - int(incumbent in ids)) + int(incumbent in ids))
                    if incumbent in ids:
                        self.assertIn(incumbent, result)

    def fixture(self, incumbent=-1):
        cfg, w = reset_world(dict(t2FirmCount=3, distributorCount=1,
                                 distributorActivation=1, t2ReservationPremium=0, seed=137))
        w.t2LineProduct[:3] = 0
        w.distributorProduct[0] = M.NP
        w.distributorPreferredSupplier[0] = incumbent
        w.distributorQMax[0] = 20
        w.distributorEta[0] = 1
        profile = M.procurement_profile(M.T2_PRODUCTS[0], cfg, M.reference_tier2_cost(M.T2_PRODUCTS[0], cfg))
        w.distributorChoke[0] = 10 / profile['valuation']
        w.t2Price[:3] = [10., 15., 30.]
        w.t2Fin[:3] = [2., 20., 20.]
        w.t2FinBasis[:3] = [2., 3., 4.]
        return cfg, w

    def test_actual_postings_and_two_engine_agreement(self):
        results = []
        for fast in (False, True):
            cfg, w = self.fixture()
            cash = w.t2Cash.copy()
            obs = empty_totals(M.NP + len(M.T2_PRODUCTS))
            counts = clear_distributors(w, cfg, 1, obs, compiled=fast)
            np.testing.assert_array_equal(w.t2Sold[:3], [2, 6, 0])
            np.testing.assert_array_equal(w.t2Fin[:3], [0, 14, 20])
            np.testing.assert_array_equal(w.t2Revenue[:3], [20, 90, 0])
            np.testing.assert_array_equal(w.t2COGS[:3], [4, 18, 0])
            self.assertEqual(float((w.t2Cash - cash).sum()), 110.)
            self.assertEqual(counts[3], 110.)
            self.assertEqual(w.distributorPreferredSupplier[0], -1)
            self.assertEqual(obs[M.NP, FIELDS.index('unitsBought')], 8)
            results.append((w, obs, counts))
        for name in results[0][0].array_names:
            np.testing.assert_array_equal(getattr(results[0][0], name), getattr(results[1][0], name), err_msg=name)
        np.testing.assert_array_equal(results[0][1], results[1][1])
        self.assertEqual(results[0][2], results[1][2])

    def test_limited_stock_keeps_full_quote_request_and_original_preference(self):
        for units in (0,2):
            for fast in (False,True):
                cfg,w=self.fixture(2)
                w.t2Fin[:3]=[units,0,0]
                cash=w.t2Cash.copy()
                obs=empty_totals(M.NP+len(M.T2_PRODUCTS))
                result=clear_distributors(w,cfg,1,obs,compiled=fast)
                self.assertEqual(w.marketPotential[M.NP],20)
                self.assertEqual(w.distributorLastQ[0],10)
                self.assertEqual(w.distributorLastFulfilled[0],units)
                self.assertEqual(w.t2Demand[0],10)
                self.assertEqual(w.t2RelAttempts[0],1)
                self.assertEqual(w.distributorPreferredSupplier[0],2)
                self.assertEqual(result[3],units*10.)
                self.assertEqual(w.t2SwitchingIncome.sum(),0)
                self.assertEqual(obs[M.NP,FIELDS.index('unitsBought')],units)
                self.assertEqual(obs[M.NP,FIELDS.index('requestLegs')],1)
                self.assertEqual(float((w.t2Cash-cash).sum()),units*10.)

    def test_split_order_pays_once_and_retains_old_incumbent(self):
        cfg, w = self.fixture(2)
        valuation = M.procurement_profile(M.T2_PRODUCTS[0], cfg, M.reference_tier2_cost(M.T2_PRODUCTS[0], cfg))['valuation']
        w.lm3 = 2 / (valuation * (1 + w.t2Rel[2]))
        obs = empty_totals(M.NP + len(M.T2_PRODUCTS))
        counts = clear_distributors(w, cfg, 1, obs)
        np.testing.assert_array_equal(w.t2Sold[:3], [2, 6, 0])
        self.assertEqual(w.distributorPreferredSupplier[0], 2)
        self.assertAlmostEqual(w.t2SwitchingIncome[w.t2LineFirm[2]], 2.)
        self.assertAlmostEqual(counts[3], 112.)
        self.assertEqual(w.loyaltySwitches[2], 1)
        self.assertEqual(obs[M.NP, FIELDS.index('preferenceChanges')], 0)

class RetailContinuationTests(unittest.TestCase):
    def test_full_tick_accounts_and_policy_checked_continuation(self):
        import tempfile
        from pathlib import Path
        from economy.server.runtime import KernelRuntime
        from economy.server.persistence import save_checkpoint, load_checkpoint
        from tools.buying_v2.engine import RetailEngine
        from tools.buying_research.recording import Recorder
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            rt = KernelRuntime(dict(t2FirmCount=4200, distributorCount=1000, seed=137))
            engine = RetailEngine(rt)
            recorder = Recorder(path, rt.world, rt.cfg)
            for tick in range(1, 5):
                old0, old1 = rt.world.t0Inv.copy(), rt.world.t1Fin.copy()
                engine.step(tick)
                recorder.record(rt.world, tick, rt.state, old0, old1)
            inv = recorder.invariants()
            for key in ('maxCompanyToleranceRatio', 'maxMoneyToleranceRatio', 'maxGoodsToleranceRatio'):
                self.assertLessEqual(inv[key], 1, key)
            stem = str(path / 'world')
            save_checkpoint(stem, rt.cfg, 4, rt.world, rt.state, {'purchasePolicy': engine.policy})
            with self.assertRaisesRegex(ValueError, 'purchasing policy'):
                load_checkpoint(stem)
            cfg, tick, world, state = load_checkpoint(stem, purchase_policy=engine.policy)
            self.assertEqual(tick, 4)
            resumed = KernelRuntime(cfg)
            resumed.world, resumed.state = world, state
            other = RetailEngine(resumed)
            for tick in range(5, 9):
                engine.step(tick)
                other.step(tick)
                for name in rt.world.array_names:
                    np.testing.assert_array_equal(getattr(rt.world, name), getattr(world, name), err_msg=name)
                np.testing.assert_array_equal(engine.observations, other.observations)
                for name in ('costSinks', 'equipmentSinks', 'lm1', 'lm3', 'aov1', 'aov3'):
                    self.assertEqual(getattr(rt.world, name), getattr(world, name))


if __name__ == '__main__':
    unittest.main()
