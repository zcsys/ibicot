import unittest
from dataclasses import replace
import test_buying_v2_continuation_search as search_tests
from test_buying_v2_persistent_supply import fixture
from test_buying_v2_information_history import fixture as info_fixture,scenario
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.phase_ledger import OpenBook,SettleBook,Purchase


class EndogenousTests(unittest.TestCase):
    def compare(self,c,s,paths,supply='independent-snapshots'):
        return search_tests.SearchTests().compare(c,s,paths,supply=supply,funding='continuation')

    def test_future_funding_multiline_and_partial_suppliers(self):
        for lines in (1,2):
            c,s,paths=case(1,2,2,2,lines=lines)
            result=self.compare(c,s,paths)
            self.assertGreater(result['diagnostics']['fundingQueries'],1)

    def test_persistent_stock_and_hypothetical_additions(self):
        for opening in (0,1):
            c,s,path=fixture();events=list(path.events)
            events[0]=replace(events[0],offers=(replace(events[0].offers[0],stock=opening),))
            result=self.compare(c,s,(replace(path,events=tuple(events)),),'persistent-arrivals')
            self.assertEqual(result['expectedValue'],.75 if opening==0 else 1.75)

    def test_observed_history_preserves_future_funding_information(self):
        c,s,b=info_fixture()
        paths=tuple(scenario((OpenBook('early'),SettleBook('early',(d,)),OpenBook('later'),SettleBook('later',(1-d,)),b,OpenBook('final'),SettleBook('final',(d,)))) for d in (0,1))
        self.compare(c,s,paths)

    def test_query_limits_and_empty_offers(self):
        c,s,paths=case(1,1,2,1)
        with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,funding='continuation',max_allocations=1)
        self.assertGreater(cm.exception.diagnostics['fundingQueries'],0)
        path=replace(paths[0],events=(replace(paths[0].events[0],offers=(),reliability=(),active_lines=()),))
        self.compare(c,s,(path,))
        with self.assertRaisesRegex(ValueError,'unsupported funding'):solve(c,s,paths,funding='unknown')


if __name__=='__main__':unittest.main()
