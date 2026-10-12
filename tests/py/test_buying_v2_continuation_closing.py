import unittest
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.benchmark_phase_search import case
from test_buying_v2_continuation_differential import cases
from test_buying_v2_continuation_query_memo import comparable


class ClosingTests(unittest.TestCase):
    def test_seeded_complete_results_preserved_with_fallback(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                base=solve(c,s,paths,funding='continuation',storage='arena',supply=supply)
                bounded=solve(c,s,paths,funding='continuation',storage='arena',supply=supply,closing=True)
                self.assertEqual(comparable(base),comparable(bounded))

    def test_supported_closing_reduces_allocations(self):
        args=case(2,2,1,1)
        base=solve(*args,funding='continuation',storage='arena')
        bounded=solve(*args,funding='continuation',storage='arena',closing=True)
        self.assertEqual(comparable(base),comparable(bounded))
        self.assertLess(bounded['diagnostics']['allocations'],base['diagnostics']['allocations'])
        self.assertGreater(bounded['diagnostics']['closingSolves'],0)

    def test_limits_return_no_partial_policy(self):
        args=case(2,2,1,1)
        with self.assertRaises(SearchLimit) as cm:solve(*args,funding='continuation',storage='arena',closing=True,max_allocations=1,max_prefixes=1)
        self.assertNotIn('leaves',cm.exception.diagnostics)


if __name__=='__main__':unittest.main()
