from dataclasses import replace
import math
import unittest
from tools.buying_v2.forecast import Forecast
from tools.buying_v2.joint_forecast import couple
from tools.buying_v2.temporal_forecast import couple_periods,sales_scenarios
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_ledger import EndTick,SetQuotes
from tools.buying_v2.phase_oracle import solve


def period(probabilities=(.5,.5),quote=10.,tick=2):
    f=Forecast((0,1),probabilities,1,dict(product=101,contemplatedQuote=quote,
                 decisionTick=tick,latestPublishedTick=tick-1,channel='retail'))
    return couple((f,),dependence='independent',max_scenarios=2)


def paths(transition,*,stockless_first=False):
    c,s,original=case(1,1,2,2)
    first=original[0].events[0]
    second=replace(original[0].events[4],offers=tuple(replace(o,price=3.) for o in original[0].events[4].offers))
    if stockless_first:second=replace(second,offers=tuple(replace(o,price=2.) for o in second.offers))
    temporal=couple_periods((period(),period()),tick_offsets=(0,1),transitions=transition,max_scenarios=4)
    scenarios=sales_scenarios(temporal,prefixes=(() if stockless_first else (first,), (EndTick('next',.15),second)),
        labels=('first','second'),suffix=(),opening_quotes=s.quotes,
        input_values=original[0].input_values,finished_values=original[0].finished_values)
    return c,s,scenarios,temporal


class TemporalForecastTests(unittest.TestCase):
    def test_explicit_kernels_preserve_marginals_and_temporal_dependence(self):
        for transition,expected in (('independent',4),((((1.,0.),(0.,1.)),),2),((((0.,1.),(1.,0.)),),2)):
            t=couple_periods((period(),period()),tick_offsets=(0,1),transitions=transition,max_scenarios=4)
            self.assertEqual(len(t.quantities),expected)
            for i in range(2):
                self.assertEqual(math.fsum(p for q,p in zip(t.quantities,t.probabilities) if q[i]==(1,)),.5)
        p=period((.25,.75))
        t=couple_periods((p,p,p),tick_offsets=(0,1,2),transitions=(((1.,0.),(0.,1.)),)*2,max_scenarios=2)
        self.assertEqual(t.quantities,(((0,),(0,),(0,)),((1,),(1,),(1,))))
        self.assertEqual(t.probabilities,(.25,.75))

    def test_joint_product_states_and_nonstationary_marginals_are_preserved(self):
        first=period((.25,.75));second=period()
        temporal=couple_periods((first,second),tick_offsets=(0,1),
                               transitions=(((1.,0.),(1./3.,2./3.)),),max_scenarios=3)
        self.assertAlmostEqual(sum(w for q,w in zip(temporal.quantities,temporal.probabilities) if q[1]==(1,)),.5)
        f=Forecast((0,1),(.5,.5),1,dict(product=101,contemplatedQuote=10.,decisionTick=2,latestPublishedTick=1,channel='retail'))
        other=replace(f,diagnostics={**f.diagnostics,'product':102})
        joint=couple((f,other),dependence='independent',max_scenarios=4)
        identity=tuple(tuple(float(i==j) for j in range(4)) for i in range(4))
        t=couple_periods((joint,joint),tick_offsets=(0,1),transitions=(identity,),max_scenarios=4)
        self.assertEqual(t.quantities,tuple((q,q) for q in joint.quantities))
        self.assertEqual(t.probabilities,joint.probabilities)
        for i in range(2):
            for q,p in zip(joint.quantities,joint.probabilities):
                self.assertEqual(sum(w for path,w in zip(t.quantities,t.probabilities) if path[i]==q),p)

    def test_conditional_opportunities_change_purchase_and_value(self):
        for transition,value in (('independent',3.),((((1.,0.),(0.,1.)),),2.25),((((0.,1.),(1.,0.)),),5.5)):
            c,s,p,t=paths(transition)
            result=solve(c,s,p,funding='continuation')
            self.assertEqual(result['expectedValue'],value)
            if transition=='independent':
                high=[leaf for leaf in result['leaves'] if leaf['trace'][2]['sold']==(1,)]
                self.assertTrue(high)
                for leaf in high:self.assertEqual(leaf['trace'][4]['allocation'],(0,0))
            elif transition[0][0][0]==1.:
                high=next(leaf for leaf in result['leaves'] if leaf['trace'][2]['sold']==(1,))
                self.assertEqual(high['trace'][4]['allocation'],(1,1))

    def test_hidden_first_demand_does_not_reveal_future_state(self):
        c,s,p,_=paths((((1.,0.),(0.,1.)),),stockless_first=True)
        result=solve(c,s,p,funding='continuation')
        self.assertEqual(len(result['leaves']),2)
        for leaf in result['leaves']:
            self.assertEqual(leaf['trace'][1]['sold'],(0,))
            self.assertEqual(leaf['trace'][3]['allocation'],(1,1))
        self.assertEqual(result['leaves'][0]['trace'][3],result['leaves'][1]['trace'][3])

    def test_limits_underflow_zero_atoms_and_bad_kernels(self):
        p=period()
        with self.assertRaisesRegex(ValueError,'scenario limit'):
            couple_periods((p,)*100,tick_offsets=tuple(range(100)),transitions='independent',max_scenarios=100)
        for transitions in (None,'guess',(),(((1.,0.),),),(((1.,1.),(0.,1.)),),(((1.,0.),(1.,0.)),)):
            with self.assertRaises(ValueError):couple_periods((p,p),tick_offsets=(0,1),transitions=transitions,max_scenarios=4)
        tiny=period((1e-200,1.))
        with self.assertRaisesRegex(ValueError,'underflow'):
            couple_periods((tiny,tiny),tick_offsets=(0,1),transitions='independent',max_scenarios=4)
        zero=period((0.,1.))
        t=couple_periods((zero,zero),tick_offsets=(0,1),transitions='independent',max_scenarios=1)
        self.assertEqual(t.quantities,(((1,),(1,)),))

    def test_publication_calendar_quote_and_path_integrity(self):
        p=period()
        with self.assertRaises(ValueError):
            couple_periods((replace(p,quantities=list(p.quantities)),),tick_offsets=(0,),transitions='independent',max_scenarios=2)
        for periods,offsets in (((p,period(tick=3)),(0,1)),((p,p),(1,0)),((p,p),(0,True))):
            with self.assertRaises(ValueError):couple_periods(periods,tick_offsets=offsets,transitions='independent',max_scenarios=4)
        t=couple_periods((p,period(quote=11.)),tick_offsets=(0,1),transitions='independent',max_scenarios=4)
        kw=dict(prefixes=((),(EndTick('next',.15),SetQuotes('quote',(11.,)))),labels=('a','b'),suffix=(),opening_quotes=(10.,),
                input_values=((0.,0.),),finished_values=((0.,0.),))
        self.assertEqual(len(sales_scenarios(t,**kw)),4)
        for change in (dict(prefixes=((),(EndTick('next',.15),))),dict(prefixes=((),(SetQuotes('quote',(11.,)),))),
                       dict(labels=('a','a')),dict(opening_quotes=(9.,))):
            with self.assertRaises(ValueError):sales_scenarios(t,**{**kw,**change})
        for altered in (replace(t,probabilities=(1.,)),replace(t,quantities=t.quantities[:-1])):
            with self.assertRaises(ValueError):sales_scenarios(altered,**kw)


if __name__=='__main__':unittest.main()
