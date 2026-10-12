import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, add_tier2_line
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket
from tools.buying_v2.industrial_adapter import company_problem, buy_t2_reference


class IndustrialAdapterTests(unittest.TestCase):
    def fixture(self):
        return reset_world(dict(t2FirmCount=3, distributorCount=1, seed=137))

    def test_joint_actual_purchase_reconciles_goods_cash_and_basis(self):
        cfg,w=self.fixture()
        phase=M.T2_PRODUCTS[int(w.t2LineProduct[0])]['complexity']
        book=InputMarket(w,1)
        book.fin[:]=10000.
        old_stock=book.fin.copy(); old_cash=book.cash.copy()
        before=float(w.t2Cash[0])
        result=buy_t2_reference(w,cfg,1,0,phase,book)
        p=result['problem']; q=result['allocation']; posted=result['postings']
        self.assertGreater(sum(q),0)
        self.assertAlmostEqual(before-w.t2Cash[0],posted['goods']+posted['fees'])
        self.assertAlmostEqual(float((book.cash-old_cash).sum()),posted['goods']+posted['fees'])
        self.assertEqual(float((old_stock-book.fin).sum()),sum(q))
        for j,m in enumerate(result['identity']['materials']):
            raw,basis,width=(w.t2Raw,w.t2RawBasis,M.NE) if m<M.NE else (w.t2T1Raw,w.t2T1Basis,M.NI)
            value=p.held[j]*p.basis[j]+sum(o.price*x for o,x in zip(p.offers,q) if o.material==j)
            self.assertAlmostEqual(raw[m]*basis[m],value)
        self.assertEqual(p.lines,())

    def test_installed_order_is_not_rotated_in_production_model(self):
        cfg,w=self.fixture()
        native=int(w.t2LineProduct[0]); phase=M.T2_PRODUCTS[native]['complexity']
        other=next(p['id'] for p in M.T2_PRODUCTS if p['complexity']==phase and p['id']!=native and p['invented'] and p['sectorIndex']==M.T2_PRODUCTS[native]['sectorIndex'])
        add_tier2_line(w,cfg,0,M.T2_PRODUCTS[other],paid=False)
        book=InputMarket(w,1)
        p,identity=company_problem(w,cfg,1,0,phase,book,K.production_line_overhead(w,cfg,'t2'),workload_values=True)
        self.assertEqual(identity['lines'],[int(w.t2FirmLines[i]) for i in range(2)])

    def test_over_slot_stock_is_retained_and_blocks_only_that_input(self):
        cfg,w=self.fixture()
        phase=M.T2_PRODUCTS[int(w.t2LineProduct[0])]['complexity']
        slots,_,_=K.tier2_storage_layout(w,cfg,0)
        m=M.T2_PRODUCTS[int(w.t2LineProduct[0])]['ingredients'][0][0]
        raw=w.t2Raw if m<M.NE else w.t2T1Raw
        raw[m]=int(slots[m])+1
        old=raw[m]
        book=InputMarket(w,1)
        book.fin[:]=10000.
        result=buy_t2_reference(w,cfg,1,0,phase,book)
        self.assertEqual(raw[m],old)
        j=result['identity']['materials'].index(m)
        self.assertEqual(result['postings']['quantities'][j],0)

    def check_engine(self, engine_type):
        import tempfile
        from pathlib import Path
        from economy.server.runtime import KernelRuntime
        from economy.server.persistence import save_checkpoint, load_checkpoint
        from tools.buying_research.recording import Recorder
        with tempfile.TemporaryDirectory() as directory:
            rt=KernelRuntime(dict(t2FirmCount=30,distributorCount=100,seed=137))
            engine=engine_type(rt)
            recorder=Recorder(Path(directory),rt.world,rt.cfg)
            for tick in range(1,5):
                old0,old1=rt.world.t0Inv.copy(),rt.world.t1Fin.copy()
                engine.step(tick)
                recorder.record(rt.world,tick,rt.state,old0,old1)
            for key,value in recorder.invariants().items():
                if key.startswith('max') and key.endswith('ToleranceRatio'):
                    self.assertLessEqual(value,1,key)
            stem=str(Path(directory)/'checkpoint')
            save_checkpoint(stem,rt.cfg,4,rt.world,rt.state,{'purchasePolicy':engine.policy})
            cfg,tick,world,state=load_checkpoint(stem,purchase_policy=engine.policy)
            resumed=KernelRuntime(cfg)
            resumed.world,resumed.state=world,state
            other=engine_type(resumed)
            for tick in range(5,7):
                engine.step(tick);other.step(tick)
                for name in world.array_names:
                    np.testing.assert_array_equal(getattr(rt.world,name),getattr(world,name),err_msg=name)
                np.testing.assert_array_equal(engine.industrial_observations,other.industrial_observations)

    def test_full_reference_ticks_reconcile_and_continue(self):
        from tools.buying_v2.engine import ReplenishmentReferenceEngine
        self.check_engine(ReplenishmentReferenceEngine)

    def test_both_industrial_tiers_reconcile_and_continue(self):
        from tools.buying_v2.engine import IndustrialReferenceEngine
        self.check_engine(IndustrialReferenceEngine)



if __name__=='__main__':
    unittest.main()
