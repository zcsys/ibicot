import unittest,random
from dataclasses import replace
from itertools import product
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_actions import AllocationFrame,ActionLimit


class ActionTests(unittest.TestCase):
    def frame(self,c,s,path):return AllocationFrame(Resident(c,s,compile_calendar(c,s,(path,))),0,0)

    def test_order_matches_independent_cartesian_filter(self):
        rng=random.Random(352)
        for trial in range(60):
            c,s,paths=case(3,2,1,1,lines=2)
            s=replace(s,cash=rng.choice((0.,.3,4.,20.,100.)),held=(rng.randrange(5),rng.randrange(4)))
            event=paths[0].events[0]
            offers=tuple(replace(o,lot=rng.choice((1,2,3)),stock=rng.randrange(7),price=rng.choice((.1,.3,2.,7.))) for o in event.offers)
            path=replace(paths[0],events=(replace(event,offers=offers),))
            frame=self.frame(c,s,path);expected=[]
            ranges=[range(0,min(o.stock,max(0,c.slots[o.material]-s.held[o.material]))+1,o.lot) for o in offers]
            for a in product(*ranges):
                bought=[0]*len(s.held);goods=0.
                for o,q in zip(offers,a):bought[o.material]+=q;goods+=q*o.price
                if goods<=s.cash and all(q<=max(0,cap-held) for q,cap,held in zip(bought,c.slots,s.held)):expected.append(a)
            actual=[]
            while True:
                a=frame.next(max_prefixes=10000)
                if a is None:break
                actual.append(a)
            self.assertEqual(actual,expected,trial)
            self.assertEqual(frame.diagnostics()['yieldedAllocations'],len(expected))
            self.assertIsNone(frame.next(max_prefixes=0))

    def test_budget_resume_and_fork_preserve_complete_traversal(self):
        c,s,paths=case(2,2,1,1);path=paths[0];full=self.frame(c,s,path);small=self.frame(c,s,path)
        expected=[]
        while (a:=full.next(max_prefixes=10000)) is not None:expected.append(a)
        actual=[];limits=0
        while True:
            try:a=small.next(max_prefixes=1)
            except ActionLimit as exc:
                limits+=1;self.assertEqual(exc.diagnostics['callPrefixes'],1);continue
            if a is None:break
            actual.append(a)
            if len(actual)==2:
                fork=small.fork();self.assertEqual(fork.next(max_prefixes=10000),expected[2])
        self.assertEqual(actual,expected);self.assertGreater(limits,0)
        self.assertEqual(small.diagnostics()['visitedPrefixes'],full.diagnostics()['visitedPrefixes'])

    def test_empty_offers_and_zero_allowance(self):
        c,s,paths=case(1,1,1,1);event=replace(paths[0].events[0],offers=(),reliability=())
        frame=self.frame(c,s,replace(paths[0],events=(event,)))
        self.assertEqual(frame.next(max_prefixes=0),());self.assertIsNone(frame.next(max_prefixes=0))
        frame=self.frame(c,s,paths[0]);before=frame.diagnostics()
        with self.assertRaises(ActionLimit):frame.next(max_prefixes=0)
        self.assertEqual(frame.diagnostics(),before)
        for limit in (-1,True,1.5):
            with self.assertRaises(ValueError):frame.next(max_prefixes=limit)


if __name__=='__main__':unittest.main()
