"""Complexity throughput must agree in procurement, production and reporting."""
import copy
import unittest
import numpy as np
from economy.core import model as M
from economy.core.config import normalize_config
from economy.core.state import reset_world, T0P
from economy.kernel import tick as K, numba as NB

class RefineryCapacityTests(unittest.TestCase):
    def test_legacy_config_and_independent_cache_keys(self):
        cfg=normalize_config({'t1Capacity':1234})
        self.assertEqual(cfg['t1CapacityC2'],1234)
        a=NB.t1_capacity_array(cfg)
        cfg['t1CapacityC2']=987
        b=NB.t1_capacity_array(cfg)
        self.assertEqual(a[4],1234)
        self.assertEqual(b[4],987)
        self.assertEqual(b[0],1234)

    def test_all_materials_produce_their_class_capacity(self):
        cfg,w=reset_world({'distributorCount':1,'t2FirmCount':1,'storage':40000})
        w.raw.fill(20000)
        w.rawBasis.fill(1)
        w.t1Cash.fill(1000000)
        w.t1Fin.fill(0)
        w.t1Price.fill(100)
        expected=copy.deepcopy(w)
        K.operate_tier1(expected,cfg,M.PRODUCTS)
        made=expected.t1Fin.reshape(M.N1,M.NP).sum(axis=0)
        np.testing.assert_array_equal(made,np.array(M.T1_PRODUCT_FIRM_COUNTS)*6000)
        if NB._HAVE_NUMBA:
            NB.operate_tier1(w,cfg)
            for name in w.array_names:
                np.testing.assert_array_equal(getattr(w,name),getattr(expected,name),err_msg=name)

    @unittest.skipUnless(NB._HAVE_NUMBA,'Numba not installed')
    def test_procurement_uses_same_class_limits(self):
        cfg,w=reset_world({'distributorCount':1,'t2FirmCount':1})
        w.raw.fill(0)
        w.t1Fin.fill(0)
        w.t0Inv.fill(1e7)
        w.t1Price.fill(100)
        expected=copy.deepcopy(w)
        K.plan_and_buy_inputs(expected,cfg,M.PRODUCTS,T0P,1)
        NB.plan_and_buy_inputs(w,cfg,1)
        for name in w.array_names:
            np.testing.assert_array_equal(getattr(w,name),getattr(expected,name),err_msg=name)
