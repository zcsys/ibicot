import unittest
from dataclasses import replace
from tools.buying_v2.policy_comparison import cases,compare
from tools.buying_v2.industry_oracle import Offer,Problem,Line
from tools.buying_v2.continuation_oracle import continuation,optimize,optimize_uncertain


class ProcurementObjectiveTests(unittest.TestCase):
    def test_complements_need_joint_funding_not_independent_targets(self):
        result=compare(cases()['complementary_inputs_scarce_cash'])
        self.assertEqual(result['storage_units']['quantities'],(4,0))
        self.assertEqual(result['storage_units']['outputs'],(0,))
        self.assertEqual(result['batch_first']['quantities'],(1,1))
        self.assertEqual(result['batch_first']['outputs'],(2,))
        self.assertEqual(result['scenario_return']['quantities'],(1,1))

    def test_conversion_cash_and_sell_through_are_distinct(self):
        conversion=compare(cases()['conversion_cash_reservation'])
        self.assertEqual(conversion['storage_units']['outputs'],(0,))
        self.assertEqual(conversion['batch_first']['outputs'],(5,))
        sales=compare(cases()['weak_realizable_sales'])
        self.assertEqual(sales['batch_first']['outputs'],(8,))
        self.assertEqual(sales['scenario_return']['outputs'],(1,))
        self.assertEqual(sales['batch_first']['value'],-6.)
        self.assertEqual(sales['scenario_return']['value'],2.75)

    def test_owned_basis_gate_is_retained_for_all_objectives(self):
        result=compare(cases()['owned_input_history_gate'])
        for policy in result.values():
            self.assertEqual(policy['outputs'],(0,))
        self.assertEqual(result['scenario_return']['quantities'],(0,0))

    def test_future_buffer_value_requires_cash_and_complement_arrival(self):
        p=cases()['useful_future_buffer_assumption']
        future=replace(p,offers=(Offer(1,1,4.,2),),terminal_values=((0.,)*5,(0.,)*5))
        best=optimize(p,future,(8,),(4,))
        self.assertEqual(best['first']['allocation'],(2,))
        self.assertEqual(best['first']['outputs'],(0,))
        self.assertEqual(best['second']['quantities'],(0,2))
        self.assertEqual(best['second']['outputs'],(4,))
        self.assertEqual(best['closingCash'],12.)
        self.assertEqual(best['scenarioValue'],1.)
        no_arrival=replace(future,offers=())
        no_buffer=optimize(p,no_arrival,(8,),(4,))
        self.assertEqual(no_buffer['first']['allocation'],(0,))
        self.assertEqual(no_buffer['scenarioValue'],0.)
        # More stock can have less continuation value when acquisition depleted
        # the cash required for future complements and conversion.
        two=continuation(p,future,(8,),(4,),(2,))
        three=continuation(p,future,(8,),(4,),(3,))
        self.assertEqual(two['continuationValue'],3.)
        self.assertEqual(three['continuationValue'],1.5)

    def test_no_double_count_of_goods_held_between_periods(self):
        p=Problem((0,),(0.,),(1.,),(1,),1.,10.,(Offer(0,0,1.,1),),(-1,),(0,),(0.,),
                  (Line((1,),1,.25,4.,0.,(0.,4.),1.),),((0.,0.),))
        future=replace(p,offers=())
        result=continuation(p,future,(1,),(1,),(1,))
        self.assertEqual(result['first']['outputs'],(1,))
        self.assertEqual(result['second']['outputs'],(0,))
        self.assertEqual(result['closingRevenue'],4.)
        self.assertEqual(result['scenarioValue'],2.75)
        self.assertEqual(result['closingCash'],12.75)
        self.assertEqual(result['remainingRoomAtSecondDecision'],0.)

    def test_uncertain_arrival_does_not_get_clairvoyant_initial_purchase(self):
        p=cases()['useful_future_buffer_assumption']
        future=replace(p,offers=(Offer(1,1,4.,2),),terminal_values=((0.,)*5,(0.,)*5))
        empty=replace(future,offers=())
        for chance,expected_q,expected_value in ((.5,(0,),0.),(.75,(2,),.25)):
            result=optimize_uncertain(p,((chance,future,((1.,(4,)),)),(1-chance,empty,((1.,(4,)),))),(8,))
            self.assertEqual(result['firstAllocation'],expected_q)
            self.assertEqual(result['expectedValue'],expected_value)

    def test_future_demand_is_not_revealed_before_second_purchase(self):
        p=Problem((0,),(0.,),(1.,),(1,),1.,10.,(),(-1,),(0,),(0.,),
                  (Line((1,),1,.25,4.,0.,(0.,4.),1.),),((0.,0.),))
        future=replace(p,offers=(Offer(0,0,3.,1),))
        result=optimize_uncertain(p,((1.,future,((.5,(0,)),(.5,(1,)))),),(1,))
        self.assertEqual(result['expectedValue'],0.)
        self.assertEqual(result['states'][0]['result']['second']['allocation'],(0,))
        split=optimize_uncertain(p,((.5,future,((1.,(0,)),)),(.5,future,((1.,(1,)),))),(1,))
        self.assertEqual(split['expectedValue'],0.)
        self.assertEqual(len(split['states']),1)
        self.assertEqual(split['states'][0]['result']['second']['allocation'],(0,))

    def test_invalid_scenario_probabilities_are_rejected(self):
        p=cases()['useful_future_buffer_assumption']
        with self.assertRaisesRegex(ValueError,'probabilities'):
            optimize_uncertain(p,((.5,p,((1.,(4,)),)),),(8,))


if __name__=='__main__':
    unittest.main()
