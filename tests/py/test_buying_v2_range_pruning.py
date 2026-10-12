import unittest
import test_buying_v2_native_resident as native
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.benchmark_phase_search import case
from test_buying_v2_continuation_query_memo import comparable
from test_buying_v2_continuation_differential import cases


class RangePruningTests(unittest.TestCase):
    def test_seeded_complete_results_match_unpruned(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                args=dict(funding='continuation',storage='arena',supply=supply)
                expected=solve(c,s,paths,**args)
                actual=solve(c,s,paths,**args,prune_prefix=True,prune_ranges=True)
                self.assertEqual(comparable(actual),comparable(expected))

    def test_native_result_and_budget_accounting(self):
        c,s,path=native.NativeResidentTests().fixture()
        for funding in ('supplied','continuation'):
            expected=solve(c,s,(path,),funding=funding)
            actual=solve(c,s,(path,),funding=funding,prune_prefix=True,prune_ranges=True)
            self.assertEqual(comparable(actual),comparable(expected))
        with self.assertRaises(SearchLimit):
            solve(c,s,(path,),prune_prefix=True,prune_ranges=True,max_prefixes=1)
        with self.assertRaisesRegex(ValueError,'requires prefix'):
            solve(c,s,(path,),prune_ranges=True)

    def test_range_pruning_preserves_complete_result_and_ties(self):
        c,s,paths=case(2,2,2,2)
        expected=solve(c,s,paths,funding='continuation',prune_prefix=True)
        actual=solve(c,s,paths,funding='continuation',prune_prefix=True,prune_ranges=True)
        self.assertEqual(comparable(actual),comparable(expected))
