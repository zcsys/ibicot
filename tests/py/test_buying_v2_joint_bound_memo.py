from dataclasses import replace
import unittest
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.closing_joint_compiled import bounder,BoundMemo
from tools.buying_v2.phase_oracle import solve


class JointBoundMemoTests(unittest.TestCase):
    def fixture(self):
        c,s,paths=case(1,2,1,1,lines=2)
        e=replace(paths[0].events[0],funded_demands=(3,3,1,1))
        p=((1.,replace(paths[0],events=paths[0].events[1:])),)
        return c,s,e,p

    def test_repeat_reuses_exact_value_and_relaxed_fields_only(self):
        c,s,e,p=self.fixture();memo=BoundMemo(2)
        problem=prepare(c,s,s,e,p);lo=(0,)*4;hi=(3,3,1,1)
        first=bounder(problem,s,s,p,memo=memo)(lo,hi)
        changed=replace(problem,basis=(50.,50.),incumbents=(0,0),fees=(20.,20.),funded_demands=(0,)*4)
        hit=bounder(changed,s,s,p,memo=memo)(lo,hi)
        self.assertEqual(hit['upperValue'],first['upperValue'])
        self.assertEqual(hit['batchStates'],0);self.assertGreater(first['batchStates'],0)
        self.assertEqual((memo.hits,memo.misses),(1,1))

    def test_cash_quotes_history_and_posterior_changes_miss(self):
        c,s,e,p=self.fixture();memo=BoundMemo(2);lo=(0,)*4;hi=(3,3,1,1)
        problem=prepare(c,s,s,e,p);bounder(problem,s,s,p,memo=memo)(lo,hi)
        variants=((replace(s,cash=50.),p),(replace(s,quotes=(9.,12.)),p),
                  (replace(s,held=(1,0),basis=(2.,0.)),p),
                  (s,((1.,replace(p[0][1],events=(p[0][1].events[0],replace(p[0][1].events[1],fee_income=2.)))),)))
        for state,posterior in variants:
            prepared=prepare(c,s,state,e,posterior)
            expected=bounder(prepared,s,state,posterior)(lo,hi)
            actual=bounder(prepared,s,state,posterior,memo=memo)(lo,hi)
            self.assertEqual(actual,expected)
        self.assertEqual(memo.hits,0);self.assertEqual(memo.misses,5)
        self.assertEqual(memo.peak_entries,2)

    def test_complete_policy_and_accounts_equal_without_cache(self):
        args=case(1,2,2,2,lines=2)
        kw=dict(funding='continuation',closing_search='compiled-joint-certified-boxes',closing_proposal_memo_size=64,
                closing_memo_size=64,max_prefix_nodes=100000)
        expected=solve(*args,**kw)
        for size in (1,4096):
            actual=solve(*args,**kw,joint_bound_memo_size=size)
            self.assertEqual(actual['leaves'],expected['leaves'])
            self.assertEqual(actual['expectedValue'],expected['expectedValue'])
            self.assertLessEqual(actual['closingSolver']['jointBoundMemo']['peakEntries'],size)
        self.assertGreater(actual['closingSolver']['jointBoundMemo']['hits'],0)
        self.assertLess(actual['closingSolver']['jointBoundWork'],expected['closingSolver']['jointBoundWork'])

    def test_dynamic_budget_allows_cached_hit_and_refuses_unfunded_miss(self):
        c,s,e,p=self.fixture();problem=prepare(c,s,s,e,p);memo=BoundMemo(2)
        bound=bounder(problem,s,s,p,memo=memo);lo=(0,)*4;hi=(3,3,1,1)
        miss=bound(lo,hi,work_budget=1)
        self.assertEqual(miss,dict(upperValue=float('inf'),batchStates=0))
        complete=bound(lo,hi,work_budget=9)
        self.assertEqual(complete['batchStates'],4)
        hit=bound(lo,hi,work_budget=1)
        self.assertEqual(hit,dict(upperValue=complete['upperValue'],batchStates=0))
        for invalid in (0,-1,True,1.5):
            with self.assertRaises(ValueError):bound(lo,hi,work_budget=invalid)

    def test_box_specific_count_can_fit_below_full_problem_reservation(self):
        c,s,e,p=self.fixture();problem=prepare(c,s,s,e,p)
        bound=bounder(problem,s,s,p);lo=hi=(0,)*4
        actual=bound(lo,hi,work_budget=3)
        self.assertEqual(actual,bound(lo,hi))
        self.assertEqual(actual['batchStates'],1)
        self.assertLessEqual(1+actual['batchStates']*(1+len(p)),3)

    def test_invalid_configuration_and_unavailable_bound_not_cached(self):
        c,s,e,p=self.fixture();problem=prepare(c,s,s,e,p);memo=BoundMemo(1)
        low=bounder(problem,s,s,p,max_states=1,memo=memo)
        low((0,)*4,(3,3,1,1));low((0,)*4,(3,3,1,1))
        self.assertEqual((memo.hits,memo.peak_entries),(0,0))
        for capacity in (0,-1,True,1.5):
            with self.assertRaises(ValueError):BoundMemo(capacity)
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),funding='continuation',joint_bound_memo_size=1)


if __name__=='__main__':unittest.main()
