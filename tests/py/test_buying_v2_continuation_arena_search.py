import unittest
import test_buying_v2_continuation_search as verification
from test_buying_v2_continuation_differential import cases
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_search import solve,SearchLimit


class ArenaSearchTests(unittest.TestCase):
    def test_all_seeded_cases_match_independent_oracle_and_release_rows(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                result=verification.SearchTests().compare(c,s,paths,supply=supply,funding='continuation',storage='arena')
                self.assertEqual(result['diagnostics']['branchArena']['active'],0)
                self.assertGreater(result['diagnostics']['branchArena']['peakBranches'],0)

    def test_capacity_limit_reports_no_partial_policy(self):
        c,s,paths=case(1,2,2,2)
        for capacity in (1,2,3):
            with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,funding='continuation',storage='arena',max_branches=capacity)
            self.assertEqual(cm.exception.diagnostics['branchArena']['active'],capacity)
            self.assertNotIn('leaves',cm.exception.diagnostics)

    def test_reuse_requires_peak_capacity_not_cumulative_allocations(self):
        c,s,paths=case(1,2,2,2)
        r=solve(c,s,paths,funding='continuation',storage='arena')
        stats=r['diagnostics']['branchArena'];self.assertGreater(stats['allocations'],stats['peakBranches'])
        limited=solve(c,s,paths,funding='continuation',storage='arena',max_branches=stats['peakBranches'])
        self.assertEqual(limited['expectedValue'],r['expectedValue'])
        self.assertEqual([x['policy'] for x in limited['leaves']],[x['policy'] for x in r['leaves']])
        self.assertEqual(limited['diagnostics']['branchArena']['active'],0)


if __name__=='__main__':unittest.main()
