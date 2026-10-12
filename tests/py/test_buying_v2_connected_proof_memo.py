import unittest
from tools.buying_v2.continuation_search import solve
from tools.buying_v2.benchmark_phase_search import case
from test_buying_v2_continuation_differential import cases
from test_buying_v2_continuation_query_memo import comparable


class ConnectedProofMemoTests(unittest.TestCase):
    def test_seeded_full_result_parity(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                options=dict(funding='continuation',storage='arena',supply=supply,closing=True,prune_prefix=True,shared_first_states=64,max_prefixes=200000)
                base=solve(c,s,paths,**options)
                for relaxed in (False,True):
                    actual=solve(c,s,paths,**options,proof_memo_entries=32,closing_cash_relaxed=relaxed)
                    self.assertEqual(comparable(base),comparable(actual))
                    for d in actual['diagnostics']['proofMemos'].values():self.assertLessEqual(d['peakEntries'],32)

    def test_actual_reuse_and_eviction_preserve_result(self):
        args=case(2,2,2,2)
        options=dict(funding='continuation',storage='arena',closing=True,prune_prefix=True,shared_first_states=64,max_prefixes=200000)
        base=solve(*args,**options)
        hits=0
        for capacity in (1,128):
            actual=solve(*args,**options,proof_memo_entries=capacity,closing_cash_relaxed=True)
            self.assertEqual(comparable(base),comparable(actual))
            for d in actual['diagnostics']['proofMemos'].values():
                hits+=d['hits'];self.assertLessEqual(d['peakEntries'],capacity)
        self.assertGreater(hits,0)

    def test_validation(self):
        for value in (-1,True,1.5):
            with self.assertRaises(ValueError):solve(*case(1,1,1,1),closing=True,proof_memo_entries=value)
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),proof_memo_entries=1)
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),closing_cash_relaxed=True)


if __name__=='__main__':unittest.main()
