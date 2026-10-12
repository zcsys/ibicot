from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.shared_first_bound import bound,BoundMemo
from tools.buying_v2.phase_oracle import solve
from test_buying_v2_prefix_pruning import semantic


class SharedBoundMemoTests(unittest.TestCase):
    def test_equivalent_profits_hit_with_separate_cash_offsets(self):
        c,s,paths=case(2,2,2,2);event=paths[0].events[0]
        posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
        memo=BoundMemo(2)
        a=bound(c,s,s,event,(),posterior,max_first_batches=2,memo=memo)
        # Basis and preferences affect the actual ledger, but this upper bound
        # explicitly relaxes them and may safely reuse the identical value.
        changed=replace(s,basis=(100.,100.),incumbents=(0,0))
        b=bound(c,s,changed,event,(),posterior,max_first_batches=2,memo=memo)
        self.assertEqual(a['value'],b['value']);self.assertEqual(b['firstBatchStates'],0)
        self.assertEqual(memo.hits,1)
        for cash in (201.,202.):
            state=replace(s,cash=cash)
            cached=bound(c,s,state,event,(),posterior,max_first_batches=2,memo=memo)
            plain=bound(c,s,state,event,(),posterior,max_first_batches=2)
            self.assertEqual(cached['value'],plain['value'])
            self.assertEqual(cached['firstBatchStates'],0)
        self.assertEqual(memo.hits,3)
        for quote in (9.,8.):
            state=replace(s,quotes=(quote,))
            cached=bound(c,s,state,event,(),posterior,max_first_batches=2,memo=memo)
            plain=bound(c,s,state,event,(),posterior,max_first_batches=2)
            self.assertEqual(cached,plain)
        self.assertEqual(memo.peak_entries,2)
        self.assertEqual(len(memo.data),2)

    def test_complete_planner_results_and_run_isolation(self):
        args=case(4,2,2,2)
        kw=dict(funding='continuation',allocation_search='feasible-prefix',prune_prefix=True,shared_first_batches=8,
                closing_search='compiled-certified-boxes',funding_memo_size=4096,closing_memo_size=4096,
                prune_continuation=True,continuation_bound_costs=True,max_prefix_nodes=100000)
        base=solve(*args,**kw)
        for capacity in (1,4096):
            cached=solve(*args,**kw,shared_bound_memo_size=capacity)
            self.assertEqual(semantic(base),semantic(cached))
            self.assertLessEqual(cached['prefixSearch']['sharedBoundMemo']['peakEntries'],capacity)
        again=solve(*args,**kw,shared_bound_memo_size=4096)
        self.assertEqual(cached,again)

    def test_invalid_capacity_rejected(self):
        for capacity in (0,-1,True,1.5):
            with self.assertRaises(ValueError):BoundMemo(capacity)
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),funding='continuation',shared_bound_memo_size=1)


if __name__=='__main__':unittest.main()
