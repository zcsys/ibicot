"""One-output recipes, weighted space and recipe-derived references."""
import copy
import unittest
from collections import Counter
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, validate_storage, add_tier2_line
from economy.kernel import tick as K
from economy.kernel import numba as NB

class MidbridgeTests(unittest.TestCase):
    def test_population_and_recipe_costs(self):
        cfg,w=reset_world({'distributorCount':1})
        self.assertEqual(cfg['distributorActivation'], .105)
        self.assertEqual(M.N1,1008)
        self.assertEqual(sum(M.refinery_capacity(p,cfg)*72 for p in M.PRODUCTS),6048000)
        self.assertEqual(cfg['t1Capacity'],6000)
        self.assertEqual(cfg['t1CapacityC2'],6000)
        self.assertEqual(sum(M.T2_PRODUCT_FIRM_COUNTS[p['id']]*cfg['t2Capacity'][p['complexity']] for p in M.T2_PRODUCTS),1695744)
        self.assertEqual(M.T1_FIRMS_PER_MATERIAL,72)
        operates=w.t1Operates.reshape(M.N1,M.NP)
        np.testing.assert_array_equal(operates.sum(axis=0),np.full(M.NP,72))
        np.testing.assert_array_equal(operates.sum(axis=1),np.ones(M.N1))
        for material in range(M.NP):
            self.assertTrue(np.all(operates[material*72:(material+1)*72,material]))
        self.assertEqual(w.t2LineCount,57960)
        self.assertEqual(M.N2_FIRMS,sum(M.T2_PRODUCT_FIRM_COUNTS.values()))
        self.assertEqual(sum(M.T2_PRODUCT_FIRM_COUNTS.values()),57960)
        self.assertEqual(M.T2_COMPLEXITY_FIRM_COUNTS,{3:38088,4:19872})
        self.assertEqual(Counter(M.T2_PRODUCT_FIRM_COUNTS[p['id']] for p in M.T2_PRODUCTS if p['complexity']==3),{1058:36})
        self.assertEqual(Counter(M.T2_PRODUCT_FIRM_COUNTS[p['id']] for p in M.T2_PRODUCTS if p['complexity']==4),{288:69})
        total_weight=sum(M.T2_COMPANY_WEIGHTS.values())
        for p in M.T2_PRODUCTS:
            ideal=57960*M.T2_COMPANY_WEIGHTS[p['catalogId']]/total_weight
            self.assertLess(abs(M.T2_PRODUCT_FIRM_COUNTS[p['id']]-ideal),1)
        self.assertEqual(cfg['t2Capacity'][3],M.T2_ALLOCATION_CAPACITIES[3])
        self.assertEqual(cfg['t2Capacity'][4],M.T2_ALLOCATION_CAPACITIES[4])
        counts=Counter(w.t2LineProduct[:w.t2LineCount])
        for p in M.T2_PRODUCTS:
            self.assertEqual(counts[p['id']],M.T2_PRODUCT_FIRM_COUNTS[p['id']])
            self.assertEqual(p['outputQty'],1)
            expected=sum(q*(M.refinery_unit_cost(M.T2_INPUT_PRODUCTS[m],cfg) if m<M.NP else M.initial_tier2_cost(M.T2_INPUT_PRODUCTS[m],cfg))*1.25 for m,q in p['ingredients'])+M.conversion_cost(p['complexity'],cfg)
            self.assertAlmostEqual(w.t2ReferenceCost[p['id']],expected)
        self.assertEqual(M.refinery_unit_cost(M.PRODUCTS[4],cfg),2.75)
        self.assertGreater(np.ptp([M.reference_tier2_cost(p,cfg) for p in M.T2_PRODUCTS if p['complexity']==4]),0)
        for sector,first in enumerate(M.T2_SECTOR_FIRM_OFFSETS):
            self.assertEqual(int(w.t2Sector[first]),sector)
            self.assertTrue(M.t2_firm_name(sector,first).endswith(' '+M.company_number('T2',first)))

    def test_example_and_repeated_ingredients(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1})
        for ingredients in ({'W':1,'W+E':1},{'W+E':2}):
            p=next(p for p in M.T2_PRODUCTS if p['inputs']==ingredients)
            w.t2LineProduct[0]=p['id']
            targets,output_space,used=K.tier2_storage_layout(w,cfg,0)
            half=(cfg['storage']-cfg['footprint'][p['complexity']])/2
            self.assertEqual(output_space,half)
            self.assertAlmostEqual(sum(targets[m]*M.T2_INPUT_PRODUCTS[m]['complexity'] for m in used),half)
            for m,q in p['ingredients']:
                self.assertAlmostEqual(targets[m]/q,half/p['complexity'])
        p=next(p for p in M.T2_PRODUCTS if p['inputs']=={'W':1,'W+E':1})
        w.t2LineProduct[0]=p['id']
        targets,space,_=K.tier2_storage_layout(w,cfg,0)
        self.assertEqual(int(space//3),2833)
        self.assertEqual(int(targets[0]),2833)
        self.assertEqual(int(targets[next(i for i,p in enumerate(M.PRODUCTS) if p['code']=='W+E')]),2833)
        w.t2T1Raw[next(i for i,p in enumerate(M.PRODUCTS) if p['code']=='W+E')]=10000 # 20k space plus machinery must fail validation.
        with self.assertRaises(ValueError):validate_storage(w,cfg)

    def test_production_conserves_space_and_value_both_engines(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1,'storageRentPerThousandPerTick':0})
        p=next(p for p in M.T2_PRODUCTS if p['inputs']=={'W':1,'W+E':1})
        w.t2LineProduct[0]=p['id'];w.t2Sector[0]=p['sectorIndex']
        w.t2Raw[0]=100;w.t2RawBasis[0]=2
        w.t2T1Raw[next(i for i,p in enumerate(M.PRODUCTS) if p['code']=='W+E')]=100;w.t2T1Basis[next(i for i,p in enumerate(M.PRODUCTS) if p['code']=='W+E')]=4
        w.t2Price[0]=100
        before=K.tier2_inventory_units(w,0)
        expected=copy.deepcopy(w)
        K.operate_tier2(expected,cfg,M.PRODUCTS,K.T0P,M.T2_PRODUCTS,1)
        self.assertEqual(expected.t2Made[0],32)
        self.assertEqual(expected.t2FinBasis[0],6.5)
        self.assertEqual(K.tier2_inventory_units(expected,0),before)
        self.assertEqual(expected.t2Raw[0],68)
        self.assertEqual(expected.t2T1Raw[next(i for i,p in enumerate(M.PRODUCTS) if p['code']=='W+E')],68)
        if NB._HAVE_NUMBA:
            NB.operate_tier2(w,cfg,1)
            for name in w.array_names:
                np.testing.assert_array_equal(getattr(w,name),getattr(expected,name),err_msg=name)

    def test_multiline_shared_input_space_budget(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1,'storage':50000})
        p=next(p for p in M.T2_PRODUCTS if p['sectorIndex']==0 and p['complexity']==4 and p['id']!=w.t2LineProduct[0])
        add_tier2_line(w,cfg,0,p,paid=False)
        targets,output,_=K.tier2_storage_layout(w,cfg,0)
        self.assertAlmostEqual(sum(targets[m]*M.T2_INPUT_PRODUCTS[m]['complexity'] for m in range(M.NI)),output*2)
