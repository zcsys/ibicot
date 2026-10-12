import unittest
import numpy as np
from tools.buying_v2.industry_oracle import Problem, Offer
from tools.buying_v2.funding import replenishment_plan
from tools.buying_v2.replenishment_compiled import fund_and_select, select, quoted_quantity
from test_buying_v2_replenishment import oracle


class CompiledFundingTests(unittest.TestCase):
    def test_joint_funding_matches_reference(self):
        rng=np.random.default_rng(887415)
        for _ in range(1000):
            n=int(rng.integers(1,4));lot=int(rng.integers(1,4))
            targets=tuple(int(rng.integers(0,7)) for m in range(n))
            spaces=tuple(float(rng.integers(1,4)) for m in range(n))
            offers=tuple(Offer(m,s,float(rng.integers(1,1000))/100,int(rng.integers(0,7)),lot) for m in range(n) for s in range(int(rng.integers(0,4))))
            inc=tuple(int(rng.integers(-1,3)) for m in range(n));fees=tuple(float(rng.integers(0,5)) for m in range(n))
            cash=float(rng.integers(0,4000))/100;room=float(rng.integers(0,30))
            p=Problem((0,)*n,(0.,)*n,spaces,targets,room,cash,offers,inc,(0,)*n,fees,(),tuple((0.,)*(t+1) for t in targets))
            funded,expected=replenishment_plan(p)
            # No-offer reference convention chooses lot 1 (all quantities zero).
            actual=fund_and_select(np.array(targets),np.array([o.material for o in offers],dtype=np.int64),
                np.array([o.supplier for o in offers],dtype=np.int64),np.array([o.price for o in offers],dtype=float),
                np.array([o.stock for o in offers],dtype=np.int64),np.array(inc),np.array(fees),cash,lot,np.array(spaces),room)
            np.testing.assert_array_equal(actual[0],funded.bids)
            np.testing.assert_array_equal(actual[1],funded.funded_demands)
            for a,b in zip(actual[3],expected):
                np.testing.assert_array_equal(a,b)

    def test_compiled_search_against_independent_enumeration(self):
        rng=np.random.default_rng(191415)
        for _ in range(400):
            targets=(4,4);lot=int(rng.integers(1,3))
            offers=tuple(Offer(m,s,float(rng.integers(1,5)),int(rng.integers(0,5)),lot) for m in range(2) for s in range(2))
            inc=(0,0);bids=(2,2);fees=(3.,2.)
            demands=tuple(int(rng.integers(0,5)) for o in offers)
            cash=float(rng.integers(0,30));room=float(rng.integers(0,13))
            expected=oracle(targets,offers,inc,bids,fees,cash,lot,room=room,demands=demands)
            actual=select(np.array(targets)//lot*lot,np.array([o.material for o in offers]),np.array([o.supplier for o in offers]),
                np.array([o.price for o in offers]),np.array([o.stock for o in offers]),np.array(inc),np.array(bids),
                np.array(fees),cash,lot,np.array(demands),np.array([1.,2.]),room,100000)
            self.assertEqual(tuple(actual[0]),expected[0]);self.assertEqual(actual[1],expected[1]);self.assertEqual(actual[2],expected[2])

    def test_empty_lot_shortcut_preserves_search_limits_and_zero_result(self):
        args=(np.array([4]),np.array([0,0]),np.array([0,1]),np.array([1.,1.]),
              np.array([1,1]),np.array([0]),np.array([2]),np.array([3.]),
              10.,2,np.array([2,4]),np.array([1.]),10.)
        # Different funded caps at equal quotes require general search even
        # when neither supplier has a complete lot. Zero-node limits still fail.
        with self.assertRaisesRegex(ValueError,'search limit'):
            select(*args,0)
        result=select(*args,1)
        np.testing.assert_array_equal(result[0],[0,0])
        self.assertEqual(result[1:3],(0,0.))
        np.testing.assert_array_equal(result[3],[0.])

    def test_same_reference_quote_reuse_with_binding_space(self):
        offers=(Offer(0,7,2.,4),Offer(0,9,2.,4),Offer(1,5,2.,4),Offer(1,6,2.,4))
        p=Problem((0,0),(0.,0.),(2.,1.),(4,4),5.,7.,offers,(7,5),(0,0),(2.,3.),(),((0.,)*5,(0.,)*5))
        funded,expected=replenishment_plan(p)
        actual=fund_and_select(np.array(p.slots),np.array([o.material for o in offers]),
            np.array([o.supplier for o in offers]),np.array([o.price for o in offers]),
            np.array([o.stock for o in offers]),np.array(p.incumbents),np.array(p.fees),p.cash,1,np.array(p.spaces),p.free_space)
        np.testing.assert_array_equal(actual[0],funded.bids)
        np.testing.assert_array_equal(actual[1],funded.funded_demands)
        for a,b in zip(actual[3],expected):np.testing.assert_array_equal(a,b)

    def test_scalar_quote_funding_preserves_ties_and_cash_boundary(self):
        targets=np.array([4,4,4]);rm=np.arange(3);prices=np.array([2.,2.,4.])
        order=np.array([1,0,2])
        for fn in (quoted_quantity,quoted_quantity.py_func):
            for k,quote,expected in ((0,2.,1),(2,2.,4),(0,1.,4),(0,3.,0)):
                self.assertEqual(fn(targets,rm,prices,targets,order,10.,1,k,quote),expected)
            for cash,expected in ((np.nextafter(5.,0.),9),(5.,10),(np.nextafter(5.,np.inf),10)):
                self.assertEqual(fn(np.array([10]),np.array([0]),np.array([.5]),np.array([10]),
                                    np.array([0]),cash,1,0,.5),expected)

    def test_limit_is_explicit(self):
        with self.assertRaisesRegex(ValueError,'search limit'):
            fund_and_select(np.array([10]),np.array([0]),np.array([0]),np.array([1.]),np.array([10]),
                            np.array([-1]),np.array([0.]),100.,1,np.array([2.]),10.,0)


if __name__=='__main__':
    unittest.main()
