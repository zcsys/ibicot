import unittest
from dataclasses import replace
from tools.buying_v2.industry_oracle import Line,Offer
from tools.buying_v2.phase_ledger import Company,State,Purchase,OpenBook,SettleBook,SetQuotes
from tools.buying_v2.phase_oracle import Scenario,solve


def fixture(second_stock=1):
    line=Line((1,),1,.25,3.,0.,(0.,0.),1.)
    c=Company((1.,),(1,),4.,(line,),(2,),0.)
    s=State(10.,(0,),(0.,),(0,),(0.,),(3.,),(-1,))
    b=Purchase('first',(Offer(0,1,1.,1),),(),(0.,),1.,0.,(0,),0.)
    second=replace(b,label='second',offers=(Offer(0,1,1.,second_stock),))
    events=(b,OpenBook('early'),SettleBook('early',(1,)),SetQuotes('lower',(2.,)),
            second,OpenBook('late'),SettleBook('late',(1,)))
    return c,s,Scenario(1.,events,((0.,0.),),((0.,)*3,))


class PersistentSupplyTests(unittest.TestCase):
    def test_consumed_stock_cannot_be_sold_again_and_arrivals_restore_it(self):
        c,s,path=fixture()
        old=solve(c,s,(path,),funding='continuation')
        carried=solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
        self.assertEqual(old['expectedValue'],2.5)
        self.assertEqual(carried['expectedValue'],1.75)
        trace=carried['leaves'][0]['trace']
        self.assertEqual(trace[0]['allocation'],(1,))
        self.assertEqual(trace[4]['observedStocks'],(0,))
        self.assertEqual(trace[4]['allocation'],(0,))
        c,s,path=fixture(2)
        restored=solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
        self.assertEqual(restored['expectedValue'],2.5)
        self.assertEqual(restored['leaves'][0]['trace'][4]['observedStocks'],(1,))

    def test_depleted_incumbent_waives_fee_against_live_stock(self):
        c,s,path=fixture();s=replace(s,quotes=(10.,))
        events=list(path.events);events[3]=SetQuotes('lower',(10.,))
        events[4]=replace(events[4],offers=(Offer(0,1,5.,1),Offer(0,2,1.,1)),reliability=(0.,0.),fee_multiple=2.)
        path=replace(path,events=tuple(events))
        old=solve(c,s,(path,),funding='continuation')
        new=solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
        self.assertEqual(old['leaves'][0]['state'].accounts.fee_expense,2.)
        self.assertEqual(new['leaves'][0]['state'].accounts.fee_expense,0.)
        self.assertEqual(new['expectedValue']-old['expectedValue'],2.)
        self.assertEqual(new['leaves'][0]['trace'][4]['observedStocks'],(0,1))

    def test_unobserved_future_arrivals_do_not_reveal_themselves_early(self):
        c,s,path=fixture();_,_,restock=fixture(2)
        result=solve(c,s,(replace(path,probability=.5),replace(restock,probability=.5)),
                     funding='continuation',supply='persistent-arrivals')
        self.assertEqual(result['expectedValue'],(1.75+2.5)/2)
        self.assertEqual([x['trace'][0]['allocation'] for x in result['leaves']],[(1,),(1,)])
        self.assertEqual([x['trace'][4]['allocation'] for x in result['leaves']],[(0,),(1,)])

    def test_stock_relaxed_funding_does_not_consume_future_arrivals(self):
        c,s,path=fixture()
        events=list(path.events);events[0]=replace(events[0],offers=(Offer(0,1,1.,0),))
        path=replace(path,events=tuple(events))
        result=solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
        # The counterfactual may add a current unit, but it cannot remove the
        # separately specified one-unit arrival at the next purchasing phase.
        first=result['leaves'][0]['trace'][0]
        self.assertEqual(first['fundedDemands'],(1,))
        self.assertEqual(first['allocation'],(0,))
        self.assertEqual(first['funding']['quoteVectors'][0]['conditionalValue'],2.5)
        self.assertEqual(result['expectedValue'],.75)

    def test_small_cases_against_independent_two_action_enumeration(self):
        for initial_stock in (0,1,2):
            for arrival in (0,1,2):
                for first_quote in (2.,4.):
                    c,s,path=fixture(initial_stock+arrival)
                    s=replace(s,quotes=(first_quote,))
                    events=list(path.events)
                    events[0]=replace(events[0],offers=(Offer(0,1,1.,initial_stock),))
                    path=replace(path,events=tuple(events))
                    values=[a*(first_quote-1.25)+b*(2.-1.25)
                            for a in (0,1) for b in (0,1)
                            if a<=initial_stock and a+b<=initial_stock+arrival]
                    result=solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
                    self.assertEqual(result['expectedValue'],max(values))

    def test_invalid_supply_contract_and_preserved_input(self):
        c,s,path=fixture(0)
        with self.assertRaisesRegex(ValueError,'nondecreasing'):
            solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
        c,s,path=fixture();original=repr(path)
        solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
        self.assertEqual(repr(path),original)
        with self.assertRaisesRegex(ValueError,'supply mode'):
            solve(c,s,(path,),funding='continuation',supply='unknown')


if __name__=='__main__':unittest.main()
