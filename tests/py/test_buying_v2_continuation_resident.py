from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.phase_ledger import Purchase,OpenBook,SettleBook,SharedSettleBook,SetQuotes,Rent,EndTick,apply


class ResidentTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=case(2,2,2,2,lines=2)
        s=replace(s,incumbents=(0,0),completed_phases=('earlier',),arrears=.3)
        scenarios=[]
        for path in paths:
            events=[]
            for event in path.events:
                if isinstance(event,Purchase):event=replace(event,funded_demands=(6,6,2,2),fee_multiple=.5)
                events.append(event)
            events.extend((SetQuotes('new',(8.,9.)),OpenBook('shared'),SharedSettleBook('shared',(2,1),.2,((0,1),)),Rent('rent',.1,0.),EndTick('end',.15)))
            scenarios.append(replace(path,events=tuple(events)))
        return c,s,tuple(scenarios)

    def test_full_and_segmented_replay_equal_independent_ledger(self):
        c,s,paths=self.fixture();p=compile_calendar(c,s,paths)
        for scenario,path in enumerate(paths):
            allocations={i:(2,0,2,0) for i,e in enumerate(path.events) if isinstance(e,Purchase)}
            full=Resident(c,s,p);segmented=Resident(c,s,p);expected=s
            full.run(scenario,allocations)
            for i,event in enumerate(path.events):
                expected,_=apply(c,expected,event,allocations.get(i))
                segmented.run(scenario,{i:allocations[i]} if i in allocations else {},start=i,stop=i+1)
                self.assertEqual(segmented.snapshot(),expected)
            self.assertEqual(full.snapshot(),expected)
            self.assertEqual(full.initial,s)

    def test_forks_are_independent_and_failed_segment_is_atomic(self):
        c,s,paths=self.fixture();p=compile_calendar(c,s,paths);root=Resident(c,s,p)
        child=root.fork();child.run(0,{0:(2,0,2,0)},stop=2)
        self.assertEqual(root.snapshot(),s);self.assertIsNotNone(child.snapshot().book)
        failed=root.fork()
        # First purchase/books succeed, second allocation fails: nothing commits.
        with self.assertRaises(ValueError):failed.run(0,{0:(2,0,2,0),4:(100,0,2,0)})
        self.assertEqual(failed.snapshot(),s)
        with self.assertRaisesRegex(ValueError,'already completed'):child.run(0,{0:(0,0,0,0)},stop=1)
        self.assertEqual(root.snapshot(),s)
        for a,b in zip(root.data,child.data):
            if hasattr(a,'shape'):
                import numpy as np
                self.assertFalse(np.shares_memory(a,b))

    def test_invalid_ranges_allocations_and_empty_segment(self):
        c,s,paths=self.fixture();r=Resident(c,s,compile_calendar(c,s,paths))
        r.run(0,{},start=0,stop=0);self.assertEqual(r.snapshot(),s)
        for scenario in (-1,2,True,1.5):
            with self.assertRaises(ValueError):r.run(scenario,{})
        for start,stop in ((-1,0),(0,100),(2,1),(False,1)):
            with self.assertRaises(ValueError):r.run(0,{},start=start,stop=stop)
        for a in ({},{1:()},{False:(0,0,0,0)}, {0:(True,0,0,0)}, {0:(-1,0,0,0)}, {0:()}):
            with self.assertRaises(ValueError):r.run(0,a,stop=1)
        self.assertEqual(r.snapshot(),s)


if __name__=='__main__':unittest.main()
