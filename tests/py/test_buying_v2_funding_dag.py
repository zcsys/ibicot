import unittest
from dataclasses import replace
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.fee_boundary_study import fee_case,income_case
from test_buying_v2_information_history import fixture,scenario
from tools.buying_v2.phase_ledger import OpenBook,SettleBook


def semantic(r):return {k:v for k,v in r.items() if k not in ('fundingMemo','fundingObservations','fundingQueries','enumeratedNodes','prefixSearch','transitionCache')}

class FundingDAGTests(unittest.TestCase):
    def test_complete_policy_and_trace_parity_with_bounded_memo(self):
        for args in (case(1,1,2,2),case(2,2,2,2),fee_case(7.,3.,3),income_case(.5)):
            for mode in ('continuation','continuation-transfer-neutral'):
                baseline=solve(*args,funding=mode,allocation_search='feasible-prefix',max_nodes=100000,max_prefix_nodes=400000)
                for size in (1,4096):
                    result=solve(*args,funding=mode,allocation_search='feasible-prefix',funding_memo_size=size,max_nodes=100000,max_prefix_nodes=400000)
                    self.assertEqual(semantic(baseline),semantic(result))
                    self.assertLessEqual(result['fundingMemo']['peakEntries'],size)
                    self.assertLessEqual(result['enumeratedNodes'],baseline['enumeratedNodes'])

    def test_different_posteriors_after_converged_balances_remain_distinct(self):
        c,s,b=fixture()
        paths=tuple(scenario((OpenBook('early'),SettleBook('early',(early,)),OpenBook('later'),
            SettleBook('later',(1-early,)),b,OpenBook('final'),SettleBook('final',(early,)))) for early in (0,1))
        for supply in ('independent-snapshots','persistent-arrivals'):
            base=solve(c,s,paths,funding='continuation',supply=supply)
            actual=solve(c,s,paths,funding='continuation',supply=supply,funding_memo_size=4096)
            self.assertEqual(semantic(base),semantic(actual))
            self.assertEqual(actual['expectedValue'],2.375)
            self.assertEqual([leaf['trace'][4]['allocation'] for leaf in actual['leaves']],[(0,),(1,)])

    def test_physical_stock_and_future_arrivals_remain_in_the_key(self):
        from test_buying_v2_persistent_supply import fixture as supply_fixture
        from tools.buying_v2.industry_oracle import Offer
        for opening in (0,1,2):
            for arrival in (0,1,2):
                c,s,path=supply_fixture(opening+arrival)
                events=list(path.events);events[0]=replace(events[0],offers=(Offer(0,1,1.,opening),))
                path=replace(path,events=tuple(events))
                base=solve(c,s,(path,),funding='continuation',supply='persistent-arrivals')
                actual=solve(c,s,(path,),funding='continuation',supply='persistent-arrivals',funding_memo_size=4096)
                self.assertEqual(semantic(base),semantic(actual))
        reused=solve(*case(1,1,2,2),funding='continuation',funding_memo_size=4096)
        self.assertGreater(reused['fundingMemo']['hits'],0)

    def test_validation_and_limit_fail_explicitly(self):
        args=case(1,1,2,2)
        for invalid in (-1,True,.5):
            with self.assertRaises(ValueError):solve(*args,funding='continuation',funding_memo_size=invalid)
        with self.assertRaisesRegex(ValueError,'node limit'):
            solve(*args,funding='continuation',funding_memo_size=4096,max_nodes=1)

if __name__=='__main__':unittest.main()
