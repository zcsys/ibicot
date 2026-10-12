"""Compare optimal purchases and cross-model returns under explicit forecasts.

No probabilities over models or robust policy are inferred. This is a bounded,
reference-only closing-decision diagnostic using the existing exact optimizer.
"""
import math
from .forecast_allocation import plan
from .industry_oracle import evaluate


def compare(problem, models, finished, *, product_ids, decision_tick, channel,
            finished_terminal, max_models, max_nodes):
    if (not isinstance(max_models, int) or isinstance(max_models, bool) or max_models < 1
            or not isinstance(models, dict) or not models or len(models) > max_models
            or any(not isinstance(name, str) or not name for name in models)):
        raise ValueError('named forecast models within an explicit positive model budget required')
    if not isinstance(max_nodes, int) or isinstance(max_nodes, bool) or max_nodes < 1:
        raise ValueError('positive per-model search budget required')
    names = sorted(models)
    # Alternative assumptions must concern the same seller, fixed action cap,
    # publication and products; do not compare distinct economic decisions.
    identity = None
    for name in names:
        fs = models[name]
        key = tuple((f.payoff_cap, f.diagnostics.get('seller'), f.diagnostics.get('catalog'),
                     f.diagnostics.get('latestPublishedTick')) for f in fs)
        if identity is None: identity = key
        elif key != identity: raise ValueError('models must share seller, catalog, publication tick and payoff cap')
    solutions = {}
    for name in names:
        solutions[name] = plan(problem, models[name], finished, product_ids=product_ids,
            decision_tick=decision_tick, channel=channel, finished_terminal=finished_terminal, max_nodes=max_nodes)
    allocations = {tuple(0 for _ in problem.offers)}
    allocations.update(tuple(int(x) for x in s['result'][0]) for s in solutions.values())
    optimal_values = {}
    for name, solution in solutions.items():
        chosen = tuple(int(x) for x in solution['result'][0])
        result = evaluate(solution['problem'], chosen)
        if result is None or not math.isclose(result['value'], float(solution['result'][3]), rel_tol=1e-12, abs_tol=1e-9):
            raise AssertionError('compiled plan and reference valuation disagree')
        optimal_values[name] = result['value']
    rows = []
    for allocation in sorted(allocations):
        physical = None
        values = {};regrets = {};total_payoffs = {}
        for name, solution in solutions.items():
            result = evaluate(solution['problem'], allocation)
            if result is None: raise AssertionError('forecast assumptions changed allocation feasibility')
            current = {key:value for key,value in result.items() if key != 'value'}
            if physical is None: physical = current
            elif current != physical: raise AssertionError('forecast assumptions changed physical execution')
            value = result['value'];best = optimal_values[name]
            tolerance = 1e-9 + 1e-12*max(abs(best),abs(value))
            if value > best + tolerance: raise AssertionError('cross-evaluated allocation exceeds claimed optimum')
            values[name] = value
            regrets[name] = max(0., best-value)
            total_payoffs[name] = value + math.fsum(solution['existingFinishedPayoff'])
        rows.append(dict(allocation=allocation, execution=physical, incrementalReturns=values,
                         returnsIncludingExistingFinished=total_payoffs, regrets=regrets,
                         worstRegret=max(regrets.values()), optimalUnder=[name for name in names
                             if allocation == tuple(int(x) for x in solutions[name]['result'][0])]))
    return dict(version=1, models=names, optimalValues=optimal_values,
        optimalAllocations={name:tuple(int(x) for x in solutions[name]['result'][0]) for name in names},
        decisionInvariant=len({tuple(int(x) for x in s['result'][0]) for s in solutions.values()}) == 1,
        candidates=rows, maxModels=max_models, maxNodesPerModel=max_nodes,
        scope='Single closing purchase with fixed funded bids, fees, quotes, resources and terminal values. Models are explicit alternatives, not probabilities or confidence bounds. Candidate set is the union of model optima and no purchase; it does not establish a minimax-regret optimum over all feasible allocations. Returns are planning values, not posted earnings.')
