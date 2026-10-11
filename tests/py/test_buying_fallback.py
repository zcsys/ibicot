"""Pin the user's A=10, B=8, A-stock=2 fallback example independently."""
import unittest
import numpy as np

from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import tick as reference, numba as accelerated
from tools.buying_research.fallback import price_fallback
from tools.buying_research.solvers import marginal_values, retail
from tools.buying_research.oracle import retail_oracle


class FallbackTests(unittest.TestCase):
    def test_user_example_and_further_fallback(self):
        prices = np.array([10., 15., 30.])  # Demand is 10, 8, 5.
        for stock, expected, requests in (
            ([2., 20., 20.], [2, 6, 0], [10, 6, -1]),
            ([2., 1., 20.], [2, 1, 2], [10, 6, 2]),
            ([2., 3., 20.], [2, 3, 0], [10, 6, 0]),
            ([0., 0., 0.], [0, 0, 0], [10, 8, 5]),
        ):
            args = (20., 10., 1., .5, prices, np.array(stock))
            for solve in (price_fallback, price_fallback.py_func):
                allocation, wanted = solve(*args)
                np.testing.assert_array_equal(allocation, expected)
                np.testing.assert_array_equal(wanted, requests)

    def test_fee_free_equivalence_to_independent_basket_oracle(self):
        rng = np.random.default_rng(28113)
        for _ in range(500):
            n = int(rng.integers(1, 5))
            latent = float(rng.integers(1, 7))
            half = float(rng.uniform(.5, 20))
            eta = float(rng.uniform(.5, 4))
            rounding = float(rng.uniform(.01, .99))
            prices = np.sort(rng.integers(1, 30, size=n)).astype(float)
            stock = rng.integers(0, 5, size=n).astype(float)
            allocation, _ = price_fallback(latent, half, eta, rounding, prices, stock)
            values = marginal_values(latent, half, eta, rounding)
            oracle = retail_oracle(values, prices, stock, -1, 0, 0., 1e9)
            candidate = retail(values, prices, stock, -1, 0, 0., 1e9)
            np.testing.assert_array_equal(allocation, oracle[0])
            np.testing.assert_array_equal(allocation, candidate[0])

    def test_existing_reference_and_compiled_retail_match_user_example(self):
        # No incumbent/fee, one active Distributor, and all three offers sampled.
        # This exercises actual stock, sales, cash, COGS and demand posting.
        for fast in (False, True):
            cfg, w = reset_world(dict(t2FirmCount=3, distributorCount=1,
                distributorActivation=1, distributorSearchOffers=20,
                t2ReservationPremium=0, seed=137))
            w.t2LineProduct[:3] = 0
            w.distributorProduct[0] = M.NP
            w.distributorPreferredSupplier[0] = -1
            w.distributorQMax[0] = 20
            w.distributorEta[0] = 1
            profile = M.procurement_profile(M.T2_PRODUCTS[0], cfg,
                M.reference_tier2_cost(M.T2_PRODUCTS[0], cfg))
            w.distributorChoke[0] = 10 / profile['valuation']
            w.t2Price[:3] = [10., 15., 30.]
            w.t2Fin[:3] = [2., 20., 20.]
            w.t2FinBasis[:3] = [2., 3., 4.]
            before = w.t2Cash.copy()
            if fast:
                accelerated.clear_distributors(w, cfg, 1)
            else:
                reference.clear_distributors(w, cfg, M.PRODUCTS, M.T2_PRODUCTS, 1)
            np.testing.assert_array_equal(w.t2Sold[:3], [2, 6, 0])
            np.testing.assert_array_equal(w.t2Fin[:3], [0, 14, 20])
            np.testing.assert_array_equal(w.t2Demand[:3], [10, 6, 0])
            np.testing.assert_array_equal(w.t2Revenue[:3], [20, 90, 0])
            np.testing.assert_array_equal(w.t2COGS[:3], [4, 18, 0])
            self.assertAlmostEqual(float((w.t2Cash-before).sum()), 110.)
            self.assertEqual(w.distributorLastFulfilled[0], 8)
            self.assertEqual(w.distributorLastQ[0], 8)
            self.assertEqual(w.loyaltyPenalties[2], 0)


if __name__ == '__main__':
    unittest.main()
