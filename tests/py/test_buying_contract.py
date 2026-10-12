"""Independent expectations for the unresolved purchasing contract choices."""
import unittest
from tools.buying_v2.contract_cases import Delivery, preference_after, order_fee


class ContractAlternativesTests(unittest.TestCase):
    def test_split_completion_is_the_decision_not_the_quantity(self):
        legs = (Delivery(1, 10, 2), Delivery(2, 8, 6))
        self.assertEqual(preference_after(0, legs, 'remaining'), 2)
        self.assertEqual(preference_after(0, legs, 'whole'), 0)
        self.assertEqual(preference_after(-1, legs, 'remaining'), 2)
        self.assertEqual(preference_after(-1, legs, 'whole'), -1)

    def test_partial_purchase_alone_never_replaces(self):
        for rule in ('remaining', 'whole'):
            self.assertEqual(preference_after(0, (Delivery(1, 10, 2),), rule), 0)
            self.assertEqual(preference_after(0, (Delivery(1, 8, 8),), rule), 1)
            self.assertEqual(preference_after(0, (Delivery(1, 0, 0),), rule), 0)

    def test_four_loyalty_table_cases_are_independent(self):
        for delivered in (2, 8):
            for stock in (7, 8, 9):
                legs = (Delivery(1, 8, delivered),)
                self.assertEqual(order_fee(0, stock, 8, 2., legs), 2. if stock >= 8 else 0.)
                self.assertEqual(preference_after(0, legs, 'whole'), 1 if delivered == 8 else 0)

    def test_fee_is_once_even_if_incumbent_sells_first(self):
        legs = (Delivery(0, 10, 2), Delivery(1, 8, 1), Delivery(2, 5, 2))
        self.assertEqual(order_fee(0, 10, 10, 3., legs), 3.)
        self.assertEqual(order_fee(0, 10, 10, 3., (Delivery(0, 10, 10),)), 0.)

    def test_no_incumbent_or_no_goods_means_no_fee(self):
        self.assertEqual(order_fee(-1, 8, 8, 2., (Delivery(1, 8, 8),)), 0.)
        self.assertEqual(order_fee(0, 8, 8, 2., (Delivery(1, 8, 0),)), 0.)
        self.assertEqual(order_fee(0, 8, 0, 2., (Delivery(1, 0, 0),)), 0.)

    def test_invalid_fallback_cannot_become_a_qualification(self):
        with self.assertRaises(ValueError):
            preference_after(0, (Delivery(1, 10, 2), Delivery(2, 8, 8)), 'remaining')
        with self.assertRaises(ValueError):
            preference_after(0, (Delivery(1, 8, 8), Delivery(2, 8, 1)), 'whole')


if __name__ == '__main__':
    unittest.main()
