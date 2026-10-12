import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve,PhaseSearchLimit


class LimitDiagnosticTests(unittest.TestCase):
    def test_outer_limit_has_context_and_no_partial_policy(self):
        with self.assertRaises(PhaseSearchLimit) as caught:
            solve(*case(2,2,2,2),funding=frozen_funding,max_nodes=1)
        d=caught.exception.diagnostics
        self.assertEqual(d['maxNodes'],1)
        self.assertGreater(d['enumeratedNodes'],1)
        self.assertTrue(d['activeDecisions'])
        self.assertNotIn('leaves',d);self.assertNotIn('expectedValue',d)
        self.assertIn('no approximate result returned',str(caught.exception))

    def test_closing_failure_is_distinguished_and_does_not_leak(self):
        args=case(2,2,1,1)
        kw=dict(funding=frozen_funding,closing_search='compiled-fast-cost-boxes')
        with self.assertRaises(PhaseSearchLimit) as caught:solve(*args,**kw,max_prefix_nodes=1)
        self.assertEqual(caught.exception.diagnostics['activeDecisions'][-1]['stage'],'closing-search')
        caught.exception.diagnostics['closingSolver']['solves']=-1
        result=solve(*args,**kw)
        self.assertGreater(result['closingSolver']['solves'],0)
        self.assertEqual(result['expectedValue'],11.)

    def test_input_errors_remain_validation_errors(self):
        try:solve(*case(1,1,1,1),funding=frozen_funding,max_nodes=0)
        except ValueError as error:self.assertNotIsInstance(error,PhaseSearchLimit)
        else:self.fail('invalid limit accepted')


if __name__=='__main__':unittest.main()
