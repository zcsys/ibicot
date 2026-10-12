from dataclasses import replace
import unittest
import numpy as np
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_ledger import Purchase
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_arena import BranchArena,ArenaResident,BranchLimit
from tools.buying_v2.continuation_branches import BranchRows
from tools.buying_v2.continuation_groups import Groups
from tools.buying_v2.continuation_funding_records import FundingRecords,FundingRecordLimit
from tools.buying_v2.continuation_resolve import resolve


def detail():
    return dict(rule='continuation-v2',referenceSuppliers=(0,0),referenceDemands=(1,1),jointQuantities=(1,1),jointGoods=4.,
        quoteVectors=tuple(dict(material=m,supplier=0,quantities=(1,1),goods=4.,conditionalValue=0.) for m in range(2)))


class ResolveTests(unittest.TestCase):
    def fixture(self,capacity=4):
        c,s,paths=case(1,1,1,2)
        paths=tuple(replace(p,events=tuple(replace(e,funded_demands=(0,0)) if isinstance(e,Purchase) else e for e in p.events)) for p in paths)
        program=compile_calendar(c,s,paths);arena=BranchArena(Resident(c,s,program),capacity);rows=BranchRows(arena,2)
        for i in range(2):rows.append((i,ArenaResident(arena,arena.create()),2**53+1))
        return arena,rows

    def test_group_clone_preserves_originals_and_shares_identical_record(self):
        arena,rows=self.fixture();before=[a[:2].copy() for a in arena.pool];records=FundingRecords()
        result=resolve(Groups(rows,(0,0))[0],0,(1,1),detail(),records)
        self.assertEqual(len(result),2);self.assertEqual(arena.active,4);self.assertEqual(records.count,2)
        for scenario,r,policy in result:
            self.assertEqual(policy,2**53+1);self.assertEqual(records.export(r.funding_node),{0:detail()})
            expected=rows[scenario][1].arena.export(rows[scenario][1].handle);expected.set_funded_demands(scenario,0,(1,1))
            np.testing.assert_array_equal(r.integers,expected.integers)
            self.assertEqual(r.snapshot(),rows[scenario][1].snapshot())
        for a,b in zip(before,arena.pool):np.testing.assert_array_equal(a,b[:2])

    def test_limits_report_completed_clones_and_records(self):
        arena,rows=self.fixture(3);records=FundingRecords()
        with self.assertRaises(BranchLimit):resolve(rows,0,(1,1),detail(),records)
        self.assertEqual(arena.active,3);self.assertEqual(records.count,2)
        arena,rows=self.fixture();records=FundingRecords(max_nodes=1)
        with self.assertRaises(FundingRecordLimit):resolve(rows,0,(1,1),detail(),records)
        self.assertEqual(arena.active,3);self.assertEqual(records.count,1)

    def test_invalid_demands_and_stale_source_rejected(self):
        arena,rows=self.fixture();records=FundingRecords()
        with self.assertRaises(ValueError):resolve(rows,0,(1.5,1),detail(),records)
        self.assertEqual(arena.active,2)
        rows[0][1].release();arena.create()
        with self.assertRaisesRegex(ValueError,'stale'):resolve(rows,0,(1,1),detail(),records)


if __name__=='__main__':unittest.main()
