import unittest
from tools.buying_v2.continuation_policy import PolicyArena,PolicyLimit
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.benchmark_phase_search import case


class PolicyTests(unittest.TestCase):
    def test_shared_prefixes_branching_and_export_isolation(self):
        p=PolicyArena();a=p.append(0,0,(1,0));b=p.append(a,3,(0,2));c=p.append(a,3,(2,0))
        before=p.diagnostics();self.assertEqual(p.append(a,3,(0,2)),b);self.assertEqual(p.diagnostics(),before)
        self.assertEqual(p.export(b),{0:(1,0),3:(0,2)});self.assertEqual(p.export(c),{0:(1,0),3:(2,0)})
        d=p.export(b);d[0]=(9,9);self.assertEqual(p.export(a),{0:(1,0)})
        empty=p.append(0,0,());self.assertEqual(p.export(empty),{0:()});self.assertEqual(p.export(0),{})

    def test_limits_are_atomic_and_existing_nodes_reuse_capacity(self):
        for kwargs in ({'max_nodes':2},{'max_values':2}):
            p=PolicyArena(**kwargs);a=p.append(0,0,(1,0));before=p.diagnostics()
            with self.assertRaises(PolicyLimit) as cm:p.append(a,1,(2,0))
            self.assertEqual(p.diagnostics(),before);self.assertEqual(p.append(0,0,(1,0)),a)
            self.assertGreater(cm.exception.diagnostics['requiredNodes'],p.count)
        for parent,event,a in ((99,0,()),(0,True,()),(0,-1,()),(0,0,(-1,)),(0,0,(True,))):
            with self.assertRaises(ValueError):PolicyArena().append(parent,event,a)
        p=PolicyArena();node=p.append(0,2,())
        with self.assertRaises(ValueError):p.append(node,2,())

    def test_search_capacity_and_exact_usage_replay(self):
        c,s,paths=case(1,2,2,2)
        for kwargs in ({'policy_nodes':1},{'policy_values':1}):
            with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,funding='continuation',storage='arena',**kwargs)
            self.assertIn('policies',cm.exception.diagnostics);self.assertNotIn('leaves',cm.exception.diagnostics)
        result=solve(c,s,paths,funding='continuation',storage='arena');usage=result['diagnostics']['policies']
        bounded=solve(c,s,paths,funding='continuation',storage='arena',policy_nodes=usage['nodes'],policy_values=usage['allocationValues'])
        self.assertEqual(bounded['expectedValue'],result['expectedValue'])
        self.assertEqual([x['policy'] for x in bounded['leaves']],[x['policy'] for x in result['leaves']])


if __name__=='__main__':unittest.main()
