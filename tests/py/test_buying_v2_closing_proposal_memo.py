from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.closing_certificate import solve as close,ProposalMemo
from test_buying_v2_prefix_pruning import semantic


class ClosingProposalMemoTests(unittest.TestCase):
    def test_untrusted_hint_requires_fresh_proof_and_full_fallback(self):
        c,s,paths=case(2,2,1,1)
        event=replace(paths[0].events[0],funded_demands=(2,)*4)
        posterior=((1.,replace(paths[0],events=paths[0].events[1:])),)
        expected=close(c,s,s,event,posterior)
        for hint in ((0,0,0,0),(9,9,9,9)):
            memo=ProposalMemo(2);p=prepare(c,s,s,event,posterior)
            memo.put(memo.key(p),hint)
            result=close(c,s,s,event,posterior,proposal_memo=memo)
            self.assertEqual(result['allocation'],expected['allocation'])
            self.assertEqual(result['value'],expected['value'])
            self.assertEqual(result['certificates'],0)
            self.assertEqual(memo.hits,1)

    def test_cash_change_reuses_hint_but_rechecks_feasibility(self):
        c,s,paths=case(2,2,1,1);event=replace(paths[0].events[0],funded_demands=(2,)*4)
        posterior=((1.,replace(paths[0],events=paths[0].events[1:])),);memo=ProposalMemo(8)
        close(c,s,s,event,posterior,proposal_memo=memo)
        low=replace(s,cash=1.)
        plain=close(c,s,low,event,posterior)
        cached=close(c,s,low,event,posterior,proposal_memo=memo)
        self.assertEqual(cached['allocation'],plain['allocation'])
        self.assertEqual(cached['value'],plain['value'])
        self.assertEqual(memo.hits,1)

    def test_changed_basis_and_loyalty_are_rechecked(self):
        c,s,paths=case(2,2,1,1);event=replace(paths[0].events[0],funded_demands=(2,)*4)
        posterior=((1.,replace(paths[0],events=paths[0].events[1:])),)
        for state,changed_event in ((replace(s,basis=(100.,100.),held=(1,1)),event),
                                  (replace(s,incumbents=(0,0)),replace(event,fee_multiple=50.))):
            memo=ProposalMemo(8);p=prepare(c,s,state,changed_event,posterior)
            memo.put(memo.key(p),(0,2,0,2))
            cached=close(c,s,state,changed_event,posterior,proposal_memo=memo)
            plain=close(c,s,state,changed_event,posterior)
            self.assertEqual(cached['allocation'],plain['allocation'])
            self.assertEqual(cached['value'],plain['value'])
            self.assertEqual(memo.hits,1)

    def test_complete_policies_and_accounts_match(self):
        args=case(4,2,2,2)
        kw=dict(funding='continuation',allocation_search='feasible-prefix',prune_prefix=True,shared_first_batches=16,
                shared_bound_memo_size=4096,closing_search='compiled-certified-boxes',funding_memo_size=4096,
                closing_memo_size=4096,prune_continuation=True,continuation_bound_costs=True,max_prefix_nodes=100000)
        plain=solve(*args,**kw)
        for size in (1,4096):
            cached=solve(*args,**kw,closing_proposal_memo_size=size)
            self.assertEqual(semantic(plain),semantic(cached))
            self.assertLessEqual(cached['closingSolver']['proposalMemo']['peakEntries'],size)
        self.assertGreater(cached['closingSolver']['proposalMemo']['hits'],0)


if __name__=='__main__':unittest.main()
