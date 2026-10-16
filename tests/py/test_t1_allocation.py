"""Equal-product cohorts must cover the fleet and survive projections."""
import copy,json,subprocess,tempfile,unittest
from pathlib import Path
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, T0P
from economy.kernel import tick as K,numba as NB
from economy.server.runtime import KernelRuntime
from economy.server.persistence import save_checkpoint,load_checkpoint

class T1AllocationTests(unittest.TestCase):
    def test_independent_recipe_demand_and_integer_apportionment(self):
        demand=np.zeros(M.NP,dtype=np.int64)
        for p in M.T2_PRODUCTS:
            for m,q in p['ingredients']:
                if m<M.NP:demand[m]+=M.T2_PRODUCT_FIRM_COUNTS[p['id']]*M.T2_ALLOCATION_CAPACITIES[p['complexity']]*q
        self.assertEqual(demand[:4].sum(),1315584)
        self.assertEqual(demand[4:].sum(),1979136)
        counts=np.array(M.T1_PRODUCT_FIRM_COUNTS)
        self.assertEqual(counts[:4].sum(),500);self.assertEqual(counts[4:].sum(),500)
        np.testing.assert_array_equal(counts, [125]*4+[50]*10)
        np.testing.assert_array_equal(np.bincount(M.T1_FIRM_PRODUCT),counts)
        for i,n in enumerate(counts):
            start=M.T1_FIRM_OFFSETS[i]
            self.assertEqual(M.T1_FIRM_PRODUCT[start:start+n],[i]*n)

    def test_reference_income_and_capacity(self):
        from economy.core.config import default_cfg
        cfg=default_cfg()
        counts=np.array(M.T1_PRODUCT_FIRM_COUNTS)
        demand=np.array(list(M.T1_NOMINAL_DEMAND.values()),dtype=float)
        costs=np.array([M.refinery_unit_cost(p,cfg) for p in M.PRODUCTS])
        prices=np.array([M.round_to_cent(M.reference_refinery_cost(p,cfg)*(1+cfg['t1Markup'])) for p in M.PRODUCTS])
        np.testing.assert_allclose(costs,[1.5]*4+[2.75]*10)
        np.testing.assert_allclose(prices,[2.32]*4+[3.88]*10)
        overhead=50000/1000*2.8+2000
        earnings=demand*(prices-costs)/counts-overhead
        self.assertTrue(np.all(demand/counts <= 6000))
        # Equal populations can leave individual products below break-even at seed prices.
        self.assertTrue(np.all(np.isfinite(earnings)))
        c1=np.sum(demand[:4]*(prices[:4]-costs[:4]))/counts[:4].sum()-overhead
        c2=np.sum(demand[4:]*(prices[4:]-costs[4:]))/counts[4:].sum()-overhead
        # Equal complexity populations do not imply equal seed-price earnings.
        self.assertGreater(c2,c1)
        # Live/seed-specific changes never reallocate the structural population.
        _,w=reset_world({'seed':999,'t1MaterialCost':99,'distributorCount':1,'t2FirmCount':1})
        np.testing.assert_array_equal(w.t1Operates.reshape(M.N1,M.NP).sum(axis=0),counts)

    @unittest.skipUnless(NB._HAVE_NUMBA,'Numba missing')
    def test_unequal_cohorts_execute_once_and_match_reference(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1})
        w.t0Inv[:]=1e8;w.t0Price[:]=1.;w.t1Cash[:]=1e8
        for t in (1,37,102):
            a=copy.deepcopy(w);b=copy.deepcopy(w)
            K.plan_and_buy_inputs(a,cfg,M.PRODUCTS,T0P,t);NB.plan_and_buy_inputs(b,cfg,t)
            self.assertTrue(np.all(a.t1Bought>0))
            for name in a.array_names:np.testing.assert_array_equal(getattr(a,name),getattr(b,name),err_msg=name)

    def test_browser_and_dashboard_cohort_boundaries(self):
        data=json.loads(subprocess.check_output(['node','-e',"require('./web/midbridge-catalog.js');const m=globalThis.Phase0Model;console.log(JSON.stringify([m.T1_PRODUCT_FIRM_COUNTS,m.T1_FIRM_OFFSETS,m.T1_FIRM_PRODUCT]));"],text=True))
        self.assertEqual(data,[M.T1_PRODUCT_FIRM_COUNTS,M.T1_FIRM_OFFSETS,M.T1_FIRM_PRODUCT])
        rt=KernelRuntime({'t2FirmCount':1,'distributorCount':1})
        for i,n in enumerate(M.T1_PRODUCT_FIRM_COUNTS):
            for firm in [M.T1_FIRM_OFFSETS[i],M.T1_FIRM_OFFSETS[i]+n-1]:
                self.assertIn(M.T1_GENERIC_BASES[M.PRODUCTS[i]['code']],M.t1_firm_name(firm))
        rt.publish()

    def test_old_cohort_checkpoint_is_rejected(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1})
        with tempfile.TemporaryDirectory() as tmp:
            stem=str(Path(tmp)/'state');save_checkpoint(stem,cfg,0,w)
            p=Path(stem+'.json');meta=json.loads(p.read_text());meta['catalogRevision']='midbridge-invented-105-reverse-v7';p.write_text(json.dumps(meta))
            with self.assertRaises(ValueError):load_checkpoint(stem)
