import unittest
from tools.buying_v2.industry_oracle import Problem, Offer, Line, solve, evaluate


def fixture(held, offers, lines, slots=None, basis=None, cash=100., terminal=None,
            incumbents=None, bids=None, fees=None, free_space=100.):
    n = len(held)
    slots = tuple(slots or [4] * n)
    return Problem(tuple(held), tuple(basis or [0.] * n), (1.,) * n, slots,
                   free_space, cash, tuple(offers), tuple(incumbents or [-1] * n),
                   tuple(bids or [0] * n), tuple(fees or [0.] * n), tuple(lines),
                   tuple(terminal or [tuple(0. for _ in range(s + 1)) for s in slots]))


class IndustrialOracleTests(unittest.TestCase):
    def test_cheaper_partial_and_fallback_both_bought(self):
        p = fixture([0], [Offer(0, 1, 1., 2), Offer(0, 2, 3., 8)],
                    [Line((1,), 8, 1., 20., 0., tuple(20. * q for q in range(9)), 1.)], slots=[8])
        result = solve(p)
        self.assertEqual(result['allocation'], (2, 6))
        self.assertEqual(result['outputs'], (8,))
        self.assertEqual(result['goods'], 20.)

    def test_owned_historical_cost_gate_blocks_false_profit(self):
        p = fixture([1, 0], [Offer(1, 1, 1., 1)],
                    [Line((1, 1), 1, .75, 10., 0., (0., 10.), 2.)], basis=[100., 0.])
        chosen = solve(p)
        self.assertEqual(chosen['allocation'], (0,))
        self.assertEqual(chosen['outputs'], (0,))
        self.assertEqual(evaluate(p, (1,))['outputs'], (0,))
        self.assertEqual(evaluate(p, (1,))['value'], -1.)

    def test_two_lines_compete_for_shared_input_and_cash(self):
        p = fixture([0], [Offer(0, 1, 2., 4)],
                    [Line((2,), 1, 1., 20., 0., (0., 20.), 2.),
                     Line((1,), 2, 1., 10., 0., (0., 10., 20.), 1.)], cash=11.)
        result = solve(p)
        self.assertEqual(result['allocation'], (4,))
        self.assertEqual(result['outputs'], (1, 2))
        self.assertEqual(result['cash'], 0.)

    def test_useful_unmatched_buffer_is_in_action_space(self):
        p = fixture([0, 0], [Offer(0, 1, 1., 2)],
                    [Line((1, 1), 2, 1., 20., 0., (0., 20., 40.), 2.)],
                    terminal=[(0., 3., 5., 5., 5.), (0., 0., 0., 0., 0.)])
        result = solve(p)
        self.assertEqual(result['allocation'], (2,))
        self.assertEqual(result['outputs'], (0,))
        self.assertEqual(result['value'], 3.)

    def test_lots_storage_and_one_fee_per_material(self):
        p = fixture([0], [Offer(0, 0, 10., 8, 2), Offer(0, 1, 1., 2, 2), Offer(0, 2, 2., 4, 2)],
                    [Line((1,), 8, 1., 30., 0., tuple(30. * q for q in range(9)), 1.)],
                    slots=[8], free_space=6., incumbents=[0], bids=[6], fees=[3.])
        result = solve(p)
        self.assertEqual(result['allocation'], (0, 2, 4))
        self.assertEqual(result['fees'], (3.,))
        self.assertEqual(result['outputs'], (6,))
        self.assertIsNone(evaluate(p, (0, 1, 4)))
        self.assertIsNone(evaluate(p, (2, 2, 4)))


class CompiledIndustrialTests(unittest.TestCase):
    def test_split_purchases_use_material_total_for_storage(self):
        from dataclasses import replace
        from tools.buying_v2.industry import solve as compiled
        from tools.buying_v2.industry_search import solve as searched
        p = fixture((0,), [Offer(0, s, 1., 3) for s in range(3)], (),
                    slots=(9,), terminal=(tuple(2.*q for q in range(10)),), free_space=.9)
        p = replace(p, spaces=(.1,))
        expected = solve(p)
        self.assertEqual(expected['allocation'], (3, 3, 3))
        for actual in (compiled(p), searched(p)[0]):
            self.assertEqual(tuple(actual[0]), expected['allocation'])
            self.assertEqual(actual[3], expected['value'])

    def test_space_conserving_production_at_exact_storage_boundary(self):
        from dataclasses import replace
        from tools.buying_v2.industry import solve as compiled
        from tools.buying_v2.industry_search import solve as searched
        p = fixture((0, 0, 0), [Offer(m, m, 1., 1) for m in range(3)],
            [Line((1, 1, 0), 1, .5, 10., 0., (0., 10.), .2)], slots=(1, 1, 1),
            terminal=((0., 0.), (0., 0.), (0., 20.)), free_space=100000000.3)
        p = replace(p, spaces=(.1, .1, 100000000.1))
        expected = solve(p)
        self.assertEqual(expected['allocation'], (1, 1, 1))
        self.assertEqual(expected['outputs'], (1,))
        for actual in (compiled(p), searched(p)[0]):
            self.assertEqual(tuple(actual[0]), expected['allocation'])
            self.assertEqual(tuple(actual[1]), expected['outputs'])
            self.assertEqual(actual[3], expected['value'])

    def test_random_multiline_split_markets_against_independent_oracle(self):
        import numpy as np
        from tools.buying_v2.industry import solve as compiled
        rng = np.random.default_rng(280417)
        for _ in range(160):
            held = rng.integers(0, 2, 2).tolist()
            slots = [3, 3]
            offers = [Offer(m, supplier, float(rng.integers(1, 8)), int(rng.integers(0, 4)))
                      for m in range(2) for supplier in range(2)]
            lines = [Line(recipe, 2, float(rng.integers(0, 3)), float(rng.integers(5, 31)),
                          float(rng.integers(0, 3)), tuple(float(v) * q for q in range(3)), float(sum(recipe)))
                     for recipe, v in [((1, 1), rng.integers(4, 30)), ((2, 0), rng.integers(4, 30))]]
            p = fixture(held, offers, lines, slots=slots, basis=rng.integers(0, 15, 2).tolist(),
                        cash=float(rng.integers(1, 35)), free_space=float(rng.integers(1, 7)),
                        terminal=[tuple(float(rng.integers(0, 3)) * q for q in range(4)) for m in range(2)],
                        incumbents=[0, 0], bids=[2, 2], fees=[2., 3.])
            expected, actual = solve(p), compiled(p)
            from tools.buying_v2.industry_bounds import solve as bounded
            pruned, certificate = bounded(p)
            np.testing.assert_array_equal(pruned[0], expected['allocation'])
            self.assertEqual(pruned[3], expected['value'])
            self.assertGreater(certificate['nodes'], 0)
            from tools.buying_v2.industry_search import solve as compiled_search
            searched, certificate = compiled_search(p)
            np.testing.assert_array_equal(searched[0], expected['allocation'])
            self.assertEqual(searched[3], expected['value'])
            np.testing.assert_array_equal(actual[0], expected['allocation'])
            np.testing.assert_array_equal(actual[1], expected['outputs'])
            np.testing.assert_array_equal(actual[2], expected['remaining'])
            self.assertAlmostEqual(actual[3], expected['value'])
            self.assertEqual(actual[4], expected['goods'] + sum(expected['fees']))
            self.assertEqual(actual[5], expected['conversion'])


class IndustrialBoundsSafetyTests(unittest.TestCase):
    def test_limit_is_not_an_optimal_result(self):
        from tools.buying_v2.industry_search import solve as search
        from tools.buying_v2.industry_bounds import SearchLimit
        p = fixture([0], [Offer(0, 1, 1., 2)], [Line((1,), 2, 1., 10., 0., (0., 10., 20.), 1.)])
        with self.assertRaises(SearchLimit):
            search(p, max_nodes=0)

    def test_nonfinite_values_and_fractional_recipe_are_rejected(self):
        from dataclasses import replace
        from tools.buying_v2.industry_search import solve as search
        p = fixture([0], [Offer(0, 1, 1., 2)], [Line((1,), 2, 1., 10., 0., (0., 10., 20.), 1.)])
        for bad in (replace(p, cash=float('nan')),
                    replace(p, lines=(replace(p.lines[0], recipe=(1.5,)),)),
                    replace(p, terminal_values=((0., float('inf'), 0., 0., 0.),))):
            with self.assertRaises(ValueError):
                search(bad)


class IndustrialUpperBoundTests(unittest.TestCase):
    def test_bound_dominates_all_feasible_allocations_in_random_boxes(self):
        import itertools
        import numpy as np
        from tools.buying_v2.industry import pack
        from tools.buying_v2.industry_search import upper_bound, solve as search
        rng = np.random.default_rng(81703)
        for index in range(80):
            if index % 2:
                increments = np.sort(rng.integers(-3, 16, 8))[::-1]
                values = tuple(np.concatenate(([0], np.cumsum(increments))).astype(float))
            else:
                values = tuple(rng.integers(-10, 90, 9).astype(float))
            p = fixture([0], [Offer(0, 0, 2., 8), Offer(0, 1, 3., 8)],
                        [Line((1,), 8, 1., 30., 0., values, 1.)], slots=[8],
                        terminal=[tuple(rng.integers(0, 5, 9).astype(float))])
            args = pack(p)
            lo = rng.integers(0, 4, 2)
            hi = lo + rng.integers(0, 5, 2)
            concave = np.array([np.all(np.diff(values, n=2) <= 0)])
            ub = upper_bound(args, lo, hi, np.maximum.accumulate(args[21], axis=1),
                             np.maximum.accumulate(args[22], axis=1), concave)
            for q in itertools.product(*(range(int(a), int(b)+1) for a, b in zip(lo, hi))):
                result = evaluate(p, q)
                if result is not None:
                    self.assertGreaterEqual(ub, result['value'])
            exhaustive = solve(p)
            actual, stats = search(p)
            self.assertEqual(actual[3], exhaustive['value'])
            np.testing.assert_array_equal(actual[0], exhaustive['allocation'])


class IndustrialRelaxationTests(unittest.TestCase):
    def test_infeasible_postproduction_storage_cannot_certify(self):
        from tools.buying_v2.industry_search import solve as optimized
        p = fixture([0], [Offer(0, 0, 1., 1)],
                    [Line((1,), 1, 1., 20., 0., (0.,20.), 10.)], slots=[1], free_space=1.)
        result, stats = optimized(p)
        self.assertEqual(tuple(result[0]), (0,))
        self.assertEqual(result[3], 0.)
        self.assertGreater(stats['nodes'], 0)

    def test_price_ties_lots_and_gate_against_independent_oracle(self):
        import numpy as np
        from tools.buying_v2.industry_search import solve as optimized
        rng = np.random.default_rng(211039)
        certified = fallback = 0
        for _ in range(400):
            lot = int(rng.integers(1, 3))
            prices = [float(rng.integers(50, 600))/100 for m in range(2)]
            offers = [Offer(m, s, prices[m] if s else prices[m]+.01,
                            int(rng.integers(0, 5)), lot) for m in range(2) for s in range(2)]
            quote = float(rng.integers(500, 3000))/100
            line = Line((1, 2), 3, .75, quote, 0., tuple(quote*q for q in range(4)), 3.)
            p = fixture(rng.integers(0, 2, 2).tolist(), offers, [line], slots=[5, 5],
                        cash=float(rng.integers(1, 45)), basis=rng.integers(0, 20, 2).tolist(),
                        incumbents=[0, 0], bids=[2, 2], fees=[0., 0.])
            expected = solve(p)
            actual, stats = optimized(p)
            np.testing.assert_array_equal(actual[0], expected['allocation'])
            np.testing.assert_array_equal(actual[1], expected['outputs'])
            self.assertAlmostEqual(actual[3], expected['value'], places=8)
            if stats['nodes'] == 0:
                certified += 1
            else:
                fallback += 1
        self.assertGreater(certified, 0)
        self.assertGreater(fallback, 0)


if __name__ == '__main__':
    unittest.main()
