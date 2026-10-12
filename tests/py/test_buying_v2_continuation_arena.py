import unittest
import numpy as np
import test_buying_v2_continuation_resident as fixtures
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_arena import BranchArena,BranchLimit,ArenaResident
from tools.buying_v2.phase_ledger import Purchase,apply


class ArenaTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=fixtures.ResidentTests().fixture();p=compile_calendar(c,s,paths)
        return c,s,paths,Resident(c,s,p,supply='persistent-arrivals')

    def test_typed_steps_match_resident_state_supply_and_observations(self):
        c,s,paths,r=self.fixture();arena=BranchArena(r,2);handle=arena.create()
        for i,event in enumerate(paths[0].events):
            allocation=(2,0,2,0) if isinstance(event,Purchase) and i==0 else ((0,0,0,0) if isinstance(event,Purchase) else None)
            records=arena.step(handle,0,i,allocation)
            r.run(0,{i:allocation} if allocation is not None else {},start=i,stop=i+1,observe=True)
            exported=arena.export(handle)
            self.assertEqual(exported.snapshot(),r.snapshot());self.assertTrue(np.array_equal(exported.integers,r.integers))
            for a,b in zip(records[0],r.observations[-1]):self.assertTrue(np.array_equal(a,b))

    def test_fork_release_and_stale_generation(self):
        c,s,paths,r=self.fixture();arena=BranchArena(r,2);root=arena.create();child=arena.fork(root)
        arena.step(child,0,0,(2,0,2,0));self.assertEqual(arena.export(root).snapshot(),s)
        with self.assertRaises(BranchLimit) as cm:arena.fork(root)
        self.assertEqual(cm.exception.diagnostics['active'],2)
        arena.release(child);fresh=arena.create();self.assertEqual(fresh[0],child[0]);self.assertNotEqual(fresh[1],child[1])
        for operation in (arena.export,arena.release,arena.fork):
            with self.assertRaisesRegex(ValueError,'stale'):operation(child)
        self.assertEqual(arena.export(fresh).snapshot(),s);self.assertEqual(arena.diagnostics()['peakBranches'],2)

    def test_numeric_search_metadata_forks_releases_and_rejects_stale_access(self):
        _,_,_,r=self.fixture();arena=BranchArena(r,2)
        parent=ArenaResident(arena,arena.create())
        parent.history_node=2**53+1;parent.history_count=3;parent.funding_node=7
        child=parent.fork()
        self.assertEqual((child.history_node,child.history_count,child.funding_node),(2**53+1,3,7))
        child.history_node=9;self.assertEqual(parent.history_node,2**53+1)
        for bad in (-1,2**63,True,1.5):
            with self.assertRaises(ValueError):child.history_count=bad
            self.assertEqual(child.history_count,3)
        old=child.handle;child.release()
        self.assertEqual(arena.search_metadata[old[0]].tolist(),[0,0,0])
        fresh=ArenaResident(arena,arena.create())
        self.assertEqual((fresh.history_node,fresh.history_count,fresh.funding_node),(0,0,0))
        with self.assertRaisesRegex(ValueError,'stale'):child.history_node
        with self.assertRaisesRegex(ValueError,'stale'):child.funding_node=2
        self.assertEqual(arena.diagnostics()['searchMetadataBytes'],48)

    def test_failed_step_and_export_cannot_mutate_stored_branch(self):
        c,s,paths,r=self.fixture();arena=BranchArena(r,1);handle=arena.create()
        before=[a.copy() for a in arena.pool]
        with self.assertRaises(ValueError):arena.step(handle,0,0,(100,0,0,0))
        for a,b in zip(before,arena.pool):self.assertTrue(np.array_equal(a,b))
        exported=arena.export(handle);exported.data[0][0]=0.;exported.integers[:]=0
        self.assertEqual(arena.export(handle).snapshot(),s)
        for bad in ((True,1),(-1,1),(0,999),[0,1]):
            with self.assertRaises(ValueError):arena.export(bad)


if __name__=='__main__':unittest.main()
