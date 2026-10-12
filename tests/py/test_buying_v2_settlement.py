import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel.input_market import InputMarket
from tools.buying_v2.industry_oracle import Problem, Offer
from tools.buying_v2.industrial_settlement import settle_t2


class IndustrialSettlementTests(unittest.TestCase):
    def fixture(self):
        cfg, w = reset_world(dict(t2FirmCount=3, distributorCount=1, seed=137))
        book = InputMarket(w, 1)
        ids = sorted(book.offers[0])[:3]
        for s, price, stock, basis in zip(ids, (10.,15.,30.), (2,20,20), (2.,3.,4.)):
            w.t1Price[s], w.t1Fin[s], w.t1FinBasis[s] = price, stock, basis
        w.t2Preferred[0] = ids[2]
        book = InputMarket(w, 1)
        w.lm2[1] = 2/(M.material_switching_reference(cfg)*(1+book.rel[ids[2]]))
        p = Problem((int(w.t2Raw[0]),), (float(w.t2RawBasis[0]),), (1.,), (10,), 100., float(w.t2Cash[0]),
                    tuple(Offer(0,s,float(book.price[s]),int(book.fin[s])) for s in ids),
                    (ids[2],), (5,), (2.,), (), ((0.,)*11,))
        return cfg,w,book,p,ids

    def test_actual_split_postings_and_single_fee(self):
        cfg,w,book,p,ids = self.fixture()
        before_buyer = w.t2Cash[0]
        before_sellers = w.t1Cash.copy()
        result = settle_t2(w,cfg,0,4,book,p,(2,6,0),(0,),(10,8,5))
        book.settle()
        self.assertEqual(result['goods'],110)
        self.assertEqual(result['fees'],2)
        self.assertEqual(result['productOrders'],1)
        self.assertEqual(result['positiveLegs'],2)
        self.assertEqual(w.t2Cash[0],before_buyer-112)
        self.assertAlmostEqual(float((w.t1Cash-before_sellers).sum()),112)
        self.assertEqual(w.t2Raw[0],8)
        self.assertEqual(w.t2RawBasis[0],110/8)
        self.assertEqual(w.t2Preferred[0],ids[2])
        np.testing.assert_array_equal(w.t1Sold[ids],[2,6,0])
        np.testing.assert_array_equal(w.t1COGS[ids],[4,18,0])
        self.assertEqual(w.t2SwitchingExpense[0],2)
        self.assertEqual(w.t1SwitchingIncome[ids[2]//M.NP],2)

    def test_invalid_request_is_atomic(self):
        cfg,w,book,p,ids = self.fixture()
        before = {name:getattr(w,name).copy() for name in w.array_names}
        stock, cash = book.fin.copy(), book.cash.copy()
        with self.assertRaisesRegex(ValueError,'remaining request'):
            settle_t2(w,cfg,0,4,book,p,(2,8,0),(0,),(10,8,5))
        for name,value in before.items():
            np.testing.assert_array_equal(getattr(w,name),value,err_msg=name)
        np.testing.assert_array_equal(book.fin,stock)
        np.testing.assert_array_equal(book.cash,cash)

    def test_all_fee_and_preference_combinations(self):
        from dataclasses import replace
        for full in (False, True):
            for available in (False, True):
                cfg,w,book,p,ids = self.fixture()
                if not available:
                    book.fin[ids[2]] = 4
                    p = replace(p, offers=(*p.offers[:2], replace(p.offers[2], stock=4)))
                allocation = (0,8,0) if full else (2,0,0)
                result = settle_t2(w,cfg,0,4,book,p,allocation,(0,),(10,8,5))
                self.assertEqual(result['fees'],2 if available else 0)
                self.assertEqual(w.t2Preferred[0],ids[1] if full else ids[2])

    def test_invalid_phase_is_rejected_before_mutation(self):
        cfg,w,book,p,ids = self.fixture()
        stock = book.fin.copy()
        with self.assertRaisesRegex(ValueError,'phase'):
            settle_t2(w,cfg,0,99,book,p,(2,6,0),(0,),(10,8,5))
        np.testing.assert_array_equal(book.fin,stock)

    def test_changed_supplier_requires_replan_before_mutation(self):
        cfg,w,book,p,ids = self.fixture()
        cash = w.t2Cash.copy()
        book.fin[ids[0]] -= 1
        with self.assertRaisesRegex(ValueError,'replan'):
            settle_t2(w,cfg,0,4,book,p,(2,6,0),(0,),(10,8,5))
        np.testing.assert_array_equal(w.t2Cash,cash)


if __name__ == '__main__':
    unittest.main()
