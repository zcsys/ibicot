# Phase-accurate continuation ledger and small oracle

Status: experimental contract implementation, not a production policy. This extends the earlier delayed-receipt counterexamples with explicit phase-book receipts, original-incumbent fees, historical inventory basis, production overhead, rent liabilities and non-anticipating decisions. It is one component of the [value-model plan](buying-behavior-v2-value-model.md); endogenous funding now has an explicit candidate; its strategic validation and population-scale execution remain open.

## Execution and information

`phase_ledger.py` applies immutable small-company events. `phase_oracle.py` enumerates all feasible supplier allocations at each purchasing event, including no purchase, partial suppliers, split allocations, wholesale lots and unmatched buffers. Shared cash, inputs, storage and installed production order remain binding. The node limit fails explicitly; it never substitutes a heuristic result.

| Event | Available information and effect |
| --- | --- |
| Open sales book | Freeze the company's offered finished stock, cost basis and posted quotes at phase entry. |
| Purchase/produce | Observe current sampled offers and own current resources. Pay actual goods/fees; capitalize inputs; run the retained production gate in installed-line order. |
| Change quotes | Change subsequent quotes; an already open book retains its original quotes. |
| Settle sales book | Sell at most the frozen opening stock, remove its original basis, and release actual sales/fee receipts. Newly produced goods stay outside that book. |
| Bill rent | Compute current book equity, assess an eligible bill, collect available cash and retain unpaid debt. |
| End tick | Update switching-net-income EMA from actual transfers and clear tick/phase counters. Forecast income is never deposited into cash. |

A retail book settles before manufacturing, so those receipts can finance manufacturing. A manufacturing input book settles after that complexity's buying/production, so its receipts cannot finance earlier purchases in that same phase. The next complexity's book may contain the new output. Refineries manufacture before those input sales phases. Callers must build the real calendar; event labels identify purchasing phases within a tick. Reopening a completed company purchasing phase is rejected, preventing a second product-order fee. A tick cannot end with an unsettled book. Billing twice or trading after rent within the same tick is rejected; an explicit tick-end transition reopens the next tick.

The planner groups branches by the currently observable company state, current offers and remembered observable history, then selects one common action for that group. Future demand, scenario labels and terminal-value tables do not enter that information key. After an actual receipt or supply observation differs, later actions may differ. Identical supply states with different hidden demand retain a common decision. Canonical supplier order prevents a scenario's enumeration order from acting as information. Calendar/label mismatches are rejected.

## Funding boundary

The original callback mode requires an explicit funding function, which receives only current own state, technology and currently observed offers. The new `funding='continuation'` mode instead derives joint intentions inside the conditional event tree; see the [continuation-funding contract](buying-behavior-v2-continuation-funding.md). Externally supplied funded-demand vectors are erased before the function runs, preventing a scenario writer from encoding hidden future demand in them. Results are cached by observable inputs. Accepted D1/D2 are then applied to the returned whole-lot quantities: original-incumbent availability is frozen, any qualifying outside purchase incurs at most one fee, and one supplier alone must deliver the whole funded demand to change preference.

The callback fixtures remain exact conditional on their supplied funding rules and scenarios. They do not by themselves prove a joint expected-return model. The new continuation mode has separate coupled-funding tests and a documented fee-avoidance counterexample. Its own-quote queries keep other inputs flexible, reserve physical/financial resources, and retain future information constraints; this remains a candidate, not an adopted world policy.

## Financial meaning

Purchasing inputs exchanges cash for inventory. Conversion adds cost to finished inventory. Neither is automatically posted as immediate operating loss. Sales recognize original book COGS. Posted earnings are sales minus COGS, plus switching income, minus switching expense and current rent expense. Every event checks this independently against its equity change; earnings are never defined from that residual.

The retained gate uses the company's current inventory basis and conversion cost. It receives allocated forecast overhead, not an extra cash debit. T1 snapshots overhead at production entry after procurement; combined T2 snapshots it before that phase's procurement. This matches the executed Python/compiled code and canon. A misleading helper docstring saying both were before procurement was corrected without changing behavior. Later trading can change actual billing eligibility.

Actual rent uses pre-charge equity including inventory, fixed book assets and arrears. Equity at the threshold is eligible. Below the threshold, both new billing and old-debt collection are suspended; debt remains. At zero new rent rate, eligible companies still repay old arrears. Bills are not proportional to occupied stock. Forecast gate overhead is not billed a second time, and debt repayments are not new expenses.

At the horizon, the candidate score is:

`closing cash − opening cash − (closing arrears − opening arrears) + explicit terminal inventory values`.

The liability adjustment prevents unpaid rent from becoming free value. Paying old arrears reduces liquidity during the plan but is not charged twice as a new expense. Terminal tables are explicit assumptions, not booked earnings or guaranteed future receipts. Initial inventory costs remain sunk for incremental choices while their historical basis stays in the gate and accounts. Existing assets' terminal values also enter the no-purchase comparison; the score must not be presented as financial net profit.

## Executable evidence

`phase-continuation-examples-v2.json` records complete small fixture inputs, transitions and source hashes. Tests include:

- Selling frozen old inventory while retaining new output and its correct remaining basis/quote; the ledger also matches an actual `InputMarket.settle()` example with production between opening and settlement.
- Deferred versus prior retail receipts, conversion liquidity and installed multiline order.
- Split completion retaining the incumbent, one fee, whole-demand reassignment, next-order fee recipients and wholesale stockout waivers.
- Threshold crossing between gate and billing, unpaid rent, suspended collection, old debt and zero-rate collection; nine rent boundary cases also match the executed kernel.
- Hidden demand: a $3 input plus $0.25 conversion and a 50% chance of a $4 sale produces no purchase. Optimizing each hidden outcome separately would falsely report an expected $0.375 gain.
- Complement buffers: with $11 cash, A at $1 now and B at $4 later, two A can support four outputs and $1 realized return if B arrives. At 50% arrival the common initial action is no purchase; at 75% it buys two A for expected return $0.25.
- An optimal A2+B6 split remains in the action space and retains the old preference; hidden labels, externally supplied bids, supplier ordering and node-limit failures cannot silently change that contract.

## Remaining scope

The event tree models one company against explicitly supplied external supply/sales scenarios. It is not an entire-world replay, endogenous market forecast, or compiled planner. The scenario generator must address correlation, price response, residual supplier stock after this company's orders, ownership changes and future configuration changes before those behaviors are claimed. Self-supply is excluded by the audited current ownership/catalog combination, as documented below; a future amendment could reopen it. The ledger supports fixed installed multiline ownership and fixed physical technology during its horizon; equipment changes are not silently inferred.

Next work is evaluation of the joint funding candidate and its exposed fee incentive, controlled information-model comparisons, and a scalable solver checked against this oracle. World-state/checkpoint/UI integration, fair-market behavior, held-out generations, stress recovery and performance gates remain required. Production defaults are unchanged.

Final evidence: `phase-continuation-final-regressions.log` passes 38 targeted tests in 3.209 seconds; `phase-ledger-book-parity.log` passes the additional actual input-book settlement comparison. The earlier example report remains preserved; v2 adds explicit tick boundaries to the rent/collection example and uses the strengthened phase/billing guards.

## Shared demand across owned lines

`SharedSettleBook` is an explicit scenario event for interchangeable output lines sharing a residual sales opportunity. Existing `SettleBook` retains independent per-line demand; historical scenarios are unchanged. The new event must partition every installed line into exactly one nonempty product group. Scenario authors supply each line's whole demand at its frozen book quote. Equal quotes require equal whole demand; demand cannot increase with the quote within a group.

Within each group, settlement processes ascending frozen quote, then installed line index. For line i:

`remaining_i = max(0, demand_at_quote_i − previous_group_sales)`

`sold_i = min(frozen_opening_stock_i, remaining_i)`

Each group has its own cumulative sales. Later quote changes and newly produced stock cannot enter the frozen book. Goods, cash, original-basis COGS and separate fee income use the same reconciled settlement as independent sales. Trace output includes whole quote demands, groups and actual group sales. The transfer-neutral funding counterfactual removes fee income from this event as it does for ordinary settlement; actual accounts still post it.

This is a supplied residual-demand allocation assumption. It is not a reconstruction of the world's buyer search, individual loyalty, rival suppliers or price response, and line-index priority is not an adopted fairness rule. Product identities and grouping come from the scenario author; the small ledger cannot infer interchangeability from recipe names. Separate product groups do not imply statistical independence: their demands must be supplied together in the scenario, with explicit probabilities. Shared demand outcomes remain hidden until settlement, so current purchasing cannot condition on future realized demand.

The `shared_sales_report` counterexample has two one-output routes, each requiring a $1 input plus $0.25 conversion and selling at $3. Independent one-unit opportunities justify buying both inputs for $3.50 return. A shared one-unit opportunity justifies only one input for $1.75 return. With one existing finished item, the shared event sells that item and the planner purchases neither input. An additional hidden-demand test rejects purchases under a 50% zero-demand/50% two-unit-demand scenario at a $2 quote, even though known high demand would justify production.

Evidence: `stats/buying-implementation/20261012-shared-sales/` preserves before-edit source, 44 passing ledger/oracle/funding regressions and complete example inputs, results and source hashes. The archived report package reproduces byte-identical results outside the repository. Tests also cover A2+B6 quote fallback, frozen prices, old inventory basis, partitions, inconsistent quote demands, separate groups and fee-neutral counterfactuals. The report command is `python -m tools.buying_v2.shared_sales_report --output <fresh-directory>`.

This closes the independent-line-sales limitation for explicitly supplied shared-demand scenarios only. A calibrated joint forecast/scenario generator, scalable planning and world integration remain open. Conditional own-purchase depletion is implemented below. The ownership audit below classifies same-product owned-line competition and self-supply as hypothetical extensions under current rules.

## Persistent supplier inventory and explicit arrivals

The oracle now accepts `supply="persistent-arrivals"`. Each offer's stock field means cumulative initial supplier stock plus external arrivals by that decision, before this company's purchases. Totals must be nonnegative whole integers and nondecreasing for each `(material, supplier)` identity within a scenario. An absent offer does not reset its stock history. Duplicate supplier/material offers are rejected. This mode supports arrivals but does not model outside buyers' withdrawals or supplier production conditional on this company's payments.

After an actual allocation, the oracle subtracts the purchased units from all later appearances of that supplier/material. Consequently later discovery, funded-intention calculations, D2 availability, allocation and fees see the remaining physical stock. Scenarios and caller inputs are immutable; each candidate action receives its own updated continuation. The scenario's future arrivals are not added to current observations. Branches can respond to different supply only when it becomes observable.

Funding queries intentionally relax current supplier stock. Define that relaxation explicitly as additional current hypothetical stock, consumed by the hypothetical purchase; it does not bring future arrivals forward. Only `min(hypothetical purchase, real observed stock)` is deducted from later stock totals. This avoids both reusing real inventory and erasing a separately declared future arrival because of a fictitious current unit. Current hypothetical preference/fee rules remain as documented in the continuation-funding contract.

The default `supply="independent-snapshots"` retains legacy scenarios in which each purchase event supplies its own availability snapshot. Those snapshots are not evidence of persistent stock conservation. New world scenario generators must declare their supply interpretation; a series of unchanged snapshots cannot be called a no-replenishment path after purchases. The result reports `supplyMode`, and persistent purchase traces include observed remaining stocks.

A two-phase example has one input available initially, input price $1, conversion $0.25, and output selling at $3 early or $2 later. Repeated independent one-item snapshots allow two purchases for $2.50 total return. Persistent stock with no arrivals allows only one purchase, optimally early, for $1.75. Declaring one later arrival restores two purchases/$2.50. Another test shows that a consumed original incumbent has zero remaining availability next phase and correctly receives no D2 fee when an outsider then delivers.

Evidence in `stats/buying-implementation/20261012-persistent-supply` includes before-edit oracle source, 36 passing targeted tests and a self-contained example archive with full scenarios/results/hashes. The archived package reproduces byte-identical results outside the repository. Tests include 18 independently enumerated two-action cases, uncertain future arrivals, immutable inputs, declining-total rejection and stock-relaxed funding. Reproduce examples with `python -m tools.buying_v2.persistent_supply_report --output <fresh-directory>`.

This implements conditional depletion from the focal company's own purchases under supplied arrivals. Outside withdrawals, endogenous supplier responses and a calibrated scenario generator remain required before whole-world supply behavior is claimed. Self-supply would require a changed ownership/catalog combination; see the audit below. No production policy or economic parameter is adopted by this extension.

## Ownership-scope correction from the authoritative catalog

The earlier open-work notes assumed that a company could consume its own manufactured output or install two lines producing the same product. Those assumptions do not describe the supported current model. `economy/core/state.py:add_tier2_line` permits only products in the company's sector and at or below its capability, and rejects a product already installed by that company. Valid multiple-line ownership remains supported for distinct eligible products.

`ownership_audit.py` examines stable ingredient identities in the authoritative complete catalog and current selection. The 269-product universe includes 255 manufactured recipes and 160 manufactured-input edges; the 105 currently selected manufactured recipes contain 14 such edges. **None of the 160 edges connects products in the same sector.** Therefore a company restricted to one sector cannot own both a manufactured output and a route consuming it, even if all dependency-closed recipes in this universe are enabled. This is an exhaustive fact about this catalog, not a rule inferred from a small population or one run.

Three tests verify the catalog result, show the audit detects a changed same-sector edge, and exercise the actual installation API. A company cannot install its required cross-sector input line or duplicate its own product, while a valid distinct same-sector installation succeeds. The runtime selection agrees with the catalog selection. Results, source/catalog hashes, tests and an exact out-of-repository replay are preserved in `stats/buying-implementation/20261012-ownership-scope/`.

Consequences for implementation scope:

- Do not add internal transfer accounting or self-supplier planning solely to satisfy the earlier assistant-generated open-work list. The current catalog/ownership combination excludes those transactions from supported ownership.
- `SharedSettleBook` remains an explicit hypothetical scenario tool. Two identical-product output lines within one company are not a current supported installation case; that example is not evidence of a current-engine demand-duplication defect.
- Preserve coupled planning for distinct owned products, shared/repeated inputs, common cash/storage, installed execution order and correlated future demand. The ownership finding does not remove any of these requirements.
- Re-run the audit if sector assignment, recipe universe, cross-sector ownership or duplicate-line rules change. It does not establish behavior for arbitrary imported catalogs or manually invalid ownership arrays.

This corrects an unsupported assumption in prior research notes; it does not narrow the master plan's requirement to handle all supported multiple-line companies. No ownership rule, catalog, production mechanic or live state was changed.

## Remembered information after current states converge

A verification counterexample exposed missing information in the original grouping rule. Two paths can have identical current cash, inventory, quotes and cumulative accounts after different observed sales sequences. If sale timing predicts future demand in the supplied scenario distribution, the company may condition its next purchase on that remembered observation. Grouping solely by current state and current offers incorrectly discards this legitimate information.

The oracle now retains an explicit observable-history key. It includes inspected purchase offers and terms, chosen allocations, and realized own transactions, production, quotes, books and accounts. It excludes scenario labels beyond the shared validated calendar, terminal value tables, funding diagnostic continuation values, and unobserved whole-demand inputs to settlement. In particular, `SharedSettleBook.quoteDemands` are not treated as observed demand when the company had no stock. Distinct hidden demands producing the same observable history still share one current action.

Worked case: a company starts with one finished item and sells it for $2 either early or later. Both paths then have the same $12 cash and empty stock. Early sale predicts a subsequent one-item demand; later sale predicts none. A new item costs $1 input plus $0.25 conversion and sells for $2. Remembering the signal supports buying only after the early sale: expected incremental cash return is `$2 + 0.5 × ($2 − $1 − $0.25) = $2.375`. The old grouping merged the paths and returned $2, buying in neither. A second regression remembers an inspected quote even when no purchase occurred. A third verifies that unseen demand at an empty-stock book, including the shared-demand event, cannot become a signal.

Evidence is in `20261012-combined-v2-verification`. All 161 existing tests in 27 buying-v2 modules passed before this additional counterexample revealed the coverage gap. After the fix, 53 relevant history/oracle/ledger/funding/shared-sales/persistent-supply tests pass in 2.940 seconds; the pre-fix combined run is not presented as a post-fix full-suite result. Original source and the $2 result are preserved. The isolated archived corrected source reproduces the $2.375 result byte-identically outside the repository.

This corrects the small planner's information contract. It does not supply a calibrated predictive relationship between sales timing and future demand, nor does it select a world forecast. Such correlations remain explicit scenario assumptions requiring separate empirical validation.

## Bounded reuse of pure ledger transitions

The small event-tree oracle now accepts `transition_cache_size` (default 4,096 entries; zero disables reuse). Each solve owns its cache. Keys include the entire immutable company state, event and allocation; company structure is fixed for that solve. Cached entries contain only the pure ledger transition or one of the two recognized allocation-infeasibility results. Unexpected validation errors are never swallowed. FIFO eviction keeps entry count bounded, and returned trace-detail mappings are copied so callers cannot mutate a cached detail through a leaf.

This does **not** cache optimal actions, continuation values, posterior groups or observable histories. In particular, the previously corrected sales-timing information groups remain separate even when their current balances converge. Persistent supplier arrivals still update each scenario outside the transition cache, and fee-neutral funding remains distinguished by its event/state inputs. Enumeration node counting and explicit failure budgets are unchanged; reuse cannot silently allow an otherwise over-budget solve.

Fifty-five relevant tests pass in 2.378 seconds, including information history, continuation funding, persistent supply, shared sales, transfer-neutral funding and ledger/oracle regressions. Cache-specific tests compare complete outputs (excluding the new cache statistics) with reuse disabled, capacities 1/16/4,096, and unchanged node-limit failure. A subsequent stronger trace-aliasing check passes in the two cache-specific tests (0.143 seconds).

`stats/buying-implementation/20261012-transition-cache/` preserves the independently captured pre-edit package and hashes, final source, tests, comparison script and measurements. Six analytical workload/mode combinations each have one warm-up and six alternating-order measured repetitions. Complete serialized decisions, traces, accounts, values and enumeration counts match the archived oracle exactly; only cache diagnostics are new.

| Fixture | Funding mode | Before median ms | Cached median ms |
| --- | --- | ---: | ---: |
| Small fee case | Continuation | 13.495 | 8.678 |
| Small fee case | Transfer-neutral | 11.432 | 8.467 |
| Larger fee case | Continuation | 14.092 | 10.681 |
| Larger fee case | Transfer-neutral | 14.215 | 9.532 |
| Uncertain fee income | Continuation | 6.364 | 4.078 |
| Uncertain fee income | Transfer-neutral | 3.828 | 2.430 |

Observed median reductions are 24.2–36.5%; these small cases use 33–134 cache entries. Capacity bounds entries, not bytes, and larger states can occupy more memory per entry. This improves the independent oracle and its future optimization comparisons; it does not remove exponential scenario/allocation growth, compile the planner, or establish population-scale performance. No production purchasing or live service changed.

## Optional exact prefix pruning

`solve(..., allocation_search='feasible-prefix')` now replaces the Cartesian allocation traversal with a lexicographic prefix generator. The default remains `exhaustive`, preserving the independent full-enumeration comparison. `feasible_prefix.py` eliminates only allocation subtrees whose already selected positive-price goods exceed current cash or whose accumulated material purchases exceed the remaining installed input slot. Existing over-slot inventory admits no additional purchases, consistent with the ledger.

Goods are accumulated in the same offer order with the same arithmetic as the ledger. Positive prices make later purchases unable to repair an over-budget prefix. Quantities and slots are integral; slot clipping is exact. The generator preserves the relative order of every retained allocation, which matters for the existing tolerance-based tie rule. It does not use an assumed future value, production output, fee waiver or preference outcome to prune. All remaining allocation/fee/space/production/continuation checks still run through the ordinary ledger and planner. The all-zero candidate reaches normal ledger validation before later branches, retaining rejection of malformed events.

The existing allocation-node budget counts retained candidate evaluations in this mode, so it is intentionally different from exhaustive enumeration cost. A separate positive `max_prefix_nodes` budget (default 100,000) bounds visited prefix work across the solve, including funding queries. Exhaustion raises explicitly and returns no approximate plan. The result reports search mode, visited prefixes, pruned Cartesian leaves and retained allocation evaluations. Cache capacities remain separate limits.

Twenty-three targeted tests pass in 0.390 seconds. Four hundred independently generated markets compare the generator against a Cartesian filter for exact feasible-allocation order and complete pruned-leaf counts. Planner comparisons cover endogenous and transfer-neutral funding, remembered sales signals, persistent supply and explicit prefix failure. Existing cache, information-history, phase-oracle and persistent-supply tests also pass.

A four-offer scarce-cash fixture illustrates the potential without claiming representative speed. Four suppliers each offer ten input units at prices $2/$3/$4/$5; the company has $3 and a ten-unit slot. Both modes return the same full decisions, traces, accounts and $5.75 value. Exhaustive search evaluates 14,641 allocations. Prefix search visits 20 prefixes, eliminates 14,638 leaves and evaluates three allocations. After one warm-up, three alternating-order repetitions have median runtimes 484.773 ms versus 0.713 ms. This deliberately constrained analytical case is not a population benchmark; affordable baskets, multiple stages and uncertain outcomes can still grow exponentially.

`stats/buying-implementation/20261012-prefix-search/` preserves the pre-edit oracle/hash, source archive, seeded verification tests and benchmark script/results. No production policy or live run changed. This is an optional exact search improvement, not adoption of a forecast, resolution of D4 funding incentives, or completion of the full scalable planner.

## Scaling screen: oracle remains unsuitable for population execution

`benchmark_phase_search.py` supplies complete reproducible cases that increase per-input capacity, supplier choices, periods and hidden sales outcomes. The frozen specification `stats/buying-implementation/phase-scaling-spec-20261012.json` sets 4,000 retained allocation nodes and 16,000 visited prefixes. It compares exhaustive and prefix search under both externally frozen caps and endogenous continuation funding. Limits report failure without returning an approximate allocation.

Every fixture has two complementary inputs, one line, prices $2/$3/$4 as suppliers are added, $0.50 conversion and a $10 output quote. Cash is deliberately ample. Fees, rent and terminal values are zero, supply is an independent snapshot each period, and the two-outcome cases have perfectly correlated zero/full demand across periods. No forecast is estimated. These conditions isolate algorithm growth; they are not a calibrated or representative company population.

| Capacity per input | Suppliers per input | Periods / outcomes | Funding | Exhaustive | Prefix |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 / 1 | Continuation | Exact: 8 nodes, 1.24 ms | Exact: 8 nodes, 1.24 ms |
| 2 | 2 | 1 / 1 | Continuation | Exact: 270 nodes, 21.48 ms | Exact: 144 nodes, 18.64 ms |
| 4 | 2 | 1 / 1 | Continuation | Exact: 1,750 nodes, 114.03 ms | Exact: 750 nodes, 90.95 ms |
| 8 | 3 | 1 / 1 | Continuation | Limit | Limit |
| 1 | 1 | 2 / 2 | Continuation | Exact: 72 nodes, 11.84 ms | Exact: 72 nodes, 10.77 ms |
| 2 | 2 | 2 / 2 | Frozen caps | Exact: 3,330 nodes, 363.60 ms | Exact: 1,548 nodes, 308.74 ms |
| 2 | 2 | 2 / 2 | Continuation | Limit | Limit |
| 4 | 2 | 2 / 2 | Continuation | Limit | Limit |
| 8 | 3 | 2 / 2 | Continuation | Limit | Limit |

Times are single screening observations, not repeated paired performance estimates. The complete output has 32 rows: 18 exact and 14 work-limit failures. Where both searches finish, their complete semantic results match. Prefix pruning reduces some counts but cannot remove growth among affordable baskets and nested future-funding queries. A limit row proves failure within the stated budget, not impossibility of exact solution by another algorithm.

Two new analytical tests pass (0.026 seconds). Certain two-period capacity-one trade returns $11, while equally likely all-zero/all-one demand returns $3.25 under both funding modes. The first purchase is the same across hidden outcomes; later purchases respond to observed sales. These cases verify the constructed timing and uncertainty rather than merely checking a benchmark status field.

`20261012-phase-scaling` preserves every company/state/scenario input, rows, frozen specification and source hashes. The archived six-file package runs outside the repository using only its own source and the standard library. `20261012-phase-scaling-replay` reproduces all 32 semantic rows and all case inputs exactly, excluding measured durations. No economic or runtime limits were changed to force completion.

Implementation consequence: retain the exhaustive/prefix planner as a correctness oracle. Do not promote it as a population candidate or spend further optimization effort on cache/pruning microbenchmarks as if they close stage 6. The next scalable implementation needs a structurally different search or compiled continuation representation with admissible value bounds, verified against this oracle. Any approximation must be explicitly proposed with measured decision/value gaps and supported ownership scope; silently dropping future decisions, splits, buffers or uncertainty is not an acceptable substitute. Forecast suitability and the unresolved funding incentive remain independent gates.

## Optional reuse of complete conditional funding queries

`funding_memo_size` adds bounded per-solve reuse of **complete optimized funding-query answers**, distinct from pure ledger-transition caching. It defaults to zero: exhaustive oracle behavior remains the reference. A nonzero capacity creates a FIFO table keyed by event index, complete current state, hypothetical offer/funding event, effective fee-neutral mode, and the ordered weighted distribution of all remaining events and terminal values. Current physical offers are included because persistent-stock counterfactuals distinguish real stock from hypothetical added supply.

A purchase information group already has one common observed-history projection. That common past prefix cannot split future branches within the group. Therefore two queries with equal complete state and equal weighted remaining futures define the same conditional optimization even if their common historical prefixes differ. A current-state-only key is not sufficient and is not used: the tests retain different decisions after identical balances but different predictive sales histories. Absolute weights and ordering are retained rather than normalized/canonicalized, making reuse conservative and preserving the existing arithmetic. Company structure, original horizon state and funding mode are fixed within each solve.

The memo stores only quantities, goods payment and conditional value, after a query finishes exactly. It does not cache or transplant output traces, partial-search results or actual preference changes. Returned answer dictionaries are copied. FIFO eviction bounds entry count, not byte size. Diagnostics report hits/misses/peak entries; skipped subproblems reduce actual enumeration and funding-query counts, so work counters intentionally differ while decisions/accounts/traces must match. Explicit work limits still fail without an approximate plan.

Thirty-seven targeted tests pass in 13.887 seconds. They include full policy/trace comparisons at capacities 1 and 4,096, endogenous and transfer-neutral funding, repeated physical stock and future arrivals, remembered predictive histories, observable-state convergence, invalid capacities and explicit work-limit failures. The no-memo and memoized paths agree on full semantic outputs in those cases.

The original bounded 32-case scaling screen was rerun with capacity 4,096 and unchanged 4,000 allocation/16,000 prefix budgets. It still finishes 18 rows and limits 14. Every completion status, completed value and initial allocation matches the original screen. For one period there is no repeated future work to share; the tiny two-period one-supplier case saves only four allocation evaluations. Thus this feature does not close the scalability gate.

An explicitly separate expanded-budget diagnostic runs the previously failing capacity-two/two-supplier/two-period uncertain-demand case to completion. Without memoization it evaluates 19,848 allocations and 995 funding queries; with memoization it evaluates 11,148 allocations and 410 queries, reusing 585 results. Both return $6.50 expected value, with complete trace parity independently covered by the tests. Single observed durations are 2,245 versus 1,208 ms; these are diagnostic timings, not a population or paired performance claim. Raising the diagnostic budget does not change the original failed gate.

`20261012-funding-dag` preserves the pre-edit oracle, final source hashes, tests, expanded-budget result and screen verification. `20261012-phase-scaling-memo` preserves complete screen inputs, archived executable source and outputs. The implementation demonstrates valid sharing of conditional subproblems but remains optional research infrastructure. It does not supply an admissible continuation-value bound, compiled population execution, calibrated forecasts or resolution of D4 incentives. Further progress must reduce search over distinct affordable states, not merely increase these budgets.

## First optimistic continuation-value envelope

`continuation_bound.upper_value` provides a separately tested envelope for a supplied remaining calendar. It is **not yet connected to search pruning**. This separation keeps an unproven pruning integration from changing the exhaustive verification oracle.

For a valid ledger continuation, it bounds return by current cash minus current arrears, relative to the initial cash/arrears boundary, plus optimistic future gross sales and explicit fee income, plus maximum terminal inventory values. All future purchasing, conversion, switching expense and rent costs are relaxed to zero. Paying old arrears does not increase cash minus arrears; new rent can only reduce it. Thus the bound does not incorrectly credit existing debt as extra income.

Potential finished quantity starts at actual current stock. Each future purchase/production event can add the line's full batch capacity with free inputs and conversion, capped at its finished capacity. The envelope deliberately does not subtract previous sales from that potential stock: doing so greedily at today's low quote could underestimate a later high-quote opportunity. Each future `OpenBook` freezes that optimistic quantity and then-current quote. A book already open uses its actual frozen quantities and quotes, so new production or a subsequent price increase cannot inflate that book's receipts. Shared-demand competition is relaxed to independent per-line sales caps, which can only increase the revenue ceiling for valid shared-demand scenarios.

For terminal inputs, use the maximum table value over zero through the larger of current holdings and installed slots. For finished stock, use the maximum over its full capacity. This handles nonmonotone terminal tables and intentionally permits revenue/terminal double counting in the **upper bound only**, never in the decision objective. Missing table coverage, unsupported event types or detected malformed boundary data produce infinity, which cannot justify pruning. This helper is not a complete scenario validator: a search integration must retain validation of all legal event and offer contracts rather than use a finite envelope to hide invalid input.

A conservative magnitude/event-count numerical cushion is added. Tests establish the envelope on the covered cases; they are not a general floating-point certification. Overflow/unusable envelopes must remain non-pruning cases. Tightening this cushion or enabling pruning requires independent comparison of full decisions and explicit numerical-boundary tests.

Eleven targeted envelope/scaling/history tests pass in 0.419 seconds. Every feasible first basket in a two-period, two-input, two-supplier fixture is followed by an independent exact continuation solve and remains below its envelope. Other tests cover frozen books, new quotes/production, fee income and fee-neutral treatment, old arrears, nonmonotone terminal values and unavailable bounds. Complete examples show the current looseness: certain one-period return $5.50 has a roughly $10 bound; correlated two-period return $3.25 also has a roughly $10 bound. Fees and uncertain-income examples remain bounded as well.

`stats/buying-implementation/20261012-continuation-bound/` preserves source hashes/archive, test logs, complete example inputs and byte-identical example replay. The envelope is an implementation primitive for a future bounded continuation solver, not a scalable solver, certified pruning gate or production change. The next work is validation-preserving integration, numerical boundary coverage and measurement of actual branch elimination on the failed scaling cases. A loose bound may prove safe but insufficiently useful; preserve that failure if observed.

## Shadow audit measures bound safety and useful depth

`solve(..., audit_continuation_bound=True)` evaluates the envelope after each feasible procurement/production allocation, then still executes the complete exact continuation. It asserts that the probability-weighted conditional envelope is never below the exact conditional result. It records checked/unavailable envelopes, minimum/maximum slack, candidates that would fall strictly below the best previously completed alternative, and how many such candidates still have another purchase ahead. The audit does not prune or change tie handling. It defaults off.

Comparisons occur inside the same conditional information group and use the same neutral-fee mode and persistent-supply-adjusted future as the exact solve. Thus a bound for one posterior or undepleted supplier book is not applied to a different branch. The hypothetical funding searches are audited too. Potential-cut counts are diagnostic candidate counts, not independent subtrees or a projected runtime saving.

Thirteen targeted audit/envelope/funding-memo tests pass in 12.368 seconds. Complete outputs and existing work counters match with the audit enabled/disabled, excluding only the new audit counters. Coverage includes ordinary and transfer-neutral funding, both supply models, fees, rent/arrears examples and monetary scales 1e−8/1/1e8. No tested envelope fell below its exact continuation value. These tests provide covered-case evidence, not a universal numerical proof.

| Case and funding | Checked continuations | Potential cuts | Cuts with future purchasing |
| --- | ---: | ---: | ---: |
| Small two-period, ordinary | 62 | 20 | 0 |
| Small two-period, transfer-neutral | 62 | 20 | 0 |
| Larger two-period, ordinary | 8,824 | 6,329 | 5 |
| Larger two-period, transfer-neutral | 8,824 | 6,329 | 5 |
| Fee fixture, ordinary | 54 | 8 | 0 |
| Fee fixture, transfer-neutral | 51 | 7 | 1 |
| Uncertain income, ordinary | 24 | 2 | 0 |
| Uncertain income, transfer-neutral | 14 | 3 | 0 |

The larger fixture is capacity two, two suppliers per input and two correlated demand outcomes over two periods, using prefix search and 4,096 funding memo entries. Diagnostic budgets of 100,000 allocations/400,000 prefixes allow it to complete for comparison; the earlier tighter scaling gate remains failed. Minimum observed slack is positive (at least about $8e−9), while maximum slack reaches about $10 in the fee fixture.

The distinction between late and early cuts changes the next implementation priority. Although the gross-receipt envelope would reject many terminal candidates, very few rejected candidates avoid another purchasing optimization. Relaxing all future input/conversion costs is too loose at the expensive early decisions. The next bound should incorporate a conservative minimum cost of future production and avoid treating existing finished inventory as repeatedly free across sales phases, while preserving book timing and valid information. Enable actual pruning only after validation-preserving integration and further exact comparisons; do not infer a scalability pass from the large potential-cut count.

`stats/buying-implementation/20261012-bound-audit/` preserves pre-edit oracle source, final source hashes/archive, tests, complete input/result reports and byte-identical replay. All launched checks completed. The audit changes research diagnostics only; production and live state remain unchanged.

## Cost-aware envelope improves early-decision discrimination

`upper_value(..., include_costs=True)` adds a fractional, independent-line relaxation. The shadow auditor selects it with `continuation_bound_costs=True`; actual pruning remains disabled. It retains the original gross envelope and uses the lower of the two upper estimates with the existing conservative numerical cushion.

For each line, aggregate its sales opportunities by frozen book quote and per-book sales cap. Existing finished inventory is available only once across those opportunities. Future output is bounded by the sum of that line's remaining active production capacities. For a candidate total sold quantity q, newly required output is `max(0, q − current finished stock)`. Its minimum conversion cost uses the actual per-output conversion rate. Minimum new input spend is the sum, per ingredient m, of:

`cheapest future quote_m × max(0, recipe_m × new output / output yield − current held input_m)`

A material with no future offer limits production to what currently held complements permit. Future offer stock, order timing, lots, liquidity, storage coupling, production gates and switching charges are relaxed. The cheapest quote may come from a later or empty offer, deliberately making cost optimistic. Each owned line may independently use all current input inventory, so shared inputs are duplicated in the relaxation; they are never duplicated in the actual planner. This is a lower bound on total required new input cost, since giving the same free holdings to several lines cannot increase their combined minimum spend.

Sales can be assigned optimistically to the highest-price opportunities, subject to each frozen-book cap and the total available finished/output quantity. Fractional production and sales are allowed solely inside the bound. Revenue is piecewise linear concave and required input cost is piecewise linear convex. The maximum relaxed return therefore occurs at a sales-cap boundary, existing-stock boundary, owned-input exhaustion boundary or quantity endpoint. The reference computes those breakpoints and their values with exact rational arithmetic over supplied integer quantities and binary floating-point prices, then rounds the resulting float upward. Final cash/terminal combination retains a conservative numerical cushion; no universal floating-point certification is claimed.

Terminal inventory maxima are still credited independently and optimistically; rent and switching expenses remain omitted, and explicit future switching income is retained unless the funding query is transfer-neutral. The actual objective and accounts still value each item once. These relaxations ensure the bound is not mistaken for an executable plan or a guaranteed market allocation.

The certain one-period capacity-one fixture now has a $5.50 envelope (plus cushion), matching its exact return rather than the original roughly $10. Sixty seeded distinct-line/shared-input cases compare the root bound to exhaustive policies. Shadow audits preserve complete results in the two-period and fee/income examples, and additional monetary-scale tests cover 1e−8/1/1e8. Fourteen targeted tests passed in 3.981 seconds before the final monetary-scale addition; the six updated cost-envelope tests then passed in 3.370 seconds.

In the larger two-period fixture, checked continuations remain 8,824. Potential cuts rise from 6,329 to 6,393, but the useful-depth measure improves much more: cuts with another purchase ahead rise from five to 69. Maximum slack falls from about $9 to $4.50. The same counts hold under transfer-neutral funding for this zero-fee fixture. In the fee fixture, future-purchase cuts rise from zero to one under ordinary funding and from one to two under transfer-neutral funding. No audited bound falls below its exact candidate value.

`20261012-cost-envelope` preserves prior/final source, tests, complete inputs/results, hashes and byte-identical report replay. These are diagnostic cut opportunities, not disjoint subtrees, measured speed gains or a scalability pass. The next step is validation-preserving optional pruning and a rerun of the unchanged failed scaling screen, with exact policy/trace comparisons. Production and live state are unchanged.

## Optional continuation pruning: correct in tests, scaling gate still fails

`prune_continuation=True` now skips a candidate's remaining event tree when its finite conditional envelope is strictly below the best completed candidate by more than the existing value-tie tolerance. It defaults off. `continuation_bound_costs=True` selects the tighter cost envelope; prefix traversal and funding memoization remain separate options. The candidate's current procurement/production transition still runs before bounding, so the implementation avoids future work but does not yet eliminate the current allocation leaf itself.

Before pruning, `scenario_validation.validate_calendar` checks all positive-probability scenario calendars, known event types, labels/book matching, purchase-phase reuse, rent/end-tick ordering, quotes, supplier offer identity/quantities/prices, reliability dimensions, fee/rent parameters, shared-sales groups and terminal-table dimensions/finiteness. State-dependent feasibility and accounting remain enforced by the normal ledger. Incomplete terminal coverage makes the bound unavailable rather than allowing a cut; the actual horizon checks remain intact. Overflow during bound construction also becomes infinity, which cannot prune.

Pruning currently requires the built-in endogenous funding modes. An arbitrary callback may behave differently in an unvisited state and cannot be validated by inspecting the calendar, so explicit-callback comparisons remain exhaustive and requesting pruning with one fails clearly. This restricts the optimization switch, not the planner's existing reference action space. Actual allocations, split suppliers, lots, owned lines, persistent stock and observed-history semantics are retained. Pruning diagnostics distinguish skipped continuations from audited completed candidates; work counters intentionally change, while policies, account states and traces must match.

Forty-two targeted pruning, envelope, history, persistent-supply, shared-sales and phase-oracle tests pass in 12.312 seconds. They compare complete semantic results across ordinary/transfer-neutral funding and independent/persistent supply; test malformed future offers, books, rent ordering and terminal values; preserve policies over monetary scales 1e−8/1/1e8; verify that unavailable envelopes do not prune; and retain explicit work-limit failure. These are covered-case correctness results, not proof of full production suitability.

The original 32-case screen was rerun with unchanged cases and 4,000 allocation/16,000 prefix budgets, 4,096 memo entries, cost-aware pruning for endogenous modes and unpruned frozen-callback controls. It still returns 18 exact rows and 14 limits. Completed economic values and initial choices match prior evidence. In the one-period capacity-four/two-supplier prefix case, all 750 allocation leaves are still visited even though 656 closing continuations are skipped. This explains why a large pruning count does not establish a useful search reduction: cuts happen after current-leaf enumeration, and rational bound evaluation itself has a cost.

The optimization remains disabled by default. Do not promote it based on passing tests or tune work budgets to relabel this screen as successful. The next structural work must avoid leaf enumeration—for example, allocation-box bounds or a verified compiled solver for eligible final-decision subproblems, with the full oracle fallback for other calendars. Any specialization must preserve economic contracts and supported ownership rather than silently shorten the planning horizon.

`20261012-continuation-pruning` preserves pre-edit/final source and tests. `20261012-phase-scaling-pruned` preserves complete screen inputs, specification, archived source and results. The archived source runs outside the repository and reproduces all 32 semantic rows exactly, excluding elapsed durations. All launched runs completed in isolation; production and live state are unchanged.

## Compiled closing-allocation adapter and an exact-cash counterexample

`tools/buying_v2/closing_allocation.py` now reduces an eligible final purchasing decision to the existing compiled industrial basket solver. It is an experimental adapter, **not enabled in `phase_oracle.solve`**. It requires explicit frozen per-offer funding, no existing open book, and precisely one following `OpenBook`/ordinary `SettleBook` pair. Shared-sales books, further decisions, future rent, quote changes and other calendars retain the general planner. After-procurement overhead with nonzero rent is also unsupported because allocation-dependent fees can change equity eligibility. Unsupported scope returns `None`; malformed contracts raise errors.

For line r and possible new output x, its value table is the posterior-weighted expectation of `quote_r × min(old_finished_r + x, demand_r) + terminal_finished_r[max(0, old_finished_r + x − demand_r)]`. Remaining-input values are posterior-weighted explicit terminal tables. The initial-to-current cash/arrears difference and expected future fee income enter once as an additive constant, retaining the absolute objective used by the relative tie tolerance. No product-independence assumption is needed: there is no subsequent decision or shared sales constraint in this calendar. Installed production order, historical basis, lots, shared inputs/cash/storage, production gate, frozen funding caps and D2 fees stay in the basket problem. The selected basket then executes through the original event ledger for actual accounting and final state.

That replay alone cannot establish equivalence for rejected baskets. In particular, combining procurement and production can change floating-point reduction order compared with the staged ledger. This adapter therefore remains disconnected until boundary checks and explicit fallback behavior are established for planner substitution. It does not derive funded demand, calibrate forecasts, remove general continuation decisions or establish population scalability.

The boundary audit found a real pre-existing compiled defect: with goods costing $0.10 and two product-order fees of $0.10 and $0.15000000000000002, the ledger's `goods + sum(fees)` is exactly $0.35. Adding each fee directly to goods instead gives $0.35000000000000003. At cash $0.35 the compiled solver rejected a feasible two-input buffer purchase and selected only one input. `industry.py` and the corresponding box bound now sum fees first, matching the independent ledger. The regression fails before the fix and passes afterward; no affordability epsilon or balancing entry was introduced.

Forty-one targeted tests pass across closing allocation, industrial solvers, forecast allocation, phase oracle and continuation funding. Closing tests include 160 seeded random two-line cases (seed 702931), correlated outcomes/terminal values, lots, inactive lines, fees, basis, constrained cash/storage, absolute horizon offsets, monetary scales 1e−8/1/1e8 and omitted future fee income. They compare selected allocation, actual final state, horizon value and every ordinary ledger trace field against exhaustive event-tree evaluation. This is finite test evidence, not a universal floating-point proof.

A separate frozen-funding, one-period screen demonstrates the potential benefit of avoiding leaf enumeration:

| Capacity / suppliers per input | Cartesian baskets | Adapter warm median (7 samples) | Reference at 4,000-node limit | Return |
| --- | ---: | ---: | --- | ---: |
| 1 / 1 | 4 | 0.275 ms | Exact, 4 nodes | $5.50 |
| 2 / 2 | 81 | 0.274 ms | Exact, 81 nodes | $11.00 |
| 4 / 2 | 625 | 0.284 ms | Exact, 625 nodes | $22.00 |
| 8 / 3 | 531,441 | 0.315 ms | Explicit limit | $44.00 |

Each adapter result uses the existing single-line, fee-free, zero-input-terminal relaxation certificate and replays actual settlement. The first call took approximately 185 ms including initialization/cache loading; it is excluded from warm medians. These are small synthetic adapter timings, not endogenous-funding, multi-period, full-world or adoption-gate results. Complete inputs, script, source hashes, pre-fix solver copies, test logs and archives are in `stats/buying-implementation/20261012-closing-allocation/`. The four semantic rows are checked in an outside-repository archived-source replay, excluding elapsed timings. Initial archives missing JIT catalog inputs and their failed replay logs are retained alongside the corrected complete archive.

## Closing-decision boundary audit inside endogenous funding

The adapter can now be checked through `phase_oracle.solve(..., audit_closing_allocation=True)`. This defaults off. It runs **after** each exhaustive conditional optimization, compares the selected allocation, conditional return and all final states, and raises on a disagreement. It reports separate `closingAudit.checked`/`unsupported` counters without replacing any primary search work. Current funding counterfactuals retain their original incumbents during the shadow replay, and fee-neutral counterfactuals omit future fee income consistently. An explicit compiled search limit remains an error, not an approximate certificate.

Two further pre-existing compiled/reference storage defects have regression tests:

- Three deliveries of three units at 0.1 space each accumulated as three `3 × 0.1` terms, yielding 0.9000000000000001. The ledger aggregates the material's nine units first, yielding 0.9. With 0.9 room, compiled execution formerly bought eight instead of nine units. Compiled evaluation and both bounds now aggregate by material.
- With occupied space 100000000.3, a line consuming two inputs of 0.1 space each and producing 0.2 space conserves storage. Subtracting each input separately before adding output yielded 100000000.30000001 and rejected the intended output. Compiled evaluation now sums consumed space first and applies the net line-space change, matching the independent oracle.

These corrections align the single-problem compiled solver with its existing reference; they do not change the approved physical model or add a tolerance. Both regressions fail against the captured prior solver and pass after the corrections.

A separate counterexample establishes why selected-basket replay is insufficient for automatic substitution. A company with storage 100000000.2 holds one input occupying 100000000.1. It can buy a 0.1-space ingredient and produce a 0.10000001-space output. The staged ledger's recomputed post-purchase room permits the purchase/output and $9 closing return; the combined problem rejects it and chooses no purchase. Replaying that zero basket finds no discrepancy, but the optimum is wrong. The adapter therefore returns `None` for fractional spatial dimensions or aggregate possible inventory space above 2^52. The general planner retains those supported states. Integral spatial dimensions and bounded sums make these space reductions exact in binary64; this is an optimization eligibility rule, not a new economy constraint. The counterexample is exercised with the shadow switch enabled and retains the $9 general-planner result.

The four-row endogenous audit uses the existing capacity-two, two-supplier, two-period, two-outcome fixture with funding memo capacity 4096 and feasible-prefix enumeration:

| Funding | Supply | Checked closing solves | Unsupported earlier solves | Value | Original allocation evaluations |
| --- | --- | ---: | ---: | ---: | ---: |
| Continuation | Independent snapshots | 603 | 6 | $6.50 | 11,148 |
| Continuation | Persistent arrivals | 551 | 6 | $5.00 | 8,656 |
| Transfer-neutral continuation | Independent snapshots | 603 | 6 | $6.50 | 11,148 |
| Transfer-neutral continuation | Persistent arrivals | 551 | 6 | $5.00 | 8,656 |

All 2,308 eligible checks agree. The test also compares the complete solve result with and without audit, excluding only the new audit counters, so policies, traces, funding results, memo statistics and original work counts remain unchanged. Forty-four targeted tests pass across closing allocation, industrial solvers, forecast allocation, continuation funding/pruning and information history. The 160 randomized two-line cases from the earlier adapter tests remain included.

`stats/buying-implementation/20261012-closing-boundaries/` preserves the pre-fix solver, failing regression logs, final tests, four-row audit script/results and source identity. This is correctness evidence for a future substitution. It is not a speed improvement: the shadow deliberately retains exhaustive work. Near-tie value arithmetic, production-gate boundaries and larger supported fixtures still need consideration before enabling replacement; the overall scaling, forecast, integration and adoption gates remain open.

The complete four-row audit also replays byte-identically from the archived source outside the repository; `verification.json` records the 2,308 checks. The replay uses the existing dependency installation and Python 3.12, with all simulation/catalog source inputs supplied by the archive.

## Ledger-order compiled closing enumeration

The value-boundary audit found that integer storage alone does not justify substituting the earlier `closing_allocation.candidate` optimizer. With cash $1,000, one input priced $0.10, no active production, and an explicit one-unit terminal value of $0.10000000100001, its algebraic table objective returns 1.0000099914808658e−9 and selects purchase. The staged cash/horizon calculation returns 9.999872596644366e−10. Under the existing 1e−9-plus-relative tie rule, the event tree retains no purchase. The shadow audit correctly rejects the discrepancy. The difference is numerically tiny but violates exact policy agreement; neither a larger tolerance nor silent oracle changes are a correction.

`tools/buying_v2/closing_values.py` supplies the replacement evaluator. For each complete basket, it uses the compiled production kernel, then follows the ledger's order: subtract goods plus summed fees from current cash; subtract each installed line's actual conversion cost; sum realized sales by installed line; add sales and fee income separately; subtract initial cash and the liability change; add terminal inputs followed by terminal finished goods. It retains the original posterior weights and performs `math.fsum(weight × scenario_value) / mass` outside compiled code, matching the event tree. It does not optimize using the earlier algebraic value-table score.

Its bounded exhaustive selector scans the same lexicographic allocation order and applies the same value/payment/quantity comparison. `phase_oracle.solve(..., closing_search='compiled-exhaustive')` optionally uses it at eligible closing decisions, including funding counterfactuals. It then executes the chosen basket through the ordinary ledger to produce complete accounting/state/traces and checks exact conditional-value agreement. The default remains `closing_search='event-tree'`. Unsupported calendars and fractional/oversized spatial configurations retain the general planner; no supported economic action is removed. The old algebraic adapter remains available only for its explicitly experimental comparison/shadow role and must not be promoted automatically.

The compiled path counts **all Cartesian baskets**, including infeasible baskets, against the remaining `max_nodes` budget. It does not label a single returned basket as one unit of search work. Consequently its counted work can exceed the feasible-prefix path even when it is faster. Oversized closing problems fail before enumeration with an explicit `closing exhaustive node limit`; no approximate basket is returned. Python posterior reduction and exhaustive selection remain in this oracle accelerator; it is not a full-population implementation.

Forty-two targeted tests pass across ledger-order closing values, the earlier adapter, industrial solvers, continuation funding/pruning and information history. New tests cover every basket in 60 seeded two-line markets (seed 173290), independently replaying all feasible baskets through the staged ledger and checking each scenario payoff bit-for-bit. They also compare selected policies, the near-tie counterexample, and full endogenous two-period results under ordinary/fee-neutral funding and both supply modes. Complete results match except declared work diagnostics. A subsequent focused test verifies the fractional-storage $9 case takes the general fallback with identical leaves.

The original 32-row screen retains its 4,000-allocation/16,000-prefix budgets and memo capacity 4096. With optional compiled closing enumeration and continuation pruning off, it still yields **18 exact results and 14 explicit limits**. All 32 semantic rows reproduce from the archived source with the original repository excluded from imports. It therefore fails the same scalability gate.

A separate warm, alternating three-pair comparison for capacity four, two suppliers per input, one period and endogenous continuation funding gives:

| Pair | Event tree with feasible prefix | Compiled closing enumeration | Return |
| --- | ---: | ---: | ---: |
| 1 | 91.536 ms | 9.353 ms | $22 |
| 2 | 91.488 ms | 8.681 ms | $22 |
| 3 | 91.512 ms | 9.448 ms | $22 |

The original path counts 750 feasible-prefix leaves versus 1,750 full Cartesian leaves in the compiled path; every measured pair compares complete policy/trace semantics. These local timings show cheaper evaluation, not improved combinatorial scope, population speed or an adoption pass.

Evidence: `stats/buying-implementation/20261012-ledger-closing/` holds tests and the paired timing script/results. `20261012-phase-scaling-ledger-closing/` holds all case inputs, specification, archived source/dependencies, manifest, 32 outcomes and replay verification; `20261012-phase-scaling-ledger-closing-replay/` holds the independent replay. Next implementation priority is pruning allocation ranges using conservative ledger-value bounds while preserving lexicographic comparison order, rather than raising budgets or returning the numerically incompatible algebraic optimizer.

## Lexicographic closing-box pruning with outward ledger bounds

`closing_search='compiled-boxes'` now optionally replaces exhaustive closing enumeration with `tools/buying_v2/closing_boxes.py`. It retains the same eligibility and general-calendar fallback as ledger-order closing enumeration. The default remains the original event tree. No forecasting, demand, fee or production policy is changed.

Each box describes inclusive whole-lot lower/upper quantities for each discovered offer. The upper bound:

1. Computes minimum goods spending and unavoidable frozen-incumbent fees from the lower quantities; rejects proved cash, input-slot or physical-room infeasibility.
2. Grants every installed line independent access to all maximum possible inputs, ignores production gates and conversion costs, and caps output by installed/finished capacity. This deliberate relaxation permits shared-input reuse only in the bound.
3. Bounds scenario sales at the frozen quotes and maximizes explicit terminal tables over possible remaining quantities.
4. Follows the actual cash, liability and terminal-value operation order. Each bound operation uses `math.nextafter` outward, including products, sums and posterior reduction; nonfinite bound calculations return positive infinity rather than prune.

The search splits the **first varying coordinate** and visits the lower half first. Thus all evaluated leaves retain the original lexicographic order even when whole contiguous ranges are skipped. A box is skipped only for proved infeasibility or a bound below the current choice beyond the existing comparison tolerance. It does not seed a different incumbent with a best-first or relaxation solution; that would change the path-dependent near-tie scan.

Evaluated leaves share the existing `max_nodes` budget. Boxes and outer feasible-prefix visits share `max_prefix_nodes`, including dynamically updated limits while an outer generator is suspended in a closing solve. Neither budget is silently increased. `closingSolver` separately records solves, evaluated allocations, visited boxes and skipped allocations. Work-limit exhaustion returns no approximate policy.

The broader audit also exposed a runtime-specific reduction mismatch. CPython 3.12's floating-point `sum` uses compensation, as documented in its [builtin implementation](https://github.com/python/cpython/blob/v3.12.8/Python/bltinmodule.c#L2444). The compiled reference had used simple accumulation. New `float_sum.py` supplies matching finite-float compensation for the relevant industrial space, fee, recipe-cost and terminal reductions, and closing sales. Explicit sequential ledger reductions remain sequential. On a three-line sales fixture, archived pre-fix code returns 1e16 while the staged ledger returns 1.0000000000000004e16; corrected compiled code matches the latter. This is a precision regression test, not a proposed monetary calibration or realistic economic scenario. The measured/supported runtime is Python 3.12.0; benchmark manifests now include Python, NumPy and Numba versions.

Verification includes a 46-test targeted run across closing boxes/values, the earlier adapter, industrial solvers, continuation funding/pruning and information history. Forty seeded three-input/three-line markets (seed 413297) compare boxed and exhaustive policies and check random boxes against every contained feasible staged-ledger basket. Additional checks compare each scenario value exactly, cover the prior near-tie counterexample, verify skipped-plus-evaluated basket counts, reject exhausted leaf/box budgets, and compare complete endogenous policies under both supply/funding modes. After adding the dynamic shared-budget check, nine closing-box/prefix tests pass, including an exact-budget pass and one-less-budget failure. This is finite verification evidence, not a proof of the whole economic model.

The final unchanged 32-row screen still yields **18 exact results and 14 explicit limits**. Selected endogenous results are:

| Capacity / suppliers / periods | Evaluated allocations | Closing boxes | Skipped closing allocations | Return |
| --- | ---: | ---: | ---: | ---: |
| 1 / 1 / 1 | 4 | 14 | 4 | $5.50 |
| 2 / 2 / 1 | 46 | 306 | 224 | $11.00 |
| 4 / 2 / 1 | 110 | 1,126 | 1,640 | $22.00 |
| 1 / 1 / 2 | 42, including 8 outer allocations | 93 | 26 | $3.25 |

For capacity four, the earlier compiled exhaustive path evaluated 1,750 allocations. Box pruning reduces that to 110, but the observed single screen time remains about 9.95 ms because bound/traversal overhead offsets the saved evaluations. This is not a paired performance claim. Capacity eight with three suppliers and the larger endogenous two-period cases still fail the original budgets. The current bounds ignore too much production cost and shared-input competition to close scalability; faster leaf evaluation alone did not address this, and the new boxes alone do not either.

Evidence is preserved in `stats/buying-implementation/20261012-closing-boxes/` (tests and archived before/after summation proof), `20261012-phase-scaling-closing-boxes/` (first screen), `20261012-phase-scaling-closing-boxes-final/` (shared-budget final screen, complete source/specification/runtime manifest), and `20261012-phase-scaling-closing-boxes-replay/`. All 32 final semantic rows replay exactly with the original repository excluded from imports, excluding elapsed timings. Completed rows explicitly satisfy the combined branch-work ceiling. Next work should tighten the admissible return bound with production/input cost information and reduce repeated bound overhead, preserving the validated ledger order and supported action space. Population, forecasting, integration and adoption gates remain open.

## Conditional production-cost bound completes five more screen cases

`closing_search='compiled-cost-boxes'` adds `closing_cost_bound.py` to the existing lexicographic box search. The original gross bound remains a separate comparator. Search takes the smaller valid upper bound, keeps the original leaf order and actual ledger evaluator, and shares the same 4,000-allocation/16,000-branch screen budgets. The default is still the original event tree.

For each installed line, the new bound conditions on every possible whole batch count `b`. At that count:

- The line requires `recipe[m] × b` input units. Existing inputs and the box's mandatory lower purchases cover part of that requirement. Remaining units receive the cheapest available quote within each offer's remaining box capacity. Wholesale lots are relaxed, so this cannot cost more than a feasible procurement plan. Other lines do not compete for those inputs in this bound.
- Mandatory purchases and this extra minimum cost are computed as exact rational numbers from the stored binary64 prices. A conservative merchandise-rounding allowance is subtracted before rounding the cost downward. The allowance includes one full ulp for every product and sequential addition, using the largest positive product/prefix in the box; unavailable finite bounds fall back to zero minimum merchandise cost.
- The fixed line's actual rounded conversion payment is subtracted in cash-operation order. Fees and other lines' conversion costs are omitted in this bound; the separate gross bound still includes unavoidable fees.
- Its known output fixes its sales and residual finished stock for each scenario. Remaining-input maxima are reduced by its recipe consumption. Other lines retain optimistic output and terminal-value allowances. Cash, liabilities, terminal values and posterior reductions use outward operations in ledger order.

Taking the maximum over that line's possible batch counts covers its output in every feasible allocation. Taking the minimum across lines remains an upper bound. This conditions the bound only; actual production still follows the retained historical-cost gate and installed line order. It does not let the company freely choose an output vector or treat sunk basis as a new cash cost.

For the capacity-four, two-supplier, single-line fixture, the whole-range gross upper bound is approximately $40. Accounting for necessary inputs and conversion tightens it to $22 plus outward rounding—the analytical optimum. This remains valid for useful incomplete buffers and explicit nonmonotone terminal tables; those values are not replaced with adopted defaults.

Verification: eleven closing-bound/box/value tests pass, including the forty seeded three-input/three-line range checks, full staged-ledger comparisons, lots, multi-unit yields, expensive owned basis, terminal buffers, near ties and money scales 1e−8/1/1e8. Complete endogenous policies agree under ordinary/fee-neutral funding and both supply modes. A subsequent eighteen-test integration run passes after tightening the fixture's error handling (one test is repeated across the two runs). Only explicit infeasible-procurement/physical-storage exceptions are accepted by the exhaustive fixture.

The unchanged 32-case screen improves from **18 exact / 14 limits to 23 exact / 9 limits**. Newly completed cases are:

| Capacity / suppliers / periods | Funding | Outer search | Return | Evaluated allocations | Closing boxes |
| --- | --- | --- | ---: | ---: | ---: |
| 8 / 3 / 1 | Frozen comparator | Exhaustive | $44 | 84 | 1,719 |
| 8 / 3 / 1 | Frozen comparator | Feasible prefix | $44 | 84 | 1,719 |
| 8 / 3 / 1 | Endogenous continuation | Exhaustive | $44 | 433 | 7,344 |
| 8 / 3 / 1 | Endogenous continuation | Feasible prefix | $44 | 433 | 7,344 |
| 2 / 2 / 2 | Endogenous continuation | Exhaustive | $6.50 | 2,646 | 15,767 |

The corresponding two-period feasible-prefix case still hits the shared branch ceiling: outer prefix visits consume budget in addition to closing boxes, whereas the exhaustive outer scan does not count prefix visits. This difference is explicit work accounting, not a different economic result or permission to increase budgets. All completed rows satisfy both original ceilings. Existing completed values and first allocations are unchanged; all completed values also match the fixture's analytical returns (certain trade: $5.50 × capacity × periods; the two-period perfectly correlated uncertain fixture: $3.25 × capacity).

The reference rational implementation is slow. Single observed screen times are about 87 ms for the larger frozen case, 363–365 ms for its endogenous counterpart, and 851 ms for the newly completed two-period case. The previously completed four-unit endogenous case takes about 34 ms versus roughly 10 ms with the gross-only boxes. These are per-company synthetic calculations, not full-tick timings or population-performance passes. The improvement is in budgeted solvable scope; nine screen cases and the full performance gate remain unresolved.

Artifacts: `stats/buying-implementation/20261012-closing-cost-boxes/` contains test logs and the reproducible baseline/candidate comparison. `20261012-phase-scaling-closing-cost-boxes/` contains the complete specification, inputs, source/runtime manifest and outcomes; `20261012-phase-scaling-closing-cost-boxes-replay/` contains the isolated archived-source replay. All 32 semantic rows match with the original repository excluded from imports, excluding elapsed timing. The original failed screens are preserved.

Next work should retain the rational bound as a verification reference while replacing repeated rational operations with a conservatively rounded, compilable calculation. Any faster bound must remain above the staged-ledger return and preserve complete policies. Earlier-phase continuation branching, suitable forecasts, production integration and all remaining adoption gates are still required.

## Compiled conservative cost bound preserves the 23-case frontier

`closing_search='compiled-fast-cost-boxes'` now uses `closing_cost_compiled.py` for the conditional production-cost bound. The rational `compiled-cost-boxes` mode remains an independent reference calculation. Default selection remains the original event tree; no production/live policy is activated.

The compiled bound retains the same relaxation and output conditioning. Instead of constructing exact rational minimum costs per box, it rounds every minimum-cost product/addition downward and rounds the merchandise-arithmetic error allowance upward. Subtracting that allowance gives a conservative lower spending bound. Cash/terminal operations continue to round upward. The posterior reduction uses an upward sequential sum with outward final division; actual selected-basket evaluation still uses the original `math.fsum` ledger-value reduction. Nonfinite interval calculations weaken the bound to positive infinity or zero minimum spending as applicable, never return an approximate decision. Source-aware Numba caching and default non-fast-math execution remain in use.

Thirteen targeted tests pass. They compare the compiled bound against the rational bound on forty seeded three-input/three-line markets and 405 additional boxes spanning subnormal prices, ordinary prices, large prices and overflowing maximum-cost sums. The compiled bound is never lower in these checks, and the random-box checks also compare against each feasible contained staged-ledger payoff. Complete policies agree for both funding/supply modes and three monetary scales. A subsequent eighteen-test integration run passes, including additional compiled checks for wholesale lots, multi-unit output, historical basis and terminal buffers (one case is repeated across runs). This is finite implementation verification; the economic model and population suitability still require their separate gates.

All 32 scaling rows match the rational run exactly after excluding elapsed timing and the mode label—including status, values, first allocations and work counters. The result remains **23 exact / 9 explicit limits** at unchanged budgets. Thus compilation speeds the same search rather than claiming more solved cases.

Three alternating warm pairs compare complete policy/trace semantics in each run:

| Fixture with endogenous funding and exhaustive outer scan | Rational median | Compiled median | Paired samples, rational / compiled |
| --- | ---: | ---: | --- |
| Capacity 8, 3 suppliers/input, 1 period | 363.727 ms | 73.579 ms | 366.184 / 73.561; 363.727 / 73.579; 361.884 / 87.009 ms |
| Capacity 2, 2 suppliers/input, 2 periods | 849.613 ms | 444.571 ms | 850.179 / 444.571; 847.745 / 422.702; 849.613 / 445.539 ms |

Each mode is warmed before measurement, and no other simulation workload is launched during the pairs. These are individual synthetic company plans, not full-world ticks. The roughly 4.9× and 1.9× median improvements do not satisfy the population-performance gate; nine cases still exceed the node/branch budgets, and preparation, repeated conditional solves and earlier-phase traversal remain substantial work.

Artifacts: `stats/buying-implementation/20261012-closing-cost-compiled/` contains tests, the timing script/results and cross-mode comparison. `20261012-phase-scaling-closing-fast-cost-boxes/` contains complete inputs, specification, archived source/runtime manifest and results; `20261012-phase-scaling-closing-fast-cost-boxes-replay/` contains isolated replay. All 32 semantic rows reproduce with the original repository excluded from imports, excluding timing. The rational and prior failed runs are preserved. Next work must address remaining branch/repeated-solve work and realistic scale, without presenting this local speedup as completion of forecasting, integration or adoption requirements.

## Reuse validated preparation within each closing solve

A warm profile of the two-period capacity-two endogenous case found 1,212 calls to `closing_allocation.prepare` across 609 closing-solver calls (six are unsupported); the supported calls prepared the same immutable inputs twice. Cumulative profiled preparation time was 0.280 seconds out of 1.161 seconds for the complete solve. These instrumented times identify cost, not uninstrumented performance.

`closing_values` now has an internal prepared evaluator used immediately by the closing selectors after their ordinary `prepare` call. Each public evaluator/selector still validates state, calendar, posterior and scope before using it. This is local reuse within one invocation, not a cross-state cache. Demand, quotes, opening finished inventory, fee-income arrays and posterior mass are also packed once per evaluator instead of once per leaf. Accounting arithmetic, reduction order, budgets, funding and allocation comparison are unchanged.

Thirty targeted tests pass across closing values/boxes/cost bounds, continuation funding, information history and phase scaling. All 32 screen rows match the prior screen exactly except elapsed time, including work counters: 23 exact results and nine limits. Two complete result comparisons, including policies, traces and diagnostics, also match the independently captured pre-edit results. Five warm samples per version give median times of 73.4→70.9 ms for capacity eight/three suppliers/one period and 423.6→381.5 ms for capacity two/two suppliers/two periods/two outcomes. Samples were collected before and after the edit, not alternating; treat these as local timing evidence, not a population-performance pass.

Evidence: `stats/buying-implementation/20261012-closing-profile/` contains the profile, before-source copies, measurement script, complete before/after results, tests and comparisons. An initial JSON serialization failure is preserved separately; corrected measurements serialize dataclass states explicitly. `20261012-phase-scaling-prepared-closing/` contains all screen inputs, source archive and runtime manifest. No new economic assumption or production activation is introduced. Remaining search limits and broader forecasting/integration/adoption requirements are unchanged.

## Exact closing memo completes a twenty-fourth screen case

An instrumented capacity-two/two-period endogenous solve observed 603 supported closing calls but only 469 distinct full `(company, initial, state, event, posterior, neutral)` inputs. Repeated calls consumed 732 evaluated leaves and 5,220 boxes. This supports exact-input reuse without reducing the economic state or merging observation histories.

The optional `closing_memo_size` argument (default zero) adds a per-`solve` LRU cache of completed closing selections. Company and initial state are fixed by that invocation. Keys retain the complete state (including accounts and phase history), purchase event, ordered weighted suffix scenarios with terminal tables, transfer-neutral flag, and hypothetical-incumbent flag. The last flag deliberately distinguishes further cases beyond the initial probe. No posterior normalization, state projection, or approximate equality is used. Failed/unsupported solves are not cached; no result survives into another top-level solve. Hits reuse only allocation/value results, while the ordinary ledger still recreates branch state, accounts, preference changes and traces.

Every hit charges one selected-basket replay against the node budget; misses charge all evaluated leaves and boxes as before. No box is visited on a hit. `closingSolver.memo` reports capacity, hits, misses, peak entries, saved allocation evaluations (excluding the required replay) and saved boxes. The existing combined prefix/box ceiling remains unchanged. A finite cache bounds entries, not bytes independently of scenario/state dimensions; population memory suitability is still unproven.

Twenty-eight targeted tests pass across closing memo/value/box behavior, continuation funding, information history and phase scaling. They compare full policies/accounts for ordinary and neutral funding, independent and persistent supply, cache sizes one and 4,096, and exhaustive and box closing modes; they also check invalid capacities, hard work limits and run isolation. The newly completed prefix case separately matches the full ordinary event tree's policy and final accounts: value $6.50, 11,148 ordinary event-tree nodes versus 2,075 cached closing-path nodes under an expanded reference-only verification budget.

Under the original 4,000-allocation/16,000-combined-work screen limits, the cache completes 24 of 32 cases, with eight explicit limits. The new success is capacity two/two suppliers/two periods/two outcomes, endogenous funding and feasible-prefix outer search. It uses 11,822 boxes plus 240 outer prefixes, versus the prior case exceeding the combined limit. Its 117 hits save 445 allocation evaluations and 3,945 boxes. Previously completed cases retain their values and first allocations. All 32 rows, including diagnostics, replay identically from archived source outside the repository, excluding elapsed time.

Three alternating warm timing pairs compare cache sizes zero and 4,096 with complete results equal after excluding work diagnostics. The capacity-eight one-period median is effectively unchanged (72.6 vs 72.4 ms; 433 nodes each). The capacity-two two-period median improves from 386.7 to 353.0 ms; nodes drop from 2,646 to 2,201. These synthetic timings do not establish full-population performance.

Evidence is in `stats/buying-implementation/20261012-closing-reuse/`, with complete screen/source/runtime archives in `20261012-phase-scaling-closing-memo/` and its `-replay` companion. Reproduction uses `python -m tools.buying_v2.benchmark_phase_search --spec stats/buying-implementation/phase-scaling-closing-memo-spec-20261012.json --output <fresh-directory>` with the repository's compatible interpreter and dependencies. The cache defaults off, and no production behavior or economic assumption changes. Eight scaling limits, suitable forecasts, integration and adoption gates remain open.

## Combined continuation pruning and closing reuse

The eight remaining memo-only screen failures were all two-period cases with larger capacity. Combining the existing cost-aware continuation pruning with compiled closing cost bounds and exact closing memoization completes one more case. This uses `closing_search='compiled-fast-cost-boxes'`, `closing_memo_size=4096`, `funding_memo_size=4096`, `prune_continuation=True`, and `continuation_bound_costs=True`; each remains an explicit experimental option. The frozen-callback screen controls retain their unpruned treatment because arbitrary callbacks are outside the pruning contract.

The unchanged 4,000-node/16,000-combined-prefix-and-box limits now yield **25 exact outcomes and seven explicit limits**. The new success is capacity four, two suppliers per input, two periods and two correlated outcomes, endogenous funding and exhaustive outer traversal. It returns the analytical $13 value with first allocation `(4, 0, 4, 0)`, 3,660 allocation nodes and 15,936 boxes. Continuation pruning skips 465 tails with future purchases; 82 closing memo hits save 676 allocation evaluations and 7,466 boxes. Its feasible-prefix counterpart still exceeds the combined budget; no limit or action scope was changed to obtain the success.

Ten targeted tests pass, including three new interaction tests. These compare the combined path's complete policies, terminal accounts and traces against the ordinary event tree on the smaller correlated-demand case and fee/income fixtures across ordinary/neutral funding and independent/persistent supply. The tests also preserve malformed-calendar rejection and cover the larger case's original budget and analytical value.

A separate plain event-tree verification of the larger case reached an explicit 500,000-node limit; it supplies no reference result and is retained as failed evidence. The existing compiled closing path, with continuation pruning and closing memoization disabled and expanded verification-only limits (500,000 nodes/1,000,000 boxes), completes with 26,799 nodes and exactly matches the combined path's full policy and final accounts. This verifies the interaction against that established path; it is not a newly completed plain-event-tree comparison for the larger case. All previously completed screen values and first allocations are preserved. All 32 screen rows reproduce from archived source outside repository imports, excluding elapsed time.

Artifacts: `stats/buying-implementation/20261012-combined-planner/` preserves tests, the successful and failed reference scripts/logs, complete successful reference results and verification. The full screen and source/runtime manifests are in `20261012-phase-scaling-combined-pruning/` and `20261012-phase-scaling-combined-pruning-replay/`; the frozen specification is `phase-scaling-combined-pruning-spec-20261012.json`. The larger comparison ran alongside verification work, so its elapsed time is not used as a comparative performance result. Seven search limits, representative-population performance, model/forecast suitability and integration/adoption gates remain unresolved.

## Strict closing certificates expand the screen to 28 cases

`closing_certificate.py` introduces an optional proof of **strict ledger-value dominance** for a supplied feasible closing allocation. It partitions the full whole-lot action box minus that allocation into disjoint boxes by the first coordinate that differs. Each alternative box is either proved infeasible or bounded using the existing outward-rounded gross and compiled cost bounds. A box passes only when the proposal's actual ledger-order conditional value exceeds the upper bound plus the comparison tolerance, with an extra upward rounding step. Otherwise it is subdivided; an unproved singleton or exhausted proof budget returns an inconclusive result. All alternatives must pass.

This strict gap matters because the current pairwise near-tie comparison is order-sensitive. Proving the candidate strictly dominates every alternative means it will replace any earlier incumbent and survive every later comparison. Merely replaying a plausible candidate, or placing it first in the scan, does not establish this property. Equal-value alternatives, fee/cost ties, and the preserved ordinary-cash near-tie counterexample therefore cannot receive a strict certificate. Failed proof never seeds or changes the fallback's original lexicographic traversal.

The optional `closing_search='compiled-certified-boxes'` path first obtains a single-line, zero-expected-terminal-input proposal from the existing algebraic relaxation. Its algebraic certificate is ignored. The proposal is evaluated using actual ledger arithmetic and must pass the new proof. Multiple-line firms, useful terminal buffers and any unsuccessful proposal retain the complete compiled cost-box fallback. Unsupported closing calendars still use the general phase planner. Thus proposal eligibility is an acceleration boundary, not a restriction on supported economic actions or ownership.

Work accounting includes two conservatively charged proposal-generator evaluations plus the actual ledger evaluation, the generator's `max_batches + 1` scan states, and every proof/fallback box. `proposalStates` is reported separately and included alongside outer prefixes and boxes in the original combined work ceiling. Generation plus proof receives at most one quarter of the available work budget, with at most 256 proof boxes; these are engineering scheduling limits, not economic parameters. If that budget or three evaluation slots are unavailable, the proposal attempt is skipped. An unsuccessful attempt consumes its actual charged work before fallback. Exact memo hits replay once and reset proposal/box work to zero while recording the saved work separately. Production defaults remain unchanged.

Verification comprises nine initial proof/value/bound tests, then sixteen integration tests and two focused extensions of existing cases. The complement partition is exhaustively checked for disjoint coverage; forty seeded one-/two-line markets compare certification and the complete wrapper with the independent event tree. Wrong proposals, equal-price ties, the known numerical near tie, hard limits, cached runs, ordinary/neutral funding, and independent/persistent supply are covered. A failed equal-price certificate falls back to the correct lexicographic allocation. Four capacity-four/two-period funding/search combinations also match complete results from the preceding solver, excluding only internal node/closing diagnostics, under expanded verification-only budgets.

The original 32-case screen now yields **28 exact results and four explicit allocation limits**, preserving all earlier completed values and first allocations. Newly completed cases are the capacity-four/two-period frozen-funding cases for both outer traversal modes, and its endogenous feasible-prefix case. The remaining four failures are capacity eight/three suppliers/two periods, across both funding and traversal modes. All successful rows remain within 4,000 charged allocation evaluations and 16,000 combined prefixes, boxes and proposal scan states. All 32 rows reproduce from archived source outside repository imports, excluding elapsed timing.

Three alternating warm pairs preserve complete semantic results while reducing the capacity-eight/one-period endogenous median from 73.0 to 4.8 ms and the capacity-four/two-period endogenous median from 515.6 to 405.8 ms. In a separate closing-only proposal probe, capacities two/four/eight/32 require respectively four/four/six/six proof boxes. These are synthetic algorithm measurements, not population timing or evidence of calibrated forecasts.

Artifacts are in `stats/buying-implementation/20261012-closing-certificate/`, including complete comparison results, tests, probe, timing and verification scripts. Full inputs/source/runtime archives are in `20261012-phase-scaling-certified-closing/` and its `-replay` companion; the specification is `phase-scaling-certified-closing-spec-20261012.json`. Remaining earlier-phase branching, full-population performance, forecast/model suitability, runtime/UI integration and adoption gates are still open.


## Search-limit diagnostics locate the remaining scaling work

`PhaseSearchLimit` now preserves a diagnostic snapshot when exact search exhausts a node budget. It remains a `ValueError` with the existing failure message, so existing rejection behavior is preserved. No partial policy, feasible answer or claimed optimum accompanies it. Diagnostics include the active decision stack (event, hypothetical-funding status and search stage), charged allocations, prefix work, completed closing-search work, funding/closing memo counters, bounds and transitions. Counters explicitly exclude work inside a closing subsolver that raises before returning; they must not be presented as a complete accounting of that interrupted subsolver.

The unchanged 32-case screen still completes 28 and explicitly rejects four at capacity 8, three suppliers, two periods and two outcomes. All original row fields other than elapsed time are unchanged. New diagnostics distinguish the failures:

| Funding | Outer search | Charged allocations on failure | Completed closing allocations | Active failure location |
| --- | --- | ---: | ---: | --- |
| Frozen callback | Exhaustive | 3,998 | 1,783 | Second purchase closing solve beneath the first purchase |
| Frozen callback | Feasible prefix | 3,999 | 3,141 | Second purchase closing solve beneath the first purchase |
| Endogenous continuation | Exhaustive | 4,001 | 1,973 | First purchase hypothetical funding allocation loop |
| Endogenous continuation | Feasible prefix | 4,001 | 2,069 | First purchase hypothetical funding allocation loop |

The frozen rows have fewer than 4,000 recorded allocations because their closing solver cannot finish inside its remaining allocation allowance; its interrupted work is excluded from the outer counters. The endogenous prefix case visits 2,571 prefixes, prunes 1,776 complete-allocation continuations, and obtains 77 closing-memo hits before exhausting allocations. It has completed 3,034 closing boxes and 5,976 proposal states; the combined prefix/box/proposal work is 11,581, below the 16,000 ceiling. Thus its binding budget is allocations, not that combined-work ceiling. More closing-cache capacity alone does not address the first-decision basket enumeration.

The next solver work should bound groups of earlier purchase allocations before enumerating their leaves, retaining exact physical/ledger semantics and deterministic selection. Do not infer cheapest-supplier dominance: historical basis, production gates, fees and future information can invalidate it. Frozen callbacks remain unpruned controls unless their purity and funding contract are explicitly restricted; do not enable the endogenous-only continuation bound indiscriminately.

Eight targeted limit/scaling/closing-memo tests pass. Tests distinguish outer versus closing failures, preserve input-validation errors and verify that diagnostic mutation cannot contaminate a later solve. The screen archive is `stats/buying-implementation/20261012-phase-limit-diagnostics/`; its source replay reproduces every row except wall-clock timing. This is diagnostic progress, not removal of any of the four limits or a population-performance improvement.


## Standalone bound for an initial allocation prefix

This section records the initial standalone verification. The optional integration and its results are documented below.

`prefix_continuation_bound.upper_value` now bounds all completions of a fixed initial segment of the current purchase's offer quantities. It is a verification primitive, not yet enabled in planner traversal. The prefix adds its known purchased inputs to a relaxed state and subtracts an understated compulsory goods payment from cash. Fixed offers are removed from the remaining current offer list; later books remain available. The existing cost-aware continuation envelope then bounds the current production phase and all later events.

The relaxation pays the compulsory prefix goods cost once, treats those acquired inputs as available inventory, allows unlimited cheapest supply from remaining/future offers, ignores current fees and production gates, and allows each line independent access to shared inputs. Fixed open sales books remain frozen. These relaxations can overstate attainable value; they must never force an otherwise feasible completion out of the search. Prefixes that exceed relaxed slots/storage/cash, nonfinite arithmetic, or unsupported continuation envelopes return infinity rather than a finite pruning claim. Malformed prefixes raise an input error.

Compulsory product/addition reductions are rounded downward and relaxed cash upward. An additional conservative cushion covers regrouping compulsory versus remaining payments; the existing envelope retains its future-ledger numerical cushion. This primitive does not establish a universal cheapest-supplier dominance rule or change historical-cost production. Its mathematical relaxation and tested numerical behavior remain separate from any future population performance claim.

Ten prefix/continuation bound tests pass both in the worktree and from archived source outside repository imports. Exhaustive small fixtures check every valid prefix against all matching complete allocations and their exact continuations, over one/two periods and hidden correlated outcomes. Additional checks cover multiple installed lines, shared inputs, expensive historical basis, D2 fees, old finished stock, nonzero terminal values, unchanged caller state and invalid/unavailable prefixes. A fixed expensive purchase yields a tighter bound than leaving the first material uncommitted.

`stats/buying-implementation/20261012-prefix-envelope/` preserves test logs, source/catalog/runtime identity and the archived replay. The next required step is optional lexicographic prefix integration with charged bound work, exact policy/account comparisons and the unchanged 32-case screen. The four existing limits are still open; this standalone bound has not changed their status.


## Optional prefix pruning integrated; scaling limits remain

`solve(..., prune_prefix=True)` now enables the verified prefix envelope during `feasible-prefix` traversal with endogenous funding. The default remains false. Arbitrary funding callbacks and exhaustive traversal reject this option; complete calendars are validated before pruning. Prefix order remains lexicographic. A subtree is skipped only if its probability-weighted upper bound is strictly below the current incumbent value beyond the existing comparison tolerance. Unsupported/infinite bounds retain the subtree. No approximate policy is returned on a work limit.

Each scenario-envelope evaluation is charged to the same combined-work ceiling as visited prefixes, closing boxes and proposal states. Closing solves receive only the remaining budget. New counters distinguish bound evaluations, pruned prefixes and raw Cartesian leaves below those prefixes; raw leaf counts include potentially infeasible descendants and are not counts of economically feasible baskets. Complete allocation prefixes bypass the new bound because the existing post-allocation continuation check already handles them.

The first integration bounded complete leaves too. It retained 28/32 completions but changed the largest endogenous-prefix failure to the combined-work limit: 4,656 bound evaluations plus 2,335 prefixes, 3,034 closing boxes and 5,976 proposal states exhausted 16,000 units. This attempted version is preserved in `20261012-phase-prefix-pruning/` with its own source. The revised group-only version is preserved in `20261012-phase-prefix-groups/`.

The revised unchanged-budget screen still completes 28/32. All 24 untreated control rows reproduce the prior screen, excluding timing. At capacity 4/two periods, the endogenous-prefix case prunes five prefixes (25 raw descendant leaves), reducing charged allocations from 1,588 to 1,583. At capacity 8 it prunes 176 prefixes (4,320 raw descendant leaves), performs 1,550 bound evaluations, and still reaches 4,001 charged allocations. There is no new passed scaling gate. Single screen timings do not establish a speed benefit; the additional envelope work can outweigh small allocation savings.

Fourteen targeted tests pass. Complete policies, traces, state and accounts match without prefix pruning across two funding modes, independent/persistent supply, capacities through four, and fee/income counterexamples. Invalid combinations and charged bound-work failures are checked. The initial small-fixture assertion incorrectly required group pruning where only complete leaves were prunable; that failure is preserved, and the final test includes the capacity-four case where group pruning actually occurs. All 32 final screen rows replay from archived source with only elapsed time excluded.

This option is an exact-search building block, not the scalable full-population solution. Stronger or cheaper earlier-decision bounds remain necessary; increasing budgets or reporting raw pruned leaves as solved cases would conceal the remaining failure.


## Shared first-production relaxation closes one information gap

The following records standalone verification; optional planner integration follows below.

`shared_first_bound.bound` is a new standalone bound for a supported two-book, single-line calendar. The prior prefix envelope maximizes each future scenario independently, allowing the first production decision to benefit from hidden future demand. This candidate instead enumerates one common first production count y, then averages optimistic subsequent returns across the posterior. Its structure is `max_y sum_s weight_s * relaxed_return(y, s) / sum_s weight_s`, rather than a sum of separate scenario maxima. This is a bound on a common first decision, not a forecast or change to agents' information.

The fixed purchase prefix is charged once and added to held inputs. Each candidate y pays conversion plus the cheapest remaining-current-offer cost of missing ingredients. It receives the first book's actual `min(opening finished + production, demand)` receipts. Remaining held inputs and unsold finished goods carry into an optimistic second-book profit calculation. Future input prices take the minimum of remaining current offers and later offers: this deliberately allows advance buffers at an optimistic price, rather than overcharging them at a more expensive future quote. Fees, gates, cash/storage limits and supplier capacities remain relaxed; terminal input/finished values use their table maxima. Supplied nonnegative fee income is included unless transfer-neutral analysis is requested. Exact fractions carry the common-decision comparison, with the existing outward-rounded line envelope and a conservative final ledger-arithmetic cushion.

Eligibility requires one installed line, no already-open book, the current purchase followed by a first book, an optional tick boundary, a second purchase and a second book, unchanged quotes, ordinary independent settlement, and the single line active in both purchases. An explicit `max_first_batches` limits enumeration; larger capacities and unsupported calendars return an infinite bound and do not restrict the planner's feasible domain. Returned counts expose first-batch states and scenario evaluations for later budget charging. The primitive is not yet called by planner traversal.

For capacity 2, two suppliers per input, two periods and correlated zero/full demand, the shared-decision bound is $6.50 plus its numerical cushion, matching the analytical exact optimum and tightening the earlier scenario-independent envelope. Fourteen shared-first/prefix/continuation tests pass in the worktree and archived source. They check all matching small prefix completions against exact future policies and exercise advance-versus-later input prices, expensive owned basis, existing finished stock, fee income, terminal values, unsupported calendars and explicit work limits.

`stats/buying-implementation/20261012-shared-first-bound/` preserves the example, source/catalog/runtime identity and test/replay logs. This closes a relaxation gap in a small supported calendar, not the master plan's solver gate. Optional integration must charge enumeration work and preserve full policies/accounts before the original scaling screen can establish whether it removes any remaining limit.


## Shared-first bound integrated with reserved work

`shared_first_batches=N` optionally adds the two-book shared-decision bound to `prune_prefix=True`. Zero disables it. Before evaluation, the planner reserves `1 + (max_batches + 1) * (posterior_branches + 1)` units from the remaining combined-work allowance. The actual charge is one call plus reported first-batch states and scenario evaluations. Insufficient reservation or capacity above N skips the optional bound and retains the existing exact search. The charge is included when deriving subsequent prefix and closing-solver allowances. No larger budget or approximate result is silently substituted.

The ordinary prefix envelope is tried first. Only a subtree it cannot prune receives the optional shared-decision bound; the same strict value tolerance applies. Counters separate calls, charged work, skipped opportunities and extra pruned prefixes. The option is restricted to the existing endogenous feasible-prefix path and stays off by default.

Twelve targeted tests pass. Full policies, traces, states and accounts match the prior solver for capacities 1, 2 and 4, both continuation funding variants and independent/persistent supplier modes. Option validation, capacity fallback, primitive prefix comparisons and existing fee counterexamples remain covered. All 24 untreated rows in the 32-case screen match the preceding run apart from timing.

The original 4,000-allocation/16,000-combined-work screen still completes 28/32. The largest endogenous-prefix case now reaches a later closing-solver work limit with 2,589 charged allocations; it has completed 511 prefixes, 530 ordinary bound evaluations, 4,650 shared-bound work units, 3,452 closing boxes and 6,813 proposal states. Those completed counts sum to 15,956 combined units; work inside the interrupted closing solve is not included. The new bound prunes 171 additional prefixes, but this is not a passed scaling case.

A separately labeled expanded diagnostic (20,000 allocations/100,000 combined units) finishes that case with exact planner value $26 and first allocation `(8,0,0,8,0,0)`. Actual charged work is 4,908 allocations and 41,148 combined units: 2,496 prefixes + 2,398 ordinary bound evaluations + 22,706 shared-bound work + 4,548 closing boxes + 9,000 proposal states. The value agrees with the fixture's analytical `3.25 * capacity`; the expanded run does not change the acceptance thresholds or completion count.

`stats/buying-implementation/20261012-phase-shared-first/` preserves the original-budget screen; `20261012-shared-first-expanded/` preserves the diagnostic. Both replay from archived source with elapsed time excluded. Remaining work includes reducing shared-bound and closing-certificate overhead, then rechecking the unchanged limits and full policies. No population speed or adoption claim follows from these small-case results.


## Exact relaxed-profit reuse reduces shared-bound work

`shared_bound_memo_size` optionally enables a bounded, per-solve LRU for completed shared-first relaxed profits. Zero disables it; positive capacity requires the shared-first bound. It stores no selected baskets, branch states, histories or accounting results. Normal state/prefix/calendar validation still precedes lookup.

The reusable quantity is the exact fractional profit before the additive `state.cash - initial.cash + initial.arrears - state.arrears - compulsory_prefix_goods` offset. The key contains the line, post-prefix held inputs, remaining-current cheapest prices, existing finished stock, selling quote and ordered weighted future paths (demands, relaxed future prices and terminal/fee values). The caller applies its own offset and numerical cushion, including its offer count and cash scale, after lookup. Thus different sunk spending or basis can reuse the same relaxed profit without reusing an incorrect total value. Basis, identities, funded bids and physical constraints are omitted only where this mathematical bound explicitly relaxes them; the actual optimizer still enforces them.

A hit charges the existing one-call work unit and reports zero batch/scenario evaluations. Worst-case reservation remains required before lookup, so a cache hit is not assumed in advance to bypass the budget. Capacity, hits, misses and peak entries are reported. Unsupported/nonfinite results are not stored. The cache is recreated for each solve.

The first attempt keyed complete bound values, including cash and compulsory payment, and obtained only 16 hits before the original budget failed. Its source/screen is preserved in `20261012-phase-shared-memo/`. The revised exact-profit cache is preserved in `20261012-phase-shared-profit-memo/`. The original 32-case screen remains 28 exact/four limits; all 24 untreated controls are unchanged apart from timing, and all final rows replay from archived source.

In the separately labeled expanded capacity-eight case, the revised cache records 1,001 hits, 188 misses and 188 peak entries at capacity 4,096. Shared-bound work falls from 22,706 to 5,057, saving 17,649 units. Complete results are identical except prefix work/cache counters: value $26, selected policy, traces, state, accounts, allocation counts and other search diagnostics all agree. Total combined work falls from 41,148 to 23,499, while allocations remain 4,908. Both still exceed the original 16,000/4,000 thresholds; the diagnostic does not count as a passed acceptance case.

Seven targeted memo/shared-bound tests pass, covering exact reuse with changed cash offsets and relaxed basis/preferences, misses for changed quotes, bounded eviction, complete planner equality, per-solve isolation and invalid capacities. The expanded full-result comparison is preserved and replays byte-identically from archived source. This establishes an exact reduction in repeated work, not a population performance result or completion of the remaining solver gate.


## Fresh proofs around reusable hints reach 29 of 32 cases

`closing_proposal_memo_size` optionally supplies a per-solve bounded LRU of allocation hints to certified closing search. The cache key retains the prepared problem's structure but normalizes cash, output-value constants, basis, incumbents, bids, fees and funded caps. These are deliberately *not* claimed equivalent economic states. Every retrieved hint must pass a new strict ledger-value dominance proof using the actual complete decision. An infeasible, invalid, tied or otherwise unproved hint falls back to the complete original lexicographic search; no cached proof or objective value is trusted.

Lookup/key work costs one proposal-work unit. A miss also charges the existing batch scan and its two candidate evaluations; a hit skips those and still charges the fresh candidate evaluation and all proof boxes. The proof retains its bounded share of remaining work and the full fallback remains available. The memo is restricted to certified closing mode and defaults off. Malformed hints are rejected as unproved before array evaluation; the initial adversarial test exposed an exception in this path, which is fixed and preserved in the failed-test log.

The first narrower key had little reuse and is archived in `20261012-phase-proposal-memo/`; the broader proved-hint variant before changing bound order is in `20261012-phase-proposal-hints/`. The final optional path also tries the shared-first bound before the ordinary scenario-independent prefix bound, avoiding the latter's cost when the stronger bound already rejects the subtree. If it cannot reject, the ordinary bound remains available. Neither proof condition nor search order changes.

Under the original 4,000-allocation and 16,000-combined-work budgets, the final screen completes **29 of 32** cases. The capacity-eight, three-supplier, two-period endogenous feasible-prefix case now completes with value $26 and first basket `(8,0,0,8,0,0)`. It uses 3,192 allocations and 15,281 combined work units: 2,496 prefixes + 892 ordinary bound evaluations + 5,067 shared-bound work + 4,548 closing boxes + 2,278 proposal work. Its 1,000 fresh strict certificates include 858 cached hints and 142 generated hints. No acceptance budget was increased.

The three remaining limits are the same dimensions under frozen/exhaustive, frozen/feasible-prefix and endogenous/exhaustive configurations. The new completion does not establish full-population performance or eliminate general multi-line/calendar scaling work. Single screen timing is not an isolated benchmark.

Eleven targeted proposal/certificate/shared-bound integration tests pass. Adversarial tests inject incorrect and out-of-stock hints and change cash, historical basis and loyalty conditions; every result agrees with fresh search. Complete policies/accounts also match at capacity four. The newly completed capacity-eight result matches the preserved expanded-budget result in full policies, traces, states, accounts and non-work diagnostics; only allocation/prefix/closing work counters differ. All 32 final rows replay from archived source, excluding elapsed time.

`stats/buying-implementation/20261012-phase-proof-first/` contains the final specification, complete result comparison, source/runtime identity, test logs and verification; its replay is `20261012-phase-proof-first-replay/`. Earlier failed attempts remain preserved. This is the current small-screen frontier, not a production-adoption result.


## Explicit slot-deficit comparator enables safe frozen-path pruning

The planner now accepts `funding='slot-deficit-v1'` as an explicit pure comparator. For each offer o its frozen cap is `max(0, company.slots[o.material] - state.held[o.material])`, exactly the former scaling harness callback. Multiple offers for one material receive that same cap; actual cumulative fallback, lots, cash, fees, storage and production feasibility remain enforced by normal execution. This names an existing experimental replenishment comparator; it does not adopt price-insensitive industrial willingness to pay or resolve D3.

Because this rule has no arbitrary callback effects, it can use the same validated-calendar continuation and prefix bounds. Other callbacks remain ineligible for pruning and are rejected before invocation when pruning is requested. Unknown funding names fail explicitly. Output metadata distinguishes `slot-deficit-v1` from `explicit-callback`. The harness uses the new representation only with the explicit `trustedFrozenFunding` flag; older specifications retain their callback behavior.

The unchanged dimensions and 4,000/16,000 budgets now complete **30 of 32** screen configurations. All 16 endogenous rows are unchanged from the preceding screen except timing. The newly completed capacity-eight frozen feasible-prefix case returns $26 with 466 allocations and 4,823 combined units: 580 prefixes + 212 ordinary bound evaluations + 3,182 shared-bound work + 576 closing boxes + 273 proposal work. All feasible-prefix rows complete; the largest frozen and endogenous exhaustive comparison rows still hit limits. This distinction does not establish scaling beyond the tested one-line fixtures or population practicality.

Nine targeted tests pass, verifying callback/built-in/pruned complete-result agreement at capacities one, two and four, independent/persistent supply, unknown names and unchanged rejection of arbitrary callbacks. An old guard-message assertion expected “endogenous”; its failure is preserved and its updated assertion checks the continuing arbitrary-callback prohibition. The model's expanded explicit-rule contract, not a weakened safety guard, motivated that test update.

For the newly completed capacity-eight case, a separate unpruned callback reference is allowed a diagnostic 200,000-allocation/1,000,000-combined-work ceiling. It completes at 81,538 allocations. The explicit pruned case uses the original acceptance limits. Full selected policies, traces, states and accounts match; only funding identity and search-work diagnostics differ. No larger reference allowance is counted as an acceptance pass.

`stats/buying-implementation/20261012-phase-slot-funding/` preserves the specification, tests, full callback comparison, source identity and verification. All 32 screen rows replay from archived source with timing excluded. Remaining work includes supported multi-line/calendar scaling, full-population performance, economic calibration and integration; production funding defaults are unchanged.


## Two-line shared-input screen exposes closing-search limits

The scaling harness now supports `lines=2` without changing its original one-line fixtures. The second installed line is a distinct output with recipe `(2,0)`, quote $12, conversion $0.50 and output space 2; the first remains recipe `(1,1)`, quote $10, conversion $0.50 and output space 2. Both have batch capacity c. Input slots are `(3c,c)`, supplier stock per material matches its slot capacity, company storage is `12c`, and finished caps are `2c` per line. Both lines execute in the existing fixed order in each purchase phase, sharing cash and ingredients. This is not independent line optimization or self-supply.

The specification retains the original 4,000-allocation/16,000-combined-work limits and eight dimension combinations, uses the optimized feasible-prefix path, and compares explicit slot-deficit and endogenous funding. There are 16 two-line configurations. Demand is per distinct product; the two products share the declared zero/full scenario, not a common pool of substitutable demand. Fees, rent and terminal values remain zero. This synthetic screen measures algorithm scope, not representative firms or economic calibration.

Nine configurations finish exactly and seven hit explicit limits:

| Capacity / suppliers / periods / outcomes | Slot-deficit | Endogenous |
| --- | --- | --- |
| 1 / 1 / 1 / 1 | Exact, $13 | Exact, $13 |
| 2 / 2 / 1 / 1 | Exact, $26 | Exact, $26 |
| 4 / 2 / 1 / 1 | Exact, $52 | Exact, $52 |
| 8 / 3 / 1 / 1 | Closing box limit | Closing box limit |
| 1 / 1 / 2 / 2 | Exact, $8.50 | Exact, $8.50 |
| 2 / 2 / 2 / 2 | Exact, $17 | Closing box limit |
| 4 / 2 / 2 / 2 | Closing allocation limit | Closing allocation limit |
| 8 / 3 / 2 / 2 | Closing box limit | Closing box limit |

For certain trade, full output earns `(10+12) - (3*2+1*2) - 2*0.5 = $13` per unit of capacity per period. At capacity one, the independent ordinary event tree also verifies $2 for a single uncertain period and $8.50 for two correlated periods, with the optimized full policies and accounts matching. The first production uses both lines in the tested optimum.

The larger failures occur in closing search, where the single-line proposal generator and shared-first-production bound deliberately do not apply. In the largest endogenous two-period case, the first subsequent hypothetical closing solve exceeds the box allowance before returning any completed closing work. Skipping an unsupported shortcut preserves correctness but does not meet the multi-line scaling requirement. Next work must strengthen bounds or proposals for joint line production and shared-input requirements; silently restricting installed lines or choosing each line independently would change the required model.

Four targeted harness/phase-scaling tests pass, including analytical values, full ordinary/optimized comparisons, structure and invalid line counts. An independent comparison to all eight preserved original case files confirms the single-line fixtures are unchanged. All 16 new screen rows replay from archived source except timing. `stats/buying-implementation/20261012-phase-multiline-screen/` preserves the frozen specification, complete cases, failures, source/runtime identity, tests and verification. The one-line 30/32 result remains historical scope-specific evidence; it does not close D6 for supported multi-line companies.

## Joint-line proposal experiment: proof bounds remain the bottleneck

`closing_search='compiled-joint-certified-boxes'` enables an experimental joint-line hint in addition to the existing single-line hints. The ordinary `compiled-certified-boxes` mode retains its prior eligibility and behavior. The new mode shares the same strict ledger proof, exact fallback, memo validation and work limits.

For each joint batch vector `b`, the proposal sums required materials across all installed lines: `need[m] = max(0, sum(recipe[r,m] * b[r]) - held[m])`. It rounds this aggregate deficit to the common supplier lot, fills cheapest available quotes, and ranks the relaxed output value less goods and conversion spend. Existing inventory is deducted once. The proposal ignores some execution constraints and may choose a target that actual sequential production does not realize. It therefore supplies no optimality certificate: actual execution and strict dominance over the entire complement remain mandatory. Mixed supplier lots or nonzero terminal input values do not receive this proposal treatment. Complete fallback still supports those cases.

The Cartesian batch-state count is reserved against the speculative quarter of the remaining work budget before enumeration. Two generator evaluations and the fresh proof evaluation remain charged. Memo entries are allocation hints only; changed cash, basis, fee eligibility or funded demands require a new proof. Ties, infeasible hints and exhausted proofs retain the original complete traversal.

The unchanged two-line screen still finishes **9/16**, with identical completion statuses, exact values and first allocations. Some uncertain-demand subsolves gain certificates, but all nine completed configurations use more allocations overall. For example, the capacity-two/two-period frozen case rises from 1,829 to 1,878 allocations; capacity-four/one-period endogenous rises from 1,689 to 1,705. This is not an optimization acceptance pass. Keeping it opt-in preserves the previous mode while retaining a candidate generator for future stronger bounds.

Fifteen targeted tests pass across joint proposals, multi-line policy comparisons, strict certificates and memo adversaries. They include aggregate shared inputs, existing stock counted once, tight cash, expensive historical basis, loyalty fees, invalid hints and complete event-tree policy/account comparisons. `stats/buying-implementation/20261012-phase-joint-proposal-opt-in/` preserves the final specification, source/runtime identity, test log and comparison. All 16 rows replay identically except timing from its archived source, launched outside the repository, with archived source hashes verified. The initial directly integrated attempt and its replay remain in `20261012-phase-joint-proposal/` and `20261012-phase-joint-proposal-archive-replay/`; the preliminary replay launched from the repository is not treated as isolated-source verification.

The next solver requirement is a conservative joint-line closing bound that deducts aggregate required materials and conversion costs without granting both lines the same shared input. Generating a plausible basket alone does not address that proof gap. Population performance, broader calendars, economic suitability and production adoption remain unverified.

## Standalone joint-line closing bound

`closing_joint_bound.bounder` implements a bounded reference relaxation for the missing joint-line proof. For each batch vector `b`, it requires `R[m] = sum(recipe[r,m] * b[r])` across all installed lines. A box contributes opening inventory plus compulsory lower-bound purchases; remaining deficits are supplied from the box's cheapest available residual offers. Vectors requiring more material than the box can supply are excluded. Opening inventory is counted once, including repeated-input recipes.

The bound subtracts a conservative lower bound on goods spending and applies each line's rounded conversion expense in installed execution order. It then evaluates actual output quantities against each supplied demand scenario. Finished-stock terminal values use the exact resulting quantity; remaining-input values use a prefix maximum over possible residual inventories. Fees, margin gates, funded caps, lots and storage constraints are relaxed, so the set includes every feasible sequentially executed output vector. The output vector is a bounding device, not a new production action available to a company.

Goods prices are represented with `Fraction`; a box-wide allowance covers the ledger's rounded positive products and sequential goods summation. Cash, sales, terminal sums and posterior values use outward rounding. The function returns `upperValue` and `batchStates`. It reserves the full Cartesian count before enumerating; insufficient `max_states` returns infinity with zero enumerated states. An over-slot compulsory box returns negative infinity. A future integration must charge the state/scenario work, not merely one bound call, and retain the branch whenever the bound is unavailable.

| Capacity per line | Earlier one-line-anchor upper value | Joint upper value | Known optimum | Joint states |
| --- | ---: | ---: | ---: | ---: |
| 1 | 17.50 | 13.00 | 13.00 | 4 |
| 2 | 35.00 | 26.00 | 26.00 | 9 |
| 4 | 70.00 | 52.00 | 52.00 | 25 |
| 8 | 140.00 | 104.00 | 104.00 | 81 |

Upper values retain a small positive numerical allowance; the table rounds for display. `stats/buying-implementation/20261012-closing-joint-bound/bounds.json` preserves full values. This closes the relaxation gap in these particular full-box, certain-demand fixtures; it does not establish tightness in all boxes or scenarios.

Seven targeted tests pass across the joint-bound and existing closing-cost modules. New checks independently execute every feasible basket in sampled boxes across 30 seeded two-line cases, plus explicit lot/output-yield and posterior cases. They cover cash scarcity, expensive basis, fees, nonmonotone terminal values, shared/repeated inputs, subnormal and large monetary scales, and refusal under insufficient work budgets. Source, commit, catalog files, runtime identity and logs are archived in the same directory. All seven tests also pass from the archived source outside the repository, and archived source hashes verify. The primitive is not yet used for pruning. The multi-line scaling screen therefore remains 9/16; compilation, integration, strict-proof fallback parity and the unchanged screen are the next verification steps.

## Compiled joint-line bound verified against the rational reference

`closing_joint_compiled.bounder` now provides the compiled counterpart to the standalone joint-output relaxation. It shares validated array packing with `closing_cost_compiled`; that existing bound retains its algorithm and return contract. Aggregate input requirements are checked against available quantities before accumulation. The batch-state Cartesian product uses a checked multiplication against the signed-integer work budget, avoiding overflow before traversal.

The compiled lower goods-cost calculation rounds downward and subtracts an upward-rounded allowance for actual ledger multiplication and summation error. Cash subtraction, sales, terminal values and posterior accumulation round upward. This may be looser than the rational reference, but must never be lower. It reports the same `upperValue`/`batchStates` fields and returns an unavailable infinite bound before enumeration when the state budget is insufficient.

Eight targeted tests pass. The four joint reference cases also run through a wrapper that checks the compiled value is at least the rational value for every tested box and that state counts match, then checks feasible baskets against independent ledger execution. Additional tests cover subnormal prices, overflow prices and oversized integer budgets. The existing compiled closing-cost tests retain full policy parity across funding, supply and money-scale variants after extracting shared packing. The evidence is archived in `stats/buying-implementation/20261012-closing-joint-compiled/`, including source hashes, runtime/commit/catalog identity and test logs. All eight tests also pass from the archived source outside the repository, and archived source hashes verify.

No traversal currently invokes this bound. Integration must reserve and charge joint state/scenario work within the existing combined limit, retain unsupported/unavailable branches, preserve strict tie handling and complete fallback, and re-run the unchanged multi-line screen. The 9/16 result and all broader implementation/adoption gaps remain open.

## Joint proof integration completes thirteen of sixteen cases

The opt-in `compiled-joint-certified-boxes` mode now uses the compiled joint bound inside strict complement proofs for multiple installed lines. Ordinary certified search remains unchanged. Each proof first tries the existing inexpensive bounds. If they cannot reject a box, it may use the joint bound after reserving `1 + product(max_batches[r]+1) * (1 + posterior_scenarios)` work units. The actual charge is `1 + batchStates * (1 + posterior_scenarios)`, reported separately as `jointBoundWork`. This deliberately charges a scenario allowance even for infeasible joint vectors.

Certificate work is boxes plus joint-bound work. The experimental mode reserves at most one quarter of remaining combined work for proposal generation and proof; unlike the ordinary mode's 256-box cap, it allows that full quarter for the joint proof. Unavailable bounds leave the box in search. Unproved/tied candidates retain the complete lexicographic fallback, and all spent joint work is deducted before fallback and later phase traversal. Exact closing-memo hits charge no repeated joint work. No work limit, action space or economic parameter increased.

| Capacity / suppliers / periods / outcomes | Frozen result | Endogenous result |
| --- | --- | --- |
| 1 / 1 / 1 / 1 | $13; 3 allocations / 16 work | $13; 4 / 28 |
| 2 / 2 / 1 / 1 | $26; 3 / 52 | $26; 16 / 261 |
| 4 / 2 / 1 / 1 | $52; 3 / 132 | $52; 16 / 661 |
| 8 / 3 / 1 / 1 | $104; 3 / 414 | $104; 22 / 2,730 |
| 1 / 1 / 2 / 2 | $8.50; 35 / 157 | $8.50; 80 / 418 |
| 2 / 2 / 2 / 2 | $17; 232 / 1,754 | $17; 1,218 / 10,515 |
| 4 / 2 / 2 / 2 | $34; 1,482 / 8,914 | Closing-work limit |
| 8 / 3 / 2 / 2 | Closing-work limit | Closing-work limit |

All completed rows fit the unchanged 4,000-allocation / 16,000-combined-work limits. The result improves from **9/16 to 13/16**. All previously completed values and first allocations remain equal. Seventeen targeted tests pass, including complete independent event-tree policy/account comparisons across funding and supply modes, wrong proposals, insufficient proof budgets, rational/compiled bounds and adversarial hints. All 16 screen rows replay identically except timing from archived source outside the repository. `stats/buying-implementation/20261012-phase-joint-proof/` preserves source/catalog/runtime identity, specification, tests, per-case results, diagnostics and verification; `20261012-phase-joint-proof-replay/` preserves replay.

The three limits still arise during closing search, chiefly after repeated joint evaluations: completed subsolves account for 13,584 joint work units in capacity-four endogenous, 13,664 in capacity-eight frozen, and 11,745 in capacity-eight endogenous. Interrupted subsolve work is still excluded from completed-work diagnostic totals, as before. Reducing repeated joint evaluation while preserving conservative bounds is the next target. General calendars, population performance, calibrated economic forecasts, world integration and adoption remain incomplete.

## Exact joint-bound reuse reduces work without clearing another limit

`joint_bound_memo_size` optionally enables a bounded per-solve LRU in `compiled-joint-certified-boxes` mode. Zero remains the default. Each entry stores a completed finite upper value for one exact bound-input/box key. The key includes held stock, slots, ordered offer materials/prices, line recipes/capacities/yields/conversion, old finished quantities, quotes, current/initial cash, liability change and every ordered posterior weight, demand, fee-income and terminal-value table. Box endpoints encode the current offer quantity constraints. No approximate matching or cached policy selection occurs.

Basis, supplier identity, funded bids, lots, gates and fees paid are absent because this particular bound relaxes them; actual proposal execution and strict proof still check them. Cash remains in the key: an additive profit shortcut cannot simply remove it because the bound includes cash feasibility and rounded ledger operations. Unavailable or nonfinite results are never cached. Exact hits charge one joint-work unit and zero enumerated batch states. Misses retain the existing state/scenario charge. The conservative reservation still precedes evaluation, including hits, so this change does not exploit a smaller hit-only reservation near exhausted budgets.

The unchanged screen remains **13/16**. All previous completion statuses, exact values and first allocations are preserved, and all completed rows remain within the original limits. Capacity-two/two-period endogenous joint work falls from 6,614 to 4,256 units, with 116 hits and 189 misses. Frozen cases have less repetition: capacity-four/two-period falls from 4,958 to 4,758 joint units. These are deterministic work counters, not population latency measurements.

Twelve targeted tests pass: exact reuse, changed cash/quotes/held stock/posteriors, bounded eviction, unavailable results, complete policy/account parity, proof-budget accounting and rational/compiled bound checks. `stats/buying-implementation/20261012-phase-joint-memo/` preserves the specification, source/runtime identity, test evidence and screen. All 16 rows replay identically except timing from archived source outside the repository, with source hashes verified. A separately saved capacity-two/two-period endogenous comparison also preserves complete policies, traces, states, accounts and non-work metadata with versus without the cache; its initial JSON serialization failure is retained alongside the corrected output. The new cache reduces repeated work but leaves all three closing-work limits open. Further reduction must preserve conservative arithmetic and the existing limits; increasing budgets is not counted as a solution.

## Joint-bound budgeting now uses the current box and cache result

A joint bound accepts an optional positive `work_budget`. An exact cache hit needs one unit; on a miss, the compiled primitive derives the current box's output limits and checks its full Cartesian count against `floor((work_budget-1)/(1+posterior_count))` before enumeration. Insufficient budget returns infinity with zero states and incurs the one-unit attempt charge. Nothing partially evaluated becomes a pruning bound or cache entry. The certificate supplies its actual remaining allowance and checks the returned charge does not exceed it.

This replaces the earlier whole-problem reservation, which could decline cheap hits or small boxes. Fourteen targeted tests pass, including explicit one-unit hit versus miss cases, box-specific reservations, full policy/account parity, integer/budget boundaries and rational/compiled comparisons. The unchanged screen remains **13/16**, and all thirteen completed rows—including allocation and work counters—are identical to the preceding cache screen. The three failures reach the same completed allocation counts (647, 79 and 64), so this reservation restriction was not the observed screen bottleneck.

`stats/buying-implementation/20261012-phase-joint-budget/` preserves specification, source/runtime identity, tests and results. All 16 rows replay identically except timing from archived source outside the repository, and source hashes verify. The change improves the budget contract but provides no demonstrated scaling gain in this screen. The remaining searches repeatedly solve closing decisions while exploring earlier purchases. Extending the common-first-decision prefix bound to multiple lines is a candidate next step; its soundness and benefit must be tested independently. Production defaults and all uncompleted master-plan gates remain unchanged.

## Joint first-production prefix bound: correct but not a scaling improvement

`shared_joint_first_bound.bound` extends the common-first-decision relaxation to multiple distinct output lines. It enumerates one joint first batch vector shared across posterior scenarios. Aggregate first input demand is `sum(recipe[r,m] * batches[r])`; existing/prefix stock is deducted once, and missing goods use cheapest remaining current quotes. Each scenario then receives independent optimistic second-period line envelopes. Those envelopes deliberately allow each line access to the residual shared input, so future recourse is relaxed rather than falsely executed independently. Current/future cheapest quotes allow advance buffers; fees, cash, margin gates and storage constraints remain relaxed. Explicit terminal tables contribute their supported maxima.

The supported calendar remains two ordinary independent sales books separated by one purchase and an optional tick boundary, with all installed lines active in both purchases. Other calendars return infinity. Exact relaxed profits may use the existing bounded shared memo before applying caller-specific cash/arrears/prefix-spend offsets and numerical allowance. Once all offers for an ingredient have been fixed, first batch ranges are capped by the actual available stock of that ingredient; impossible ranges are skipped.

`shared_first_joint_states=0` is the default. Enabling it requires feasible-prefix pruning. The planner reserves `1 + product(max_batches+1) * (1 + posterior_count * (line_count+1))` work, then charges one plus actual joint states and scenario/line-envelope evaluations. Multiple-line traversal tries the existing cheaper prefix bound first; ordinary single-line behavior and disabled-feature diagnostics are preserved. No incomplete result prunes a branch.

Fifteen targeted tests pass, including every matching continuation for all prefixes of a small two-line market, changing current/future prices, historical basis, fees, nonmonotone terminal values, exact memo offsets, fixed-input caps, unsupported calendars and complete policy/account parity across funding and supply modes. The empty-prefix small certain/correlated-demand fixtures reach the known optimum within the numerical allowance.

However, the unchanged enabled screen completes only **12/16**, versus **13/16** with this option off. Capacity-two frozen allocations fall from 232 to 108 and endogenous from 1,218 to 828, but capacity-four frozen now exhausts combined work after 9,678 shared-bound units. Capacity-eight endogenous reaches its limit before any shared-prefix call, so this bound cannot resolve that failure in its present location. The disabled control reproduces all 16 preceding rows, including diagnostics and counters, except timing. This option is experimental and is not the preferred screen configuration.

Evidence: `20261012-phase-shared-joint/` retains the initial shared-first attempt; `20261012-phase-shared-joint-cheap-first/` retains reordered bounds; `20261012-phase-shared-joint-fixed-inputs/` retains the final fixed-input cap variant and tests; `20261012-phase-shared-joint-control/` verifies unchanged disabled behavior, all under `stats/buying-implementation/`. All 16 final enabled rows replay identically except timing from archived source outside the repository, with source hashes verified. Further work should reduce closing-proof cost where early hypothetical funding prevents prefix pruning from running; this result does not justify larger budgets or restricted ownership. The full master-plan implementation remains incomplete.

## Standalone cash-relaxed closing bound for future reuse

`closing_cash_relaxed_bound.bounder` investigates reuse across funding queries with different cash offsets. It normalizes both opening and initial cash to an upward-rounded amount covering the box's maximum goods spend and maximum conversion plus one unit, and normalizes both arrears to zero. It invokes the rational joint closing bound on that normalized state. This removes cash scarcity from the bound's production-vector set; it does not give a buyer extra money or change actual funded decisions.

Let `U0` be the normalized upper value, `D = current_cash - initial_cash - current_arrears + initial_arrears`, and `R = sum(exact_float_weights) / exact_float(fsum(weights))`. The translated bound is an outward-rounded `U0 + D*R + E`. Keeping `R` matters: the floating posterior denominator need not equal the exact rational sum of the weights.

The allowance `E` is explicit rather than inherited from another caller. An exact rational magnitude covers absolute opening/initial cash and arrears, maximum box goods and conversion, maximum gross sales, terminal-table absolute maxima, fee income and normalized cash. Twice that magnitude bounds intermediate operations after allowing rounding. A deliberately conservative operation count `64 + 32*lines + 4*inputs + 2*offers` times its ulp bounds leaf arithmetic, including compensated sales summation; the function rejects the bound if that allowance consumes the magnitude. Separate product, posterior-reduction and division ulp allowances cover weighted evaluation. The final translation uses `Fraction` and rounds outward. Nonfinite scales or an insufficient joint-state budget return an unavailable infinite bound.

Seven targeted tests pass across the new reference and joint-bound modules. New independent ledger comparisons cover every feasible basket in selected boxes under cash from zero through large balances, nonzero initial offsets/arrears, prices scaled by `1e-8`, `1`, and `1e8`, weights scaled by `1e-200`, `1`, and `1e100`, fees, expensive historical basis and signed terminal values. A certain-demand fixture remains within `1e-8` of the $13 optimum. These tests verify the stated finite fixture scope; they are not a population or economic-model acceptance claim.

`stats/buying-implementation/20261012-closing-cash-relaxed/` preserves source hashes, commit/runtime/catalog identity and test logs. All seven tests also pass from archived source outside the repository, and source hashes verify. This is a standalone reference only: no normalized profit cache, compiled port or planner pruning integration is enabled. Those steps must preserve the allowance and complete policy/account parity before any scaling claim. The preferred screen remains 13/16 and the full implementation goal remains open.

## Normalized cash reuse integrated; remaining failure types change

The cash-relaxed bound now supports compiled joint enumeration and a bounded `ProfitMemo`. It caches only the finite normalized upper value. Its key retains slots, held inputs, ordered materials/prices, line recipes/capacities/yields/conversion, old finished quantities, quotes, ordered posterior weights/demand/fee income/terminal tables, box endpoints and backend identity. Actual cash and arrears are intentionally excluded: every hit recomputes the caller's exact offset, posterior normalization factor and numerical allowance. The compiled and rational backends have separate keys. Unavailable normalized enumerations are not cached.

`cash_relaxed_joint_bound=True` optionally selects this bound in `compiled-joint-certified-boxes`; it defaults false. Existing `joint_bound_memo_size` controls the normalized cache when selected. Actual proposal execution, strict proof, tie handling and complete fallback remain unchanged. One work unit is charged on a hit; a miss charges completed batch/scenario work. If translation becomes unavailable after enumeration—for example at a `1e308` cash balance—the enumerated states remain charged. Fresh and cached translated values agree in tests across changed cash and arrears.

The unchanged cash-relaxed screen completes **13/16**, preserving earlier completed values and first allocations while reducing joint work substantially: capacity-two/two-period endogenous falls from 4,256 to 1,772; capacity-four/two-period frozen falls from 4,758 to 1,108. Capacity-four endogenous now reaches a prefix-work limit after 3,041 allocations; capacity-eight frozen reaches 4,001 allocations and the allocation limit. Capacity-eight endogenous still fails in closing work before earlier-prefix pruning. These are different bottlenecks from simply repeating expensive closing bounds.

Combining normalized reuse with the optional joint-first prefix bound also completes 13/16. Capacity-four frozen completes with 246 allocations, recovering the case lost by the earlier prefix-only experiment, but adds 9,854 shared-prefix work units. The combination still fails larger cases, so it is not a completed scalability gate and no universal best configuration is claimed.

Seventeen targeted tests cover normalized cache keys, cash/arrears translation, compiled-versus-rational comparison, independent ledger outcomes, full policy/account parity under both funding and supply modes, the combined prefix option, unavailable translations, work budgets and invalid options. Final source and screen evidence are in `stats/buying-implementation/20261012-phase-cash-relaxed-accounted/`. The initial integration is preserved in `20261012-phase-cash-relaxed/`, and the combined experiment in `20261012-phase-cash-shared-joint/`. Both 16-row screens replay identically except timing from archived source outside the repository; source hashes verify. No economic parameter, action set or search budget changed. Broader calendars, population performance, model suitability, world integration and rollout remain incomplete.
