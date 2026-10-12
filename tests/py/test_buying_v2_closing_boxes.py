from dataclasses import replace
from itertools import product
import math
import random
import unittest
from tools.buying_v2.closing_boxes import solve as boxed, upper_value
from tools.buying_v2.closing_values import solve as exhaustive, evaluate, evaluator
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.closing_cost_bound import bounder
from tools.buying_v2.closing_cost_compiled import bounder as fast_bounder
from tools.buying_v2.phase_oracle import Scenario
from tools.buying_v2.phase_ledger import Company, State, Line, Offer, Purchase, OpenBook, SettleBook, apply, horizon_value


class ClosingBoxTests(unittest.TestCase):
    def test_bounds_and_selected_policy_against_every_staged_basket(self):
        rng = random.Random(413297)
        for case in range(40):
            lines = tuple(Line(recipe, 1, .1, 5., 0., (0., 0.), float(sum(recipe)))
                          for recipe in ((1, 1, 1), (1, 0, 0), (0, 1, 0)))
            company = Company((1.,)*3, (1,)*3, 6., lines, (1,)*3, 0.)
            state = State(rng.choice((.3, 2., 10., 1000.)), (0,)*3, (0.,)*3, (0,)*3, (0.,)*3, (5.,)*3, (0, 2, 4))
            offers = tuple(Offer(m, 2*m+s, rng.choice((.1, .3, 1.1)), rng.randrange(2)) for m in range(3) for s in range(2))
            event = Purchase('buy', offers, (1,)*6, (.1, .2, .3, .4, .5, .6), .1, 1., (0, 1, 2), 0.)
            posterior = tuple((w, Scenario(w, (OpenBook('sales'), SettleBook('sales', tuple(rng.randrange(2) for _ in lines), .1)),
                tuple(tuple(rng.choice((-.3, 0., .1)) for _ in range(2)) for _ in range(3)),
                tuple(tuple(rng.choice((-.3, 0., .7)) for _ in range(2)) for _ in range(3)))) for w in (.1, .2, .7))
            problem = prepare(company, state, state, event, posterior)
            run = evaluator(company, state, state, event, posterior)
            costs = bounder(problem, state, state, posterior)
            fast_costs = fast_bounder(problem, state, state, posterior)
            expected = exhaustive(company, state, state, event, posterior)
            actual = boxed(company, state, state, event, posterior)
            costed = boxed(company, state, state, event, posterior, include_costs=True)
            self.assertEqual({k:actual[k] for k in expected if k != 'enumeratedAllocations'},
                             {k:v for k,v in expected.items() if k != 'enumeratedAllocations'})
            self.assertEqual(actual['enumeratedAllocations']+actual['skippedAllocations'], actual['cartesianAllocations'])
            self.assertEqual({k:costed[k] for k in expected if k != 'enumeratedAllocations'},
                             {k:v for k,v in expected.items() if k != 'enumeratedAllocations'})
            for repeat in range(3):
                lo = tuple(rng.randrange(o.stock+1) for o in offers)
                hi = tuple(rng.randrange(a, o.stock+1) for a, o in zip(lo, offers))
                bound = upper_value(problem, state, state, posterior, lo, hi)
                cost_bound = costs(lo, hi)
                fast_cost_bound = fast_costs(lo, hi)
                self.assertGreaterEqual(fast_cost_bound, cost_bound)
                for allocation in product(*(range(a, b+1) for a, b in zip(lo, hi))):
                    try:bought, _ = apply(company, state, event, allocation)
                    except ValueError as exc:
                        self.assertIn(str(exc), ('infeasible procurement allocation', 'production would exceed physical storage'))
                        continue
                    values = [];scenario_values = []
                    for weight, scenario in posterior:
                        final = bought
                        for following in scenario.events:final, _ = apply(company, final, following)
                        payoff = horizon_value(state, final, scenario.input_values, scenario.finished_values)
                        scenario_values.append(payoff);values.append(weight*payoff)
                    with self.subTest(case=case, repeat=repeat, allocation=allocation):
                        self.assertEqual(run((allocation,))[0]['scenarioValues'], tuple(scenario_values))
                        self.assertGreaterEqual(bound, math.fsum(values))
                        self.assertGreaterEqual(cost_bound, math.fsum(values))
                        self.assertGreaterEqual(fast_cost_bound, math.fsum(values))

    def test_three_line_sales_use_reference_compensated_sum(self):
        lines = (Line((1,), 0, 0., 1., 0., (0.,), 1.),)*3
        company = Company((1.,), (1,), 4., lines, (1,)*3, 0.)
        state = State(1., (0,), (0.,), (1,)*3, (0.,)*3, (1e16, 1., 1.), (-1,))
        event = Purchase('buy', (), (), (), 0., 0., (), 0.)
        scenario = Scenario(1., (OpenBook('sales'), SettleBook('sales', (1,)*3)), ((0., 0.),), ((0., 0.),)*3)
        final, _ = apply(company, state, event, ())
        for following in scenario.events:final, _ = apply(company, final, following)
        row = evaluate(company, state, state, event, ((1., scenario),), ((),))[0]
        self.assertEqual(row['value'], horizon_value(state, final, scenario.input_values, scenario.finished_values))
        self.assertEqual(row['value'], 1.0000000000000004e16)

    def test_near_tie_order_and_explicit_budgets(self):
        company = Company((1.,), (1,), 2., (Line((1,), 0, 0., 1., 0., (0.,), 1.),), (1,), 0.)
        state = State(1000., (0,), (0.,), (0,), (0.,), (1.,), (-1,))
        event = Purchase('buy', (Offer(0, 0, .1, 1),), (1,), (0.,), 0., 0., (), 0.)
        scenario = Scenario(1., (OpenBook('sales'), SettleBook('sales', (0,))), ((0., .10000000100001),), ((0., 0.),))
        result = boxed(company, state, state, event, ((1., scenario),))
        self.assertEqual(result['allocation'], (0,))
        self.assertEqual(boxed(company, state, state, event, ((1., scenario),), include_costs=True)['allocation'], (0,))
        for limits in (dict(max_boxes=1), dict(max_allocations=1)):
            with self.assertRaisesRegex(ValueError, 'node limit'):
                boxed(company, state, state, event, ((1., scenario),), **limits)

    def test_integrated_policies_under_both_funding_and_supply_modes(self):
        from tools.buying_v2.phase_oracle import solve
        from tools.buying_v2.benchmark_phase_search import case
        for funding in ('continuation', 'continuation-transfer-neutral'):
            for supply in ('independent-snapshots', 'persistent-arrivals'):
                args = case(2, 2, 2, 2)
                options = dict(funding=funding, supply=supply, allocation_search='feasible-prefix', funding_memo_size=4096)
                expected = solve(*args, **options)
                actual = solve(*args, **options, closing_search='compiled-boxes')
                work = ('enumeratedNodes', 'prefixSearch', 'transitionCache', 'closingSolver')
                self.assertEqual({k:v for k,v in actual.items() if k not in work},
                                 {k:v for k,v in expected.items() if k not in work})
                self.assertGreater(actual['closingSolver']['skippedAllocations'], 0)
                self.assertLess(actual['enumeratedNodes'], expected['enumeratedNodes'])

    def test_boxes_and_outer_prefixes_share_one_branch_budget(self):
        from tools.buying_v2.phase_oracle import solve
        from tools.buying_v2.benchmark_phase_search import case
        args = case(1, 1, 2, 2)
        options = dict(funding='continuation', allocation_search='feasible-prefix', closing_search='compiled-boxes')
        result = solve(*args, **options)
        required = result['prefixSearch']['visitedPrefixes']+result['closingSolver']['boxes']
        self.assertEqual(solve(*args, **options, max_prefix_nodes=required)['leaves'], result['leaves'])
        with self.assertRaisesRegex(ValueError, 'node limit'):
            solve(*args, **options, max_prefix_nodes=required-1)


if __name__ == '__main__':unittest.main()
