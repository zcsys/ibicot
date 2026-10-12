import unittest
import numpy as np
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_arena import BranchArena,ArenaResident
from tools.buying_v2.continuation_branches import BranchRows
from tools.buying_v2.continuation_results import Results,ResultLimit
from tools.buying_v2.continuation_terminal import capture
from tools.buying_v2.phase_ledger import horizon_value


class TerminalCaptureTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=case(1,1,1,2);p=compile_calendar(c,s,paths);arena=BranchArena(Resident(c,s,p),len(paths));rows=BranchRows(arena,len(paths))
        for i in range(len(paths)):
            r=ArenaResident(arena,arena.create());r.history_node=2**53+1;r.funding_node=3
            rows.append((i,r,2**53+2))
        return s,paths,rows

    def test_capture_matches_ledger_value_and_preserves_state(self):
        s,paths,rows=self.fixture();result=Results();before=[a.copy() for a in rows.arena.pool]
        leaves,weighted=capture(rows,s,result)
        self.assertEqual(list(leaves),list(range(len(paths))))
        for i,path in enumerate(paths):
            expected=horizon_value(s,s,path.input_values,path.finished_values)
            self.assertEqual(result.read(i),(i,2**53+2,2**53+1,3,expected))
            self.assertEqual(weighted[i],path.probability*expected)
        for a,b in zip(before,rows.arena.pool):np.testing.assert_array_equal(a,b)

    def test_capacity_failure_retains_completed_records(self):
        s,paths,rows=self.fixture();self.assertGreater(len(paths),1);result=Results(1)
        with self.assertRaises(ResultLimit) as cm:capture(rows,s,result)
        self.assertEqual(result.count,1);self.assertEqual(cm.exception.diagnostics['requiredRecords'],2)
        self.assertEqual(result.read(0)[0],0)

    def test_stale_and_unsettled_rows_reject_capture(self):
        s,paths,rows=self.fixture();result=Results()
        rows.arena.pool[11][0,0]=0
        with self.assertRaisesRegex(ValueError,'unsettled'):capture(rows,s,result)
        self.assertEqual(result.count,0)
        rows.arena.pool[11][0,0]=-1;rows[0][1].release();rows.arena.create()
        with self.assertRaisesRegex(ValueError,'stale'):capture(rows,s,result)


if __name__=='__main__':unittest.main()
