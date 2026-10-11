import tempfile
import unittest
from pathlib import Path
import numpy as np

from economy.core import model as M
from economy.kernel import tick as K, numba as N
from economy.server.runtime import KernelRuntime
from economy.server.persistence import save_checkpoint,load_checkpoint
from tools.buying_research.engine import ResearchEngine
from tools.buying_research.recording import Recorder
import tools.buying_research.engine as E


# Truncating below 4,033 companies leaves only C4 buyers and no C3 suppliers in
# this catalog's initialization order. Use enough active firms to exercise both
# complexity phases; small-population fixtures are not economic comparisons.
CFG={'t2FirmCount':4200,'distributorCount':1000,'seed':811}


def compare(test,a,b):
    for name in a.array_names:
        np.testing.assert_array_equal(getattr(a,name),getattr(b,name),err_msg=name)
    for name in ('costSinks','equipmentSinks','lm1','lm3','aov1','aov3'):
        test.assertEqual(getattr(a,name),getattr(b,name),name)
    np.testing.assert_array_equal(a.lm2,b.lm2);np.testing.assert_array_equal(a.aov2,b.aov2)


class WorldTests(unittest.TestCase):
    def test_compiled_reference_settlement_and_accounting(self):
        with tempfile.TemporaryDirectory() as d:
            pa=Path(d)/'a';pb=Path(d)/'b';pa.mkdir();pb.mkdir()
            a=KernelRuntime(CFG);b=KernelRuntime(CFG)
            ea=ResearchEngine(a,'hybrid',pa);eb=ResearchEngine(b,'hybrid',pb,{'skipRedundantSolves':False})
            recorder=Recorder(pa,a.world,a.cfg)
            for t in range(1,5):
                old0=a.world.t0Inv.copy();old1=a.world.t1Fin.copy();ea.step(t,a.state)
                original=(E.procure,E.clear_retail,E.manufacture)
                try:
                    E.procure=original[0].py_func;E.clear_retail=original[1].py_func;E.manufacture=original[2].py_func
                    eb.step(t,b.state)
                finally:E.procure,E.clear_retail,E.manufacture=original
                compare(self,a.world,b.world)
                for name in ('events1','events2','events3','local_requests1','local_requests2'):
                    np.testing.assert_array_equal(getattr(ea,name),getattr(eb,name),err_msg=name)
                before={k:getattr(a.world,k).copy() for k in a.world.array_names}
                if t==1:self.assertTrue(np.any(a.world.t2Preferred>=0),'successful full input orders establish incumbents')
                recorder.record(a.world,t,a.state,old0,old1)
                for key,value in before.items():np.testing.assert_array_equal(value,getattr(a.world,key),err_msg=key)
                from economy.core.state import validate_storage
                validate_storage(a.world,a.cfg)
            inv=recorder.invariants()
            self.assertLess(inv['maxCompanyEquityResidual'],1e-6)
            self.assertLess(inv['maxMoneyResidual'],1e-4)
            self.assertEqual(inv['maxEmbodiedGoodsResidual'],0)
            self.assertGreaterEqual(inv['minStock'],0);self.assertGreaterEqual(inv['minCash'],0)

    def test_checkpoint_continuation(self):
        with tempfile.TemporaryDirectory() as d:
            pa=Path(d)/'a';pb=Path(d)/'b';pa.mkdir();pb.mkdir()
            a=KernelRuntime(CFG);ea=ResearchEngine(a,'local',pa)
            for t in range(1,5):ea.step(t,a.state)
            save_checkpoint(str(pa/'world'),a.cfg,4,a.world,a.state)
            ea.save(pa/'research.npz')
            cfg,t,w,state=load_checkpoint(str(pa/'world'))
            b=KernelRuntime(cfg);b.world=w;b.state=state;b.tick=t
            eb=ResearchEngine(b,'local',pb);eb.restore(pa/'research.npz')
            for t in range(5,9):
                ea.step(t,a.state);eb.step(t,b.state);compare(self,a.world,b.world)
                for name in ('local1','local2','market1','market2'):np.testing.assert_array_equal(getattr(ea,name),getattr(eb,name))

    def test_production_gate_and_price_learning_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            a=KernelRuntime(CFG);b=KernelRuntime(CFG)
            for rt in (a,b):
                w=rt.world
                for firm in range(CFG['t2FirmCount']):
                    slots,_,used=K.tier2_storage_layout(w,rt.cfg,firm)
                    for m in used:
                        arr=w.t2Raw if m<4 else w.t2T1Raw
                        basis=w.t2RawBasis if m<4 else w.t2T1Basis
                        index=firm*(4 if m<4 else M.NI)+m
                        arr[index]=np.floor(slots[m]);basis[index]=1.25
                w.t2LearnTicks[:int(w.t2LineCount)]=30
            eb=ResearchEngine(b,'hybrid',Path(d))
            N.operate_tier2(a.world,a.cfg,30)
            for phase in M.TIER_BOUNDARIES['T2']:
                eb.buy_make_phase(30,phase,eb.local2)
            compare(self,a.world,b.world)

    def test_sales_floor_signal_and_checkpoint(self):
        from tools.buying_research.local_floor import LocalSalesFloor
        with tempfile.TemporaryDirectory() as d:
            pa=Path(d)/'a';pb=Path(d)/'b';pa.mkdir();pb.mkdir()
            a=KernelRuntime(CFG);ea=LocalSalesFloor(a,'local',pa)
            for tick in range(1,5):
                old1=ea.local1.copy();old2=ea.local2.copy();ea.step(tick,a.state)
                alpha=2/(ea.options['window']+1)
                # Independent expression of the declared observation: actual
                # fallback sales are a floor, never added to fulfilled requests.
                np.testing.assert_allclose(ea.local1,(1-alpha)*old1+alpha*np.maximum(ea.local_requests1,a.world.t1Sold),rtol=1e-14,atol=1e-12)
                np.testing.assert_allclose(ea.local2,(1-alpha)*old2+alpha*np.maximum(ea.local_requests2,a.world.t2Sold[:ea.lc]),rtol=1e-14,atol=1e-12)
            save_checkpoint(str(pa/'world'),a.cfg,4,a.world,a.state);ea.save(pa/'research.npz')
            cfg,t,w,state=load_checkpoint(str(pa/'world'));b=KernelRuntime(cfg);b.world=w;b.state=state;b.tick=t
            eb=LocalSalesFloor(b,'local',pb);eb.restore(pa/'research.npz')
            for tick in range(5,9):
                ea.step(tick,a.state);eb.step(tick,b.state);compare(self,a.world,b.world)
                for name in ('local1','local2','market1','market2'):
                    np.testing.assert_array_equal(getattr(ea,name),getattr(eb,name))


if __name__=='__main__':unittest.main()
