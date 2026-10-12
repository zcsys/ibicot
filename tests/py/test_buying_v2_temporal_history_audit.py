import unittest
import numpy as np
from tools.buying_v2.seller_history import SellerHistory
from tools.buying_v2.temporal_history_audit import audit


class TemporalHistoryAuditTests(unittest.TestCase):
    def fixture(self):
        h=SellerHistory(4)
        for tick in (1,2):
            offered=np.ones(8);offered[0]=tick==2
            sold=np.array([0,0,0,0,0 if tick==1 else 1,1 if tick==1 else 0,1,0],float)
            closing=np.full(8,2.);closing[1]=0
            quote=np.ones(8);quote[3]=float(tick)
            exposure=np.ones((3,8));exposure[2]=0;exposure[:,0]=0;exposure[:,7]=0
            if tick==1:exposure[2,2]=1
            h.record('retail',tick,np.array([0]*4+[1]*4),np.arange(8),offered,sold+closing,closing,quote,sold,exposure)
        return h

    def test_exclusions_and_product_denominators_reconcile(self):
        result=audit(self.fixture(),decision_tick=3)['channels'][0]
        total=result['totals']
        self.assertEqual(total['candidatePairs'],8)
        self.assertEqual(total['exclusions'],dict(nonconsecutive=0,unoffered=1,emptyOpening=1,recordedStockConstraint=1,changedQuote=1))
        self.assertEqual(total['comparablePairs'],4)
        self.assertEqual(total['transitionCounts'],[[1,1],[1,1]])
        self.assertEqual(total['conditionalPositiveSaleProbability'],[.5,.5])
        self.assertEqual(total['pooledBinaryCorrelation'],0.)
        self.assertEqual(total['sellersWithBothOriginStates'],0)
        self.assertEqual(total['sameOpeningStockPairs'],2)
        self.assertEqual(result['products'][0]['conditionalPositiveSaleProbability'],[None,None])
        self.assertEqual(sum(p['candidatePairs'] for p in result['products']),total['candidatePairs'])

    def test_future_observations_and_new_columns_do_not_change_result(self):
        h=self.fixture();expected=audit(h,decision_tick=3)
        h.record('retail',3,np.array([0]*4+[1]*4+[2]),np.arange(9),np.ones(9),np.ones(9),np.ones(9),np.full(9,100.),np.zeros(9),np.zeros((3,9)))
        h.record('future-channel',3,np.array([0]),np.array([0]),np.ones(1),np.ones(1),np.ones(1),np.ones(1),np.zeros(1),np.zeros((3,1)))
        self.assertEqual(expected,audit(h,decision_tick=3))

    def test_no_history_single_row_and_invalid_metadata(self):
        h=self.fixture()
        self.assertEqual(audit(h,decision_tick=1)['channels'],[])
        for tick in (2,):
            result=audit(h,decision_tick=tick)['channels'][0]['totals']
            self.assertEqual(result['candidatePairs'],0)
            self.assertEqual(result['conditionalPositiveSaleProbability'],[None,None])
        for tick in (0,-1,True,1.5):
            with self.assertRaises(ValueError):audit(h,decision_tick=tick)
        h.channels['retail']['ticks'][1]=4
        with self.assertRaises(ValueError):audit(h,decision_tick=5)


if __name__=='__main__':unittest.main()
