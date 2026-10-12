from dataclasses import replace
from itertools import product
import unittest
from tools.buying_v2.closing_allocation import prepare
from tools.buying_v2.closing_cost_bound import bounder
from tools.buying_v2.closing_cost_compiled import bounder as fast_bounder
from tools.buying_v2.benchmark_phase_search import case, frozen_funding
from tools.buying_v2.phase_oracle import solve


class CompiledClosingCostTests(unittest.TestCase):
    def test_bound_dominates_rational_at_money_and_overflow_boundaries(self):
        for price in (5e-324, 1e-8, .1, 1e8, 1e308):
            company, state, paths = case(2, 2, 1, 2)
            event = replace(paths[0].events[0], funded_demands=(2,)*4,
                offers=tuple(replace(o, price=price) for o in paths[0].events[0].offers))
            posterior = tuple((s.probability, replace(s, events=s.events[1:])) for s in paths)
            problem = prepare(company, state, state, event, posterior)
            slow = bounder(problem, state, state, posterior)
            fast = fast_bounder(problem, state, state, posterior)
            for lo in product(range(3), repeat=4):
                with self.subTest(price=price, lo=lo):
                    self.assertGreaterEqual(fast(lo, (2,)*4), slow(lo, (2,)*4))

    def test_full_policies_under_funding_supply_and_money_scales(self):
        work = ('enumeratedNodes', 'prefixSearch', 'transitionCache', 'closingSolver')
        for funding in ('continuation', 'continuation-transfer-neutral'):
            for supply in ('independent-snapshots', 'persistent-arrivals'):
                args = case(2, 2, 2, 2)
                options = dict(funding=funding, supply=supply, allocation_search='feasible-prefix', funding_memo_size=4096)
                expected = solve(*args, **options, closing_search='compiled-cost-boxes')
                actual = solve(*args, **options, closing_search='compiled-fast-cost-boxes')
                self.assertEqual({k:v for k,v in actual.items() if k not in work}, {k:v for k,v in expected.items() if k not in work})
        for scale in (1e-8, 1., 1e8):
            company, state, paths = case(2, 2, 1, 2)
            company = replace(company, lines=tuple(replace(line, conversion=line.conversion*scale, quote=line.quote*scale) for line in company.lines))
            state = replace(state, cash=state.cash*scale, quotes=tuple(q*scale for q in state.quotes))
            paths = tuple(replace(s, events=(replace(s.events[0], offers=tuple(replace(o, price=o.price*scale) for o in s.events[0].offers)),)+s.events[1:]) for s in paths)
            expected = solve(company, state, paths, funding='continuation')
            actual = solve(company, state, paths, funding='continuation', closing_search='compiled-fast-cost-boxes')
            self.assertEqual({k:v for k,v in actual.items() if k not in work}, {k:v for k,v in expected.items() if k not in work})


if __name__ == '__main__':unittest.main()
