import random
import unittest
from dataclasses import replace
from tools.buying_v2.closing_allocation import candidate, prepare
from tools.buying_v2.industry_oracle import Line, Offer
from tools.buying_v2.phase_ledger import Company, State, Purchase, OpenBook, SettleBook, EndTick, SharedSettleBook
from tools.buying_v2.phase_oracle import Scenario, solve
from tools.buying_v2.benchmark_phase_search import case, frozen_funding


class ClosingAllocationTests(unittest.TestCase):
    def compare(self, company, state, event, scenarios):
        posterior = tuple((s.probability, replace(s, events=s.events[1:])) for s in scenarios)
        actual = candidate(company, state, state, event, posterior)
        expected = solve(company, state, scenarios, funding=lambda *_: event.funded_demands)
        self.assertIsNotNone(actual)
        self.assertEqual(actual['allocation'], expected['leaves'][0]['trace'][0]['allocation'])
        self.assertAlmostEqual(actual['expectedValue'], expected['expectedValue'], places=8)
        for left, right in zip(actual['leaves'], expected['leaves']):
            self.assertEqual(left['state'], right['state'])
            self.assertEqual(left['value'], right['value'])
            for a, b in zip(left['trace'], right['trace']):
                for key, value in a.items():
                    self.assertEqual(value, b[key], key)
        return actual

    def test_random_shared_inputs_fees_basis_lots_and_correlated_terminal_values(self):
        rng = random.Random(702931)
        for index in range(160):
            with self.subTest(index=index):
                held = tuple(rng.randrange(2) for _ in range(2))
                finished = tuple(rng.randrange(2) for _ in range(2))
                lines = tuple(Line(recipe, 2, rng.choice((0., .1, .5, 2.)), 10., 0., (0.,)*3, space)
                              for recipe, space in (((1, 1), 2.), ((1, 0), 1.)))
                occupied = sum(held)+2*finished[0]+finished[1]
                company = Company((1., 1.), (3, 3), float(occupied+rng.randrange(2, 10)), lines, (4, 4), 0.)
                state = State(rng.choice((0., 3., 7., 30.)), held,
                    tuple(rng.choice((.1, 2., 9.)) for _ in held), finished, (1., 2.),
                    tuple(rng.choice((3., 5., 10.)) for _ in lines), (0, 2), switching_net_ema=rng.choice((-2., 0., 1.)))
                offers = tuple(Offer(m, 2*m+s, rng.choice((.1, 1., 2., 4.)), rng.randrange(4), rng.choice((1, 2)))
                               for m in range(2) for s in range(2))
                demands = tuple((3-held[o.material])//o.lot*o.lot for o in offers)
                event = Purchase('buy', offers, demands, (.5,)*4, 1., rng.choice((0., .5, 2.)),
                    rng.choice(((0, 1), (0,), (1,), ())), 0.)
                scenarios = tuple(Scenario(probability, (event, OpenBook('sales'), SettleBook('sales',
                    tuple(rng.randrange(5) for _ in lines), rng.choice((0., 2.)))),
                    tuple(tuple(rng.choice((0., .5, 2.)) for _ in range(4)) for _ in held),
                    tuple(tuple(rng.choice((0., .25, 1.)) for _ in range(5)) for _ in lines))
                    for probability in (.25, .75))
                self.compare(company, state, event, scenarios)

    def test_existing_scaling_fixture_and_absolute_horizon_offset(self):
        company, state, scenarios = case(4, 2, 1, 2)
        event = replace(scenarios[0].events[0], funded_demands=frozen_funding(company, state, scenarios[0].events[0]))
        scenarios = tuple(replace(s, events=(event,)+s.events[1:]) for s in scenarios)
        self.compare(company, state, event, scenarios)
        posterior = tuple((s.probability, replace(s, events=s.events[1:])) for s in scenarios)
        base = candidate(company, state, state, event, posterior)
        shifted = candidate(company, replace(state, cash=state.cash+12., arrears=7.), state, event, posterior)
        self.assertEqual(base['allocation'], shifted['allocation'])
        self.assertAlmostEqual(shifted['expectedValue'], base['expectedValue']-5.)

    def test_exact_cash_boundary_sums_fees_before_adding_goods(self):
        line = Line((1, 1), 1, 0., 10., 0., (0., 0.), 2.)
        company = Company((1., 1.), (1, 1), 4., (line,), (1,), 0.)
        state = State(.35, (0, 0), (0., 0.), (0,), (0.,), (10.,), (0, 2))
        offers = (Offer(0, 0, 10., 1), Offer(0, 1, .05, 1),
                  Offer(1, 2, 10., 1), Offer(1, 3, .05, 1))
        event = Purchase('buy', offers, (1,)*4, (0., 0., .5, 0.), 1., .1, (), 0.)
        scenario = Scenario(1., (event, OpenBook('sales'), SettleBook('sales', (0,))),
                            ((0., 1.), (0., 1.)), ((0., 0.),))
        result = self.compare(company, state, event, (scenario,))
        self.assertEqual(result['allocation'], (0, 1, 0, 1))
        self.assertEqual(result['leaves'][0]['state'].cash, 0.)

    def test_unsupported_calendars_and_after_fee_rent_boundary_remain_general(self):
        company, state, scenarios = case(1, 1, 1, 1)
        event = replace(scenarios[0].events[0], funded_demands=(1, 1))
        suffix = replace(scenarios[0], events=scenarios[0].events[1:])
        for altered in (replace(suffix, events=suffix.events+(EndTick('end', .15),)),
                        replace(suffix, events=(suffix.events[0], SharedSettleBook('sales-0', (1,), groups=((0,),))))):
            # Use the actual book label from the fixture.
            if isinstance(altered.events[-1], SharedSettleBook):
                altered = replace(altered, events=(altered.events[0], replace(altered.events[-1], label=altered.events[0].label)))
            self.assertIsNone(prepare(company, state, state, event, ((1., altered),)))
        self.assertIsNone(prepare(company, state, state, replace(event, overhead_timing='after', rent_bill=1.), ((1., suffix),)))
        with self.assertRaises(ValueError):
            prepare(company, state, state, event, ((0., suffix),))
        with self.assertRaises(ValueError):
            prepare(company, state, state, replace(event, funded_demands=()), ((1., suffix),))

    def test_monetary_scales_and_neutral_future_fee_income(self):
        company, state, scenarios = case(2, 2, 1, 2)
        for scale in (1e-8, 1., 1e8):
            lines = tuple(replace(line, quote=line.quote*scale, conversion=line.conversion*scale) for line in company.lines)
            firm = replace(company, lines=lines)
            opening = replace(state, cash=state.cash*scale, quotes=tuple(p*scale for p in state.quotes))
            event = replace(scenarios[0].events[0], funded_demands=(2,)*4,
                offers=tuple(replace(o, price=o.price*scale) for o in scenarios[0].events[0].offers))
            paths = tuple(replace(s, events=(event, s.events[1], replace(s.events[2], fee_income=3.*scale))) for s in scenarios)
            actual = self.compare(firm, opening, event, paths)
            posterior = tuple((s.probability, replace(s, events=s.events[1:])) for s in paths)
            neutral = candidate(firm, opening, opening, event, posterior, neutral=True)
            self.assertEqual(actual['allocation'], neutral['allocation'])
            self.assertAlmostEqual((actual['expectedValue']-neutral['expectedValue'])/scale, 3., places=7)

    def test_fractional_storage_cancellation_uses_general_planner(self):
        line = Line((0, 1), 1, 0., 10., 0., (0., 0.), .10000001)
        company = Company((100000000.1, .1), (1, 1), 100000000.2, (line,), (1,), 0.)
        state = State(10., (1, 0), (1., 0.), (0,), (0.,), (10.,), (-1, -1))
        event = Purchase('buy', (Offer(1, 0, 1., 1),), (1,), (0.,), 0., 0., (0,), 0.)
        path = Scenario(1., (event, OpenBook('sales'), SettleBook('sales', (1,))),
                        ((0., 0.), (0., 0.)), ((0., 0.),))
        self.assertIsNone(candidate(company, state, state, event, ((1., replace(path, events=path.events[1:])),)))
        actual = solve(company, state, (path,), funding=lambda *_: (1,), audit_closing_allocation=True)
        self.assertEqual(actual['expectedValue'], 9.)
        self.assertEqual(actual['closingAudit'], dict(checked=0, unsupported=1))
        integrated = solve(company, state, (path,), funding=lambda *_: (1,), closing_search='compiled-exhaustive')
        self.assertEqual(integrated['leaves'], actual['leaves'])
        self.assertEqual(integrated['closingSolver']['unsupported'], 1)

    def test_shadow_audit_checks_endogenous_funding_without_changing_policies(self):
        for funding in ('continuation', 'continuation-transfer-neutral'):
            for supply in ('independent-snapshots', 'persistent-arrivals'):
                args = case(2, 2, 2, 2)
                expected = solve(*args, funding=funding, supply=supply, allocation_search='feasible-prefix', funding_memo_size=4096)
                actual = solve(*args, funding=funding, supply=supply, allocation_search='feasible-prefix', funding_memo_size=4096,
                               audit_closing_allocation=True)
                self.assertGreater(actual['closingAudit']['checked'], 0)
                self.assertGreater(actual['closingAudit']['unsupported'], 0)
                self.assertEqual({k:v for k,v in actual.items() if k != 'closingAudit'},
                                 {k:v for k,v in expected.items() if k != 'closingAudit'})


if __name__ == '__main__':
    unittest.main()
