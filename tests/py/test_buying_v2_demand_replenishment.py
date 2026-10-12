import unittest
from dataclasses import replace
from tools.buying_v2.forecast import Forecast
from tools.buying_v2.demand_replenishment import plan
from tools.buying_v2.policy_comparison import cases
from tools.buying_v2.industry_oracle import Line,Offer,Problem


def forecast(quote,cap,quantities,probabilities):
    return Forecast(quantities,probabilities,cap,{'contemplatedQuote':quote})


class DemandReplenishmentTests(unittest.TestCase):
    def test_weak_sales_reduces_target_without_changing_production_rule(self):
        p=cases()['weak_realizable_sales']
        r=plan(p,(forecast(4.,8,(1,),(1.,)),),(0,))
        self.assertEqual(r['targetBatches'],(1,))
        self.assertEqual(r['result']['quantities'],(1,))
        self.assertEqual(r['result']['outputs'],(1,))
        self.assertEqual(r['result']['value'],2.75)

    def test_old_stock_is_subtracted_inside_each_uncertain_outcome(self):
        p=cases()['weak_realizable_sales']
        r=plan(p,(forecast(4.,10,(0,4),(.5,.5)),),(2,))
        self.assertEqual(r['expectedResidualSales'],(1.,))
        self.assertEqual(r['targetBatches'],(1,))
        self.assertEqual(r['result']['quantities'],(1,))

    def test_shared_repeated_inputs_and_batch_yields(self):
        lines=(Line((2,1),2,.25,10.,0.,(0.,)*5,1.,2),Line((1,2),3,.25,12.,0.,(0.,)*4,1.))
        p=Problem((1,2),(1.,1.),(1.,1.),(10,10),30.,100.,
                  (Offer(0,1,1.,10),Offer(1,2,1.,10)),(-1,-1),(0,0),(0.,0.),lines,((0.,)*11,(0.,)*11))
        r=plan(p,(forecast(10.,4,(3,),(1.,)),forecast(12.,3,(1,),(1.,))),(0,0))
        self.assertEqual(r['targetBatches'],(2,1))
        self.assertEqual(r['inputHoldingTargets'],(5,4))
        self.assertEqual(r['result']['quantities'],(4,2))

    def test_conversion_liquidity_and_basis_gate_limit_comparator(self):
        p=cases()['conversion_cash_reservation']
        r=plan(p,(forecast(4.,10,(10,),(1.,)),),(0,))
        self.assertEqual(r['result']['quantities'],(10,))
        self.assertEqual(r['result']['outputs'],(0,))
        p=cases()['owned_input_history_gate']
        r=plan(p,(forecast(3.,2,(2,),(1.,)),),(0,))
        self.assertEqual(r['result']['quantities'],(0,1))
        self.assertEqual(r['result']['outputs'],(0,))

    def test_zero_demand_and_input_price_do_not_create_profit_optimizer(self):
        p=cases()['weak_realizable_sales']
        r=plan(p,(forecast(4.,8,(0,),(1.,)),),(0,))
        self.assertEqual(r['result']['quantities'],(0,))
        # Affordably filling a demand target can still buy loss-making inputs.
        p=replace(p,cash=100.,offers=(Offer(0,0,5.,8),))
        r=plan(p,(forecast(4.,8,(1,),(1.,)),),(0,))
        self.assertEqual(r['result']['quantities'],(1,))
        self.assertEqual(r['result']['outputs'],(0,))
        self.assertEqual(r['result']['value'],-5.)

    def test_wholesale_target_below_one_lot_remains_unfilled(self):
        p=cases()['weak_realizable_sales']
        p=replace(p,offers=(Offer(0,0,1.,8,lot=2),))
        r=plan(p,(forecast(4.,8,(1,),(1.,)),),(0,))
        self.assertEqual(r['inputHoldingTargets'],(1,))
        self.assertEqual(r['result']['quantities'],(0,))
        # Preserve the existing floor-to-lot replenishment contract; report
        # this mismatch instead of silently adding surplus buffer targets.

    def test_invalid_or_misaligned_forecasts_fail(self):
        p=cases()['weak_realizable_sales'];f=forecast(4.,8,(1,),(1.,))
        for forecasts,finished in (((),()),((replace(f,payoff_cap=7),),(0,)),((replace(f,payoff_cap=float('nan')),),(0,)),
                ((replace(f,probabilities=(.5,)),),(0,)),((f,),(-1,)),
                ((replace(f,diagnostics={'contemplatedQuote':3.}),),(0,))):
            with self.assertRaises(ValueError):plan(p,forecasts,finished)


if __name__=='__main__':unittest.main()
