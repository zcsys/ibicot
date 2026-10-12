from dataclasses import replace
from itertools import product
import math
import unittest
import numpy as np
from tools.buying_v2.forecast import Forecast
from tools.buying_v2.forecast_allocation import prepare,plan
from tools.buying_v2.industry_oracle import evaluate,Offer,Line,Problem


def forecast(pid,quote,cap,quantities,probabilities):
    return Forecast(tuple(quantities),tuple(probabilities),cap,dict(product=pid,contemplatedQuote=quote,decisionTick=2,latestPublishedTick=1,channel='retail',catalog='test'))


def fixture(price=1.,cash=10.,basis=0.):
    return Problem((0,),(basis,),(1.,),(4,),8.,cash,(Offer(0,1,price,4),),(-1,),(0,),(0.,),
                   (Line((1,),4,.5,4.,0.,(0.,)*5,1.),),((0.,)*5,),funded_demands=(4,))

class ForecastAllocationTests(unittest.TestCase):
    def run_plan(self,p,fs,old,terminal=None):
        return plan(p,fs,old,product_ids=tuple(range(len(fs))),decision_tick=2,channel='retail',
                    finished_terminal=terminal or tuple((0.,)*(x+l.max_batches*l.output_qty+1) for x,l in zip(old,p.lines)))

    def test_old_stock_consumes_demand_and_unsold_value_is_not_double_counted(self):
        p=fixture();f=forecast(0,4.,6,(0,3),(.5,.5))
        result=self.run_plan(p,(f,),(2,))
        self.assertEqual(tuple(result['result'][0]),(1,))
        self.assertAlmostEqual(result['result'][3],.5)
        self.assertEqual(result['existingFinishedPayoff'],(4.,))
        valued,base=prepare(p,(f,),(2,),product_ids=(0,),decision_tick=2,channel='retail',finished_terminal=(tuple(.25*q for q in range(7)),))
        # Three stock: half sell none and retain .75; half sell all for 12.
        self.assertAlmostEqual(base[0]+valued.lines[0].output_values[1],6.375)

    def test_price_and_conversion_liquidity_control_purchase(self):
        f=forecast(0,4.,4,(1,),(1.,))
        self.assertEqual(tuple(self.run_plan(fixture(),(f,),(0,))['result'][0]),(1,))
        self.assertEqual(tuple(self.run_plan(fixture(price=4.),(f,),(0,))['result'][0]),(0,))
        self.assertEqual(tuple(self.run_plan(fixture(cash=1.),(f,),(0,))['result'][0]),(0,))

    def test_random_shared_input_cases_against_direct_scenario_scoring(self):
        rng=np.random.default_rng(620813)
        for _ in range(120):
            old=tuple(int(x) for x in rng.integers(0,3,2));quotes=(6.,8.)
            lines=tuple(Line(recipe,2,.5,q,0.,(0.,)*3,float(sum(recipe))) for recipe,q in zip(((1,1),(2,0)),quotes))
            offers=tuple(Offer(m,s,float(rng.integers(1,5)),2) for m in range(2) for s in range(2))
            p=Problem((0,0),(0.,0.),(1.,1.),(3,3),8.,float(rng.integers(1,18)),offers,(0,0),(2,2),(1.,2.),lines,((0.,)*4,)*2,funded_demands=(3,)*4)
            fs=tuple(forecast(i,q,old[i]+2,(0,old[i]+2),(.25,.75)) for i,q in enumerate(quotes))
            answer=self.run_plan(p,fs,old);best=-math.inf
            for allocation in product(range(3),repeat=4):
                actual=evaluate(p,allocation)
                if actual is None:continue
                value=actual['value']
                for i,(q,f) in enumerate(zip(quotes,fs)):
                    # Independent direct expected incremental receipts, without
                    # using the adapter's output table or expected_sales method.
                    value+=sum(prob*q*(min(old[i]+actual['outputs'][i],d)-min(old[i],d)) for d,prob in zip(f.quantities,f.probabilities))
                best=max(best,value)
            self.assertAlmostEqual(answer['result'][3],best)

    def test_historical_basis_gate_and_explicit_search_failure(self):
        p=fixture()
        p=replace(p,held=(1,),basis=(100.,))
        f=forecast(0,4.,4,(4,),(1.,))
        answer=self.run_plan(p,(f,),(0,))
        self.assertEqual(tuple(answer['result'][0]),(0,))
        self.assertEqual(tuple(answer['result'][1]),(0,))
        from tools.buying_v2.industry_bounds import SearchLimit
        with self.assertRaises(SearchLimit):
            plan(fixture(),(f,),(0,),product_ids=(0,),decision_tick=2,channel='retail',finished_terminal=((0.,)*5,),max_nodes=0)

    def test_rejects_unfunded_misaligned_and_incomplete_forecasts(self):
        p=fixture();f=forecast(0,4.,4,(1,),(1.,))
        for bad in (replace(f,payoff_cap=3),replace(f,probabilities=(.5,)),replace(f,diagnostics={**f.diagnostics,'product':1}),replace(f,diagnostics={**f.diagnostics,'latestPublishedTick':2})):
            with self.assertRaises(ValueError):self.run_plan(p,(bad,),(0,))
        with self.assertRaises(ValueError):self.run_plan(replace(p,funded_demands=None),(f,),(0,))

if __name__=='__main__':unittest.main()
