import unittest
from dataclasses import replace
import numpy as np
from test_buying_v2_persistent_supply import fixture
import test_buying_v2_continuation_search as search_tests
from tools.buying_v2.phase_ledger import Purchase,SetQuotes
from tools.buying_v2.industry_oracle import Offer
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_search import solve


def funded(path):
    return replace(path,events=tuple(replace(e,funded_demands=(1,)*len(e.offers)) if isinstance(e,Purchase) else e for e in path.events))


class SupplyTests(unittest.TestCase):
    def compare(self,c,s,paths):return search_tests.SearchTests().compare(c,s,paths,supply='persistent-arrivals')

    def test_depletion_arrivals_and_hidden_future_branching(self):
        c,s,path=fixture();_,_,restock=fixture(2)
        paths=(replace(funded(path),probability=.5),replace(funded(restock),probability=.5))
        result=self.compare(c,s,paths)
        self.assertEqual(result['expectedValue'],(1.75+2.5)/2)
        self.assertEqual([l['policy'][0] for l in result['leaves']],[(1,),(1,)])
        self.assertEqual([l['policy'][4] for l in result['leaves']],[(0,),(1,)])

    def test_live_incumbent_stock_controls_fee(self):
        c,s,path=fixture();s=replace(s,quotes=(10.,));events=list(path.events)
        events[3]=SetQuotes('lower',(10.,))
        events[4]=replace(events[4],offers=(Offer(0,1,5.,1),Offer(0,2,1.,1)),reliability=(0.,0.),fee_multiple=2.)
        path=funded(replace(path,events=tuple(events)))
        result=self.compare(c,s,(path,))
        self.assertEqual(result['leaves'][0]['state'].accounts.fee_expense,0.)

    def test_resident_supply_forks_failure_and_program_immutability(self):
        c,s,path=fixture();path=funded(path);p=compile_calendar(c,s,(path,));original=p.integers.copy()
        root=Resident(c,s,p,supply='persistent-arrivals');child=root.fork()
        child.run(0,{0:(1,)},stop=1,observe=True)
        self.assertFalse(np.array_equal(child.integers,root.integers));self.assertTrue(np.array_equal(p.integers,original))
        before=root.integers.copy()
        with self.assertRaisesRegex(ValueError,'infeasible procurement'):root.run(0,{0:(1,),4:(1,)},observe=True)
        self.assertTrue(np.array_equal(root.integers,before));self.assertEqual(root.snapshot(),s);self.assertEqual(root.observations,())
        child.run(0,{4:(0,)},start=1,observe=True)
        self.assertEqual(child.snapshot().accounts.goods_paid,1.)

    def test_arrival_grid_and_invalid_decreasing_supply(self):
        for stock in (0,1,2):
            for arrival in (0,1,2):
                c,s,path=fixture(stock+arrival);events=list(path.events)
                events[0]=replace(events[0],offers=(Offer(0,1,1.,stock),));path=funded(replace(path,events=tuple(events)))
                result=self.compare(c,s,(path,))
                expected=max(a*1.75+b*.75 for a in (0,1) for b in (0,1) if a<=stock and a+b<=stock+arrival)
                self.assertEqual(result['expectedValue'],expected)
        c,s,path=fixture(0)
        with self.assertRaisesRegex(ValueError,'nondecreasing'):solve(c,s,(funded(path),),supply='persistent-arrivals')
        with self.assertRaisesRegex(ValueError,'supply mode'):solve(c,s,(funded(path),),supply='unknown')


if __name__=='__main__':unittest.main()
