import unittest
from dataclasses import replace
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.closing_boxes import solve as boxes
from tools.buying_v2.closing_values import solve as exhaustive
from tools.buying_v2.continuation_search import solve
from test_buying_v2_continuation_differential import cases
from test_buying_v2_continuation_query_memo import comparable


class JointFallbackTests(unittest.TestCase):
    def test_direct_fallback_matches_exhaustive_and_charges_work(self):
        used=0
        for capacity in (1,2):
            c,s,paths=case(capacity,2,1,2,lines=2)
            event=replace(paths[0].events[0],funded_demands=tuple(o.stock for o in paths[0].events[0].offers))
            posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
            expected=exhaustive(c,s,s,event,posterior)
            for relaxed in (False,True):
                actual=boxes(c,s,s,event,posterior,include_costs=True,compiled_costs=True,joint_bound=True,cash_relaxed_joint_bound=relaxed)
                for k in ('allocation','payment','value'):self.assertEqual(expected[k],actual[k])
                used+=actual['jointBoundWork']
                self.assertLessEqual(actual['boxes']+actual['jointBoundWork'],100000)
        self.assertGreater(used,0)

    def test_seeded_full_results(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                opts=dict(funding='continuation',storage='arena',supply=supply,closing=True,proof_memo_entries=32,closing_cash_relaxed=True,max_prefixes=200000)
                a=solve(c,s,paths,**opts);b=solve(c,s,paths,**opts,closing_joint_fallback=True)
                self.assertEqual(comparable(a),comparable(b))

    def test_mode_validation(self):
        for value in (True,1):
            with self.assertRaises(ValueError):solve(*case(1,1,1,1),closing_joint_fallback=value)


if __name__=='__main__':unittest.main()
