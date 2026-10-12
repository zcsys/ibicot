import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_oracle import solve


def semantics(result):
    return {k:v for k,v in result.items() if k not in ('enumeratedNodes','closingSolver')}


class ClosingMemoTests(unittest.TestCase):
    def test_complete_policies_and_accounts_match_without_cache(self):
        args=case(2,2,2,2)
        for funding in ('continuation','continuation-transfer-neutral'):
            for supply in ('independent-snapshots','persistent-arrivals'):
                kw=dict(funding=funding,supply=supply,closing_search='compiled-fast-cost-boxes',
                        funding_memo_size=4096,max_nodes=20000,max_prefix_nodes=100000)
                base=solve(*args,**kw)
                for size in (1,4096):
                    result=solve(*args,**kw,closing_memo_size=size)
                    self.assertEqual(semantics(base),semantics(result))
                    memo=result['closingSolver']['memo']
                    self.assertLessEqual(memo['peakEntries'],size)
                    self.assertEqual(base['enumeratedNodes']-result['enumeratedNodes'],memo['savedAllocations'])
                    self.assertEqual(base['closingSolver']['boxes']-result['closingSolver']['boxes'],memo['savedBoxes'])
                    if size==4096:
                        self.assertGreater(memo['hits'],0)
                        self.assertGreater(memo['savedBoxes'],0)

    def test_exhaustive_mode_and_run_isolation(self):
        args=case(1,2,2,2)
        kw=dict(funding='continuation',closing_search='compiled-exhaustive',funding_memo_size=4096)
        base=solve(*args,**kw)
        cached=solve(*args,**kw,closing_memo_size=4096)
        self.assertEqual(semantics(base),semantics(cached))
        cached['leaves'][0]['trace'][0]['cash']=-100.
        self.assertEqual(semantics(base),semantics(solve(*args,**kw,closing_memo_size=4096)))

    def test_invalid_capacity_and_work_limits(self):
        args=case(2,2,2,2)
        kw=dict(funding='continuation',closing_search='compiled-fast-cost-boxes')
        for size in (-1,True,1.5):
            with self.assertRaisesRegex(ValueError,'closing memo size'):
                solve(*args,**kw,closing_memo_size=size)
        for size in (0,4096):
            for budget in (dict(max_nodes=1),dict(max_prefix_nodes=1)):
                with self.assertRaisesRegex(ValueError,'node limit; no approximate result returned'):
                    solve(*args,**kw,closing_memo_size=size,**budget)


if __name__=='__main__':unittest.main()
