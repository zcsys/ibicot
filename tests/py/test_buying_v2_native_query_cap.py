import math
import unittest
from dataclasses import replace
from test_buying_v2_phase_ledger import company,state,buy
from tools.buying_v2.phase_oracle import Scenario
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_query import native_cap,prepare


class NativeQueryCapTests(unittest.TestCase):
    def test_matches_exhaustive_native_addition(self):
        for held in (0.,.1,.5,1.0000000000000002,3.9):
            for slot in (0.,1.,2.,2.5,4.,9.9):
                for lot in (1,2,3):
                    expected=max(q for q in range(0,30,lot) if held+q<=max(held,slot))
                    self.assertEqual(native_cap(held,slot,lot),expected,(held,slot,lot))

    def test_large_float_boundary_and_frame_limit(self):
        for held in (float(2**53),float(2**54),float(2**60)):
            expected=max(q for q in range(1000) if held+q<=held)
            self.assertEqual(native_cap(held,held,1),expected)
        with self.assertRaisesRegex(ValueError,'signed int64'):
            native_cap(0.,float(2**63),1)

    def test_query_retains_feasible_boundary_order(self):
        c=replace(company(),slots=(2.,));s=state(held=(1.0000000000000002,))
        path=Scenario(1.,(buy(),),((0.,)*21,),((0.,)*11,))
        resident=Resident(c,s,compile_calendar(c,s,(path,)))
        iv,_,_=prepare(resident,0,0)
        self.assertEqual(iv[6],1)
        self.assertEqual(iv[8],1)
        resident.funding_purchase(0,0,(1,))
        self.assertEqual(resident.snapshot().finished,(2.,))
