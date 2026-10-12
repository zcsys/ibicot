import unittest
from dataclasses import replace
from tools.buying_v2.industry_oracle import Line, Offer
from tools.buying_v2.phase_ledger import (Accounts, Company, State, Purchase, OpenBook,
    SettleBook, SetQuotes, Rent, EndTick, apply, replay, equity, horizon_value)


def company(fixed=0.,lines=None):
    lines=lines or (Line((1,),5,.5,3.,0.,(0.,)*6,1.),)
    return Company((1.,),(20,),40.,lines,(10,)*len(lines),fixed)


def state(cash=10.,held=(0,),basis=(0.,),finished=(0,),finished_basis=(0.,),quotes=(3.,),incumbents=(-1,),**extra):
    return State(cash,held,basis,finished,finished_basis,quotes,incumbents,**extra)


def buy(offers=(Offer(0,1,1.,5),),demands=(5,),active=(0,),**changes):
    args=dict(label='buy',offers=offers,funded_demands=demands,reliability=(.5,)*len(offers),
              fee_unit_cost=1.,fee_multiple=0.,active_lines=active,rent_bill=0.)
    args.update(changes)
    return Purchase(**args)


class PhaseLedgerTests(unittest.TestCase):
    def test_goods_and_conversion_are_capitalized_not_immediate_losses(self):
        c=company();s=state(cash=5.)
        end,detail=apply(c,s,buy(),(3,))
        self.assertEqual(end.cash,.5)
        self.assertEqual(end.finished,(3,))
        self.assertEqual(end.finished_basis,(1.5,))
        self.assertEqual(end.accounts.earnings,0.)
        self.assertEqual(equity(c,s),equity(c,end))
        self.assertEqual(detail['conversion'],1.5)

    def test_open_book_excludes_new_output_and_preserves_old_basis_and_quote(self):
        line=Line((1,),1,1.,10.,0.,(0.,0.),1.)
        c=company(lines=(line,));s=state(held=(1,),basis=(4.,),finished=(1,),finished_basis=(1.,),quotes=(10.,))
        events=(OpenBook('C3'),buy(offers=(),demands=()),SetQuotes('pricing',(20.,)),
                SettleBook('C3',(2,)),OpenBook('C4'),SettleBook('C4',(2,)))
        end,trace=replay(c,s,events,{1:()})
        self.assertEqual(trace[3]['sold'],(1,))
        self.assertEqual(trace[3]['sales'],10.)
        self.assertEqual(trace[3]['cogs'],1.)
        self.assertEqual(trace[4]['openingBasis'],(5.,))
        self.assertEqual(trace[5]['sold'],(1,))
        self.assertEqual(trace[5]['sales'],20.)
        self.assertEqual(trace[5]['cogs'],5.)
        self.assertEqual(end.cash,39.)
        self.assertEqual(end.accounts.earnings,24.)
        self.assertEqual(equity(c,end)-equity(c,s),24.)

    def test_deferred_receipts_cannot_finance_earlier_production(self):
        line=Line((1,),2,1.,3.,0.,(0.,)*3,1.)
        c=company(lines=(line,));s=state(cash=1.,finished=(1,),finished_basis=(.5,))
        opened,_=apply(c,s,OpenBook('C3'))
        before,detail=apply(c,opened,buy(demands=(1,)),(1,))
        self.assertEqual(before.held,(1,))
        self.assertEqual(detail['outputs'],(0,))
        self.assertEqual(before.cash,0.)
        received,_=apply(c,before,SettleBook('C3',(1,)))
        after,later=apply(c,received,buy(offers=(),demands=(),label='next-phase'),())
        self.assertEqual(later['outputs'],(1,))
        self.assertEqual(after.cash,2.)
        # Retail settles before manufacturing, so the same old-stock receipt
        # can instead fund current production if its actual event occurs first.
        settled,_=apply(c,opened,SettleBook('C3',(1,)))
        immediate,now=apply(c,settled,buy(demands=(1,)),(1,))
        self.assertEqual(now['outputs'],(1,))
        self.assertEqual(immediate.cash,2.)

    def test_split_preference_and_original_incumbent_fee(self):
        c=company();s=state(cash=100.,incumbents=(7,))
        event=buy(offers=(Offer(0,1,1.,2),Offer(0,2,2.,8),Offer(0,7,3.,10)),
                  demands=(10,8,10),active=(),fee_multiple=2.)
        end,detail=apply(c,s,event,(2,6,0))
        self.assertEqual(end.incumbents,(7,))
        self.assertEqual(detail['fees'],(3.,))
        self.assertEqual(detail['feeRecipients'],(7,))
        self.assertEqual(end.cash,83.)
        self.assertEqual(end.accounts.earnings,-3.)
        complete,detail=apply(c,s,event,(0,8,0))
        self.assertEqual(complete.incumbents,(2,))
        self.assertEqual(detail['feeRecipients'],(7,))
        self.assertEqual(detail['fees'],(3.,))
        # Next order pays the new original incumbent, not the old one.
        event2=buy(label='next-phase',offers=(Offer(0,2,2.,2),Offer(0,8,1.,2)),demands=(2,2),active=(),fee_multiple=2.)
        again,d2=apply(c,complete,event2,(0,2))
        self.assertEqual(d2['feeRecipients'],(2,))
        self.assertEqual(again.incumbents,(8,))

    def test_incumbent_shortage_waives_fee_independently_of_preference(self):
        c=company();s=state(cash=100.,incumbents=(7,))
        event=buy(offers=(Offer(0,7,3.,3,4),Offer(0,2,1.,8,4)),demands=(4,8),active=(),fee_multiple=9.)
        end,detail=apply(c,s,event,(0,8))
        self.assertEqual(detail['fees'],(0.,))
        self.assertEqual(end.incumbents,(2,))
        with self.assertRaisesRegex(ValueError,'whole-lot'):
            apply(c,s,replace(event,funded_demands=(3,8)),(0,8))

    def test_rent_threshold_arrears_suspension_and_zero_rate_collection(self):
        c=company(fixed=2_000_000.)
        start=state(cash=0.,finished=(1,),finished_basis=(0.,),quotes=(10.,))
        charged,first=apply(c,start,Rent('tick1',4.))
        self.assertTrue(first['eligible'])
        self.assertEqual(charged.arrears,4.)
        next_tick,_=apply(c,charged,EndTick('tick1-end',.15))
        suspended,next_bill=apply(c,next_tick,Rent('tick2',4.))
        self.assertFalse(next_bill['eligible'])
        self.assertEqual(suspended.arrears,4.)
        self.assertEqual(suspended.accounts.rent_charge,4.)
        next_tick,_=apply(c,suspended,EndTick('tick2-end',.15))
        opened,_=apply(c,next_tick,OpenBook('retail'))
        sold,_=apply(c,opened,SettleBook('retail',(1,)))
        collected,detail=apply(c,sold,Rent('zero-rate',0.))
        self.assertEqual(collected.cash,6.)
        self.assertEqual(collected.arrears,0.)
        self.assertEqual(detail['paid'],4.)
        self.assertEqual(collected.accounts.earnings,6.)
        self.assertEqual(horizon_value(start,collected,((0.,),),((0.,),)),6.)

    def test_terminal_liability_prevents_free_unpaid_rent(self):
        c=company(fixed=2_000_000.);s=state(cash=0.)
        end,_=apply(c,s,Rent('bill',4.))
        self.assertEqual(end.cash,s.cash)
        self.assertEqual(horizon_value(s,end,((0.,),),((0.,),)),-4.)

    def test_old_arrears_payment_is_liquidity_use_not_new_expense(self):
        c=company(fixed=2_000_004.);s=state(cash=10.,arrears=4.)
        end,_=apply(c,s,Rent('old-debt',0.))
        self.assertEqual(end.cash,6.)
        self.assertEqual(end.accounts.earnings,0.)
        self.assertEqual(horizon_value(s,end,((0.,),),((0.,),)),0.)

    def test_gate_snapshot_timing_and_actual_bill_are_distinct(self):
        line=Line((1,),1,0.,1.5,0.,(0.,0.),1.)
        c=company(fixed=1_999_990.,lines=(line,));s=state(quotes=(1.5,),incumbents=(7,))
        event=buy(offers=(Offer(0,7,2.,1),Offer(0,2,1.,1)),demands=(1,1),
                  reliability=(0.,0.),fee_multiple=2.,rent_bill=1.)
        before,d0=apply(c,s,event,(0,1))
        after,d1=apply(c,s,replace(event,overhead_timing='after'),(0,1))
        self.assertEqual(d0['gateOverhead'],1.)
        self.assertEqual(d1['gateOverhead'],0.)
        self.assertEqual(d0['outputs'],(0,))
        self.assertEqual(d1['outputs'],(1,))
        for result in (before,after):
            billed,detail=apply(c,result,Rent('actual',1.))
            self.assertEqual(detail['charge'],0.)
            self.assertEqual(billed.accounts.rent_charge,0.)
            self.assertEqual(billed.accounts.earnings,-2.)

    def test_fee_income_arrives_only_at_book_settlement_and_ema_updates_at_end(self):
        c=company();s=state(cash=0.,switching_net_ema=0.)
        opened,_=apply(c,s,OpenBook('C4'))
        settled,_=apply(c,opened,SettleBook('C4',(0,),fee_income=8.))
        self.assertEqual(opened.cash,0.)
        self.assertEqual(settled.cash,8.)
        self.assertEqual(settled.switching_net_ema,0.)
        ended,_=apply(c,settled,EndTick('year1-tick1',.25))
        self.assertEqual(ended.switching_net_ema,2.)
        self.assertEqual(ended.tick_fee_income,0.)
        idle,d=apply(c,ended,buy(offers=(),demands=()),())
        self.assertEqual(d['gateOverhead'],-2.)
        self.assertEqual(idle.cash,8.)  # Forecast income is not cash.

    def test_multiline_installed_order_shares_inputs_and_cash(self):
        line=Line((1,),2,1.,5.,0.,(0.,)*3,1.)
        c=company(lines=(line,line));s=state(cash=2.,held=(2,),basis=(1.,),
            finished=(0,0),finished_basis=(0.,0.),quotes=(5.,5.))
        end,detail=apply(c,s,buy(offers=(),demands=(),active=(1,0)),())
        self.assertEqual(detail['outputs'],(2,0))
        self.assertEqual(end.cash,0.)
        self.assertEqual(end.held,(0,))

    def test_invalid_events_leave_immutable_input_unchanged(self):
        c=company();s=state()
        with self.assertRaisesRegex(ValueError,'infeasible'):
            apply(c,s,buy(),(6,))
        with self.assertRaisesRegex(ValueError,'allocation'):
            apply(c,s,buy(),(.5,))
        with self.assertRaisesRegex(ValueError,'missing/mismatched'):
            apply(c,s,SettleBook('never-opened',(1,)))
        opened,_=apply(c,s,OpenBook('C3'))
        with self.assertRaisesRegex(ValueError,'overlap'):
            apply(c,opened,OpenBook('C4'))
        purchased,_=apply(c,s,buy(),(1,))
        with self.assertRaisesRegex(ValueError,'already completed'):
            apply(c,purchased,buy(),(1,))
        billed,_=apply(c,s,Rent('bill',0.))
        with self.assertRaisesRegex(ValueError,'duplicate rent'):
            apply(c,billed,Rent('second-bill',0.))
        with self.assertRaisesRegex(ValueError,'new tick'):
            apply(c,billed,OpenBook('late-retail'))
        self.assertEqual(s,state())

    def test_frozen_stock_basis_and_receipts_match_actual_input_book_settlement(self):
        from economy.core import model as M
        from economy.core.state import reset_world
        from economy.kernel.input_market import InputMarket
        cfg,w=reset_world(dict(t2FirmCount=4200,distributorCount=1))
        line_id=next(i for i in range(int(w.t2LineCount)) if M.T2_PRODUCTS[int(w.t2LineProduct[i])]['complexity']==3)
        firm=int(w.t2LineFirm[line_id])
        w.t2Fin[line_id]=1.;w.t2FinBasis[line_id]=1.;w.t2Price[line_id]=10.;w.t2Cash[firm]=10.
        book=InputMarket(w,1)
        supplier=book.n1+line_id
        # Simulate a production posting between book opening and settlement:
        # one extra output at basis 5 and conversion cash 1. This test compares
        # book accounting, not the catalog recipe that produced that unit.
        w.t2Fin[line_id]=2.;w.t2FinBasis[line_id]=3.;w.t2Cash[firm]=9.;w.t2Price[line_id]=20.
        book.fin[supplier]-=1;book.sold[supplier]+=1;book.revenue[supplier]+=10;book.cogs[supplier]+=1
        book.cash[book.owner[supplier]]+=10
        book.settle()
        c=company(lines=(Line((1,),1,1.,10.,0.,(0.,0.),1.),))
        s=state(held=(1,),basis=(4.,),finished=(1,),finished_basis=(1.,),quotes=(10.,))
        end,trace=replay(c,s,(OpenBook('C3'),buy(offers=(),demands=()),SetQuotes('price',(20.,)),SettleBook('C3',(1,))),{1:()})
        self.assertEqual(end.cash,w.t2Cash[firm])
        self.assertEqual(end.finished[0],w.t2Fin[line_id])
        self.assertEqual(end.finished_basis[0],w.t2FinBasis[line_id])
        self.assertEqual(end.accounts.sales,w.t2Revenue[line_id])
        self.assertEqual(end.accounts.cogs,w.t2COGS[line_id])

    def test_rent_matches_executed_kernel_at_threshold_and_cash_boundaries(self):
        from economy.core import model as M
        from economy.core.state import reset_world
        from economy.kernel import tick as K
        for target in (1_999_999.,2_000_000.,2_000_001.):
            for cash,debt,rate in ((0.,0.,1.008),(3.,5.,1.008),(100.,5.,0.)):
                cfg,w=reset_world(dict(t2FirmCount=1,distributorCount=1))
                cfg['storageRentPerUnitYear']=rate
                w.t2Raw.fill(0);w.t2T1Raw.fill(0);w.t2Fin.fill(0)
                w.t2Cash[0]=cash;w.t2RentArrears[0]=debt
                fixed=target-cash+debt
                w.t2EqBook[0]=fixed-cfg['t2License']
                c=company(fixed=fixed);s=state(cash=cash,arrears=debt)
                end,d=apply(c,s,Rent('actual',cfg['storage']*rate/M.TIME['ticksPerYear']))
                K.settle_storage_rent(w,cfg,1)
                self.assertEqual(end.cash,w.t2Cash[0])
                self.assertEqual(end.arrears,w.t2RentArrears[0])
                self.assertEqual(d['charge'],w.t2RentCharge[0])
                self.assertEqual(d['paid'],w.t2RentPaid[0])


if __name__=='__main__':unittest.main()
