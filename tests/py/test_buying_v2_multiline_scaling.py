from dataclasses import asdict
import json
from pathlib import Path
import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve
from test_buying_v2_prefix_pruning import semantic


class MultilineScalingTests(unittest.TestCase):
    def test_shared_input_structure_and_analytical_returns(self):
        for periods,outcomes,expected in ((1,1,13.),(2,1,26.),(1,2,2.),(2,2,8.5)):
            args=case(1,1,periods,outcomes,lines=2)
            c,s,paths=args
            self.assertEqual(c.slots,(3,1))
            self.assertEqual(tuple(l.recipe for l in c.lines),((1,1),(2,0)))
            self.assertEqual(paths[0].events[0].active_lines,(0,1))
            for funding in ('slot-deficit-v1','continuation'):
                base=solve(*args,funding=funding)
                self.assertAlmostEqual(base['expectedValue'],expected)
                optimized=solve(*args,funding=funding,allocation_search='feasible-prefix',prune_prefix=True,
                    prune_continuation=True,continuation_bound_costs=True,closing_search='compiled-certified-boxes',
                    closing_memo_size=4096,closing_proposal_memo_size=4096,funding_memo_size=4096,
                    shared_first_batches=16,shared_bound_memo_size=4096)
                actual=semantic(optimized);reference=semantic(base)
                actual.pop('allocationSearch');reference.pop('allocationSearch')
                self.assertEqual(actual,reference)
                self.assertEqual(optimized['leaves'][0]['trace'][0]['outputs'],(1,1))

    def test_original_case_unchanged_and_bad_line_counts_rejected(self):
        self.assertEqual(case(2,2,2,2),case(2,2,2,2,lines=1))
        for lines in (0,3,True,1.5):
            with self.assertRaises(ValueError):case(1,1,1,1,lines=lines)


if __name__=='__main__':unittest.main()
