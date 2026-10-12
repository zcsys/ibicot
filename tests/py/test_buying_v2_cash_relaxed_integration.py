from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.closing_cash_relaxed_bound import bounder,ProfitMemo
from tools.buying_v2.closing_allocation import prepare


class CashRelaxedIntegrationTests(unittest.TestCase):
    def test_full_policies_accounts_and_work_limits(self):
        for dims in ((1,2,2,2),(2,2,1,1)):
            for funding in ('slot-deficit-v1','continuation'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    args=case(*dims,lines=2)
                    expected=solve(*args,funding=funding,supply=supply)
                    actual=solve(*args,funding=funding,supply=supply,allocation_search='feasible-prefix',prune_prefix=True,
                        closing_search='compiled-joint-certified-boxes',closing_memo_size=64,closing_proposal_memo_size=64,
                        joint_bound_memo_size=64,cash_relaxed_joint_bound=True,max_prefix_nodes=100000)
                    self.assertEqual(actual['leaves'],expected['leaves'])
                    self.assertEqual(actual['expectedValue'],expected['expectedValue'])
                    p=actual['prefixSearch'];c=actual['closingSolver']
                    work=p['visitedPrefixes']+p.get('boundEvaluations',0)+p.get('sharedBoundWork',0)+c['boxes']+c['proposalStates']+c.get('jointBoundWork',0)
                    self.assertLessEqual(work,100000)

    def test_combined_shared_prefix_bound_preserves_complete_policy(self):
        args=case(2,2,2,2,lines=2)
        options=dict(funding='continuation',allocation_search='feasible-prefix',prune_prefix=True,
            closing_search='compiled-joint-certified-boxes',closing_memo_size=4096,closing_proposal_memo_size=4096,
            joint_bound_memo_size=4096,cash_relaxed_joint_bound=True,max_prefix_nodes=100000)
        expected=solve(*args,**options)
        actual=solve(*args,**options,shared_first_joint_states=9,shared_bound_memo_size=4096)
        self.assertEqual(expected['leaves'],actual['leaves'])
        self.assertEqual(expected['expectedValue'],actual['expectedValue'])
        self.assertGreater(actual['prefixSearch']['sharedBoundPruned'],0)

    def test_cash_scarcity_and_old_basis_still_control_actual_execution(self):
        c,s,paths=case(1,2,1,2,lines=2)
        for state in (replace(s,cash=.1),replace(s,cash=5.),replace(s,held=(1,0),basis=(100.,0.))):
            expected=solve(c,state,paths,funding='slot-deficit-v1')
            actual=solve(c,state,paths,funding='slot-deficit-v1',closing_search='compiled-joint-certified-boxes',
                         joint_bound_memo_size=8,cash_relaxed_joint_bound=True)
            self.assertEqual(actual['leaves'],expected['leaves'])
            self.assertEqual(actual['expectedValue'],expected['expectedValue'])

    def test_unavailable_translation_still_charges_completed_enumeration(self):
        c,s,paths=case(1,2,1,1,lines=2);s=replace(s,cash=1e308)
        e=replace(paths[0].events[0],funded_demands=(3,3,1,1))
        posterior=((1.,replace(paths[0],events=paths[0].events[1:])),)
        problem=prepare(c,s,s,e,posterior)
        result=bounder(problem,s,s,posterior,compiled=True)((0,)*4,(3,3,1,1))
        self.assertEqual(result['upperValue'],float('inf'))
        self.assertEqual(result['batchStates'],4)

    def test_cached_normalized_result_needs_only_one_work_unit(self):
        c,s,paths=case(1,2,1,1,lines=2);e=replace(paths[0].events[0],funded_demands=(3,3,1,1))
        p=((1.,replace(paths[0],events=paths[0].events[1:])),);problem=prepare(c,s,s,e,p);memo=ProfitMemo(1)
        bound=bounder(problem,s,s,p,memo=memo,compiled=True)
        first=bound((0,)*4,(3,3,1,1),work_budget=9)
        hit=bound((0,)*4,(3,3,1,1),work_budget=1)
        self.assertEqual(hit['upperValue'],first['upperValue']);self.assertEqual(hit['batchStates'],0)
        for flag in (1,'yes',None):
            with self.assertRaises(ValueError):solve(c,s,paths,funding='continuation',cash_relaxed_joint_bound=flag)
        with self.assertRaises(ValueError):solve(c,s,paths,funding='continuation',cash_relaxed_joint_bound=True)


if __name__=='__main__':unittest.main()
