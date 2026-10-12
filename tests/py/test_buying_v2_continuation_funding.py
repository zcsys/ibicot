import itertools
import math
import random
import unittest
from dataclasses import replace
from tools.buying_v2.industry_oracle import Line, Offer
from tools.buying_v2.phase_ledger import Company, State, Purchase, OpenBook, SettleBook, Rent
from tools.buying_v2.phase_oracle import Scenario, solve


def fixture(slots=(4,2),cash=4.,prices=(1.,2.),conversion=.5,quote=5.,batches=2,demand=2,held=None,basis=None,output_qty=1):
    n=len(slots);held=held or (0,)*n;basis=basis or (0.,)*n
    line=Line((1,)*n,batches,conversion,quote,0.,(0.,)*(batches*output_qty+1),1.,output_qty)
    c=Company((1.,)*n,slots,float(sum(slots)+batches*output_qty),(line,),(batches*output_qty,),0.)
    s=State(cash,held,basis,(0,),(0.,),(quote,),(-1,)*n)
    offers=tuple(Offer(m,m+1,p,slots[m]) for m,p in enumerate(prices))
    b=Purchase('buy',offers,(),(.5,)*n,1.,0.,(0,),0.)
    path=Scenario(1.,(b,OpenBook('sales'),SettleBook('sales',(demand,))),
                  tuple((0.,)*(cap+1) for cap in slots),((0.,)*(batches*output_qty+1),))
    return c,s,path


def first(result):
    return result['leaves'][0]['trace'][0]


class ContinuationFundingTests(unittest.TestCase):
    def test_joint_complements_and_conversion_cash(self):
        c,s,path=fixture()
        result=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(result)['funding']['jointQuantities'],(1,1))
        self.assertEqual(first(result)['fundedDemands'],(1,1))
        self.assertEqual(first(result)['allocation'],(1,1))
        self.assertEqual(result['expectedValue'],1.5)
        c,s,path=fixture(slots=(10,),cash=10.,prices=(1.,),conversion=1.,quote=4.,batches=10,demand=10)
        result=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(result)['fundedDemands'],(5,))
        self.assertEqual(first(result)['allocation'],(5,))
        self.assertEqual(result['expectedValue'],10.)

    def test_sales_and_owned_basis_can_reduce_funding_to_zero(self):
        c,s,path=fixture(slots=(8,),cash=20.,prices=(1.,),conversion=.25,quote=4.,batches=8,demand=1)
        result=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(result)['fundedDemands'],(1,))
        s=replace(s,finished=(1,),finished_basis=(1.,))
        result=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(result)['fundedDemands'],(0,))
        self.assertEqual(first(result)['allocation'],(0,))
        c,s,path=fixture(slots=(1,1),cash=10.,prices=(100.,1.),conversion=.25,quote=3.,batches=1,demand=1,
                         held=(1,0),basis=(100.,0.))
        result=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(result)['fundedDemands'],(0,0))
        self.assertEqual(first(result)['allocation'],(0,0))

    def test_funding_ignores_current_stock_but_actual_selection_does_not(self):
        c,s,path=fixture(slots=(3,),cash=20.,prices=(2.,),conversion=0.,quote=4.,batches=3,demand=3)
        s=replace(s,incumbents=(7,))
        b=replace(path.events[0],offers=(Offer(0,7,2.,2),Offer(0,2,1.,3)),reliability=(0.,0.),fee_multiple=5.)
        path=replace(path,events=(b,*path.events[1:]))
        result=solve(c,s,(path,),funding='continuation')
        trace=first(result)
        self.assertEqual(trace['funding']['referenceSuppliers'],(7,))
        self.assertEqual(trace['funding']['jointQuantities'],(3,))
        self.assertEqual(trace['fundedDemands'],(3,3))
        self.assertEqual(trace['allocation'],(3,0))  # canonical supplier order 2,7
        self.assertEqual(trace['fees'],(0.,))
        self.assertEqual(result['expectedValue'],9.)
        # One more incumbent unit activates the fee. Goods-only intentions stay
        # at three, while actual selection now prefers the incumbent.
        b=replace(b,offers=(replace(b.offers[0],stock=3),b.offers[1]))
        result=solve(c,s,(replace(path,events=(b,*path.events[1:])),),funding='continuation')
        self.assertEqual(first(result)['fundedDemands'],(3,3))
        self.assertEqual(first(result)['allocation'],(0,3))
        self.assertEqual(result['expectedValue'],6.)

    def test_unprofitable_incumbent_quote_does_not_create_positive_fee_bid(self):
        c,s,path=fixture(slots=(3,),cash=5.,prices=(4.,),conversion=0.,quote=3.,batches=3,demand=3)
        s=replace(s,incumbents=(7,))
        b=replace(path.events[0],offers=(Offer(0,7,4.,3),Offer(0,2,1.,3)),reliability=(0.,0.),fee_multiple=100.)
        result=solve(c,s,(replace(path,events=(b,*path.events[1:])),),funding='continuation')
        self.assertEqual(first(result)['funding']['referenceDemands'],(0,))
        self.assertEqual(first(result)['fundedDemands'],(3,0))
        self.assertEqual(first(result)['fees'],(0.,))
        self.assertEqual(result['expectedValue'],6.)

    def test_hidden_demand_cannot_leak_into_quote_funding(self):
        c,s,path=fixture(slots=(1,),cash=10.,prices=(3.,),conversion=.25,quote=4.,batches=1,demand=1)
        low=replace(path,probability=.5,events=(*path.events[:-1],SettleBook('sales',(0,))))
        high=replace(path,probability=.5)
        result=solve(c,s,(low,high),funding='continuation')
        self.assertEqual(result['expectedValue'],0.)
        for leaf in result['leaves']:
            self.assertEqual(leaf['trace'][0]['fundedDemands'],(0,))
            self.assertEqual(leaf['trace'][0]['allocation'],(0,))
        certain=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(certain)['fundedDemands'],(1,))
        self.assertEqual(certain['expectedValue'],.75)

    def test_joint_buffer_funding_responds_to_conditional_supply(self):
        c,s,path=fixture(slots=(2,2),cash=11.,prices=(1.,4.),conversion=.25,quote=3.,batches=2,demand=4,output_qty=2)
        original=path.events[0]
        now=replace(original,offers=(original.offers[0],),reliability=(.5,))
        later=replace(original,label='later',offers=(original.offers[1],),reliability=(.5,))
        absent=replace(later,offers=(),reliability=())
        def branch(event,probability):
            return replace(path,probability=probability,events=(now,event,*path.events[1:]))
        for chance,quantity,value in ((.5,0,0.),(.75,2,.25),(1.,2,1.)):
            result=solve(c,s,(branch(later,chance),branch(absent,1-chance)),funding='continuation')
            self.assertEqual(result['expectedValue'],value)
            for leaf in result['leaves']:
                self.assertEqual(leaf['trace'][0]['fundedDemands'],(quantity,))
                self.assertEqual(leaf['trace'][0]['allocation'],(quantity,))

    def test_receipts_are_not_advanced_by_funding(self):
        c,s,path=fixture(slots=(1,),cash=0.,prices=(1.,),conversion=.25,quote=4.,batches=1,demand=1)
        c=replace(c,finished_caps=(2,),storage=4.)
        s=replace(s,finished=(1,))
        terminal=((0.,)*3,)
        b=path.events[0]
        before=replace(path,finished_values=terminal,events=(OpenBook('old'),b,SettleBook('old',(1,)),
            OpenBook('closing'),SettleBook('closing',(1,))))
        after=replace(before,events=(OpenBook('old'),SettleBook('old',(1,)),b,OpenBook('closing'),SettleBook('closing',(1,))))
        early=solve(c,s,(before,),funding='continuation')
        late=solve(c,s,(after,),funding='continuation')
        self.assertEqual(early['leaves'][0]['trace'][1]['fundedDemands'],(0,))
        self.assertEqual(late['leaves'][0]['trace'][2]['fundedDemands'],(1,))
        self.assertEqual(early['expectedValue'],4.)
        self.assertEqual(late['expectedValue'],6.75)

    def test_lots_and_node_budget_apply_to_funding_queries(self):
        c,s,path=fixture(slots=(4,),cash=10.,prices=(1.,),conversion=0.,quote=3.,batches=3,demand=3)
        b=replace(path.events[0],offers=(Offer(0,1,1.,6,2),Offer(0,2,1.5,4,1)),reliability=(.5,.5))
        path=replace(path,events=(b,*path.events[1:]))
        result=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(result)['fundedDemands'],(4,3))
        self.assertEqual(first(result)['allocation'],(2,1))
        self.assertEqual(result['expectedValue'],5.5)
        with self.assertRaisesRegex(ValueError,'node limit'):
            solve(c,s,(path,),funding='continuation',max_nodes=1)

    def test_current_fee_free_funding_still_accounts_for_future_real_fees(self):
        c,s,path=fixture(slots=(1,),cash=10.,prices=(1.,),conversion=0.,quote=5.,batches=1,demand=1)
        s=replace(s,incumbents=(7,))
        b=replace(path.events[0],offers=(Offer(0,7,4.,1),Offer(0,2,1.,1)),reliability=(0.,0.),fee_multiple=1.)
        future=replace(b,label='later',offers=(Offer(0,7,1.,1),Offer(0,2,4.,1)))
        events=(b,OpenBook('sales'),SettleBook('sales',(1,)),future,OpenBook('later-sales'),SettleBook('later-sales',(1,)))
        result=solve(c,s,(replace(path,events=events),),funding='continuation')
        self.assertEqual(result['expectedValue'],6.)
        trace=result['leaves'][0]['trace']
        self.assertEqual(trace[0]['feeRecipients'],(7,))
        self.assertEqual(trace[3]['feeRecipients'],(2,))
        self.assertEqual(result['leaves'][0]['state'].accounts.fee_expense,2.)
        # Rent is a real later expense, not an extra copy of gate overhead.
        c=replace(c,fixed_assets=2_000_000.)
        b=replace(b,offers=(Offer(0,7,1.,1),),reliability=(0.,),rent_bill=1.)
        result=solve(c,s,(replace(path,events=(b,*path.events[1:],Rent('bill',1.))),),funding='continuation')
        self.assertEqual(result['expectedValue'],3.)
        self.assertEqual(result['leaves'][0]['state'].accounts.rent_charge,1.)

    def test_cash_truncation_fee_incentive_is_exposed_not_hidden(self):
        # Buying one extra A unit leaves $5: enough for the incumbent's $5
        # goods quote but not its additional $0.25 conversion, waiving a $3 fee. This is a consequence
        # of the frozen feasible-bid contract, not a desirable-model assertion.
        c,s,path=fixture(slots=(3,1),cash=7.,prices=(1.,5.),conversion=.25,quote=10.,batches=1,demand=1)
        s=replace(s,incumbents=(-1,7))
        now=replace(path.events[0],offers=(Offer(0,1,1.,3),),reliability=(0.,))
        later=replace(now,label='later',offers=(Offer(1,7,5.,1),Offer(1,2,1.,1)),reliability=(0.,0.),fee_multiple=3.)
        events=(now,later,*path.events[1:])
        result=solve(c,s,(replace(path,events=events),),funding='continuation')
        trace=result['leaves'][0]['trace']
        self.assertEqual(trace[0]['allocation'],(2,))
        self.assertEqual(trace[1]['fundedDemands'],(1,0))
        self.assertEqual(trace[1]['fees'],(0.,0.))
        self.assertEqual(result['leaves'][0]['state'].held,(1,0))
        self.assertEqual(result['expectedValue'],6.75)
        no_fee=replace(later,fee_multiple=0.)
        control=solve(c,s,(replace(path,events=(now,no_fee,*path.events[1:])),),funding='continuation')
        self.assertEqual(first(control)['allocation'],(1,))
        self.assertEqual(control['expectedValue'],7.75)

    def test_quote_queries_keep_other_markets_flexible(self):
        # At A=$1/B=$2, $5 funds one kit after conversion. The discovered B=$1
        # quote makes two kits feasible. Fixing B to its incumbent quote while
        # funding A would cap A at one and discard that useful second kit.
        c,s,path=fixture(slots=(2,2),cash=5.,prices=(1.,2.),conversion=.5,quote=5.,batches=2,demand=2)
        s=replace(s,incumbents=(1,2))
        event=replace(path.events[0],offers=(Offer(0,1,1.,2),Offer(1,2,2.,2),Offer(1,3,1.,2)),
                      reliability=(.5,.5,.5))
        path=replace(path,events=(event,*path.events[1:]))
        old=solve(c,s,(path,),funding='continuation-reference-v1')
        new=solve(c,s,(path,),funding='continuation')
        self.assertEqual(first(old)['fundedDemands'],(1,1,2))
        self.assertEqual(first(old)['allocation'],(1,0,1))
        self.assertEqual(old['expectedValue'],2.5)
        self.assertEqual(first(new)['fundedDemands'],(2,1,2))
        self.assertEqual(first(new)['allocation'],(2,0,2))
        self.assertEqual(new['expectedValue'],5.)
        self.assertEqual(first(new)['funding']['jointQuantities'],(2,2))
        for record in first(new)['funding']['quoteVectors']:
            self.assertLessEqual(record['goods'],s.cash)

    def test_single_quote_markets_match_independent_exhaustive_economics(self):
        rng=random.Random(7031)
        for case in range(100):
            slots=tuple(rng.randint(1,4) for _ in range(2))
            held=tuple(rng.randint(0,min(2,cap)) for cap in slots)
            basis=tuple(rng.choice((1.,2.,3.)) for _ in slots)
            prices=tuple(rng.choice((.5,1.,2.,3.)) for _ in slots)
            cash=rng.randint(0,48)/4;conversion=rng.choice((.25,.5,1.));batches=rng.randint(1,3)
            demand=rng.randint(0,batches);quote=20.
            c,s,path=fixture(slots,cash,prices,conversion,quote,batches,demand,held,basis)
            candidates=[]
            for quantities in itertools.product(*(range(cap-h+1) for cap,h in zip(slots,held))):
                paid=sum(q*p for q,p in zip(quantities,prices))
                if paid>cash:continue
                # Quotes are deliberately far above every possible basis cost,
                # so the independently calculated production ramp is always full.
                made=min(batches,*(q+h for q,h in zip(quantities,held)),math.floor((cash-paid)/conversion))
                value=min(made,demand)*quote-paid-made*conversion
                candidates.append(((-value,paid,sum(quantities),quantities),value,quantities))
            _,expected,allocation=min(candidates)
            result=solve(c,s,(path,),funding='continuation')
            with self.subTest(case=case):
                self.assertAlmostEqual(result['expectedValue'],expected)
                self.assertEqual(first(result)['allocation'],allocation)
                self.assertEqual(first(result)['funding']['jointQuantities'],allocation)


if __name__=='__main__':unittest.main()
