import unittest
import numpy as np
from tools.buying_v2.decision_traces import DecisionTrace, capture, verify_export


class DecisionTraceTests(unittest.TestCase):
    def test_sampling_is_bounded_repeatable_and_handles_empty_populations(self):
        for population in (0,1,7,1008,60000):
            a=DecisionTrace(population,32,137,11,2,4)
            b=DecisionTrace(population,32,137,11,2,4)
            np.testing.assert_array_equal(a.firms,b.firms)
            self.assertEqual(len(set(a.firms)),min(32,population))
            self.assertTrue(all(0<=f<population for f in a.firms))
            self.assertEqual(a.export(),b.export())
        with self.assertRaises(ValueError):
            DecisionTrace(10,-1,137,1,1,1)

    def split_trace(self, fn=capture):
        trace=DecisionTrace(1,1,137,1,2,4)
        ints=lambda v: np.array(v,dtype=np.int64)
        floats=lambda v: np.array(v,dtype=float)
        args=(0,100.,20.,1,ints([7]),ints([0]),floats([2.]),ints([8]),floats([1.]),
              ints([0]),ints([8]),floats([3.]),ints([0]),floats([0.]),
              ints([0,0]),ints([0,1]),floats([1.,1.]),ints([2,6]),ints([8,8]),ints([2,6]),ints([8,6]))
        before=[a.copy() if isinstance(a,np.ndarray) else a for a in args]
        fn(trace.arrays,*args)
        for a,b in zip(args,before):
            np.testing.assert_array_equal(a,b)
        return trace,args

    def test_split_reconstruction_and_tamper_detection(self):
        import copy,json
        a,args=self.split_trace()
        b,_=self.split_trace(capture.py_func)
        self.assertEqual(a.export(),b.export())
        document=json.loads(json.dumps(a.export()))
        self.assertEqual(verify_export(document),dict(sampled=1,captured=1,notObserved=0))
        self.assertEqual(document['decisions'][0]['materials'][0][8],0)
        for group,index,column,value in (('offers',1,6,8),('materials',0,9,3),('materials',0,8,1),('offers',1,5,5)):
            damaged=copy.deepcopy(document)
            damaged['decisions'][0][group][index][column]=value
            with self.assertRaises(ValueError):
                verify_export(damaged)
        before=[x.copy() for x in a.arrays]
        with self.assertRaisesRegex(ValueError,'duplicate'):
            capture(a.arrays,*args)
        for x,y in zip(before,a.arrays):
            np.testing.assert_array_equal(x,y)

    def test_missing_callback_and_empty_offers_are_distinct(self):
        trace=DecisionTrace(1,1,137,1,1,1)
        self.assertEqual(verify_export(trace.export())['notObserved'],1)
        ints=lambda v: np.array(v,dtype=np.int64)
        floats=lambda v: np.array(v,dtype=float)
        capture(trace.arrays,0,0.,0.,10,ints([0]),ints([5]),floats([2.]),ints([0]),floats([1.]),
                ints([-1]),ints([0]),floats([0.]),ints([-1]),floats([0.]),ints([]),ints([]),floats([]),
                ints([]),ints([]),ints([]),ints([]))
        self.assertEqual(verify_export(trace.export())['captured'],1)
        self.assertEqual(trace.export()['decisions'][0]['offers'],[])

    def test_reference_compiled_traces_and_uninstrumented_world_agree(self):
        from economy.server.runtime import KernelRuntime
        from tools.buying_v2.engine import IndustrialReferenceEngine, IndustrialCompiledEngine
        runtimes=[KernelRuntime(dict(t2FirmCount=4200,distributorCount=1000,seed=137)) for _ in range(3)]
        from economy.core import model as M
        from economy.core.state import add_tier2_line
        selected=DecisionTrace(4200,12,137,1,2,4).firms[:2]
        for rt in runtimes:
            w=rt.world
            for firm in selected:
                line=w.t2FirmLines[int(firm)*M.T2_MAX_PRODUCTS_PER_FIRM]
                native=M.T2_PRODUCTS[int(w.t2LineProduct[line])]
                other=next(p for p in M.T2_PRODUCTS if p['invented'] and p['sectorIndex']==native['sectorIndex']
                           and p['complexity']<=native['complexity'] and p['id']!=native['id'])
                add_tier2_line(w,rt.cfg,int(firm),other,paid=False)
        engines=[IndustrialReferenceEngine(runtimes[0],trace_sample=12),
                 IndustrialCompiledEngine(runtimes[1],trace_sample=12),
                 IndustrialCompiledEngine(runtimes[2])]
        observed=set()
        for tick in range(1,3):
            for engine in engines:
                engine.step(tick)
            for key,trace in engines[0].decision_traces.items():
                other=engines[1].decision_traces[key]
                self.assertEqual(trace.metadata,other.metadata)
                for a,b in zip(trace.arrays,other.arrays):
                    np.testing.assert_array_equal(a,b,err_msg=str((tick,key)))
                verified=verify_export(trace.export())
                self.assertEqual(verified['sampled'],12)
                rows=trace.export()['decisions']
                if any(r['status']=='captured' for r in rows):
                    observed.add(key)
            for rt in runtimes[1:]:
                for name in rt.world.array_names:
                    np.testing.assert_array_equal(getattr(runtimes[0].world,name),getattr(rt.world,name),err_msg=name)
                self.assertEqual(runtimes[0].state,rt.state)
            if tick==1:
                import tempfile
                from economy.server.persistence import save_checkpoint,load_checkpoint
                with tempfile.TemporaryDirectory() as directory:
                    rt=runtimes[1]
                    stem=directory+'/checkpoint'
                    save_checkpoint(stem,rt.cfg,tick,rt.world,rt.state,{'purchasePolicy':engines[1].policy})
                    cfg,saved_tick,world,state=load_checkpoint(stem,purchase_policy=engines[1].policy)
                    self.assertEqual(saved_tick,tick)
                    rt.cfg,rt.world=cfg,world
                    rt.state={key:state[key] for key in rt.state}
                    engines[1]=IndustrialCompiledEngine(rt,trace_sample=12)
        self.assertEqual(observed,{(1,1),(2,3),(2,4)})
        self.assertFalse(engines[2].decision_traces)

if __name__=='__main__':
    unittest.main()
