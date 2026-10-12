import unittest
from tools.buying_v2.continuation_search import solve, SearchLimit
from test_buying_v2_continuation_differential import cases
from test_buying_v2_continuation_query_memo import comparable
from tools.buying_v2.benchmark_phase_search import case


class ConnectedPruningTests(unittest.TestCase):
    def test_seeded_complete_result_parity(self):
        checked=0
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                options=dict(funding='continuation',storage='arena',supply=supply)
                base=solve(c,s,paths,**options)
                bounded=solve(c,s,paths,**options,prune_continuation=True)
                self.assertEqual(comparable(base),comparable(bounded))
                checked+=bounded['diagnostics']['boundEvaluations']
        self.assertGreater(checked,0)

    def test_mode_validation(self):
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),prune_continuation=1)

    def test_budget_failure_has_no_policy(self):
        with self.assertRaises(SearchLimit) as caught:
            solve(*case(2,2,2,2),funding='continuation',storage='arena',prune_continuation=True,max_prefixes=10)
        self.assertNotIn('leaves',caught.exception.diagnostics)


if __name__=='__main__':unittest.main()
