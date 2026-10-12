from dataclasses import replace
from itertools import product
import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.phase_ledger import apply,SetQuotes
from tools.buying_v2.shared_first_bound import bound
from tools.buying_v2.prefix_continuation_bound import upper_value


class SharedFirstBoundTests(unittest.TestCase):
    def test_common_first_production_removes_perfect_information_gap(self):
        c,s,paths=case(2,2,2,2);e=replace(paths[0].events[0],funded_demands=(2,)*4)
        posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
        result=bound(c,s,s,e,(),posterior,max_first_batches=2)
        independent=sum(p.probability*upper_value(c,s,s,e,(),p.events[1:],p.input_values,p.finished_values) for p in paths)
        self.assertAlmostEqual(result['value'],6.5,places=6)
        self.assertLess(result['value'],independent)
        self.assertEqual(result['firstBatchStates'],3)
        self.assertEqual(result['scenarioEvaluations'],6)

    def test_every_prefix_bounds_matching_continuation_policies(self):
        c,s,paths=case(2,2,2,2);e=replace(paths[0].events[0],funded_demands=(2,)*4)
        future=tuple(replace(p,events=p.events[1:]) for p in paths);values={}
        for a in product(range(3),repeat=4):
            try:new,_=apply(c,s,e,a)
            except ValueError as error:
                if str(error) in ('infeasible procurement allocation','production would exceed physical storage'):continue
                raise
            result=solve(c,new,future,funding=frozen_funding,allocation_search='feasible-prefix')
            values[a]=result['expectedValue']+new.cash-s.cash
        for length in range(5):
            for prefix in {a[:length] for a in values}:
                result=bound(c,s,s,e,prefix,tuple((p.probability,p) for p in future),max_first_batches=2)
                self.assertGreaterEqual(result['value'],max(v for a,v in values.items() if a[:length]==prefix))

    def test_advance_buffers_fees_and_terminal_values(self):
        for first_price,later_price in ((1.,20.),(7.,1.)):
            c,s,paths=case(2,2,2,2)
            s=replace(s,finished=(1,),finished_basis=(3.,),held=(1,0),basis=(40.,0.),incumbents=(0,0))
            modified=[]
            for path in paths:
                events=list(path.events)
                for index,price in ((0,first_price),(4,later_price)):
                    e=events[index]
                    events[index]=replace(e,offers=tuple(replace(o,price=price+o.supplier) for o in e.offers),fee_multiple=3.)
                events[2]=replace(events[2],fee_income=2.)
                events[6]=replace(events[6],fee_income=3.)
                modified.append(replace(path,events=tuple(events),input_values=((0.,.5,1.),)*2,
                    finished_values=((0.,1.,1.5,1.75,2.),)))
            exact=solve(c,s,tuple(modified),funding=frozen_funding,allocation_search='feasible-prefix')['expectedValue']
            posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in modified)
            result=bound(c,s,s,modified[0].events[0],(),posterior,max_first_batches=2)
            self.assertGreaterEqual(result['value'],exact)

    def test_explicit_budget_and_unsupported_calendar(self):
        c,s,paths=case(2,2,2,2);e=paths[0].events[0]
        p=replace(paths[0],events=paths[0].events[1:]);posterior=((1.,p),)
        self.assertEqual(bound(c,s,s,e,(),posterior,max_first_batches=1)['value'],float('inf'))
        p=replace(p,events=(SetQuotes('new',(4.,)),)+p.events)
        self.assertEqual(bound(c,s,s,e,(),((1.,p),),max_first_batches=2)['value'],float('inf'))
        with self.assertRaises(ValueError):bound(c,s,s,e,(),posterior,max_first_batches=True)


if __name__=='__main__':unittest.main()
