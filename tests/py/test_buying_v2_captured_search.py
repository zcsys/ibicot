import unittest
from copy import deepcopy
import test_buying_v2_prepurchase_projection as fixtures
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket
from tools.buying_v2.prepurchase_state import capture_t2
from tools.buying_v2.prepurchase_projection import project
from tools.buying_v2.captured_search import select,scenario,geometry
from tools.buying_v2.continuation_program import compile_calendar


class CapturedSearchTests(unittest.TestCase):
    def record(self):
        cfg,w,phase=fixtures.ProjectionTests().fixture()
        return capture_t2(w,cfg,1,0,phase,InputMarket(w,1),K.production_line_overhead(w,cfg,'t2'))

    def test_selection_is_deterministic_and_retains_record(self):
        a=self.record();b=deepcopy(a);b['firm']=1
        for m in b['offers']:
            for s in m['suppliers']:s['current']['fin']=0
        self.assertLessEqual(geometry(b),geometry(a))
        self.assertEqual(select([a,b]),select([b,a]))
        self.assertEqual(len(select([a])),1)

    def test_diagnostic_scenarios_preserve_captured_state_and_close_books(self):
        raw=self.record();before=deepcopy(raw);p=project(raw)
        for mode in ('zero-sales','full-clearance'):
            path=scenario(p,mode)
            self.assertIs(path.events[0],p.purchase)
            self.assertEqual(path.events[1],p.settlement((0,)))
            self.assertEqual(path.input_values[0].at(.5),0.)
            compile_calendar(p.company,p.state,(path,))
        self.assertEqual(raw,before)
        with self.assertRaises(ValueError):scenario(p,'forecast')
