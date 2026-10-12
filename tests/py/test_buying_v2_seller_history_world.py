import tempfile
import unittest
from pathlib import Path
import numpy as np
from economy.core import model as M
from economy.core.state import add_tier2_line
from economy.server.runtime import KernelRuntime
from tools.buying_v2.engine import IndustrialReferenceEngine, IndustrialCompiledEngine
from tools.buying_v2.seller_history import SellerHistory
from tools.buying_v2.seller_exposure import record_exposure


class SellerHistoryWorldTests(unittest.TestCase):
    def test_exposure_uses_funded_whole_lots_and_never_mutates_inputs(self):
        ids=np.array([4,1,2,3]);stock=np.array([19,20,0,0]);demands=np.array([20,20,0,10])
        expected=np.zeros((3,5),dtype=np.uint64)
        expected[:,4]=[1,1,1];expected[:,1]=[1,1,0]
        expected[:,2]=[1,0,0];expected[:,3]=[1,1,1]
        for fn in (record_exposure.py_func,record_exposure):
            out=np.zeros_like(expected)
            fn(out,ids,stock,demands,10)
            np.testing.assert_array_equal(out,expected)
        np.testing.assert_array_equal(stock,[19,20,0,0])
        np.testing.assert_array_equal(demands,[20,20,0,10])

    def test_phase_histories_match_engines_and_do_not_change_world(self):
        runtimes=[KernelRuntime(dict(t2FirmCount=4200,distributorCount=1000,seed=137)) for _ in range(3)]
        engines=[IndustrialReferenceEngine(runtimes[0],history_window=2),
                 IndustrialCompiledEngine(runtimes[1],history_window=2),
                 IndustrialCompiledEngine(runtimes[2])]
        for tick in range(1,4):
            if tick==2:
                for rt in runtimes:
                    w=rt.world
                    native=M.T2_PRODUCTS[int(w.t2LineProduct[0])]
                    other=next(p for p in M.T2_PRODUCTS if p['invented'] and p['sectorIndex']==native['sectorIndex']
                               and p['complexity']<=native['complexity'] and p['id']!=native['id'])
                    add_tier2_line(w,rt.cfg,0,other,paid=False)
            for engine in engines:
                engine.step(tick)
            for rt in runtimes[1:]:
                for name in runtimes[0].world.array_names:
                    np.testing.assert_array_equal(getattr(runtimes[0].world,name),getattr(rt.world,name),err_msg=f'{name} tick {tick}')
                self.assertEqual(runtimes[0].state,rt.state)
            a,b=engines[0].seller_history,engines[1].seller_history
            expected={'t0-wholesale','retail'}|{f'input-C{phase}' for phase in M.TIER_BOUNDARIES['T2']}
            self.assertEqual(set(a.channels),expected)
            for channel in expected:
                av,bv=a.view(channel),b.view(channel)
                for key in av:
                    np.testing.assert_array_equal(av[key],bv[key],err_msg=f'{channel} {key} tick {tick}')
            # Histories reconcile to independently posted transaction counters.
            w=runtimes[1].world
            self.assertEqual(b.view('t0-wholesale')['sold'][-1].sum(),w.t0Sold.sum())
            total=b.view('retail')['sold'][-1].sum()
            total+=sum(b.view(f'input-C{p}')['sold'][-1,M.N1*M.NP:].sum() for p in M.TIER_BOUNDARIES['T2'])
            self.assertEqual(total,w.t2Sold[:int(w.t2LineCount)].sum())
            if tick==2:
                with tempfile.TemporaryDirectory() as directory:
                    path=Path(directory)/'history.npz'
                    b.save(path)
                    engines[1].seller_history=SellerHistory.load(path,expected_tick=2,expected_channels=expected)
        self.assertTrue(sum(a.view(c)['discoveries'].sum() for c in expected)>0)


if __name__=='__main__':
    unittest.main()
