import unittest
from tools.buying_v2.continuation_results import Results,ResultLimit,terminal_value
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.phase_ledger import horizon_value


class ResultTests(unittest.TestCase):
    def test_exact_fields_and_capacity_failure(self):
        r=Results(1);row=r.append(0,2**53+1,2,3,-.2);before=r.diagnostics()
        self.assertEqual(r.read(row),(0,2**53+1,2,3,-.2))
        with self.assertRaises(ResultLimit):r.append(1,0,0,0,1.)
        self.assertEqual(r.diagnostics(),before)
        for row in (-1,True,1):
            with self.assertRaises(ValueError):r.read(row)
        with self.assertRaises(ValueError):Results().append(0,0,0,0,float('nan'))

    def test_typed_terminal_matches_independent_ledger(self):
        c,s,paths=case(1,1,1,2,lines=2);p=compile_calendar(c,s,paths);r=Resident(c,s,p)
        for i,path in enumerate(paths):
            self.assertEqual(terminal_value(r.data,s.cash,s.arrears,i,p.inputs+p.lines,p.terminal_offsets,p.terminal_values),horizon_value(s,s,path.input_values,path.finished_values))

    def test_search_result_limit_and_exact_usage(self):
        c,s,paths=case(1,1,2,1)
        with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,funding='continuation',max_results=1)
        self.assertEqual(cm.exception.diagnostics['results']['records'],1);self.assertNotIn('leaves',cm.exception.diagnostics)
        result=solve(c,s,paths,funding='continuation',storage='arena')
        exact=solve(c,s,paths,funding='continuation',storage='arena',max_results=result['diagnostics']['results']['records'])
        self.assertEqual(result['expectedValue'],exact['expectedValue'])
        self.assertEqual([x['state'] for x in result['leaves']],[x['state'] for x in exact['leaves']])
        self.assertEqual([x['policy'] for x in result['leaves']],[x['policy'] for x in exact['leaves']])


if __name__=='__main__':unittest.main()
