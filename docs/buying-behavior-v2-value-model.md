# Industrial value model: implementation contract and counterexamples

Status: candidate design and executable small-instance evidence, 2026-10-12. This does not adopt a forecasting model, alter production defaults, or rehabilitate R1. It implements the master plan's D3 comparison and establishes requirements for D4–D5. See the [industrial solver contract](buying-behavior-v2-industrial-contract.md) for the current action space and the [source review](buying-behavior-source-review.md) for literature support and its limits.

## What the objective comparison establishes

`tools/buying_v2/policy_comparison.py` independently enumerates actual feasible purchases and production for the batch-first and scenario-return objectives. Every objective computes its own joint, stock-unconstrained funded quantities. Reusing a maximum-item bid for another objective can exclude an essential complement before that objective evaluates any basket.

The storage comparator maximizes input items bought, then minimizes goods/fees. Batch-first maximizes actual produced output items under the retained production gate, then input items bought, then minimizes goods/fees. Scenario-return uses explicitly supplied output and terminal-input values, minus goods, fees and actual conversion. None of these fixture value tables is a measured forecast.

| Counterexample | Storage comparator | Batch-first | Scenario-return |
| --- | --- | --- | --- |
| $4 cash; two complementary inputs at $1/$2; $0.50 conversion per two-output batch | Buys four cheap inputs; produces zero | Buys one of each; produces two | Same useful kit; scenario value $2.50 |
| $10 cash; input $1; conversion $1/item | Buys ten; no cash to produce | Buys/produces five | Produces five; scenario value $10 |
| Output quote $4 but only one output is expected to sell; input $1, conversion $0.25 | Produces eight; scenario value −$6 | Same unsold-output exposure | Produces one; scenario value $2.75 |
| One owned input with historical basis $100; cheap complement; output quote $3 | Buys complements; gate prevents production | Secondary buffer objective still buys; gate prevents production | Buys nothing |
| Complement unavailable now; explicitly valuable future buffer | Fills four input slots | Same quantity despite no current output | Buys two under the stated terminal-value table |

Evidence: `stats/buying-implementation/industrial-objective-counterexamples-v2.json`. The first output attempt is retained as a partial JSON file after a NumPy-scalar serialization error; it is not valid evidence. Serialization now completes before opening the destination.

These are counterexamples, not population-level causal estimates. They rule out treating either item count or immediate production as the final economic objective. Retain the existing storage comparator for isolated mechanics attribution; do not silently promote batch-first as a demand model. A final candidate needs realizable sales, conversion liquidity and justified continuation value.

## A buffer's value is conditional on the future plan

`continuation_oracle.py` enumerates two purchase decisions with the same cash, lots, stock, input/finished storage, historical basis and ordered production gate. This benchmark deliberately has no intermediate sales receipts, no rent and no loyalty fees. Closing sales occur after the second decision; unsold finished goods have zero terminal value. It is a delayed-receipt scenario, not a replacement for every tier's actual execution schedule.

Worked fixture: start with $11; input A costs $1 now; B is unavailable. At the second decision, up to two B units may arrive at $4 each. A+B produces two output units, with $0.50 conversion per batch. Closing demand can buy four units at $3 each.

- With B certain to arrive and closing demand certain, buy two A now, then two B, and produce four. Costs are $2+$8+$1; closing receipts are $12. Closing cash is $12, a $1 increase over the initial $11.
- If B never arrives, buy nothing. An assumed permanent buffer value would buy stranded inventory in this scenario.
- Buying three A leaves only $8 for B and conversion. Continuation value falls from $3 at two A to $1.50 at three A. An input's terminal value cannot generally be a fixed quantity-only curve independent of remaining cash and complement availability.
- With a 50% arrival chance, the same initial action must serve both states. Buying two has expected value `0.5 × $3 − $2 = −$0.50`, so no purchase is optimal. At 75%, expected value is `$0.25`, so buying two is optimal.

The second decision may observe supply and quotes, but not the closing demand realization. Its value table averages possible demand before selecting one basket. Averaging separately optimized demand-realization outcomes would give the buyer foresight it does not have; an explicit regression rejects that result. Branches with identical observed supply/technology are merged before optimization, even when their scenario labels or hidden demand/terminal values differ. Labels cannot act as an information channel.

Evidence: `industrial-continuation-counterexamples.json` and `industrial-continuation-information-tests.log`. The latter passes eight tests, including no double counting of output held between periods, complement arrival, shared conversion cash and hidden future demand. The small continuation oracle is not yet compiled, population-scaled, or integrated with all phase-specific receipts/fees/rent. It supplements, rather than validates, the existing additive terminal-value solver.

## Candidate economic contract

Implement a scenario-based expected-return candidate which replans at each actual purchasing phase. The first action is one coupled basket across every eligible owned line and input; subsequent scenario actions may respond only to information revealed by their decision time. Include no purchase, splits, wholesale lots, shared resources and unmatched buffers. Preserve the accepted preference and fee rules for all actual actions.

The objective is expected realizable sales receipts plus terminal asset value, minus new input payments, conversion and incremental operating payments over the declared horizon. Treat initial purchase costs as sunk for this decision, but retain their basis in production feasibility and COGS. This is a cash-return decision objective, not the financial definition of net earnings. Real accounts continue to capitalize inventory purchases and post COGS only upon sale.

Requirements:

1. Run the actual production gate against planned resulting basis and available conversion cash. An optimistic output plan cannot override the gate.
2. Place receipts at the real tier/complexity phase boundaries. Do not reuse same-phase deferred supplier receipts or future retail receipts early. The delayed-receipt fixture above is one test scenario, not universal timing.
3. Value finished goods once: a unit is either sold within the horizon or remains in terminal inventory. Do not credit both current quote revenue and a terminal sale for it. Existing finished stock consumes prospective demand before new output.
4. Make input continuation value conditional on remaining cash, all complementary inputs, installed routes, future supply and production feasibility. Additive input tables may be a tested approximation, not assumed equivalent to the coupled value function.
5. Model loyalty fees under original-incumbent availability at each actual future decision. Fee transfers stay separate from goods cost. Future fee income is uncertain; do not guarantee it to finance purchasing.
6. Include incremental rent/payment exposure and threshold transitions without subtracting the same allocated overhead twice. Overhead in the gate is not itself an additional cash posting. Current small fixtures use zero rent/fees and cannot validate this requirement.
7. Declare the horizon and terminal boundary. Zero terminal value is a conservative experiment, not a ban on buffers: buffers with realizable use inside the horizon remain admissible. Test horizon-extension sensitivity before adoption.
8. Compare the scalable solver with the non-anticipating small oracle. State any approximation explicitly and measure its decision/value gap; neither a hidden heuristic nor a narrowed player action space satisfies the existing contract.

## Information and estimator contract

Do not feed a sum of legacy quoted remainders to a forecast as if it were unique demand. The new industrial observations distinguish those remainders, funded availability checks and actual purchases. Aggregate sampled checks also do not identify a supplier's future customers.

Implement and compare these information regimes with the same objective and action space:

| Regime | Permitted observations | Required caveat |
| --- | --- | --- |
| Local | Own phase-specific stock, realized sales/revenue, posted quotes, actual buyer interactions and own procurement observations | Zero sales with zero exposure is missing information; depleted stock censors potential sales. Ending tick stock alone cannot establish whether an earlier purchasing phase stocked out. |
| Market | Archived product-level transaction and indicated-quantity distributions, quotes and availability diagnostics, published after the tick | Product totals must not be repeated as each company's forecast. Use an explicit estimated share with a cold-start rule; shares do not guarantee customers. |
| Hybrid | A declared blend of the two distributions | Use the same observation lag and comparable units. Test synchronization and upstream order amplification. |

The forecast must describe **realizable sales for this company at its contemplated quote**, not consumer utility or technological capacity. Preserve complete observations separately from lower-bound censored observations. Where missing/censored data leave a tail unidentified, represent that uncertainty with explicit scenarios instead of declaring sales equal demand. For valuation, demand beyond physically sellable output can be represented by a saturated-sale scenario; this bounds the payoff calculation without claiming an economic demand ceiling.

Cold-start priors, censoring-tail weights, quote-response assumptions and local/market blend weights are calibration assumptions to preregister before the next campaign. No value is adopted here. One price/quantity observation does not identify an elasticity. The implementation must expose these parameters and report sensitivity, shutdown/re-entry, no-history behavior and failed candidates. Do not conceal a permanent demand floor or guaranteed margin inside a prior.

Collector work required before a world candidate: phase-specific seller exposure/stock histories, realized price/quantity observations, versioned forecast state, initialization/reset/continuation and a bounded decision trace. Existing period totals alone do not supply all of this information.

## Next implementation gates

Extend the small continuation contract to real phase timing, fees and rent; then implement the local/market/hybrid scenario collectors and a scalable candidate against that oracle. Use calibration runs only, preserve failures and preregister new held-out seeds before evaluation. The mechanics comparison, forecast model and performance/economic validation remain separate claims. No production adoption or live reset is authorized by these fixture results.

## Observation implementation

The [phase-specific seller-history contract](buying-behavior-v2-seller-history.md) documents the implemented read-only collector, persistence and full-population state-preservation evidence. These observations are inputs for future estimator comparisons; no demand estimate, continuation-value default or live policy has been adopted.

The [forecast candidate contract](buying-behavior-v2-forecast-contract.md) now defines executable local/market/hybrid reference distributions, their mandatory assumptions and historical calibration limitations. It also implements inquiry-informed versus transaction-only feedback with a paired historical calibration screen. These candidates are not yet consumed by world purchasing; lower retrospective error is not an adoption result.

## Phase-aware continuation implementation

The [phase ledger and oracle contract](buying-behavior-v2-phase-oracle.md) now supplies immutable book settlement, phase-specific receipt availability, accepted preference/fee transitions, historical basis, rent/arrears and non-anticipating small event-tree optimization. It supersedes the old delayed-receipt fixture as the broader timing test harness, while retaining that fixture as a regression. Exactness is conditional on the explicit supplied funding rule and external scenarios; a [joint continuation-funding candidate](buying-behavior-v2-continuation-funding.md) is now implemented, with strategic and world-validation gates still open.

The phase oracle now supports explicitly grouped residual sales through `SharedSettleBook`, preventing two interchangeable owned output lines from each receiving the whole same-product opportunity. Its verified counterexample changes procurement from two inputs to one when demand is shared, and to no new input when old stock already covers the opportunity. This is a scenario interface and accounting/planning check; it does not select the joint forecast, competitor model or market allocation rule. See the [shared-demand contract](buying-behavior-v2-phase-oracle.md#shared-demand-across-owned-lines).

Controlled actual-retail-phase [stock/quote probes](buying-behavior-v2-forecast-contract.md#controlled-stock-and-quote-probes-candidate-limitations) now expose competitive displacement and cold-start limitations in the empirical forecast. Better historical transaction-only MAE does not justify consuming that candidate in production: it predicts positive sales after an own-price increase causes all buyers to choose cheaper stocked rivals. The next forecast proposal must address competitive response and re-entry explicitly, while retaining the shared-sales and continuation constraints above.

Ownership correction: the [complete-catalog audit](buying-behavior-v2-phase-oracle.md#ownership-scope-correction-from-the-authoritative-catalog) establishes that neither self-supply nor two identical-product installations within one company is supported under current rules. The shared-demand example above is a hypothetical scenario capability, not a demonstrated current-world defect. The production candidate must still coordinate distinct owned products, shared inputs, cash/storage and correlated demand; this audit does not relax those requirements.

## Implemented demand-informed replenishment comparator

`demand_replenishment.plan` supplies the explicitly labeled demand-informed comparator required by stages 5–6. It consumes one explicit one-sales-phase forecast at the current quote for each eligible installed line, plus existing finished stock. It does not select or calibrate a forecast. Forecast coverage must include existing finished stock plus every feasible new output; mismatched quotes, incomplete caps, invalid distributions and dimensions are rejected.

For line r, with existing finished items F_r, forecast sales quantity D_r, maximum batches B_r and output yield y_r:

`expected residual sales_r = E[min(B_r × y_r, max(0, D_r − F_r))]`

`target batches_r = min(B_r, ceil(expected residual sales_r / y_r))`

Sum each line's recipe quantities times target batches across all lines, including repeated/shared inputs. Clip the resulting input holding target to the existing physical slot, while retaining already-owned inputs above that target. The existing jointly funded replenishment solver then maximizes target units and minimizes payable goods/fees under shared resources. Its original floor-to-lot rule remains: a one-item target in a two-item wholesale market is unfilled, rather than silently enlarged into a surplus buffer.

Existing finished goods meet each scenario's sales before calculating new needs. `E[max(0,D−F)]` generally differs from `max(0,E[D]−F)`: with equal chances of zero/four demand and two finished items, expected residual sales are one, not zero. Summing expected target requirements across distinct owned products does not require an independence assumption, but it also does not account for the economic effects of joint uncertainty on future constrained actions.

This is an inventory-target policy, not industrial willingness to pay. It does not reserve conversion cash, solve complementary production economics, value continuation or change the actual production gate. Production may still use existing inputs beyond the target. Ceiling to batches can trigger a whole batch from a tiny positive expected demand; that rounding consequence is explicit, not a justified permanent demand floor. `result.value` is scored using the caller's original problem output/terminal tables, not inferred from the target or described as booked net earnings.

The archived report compares four policies under the same five analytical fixtures and scoring tables:

| Case | Demand-target result | Coupled scenario-return result |
| --- | --- | --- |
| Scarce cash for complements | Buys four cheap inputs, produces zero, value −$4 | Buys one of each, produces two, value $2.50 |
| Conversion liquidity | Buys ten inputs, produces zero, value −$10 | Buys/produces five, value $10 |
| One realizable sale | Buys/produces one, value $2.75 | Same |
| Expensive owned basis blocks production | Buys one complement, produces zero, value −$1 | Buys nothing, value $0 |
| Valuable future buffer with no current sale | Buys nothing, value $0 | Buys two buffer inputs, value $1 under the explicit terminal assumption |

The scenario-return column remains the existing small analytical comparator, not the final calibrated continuation model. These failures rule out promoting the new target policy as a substitute for coupled expected-return planning. They do not estimate population effects.

Fifteen targeted demand-target and prior objective/continuation tests pass in 1.804 seconds. They include existing stock under uncertainty, multiple lines with shared/repeated ingredients and batch yields, zero demand, high input prices, wholesale rounding, production-gate and conversion-liquidity failures, and invalid forecasts. `20261012-demand-target-comparator/final-examples` preserves complete inputs/results and a source archive with all hashes verified. Added validation leaves the five original comparison outcomes byte-identical to the first archived report. Reproduce with `python -m tools.buying_v2.demand_target_report --output <fresh-directory>` using the compatible interpreter and archived dependencies.

The comparator is currently a small reference implementation. World integration, compiled execution and calibration are not claimed, and it does not close the final industrial-model or adoption gates.

## Forecast-valued coupled allocation adapter

`tools/buying_v2/forecast_allocation.py` connects explicit marginal sales forecasts to the existing exact compiled industrial allocation search. It is a single-purchase, single-closing-sales comparator: production occurs before sales are observed and there is no later purchasing recourse. It does not select a forecast regime, derive funded intentions or implement the full phase-aware policy. Per-offer funded caps must already be supplied; the adapter rejects an unspecified cap vector and preserves supplied incumbent bids and fees. In particular, it does not silently invoke the older reference-quote funding decomposition rejected by the continuation counterexample.

For line r with existing finished stock F, new output x, contemplated quote p and a caller-supplied terminal finished-stock table T, the total closing payoff is:

`G(F + x) = E[p × min(F + x, D) + T(max(0, F + x − D))]`

The line's new-output value table is `G(F + x) − G(F)`. Thus old stock consumes sales opportunities first, sold items receive no terminal inventory value, and the unchanged opening-stock payoff is recorded separately as a constant. Terminal input tables remain explicit problem inputs; no fixed buffer valuation is adopted. The planner subtracts actual procurement/fees/conversion through the existing solver and preserves cash, lots, splits, shared inputs/storage, installed production order, historical basis and the retained margin gate. Gate overhead is not posted again as cash expense.

Because this comparator has an additive closing payoff and no sales-dependent recourse or shared sales capacity, marginal expectations suffice even if distinct products' demand is correlated. That statement does not extend to the multi-phase planner: the joint-forecast financing example already demonstrates why dependence changes later feasible actions. Product identities, quote, publication tick, channel and consistent catalog metadata are checked; the caller remains responsible for mapping the physical company's installed lines and occupied finished-stock space correctly. Forecast support must cover existing stock plus maximum new output. Invalid distributions, incomplete terminal tables and unavailable search budgets fail explicitly.

Five executable examples cover a one-sale forecast, old stock serving demand first, an unprofitable input quote, insufficient conversion liquidity and historical basis blocking production. With two old items and demand equally likely to be zero or three at a $4 quote, one new item has expected incremental revenue $2; a $1 input plus $0.50 conversion yields $0.50 expected incremental return. Including a $0.25 residual-item terminal value gives a total payoff of $6.375 for three finished items: half of outcomes sell all three for $12, half retain three worth $0.75. No sale or terminal quantity is counted twice.

Thirty-two targeted adapter, industrial-search and forecast tests pass in 0.611 seconds. The new tests include 120 seeded shared-input/two-line cases: an independent exhaustive traversal uses the independent production evaluator and directly sums scenario receipts, without using the adapter's generated value tables. It agrees with the compiled optimizer's optimal value. Other checks cover price response, old-stock demand coverage, conversion cash, historical basis, malformed/misaligned forecasts and explicit search-limit failure.

`stats/buying-implementation/20261012-forecast-allocation/` preserves complete example inputs/results, tests, source hashes/archive and byte-identical example replay. This is an implemented comparator and integration primitive, not calibrated demand, scalable multi-phase planning, a world adapter or completion of D4–D6. Current forecast failures, conditional continuation values, funding incentives, operating timing and population performance remain required before adoption. Production behavior is unchanged.
