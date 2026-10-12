import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve

class PhaseScalingTests(unittest.TestCase):
    def test_certain_and_hidden_correlated_sales_have_analytical_values(self):
        for outcomes,expected in ((1,11.),(2,3.25)):
            args=case(1,1,2,outcomes)
            for funding in (frozen_funding,'continuation'):
                result=solve(*args,funding=funding,allocation_search='feasible-prefix')
                self.assertEqual(result['expectedValue'],expected)
                for leaf in result['leaves']:
                    self.assertEqual(leaf['trace'][0]['allocation'],(1,1))
                if outcomes==2:
                    self.assertEqual([leaf['trace'][4]['allocation'] for leaf in result['leaves']],[(0,0),(1,1)])

    def test_invalid_case_dimensions_fail(self):
        for args in ((0,1,1,1),(1,0,1,1),(1,1,0,1),(1,1,1,3),(True,1,1,1)):
            with self.assertRaises(ValueError):case(*args)

if __name__=='__main__':unittest.main()
