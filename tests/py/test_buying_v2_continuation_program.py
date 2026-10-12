from dataclasses import replace
import unittest
import numpy as np
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_program import compile_calendar,decode_calendar,INTEGER_ARRAYS,FLOAT_ARRAYS
from tools.buying_v2.phase_ledger import Purchase,OpenBook,SettleBook,SharedSettleBook,SetQuotes,Rent,EndTick
from tools.buying_v2.industry_oracle import Offer
from tools.buying_v2.phase_oracle import Scenario,solve


class ContinuationProgramTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=case(2,2,1,1,lines=2)
        buy=replace(paths[0].events[0],label='buy α',offers=(Offer(0,2**53+1,.1,6,2),Offer(1,7,.2,2)),
                    funded_demands=(4,2),reliability=(.2,.9),active_lines=(1,0),fee_unit_cost=.4,
                    fee_multiple=3.,rent_bill=.8,rent_threshold=50.,overhead_timing='after')
        events=(buy,OpenBook('sales α'),SharedSettleBook('sales α',(2,1),.3,((0,1),)),
                SetQuotes('quote',(11.,13.)),OpenBook('sales β'),SettleBook('sales β',(0,2),.1),
                Rent('rent',1.,100.),EndTick('end',.15),replace(buy,funded_demands=(),offers=(),reliability=(),active_lines=()),
                OpenBook('sales α'),SettleBook('sales α',(1,1)),EndTick('end',.2))
        a=Scenario(.25,events,((0.,-.1,.2,.3,.4,.5,.6),(0.,.1,.2)),((0.,.3,.1,.7,1.),)*2)
        b=replace(a,probability=.75,events=tuple(replace(e,fee_income=.5) if type(e) is SettleBook else e for e in events))
        return c,s,(a,b)

    def test_all_events_and_ragged_tables_round_trip_exactly(self):
        c,s,paths=self.fixture();program=compile_calendar(c,s,paths)
        self.assertEqual(decode_calendar(program,c,s),paths)
        self.assertEqual(set(program.event_kinds),set(range(7)))
        self.assertIn(2**53+1,program.integers)
        self.assertEqual(program.labels.count('sales α'),1)
        for name in INTEGER_ARRAYS+FLOAT_ARRAYS:
            a=getattr(program,name)
            self.assertEqual(a.ndim,1);self.assertTrue(a.flags.c_contiguous)
            self.assertFalse(a.flags.writeable)
            with self.assertRaises(ValueError):a.setflags(write=True)

    def test_first_purchase_wire_layout_is_independently_specified(self):
        c,s,paths=self.fixture();p=compile_calendar(c,s,paths)
        self.assertEqual(tuple(p.event_kinds[:12]),(0,1,3,4,1,2,5,6,0,1,2,6))
        self.assertEqual(tuple(p.integers[:p.integer_offsets[1]]),
                         (2,2,2,1,0,2**53+1,6,2,1,7,2,1,4,2,1,0))
        self.assertEqual(tuple(p.floats[:p.float_offsets[1]]),(.4,3.,.8,50.,.1,.2,.2,.9))

    def test_decoded_calendars_preserve_complete_oracle_results(self):
        for args in (self.fixture(),case(1,1,2,2),case(1,2,2,2,lines=2)):
            company,state,scenarios=args
            decoded=decode_calendar(compile_calendar(*args),company,state)
            expected=solve(company,state,scenarios,funding='slot-deficit-v1')
            actual=solve(company,state,decoded,funding='slot-deficit-v1')
            self.assertEqual(actual,expected)

    def test_independent_compilation_is_byte_identical_and_unaliased(self):
        c,s,paths=self.fixture();a=compile_calendar(c,s,paths);b=compile_calendar(c,s,paths)
        self.assertEqual(a.labels,b.labels)
        for name in INTEGER_ARRAYS+FLOAT_ARRAYS:
            aa=getattr(a,name);bb=getattr(b,name)
            self.assertEqual(aa.tobytes(),bb.tobytes());self.assertFalse(np.shares_memory(aa,bb))
        self.assertEqual(paths,self.fixture()[2])

    def test_corrupt_encodings_reject_before_execution(self):
        c,s,paths=self.fixture();program=compile_calendar(c,s,paths)
        variants=[replace(program,version=2),replace(program,inputs=3),replace(program,labels=program.labels+('unused',)),
                  replace(program,probabilities=np.array([.1,.1])),replace(program,event_kinds=np.full(len(program.event_kinds),99,dtype=np.int64)),
                  replace(program,event_labels=np.full(len(program.event_labels),-1,dtype=np.int64)),
                  replace(program,integers=program.integers.astype(np.float64)),replace(program,floats=program.floats.reshape(1,-1))]
        for name in ('scenario_offsets','integer_offsets','float_offsets','terminal_offsets'):
            values=getattr(program,name).copy();values[-1]+=1;variants.append(replace(program,**{name:values}))
            values=getattr(program,name).copy();values[1]=-1;variants.append(replace(program,**{name:values}))
        integers=program.integers.copy();integers[0]=2**62;variants.append(replace(program,integers=integers))
        floats=program.floats.copy();floats[0]=float('nan');variants.append(replace(program,floats=floats))
        for variant in variants:
            with self.subTest(variant=id(variant)):
                with self.assertRaises(ValueError):decode_calendar(variant,c,s)

    def test_invalid_input_and_integer_overflow_are_explicit(self):
        c,s,paths=self.fixture();path=paths[0];buy=path.events[0]
        cases=(replace(buy,offers=(replace(buy.offers[0],supplier=2**63),buy.offers[1])),
               replace(buy,funded_demands=(1,)),replace(buy,funded_demands=(True,2)),
               replace(buy,offers=(replace(buy.offers[0],price=2**53+1),buy.offers[1])))
        for event in cases:
            bad=replace(path,probability=1.,events=(event,)+path.events[1:])
            with self.assertRaises(ValueError):compile_calendar(c,s,(bad,))
        with self.assertRaises(ValueError):compile_calendar(c,s,())
        with self.assertRaises(ValueError):compile_calendar(c,s,(replace(path,probability=1.,events=(buy,buy)+path.events[1:]),))
        with self.assertRaises(ValueError):compile_calendar(c,s,(path,replace(paths[1],events=paths[1].events[:-1])))

    def test_zero_weight_and_empty_calendars_are_preserved(self):
        c,s,paths=case(1,1,1,1)
        empty=replace(paths[0],events=())
        scenarios=(replace(empty,probability=0.),empty)
        self.assertEqual(decode_calendar(compile_calendar(c,s,scenarios),c,s),scenarios)


if __name__=='__main__':unittest.main()
