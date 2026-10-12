import unittest
import math
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import tick as K
from tools.buying_v2.native_inventory import checked_produce


class NativeInventoryTests(unittest.TestCase):
    def test_fractional_input_and_finished_stock_match_actual_phase(self):
        for fraction in (.1,.5,.999999999):
            cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=1,seed=137))
            product=M.T2_PRODUCTS[int(w.t2LineProduct[0])];phase=product['complexity']
            for m,q in product['ingredients']:
                (w.t2Raw if m<M.NE else w.t2T1Raw)[m]+=q*2+fraction
                (w.t2RawBasis if m<M.NE else w.t2T1Basis)[m]=.1
            w.t2Fin[0]=fraction;w.t2FinBasis[0]=.2;w.t2Price[0]=100.
            inputs=np.array([(w.t2Raw if m<M.NE else w.t2T1Raw)[m] for m in range(M.NI)])
            basis=np.array([(w.t2RawBasis if m<M.NE else w.t2T1Basis)[m] for m in range(M.NI)])
            _,slot,_=K.tier2_storage_layout(w,cfg,0)
            expected=checked_produce(inputs,basis,[m for m,q in product['ingredients']],[q for m,q in product['ingredients']],
                cash=w.t2Cash[0],finished=w.t2Fin[0],finished_basis=w.t2FinBasis[0],output_qty=product['outputQty'],
                capacity=cfg['t2Capacity'][phase],finished_slot=math.floor(slot/phase),conversion=M.conversion_cost(phase,cfg),
                quote=100.,overhead=K.production_line_overhead(w,cfg,'t2')[0],margin_band=cfg['productionMarginBand'])
            K._operate_tier2_phase(w,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1,phase,purchase_company=lambda *args:None)
            actual=np.array([(w.t2Raw if m<M.NE else w.t2T1Raw)[m] for m in range(M.NI)])
            np.testing.assert_array_equal(expected[0],actual)
            self.assertEqual(expected[1],w.t2Cash[0]);self.assertEqual(expected[2],w.t2Fin[0])
            self.assertEqual(expected[3],w.t2FinBasis[0]);self.assertEqual(expected[4],w.t2Made[0])

    def test_subunit_scaling_changes_existing_gate_and_must_not_be_used(self):
        quote=1.;unit=1.+1.5e-9
        self.assertEqual(M.production_batches(1,1,unit,quote,-1.,.05),0)
        self.assertEqual(M.production_batches(1,2,unit/2,quote/2,-1.,.05),1)

    def test_fixed_fractional_residue_is_not_native_arithmetic(self):
        self.assertNotEqual((.1+3)-3,.1)
        result=checked_produce([3.1],[1.],[0],[3],cash=10.,finished=0.,finished_basis=0.,output_qty=1,
            capacity=1,finished_slot=10,conversion=.5,quote=10.,overhead=0.,margin_band=.05)
        self.assertEqual(result[0][0],3.1-3)
        self.assertNotEqual(result[0][0],.1)

    def test_baseline_checkpoint_retains_fractional_inventory(self):
        import tempfile
        from pathlib import Path
        from economy.server.persistence import save_checkpoint,load_checkpoint
        cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=1,seed=137))
        w.t2Raw[0]=.1;w.t2Fin[0]=.5
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/'fractional')
            save_checkpoint(path,cfg,0,w)
            _,_,loaded,_=load_checkpoint(path)
            self.assertEqual(loaded.t2Raw[0],.1)
            self.assertEqual(loaded.t2Fin[0],.5)
