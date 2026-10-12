import unittest
from dataclasses import replace
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.fee_boundary_study import fee_case,income_case
from tools.buying_v2.phase_ledger import Purchase,OpenBook,SettleBook,Rent
from test_buying_v2_persistent_supply import fixture


def semantic(r):return {k:v for k,v in r.items() if k not in ('boundAudit','fundingMemo','fundingQueries','fundingObservations','enumeratedNodes','prefixSearch','transitionCache')}

class ContinuationPruningTests(unittest.TestCase):
    def test_complete_policy_parity_and_actual_pruning(self):
        c,s,p=fixture(2)
        cases=(case(1,1,2,2),case(2,2,2,2),fee_case(7.,3.,3),income_case(.5),(c,s,(p,)))
        cuts=0
        for args in cases:
            for funding in ('continuation','continuation-transfer-neutral'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    kw=dict(funding=funding,supply=supply,allocation_search='feasible-prefix',funding_memo_size=4096,max_prefix_nodes=400000)
                    original=solve(*args,**kw)
                    actual=solve(*args,**kw,prune_continuation=True,continuation_bound_costs=True)
                    self.assertEqual(semantic(original),semantic(actual))
                    cuts+=actual['boundAudit']['pruned']
                    self.assertLessEqual(actual['enumeratedNodes'],original['enumeratedNodes'])
        self.assertGreater(cuts,0)

    def test_invalid_future_calendar_and_offer_cannot_hide_in_a_pruned_tail(self):
        c,s,paths=case(1,1,2,2)
        for change in ('price','book','rent','terminal'):
            altered=[]
            for path in paths:
                events=list(path.events)
                if change=='price':events[4]=replace(events[4],offers=(replace(events[4].offers[0],price=-1.),)+events[4].offers[1:])
                if change=='book':events[-1]=replace(events[-1],label='wrong')
                if change=='rent':events.insert(4,Rent('rent',1.,0.))
                path=replace(path,events=tuple(events))
                if change=='terminal':path=replace(path,input_values=((float('nan'),0.),)*2)
                altered.append(path)
            with self.assertRaises(ValueError):solve(c,s,tuple(altered),funding='continuation',prune_continuation=True,continuation_bound_costs=True)

    def test_scaled_values_and_unavailable_terminal_bound_preserve_policy(self):
        for scale in (1e-8,1.,1e8):
            c,s,paths=case(1,1,1,1)
            c=replace(c,lines=(replace(c.lines[0],conversion=.5*scale,quote=10.*scale),))
            s=replace(s,cash=100.*scale,quotes=(10.*scale,))
            event=paths[0].events[0]
            event=replace(event,offers=tuple(replace(o,price=o.price*scale) for o in event.offers))
            path=replace(paths[0],events=(event,)+paths[0].events[1:])
            for terminal in (path.finished_values,((0.,),)):
                current=replace(path,finished_values=terminal)
                base=solve(c,s,(current,),funding='continuation')
                new=solve(c,s,(current,),funding='continuation',prune_continuation=True,continuation_bound_costs=True)
                self.assertEqual(semantic(base),semantic(new))
                if len(terminal[0])==1:
                    self.assertGreater(new['boundAudit']['unavailable'],0)
                    self.assertEqual(new['boundAudit']['pruned'],0)

    def test_unknown_callback_and_work_limit_fail_explicitly(self):
        args=case(1,1,2,2)
        with self.assertRaisesRegex(ValueError,'arbitrary callbacks'):solve(*args,funding=lambda c,s,e:(),prune_continuation=True)
        with self.assertRaisesRegex(ValueError,'node limit'):solve(*args,funding='continuation',prune_continuation=True,max_nodes=1)

if __name__=='__main__':unittest.main()
