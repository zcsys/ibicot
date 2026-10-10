"""Restocking respects input partitions independently of production profitability."""
import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, add_tier2_line, tier1_goods_space, tier2_goods_space
from economy.kernel import tick as K
from economy.kernel import numba as NB

class StorageSlotTests(unittest.TestCase):
    def test_split_and_shared_input_deduplication(self):
        cfg,w=reset_world({'t2FirmCount':200,'distributorCount':30})
        w.t1Operates[4]=1  # Shared element across installed refinery lines.
        raw,finished,inputs=K.tier1_storage_layout(w,cfg,0)
        self.assertEqual(raw*len(inputs),tier1_goods_space(w,cfg,0)/2)
        self.assertEqual(finished*2,tier1_goods_space(w,cfg,0)/2)
        p=next(p for p in M.T2_PRODUCTS if len(p['ingredients'])==3)
        w.t2LineProduct[0]=p['id']
        raw,finished,inputs=K.tier2_storage_layout(w,cfg,0)
        self.assertEqual(len(inputs),3)
        self.assertAlmostEqual(raw,tier2_goods_space(w,cfg,0)/6)
        self.assertEqual(finished,tier2_goods_space(w,cfg,0)/2)

    def test_both_engines_buy_into_slots_even_when_production_is_unprofitable(self):
        worlds=[]
        for fast in (False,True):
            if fast and not NB._HAVE_NUMBA:continue
            cfg,w=reset_world({'t2FirmCount':200,'distributorCount':30})
            # Include every recipe and complexity, not only the first market.
            for i,p in enumerate(M.T2_PRODUCTS):
                w.t2LineProduct[i]=i;w.t2Sector[i]=p['sectorIndex']
            w.t0Inv[:]=np.isfinite(w.t0Price)*500000
            w.t0Price[np.isfinite(w.t0Price)]=1
            w.t0InvBasis[:]=1
            w.t1Price[:]=.01
            if fast:NB.plan_and_buy_inputs(w,cfg,1)
            else:K.plan_and_buy_inputs(w,cfg,M.PRODUCTS,K.T0P,1)
            self.assertGreater(w.t1Bought.sum(),0)
            for firm in range(M.N1):
                slot,_,inputs=K.tier1_storage_layout(w,cfg,firm)
                for e in range(M.NE):self.assertLessEqual(w.raw[firm*M.NE+e],slot if e in inputs else 0)
            # Sell plenty of refinery goods, while manufacturers' output price is below cost.
            w.t1Fin[:]=w.t1Operates*100000.;w.t1FinBasis[:]=1.;w.t1Price[:]=1.
            w.t2Price[:200]=.01
            if fast:NB.operate_tier2(w,cfg,1)
            else:K.operate_tier2(w,cfg,M.PRODUCTS,K.T0P,M.T2_PRODUCTS,1)
            self.assertGreater(w.t2Bought.sum(),0)
            self.assertEqual(w.t2Made.sum(),0)
            for firm in range(200):
                slot,_,inputs=K.tier2_storage_layout(w,cfg,firm)
                for m in range(M.NP):
                    held=(w.t2Raw if m<4 else w.t2T1Raw)[firm*(M.NE if m<4 else M.NP)+m]
                    self.assertLessEqual(held,slot if m in inputs else 0)
            worlds.append(w)
        if len(worlds)==2:
            for name in worlds[0].array_names:
                np.testing.assert_array_equal(getattr(worlds[0],name),getattr(worlds[1],name),err_msg=name)

    def test_existing_overfull_input_cannot_buy_more(self):
        cfg,w=reset_world({'t2FirmCount':12,'distributorCount':30})
        slot,_,inputs=K.tier2_storage_layout(w,cfg,0)
        m=next(iter(inputs));arr=w.t2Raw if m<4 else w.t2T1Raw
        arr[m]=slot+10
        self.assertEqual(K.transfer_tier2_input(w,cfg,0,m,0,100),0)
        self.assertEqual(arr[m],slot+10)
