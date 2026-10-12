from dataclasses import replace
import random
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_executor import Executor
from tools.buying_v2.phase_oracle import Scenario
from tools.buying_v2.phase_ledger import (Accounts,OpenBook,SettleBook,SharedSettleBook,SetQuotes,Rent,EndTick,apply)


class ContinuationExecutorTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=case(1,1,1,1,lines=2)
        s=replace(s,finished=(1,2),finished_basis=(.1,.3),cash=.5,arrears=4.,
                  switching_net_ema=.3,tick_fee_income=.2,tick_fee_expense=.4,
                  accounts=Accounts(2.,.5,3.,1.,.2,.4,.6,.1),completed_phases=('earlier',))
        events=(OpenBook('first'),SharedSettleBook('first',(2,1),.1,((1,0),)),
                SetQuotes('quotes',(12.,10.)),OpenBook('later'),SettleBook('later',(2,2),.2),
                Rent('rent',30.,0.),EndTick('end',.15))
        path=replace(paths[0],events=events)
        return c,s,path

    def test_all_nonpurchase_events_match_full_reference_state_and_details(self):
        c,s,path=self.fixture();executor=Executor(c,s,compile_calendar(c,s,(path,)))
        reference=compiled=s
        for index,event in enumerate(path.events):
            reference,detail=apply(c,reference,event)
            compiled,actual=executor.apply(compiled,index)
            self.assertEqual(compiled,reference)
            self.assertEqual(actual,detail)
        self.assertEqual(s,self.fixture()[1])
        self.assertEqual(compiled.completed_phases,())
        self.assertFalse(compiled.rent_settled)

    def test_random_cash_basis_quotes_rent_and_transfer_boundary_parity(self):
        rng=random.Random(726451)
        for _ in range(80):
            c,s,path=self.fixture();scale=rng.choice((1e-8,.1,1.,1e8))
            quote=rng.choice(((10.,12.),(12.,10.),(10.,10.)))
            state=replace(s,cash=rng.choice((0.,.1,20.))*scale,quotes=tuple(x*scale for x in quote),
                finished=(rng.randrange(3),rng.randrange(3)),finished_basis=tuple(rng.choice((.1,.2,.3))*scale for _ in range(2)),
                arrears=rng.choice((0.,3.))*scale,accounts=Accounts(),tick_fee_income=.2*scale,tick_fee_expense=.4*scale)
            demand=(2,1) if quote[0]<quote[1] else ((1,2) if quote[0]>quote[1] else (2,2))
            events=list(path.events);events[1]=replace(events[1],demand=demand,fee_income=.1*scale)
            events[2]=replace(events[2],quotes=(12.*scale,10.*scale))
            events[4]=replace(events[4],fee_income=.2*scale)
            events[5]=replace(events[5],bill=30.*scale,threshold=rng.choice((0.,1000.))*scale)
            scenario=replace(path,events=tuple(events));executor=Executor(c,state,compile_calendar(c,state,(scenario,)))
            left=right=state
            for index,event in enumerate(events):
                left,a=apply(c,left,event);right,b=executor.apply(right,index)
                self.assertEqual(right,left);self.assertEqual(b,a)

    def test_opening_book_excludes_new_inventory_and_preserves_cost_basis(self):
        c,s,path=self.fixture();events=(OpenBook('book'),SettleBook('book',(2,2)))
        path=replace(path,events=events);executor=Executor(c,s,compile_calendar(c,s,(path,)))
        opened,_=executor.apply(s,0)
        added=replace(opened,finished=(2,2),finished_basis=((.1+3.)/2,.3))
        expected,detail=apply(c,added,events[1]);actual,found=executor.apply(added,1)
        self.assertEqual(actual,expected);self.assertEqual(found,detail)
        self.assertEqual(found['sold'],(1,2));self.assertAlmostEqual(actual.finished_basis[0],3.)

    def test_purchase_exhaustive_allocations_and_varied_gate_states(self):
        from itertools import product
        rng=random.Random(1358)
        accepted=rejected=0
        for trial in range(32):
            c,s,paths=case(2,2,1,1,lines=2)
            s=replace(s,cash=rng.choice((0.,3.,9.,100.)),held=(rng.randrange(3),rng.randrange(2)),
                basis=(rng.choice((.1,.3,4.)),.2),incumbents=(0,0),
                switching_net_ema=rng.choice((-.3,0.,2.)),arrears=.5,
                finished=(1,0),finished_basis=(.3,0.))
            event=replace(paths[0].events[0],funded_demands=(4,4,2,2),
                fee_multiple=1.,reliability=(-1.,.2,2.,.5),rent_bill=4.,
                rent_threshold=rng.choice((0.,10.,1000.)),
                active_lines=rng.choice(((0,1),(1,),(0,),())),
                overhead_timing=rng.choice(('before','after')))
            path=replace(paths[0],events=(event,))
            executor=Executor(c,s,compile_calendar(c,s,(path,)))
            for allocation in product(range(3),repeat=4):
                try:expected,detail=apply(c,s,event,allocation)
                except ValueError:
                    rejected+=1
                    with self.assertRaises(ValueError):executor.apply(s,0,allocation)
                else:
                    actual,found=executor.apply(s,0,allocation);accepted+=1
                    self.assertEqual(actual,expected,(trial,allocation))
                    self.assertEqual(found,detail,(trial,allocation))
                    with self.assertRaisesRegex(ValueError,'already completed'):executor.apply(actual,0,allocation)
        self.assertGreater(accepted,100);self.assertGreater(rejected,100)

    def test_split_preference_single_fee_lots_and_full_calendar(self):
        from tools.buying_v2.industry_oracle import Offer
        c,s,paths=case(4,2,1,1,lines=2)
        c=replace(c,spaces=(.5,1.5),lines=tuple(replace(line,output_qty=2,output_space=.75,
            output_values=(0.,)*9) for line in c.lines))
        s=replace(s,incumbents=(99,99))
        e=replace(paths[0].events[0],offers=(Offer(0,1,1.,2,2),Offer(0,2,2.,6,2),
            Offer(0,99,3.,8,2),Offer(1,99,1.,4,2)),funded_demands=(10,8,8,4),
            reliability=(0.,0.,.5,0.),fee_unit_cost=2.,fee_multiple=1.)
        events=(e,OpenBook('sell'),SettleBook('sell',(8,8)),Rent('rent',1.,0.),EndTick('end',.2))
        path=replace(paths[0],events=events);executor=Executor(c,s,compile_calendar(c,s,(path,)))
        left=right=s
        for i,event in enumerate(events):
            allocation=(2,6,0,4) if i==0 else None
            left,a=apply(c,left,event,allocation);right,b=executor.apply(right,i,allocation)
            self.assertEqual(right,left);self.assertEqual(b,a)
            if i==0:
                self.assertEqual(b['preferences'],(99,99));self.assertEqual(b['fees'],(3.,0.))
        for allocation in ((1,6,0,4),(2,8,0,4),(2,6,2,4)):
            with self.assertRaises(ValueError):executor.apply(s,0,allocation)
        with self.assertRaises(ValueError):executor.apply(s,0,(-1,0,0,0))
        c,s,paths=case(1,1,1,1)
        executor=Executor(c,s,compile_calendar(c,s,paths))
        with self.assertRaisesRegex(ValueError,'resolved funded'):executor.apply(s,0,(0,0))

    def test_runtime_guards_do_not_mutate_input(self):
        c,s,path=self.fixture();executor=Executor(c,s,compile_calendar(c,s,(path,)))
        with self.assertRaisesRegex(ValueError,'missing/mismatched'):executor.apply(s,1)
        opened,_=executor.apply(s,0)
        for index,message in ((0,'overlap'),(5,'unsettled'),(6,'unsettled')):
            with self.assertRaisesRegex(ValueError,message):executor.apply(opened,index)
        rented=replace(s,rent_settled=True)
        with self.assertRaisesRegex(ValueError,'trading after rent'):executor.apply(rented,0)
        for index in (-1,True,1.5,len(path.events)):
            with self.assertRaises(ValueError):executor.apply(s,index)
        c,s,paths=case(1,1,1,1);executor=Executor(c,s,compile_calendar(c,s,paths))
        with self.assertRaisesRegex(ValueError,'purchase allocation required'):executor.apply(s,0)
        self.assertEqual(s,case(1,1,1,1)[1])


if __name__=='__main__':unittest.main()
