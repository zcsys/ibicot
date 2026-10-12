import unittest
from dataclasses import replace
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.shared_first_bound import BoundMemo
from tools.buying_v2.shared_joint_first_bound import bound
from tools.buying_v2.continuation_search import solve
from test_buying_v2_continuation_differential import cases
from test_buying_v2_continuation_query_memo import comparable


class SharedRecourseMemoTests(unittest.TestCase):
    def test_bound_values_and_charged_work_match_with_key_changes(self):
        c,s,paths=case(2,2,2,2,lines=2);e=paths[0].events[0]
        posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
        for capacity in (1,64):
            memo=BoundMemo(capacity)
            for state in (s,replace(s,quotes=(7.,9.)),replace(s,held=(1,1)),replace(s,cash=s.cash-5),s):
                for prefix in ((),(0,),(1,)):
                    args=(c,s,state,e,prefix,posterior)
                    self.assertEqual(bound(*args,max_first_states=64),bound(*args,max_first_states=64,recourse_memo=memo))
            self.assertLessEqual(memo.peak_entries,capacity)
            if capacity==64:self.assertGreater(memo.hits,0)

    def test_seeded_complete_results_and_work_unchanged(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                opts=dict(funding='continuation',storage='arena',supply=supply,prune_prefix=True,shared_first_states=64,closing=True,proof_memo_entries=32,closing_cash_relaxed=True,max_prefixes=200000)
                a=solve(c,s,paths,**opts);b=solve(c,s,paths,**opts,shared_recourse_memo_entries=64)
                self.assertEqual(comparable(a),comparable(b))
                self.assertEqual(a['diagnostics']['prefixBoundWork'],b['diagnostics']['prefixBoundWork'])
                self.assertLessEqual(b['diagnostics']['proofMemos']['recourse']['peakEntries'],64)

    def test_validation(self):
        for value in (-1,True,1.5):
            with self.assertRaises(ValueError):solve(*case(1,1,1,1),prune_prefix=True,shared_first_states=64,shared_recourse_memo_entries=value)
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),shared_recourse_memo_entries=1)


if __name__=='__main__':unittest.main()
