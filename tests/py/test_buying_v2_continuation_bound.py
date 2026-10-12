import unittest
from dataclasses import replace
from itertools import product
from tools.buying_v2.continuation_bound import upper_value
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.phase_ledger import apply,horizon_value,Purchase,OpenBook,SettleBook,SetQuotes,Rent
from tools.buying_v2.fee_boundary_study import fee_case,income_case

class ContinuationBoundTests(unittest.TestCase):
    def test_bound_exceeds_exact_conditional_values(self):
        for args in (case(1,1,1,1),case(2,2,1,1),case(1,1,2,2),fee_case(7.,3.,3),income_case(.5)):
            c,s,paths=args
            bound=sum(p.probability*upper_value(c,s,s,p.events,p.input_values,p.finished_values) for p in paths)
            exact=solve(c,s,paths,funding='continuation')['expectedValue']
            self.assertGreaterEqual(bound,exact)

    def test_every_feasible_first_allocation_and_its_remaining_policy_is_bounded(self):
        c,s,paths=case(2,2,2,2)
        checked=0
        for allocation in product(range(3),repeat=4):
            event=replace(paths[0].events[0],funded_demands=(2,)*4)
            try:new,_=apply(c,s,event,allocation)
            except ValueError as exc:
                if str(exc) in ('infeasible procurement allocation','production would exceed physical storage'):continue
                raise
            remaining=tuple(replace(p,events=p.events[1:]) for p in paths)
            # Oracle continuation is relative to new state. Restore the sunk
            # cash/liability delta for comparison to the original horizon.
            exact=solve(c,new,remaining,funding=frozen_funding,allocation_search='feasible-prefix')['expectedValue']
            exact+=new.cash-s.cash-(new.arrears-s.arrears)
            bound=sum(p.probability*upper_value(c,s,new,p.events,p.input_values,p.finished_values) for p in remaining)
            self.assertGreaterEqual(bound,exact);checked+=1
        self.assertGreater(checked,10)

    def test_frozen_open_book_excludes_new_production_and_new_quotes(self):
        c,s,paths=case(1,1,1,1)
        opened,_=apply(c,s,OpenBook('old'))
        buy=replace(paths[0].events[0],funded_demands=(1,1))
        events=(buy,SetQuotes('raise',(100.,)),SettleBook('old',(1,)))
        bound=upper_value(c,s,opened,events,((0.,0.),)*2,((0.,)*3,))
        self.assertLess(bound,1e-5)

    def test_old_arrears_and_fee_income_are_separate(self):
        c,s,paths=case(1,1,1,1);s=replace(s,arrears=3.)
        events=(OpenBook('fee'),SettleBook('fee',(0,),fee_income=5.),Rent('rent',2.,0.))
        normal=upper_value(c,s,s,events,((0.,0.),)*2,((0.,)*3,))
        neutral=upper_value(c,s,s,events,((0.,0.),)*2,((0.,)*3,),neutral=True)
        self.assertAlmostEqual(normal-neutral,5.,places=6)
        self.assertLess(neutral,1e-5)

    def test_nonmonotone_terminal_table_uses_its_maximum(self):
        c,s,paths=case(1,1,1,1)
        value=upper_value(c,s,s,(),((0.,0.),)*2,((0.,7.,1.),))
        self.assertAlmostEqual(value,7.,places=6)

    def test_incomplete_or_unknown_envelopes_never_claim_finite_bound(self):
        import math
        c,s,paths=case(1,1,1,1)
        for events,tables in (((object(),),((0.,0.),)*2),(paths[0].events,((0.,),)*2)):
            self.assertEqual(upper_value(c,s,s,events,tables,((0.,)*3,)),math.inf)

if __name__=='__main__':unittest.main()
