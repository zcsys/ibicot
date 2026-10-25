"""Product-specific Distributor loyalty, including checkpoint continuity."""
import tempfile
import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import tick as reference, numba as accelerated
from economy.server.persistence import save_checkpoint, load_checkpoint


class DistributorPreferences(unittest.TestCase):
    def test_route_changes_restore_independent_incumbents(self):
        for fast in (False, True):
            cfg, w = reset_world({'t2FirmCount': 12, 'distributorCount': 2,
                                  'distributorActivation': 0})
            w.distributorProduct[:2] = [M.NP, M.NP]
            w.distributorPreferredSupplier[:2] = [3, 4]
            def clear(tick):
                if fast:
                    accelerated.clear_distributors(w, cfg, tick)
                else:
                    reference.clear_distributors(w, cfg, M.PRODUCTS, M.T2_PRODUCTS, tick)
            clear(1)
            w.distributorProduct[0] = M.NP + 1
            clear(2)
            self.assertEqual(w.distributorPreferredSupplier[:2].tolist(), [-1, 4])
            w.distributorPreferredSupplier[0] = 7
            w.distributorProduct[0] = M.NP
            clear(3)
            self.assertEqual(w.distributorPreferredSupplier[:2].tolist(), [3, 4])
            w.distributorProduct[0] = M.NP + 1
            clear(4)
            self.assertEqual(w.distributorPreferredSupplier[:2].tolist(), [7, 4])
            self.assertEqual(w.loyaltyPenalties[2], 0)

    def test_new_product_cannot_buy_old_incumbents_stock(self):
        for fast in (False, True):
            cfg, w = reset_world({'t2FirmCount': 2, 'distributorCount': 1,
                                  'distributorActivation': 1,
                                  'distributorSearchOffers': 20})
            w.t2LineProduct[:2] = [0, 1]
            w.t2Price[:2] = [0.01, 1.0]
            w.t2Fin[:2] = 100
            w.distributorChoke[0] = 100
            w.distributorProduct[0] = M.NP
            w.distributorPreferredSupplier[0] = 0
            w.sync_distributor_preferences()
            w.distributorProduct[0] = M.NP + 1
            if fast:
                accelerated.clear_distributors(w, cfg, 1)
            else:
                reference.clear_distributors(w, cfg, M.PRODUCTS, M.T2_PRODUCTS, 1)
            self.assertEqual(w.t2Fin[0], 100)
            self.assertLess(w.t2Fin[1], 100)
            self.assertEqual(w.distributorLastSupplier[0], 1)
            self.assertEqual(w.distributorPreferredSupplier[0], 1)
            self.assertEqual(w.loyaltyPenalties[2], 0)

    def test_checkpoint_preserves_history_and_pending_route_change(self):
        cfg, w = reset_world({'t2FirmCount': 12, 'distributorCount': 1})
        w.distributorProduct[0] = M.NP
        w.distributorPreferredSupplier[0] = 3
        w.sync_distributor_preferences()
        w.distributorProduct[0] = M.NP + 1
        w.sync_distributor_preferences()
        w.distributorPreferredSupplier[0] = 7
        w.distributorProduct[0] = M.NP
        with tempfile.TemporaryDirectory() as d:
            save_checkpoint(d + '/world', cfg, 2, w)
            _, _, restored, _ = load_checkpoint(d + '/world')
        for name in w.array_names:
            np.testing.assert_array_equal(getattr(w, name), getattr(restored, name))
        self.assertEqual(restored.distributorSupplierHistory, w.distributorSupplierHistory)
        restored.sync_distributor_preferences()
        self.assertEqual(restored.distributorPreferredSupplier[0], 3)
        self.assertEqual(restored.distributorSupplierHistory[(0, M.NP + 1)], 7)
