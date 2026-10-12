import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_oracle import solve,PhaseSearchLimit
from test_buying_v2_prefix_pruning import semantic


class SharedFirstPruningTests(unittest.TestCase):
    def test_policy_accounts_and_charged_work(self):
        pruned=0
        for capacity in (1,2,4):
            for funding in ('continuation','continuation-transfer-neutral'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    kw=dict(funding=funding,supply=supply,allocation_search='feasible-prefix',prune_prefix=True,
                        closing_search='compiled-certified-boxes',funding_memo_size=4096,closing_memo_size=4096,
                        prune_continuation=True,continuation_bound_costs=True,max_prefix_nodes=100000)
                    args=case(capacity,2,2,2)
                    base=solve(*args,**kw)
                    result=solve(*args,**kw,shared_first_batches=8)
                    self.assertEqual(semantic(base),semantic(result))
                    stats=result['prefixSearch'];pruned+=stats['sharedBoundPruned']
                    self.assertGreaterEqual(stats['sharedBoundWork'],stats['sharedBoundCalls'])
        self.assertGreater(pruned,0)

    def test_budget_option_validation_and_capacity_fallback(self):
        args=case(2,2,2,2)
        for limit in (-1,True,1.5):
            with self.assertRaises(ValueError):solve(*args,funding='continuation',shared_first_batches=limit)
        with self.assertRaises(ValueError):solve(*args,funding='continuation',shared_first_batches=2)
        kw=dict(funding='continuation',allocation_search='feasible-prefix',prune_prefix=True)
        base=solve(*args,**kw)
        result=solve(*args,**kw,shared_first_batches=1)
        self.assertEqual(semantic(base),semantic(result))
        self.assertEqual(result['prefixSearch']['sharedBoundWork'],0)
        self.assertGreater(result['prefixSearch']['sharedBoundSkipped'],0)


if __name__=='__main__':unittest.main()
