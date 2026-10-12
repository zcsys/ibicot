"""C2 storage follows native refinery cohorts in both engines and accounting."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, tier1_storage_capacities, validate_storage, T0P
from economy.kernel import tick as K, numba as NB
from economy.server.runtime import KernelRuntime

class C2StorageTests(unittest.TestCase):
    def test_defaults_and_legacy_shared_pool(self):
        cfg,w=reset_world({'distributorCount':1,'t2FirmCount':1})
        sizes=tier1_storage_capacities(cfg)
        np.testing.assert_array_equal(sizes[:288],50000)
        np.testing.assert_array_equal(sizes[288:],50000)
        self.assertEqual(cfg['storage'],20000)
        self.assertEqual(sizes.sum(),50400000)
        old,_=reset_world({'distributorCount':1,'t2FirmCount':1,'storage':30000})
        np.testing.assert_array_equal(tier1_storage_capacities(old),30000)
        slots,out,_=K.tier1_storage_layout(w,cfg,5*72)
        self.assertEqual(out,24500)
        np.testing.assert_array_equal(slots,[12250,12250,0,0])

    def test_refill_production_reaches_full_rate_in_both_engines(self):
        cfg,w=reset_world({'distributorCount':1,'t2FirmCount':1,'storageRentPerThousandPerTick':0})
        w.raw.fill(0);w.t1Fin.fill(0);w.t1Cash.fill(1e8)
        w.t0Inv.fill(1e8);w.t0Price.fill(1.25);w.t1Price.fill(100)
        expected=copy.deepcopy(w)
        K.plan_and_buy_inputs(expected,cfg,M.PRODUCTS,T0P,1)
        K.operate_tier1(expected,cfg,M.PRODUCTS)
        np.testing.assert_array_equal(expected.t1Fin.reshape(M.N1,M.NP).sum(axis=0),432000)
        validate_storage(expected,cfg)
        if NB._HAVE_NUMBA:
            NB.plan_and_buy_inputs(w,cfg,1);NB.operate_tier1(w,cfg)
            for name in w.array_names:
                np.testing.assert_array_equal(getattr(w,name),getattr(expected,name),err_msg=name)

    def test_rent_forecast_settlement_and_equity_reconcile(self):
        cfg,w=reset_world({'distributorCount':1,'t2FirmCount':1,'storageRentPerThousandPerTick':2.8})
        w.t1Cash.fill(3e6)
        before=K.storage_rent_equity(w,cfg,'t1').copy()
        forecast=K.production_line_rent(w,cfg,'t1')
        np.testing.assert_allclose(forecast[:288],140)
        np.testing.assert_allclose(forecast[288:],140)
        K.settle_storage_rent(w,cfg,1)
        np.testing.assert_allclose(w.t1RentCharge,forecast)
        np.testing.assert_allclose(before-K.storage_rent_equity(w,cfg,'t1'),forecast + w.t1IntelligenceCharge)

    def test_reporting_and_live_shrink_validation(self):
        with tempfile.TemporaryDirectory() as d, patch('economy.server.runtime._STATS_DIR',Path(d)), patch('economy.server.service._STATS_DIR',Path(d)):
            rt=KernelRuntime({'distributorCount':1,'t2FirmCount':1,'storageRentPerThousandPerTick':2.8})
            self.assertEqual(rt._storage_view('t1',0)['storageCapacitySpace'],50000)
            view=rt._storage_view('t1',288)
            self.assertEqual(view['storageCapacitySpace'],50000)
            self.assertEqual(view['machinerySpace'],1000)
            self.assertEqual(rt._storage_view('t2',0)['storageCapacitySpace'],20000)
            self.assertAlmostEqual(rt._company_rent('t1',288)['storageRentPerTick'],140)
            rt.world.raw[288*M.NE]=30000
            validate_storage(rt.world,rt.cfg)
            with self.assertRaises(ValueError):rt.apply_config({'t1C2Storage':20000})
            self.assertEqual(rt.cfg['t1C2Storage'],50000)
