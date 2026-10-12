import unittest
from dataclasses import replace
from tools.buying_v2.industry_oracle import Line, Offer
from tools.buying_v2.phase_ledger import Company, State, Purchase, OpenBook, SettleBook, SharedSettleBook, SetQuotes, apply
from tools.buying_v2.phase_oracle import Scenario, solve


def fixture(quote=3.):
    lines=tuple(Line(recipe,1,.25,quote,0.,(0.,0.),1.) for recipe in ((1,0),(0,1)))
    c=Company((1.,1.),(1,1),8.,lines,(2,2),0.)
    s=State(10.,(0,0),(0.,0.),(0,0),(0.,0.),(quote,quote),(-1,-1))
    b=Purchase('buy',(Offer(0,10,1.,1),Offer(1,11,1.,1)),(),(0.,0.),1.,0.,(0,1),0.)
    return c,s,b


def path(b,sales,probability=1.):
    return Scenario(probability,(b,OpenBook('sales'),sales),((0.,0.),(0.,0.)),((0.,)*3,(0.,)*3))


class SharedSalesTests(unittest.TestCase):
    def test_shared_opportunity_changes_coupled_procurement(self):
        c,s,b=fixture()
        independent=solve(c,s,(path(b,SettleBook('sales',(1,1))),),funding='continuation')
        shared=solve(c,s,(path(b,SharedSettleBook('sales',(1,1),groups=((0,1),))),),funding='continuation')
        self.assertEqual(independent['expectedValue'],3.5)
        self.assertEqual(shared['expectedValue'],1.75)
        self.assertEqual(sum(independent['leaves'][0]['trace'][0]['allocation']),2)
        self.assertEqual(sum(shared['leaves'][0]['trace'][0]['allocation']),1)
        self.assertEqual(sum(shared['leaves'][0]['trace'][2]['sold']),1)

    def test_old_stock_consumes_shared_demand_before_new_output(self):
        c,s,b=fixture();s=replace(s,finished=(1,0),finished_basis=(.5,0.))
        result=solve(c,s,(path(b,SharedSettleBook('sales',(1,1),groups=((0,1),))),),funding='continuation')
        self.assertEqual(result['expectedValue'],3.)
        self.assertEqual(result['leaves'][0]['trace'][0]['allocation'],(0,0))
        self.assertEqual(result['leaves'][0]['state'].accounts.cogs,.5)

    def test_frozen_quotes_fallback_and_accounting(self):
        c,s,_=fixture();c=replace(c,finished_caps=(10,10),storage=40.)
        s=replace(s,finished=(2,8),finished_basis=(.5,1.),quotes=(2.,3.))
        opened,_=apply(c,s,OpenBook('sales'))
        changed,_=apply(c,opened,SetQuotes('new',(20.,30.)))
        end,detail=apply(c,changed,SharedSettleBook('sales',(10,8),fee_income=2.,groups=((1,0),)))
        self.assertEqual(detail['sold'],(2,6))
        self.assertEqual(detail['sales'],22.)
        self.assertEqual(detail['cogs'],7.)
        self.assertEqual(detail['groupSales'],(8,))
        self.assertEqual(end.cash,34.)
        self.assertEqual(end.finished,(0,2))
        self.assertEqual(end.accounts.earnings,17.)

    def test_no_hidden_future_demand_information(self):
        c,s,b=fixture(quote=2.)
        scenarios=tuple(path(b,SharedSettleBook('sales',(q,q),groups=((0,1),)),.5) for q in (0,2))
        result=solve(c,s,scenarios,funding='continuation')
        self.assertEqual(result['expectedValue'],0.)
        self.assertEqual([x['trace'][0]['allocation'] for x in result['leaves']],[(0,0),(0,0)])
        known=solve(c,s,(replace(scenarios[1],probability=1.),),funding='continuation')
        self.assertEqual(known['expectedValue'],1.5)

    def test_groups_partition_and_quote_consistency(self):
        c,s,_=fixture();opened,_=apply(c,s,OpenBook('sales'))
        for groups in ((),((0,),),((0,0),(1,)),((0,2),),((0,1),())):
            with self.assertRaisesRegex(ValueError,'partition'):
                apply(c,opened,SharedSettleBook('sales',(1,1),groups=groups))
        with self.assertRaisesRegex(ValueError,'frozen quotes'):
            apply(c,opened,SharedSettleBook('sales',(1,2),groups=((0,1),)))
        # Separate product groups retain independent sales semantics.
        s=replace(s,finished=(1,1));opened,_=apply(c,s,OpenBook('sales'))
        a,_=apply(c,opened,SettleBook('sales',(1,1),fee_income=2.))
        b,_=apply(c,opened,SharedSettleBook('sales',(1,1),fee_income=2.,groups=((0,),(1,))))
        self.assertEqual(a,b)

    def test_shared_sales_fee_income_is_removed_only_in_neutral_funding(self):
        # Inherited settlement type keeps the neutral counterfactual's fee
        # removal while actual settlement still posts the real transfer.
        c,s,b=fixture()
        result=solve(c,s,(path(b,SharedSettleBook('sales',(1,1),fee_income=2.,groups=((0,1),))),),
                     funding='continuation-transfer-neutral')
        self.assertEqual(result['expectedValue'],3.75)
        self.assertEqual(result['leaves'][0]['state'].accounts.fee_income,2.)
        vectors=result['leaves'][0]['trace'][0]['funding']['quoteVectors']
        self.assertTrue(all(x['conditionalValue']==1.75 for x in vectors))


if __name__=='__main__':unittest.main()
