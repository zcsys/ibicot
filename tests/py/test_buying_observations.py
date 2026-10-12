import unittest
import numpy as np
from tools.buying_v2.observations import record_order, empty_totals, FIELDS


class ObservationTests(unittest.TestCase):
    def reduce(self, demands, delivered, old=0, new=0, fee=0.):
        rows = []
        for fn in (record_order, record_order.py_func):
            totals = empty_totals(2)
            q = np.array(demands, dtype=np.int64)
            x = np.array(delivered, dtype=np.int64)
            q_before, x_before = q.copy(), x.copy()
            fn(totals, 1, len(q), q, x, len(q), old, new, fee)
            np.testing.assert_array_equal(totals[0], 0)
            np.testing.assert_array_equal(q, q_before)
            np.testing.assert_array_equal(x, x_before)
            rows.append(totals)
        np.testing.assert_array_equal(*rows)
        return dict(zip(FIELDS, rows[0][1]))

    def test_terminal_zero_remaining_is_not_three_missing_units(self):
        row = self.reduce([10, 8, 5], [2, 3, 0])
        self.assertEqual(row['initialQuoteQuantity'], 10)
        self.assertEqual(row['terminalQuoteQuantity'], 5)
        self.assertEqual(row['remainingRequests'], 16)
        self.assertEqual(row['unitsBought'], 5)
        self.assertEqual(row['terminalShortfall'], 0)

    def test_split_fill_does_not_duplicate_product_intention(self):
        row = self.reduce([10, 8], [2, 6], old=-1, new=2)
        self.assertEqual(row['orders'], 1)
        self.assertEqual(row['unitsBought'], 8)
        self.assertEqual(row['initialQuoteQuantity'], 10)
        self.assertEqual(row['remainingRequests'], 16)
        self.assertEqual(row['firstAssignments'], 1)
        self.assertEqual(row['preferenceChanges'], 0)

    def test_fee_and_preference_events_are_independent(self):
        partial = self.reduce([10], [2], fee=3.)
        self.assertEqual(partial['feeOrders'], 1)
        self.assertEqual(partial['feeAmount'], 3)
        self.assertEqual(partial['preferenceChanges'], 0)
        switched = self.reduce([8], [8], new=2)
        self.assertEqual(switched['preferenceChanges'], 1)
        self.assertEqual(switched['feeOrders'], 0)

    def test_no_history_and_stock_empty_differ(self):
        none = self.reduce([], [])
        self.assertEqual(none['requestLegs'], 0)
        self.assertEqual(none['initialQuoteQuantity'], 0)
        empty = self.reduce([10, 8], [0, 0])
        self.assertEqual(empty['terminalShortfall'], 8)
        self.assertEqual(empty['unitsBought'], 0)
        self.assertEqual(empty['feeOrders'], 0)


if __name__ == '__main__':
    unittest.main()
