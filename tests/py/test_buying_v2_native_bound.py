from dataclasses import replace
from itertools import product
import unittest
import test_buying_v2_native_resident as fixtures
from tools.buying_v2.continuation_bound import upper_value
from tools.buying_v2.phase_ledger import apply,horizon_value
from tools.buying_v2.quantity_value import LinearQuantityValue


class NativeBoundTests(unittest.TestCase):
    def test_envelope_covers_every_feasible_allocation_and_suffix(self):
        c,initial,path=fixtures.NativeResidentTests().fixture()
        for fraction in (.1,.5,.999999999):
            start=replace(initial,held=(fraction,),finished=(fraction,))
            for q in range(6):
                state=start
                for index,event in enumerate(path.events):
                    bound=upper_value(c,start,state,path.events[index:],path.input_values,path.finished_values,include_costs=True)
                    try:
                        end=state
                        for j,e in enumerate(path.events[index:],index):end,_=apply(c,end,e,(q,) if j==1 else None)
                    except ValueError:break
                    self.assertGreaterEqual(bound,horizon_value(start,end,path.input_values,path.finished_values),(fraction,q,index))
                    state,_=apply(c,state,event,(q,) if index==1 else None)

    def test_terminal_peak_and_incomplete_domain(self):
        c,s,path=fixtures.NativeResidentTests().fixture()
        curve=LinearQuantityValue((0.,.5,20.),(0.,100.,0.))
        bound=upper_value(c,s,s,(),(curve,),(curve,))
        self.assertGreaterEqual(bound,200.)
        short=LinearQuantityValue((0.,1.),(0.,0.))
        self.assertEqual(upper_value(c,s,s,(),(short,),(curve,)),float('inf'))

    def test_multiline_multiperiod_envelope_covers_exhaustive_optimum(self):
        from tools.buying_v2.benchmark_phase_search import case
        from tools.buying_v2.phase_oracle import solve
        from tools.buying_v2.phase_ledger import Purchase
        c,s,paths=case(1,1,2,2,lines=2)
        c=replace(c,slots=tuple(q+.5 for q in c.slots))
        curve=LinearQuantityValue((0.,.5,20.),(0.,.3,0.))
        for fraction in (.1,.5,.999999999):
            initial=replace(s,held=(fraction,fraction),basis=(.2,.3),finished=(fraction,fraction),finished_basis=(.4,.2))
            for path in paths:
                path=replace(path,probability=1.,input_values=(curve,)*2,finished_values=(curve,)*2)
                expected=solve(c,initial,(path,),funding=lambda c,s,e:tuple(o.stock for o in e.offers))['expectedValue']
                bound=upper_value(c,initial,initial,path.events,path.input_values,path.finished_values,include_costs=True)
                self.assertGreaterEqual(bound,expected)

    def test_native_cost_refinement_is_finite_and_tighter(self):
        c,s,path=fixtures.NativeResidentTests().fixture()
        gross=upper_value(c,s,s,path.events,path.input_values,path.finished_values)
        costs=upper_value(c,s,s,path.events,path.input_values,path.finished_values,include_costs=True)
        self.assertLess(costs,gross)
        from tools.buying_v2.continuation_bound import line_envelope
        result=line_envelope(c.lines[0],.5,(.1,),(1.,),5,((5.5,3.),))
        self.assertGreaterEqual(result,9.1)
        self.assertAlmostEqual(result,9.1,places=12)

    def test_free_input_ceiling_can_deduct_actual_purchase_payments(self):
        c,start,path=fixtures.NativeResidentTests().fixture()
        gross=upper_value(c,start,start,path.events,path.input_values,path.finished_values)
        ceiling=upper_value(c,start,start,path.events,path.input_values,path.finished_values,include_costs=True,free_inputs=True)
        priced=upper_value(c,start,start,path.events,path.input_values,path.finished_values,include_costs=True)
        self.assertLess(ceiling,gross);self.assertGreaterEqual(ceiling,priced)
        for q in range(6):
            state=start;goods=0.
            try:
                for i,event in enumerate(path.events):
                    state,detail=apply(c,state,event,(q,) if i==1 else None)
                    goods+=detail.get('goods',0.)
            except ValueError:continue
            self.assertGreaterEqual(ceiling-goods,horizon_value(start,state,path.input_values,path.finished_values))
        with self.assertRaisesRegex(ValueError,'requires cost'):
            upper_value(c,start,start,path.events,path.input_values,path.finished_values,free_inputs=True)
