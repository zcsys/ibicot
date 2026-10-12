"""T2 input buying is price-sensitive around the input's reference cost.

The industrial buying rule is: latent demand = fill storage to the brim, and the
actual request follows the Tier 3 curve with the input's reference cost as the
halving price (canon V = unit cost; elasticity = 2). This test only verifies the
direction of the response; the reference/compiled byte-equality is covered by
`test_buying_world.test_compiled_reference_settlement_and_accounting`.
"""
import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import numba as NB


class PriceSensitiveBuyingTests(unittest.TestCase):
    def _buy_sum(self, price):
        cfg, w = reset_world({'t2FirmCount': 200, 'distributorCount': 30})
        for i, p in enumerate(M.T2_PRODUCTS):
            w.t2LineProduct[i] = i
            w.t2Sector[i] = p['sectorIndex']
        w.t0Inv[:] = np.isfinite(w.t0Price) * 500000
        w.t0Price[np.isfinite(w.t0Price)] = price
        w.t0InvBasis[:] = 1
        w.t1Price[:] = price
        NB.plan_and_buy_inputs(w, cfg, 1)
        w.t1Fin[:] = w.t1Operates * 100000.0
        w.t1FinBasis[:] = 1.0
        NB.operate_tier2(w, cfg, 1)
        return float(w.t2Bought.sum())

    def test_higher_input_price_buys_less(self):
        low = self._buy_sum(0.1)
        mid = self._buy_sum(1.0)
        high = self._buy_sum(3.0)
        self.assertGreater(low, mid)
        self.assertGreater(mid, high)
