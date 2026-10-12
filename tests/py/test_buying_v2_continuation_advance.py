import unittest
import numpy as np
from test_buying_v2_information_history import fixture,scenario
from tools.buying_v2.phase_ledger import OpenBook,SettleBook
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_arena import BranchArena,ArenaResident
from tools.buying_v2.continuation_branches import BranchRows
from tools.buying_v2.continuation_history import NumericHistory,HistoryLimit
from tools.buying_v2.continuation_advance import advance


class AdvanceTests(unittest.TestCase):
    def fixture(self,**limits):
        c,s,b=fixture();paths=tuple(scenario((OpenBook('first'),SettleBook('first',(q,)),OpenBook('next'),SettleBook('next',(1-q,)),b)) for q in (0,1))
        p=compile_calendar(c,s,paths);r=Resident(c,s,p);arena=BranchArena(r,2);rows=BranchRows(arena,2)
        for i in range(2):rows.append((i,ArenaResident(arena,arena.create()),0))
        return rows,NumericHistory(p,**limits),dict(transitions=0),r

    def test_batch_and_segmented_advance_match_resident_observations(self):
        for segmented in (False,True):
            rows,h,stats,template=self.fixture()
            if segmented:self.assertEqual(advance(rows,0,2,h,stats),2)
            self.assertEqual(advance(rows,2 if segmented else 0,5,h,stats),4)
            self.assertEqual(stats['transitions'],8)
            for scenario,r,_ in rows:
                reference=template.fork();reference.run(scenario,{},stop=4,observe=True)
                self.assertEqual(r.snapshot(),reference.snapshot());self.assertEqual(r.history_count,4)
                for a,b in zip(h.export(r.history_node),reference.observations):
                    for x,y in zip(a,b):np.testing.assert_array_equal(x,y)
            self.assertEqual(advance(rows,4,5,h,stats),4);self.assertEqual(stats['transitions'],8)

    def test_history_capacity_reports_completed_work(self):
        rows,h,stats,_=self.fixture(max_nodes=1)
        with self.assertRaises(HistoryLimit) as cm:advance(rows,0,5,h,stats)
        self.assertEqual(h.count,1);self.assertEqual(stats['transitions'],0)
        self.assertEqual(cm.exception.diagnostics['requiredNodes'],2)
        self.assertEqual(rows[0][1].history_count,0)

    def test_nonfinite_emitted_equity_is_not_interned(self):
        rows,h,stats,_=self.fixture()
        rows.arena.pool[0][0,0]=1.7e308
        rows.arena.pool[4][0,0]=1.7e308
        with self.assertRaisesRegex(ValueError,'observation arrays'):advance(rows,0,1,h,stats)
        self.assertEqual(h.count,1);self.assertEqual(stats['transitions'],0)

    def test_stale_handles_and_incomplete_history_fail(self):
        rows,h,stats,_=self.fixture()
        with self.assertRaisesRegex(ValueError,'history'):advance(rows,1,5,h,stats)
        rows[0][1].release();rows.arena.create()
        with self.assertRaisesRegex(ValueError,'stale'):advance(rows,0,5,h,stats)


if __name__=='__main__':unittest.main()
