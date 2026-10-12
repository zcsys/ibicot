import unittest
import numpy as np
from tools.buying_v2.quote_support_audit import audit
from tools.buying_v2.seller_history import SellerHistory


class QuoteSupportTests(unittest.TestCase):
    def history(self, quotes=(4., 8., 11.), zero=False, constrained=False):
        h = SellerHistory(8)
        for tick, q in enumerate(quotes, 1):
            sold = np.array([0. if zero else 10., 2., 1.])
            closing = np.full(3, 100.)
            exposure = np.array([[1., 1., 1.], [1., 1., 1.], [0., 0., 0.]])
            if constrained: exposure[2, 2] = 1.
            h.record('retail', tick, np.zeros(3, dtype=int), np.arange(3), np.ones(3),
                     sold+closing, closing, np.array([q, 20., 24.]), sold, exposure)
        return h

    def counts(self, h, tick=4, budget=16):
        return audit(h, decision_tick=tick, max_quote_folds=budget)['channels'][0]['sellerSupport']

    def test_support_and_disjoint_rejections(self):
        h = self.history()
        self.assertEqual(self.counts(h), dict(noEligibleObservations=0, nonpositiveSales=0,
            insufficientQuotes=2, foldBudgetExceeded=0, structurallySupported=1))
        self.assertEqual(self.counts(h, budget=2)['foldBudgetExceeded'], 1)
        self.assertEqual(self.counts(self.history(zero=True))['nonpositiveSales'], 1)
        self.assertEqual(self.counts(self.history(constrained=True))['noEligibleObservations'], 3)
        self.assertEqual(self.counts(self.history((4., 4., 8.)))['insufficientQuotes'], 3)

    def test_ties_and_future_rows(self):
        h = self.history((20., 20., 20.))
        self.assertEqual(self.counts(h)['insufficientQuotes'], 3)
        expected = audit(h, decision_tick=4, max_quote_folds=16)
        h.record('retail', 4, np.array([0,0,0,1]), np.arange(4), np.ones(4),
                 np.ones(4)*2, np.ones(4), np.ones(4), np.ones(4), np.array([[1.]*4, [1.]*4, [0.]*4]))
        self.assertEqual(audit(h, decision_tick=4, max_quote_folds=16), expected)

    def test_book_exclusions(self):
        h = self.history()
        # One changed-size book, one undiscovered offer, and one constrained
        # offer leave zero usable books. Exclusions count books, not sellers.
        state = h.channels['retail']
        state['offered'][0, 2] = 0
        state['quote'][0, 2] = np.nan
        state['sold'][0, 2] = 0
        state['discoveries'][0, 2] = 0
        state['fundedChecks'][0, 2] = 0
        state['discoveries'][1, 1] = 0
        state['fundedChecks'][1, 1] = 0
        state['sold'][1, 1] = 0
        state['shortChecks'][2, 0] = 1
        product = audit(h, decision_tick=4, max_quote_folds=16)['channels'][0]['products'][0]
        self.assertEqual(product['exclusions'], dict(changedSellerCount=1, uninformedBook=1, constrainedBook=1, emptyOpening=0))
        self.assertEqual(product['eligibleBooks'], 0)

    def test_empty_history_invalid_budget_and_missing_phase(self):
        self.assertEqual(audit(SellerHistory(3), decision_tick=1, max_quote_folds=16)['channels'], [])
        h = self.history()
        for budget in (0, -1, True, 1.5):
            with self.assertRaises(ValueError): audit(h, decision_tick=4, max_quote_folds=budget)
        with self.assertRaises(ValueError): audit(h, decision_tick=5, max_quote_folds=16)


if __name__ == '__main__': unittest.main()
