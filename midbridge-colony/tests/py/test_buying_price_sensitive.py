"""Final procurement reduction: economic feasibility, eta, then legal rounding."""
import unittest
import copy
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import numba as NB
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket


class PriceSensitiveBuyingTests(unittest.TestCase):
    def test_lot_rounding_follows_reduction(self):
        from economy.core.trading import affordable_order
        # 2,500 feasible / (1 + 1.25²) = 975.61: no legal lot.
        # 2,600 feasible / 2.5625 = 1,014.63: one legal lot.
        # Rounding 2,600 to 2,000 before eta would incorrectly yield zero.
        for feasible, expected in ((2500, 0), (2600, 1000)):
            result = affordable_order(0, -1, feasible, 1e9,
                np.array([1e6]), np.array([1.25]), np.array([1.]),
                1., 0., 1000, 1., 2., .99)
            self.assertEqual(result, (0, expected, expected, 0.))

    def test_stochastic_rounding_with_hard_limits(self):
        from economy.core.trading import affordable_order
        for feasible, price, reference, expected in (
            (4., 15.84, 8.1875, 1), (2., 1., 1., 1),
            (1., 2., 1., 0), (.9, .1, 1., 0),
            (3., 1., 1., 1), (5., 1., 1., 2)):
            for binding in ('cash', 'stock', 'space'):
                result = affordable_order(0, -1, feasible if binding == 'space' else 100.,
                    feasible * price if binding == 'cash' else 1e6,
                    np.array([feasible if binding == 'stock' else 100.]),
                    np.array([price]), np.array([1.]), 1., 0., 1, reference, 2.)
                self.assertEqual(result[2], expected, (feasible, binding))

    def test_rounding_frequency_and_incumbent_draw_reuse(self):
        from economy.core.trading import affordable_order
        for lot in (1, 1000):
            quantities = [affordable_order(0, -1, 3*lot, 1e9,
                np.array([3.*lot]), np.array([1.]), np.array([1.]),
                1., 0., lot, 1., 2., (i+.5)/1000)[2] for i in range(1000)]
            self.assertEqual(set(quantities), {lot, 2*lot})
            self.assertEqual(sum(quantities)/len(quantities), 1.5*lot)
        # Both alternate seller computations reuse the same supplied draw.
        for draw, expected in ((.2, 1), (.999, 0)):
            result = affordable_order(1, 0, 100., 10000.,
                np.array([1000., 1000.]), np.array([10., 9.]), np.array([1., 1.]),
                1., 10., 1, 1., 2., draw)
            self.assertEqual(result, (0, expected, expected, 0.))

    def test_fee_rechecked_after_reduction(self):
        from economy.core.trading import affordable_order
        # Before eta: challenger saves $100 and owes $20. After eta the
        # $1-reference curve permits only 1 unit, so remain with incumbent.
        result = affordable_order(1, 0, 100., 10000.,
            np.array([1000., 1000.]), np.array([10., 9.]), np.array([1., 1.]),
            1., 10., 1, 1., 2.)
        self.assertEqual(result, (0, 1, 1, 0.))

    @unittest.skipUnless(NB._HAVE_NUMBA, 'Numba not installed')
    def test_t1_final_reduction_and_compiled_parity(self):
        cfg, w = reset_world({'t2FirmCount': 1, 'distributorCount': 1})
        w.t1Operates[:] = 0
        w.t1Operates[0] = 1
        slots, _, _ = K.tier1_storage_layout(w, cfg, 0)
        w.raw[0] = slots[0] - 2600
        w.t0Inv[:] = np.isfinite(w.t0Price) * 100000
        w.t0Price[np.isfinite(w.t0Price)] = 1.25
        w.t1Cash[:] = 1000000
        reference = copy.deepcopy(w)
        K.plan_and_buy_inputs(reference, cfg, M.PRODUCTS, K.T0P, 1)
        NB.plan_and_buy_inputs(w, cfg, 1)
        self.assertEqual(w.t1Bought[0], 1000)
        for name in w.array_names:
            np.testing.assert_array_equal(getattr(w, name), getattr(reference, name), err_msg=name)

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

    def test_input_eta_is_independent_of_distributor_eta(self):
        for eta, fraction in ((.5, 1/3), (2., 1/17)):
            cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1,'t2InputElasticity':eta})
            self.assertEqual(cfg['elasticity'],2.)
            slots,_,inputs=K.tier2_storage_layout(w,cfg,0)
            material=min(inputs);book=InputMarket(w,1);supplier=book.offers[material][0]
            book.price[supplier]=4*M.input_reference_cost(material,cfg)
            book.fin[supplier]=100000;w.t2Cash[0]=1000000
            bought=K.transfer_tier2_input(w,cfg,0,material,supplier,slots[material],[supplier],book)
            self.assertIn(bought, (int(slots[material]*fraction), int(slots[material]*fraction)+1))

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
                    expected = 1
                elif limit == 'stock':
                    book.fin[supplier] = 3.5
                    expected = 1
                elif limit == 'slot':
                    raw[material] = slots[material] - 2.25
                    expected = 1
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
                self.assertIn(quantity, (expected, expected+1) if limit in ('curve', 'cash', 'stock', 'slot') else (expected,))
                expected = quantity
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

    def test_latent_need_survives_no_stock_and_no_cash(self):
        cfg, w = reset_world({'t2FirmCount': 1, 'distributorCount': 1})
        slots, _, inputs = K.tier2_storage_layout(w, cfg, 0)
        w.t1Fin[:] = 0
        w.t2Raw[:] = 0
        w.t2T1Raw[:] = 0
        w.t2Fin[:] = 0
        w.t2Cash[:] = 0
        expected = np.zeros(M.NP)
        for material in inputs:
            if material < M.NP:
                expected[material] = int(slots[material])
        reference = copy.deepcopy(w)
        K.operate_tier2(reference, cfg, M.PRODUCTS, K.T0P, M.T2_PRODUCTS, 1)
        np.testing.assert_array_equal(reference.potential, expected)
        self.assertGreater(expected.sum(), 0)
        self.assertEqual(reference.t2Bought.sum(), 0)
        if NB._HAVE_NUMBA:
            NB.operate_tier2(w, cfg, 1)
            np.testing.assert_array_equal(w.potential, expected)
        K.reset_tick(reference)
        self.assertEqual(reference.potential.sum(), 0)
        reference.t2Operating[:] = 0
        K.operate_tier2(reference, cfg, M.PRODUCTS, K.T0P, M.T2_PRODUCTS, 2)
        self.assertEqual(reference.potential.sum(), 0)

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
