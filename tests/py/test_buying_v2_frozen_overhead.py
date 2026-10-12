from dataclasses import replace
import unittest
from test_buying_v2_phase_ledger import company, state, buy
from tools.buying_v2.phase_ledger import apply, OpenBook, SettleBook
from tools.buying_v2.phase_oracle import Scenario, solve
from tools.buying_v2.scenario_validation import validate_calendar
from tools.buying_v2.continuation_program import compile_calendar, decode_calendar
from tools.buying_v2.closing_allocation import candidate


class FrozenOverheadTests(unittest.TestCase):
    def paths(self,event):
        return (Scenario(1.,(event,OpenBook('sales'),SettleBook('sales',(10,))),
                         ((0.,)*21,),((0.,)*11,)),)

    def test_frozen_snapshot_does_not_recompute_current_equity(self):
        c=company(fixed=2_000_000.);s=state(cash=20.)
        e=buy(rent_bill=100.,frozen_overhead=0.)
        ordinary,old=apply(c,s,replace(e,frozen_overhead=None),(5,))
        frozen,new=apply(c,s,e,(5,))
        self.assertEqual(old['outputs'],(0,))
        self.assertEqual(new['outputs'],(5,))
        self.assertEqual(new['gateOverhead'],0.)
        self.assertEqual(frozen.accounts.rent_charge,0.)
        self.assertEqual(frozen.accounts.rent_paid,0.)
        self.assertEqual(ordinary.accounts.goods_paid,frozen.accounts.goods_paid)

    def test_negative_snapshot_is_valid_and_has_no_cash_transfer(self):
        c=company();s=state(cash=20.)
        end,d=apply(c,s,buy(frozen_overhead=-10.),(5,))
        self.assertEqual(d['gateOverhead'],-10.)
        self.assertEqual(end.cash,12.5)
        self.assertEqual(end.accounts.fee_income,0.)

    def test_invalid_or_ambiguous_snapshots_reject_in_both_validators(self):
        c=company();s=state()
        for e in (buy(frozen_overhead=float('nan')),buy(frozen_overhead=float('inf')),
                  buy(frozen_overhead=True),buy(frozen_overhead=0.,overhead_timing='after')):
            with self.assertRaisesRegex(ValueError,'frozen'): apply(c,s,e,(0,))
            with self.assertRaisesRegex(ValueError,'frozen'): validate_calendar(c,s,self.paths(e)[0])

    def test_schema_one_cannot_silently_drop_snapshot(self):
        c=company();s=state()
        paths=self.paths(buy(frozen_overhead=0.))
        program=compile_calendar(c,s,paths)
        self.assertEqual(program.version,2)
        self.assertEqual(decode_calendar(program,c,s),paths)
        with self.assertRaises(ValueError):decode_calendar(replace(program,version=1),c,s)

    def test_closing_adapter_matches_independent_event_tree(self):
        c=company(fixed=2_000_000.);s=state(cash=20.)
        for frozen in (-3.,0.,5.,100.):
            e=buy(rent_bill=100.,frozen_overhead=frozen);paths=self.paths(e)
            expected=solve(c,s,paths,funding=lambda *_: e.funded_demands)
            actual=candidate(c,s,s,e,((1.,replace(paths[0],events=paths[0].events[1:])),))
            self.assertIsNotNone(actual)
            self.assertEqual(actual['expectedValue'],expected['expectedValue'])
            self.assertEqual(actual['leaves'][0]['state'],expected['leaves'][0]['state'])
            self.assertEqual(expected['leaves'][0]['trace'][0]['observedPurchase'][-1],frozen)

    def test_connected_results_queries_and_history_match_oracle(self):
        from test_buying_v2_continuation_search import SearchTests
        from tools.buying_v2.benchmark_phase_search import case
        from tools.buying_v2.phase_ledger import Purchase
        for storage in ('resident','arena'):
            for overhead in (-3.,0.,100.):
                c,s,paths=case(1,2,2,2)
                paths=tuple(replace(p,events=tuple(replace(e,frozen_overhead=overhead) if isinstance(e,Purchase) else e for e in p.events)) for p in paths)
                SearchTests().compare(c,s,paths,funding='continuation',storage=storage)

    def test_different_observed_snapshots_do_not_merge(self):
        from test_buying_v2_continuation_search import SearchTests
        from tools.buying_v2.benchmark_phase_search import case
        from tools.buying_v2.phase_ledger import Purchase
        c,s,paths=case(1,1,1,2)
        paths=tuple(replace(p,events=tuple(replace(e,frozen_overhead=float(index*100)) if isinstance(e,Purchase) else e for e in p.events)) for index,p in enumerate(paths))
        SearchTests().compare(c,s,paths,funding='continuation',storage='arena')

    def test_frozen_closing_and_prefix_modes_preserve_public_result(self):
        from tools.buying_v2.continuation_search import solve as connected
        from tools.buying_v2.benchmark_phase_search import case
        from tools.buying_v2.phase_ledger import Purchase
        from test_buying_v2_continuation_query_memo import comparable
        c,s,paths=case(1,2,2,2,lines=2)
        paths=tuple(replace(p,events=tuple(replace(e,frozen_overhead=-.5) if isinstance(e,Purchase) else e for e in p.events)) for p in paths)
        plain=connected(c,s,paths,funding='continuation',storage='arena')
        optimized=connected(c,s,paths,funding='continuation',storage='arena',closing=True,
            closing_memo_entries=32,prune_prefix=True,prune_continuation=True,shared_first_states=100,
            proof_memo_entries=32,closing_cash_relaxed=True,shared_recourse_memo_entries=32,closing_joint_fallback=True)
        self.assertEqual(comparable(plain),comparable(optimized))
