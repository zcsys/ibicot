import unittest
from dataclasses import replace
from tools.buying_v2.forecast import Forecast
from tools.buying_v2.joint_forecast import couple,sales_scenarios
from tools.buying_v2.industry_oracle import Line,Offer
from tools.buying_v2.phase_ledger import Company,State,Purchase,OpenBook,SettleBook
from tools.buying_v2.phase_oracle import solve


def f(product,quantities=(0,1),probabilities=(.5,.5)):
    return Forecast(quantities,probabilities,max(quantities),dict(product=product,contemplatedQuote=2.,decisionTick=2,latestPublishedTick=1,channel='retail'))


class JointForecastTests(unittest.TestCase):
    def test_two_explicit_couplings_preserve_marginals_and_change_joint_risk(self):
        forecasts=(f(1),f(2))
        independent=couple(forecasts,dependence='independent',max_scenarios=4)
        aligned=couple(forecasts,dependence='common-quantile',max_scenarios=4)
        self.assertEqual(independent.quantities,((0,0),(0,1),(1,0),(1,1)))
        self.assertEqual(independent.probabilities,(.25,)*4)
        self.assertEqual(aligned.quantities,((0,0),(1,1)))
        self.assertEqual(aligned.probabilities,(.5,.5))
        for joint in (independent,aligned):
            for i,forecast in enumerate(forecasts):
                for q,p in zip(forecast.quantities,forecast.probabilities):
                    self.assertAlmostEqual(sum(w for row,w in zip(joint.quantities,joint.probabilities) if row[i]==q),p)

    def test_unequal_masses_zero_atoms_and_scenario_budgets(self):
        forecasts=(f(1,(0,1,2),(.25,0.,.75)),f(2,(0,3),(.6,.4)))
        joint=couple(forecasts,dependence='common-quantile',max_scenarios=3)
        self.assertEqual(joint.quantities,((0,0),(2,0),(2,3)))
        for a,b in zip(joint.probabilities,(.25,.35,.4)):self.assertAlmostEqual(a,b)
        for mode in ('independent','common-quantile'):
            with self.assertRaisesRegex(ValueError,'scenario limit'):couple(forecasts,dependence=mode,max_scenarios=2)

    def test_same_mean_sales_different_financing_opportunity(self):
        c=Company((1.,),(1,),10.,tuple(Line((1,),1,.5,2.,0.,(0.,0.),1.) for _ in range(3)),(2,2,2),0.)
        s=State(0.,(0,),(0.,),(1,1,0),(.5,.5,0.),(2.,2.,2.),(-1,))
        buy=Purchase('buy',(Offer(0,1,1.,1),),(),(0.,),1.,0.,(2,),0.)
        suffix=(buy,OpenBook('final'),SettleBook('final',(0,0,1)))
        for mode,expected in (('independent',2.375),('common-quantile',2.25)):
            joint=couple((f(1),f(2),f(3,(0,),(1.,))),dependence=mode,max_scenarios=4)
            paths=sales_scenarios(joint,prefix=(),label='retail',suffix=suffix,input_values=((0.,0.),),finished_values=((0.,)*3,)*3)
            result=solve(c,s,paths,funding='continuation')
            self.assertEqual(result['expectedValue'],expected)
            for leaf in result['leaves']:
                cash=leaf['trace'][1]['cash'];allocation=leaf['trace'][2]['allocation']
                self.assertEqual(allocation,(int(cash>=1.5),))

    def test_unrepresentable_positive_tail_is_rejected(self):
        marginal=f(1,(0,1),(1.,1e-30))
        with self.assertRaisesRegex(ValueError,'precision loss'):
            couple((marginal,),dependence='common-quantile',max_scenarios=2)

    def test_invalid_metadata_duplicate_products_and_distribution_fail(self):
        a=f(1)
        for forecasts in ((a,a),(a,replace(f(2),diagnostics={**f(2).diagnostics,'decisionTick':3})),
                (replace(a,probabilities=(.2,.2)),),(replace(a,diagnostics={**a.diagnostics,'latestPublishedTick':2}),)):
            with self.assertRaises(ValueError):couple(forecasts,dependence='independent',max_scenarios=4)
        with self.assertRaises(ValueError):couple((a,),dependence='implicit',max_scenarios=4)


if __name__=='__main__':unittest.main()
