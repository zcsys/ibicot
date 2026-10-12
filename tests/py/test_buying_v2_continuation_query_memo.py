import unittest
from tools.buying_v2.continuation_query_memo import QueryMemo
from tools.buying_v2.continuation_search import solve
from tools.buying_v2.benchmark_phase_search import case
from test_buying_v2_continuation_differential import cases


def semantic(result):
    return {k:v for k,v in result.items() if k!='diagnostics'}


def comparable(result):
    import json
    from tools.buying_v2.benchmark_continuation import encode
    return json.dumps(semantic(result),default=encode,sort_keys=True)


class QueryMemoTests(unittest.TestCase):
    def test_all_seeded_cases_preserve_complete_results(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                base=solve(c,s,paths,funding='continuation',storage='arena',supply=supply)
                cached=solve(c,s,paths,funding='continuation',storage='arena',supply=supply,funding_memo_entries=128)
                self.assertEqual(comparable(base),comparable(cached))
                self.assertLessEqual(cached['diagnostics']['allocations'],base['diagnostics']['allocations'])

    def test_reuse_and_tiny_eviction_keep_policy(self):
        args=case(1,1,2,2);base=solve(*args,funding='continuation',storage='arena')
        for capacity in (1,128):
            cached=solve(*args,funding='continuation',storage='arena',funding_memo_entries=capacity)
            self.assertEqual(comparable(base),comparable(cached))
            self.assertLessEqual(cached['diagnostics']['fundingMemo']['peakEntries'],capacity)
        self.assertGreater(cached['diagnostics']['fundingMemo']['hits'],0)

    def test_key_keeps_posterior_supply_and_common_history_boundary(self):
        from tools.buying_v2.continuation_program import compile_calendar
        from tools.buying_v2.continuation_resident import Resident
        from tools.buying_v2.continuation_query import prepare
        c,s,paths=case(1,1,2,2);p=compile_calendar(c,s,paths);rs=[Resident(c,s,p) for _ in paths]
        for r in rs:r.history_node=0;r.history_count=0
        memo=QueryMemo(p,2,100000);iv,fv,_=prepare(rs[0],0,0)
        a=memo.key([(0,rs[0],0)],0,iv,fv)
        self.assertNotEqual(a,memo.key([(1,rs[1],0)],0,iv,fv))
        rs[0].data[8][:]=123;rs[0].data[12][:]=123
        self.assertEqual(a,memo.key([(0,rs[0],999)],0,iv,fv))
        rs[0].integers[6]+=1
        self.assertNotEqual(a,memo.key([(0,rs[0],0)],0,iv,fv))
        rs[0].integers[6]-=1;rs[0].history_node=1
        self.assertEqual(a,memo.key([(0,rs[0],0)],0,iv,fv))
        with self.assertRaisesRegex(ValueError,'common observed prefix'):memo.key([(0,rs[0],0),(1,rs[1],0)],0,iv,fv)

    def test_payload_limits_and_fifo_eviction(self):
        memo=QueryMemo(None,2,40);memo.put(b'a',((1,),2.,3.));self.assertEqual(memo.get(b'a'),((1,),2.,3.))
        memo.put(b'b',((2,),3.,4.));self.assertIsNone(memo.get(b'a'));self.assertEqual(memo.evictions,1)
        memo.put(b'x'*100,((1,),2.,3.));self.assertEqual(memo.oversized,1)
        self.assertLessEqual(memo.peak_bytes,40)


if __name__=='__main__':unittest.main()
