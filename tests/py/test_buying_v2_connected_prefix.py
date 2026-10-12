import unittest
from tools.buying_v2.continuation_search import solve
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_actions import AllocationFrame,ActionLimit
from test_buying_v2_continuation_differential import cases
from test_buying_v2_continuation_query_memo import comparable


class ConnectedPrefixTests(unittest.TestCase):
    def test_seeded_complete_results(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number):
                kw=dict(funding='continuation',storage='arena',supply=supply)
                base=solve(c,s,paths,**kw)
                actual=solve(c,s,paths,**kw,prune_prefix=True,shared_first_states=64)
                self.assertEqual(comparable(base),comparable(actual))

    def test_prefix_cut_order_resume_and_work(self):
        c,s,paths=case(2,2,1,1);r=Resident(c,s,compile_calendar(c,s,paths))
        def collect(frame,prune=None,budget=10000):
            result=[]
            while True:
                try:a=frame.next(max_prefixes=budget,prune=prune)
                except ActionLimit:continue
                if a is None:return result
                result.append(a)
        baseline=collect(AllocationFrame(r,0,0))
        self.assertEqual(collect(AllocationFrame(r,0,0),lambda p,b:(False,min(b,1)),3),baseline)
        cut=lambda p,b:(p[0]>0,0)
        actual=collect(AllocationFrame(r,0,0),cut,2)
        self.assertEqual(actual,[a for a in baseline if a[0]==0])

    def test_shared_proofs_preserve_complete_two_period_results(self):
        cuts=0
        for lines in (1,2):
            args=case(2,2,2,2,lines=lines)
            kw=dict(funding='continuation',storage='arena',closing=True,max_prefixes=200000)
            base=solve(*args,**kw)
            result=solve(*args,**kw,prune_prefix=True,shared_first_states=64)
            self.assertEqual(comparable(base),comparable(result))
            cuts+=result['diagnostics']['prefixBoundPruned']
        self.assertGreater(cuts,0)

    def test_options(self):
        for value in (-1,True,1.5):
            with self.assertRaises(ValueError):solve(*case(1,1,1,1),prune_prefix=True,shared_first_states=value)
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),shared_first_states=3)


if __name__=='__main__':unittest.main()
