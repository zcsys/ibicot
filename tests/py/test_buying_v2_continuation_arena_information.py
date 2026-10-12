from dataclasses import replace
import unittest
import numpy as np
from test_buying_v2_information_history import fixture,scenario
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_arena import BranchArena,ArenaResident
from tools.buying_v2.continuation_branches import BranchRows
from tools.buying_v2.continuation_information import History,group_decisions
from tools.buying_v2.continuation_arena_information import group_arena_decisions


class ArenaInformationTests(unittest.TestCase):
    def fixture(self):
        c,s,b=fixture();paths=(scenario((b,)),scenario((replace(b,fee_multiple=3.),)))
        p=compile_calendar(c,s,paths);arena=BranchArena(Resident(c,s,p),2);rows=BranchRows(arena,2)
        for i in range(2):rows.append((i,ArenaResident(arena,arena.create()),0))
        return arena,rows,History()

    def compare(self,rows,h,neutral=False):
        branches=list(rows)
        expected=group_decisions([r for _,r,_ in branches],[s for s,_,_ in branches],0,[r.history_node for _,r,_ in branches],h,neutral=neutral)
        before=[a.copy() for a in rows.arena.pool]
        self.assertEqual(tuple(group_arena_decisions(rows,0,h,neutral=neutral)),expected)
        for a,b in zip(before,rows.arena.pool):np.testing.assert_array_equal(a,b)

    def test_live_state_history_offers_and_neutral_mode_match(self):
        arena,rows,h=self.fixture();self.compare(rows,h);self.compare(rows,h,True)
        arena.pool[8][1].fill(123);arena.pool[10][1].fill(123);self.compare(rows,h,True)
        arena.pool[0][1,5]+=1;self.compare(rows,h,True)
        arena.pool[0][1,5]-=1
        rows[1][1].history_node=h.append(0,dict(event='test',label='test'));self.compare(rows,h,True)

    def test_invalid_history_event_and_stale_handle_rejected(self):
        arena,rows,h=self.fixture()
        for index in (-1,True,1):
            with self.assertRaises(ValueError):group_arena_decisions(rows,index,h)
        rows[0][1].history_node=999
        with self.assertRaisesRegex(ValueError,'unknown history'):group_arena_decisions(rows,0,h)
        rows[0][1].history_node=0;rows[0][1].release();arena.create()
        with self.assertRaisesRegex(ValueError,'stale'):group_arena_decisions(rows,0,h)


if __name__=='__main__':unittest.main()
