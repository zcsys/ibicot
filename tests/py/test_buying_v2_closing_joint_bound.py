from dataclasses import replace
from itertools import product
import math
import random
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.closing_joint_bound import bounder
from tools.buying_v2.closing_cost_bound import bounder as old_bounder
from tools.buying_v2.phase_ledger import apply, horizon_value


class JointClosingBoundTests(unittest.TestCase):
    def fixture(self,capacity=2):
        c,s,paths=case(capacity,2,1,1,lines=2)
        e=replace(paths[0].events[0],funded_demands=(3*capacity,)*2+(capacity,)*2)
        p=tuple((x.probability,replace(x,events=x.events[1:])) for x in paths)
        return c,s,e,p

    def test_root_bound_charges_both_lines_and_shared_material(self):
        c,s,e,p=self.fixture(8);problem=prepare(c,s,s,e,p)
        hi=tuple(o.stock for o in e.offers);lo=(0,)*len(hi)
        actual=bounder(problem,s,s,p)(lo,hi)
        self.assertEqual(actual['batchStates'],81)
        self.assertGreaterEqual(actual['upperValue'],104.)
        self.assertLess(actual['upperValue'],104.+1e-9)
        self.assertGreater(old_bounder(problem,s,s,p)(lo,hi),actual['upperValue']+1.)

    def test_every_matching_basket_in_random_boxes_is_bounded(self):
        rng=random.Random(2026101207)
        checked=0
        for trial in range(30):
            c,s,e,p=self.fixture(1)
            scale=rng.choice((1e-8,.1,1.,1e8))
            c=replace(c,lines=tuple(replace(line,conversion=rng.choice((0.,.1,1.))*scale) for line in c.lines))
            s=replace(s,cash=rng.choice((1.,10.,100.))*scale,held=(rng.randrange(2),0),
                      basis=(rng.choice((0.,.1,100.))*scale,0.),quotes=(10.*scale,12.*scale),incumbents=(0,0))
            e=replace(e,offers=tuple(replace(o,price=rng.choice((.1,1.,3.))*scale) for o in e.offers),
                      fee_unit_cost=scale,fee_multiple=rng.choice((0.,2.)))
            p=tuple((w,replace(path,events=(path.events[0],replace(path.events[1],demand=(rng.randrange(2),rng.randrange(2)),fee_income=.1*scale)),
                 input_values=tuple(tuple(rng.choice((0.,.1,.5))*scale for _ in table) for table in path.input_values),
                 finished_values=tuple(tuple(rng.choice((0.,.2,.6))*scale for _ in table) for table in path.finished_values))) for w,path in p)
            problem=prepare(c,s,s,e,p);bound=bounder(problem,s,s,p)
            hi=tuple(min(o.stock,c.slots[o.material]-s.held[o.material]) for o in e.offers)
            for _ in range(8):
                lo=tuple(rng.randrange(q+1) for q in hi);top=bound(lo,hi)['upperValue']
                for allocation in product(*(range(a,b+1) for a,b in zip(lo,hi))):
                    try:final,_=apply(c,s,e,allocation)
                    except ValueError as exc:
                        self.assertIn(str(exc),('infeasible procurement allocation','production would exceed physical storage'))
                        continue
                    for event in p[0][1].events:final,_=apply(c,final,event)
                    value=horizon_value(s,final,p[0][1].input_values,p[0][1].finished_values)
                    self.assertGreaterEqual(top,value,(trial,allocation,lo,hi));checked+=1
        self.assertGreater(checked,100)

    def test_lots_yields_and_posterior_values_against_independent_ledger(self):
        c,s,e,p=self.fixture(2)
        c=replace(c,storage=30.,lines=(replace(c.lines[0],output_qty=2,output_values=(0.,)*5),c.lines[1]))
        e=replace(e,offers=tuple(replace(o,lot=2) if o.material==0 else o for o in e.offers))
        path=p[0][1]
        p=((.25,replace(path,events=(path.events[0],replace(path.events[1],demand=(1,0))),
                       input_values=((0.,.1,.9,.2,.5,.1,.8),(0.,.8,.1)))),
           (.75,replace(path,events=(path.events[0],replace(path.events[1],demand=(4,2),fee_income=.2)))))
        for scale in (5e-324,1.,1e100):
            scaled_c=replace(c,lines=tuple(replace(line,conversion=line.conversion*scale) for line in c.lines))
            state=replace(s,cash=s.cash*scale,quotes=tuple(q*scale for q in s.quotes))
            event=replace(e,offers=tuple(replace(o,price=o.price*scale) for o in e.offers))
            problem=prepare(scaled_c,state,state,event,p)
            bound=bounder(problem,state,state,p)
            hi=tuple(o.stock for o in event.offers)
            for lo in ((0,0,0,0),(2,0,0,0),(0,2,1,0)):
                top=bound(lo,hi)['upperValue']
                for allocation in product(*(range(a,b+1,o.lot) for a,b,o in zip(lo,hi,event.offers))):
                    try:after,_=apply(scaled_c,state,event,allocation)
                    except ValueError as exc:
                        self.assertIn(str(exc),('infeasible procurement allocation','production would exceed physical storage'))
                        continue
                    values=[]
                    for weight,path in p:
                        final=after
                        for following in path.events:final,_=apply(scaled_c,final,following)
                        values.append(weight*horizon_value(state,final,path.input_values,path.finished_values))
                    self.assertGreaterEqual(top,math.fsum(values),(scale,lo,allocation))

    def test_work_limit_and_invalid_budgets_never_supply_finite_pruning_bound(self):
        c,s,e,p=self.fixture(2);problem=prepare(c,s,s,e,p)
        hi=tuple(o.stock for o in e.offers)
        self.assertEqual(bounder(problem,s,s,p,max_states=8)((0,)*4,hi),dict(upperValue=math.inf,batchStates=0))
        for value in (0,-1,True,1.5):
            with self.assertRaises(ValueError):bounder(problem,s,s,p,max_states=value)


if __name__=='__main__':unittest.main()
