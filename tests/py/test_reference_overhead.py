"""Nominal overhead changes decision references, not posted production cost."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import numba as NB
from economy.server.runtime import KernelRuntime
from economy.server.persistence import save_checkpoint, load_checkpoint

class ReferenceOverheadTests(unittest.TestCase):
    def test_default_allowances_and_reference_routes(self):
        cfg,w=reset_world({'distributorCount':1,'t2FirmCount':1})
        for p in M.PRODUCTS+M.T2_PRODUCTS:
            c=p['complexity']
            expected=2140/6000 if c<=2 else 76/(32 if c==3 else 24)
            self.assertAlmostEqual(M.reference_overhead_per_unit(p,cfg),expected)
        self.assertAlmostEqual(M.reference_refinery_cost(M.PRODUCTS[0],cfg),1.5+2140/6000)
        self.assertAlmostEqual(M.input_reference_cost(0,cfg),1.25+2140/6000)
        self.assertAlmostEqual(M.input_reference_cost(4,cfg),2.75+2140/6000)
        c3=next(p for p in M.T2_PRODUCTS if p['complexity']==3)
        self.assertEqual(M.reference_tier2_cost(c3,cfg),5.8125+76/32)
        for p in M.T2_PRODUCTS:
            if p['complexity']==4:
                self.assertAlmostEqual(M.reference_tier2_cost(p,cfg),M.initial_tier2_cost(p,cfg)+76/24)
        self.assertEqual(w.t1UnitCost[0],1.5)
        self.assertEqual(w.t1Price[0],2.32)
        self.assertEqual(w.t2UnitCost[0],9.890625)
        self.assertEqual(w.t2Price[0],16.32)
        self.assertEqual(float(w.t1FinBasis.sum()+w.t2FinBasis.sum()),0.)
        self.assertEqual(w.costSinks,0.)

    def test_switching_references_exclude_overhead(self):
        cfg,_=reset_world({'distributorCount':1,'t2FirmCount':1})
        for p in M.T2_PRODUCTS:
            profile=M.procurement_profile(p,cfg,M.reference_tier2_cost(p,cfg))
            self.assertEqual(profile['switchingReference'],M.initial_tier2_cost(p,cfg))
        np.testing.assert_array_equal(NB._switching_reference_cached(NB._reference_key(cfg)),
            [M.initial_tier2_cost(p,cfg) for p in M.T2_PRODUCTS])

    def test_zero_overhead_and_capacity_scaling(self):
        cfg,_=reset_world({'distributorCount':1,'t2FirmCount':1})
        p=M.PRODUCTS[4]
        changed={**cfg,'t1CapacityC2':3000}
        self.assertAlmostEqual(M.reference_overhead_per_unit(p,changed),2140/3000)
        zero={**cfg,'storageRentPerThousandPerTick':0,'t1IntelligencePerTick':0,'t2IntelligencePerTick':0}
        for p in M.T2_PRODUCTS:self.assertEqual(M.reference_tier2_cost(p,zero),M.initial_tier2_cost(p,zero))
        self.assertEqual(M.input_reference_cost(0,zero),1.25)

    def test_cache_tracks_all_overhead_inputs(self):
        cfg,_=reset_world({'distributorCount':1,'t2FirmCount':1})
        for key,value in [('storage',24000),('t1C1Storage',60000),('t1C2Storage',70000),('t1Capacity',3000),('t1CapacityC2',2000),('storageRentPerThousandPerTick',5),('t1IntelligencePerTick',3000),('t2IntelligencePerTick',40),('t2Capacity',{3:16,4:12,5:10})]:
            c={**cfg,key:value}
            np.testing.assert_array_equal(NB.input_reference_arrays(c),[M.input_reference_cost(m,c) for m in range(M.NI)])
            np.testing.assert_array_equal(NB.procurement_arrays(c),[M.reference_tier2_cost(p,c) for p in M.T2_PRODUCTS])
        np.testing.assert_array_equal(NB.input_reference_arrays(cfg),[M.input_reference_cost(m,cfg) for m in range(M.NI)])

    def test_live_reference_refresh_preserves_books_and_prices(self):
        rt=KernelRuntime({'t2FirmCount':1,'distributorCount':1})
        old=copy.deepcopy(rt.world)
        rt.apply_config({'t2IntelligencePerTick':52})
        self.assertAlmostEqual(rt.world.t2ReferenceCost[0]-old.t2ReferenceCost[0],32/24)
        for name in ['t1Price','t2Price','t1FinBasis','t2FinBasis','t1Cash','t2Cash','t2UnitCost']:
            np.testing.assert_array_equal(getattr(rt.world,name),getattr(old,name))
        self.assertEqual(rt.world.costSinks,old.costSinks)

    def test_checkpoint_migration_only_refreshes_derived_reference(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1})
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'state')
            save_checkpoint(path,cfg,0,w)
            _,_,loaded,_=load_checkpoint(path)
            for name in w.array_names:np.testing.assert_array_equal(getattr(w,name),getattr(loaded,name))
            w.t2ReferenceCost[:]=0
            save_checkpoint(path,cfg,0,w)
            meta=json.loads(Path(path+'.json').read_text());meta['version']=12
            Path(path+'.json').write_text(json.dumps(meta))
            _,_,loaded,_=load_checkpoint(path)
            self.assertEqual(loaded.t2ReferenceCost[0],9.890625+76/24)
            np.testing.assert_array_equal(loaded.t2Price,w.t2Price)
            np.testing.assert_array_equal(loaded.t2FinBasis,w.t2FinBasis)

    def test_browser_reference_matches_backend(self):
        data=subprocess.check_output(['node','-e',"require('./web/midbridge-catalog.js');const m=globalThis.Phase0Model;console.log(JSON.stringify(m.T2_PRODUCTS.map(p=>m.referenceTier2Cost(p))));"],text=True)
        cfg,_=reset_world({'t2FirmCount':1,'distributorCount':1})
        np.testing.assert_allclose(json.loads(data),[M.reference_tier2_cost(p,cfg) for p in M.T2_PRODUCTS],rtol=0,atol=1e-12)
