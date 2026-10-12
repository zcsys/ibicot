import unittest
from dataclasses import replace
import numpy as np
from test_buying_v2_information_history import fixture,scenario
from tools.buying_v2.phase_ledger import OpenBook,SettleBook,SharedSettleBook
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_history import NumericHistory,HistoryLimit,group_observed
from tools.buying_v2.continuation_information import History
from tools.buying_v2.continuation_observation import decode


class NumericHistoryTests(unittest.TestCase):
    def fixture(self,hidden=False):
        c,s,b=fixture()
        if hidden:
            s=replace(s,finished=(0,),finished_basis=(0.,))
            paths=tuple(scenario((OpenBook('empty'),SharedSettleBook('empty',(d,),groups=((0,),)),b)) for d in (0,9))
        else:
            paths=tuple(scenario((OpenBook('early'),SettleBook('early',(d,)),OpenBook('later'),SettleBook('later',(1-d,)),b)) for d in (0,1))
        p=compile_calendar(c,s,paths);rs=[Resident(c,s,p) for _ in paths];index=len(paths[0].events)-1
        for j,r in enumerate(rs):r.run(j,{},stop=index,observe=True)
        return p,rs,index

    def test_direct_grouping_matches_reference_history_partition(self):
        for hidden in (False,True):
            p,rs,index=self.fixture(hidden);h=NumericHistory(p);reference=History()
            ids=[h.trace(r.observations) for r in rs]
            expected=[reference.trace(tuple(decode(x,r.labels) for x in r.observations)) for r in rs]
            self.assertEqual(ids[0]==ids[1],expected[0]==expected[1])
            self.assertEqual(group_observed(rs,[0,1],index,h),(0,0) if hidden else (0,1))
            before=h.diagnostics();self.assertEqual(h.trace(rs[0].observations),ids[0]);self.assertEqual(h.diagnostics(),before)
            parent=h.extend(0,rs[0].observations[:1]);self.assertEqual(h.extend(parent,rs[0].observations[1:]),ids[0])

    def test_every_event_record_matches_dictionary_history_equivalence(self):
        import test_buying_v2_continuation_resident as fixtures
        from tools.buying_v2.phase_ledger import Purchase
        c,s,paths=fixtures.ResidentTests().fixture();p=compile_calendar(c,s,paths)
        h=NumericHistory(p);reference=History();pairs=[]
        for j,path in enumerate(paths):
            r=Resident(c,s,p)
            r.run(j,{i:(2,0,2,0) for i,e in enumerate(path.events) if isinstance(e,Purchase)},observe=True)
            for stop in range(len(r.observations)+1):
                records=r.observations[:stop]
                pairs.append((h.trace(records),reference.trace(tuple(decode(x,r.labels) for x in records))))
        for a in pairs:
            for b in pairs:self.assertEqual(a[0]==b[0],a[1]==b[1])

    def test_capacity_failure_rolls_back_live_arena_and_reports_work(self):
        p,rs,index=self.fixture()
        for kwargs in ({'max_nodes':2},{'max_integers':6},{'max_floats':5}):
            h=NumericHistory(p,**kwargs);before=h.diagnostics()
            with self.assertRaises(HistoryLimit) as cm:h.trace(rs[0].observations)
            self.assertEqual(h.diagnostics(),before)
            self.assertGreater(cm.exception.diagnostics['requiredNodes'],1)
            self.assertIn('processedRecords',cm.exception.diagnostics)
            first=h.trace(rs[0].observations[:1]);self.assertEqual(first,1)
            self.assertEqual(h.trace(rs[0].observations[:1]),first)

    def test_single_record_limits_preserve_live_counters(self):
        p,rs,index=self.fixture();record=rs[0].observations[:1]
        for kwargs in ({'max_nodes':1},{'max_integers':1},{'max_floats':1}):
            h=NumericHistory(p,**kwargs);before=h.diagnostics()
            with self.assertRaises(HistoryLimit) as cm:h.extend(0,record)
            self.assertEqual(h.diagnostics(),before)
            self.assertEqual(cm.exception.diagnostics['processedRecords'],0)

    def test_complete_prefix_required(self):
        p,rs,index=self.fixture();h=NumericHistory(p)
        rs[0].observation_positions=(1,)*index
        with self.assertRaisesRegex(ValueError,'complete observed prefix'):group_observed(rs,[0,1],index,h)
        self.assertEqual(h.count,1)

    def test_payload_validation_aliasing_and_numeric_equality(self):
        p,rs,index=self.fixture();h=NumericHistory(p);record=rs[0].observations[0]
        copied=tuple(a.copy() for a in record);node=h.trace((copied,));copied[1][0]+=1
        self.assertEqual(h.trace((record,)),node)
        for bad in ((record[0][:-1],record[1]),(record[0],record[1][:-1]),(record[0].astype(float),record[1])):
            with self.assertRaises(ValueError):h.trace((bad,))
        with self.assertRaises(ValueError):h.extend(999,())
        self.assertEqual(h.extend(node,()),node)
        zero=tuple(a.copy() for a in record);zero[1][2]=-0.
        self.assertEqual(h.trace((zero,)),node)


if __name__=='__main__':unittest.main()
