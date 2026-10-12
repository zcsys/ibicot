from dataclasses import replace
from itertools import product
import math
import unittest
from tools.buying_v2.closing_cost_bound import bounder
from tools.buying_v2.closing_cost_compiled import bounder as fast_bounder
from tools.buying_v2.closing_boxes import solve as boxed, upper_value
from tools.buying_v2.closing_values import solve as exhaustive
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.benchmark_phase_search import case, frozen_funding
from tools.buying_v2.phase_oracle import Scenario, solve
from tools.buying_v2.phase_ledger import Company, State, Line, Offer, Purchase, OpenBook, SettleBook, apply, horizon_value


class ClosingCostBoundTests(unittest.TestCase):
    def test_complete_box_bound_includes_required_inputs_and_conversion(self):
        company, state, paths = case(4, 2, 1, 1)
        event = replace(paths[0].events[0], funded_demands=(4,)*4)
        posterior = ((1., replace(paths[0], events=paths[0].events[1:])),)
        problem = prepare(company, state, state, event, posterior)
        gross = upper_value(problem, state, state, posterior, (0,)*4, (4,)*4)
        costs = bounder(problem, state, state, posterior)((0,)*4, (4,)*4)
        self.assertGreaterEqual(costs, 22.)
        self.assertLess(costs, 22.+1e-9)
        self.assertGreater(gross, 39.)

    def test_lots_yields_owned_basis_and_terminal_buffers_against_ledger(self):
        line = Line((2, 1), 2, .1, 10., 0., (0.,)*7, 3., output_qty=3)
        company = Company((1., 1.), (5, 3), 12., (line,), (6,), 0.)
        offers = (Offer(0, 0, .1, 2, 2), Offer(0, 1, .3, 2, 2), Offer(1, 2, .2, 3))
        event = Purchase('buy', offers, (4, 4, 3), (0.,)*3, 0., 0., (0,), 0.)
        path = Scenario(1., (OpenBook('sales'), SettleBook('sales', (4,), .1)),
                        ((0., .1, .7, .2, .8, .4), (0., .5, .1, .3)), ((0., .1, .3, .2, .7, .2, .4),))
        for basis in (.1, 100.):
            state = State(10., (1, 0), (basis, 0.), (0,), (0.,), (10.,), (-1, -1))
            posterior = ((1., path),)
            problem = prepare(company, state, state, event, posterior)
            bound = bounder(problem, state, state, posterior)
            fast = fast_bounder(problem, state, state, posterior)
            for lo in product((0, 2), (0, 2), range(4)):
                hi = (2, 2, 3)
                top = bound(lo, hi)
                self.assertGreaterEqual(fast(lo, hi), top)
                for allocation in product(range(lo[0], 3, 2), range(lo[1], 3, 2), range(lo[2], 4)):
                    try:final, _ = apply(company, state, event, allocation)
                    except ValueError as exc:
                        self.assertIn(str(exc), ('infeasible procurement allocation', 'production would exceed physical storage'))
                        continue
                    for following in path.events:final, _ = apply(company, final, following)
                    self.assertGreaterEqual(top, horizon_value(state, final, path.input_values, path.finished_values))
            actual = boxed(company, state, state, event, posterior, include_costs=True)
            expected = exhaustive(company, state, state, event, posterior)
            self.assertEqual(actual['allocation'], expected['allocation'])
            self.assertEqual(actual['value'], expected['value'])
            compiled = boxed(company, state, state, event, posterior, include_costs=True, compiled_costs=True)
            self.assertEqual(compiled['allocation'], expected['allocation'])
            self.assertEqual(compiled['value'], expected['value'])

    def test_scaled_money_and_full_funding_policy_parity(self):
        work = ('enumeratedNodes', 'prefixSearch', 'transitionCache', 'closingSolver')
        for scale in (1e-8, 1., 1e8):
            company, state, paths = case(2, 2, 1, 2)
            company = replace(company, lines=tuple(replace(line, conversion=line.conversion*scale, quote=line.quote*scale) for line in company.lines))
            state = replace(state, cash=state.cash*scale, quotes=tuple(q*scale for q in state.quotes))
            paths = tuple(replace(p, events=(replace(p.events[0], offers=tuple(replace(o, price=o.price*scale) for o in p.events[0].offers)),)+p.events[1:]) for p in paths)
            expected = solve(company, state, paths, funding='continuation')
            actual = solve(company, state, paths, funding='continuation', closing_search='compiled-cost-boxes')
            self.assertEqual({k:v for k,v in actual.items() if k not in work}, {k:v for k,v in expected.items() if k not in work})
        for funding in ('continuation', 'continuation-transfer-neutral'):
            for supply in ('independent-snapshots', 'persistent-arrivals'):
                args = case(2, 2, 2, 2)
                options = dict(funding=funding, supply=supply, funding_memo_size=4096, allocation_search='feasible-prefix')
                expected = solve(*args, **options)
                actual = solve(*args, **options, closing_search='compiled-cost-boxes')
                self.assertEqual({k:v for k,v in actual.items() if k not in work}, {k:v for k,v in expected.items() if k not in work})


if __name__ == '__main__':unittest.main()
