import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, add_tier2_line
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket
from tools.buying_v2.prepurchase_state import capture_t2


class PrepurchaseStateTests(unittest.TestCase):
    def fixture(self):
        cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=1,seed=137))
        phase=M.T2_PRODUCTS[int(w.t2LineProduct[0])]['complexity']
        return cfg,w,phase

    def test_fractional_state_pending_settlement_and_no_mutation(self):
        cfg,w,phase=self.fixture()
        w.t2Fin[0]=9.5
        w.t2FinBasis[0]=2.25
        w.t2Raw[0]=.75
        overhead=K.production_line_overhead(w,cfg,'t2')
        overhead[0]=17.25
        book=InputMarket(w,1)
        s=book.n1
        book.fin[s]-=2.5
        book.cash[M.N1]+=10
        book.switch_income[M.N1]+=3
        before={n:getattr(w,n).copy() for n in w.array_names}
        bbefore={n:v.copy() for n,v in vars(book).items() if isinstance(v,np.ndarray)}
        result=capture_t2(w,cfg,1,0,phase,book,overhead)
        self.assertEqual(result['lines'][0]['finished'],9.5)
        self.assertEqual(result['lines'][0]['sellerBook']['current']['fin'],7)
        self.assertEqual(result['lines'][0]['sellerBook']['opening']['fin'],9.5)
        self.assertEqual(result['materials'][0]['held'],.75)
        self.assertEqual(result['pendingSellerCash'],10)
        self.assertEqual(result['pendingSwitchingIncome'],3)
        self.assertEqual(result['phaseEntryOverheadPerLine'],17.25)
        for n,v in before.items(): np.testing.assert_array_equal(getattr(w,n),v,err_msg=n)
        for n,v in bbefore.items(): np.testing.assert_array_equal(getattr(book,n),v,err_msg=n)
        result['config']['t2Capacity'][phase]=999
        self.assertNotEqual(cfg['t2Capacity'][phase],999)
        w.t2Fin[0]=0
        self.assertEqual(result['lines'][0]['finished'],9.5)

    def test_installed_order_and_inactive_phase_are_preserved(self):
        cfg,w,phase=self.fixture()
        p=M.T2_PRODUCTS[int(w.t2LineProduct[0])]
        other=next(x for x in M.T2_PRODUCTS if x['invented'] and x['sectorIndex']==p['sectorIndex'] and x['complexity']<=phase and x['id']!=p['id'])
        add_tier2_line(w,cfg,0,other,paid=False)
        book=InputMarket(w,1)
        result=capture_t2(w,cfg,1,0,phase,book,K.production_line_overhead(w,cfg,'t2'))
        ids=[int(w.t2FirmLines[i]) for i in range(2)]
        self.assertEqual(result['installedLines'],ids)
        self.assertEqual(result['productionOrder'],[i for i in ids if M.T2_PRODUCTS[int(w.t2LineProduct[i])]['complexity']==phase])
        self.assertEqual(len(result['materials']),M.NI)
        for row in result['offers']:
            self.assertLessEqual(len(row['suppliers']),6)
        self.assertTrue(result['missingPlannerInputs'])
        # Capture the other phase even if this firm has no eligible line there.
        other_phase=7-phase
        other_capture=capture_t2(w,cfg,1,0,other_phase,book,K.production_line_overhead(w,cfg,'t2'))
        self.assertEqual(other_capture['installedLines'],ids)
        self.assertEqual(other_capture['activeLines'],[i for i in ids if M.T2_PRODUCTS[int(w.t2LineProduct[i])]['complexity']==other_phase])

    def test_reject_missing_snapshot_and_wrong_book(self):
        cfg,w,phase=self.fixture()
        book=InputMarket(w,1)
        with self.assertRaises(ValueError): capture_t2(w,cfg,1,0,phase,book,None)
        with self.assertRaises(ValueError): capture_t2(w,cfg,2,0,phase,book,np.zeros(3))

    def test_capture_in_real_phase_does_not_change_d3_trajectory(self):
        from tools.buying_v2.industrial_adapter import buy_t2_reference
        cfg,a,phase=self.fixture()
        _,b,_=self.fixture()
        overhead=K.production_line_overhead(b,cfg,'t2')
        records=[]
        def observe_then_buy(w,cfg,tick,firm,phase,book):
            records.append(capture_t2(w,cfg,tick,firm,phase,book,overhead))
            return buy_t2_reference(w,cfg,tick,firm,phase,book)
        K._operate_tier2_phase(a,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1,phase,purchase_company=buy_t2_reference)
        K._operate_tier2_phase(b,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1,phase,purchase_company=observe_then_buy)
        self.assertTrue(records)
        for n in a.array_names:
            np.testing.assert_array_equal(getattr(a,n),getattr(b,n),err_msg=n)
        self.assertEqual(a.costSinks,b.costSinks)
