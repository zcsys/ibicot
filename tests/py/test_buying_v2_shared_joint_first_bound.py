from dataclasses import replace
from itertools import product
import math
import unittest
from tools.buying_v2.benchmark_phase_search import case,frozen_funding
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.phase_ledger import apply,SetQuotes
from tools.buying_v2.shared_joint_first_bound import bound
from tools.buying_v2.shared_first_bound import BoundMemo


class SharedJointFirstBoundTests(unittest.TestCase):
    def test_joint_common_decision_bound_matches_small_known_optimum(self):
        for capacity in (1,2,4):
            c,s,paths=case(capacity,2,2,2,lines=2);e=paths[0].events[0]
            posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
            result=bound(c,s,s,e,(),posterior,max_first_states=(capacity+1)**2)
            self.assertGreaterEqual(result['value'],8.5*capacity)
            self.assertAlmostEqual(result['value'],8.5*capacity,places=5)
            self.assertEqual(result['firstBatchStates'],(capacity+1)**2)
            self.assertEqual(result['scenarioEvaluations'],6*(capacity+1)**2)

    def test_all_prefixes_dominate_independent_continuation_policies(self):
        c,s,paths=case(1,2,2,2,lines=2)
        e=replace(paths[0].events[0],funded_demands=(3,3,1,1))
        future=tuple(replace(p,events=p.events[1:]) for p in paths)
        values={}
        for allocation in product(range(4),range(4),range(2),range(2)):
            try:new,_=apply(c,s,e,allocation)
            except ValueError as error:
                self.assertIn(str(error),('infeasible procurement allocation','production would exceed physical storage'));continue
            result=solve(c,new,future,funding=frozen_funding)
            values[allocation]=result['expectedValue']+new.cash-s.cash
        for length in range(5):
            for prefix in {a[:length] for a in values}:
                result=bound(c,s,s,e,prefix,tuple((p.probability,p) for p in future),max_first_states=4)
                self.assertGreaterEqual(result['value'],max(v for a,v in values.items() if a[:length]==prefix))

    def test_prices_basis_fees_and_terminal_values(self):
        for first_price,later_price in ((1.,20.),(7.,1.)):
            c,s,paths=case(1,1,2,2,lines=2)
            s=replace(s,held=(1,0),basis=(40.,0.),finished=(1,0),finished_basis=(2.,0.),incumbents=(0,0))
            changed=[]
            for path in paths:
                events=list(path.events)
                for index,price in ((0,first_price),(4,later_price)):
                    events[index]=replace(events[index],offers=tuple(replace(o,price=price) for o in events[index].offers),fee_multiple=3.)
                events[2]=replace(events[2],fee_income=2.)
                events[6]=replace(events[6],fee_income=3.)
                changed.append(replace(path,events=tuple(events),input_values=((0.,.5,1.,.2),(0.,.5)),finished_values=((0.,.2,1.),)*2))
            expected=solve(c,s,tuple(changed),funding=frozen_funding)['expectedValue']
            posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in changed)
            result=bound(c,s,s,changed[0].events[0],(),posterior,max_first_states=4)
            self.assertGreaterEqual(result['value'],expected)

    def test_fixed_input_prefix_skips_impossible_first_batch_ranges(self):
        c,s,paths=case(2,2,2,2,lines=2);event=paths[0].events[0]
        posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
        # Material 0 has no remaining quote after fixing its two offers to zero.
        result=bound(c,s,s,event,(0,0),posterior,max_first_states=9)
        self.assertEqual(result['firstBatchStates'],1)
        self.assertEqual(result['scenarioEvaluations'],6)
        self.assertTrue(math.isfinite(result['value']))

    def test_integrated_pruning_preserves_complete_policy_and_work_limit(self):
        for funding in ('slot-deficit-v1','continuation'):
            for supply in ('independent-snapshots','persistent-arrivals'):
                args=case(1,2,2,2,lines=2)
                options=dict(funding=funding,supply=supply,allocation_search='feasible-prefix',prune_prefix=True,
                             closing_search='compiled-joint-certified-boxes',joint_bound_memo_size=64,
                             closing_proposal_memo_size=64,max_prefix_nodes=100000)
                reference=solve(*args,**options)
                actual=solve(*args,**options,shared_first_joint_states=4,shared_bound_memo_size=64)
                self.assertEqual(reference['leaves'],actual['leaves'])
                self.assertEqual(reference['expectedValue'],actual['expectedValue'])
                prefix=actual['prefixSearch'];closing=actual['closingSolver']
                work=prefix['visitedPrefixes']+prefix.get('boundEvaluations',0)+prefix['sharedBoundWork']
                work+=closing['boxes']+closing['proposalStates']+closing.get('jointBoundWork',0)
                self.assertLessEqual(work,100000)
                self.assertGreater(prefix['sharedBoundCalls'],0)
        for bad in (-1,True,1.5):
            with self.assertRaises(ValueError):solve(*args,**options,shared_first_joint_states=bad)

    def test_cache_offsets_budget_and_unsupported_calendar(self):
        c,s,paths=case(1,1,2,2,lines=2);event=paths[0].events[0]
        p=tuple((x.probability,replace(x,events=x.events[1:])) for x in paths);memo=BoundMemo(2)
        a=bound(c,s,s,event,(),p,max_first_states=4,memo=memo)
        changed=replace(s,cash=s.cash+10.)
        b=bound(c,s,changed,event,(),p,max_first_states=4,memo=memo)
        direct=bound(c,s,changed,event,(),p,max_first_states=4)
        self.assertEqual(b['value'],direct['value']);self.assertEqual(b['firstBatchStates'],0)
        self.assertAlmostEqual(b['value']-a['value'],10.,places=5)
        self.assertEqual(bound(c,s,s,event,(),p,max_first_states=3)['value'],math.inf)
        altered=replace(p[0][1],events=(SetQuotes('new',(4.,5.)),)+p[0][1].events)
        self.assertEqual(bound(c,s,s,event,(),((1.,altered),),max_first_states=4)['value'],math.inf)
        for invalid in (0,-1,True,1.5):
            with self.assertRaises(ValueError):bound(c,s,s,event,(),p,max_first_states=invalid)


if __name__=='__main__':unittest.main()
