from dataclasses import replace
from itertools import product
import math
import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_ledger import apply
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.prefix_continuation_bound import upper_value


class PrefixContinuationBoundTests(unittest.TestCase):
    def test_every_prefix_bounds_every_matching_exact_continuation(self):
        checked=0
        for periods in (1,2):
            c,s,paths=case(1,2,periods,2)
            event=replace(paths[0].events[0],funded_demands=(1,)*4)
            values={}
            for allocation in product(range(2),repeat=4):
                try:new,_=apply(c,s,event,allocation)
                except ValueError as e:
                    if str(e) in ('infeasible procurement allocation','production would exceed physical storage'):continue
                    raise
                future=tuple(replace(p,events=p.events[1:]) for p in paths)
                exact=solve(c,new,future,funding=frozen_funding)['expectedValue']
                values[allocation]=exact+new.cash-s.cash-(new.arrears-s.arrears)
            for length in range(5):
                for prefix in product(range(2),repeat=length):
                    matching=[v for a,v in values.items() if a[:length]==prefix]
                    if not matching:continue
                    bound=math.fsum(p.probability*upper_value(c,s,s,event,prefix,p.events[1:],p.input_values,p.finished_values) for p in paths)
                    self.assertGreaterEqual(bound,max(matching),(periods,prefix,bound,matching));checked+=1
        self.assertGreater(checked,40)

    def test_fixed_expensive_purchase_tightens_bound_and_preserves_state(self):
        c,s,paths=case(2,2,1,1);p=paths[0];e=replace(p.events[0],funded_demands=(2,)*4)
        def bound(prefix):return upper_value(c,s,s,e,prefix,p.events[1:],p.input_values,p.finished_values)
        # Fixing zero at cheap supplier then two at expensive supplier raises
        # compulsory cost compared with leaving that material uncommitted.
        self.assertLess(bound((0,2)),bound(()))
        self.assertEqual(s.held,(0,0));self.assertEqual(s.cash,200.)

    def test_shared_lines_basis_fees_and_terminal_values(self):
        from tools.buying_v2.phase_ledger import horizon_value
        from tools.buying_v2.industry_oracle import Line
        c,s,paths=case(2,2,1,1)
        c=replace(c,lines=c.lines+(Line((1,0),2,.25,8.,0.,(0.,)*3,1.),),finished_caps=(4,4))
        s=replace(s,held=(1,0),basis=(30.,0.),finished=(0,1),finished_basis=(0.,3.),quotes=(10.,8.),incumbents=(0,0))
        e=replace(paths[0].events[0],funded_demands=(2,)*4,fee_multiple=3.,active_lines=(0,1))
        events=(paths[0].events[1],replace(paths[0].events[2],demand=(2,2)))
        inputs=((0.,.5,1.),)*2;finished=((0.,1.,1.5,1.75,2.),)*2
        values={}
        for allocation in product(range(3),repeat=4):
            try:
                state,_=apply(c,s,e,allocation)
                for event in events:state,_=apply(c,state,event)
            except ValueError as error:
                if str(error) in ('infeasible procurement allocation','production would exceed physical storage'):continue
                raise
            values[allocation]=horizon_value(s,state,inputs,finished)
        self.assertGreater(len(values),5)
        for length in range(5):
            prefixes={a[:length] for a in values}
            for prefix in prefixes:
                bound=upper_value(c,s,s,e,prefix,events,inputs,finished)
                self.assertGreaterEqual(bound,max(v for a,v in values.items() if a[:length]==prefix))

    def test_invalid_prefix_and_unavailable_relaxation(self):
        c,s,paths=case(1,2,1,1);p=paths[0];e=p.events[0]
        for prefix in ((True,),(-1,),(2,), (0,)*5):
            with self.assertRaises(ValueError):upper_value(c,s,s,e,prefix,p.events[1:],p.input_values,p.finished_values)
        self.assertEqual(upper_value(c,s,s,e,(1,1),p.events[1:],p.input_values,p.finished_values),math.inf)


if __name__=='__main__':unittest.main()
