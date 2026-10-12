from dataclasses import replace
from itertools import product
import math
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.closing_cash_relaxed_bound import bounder
from tools.buying_v2.phase_ledger import apply,horizon_value


class CashRelaxedBoundTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=case(1,2,1,2,lines=2)
        e=replace(paths[0].events[0],funded_demands=(3,3,1,1))
        posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
        return c,s,e,posterior

    def test_every_basket_under_cash_offsets_and_money_scales(self):
        c,s,e,p=self.fixture();checked=0
        for scale in (1e-8,1.,1e8):
            company=replace(c,lines=tuple(replace(line,conversion=line.conversion*scale) for line in c.lines))
            event=replace(e,offers=tuple(replace(o,price=o.price*scale) for o in e.offers))
            for cash in (0.,.1,5.,100.,1e12):
                state=replace(s,cash=cash*scale,quotes=tuple(q*scale for q in s.quotes),arrears=3.*scale)
                initial=replace(state,cash=50.*scale,arrears=7.*scale)
                problem=prepare(company,initial,state,event,p)
                bound=bounder(problem,initial,state,p)
                for lo in ((0,0,0,0),(1,0,0,0),(0,1,1,0)):
                    hi=(3,3,1,1);top=bound(lo,hi)['upperValue']
                    for allocation in product(*(range(a,b+1) for a,b in zip(lo,hi))):
                        try:after,_=apply(company,state,event,allocation)
                        except ValueError as exc:
                            self.assertIn(str(exc),('infeasible procurement allocation','production would exceed physical storage'));continue
                        values=[]
                        for weight,path in p:
                            final=after
                            for following in path.events:final,_=apply(company,final,following)
                            values.append(weight*horizon_value(initial,final,path.input_values,path.finished_values))
                        actual=math.fsum(values)/math.fsum(w for w,_ in p)
                        self.assertGreaterEqual(top,actual,(scale,cash,lo,allocation));checked+=1
        self.assertGreater(checked,100)

    def test_posterior_rounding_signed_terminal_values_and_fees(self):
        c,s,e,p=self.fixture();s=replace(s,cash=20.,held=(1,0),basis=(100.,0.),incumbents=(0,0))
        e=replace(e,fee_multiple=2.)
        for scale in (1e-200,1.,1e100):
            posterior=tuple((weight*scale,replace(p[index%2][1],
                events=(p[index%2][1].events[0],replace(p[index%2][1].events[1],fee_income=.1)),
                input_values=((-.1,.2,-.4,.3),(0.,-.2)),finished_values=((0.,-.1,.3),)*2))
                for index,weight in enumerate((.1,.2,.7)))
            problem=prepare(c,s,s,e,posterior)
            top=bounder(problem,s,s,posterior)((0,)*4,(2,2,1,1))['upperValue']
            for allocation in product(range(3),range(3),range(2),range(2)):
                try:after,_=apply(c,s,e,allocation)
                except ValueError as exc:
                    self.assertIn(str(exc),('infeasible procurement allocation','production would exceed physical storage'));continue
                values=[]
                for weight,path in posterior:
                    final=after
                    for following in path.events:final,_=apply(c,final,following)
                    values.append(weight*horizon_value(s,final,path.input_values,path.finished_values))
                self.assertGreaterEqual(top,math.fsum(values)/math.fsum(w for w,_ in posterior))

    def test_tight_certain_case_and_unavailable_budget(self):
        c,s,e,p=self.fixture();p=(p[1],)
        problem=prepare(c,s,s,e,p)
        result=bounder(problem,s,s,p)((0,)*4,(3,3,1,1))
        self.assertGreaterEqual(result['upperValue'],13.)
        self.assertLess(result['upperValue'],13.+1e-8)
        self.assertEqual(bounder(problem,s,s,p,max_states=1)((0,)*4,(3,3,1,1))['upperValue'],math.inf)
        for value in (0,-1,True,1.5):
            with self.assertRaises(ValueError):bounder(problem,s,s,p,max_states=value)


if __name__=='__main__':unittest.main()
