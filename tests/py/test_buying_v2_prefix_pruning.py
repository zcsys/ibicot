import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve,PhaseSearchLimit


def semantic(result):
    ignored=('enumeratedNodes','prefixSearch','transitionCache','boundAudit','fundingMemo','fundingQueries','fundingObservations','closingSolver')
    return {k:v for k,v in result.items() if k not in ignored}


class PrefixPruningTests(unittest.TestCase):
    def test_complete_policies_and_accounts_match(self):
        total=0
        for dims in ((1,2,2,2),(2,2,2,2),(2,2,1,1),(4,2,2,2)):
            args=case(*dims)
            for funding in ('continuation','continuation-transfer-neutral'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    kw=dict(funding=funding,supply=supply,allocation_search='feasible-prefix',
                        closing_search='compiled-certified-boxes',closing_memo_size=4096,funding_memo_size=4096,
                        prune_continuation=True,continuation_bound_costs=True,max_nodes=100000,max_prefix_nodes=100000)
                    before=solve(*args,**kw)
                    after=solve(*args,**kw,prune_prefix=True)
                    self.assertEqual(semantic(before),semantic(after))
                    total+=after['prefixSearch']['boundPrunedPrefixes']
        self.assertGreater(total,0)

    def test_fee_and_income_counterexamples_preserve_complete_results(self):
        from tools.buying_v2.fee_boundary_study import fee_case,income_case
        for args in (fee_case(7.,3.,3),income_case(.5)):
            kw=dict(funding='continuation',allocation_search='feasible-prefix',max_prefix_nodes=100000,
                    prune_continuation=True,continuation_bound_costs=True)
            self.assertEqual(semantic(solve(*args,**kw)),semantic(solve(*args,**kw,prune_prefix=True)))

    def test_requires_known_funding_and_charges_bound_work(self):
        args=case(2,2,2,2)
        for kw in (dict(funding=frozen_funding,allocation_search='feasible-prefix'),dict(funding='continuation')):
            with self.assertRaises(ValueError):solve(*args,**kw,prune_prefix=True)
        with self.assertRaises(PhaseSearchLimit) as caught:
            solve(*args,funding='continuation',allocation_search='feasible-prefix',prune_prefix=True,max_prefix_nodes=30)
        d=caught.exception.diagnostics
        self.assertGreater(d['prefixSearch']['boundEvaluations'],0)
        self.assertGreater(d['prefixSearch']['visitedPrefixes']+d['prefixSearch']['boundEvaluations'],30)


if __name__=='__main__':unittest.main()
