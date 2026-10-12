from dataclasses import replace
from itertools import product
import math
import random
import unittest
from tools.buying_v2.closing_values import evaluate, solve as closing_solve
from tools.buying_v2.closing_allocation import candidate
from tools.buying_v2.phase_oracle import Scenario, solve
from tools.buying_v2.phase_ledger import Company, State, Line, Offer, Purchase, OpenBook, SettleBook, apply, horizon_value


class ClosingValueTests(unittest.TestCase):
    def test_ordinary_cash_near_tie_matches_ledger_not_algebraic_reduction(self):
        company = Company((1.,), (1,), 2., (Line((1,), 1, 0., 10., 0., (0., 0.), 1.),), (1,), 0.)
        state = State(1000., (0,), (0.,), (0,), (0.,), (10.,), (-1,))
        event = Purchase('buy', (Offer(0, 0, .1, 1),), (1,), (0.,), 0., 0., (), 0.)
        path = Scenario(1., (event, OpenBook('sales'), SettleBook('sales', (0,))),
                        ((0., .10000000100001),), ((0., 0.),))
        posterior = ((1., replace(path, events=path.events[1:])),)
        reduced = candidate(company, state, state, event, posterior)
        self.assertEqual(reduced['allocation'], (1,))
        expected = solve(company, state, (path,), funding=lambda *_: (1,))
        self.assertEqual(expected['leaves'][0]['trace'][0]['allocation'], (0,))
        with self.assertRaisesRegex(AssertionError, 'differs from exhaustive phase policy'):
            solve(company, state, (path,), funding=lambda *_: (1,), audit_closing_allocation=True)
        actual = evaluate(company, state, state, event, posterior, ((0,), (1,)))
        self.assertEqual(actual[0]['value'], 0.)
        self.assertEqual(actual[1]['value'], reduced['expectedValue'])
        self.assertLess(actual[1]['value'], 1e-9)
        self.assertGreater(reduced['compiledValue'], 1e-9)
        fixed = closing_solve(company, state, state, event, posterior)
        self.assertEqual(fixed['allocation'], (0,))
        self.assertEqual(fixed['value'], expected['expectedValue'])
        integrated = solve(company, state, (path,), funding=lambda *_: (1,), closing_search='compiled-exhaustive')
        self.assertEqual(integrated['leaves'], expected['leaves'])
        with self.assertRaisesRegex(ValueError, 'node limit'):
            closing_solve(company, state, state, event, posterior, max_allocations=1)

    def test_every_basket_matches_independent_staged_ledger(self):
        rng = random.Random(173290)
        checked = 0
        for case in range(60):
            lines = tuple(Line(recipe, 2, rng.choice((.1, .3, .75)), 10., 0., (0.,)*3, float(sum(recipe)))
                          for recipe in ((1, 1), (1, 0)))
            company = Company((1., 1.), (2, 2), 8., lines, (3, 3), 0.)
            state = State(rng.choice((.3, 2., 10., 1000.)), (rng.randrange(2), rng.randrange(2)),
                (rng.choice((.1, 2., 9.)), rng.choice((.3, 3., 7.))), (0, 1), (.1, .7),
                (rng.choice((2., 10.)), rng.choice((2., 10.))), (0, 2), arrears=.3, switching_net_ema=.1)
            offers = tuple(Offer(m, 2*m+s, rng.choice((.1, .3, .7, 2.)), rng.randrange(3))
                           for m in range(2) for s in range(2))
            event = Purchase('buy', offers, tuple(2-state.held[o.material] for o in offers),
                             (.1, .3, .5, .7), .1, rng.choice((0., 1.)), (0, 1), 0.)
            posterior = tuple((weight, Scenario(weight, (OpenBook('sales'), SettleBook('sales',
                (rng.randrange(4), rng.randrange(4)), .1)),
                tuple(tuple(rng.choice((0., .1, .3)) for _ in range(3)) for _ in range(2)),
                tuple(tuple(rng.choice((0., .1, .7)) for _ in range(4)) for _ in range(2)))) for weight in (.1, .2, .7))
            allocations = tuple(product(*(range(o.stock+1) for o in offers)))
            actual = evaluate(company, state, state, event, posterior, allocations)
            paths = tuple(replace(s, events=(event,)+s.events) for _, s in posterior)
            expected_policy = solve(company, state, paths, funding=lambda *_: event.funded_demands)
            actual_policy = closing_solve(company, state, state, event, posterior)
            self.assertEqual(actual_policy['value'], expected_policy['expectedValue'])
            self.assertEqual(actual_policy['allocation'], expected_policy['leaves'][0]['trace'][0]['allocation'])
            for allocation, row in zip(allocations, actual):
                with self.subTest(case=case, allocation=allocation):
                    try:
                        bought, _ = apply(company, state, event, allocation)
                    except ValueError as exc:
                        self.assertIn(str(exc), ('infeasible procurement allocation', 'production would exceed physical storage'))
                        self.assertIsNone(row)
                        continue
                    values = []
                    for _, scenario in posterior:
                        final = bought
                        for following in scenario.events:final, _ = apply(company, final, following)
                        values.append(horizon_value(state, final, scenario.input_values, scenario.finished_values))
                    self.assertEqual(row['scenarioValues'], tuple(values))
                    self.assertEqual(row['value'], math.fsum(w*v for (w, _), v in zip(posterior, values)))
                    checked += 1
        self.assertGreater(checked, 200)

    def test_integrated_endogenous_funding_and_general_calendar_fallback(self):
        from tools.buying_v2.benchmark_phase_search import case
        for funding in ('continuation', 'continuation-transfer-neutral'):
            for supply in ('independent-snapshots', 'persistent-arrivals'):
                args = case(2, 2, 2, 2)
                common = dict(funding=funding, supply=supply, allocation_search='feasible-prefix', funding_memo_size=4096)
                baseline = solve(*args, **common)
                compiled = solve(*args, **common, closing_search='compiled-exhaustive')
                work = ('enumeratedNodes', 'prefixSearch', 'transitionCache', 'closingSolver')
                self.assertEqual({k:v for k,v in baseline.items() if k not in work},
                                 {k:v for k,v in compiled.items() if k not in work})
                self.assertGreater(compiled['closingSolver']['solves'], 0)
                self.assertGreater(compiled['closingSolver']['unsupported'], 0)
        with self.assertRaisesRegex(ValueError, 'node limit'):
            solve(*case(2, 2, 1, 1), funding='continuation', closing_search='compiled-exhaustive', max_nodes=1)


if __name__ == '__main__':unittest.main()
