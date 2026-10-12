from dataclasses import replace
import unittest
import numpy as np
from tools.buying_v2.quantity_value import LinearQuantityValue
from tools.buying_v2.continuation_program import compile_calendar,decode_calendar
from tools.buying_v2.continuation_results import quantity_value
from tools.buying_v2.benchmark_phase_search import case
import test_buying_v2_continuation_search as verification


class NativeTerminalTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=case(1,2,2,2)
        paths=tuple(replace(p,input_values=tuple(LinearQuantityValue((0.,.5,float(len(t)-1)),(0.,.2,.7)) for t in p.input_values),
            finished_values=tuple(LinearQuantityValue((0.,.5,float(len(t)-1)),(0.,.1,.3)) for t in p.finished_values)) for p in paths)
        return c,s,paths

    def test_calendar_round_trip_and_schema_guard(self):
        c,s,paths=self.fixture();p=compile_calendar(c,s,paths)
        self.assertEqual(p.version,3);self.assertEqual(decode_calendar(p,c,s),paths)
        self.assertFalse(p.terminal_modes.flags.writeable);self.assertFalse(p.terminal_quantities.flags.writeable)
        with self.assertRaises(ValueError):decode_calendar(replace(p,version=1),c,s)
        bad=p.terminal_quantities.copy();bad[1]=bad[0]
        with self.assertRaises(ValueError):decode_calendar(replace(p,terminal_quantities=bad),c,s)

    def test_fractional_lookup_matches_explicit_python_curve(self):
        table=LinearQuantityValue((0.,.1,.75,3.),(1.,-2.,4.,5.))
        offsets=np.array([0,4],dtype=np.int64);values=np.array(table.values);knots=np.array(table.quantities);modes=np.array([1],dtype=np.int64)
        for q in (0.,.05,.1,.2,.75,1.,2.99,3.):
            self.assertEqual(quantity_value(q,0,offsets,values,modes,knots),table.at(q))
        for q in (-.1,3.1):
            with self.assertRaises(ValueError):quantity_value(q,0,offsets,values,modes,knots)
        with self.assertRaises(ValueError):quantity_value(.5,0,offsets,values)

    def test_connected_endogenous_results_match_independent_oracle(self):
        c,s,paths=self.fixture()
        for storage in ('resident','arena'):
            verification.SearchTests().compare(c,s,paths,funding='continuation',storage=storage)

    def test_mixed_values_and_frozen_overhead_round_trip(self):
        from tools.buying_v2.phase_ledger import Purchase
        c,s,paths=self.fixture()
        paths=tuple(replace(p,input_values=((0.,)*3,)+p.input_values[1:],
            events=tuple(replace(e,frozen_overhead=-.2) if isinstance(e,Purchase) else e for e in p.events)) for p in paths)
        p=compile_calendar(c,s,paths)
        self.assertEqual(p.version,3);self.assertEqual(decode_calendar(p,c,s),paths)
        self.assertIn(0,p.terminal_modes);self.assertIn(1,p.terminal_modes)

    def test_optional_integer_bounds_decline_curves_without_changing_result(self):
        from tools.buying_v2.continuation_search import solve
        from test_buying_v2_continuation_query_memo import comparable
        c,s,paths=self.fixture()
        plain=solve(c,s,paths,funding='continuation',storage='arena')
        optimized=solve(c,s,paths,funding='continuation',storage='arena',closing=True,
            prune_prefix=True,prune_continuation=True,shared_first_states=100)
        self.assertEqual(comparable(plain),comparable(optimized))
