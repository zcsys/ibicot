from dataclasses import replace
import unittest
from test_buying_v2_forecast_allocation import fixture, forecast
from tools.buying_v2.forecast_sensitivity import compare


class SensitivityTests(unittest.TestCase):
    def compare(self, p=None, models=None, old=(0,), terminal=None, **kwargs):
        return compare(p or fixture(), models or {'low':(forecast(0,4.,4,(1,),(1.,)),),
            'high':(forecast(0,4.,4,(4,),(1.,)),)}, old, product_ids=(0,),decision_tick=2,
            channel='retail',finished_terminal=terminal or ((0.,)*5,),max_models=kwargs.get('max_models',4),max_nodes=1000)

    def test_cross_returns_and_regret_independently_calculated(self):
        result = self.compare()
        self.assertFalse(result['decisionInvariant'])
        self.assertEqual(result['optimalAllocations'], {'high':(4,), 'low':(1,)})
        rows = {r['allocation']:r for r in result['candidates']}
        self.assertEqual(rows[(1,)]['incrementalReturns'], {'high':2.5,'low':2.5})
        self.assertEqual(rows[(4,)]['incrementalReturns'], {'high':10.,'low':-2.})
        self.assertEqual(rows[(4,)]['regrets'], {'high':0.,'low':4.5})
        self.assertEqual(rows[(1,)]['regrets'], {'high':7.5,'low':0.})
        self.assertEqual(rows[(0,)]['regrets'], {'high':10.,'low':2.5})

    def test_existing_finished_baseline_and_identical_decisions(self):
        low=forecast(0,4.,6,(1,),(1.,)); high=forecast(0,4.,6,(2,),(1.,))
        result=self.compare(models={'low':(low,),'high':(high,)},old=(2,),terminal=((0.,)*7,))
        self.assertTrue(result['decisionInvariant'])
        self.assertEqual(result['candidates'][0]['returnsIncludingExistingFinished'],{'high':8.,'low':4.})
        self.assertEqual(result['candidates'][0]['incrementalReturns'],{'high':0.,'low':0.})

    def test_multiple_lines_and_shared_input_cross_values(self):
        from tools.buying_v2.industry_oracle import Line, evaluate
        p=fixture()
        p=replace(p,lines=(Line((1,),2,.5,4.,0.,(0.,)*3,1.),Line((1,),2,.5,6.,0.,(0.,)*3,1.)))
        models={'a':(forecast(0,4.,2,(1,),(1.,)),forecast(1,6.,2,(2,),(1.,))),
                'b':(forecast(0,4.,2,(2,),(1.,)),forecast(1,6.,2,(0,),(1.,)))}
        result=compare(p,models,(0,0),product_ids=(0,1),decision_tick=2,channel='retail',
            finished_terminal=((0.,)*3,)*2,max_models=2,max_nodes=1000)
        best={}
        for name, fs in models.items():
            values=[]
            for q in range(5):
                physical=evaluate(p,(q,))
                if physical is None:continue
                values.append(physical['value']+sum(line.quote*min(out,f.quantities[0])
                    for line,out,f in zip(p.lines,physical['outputs'],fs)))
            best[name]=max(values)
        self.assertEqual(result['optimalValues'],best)
        for row in result['candidates']:
            physical=evaluate(p,row['allocation'])
            for name,fs in models.items():
                expected=physical['value']+sum(line.quote*min(out,f.quantities[0])
                    for line,out,f in zip(p.lines,physical['outputs'],fs))
                self.assertEqual(row['incrementalReturns'][name],expected)
                self.assertEqual(row['regrets'][name],best[name]-expected)

    def test_cash_gate_and_model_identity(self):
        self.assertTrue(self.compare(p=fixture(cash=1.))['decisionInvariant'])
        with self.assertRaises(ValueError):self.compare(max_models=1)
        f=forecast(0,4.,4,(1,),(1.,))
        for bad in (replace(f,payoff_cap=5),replace(f,diagnostics={**f.diagnostics,'seller':9}),
                    replace(f,diagnostics={**f.diagnostics,'catalog':'other'})):
            with self.assertRaises(ValueError):self.compare(models={'a':(f,),'b':(bad,)})


if __name__=='__main__':unittest.main()
