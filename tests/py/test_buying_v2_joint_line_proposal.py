from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.closing_certificate import solve as close, ProposalMemo
from tools.buying_v2.industry import pack
from tools.buying_v2.joint_line_proposal import candidate
from tools.buying_v2.phase_oracle import solve


class JointLineProposalTests(unittest.TestCase):
    def fixture(self, capacity=2):
        c,s,paths=case(capacity,2,1,1,lines=2)
        e=replace(paths[0].events[0],funded_demands=(3*capacity,)*2+(capacity,)*2)
        posterior=((1.,replace(paths[0],events=paths[0].events[1:])),)
        return c,s,e,posterior

    def test_aggregate_deficit_buys_shared_material_once_for_both_lines(self):
        c,s,e,p=self.fixture()
        result,certified=candidate(pack(prepare(c,s,s,e,p)))
        self.assertFalse(certified)
        self.assertEqual(tuple(result[0]),(6,0,2,0))
        self.assertEqual(tuple(result[1]),(2,2))
        self.assertEqual(result[3],26.)
        # Opening shared inventory offsets the aggregate demand, not each line.
        held=replace(s,held=(2,0),basis=(4.,0.))
        result,certified=candidate(pack(prepare(c,s,held,e,p)))
        self.assertEqual(tuple(result[0]),(4,0,2,0))
        self.assertFalse(certified)

    def test_bad_multiline_hints_and_resource_limits_match_event_tree(self):
        c,s,e,p=self.fixture(1)
        for state,event in ((s,e),(replace(s,cash=3.),e),
                            (replace(s,held=(1,0),basis=(100.,0.)),e),
                            (replace(s,incumbents=(0,0)),replace(e,fee_multiple=30.))):
            paths=tuple(replace(path,probability=w,events=(event,)+path.events) for w,path in p)
            expected=solve(c,state,paths,funding=lambda *_:event.funded_demands)
            problem=prepare(c,state,state,event,p)
            for hint in ((0,0,0,0),(0,3,0,1),(99,0,0,0)):
                memo=ProposalMemo(1);memo.put(memo.key(problem),hint)
                actual=close(c,state,state,event,p,proposal_memo=memo,joint_proposals=True)
                self.assertEqual(actual['allocation'],expected['leaves'][0]['trace'][0]['allocation'])
                self.assertEqual(actual['value'],expected['expectedValue'])
                self.assertEqual(memo.hits,1)

    def test_opt_in_mode_preserves_complete_policy(self):
        args=case(1,1,2,2,lines=2)
        expected=solve(*args,funding='continuation')
        actual=solve(*args,funding='continuation',closing_search='compiled-joint-certified-boxes',closing_proposal_memo_size=32)
        self.assertEqual(actual['leaves'],expected['leaves'])
        self.assertEqual(actual['expectedValue'],expected['expectedValue'])
        self.assertGreater(actual['closingSolver']['proposalStates'],0)

    def test_joint_scan_is_skipped_when_reservation_exceeds_budget(self):
        c,s,e,p=self.fixture(1)
        # The four joint target states cannot fit the speculative quarter.
        with self.assertRaisesRegex(ValueError,'node limit'):
            close(c,s,s,e,p,max_boxes=1,joint_proposals=True)
        full=close(c,s,s,e,p,joint_proposals=True)
        self.assertGreaterEqual(full['proposalStates'],4)
        self.assertEqual(full['value'],13.)


if __name__=='__main__':unittest.main()
