"""Enumerate every allocation independently of the prefix solver."""
import itertools
import unittest
import numpy as np
from tools.buying_v2.retail import solve_retail


def exhaustive(values, prices, stock, ids, incumbent, bid, fee, cash):
    inc_stock = sum(s for s, i in zip(stock, ids) if i == incumbent)
    payable = fee if incumbent >= 0 and bid > 0 and inc_stock >= bid else 0
    best = 0.
    winners = []
    for allocation in itertools.product(*(range(min(int(s), len(values)) + 1) for s in stock)):
        units = sum(allocation)
        if units > len(values):
            continue
        goods = sum(q * p for q, p in zip(allocation, prices))
        charge = payable if any(q and i != incumbent for q, i in zip(allocation, ids)) else 0
        if goods + charge > cash:
            continue
        objective = sum(values[:units]) - goods - charge
        if objective > best:
            best, winners = objective, [allocation]
        elif objective == best:
            winners.append(allocation)
    return best, winners


class RetailSolverTests(unittest.TestCase):
    def test_random_markets_against_all_allocations(self):
        rng = np.random.default_rng(719032)
        for _ in range(600):
            n = int(rng.integers(1, 5))
            ids = rng.permutation(np.arange(n, dtype=np.int64))
            prices = rng.integers(1, 15, n).astype(float)
            stock = rng.integers(0, 5, n).astype(np.int64)
            values = np.sort(rng.integers(1, 21, int(rng.integers(1, 7))))[::-1].astype(float)
            incumbent = int(rng.integers(-1, n))
            bid = int(rng.integers(0, 7))
            fee = float(rng.integers(0, 16))
            cash = float(rng.integers(0, 80))
            demands = np.array([min(int(np.count_nonzero(values > p)), int(cash // p)) for p in prices])
            expected, allocations = exhaustive(values, prices, stock, ids, incumbent, bid, fee, cash)
            args = values, prices, stock, ids, incumbent, bid, fee, cash, demands
            actual = solve_retail(*args)
            slow = solve_retail.py_func(*args)
            self.assertEqual(actual[1], expected)
            self.assertIn(tuple(actual[0]), allocations)
            np.testing.assert_array_equal(actual[0], slow[0])
            self.assertEqual(actual[1:], slow[1:])

    def test_whole_demand_qualification_retains_split_incumbent(self):
        # Ten values justify $10; eight justify $15. Incumbent can fill its bid.
        values = np.array([20.] * 8 + [12.] * 2)
        args = (values, np.array([18., 10., 15.]), np.array([10, 2, 20]),
                np.array([0, 1, 2]), 0, 8, 2., 1000., np.array([8, 10, 8]))
        result = solve_retail(*args)
        np.testing.assert_array_equal(result[0], [0, 2, 6])
        self.assertEqual(result[3], 2.)
        self.assertEqual(result[4], 0)

    def test_fee_can_make_incumbent_only_better_than_cheapest_goods(self):
        result = solve_retail(np.array([20., 20.]), np.array([10., 9.]),
                              np.array([2, 2]), np.array([0, 1]), 0, 2, 4.,
                              100., np.array([2, 2]))
        np.testing.assert_array_equal(result[0], [2, 0])
        self.assertEqual(result[3], 0)


if __name__ == '__main__':
    unittest.main()
