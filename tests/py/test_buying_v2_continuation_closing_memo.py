import unittest
from tools.buying_v2.continuation_search import solve
from tools.buying_v2.benchmark_phase_search import case
from test_buying_v2_continuation_differential import cases
from test_buying_v2_continuation_query_memo import comparable


class ClosingMemoTests(unittest.TestCase):
    def test_complete_seeded_results_preserved(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                base=solve(c,s,paths,funding='continuation',storage='arena',supply=supply,closing=True)
                cached=solve(c,s,paths,funding='continuation',storage='arena',supply=supply,closing=True,closing_memo_entries=128)
                self.assertEqual(comparable(base),comparable(cached))
                self.assertLessEqual(cached['diagnostics']['allocations'],base['diagnostics']['allocations'])

    def test_eviction_and_small_byte_budget_preserve_results(self):
        args=case(1,1,2,2);base=solve(*args,funding='continuation',storage='arena',closing=True)
        for size,bytecap in ((1,16777216),(128,16777216),(128,1)):
            cached=solve(*args,funding='continuation',storage='arena',closing=True,closing_memo_entries=size,closing_memo_bytes=bytecap)
            self.assertEqual(comparable(base),comparable(cached))
            self.assertLessEqual(cached['diagnostics']['closingMemo']['peakPayloadBytes'],bytecap)
            if size==128 and bytecap>1:self.assertGreater(cached['diagnostics']['closingMemo']['hits'],0)

    def test_requires_closing_mode(self):
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),closing_memo_entries=1)


if __name__=='__main__':unittest.main()
