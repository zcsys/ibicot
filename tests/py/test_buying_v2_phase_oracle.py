import unittest
from dataclasses import replace
from tools.buying_v2.industry_oracle import Line, Offer
from tools.buying_v2.phase_ledger import Company, State, Purchase, OpenBook, SettleBook, Rent
from tools.buying_v2.phase_oracle import Scenario, solve


def one_unit_funding(company,state,event):
    # Explicit single-material fixture rule; no future scenario is available.
    # For these tiny cases every hypothetical quote admits at most one item.
    assert len(company.slots)==1
    return tuple(min(1,max(0,company.slots[0]-state.held[0]),int(state.cash//o.price)) for o in event.offers)


def fixture(price=3.,conversion=.25,quote=4.):
    line=Line((1,),1,conversion,quote,0.,(0.,0.),1.)
    company=Company((1.,),(1,),4.,(line,),(2,),0.)
    initial=State(10.,(0,),(0.,),(0,),(0.,),(quote,),(-1,))
    event=Purchase('buy',(Offer(0,1,price,1),),(999,),(.5,),1.,0.,(0,),0.)
    return company,initial,event


def scenario(events,probability=1.):
    return Scenario(probability,events,((0.,0.),),((0.,0.,0.),))


class PhaseOracleTests(unittest.TestCase):
    def test_hidden_future_sales_cannot_choose_current_basket(self):
        c,s,b=fixture()
        low=scenario((b,OpenBook('sales'),SettleBook('sales',(0,))),.5)
        high=scenario((b,OpenBook('sales'),SettleBook('sales',(1,))),.5)
        result=solve(c,s,(low,high),funding=one_unit_funding)
        self.assertEqual(result['expectedValue'],0.)
        self.assertEqual([leaf['trace'][0]['allocation'] for leaf in result['leaves']],[(0,),(0,)])
        # Perfect-information branches buy only in the high state. Averaging
        # those optima would give .375 and is explicitly not our result.
        known=solve(c,s,(replace(high,probability=1.),),funding=one_unit_funding)
        self.assertEqual(known['expectedValue'],.75)
        self.assertEqual(known['leaves'][0]['trace'][0]['allocation'],(1,))

    def test_realized_prior_receipts_are_observable_and_can_fund_next_action(self):
        c,s,b=fixture(price=1.)
        s=replace(s,cash=0.,finished=(1,))
        paths=tuple(scenario((OpenBook('retail'),SettleBook('retail',(d,)),b,
                    OpenBook('closing'),SettleBook('closing',(1,))),.5) for d in (0,1))
        result=solve(c,s,paths,funding=one_unit_funding)
        self.assertAlmostEqual(result['expectedValue'],5.375)
        actions=[leaf['trace'][2]['allocation'] for leaf in result['leaves']]
        self.assertEqual(actions,[(0,),(1,)])
        self.assertEqual([leaf['state'].cash for leaf in result['leaves']],[4.,6.75])

    def test_whole_fill_preference_changes_future_original_fee_recipient(self):
        c,s,b=fixture(price=1.,conversion=0.,quote=5.)
        s=replace(s,incumbents=(7,))
        first=replace(b,offers=(Offer(0,7,4.,1),Offer(0,2,1.,1)),reliability=(0.,0.),fee_multiple=1.)
        second=replace(first,label='buy-again',offers=(Offer(0,7,1.,1),Offer(0,2,4.,1)))
        events=(first,OpenBook('first-sales'),SettleBook('first-sales',(1,)),second,
                OpenBook('next-sales'),SettleBook('next-sales',(1,)))
        result=solve(c,s,(scenario(events),),funding=one_unit_funding)
        self.assertEqual(result['expectedValue'],6.)
        trace=result['leaves'][0]['trace']
        self.assertEqual(trace[0]['offerIdentities'],((0,2),(0,7)))
        self.assertEqual(trace[0]['allocation'],(1,0))
        self.assertEqual(trace[0]['feeRecipients'],(7,))
        self.assertEqual(trace[3]['allocation'],(0,1))
        self.assertEqual(trace[3]['feeRecipients'],(2,))
        self.assertEqual(result['leaves'][0]['state'].accounts.fee_expense,2.)

    def test_future_labels_and_declared_bid_vectors_do_not_reveal_demand(self):
        c,s,b=fixture()
        low=scenario((replace(b,funded_demands=(0,)),OpenBook('sales'),SettleBook('sales',(0,))),.5)
        high=scenario((replace(b,funded_demands=(1,)),OpenBook('sales'),SettleBook('sales',(1,))),.5)
        result=solve(c,s,(low,high),funding=one_unit_funding)
        self.assertEqual(result['expectedValue'],0.)
        with self.assertRaisesRegex(ValueError,'calendars/labels'):
            solve(c,s,(low,replace(high,events=(replace(b,label='high-demand'),*high.events[1:]))),funding=one_unit_funding)

    def test_canonical_offer_order_prevents_scenario_order_information(self):
        c,s,b=fixture()
        a=replace(b,offers=(Offer(0,1,3.,1),Offer(0,2,3.,1)),reliability=(.5,.5))
        reverse=replace(a,offers=tuple(reversed(a.offers)))
        low=scenario((a,OpenBook('sales'),SettleBook('sales',(0,))),.5)
        high=scenario((reverse,OpenBook('sales'),SettleBook('sales',(1,))),.5)
        result=solve(c,s,(low,high),funding=one_unit_funding)
        self.assertEqual(result['expectedValue'],0.)
        self.assertEqual([leaf['trace'][0]['allocation'] for leaf in result['leaves']],[(0,0),(0,0)])

    def test_complement_buffer_value_depends_on_future_supply_and_cash(self):
        line=Line((1,1),2,.25,3.,0.,(0.,)*5,1.,output_qty=2)
        c=Company((1.,1.),(2,2),8.,(line,),(4,),0.)
        s=State(11.,(0,0),(0.,0.),(0,),(0.,),(3.,),(-1,-1))
        first=Purchase('A-now',(Offer(0,1,1.,2),),(),(.5,),1.,0.,(0,),0.)
        future=replace(first,label='B-later',offers=(Offer(1,2,4.,2),))
        empty=replace(future,offers=(),reliability=())
        def single_quote_funding(company,state,event):
            assert len(event.offers)<=1
            return tuple(min(company.slots[o.material]-state.held[o.material],int(state.cash//o.price)) for o in event.offers)
        def path(event,weight):
            return Scenario(weight,(first,event,OpenBook('closing'),SettleBook('closing',(4,))),
                            ((0.,)*3,(0.,)*3),((0.,)*5,))
        certain=solve(c,s,(path(future,1.),),funding=single_quote_funding)
        self.assertEqual(certain['expectedValue'],1.)
        self.assertEqual(certain['leaves'][0]['trace'][0]['allocation'],(2,))
        self.assertEqual(certain['leaves'][0]['trace'][1]['allocation'],(2,))
        self.assertEqual(certain['leaves'][0]['state'].cash,12.)
        for chance,allocation,value in ((.5,(0,),0.),(.75,(2,),.25)):
            result=solve(c,s,(path(future,chance),path(empty,1-chance)),funding=single_quote_funding)
            self.assertEqual(result['expectedValue'],value)
            self.assertEqual([x['trace'][0]['allocation'] for x in result['leaves']],[allocation,allocation])

    def test_optimal_split_remains_in_full_action_space(self):
        line=Line((1,),8,0.,3.,0.,(0.,)*9,1.)
        c=Company((1.,),(8,),16.,(line,),(8,),0.)
        s=State(100.,(0,),(0.,),(0,),(0.,),(3.,),(7,))
        b=Purchase('split',(Offer(0,1,1.,2),Offer(0,2,2.,6),Offer(0,7,5.,8)),(),
                   (0.,0.,0.),1.,1.,(0,),0.)
        event_path=Scenario(1.,(b,OpenBook('retail'),SettleBook('retail',(8,))),((0.,)*9,),((0.,)*9,))
        result=solve(c,s,(event_path,),funding=lambda company,state,event:(8,)*len(event.offers))
        self.assertEqual(result['expectedValue'],9.)
        self.assertEqual(result['leaves'][0]['trace'][0]['allocation'],(2,6,0))
        self.assertEqual(result['leaves'][0]['state'].incumbents,(7,))
        self.assertEqual(result['leaves'][0]['state'].accounts.fee_expense,1.)

    def test_rent_is_charged_once_and_node_limits_fail_explicitly(self):
        c,s,b=fixture(price=1.,conversion=0.,quote=3.)
        c=replace(c,fixed_assets=2_000_000.)
        events=(replace(b,rent_bill=1.),OpenBook('sales'),SettleBook('sales',(1,)),Rent('rent',1.))
        result=solve(c,s,(scenario(events),),funding=one_unit_funding)
        self.assertEqual(result['expectedValue'],1.)
        self.assertEqual(result['leaves'][0]['state'].accounts.rent_charge,1.)
        with self.assertRaisesRegex(ValueError,'node limit'):
            solve(c,s,(scenario(events),),funding=one_unit_funding,max_nodes=1)


if __name__=='__main__':unittest.main()
