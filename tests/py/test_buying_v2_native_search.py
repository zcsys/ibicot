from dataclasses import replace
from itertools import product
import unittest
import test_buying_v2_continuation_search as comparison
import test_buying_v2_native_resident as fixtures
from test_buying_v2_phase_ledger import company,state,buy
from tools.buying_v2.industry_oracle import Offer
from tools.buying_v2.phase_ledger import apply
from tools.buying_v2.phase_oracle import Scenario,solve as oracle
from tools.buying_v2.quantity_value import LinearQuantityValue
from tools.buying_v2.continuation_search import solve
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_actions import AllocationFrame


class NativeSearchTests(unittest.TestCase):
    def test_prescribed_fixture_now_optimizes_against_independent_oracle(self):
        c,s,path=fixtures.NativeResidentTests().fixture()
        for storage in ('resident','arena'):
            comparison.SearchTests().compare(c,s,(path,),storage=storage)

    def test_subtraction_boundary_does_not_hide_feasible_purchase(self):
        held=1.0000000000000002
        self.assertEqual(int(2.-held),0)
        self.assertEqual(held+1,2.)
        c=replace(company(),slots=(2.,))
        s=state(held=(held,),basis=(0.,))
        event=buy(offers=(Offer(0,1,1.,1),),demands=(1,),active=())
        value=LinearQuantityValue((0.,10.),(0.,30.))
        path=Scenario(1.,(event,),(value,),(value,))
        expected,_=apply(c,s,event,(1,))
        for storage in ('resident','arena'):
            result=comparison.SearchTests().compare(c,s,(path,),storage=storage)
            self.assertEqual(result['leaves'][0]['policy'],{0:(1,)})
            self.assertEqual(result['leaves'][0]['state'],expected)

    def test_split_offer_frame_matches_feasible_native_grid(self):
        c=replace(company(),slots=(2.5,))
        s=state(cash=100.,held=(.1,))
        event=buy(offers=(Offer(0,1,1.,2),Offer(0,2,2.,3)),demands=(2,3),active=())
        value=LinearQuantityValue((0.,10.),(0.,30.))
        path=Scenario(1.,(event,),(value,),(value,))
        frame=AllocationFrame(Resident(c,s,compile_calendar(c,s,(path,))),0,0)
        actual=[]
        while True:
            row=frame.next(max_prefixes=1000)
            if row is None:break
            actual.append(row)
        self.assertEqual(actual,[a for a in product(range(3),range(4)) if (s.held[0]+a[0])+a[1]<=c.slots[0]])
        for storage in ('resident','arena'):
            comparison.SearchTests().compare(c,s,(path,),storage=storage)
        for storage in ('resident','arena'):
            comparison.SearchTests().compare(c,s,(path,),storage=storage,funding='continuation')

    def test_shared_inputs_multiple_lines_and_observed_outcomes(self):
        from tools.buying_v2.benchmark_phase_search import case
        from tools.buying_v2.phase_ledger import Purchase
        c,s,paths=case(1,1,2,2,lines=2)
        c=replace(c,slots=tuple(q+.5 for q in c.slots))
        s=replace(s,held=(.1,.5),basis=(.2,.3),finished=(.5,.1),finished_basis=(.4,.2))
        value=LinearQuantityValue((0.,20.),(0.,2.))
        paths=tuple(replace(p,events=tuple(replace(e,funded_demands=tuple(o.stock for o in e.offers)) if isinstance(e,Purchase) else e for e in p.events),input_values=(value,)*2,finished_values=(value,)*2) for p in paths)
        for storage in ('resident','arena'):
            for funding in ('supplied','continuation'):
                comparison.SearchTests().compare(c,s,paths,storage=storage,funding=funding)

    def test_optional_integer_proofs_do_not_change_native_result(self):
        from test_buying_v2_continuation_query_memo import comparable
        c,s,path=fixtures.NativeResidentTests().fixture()
        expected=comparable(solve(c,s,(path,)))
        for options in ({'closing':True},{'prune_continuation':True},
                        {'prune_prefix':True,'shared_first_states':16}):
            self.assertEqual(comparable(solve(c,s,(path,),**options)),expected)

    def test_native_endogenous_multiphase_against_oracle(self):
        c,s,path=fixtures.NativeResidentTests().fixture()
        for storage in ('resident','arena'):
            comparison.SearchTests().compare(c,s,(path,),storage=storage,funding='continuation')

    def test_native_endogenous_fees_cash_and_wholesale_lots(self):
        c=replace(company(),slots=(5.5,))
        value=LinearQuantityValue((0.,20.),(0.,60.))
        for cash in (2.4,10.):
            s=state(cash=cash,held=(.5,),basis=(.2,),incumbents=(1,))
            event=buy(offers=(Offer(0,1,2.,2,2),Offer(0,2,1.,4,2)),demands=(),active=(),fee_multiple=.5)
            path=Scenario(1.,(event,),(value,),(value,))
            for storage in ('resident','arena'):
                comparison.SearchTests().compare(c,s,(path,),storage=storage,funding='continuation')
