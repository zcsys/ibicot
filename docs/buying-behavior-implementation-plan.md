# Company buying behavior implementation master plan

Date: 2026-10-12. Status: implementation in progress; D1 and D2 accepted. Unresolved economic choices and live adoption remain subject to the validation and decision gates below. See the [implementation progress record](buying-behavior-implementation-progress.md) for completed evidence.

Keep the existing engine as the production baseline, correct the documented purchasing mechanics, and evaluate a new industrial buying model against that corrected baseline. Historical R1 remains rejected. Deliver the mechanics correction and the industrial replacement as separately reviewable milestones; either can fail validation without forcing adoption of the other.

The [completed research report](buying-behavior-research-report.md), [requirements audit](buying-behavior-requirements-audit.md), and [research brief](buying-behavior-research-brief.md) establish the evidence and confirmed requirements. The [integration rules](midbridge-integration.md) govern current execution and ownership. The [R1 model](buying-behavior-model.md) describes a rejected experiment, not the specification for its replacement.

## Purchasing scope boundary

The [current scope audit](buying-behavior-scope-audit.md) records code and documentation checks against this boundary.

The user explicitly confirmed on 2026-10-12 that this buying-behavior work must not change outside parameters or logic. Preserve population, active recipes/complexities, capacities, sell-side price parameters and pricing rules, production rules and historical-cost gates, storage, rent, demand settings, execution order and other non-purchasing mechanics. Different outcomes caused by changed purchases are not permission to alter those rules. Isolated synthetic fixtures may vary inputs for tests; they do not change production defaults. Any candidate requiring an outside amendment must be reported as incompatible with the current authorized scope, not silently implemented or treated as a pending part of an approved model change. Purchasing observations, accounting of actual purchases and policy-compatible persistence must retain existing non-purchasing behavior.

## Outcomes and scope

The intended result is companies that consider partial and split offers, pay economically justified loyalty fees under explicit rules, and buy quantities responsive to price without violating cash, storage, recipes, or actual production feasibility. Decisions must remain deterministic, explainable, and practical at full population.

| Buyer | Implementation scope |
| --- | --- |
| Gaia and T0 | Preserve environmental sourcing and extraction behavior. Measure upstream consequences; do not invent procurement for Gaia or new T0 input markets. |
| T1 | Raw-input purchases, wholesale lots, complementary recipes, incumbents per input, and shared company resources. |
| T2 | Purchases from T1 and T2, repeated inputs, multiple installations, industrial split purchases, and complexity-phase execution. |
| T3 | Preserve the verified price-sensitive quantity rule; correct discovery, fee-aware selection, preference semantics, and measurement as needed. |

No incidental changes to consumer demand, credit, expansion, machinery markets, recipe allocations, rent, loyalty calibration, sell-side pricing, or the production margin gate. A candidate requiring a change to one of these is outside this task’s authorization. Report that limitation; do not implement the amendment or treat it as an approved treatment.

## Evidence that determines the sequence

R1 passes important accounting and restricted-solver checks, but its industrial action space excludes required splits and supported multiple-route ownership. Its market-information variant retains only 12.21% of baseline retail volume in the final year of two generations. All five matched timing pairs fail the relative budgets. These failures rule out promoting R1 and then repairing it in production.

The existing engine also has documented defects: preference for full-fill suppliers, industrial incumbent changes after partial deliveries, inconsistent search scope, and demand counters that mix different intentions. The production retail fallback calculation already passes the user's example. Preserve that calculation and its tests.

Market requests are a useful next-study comparator, not a selected production information regime. Local observations including fallback sales and hybrid forecasts remain candidates. No tested estimator solves the generation-scale failure by itself.

## Decision register

D1 and D2 were resolved by the user on 2026-10-12: one supplier must alone supply the whole demand to qualify; freeze the original incumbent and charge at most one fee per product order under the proposed availability rule. See the [accepted contract decisions](buying-behavior-contract-decisions.md). Other implementation and validation gates remain open.

Resolve these in a new replacement contract before dependent behavior changes. Independent recording, fixtures, and baseline work can proceed meanwhile. The existing research documents remain historical evidence.

| ID | Decision | Required resolution |
| --- | --- | --- |
| D1 | Whole relevant bid and preference qualification | Accepted: retain the old preference in A=2/B=6. One supplier alone must supply the whole funded demand at its own quote. Apply to first assignment as well; verify equal prices, cash limits and multiple challengers. |
| D2 | Fee reference and order boundary | Accepted: freeze the original incumbent and live availability against the funded demand at its own quote; one existing-formula fee per product order if an outside supplier sells and the incumbent could fill. Test inflated bids, order splitting, fee farming and lock-in. |
| D3 | Supplier objective during mechanics correction | Resolved (user-directed): latent demand = "fill to brim" (storage slot); quantity follows the Tier 3 curve with the input's reference cost as the halving price. Labeled replenishment, not newly derived industrial demand. |
| D4 | Industrial value and execution | Resolved (user-directed): halving price = reference cost (canon V = unit cost), elasticity 2; no forecast. The historical-cost production gate is unchanged. |
| D5 | Information available to firms | Resolved (user-directed): the buyer uses its own slot shortage and the offered quote; no market intelligence. |
| D6 | Solver scope and complexity | Resolved (user-directed): the rule is closed-form (`demand_at_price`), so no solver is required for the adopted model. |

D1 and D2 are resolved and govern implementation; do not reopen them. D3–D6 were resolved by the user on 2026-10-12 with the simple price-sensitive fill-to-brim rule above (latent demand = storage slot, quantity = Tier 3 curve with the input's reference cost as the halving price, elasticity 2). The contract decision pack and baseline fixtures are available; remaining work is tracked in the implementation progress record.

## Sequence and dependencies

| Stage | Deliverable | Depends on | Exit condition |
| --- | --- | --- | --- |
| 0 | Frozen current baseline and evidence map | Repository inspection | Reproducible code/config/catalog identity and verified recording window. |
| 1 | Purchasing contract and independent fixtures | Stage 0 | D1–D3 settled for mechanics; adversarial cases specify expected outcomes. |
| 2 | Versioned purchasing observations | Stage 0 and metric definitions | Instrumentation leaves economic state and decisions unchanged. |
| 3 | Reference mechanics correction | Stages 1–2 | Required scope passes independent allocation and settlement checks. |
| 4 | Compiled mechanics and corrected baseline | Stage 3 | Reference parity, determinism, ownership, economics, and performance pass. |
| 5 | New industrial model and small oracle | D4–D6; Stage 4 for comparison | No unresolved structural counterexample in the supported scope. |
| 6 | Isolated compiled industrial candidate | Stage 5 | Full-world implementation and continuation checks pass; practical timing. |
| 7 | Preregistered economic validation | Stages 4 and 6 | Held-out long-run, stress, fairness, and performance gates pass. |
| 8 | Integration and reviewed rollout package | Passing gates for the selected milestone | Exact artifact, schema, documentation, dashboard, and rollback are ready. |

This is dependency order, not authorization to start multiple agents. Estimate implementation effort after the contract and solver feasibility are known. Estimate experiment duration from measured warm full-population ticks and recording overhead; do not promise a completion date from R1 timing.

### Current stage status (2026-10-12)

| Stage | Status | Current evidence and remaining blocker |
| --- | --- | --- |
| 0 | Complete | Baseline, catalog/config identity and recording window preserved under `stats/buying-implementation/`. |
| 1 | Complete | D1/D2 accepted and executable; D3–D6 resolved by the user with the price-sensitive fill-to-brim rule. |
| 2 | Complete | Typed counters, seller history, bounded decision traces and a rendered recorded-data inspector. |
| 3 | Complete | Reference T1/T2 retail and industrial purchasing with atomic settlement and independent oracles. |
| 4 | Complete | Compiled mechanics; fresh full discovery passes 663 tests (430s) after the offer-collapse optimization. |
| 5 | Complete | D3–D6 resolved with the price-sensitive fill-to-brim rule; `input_reference_cost` (V = unit cost) + `demand_at_price` (η = 2) implemented in both kernels. |
| 6 | Complete | The user-directed closed-form rule (price-sensitive fill-to-brim) supersedes the continuation solver and is already in the compiled production kernel; full-population benchmark measures step median 137 ms/tick (p95 160 ms). The continuation solver (captured 8/8, offer-collapse/funded-cap/dedup/symmetry-break) is retained as historical evidence, not the adopted model. |
| 7 | Not started | Requires passing Stage 5/6 plus authorized isolated live runs; cannot be run under the current no-live-runs restriction. |
| 8 | Not started | Requires Stage 7 gates and the user's explicit rollout decision. |

The mechanics milestone (Stages 0–4) is complete and independently verifiable. The industrial model (Stage 5) and its compiled full-world implementation (Stage 6) are complete under the user's price-sensitive fill-to-brim directive (step median 137 ms/tick). Stages 7–8 (authorized live economic validation and rollout) remain open; the ~40% T2 fulfillment at the reference halving price is a calibration choice flagged for the user.

## Stage 0 Preserve the baseline

Inspect branch, diff, applicable instructions, catalog, launcher interpreter, and current tests. Preserve unrelated work. Before interacting with any live experiment, establish its process, configuration, tick, output directory, and recording status. Use a separate port and uniquely named output directories for development.

Capture the current production baseline independently of the historical R1 archive. Record commit and patch hashes, catalog/configuration, seeds, initialization or checkpoint, runtime versions, and tick coverage. Retain the completed research campaign unchanged.

Build a compact evidence map from each reported defect to its source path, executable counterexample, and proposed acceptance test. Do not assume a defect remains merely because the old report describes it.

## Stage 1 Specify purchasing and settlement

Write a new purchasing contract with equations, units, observation timing, feasible actions, deterministic ties, integer/lot rounding, order boundaries, and accounting postings. Reuse research fixtures only after checking that their expected behavior matches the new contract.

Preserve the confirmed same-product fallback rule:

`remaining_s = max(0, q(price_s) - cumulative_purchased)`

The delivered quantity is bounded by this remainder, live stock, lot size, affordable goods plus payable fees, and remaining storage. The rule determines the remaining request; it does not itself define industrial `q`, supplier order, fee eligibility, or incumbent qualification. For industrial complements, recompute a coupled feasible plan rather than treating every ingredient as an independent consumer.

Specify five distinct alternatives plus the incumbent, without replacement. Define the eligible supplier universe, fewer-than-five markets, empty stock, ownership restrictions, inactive lines, stable tie rules, and sampling roles keyed by stable identity. Read live stock at the declared decision point after earlier buyers settle. A quote inspected during search is not an incoming order.

Create independent exhaustive fixtures for cheap partial versus expensive full supply; A=2/B=6 and longer fallback chains; Q−1/Q/Q+1 incumbent stock; all four required fee/preference combinations; zero purchases; fee-unaffordable cash; repeated inputs; wholesale rounding; storage limits; useful unmatched buffers; shared inputs and multiple lines; and sequential buyers competing for stock.

## Stage 2 Make observations trustworthy

Define and record separate events for offers inspected, price-dependent intentions, actual requests, fulfilled quantities, stock/cash constraints, fee-bearing purchases, initial incumbent assignments, and true incumbent changes. Assign a stable order identity where needed to deduplicate split attempts. Preserve per-supplier attempts for reliability without interpreting their sum as unique product demand.

For every demand and fulfillment metric, state its reference quote, numerator, denominator, time window, and treatment of zero demand. Baseline `LastQ` and R1's first-funded-intention counter must remain distinguishable in historical exports. Introduce versioned fields rather than silently changing the meaning of old recordings.

Aggregate hot-path counters in typed arrays; retain bounded deterministic decision samples for reconstruction. Measure instrumentation overhead separately. Prove that adding observations leaves world state and economic decisions unchanged, excluding explicitly new measurement arrays. The optional [industrial decision traces](buying-behavior-v2-decision-traces.md) now provide bounded reconstruction and measured startup overhead; [Distributor samples](buying-behavior-v2-retail-traces.md) now cover retail decisions as well; a [recorded-data inspector](buying-behavior-v2-inspector.md) has been rendered and checked against actual samples. Live integration and the remaining performance checks are still open.

## Stages 3 and 4 Correct mechanics and establish the comparison engine

Implement the reference path first, using shared primitives where compatible with Numba. Separate discovery, feasible basket evaluation, availability checks, fee calculation, transactional settlement, and incumbent updates. Commit actual goods, cash, COGS, and fees consistently; candidate evaluation must not mutate state or create fees.

Introduce isolated treatments for distinct discovery, partial eligibility, fee handling, and preference rules, then test their combined effect. Keep these switches in the experimental harness where possible instead of creating a permanent matrix of production options. Hold industrial replenishment targets fixed in this milestone. It does not fulfill the later goal of price-sensitive industrial willingness to pay.

Port verified behavior to compiled loops, retaining active-population slices and source-aware JIT invalidation. Preserve retail access to opening stock and ascending manufacturing complexity. Within each current phase, coordinate the company's eligible lines against shared cash/storage; do not buy future-phase stock early or use unavailable future receipts. Specify cross-phase planning and revalidation for multiple-line ownership without changing supply-access timing.

Run reference/compiled differential tests, conservation checks, independent small oracles, checkpoint continuation, and full-population comparisons. Expected changes caused by corrected behavior must be explained rather than hidden by regenerating golden results. The accepted result becomes the corrected comparison baseline; it remains isolated until its own rollout gates pass.

The [ownership-scope audit](buying-behavior-v2-phase-oracle.md#ownership-scope-correction-from-the-authoritative-catalog) verifies that current installations are sector-restricted and unique by product, with no same-sector manufactured-input edge anywhere in the complete catalog. Thus self-supply and duplicate identical-product owned lines are not required current mechanics. Preserve full supported distinct-product multiple-line planning, shared inputs and phase timing. Re-audit this boundary for ownership or catalog amendments.

## Stages 5 and 6 Build a new industrial demand model

The [value-model implementation contract](buying-behavior-v2-value-model.md) now contains executable D3 counterexamples and conditional buffer-value tests; it is not an adopted forecast.

Prepare a model comparison before committing to a formula. Include corrected storage replenishment, an explicitly labeled demand-informed replenishment policy, and a coupled expected-return policy if it survives analytical review. Do not present an inventory target as proof of price-sensitive demand. The [demand-informed target comparator](buying-behavior-v2-value-model.md#implemented-demand-informed-replenishment-comparator) now has an executable reference and side-by-side analytical evidence; its documented failures prevent treating it as the final industrial policy.

For an expected-return candidate, specify a proposed objective in dollars over a declared horizon:

`expected realized sales revenue + terminal inventory value - new input spend - incremental conversion/operating costs - payable fees`

Define every term before implementation. Treat existing purchase costs as sunk for incremental choice while preserving their book basis in COGS and the actual production gate. Prevent double counting between sales revenue and terminal inventory value. Include buying nothing and explain uncertainty in sale quantities and realized prices; the company's own quote is not guaranteed revenue. No parameter values are adopted by this outline.

Test the known owned-input/cheap-complement production-gate counterexample, inventory valuation, cold starts, shutdown/re-entry, and price jumps analytically first. Compare local observations including fallback sales, market-request estimates, and a hybrid under the same action space and objective. Distinguish censored sales from demand; one aggregate price/quantity observation does not identify an entire demand curve. A [bounded multi-quote comparator](buying-behavior-v2-forecast-contract.md#bounded-quote-response-comparator-with-explicit-identification-requirements) now improves the controlled ample-stock price-response case, but retains empty/limited-stock failures and is not an adopted industrial forecast. Its [response-family stress](buying-behavior-v2-forecast-contract.md#response-family-stress-the-bounded-curve-is-not-a-universal-replacement) also finds a steeper-response counterexample, so model adequacy must be checked rather than assuming the fitted family is universally better. A [published quote-validation selector](buying-behavior-v2-forecast-contract.md#published-quote-validation-for-response-selection) now compares the two candidates on withheld historical quote levels with an explicit fold budget. It preserves improvements in the inspected calibration profiles but does not establish held-out suitability or population performance. The [full-population support audit](buying-behavior-v2-forecast-contract.md#full-population-quote-support-audit) finds no structurally supported latest offers in the saved 30-tick startup window, making incomplete-observation modeling a prerequisite to general use. An [executable paired-world counterexample](buying-behavior-v2-forecast-contract.md#identical-censored-histories-can-conceal-different-replenished-demand) further requires explicit assumptions and sensitivity for stock-censored extrapolation: identical full recorded histories can conceal materially different replenished sales. The [closing-decision sensitivity adapter](buying-behavior-v2-forecast-contract.md#purchasing-sensitivity-to-explicit-forecast-alternatives) now measures resulting basket changes and cross-model regret under explicit alternative forecasts; it does not select a prior or risk preference.

An [explicit temporal forecast adapter](buying-behavior-v2-forecast-contract.md#explicit-temporal-coupling-and-observed-information-checks) now connects per-period joint distributions through supplied transition kernels and verifies observed-information timing. It preserves supplied marginals but does not estimate or adopt temporal probabilities; empirical calibration and closed-loop validation remain required. The [temporal-history coverage audit](buying-behavior-v2-forecast-contract.md#temporal-history-coverage-audit-do-not-fit-a-population-kernel-from-pooled-counts) finds sparse and selected zero/positive-state evidence in the existing records; pooled counts cannot be treated as an adopted population transition kernel.

Build an independent general small-market oracle that enumerates split allocations, lots, multiple routes, cash/storage, fees, and incomplete buffers. Establish computational bounds before optimization. Reuse R1 accounting or recorder utilities only where contracts match; do not inherit its one-supplier-per-ingredient restriction or canonical-bid policy implicitly.

The [phase-planner scaling screen](buying-behavior-v2-phase-oracle.md#scaling-screen-oracle-remains-unsuitable-for-population-execution) now demonstrates work-budget failures even for small two-period endogenous-funding cases. Keep that planner as the verification oracle; its cache and feasibility pruning do not establish a scalable candidate. A different continuation search/representation must preserve supported decisions and be checked against the oracle before population integration.

An earlier experimental path adds a [strict ledger-value certificate](buying-behavior-v2-phase-oracle.md#strict-closing-certificates-expand-the-screen-to-28-cases) to compiled closing cost bounds, exact closing memoization, and cost-aware continuation pruning. It completes 28 of 32 cases under the original budgets, including charged proposal work. Four larger two-period cases still reach allocation limits. [Failure diagnostics](buying-behavior-v2-phase-oracle.md#search-limit-diagnostics-locate-the-remaining-scaling-work) now locate the endogenous bottleneck in first-purchase hypothetical basket enumeration and distinguish the frozen controls' interrupted closing solves. An [optional initial-prefix pruning mode](buying-behavior-v2-phase-oracle.md#optional-prefix-pruning-integrated-scaling-limits-remain) now preserves tested policies/accounts and charges bound work explicitly, but the unchanged screen still completes only 28/32. Stronger or cheaper earlier-decision bounds remain necessary. The [shared first-production bound](buying-behavior-v2-phase-oracle.md#shared-first-bound-integrated-with-reserved-work) is now optionally integrated with charged work. Its largest case completes only under an explicitly expanded diagnostic budget (4,908 allocations/41,148 combined units used), so the original screen remains 28/32. [Exact relaxed-profit reuse](buying-behavior-v2-phase-oracle.md#exact-relaxed-profit-reuse-reduces-shared-bound-work) reduces that expanded case to 23,499 combined units with identical full results, but allocations remain 4,908 and both original thresholds are still exceeded. Tested policies and accounts are preserved, but D6 and population suitability remain open.

The earlier [fresh-proof hint reuse and bound ordering](buying-behavior-v2-phase-oracle.md#fresh-proofs-around-reusable-hints-reach-29-of-32-cases) advances this screen to **29/32** under unchanged budgets. The largest endogenous feasible-prefix case now completes at 3,192 allocations/15,281 combined work units with complete policies/accounts matching preserved evidence. Three comparison configurations still reach limits; this is not population validation.

The latest [explicit slot-deficit comparator](buying-behavior-v2-phase-oracle.md#explicit-slot-deficit-comparator-enables-safe-frozen-path-pruning) advances the unchanged screen to **30/32**. Its largest frozen-prefix case matches a complete unpruned callback reference and uses 466 allocations/4,823 combined units. All feasible-prefix rows pass; two exhaustive comparison modes remain limited. The subsequent [two-line shared-input screen](buying-behavior-v2-phase-oracle.md#two-line-shared-input-screen-exposes-closing-search-limits) completes only **9/16** optimized configurations under the same limits; seven fail in closing search. The [joint-line proposal experiment](buying-behavior-v2-phase-oracle.md#joint-line-proposal-experiment-proof-bounds-remain-the-bottleneck) preserves these results but adds work, so it remains opt-in. A [standalone joint-line bound](buying-behavior-v2-phase-oracle.md#standalone-joint-line-closing-bound) now matches the known full-box optimum in small certain-demand fixtures; its [compiled counterpart](buying-behavior-v2-phase-oracle.md#compiled-joint-line-bound-verified-against-the-rational-reference) passes reference comparisons. The [integrated joint proof](buying-behavior-v2-phase-oracle.md#joint-proof-integration-completes-thirteen-of-sixteen-cases) advances the multi-line screen to **13/16** with explicit state/scenario charging under unchanged limits. Optional [exact joint-bound reuse](buying-behavior-v2-phase-oracle.md#exact-joint-bound-reuse-reduces-work-without-clearing-another-limit) reduces work but retains the same 13/16 result. Subsequent [box-specific budgeting](buying-behavior-v2-phase-oracle.md#joint-bound-budgeting-now-uses-the-current-box-and-cache-result) preserves that result without a measured scaling gain. The [multi-line common-first prefix experiment](buying-behavior-v2-phase-oracle.md#joint-first-production-prefix-bound-correct-but-not-a-scaling-improvement) is correct in targeted tests but regresses completion to 12/16, so it remains off; the preferred configuration still completes 13/16. A [cash-relaxed closing reference](buying-behavior-v2-phase-oracle.md#standalone-cash-relaxed-closing-bound-for-future-reuse) now passes targeted ledger checks, preparing reuse across funding cash offsets; its [compiled normalized reuse is now integrated experimentally](buying-behavior-v2-phase-oracle.md#normalized-cash-reuse-integrated-remaining-failure-types-change), preserving 13/16 while changing the remaining failures to prefix, allocation and closing-work limits. Broader calendars and population validation remain open.

The [compiled continuation candidate](buying-behavior-compiled-continuation-plan.md) now connects typed calendars, all ledger transitions, resident state, observation-history grouping, exact action traversal, persistent supply and endogenous continuation-v2 funding. Its [explicit search stack](buying-behavior-compiled-continuation-plan.md#endogenous-continuation-v2-funding-connected) matches small-calendar oracle policies, accounts and detailed funding results. Arena-backed branch sequences, group membership, histories, funding/policy/result records and scalar control fields now use bounded numeric storage. Temporary adapters and control dispatch still use Python; a compiled driver and representative population measurements are still required. These integration results do not establish stage 6 or settle economic adoption.

Compile only a candidate that passes these tests. Verify optimization against an independently captured reference baseline including accounts, forecasts, and deterministic continuation, not timing alone.

The [recorded search-size audit](buying-behavior-recorded-search-geometry.md) now measures actual startup order grids. It confirms that the small continuation screen does not cover recorded offer/quantity ranges; complete pre-purchase state and explicit forecast inputs are required for representative timing.

## Stage 7 Validate economics and performance

Publish a new experiment protocol before evaluation. Existing seeds 137, 271, 811, 1597, and 2027 have already been examined; use them as historical/calibration comparisons and preregister fresh held-out seeds. Do not tune to the new held-out results. Preserve failed candidates and all run manifests.

Preregistered held-out seeds (2026-10-12, before any Stage 7 run): **313, 421, 907, 1543, 2099**. The gate thresholds in the table below are frozen against these seeds. No validation run has been executed under these seeds as of this writing.

Use paired initial states and stable random roles. Compare untouched production, corrected mechanics, and the new industrial candidate so the benefit or harm of mechanics is not attributed to demand forecasting. Run short screening first, a complete generation for surviving candidates across held-out seeds, and at least two generations for the selected candidate and its matched baselines. Extend runs when drift remains unresolved.

Proposed gates retain the prior protocol's thresholds; freeze them in the new protocol before outcomes are inspected. They are research acceptance criteria, not established economic laws.

| Gate | Required evidence |
| --- | --- |
| Algorithm and implementation | Independent oracle agreement over the supported actions; reference/compiled parity; no unresolved counterexample; exact deterministic continuation. |
| Accounting | Per-company per-tick equity residual ≤ $1e−6 + 1e−12 × max absolute opening/closing equity; aggregate money residual ≤ $1e−4 + 1e−12 × total cash. Posted earnings remain independent of equity reconciliation. |
| Goods and feasibility | Exact integral purchases/production and stock decrements; no unsupported cash, stock, or storage violations. Preserve fractional T0 extraction and the protocol amendment's aggregate reduction bound of 32 × spacing(max absolute opening/closing goods). No balancing write-offs. |
| Long-run trade | Held-out final-generation retail units ≥ 90% of the paired comparison baseline; report the untouched baseline too. A degraded corrected baseline must not lower the effective adoption bar. |
| Company and product health | No previously active product permanently loses trade; each route's negative annual-earner share ≤ baseline + 5 percentage points; no price guardrail contacts or unexplained >10% final-two-year price drift with collapsing units. Define persistent zero trade before running. |
| Recovery | Temporary-shock 360-tick trailing trade reaches ≥90% of the same-policy no-shock control within 720 ticks. Report overshoot and distributions. |
| Fairness | Rotate/reverse priority and test stable identities; investigate and resolve route mean shifts >5% and tail shifts >10% in earnings or fulfillment. |
| Performance | Warm observed full-tick median ≤2× baseline and ≤500 ms on the measured host; p95 ≤2.5×; peak memory ≤2× baseline +256 MiB. Compare with both original and corrected baselines to avoid compounded regressions. |

Stress demand increases/collapses, temporary supplier outages, one-time quote shocks, low/asymmetric cash, large fees, empty stock, no history, heterogeneous ownership, and dependency-closed expanded catalogs. Expanded-catalog support requires its own stated observation horizon; short tests do not establish long-run suitability.

Report totals and distributions by T0/T1/T2/T3 and C1–C4, including C4 basic-plus-C3 versus compound-plus-compound routes; include any additional enabled complexity explicitly. Show sold units and posted earnings together, per-company denominators, inventory/turnover, utilization, realized prices, margins from summed accounts, fees, and event counts. Undefined margins remain unavailable.

Benchmark startup, mature states, high fees, and sustained empty-stock conditions without competing simulation workloads. Separate compilation, kernel, recording, projection/encoding, transport, and actual browser rendering. Report seed-level uncertainty; correlated ticks are not independent replications.

## Implementation map

| Area | Expected files and responsibility |
| --- | --- |
| Discovery and affordability | `economy/core/trading.py`; define shared selection/fee primitives after contract approval. |
| Reference and compiled execution | `economy/kernel/tick.py`, `economy/kernel/numba.py`, `economy/kernel/input_market.py`; preserve settlement and phase timing. |
| Configuration and state | `economy/core/config.py`, `economy/core/state.py`, `economy/core/model.py`; initialize/reset/version new state and use stable identities. |
| Financial posting | `economy/core/accounting.py`; inventory capitalization, basis, COGS, and separate fee income/expense. |
| Runtime and persistence | `economy/server/runtime.py`, `economy/server/persistence.py`; policy identity, continuation, compatibility, and explicit migration. |
| Measurements and UI data | `economy/server/recording.py`, `economy/server/aggregates.py`, `economy/server/service.py`, `web/`; consistent labels, denominators, detail traces, and exports. |
| Isolated research | New versioned candidate harness beside `tools/buying_research/`; preserve the archived R1 source and results. |
| Verification | `tests/py/` and `tests/js/`; extend relevant buying, preferences, stock-access, storage, earnings, recording, and performance coverage. |
| Documentation | New approved purchasing contract; update integration rules, relevant canon sections, README, and metric definitions only for adopted behavior. |

## Verification commands and delivery checks

Current integration checkpoint: **663 discovered Python tests pass** in 409.502 seconds (2026-10-12, after the offer-collapse, funded-cap pruning, semantic funding-query dedup and symmetry-break optimizations); three JavaScript test files and `web/app.js` syntax pass. Evidence: `stats/buying-implementation/20261012-captured-symmetry-break/full-discovery.log`. The [scope audit](buying-behavior-scope-audit.md) records the purchasing-only boundary and current model checks. No economic or population-performance gate is inferred.

Historical integration checkpoint (before subsequent solver work): all 400 discovered Python tests (305 buying and 95 non-buying) and the three JavaScript test files pass; `web/app.js` passes syntax checking. See `stats/buying-implementation/20261012-buying-suite-integration/` for source identity and logs. These checks do not establish the economic or performance gates above.

Historical integration checkpoint: **469 tests passed in full Python discovery**, plus the three JavaScript test files and `web/app.js` syntax check. `stats/buying-implementation/20261012-current-suite-audit/` preserves commands, logs and 217 unchanged source hashes. No population-performance or economic gate is inferred from this result.

Use the compatible interpreter selected by `run.sh`; inspect dependencies before changing them. Relevant commands include:

```sh
./run.sh test
PYTHONPATH=.pydeps:.:tests/py "$ECONOMY_PY" -m unittest test_buying_fallback test_distributor_preferences test_production_stock_access test_net_earnings test_recording
PYTHONPATH=.pydeps:.:tests/py "$ECONOMY_PY" -m unittest discover -s tests/py -p 'test_*.py'
node --check web/app.js
node tests/js/test_formatting.js
node tests/js/test_profitability.js
```

Set `ECONOMY_PY` to the launcher's inspected compatible interpreter before the direct commands. Add the new contract/oracle test modules as they are implemented. The launcher is a curated subset; full discovery is separate. For behavior-preserving optimizations, use `./run.sh bench --verify` against a fresh independently captured baseline. For intentional behavior changes, validate expected differences instead of requiring identical economic state.

Inspect the served dashboard using actual candidate data on an isolated service. Verify assets, tier/complexity grouping, sorting, totals, missing values, units, per-company denominators, and agreement with recorded accounts. Do not add rows backed by placeholders.

## Stage 8 Integration and rollout

Package each accepted milestone with exact code/configuration/catalog identity, supported ownership, protocol results, known limitations, warm timing, and a reviewed diff. Update production documentation to the selected contract without rewriting the rejected R1 history.

Persist policy and measurement versions and all forecast/sampling state needed for exact continuation. Inspect the then-current checkpoint schema before choosing a new version. Either provide and test an explicit migration with stated initialization or reject incompatible checkpoints clearly. Never silently synthesize missing history or reinterpret a checkpoint under a new policy.

Prepare a rollback bundle containing the previous executable/configuration, pre-transition checkpoint, and recording locations. Rollback restores a compatible checkpoint into the previous engine; toggling a flag on a state already evolved by a different policy is not equivalent. Retain the intervening recording and state as evidence.

Before live adoption, present the exact artifact, validation result, transition method, and rollback consequences for the user's final green light, as required by the research brief. Verify the target process and save evidence before any authorized restart. Observe an initial rollout window with the same invariant/metric definitions and explicit stop conditions for conservation failures, incompatible state, or unvalidated behavior.

## Completion criteria

The mechanics milestone is complete when its approved contract is implemented across both engines and supported ownership, the corrected baseline passes its gates, and persistence, recordings, UI, and documentation agree. It can be delivered independently of the industrial replacement.

The industrial milestone is complete only when the declared full action space, economic model, implementation, performance, and long-run adoption gates all pass. A rejected candidate is a completed experiment, not a completed replacement. If no candidate passes, retain the validated baseline and report the failed hypotheses and remaining decisions.

Implementation is active; use the progress record to locate completed stages and current evidence. Baseline capture and the D1–D2 decisions are complete. Production adoption still requires the gates and final live-transition decision above.
