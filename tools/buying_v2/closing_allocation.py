"""Experimental reduction of a final purchase to the compiled basket solver.

The phase oracle can audit this result in shadow; it does not select policies
with this adapter. Remaining arithmetic boundaries require certification first.
Unsupported calendars return None; they must retain the general event tree.
"""
from dataclasses import replace
import math
from .quantity_value import LinearQuantityValue
from .industry_oracle import Problem, validate
from .industry_search import solve
from .phase_ledger import OpenBook, SettleBook, apply, horizon_value, room, _overhead, validate_state
from .scenario_validation import validate_calendar


def prepare(company, initial, state, event, posterior, *, neutral=False):
    """posterior contains (positive weight, Scenario with ONLY the suffix).

    Current funded demands are explicit, including for hypothetical funding
    queries. No forecast, terminal value, or independence assumption is invented.
    """
    validate_state(company, initial)
    validate_state(company, state)
    if any(q!=int(q) for q in (*state.held,*state.finished,*company.slots)):
        return None
    if not posterior or any(not math.isfinite(w) or w <= 0 for w, _ in posterior):
        raise ValueError('positive finite posterior weights required')
    if any(isinstance(t,LinearQuantityValue) for _,p in posterior for t in p.input_values+p.finished_values):return None
    mass = math.fsum(w for w, _ in posterior)
    if not math.isfinite(mass):
        raise ValueError('nonfinite posterior mass')
    for _, scenario in posterior:
        validate_calendar(company, state, replace(scenario, events=(event,)+scenario.events))
    if state.book is not None:
        return None
    # The staged ledger recomputes physical room after purchases. With fractional
    # spaces, cancellation can differ from the combined solver's running total
    # enough to change feasibility. Keep those states on the general planner.
    spatial = (company.storage, *company.spaces, *(line.output_space for line in company.lines))
    if any(x != int(x) or abs(x) > 2**52 for x in spatial):
        return None
    maximum_space = sum(max(int(h), int(s))*int(v) for h, s, v in zip(state.held, company.slots, company.spaces))
    maximum_space += sum(int(q)*int(line.output_space) for q, line in zip((max(q,h) for q,h in zip(company.finished_caps,state.finished)), company.lines))
    if maximum_space > 2**52:
        return None
    # After-procurement equity can cross the rent threshold when fees are paid.
    # Even fee-free floating-point asset exchanges need a separate boundary audit.
    if event.overhead_timing == 'after' and event.rent_bill != 0:
        return None
    for _, scenario in posterior:
        if (len(scenario.events) != 2 or type(scenario.events[0]) is not OpenBook
                or type(scenario.events[1]) is not SettleBook):
            return None
    n = len(state.held)
    slots = tuple(max(h, s) for h, s in zip(state.held, company.slots))
    if any(len(s.input_values[m]) <= slots[m] for _, s in posterior for m in range(n)):
        return None
    if any(len(s.finished_values[r]) <= max(company.finished_caps[r],state.finished[r])
           for _, s in posterior for r in range(len(company.lines))):
        return None
    bids = [0]*n
    fees = [0.]*n
    if len(event.funded_demands) != len(event.offers):
        raise ValueError('explicit frozen funded demands required')
    for i, offer in enumerate(event.offers):
        if offer.supplier == state.incumbents[offer.material]:
            bids[offer.material] = event.funded_demands[i]
            fees[offer.material] = event.fee_multiple*event.fee_unit_cost*(1+min(1., max(0., event.reliability[i])))
    overhead = (_overhead(company, state, event.rent_bill, event.rent_threshold)
                if event.frozen_overhead is None else event.frozen_overhead)
    constant = state.cash-initial.cash+initial.arrears-state.arrears
    constant += math.fsum(w*(0. if neutral else s.events[1].fee_income) for w, s in posterior)/mass
    lines = []
    for r, line in enumerate(company.lines):
        limit = max(0,min(line.max_batches, (company.finished_caps[r]-state.finished[r])//line.output_qty)) if r in event.active_lines else 0
        values = []
        for produced in range(limit*line.output_qty+1):
            stock = state.finished[r]+produced
            value = math.fsum(w*(state.quotes[r]*min(stock, s.events[1].demand[r])
                +s.finished_values[r][max(0, stock-s.events[1].demand[r])]) for w, s in posterior)/mass
            # Preserve the absolute horizon objective used by relative tie tolerance.
            values.append(value+(constant if r == 0 else 0.))
        lines.append(replace(line, max_batches=limit, quote=state.quotes[r], overhead=overhead, output_values=tuple(values)))
    terminal = tuple(tuple(math.fsum(w*s.input_values[m][q] for w, s in posterior)/mass
                           for q in range(slots[m]+1)) for m in range(n))
    problem = Problem(state.held, state.basis, company.spaces, slots, max(0., room(company, state)),
        state.cash, event.offers, state.incumbents, tuple(bids), tuple(fees), tuple(lines), terminal,
        company.margin_band, event.funded_demands)
    validate(problem)
    return problem


def candidate(company, initial, state, event, posterior, *, neutral=False, hold_incumbents=False, max_nodes=100000):
    """Return a candidate plus actual ledger outcomes, NOT an oracle certificate.

    Replaying the selected basket detects a discrepancy there. It cannot prove
    that every rejected basket had equivalent production or tie behavior.
    """
    problem = prepare(company, initial, state, event, posterior, neutral=neutral)
    if problem is None:
        return None
    result, certificate = solve(problem, max_nodes=max_nodes)
    allocation = tuple(int(q) for q in result[0])
    purchased, detail = apply(company, state, event, allocation)
    if hold_incumbents:
        purchased = replace(purchased, incumbents=state.incumbents)
        detail = {**detail, 'preferences': state.incumbents}
    mass = math.fsum(w for w, _ in posterior)
    leaves = []
    for weight, scenario in posterior:
        final = purchased
        trace = [detail]
        for following in scenario.events:
            if neutral and type(following) is SettleBook:
                following = replace(following, fee_income=0.)
            final, step = apply(company, final, following)
            trace.append(step)
        leaves.append(dict(probability=weight/mass, value=horizon_value(initial, final, scenario.input_values,
            scenario.finished_values), state=final, trace=tuple(trace)))
    actual = math.fsum(leaf['probability']*leaf['value'] for leaf in leaves)
    tolerance = 1e-9+1e-12*max(abs(actual), abs(result[3]))
    if tuple(result[1]) != detail['outputs'] or abs(actual-result[3]) > tolerance:
        raise AssertionError('compiled closing candidate differs from staged ledger')
    return dict(allocation=allocation, expectedValue=actual, compiledValue=float(result[3]),
                leaves=leaves, certificate=certificate)
