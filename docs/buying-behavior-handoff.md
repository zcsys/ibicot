# Buying behavior implementation handoff

## Adopted as the production default (Stage 8 complete)

The user adopted the price-sensitive fill-to-brim rule as the production default on 2026-10-12, with **no calibration retune** (the T1 margin is accepted as-is). Stage 8 rollout is complete: artifact `db131cc`, service version 0.1.8. Stage 7's preregistered multi-seed validation is deferred by the adoption decision; the single-seed 1-generation run (98.6% T2 fulfillment) is the supporting observation.

## 1-generation run: 98.6% T2 fulfillment — the ~40% was a startup transient

A live app run (57,960 T2 firms, C3/C4, default seed/config) auto-paused at tick 7,200. The earlier ~40% T2 fulfillment (flagged from the 361-tick benchmark) was only the first-year ramp-up: the fill rate reaches 93% by year 4 and settles at ~98% through year 20 (**98.6%** at tick 7,200). All 123 products are profitable (0 negative-earners); T2 cash grows 17.97B → 57.29B (3.2×); distributors are 99.99% fulfilled. Tier gross margins: T0 47.5%, T1 54.4%, T2 21.0% (C3 20.6%, C4 21.7%). The one remaining calibration lever: T1 prices drifted 3.05 → 7.53 vs a 2.75 reference (54% T1 margin). Report: `stats/buying-implementation/20261012-price-sensitive-buying/generation-report.md`.

## Population benchmark and economic observation of the price-sensitive rule

Full-population isolated benchmark (57,960 T2, C3/C4, 361 ticks): step median **137 ms/tick** (p95 160 ms), so the closed-form rule adds negligible overhead. Economic snapshot at tick 361: T0 sold 5.27M (net 800k), T1 sold 3.29M (net 2.02M), T2 sold 1.70M vs demand 4.25M (**unmet 2.55M**), T2 net 5.72M, T2 intermediate sold 97,773, all tiers profitable, no negatives, money/goods reconcile. Evidence: `stats/buying-implementation/20261012-price-sensitive-buying/`.

Calibration note: at price ≈ reference the demand curve buys half of fill-to-brim, so the T2 firms hold ~half their input slots and fulfill ~40% of distributor demand. That is the direct consequence of "halving price = reference cost"; a higher halving price would soften this. Flagged for the user rather than silently retuned.

## Price-sensitive fill-to-brim industrial buying (user-directed)

The user resolved the open D3–D6 model decisions with a simpler rule: latent demand = "fill to brim" (the storage slot), quantity = the Tier 3 price-response curve with a heuristically chosen halving price, and no elaborate continuation planner for the adopted model. Implementation, mirrored in the reference and compiled kernels:

- `economy/core/model.py`: `input_reference_cost(material, cfg)` — the halving price (canon "V = unit cost"): `t1MaterialCost` for basic elements, `refinery_unit_cost` for refinery products, `initial_tier2_cost` for T2 intermediates.
- `economy/kernel/tick.py` (`transfer_tier2_input`) and `economy/kernel/numba.py` (`_operate_tier2_nb` + cached `input_reference_arrays`): `buy_request = min(demand_at_price(slot, halving, quote, 2.0), shortage)`. Elasticity fixed at 2 (canon η = 2); the result is capped by the actual slot shortage so a nearly-full firm never overbuys.

D3–D6 resolution: D3 target = fill-to-brim; D4 value = reference cost (no forecast); D5 information = quote + own slot/reference; D6 solver = none required (closed form). Verification: kernel determinism/conservation pass; reference/compiled byte-equality holds; three golden tests updated (24 → 6) and a new `tests/py/test_buying_price_sensitive.py` checks the price-response direction. Full discovery pending at the time of writing.

## Recent optimizations are case-specific; synthetic closing-bound screen unchanged

Re-ran the 16-case connected screen (prefix-bound spec: `closing=True`, 4,000/16,000 budgets, `prunePrefix`/`pruneContinuation`, shared-first 256): **12/16 exact**, with cases 7/13/14/15 still hitting the closing box-node limit. This confirms the recent wins (funded-cap pruning, semantic dedup, symmetry break) target the captured diagnostic's specific structure — uniform prices, no incumbent, funded-demand-bound — and do not move the closing-bound bottleneck of the heterogeneous-price synthetic screen (whose historical result under the later proof-memo knobs is 13/16). The captured diagnostic is 8/8, but closing-bound scaling for heterogeneous multi-period cases remains a separate research-level task.

## Symmetry break completes the captured diagnostic (8/8)

The actual purchase now applies a gated symmetry break: when a decision has no incumbent for any material, no later purchase phase, and each material's first offer holds at least its maximum funded demand, the action frame caps every non-first offer of a `(material, price, lot)` group to zero (`AllocationFrame` `canonical=True`). Under that condition the per-offer split is value-irrelevant (no current fee, the incumbent update has no future consequence, and terminal value is incumbent-independent), so enumerating only the front-loaded split is exact.

All eight captured diagnostics now complete exactly (0 limits); case 0/full-clearance returns value 46.4. Verification: full `test_buying_v2*.py` discovery passes 536 tests, including the 24 seeded comparisons and the differential funding check. Evidence: `stats/buying-implementation/20261012-captured-symmetry-break/` (318 source hashes, 8/8 fingerprints, tests.log).

This is a solver-screen milestone, not project completion: the captured diagnostic is a small fixture, and the master plan's forecast/model decisions, full integration, population performance, economic validation and rollout remain open.

## Semantic funding-query dedup completes case 2 (7/8)

Funding queries are now deduplicated by a supplier- and order-independent identity — the sorted `(material, price, lot)` of each collapsed offer — computed by `continuation_query.query_key` and used by `QueryAnswers.request` (now keyed by a hashable tuple instead of offer indices). Independent-snapshot supply makes the hypothetical value depend only on those fields, so the dedup is exact; persistent arrivals keep the unique offer-subset key. For the captured uniform-price states all 11 funding queries collapse to one.

Completion rises 6/8 → **7/8**: case 2/full-clearance (no stock at all) completes exactly (value 0). Case 0/full-clearance now passes funding (`fundingQueries=1`) and fails in the actual purchase, which enumerates the symmetric per-offer compositions described in the prior entry. Verification: full `test_buying_v2*.py` discovery passes 536 tests; the two `prepare`/`QueryAnswers.request` contract tests were updated to the new hashable-key contract. Evidence: `stats/buying-implementation/20261012-captured-semantic-dedup-final/`.

## Full-clearance limits diagnosed: symmetric composition, not bound slack

The two remaining limits (cases 0/2 full-clearance) fail inside a per-offer funding query (`fundingQueries=4/6`). Both captured states have **no incumbent for any material** (all incumbents −1), and the diagnostic calendar has no later purchase phase, so the fee is zero and the first-assignment incumbent update has no value consequence. The actual purchase value is therefore symmetric across per-offer splits, and the cost-aware prefix bound (which relaxes the current-order fee) cannot distinguish equivalent compositions — it would enumerate on the order of millions of equivalent material-0 × material-4 splits. Collapsing those offers would be safe only under this no-incumbent/no-future-purchase condition, not in general (a positive fee or a later purchase breaks the symmetry). The solver stands at 6/8; the remaining two cases need either a fee-aware bound or an explicit symmetry break gated on the no-incumbent condition.

Full discovery passes **663 tests in 416.084s** after the funded-cap pruning (log preserved in the funded-cap evidence directory).

## Funded-cap pruning completes the zero-sales cases (6/8)

The action frame now bounds each material's total purchase by its maximum funded demand (`AllocationFrame.max_funded`, enforced in `continuation_actions.advance`). The ledger already rejects allocations whose per-material total exceeds the funded cap, so pruning those prefixes earlier is behavior-preserving; the bound is tight for uniform funded demands and conservative otherwise, and a zero funded demand admits only the empty allocation.

Completion rises from 4/8 to **6/8**: cases 1/zero-sales and 3/zero-sales now complete exactly (values −16 and −18, the forced-production conversion cost of buying nothing). The two remaining limits are the full-clearance cases 0/2, whose positive funded demand keeps the per-offer composition structure (which cannot be collapsed safely because fees and preferences depend on the split).

Verification: `test_buying_v2_continuation_actions`, `test_buying_v2_range_pruning` (24 seeded complete-result comparisons) and `test_buying_v2_continuation_differential` pass; full `test_buying_v2*.py` discovery passes **536 tests in 450.944s**. Evidence and source snapshot: `stats/buying-implementation/20261012-captured-funded-cap/` (318 source hashes, 8 fingerprints, tests.log).

## Scope re-verified against the explicit base; audit script's HEAD reference is stale

Re-ran the scope checks against the documented base commit `572e586fae665e10edd9ea5ea459d5f165f1dfd4`. All four retained phase bodies match after removing the purchase/observer hooks (`plan_and_buy_inputs`, `_operate_tier2_phase`, `_plan_and_buy_inputs_nb`, `_operate_tier2_nb`); no protected tracked path (`economy/core`, `catalogs`, runtime/scheduler/recording/aggregates/service, `web/catalog.js`, `web/midbridge-catalog.js`) changed; loaded defaults remain 57,960 T2 companies / 36 C3 + 69 C4 / C3–C4 phases only. The offer-collapse is the only source change beyond these.

The preserved `audit_scope.py` scripts use `git show HEAD:` for the pre-modification phase bodies. HEAD has since advanced to the `gpt work` commit (`1b1b87b`), which already contains the purchase/observer hooks, so re-running those scripts as-is now spuriously fails the `_operate_tier2_phase` comparison. This is a reproducibility artifact, not a scope violation; a future re-run must reference `572e586` explicitly, as done here.

## Range-proof tightening is structurally blocked; production scope re-verified

Instrumented the full-clearance per-offer query (case 0, after the offer collapse) to confirm the remaining slack precisely: the range proof's free-input ceiling is 216.64 and tail-prunes only 105 of 5,365 prefixes, while the cost-aware prefix bound (actual prices) prunes 5,061 of 5,260 and is already the effective pruner. The range proof cannot be tightened by a small change. Its tail-prune is valid only because `gross_return − paid` (free inputs) is monotone non-increasing in the scanned coordinate; an actual-price ceiling either double-counts the prefix's `paid` deduction (computed from the decision-point state), double-counts the last coordinate (parent-conditioned with full `paid`, since the coordinate is also priced in `line_envelope`), or becomes constant in the coordinate (parent-only `paid`), which would prune the optimal completion. This monotonicity-versus-input-cost tension is why parent-conditioning and resource caching (both free-input) failed to improve completion. Empirically confirmed: switching the ceiling to `free_inputs=False` makes `test_buying_v2_range_pruning` fail 2 of the 24 seeded complete-result comparisons (the range proof prunes an optimal completion), so the free-input ceiling is the correct monotone structure despite its slack. A genuinely tighter tail certificate needs a different structure, not a tweak to `line_envelope` or `continuation_range.py`.

Production scope re-verified after the offer collapse: all `economy/` files and the four modified production files (`economy/kernel/tick.py`, `numba.py`, `input_market.py`, `economy/server/persistence.py`) remain byte-identical to the retained conversion-range snapshot; only the three `tools/buying_v2/` funding-query files changed for the collapse.

## Offer-collapse optimization retained after fixing the dedup key

The offer-collapse optimization is now correct and retained in the working tree. The earlier dedup-key defect — returning `np.arange(count)` as `selected`, which collided across queries in `QueryAnswers.request` — is fixed by returning the original offer subset and validating the allocation length against the collapsed `iv[0]` in both `funding_purchase` paths. It applies to all continuation-v2 funding queries under independent-snapshot supply (persistent arrivals keep the original enumeration). Verification: full `test_buying_v2*.py` discovery passes **536 tests in 455.573s**, including the 24 seeded oracle comparisons and the seeded differential funding/policy/account check. Evidence and source snapshot: `stats/buying-implementation/20261012-captured-offer-collapse/` (318 source hashes, specification, 8 fingerprints).

Completion remains 4/8, but the zero-sales bottleneck moves past funding: cases 1/3 now finish all 13 funding queries (`fundingQueries=13`) and fail later in the actual purchase traversal (12 offers, depth 11), while full-clearance cases 0/2 still exhaust work inside a collapsed per-offer query (`fundingQueries=4/6`; their `held=0` keeps per-material caps at ~2,833/2,000, so the 2-offer query space is ~8M and remains bound-slack-bound). Solved-case prefix work falls ~2.6–2.8× (0/zero-sales 156→60, 1/full-clearance 216→76, 2/zero-sales 150→54, 3/full-clearance 216→76). This is a behavior-preserving search-work reduction, not a completion pass.

Remaining completion levers are unchanged: the actual purchase and the large-cap per-offer queries still carry the forced-production and free-input bound slack. Collapsing the actual purchase frame is unsafe because fees and preferences depend on the per-offer split under a positive funded demand. The next step remains tightening `continuation_bound.line_envelope` to lower-bound the forced gate-limited production conversion cost.

## Collapse experiment rejected: dedup key blocks it, and bound slack stays the lever

Attempted to collapse same-(material, price, lot) offers inside the continuation-v2 funding queries to remove the redundant per-offer composition enumeration. The joint-query-only collapse is correct (24 seeded comparisons plus native/tie tests pass) but leaves completion at 4/8 and only trims work in solved cases. Extending it to the per-offer queries broke the seeded differential comparison: the collapsed payload returned `np.arange(count)` as `selected`, and `QueryAnswers.request` keys its dedup on that offer-set tuple, so distinct joint/per-offer queries with the same collapsed shape shared one answer and produced wrong funding vectors. The source was restored byte-for-byte from the retained conversion-range snapshot (318 hashes re-verified).

The attempt still sharpens the diagnosis. Collapsing the joint query from 10→2 offers leaves the full-clearance limit cases essentially unchanged (case 0: 5,369→5,372 prefixes), confirming they are bound-slack-bound, not action-space-bound. The zero-sales cases are partly composition-bound (0/zero-sales falls to ~20 prefixes under the buggy extended collapse) but still cannot certify optimality because of the forced-production slack. The completion lever remains `continuation_bound.line_envelope`: it must lower-bound the forced gate-limited production conversion cost. A dedup-safe collapse would additionally need to key `QueryAnswers` on the original offer subset rather than the collapsed representative indices.

## Precise limit-case diagnosis: bound slack, not range-proof leverage

Instrumented the retained conversion-range search on all four limit cases and measured the range-proof values directly. The joint all-quotes funding query is confirmed as the failure point (`fundingQueries=1`, `activeFrames=3`). Two distinct slack mechanisms explain why the search cannot certify optimality:

- **zero-sales cases (1/3):** best-so-far `prior ≈ −16`, range ceiling `≈ 0`. The −16 is the conversion cost of gate-limited production from already-held inputs (`held=2801`/`1976` already exceeds `max_batches`); the envelope reports ≈0 because `line_envelope` caps realized production at `min(demand, capacity)` = 0 under zero demand. The bound is valid but loose by exactly that forced-production conversion cost.
- **full-clearance cases (0/2):** `prior = 0`, range ceiling `≈ 216.64`/`278.64` (free-input gross return). Because the range ceiling prices suffix inputs at zero, it only prunes when the prefix goods payment exceeds ~216–278, so it prunes just 87/147 of ~5,359 range checks (case 0/2) and is nearly inert; the cost-aware prefix bound performs ~98% of the pruning.

Completion was 4/8 both before and after the range proof (the range proof only reduced work in already-completed cases), so the range proof is not the completion lever. The remaining slack is in the cost-aware prefix bound's `line_envelope`: it optimizes production as demand-limited (and assumes omniscient production), while the actual `purchase` event produces gate-limited regardless of future demand. Next work: tighten `line_envelope` to lower-bound the forced gate-limited production conversion cost (closes zero-sales) and to price suffix inputs at their actual costs (closes full-clearance). The earlier "collapse same-price same-material offers inside the joint query" idea remains a separate, orthogonal lever with the tie-break caveats already noted. No source, test, parameter, or live run was changed by this diagnosis.

## Archived replay completed; four-case bottleneck analyzed

The previously missing archived execution replay of the rejected resource-keyed range-cache candidate is now complete. Running the candidate archived source from `/tmp` reproduces all eight captured result/failure fingerprints exactly (4 exact, 4 limit), and all 318 archived source hashes match. Evidence: `stats/buying-implementation/20261012-captured-resource-cache/archived-replay-verification.json`, `replay/`, `replay.log`. No working-tree code changed and no new test or simulation was run. The rejection decision is unchanged; this replay only authenticates the recorded candidate results, matching the standard used for retained milestones.

The four unresolved captured cases were analyzed directly. All four exhaust the 16,000 combined prefix/bound-work budget inside the **first** funding query (the joint all-quotes query, ordinal 0): `fundingQueries=1` and the failure reason is `action prefix work limit`. Bound work dominates (about 9,700–10,600 of 16,000), roughly two units per visited prefix (range proof plus prefix bound for a single-scenario group). The joint query's result is recorded metadata only: `encode_answers`/`resolve_answers` derive the actual funded `demands` from the per-offer queries, while `jointQuantities`/`jointGoods` (and never the joint conditional value) are stored in the funding record and do not influence the purchase, fees, preferences, or terminal value. The per-offer queries never run in these cases because the joint query fails first. The loose frame `remaining` aggregate (sum of per-offer caps) is not the bottleneck: the compiled `advance` native `inventory` check already enforces the tight per-material slot bound.

A candidate next step is to collapse same-price same-material offers inside the joint query only. All four captured cases have uniform within-material prices, so the hypothetical continuation depends only on per-material aggregate quantity and cost (incumbents are held and current fees are removed inside the query). That would reduce the joint query from 10–12 offers to 2 in these cases. It is not yet implemented: it must preserve lexicographic tie-breaking and the seeded oracle funding comparisons, and must not change per-offer-query or actual-selection semantics. The retained global conversion-aware range proof remains the current starting point.

## Latest state — resource-cache candidate rejected and restored

The resource-keyed range cache is no longer in the working tree. It completed the same 4/8 captured cases as the retained implementation and increased combined prefix/proof work for every completed case (244→308, 338→432, 231→290, 338→432). This evidence does not justify adopting its extra complexity. It is not proof that resource caching can never help another workload.

Only `tools/buying_v2/continuation_range.py` and `tests/py/test_buying_v2_range_pruning.py` were restored from `stats/buying-implementation/20261012-captured-conversion-range/source/`, after checking that both current files still matched the preserved candidate. All 318 current source hashes now match that previously verified retained snapshot. Candidate source, tests and captured results remain under `stats/buying-implementation/20261012-captured-resource-cache/`; `restoration.json` records restoration and `static-handoff-verification.json` records the comparison. No new tests or simulations were run; candidate archived execution replay was not performed. Earlier entries saying adoption is pending or the candidate remains current are historical and superseded.

Next implementation work must improve exact search on the four unresolved captured cases without changing funding semantics, supplier/line scope, or outside economic rules. The retained global conversion-aware range proof is the starting point. A native-resource interval/box proof is a possible direction, not an adopted design; existing integer closing-allocation guards cannot simply be removed. Full master-plan integration, forecast decisions, performance and economic gates remain unfinished. The continuation prompt's immediate-pending-work paragraph is superseded by this entry.


## Handoff verification addendum — existing artifacts inspected

Static comparison is now recorded in `stats/buying-implementation/20261012-captured-resource-cache/static-handoff-verification.json`. All 318 archived and current source hashes match the candidate manifest. All four completed public results match the retained conversion-range baseline exactly after excluding diagnostics. Completion remains 4/8. Combined prefix/proof work for completed cases increases 244→308, 338→432, 231→290, and 338→432; all four incomplete cases still exhaust 16,000 work units. More cache hits or visited allocations do not establish faster convergence. No new simulation or test was run. Archived execution replay and adoption/rejection remain pending; the candidate is still in the working tree. This addendum supersedes the prior pending status for static hash/result comparison only.


## Latest handoff — 2026-10-12, resource-cache candidate pending review

The user requested a handoff because their token quota is nearly exhausted. No further experiments were started. This entry supersedes earlier statements that the working tree exactly matches the retained conversion-range snapshot.

Current unaccepted candidate changes `tools/buying_v2/continuation_range.py` and `tests/py/test_buying_v2_range_pruning.py`: a bounded 128-entry LRU caches parent-conditioned relaxed ceilings by `(depth, tuple(held))`, with mandatory payments deducted outside the cache. It preserves native floating holdings; cache capacity bounds entries, not total memory. Sixteen targeted tests passed in 60.525s (including 24 seeded complete-result comparisons); log: `stats/buying-implementation/20261012-resource-range-cache/tests.log`.

Captured experiment completed successfully as a process, but only 4/8 solver cases completed exactly; the other four reached limits. Exact cases remain 0/zero-sales, 1/full-clearance, 2/zero-sales, 3/full-clearance. Evidence and source snapshot: `stats/buying-implementation/20261012-captured-resource-cache/`; sibling `20261012-captured-resource-cache-run.log`. Archived replay, source-hash reconciliation, full public-result comparison, and adoption/rejection are still pending. Session 98007 exited with code 0; no known task processes remain running.

Next: inspect this candidate against the last verified retained snapshot `stats/buying-implementation/20261012-captured-conversion-range/source/`. Decide on evidence whether to retain it; do not infer improvement from test success or process exit. Preserve rejected evidence. Restore only the two candidate files if rejecting, never reset the entire working tree. Previous parent-conditioned candidate was rejected for added proof work; this candidate attempts resource-key reuse.

All purchasing-only scope constraints and accepted D1/D2 decisions remain binding. Full implementation is unfinished: production defaults have not adopted the experimental planner, and forecast decisions, population performance, integration, economic validation and rollout remain open. Preserve all uncommitted/untracked files and ignored experiment evidence when transferring to another AI.


Updated 2026-10-12. The active user objective is **implement the master plan in full**. It is unfinished. The user requested a durable handoff so another AI can continue if the current AI reaches its token limit. This request does not pause the work. Production purchasing defaults remain unchanged; no live rollout has occurred.

## Purchasing scope boundary

The user explicitly confirmed on 2026-10-12 that this buying-behavior work must not change outside parameters or logic. Preserve population, active recipes/complexities, capacities, sell-side price parameters and pricing rules, production rules and historical-cost gates, storage, rent, demand settings, execution order and other non-purchasing mechanics. Different outcomes caused by changed purchases are not permission to alter those rules. Isolated synthetic fixtures may vary inputs for tests; they do not change production defaults. Any candidate requiring an outside amendment must be reported as incompatible with the current authorized scope, not silently implemented or treated as a pending part of an approved model change. Purchasing observations, accounting of actual purchases and policy-compatible persistence must retain existing non-purchasing behavior.

## Current audit and continuation status

The implementation/documentation audit was refreshed after native Resident support. Evidence: `stats/buying-implementation/20261012-scope-docs-final-audit/`. Loaded backend and browser defaults remain 57,960 manufacturers and 105 C3/C4 products. Protected model/config/catalog/runtime files remain unchanged from the base commit; all four retained phase bodies still match after removal of explicit purchasing/observer hooks. The four modified production files and three contract/world test modules are byte-identical to the prior 14-test scope audit. No new test run or live-process inspection is claimed here.

Current support: native fractional prescribed execution works in Resident/ArenaResident, with explicit native terminal curves. Fractional supplied-demand connected search and exhaustive event-tree search now pass independent comparisons. Native endogenous funding is now enabled with arithmetic-exact query caps and independent oracle comparisons. Raw fractional resource projection now preserves slots/holdings and matches actual phase/book checks. Captured-state planning diagnostics now expose first-query allocation limits in all eight tested cases. Optional range proofs plus native cost-aware envelopes now complete four of eight captured diagnostics; native prefix feasibility now prunes safely with saved inventory; next address interval-level economic bounds and cheaper evaluations; unsupported non-whole committed sale movements still fail explicitly. The synthetic solver screen remains 13/16, and even 16/16 would not complete the model, integration, population-performance, economic and rollout gates.

The milestone sections below preserve checkpoint evidence. Their “next” statements, unsupported-feature statements, test totals and process status describe that checkpoint only; use this current status and the newest milestone for continuation. Historical notes do not override implemented support or authorize outside economic changes.

## Current status after rejected parent-conditioning experiment

The parent-conditioned ceiling passed correctness checks but did not improve the captured 4/8 completion count and increased work in already completed cases. It is preserved in `stats/buying-implementation/20261012-captured-parent-range/source/` and is **not adopted**. The working proof and test module were restored to the preceding conversion-range snapshot; all 318 source hashes match. All eight candidate fingerprints match archived replay from `/tmp`; completed public results are unchanged, and all commands exited. Next investigate bounded reuse based on actual relaxed-resource dependencies before retrying parent conditioning. No production parameters/rules changed; the full goal remains unfinished.

## Retained conversion-aware range result

The optional range ceiling now prices eligible inputs at zero internally while retaining relaxed conversion expense, so mandatory prefix goods payments can safely be deducted once. Twenty-one targeted tests pass, including all 24 seeded complete-result comparisons. Captured completion remains four of eight, but both completed full-clearance cases fall to 338 combined prefix/bound work units. Evidence: `stats/buying-implementation/20261012-captured-conversion-range/` and `20261012-conversion-range/`; all eight archived fingerprints and 318 source hashes verify, all four prior completed public results are unchanged, and all commands exited. Next condition range ceilings on already fixed earlier offers; the current decision-wide relaxation can keep unavailable inputs artificially available. Preserve arithmetic, payment accounting, full scope and conservative fallback. Production rules/defaults remain unchanged.

## Historical milestone: native cost-envelope result

Exact rational resource breakpoints now enable the existing optional cost-aware bound for fractional states. Twenty targeted tests pass, including native exhaustive cases and all 24 seeded range-pruning comparisons. Captured completion rises to four of eight at unchanged budgets; the new case 1/full-clearance returns 216.64000000001397. All four completed states/values replay through the independent ledger. Evidence: `stats/buying-implementation/20261012-captured-native-cost/` and `20261012-native-cost-envelope/`; all eight archived fingerprints and 318 source hashes verify, prior completed public results are unchanged, and all commands exited. Next strengthen interval/box proofs for the four remaining cases without restricting purchases to immediate production needs or altering historical-cost gates. Production rules/defaults remain unchanged.

## Historical milestone: optional range-proof result

The new opt-in `prune_ranges=True` proves entire coordinate tails inferior using a cached gross-return ceiling minus minimum mandatory goods payment. Actual profit need not be monotone. Fifteen targeted tests pass, including all 24 seeded complete-result comparisons. At unchanged captured-case budgets, three of eight diagnostics now complete. All completed states/values replay through the independent ledger; the two new zero-sale cases also pass a global no-purchase certificate. Evidence: `stats/buying-implementation/20261012-captured-range-proof/` and `20261012-range-proof/`; all eight fingerprints match archived replay from `/tmp`, all 318 source hashes verify, and all commands exited. Next strengthen production/cost-aware bounds for the five remaining cases without reducing scope or returning approximations. Production rules/defaults remain unchanged.

## Historical milestone: native action feasibility

Native action traversal now checks ordered additions against input slots and restores saved floating inventory on backtracking. Fifteen targeted tests (including 50 independent seeded grids) and nine archived tests pass. Evidence: `stats/buying-implementation/20261012-native-action-slots/` and `20261012-captured-native-slots/`; all 316 source hashes verify. Captured completion remains one of eight; case 1's allocations fall from 4,000 to 239 but it still hits the work limit. The completed public result is unchanged. All commands exited. Next address interval-level economic proofs and cheaper bound evaluation without assuming value monotonicity. Production rules/parameters remain unchanged.

## Historical milestone: native-bound scaling result

A conservative native-resource continuation envelope now supports optional prefix pruning with explicit native terminal curves. At unchanged budgets it completes one of eight captured diagnostics; seven still fail. Twenty-four targeted tests and ten archived tests pass, and the completed policy's full state/value replay through the independent ledger. Evidence: `stats/buying-implementation/20261012-captured-native-bound/`; all 315 final source hashes verify and all commands exited. This is not population readiness or a separate exhaustive proof for the completed captured case. Next reduce individual prefix checks through exact native feasibility and justified interval proofs; do not assume one rejected quantity proves the rest. Production rules/defaults remain unchanged.

## Historical milestone: captured-state planning diagnostic

Four unchanged captured states (minimum/maximum offer grids in C3/C4) were tested under explicit zero-sales/full-clearance diagnostic scenarios. All eight hit 4,000 allocations during the first endogenous funding query; no policy or approximate value returned. Even the state with an actual stock grid of one hits the query limit, because hypothetical funding relaxes stock. Evidence: `stats/buying-implementation/20261012-captured-search/`; all eight failure payloads match archived replay from `/tmp`, and 314 source hashes verify. All milestone commands exited. The newest progress entry and [search geometry report](buying-behavior-recorded-search-geometry.md) give assumptions, commands and replay verification. Next improve exact native-resource funding search using these failures, preserving full supplier/line scope and funding semantics. Production rules and parameters remain unchanged.

## Historical milestone: native captured-state projection

Fractional holdings, finished/opening book stock and input slots now project without truncation. Whole-unit offers retain fractional residue in the raw record. Actual phase/book tests exposed and fixed research-only zero-sale basis recalculation; production accounting is unchanged. Evidence: `stats/buying-implementation/20261012-native-projection/`: 35 tests pass in 2.075 seconds and all 1,035 preserved captures reconcile, including exact native resources. Eight archived projection tests pass from `/tmp`, and all 312 source hashes match. No milestone process remains active. Next exercise representative captured-state planning with explicit diagnostic scenarios and preserve scaling failures; no forecast/terminal calibration is adopted.

## Historical milestone: native endogenous funding

Own-quote caps now search the native-addition predicate, independently implemented in compiled queries and the Python oracle. Native continuation funding is enabled in connected search and exhaustive event-tree search. Evidence: `stats/buying-implementation/20261012-native-endogenous-search/`; 35 targeted tests pass in 42.599 seconds and 10 archived tests from `/tmp` pass in 25.985 seconds; all 311 source hashes match. No milestone process remains active. Production kernels and outside economic parameters are unchanged. Fractional raw projection is the next integration step; full forecast/integration/performance/economic gates remain open.

## Historical milestone: native supplied-demand search

Native allocation frames enumerate whole-lot stock ranges, leaving slot feasibility to the ledger; they no longer truncate a feasible purchase through subtraction rounding. Both connected storage modes and the independent exhaustive oracle support native fractional resources with supplied funding. Integer-only proofs remain conservative. Evidence: `stats/buying-implementation/20261012-native-supplied-search/`; 21 regressions pass, followed by five expanded native tests and five archived-source tests from `/tmp`; all 310 source hashes verify. See the progress entry for archive replay and exact limitations. No production kernel, parameter or live policy changed.

## Historical milestone: native compiled resident execution

Schema 4 now preserves native float inventory/slots in Resident and ArenaResident; opening-book observation schema 3 stores fractional quantities without truncation. Prescribed transactions, production, whole sales, rent, tick end, own-quote queries, terminal values and atomic failure match the reference ledger. Evidence: `stats/buying-implementation/20261012-native-resident/`: two overlapping 17-test sets pass, plus 4 archived tests from `/tmp`; all 309 source hashes verify. No process remains active, and production rules/defaults remain unchanged.

Native supplied-demand action traversal is now verified by the milestone above. Endogenous fractional funding and the raw projector **remain guarded** pending the own-quote cap audit. The older per-event Executor rejects schema 4; use Resident for verified native prescribed execution. Check subtraction-versus-addition rounding at slot boundaries before loosening guards. Full model/integration/economic/performance gates are still open.

## Historical milestone: compiled native terminal schema

Schema 3 now encodes explicit native quantity curves alongside legacy integer tables, with compiled interpolation and resident/arena terminal integration. Frozen overhead remains supported. Independent oracle and connected results agree; optional integer bounds decline native curves safely. Evidence: `stats/buying-implementation/20261012-native-terminal-schema/`: initial 16 tests, expanded 8 tests (overlapping), and 5 archived tests from `/tmp` all pass; all 308 source hashes verify. No process remains active. Production rules/defaults are unchanged; no terminal calibration was adopted.

Next integrate native float state, purchase/settlement execution, observation/history and action/funding bounds. **Fractional compiled state and raw projection remain guarded** until that integration is complete. Older notes rejecting native terminal curves are superseded; fractional state rejection remains intentional.

## Historical milestone: native reference ledger

The independent ledger now supports fractional holdings/finished goods/input slots while preserving whole purchases/sales and native arithmetic. Explicit `LinearQuantityValue` provides caller-declared native terminal curves without extrapolation; integer tables reject fractional lookups. Evidence: `stats/buying-implementation/20261012-native-reference-ledger/`: 29 regressions passed, then 6 tests after adding guards. No process remains active; source/log copies are preserved, no archived replay claimed.

At this reference-only checkpoint, compiled state/calendar and event-tree search explicitly rejected fractions; integer-only bounds return unavailable/infinity and closing search declines them. The projector remains guarded. Next implement native compiled state, valuation encoding, funding/traversal and observations/history before lifting those guards. No economic parameters or production kernels changed, and no terminal model was adopted.

## Historical milestone: native fractional arithmetic evidence

`native_inventory.py` adds a native-unit float64 production primitive for eventual fractional planner integration. Four tests pass in 0.655 seconds, including exact real-phase comparison at three fractions and baseline checkpoint preservation. Subunit scaling and fixed-residue encoding both have preserved counterexamples; do not use them as exact shortcuts. Evidence: `stats/buying-implementation/20261012-native-fractional-production/`. No process remains active; no production code/config changed; no archived replay is claimed.

Fractional connected-planner support is **not complete**. Next define and implement native-float state plus explicit terminal-value lookup domains, then propagate them through funding, serialization, observations and bounds. The raw projector still rejects fractional records deliberately until that integration exists. All broader forecast/integration/economic/performance gates remain open.

## Historical milestone: above-slot finished-stock support

The connected phase ledger, compiled replay and projection now preserve existing finished goods above a reallocated output slot, while retaining physical storage limits and the original slot for future production. Ordinary/shared bounds and the closing adapter include this stock safely. Evidence: `stats/buying-implementation/20261012-overcap-finished/`: 46 regressions pass in 46.539 seconds, plus one actual-phase comparison. Initial compiled rejection failures are preserved; no process remains active. Production rules/defaults are unchanged. No archived replay is claimed.

Next address fractional holdings (still explicitly unsupported), then projected-state scaling and unresolved forecast/integration/economic gates. Prior handoff notes calling over-cap stock unsupported are historical and superseded by this milestone.

## Historical milestone: captured-state projection

`prepurchase_projection.py` now maps raw records into Company/State/Purchase, preserving installed order, all materials, frozen overhead, opening books and deferred sales/fees. Explicit future settlement adds committed sales once and limits additional sales to remaining opening stock. Nine tests pass in 6.511 seconds, including actual production and real/reference/compiled settlement comparisons. All 1,035 saved captures project with cash/equity/space/identity checks and verified input hashes. Evidence: `stats/buying-implementation/20261012-prepurchase-projection/`; no archived replay is claimed. No process is active.

Next address explicitly unsupported fractional holdings and over-cap finished inventory in the planner; do not round goods or enlarge slots to hide these gaps. Then perform projected-state scaling with clearly labeled diagnostic scenarios. Adopted forecasts/terminal values and wider integration/economic/performance gates remain unresolved. Production rules/defaults remain unchanged.

## Historical milestone: compiled frozen-overhead support

The previous compiled rejection is superseded: schema 2 now carries explicit frozen phase overhead through calendar decoding, own-quote queries, production, observations/history and scenario grouping. Legacy calendars remain schema 1. Complete oracle and optimized-path comparisons pass. Evidence: `stats/buying-implementation/20261012-frozen-overhead-compiled/`: 30 tests in 44.863 seconds; 8 archived tests run from `/tmp` in 38.542 seconds; all 300 source hashes verify. No process remains active, and no production defaults/rules changed. See the final progress entry and compiled-plan wire contract.

Next finish raw-record-to-planner state projection and pending seller settlement handling. Forecast/horizon/terminal choices remain unresolved, and the full master plan remains incomplete.

## Historical reference-only frozen-overhead correction

The reference planner now accepts optional `Purchase.frozen_overhead`, preserving the real T2 phase-entry snapshot instead of recomputing it at buyer entry. Closing basket comparisons and ledger/calendar regressions pass: 33 tests in 17.383 seconds. Evidence: `stats/buying-implementation/20261012-frozen-overhead-reference/`. No production rule changed. The compiled calendar **explicitly rejects** this new field until its wire format, query transformations, execution and observation/history paths are extended; do not silently drop it. Existing `None` behavior remains unchanged. No process remains active.

Next implement that compiled support and compare against the independent oracle, then complete raw-record projection and pending settlements. See the final progress entry for exact checks and limitations.

## Historical milestone: raw-state sampling milestone

`prepurchase_run.py` and `prepurchase_audit.py` now collect isolated real phase states and reconcile persisted cash/units/book value. Latest evidence: `stats/buying-implementation/20261012-prepurchase-suppliers-137/`: 72 captures over six ticks (300 manufacturers/1,000 distributors), 65 positive sampled supplier/phase records totaling 332,000 supplier sales units. These include sales to unsampled buyers, not just captured purchases. Five tests pass in 5.133 seconds, source/archive/capture hashes verify, and no process remains active. No archived execution replay is claimed. Earlier 300/4,200-company runs are preserved and exposed the need to check suppliers, not just buyers’ own lines. See the final progress entry for commands and limits.

Next: raw-record-to-continuation-state projection, independently tested for frozen overhead and pending settlement. Forecast/horizon/terminal inputs remain unadopted; this milestone does not supply them. Production defaults and rules remain unchanged.

## Historical milestone: raw-state capture

`tools/buying_v2/prepurchase_state.py:capture_t2` now captures read-only raw company/book state for reference callbacks, preserving phase-entry overhead and pending seller settlement separately. Four tests pass in 2.016 seconds, including real-phase D3 capture on/off equality of all world arrays and cost sinks. Evidence: `stats/buying-implementation/20261012-prepurchase-state/`. No production kernel or parameter changed. See the final progress entry for scope and commands. Next collect bounded isolated real samples and validate the continuation projection; the raw record is not yet that projection or a checkpoint.

## Historical milestone: scope re-audit

The requested implementation/documentation re-audit is complete: unchanged active 57,960/C3/C4 model, retained phase-body AST equality, and 14 fresh contract/world-parity tests passing in 58.463 seconds. Evidence: `stats/buying-implementation/20261012-scope-reaudit/`; see the final section of [scope audit](buying-behavior-scope-audit.md). No implementation changes or live operations were made. Earlier full-suite/hash claims are checkpoint-specific. Next implementation work remains the representative pre-purchase-state capture/adapter contract below.

## Start here

Work in `/Users/csys/Desktop/ibicot`. Read `AGENTS.md`, [README](../README.md), [integration rules](midbridge-integration.md), and relevant [design canon](design_canon.md). Then read the [master plan](buying-behavior-implementation-plan.md), [accepted contracts](buying-behavior-contract-decisions.md), and [compiled continuation plan](buying-behavior-compiled-continuation-plan.md). The [progress log](buying-behavior-implementation-progress.md) preserves chronological findings, including failed candidates; older remaining-work lists and test counts are historical.

Branch at handoff: `new-recipes`. Base commit: `572e586fae665e10edd9ea5ea459d5f165f1dfd4`. **The implementation is extensively uncommitted and untracked. A checkout of that commit alone does not contain this work.** Preserve the whole workspace, including `docs/`, `tools/buying_v2/`, the new tests, inspector assets, and ignored `stats/buying-implementation/` evidence. Inspect `git status` before editing. Do not reset, clean, discard, or sweep unrelated work into a commit. Source manifests establish experiment identity beyond the base commit.

Tracked modifications include README, `docs/design_canon.md`, `economy/kernel/input_market.py`, `numba.py`, `tick.py`, and `economy/server/persistence.py`. No commit, deployment, live reset, or dependency change was performed for this handoff. No subagents are authorized. Inspect processes/configuration before operating any simulation; an earlier process inspection is not a current inventory.

## Decisions that carry forward

- **D1 accepted:** retain the incumbent unless one supplier alone supplies the whole funded demand at its own quote. A supplies 2 and B supplies 6: retain the old incumbent. Apply the same qualification to first assignment. Do not substitute completion of the remaining request.
- **D2 accepted:** freeze the original incumbent and its live availability at this buyer's product-order opening against positive funded demand at its own quote. If it could fill that demand and any outside supplier makes a positive sale, pay the original incumbent one existing-formula fee. The boundary is buyer, product, purchasing phase within a tick, shared across eligible lines. Earlier buyers' transactions are already committed. Do not reopen the order to multiply or evade fees.
- **D3 resolved:** latent demand = "fill to brim" (the storage slot); the bounded-replenishment comparator is retained as historical evidence, not the adopted model.
- **D4–D6 resolved:** halving price = the input's reference cost (canon `V = unit cost`), elasticity 2, a closed-form rule in both kernels — no forecast or solver required for the adopted model. Stage 7 validation and Stage 8 rollout remain open.

The original research rejected R1. Its equations are not production defaults. See the master plan for full stage and acceptance requirements.

## Implemented work and its limits

| Area | Implemented | Still required |
| --- | --- | --- |
| Purchasing mechanics | D1/D2 contracts; isolated reference/compiled retail and T1/T2 replenishment; split supplies, coupled resources, accounting and independent small oracles | Economic choice and fairness/stress/performance gates; production integration |
| Observations and inspection | Typed counters, seller history, bounded decision traces, experimental exports and recorded-data browser inspector | Production history/checkpoint continuation, live projections, UI and overhead verification |
| Industrial planning | Independent phase ledger/event-tree oracle; endogenous funding; persistent supply; multiple lines/shared inputs; compiled primitives, bounds and certificates | Scalable exact connected solver, fully compiled orchestration, full-world execution |
| Forecasts | Marginal/joint/temporal adapters, response comparators, support and sensitivity audits | Identifiable observation model, explicit priors/calibration, held-out and closed-loop validation |
| Persistence | Policy-marker mismatch rejection and isolated research archives | Complete production schema, migration/resume, rollback package |

The latest connected solver is `tools/buying_v2/continuation_search.py`: an exact small conditional search with a Python outer driver around compiled primitives. Walk/choose/fund frames keep actual and hypothetical transactions separate. Bounded failure raises `SearchLimit`; never turn it into an approximate policy silently. Final selected leaves replay through the connected ledger and verify observations and terminal values.

Implementation map:

- `continuation_program.py`, `continuation_resident.py`: typed event calendar and compiled transaction/accounting execution.
- `continuation_arena.py`, `continuation_branches.py`, `continuation_groups.py`, `continuation_arena_information.py`: bounded state handles, branch rows and information partitions.
- `continuation_advance.py`, `continuation_terminal.py`: compiled nonpurchase advancement and terminal result collection.
- `continuation_actions.py`, `continuation_query.py`, `continuation_query_answers.py`, `continuation_funding_encoding.py`, `continuation_resolve.py`: action traversal, hypothetical queries and funding resolution.
- `continuation_history.py`, `continuation_policy.py`, `continuation_funding_records.py`, `continuation_results.py`, `continuation_leaf_rows.py`, `continuation_control.py`: bounded histories/results and typed control scalars. Python dispatch and object-reference slots remain.
- `continuation_query_memo.py`: bounded exact funding-query reuse, disabled by default.
- `continuation_closing.py`: opt-in certified closing selection and optional exact selection memo. Unsupported eligibility falls back to general search; completed selections still execute through the real ledger. Both remain Python prototypes and default off.

Use the research source-aware JIT wrapper in `tools/buying_v2/jit.py`. Preserve stable ordering, exact state/accounting, strict certificate gaps and tie behavior. `float_sum.py` models Python 3.12 builtin sum; it is not a replacement for `math.fsum`. The independent references are `phase_ledger.py`, `scenario_validation.py` and `phase_oracle.py`; do not make them call the candidate they verify.

## Historical milestone: recorded order size audit

Read [recorded purchasing search sizes](buying-behavior-recorded-search-geometry.md) before treating the small screen as representative. The read-only `trace_search_geometry.py` verifies all 30 files from `20261012-industrial-traces-fullpop-137` and analyzes 484 captured rows out of 720 sampled identities. Median T1 stock/lot/per-material-slot grid is 18,564; the largest captured C3 grid is 1,460,317,392,681,147. These exclude cash, fees, shared total space, production and future decisions; they are not actual search-work counts or a population estimate.

Evidence: `stats/buying-implementation/20261012-recorded-search-geometry/`. Three tests pass; archived analysis source and all input hashes verify, and `archived-replay.json` from `/tmp` equals the full result. No run remains active. Solver code and original-screen completion remain as the prior milestone (13/16); only a read-only analysis tool/test and documentation were added.

Next expand representative scaling via a pre-purchase-state capture/adapter contract. Existing traces do not supply all line execution state or an approved continuation forecast/terminal model. Do not invent those inputs or claim grid cardinality is solver runtime. Retain the 16-case regression while addressing real offer/lot/slot ranges, full-world integration and unresolved model choices within the purchasing-only scope.

## Historical milestone: joint closing fallback milestone

The latest optional mode is `closing_joint_fallback=False` (benchmark key `closingJointFallback`). When enabled, fallback uses the existing joint/cash-relaxed bound only for non-singleton boxes after an incumbent exists. It preserves exact traversal/tie behavior and charges joint work to the existing budget. It remains off by default and changes no outside economic rules.

Evidence: `stats/buying-implementation/20261012-joint-closing-fallback/`. Ten targeted tests passed in 48.119 seconds, including exhaustive and seeded comparisons. Original completion remains 13/16. Expanded case 14 decreases from 2,646 to 2,325 allocations and 34,234 to 33,391 work; case 15 from 23,749 to 12,124 allocations and 447,075 to 406,175 work. All expanded public results are identical; case 7 is unchanged. This improvement supports retaining the optional mode, but not increasing the claimed completed scope.

Snapshot contains 271 files. Archived replay exited successfully: all 16 fingerprints match and all 271 hashes match current and archived source. All thirteen earlier complete public results and three expanded results are unchanged (`verification.json`). All runs from this milestone completed. Next target remaining shared-prefix and fallback complexity; the single-line allocation limit also remains. The full 587-test checkpoint predates the optional recourse cache and this mode; do not claim full discovery on latest source.

## Historical milestone: exact recourse cache milestone

Current research source adds optional `shared_recourse_memo_entries` (default zero) to avoid identical `line_envelope` calls inside shared multi-line proofs. Keys contain all actual function inputs; caller costs/offsets/posterior weighting remain outside. The existing evaluation charge is preserved even for hits. Cache capacity limits entries, not total Python memory.

Evidence: `stats/buying-implementation/20261012-shared-recourse-memo/`. Twelve targeted tests passed in 50.740 seconds. All 16 original screen result/failure payloads match the prior version except recourse cache counters, so completion remains 13/16. Snapshot has 270 files. The previous 587-test full-discovery result predates this change. `timing.py` runs one warmup plus three measured cache-off/on pairs on expanded case 15 and compares full public results and existing counters. Timing completed: three warm interleaved samples give median 15.5389 seconds cache-off and 12.0806 seconds cache-on (22.3% lower), with 140,436 hits/2,832 misses per cached solve. Complete results and existing counters match. Archived replay exited successfully: all 16 fingerprints match and all 270 source hashes match current and archived files (`verification.json`). No run from this milestone remains active. No population-performance claim follows from this single synthetic fixture.

The measured computation saving supports retaining this opt-in prototype. Archive verification is complete; next address remaining proof complexity. Shared proof/fallback complexity and all production/model/integration/economic gates remain open under the purchasing-only restriction.

## Historical milestone: proof cost diagnosis and rejected experiment

At that historical milestone, all 273 hashes matched the 587-test integration checkpoint after the rejected experiment was restored. Its runs completed. The later recourse-cache milestone above describes current source.

`stats/buying-implementation/20261012-closing-proof-diagnosis/` reproduces case 15's entire expanded result including counters. Of 1,800 closing calls, 1,787 certify strictly and 13 fall back. Prefix proofs cost 270,558 work units versus 164,876 closing work; a few fallback calls use over 2,300 allocations each. Shared-prefix work, not just closing work, needs attention.

The candidate in `20261012-prefix-proof-order/` tried ordinary bounds before shared bounds for multi-line prefixes. Seven tests passed and all 16 archived screen fingerprints matched, but expanded case 14 grew from 34,234 to 35,914 work units and case 15 from 447,075 to 461,836, with identical allocations and complete results. The candidate is rejected; do not reapply its archived `continuation_prefix.py`. `verification.json` confirms restoration against the current integration snapshot. Next inspect shared-bound misses/evaluation cost and the few expensive closing fallbacks; avoid repeating this proof-order change or increasing budgets as a claimed optimization.

## Current scope audit and integration checkpoint

The user noticed the README's obsolete 60,000/C5 claims and explicitly prohibited any outside parameter or logic change. Both implementation and relevant documentation were audited. See [scope audit](buying-behavior-scope-audit.md). Loaded backend and effective browser metadata remain 57,960 T2 firms, 105 active C3/C4 products and no C5 phase. Core model/config/catalog files are unchanged from the starting commit. Removing explicit purchasing/observer hooks leaves the four retained phase bodies AST-identical to the originals. README population, execution order and benchmark descriptions were corrected; historical measurements retain their actual historical population.

Evidence: `stats/buying-implementation/20261012-connected-integration-checkpoint/`. Full Python discovery passed: **587 tests in 388.463 seconds**, exit 0. All 273 snapshot hashes matched the working and archived files at that checkpoint (`verification.json`). No run from this checkpoint remains active. Three JS test files and app syntax pass. The expanded diagnostic screen exited successfully: original cases 7, 14 and 15 need respectively 7,238/2,646/23,749 allocations and 20,890/34,234/447,075 combined work units. These are explicitly expanded 100,000/1,000,000 diagnostic limits; the original screen remains **13/16**. Do not count increased budgets as an optimization or production-performance pass. The later proof-cost diagnosis above supersedes this next-step note; preserve the purchasing-only constraint.

## Historical milestone: normalized proof reuse milestone

The latest connected screen completes **13/16**. Opt-in `proof_memo_entries` reuses existing proposal hints, joint proof values and shared-first-production bounds; `closing_cash_relaxed` selects the existing normalized cash-relaxed joint proof. Hints still require a fresh strict certificate; actual decisions still replay through the ledger. Cache limits count entries, not total Python-object bytes. Defaults remain off.

Evidence: `stats/buying-implementation/20261012-connected-proof-memo/`. Ten targeted tests passed in 91.284 seconds, including seeded comparisons of both proof variants, cache eviction/capacity checks, prefix traversal and independent-oracle coverage. All twelve previously completed public results are unchanged. Newly completed case 13 (two lines, capacity 2, two suppliers, two periods/outcomes) matches the larger-budget connected closing search's complete result: value 17, 9,957 versus 1,292 allocations. `new-case-verification.json` labels this comparison scope; it is not a separate unpruned phase-oracle run of case 13.

Case 7 still hits an allocation limit; cases 14–15 hit closing proof-work limits. Next investigate their distinct allocation/closing work before choosing a further optimization. Source snapshot has 269 files. Archived replay is `archived-replay/`, launched from `/tmp`; `replay/` was inadvertently launched from the workspace and is retained as working-tree evidence only. The archived replay exited successfully: all 16 fingerprints match and all 269 hashes match current and archived source (`verification.json`). Tests, screens and new-case verification have also exited successfully; no run from this milestone remains active.

The user asked whether work ends at 16/16: **no**. This is only a synthetic solver screen. Population practicality, unresolved economic decisions, full-world integration, held-out generations/shocks/fairness/recovery, and adoption/rollback review are still necessary. Do not redefine the goal around the screen.

## Historical milestone: prefix proof milestone

The connected action traversal now suspends after each feasible prefix for an optional proof callback. `continuation_prefix.py` uses existing prefix and shared-first-production bounds. Actual proof work shares the prefix/closing budget; unavailable or unbudgeted proofs fall back to traversal. New options are `prune_prefix=False` and `shared_first_states=0`. Production defaults remain unchanged.

Evidence: `stats/buying-implementation/20261012-connected-prefix-bound/`. Ten targeted tests passed in 49.925 seconds; four further tests passed after a diagnostic-only counter refinement. The screen now completes **12/16**. Case 6 matches the entire public result of the connected closing search with new pruning disabled and larger budgets: value 13, allocations 12,270 versus 1,353. See `verify_new_case.py` and `new-case-verification.json`; this was not an independent unpruned phase-oracle run of case 6. The independent-oracle seeded campaign is covered separately by the targeted tests.

Cases 7 and 13–15 still hit limits. Next work should inspect remaining joint closing/proof costs and whether proof memoization or tighter bounds reduce them, while preserving the complete model scope. Full compilation and economic/integration gates remain required. Run `test_buying_v2_connected_prefix test_buying_v2_continuation_actions test_buying_v2_continuation_arena_search` with the established interpreter. Both final screen and archived replay exited successfully. All 16 fingerprints match; all 268 source hashes match current and archived files, and the eleven previously completed results are unchanged (`verification.json`). No process from this milestone remains active. `run/` is preserved before the diagnostic refinement; final source uses `final-run/` and `replay/`. Timing overlaps other local execution and does not establish isolated performance.

## Historical milestone: continuation bound milestone

The next turn added `prune_continuation=True` to `continuation_search.solve`, default off. It evaluates the existing cost-free optimistic bound after a feasible purchase and prunes only strictly inferior suffixes. Each scenario evaluation shares the action-prefix/closing work budget; pruned arena children are released. Unsupported envelopes cannot prune. The benchmark accepts `pruneContinuation`.

Evidence: `stats/buying-implementation/20261012-connected-continuation-bound/`. Six targeted tests passed in 35.835 seconds, covering 24 seeded full-result on/off comparisons and the existing independent-oracle campaign. All eleven completed screen results match the prior checkpoint; completion remains 11/16. Case 5 prunes five suffixes in 236 evaluations; no screened two-line case prunes. The snapshot contains 266 files. The archived replay exited successfully: all 16 fingerprints match, and all 266 hashes match both current and archived files (`verification.json`). No run from this milestone remains active.

Next priority: tighter prefix/shared-resource bounds; this simple envelope does not solve the remaining limits. Run targeted checks with `test_buying_v2_connected_pruning test_buying_v2_continuation_arena_search`. The commands and older confirmed checkpoint below remain valid for reproducing their archived source, not as latest-source full-suite evidence.

## Historical milestone: confirmed checkpoint

Evidence root: `stats/buying-implementation/20261012-continuation-closing-memo/`.

- **18 targeted tests passed in 57.761 seconds**, including cached/uncached full-result comparisons over 24 seeded cases, bounded cache behavior and mode validation. See `tests.log`.
- **265 source/catalog/test hashes verified** against both the current files and archived `source/`.
- The archived benchmark exited successfully. **All 16 result/failure fingerprints match** the working-tree benchmark. See `verification.json`, `run/result.json`, `replay/result.json`, `comparison.json`, and both benchmark logs. No separate archived run of the 18-test suite was performed at this checkpoint.
- **11 of 16 synthetic cases complete exactly; five still reach work limits.** Closing memoization preserves all eleven complete public results. Case 5 falls from 3,708 to 2,304 allocations and from 7,324 to 3,010 closing-work units; no additional case completes.
- Cases 6 and 7 reach allocation limits; cases 13–15 reach closing-work limits. The screen uses 4,000 allocation and 16,000 prefix/closing-work budgets. Cases cover one/two lines and small capacity/supplier/period/outcome combinations. They are not a representative population or calibrated forecast workload. Three timing samples are not a population tail-latency result.

Recent evidence directories under the same `stats/buying-implementation/` parent:

| Directory | Confirmed finding |
| --- | --- |
| `20261012-continuation-storage-audit` | 551 full-discovery Python tests passed in 329.884 seconds; 23 archived selected tests passed; 249 source hashes verified. This predates several later bridges and memo changes. |
| `20261012-connected-scaling` | Connected baseline completes 7/16 synthetic cases; preserved source, repeated fingerprints and archived replay. |
| `20261012-continuation-history-fast-path` | 21 targeted tests and archive replay pass; all 16 screen fingerprints unchanged; reduced history insertion overhead. |
| `20261012-continuation-query-memo` | Exact funding memo passes 16 targeted tests and archive checks; still 7/16 screen completion. |
| `20261012-continuation-closing` | Certified closing bridge reaches 11/16; 15 targeted tests pass, archive replay matches. Newly solved case 5 independently matches the unpruned oracle's complete result at value 6.5, using 35,562 oracle allocations versus 3,708 connected allocations. |
| `20261012-continuation-closing-memo` | Current checkpoint described above. |

The 551-test checkpoint is the latest full-discovery evidence, **not a full-suite result for the latest source**. Older 469/518 totals remain historical. The environment logs a nonfatal NumPy 2.5.3/SciPy compatibility warning; dependencies were not changed. Do not infer latest browser coverage from Python-only checks.

## Continue from here

1. Inspect the current tree and read the latest compiled-plan sections. The closing-memo replay and hash verification are finished; do not repeat them without a change or unresolved concern.
2. Prioritize proven earlier-decision bounds and distinct closing-state work. Exact memoization did not clear the five remaining synthetic limits. Inspect the existing oracle's continuation/prefix/shared-first bounds and closing joint/cash-relaxed proofs before porting. Preserve exact tie traversal, charge work honestly, and compare complete states, policies, observations and funding against the independent oracle.
3. Finish compiled orchestration after establishing solver feasibility. Avoid optimizing another Python layer without evidence that it addresses the remaining cost. Keep multiple-line ownership, repeated ingredients, shared resources and both supply modes; no silent horizon or model narrowing.
4. Run a new full Python checkpoint when the next coherent integration milestone is ready. Add relevant reference/compiled and independent exhaustive checks, then representative configured-population timing, memory and recording/UI overhead measurements.
5. Resolve the remaining economic/forecast choices with a concrete reviewable decision pack. Complete world/runtime/checkpoint/UI integration, held-out generations, shocks, fairness, recovery/drift and expanded-catalog gates. Prepare the rollout/rollback review bundle. Do not activate or mark the full goal complete before its required gates and adoption decision.

Important unresolved economic evidence:

- The seed-137 ticks 1–30/decision-31 quote-support audit found zero structurally supported multi-quote observations in the audited groups. Censored identical histories can conceal replenished future sales of 7,682 versus 10,529 at quote 3. Do not assume these observations identify a demand curve.
- Continuation funding can alter fee eligibility: cash 7, A input price 1, incumbent B price 5/outside B price 1, fee 3 and conversion 0.25 yield value 6.75 after buying two A versus 4.75 after one A because the incumbent funded bid becomes zero. Preserve the counterexample; do not silently change accepted D2 to remove it. See [fee incentives](buying-behavior-v2-fee-incentives.md) and [continuation funding](buying-behavior-v2-continuation-funding.md).
- Transfer-neutral alternatives also have useful fee-funded-buffer counterexamples. Bounded replenishment is not an automatically approved solution.
- Existing startup/year screens and a plausible aggregate equilibrium do not validate generations, company incentives or model suitability.

## Reproduction commands

Use the compatible Python interpreter already installed. From the repository root, the latest targeted selection is:

```sh
PYTHONPATH=.pydeps:.:tests/py /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m unittest test_buying_v2_continuation_closing_memo test_buying_v2_continuation_closing test_buying_v2_continuation_arena_search test_buying_v2_continuation_endogenous test_buying_v2_continuation_search
```

For a new full-discovery checkpoint:

```sh
PYTHONPATH=.pydeps:.:tests/py /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m unittest discover -s tests/py -p 'test_*.py'
```

For an isolated archived benchmark replay, run from `/tmp` and choose a fresh output directory (the tool rejects existing output):

```sh
PYTHONPATH=/Users/csys/Desktop/ibicot/stats/buying-implementation/20261012-continuation-closing-memo/source:/Users/csys/Desktop/ibicot/.pydeps /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m tools.buying_v2.benchmark_continuation --spec /Users/csys/Desktop/ibicot/stats/buying-implementation/20261012-continuation-closing-memo/specification.json --output /tmp/buying-continuation-replay-CHOOSE-UNIQUE-NAME
```

Preserve source snapshots, specification, logs, failures, starting checkpoint, seeds, tick window and terminal exit status for new experiments. Do not overwrite earlier evidence or regenerate goldens merely to hide a failure. `./run.sh test` is curated, not full discovery.

## Keep the handoff current

At every meaningful milestone and before stopping: update this current checkpoint, the progress summary, completed/open items, evidence paths, exact checks and the next action. Record running process/session/output details if leaving a run active. Update accepted decisions only from explicit user instructions. Preserve historical evidence and failed candidates. Another AI should be able to resume from these files without relying on this conversation.
