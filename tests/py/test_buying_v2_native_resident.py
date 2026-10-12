from dataclasses import replace
import unittest
from test_buying_v2_phase_ledger import company,state,buy
from tools.buying_v2.phase_ledger import apply,OpenBook,SettleBook,Rent,EndTick,horizon_value
from tools.buying_v2.phase_oracle import Scenario
from tools.buying_v2.quantity_value import LinearQuantityValue
from tools.buying_v2.continuation_program import compile_calendar,decode_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_observation import decode
from tools.buying_v2.continuation_history import NumericHistory
from tools.buying_v2.continuation_results import terminal_value


class NativeResidentTests(unittest.TestCase):
    def fixture(self):
        c=replace(company(),slots=(3.5,))
        s=state(held=(.1,),basis=(.17,),finished=(.5,),finished_basis=(.23,))
        events=(OpenBook('early'),buy(frozen_overhead=-.2),SettleBook('early',(10,)),
                OpenBook('late'),SettleBook('late',(10,)),Rent('rent',1.,0.),EndTick('end',.1))
        value=LinearQuantityValue((0.,20.),(0.,2.))
        return c,s,Scenario(1.,events,(value,),(value,))

    def test_native_transitions_observations_and_terminal_equal_reference(self):
        c,s,path=self.fixture();p=compile_calendar(c,s,(path,))
        self.assertEqual(p.version,4);self.assertEqual(decode_calendar(p,c,s),(path,))
        resident=Resident(c,s,p);expected=s;history=NumericHistory(p)
        for index,event in enumerate(path.events):
            allocations={index:(2,)} if index==1 else {}
            expected,detail=apply(c,expected,event,(2,) if index==1 else None)
            resident.run(0,allocations,start=index,stop=index+1,observe=True)
            self.assertEqual(resident.snapshot(),expected)
            observed=decode(resident.observations[-1],p.labels)
            for key in ('openingStock','openingBasis','openingQuote','sold','sales','cogs','feeIncome','outputs','fees','goods','conversion'):
                if key in detail:self.assertEqual(observed[key],detail[key])
        history.trace(resident.observations)
        self.assertEqual(terminal_value(resident.data,s.cash,s.arrears,0,p.inputs+p.lines,p.terminal_offsets,p.terminal_values,p.terminal_modes,p.terminal_quantities),
                         horizon_value(s,expected,path.input_values,path.finished_values))
        self.assertEqual(expected.finished,(.5,))

    def test_fork_preserves_fractional_buffers_without_aliasing(self):
        c,s,path=self.fixture();r=Resident(c,s,compile_calendar(c,s,(path,)))
        child=r.fork();child.run(0,{1:(2,)},start=0,stop=2)
        self.assertEqual(r.snapshot(),s);self.assertNotEqual(child.snapshot(),s)

    def test_native_arena_and_own_quote_query_preserve_all_resources(self):
        from tools.buying_v2.continuation_arena import BranchArena,ArenaResident
        from tools.buying_v2.industry_oracle import Offer
        c,s,path=self.fixture();p=compile_calendar(c,s,(path,))
        arena=BranchArena(Resident(c,s,p),3)
        root=ArenaResident(arena,arena.create());expected=s
        for index,event in enumerate(path.events):
            expected,_=apply(c,expected,event,(2,) if index==1 else None)
            root.run(0,{index:(2,)} if index==1 else {},start=index,stop=index+1,observe=True)
            self.assertEqual(root.snapshot(),expected)
        NumericHistory(p).trace(root.observations)
        query=ArenaResident(arena,arena.create())
        query.run(0,{},start=0,stop=1)
        query.funding_purchase(0,1,(2,))
        opening,_=apply(c,s,path.events[0])
        e=replace(path.events[1],offers=(replace(path.events[1].offers[0],stock=3),),funded_demands=(3,),fee_multiple=0.)
        expected,_=apply(c,opening,e,(2,))
        expected=replace(expected,incumbents=s.incumbents)
        self.assertEqual(query.snapshot(),expected)
        root.release();query.release();self.assertEqual(arena.active,0)

    def test_failed_native_purchase_is_atomic(self):
        c,s,path=self.fixture();r=Resident(c,s,compile_calendar(c,s,(path,)))
        r.run(0,{},start=0,stop=1);before=r.snapshot()
        with self.assertRaises(ValueError):r.run(0,{1:(5,)},start=1,stop=2)
        self.assertEqual(r.snapshot(),before)
