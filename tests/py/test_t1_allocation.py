"""Demand-balanced cohorts must cover the fleet and survive projections."""
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
        self.assertEqual(counts[:4].sum(),392);self.assertEqual(counts[4:].sum(),590)
        ideal=982*demand/demand.sum()
        self.assertTrue(np.all(np.abs(counts-ideal)<1))
        np.testing.assert_array_equal(np.bincount(M.T1_FIRM_PRODUCT),counts)
        for i,n in enumerate(counts):
            start=M.T1_FIRM_OFFSETS[i]
            self.assertEqual(M.T1_FIRM_PRODUCT[start:start+n],[i]*n)

    def test_fleet_size_minimizes_spread_near_one_thousand(self):
        demand=np.array(list(M.T1_NOMINAL_DEMAND.values()),dtype=float)
        scores=[]
        for total in range(950,1051):
            ideal=total*demand/demand.sum()
            counts=np.floor(ideal).astype(int)
            # Independent largest remainder, stable product order for ties.
            rank=sorted(range(M.NP),key=lambda i:(-(ideal[i]-counts[i]),i))
            for i in rank[:total-counts.sum()]:counts[i]+=1
            per_company=demand/counts
            scores.append(((per_company.max()-per_company.min())/(demand.sum()/total),total))
        self.assertEqual(min(scores)[1],M.N1)

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
