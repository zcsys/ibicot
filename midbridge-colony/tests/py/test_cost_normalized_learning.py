"""Price learning must not mistake an input-cost change for a pricing gain."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from economy.core.config import normalize_config
from economy.core.state import reset_world
from economy.kernel import tick as K, numba as NB
from economy.server.persistence import save_checkpoint, load_checkpoint


class CostNormalizedLearningTests(unittest.TestCase):
    def test_price_response_and_engine_parity(self):
        # Prior period: price 10, sales 100/tick, old cost 8 (gross 200/tick).
        # New cost 5 must not turn a harmful cut to 9 into an apparent improvement.
        for tier in ('t0', 't1', 't2'):
            for price, quantity, cost, expected in [(10,100,5,'hold'), (10,100,9,'hold'),
                    (9,100,5,'up'), (9,150,5,'down'), (9,0,5,'up')]:
                with self.subTest(tier=tier, price=price, quantity=quantity, cost=cost):
                    cfg=normalize_config({})
                    def make():
                        w=SimpleNamespace()
                        vals={'Price':price,'LearnTicks':60,'LearnProfit':(price-cost)*quantity*60,
                              'LearnRevenue':price*quantity*60,'LearnSales':quantity*60,
                              'LearnPrevious':200,'LearnPreviousRevenue':1000,'LearnPreviousSales':100,
                              'LearnDirection':-1,'LearnDemand':quantity*60,'LearnStep':1,
                              'LearnOpportunity':1000,'LearnPotentialOpportunity':1000}
                        for k,v in vals.items():setattr(w,tier+k,np.array([float(v)]))
                        setattr(w,'t0InvBasis' if tier=='t0' else tier+'FinBasis',np.array([float(cost)]))
                        return K.price_learning_view(w,tier)
                    v=make(); fast=make()
                    result=K.learned_quote(v,cfg,0,10000,60,price)
                    if expected=='hold':self.assertEqual(result,price)
                    elif expected=='up':self.assertGreater(result,price)
                    else:self.assertLess(result,price)
                    nr=NB._learned_quote(int(tier[-1]),fast['price'],fast['ages'],fast['profits'],fast['sales'],
                        fast['previous'],fast['revenues'],fast['previousRevenue'],fast['previousSales'],
                        fast['costBasis'],fast['direction'],fast['demand'],fast['steps'],fast['opportunity'],
                        fast['potentialOpportunity'],0,10000.,60,cfg['priceObservationTicks'],
                        cfg['researchPriceMinimumPotentialOrders'],cfg['researchPriceMaxObservationTicks'],
                        cfg['researchPriceMinimumOpportunities'],float(price),cfg['marketAnchorBand'],
                        cfg['pricingAggressiveness'],cfg['wholesalePriceResponse'])
                    self.assertEqual(result,nr)
                    for key in v:
                        if key!='tier':np.testing.assert_allclose(v[key],fast[key],equal_nan=True)
                    self.assertEqual(v['previousSales'][0],quantity)
                    self.assertEqual(v['previousRevenue'][0],price*quantity)
                    self.assertEqual(v['revenues'][0],0)

    def test_checkpoint_roundtrip_and_legacy_learning_migration(self):
        cfg,w=reset_world({'t2FirmCount':2,'distributorCount':2})
        w.t1LearnRevenue[0]=100;w.t1LearnPreviousRevenue[0]=50;w.t1LearnPreviousSales[0]=5
        with tempfile.TemporaryDirectory() as td:
            stem=str(Path(td)/'state');save_checkpoint(stem,cfg,30,w)
            _,_,loaded,_=load_checkpoint(stem)
            for name in w.array_names:np.testing.assert_array_equal(getattr(w,name),getattr(loaded,name))
            meta=json.loads(Path(stem+'.json').read_text());meta['version']=13
            Path(stem+'.json').write_text(json.dumps(meta))
            new=('LearnRevenue','LearnPreviousRevenue','LearnPreviousSales')
            np.savez(stem+'.npz',**{k:getattr(w,k) for k in w.array_names if not k.endswith(new)})
            _,_,loaded,_=load_checkpoint(stem)
            self.assertEqual(loaded.t1LearnRevenue[0],0)
            self.assertTrue(np.isnan(loaded.t1LearnPreviousRevenue[0]))
            np.testing.assert_array_equal(loaded.t1Price,w.t1Price)
            np.testing.assert_array_equal(loaded.t1Cash,w.t1Cash)
