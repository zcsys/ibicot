import unittest
from itertools import product
from dataclasses import replace
import numpy as np
from tools.buying_v2.feasible_prefix import allocations
from tools.buying_v2.industry_oracle import Offer
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.fee_boundary_study import fee_case,income_case


def semantic(result):
    return {k:v for k,v in result.items() if k not in ('enumeratedNodes','allocationSearch','prefixSearch','transitionCache')}

class PrefixSearchTests(unittest.TestCase):
    def test_generator_matches_independent_filter_in_exact_order(self):
        rng=np.random.default_rng(518923)
        for _ in range(400):
            held=(int(rng.integers(0,3)),int(rng.integers(0,3)));slots=(3,3)
            offers=tuple(Offer(i//2,i,float(rng.integers(1,10))/.7,int(rng.integers(0,5)),int(rng.integers(1,3))) for i in range(4))
            ranges=[range(0,o.stock+1,o.lot) for o in offers];cash=float(rng.integers(0,100))/.7
            expected=[]
            for q in product(*ranges):
                goods=0.
                for o,a in zip(offers,q):goods+=o.price*a
                if goods<=cash and all(held[m]+sum(a for o,a in zip(offers,q) if o.material==m)<=slots[m] for m in range(2)):
                    expected.append(q)
            stats=dict(visitedPrefixes=0,prunedLeaves=0)
            actual=list(allocations(ranges,offers,held,slots,cash,stats,100000))
            self.assertEqual(actual,expected)
            self.assertEqual(stats['prunedLeaves']+len(actual),np.prod([len(x) for x in ranges]))

    def test_full_planner_semantics_preserved_with_endogenous_funding(self):
        for args in (fee_case(7.,3.,3),fee_case(11.,5.,4),income_case(.5)):
            for mode in ('continuation','continuation-transfer-neutral'):
                baseline=solve(*args,funding=mode)
                pruned=solve(*args,funding=mode,allocation_search='feasible-prefix')
                self.assertEqual(semantic(baseline),semantic(pruned))
                self.assertLessEqual(pruned['enumeratedNodes'],baseline['enumeratedNodes'])

    def test_remembered_signal_and_persistent_supply_are_preserved(self):
        from test_buying_v2_information_history import fixture,scenario
        c,s,b=fixture()
        from tools.buying_v2.phase_ledger import OpenBook,SettleBook
        paths=tuple(scenario((OpenBook('early'),SettleBook('early',(early,)),
            OpenBook('later'),SettleBook('later',(1-early,)),b,
            OpenBook('final'),SettleBook('final',(early,)))) for early in (0,1))
        for supply in ('independent-snapshots','persistent-arrivals'):
            base=solve(c,s,paths,funding='continuation',supply=supply)
            result=solve(c,s,paths,funding='continuation',supply=supply,allocation_search='feasible-prefix')
            self.assertEqual(semantic(base),semantic(result))
            self.assertEqual(result['expectedValue'],2.375)

    def test_prefix_limit_is_explicit_and_invalid_events_still_fail(self):
        args=fee_case(7.,3.,3)
        with self.assertRaisesRegex(ValueError,'prefix node limit'):
            solve(*args,funding='continuation',allocation_search='feasible-prefix',max_prefix_nodes=1)
        c,s,paths=args
        event=paths[0].events[0];bad=replace(event,offers=(replace(event.offers[0],price=-1.),))
        path=replace(paths[0],events=(bad,)+paths[0].events[1:])
        for search in ('exhaustive','feasible-prefix'):
            with self.assertRaisesRegex(ValueError,'invalid offer'):
                solve(c,s,(path,),funding=lambda c,s,e:(1,)*len(e.offers),allocation_search=search)

if __name__=='__main__':unittest.main()
