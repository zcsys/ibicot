from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.closing_certificate import certify
from tools.buying_v2.phase_oracle import solve


class JointProofIntegrationTests(unittest.TestCase):
    def test_joint_proof_respects_combined_budget_and_incomplete_is_not_certified(self):
        c,s,paths=case(4,2,1,1,lines=2)
        event=replace(paths[0].events[0],funded_demands=(12,12,4,4))
        posterior=((1.,replace(paths[0],events=paths[0].events[1:])),)
        allocation=(12,0,4,0)
        completed=certify(c,s,s,event,posterior,allocation,joint_bound=True,max_boxes=4000)
        self.assertTrue(completed['certified'])
        self.assertGreater(completed['jointBoundWork'],0)
        for budget in (1,10,50,200,4000):
            result=certify(c,s,s,event,posterior,allocation,joint_bound=True,max_boxes=budget)
            self.assertLessEqual(result['boxes']+result.get('jointBoundWork',0),budget)
            if result['reason']=='proof-limit':self.assertFalse(result['certified'])
        self.assertFalse(certify(c,s,s,event,posterior,(0,)*4,joint_bound=True,max_boxes=4000)['certified'])

    def test_complete_policies_accounts_and_combined_work(self):
        for dims in ((1,1,2,2),(1,2,2,2),(2,2,1,1)):
            for funding in ('slot-deficit-v1','continuation'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    args=case(*dims,lines=2)
                    expected=solve(*args,funding=funding,supply=supply,max_nodes=100000)
                    actual=solve(*args,funding=funding,supply=supply,max_nodes=100000,max_prefix_nodes=100000,
                                 closing_search='compiled-joint-certified-boxes',closing_memo_size=4096,
                                 closing_proposal_memo_size=4096)
                    self.assertEqual(expected['leaves'],actual['leaves'])
                    self.assertEqual(expected['expectedValue'],actual['expectedValue'])
                    closing=actual['closingSolver'];prefix=actual['prefixSearch']
                    charged=closing['boxes']+closing['proposalStates']+closing.get('jointBoundWork',0)
                    charged+=prefix['visitedPrefixes']+prefix.get('boundEvaluations',0)+prefix.get('sharedBoundWork',0)
                    self.assertLessEqual(charged,100000)
                    self.assertGreater(closing.get('jointBoundWork',0),0)


if __name__=='__main__':unittest.main()
