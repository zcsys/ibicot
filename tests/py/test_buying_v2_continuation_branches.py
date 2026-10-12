import unittest
import test_buying_v2_continuation_arena as arena_tests
from tools.buying_v2.continuation_arena import BranchArena,ArenaResident
from tools.buying_v2.continuation_branches import BranchRows


class BranchRowsTests(unittest.TestCase):
    def fixture(self):
        _,_,_,r=arena_tests.ArenaTests().fixture();arena=BranchArena(r,2)
        return arena,ArenaResident(arena,arena.create())

    def test_numeric_rows_preserve_metadata_and_identity(self):
        arena,r=self.fixture();rows=BranchRows(arena,1);r.history_node=9;rows.append((0,r,2**53+1))
        scenario,view,policy=rows[0]
        self.assertEqual((scenario,view.handle,policy),(0,r.handle,2**53+1))
        self.assertIsNot(view,r);view.history_count=7;self.assertEqual(r.history_count,7)
        self.assertEqual(view.history_node,9);self.assertEqual(rows.rows.nbytes,32)
        self.assertEqual(len(list(rows)),1)
        with self.assertRaises(ValueError):rows.append((0,r,0))
        self.assertEqual(len(rows),1)

    def test_released_handles_cannot_alias_reused_rows(self):
        arena,r=self.fixture();rows=BranchRows(arena,1);rows.append((0,r,0));r.release();arena.create()
        with self.assertRaisesRegex(ValueError,'stale'):rows[0]

    def test_uninterned_observations_and_invalid_identity_rejected(self):
        arena,r=self.fixture();rows=BranchRows(arena,1)
        for scenario,policy in ((True,0),(-1,0),(999,0),(0,2**63),(0,1.5)):
            with self.assertRaises(ValueError):rows.append((scenario,r,policy))
        r.observation_positions=(0,)
        with self.assertRaisesRegex(ValueError,'interned'):rows.append((0,r,0))
        self.assertEqual(len(rows),0)
        _,foreign=self.fixture()
        with self.assertRaises(ValueError):rows.append((0,foreign,0))


if __name__=='__main__':unittest.main()
