import unittest
import numpy as np
from tools.buying_v2.continuation_history import NumericHistory
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_ledger import OpenBook,SettleBook
from dataclasses import replace


class HistoryStorageTests(unittest.TestCase):
    def test_export_preserves_order_values_and_isolation(self):
        c,s,paths=case(1,1,1,1);path=replace(paths[0],events=(OpenBook('b'),SettleBook('b',(0,))))
        p=compile_calendar(c,s,(path,));r=Resident(c,s,p);r.run(0,{},observe=True)
        h=NumericHistory(p);node=h.trace(r.observations);exported=h.export(node)
        for a,b in zip(exported,r.observations):
            for x,y in zip(a,b):self.assertTrue(np.array_equal(x,y))
        exported[0][1][0]+=10
        self.assertEqual(h.export(node)[0][1][0],s.cash)
        self.assertEqual(h.export(0),())
        with self.assertRaises(ValueError):h.export(True)
        with self.assertRaises(ValueError):h.export(h.count)

    def test_terminal_only_observations_are_bounded(self):
        c,s,paths=case(1,1,1,1);paths=(replace(paths[0],events=(OpenBook('b'),SettleBook('b',(0,)))),)
        for storage in ('resident','arena'):
            with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,storage=storage,history_nodes=1)
            self.assertEqual(cm.exception.diagnostics['history']['nodes'],1)
            self.assertNotIn('leaves',cm.exception.diagnostics)

    def test_exact_history_capacity_reproduces_selected_result(self):
        c,s,paths=case(1,2,2,2)
        result=solve(c,s,paths,funding='continuation',storage='arena');h=result['diagnostics']['history']
        exact=solve(c,s,paths,funding='continuation',storage='arena',history_nodes=h['nodes'],history_integers=h['integerValues'],history_floats=h['floatValues'])
        self.assertEqual(result['expectedValue'],exact['expectedValue'])
        self.assertEqual([l['policy'] for l in result['leaves']],[l['policy'] for l in exact['leaves']])
        for a,b in zip(result['leaves'],exact['leaves']):
            for x,y in zip(a['observations'],b['observations']):
                for u,v in zip(x,y):self.assertTrue(np.array_equal(u,v))


if __name__=='__main__':unittest.main()
