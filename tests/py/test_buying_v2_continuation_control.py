import unittest
from tools.buying_v2.continuation_control import ControlStack
from tools.buying_v2.continuation_search import solve
from tools.buying_v2.benchmark_phase_search import case


class ControlTests(unittest.TestCase):
    def test_nested_frames_preserve_fields_and_release_references(self):
        s=ControlStack(2);branches=[];s.append(dict(kind='walk',stage='enter',index=2**53+1,branches=branches));parent=s[-1]
        s.append(dict(kind='choose',stage='next',index=2,query=True,offer=None,mass=.3,best=None))
        child=s[-1];child.update(stage='child-return',payment=.2,allocation=(1,0))
        self.assertEqual(child['payment'],.2);self.assertIsNone(child['offer']);self.assertTrue(child['query'])
        self.assertIs(parent['branches'],branches);self.assertEqual(parent['index'],2**53+1)
        with self.assertRaises(ValueError):s.append(dict(kind='walk',stage='enter',index=0))
        s.pop();self.assertTrue(all(x is None for x in s.refs[1]))
        with self.assertRaises(ValueError):child['index']
        s.append(dict(kind='fund',stage='next-query',index=3,cursor=0))
        with self.assertRaises(ValueError):child['index']
        s.pop();s.pop();self.assertEqual(s.diagnostics()['activeFrames'],0)

    def test_invalid_fields_do_not_partially_update(self):
        s=ControlStack(1)
        for d in (dict(kind='walk',stage='next',index=0),dict(kind='walk',stage='enter',index=True),dict(kind='walk',stage='enter',index=0,unknown=1)):
            with self.assertRaises((ValueError,KeyError)):s.append(d)
            self.assertEqual(len(s),0)
        s.append(dict(kind='choose',stage='next',index=0,mass=1.));f=s[-1]
        with self.assertRaises(ValueError):f.update(stage='child-return',payment=float('nan'))
        self.assertEqual(f['stage'],'next');self.assertIsNone(f.get('payment'))
        with self.assertRaises(ValueError):f['kind']='walk'

    def test_typed_and_python_control_complete_results_match(self):
        c,s,paths=case(1,2,2,2)
        typed=solve(c,s,paths,funding='continuation',storage='arena')
        python=solve(c,s,paths,funding='continuation',storage='arena',control='python')
        self.assertEqual(typed['expectedValue'],python['expectedValue'])
        for a,b in zip(typed['leaves'],python['leaves']):
            for key in ('state','policy','funding','value'):self.assertEqual(a[key],b[key])
        self.assertEqual(typed['diagnostics']['control']['activeFrames'],0)
        self.assertEqual(typed['diagnostics']['control']['peakFrames'],typed['diagnostics']['peakFrames'])


if __name__=='__main__':unittest.main()
