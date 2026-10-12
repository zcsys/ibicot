import unittest
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.fee_boundary_study import fee_case,income_case

class TransitionCacheTests(unittest.TestCase):
    def test_bounded_cache_preserves_full_results_and_node_budget(self):
        for args in (fee_case(7.,3.,3),income_case(.5)):
            for mode in ('continuation','continuation-transfer-neutral'):
                base=solve(*args,funding=mode,transition_cache_size=0)
                base_stats=base.pop('transitionCache')
                self.assertEqual(base_stats['hits'],0)
                for capacity in (1,16,4096):
                    cached=solve(*args,funding=mode,transition_cache_size=capacity)
                    stats=cached.pop('transitionCache')
                    self.assertEqual(base,cached)
                    self.assertLessEqual(stats['peakEntries'],capacity)
                    if capacity==4096:self.assertGreater(stats['hits'],0)
                for capacity in (0,4096):
                    with self.assertRaisesRegex(ValueError,'node limit'):
                        solve(*args,funding=mode,max_nodes=1,transition_cache_size=capacity)

    def test_invalid_capacity_and_run_isolation(self):
        args=income_case(.5)
        for size in (-1,1.5,True):
            with self.assertRaises(ValueError):solve(*args,funding='continuation',transition_cache_size=size)
        first=solve(*args,funding='continuation')
        expected=solve(*args,funding='continuation')
        # The shared opening-book transition is cached, but each exposed
        # trace mapping remains independent.
        left=first['leaves'][0]['trace'][2];right=first['leaves'][1]['trace'][2]
        self.assertIsNot(left,right)
        old_cash=right['cash'];left['cash']=-100.
        self.assertEqual(right['cash'],old_cash)
        first['leaves'][0]['trace'][0]['cash']=-100.
        self.assertEqual(expected,solve(*args,funding='continuation'))

if __name__=='__main__':unittest.main()
