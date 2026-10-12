"""Retail sees opening inventory; downstream manufacturers see fresh output."""
import copy
import unittest
from unittest.mock import patch
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, validate_storage
from economy.core.accounting import company_earnings
from economy.kernel import tick as K, numba as NB


class ProductionStockAccess(unittest.TestCase):
    def setup_market(self, opening_stock=0):
        cfg, w = reset_world({'t2FirmCount': 2, 'distributorCount': 1,
                             'distributorActivation': 1, 'distributorSearchOffers': 20,
                             'storageRentPerThousandPerTick': 0})
        buyer = next(p for p in M.T2_PRODUCTS if p['demandGroup'] == 'c4_basic_c3')
        market = next(m for m, q in buyer['ingredients'] if m >= M.NP)
        seller = M.T2_INPUT_PRODUCTS[market]
        for firm, product in enumerate((seller, buyer)):
            w.t2LineProduct[firm] = product['id']
            w.t2Price[firm] = 100 if firm == 0 else 200
            for material, quantity in product['ingredients']:
                if material >= M.NP:
                    continue
                raw, basis = (w.t2Raw, w.t2RawBasis) if material < M.NE else (w.t2T1Raw, w.t2T1Basis)
                index = firm * (M.NE if material < M.NE else M.NI) + material
                raw[index] = 100
                basis[index] = 2
        w.t2Fin[:2] = [opening_stock, 0]
        w.t2FinBasis[0] = 5
        w.distributorProduct[0] = M.NP + seller['id']
        w.distributorChoke[0] = 10000
        return cfg, w, seller

    def test_fresh_output_reaches_manufacturers_not_retail_in_both_engines(self):
        for opening in (0, 10):
            cfg, initial, seller = self.setup_market(opening)
            results = []
            for fast in (False, True):
                if fast and not NB._HAVE_NUMBA:
                    continue
                w = copy.deepcopy(initial)
                before = K.storage_rent_equity(w, cfg, 't2').copy()
                with patch.object(NB, '_HAVE_NUMBA', fast):
                    K.tick(w, cfg, 1)
                self.assertEqual(w.marketFulfilled[M.NP + seller['id']], opening)
                self.assertEqual(w.t2Made[0], 32)
                self.assertGreater(w.t2IntermediateSold[seller['id']], 0)
                # Price-sensitive buying scales the buyer's order around the
                # intermediate's reference cost, so it produces 6, not the full 24.
                self.assertEqual(w.t2Made[1], 6)
                self.assertGreater(w.t2RelAttempts[0], 0)
                self.assertEqual(w.t2RelAvailable[0], 0)
                validate_storage(w, cfg)
                np.testing.assert_allclose(K.storage_rent_equity(w, cfg, 't2') - before,
                                           company_earnings(w, cfg, 't2'), atol=1e-8, rtol=0)
                results.append(w)
            if len(results) == 2:
                for name in results[0].array_names:
                    np.testing.assert_allclose(getattr(results[0], name), getattr(results[1], name),
                                               atol=1e-9, rtol=0, err_msg=name)

    def test_downstream_access_does_not_depend_on_company_rotation(self):
        for tick in (1, 2):  # With two firms these reverse the processing order.
            for fast in (False, True):
                if fast and not NB._HAVE_NUMBA:
                    continue
                cfg, w, seller = self.setup_market()
                if fast:
                    NB.operate_tier2(w, cfg, tick)
                else:
                    K.operate_tier2(w, cfg, M.PRODUCTS, K.T0P, M.T2_PRODUCTS, tick)
                self.assertEqual(w.t2Made[:2].tolist(), [32, 6])
                self.assertEqual(w.t2MonthlyCapacity[:2].tolist(), [32, 24])
                self.assertEqual(w.t2RelPriceSamples[:2].tolist(), [1, 1])
