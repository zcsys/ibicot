from dataclasses import replace
from itertools import product
import random
import unittest
import test_buying_v2_continuation_actions as helpers
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_actions import ActionLimit


class NativeActionTests(unittest.TestCase):
    def test_seeded_order_matches_independent_native_filter(self):
        rng=random.Random(9103)
        for trial in range(50):
            c,s,paths=case(3,2,1,1,lines=2)
            c=replace(c,slots=(rng.choice((2.,3.5,5.)),rng.choice((1.,2.5,4.))))
            s=replace(s,held=(rng.choice((.1,.5,1.0000000000000002)),rng.choice((.1,.9,1.5))),cash=rng.choice((0.,.3,4.,20.)))
            offers=tuple(replace(o,stock=rng.randrange(5),lot=rng.choice((1,2)),price=rng.choice((.1,.3,1.,3.))) for o in paths[0].events[0].offers)
            path=replace(paths[0],events=(replace(paths[0].events[0],offers=offers),))
            expected=[]
            for a in product(*(range(0,o.stock+1,o.lot) for o in offers)):
                inventory=list(s.held);payment=0.
                for o,q in zip(offers,a):inventory[o.material]+=q;payment+=q*o.price
                if payment<=s.cash and all(h<=max(old,slot) for h,old,slot in zip(inventory,s.held,c.slots)):expected.append(a)
            frame=helpers.ActionTests().frame(c,s,path);actual=[]
            while True:
                try:row=frame.next(max_prefixes=1)
                except ActionLimit:continue
                if row is None:break
                actual.append(row)
            self.assertEqual(actual,expected,trial)
            self.assertEqual(tuple(frame.inventory),s.held)

    def test_pruning_and_forks_restore_saved_inventory_exactly(self):
        c,s,paths=case(3,2,1,1)
        c=replace(c,slots=(3.5,3.5));s=replace(s,held=(.1,.1))
        frame=helpers.ActionTests().frame(c,s,paths[0]);actual=[]
        def prune(prefix,budget):return (len(prefix)==1 and prefix[0]==1),0
        while (row:=frame.next(max_prefixes=10000,prune=prune)) is not None:
            actual.append(row)
            clone=frame.fork()
            self.assertIsNot(clone.inventory,frame.inventory)
            before=frame.inventory.copy();clone.next(max_prefixes=10000,prune=prune)
            self.assertTrue((frame.inventory==before).all())
        expected=[]
        offers=paths[0].events[0].offers
        for row in product(range(4),repeat=4):
            held=list(s.held)
            for o,q in zip(offers,row):held[o.material]+=q
            if row[0]!=1 and all(q<=3.5 for q in held):expected.append(row)
        self.assertEqual(actual,expected)
        self.assertEqual(tuple(frame.inventory),s.held)
