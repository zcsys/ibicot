"""Interaction checks for exact pruning, closing bounds and memoization."""
from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.fee_boundary_study import fee_case,income_case


def outcome(result):
    # Search changes diagnostic counts. Preserve full terminal states and traces.
    return result['expectedValue'],result['leaves'],result['fundingRule'],result['supplyMode']


class CombinedPlannerTests(unittest.TestCase):
    def test_policies_accounts_and_information_match_ordinary_event_tree(self):
        for args in (case(2,2,2,2),fee_case(7.,3.,3),income_case(.5)):
            for funding in ('continuation','continuation-transfer-neutral'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    kw=dict(funding=funding,supply=supply,funding_memo_size=4096,
                            max_nodes=50000,max_prefix_nodes=100000)
                    expected=solve(*args,**kw)
                    actual=solve(*args,**kw,closing_search='compiled-fast-cost-boxes',closing_memo_size=4096,
                                 prune_continuation=True,continuation_bound_costs=True)
                    self.assertEqual(outcome(expected),outcome(actual))

    def test_four_unit_case_completes_original_budget(self):
        result=solve(*case(4,2,2,2),funding='continuation',funding_memo_size=4096,
                     max_nodes=4000,max_prefix_nodes=16000,closing_search='compiled-fast-cost-boxes',
                     closing_memo_size=4096,prune_continuation=True,continuation_bound_costs=True)
        self.assertEqual(result['expectedValue'],13.)
        self.assertEqual(result['leaves'][0]['trace'][0]['allocation'],(4,0,4,0))
        self.assertLessEqual(result['enumeratedNodes'],4000)
        self.assertLessEqual(result['closingSolver']['boxes']+result['prefixSearch']['visitedPrefixes'],16000)
        self.assertGreater(result['boundAudit']['pruned'],0)
        self.assertGreater(result['closingSolver']['memo']['hits'],0)

    def test_malformed_future_event_still_rejected(self):
        c,s,paths=case(2,2,2,2)
        paths=tuple(replace(p,events=p.events[:-1]+(replace(p.events[-1],label='wrong'),)) for p in paths)
        with self.assertRaises(ValueError):
            solve(c,s,paths,funding='continuation',closing_search='compiled-fast-cost-boxes',
                  closing_memo_size=4096,prune_continuation=True,continuation_bound_costs=True)


if __name__=='__main__':unittest.main()
