import unittest
from dataclasses import replace
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import tick as K
from tools.buying_v2.industry_oracle import Problem, Offer
from tools.buying_v2.refinery import settle, buy_reference, company_problem


class RefineryTests(unittest.TestCase):
    def fixture(self):
        cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=1,seed=137,minWholesaleLot=10))
        firm=0
        m=next(iter(K.tier1_storage_layout(w,cfg,firm)[2]))
        ids=[s for s in range(M.N0) if M.ELEMENTS[m] in K.T0P[s]['elements']][:3]
        for s,price,stock in zip(ids,(1.,2.,3.),(20,100,100)):
            w.t0Price[s*M.NE+m]=price;w.t0Inv[s*M.NE+m]=stock;w.t0InvBasis[s*M.NE+m]=.5
        w.preferredWholesale[m]=ids[2]
        w.lm1=2/(cfg['baseCost']*(1+w.t0Rel[ids[2]*M.NE+m]))
        p=Problem((int(w.raw[m]),),(float(w.rawBasis[m]),),(1.,),(100,),100.,float(w.t1Cash[firm]),
                  tuple(Offer(0,s,float(w.t0Price[s*M.NE+m]),int(w.t0Inv[s*M.NE+m]),10) for s in ids),
                  (ids[2],),(50,),(2.,),(),((0.,)*101,),funded_demands=(100,80,50))
        return cfg,w,firm,m,ids,p

    def test_split_lots_single_fee_and_preference_retention(self):
        cfg,w,firm,m,ids,p=self.fixture()
        cash=w.t1Cash[firm];seller_cash=w.t0Cash.copy()
        result=settle(w,cfg,firm,K.T0P,p,(20,60,0),(m,))
        self.assertEqual(result['goods'],140.)
        self.assertEqual(result['fees'],2.)
        self.assertEqual(w.raw[m],80)
        self.assertEqual(w.rawBasis[m],140/80)
        self.assertEqual(w.t1Cash[firm],cash-142)
        self.assertAlmostEqual(float((w.t0Cash-seller_cash).sum()),142.)
        self.assertEqual(w.preferredWholesale[m],ids[2])
        self.assertEqual(sum(w.t0COGS),40.)
        self.assertEqual(w.t0SwitchingIncome[ids[2]],2.)
        self.assertEqual(w.t0Demand[ids[0]*M.NE+m],100)
        self.assertEqual(w.t0Demand[ids[1]*M.NE+m],60)

    def test_fee_availability_and_whole_supplier_qualification(self):
        for available in (False,True):
            cfg,w,firm,m,ids,p=self.fixture()
            if not available:
                w.t0Inv[ids[2]*M.NE+m]=40
                p=replace(p,offers=(*p.offers[:2],replace(p.offers[2],stock=40)))
            result=settle(w,cfg,firm,K.T0P,p,(0,80,0),(m,))
            self.assertEqual(result['fees'],2. if available else 0.)
            self.assertEqual(w.preferredWholesale[m],ids[1])

    def test_invalid_baskets_are_atomic(self):
        for allocation in ((20,70,0),(21,50,0)):
            cfg,w,firm,m,ids,p=self.fixture()
            before={name:getattr(w,name).copy() for name in w.array_names}
            with self.assertRaises(ValueError):
                settle(w,cfg,firm,K.T0P,p,allocation,(m,))
            for name,value in before.items():
                np.testing.assert_array_equal(getattr(w,name),value,err_msg=name)

    def test_actual_adapter_shared_cash_and_distinct_inputs(self):
        cfg,w,firm,m,ids,p=self.fixture()
        # Multiple installed recipes share raw slots and one company budget.
        w.t1Operates[:M.NP]=1
        w.t1Cash[firm]=100.
        w.t0Inv[:]=10000.
        result=buy_reference(w,cfg,1,firm,K.T0P)
        self.assertGreater(len(result['materials']),1)
        self.assertLessEqual(result['postings']['goods']+result['postings']['fees'],100.)
        self.assertTrue(all(q%cfg['minWholesaleLot']==0 for q in result['allocation']))
        self.assertGreaterEqual(w.t1Cash[firm],0)
        for j in range(len(result['materials'])):
            suppliers=[o.supplier for o in result['problem'].offers if o.material==j]
            self.assertEqual(len(suppliers),len(set(suppliers)))
            self.assertLessEqual(len(suppliers),6)


if __name__=='__main__':
    unittest.main()
