# Compiled continuation candidate: implementation contract

Status: proposed implementation architecture, 2026-10-12. It preserves the existing experimental economic contract and does not adopt forecasts, change D1/D2, authorize approximation, or enable production purchasing. It is the next structural implementation step under D6 of the [master plan](buying-behavior-implementation-plan.md).

## Why change direction

The general Python event-tree solver is an independent verification oracle. The latest normalized-bound configuration completes 13 of 16 synthetic two-line cases under 4,000 allocation and 16,000 combined-work limits. Three cases still fail, and full-population execution has not been demonstrated. Success in these cases would remain insufficient: they are small supplied calendars, not a representative production workload.

The [phase contract](buying-behavior-v2-phase-oracle.md#scaling-screen-oracle-remains-unsuitable-for-population-execution) already requires a different continuation representation. Retain all prior bounds, failed experiments and oracle fixtures as evidence. Do not treat further cache/pruning screens as completion of stage 6.

The proposed candidate lowers complete calendars into typed data, executes transitions in compiled loops and evaluates conditional decision graphs using an explicit bounded work arena. This is an exact candidate, not a claim of polynomial complexity. If it remains impractical, report that limitation and prepare a concrete approximation decision with measured loss and funding consequences; do not silently return an unfinished incumbent plan.

## Representation and behavior contracts

| Component | Required representation and invariant |
| --- | --- |
| Company structure | Integer recipe matrix, input spaces/slots, finished caps, installed line order and conversion/quote/overhead data. Preserve distinct outputs, shared inputs, repeated ingredients and recipe yields. |
| Calendar | Integer event kinds and stable label IDs; scenario/event offsets into contiguous payload arrays. Labels are interned outside compiled loops and retain their original text for diagnostics. |
| Events | Support every current ledger event: Purchase, OpenBook, SettleBook, SharedSettleBook, SetQuotes, Rent and EndTick. Payload lengths and integer ranges are validated before execution. An unsupported event produces an explicit error, never silent omission. |
| Offers | Stable material/supplier IDs, exact order, price, stock, lot, reliability and explicit or generated funded quantities. No supplier sorting that changes lexicographic tie order. |
| State | Cash, input quantities/basis, finished quantities/basis, quotes, incumbents, arrears, fee EMA and current-tick fees, open-book snapshot, completed-phase flags and rent-settled flag. No rounding or binning to merge states. |
| Accounts | Posted goods, conversion, sales, COGS, fees, rent and payments remain separate from value. First implementation retains complete accounts in state identity; stripping sunk accounts requires a separate equivalence proof and caller-specific replay. |
| Posterior | Ordered positive scenario weights and remaining calendars plus explicit terminal tables. Equal physical balances alone do not identify a decision state. Scenarios with different future conditional distributions must remain distinct. |
| Supply | Explicit independent snapshots or persistent cumulative arrivals. Real purchases reduce later persistent supply; hypothetical added stock follows the existing tested continuation-funding boundary. |
| Decision graph | A node identifies a full validated state, event position, conditional scenario group, supply remainder, neutral-value mode and actual/hypothetical funding role. Begin with conservative full keys; canonicalization is a later proved optimization. |
| Actions | Complete feasible split baskets, including no purchase and unmatched buffers, under shared cash/storage, lots and stock. Production remains the installed sequential ledger transition, not an independently selectable output vector. |
| Observations | Preserve the oracle's observed event and realized trace grouping. Future demand and terminal tables cannot enter the observation signature before their declared observation point. Do not pre-partition by hidden outcomes. |
| Funding | Preserve continuation-v2 own-quote queries with other materials' quotes retained, current hypothetical fees removed and current hypothetical incumbents held fixed. Keep rejected reference-only and transfer-neutral variants explicit comparators. |
| Numerical behavior | No fast-math. Preserve compensated sums, posterior reduction order, monetary tolerance and lexicographic tie semantics. A mathematical value equivalence is insufficient if it changes a ledger boundary or the existing non-transitive tolerance behavior. |

## Implementation order and reviewable outputs

1. **Typed calendar compiler and lossless decoder.** Validate all existing event forms and terminal tables. Round-trip event type, labels, identities, quantities, floats and ordering. Check array dtypes, offsets, bounds, mutation isolation and deterministic byte identity. This stage does not execute economic decisions.
2. **Compiled transition executor.** Differentially replay explicit allocation sequences against `phase_ledger.apply`, event by event. Cover full state, books, accounting, phase/rent guards and each supported event. Retain an independent reference; do not make the oracle call the candidate implementation.
3. **Observed-information grouping.** Construct conditional groups from the same observable data as the oracle. Verify converged-balance/different-history counterexamples, hidden demand, shared books and supplier observations before adding search.
4. **Explicit decision/funding work stack.** Replace recursive Python calls with typed frames. Preserve actual versus hypothetical state, quote queries, future fees and persistent stock. Record high-water memory and reject arena exhaustion with a complete work diagnostic.
5. **Exact conditional search and replay.** Preserve action/tie traversal and complete choices. Introduce validated bounds individually. Return exact policies only after every live alternative is resolved; replay selected actions to obtain traces and accounts rather than reconstructing financial postings from objective differences.
6. **Differential verification.** Compare complete policies, states, funded bids, preferences, fees, traces, posted accounts and terminal values to independently captured oracle results. Include every supported event/ownership case, not only the 16-row screen. Cache-off and cache-on results must agree. Preserve all failed comparisons.
7. **Representative feasibility gate.** Construct a declared cohort from actual configured company/line/catalog distributions and supplied calibrated-or-explicit forecast workloads. Measure compile/startup, warm median/p95, memory, recording and projection costs. Check full-population timing against both original and corrected baselines. Synthetic work counts remain diagnostic, not the acceptance gate.

Only after these steps pass should the candidate be connected to world execution. A missing transition, truncated horizon, fewer suppliers, dropped line or altered forecast is an unsupported scope change, not a performance optimization.

## Separate decisions that this work cannot resolve

- Forecast distributions, cold starts, censored-demand extrapolation, temporal dependence and terminal values still require explicit assumptions and economic evidence.
- The continuation funding model's exposed fee-avoidance incentive remains a separate adoption question. Faster exact execution does not settle it.
- D3 mechanics correction remains an explicitly labeled replenishment comparator until its contract and gates are settled.
- Held-out generations, shocks, fairness, checkpoint continuation, live dashboard integration, memory/latency gates and the final transition/rollback decision remain required.

## Current evidence and next action

`phase_ledger.py`, `scenario_validation.py` and `phase_oracle.py` remain the independent comparison boundary. The candidate now connects typed calendars, all seven compiled transitions, resident replay, numeric observed histories, exact action traversal, persistent supply and continuation-v2 funding through an explicit Python control stack. Small-calendar comparisons cover selected policies, accounts, funded quantities and query values. Arena-backed search now retains numeric branch handles, history/funding IDs, group membership, policy/result records, selected leaf IDs and scalar control fields in bounded arrays. Temporary adapters, action/query objects and control dispatch still use Python. The next structural work is a compiled driver over these buffers, followed by representative performance and economic validation. No request to weaken supported behavior or approve live rollout is made by this document.

## First implementation coverage matrix

The calendar compiler must round-trip these fields before its output drives execution. A successful decode is representation evidence only; transition equivalence still requires stage 2 above.

| Event type | Exact payload beyond event kind and label |
| --- | --- |
| Purchase | Ordered offers `(material, supplier, price, stock, lot)`; `funded_demands`; `reliability`; `fee_unit_cost`; `fee_multiple`; `active_lines`; `rent_bill`; `rent_threshold`; `overhead_timing`. An empty funded-demand tuple stays empty; it is not synthesized as zeros. |
| OpenBook | No additional payload. Preserve the label shared with its later settlement. |
| SettleBook | `demand` per installed line and `fee_income`. |
| SharedSettleBook | All ordinary settlement fields plus ordered groups and each group's ordered line indices. Retain the subclass identity. |
| SetQuotes | The ordered `quotes` tuple. |
| Rent | `bill` and `threshold`. |
| EndTick | `alpha`. |
| Scenario boundary | Probability and separate input/finished terminal tables, including ragged lengths and signed values. |

Use separate integer and float arrays; never route stable integer IDs through floating-point storage. Record schema identity and explicit lengths/offsets for ragged payloads. The first compiler must reject malformed offsets, unknown event kinds and integer overflow clearly. Production integration cannot silently shrink the supported state range: a candidate representation limitation must remain visible and retain the independent reference path until resolved.

Tests must include repeated labels where legal (including matching book/settlement and later ticks), duplicate purchase labels where illegal, no offers, differing line/input counts, multiple posterior paths with identical visible prefixes, nonuniform lots, multiple active lines and independently owned arrays. Encode/decode must not mutate the input dataclasses or expose an array alias whose mutation changes another compiled program. Byte identity must be checked from independently compiled copies, not a shared object.


## Implemented schema 1 and verification

`compile_calendar(company, initial, scenarios)` validates state, calendar structure and probability mass, then returns a `Program`. `decode_calendar(program, company, initial)` validates dtypes, dimensions, offset ranges, event IDs, payload lengths and ledger semantics, then verifies canonical re-encoding. Unknown schemas, malformed payloads, unused/noncanonical label tables and unsupported integer/float conversions fail explicitly.

The program contains schema version, input/line counts and an immutable tuple of labels, plus ten contiguous one-dimensional arrays. Integer arrays use little-endian signed int64; probability, event-money and terminal-value arrays use little-endian float64. Arrays are backed by fresh immutable bytes, so independent compilations do not share storage and callers cannot re-enable writing to the data. Stable integer IDs never pass through float storage. Non-exact float64 conversion is rejected rather than rounded silently.

| Array | Meaning |
| --- | --- |
| `probabilities` | Original ordered scenario probabilities, including zero-weight paths. |
| `scenario_offsets` | Event boundaries per scenario. |
| `event_kinds`, `event_labels` | Event kind (Purchase=0 through EndTick=6 in the declared kind table) and interned label index. Shared settlement has its own kind. |
| `integer_offsets`, `float_offsets` | Boundaries into per-event integer and float payloads. |
| `integers`, `floats` | Typed event payload data. |
| `terminal_offsets`, `terminal_values` | Ragged terminal tables in scenario order, then inputs followed by finished lines. |

Purchase integer payload is `(offer_count, funded_count, active_count, after_flag)`, followed by ordered `(material, supplier, stock, lot)` rows, funded demands and active-line indices. Its float payload is `(fee_unit_cost, fee_multiple, rent_bill, rent_threshold)`, followed by prices and reliability. Ordinary settlement stores count/demand integers and fee income; shared settlement adds group count and length-prefixed line-index groups. Quotes store their count and ordered floats. Rent stores bill/threshold; EndTick stores alpha; OpenBook has no additional payload.

Twenty-seven targeted tests pass across the new representation, independent ledger and shared-sales modules. New tests cover all seven event types, all purchase fields, repeated book/tick labels, empty offers and funded demands, signed/ragged terminal tables, zero-weight and empty calendars, supplier ID `2**53+1`, int64 overflow, byte identity, isolated read-only buffers and corrupted encodings. A fixed purchase payload is specified independently of the decoder. Original and decoded calendars yield equal complete oracle results in three single/multi-line fixtures, including the all-event calendar.

`stats/buying-implementation/20261012-continuation-program/` preserves the encoded arrays, example inputs/header/array hashes, exact source snapshot, runtime/catalog identity and test logs. All 27 tests also pass from archived source outside the repository; source and encoded-array hashes verify. No checkpoint schema, live configuration or production policy changed. No population-performance or economic gate is claimed. Compiled transitions, information grouping, explicit decision/funding execution and all later stages remain required.

## Compiled non-purchase transitions verified

`tools/buying_v2/continuation_executor.py` implements compiled OpenBook, SettleBook, SharedSettleBook, SetQuotes, Rent and EndTick transitions. The verification adapter packs and reconstructs state per event; it is not yet a resident compiled state arena or a population planner. Purchase explicitly raises an unsupported-transition error rather than falling back to reference execution.

Thirty-one targeted tests pass across the executor, calendar representation, independent ledger and shared-sales modules. Complete states and diagnostic details match the reference, including 80 varied state/price cases, frozen opening inventory and basis, shared-demand allocation, rent/arrears, posted accounts and tick-end updates. Guards cover invalid transitions and indices; caller state and program remain unchanged.

`stats/buying-implementation/20261012-continuation-executor/` preserves source hashes, runtime/catalog identity, final test logs and a successful 31-test replay from archived source outside the repository. Archive and working source hashes match. The initial Numba compilation failure on boolean-to-float conversion and its source are retained; explicit numeric conversion corrected it before the passing run. The earlier 469-test discovery predates this executor and calendar compiler. This work partially completes transition stage 2; compiled purchasing, persistent state, information grouping, planning and population validation remain open.

## Compiled purchase transition with resolved funding

`continuation_purchase.py` now executes procurement and sequential production in compiled loops. The adapter accepts `apply(state, index, allocation)` for a Purchase with resolved per-offer funded demands. Empty unresolved funding fails explicitly. It preserves sorted residual-demand constraints, lots, stock/cash/storage limits, D1 preference qualification, D2 one-fee settlement, historical-cost production gates, before/after overhead snapshots, shared inputs, finished capacities, conversion capitalization and accounts. Existing book snapshots remain intact. No reference transition is called to execute a purchase.

Thirty-three targeted tests pass. The new purchase comparison covers 2,592 allocations over 32 cash, basis, overhead, active-line and rent-threshold configurations, checking both rejected allocations and complete accepted states/details. A separate complete calendar covers nonuniform spatial units, output yields, wholesale lots, A=2/B=6 incumbent retention, a single fee, settlement, rent and tick end. This is small-fixture transition evidence, not a population or economic validation gate. The source and logs are preserved in `stats/buying-implementation/20261012-continuation-purchase/`.

All seven event kinds now have compiled transition coverage through the verification adapter. Stage 2 still needs integration into resident typed state; per-event packing, decoded Python event metadata and Python trace reconstruction remain. Funding resolution, observed-information grouping, exact decision execution and representative population validation remain required.

## Resident typed replay implemented

`continuation_resident.py` packs company/state once and runs a calendar segment in one compiled call. Typed state holds all inventory, basis, quotes, incumbents, accounts, frozen book, rent flag and ordered completed phases. `fork()` copies state arrays for independent continuations; `snapshot()` reconstructs a ledger state only when requested. Each transition checks cash/equity reconciliation and resource boundaries. A failed segment cannot commit its partial work. Scenario selection and allocation indices/ranges are validated before execution.

Thirty-six targeted tests pass. Full and segmented replay match independent ledger states after every event across two posterior paths, including all seven event kinds and two ticks. Tests check independent forks, frozen books, retained initial phase labels, empty segments, invalid indices and allocation failures after earlier successful events.

A warm 12-event replay microbenchmark (five samples of 200 calendars per implementation, complete final-state equality throughout) measures median 57.9 microseconds resident, 835.9 microseconds through the per-event compiled adapter, and 649.5 microseconds through the reference ledger. This includes resident fork/final snapshot but excludes initial construction, compilation, funding and policy search; it is not a population-performance gate. Source, test logs, benchmark script and timing samples are preserved in `stats/buying-implementation/20261012-continuation-resident/`.

This closes per-event Python state repacking for supplied-decision replay. It does not implement a bounded search arena, observed-information grouping, endogenous funding or policy optimization. Segment allocation packing remains Python work at the public boundary. Those remaining stages must use typed state directly and retain the independent oracle comparisons.

## Observed-information grouping verification component

`continuation_information.py` provides stable, first-occurrence decision groups using compiled equality of complete resident state and observed current offers, plus collision-free history IDs. State equality retains all posted accounts, active book fields and ordered completed phases; inactive book buffers and unused phase-buffer tails do not affect identity. Current offers match by unique material/supplier identity with price, stock, lot and reliability; offer enumeration order and supplied funded demands do not affect the observed event. Neutral mode removes only the current fee multiple, matching the existing comparator. Future demand, terminal values and scenario probability are excluded from observation identity. Group membership preserves branches rather than merging their future distributions.

A Python history trie currently accepts the oracle's declared realized trace fields. It remembers timing, inspected offers, actions and funded demands while excluding unobserved unmet demand and diagnostic-only fields. This is a verification boundary, not yet compiled observation generation. History IDs must belong to the same trie, program and company scope.

Twenty-four targeted tests pass across information grouping, the independent information-history counterexamples, resident replay, transitions and calendar representation. Tests cover converged balances with different sales timing, censored ordinary/shared demand, reordered offers, differing supplied funding, hidden terminal values, neutral fees, inspected quotes without transactions, account identity and inactive buffer tails. Evidence is preserved in `stats/buying-implementation/20261012-continuation-information/`. This partially implements stage 3: direct observation emission during resident replay and integration with the decision/funding stack remain required. No population scalability claim is made for the pairwise grouping kernel.

## Compiled realized observation emission

`continuation_observation.py` emits schema-1 integer/float records inside resident replay when `observe=True`. Each record preserves event kind/label and the exact declared observation fields: realized cash/equity/earnings, frozen books, sales, fees, rent, tick transfers, quotes, and purchase actions/funding/preferences/production. Purchase offers are canonicalized by material/supplier; identifiers remain integers. Unmet demand and terminal tables never enter records. The diagnostic decoder reconstructs only these fields, not full ledger diagnostics.

Twenty-seven targeted tests pass. Every decoded field matches independently generated reference observations across all seven event kinds and two scenario paths. Hidden shared-book demand produces equal numeric records. Observed and quiet replay produce equal final states; forks isolate observation buffers, and failed segments commit neither state nor records. Initial test discovery included an imported test class twice; the test import was corrected before the final 27-test run.

Records are optional and accumulated only for observed segments. A planner must enable recording throughout any history used for grouping; a partial observation sequence is not a complete history. Numeric history interning remains to be integrated with grouping and the decision/funding stack. Source and verification evidence are preserved in `stats/buying-implementation/20261012-continuation-observation/`. Earlier replay timings predate this optional emission path and are not measurements of observed replay.

## Bounded numeric histories connected to grouping

`continuation_history.py` stores parent-linked observation records in bounded integer/float arrays. Its compiled interner compares complete numeric payloads, preserving numerical equality including signed zero, without hash-collision assumptions or dictionary-trace reconstruction. `group_observed` interns resident observations and passes history IDs directly into the compiled state/offer grouping component. Resident replay now retains observed event positions; missing, repeated or reordered prefix positions are rejected before grouping.

Node, integer-value and float-value capacities are explicit. Exhaustion raises `HistoryLimit` with committed usage, allocated bytes, processed-record count and the next required capacities. Live counters remain unchanged after a failed extension; partially written unused storage cannot become a visible history. Existing history reuse consumes no new capacity. Record schema, payload lengths and finite values are checked at the adapter boundary.

Thirty-two targeted tests pass. Tests compare numeric and dictionary-history equivalence across all event kinds and both full-calendar scenario paths; they also cover the sales-timing and hidden-demand grouping counterexamples, prefix extension/reuse, signed zero, input aliasing, malformed records, incomplete histories and each independent arena-capacity limit. Evidence is preserved in `stats/buying-implementation/20261012-continuation-history/`.

This supplies the history-to-grouping connection for supplied-decision replay. Python still orchestrates branch lists and invokes the compiled components. The interner uses an exact linear scan and grouping uses pairwise comparison; representative scalability is unproven. An explicit decision/funding work stack, persistent-supply integration and exact conditional search remain required before population evaluation.

## Resumable action frame implemented

`continuation_actions.py` replaces the action generator with a typed iterative depth-first frame. It enumerates the oracle's supplied offer-order Cartesian ranges, pruning only aggregate input-slot and monotone goods-cash violations. It preserves lexicographic order, includes no purchase and unmatched buffers, and respects each offer's lot. Fees, funded residual demands, physical storage and sequential production remain the ledger's responsibility; a yielded action is not asserted to be fully executable.

Each call has an explicit prefix-work allowance. Exhaustion raises `ActionLimit` with depth, completed prefix count, yielded allocation count, peak depth, allocated bytes and work spent in that call. The frame retains the exact frontier for an explicit resume; it returns no approximate policy. Forks copy frame arrays. Empty-offer traversal yields one empty action. Integer ranges whose next-quantity sentinel cannot fit int64 fail explicitly.

Seventeen targeted tests pass across the action frame, numeric histories, resident execution and transition modules. Sixty seeded fixtures compare the complete ordered sequence with an independent Cartesian-product filter. One-prefix resumes and independent forks preserve the sequence and total work count; zero allowance and empty-offer boundaries are covered. Source and logs are preserved in `stats/buying-implementation/20261012-continuation-actions/`.

This is the action-enumeration component of stage 4, not the full decision/funding stack. Conditional groups, child continuation returns, actual/hypothetical funding roles, persistent supply, posterior reduction and tolerance-based winner selection still need explicit frames and integration. No population or economic gate is claimed.

## Supplied-funding conditional search connected

`continuation_search.py` now connects resident execution, numeric history grouping and resumable action frames using explicit walk/choice control frames. It searches complete supplied calendars without recursive Python calls, selects a common action for each observed-information group, and preserves the oracle's posterior summation, monetary tolerances and lexicographic tie ordering. Selected leaves retain complete state, per-event allocation policy and numeric observations. Payment comparison reads numeric purchase records directly.

This implementation requires explicit funded demands and independent stock snapshots. Supplied funded demands that differ inside one observed-information group are rejected rather than revealing hidden scenarios. Offers are canonicalized by material/supplier before traversal, as in the oracle. Zero-probability paths do not enter search. Frame, allocation, prefix-work and history limits fail with completed-work diagnostics and no approximate policy.

Nineteen targeted tests pass across search, action frames, histories, observations and the independent information-history cases. Complete values, policies, states, accounts and observation fields match the oracle for multiple purchases, multiple lines, outcome branching, sales-timing signals, censored demand, rent, quote changes, tick end and empty calendars. Tests exercise each limit and hidden-funding rejection. Evidence is preserved in `stats/buying-implementation/20261012-continuation-search/`.

Control frames and branch lists are still Python objects; this is an integration proof around compiled kernels, not the final typed work arena. Endogenous own-quote funding, actual/hypothetical roles, persistent supply and fully compiled control remain required. No scalability or economic adoption gate is claimed.

## Persistent supply connected to resident search

Resident replay and supplied-funding search now accept `supply='persistent-arrivals'` alongside independent snapshots. Scenario stock is validated as nondecreasing cumulative initial stock plus external arrivals. Each actual purchase subtracts its quantities from later offers of the same material/supplier in that scenario. Updated stock drives action ranges, observed-offer grouping, D2 availability and emitted purchase observations. The immutable calendar remains unchanged.

Resident branches own their event-integer buffers. Forks copy supply state; persistent replay stages updates on a copy and commits them with company state and observations only after the segment succeeds. Future scenario arrivals remain hidden until their offer is observed. This representation currently copies the calendar integer buffer; it is not a demonstrated memory-efficient population supply arena. Earlier replay timings do not cover this new supply path.

Twenty-three targeted tests pass, including complete oracle policy/state/observation parity, depletion/restocking, hidden future arrivals, depleted-incumbent fee waiver, a nine-case stock/arrival grid, input preservation and atomic segment failure. Evidence is preserved in `stats/buying-implementation/20261012-continuation-supply/`.

Endogenous funding is still absent from this search. Its hypothetical stock relaxation must not subtract invented current stock from future arrivals; that separate boundary remains to be implemented and tested when funding frames are added. Fully typed control frames and representative memory/latency validation remain open.

## Typed own-quote funding boundary implemented

`continuation_query.py` constructs the joint reference query and each own-quote query directly from typed current offers. Only the queried material is restricted to one offer; all other materials retain their discovered offers. Selected stock and funded caps become the whole-lot available input-slot capacity. Current fee multiple becomes zero; quote, reliability, active-line and overhead metadata retain their values. The helper returns selected original offer indices for later funding-result assembly.

`Resident.funding_purchase` executes an explicitly supplied hypothetical allocation with this payload. It holds current incumbents fixed before observation emission. Under persistent supply, each selected offer reduces future real stock by `min(hypothetical_purchase, real_opening_stock)`, preserving hypothetical additions separately from real future arrivals. The override applies only to this event; future fees and offer payloads remain real. State, observations and supply still commit atomically.

Fifteen targeted tests pass across query, persistent supply, conditional search and resident execution. Independent dataclass construction plus ledger evaluation checks each offer-query subset and its enumerated allocations. Additional checks cover fixed incumbents, zero current fees, phantom stock versus real arrivals, immutable calendar inputs, invalid query indices and atomic failure. Source and logs are preserved in `stats/buying-implementation/20261012-continuation-query/`.

This implements counterfactual payload/execution semantics only. It does not derive funded demand, optimize a query or connect recursive future funding. Explicit query/result frames, selected-quantity aggregation and integration with the conditional search remain required; the supplied-funding search remains the only connected solver at this point.

## Endogenous continuation-v2 funding connected

`continuation_search.solve(..., funding='continuation')` now uses explicit funding/query/result frames. Each observed decision evaluates the joint query and each own-quote query, deduplicates identical selected-offer sets, aggregates selected quantities by input and writes the resulting actual funded demands into a preallocated event payload. Hypothetical choices use the typed query boundary; future purchasing decisions derive their own funding through the same stack. Actual and hypothetical branches remain separate. Supplied funding remains available as an explicit comparator; unknown modes fail rather than falling back.

Selected leaves include per-decision reference suppliers/demands, joint quantities/goods and every quote query's quantities, goods cost and conditional value. These come from completed query searches. Current fees and incumbent acquisition are omitted only in the current query; future decisions retain real fees and preferences. Persistent supply retains the real-versus-phantom rule. Stack, allocation, prefix and history limits apply throughout nested funding work and return no approximate policy.

Twenty-one targeted tests pass across endogenous funding, query execution, supplied search, persistent supply and numeric histories. Independent oracle comparisons cover full selected policies, funded observations, states/accounts, query quantities/costs/conditional values, multiple purchases, multiple lines, censored/history-sensitive outcomes, zero-offer queries and persistent hypothetical stock. Evidence is preserved in `stats/buying-implementation/20261012-continuation-endogenous/`.

This completes the initial integration proof for continuation-v2 on the tested small calendars. It does not close stages 4–7: control frames and branch storage remain Python, full arena memory is not measured, exhaustive search remains potentially exponential, and no representative population performance or economic validation has passed. Reference-only and transfer-neutral funding variants remain in the independent oracle; the new search currently supports supplied funding and continuation-v2 only.

## Connected-search differential and integration checkpoint

A seeded 24-case differential campaign (`test_buying_v2_continuation_differential.py`, seed 84371) compares complete continuation-v2 results against the independent oracle. Cases vary one/two installed lines, two purchasing periods, unequal posterior weights, cash, input basis, starting stock, incumbents, transfer EMA, arrears, fractional storage units, conversion costs, quotes, lots, supplier availability, fee parameters and before/after rent snapshots. Both independent snapshots and persistent arrivals are included, with explicit nonzero terminal tables. All selected policies, states/accounts, observations and per-quote quantities/costs/values match. This finite campaign is not a general proof or a population calibration.

Fresh full Python discovery passes **518 tests in 287.023 seconds**. All 229 captured source/catalog hashes remain unchanged at completion. The 24-case campaign also passes from archived source outside the repository. The first archived replay failed because the snapshot omitted catalog JSON needed by the JIT hash; that packaging failure is retained, and the required catalogs were added before successful replay. The existing NumPy/SciPy warning remains nonfatal; no dependency changes were made.

`stats/buying-implementation/20261012-continuation-integration-audit/` preserves commands, runtime, all 24 serialized cases, source/catalog hashes and snapshots, discovery/differential logs and verification. This is a Python integration checkpoint. No browser checks, population timings, long-run economic validation or live adoption are claimed.

## Typed branch state/supply pool implemented

`continuation_arena.py` stores complete resident state and per-branch event integers in fixed-capacity typed rows. Compiled load/store and event stepping preserve cash, accounts, inventories/basis, quotes, incumbents, open-book data, ordered phases, rent state and persistent supply. Handles include slot and generation; release/reuse invalidates stale references. Forks copy rows, exports copy data, and a failed event commits no row changes. Capacity exhaustion raises `BranchLimit` with active/peak branches and cumulative allocations.

Diagnostics distinguish pool/handle buffer bytes from copied template-buffer bytes. They do not claim total process memory: Python objects, immutable program/company metadata, temporary transition allocations and observation/result storage are separate. Observation records are returned by stepping; the pool does not store trace history. Export therefore provides state/supply with an empty observation prefix, which cannot be passed off as complete observed history.

Ten targeted tests pass across the arena, resident replay and persistent supply. Every event in the full fixture matches resident state, supply and observations. Tests cover independent forks, capacity exhaustion, stale handles after reuse, export isolation and atomic failed purchasing. Evidence is preserved in `stats/buying-implementation/20261012-continuation-arena/`. The preceding 518-test discovery predates this new component.

The existing search still uses resident Python branch objects. Integrating this pool with typed control, numeric history IDs, funding overrides and retained result/policy storage remains required. This is a storage/execution component, not a completed typed search or a population-performance result.

## Branch arena integrated with conditional search

`continuation_search.solve(..., storage='arena', max_branches=...)` now stores branch state and persistent supply in the typed pool. An adapter supplies actual and hypothetical event execution, funding-payload updates, forks and leaf snapshots. Search explicitly releases completed walk branches, resolved funding branches and rejected candidate branches. Capacity failures become `SearchLimit` diagnostics with arena usage and no partial policy. The resident path remains available as a comparison; no production default changes.

Ten targeted tests pass, including all 24 seeded differential cases against independent oracle policies, observations, funding results and accounts. Successful searches finish with zero live rows. A two-period/two-outcome example performs 2,630 branch allocations with a peak of ten live rows; rerunning with exactly ten slots gives the same policy. One-, two- and three-slot capacity limits fail explicitly. The 256-slot example allocates 309,504 pool/handle buffer bytes plus 1,176 copied template-buffer bytes; these exclude Python controls, results, observations and transient arrays.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-arena-search/`, including the reuse diagnostics. The adapter currently loads typed state copies for grouping and still keeps observations/policies in Python. Fully compiled control, bounded history/result ownership and representative memory/latency gates remain required; this is not a whole-search memory bound or demonstrated speedup.

## Bounded numeric policy prefixes integrated

`continuation_policy.py` stores immutable parent/event/allocation records in fixed-capacity integer arrays. Compiled insertion reuses exact matching prefixes; branches carry one policy-node ID. Both resident and arena search paths now append IDs instead of copying policy dictionaries for candidate branches. Only final selected leaves reconstruct event-to-allocation dictionaries. Event indices must increase, and allocations retain their original order and whole quantities.

Node and allocation-value limits are explicit. Failure leaves existing records unchanged and becomes `SearchLimit` with policy usage, required capacity and no partial policy. Diagnostics report array buffer bytes. Unselected records are retained until the solve ends; this is bounded append-only storage, not live-prefix garbage collection. It does not bound observation buffers, funding details, leaf state objects or control frames.

Fifteen targeted tests pass, including the 24-case arena-backed differential campaign and complete endogenous/supplied search comparisons. New tests cover shared prefixes, divergent actions, empty actions, output isolation, malformed records, independent capacity limits and rerunning a search at its exact measured policy-node/value usage. Evidence is preserved in `stats/buying-implementation/20261012-continuation-policy/`. No full discovery or population performance gate was repeated for this component.

## Search observations retained only in bounded numeric history

Both search paths now intern each completed event's observation immediately and retain only a history-node ID and event count on the branch. Temporary observation tuples are cleared after interning. Decision grouping uses those IDs directly; final selected leaves reconstruct independent numeric traces through `NumericHistory.export`. This removes growing per-branch observation tuples from search while retaining the complete observed history, including events after the final purchase.

Every search event now encounters the history capacity checks, not just events preceding another decision. A history-limit failure aborts the solve with diagnostics and no partial policy. The underlying standalone resident replay still supports its explicit observation API; only search's retention strategy changed. History storage remains append-only, so discarded candidate prefixes count toward the configured bound. Funding-detail dictionaries, leaf state/result objects and control frames remain outside this bound.

Fifteen targeted tests pass, including all 24 seeded arena/oracle comparisons, complete endogenous/supplied policies and observations, final-only history-limit failures, output isolation and search replay at exactly the measured history node/integer/float capacities. Evidence is preserved in `stats/buying-implementation/20261012-continuation-history-storage/`. No full discovery or population performance gate was run for this step.

## Retained funding details moved into numeric storage

`continuation_funding_records.py` stores completed continuation-v2 funding details as bounded parent-linked integer/float records. Each record retains event index, reference supplier identities/demands, joint quantities/goods cost and ordered per-quote material/supplier identities, quantities, goods costs and conditional values. Stable identities remain int64. Exact repeated prefixes reuse their existing node. Branches carry one funding-node ID, and only selected final leaves reconstruct the public funding dictionaries.

Both search storage paths use this arena. Node/integer/float capacity failures become `SearchLimit` with usage and required capacities, without partial policies. Failed insertion preserves committed counters and records. The arena is append-only for a solve; discarded search results are not reclaimed. Transient query-answer dictionaries, control frames and leaf-state/result objects remain outside its buffer-byte accounting.

Fifteen targeted tests pass, including 24 seeded arena/oracle comparisons and complete endogenous/supplied search results. New tests cover exact round trips, shared prefixes, supplier ID `2**53+1`, negative conditional values, export isolation, invalid records, all three capacity limits and replay with exactly the measured funding-record capacity. Evidence is preserved in `stats/buying-implementation/20261012-continuation-funding-records/`. Fully typed control and transient/result storage remain required; no whole-process memory or population-performance gate is claimed.

## Transient query answers moved into typed scratch arrays

`continuation_query_answers.py` replaces each funding frame's answer dictionary and selected-offer key lists with typed arrays for keys, ordinal-to-answer mapping, completion flags, quantities, goods costs and conditional values. Exact key comparison preserves the existing query-deduplication rule. The joint query and per-offer queries retain their original execution order. Small dictionaries are reconstructed only when assembling completed diagnostic records.

Search reserves each frame's exact array-buffer requirement before allocation and enforces `max_query_bytes` across simultaneously live funding frames. Diagnostics report current and peak scratch bytes; successful completion returns current scratch usage to zero. This byte budget covers these arrays only, not Python frame overhead or leaf-result objects. Frame storage is released after the actual decision returns. Selected-offer IDs must be integral and valid; fractional or boolean IDs are rejected.

Fifteen targeted tests pass on the final source, including 24 seeded arena/oracle comparisons and complete endogenous/supplied results. New tests cover duplicate queries, incomplete/invalid answers, empty offers, exact buffer-size accounting, export isolation and replay at the measured peak scratch budget. Reducing that budget by one byte fails explicitly. Evidence is preserved in `stats/buying-implementation/20261012-continuation-query-answers/`; the earlier test log predating the final identity guard is retained separately.

Typed control frames and leaf-result storage remain open. These changes bound another component; they do not establish a whole-process memory bound, a performance gain or population suitability.

## Terminal results compacted; selected policies replayed

`continuation_results.py` replaces retained candidate leaf-state dictionaries with fixed-capacity records containing scenario, policy/history/funding node IDs and terminal value. Each record uses four int64 values plus one float64 value (40 buffer bytes). Compiled terminal evaluation preserves the ledger's sequential terminal-table sum and cash/liability ordering. Result capacity exhaustion raises `SearchLimit` with committed usage and no partial policy. Records remain append-only for each solve.

After all alternatives are resolved, search reconstructs only selected policies, histories and funding diagnostics. It replays each selected policy from the initial resident state, using the stored funded demands and declared supply mode, and requires exact equality of every emitted observation and terminal value before returning the final state. This avoids retaining a full state snapshot for every candidate terminal branch.

Fifteen targeted tests pass, including all 24 seeded arena/oracle comparisons, complete endogenous/supplied results, stable integer IDs, isolated result-capacity failure and replay at the exact measured record count. Evidence is preserved in `stats/buying-implementation/20261012-continuation-results/`.

Control frames still contain Python branch/group/result-ID lists. Public output materialization and selected replay also use Python orchestration. These remain to be lowered or bounded explicitly; the numeric result buffer alone is not a whole-process memory bound or a population-performance result.

## Scalar control frames moved into typed storage

`continuation_control.py` stores frame kind, stage, event position, cursors, flags and optional offer IDs in int64 arrays, and mass/payment in float64 arrays. Presence flags distinguish missing values. Fixed frame capacity retains the existing search limit; generation checks reject stale views after a frame is popped or its row reused. Field validation completes before append or multi-field update changes storage. Pop clears retained object references.

The experimental search defaults to this storage and retains `control='python'` as a comparison path. Its mapping adapter preserves the existing traversal, query ordering and tie-breaking. Diagnostics expose active/peak frames, scalar buffer bytes and allocated reference slots. Eight reference fields per frame still hold branch/group/result lists, allocation frames, query scratch or best-result objects. Python dispatch and these referenced contents remain unfinished structural work; scalar buffer bytes are not total memory usage.

Fifteen targeted tests pass, including all 24 seeded arena/oracle comparisons and direct typed/Python control comparison. Focused cases exercise nested frames, IDs above `2**53`, nullable offers, capacity, atomic invalid updates, reference release and stale handles. Source and replay evidence are preserved in `stats/buying-implementation/20261012-continuation-control/`. No performance improvement or population suitability is claimed. Production defaults and the accepted D1/D2 rules are unchanged.

## Selected leaf IDs and group totals use bounded arrays

`continuation_leaf_rows.py` replaces selected terminal-row lists with fixed-capacity int64 buffers. Each walk frame reserves one row per incoming scenario branch: conditional groups partition those branches, and each selected action returns one terminal row per branch. Alternative actions replace the selected result rather than accumulating selected rows. Extending a result validates capacity before mutation and copies identifiers, preserving exact integers above `2**53`. A capacity violation is an invariant failure, not a truncated policy.

Group totals now use one float64 slot per information group, filled in the original group-return order. Terminal weighted values use one float64 slot per branch. Both retain `math.fsum` and the original sequence, avoiding a changed reduction rule. These buffers bound retained selected IDs and sums within a frame; branch/group objects, allocation scratch and Python dispatch remain. This is not a whole-process memory or population-performance claim.

Verification evidence is stored in `stats/buying-implementation/20261012-continuation-leaf-rows/`. The targeted campaign includes independent complete-policy oracle checks, both control adapters, empty results, exact integer IDs, copy isolation and atomic capacity failures. Production defaults and D1/D2 are unchanged.

## Information-group membership uses numeric partitions

`continuation_groups.py` stores group offsets and branch indices in int64 arrays. A compiled stable counting partition preserves first-seen group order and original branch order within each group. The input IDs must be contiguous in first-appearance order; invalid IDs are rejected before calling the compiled kernel. Every branch appears exactly once. Arrays require `8 * (branches + groups + 1)` bytes, excluding temporary construction arrays and Python wrappers.

Search frames now retain this partition rather than lists of branch lists. A group view resolves indices against the original branch sequence; it does not copy branch objects or own/release their arena rows. The original branch sequence remains structurally unchanged while a partition is live. Existing walk/choose ownership and release rules remain responsible for branch lifetime. This removes duplicated group membership objects but does not yet replace the original Python branch tuples or dispatch.

Verification is preserved in `stats/buying-implementation/20261012-continuation-groups/`. Focused checks compare 100 seeded partitions against independently built lists, validate exact coverage/order, reject malformed IDs and check source identity through views. The connected campaign compares complete funding, policies, observations and accounts with the independent oracle. No population-performance result or production adoption is claimed.

## Search history and funding IDs belong to branch arena rows

The arena now owns three int64 search-metadata columns: history node ID, recorded event count and funding-record node ID. Create initializes them to zero, fork copies them independently, and release clears them. The search adapter exposes checked properties rather than retaining duplicate Python attributes; stale handles reject both reads and writes. Values must be nonnegative Python integers fitting signed int64.

Diagnostics include the 24 bytes per allocated branch row in `poolBufferBytes` and separately report `searchMetadataBytes`. These are identifiers into separate bounded stores, not copies of observations or funding records. State export continues to expose economic state with an empty observation trace; it does not claim to reconstruct search history. Temporary observation emissions still pass through the adapter before numeric history interning.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-branch-metadata/`. Targeted checks cover exact IDs above `2**53`, fork isolation, invalid writes, row reuse, stale access and complete independent oracle comparisons. Original branch sequences and Python dispatch remain structural work; this change establishes no new performance or adoption claim.

## Arena search retains numeric branch sequences

`continuation_branches.py` replaces retained `(scenario, resident, policy)` tuples in arena-backed search with four int64 columns: scenario ID, arena row, generation and policy node ID. Root storage is bounded by the scenario count; child and resolved-funding sequences are bounded by their incoming group size. Each allocated sequence row uses 32 buffer bytes. The resident comparison path retains its original lists.

Access validates the handle and constructs a temporary adapter over the arena row. History and funding metadata survive these adapters because they already belong to typed arena storage. Append rejects pending observations, preventing transient adapter recreation from silently discarding observations before interning. Invalid identifiers, foreign arenas, stale handles and capacity overflow fail before sequence mutation. The sequence does not release rows; existing search ownership still controls their lifetime.

Stable group views now index these numeric sequences. Python wrappers, transient adapters, action scratch and dispatch remain, so this is a storage milestone rather than a fully compiled planner or a performance claim. Evidence is preserved in `stats/buying-implementation/20261012-continuation-branches/`, including complete seeded oracle comparisons, exact policy IDs, shared metadata access, stale generation checks and observation-retention guards.

## Bounded-storage integration checkpoint

Fresh full Python discovery passes **551 tests in 329.884 seconds** after the arena, policy, history, funding/query, result, control, group and branch-sequence changes. An archived-source replay of 23 selected tests also passes, including the 24 seeded complete-search oracle cases. All 249 recorded source/catalog hashes match the tested working tree. Evidence, commands and source are preserved in `stats/buying-implementation/20261012-continuation-storage-audit/`.

The audit corrected the grouping module to use the research source-aware JIT wrapper, which incorporates research dependency changes, and changed a fixture import to avoid duplicate unittest discovery. No dependencies were changed; the existing NumPy/SciPy compatibility warning remains nonfatal. The archive preparation initially referenced a nonexistent field in an older manifest; it was corrected before the archive replay, without restarting the full test process or changing tested source.

This establishes a current Python integration checkpoint, not full economic or algorithmic validation. JavaScript/browser behavior was not rechecked here. A compiled driver, representative population timing/memory, adopted forecast/funding choices, held-out economic validation and full-world integration remain open. The current summaries now reflect typed retained storage and remaining Python dispatch rather than the older all-Python storage description.

## Information grouping reads arena rows directly

`continuation_arena_information.py` executes arena-backed decision grouping in one compiled loop over numeric branch rows. It validates every generation, scenario/event position and history ID before comparison. State comparisons use read-only row views rather than copied resident states and a temporary Numba list. Current offers are compared against each row's live supply payload. Full account/history identity, unused-buffer semantics, first-seen grouping order and optional neutral-fee comparison retain the existing comparator rules.

The resident path remains available for differential checks. The arena path returns numeric group IDs directly to the stable partition builder. Python dispatch still calls this kernel; a complete compiled driver and its arithmetic/scratch contracts remain open. Eliminating these copies is a structural change, not a measured performance result.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-arena-information/`. Targeted checks compare live-state/history/offer grouping, neutral mode, unused buffers, stale handles and invalid history/event positions, and verify that comparison leaves state pools unchanged. Connected search is checked against the independent oracle across all 24 seeded cases. The preceding 551-test integration checkpoint predates this change.

## Non-purchase advancement and history interning share a compiled loop

`continuation_advance.py` advances arena branches in event-major, branch-minor order until the next purchase or the requested boundary. Each compiled event immediately interns its numeric observation and updates the row's history ID/count. Mutable numeric counters retain completed history usage and transitions even when a later event raises. Python receives the next event position once per segment. The resident comparison path retains its original event loop.

The kernel validates live generations and complete history prefixes before advancement. Emitted floating values must be finite before interning. History exhaustion preserves completed-record diagnostics and returns no policy; an event may already have committed state before its observation fails to fit, matching the preceding step-then-record boundary. Such a failed search is not resumable from that row. This is not an atomic multi-event transaction.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-advance/`, including segmented/full advancement, purchase-boundary stopping, exact resident state/observation comparisons, history exhaustion, stale handles and nonfinite emitted-equity rejection. The pre-finite-guard passing log/source are retained separately. Complete search is also checked against all 24 seeded oracle cases. Purchase/funding traversal and remaining scratch management still require a compiled driver; no performance or economic-adoption claim follows from this change.

## Terminal capture reads arena state and writes result buffers in one loop

`continuation_terminal.py` evaluates each terminal branch through a read-only state view and writes scenario, policy/history/funding IDs and value directly into the bounded result arrays. Weighted values and selected result IDs retain branch order. Search still applies `math.fsum` in that order; no different reduction or tie rule is introduced. Final selected-policy replay and exact observation/value checks are unchanged.

Live handles, scenario bounds, nonnegative IDs, finite values and closed sales books are required. Capacity failure reports the completed records and the next required count without returning partial leaves. Mutable counters retain completed records on later errors, matching sequential append semantics; the operation is not an atomic multi-branch transaction. State pools are not modified.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-terminal/`, including independent ledger terminal values, exact IDs above `2**53`, state immutability, capacity exhaustion, unsettled books, stale handles and the 24 seeded complete-search oracle comparisons. Purchase/funding traversal, scratch management and the overall driver remain Python. No population-performance or economic-adoption gate is claimed.

## Actual funded branches are cloned and recorded in a compiled batch

`continuation_resolve.py` consumes numeric arena groups and the completed own-quote demand vector. In branch order it claims a row, copies state/supply and history metadata, assigns validated whole-lot funded quantities, interns the completed funding record and retains the new numeric branch handle. Original branches are unchanged. Group views are gathered as numeric rows, without constructing per-branch adapters. Funding-detail encoding remains Python and is shared with the existing record API.

Mutable counters preserve completed clone and funding-record usage on failure. Branch capacity failure retains the already completed clones; funding-record capacity failure can include a claimed row whose record could not be stored. As before, no partial policy is returned, and failed search arenas are discarded. Input demand validation now precedes row claiming; this affects malformed-input failure timing only. Successful action traversal, actual/hypothetical separation and funding records are unchanged.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-resolve/`. Fifteen integration tests plus three lifecycle tests pass, covering all 24 seeded complete-search oracle cases, numeric group views, shared record reuse, original-state isolation, exact policy IDs, stale handles and both capacity failures. Hypothetical query construction, diagnostic detail assembly and the outer search driver remain Python; representative performance and economic adoption are still open.

## Completed funding records are encoded directly from numeric answers

`continuation_funding_encoding.py` constructs the resolved per-offer demand vector and funding-record arrays directly from completed query scratch. Arena search no longer reconstructs query-answer dictionaries, candidate lists or quote-vector dictionaries before actual-funding resolution. The resident path retains the prior assembly for comparison.

The encoder selects an available incumbent first, otherwise the lowest `(price, supplier ID)` quote; missing materials retain supplier `-1` and zero reference demand. Each offer receives its own-quote answer's quantity for that material, while joint quantities/cost and all per-query cost/value details preserve the existing record schema. Reused query rows remain reused; incomplete answers fail. Empty offer books preserve a completed joint query and missing reference fields.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-funding-encoding/`. Twenty integration tests and one added empty-book test pass, including exact array comparisons with the existing encoder, incumbent/cheapest/tie cases, negative conditional values, query reuse and all 24 seeded complete-search oracle comparisons. The pre-empty-case test source is retained with its original log. Query traversal and the overall driver remain Python; no performance or economic-adoption claim is made.

## Connected candidate scaling screen exposes two independent bottlenecks

The connected arena candidate was screened on the eight historical capacity/supplier/calendar fixtures for each of one and two installed lines, using continuation funding only. Each run allows 4,000 allocations and 16,000 action prefixes. These separate limits are **not equivalent** to the older solver's combined-work budget. No callbacks, reduced action scope or approximate answers were substituted.

It completes **7/16 cases**: 4/8 single-line and 3/8 two-line cases. All nine failures reach the allocation limit. Three measured repeats have identical full-result or failure-diagnostic fingerprints for every case. The warm-up/first solve took 23.162 seconds and is excluded below. Times are local medians of three samples; a limit row reports time to failure, not time to an optimum. Three samples provide only a coarse empirical tail.

| Capacity / suppliers / periods / outcomes | One line | Median ms | Two lines | Median ms |
| --- | --- | ---: | --- | ---: |
| 1 / 1 / 1 / 1 | exact | 2.84 | exact | 4.35 |
| 2 / 2 / 1 / 1 | exact | 27.53 | exact | 104.48 |
| 4 / 2 / 1 / 1 | exact | 133.12 | limit | 743.93 |
| 8 / 3 / 1 / 1 | limit | 906.42 | limit | 928.44 |
| 1 / 1 / 2 / 2 | exact | 22.74 | exact | 79.15 |
| 2 / 2 / 2 / 2 | limit | 771.06 | limit | 847.02 |
| 4 / 2 / 2 / 2 | limit | 1058.23 | limit | 947.94 |
| 8 / 3 / 2 / 2 | limit | 1607.40 | limit | 1628.93 |

The earlier joint-budget solver completed 6/8 continuation-funded two-line cases; the connected candidate completes 3/8. Values match in all three commonly completed cases. Different pruning, memoization and work accounting prevent a controlled speedup or equal-budget claim. The new representation has not yet recovered the earlier solver's search reductions.

A warm instrumented profile of the single-line capacity-2, supplier-2, two-period/two-outcome failure shows 4,100 Python purchase-history `record` calls taking 0.683 seconds cumulatively out of 1.615 seconds in `solve`. Creating Numba typed lists inside history insertion accounts for 0.462 seconds cumulatively. These nested times must not be added together. This identifies a concrete boundary to lower next; it does not explain away allocation exhaustion. Proven pruning/reuse must also be integrated and verified before claiming solver feasibility.

Evidence, complete inputs/results, source hashes, three-sample timings, diagnostics and the profile are preserved in `stats/buying-implementation/20261012-connected-scaling/`. The first profiler launch shadowed Python's `profile` module; its failure log is retained, and the renamed diagnostic script succeeded. This is a synthetic screen with independent stock snapshots, ample cash, zero fees/rent/terminal value and perfectly correlated demand outcomes. It does not validate calibrated forecasts, representative population latency/memory, recording/UI costs or long-run economics.

## Single-observation history insertion avoids Python typed-list construction

`NumericHistory.extend` now routes a validated single observation through a compiled wrapper that constructs the one-record container inside compiled code. The trie insertion kernel, payload validation, defensive array copies, exact equality and capacity/rollback semantics remain unchanged. Multi-record callers retain the existing typed-list path after complete validation. This targets the measured purchase-history boundary without changing the planner's action space, traversal, pruning or budgets.

Twenty-one targeted tests pass, including single-record exhaustion of each capacity, multi-record rollback, observation aliasing, complete event/history equivalence and all 24 seeded complete-search oracle cases. Evidence and the unchanged scaling specification are preserved in `stats/buying-implementation/20261012-continuation-history-fast-path/`.

The unchanged 16-case screen, run from archived source with three repeats per case, matches **all 16 prior result/failure fingerprints**. Completion remains **7/16** with the same nine allocation-limit failures. Local median-time ratios range from 1.24× to 1.48×, with a median case ratio of **1.40×**. The single-line capacity-2/two-supplier/two-period/two-outcome limit case falls from 771.06 ms to 539.92 ms median. These sequential local samples are not a controlled population benchmark or tail guarantee.

In the same warm instrumented diagnostic, 4,100 `record` calls fall from 0.683 to 0.146 seconds cumulatively, and total profiled solve time falls from 1.615 to 1.026 seconds. The profiler adds overhead, so these figures explain the removed cost rather than substitute for the uninstrumented samples. Search-work reduction remains the next priority: faster execution alone has not cleared another case.

## Exact funding-query reuse prototype does not clear another scaling case

An opt-in `funding_memo_entries` setting now reuses completed hypothetical query answers within one solve. The key includes query payload, complete live economic state/accounts, supply mode, ordered scenario IDs and each branch's current/future integer payload. Program, initial state, probabilities, future float payloads and terminal tables are fixed for that solve. Scenario identity conservatively distinguishes even identical future paths. Inactive book/phase buffer tails and past payloads are excluded under the existing live-state contract.

Every input group must have a common observed prefix. Its identity can be omitted because adding the same prefix to every future observation history cannot change equality within that group's continuation. Ordered scenario identities preserve the posterior; current physical stock remains in the key for real/phantom supply distinctions. Only quantities, cost and conditional value are reused, not policy/history records. Policy prefixes and funding-record IDs do not affect these values. Cache-off comparisons retain complete final policies, observations, accounting and funding records.

This is a bounded **Python index prototype**, disabled by default. FIFO eviction is deterministic. Entry count and retained key/answer payload bytes are bounded; Python object overhead and pending frame keys are excluded from byte diagnostics. It is not the final compiled memo or a whole-process memory bound. The initial over-keyed prototype preserved results but failed the expected-hit check; its source and failure log are retained.

Fifteen integration tests plus an additional key-boundary test pass, including cache on/off over all 24 seeded cases, tiny FIFO capacity, byte limits, posterior/supply distinction and common-prefix validation. The unchanged 16-case screen still completes **7/16**. Only cases 4 and 12 hit the cache: allocations fall from 72 to 68 and from 376 to 346 respectively. No allocation-limited case records a hit or clears its limit. All seven completed results match the cache-off policies, states and observations exactly.

Evidence is preserved in `stats/buying-implementation/20261012-continuation-query-memo/`. This result favors integrating validated closing bounds next rather than treating memoization as a population solution. Full compiled orchestration, representative feasibility, economic decisions and integration remain open.

## Certified closing bridge advances connected scaling to eleven cases

An opt-in `closing=True` adapter now connects the existing strict-certificate/joint-bound closing solver to connected search. It reconstructs the current purchase from live stock/funded payloads, including the exact hypothetical query payload where applicable, and uses the ordered weighted suffixes. The existing closing eligibility checks remain authoritative: unsupported calendars, open books, fractional spatial arithmetic and other unsupported boundaries return to the general action traversal. No line, offer or future event is dropped to obtain eligibility.

For supported problems, the certified solver either proves strict ledger-value dominance or completes its existing lexicographic bounded fallback. Only the selected allocation enters the connected transition path; selected-policy replay still checks every observation and terminal value. This bridge retains Python preparation/dispatch and is disabled by default. It is not yet the final fully compiled planner.

Closing allocation evaluations count against the existing allocation limit (the selected replay is charged once). Boxes, proposal states and joint-bound work share the prefix-work budget with ordinary action prefixes. Interrupted legacy closing calls do not return internal consumed-work counts; failure diagnostics explicitly distinguish prior completed work from the interrupted call's assigned budgets. They never return an unfinished policy or imply those counters cover the interrupted call.

Fifteen targeted tests pass, including full-result on/off comparisons for all 24 seeded cases, unsupported fallback and explicit limits. Under 4,000 allocations and 16,000 shared prefix/proof work units, the same 16-case screen improves from **7/16 to 11/16**. Cases 3, 5, 10 and 11 newly complete. The new certain-demand cases also meet their analytical profit checks. All seven previously completed cases retain identical full results.

The remaining failures are case 6 at the closing allocation limit and cases 7, 13, 14 and 15 at closing box/work limits. Completion remains insufficient for D6 or population adoption. Evidence, complete results, source and commands are preserved in `stats/buying-implementation/20261012-continuation-closing/`. Proven reuse of closing work and better earlier-decision bounds remain candidates; do not hide these failures by raising budgets or reducing supported scope.

Archived replay reproduces all 16 complete result/failure fingerprints. Newly completed case 5 also matches the independent unpruned event-tree oracle in full policies, states, observations and funding details: 35562 oracle allocations versus 3708 candidate allocations. This is an algorithm-work comparison for that fixture, not a population speedup claim.

## Exact closing-selection reuse reduces work without clearing a further case

The opt-in `closing_memo_entries` setting caches only completed closing selections. Its exact serialized key contains the full ledger state, reconstructed live purchase, ordered weighted suffix scenarios with terminal tables, and actual/hypothetical role. Company and initial state are fixed within the owning solve. The key is compared as complete bytes, never by a hash alone. Serialization may conservatively distinguish different object-sharing patterns; it cannot intentionally merge unequal economic inputs. Nothing is deserialized to execute code.

A hit still executes the selected basket through the connected ledger and charges one allocation. Prior proof/allocation work is not recharged, and no branch state, accounting or observation is taken from the cache. Failed/incomplete proofs are never stored. FIFO entry and retained payload-byte bounds use the existing experimental cache container; Python object overhead remains outside those byte counters. This is a Python prototype, disabled by default, not the final compiled memo representation.

Eighteen targeted tests pass, including cache-on/off complete results for all 24 seeded cases, capacity-one eviction, a one-byte budget that retains nothing, and a requirement that closing mode be enabled. The 16-case screen remains **11/16**. All eleven completed cases preserve full results. Case 5 falls from 3,708 to 2,304 allocations and from 7,324 to 3,010 closing-work units, with 702 hits. Cases 4 and 12 also reuse results. Case 7 has 672 hits but still fails, now at the allocation limit rather than closing box/work exhaustion. Cases 6 and 13–15 remain limited without hits.

Evidence and source are preserved in `stats/buying-implementation/20261012-continuation-closing-memo/`. The result supports retaining exact reuse as an optional optimization while pursuing bounds for earlier decisions and distinct closing states. It does not establish representative performance, economic adoption or full-world integration.

## Connected continuation envelope preserves results but leaves five limits

An opt-in `prune_continuation=True` bridge now evaluates the existing optimistic continuation envelope after a feasible purchase, before searching its suffix. It uses each child's actual state, scenario suffix and terminal tables. Future supply is relaxed by the bound, so original future stock payloads remain optimistic under persistent arrivals. Unsupported suffixes return infinity and cannot prune. It prunes only strictly below the current best value by the existing tolerance; ties retain the complete traversal. No new economic rule is introduced.

Each scenario envelope evaluation shares the prefix/closing work budget. Allocation and transition work already performed remains charged; pruned arena children are released. The default remains off. This is a Python proof bridge, not the final compiled driver. The existing cost-free envelope is deliberately used first; cost-tightened and prefix/shared-first variants remain separate next candidates.

Evidence: `stats/buying-implementation/20261012-connected-continuation-bound/`. Six targeted tests passed in 35.835 seconds, including 24 seeded on/off complete-result comparisons and the existing independent-oracle campaign. All eleven completed scaling results equal the prior closing-memo screen after excluding diagnostics. Case 5 prunes five suffix searches in 236 envelope evaluations; cases 6 and 7 prune four and seventeen respectively. Completion remains 11/16. Two-line cases prune none in this screen. The result supports testing tighter shared-resource bounds rather than claiming scalability from this relaxation. Source snapshot: 266 files; archived replay status is recorded in the verification artifact when complete.

Archived continuation-bound replay verification completed: all 16 fingerprints match; all 266 source hashes match current and archived files. See `20261012-connected-continuation-bound/verification.json`.

## Resumable prefix proofs clear a further connected case

`AllocationFrame.next` now optionally suspends its compiled lexicographic traversal after each feasible prefix. A proof callback may prune the subtree and restore its reserved input slots, or resume exactly where it stopped. Traversal order, complete-action feasibility and tie handling are unchanged. The ordinary path has no callback. Budget/resume tests compare the complete sequence against the original traversal and explicitly filter a pruned subtree.

`continuation_prefix.py` bridges to the existing prefix cost envelope and common-first-production bounds. It reconstructs the live actual or hypothetical purchase payload through the same helper as closing selection. It reserves worst-case shared-proof work before evaluating, skips proofs that do not fit, charges actual batch/scenario work, and falls back to ordinary optimistic prefix bounds. Only strict inferiority beyond tolerance permits pruning. Unsupported calendars return infinity. Original future stocks are optimistic because these bounds relax future supply. `prune_prefix=False` and `shared_first_states=0` remain defaults; the benchmark enables them with `prunePrefix` and `sharedFirstStates`.

Evidence: `stats/buying-implementation/20261012-connected-prefix-bound/`. Ten targeted tests passed in 49.925 seconds, including 24 seeded complete-result comparisons and the existing independent-oracle campaign. Four additional tests passed after separating action-prefix and proof-work failure counters. The screen completes **12/16**, up from 11/16. Newly completed case 6 (single line, capacity 4, two suppliers, two periods, two outcomes) matches the complete public result of the larger-budget connected closing search with both new pruning modes disabled: value 13, 12,270 versus 1,353 allocations. This is not a separate unpruned phase-oracle run for case 6; its comparison script and scope are preserved.

Case 7 and the three larger two-line cases still reach limits. Proof cost and joint closing work remain material; this bridge is not yet fully compiled or population-ready. Final source and archived replay verification are recorded in this experiment's `verification.json` when complete. Initial `run/` predates a diagnostic-only failure-counter refinement; `final-run/` and `replay/` use the archived final source. Concurrent local execution means these timings are not an isolated performance claim.

## Existing proof reuse advances connected completion to thirteen cases

The connected driver now exposes opt-in `proof_memo_entries` and `closing_cash_relaxed`. Per-solve bounded-entry caches reuse existing proposal hints, joint bounds (or normalized cash-relaxed profits), and shared-first-production bounds. Proposal hits still require a fresh strict certificate; exact closing selection retains its separate full-input key and real ledger replay. Caller cash, offsets and numerical cushions are recomputed according to the existing normalized-bound contracts. The caches bound entries, not total Python-object bytes; they remain experimental Python containers. Defaults remain zero/false.

Evidence: `stats/buying-implementation/20261012-connected-proof-memo/`. Ten targeted tests pass in 91.284 seconds, including 24 seeded full-result comparisons with both joint-proof variants, cache capacity/eviction checks, prefix traversal checks and the existing independent-oracle campaign. The fixed screen now completes **13/16**. All twelve earlier complete public results are unchanged. Newly complete two-line case 13 has value 17 and matches the entire public result of a larger-budget connected closing search with new pruning and proof reuse disabled: 9,957 versus 1,292 allocations. This comparison is preserved in `verify_new_case.py` and `new-case-verification.json`; it is not a separate unpruned phase-oracle run of this case.

Case 7 still reaches an allocation limit; cases 14 and 15 still reach closing-work limits. Working source is archived in 269 files. `archived-replay/` is the independent replay from `/tmp`; the earlier `replay/` was invoked from the workspace and is retained only as another working-tree run. `verification.json` records terminal/hash/fingerprint checks when completed. Local overlapping runs prevent isolated timing claims.

The user explicitly asked whether 16/16 ends the work: it does not. This screen is only a small solver feasibility checkpoint. Configured-population practicality, final model/forecast/funding decisions, full-world accounting/runtime/checkpoint/UI integration, held-out generation/shock/fairness/recovery gates and adoption/rollback review remain required even if all sixteen complete.

## Proof ordering experiment rejected after measured work regression

A diagnostic wrapper around closing selection and certificate calls preserves the entire case-15 result including counters. It records 1,800 closing solves: 1,787 strict certificates and 13 inconclusive `not-strictly-dominated` proofs. Certificate work totals 79,685; total closing work is 164,876, while prefix-bound work is 270,558. Thus the largest expanded case cannot be characterized solely as a closing bottleneck. A few fallback calls are expensive (up to 2,335 allocations), but shared-prefix evaluation dominates the combined charge. Evidence: `stats/buying-implementation/20261012-closing-proof-diagnosis/`.

An isolated candidate evaluated the cheap ordinary prefix bound before the shared bound for multiple lines. Seven targeted tests passed in 79.728 seconds; all 16 archived screen fingerprints matched and complete expanded-budget results remained identical. However, allocation counts did not fall, and combined work rose from 34,234 to 35,914 in case 14 and from 447,075 to 461,836 in case 15. Case 7 was unchanged at 20,890. The original-budget screen remained 13/16. This ordering is **rejected**, and only the candidate's `continuation_prefix.py` change was reverted to its prior archived version.

`stats/buying-implementation/20261012-prefix-proof-order/` preserves the candidate, tests, fixed/expanded specifications, results, comparison and archived replay. Its `verification.json` also confirms all 273 current implementation/test/browser hashes again match the 587-test integration checkpoint. No production model, outside parameter or logic changed. Next work should target shared-proof evaluation/reuse and the limited expensive fallback cases rather than repeat this weaker-proof-first strategy. All processes from this experiment completed.

## Exact per-line recourse reuse with unchanged work charges

The opt-in `shared_recourse_memo_entries` cache targets repeated `line_envelope` calls inside the multi-line shared-first bound. Its immutable key includes the complete line, remaining finished inventory, every held input, every input quote, production allowance and sales opportunity quantity/quote. It caches only a completed finite envelope value. First-period costs, posterior weighting, caller offsets and rounding cushions remain outside the cache. Capacity is an entry limit, not a total Python-byte claim; default is zero.

Both hits and misses retain the prior scenario-evaluation charge. Thus the cache cannot clear a work-budget failure merely by reclassifying effort. It changes neither the bound value nor the strict pruning condition and changes no outside economic parameter or rule.

Evidence: `stats/buying-implementation/20261012-shared-recourse-memo/`. Twelve targeted tests pass in 50.740 seconds, including changed-key/capacity cases and 24 seeded complete-result comparisons. All sixteen original screen result/failure payloads match the earlier proof-memo screen after removing only the new recourse counters. Completion remains 13/16. Source snapshot contains 270 files. `timing.py` performs a warm, interleaved cache-off/on comparison of expanded case 15 and asserts complete-result and existing-counter equality every time; timing and archive terminal checks are recorded in their artifacts when complete. The latest full-discovery checkpoint remains the earlier 587-test integration audit.

Warm interleaved case-15 timing completed: median 15.5389 seconds without recourse cache versus 12.0806 seconds with it (22.3% lower; three measured samples each). Every public result and existing work counter matches. Each cached solve has 140,436 hits and 2,832 misses. This supports retaining the opt-in cache, not a population or tail-latency claim. See `20261012-shared-recourse-memo/timing.json`.

## Joint bounds reduce expensive closing fallback work

The experimental `closing_joint_fallback` option applies the existing joint or cash-relaxed joint upper bound inside lexicographic closing fallback. It runs only after an incumbent result exists, the ordinary bounds have not rejected the box, and the box is not a singleton. A strict value gap beyond the existing tolerance is required to prune. Leaf order and payment/unit/lex tie rules remain unchanged; ties are explored. Joint batch/scenario work shares the existing closing budget, and certificate plus fallback proof work is added rather than overwritten. Defaults remain false.

Evidence: `stats/buying-implementation/20261012-joint-closing-fallback/`. Ten targeted tests passed in 48.119 seconds, including direct exhaustive comparisons, both joint proof variants, seeded full-result comparisons and existing proof-budget tests. The original screen remains 13/16. Expanded case 14 falls from 2,646 to 2,325 allocations and 34,234 to 33,391 total work. Expanded case 15 falls from 23,749 to 12,124 allocations and 447,075 to 406,175 work. Case 7 is unchanged at 7,238 allocations/20,890 work. All three expanded public results match exactly. These are diagnostic budgets, not original-screen or population success.

The optional mode is retained because it reduces both allocations and work in the difficult multi-line cases. It does not change purchasing economics or outside parameters/logic. Source snapshot contains 271 files; `verification.json` records archived replay and hash checks when terminal. Full compilation, representative performance, remaining model decisions and world/economic/adoption gates remain open.

## 2026-10-12 frozen phase-entry overhead wire contract

`Purchase.frozen_overhead` now passes through the compiled path. Calendars without an explicit snapshot remain schema 1 and keep their existing payload bytes. A calendar containing a snapshot is schema 2: purchase integer header timing code 2 identifies the frozen snapshot, and one float is appended after the existing offer prices/reliabilities. Codes 0/1 retain before/after calculation. Decode requires the matching schema and canonical representation; schema 1 cannot reinterpret a frozen event.

Own-quote payloads retain the appended value while removing switching fees as before. Actual production uses the value directly, with no recomputation or cash transfer. Event grouping compares snapshots even in neutral queries. Frozen purchase observations use schema 2 with the snapshot appended after existing values; other observations keep schema 1. History interning and observation decoding retain the new value. This exposes already-known phase-entry overhead, not future information. Closing/prefix reconstruction retains the original event field.

This is research planner integration, not a new production rule. The ordinary engine still takes its own unchanged phase-entry snapshot. Raw-record state projection, deferred seller settlement mapping and adopted forecast inputs remain outstanding.

## 2026-10-12 native terminal-value schema

Calendar schema 3 adds immutable `terminal_modes` and `terminal_quantities` arrays. Mode 0 is the legacy integer-indexed table; mode 1 is an explicitly supplied `LinearQuantityValue`. Existing terminal offsets delimit both values and quantity knots. Mixed calendars retain every mode explicitly, and frozen-overhead purchases remain compatible. Calendars without native curves keep their existing schema 1/2 encoding. Decode checks dimensions, modes, finite strictly increasing native knots and canonical round trips; changing a schema number cannot reinterpret a payload.

Compiled terminal evaluation uses integer lookup for mode 0 and binary-search piecewise interpolation for mode 1, rejecting missing quantities or extrapolation. Both resident result capture and arena result buffers use these arrays. The independent oracle uses the separate Python curve implementation. Integer-only cost/closing/shared bounds decline native curves until a native bound is implemented; the general exact search remains available for integer states with native terminal curves. This does not yet support fractional state buffers, and it does not adopt a forecast or terminal-value calibration.

## 2026-10-12 native resident state and observations

Calendar schema 4 marks a native fractional initial state or input slot domain. It includes the schema-3 terminal metadata. Resident quantities, phase-book stock and company input slots use float64 buffers for schema 4; integer legacy buffers retain their existing representation. Snapshot/fork/arena export retain fractional quantities. Prescribed purchases and production use original item units and the native no-purchase basis rule; phase-book sales remain whole units. No subunit scaling or fixed residue is used.

Opening-book observations with fractional quantities use observation schema 3: the quantity vector follows the three financial scalars in the float payload, then basis and quote vectors. The integer payload contains its count rather than truncated quantities. Other observations retain their previous schemas. Numeric history validates and stores the new payload.

Native Resident and ArenaResident prescribed execution, own-quote queries, terminal capture and atomic failure are verified against the independent ledger. The older per-event Executor adapter explicitly declines schema 4. Connected/event-tree allocation search remains guarded until allocation limits and endogenous funding traversal support the fractional resource domain; enabling execution is not a claim that fractional optimization is finished.

## Native fractional supplied-demand allocation search

The action frame no longer uses `int(slot-held)` for native resources: `held=1.0000000000000002`, slot 2 and purchase 1 is feasible under native addition although subtraction floors to zero. Native frames enumerate whole-lot offer stock and use integer aggregate stock bounds, checking signed-int64 capacity before traversal. The existing ledger decides slots, cash, fees, physical storage and production. This preserves native arithmetic without rounding holdings, enlarging slots or changing production gates. The independently implemented exhaustive oracle uses stock ranges too.

Connected supplied-demand search now supports fractional resources in Resident and ArenaResident. The oracle supports them with callable supplied funding and exhaustive event-tree traversal. Endogenous fractional funding remains rejected pending an own-quote cap audit; the raw projector remains guarded. This is a correctness step, not a scalable enumeration claim or adoption of supplied demand as the industrial model.

Evidence: `stats/buying-implementation/20261012-native-supplied-search/`. The initial 12-test run had three Numba errors because a frame buffer was read-only; the corrected frame owns a writable copy. Then 21 targeted tests passed in 28.789 seconds. Expanded native testing passed four tests in 0.778 seconds, followed by five in 0.666 seconds after adding optional-proof coverage; these sets overlap. Tests compare complete policies, leaf states, accounts, values and observations with the independent oracle, including the rounding boundary, split offers, shared/repeated inputs, two installed lines, two periods and observed outcomes. Explicit stock-grid enumeration is also checked independently. Commands use the established Python 3.12 interpreter and `PYTHONPATH=.pydeps:.:tests/py` with `-m unittest test_buying_v2_native_search test_buying_v2_native_ledger test_buying_v2_continuation_actions test_buying_v2_continuation_search test_buying_v2_native_resident`; the final expanded module is `test_buying_v2_native_search`.

No production code or outside economic parameter changed. The original synthetic acceptance screen was not rerun and remains last measured at 13/16. Forecast adoption, endogenous native funding, full-world integration, population performance and economic/rollout gates remain open. The full goal remains unfinished.

Archived-source execution from `/tmp` also passed all five native-search tests; `archived-tests.log` preserves the timing. All 310 working/archive source hashes match (`verification.json`). All commands are terminal; no process from this milestone remains active.

## Native fractional endogenous funding

Own-quote query caps now use the ledger's native-addition predicate rather than flooring `slot-held`. The compiled query finds the largest supported whole-lot purchase by bounded integer binary search; the independent Python oracle uses exponential bracketing followed by bisection. Both preserve the existing effective slot `max(held,slot)` and reject an unrepresentable signed-int64 action range explicitly. No stock, slot, physical-space, fee or production rule is changed. The query payload retains integer cap typing rather than converting large integers through floats.

Native connected continuation funding is now enabled, as is exhaustive event-tree continuation funding. Supplied-demand support is retained. Integer-only closing/prefix proofs still decline unsupported native resources. Native event-tree optimized traversal and slot-deficit funding remain unsupported. The raw projector still rejects fractional records pending its own integration; no calibrated forecast or terminal model is adopted by these arithmetic changes.

Evidence and exact verification logs: `stats/buying-implementation/20261012-native-endogenous-search/`. Tests cover exhaustive small native-addition caps, large float boundaries, explicit frame limits, complete oracle comparisons with split supplies, fees, cash limits, wholesale lots, multiple lines/shared inputs and multiple periods/outcomes. The six-module command uses Python 3.12 and `PYTHONPATH=.pydeps:.:tests/py`: `-m unittest test_buying_v2_native_query_cap test_buying_v2_native_search test_buying_v2_native_ledger test_buying_v2_continuation_query test_buying_v2_continuation_endogenous test_buying_v2_continuation_funding`. Intermediate and final logs are distinct; their test counts overlap.

Next connect fractional raw-state projection without rounding its input slots or holdings, then exercise captured-state planning with explicitly labeled supplied scenarios. Full forecast adoption, production integration, population performance and economic/rollout gates remain unfinished. The synthetic acceptance screen is not rerun by this milestone; the full goal remains active.

Final verification: **35 targeted tests passed in 42.599 seconds**. Archived-source execution from `/tmp` passed **10 native tests in 25.985 seconds**. All **311** working/archive source hashes match (`verification.json`). All milestone commands have exited; no process remains active. The NumPy/SciPy warning is nonfatal and dependencies are unchanged.

## Native captured-state projection and settlement parity

The raw-state bridge now preserves finite nonnegative fractional holdings, finished stock, opening/current book stock and input slots. Exactly integral quantities retain integer encoding for legacy calendar compatibility; no fractional goods are rounded. Whole-unit supplier offers use `floor(current stock)` while the raw capture preserves the residue: this is the available whole-unit action range, not a mutation of seller stock. Fractional pending stock movements that cannot be represented as whole committed sales still fail explicitly; arbitrary fractional deliveries are not introduced. Recipe/yield/capacity and other existing validation restrictions remain.

Real-book comparison exposed a research-ledger mismatch: it recalculated basis on zero-sale lines. Both the independent ledger and compiled replay now leave basis untouched when no goods sold and reconstruct pre-settlement units after the stock delta for sold lines, matching the existing `InputMarket.settle` operation order. The production book itself is unchanged. Tests compare actual phase production and real pending book settlement at fractions 0.1, 0.5 and 0.999999999, including native Resident replay; another case checks fractional slots and supplier residues.

Evidence: `stats/buying-implementation/20261012-native-projection/`. Final targeted verification passes **35 tests in 2.075 seconds**. Initial failures are preserved separately: integral float encoding, zero-sale basis mismatch and a test calendar with an unclosed book; these were corrected before the final run. The command uses the established interpreter with `PYTHONPATH=.pydeps:.:tests/py -m unittest test_buying_v2_native_projection test_buying_v2_prepurchase_projection test_buying_v2_native_search test_buying_v2_phase_ledger test_buying_v2_continuation_executor` (place the interpreter before `-m`).

`audit_records.py` verifies original capture hashes and projects all **1,035 preserved captures** from the 300/4,200-company runs, now requiring exact slot/held/finished preservation as well as cash, identity, overhead and equity/room reconciliation. No capture is unsupported. These saved samples and the constructed fractional test worlds are distinct evidence; this is not a new population experiment or forecast calibration.

Next run bounded connected planning on representative captured states using explicit diagnostic scenarios/terminal assumptions, preserve limit failures, and measure practical work before claiming integration or scaling. Full-world policy/history/persistence/UI integration, adopted forecasts and economic/performance/rollout gates remain open. Production code and outside parameters are unchanged; the full goal remains active.

Archived execution from `/tmp` passes all eight projection tests (`archived-tests.log`). All 312 working/archive source hashes match. All milestone commands have exited, and no process remains active. No dependency change was made.
