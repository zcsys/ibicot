import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve
from test_buying_v2_prefix_pruning import semantic


def economics(result):
    return {k:v for k,v in semantic(result).items() if k!='fundingRule'}


class SlotFundingTests(unittest.TestCase):
    def test_builtin_matches_callback_then_pruned_execution(self):
        for capacity in (1,2,4):
            for supply in ('independent-snapshots','persistent-arrivals'):
                args=case(capacity,2,2,2)
                kw=dict(supply=supply,allocation_search='feasible-prefix',closing_search='compiled-certified-boxes',
                        closing_memo_size=4096,closing_proposal_memo_size=4096,max_nodes=100000,max_prefix_nodes=100000)
                callback=solve(*args,**kw,funding=frozen_funding)
                explicit=solve(*args,**kw,funding='slot-deficit-v1')
                self.assertEqual(economics(callback),economics(explicit))
                pruned=solve(*args,**kw,funding='slot-deficit-v1',prune_prefix=True,prune_continuation=True,
                             continuation_bound_costs=True,shared_first_batches=16,shared_bound_memo_size=4096)
                self.assertEqual(economics(callback),economics(pruned))
                self.assertEqual(pruned['fundingRule'],'slot-deficit-v1')

    def test_arbitrary_callbacks_still_cannot_be_pruned(self):
        args=case(1,1,1,1)
        calls=[]
        def custom(company,state,event):
            calls.append(1);return frozen_funding(company,state,event)
        with self.assertRaisesRegex(ValueError,'arbitrary callbacks'):
            solve(*args,funding=custom,prune_continuation=True)
        self.assertEqual(calls,[])
        with self.assertRaises(ValueError):solve(*args,funding='slot-deficit-unknown')


if __name__=='__main__':unittest.main()
