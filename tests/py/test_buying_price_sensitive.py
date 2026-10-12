"""T2 input buying is price-sensitive around the input's reference cost.

The industrial buying rule is: latent demand = fill storage to the brim, and the
actual request follows the Tier 3 curve with the input's reference cost as the
halving price (canon V = unit cost; elasticity = 2). Cover reference costs,
quantity boundaries, and reference/compiled state and accounting parity.
"""
import unittest
import copy
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import numba as NB
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket


class PriceSensitiveBuyingTests(unittest.TestCase):
    def test_cached_references_follow_runtime_cost_settings(self):
        cfg, _ = reset_world({'t2FirmCount': 1, 'distributorCount': 1})
        original = NB.input_reference_arrays(cfg).copy()
        for key, value in (('t1MaterialCost', 2.5), ('conversionFactor', .73),
                           ('t1Markup', .41)):
            changed = {**cfg, key: value}
            expected = np.array([M.input_reference_cost(m, changed) for m in range(M.NI)])
            np.testing.assert_array_equal(NB.input_reference_arrays(changed), expected)
            self.assertFalse(np.array_equal(expected, original), key)
        np.testing.assert_array_equal(NB.input_reference_arrays(cfg), original)

    def test_reference_price_and_binding_limits(self):
        for limit in ('curve', 'cash', 'stock', 'slot', 'fractional-slot', 'over-slot'):
            with self.subTest(limit=limit):
                cfg, w = reset_world({'t2FirmCount': 1, 'distributorCount': 1})
                slots, _, inputs = K.tier2_storage_layout(w, cfg, 0)
                material = min(inputs)
                raw = w.t2Raw if material < M.NE else w.t2T1Raw
                raw[:] = 0
                w.t2Fin[:] = 0
                book = InputMarket(w, 1)
                supplier = book.offers[material][0]
                quote = M.input_reference_cost(material, cfg)
                book.price[supplier] = quote
                book.fin[supplier] = 100000
                w.t2Cash[0] = 1000000
                w.t2Preferred[:] = -1
                expected = int(slots[material] / 2)
                if limit == 'cash':
                    w.t2Cash[0] = quote * 2.5
                    expected = 2
                elif limit == 'stock':
                    book.fin[supplier] = 3.5
                    expected = 3
                elif limit == 'slot':
                    raw[material] = slots[material] - 2.25
                    expected = 2
                elif limit == 'fractional-slot':
                    raw[material] = slots[material] - .75
                    expected = 0
                elif limit == 'over-slot':
                    raw[material] = slots[material] + 1
                    expected = 0
                cash = w.t2Cash[0]
                held = raw[material]
                quantity = K.transfer_tier2_input(w, cfg, 0, material, supplier,
                                                slots[material], [supplier], book)
                self.assertEqual(quantity, expected)
                self.assertEqual(raw[material], held + expected)
                self.assertEqual(w.t2Cash[0], cash - expected * quote)
                self.assertEqual(book.revenue[supplier], expected * quote)

    @unittest.skipUnless(NB._HAVE_NUMBA, 'Numba not installed')
    def test_price_sensitive_phase_matches_reference(self):
        for price in (.1, 1., 3.):
            cfg, w = reset_world({'t2FirmCount': 200, 'distributorCount': 30,
                                 'conversionFactor': .37, 't1MaterialCost': 1.4,
                                 't1Markup': .31})
            for i, product in enumerate(M.T2_PRODUCTS):
                w.t2LineProduct[i] = i
                w.t2Sector[i] = product['sectorIndex']
            w.t1Fin[:] = w.t1Operates * 100000.
            w.t1FinBasis[:] = 1.
            w.t1Price[:] = price
            # Fractional opening holdings and restricted cash exercise funded
            # demand and rounding, with every active recipe represented.
            w.t2Raw[:] = .25
            w.t2T1Raw[:] = .25
            w.t2Cash[:200:3] = 2.5
            reference = copy.deepcopy(w)
            K.operate_tier2(reference, cfg, M.PRODUCTS, K.T0P, M.T2_PRODUCTS, 1)
            NB.operate_tier2(w, cfg, 1)
            for name in w.array_names:
                self.assertEqual(getattr(w, name).tobytes(),
                                 getattr(reference, name).tobytes(), (price, name))
            # The reference adds per-line conversion costs; the compiled path
            # returns a phase subtotal. Arrays agree byte-for-byte, while this
            # scalar reduction retains the kernel's existing 1e-9 tolerance.
            self.assertAlmostEqual(w.costSinks, reference.costSinks, delta=1e-9)

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
