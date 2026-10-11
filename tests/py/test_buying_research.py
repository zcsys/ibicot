import itertools
import math
import unittest
import numpy as np

from tools.buying_research.solvers import (retail, marginal_values, demand_quantity,
    industry, industry_enumerate, canonical_industry, sample_distinct, industrial_value)
from tools.buying_research.oracle import retail_oracle, industry_oracle, multi_route_oracle
from tools.buying_research.scalar_solver import solve as scalar_industry


class BasketTests(unittest.TestCase):
    def check_retail(self,values,prices,stock,pref,bid,fee,cash=1e10):
        args=(np.array(values,dtype=float),np.array(prices,dtype=float),np.array(stock,dtype=float),pref,bid,float(fee),float(cash))
        result=retail(*args);reference=retail.py_func(*args);oracle=retail_oracle(*args)
        np.testing.assert_array_equal(result[0],oracle[0]);np.testing.assert_array_equal(result[0],reference[0])
        np.testing.assert_allclose(result[1:4],oracle[1:4],atol=1e-9,rtol=1e-12)
        self.assertEqual(result[4],oracle[4]);return result

    def test_retail_random_independent_oracle(self):
        rng=np.random.default_rng(92753)
        for _ in range(1500):
            n=int(rng.integers(1,5));limit=int(rng.integers(1,6))
            values=np.sort(rng.integers(0,20,size=limit))[::-1]
            self.check_retail(values,rng.integers(1,15,size=n),rng.integers(0,5,size=n),
                int(rng.integers(-1,n)),int(rng.integers(0,6)),int(rng.integers(0,15)),int(rng.integers(0,60)))

    def test_four_fee_preference_cases(self):
        # Q=2 at incumbent quote 11; partial challenger leads to a split basket.
        for full,available in itertools.product((False,True),repeat=2):
            out=self.check_retail([20,15],[11,1],[2 if available else 1,2 if full else 1],0,2,2)
            self.assertEqual(out[3],2 if available else 0)
            self.assertEqual(out[4],1 if full else 0)

    def test_bid_boundary(self):
        for stock in (1,2,3):
            result=self.check_retail([20,15],[11,1],[stock,2],0,2,2)
            self.assertEqual(result[3],2 if stock>=2 else 0)

    def test_cash_goods_but_not_fee_and_fee_greater_than_savings(self):
        out=self.check_retail([10],[8,7],[1,1],0,1,3,7)
        self.assertEqual(sum(out[0]),0)
        out=self.check_retail([10],[8,7],[1,1],0,1,3,20)
        np.testing.assert_array_equal(out[0],[1,0])

    def test_empty_zero_no_incumbent_equal_quotes(self):
        for pref in (-1,0,1):
            self.assertEqual(sum(self.check_retail([10,5],[2,2],[0,0],pref,2,4)[0]),0)
        np.testing.assert_array_equal(self.check_retail([10,5],[2,2],[2,2],1,2,0)[0],[0,2])
        self.check_retail([2+1e-10],[2,2],[1,1],-1,1,0)
        self.assertEqual(self.check_retail([1],[2,3],[2,2],-1,1,0)[3],0)
        self.assertEqual(self.check_retail([10,5],[2,3],[2,2],-1,2,0)[4],0)

    def test_fallback_is_price_sensitive_and_stock_live(self):
        result=self.check_retail([12,8,4],[1,10],[1,5],-1,3,0)
        np.testing.assert_array_equal(result[0],[1,0])
        # Sequential buyers cannot consume the same available units twice.
        first=self.check_retail([12,8],[1],[2],-1,2,0)
        second=self.check_retail([12,8],[1],[2-first[0][0]],-1,2,0)
        self.assertEqual(sum(first[0])+sum(second[0]),2)

    def test_curve_half_price_and_rounding(self):
        for eta in (0.5,1.,2.,4.):
            self.assertAlmostEqual(20/(1+(7/7)**eta),10)
            for u in (0.,1e-12,.01,.3,.77,.999):
                v=marginal_values(20.,7.,eta,u)
                for p in (0.1,1.,7.,14.,100.,1e9):
                    q=demand_quantity(20.,7.,eta,p,u)
                    self.assertEqual(q,int(np.count_nonzero(v>p)))

    def test_distinct_sampling_and_small_markets(self):
        for n in (0,1,4,6,30):
            for pref in (-1,0):
                ids=np.arange(n,dtype=np.int64)
                out=sample_distinct(ids,pref,137,40,70,3)
                self.assertEqual(len(set(out)),len(out))
                self.assertEqual(len(out),min(n,5+(1 if pref in ids else 0)))
                np.testing.assert_array_equal(out,sample_distinct.py_func(ids,pref,137,40,70,3))
                if pref in ids:self.assertIn(pref,out)

    def test_industry_random_oracle(self):
        rng=np.random.default_rng(8756)
        for _ in range(500):
            m=int(rng.integers(1,3));n=3
            held=rng.integers(0,4,size=m).astype(float);ratios=rng.integers(1,3,size=m).astype(float)
            lots=rng.integers(1,3,size=m).astype(float);spaces=rng.integers(1,4,size=m).astype(float)
            slots=np.full(m,6.);prices=rng.integers(1,10,size=(m,n)).astype(float)
            stocks=rng.integers(0,7,size=(m,n)).astype(float);counts=np.full(m,n,dtype=np.int64)
            prefs=rng.integers(-1,n,size=m);fees=rng.integers(0,5,size=m).astype(float);bids=rng.integers(0,7,size=m)
            args=(held,ratios,lots,spaces,slots,15.,prices,stocks,counts,prefs,fees,bids,6,
                  float(rng.integers(0,3)),float(rng.integers(3,30)),float(rng.integers(1,10)),1.,float(rng.integers(1,50)),1.)
            result=industry(*args);oracle=industry_oracle(*args)
            np.testing.assert_array_equal(result[0],oracle[0]);np.testing.assert_array_equal(result[1],oracle[1])
            np.testing.assert_allclose(result[2],oracle[2],atol=1e-9,rtol=0)
            self.assertEqual(result[3],oracle[3]);self.assertAlmostEqual(result[4],oracle[4],places=8)
            reference=industry.py_func(*args)
            np.testing.assert_array_equal(result[0],reference[0]);self.assertAlmostEqual(result[4],reference[4],places=8)

    def test_shared_input_multiple_routes(self):
        # Two routes share ingredient 0; independent 2-unit plans would overbuy it.
        out=multi_route_oracle([0,0],[[1,1],[2,0]],[2,2],[[0,8,12],[0,7,9]],
            [[(1,3,0,0)],[(2,2,0,1)]],[1,1],[1,1],[3,2],5,8,[1,1])
        self.assertEqual(out[1],(1,1));self.assertEqual(out[3],(3,1));self.assertEqual(out[0],10)

    def test_fast_path_decimal_boundaries_against_full_enumeration(self):
        rng=np.random.default_rng(65751)
        for _ in range(3000):
            m=int(rng.integers(1,3));n=6;held=rng.integers(0,12,size=m).astype(float)
            ratio=rng.integers(1,3,size=m).astype(float);prices=rng.integers(1,1500,size=(m,n))/100
            stocks=rng.integers(0,30,size=(m,n)).astype(float);fees=rng.integers(0,100,size=m)/137
            cash=float(rng.integers(1,10000))/100;reserve=.75
            if rng.random()<.25:cash=float(prices[0,0]*int(rng.integers(1,20)))
            args=(held,ratio,np.ones(m),np.ones(m),np.full(m,30.),60.,prices,stocks,np.full(m,n,dtype=np.int64),
                rng.integers(-1,n,size=m),fees,rng.integers(0,30,size=m),24,float(rng.integers(0,12)),
                float(rng.integers(500,5000))/100,float(rng.integers(1,30)),reserve,cash,reserve)
            result=industry(*args);slow=industry_enumerate(*args)
            np.testing.assert_array_equal(result[0],slow[0]);np.testing.assert_array_equal(result[1],slow[1])
            self.assertEqual(result[3],slow[3]);self.assertAlmostEqual(result[4],slow[4],places=8)
            scalar=scalar_industry(m,args[0],args[1],args[3],args[4],*args[5:],np.empty(42,dtype=np.int64))
            np.testing.assert_array_equal(scalar[:m],slow[0]);np.testing.assert_array_equal(scalar[2:2+m],slow[1])
            self.assertEqual(scalar[6],slow[3]);self.assertAlmostEqual(scalar[7],slow[4],places=8)

    def test_canonical_bid_uses_finite_physical_bounds(self):
        held=np.zeros(2);ratio=np.ones(2);lots=np.ones(2);spaces=np.ones(2);slots=np.full(2,100.)
        bids,y=canonical_industry(held,ratio,lots,spaces,slots,200.,np.full(2,3.4),36,0.,9.,90.,.5)
        expected=industry_enumerate(held,ratio,lots,spaces,slots,200.,np.full((2,1),3.4),np.full((2,1),36.),
            np.ones(2,dtype=np.int64),np.full(2,-1,dtype=np.int64),np.zeros(2),np.zeros(2,dtype=np.int64),36,
            0.,9.,90.,.5,1e9,0.)
        self.assertGreater(y,0);self.assertEqual(y,expected[3]);np.testing.assert_array_equal(bids,expected[1])

    def test_uniform_input_price_comparative_static(self):
        # One stocked supplier per ingredient, fixed valuations/fees/physical
        # limits, and ample cash: scaling all acquisition prices upward cannot
        # increase the chosen output plan. This claim deliberately excludes
        # supplier switches and endogenous fee-availability discontinuities.
        rng=np.random.default_rng(30817)
        for _ in range(80):
            held=rng.integers(0,5,size=2).astype(float);ratios=rng.integers(1,3,size=2).astype(float)
            lots=rng.integers(1,3,size=2).astype(float);base=rng.integers(1,8,size=(2,1)).astype(float)
            plans=[]
            for scale in (.25,.5,1.,2.,4.):
                out=industry(held,ratios,lots,np.ones(2),np.full(2,50.),100.,base*scale,np.full((2,1),100.),
                    np.ones(2,dtype=np.int64),np.full(2,-1,dtype=np.int64),np.zeros(2),np.zeros(2,dtype=np.int64),
                    20,0.,20.,20.,.5,1e6,.5)
                plans.append(out[3])
            self.assertEqual(plans,sorted(plans,reverse=True))


if __name__=='__main__':unittest.main()
