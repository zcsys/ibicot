"""Independent extraction-machine throughput and shared resource constraints."""
import unittest
import numpy as np
from economy.core.state import reset_world, T0P
from economy.kernel.tick import operate_tier0


class ExtractionCapacity(unittest.TestCase):
    def world(self):
        cfg, w = reset_world({'t2FirmCount': 2, 'distributorCount': 0})
        w.t0Inv.fill(0)
        w.t0Cash.fill(1e8)
        w.t0Price.fill(10)
        w.difficulty.fill(1)
        return cfg, w

    def test_each_machine_has_full_independent_capacity(self):
        cfg, w = self.world()
        self.assertEqual(cfg['t0Storage'], 40000000)
        self.assertEqual(cfg['t0Capacity'], 500000)
        cash = w.t0Cash.copy()
        sink = w.costSinks
        operate_tier0(w, cfg, T0P, 1)
        for firm, profile in enumerate(T0P):
            for element in range(4):
                expected = 250000 if element in profile['element_indices'] else 0
                self.assertEqual(w.t0Inv[firm * 4 + element], expected)
            self.assertEqual(cash[firm] - w.t0Cash[firm], 250000 * len(profile['elements']))
        np.testing.assert_array_equal(w.t0Inv.reshape(-1, 4).sum(axis=0), [2500000] * 4)
        self.assertEqual(w.costSinks - sink, 10000000)

    def test_idle_machine_cannot_donate_throughput(self):
        cfg, w = self.world()
        target = cfg['t0Storage'] / 4
        w.t0Inv[:4] = [target, target, target, 0]
        operate_tier0(w, cfg, T0P, 1)
        np.testing.assert_array_equal(w.t0Inv[:4], [target, target, target, min(500000, target) / 2])

    def test_cash_and_storage_still_limit_company(self):
        cfg, w = self.world()
        cfg['t0Storage'] = 12000
        w.t0Cash[0] = 7000
        operate_tier0(w, cfg, T0P, 1)
        self.assertAlmostEqual(w.t0Inv[:4].sum(), 3500)
        self.assertGreaterEqual(w.t0Cash[0], 0)
        self.assertLessEqual(w.t0Inv[4:8].sum(), 12000)

    def test_final_cost_response_is_not_refilled(self):
        cfg, w = self.world()
        w.difficulty.fill(2)
        w.t0Cash[0] = 8000
        before = w.t0Cash[0]
        operate_tier0(w, cfg, T0P, 1)
        # 4,000 feasible units across four machines, divided by 1 + 2².
        self.assertLessEqual(abs(w.t0Inv[:4].sum() - 800), 4)
        self.assertAlmostEqual(before - w.t0Cash[0], 2 * w.t0Inv[:4].sum())

    def test_whole_extraction_with_fractional_costs_and_limits(self):
        cfg, w = self.world()
        w.difficulty[:] = [1.13, 1.27, 1.41, 1.59]
        w.t0Cash[:] = 17.3
        cfg['t0Storage'] = 13.7
        cfg['t0Capacity'] = 8.9
        before = w.t0Cash.copy()
        operate_tier0(w, cfg, T0P, 7)
        np.testing.assert_array_equal(w.t0Inv, np.floor(w.t0Inv))
        self.assertTrue(np.all(w.t0Cash >= 0))
        self.assertTrue(np.all(w.t0Inv.reshape(-1, 4).sum(axis=1) <= cfg['t0Storage']))
        np.testing.assert_allclose(before-w.t0Cash,
            (w.t0Inv.reshape(-1,4)*w.difficulty).sum(axis=1), atol=1e-12)
