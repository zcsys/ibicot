import unittest
import numpy as np
from tools.buying_v2.industrial_observations import record,empty_totals,FIELDS


class IndustrialObservationTests(unittest.TestCase):
    def evaluate(self,stocks=(2,20,20),demands=(10,8,5),allocation=(2,6,0),requests=(10,6,0),old=2,new=2,fee=2.,lot=1):
        rows=[]
        for fn in (record,record.py_func):
            totals=empty_totals()
            args=(0,np.array([0]),np.array([10]),lot,np.array([0,0,0]),np.array([0,1,2]),np.array([10.,15.,30.]),
                  np.array(stocks),np.array(demands),np.array([old]),np.array([demands[2] if old==2 else 0]),
                  np.array(allocation),np.array(requests),np.array([new]),np.array([fee]))
            before=[x.copy() if isinstance(x,np.ndarray) else x for x in args]
            fn(totals,*args)
            for a,b in zip(args,before):
                np.testing.assert_array_equal(a,b)
            rows.append(totals)
        np.testing.assert_array_equal(*rows)
        return dict(zip(FIELDS,rows[0][0]))

    def test_split_counts_are_distinct_and_not_unique_demand(self):
        row=self.evaluate()
        self.assertEqual(row['decisions'],1)
        self.assertEqual(row['offersObserved'],3)
        self.assertEqual(row['fundedOfferChecks'],3)
        self.assertEqual(row['sufficientStockChecks'],2)
        self.assertEqual(row['referenceFundedQuantity'],5)
        self.assertEqual(row['purchasedQuantity'],8)
        self.assertEqual(row['quotedRemainingQuantity'],16)
        self.assertEqual(row['positiveLegs'],2)
        self.assertEqual(row['goodsSpend'],110)
        self.assertEqual(row['feesPaid'],1)
        self.assertEqual(row['preferenceChanges'],0)
        self.assertEqual(row['stockLimitedLegs'],1)

    def test_empty_discovery_does_not_invent_orders(self):
        row=self.evaluate(stocks=(0,0,0),allocation=(0,0,0),requests=(0,0,0),fee=0)
        self.assertEqual(row['belowLotStockChecks'],3)
        self.assertEqual(row['positiveLegs'],0)
        self.assertEqual(row['quotedRemainingQuantity'],0)
        self.assertEqual(row['referenceShortfall'],5)
        self.assertEqual(row['noPurchaseDecisions'],1)
        self.assertEqual(row['incumbentAvailableChecks'],0)

    def test_zero_funding_does_not_penalize_availability(self):
        row=self.evaluate(stocks=(0,0,0),demands=(0,0,0),allocation=(0,0,0),requests=(0,0,0),fee=0)
        self.assertEqual(row['fundedOfferChecks'],0)
        self.assertEqual(row['belowLotStockChecks'],0)
        self.assertEqual(row['incumbentAvailabilityChecks'],0)
        self.assertEqual(row['noFundedOfferDecisions'],1)

    def test_lots_and_fee_waiver_are_separate(self):
        row=self.evaluate(stocks=(2,20,4),demands=(10,10,10),allocation=(0,10,0),requests=(0,10,0),new=1,fee=0,lot=10)
        self.assertEqual(row['belowLotStockChecks'],2)
        self.assertEqual(row['feeWaivedUnavailableOrders'],1)
        self.assertEqual(row['preferenceChanges'],1)
        self.assertEqual(row['feesPaid'],0)

    def test_available_stock_without_purchase_is_not_stock_loss(self):
        row=self.evaluate(stocks=(100,100,100),allocation=(0,0,0),requests=(0,0,0),fee=0)
        self.assertEqual(row['sufficientStockChecks'],3)
        self.assertEqual(row['stockLimitedLegs'],0)
        self.assertEqual(row['referenceShortfall'],5)
        self.assertEqual(row['noPurchaseDecisions'],1)
        self.assertEqual(row['quotedRemainingQuantity'],0)

    def test_no_supplier_is_not_zero_demand(self):
        totals=empty_totals()
        ints=np.array([],dtype=np.int64);floats=np.array([],dtype=float)
        record(totals,0,np.array([0]),np.array([10]),1,ints,ints,floats,ints,ints,np.array([-1]),np.array([0]),ints,ints,np.array([-1]),np.array([0.]))
        row=dict(zip(FIELDS,totals[0]))
        self.assertEqual(row['noOfferDecisions'],1)
        self.assertEqual(row['storageTargetQuantity'],10)
        self.assertEqual(row['referenceFundedQuantity'],0)

    def test_projection_denominators_and_uninstrumented_rows(self):
        from tools.buying_v2.purchase_reporting import project
        from tools.buying_v2.industrial_observations import schema
        totals=empty_totals()
        result=project(totals,schema(),('t1',),1,30)
        self.assertIsNone(result['rows'][0]['observedStockAvailability'])
        self.assertTrue(result['rows'][0]['measured'])
        self.assertFalse(result['rows'][-1]['measured'])
        self.assertIsNone(result['rows'][-1]['purchasedQuantity'])
        index={name:i for i,name in enumerate(FIELDS)}
        for name,value in dict(decisions=10,noPurchaseDecisions=2,positiveLegs=12,
                               fundedOfferChecks=20,sufficientStockChecks=5,feesPaid=4,
                               referenceFundedQuantity=40,referenceShortfall=10).items():
            totals[0,index[name]]=value
        row=project(totals,schema(),('t1',),1,30)['rows'][0]
        self.assertEqual(row['observedStockAvailability'],.25)
        self.assertEqual(row['meanSuppliersPerPurchase'],1.5)
        self.assertEqual(row['feeIncidence'],.5)
        self.assertEqual(row['purchaseDecisionRate'],.8)
        self.assertEqual(row['referenceShortfallRate'],.25)

    def test_instrumentation_leaves_world_unchanged(self):
        from economy.server.runtime import KernelRuntime
        from tools.buying_v2.engine import IndustrialCompiledEngine
        runtimes=[KernelRuntime(dict(t2FirmCount=4200,distributorCount=1000,seed=137)) for _ in range(2)]
        engines=[IndustrialCompiledEngine(runtimes[0]),IndustrialCompiledEngine(runtimes[1],industrial_observations=False)]
        for tick in range(1,5):
            for engine in engines:
                engine.step(tick)
            for name in runtimes[0].world.array_names:
                np.testing.assert_array_equal(getattr(runtimes[0].world,name),getattr(runtimes[1].world,name),err_msg=name)
            self.assertEqual(runtimes[0].state,runtimes[1].state)
        w=runtimes[0].world;obs=engines[0].industrial_observations;idx={name:i for i,name in enumerate(FIELDS)}
        from economy.core import model as M
        self.assertEqual(obs[:M.NE,idx['purchasedQuantity']].sum(),w.t1Bought.sum())
        self.assertEqual(obs[M.NE:,idx['purchasedQuantity']].sum(),w.t2Bought.sum())
        self.assertAlmostEqual(obs[:M.NE,idx['feeAmount']].sum(),w.t1SwitchingExpense.sum())
        self.assertAlmostEqual(obs[M.NE:,idx['feeAmount']].sum(),w.t2SwitchingExpense.sum())


if __name__=='__main__':
    unittest.main()
