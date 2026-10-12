from dataclasses import replace
import unittest
from unittest.mock import patch
from tools.buying_v2.closing_cash_relaxed_bound import bounder,ProfitMemo
from tools.buying_v2.closing_allocation import prepare
import test_buying_v2_closing_cash_relaxed_bound as ledger_cases


class CompiledCashRelaxedTests(ledger_cases.CashRelaxedBoundTests):
    def setUp(self):
        def checked(*args,**kwargs):
            reference=bounder(*args,**kwargs);compiled=bounder(*args,**kwargs,compiled=True)
            def compare(lo,hi):
                expected=reference(lo,hi);actual=compiled(lo,hi)
                self.assertGreaterEqual(actual['upperValue'],expected['upperValue'])
                self.assertEqual(actual['batchStates'],expected['batchStates'])
                return actual
            return compare
        self.patcher=patch.object(ledger_cases,'bounder',checked)
        self.patcher.start();self.addCleanup(self.patcher.stop)

    def test_cash_and_arrears_changes_hit_but_recompute_allowance(self):
        c,s,e,p=self.fixture();memo=ProfitMemo(2);lo=(0,)*4;hi=(3,3,1,1)
        for compiled in (False,True):
            for cash in (.1,20.,1e12):
                state=replace(s,cash=cash,arrears=3.)
                initial=replace(s,cash=50.,arrears=7.)
                problem=prepare(c,initial,state,e,p)
                expected=bounder(problem,initial,state,p,compiled=compiled)(lo,hi)
                actual=bounder(problem,initial,state,p,compiled=compiled,memo=memo)(lo,hi)
                self.assertEqual(actual['upperValue'],expected['upperValue'])
                if cash!=.1:self.assertEqual(actual['batchStates'],0)
        self.assertEqual((memo.hits,memo.misses),(4,2))

    def test_forecast_or_quote_changes_miss_and_cache_is_bounded(self):
        c,s,e,p=self.fixture();memo=ProfitMemo(1);lo=(0,)*4;hi=(3,3,1,1)
        for state,posterior in ((s,p),(replace(s,quotes=(9.,12.)),p),
                (s,((1.,replace(p[0][1],events=(p[0][1].events[0],replace(p[0][1].events[1],fee_income=2.)))),))):
            problem=prepare(c,s,state,e,posterior)
            plain=bounder(problem,s,state,posterior)(lo,hi)
            cached=bounder(problem,s,state,posterior,memo=memo)(lo,hi)
            self.assertEqual(plain,cached)
        self.assertEqual(memo.hits,0);self.assertEqual(memo.peak_entries,1)

    def test_unavailable_results_are_not_cached(self):
        c,s,e,p=self.fixture();problem=prepare(c,s,s,e,p);memo=ProfitMemo(1)
        bound=bounder(problem,s,s,p,max_states=1,memo=memo)
        for _ in range(2):bound((0,)*4,(3,3,1,1))
        self.assertEqual((memo.hits,memo.peak_entries),(0,0))
        for value in (0,-1,True,1.5):
            with self.assertRaises(ValueError):ProfitMemo(value)


if __name__=='__main__':unittest.main()
