import copy
import unittest
import numpy as np
from tools.buying_v2.retail_traces import RetailTrace,verify_export
from tools.buying_v2.retail_world import clear_distributors
from tools.buying_v2.observations import empty_totals
from economy.core import model as M
from economy.server.runtime import KernelRuntime


class RetailTraceTests(unittest.TestCase):
    def test_connected_reference_compiled_and_no_trace_match(self):
        from tools.buying_v2.engine import IndustrialCompiledEngine
        runtimes=[KernelRuntime(dict(t2FirmCount=4200,distributorCount=1000,distributorActivation=.5,seed=137)) for _ in range(3)]
        for rt in runtimes:
            rt.world.distributorProduct[:]=M.NP+int(rt.world.t2LineProduct[0])
        engines=[IndustrialCompiledEngine(runtimes[0],compiled=False,trace_sample=64),
                 IndustrialCompiledEngine(runtimes[1],trace_sample=64),IndustrialCompiledEngine(runtimes[2])]
        total=dict(inactive=0,zeroPotential=0,captured=0)
        captured_doc=None
        for tick in range(1,4):
            for e in engines:
                e.step(tick)
            a,b=engines[0].retail_trace.export(),engines[1].retail_trace.export()
            # The inverse curve uses Python/NumPy versus native scalar pow.
            # Preserve exact allocations, requests and accounts; only the
            # diagnostic surplus permits ordinary floating-point roundoff.
            normalized=copy.deepcopy(b)
            for left,right in zip(a['decisions'],normalized['decisions']):
                if left['status']=='captured':
                    x,y=left['inputs']['surplus'],right['inputs']['surplus']
                    self.assertAlmostEqual(x,y,delta=1e-12*max(1.,abs(x),abs(y)))
                    right['inputs']['surplus']=x
            self.assertEqual(a,normalized)
            counts=verify_export(a)
            for k,v in counts.items():
                total[k]+=v
            captured_doc=a
            for rt in runtimes[1:]:
                for name in rt.world.array_names:
                    np.testing.assert_array_equal(getattr(rt.world,name),getattr(runtimes[0].world,name),err_msg=name)
                self.assertEqual(rt.state,runtimes[0].state)
        self.assertGreater(total['captured'],0)
        self.assertGreater(total['inactive'],0)
        self.assertIsNone(engines[2].retail_trace)
        row=next(i for i,r in enumerate(captured_doc['decisions']) if r['status']=='captured' and r['offers'])
        for field in ('desired','allocated','requested'):
            damaged=copy.deepcopy(captured_doc)
            col=damaged['offerFields'].index(field)
            damaged['decisions'][row]['offers'][0][col]+=1
            with self.assertRaises(ValueError):
                verify_export(damaged)

    def test_inactive_zero_potential_and_empty_stock_are_distinct(self):
        rt=KernelRuntime(dict(t2FirmCount=300,distributorCount=20,distributorActivation=1.,seed=137))
        w=rt.world
        w.distributorProduct[:]=M.NP+int(w.t2LineProduct[0])
        obs=empty_totals(M.NP+len(M.T2_PRODUCTS))
        for activation,latent,status in ((0.,20.,'inactive'),(1.,0.,'zero-potential'),(1.,20.,'captured')):
            rt.cfg['distributorActivation']=activation
            w.distributorQMax[:]=latent
            w.t2Fin[:]=0
            trace=RetailTrace(20,20,137,1,activation)
            clear_distributors(w,rt.cfg,1,obs,trace=trace.arrays)
            document=trace.export()
            self.assertEqual({r['status'] for r in document['decisions']},{status})
            self.assertEqual(sum(verify_export(document).values()),20)
            if status=='captured':
                self.assertTrue(all(sum(o[4] for o in r['offers'])==0 for r in document['decisions']))
                self.assertTrue(any(sum(o[5] for o in r['offers'])>0 for r in document['decisions']))
        damaged=copy.deepcopy(document)
        damaged['decisions'][0]={'buyer':0,'status':'inactive'}
        with self.assertRaisesRegex(ValueError,'activation'):
            verify_export(damaged)
        absent=next(p['id'] for p in M.T2_PRODUCTS if p['invented'] and p['id'] not in set(w.t2LineProduct[:w.t2LineCount]))
        w.distributorProduct[:]=M.NP+absent
        trace=RetailTrace(20,20,137,2,1.)
        clear_distributors(w,rt.cfg,2,obs,trace=trace.arrays)
        self.assertEqual(verify_export(trace.export())['captured'],20)
        self.assertTrue(all(r['offers']==[] for r in trace.export()['decisions']))

if __name__=='__main__':
    unittest.main()
