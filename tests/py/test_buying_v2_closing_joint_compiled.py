from dataclasses import replace
from itertools import product
import unittest
from unittest.mock import patch
from tools.buying_v2.closing_joint_bound import bounder as reference
from tools.buying_v2.closing_joint_compiled import bounder
from tools.buying_v2.closing_allocation import prepare
import test_buying_v2_closing_joint_bound as ledger_cases


class CompiledJointBoundTests(ledger_cases.JointClosingBoundTests):
    def setUp(self):
        def checked(*args,**kwargs):
            slow=reference(*args,**kwargs);fast=bounder(*args,**kwargs)
            def compare(lo,hi):
                expected=slow(lo,hi);actual=fast(lo,hi)
                self.assertEqual(actual['batchStates'],expected['batchStates'])
                self.assertGreaterEqual(actual['upperValue'],expected['upperValue'])
                return actual
            return compare
        self.patcher=patch.object(ledger_cases,'bounder',checked)
        self.patcher.start();self.addCleanup(self.patcher.stop)

    def test_price_overflow_and_subnormal_boundaries(self):
        c,s,e,p=self.fixture(1)
        for price in (5e-324,1e-8,.1,1e8,1e308):
            event=replace(e,offers=tuple(replace(o,price=price) for o in e.offers))
            problem=prepare(c,s,s,event,p)
            slow=reference(problem,s,s,p);fast=bounder(problem,s,s,p)
            hi=tuple(o.stock for o in event.offers)
            for lo in product(*(range(q+1) for q in hi)):
                expected=slow(lo,hi);actual=fast(lo,hi)
                self.assertEqual(actual['batchStates'],expected['batchStates'])
                self.assertGreaterEqual(actual['upperValue'],expected['upperValue'])

    def test_compiled_budget_must_fit_signed_integer(self):
        c,s,e,p=self.fixture(1);problem=prepare(c,s,s,e,p)
        with self.assertRaises(ValueError):bounder(problem,s,s,p,max_states=2**63)


if __name__=='__main__':unittest.main()
