import unittest
from dataclasses import replace
from tools.buying_v2.industry_oracle import Problem, Offer, Line
from tools.buying_v2.funding import funded_intentions


class FundingTests(unittest.TestCase):
    def test_quantity_recomputed_at_each_quote_without_stock_cap(self):
        values = (0.,)+tuple(20.*min(y,8)+12.*max(0,y-8) for y in range(1,11))
        p = Problem((0,), (0.,), (1.,), (10,), 10., 1000.,
                    (Offer(0,0,10.,2),Offer(0,1,15.,20)), (0,), (0,), (2.,),
                    (Line((1,),10,0.,100.,0.,values,1.),), ((0.,)*11,))
        result = funded_intentions(p)
        from tools.buying_v2.funding import plan
        funded, allocation, evidence = plan(p)
        self.assertEqual(tuple(allocation[0]),(2,6))
        self.assertEqual(funded.funded_demands,(10,8))
        self.assertEqual(result['bids'],(10,))
        self.assertEqual(result['funded_demands'],(10,8))
        self.assertEqual(result['reference_goods'],100.)
        empty = replace(p,offers=tuple(replace(o,stock=0) for o in p.offers))
        self.assertEqual(funded_intentions(empty)['funded_demands'],(10,8))

    def test_shared_cash_is_not_reused_for_each_ingredient(self):
        p = Problem((0,0),(0.,0.),(1.,1.),(4,4),8.,45.,
                    (Offer(0,0,10.,4),Offer(1,1,20.,4)),(0,1),(0,0),(0.,0.),
                    (Line((1,1),4,1.,100.,0.,(0.,100.,200.,300.,400.),2.),),((0.,)*5,(0.,)*5))
        result = funded_intentions(p)
        self.assertEqual(result['bids'],(1,1))
        self.assertEqual(result['reference_quantities'],(1,1))
        self.assertEqual(result['reference_goods'],30.)

    def test_cash_and_lots_remain_hard_constraints(self):
        p = Problem((0,),(0.,),(1.,),(8,),8.,7.,
                    (Offer(0,0,2.,8,4),),(0,),(0,),(0.,),
                    (Line((1,),8,0.,100.,0.,tuple(100.*q for q in range(9)),1.),),((0.,)*9,))
        self.assertEqual(funded_intentions(p)['bids'],(0,))

    def test_history_gate_is_not_removed_from_funding(self):
        p = Problem((1,0),(100.,0.),(1.,1.),(2,2),4.,100.,
                    (Offer(1,1,1.,1),),(-1,1),(0,0),(0.,0.),
                    (Line((1,1),1,.75,10.,0.,(0.,10.),2.),),((0.,)*3,(0.,)*3))
        self.assertEqual(funded_intentions(p)['bids'],(0,0))


if __name__ == '__main__':
    unittest.main()
