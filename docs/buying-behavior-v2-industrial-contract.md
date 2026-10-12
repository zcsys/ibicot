# Industrial buying reference contract

Status: executable small-market contract under development. This specifies the full purchase action space and its connection to actual production. It does not adopt an output forecast, terminal-value calibration, or production purchasing policy. The [master plan](buying-behavior-implementation-plan.md) still requires scalable optimization, world settlement, validated demand information, and long-run tests.

## Supported actions and resources

A company acts within one manufacturing phase, with a declared ordering of its eligible production lines. Each sampled offer identifies one material and stable supplier, positive unit quote, currently available stock, and purchase lot. An allocation specifies a nonnegative whole-lot quantity for every offer. Multiple suppliers of the same material may contribute, including cheaper partial suppliers. Inputs may serve several lines and recipes may consume repeated units of a material.

The company has opening input quantities and book bases, per-material input slots, physical free storage after machinery and existing inventory, and one cash balance. All purchase allocations are checked jointly against these resources. A useful unmatched buffer is an admissible action; the optimizer may choose it only if the explicitly supplied valuation justifies it. The independent enumeration does not require purchases to be a minimal complete kit.

Pay the accepted single fee per input-product order if an outside delivery occurs and the original incumbent's opening stock can meet the frozen positive funded bid. Bid derivation remains a separate coupled-planning requirement; fixture-supplied bids are not a production algorithm. Preference qualification under the accepted whole-demand rule must be added to world settlement after industrial per-quote demand is specified.

## Production feasibility is execution feasibility

For each purchase allocation, capitalize goods into the material's weighted inventory basis. Fees do not enter inventory basis. Deduct purchases and fees from the shared cash balance, then simulate the actual line sequence:

1. Bound batches by installed capacity and output-slot room supplied by the adapter, available recipe inputs, and remaining cash for conversion.
2. Compute the book-basis input cost per output plus conversion.
3. Apply the retained production margin ramp and reduced-batch overhead test.
4. Consume the gate's actual output requirements, pay conversion, and pass the remaining inputs/cash to the next line.

Production is therefore not a free output vector chosen by the optimizer. The reference cannot purchase a cheap missing complement and then assume output that the unchanged historical-cost gate prohibits. It also cannot spend cash independently for each recipe. The adapter must pass correct phase-specific capacities, room, overhead, and ordering; no future-phase inventory or receipts are available early.

## Objective and unadopted valuation inputs

For each feasible purchase allocation, evaluate:

`value of actual new output + terminal value of remaining inputs - goods payment - fees - actual conversion cost`

Output values are explicit tables by line and quantity. They must eventually represent realizable sales revenue plus any nonoverlapping terminal finished-inventory value, conditional on existing finished stock and information available before the decision. The current tests provide simple scenario tables; these are not calibrated forecasts. Existing input purchase cost is sunk in this incremental objective, but its book basis still constrains the actual production gate and later COGS.

Terminal input values are explicit tables by remaining quantity. Zero is one test scenario, not an imposed ban on useful buffers. Prevent double counting input value already consumed in valued output. Fixed overhead remains in the production gate; valuation comparisons must distinguish sunk period costs from any incremental operating expense not already represented.

Buying nothing is always enumerated. It can still lead to production from owned inputs, so its value need not be zero. Report gains relative to that actual no-purchase plan when comparing the benefit of procurement. For exact objective ties, prefer lower goods-plus-fee payment, then fewer purchased units, then the declared offer allocation ordering. These deterministic ties still need buyer/supplier identity fairness validation.

## Implementations and verification

`tools/buying_v2/industry_oracle.py` independently enumerates all small-market allocations and computes execution without importing the optimized solver or production-gate helper. `tools/buying_v2/industry.py` uses a compiled odometer enumeration and the actual shared production gate. Both reject oversized oracle jobs explicitly; neither is a population-scale purchasing implementation.

Six tests include cheap partial plus fallback supply, the $100-owned-input/$1-complement counterexample, two lines competing for shared cash, useful unmatched buffers, lots/storage/one-fee checks, and 160 independent randomized split-supplier/multiple-line comparisons. Test outcome and runtime are preserved under `stats/buying-implementation/industrial-reference-tests.log`.

The exact search size is the product over offers of `(maximum purchasable lots + 1)`. This is exponential in the number of offers and is unsuitable for full-population execution. The next optimizer must reduce this space with proved bounds or decomposition, retaining every supported economic action. In particular, cheapest purchase cost alone is not automatically a valid dominance rule: inventory basis changes the production gate, and changing actual output can change expected value. If an approximation is needed, it must be named, measured against this oracle, and explicitly reviewed rather than silently replacing the full problem.

## Remaining decisions

D3 still needs a precise corrected-replenishment objective and its scalable allocation algorithm. D4–D5 still need defensible output-price/quantity and terminal-value estimates, including no-history and recovery. D6 now has a full small-market reference action space but no scalable solver. These are implementation work remaining under the goal, not passing adoption gates or permission to deploy the small oracle.


## Exact pruning and its current limits

`industry_bounds.py` implements a readable best-first box search, while `industry_search.py` implements a compiled depth-first search. Both retain every whole-lot offer allocation. A box gives lower/upper purchased quantities per offer; infeasible minimum cash/storage requirements prune the entire box. Search limits raise `SearchLimit` and never silently return an approximate optimum.

The objective upper bound initially gives each line its maximum possible output value independently and gives inputs their maximum possible remaining value simultaneously. This deliberate resource double counting occurs only in the bound, never in reported earnings. Minimum committed goods/fees are deducted. Relaxing the gate and shared-resource competition cannot reduce that upper bound.

For each line, strengthen the bound by subtracting a lower bound on the additional input and conversion cost needed for that line's particular output. Each missing input unit is provisionally priced at the cheapest remaining quote, ignoring finite stock competition and lots; other lines remain optimistically free. Taking the minimum across these per-line upper bounds remains safe. This does not assume that cheapest procurement dominates other cost-basis/gate outcomes.

Prefix maxima avoid rescanning terminal-value tables. When the supplied output-value table is discretely concave, the anchored value subtracts convex missing-input cost and linear conversion cost; binary search locates its maximum. Nonconcave tables retain exhaustive quantity scanning. Outward floating-point allowances protect pruning near numerical boundaries.

Nine tests pass in `industrial-bound-certificate-tests.log`: existing examples and 160 randomized multiple-line comparisons, explicit work-limit/input-validation cases, and 80 random boxes with concave or nonconcave values whose upper bounds are checked against every feasible allocation in each box. Full-scope correctness and numerical review remain necessary before adoption.

The preserved initial scaling probe (`industrial-search-scaling.json`) reaches its 100,000-node limit on the larger synthetic cases. The stronger bound solves them exactly (`industrial-anchored-search-scaling.json`). Prefix/concavity optimization lowers the capacity-256, six-suppliers-per-input probe from approximately 6.01 to 2.27 ms (`industrial-concave-search-scaling.json`), with 1,605 nodes and one evaluated leaf out of about 8.3e28 possible allocations. These are simple synthetic one-line warm probes, not performance claims for heterogeneous full-world firms. This remains insufficient evidence for population-scale deployment.


## Actual-company workloads and verified relaxation

`world_cases.py` extracts snapshot resources and sampled offers without mutating the world. Nine first/middle/last stable-line cases cover the three current manufacturing routes at tick 360 of the preserved seed-137 baseline. These are coverage fixtures, not a statistically representative sample. Output quotes times quantity are explicitly synthetic algorithm-test values; fees and terminal values are disabled. They do not validate a demand model. Multi-line extraction follows installed-line production order within the phase. Earlier extraction incorrectly rotated this order: the kernel rotates planning, but executes production in installed slot order. Single-line archived workloads are unaffected.

The original search hit its 20,000-node limit for firm 4031, which owns 1,992 units of one input and zero of its C3 complement. The captured offers include several equal-price complement suppliers. Preserve `20261012-industrial-world-cases` as the unsuccessful probe.

`industry_relaxation.py` provides a verified fast path for a single line, no payable fee, zero terminal value, and a uniform lot per material. It enumerates possible output quantities and computes each minimum required input basket. This relaxes the production gate, not the purchase action space of the fallback. Actual execution must realize the relaxed optimum before the fast path is accepted; otherwise full search remains. Multiple lines, useful terminal buffers, unequal lots and payable fees still use the full solver.

All nine cases now solve in `20261012-industrial-world-cases-relaxed`. Firm 4031 purchases three eight-unit partial fills and produces 24 units; it took approximately 0.256 ms including Python packing in this probe. Other warmed cases were about 0.24–0.31 ms. Compilation is included only in the first case. These times remain too indirect to certify a full-population hot path; fees and actual forecast tables can defeat the fast path.

## Numerical decision convention

The industrial prototype now treats objective differences within `1e-9 dollars + 1e-12 × max absolute compared objective` as ties. Payment comparisons use the same absolute/relative rule before fewer purchased units and lexicographic allocation. This explicitly replaces the early prototype's strict binary64 objective ties, which distinguished mathematically equal-price split baskets by floating summation noise. It is a candidate numerical convention, not a change to posted money or inventory basis. The independent oracle, exhaustive compiled reference, readable/compiled search and relaxation use the same declared comparison scope; actual production still uses the existing gate arithmetic.

This numerical change is separate from behavior-preserving retail optimization. Do not claim byte-identical industrial allocations versus the earlier strict-tie prototype. Oracle tests include 400 randomized decimal-price/lot/gate cases exercising both relaxation acceptance and fallback, in addition to the existing multiline and bound checks. A nonfinite/infeasible actual result cannot certify the relaxation; postproduction-storage infeasibility has a dedicated regression.

## Atomic reference settlement

`industrial_settlement.py` implements T2 settlement independently of the future valuation adapter. It receives an already solved allocation and funded per-quote demands, then validates every quantity, phase/input mapping, live quote/stock, buyer cash/inventory/preference, per-input and total storage, incumbent bid and existing loyalty formula before mutation. Stale inputs require replanning. Purchased cost is accumulated into book basis in the declared offer order; fees remain separate expenses/income.

A positive leg records its remaining request, goods transfer, seller revenue/COGS, input basis, and intermediate sales. One fee is posted per qualifying input order. A supplier changes preference only by individually filling the whole funded demand at its quote. The existing native-company-class AOV arrays count successful transaction legs; new product-order counts remain separate rather than silently changing the annual adaptation denominator. The compiled population adapter remains unfinished.

Settlement tests cover actual split cash/stock/revenue/COGS/basis, all four fee/preference combinations, stale stock, invalid phase, and atomic rejection of an oversized fallback request. This verifies the transaction contract; it does not derive funded demands or authorize a production policy.


## Coupled funding and D3 reference integration

`funding.py` removes seller-stock caps for the hypothetical funding question while retaining shared company cash, storage and lot constraints. Each input references its incumbent quote when valid, otherwise the cheapest discovered quote. To compute demand at another quote, replace that input's reference and solve the joint problem again; other reference quotes stay fixed. These hypothetical calculations do not post supplier requests. Freeze incumbent quantities from the original joint plan; actual selection reserves payable fees and respects cumulative per-quote fallback limits inside its feasible space.

The value-model funding path additionally retains actual production gates and explicit scenario value tables. It is not an adopted forecasting model. The separate D3 replenishment path maximizes purchased input item count up to existing storage deficits, then minimizes goods plus fees. Conversion is not reserved in that comparison policy, matching the existing separation of replenishment and production. This can leave no cash for production or favor an unmatched cheap buffer; batch-first comparison and economic suitability remain open.

`replenishment.py` uses an exact uniform-lot fee-subset solver for nonbinding total storage. Binding space or equal-price offers with differing funded caps use bounded exhaustive box search; exceeding the limit raises explicitly. Independent tests cover 600 cash/fees/lots/space fixtures and 1,000 arbitrary per-quote cap fixtures. The latter found a tie-order counterexample, now retained by its seeded regression. Fixed stable-ID ties still need fairness validation.

`industrial_adapter.py` gathers actual phase resources and five distinct alternatives plus the incumbent. Normal replenishment problems contain no synthetic output values. It preserves over-slot stock after installation changes and blocks new purchases of that input. `buy_t2_reference` executes one atomic company-phase basket. Its caller owns the once-per-phase order boundary; this API is not an idempotent external order endpoint.

`ReplenishmentReferenceEngine` connects this adapter to the real reference production and phase-end accounting through an optional purchase callback. Its policy marker is `v2-t2-replenishment-reference-v1`; T1 still uses baseline purchasing. Ordinary reference calls omit the callback, and compiled production defaults remain unchanged. Small complete-world accounting/continuation tests pass. Four ticks of all-phase baseline comparison against independently loaded HEAD source match every world array and cost/equipment sinks. This is not compiled industrial parity, population-scale validation, or live adoption.

## T1 reference purchasing

`refinery.py` implements the same D3 comparison objective for all installed T1 recipes against one company cash/storage pool. It discovers up to five distinct T0 company alternatives plus the incumbent per raw element, retains empty-stock offers, and uses the configured wholesale lot for every delivery. T0 IDs identify companies; T2 input-market supplier IDs identify lines. The discovery stream separates the T1 raw markets from T2 input markets.

Settlement validates the entire basket before mutation, including current stock/quotes/basis, valid installations, lots, storage, funded fallback quantities and incumbent fee eligibility. It posts raw inventory/basis, T0 cash/revenue/COGS, T1 cash, separate fee income/expense and whole-demand preference qualification. Receipts post immediately to T0 as in the ordinary T1 phase. T1 production retains the existing compiled execution and installed-product order. The legacy annual T1 AOV denominator remains the number of companies with positive `t1Bought`, not the number of product orders or legs.

`IndustrialReferenceEngine` replaces both industrial purchasing phases under marker `v2-industrial-replenishment-reference-v1`. The ordinary T1 reference function has an optional purchasing callback, omitted by production callers; four ticks of all-array comparison with independently loaded HEAD source match exactly. T1 deficit/request fields represent storage-target quantities; `t0FundedReq` represents the stock-unconstrained coupled reference quantity. Supplier demand/availability fields currently represent positive delivery legs only. Empty-stock failed-request traces still need an explicit implementation contract; do not interpret this policy's observed reliability as a completed correction of demand measurement.

The isolated runner accepts `--policy industrial-reference` (or `t2-reference`, default `retail`), records policy identity, and archives source/config/checkpoints. At that initial reference milestone, the purchasing sidecar was retail-only. The later compiled execution and industrial-observation milestones below supersede that limitation; live production integration remains outstanding.

Screening evidence: `stats/buying-implementation/20261012-both-industrial-reference-screen-137/`, seed 137, 30 ticks, 300 manufacturers and 1,000 distributors, with the configured T0/T1 populations. All recorded company/money/goods tolerance ratios pass; stock/cash remain nonnegative and there are no price-bound contacts. Warm median is approximately 1,130 ms on the local host, including unisolated reference execution. This is already unsuitable as a production implementation at the reduced manufacturer population; no full-population performance claim follows. It is not long-run model validation.

## Compiled industrial execution

`replenishment_compiled.py` implements joint quote funding in typed arrays. Nonbinding-space reference funding uses the same ascending-price/reverse-index tie traversal and sequential cash subtraction as the reference allocator; a total-spend shortcut is deliberately avoided at rounding boundaries. Actual selection retains the fee-subset solver. Binding total space and heterogeneous same-price demand caps use exact depth-first box search, with conservative outward bounds, the declared numerical tie convention and an explicit node-limit error. A limit never returns an approximate basket.

`refinery_compiled.py` and `manufacturer_compiled.py` sample and settle whole company baskets inside the retained compiled production loops. Optional callbacks leave ordinary callers on their existing purchasing path. Experiment-specific compilation of the shared loop uses the v2 source-aware cache, so edits to experimental dependencies invalidate compiled callers. Owned industrial inputs must be integral; compiled callbacks reject fractional owned quantities before transfers, matching the reference snapshot validation instead of truncating them.

`IndustrialCompiledEngine` uses the same purchasing-policy marker as the validated reference engine. Both tiers preserve company sequence, production order, live supplier availability, fee recipients, weighted basis and cash-transfer timing. Complete-world comparisons include installed multiline ownership and a 4,200-manufacturer configuration that contains both C3 and C4 supplier/buyer cohorts. Independent allocation enumeration supplements implementation parity.

Preserved proofs and screening runs:

- `industrial-compilation-world-proof.json`: 210 stored arrays, checkpoint JSON, schemas/configuration and per-tick invariant histories match the prior 30-tick reference run with 300 manufacturers/1,000 distributors. Compiled warm median was 12.69 ms, versus reference 1,129.98 ms. Compilation/startup are excluded from these warm medians.
- `20261012-industrial-compiled-fullpop-137`: full starting population, seed 137, ticks 1–30, recorded invariants passing; warm median 499.02 ms.
- `industrial-funding-specialization-world-proof.json`: another 210-array exact comparison at full population after reference-funding specialization. Warm median fell to 435.29 ms in `20261012-industrial-compiled-funding-fast-137`.
- `compiled-industrial-warm-profile.log` and its preserved script profile fresh-world ticks 2–6 without recording. Manufacturer phases dominate; supplier-book construction remains a material Python cost. This informed use of the existing vectorized book builder in the experimental compiled path.

These are short, single-seed screening measurements. They do not pass the relative speed budget, p95/memory gates, long-run health, fairness, forecast quality or adoption requirements. The industrial failed-request measurement gap remains; compiled parity preserves that explicitly incomplete contract rather than certifying its economic meaning.

The vectorized-book version subsequently completed the same 30 full-population ticks at 400.20 ms warm median. `industrial-vector-book-world-proof.json` confirms exact equality of its 210 recorded arrays and checkpoint/metric data against the preceding full-population run. The final 19-test targeted regression includes fractional-input rejection, C3/C4 multiline world parity and existing production contracts. Relative timing, tail latency and memory validation remain open.

## Industrial purchasing observations, version 1

The purchase recording envelope is now version 2, retaining the original retail schema and adding a separately versioned industrial array. `industrial_observations.py` aggregates one row per buyer-tier/input market with archived stable product IDs. A decision is one company's evaluation of one input in one purchasing phase, including zero targets and missing suppliers. Counts are not distinct-company counts; a multiline company may evaluate a shared input in more than one phase.

The protocol is stock-aware: suppliers are observed before allocation, and only positive chosen allocations create transaction legs. An empty-stock discovery is therefore recorded as a **funded availability check**, not invented as a submitted order or backorder. The reducer records these hypothetical checks separately from quote-funded remainders on positive legs, purchased units, storage targets, the coupled reference quantity, fees and preference changes. It does not modify the world or existing supplier reliability. Legacy demand counters remain quote-remainder observations and can exceed actual placed quantities; they must not be labelled unique incoming market demand.

For each sampled offer with positive funded quote quantity, a sufficient-stock check asks whether opening live stock, rounded down to whole purchase lots, covers that quantity. Zero-funded quotes create no availability check. A below-lot-stock check records positive funding with less than one available lot. Incumbent availability against its own frozen bid is counted independently of fees and preference changes. Stock-limited and other-limited leg flags are diagnostics that may overlap; they do not allocate causal units lost to stock versus cash/fees/shared resources.

`referenceShortfall = max(0, referenceFundedQuantity − purchasedQuantity)` is accumulated per decision. The reference quantity is evaluated at the incumbent quote, or the cheapest observed quote without a valid incumbent, with joint cash/storage funding but without seller-stock caps or switching fees. Purchases may exceed this reference when cheaper alternatives are selected. Do not calculate a purported fulfillment rate as purchased/reference quantity, or label the reference shortfall as stock loss.

`purchase_reporting.py` projects summed period totals and explicit denominator ratios. A zero denominator or uninstrumented tier yields null. It rejects old schemas, missing arrays, nonfinite/negative observations, gaps/overlaps, and windows that do not cover a completed run. T1/T2 coverage is declared separately so an uninstrumented tier cannot masquerade as zero demand. Purchasing arrays reset each tick; continuation needs no hidden observation history and subsequent recorded metrics are checked across checkpoint resume.

These observations support the next information-model comparison; they do not settle whether firms should communicate additional nonbinding inquiries or use a different request protocol. Such a change would affect reliability/learning and requires its own versioned treatment and evidence. No such economic change is hidden inside this instrumentation work. Bounded [industrial decision samples](buying-behavior-v2-decision-traces.md) and a [recorded-data inspector](buying-behavior-v2-inspector.md) now support reconstruction. Production-dashboard integration remains outstanding.

Measurement-only full-world proof: `industrial-observation-world-proof.json` compares ticks 1–30 at full population and finds every pre-existing recorded array/checkpoint/config/invariant unchanged. The added 54 industrial rows are separately shape/coverage/finite-value checked. `industrial-purchase-summary-137.json` provides the summed-period projection. The final eight observation tests pass; the instrumentation does not establish economic suitability or complete the remaining dashboard/request-protocol work.

## Objective and continuation-model boundary

The [value-model contract](buying-behavior-v2-value-model.md) now supplies executable storage-versus-batch-first comparisons and a small non-anticipating continuation oracle. These counterexamples show why maximizing output is not sufficient and why an input buffer's future value can depend on remaining cash and complement arrival. The existing additive output/terminal-table optimizer is an exact solver for its declared tables; it is not thereby an exact implementation of the coupled continuation model. That initial oracle excludes fees/rent and uses a stated delayed-receipt scenario. The later [phase oracle](buying-behavior-v2-phase-oracle.md) and [joint continuation funding](buying-behavior-v2-continuation-funding.md) model explicit receipt timing, fees and rent for supplied small scenarios. Forecast selection, full ownership/supply behavior, scalable population execution and economic adoption remain unvalidated.


## Exact procurement shortcuts

The compiled D3 funding path reuses its original reference quantity when a queried offer has exactly the reference quote. Its hypothetical book has one offer per material, no switching fee, no incumbent preference and unchanged stock-independent caps. Changing only that offer’s supplier identity cannot change the allocation: within-material supplier tie-breaking cannot arise in this one-offer book. The original sequential cash arithmetic is retained. This argument also covers binding total storage; it does not authorize reusing intentions when prices, resources or other quotes change.

Selection returns a zero allocation directly when every offer satisfies `min(stock, target) < lot`. Zero is then the sole feasible whole-lot basket, so fees, payment and purchased units are zero. Funding/discovery observations are still computed; empty stock is not reinterpreted as zero intended demand. The shortcut requires at least one permitted search node. With a zero-node budget, the original dispatch remains responsible for its explicit general-search failure, including heterogeneous same-price demand caps. No approximate result replaces a search-limit error.

These are optimizations of the existing replenishment comparison, not a change to its target objective or an adoption of industrial willingness to pay. Pre-optimization source, recorded-case exact comparisons and performance evidence are preserved in `stats/buying-implementation/20261012-procurement-shortcuts`.

Verification for these shortcuts: twelve targeted tests pass, including 1,000 reference-funding cases, 400 independent allocation cases, zero-node/heterogeneous-cap boundaries and installed multi-line world comparisons. All 1,926 captured industrial decisions match every result from an independently archived pre-edit implementation. Their 17,949 offers all match their material's reference quote in this startup sample, so the 20.8–26.3% funding/selection microbenchmark improvement must not be generalized to heterogeneous mature quotes.

Three alternating-order whole-world pairs resume the same corrected-policy tick-30 checkpoint and measure ticks 32–41 after warming tick 31. Median full-kernel time falls from 498.25–504.06 ms to 455.96–461.79 ms (8.17–8.49%). Every world array, selected scalar ledger, supplier history, observation array and economic runtime state agrees each tick. A separate fresh full-population 30-tick run, `20261012-industrial-shortcuts-fullpop-137`, passes accounting and reproduces all 211 recorded arrays, checkpoint JSON, schemas/config and invariants of the preserved uninstrumented comparison. Its source identity is `dd25bf37669f11910b963ec55ad64db17f98c3146dc3fc611b9f0c5e72e3befd`.

The original-policy budget remains unmet. In a separate contemporaneous three-pair kernel screen, each policy follows its own trajectory under the same frozen config/seed to tick 30. Corrected/original median ratios are 3.72, 3.77 and 3.78; p95 ratios are 3.75, 3.86 and 3.67. These exceed the plan's relative thresholds. This screen omits recorder/UI/transport and total process memory and cannot pass the overall performance gate. Absolute timings from the two different screens should not be combined as one experiment.

## First-year full-population mechanics screen

Run `20261012-corrected-year-137` covers seed 137, ticks 1–360, with the full configured population: 20 T0, 1,008 T1, 57,960 T2 companies and 1,000,000 Distributors. It compares with the independently preserved `20261012-baseline-137-stage0`. The analysis verifies identical config/catalog identities and opening company accounts, contiguous coverage, and product totals reconciled to independently recorded company earnings/revenue/units. The specification was saved before the run. This historical-seed first-year screen is not generation-scale or held-out validation.

Annual goods sold and posted net earnings (millions of items and dollars respectively; route rows are subgroups of tier totals):

| Tier / route | Companies | Baseline sold, M | Corrected sold, M | Baseline earnings, $M | Corrected earnings, $M |
| --- | ---: | ---: | ---: | ---: | ---: |
| T0 / all | 20 | 2158.608 | 2159.474 | 465.808 | 463.549 |
| T1 / all | 1,008 | 1327.110 | 1326.479 | 809.095 | 916.079 |
| T2 / all | 57,960 | 531.555 | 531.250 | 1294.303 | 1228.156 |
| T1 / c1 | 288 | 526.307 | 526.065 | 253.822 | 278.474 |
| T1 / c2 | 720 | 800.803 | 800.414 | 555.273 | 637.605 |
| T2 / c3 | 38,088 | 387.186 | 386.901 | 856.997 | 809.334 |
| T2 / c4_basic_c3 | 4,032 | 23.189 | 23.223 | 79.115 | 78.838 |
| T2 / c4_compound_pair | 15,840 | 121.180 | 121.125 | 358.191 | 339.983 |

T3 purchased 499,958,599 retail items versus 500,676,193 baseline: 99.8567%. The final 90 ticks retain 99.9218% of baseline retail units. T2 goods-sold totals above also include intermediate sales, so they must not be used as final retail demand. The report does not invent producer earnings for T3 buyers.

No baseline-active product has zero corrected sales over either the full year or ticks 271–360. Every producer has positive annual posted earnings in both runs; this does not establish late-period profitability or permanent product survival. Per-company counts, means, minimum/p10/median/p90/maximum earnings and units, summed-value margins/prices, utilization and fee totals are in `20261012-corrected-year-screen/comparison.json`. Undefined ratios are null.

Manufacturer earnings fall 5.1106%, refinery earnings rise 13.2227%, and extractor earnings fall 0.4851%. These are combined-treatment differences, not causal estimates for an individual mechanism. Switching transfers alone do not explain the earnings changes. No calibration was changed to restore baseline profits.

Conservation passes: maximum company/money/goods tolerance ratios are 0.0096025 / 0.0008856 / 0.0209961, with nonnegative cash/stock and no price-floor/ceiling contacts. The recorded period is complete; the final checkpoint, product/company archives and procurement counters are preserved.

Performance remains unacceptable for adoption. The observed corrected median/p95 are 522.71/552.55 ms versus historical-baseline 124.96/145.12 ms (4.18×/3.81×). These are unpaired recording-run timings, not the final controlled performance protocol, but the corrected median exceeds the 500 ms ceiling. The earlier relative performance failures also remain unresolved. No mature-state memory/UI-overhead gate is established.

The analysis is reproducible with `PYTHONPATH=.pydeps:. /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 stats/buying-implementation/20261012-corrected-year-screen/analyze.py --output <fresh-json-path>`. Its recorded rerun is byte-identical. This advances the corrected comparison evidence; it neither validates the final industrial value model nor authorizes production activation.

## Year-end profiling and exact discovery sort

A warm profile resumes the preserved corrected tick-360 checkpoint, warms tick 361 and measures ticks 362–371. In this profile, manufacturing takes 3.501 of 5.087 seconds (about 69%) and retail 1.446 seconds (about 28%). Bounded samples at ticks 361–362 capture 2,049 industrial decisions with identical economic arrays/observations versus uninstrumented continuation. None has cash insufficient for every offered lot; sampled T2 decisions all buy something, and 951 of 1,025 sampled T2 decisions have differing quotes within at least one input. These are diagnostic samples, not population estimates. Evidence is in `20261012-year-end-profile`.

Discovery now sorts its selected IDs in place by insertion. Production discovery contains at most five alternatives plus the valid incumbent. This replaces a general array sort/copy without changing Floyd draws, RNG roles, eligible books, incumbent inclusion, ascending IDs or subsequent tie-breaking. Explicitly larger diagnostic sample counts remain supported and tested; production scope is unchanged.

`20261012-discovery-sort` archives the entire pre-edit experimental package and final changed source. All 4,500 discovery cases match archived compiled output exactly in both current reference and compiled paths. Eight connected retail/industrial tests pass, plus the strengthened ascending-order test. Cases cover empty/small/large markets, incumbent presence/absence and zero/default/expanded sample counts.

Three alternating-order full-population pairs resume the identical corrected checkpoint, warm tick 361 and measure ticks 362–371. Before/after medians are 547.46/473.01, 540.81/464.03 and 532.66/461.69 ms: 13.60%, 14.20% and 13.33% improvement. Before/after p95 values are 560.61/511.15, 603.90/513.00 and 539.65/469.66 ms. Every one of 168 world arrays, checked scalar/array ledgers, supplier history, retail/industrial observations and runtime economic state matches at every tick.

These short kernel screens bring observed medians below 500 ms; they do not establish the relative-to-original, process-memory, recording/UI or full performance/adoption gates. No price-sensitive industrial model is supplied by this optimization. The first profiling attempt failed because its script was named `profile.py`, shadowing Python's profiling module. Its source/log are preserved; the renamed script completed successfully. No live run or production default changed.

## Scalar funding extraction without changed decisions

The experimental compiled funding path previously reconstructed an entire hypothetical input basket for every distinct supplier quote, although it retained only the queried material's quantity. When total rounded input targets fit available storage, funding visits one reference offer per material in ascending price/reverse-index tie order and subtracts spending sequentially. Only offers before the queried material can affect its funded quantity.

`replenishment_compiled.quoted_quantity` now traverses that unchanged prefix and computes the one required result. A single reference order is reused across quotes. It preserves exact sequential cash subtraction and lot flooring, including floating-point boundaries; it does not replace them with an aggregate affordability test. The storage-binding path retains the general solver. Existing same-quote reuse remains valid. This changes only experimental execution cost, not D3 objectives, D1/D2 rules or industrial value assumptions.

`stats/buying-implementation/20261012-scalar-funding/` preserves the independently archived pre-edit tool package, source hashes, scalar verifier, test logs and paired continuation script/results. Ten thousand seeded cases compare both Python and compiled scalar extraction against the archived full-basket implementation, covering 1–12 materials, lots, quote ties and near-boundary cash. Six funding tests pass in 0.646 seconds, including the existing 1,000 joint-reference and 400 independent-enumeration cases plus explicit scalar tie/cash regressions.

Three alternating-order pairs load the same corrected tick-360 checkpoint, warm tick 361 and measure ticks 362–371:

| Pair | Before median ms | After median ms | Before p95 ms | After p95 ms |
| --- | ---: | ---: | ---: | ---: |
| 1 | 453.24 | 437.44 | 464.49 | 449.77 |
| 2 | 457.46 | 436.12 | 469.70 | 445.90 |
| 3 | 455.94 | 436.75 | 460.70 | 442.00 |

Median improvement is 3.49–4.67%. All 168 world arrays, selected scalar/array ledgers, supplier histories, industrial/retail observations and runtime state match at every compared tick. This is a short kernel benchmark relative to the preceding corrected implementation, not proof of the relative-to-original, memory, recording or UI performance gates. The existing SciPy/NumPy compatibility warning remains nonfatal. Production defaults and live services are unchanged.

## Isolated industrial preference-rule startup control

`stats/buying-implementation/20261012-preference-ablation/` isolates one mechanism over full-population seed-137 ticks 1–30. The accepted whole-demand industrial qualification rule is compared with a diagnostic control in which the last positive delivery qualifies. Retail behavior, discovery, D3 funding/objective, fee rules, production, accounting and pricing are held fixed. The control is not a reproduction of the original production engine and does not reopen D1.

The experimental package differs in exactly two guarded source substitutions: the preference condition in the T1 and T2 compiled purchase callbacks. A source audit verifies every other package file is identical. Matching fresh configurations and opening accounting records are retained. After tick 1, all compared world arrays are identical except 35 `preferredWholesale` entries and 778 `t2Preferred` entries; thus this treatment changes preferences without changing first-tick goods or financial outcomes. Subsequent differences include the endogenous effect of retaining a different incumbent in discovery.

Both treatments pass per-tick cumulative accounting/goods/cash checks and final physical storage validation, with no price guardrail contacts. Industrial whole-demand versus partial-delivery controls produce 178 versus 11,927 true preference changes and 55,689 versus 64,663 first assignments. Neither pays any switching fee in this startup window. Retail units total 3,909,425 versus 3,804,044, a difference of 105,381 (2.77% relative to the partial control).

| Producer route | Companies | Whole-demand sold | Partial-control sold | Whole-demand net earnings | Partial-control net earnings |
| --- | ---: | ---: | ---: | ---: | ---: |
| T0 extraction | 20 | 322,900,000 | 322,900,000 | $80,812,037.38 | $80,811,559.33 |
| T1 C1 | 288 | 51,516,000 | 51,516,000 | $19,576,080.00 | $19,576,080.00 |
| T1 C2 | 720 | 128,780,000 | 128,780,000 | $88,858,200.00 | $88,858,200.00 |
| T2 C3 | 38,088 | 5,619,846 | 5,623,242 | $8,148,776.70 | $8,153,700.90 |
| T2 C4 basic+C3 | 4,032 | 0 | 0 | $0.00 | $0.00 |
| T2 C4 compound pair | 15,840 | 24,504 | 24,604 | $46,557.60 | $46,747.60 |

Sold figures include intermediate and final deliveries; retail totals above count only final Distributor sales. Company counts are the recorded mean over this fixed-population window. Producer totals reconcile against independently accumulated company records. The saved analysis also includes revenue, company earnings percentiles, negative-earner counts, fees and full industrial event totals. No negative-earner count in these 30 startup ticks establishes long-run health: manufacturer median earnings and the entire basic+C3 route's sales are zero in both treatments.

The source archive includes economic code, candidate code, catalog JSON and the executed scripts. Original/variant source hashes, configurations, records and comparison evidence are preserved. Analysis replay is byte-identical; no full simulation replay in an archived standalone environment is claimed. This is a short controlled comparison conditional on corrected mechanics, not attribution of the previously observed annual earnings differences. It leaves mature fee-active windows, separate discovery/fee/partial-eligibility controls, interaction tests, held-out seeds and the master-plan adoption gates open. All launched processes completed; production and live services are unchanged.

## Preference qualification with year-end fees active

The follow-up `stats/buying-implementation/20261012-preference-yearend/` loads the identical corrected-policy tick-360 checkpoint for both rules and records ticks 361–390. The same two guarded industrial preference substitutions are the only policy differences. This is a conditional continuation from a history generated by the accepted rule, not separate equilibrated histories or a stationary comparison. Both configurations, checkpoint hashes and opening company accounts match. At tick 361, all world arrays match except 420 manufacturer preference entries.

Both treatments pass cumulative per-tick company equity, money and goods invariants and final physical storage checks; neither contacts a price guardrail. Maximum company tolerance ratios are 0.0088352/0.0087490 and money ratios 0.0005996/0.0006453 (whole/partial); goods residual is zero. Minimum cash is positive in both. The recorded company period explicitly starts at 361, so no startup/earlier-period earnings are silently included.

| Metric, ticks 361–390 | Whole-demand rule | Partial-delivery control |
| --- | ---: | ---: |
| Final retail units | 47,979,233 | 47,979,654 |
| Industrial preference changes | 4,047 | 5,584 |
| Industrial first assignments | 0 | 0 |
| Industrial fee-bearing orders | 224 | 556 |
| Industrial fees paid | $1,440.01 | $3,584.69 |
| Industrial reference quantity shortfall | 2,596 | 2,424 |
| Industrial stock-limited delivery legs | 11,232 | 3,629 |

Retail differs by 421 units (0.000877% relative to the partial control), opposite in sign and much smaller than the startup result. Whole-demand qualification reduces preference turnover and fee payments here, but retains more stock-limited delivery legs. The latter counts supplier legs, not unique failed company orders; reference shortfall is a replenishment metric, not unmet final consumer demand. These findings are consequences to retain in diagnostics, not reasons to silently change the accepted rule. Industrial fee sums reconcile to posted producer switching expense. Total producer switching income also includes Distributor fees, so it need not equal industrial fee expense.

| Producer route | Companies | Whole sold | Partial sold | Whole net earnings | Partial net earnings |
| --- | ---: | ---: | ---: | ---: | ---: |
| T0 extraction | 20 | 158,222,000 | 158,232,000 | $23,964,425.31 | $23,971,088.64 |
| T1 C1 | 288 | 39,467,928 | 39,467,928 | $29,178,324.37 | $29,171,811.78 |
| T1 C2 | 720 | 59,374,080 | 59,374,080 | $56,777,110.62 | $56,767,415.62 |
| T2 C3 | 38,088 | 36,577,104 | 36,577,525 | $102,966,031.68 | $102,970,518.80 |
| T2 C4 basic+C3 | 4,032 | 2,902,840 | 2,902,840 | $11,272,325.86 | $11,267,470.43 |
| T2 C4 compound pair | 15,840 | 11,402,329 | 11,402,329 | $44,413,992.98 | $44,414,312.54 |

Sold quantities include intermediate deliveries; the separate retail row counts final sales. Company counts are constant across this window. Saved results include company earnings percentiles, revenue, fees and full event totals. No producer has negative period earnings in either treatment, but this 30-tick result does not establish annual or generation-scale health.

Source archives, exact mutation audit, checkpoint/configuration identities, complete observation windows and byte-identical analysis replay are verified. The archive includes the executed alternative package; no standalone full-simulation replay is claimed. All launched processes completed. This addresses the earlier absence of active fees in the preference screen, while leaving other-mechanism attribution, interactions, multiple seeds and long-run validation open. Production defaults and live services remain unchanged.
