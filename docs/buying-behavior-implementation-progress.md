# Buying behavior implementation progress

## Adopted as the production default (Stage 8 complete)

The user adopted the price-sensitive fill-to-brim rule as the production default on 2026-10-12, with **no calibration retune** (T1 margin accepted as-is). Stage 8 rollout complete: artifact `db131cc`, service version 0.1.8. Stage 7's preregistered multi-seed validation is deferred by the adoption decision.

## 1-generation run: 98.6% T2 fulfillment — the ~40% was a startup transient

A live app run (57,960 T2 firms, C3/C4, default seed/config) auto-paused at tick 7,200. The earlier ~40% T2 fulfillment (flagged from the 361-tick benchmark) was only the first-year ramp-up: fill rate reaches 93% by year 4 and settles at ~98% through year 20 (**98.6%** at tick 7,200). All 123 products profitable (0 negative-earners); T2 cash 17.97B → 57.29B (3.2×); distributors 99.99% fulfilled. Tier gross margins: T0 47.5%, T1 54.4%, T2 21.0%. Remaining calibration lever: T1 prices 3.05 → 7.53 vs a 2.75 reference. Report: `stats/buying-implementation/20261012-price-sensitive-buying/generation-report.md`.

## Price-sensitive fill-to-brim industrial buying (user-directed)

The user resolved D3–D6 with a simpler rule: latent demand = "fill to brim" (storage slot), quantity = the Tier 3 curve with a heuristically chosen halving price, no continuation planner for the adopted model. Implemented identically in `economy/kernel/tick.py` and `economy/kernel/numba.py` (plus `M.input_reference_cost` in `economy/core/model.py`): `buy_request = min(demand_at_price(slot, halving, quote, 2.0), shortage)`; halving price = the input's reference cost (canon V = unit cost), elasticity 2. D3–D6 are thereby resolved. Three golden tests updated (24 → 6) and a new `tests/py/test_buying_price_sensitive.py` checks the direction; kernel determinism/conservation and reference/compiled byte-equality pass. Full discovery pending at the time of writing.

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

The offer-collapse optimization is now correct and retained. The earlier dedup-key defect — returning `np.arange(count)` as `selected`, which collided across queries in `QueryAnswers.request` — is fixed by returning the original offer subset and validating the allocation length against the collapsed `iv[0]` in both `funding_purchase` paths (`continuation_resident.py`, `continuation_arena.py`). It applies to all continuation-v2 funding queries under independent-snapshot supply; persistent arrivals keep the original enumeration. Verification: full `test_buying_v2*.py` discovery passes **536 tests in 455.573s**, including the 24 seeded oracle comparisons and the seeded differential funding/policy/account check. Evidence and source snapshot: `stats/buying-implementation/20261012-captured-offer-collapse/` (318 source hashes, specification, 8 fingerprints).

Completion remains 4/8, but the zero-sales bottleneck moves past funding: cases 1/3 now finish all 13 funding queries (`fundingQueries=13`) and fail later in the actual purchase traversal (12 offers, depth 11), while full-clearance cases 0/2 still exhaust work inside a collapsed per-offer query (`fundingQueries=4/6`; their `held=0` keeps per-material caps at ~2,833/2,000, so the 2-offer query space is ~8M and remains bound-slack-bound). Solved-case prefix work falls ~2.6–2.8× (0/zero-sales 156→60, 1/full-clearance 216→76, 2/zero-sales 150→54, 3/full-clearance 216→76). This is a behavior-preserving search-work reduction, not a completion pass.

Remaining completion levers are unchanged: the actual purchase and the large-cap per-offer queries still carry the forced-production and free-input bound slack. Collapsing the actual purchase frame is unsafe because fees and preferences depend on the per-offer split under a positive funded demand. The next step remains tightening `continuation_bound.line_envelope` to lower-bound the forced gate-limited production conversion cost.

## Collapse experiment rejected: dedup key blocks it, and bound slack stays the lever

Attempted to collapse same-(material, price, lot) offers inside the continuation-v2 funding queries to remove the redundant per-offer composition enumeration. The joint-query-only collapse is correct (24 seeded comparisons plus native/tie tests pass) but leaves completion at 4/8 and only trims work in solved cases. Extending it to the per-offer queries broke the seeded differential comparison: the collapsed payload returned `np.arange(count)` as `selected`, and `QueryAnswers.request` keys its dedup on that offer-set tuple, so distinct joint/per-offer queries with the same collapsed shape shared one answer and produced wrong funding vectors. The source was restored byte-for-byte from the retained conversion-range snapshot (318 hashes re-verified).

The attempt still sharpens the diagnosis. Collapsing the joint query from 10→2 offers leaves the full-clearance limit cases essentially unchanged (case 0: 5,369→5,372 prefixes), confirming they are bound-slack-bound, not action-space-bound. The zero-sales cases are partly composition-bound (0/zero-sales falls to ~20 prefixes under the buggy extended collapse) but still cannot certify optimality because of the forced-production slack. The completion lever remains `continuation_bound.line_envelope`: it must lower-bound the forced gate-limited production conversion cost. A dedup-safe collapse would additionally need to key `QueryAnswers` on the original offer subset rather than the collapsed representative indices.

## Precise limit-case diagnosis: bound slack, not range-proof leverage

Instrumented the retained conversion-range search on all four limit cases and measured the range-proof values directly (monkeypatched `continuation_range.RangeProof.check`; no source changed). The joint all-quotes funding query is confirmed as the failure point (`fundingQueries=1`, `activeFrames=3`, `action prefix work limit`). Two distinct slack mechanisms explain why optimality cannot be certified within the 16,000 combined-work budget:

- **zero-sales cases (1/3):** `prior ≈ −16`, range ceiling `≈ 0`. The −16 is the conversion cost of gate-limited production from already-held inputs (`held=2801`/`1976` ≥ `max_batches`); the envelope reports ≈0 because `line_envelope` caps realized production at `min(demand, capacity)` = 0 under zero demand. The bound is valid but loose by exactly that forced-production conversion cost, so it cannot prune prefixes whose goods payment is ≤ ~16.
- **full-clearance cases (0/2):** `prior = 0`, range ceiling `≈ 216.64`/`278.64` (free-input gross return). Because the range ceiling prices suffix inputs at zero, it only prunes when the prefix goods payment exceeds ~216–278; it prunes just 87/147 of ~5,359 range checks (case 0/2) and is nearly inert. The cost-aware prefix bound performs ~98% of the pruning.

Completion was 4/8 both before and after the range proof (the range proof only reduced work in already-completed cases), so the range proof is not the completion lever. The remaining slack lives in the cost-aware prefix bound's `line_envelope`: it optimizes production as demand-limited (and assumes omniscient production), while the actual `purchase` event produces gate-limited regardless of future demand. Next work: tighten `line_envelope` to lower-bound the forced gate-limited production conversion cost (closes zero-sales) and to price suffix inputs at their actual costs (closes full-clearance). The earlier "collapse same-price same-material offers inside the joint query" idea remains a separate, orthogonal lever with the tie-break caveats already noted. No source, test, parameter, or live run was changed by this diagnosis.

## Archived replay completed; four-case bottleneck analyzed

Completed the previously missing archived execution replay of the rejected resource-keyed range-cache candidate. Running the candidate archived source from `/tmp` reproduces all eight captured result/failure fingerprints exactly (4 exact, 4 limit), and all 318 archived source hashes match the candidate manifest. Evidence: `stats/buying-implementation/20261012-captured-resource-cache/archived-replay-verification.json`, plus `replay/` and `replay.log` preserved beside the candidate. No working-tree source, test, parameter, or live run changed. The rejection decision is unchanged; the replay authenticates the recorded candidate results against the archived source.

Direct analysis of the four unresolved captured cases (0/full-clearance, 1/zero-sales, 2/full-clearance, 3/zero-sales) shows they all exhaust the 16,000 combined prefix/bound-work budget inside the first funding query — the joint all-quotes query (ordinal 0). Each reports `fundingQueries=1`, `activeFrames=3` (fund/choose/walk), and fails with `action prefix work limit`. Bound work dominates (≈9,700–10,600 of 16,000; roughly two units per visited prefix = range proof + prefix bound for a one-scenario group). The joint query result is metadata only: `continuation_funding_encoding.encode_answers` and `continuation_resolve.resolve_answers` take the actual funded `demands` from the per-offer queries, while `jointQuantities`/`jointGoods` are written to the funding record and never affect the purchase, fees, preferences, or terminal value; the joint conditional value is not even stored. The per-offer queries never run because the joint query fails first. The frame's aggregate `remaining` bound (sum of per-offer caps) is confirmed not to be the bottleneck: the compiled `advance` native `inventory` check already enforces the tight `held + Σq ≤ max(held, slot)` constraint.

Next direction (not implemented): collapse same-price same-material offers inside the joint query only. All four captured cases have uniform within-material prices, so the hypothetical continuation value and goods cost depend only on the per-material aggregate, and incumbents are held plus current fees are removed inside the query. This would shrink the joint query from 10–12 offers to 2 here. It requires preserving lexicographic tie-breaking and the seeded oracle funding comparisons, and must leave per-offer-query and actual-selection semantics untouched. The retained global conversion-aware range proof remains the starting point.

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


Updated 2026-10-12. Active objective: implement the [master plan](buying-behavior-implementation-plan.md) in full. This is an implementation record, not an adoption recommendation. Production purchasing defaults remain unchanged. The checkpoint loader now rejects a mismatched purchasing-policy marker; isolated retail execution is implemented under tools/buying_v2.

**Continuation entry point:** [Implementation handoff](buying-behavior-handoff.md) contains the current checkpoint, accepted decisions, source map, evidence, reproduction commands and next work. Keep it updated at milestones and before stopping.

## Accepted decisions

The user answered both contract questions during implementation:

- D1: keep the old preference unless one supplier alone supplies the whole demand. A=2/B=6 therefore retains the old incumbent.
- D2: use one fee per product order as proposed, freezing the original incumbent and its availability against the funded demand at its own quote before this order's deliveries.

The [contract decision pack](buying-behavior-contract-decisions.md) records details, alternatives, and consequences. Do not reopen these choices or silently substitute terminal-remainder qualification. In particular, persistent preference retention under repeated split orders is an accepted rule's possible consequence, not permission to change it.

## Initial evidence (historical)

| Work | Evidence | Scope |
| --- | --- | --- |
| Current source inspection | Commit `572e586fae665e10edd9ea5ea459d5f165f1dfd4`, branch `new-recipes`; baseline source archive | Shared selector still favors full fills; T1/T2 still set preference after positive delivery; T3 still draws with replacement and deduplicates. |
| Fresh baseline | `stats/buying-implementation/20261012-baseline-137-stage0/` | Full population, seed 137, ticks 1–360; config/catalog/source hashes, product/company accounts, and final checkpoint preserved. |
| Archive audit | `stats/buying-implementation/stage0-baseline-audit.json` | All 71 archived files verified; exact 360-tick recording coverage; 168 checkpoint arrays; recorded invariant checks pass. This is not an independent replay or long-run adoption proof. |
| Baseline Python discovery | `stats/buying-implementation/stage0-python-discovery.log` | 121 tests passed in 34.640 seconds, including the six contract-alternative tests present when discovery started. Later tests have separate evidence. |
| Contract alternatives | `tools/buying_v2/contract_cases.py`, `tests/py/test_buying_contract.py` | Executable whole-versus-remainder qualification and proposed one-fee settlement boundary. Does not derive bids or prove incentives. |
| Observation reducer | `tools/buying_v2/observations.py`, `tests/py/test_buying_observations.py` | Four tests pass for compiled/reference reduction, no input mutation, distinct request stages, fees versus switches, and no-history cases. Not connected to kernels/recordings/UI yet. |
| Retail basket solver | `tools/buying_v2/retail.py`, `tests/py/test_buying_v2_retail.py` | Three tests including 600 independent exhaustive allocation comparisons, compiled/reference agreement, fee-versus-incumbent choice, and accepted whole-demand preference. Isolated solver only. |

The 360-tick baseline recorded maximum company/money/goods tolerance ratios of 0.0181531 / 0.000726426 / 0.020752, nonnegative cash/stock, and zero price-bound contacts. Its timing includes ordinary local contention and is a baseline capture, not the final isolated performance gate. No simulation service process was found in the initial process inspection; no process was reset or terminated.

The existing SciPy/NumPy compatibility warning remains in test logs. Dependencies were not changed, and the reported checks passed despite that warning.

## Current implementation status

The initial table above records the starting state. Later entries are chronological evidence; their historical “remaining” lists do not override this current summary.

| Area | Implemented experimental components | Remaining completion evidence |
| --- | --- | --- |
| Mechanics | D1/D2 contracts; reference/compiled retail and T1/T2 replenishment; partial/split suppliers, coupled resources, phase settlement and independent small oracles | Resolve D3 objective; complete fairness, stress, performance and economic gates for the corrected baseline |
| Observations | Typed counters, phase-specific seller history, bounded retail/industrial traces, isolated exports and rendered recorded-data inspector | Production runtime, checkpoint/history continuation, live projections and UI integration; full overhead/memory measurements |
| Industrial planning | Ledger/event-tree oracle, endogenous funding, persistent supply, supported multiple lines, compiled closing bounds/certificates and exact reuse | Single-line screen: 30/32 (all feasible-prefix rows complete). Two-line shared-input screen: 13/16 with joint proofs, with three remaining search limits (prefix, allocation and closing under normalized reuse); full-population practicality and complete world execution of the new value model |
| Forecasts | Marginal, joint and temporal adapters; price-response comparators; coverage/identification probes; purchasing sensitivity | Adequate incomplete-observation model with explicit priors, empirical calibration, industrial/temporal and closed-loop validation |
| Reproducibility | Source manifests, isolated archives/replays, policy compatibility checks and preserved baseline/year screens | Unified production persistence/migration and complete rollout/rollback bundle |

Latest full-discovery checkpoint (after the offer-collapse optimization): **663 Python tests passed** in 430.458 seconds. The offer-collapse (equal-(material, price, lot) grouping inside continuation-v2 funding queries, retained 2026-10-12) reduces solved captured-case prefix work ~2.6–2.8× and is covered by the 24 seeded oracle comparisons and the seeded differential funding/policy/account check. Evidence: `stats/buying-implementation/20261012-captured-offer-collapse/` (318 source hashes). Production files remain byte-identical to the pre-collapse retained snapshot; only `tools/buying_v2/continuation_query.py`, `continuation_resident.py` and `continuation_arena.py` changed.

Latest synthetic connected checkpoint remains **13/16** (unchanged by the collapse). The captured-state diagnostic remains **4/8**: zero-sales cases 1/3 now complete funding and fail in the actual purchase, while full-clearance cases 0/2 fail inside a collapsed per-offer query. Tightening the range proof is structurally blocked (monotonicity versus input-cost accounting), so a different tail certificate is required. See the newest entries above. This establishes integration checks, not economic suitability or population performance. Earlier counts are historical.

D1 and D2 remain accepted. D3–D6 contain unresolved model/implementation choices, including the industrial fee-incentive question. No answer is inferred from an experiment or an assistant proposal.

The required held-out generation, recovery, fairness, expanded-catalog and performance campaign remains incomplete. Existing inspected seeds are calibration evidence. Production documentation and live adoption follow passing gates and the user's final transition decision; no live rollout has occurred. Passing small or combined tests cannot substitute for those gates.


## Retail integration continuation

The previous goal turn made concrete progress. This continuation adds distinct bounded discovery, actual retail stock/cash/revenue/COGS/fee settlement, an isolated full-tick engine, a source-aware replacement JIT namespace, and a policy-checked checkpoint loader. The current retail contract is in [Replacement retail implementation contract](buying-behavior-v2-retail-contract.md).

`20261012-retail-v2-screen-137` completed 360 full-population ticks under archived policy `v2-retail-only-v1`. All recorded invariants pass. Retail volume was 1,391,734.55 units/tick versus 1,390,767.20 in the matched original baseline; manufacturer posted net earnings were $1,288,083,381.74 versus $1,294,302,663.87 over ticks 1–360. These startup observations establish neither long-run suitability nor a causal effect of one mechanic. Timing is unisolated and materially slower, so optimization and final performance gates remain open. Exact comparison accounts are preserved in `stats/buying-implementation/retail-screen-comparison.json`.

A review corrected fee/valuation rejections being represented as request legs in that initial adapter. Current policy `v2-retail-only-v2` creates no supplier request for those rejected evaluations. The archived v1 run is retained; do not present it as a test of this revised policy.

Tests in `retail-v2-integration-tests.log` pass 20 cases including actual reference/compiled postings, native continuation and baseline-loader rejection. After removing intermediate allocation-array copies, `retail-prefix-optimization-tests.log` passes 17 relevant tests. `retail-prefix-optimization-proof.json` additionally compares all allocation/objective/cost/fee/preference outputs exactly against the independently archived original solver for 2,000 random floating-point cases. These proofs do not claim full-world behavior equivalence across the separate observation-policy revision.

The current-policy 360-tick run is `stats/buying-implementation/20261012-retail-v2-current-137`, with process output in `retail-v2-current-137.log`. Revalidate its process/session and manifest before interpreting completion; it was launched at the end of this continuation. Production industrial buying is still baseline. The immediate next work is to inspect this run, finish observation/metric semantics and fair tie treatment, and implement the coupled industrial mechanics and independent general oracle. Stage 2 integration into production recording/UI and every long-run adoption gate remain unfinished.


## Industrial reference and retail workspace continuation

The prior continuation was progress: it added executable settlement, verified continuation, and preserved a live screening run. That run, `20261012-retail-v2-current-137`, is now complete with all recorded invariants passing. Its unisolated warm kernel median was 355.19 ms, versus about 125 ms for the earlier baseline capture; this is a warning for the relative performance gate, not an isolated final benchmark.

The new industrial contract is in [Industrial buying reference contract](buying-behavior-v2-industrial-contract.md). `industry_oracle.py` enumerates every small feasible purchase allocation including split suppliers and unmatched buffers, then simulates actual ordered production with the retained book-cost gate. `industry.py` independently implements compiled enumeration using the real gate. Six tests pass, including 160 randomized multiline/shared-resource comparisons and the historical-cost counterexample. Evidence: `industrial-reference-arithmetic-tests.log`. This establishes a small reference contract, not a scalable full-world optimizer; output and terminal-value tables are explicit test assumptions, not adopted forecasts.

Retail now reuses per-tick scratch arrays for marginal values, quantities, allocations and observations. Thirteen combined retail/world/industrial tests pass in `reusable-workspace-tests.log`. A separate full-population same-policy run, `20261012-retail-v2-workspace-137`, is checking the optimization against the independently preserved current-policy run. Its launch session is 2099; revalidate the handle before acting on it. `tools/buying_v2/compare_runs.py` will compare all recorded NPZ arrays, checkpoint JSON, config/schema, and tick invariant histories when it finishes. Do not claim exact whole-world equivalence until this comparison passes.

Next steps remain scalable coupled industrial allocation and valuation, retail performance/fairness, full observation/recording/UI integration, and the master plan's complete economic/adoption gates. No live deployment has occurred.


## Exact optimization proofs and compiled industrial search

The previous continuation was progress. The retail workspace run completed; `retail-workspace-world-proof.json` verifies all 210 stored arrays, native checkpoint JSON, measurement schemas/configuration, and tick invariant histories exactly against the preserved same-policy run. Warm kernel median fell from 355.19 to 251.60 ms; runtime fell from about 139.66 to 98 seconds. These remain unisolated screening measurements, not the final adoption budget.

Industrial search now has readable and compiled branch-and-bound implementations with explicit optimality certificates and no silent approximate fallback. Its bounds retain split suppliers, unmatched buffers, multiple lines, historical basis and production-gate behavior. Initial failed scaling probes are preserved. Stronger per-line input/conversion cost bounds solve all five synthetic cases; the largest has about 8.3e28 possible allocations but requires 1,605 visited nodes in this fixture. Prefix/concavity bounds reduce its measured time to approximately 2.27 ms. That is still not practical evidence for tens of thousands of arbitrary firms every tick.

`industrial-bound-certificate-tests.log` records nine passing tests, including 160 oracle comparisons and 80 random-box upper-bound checks covering nonconcave valuations. Input validation now rejects fractional quantities and nonfinite value tables before compiled casts can reinterpret them. Details and bound arguments are recorded in the industrial contract.

No simulation or test process remains intentionally running at this handoff. Next: capture representative real-company solver workloads from the preserved checkpoint, optimize against those without restricting actions, implement the D3 corrected-replenishment adapter and actual shared-resource settlement, and define/test the D4–D5 information and valuation candidates. Full kernel/recording/UI integration and long-run validation remain open. The master-plan objective is active and incomplete.


## Real company cases and atomic industrial settlement

This continuation made concrete progress. Nine actual-resource manufacturer cases were captured from the preserved tick-360 baseline without modifying it. Eight solved under the original bound search; one hit the explicit 20,000-node limit. The new single-line relaxation verifies its proposed optimum against actual production and otherwise falls back. All nine captured cases now solve, including the previously limited case with three eight-unit complement deliveries. Original and improved case directories are retained separately. Their quote-based value tables and disabled fees are workload assumptions, not adopted economics.

Industrial objective/payment comparisons now have an explicitly documented numerical tie tolerance; this is an intentional prototype convention change, not a claimed bit-preserving optimization. The independent oracle and search implementations were updated together, with 400 additional decimal-price/lot/gate comparisons and an invalid-production-certificate regression. Production accounting and retail behavior were not changed.

Added atomic T2 reference settlement with whole-basket validation before mutation, existing-formula fees, original-incumbent availability, whole-demand preference qualification, weighted inventory basis, seller COGS, and separate intermediate/fee postings. Its AOV counters retain the existing native-company-class successful-leg denominator. It is not yet connected to a full industrial decision kernel. Final combined evidence for this continuation is `industrial-certified-regressions.log`.

Next work: implement the coupled funded-demand and corrected-replenishment adapter, extend settlement to T1 and compiled population execution, specify candidate output/terminal forecasts, and test complete worlds. The numerical fast-path scope and real-case timing do not satisfy the remaining performance, ownership, UI, long-run, or adoption requirements. The goal remains active; no deployment or live reset occurred.


## Coupled funding and reference T2 integration

Implemented stock-unconstrained joint hypothetical funding, per-quote cumulative fallback constraints, and the D3 item-count/cost replenishment comparator. Its uniform-lot solver and binding-space exact fallback pass 600 exhaustive randomized comparisons. A further 1,000 arbitrary-cap comparisons caught and now cover an equal-price/tie-order feasibility defect. Evidence: `replenishment-arbitrary-caps-tests.log` (four tests passed).

The actual-resource adapter now feeds atomic settlement and an isolated full reference T2 phase, preserving real production and phase-end receipts. Corrected a prototype ordering error: production uses installed slots, even though planning rotates slots. Existing over-slot inventory is retained after equipment reallocation. The ordinary purchasing path remains default; the optional reference callback is only supplied by the experimental engine.

`industrial-adapter-tests-v2.log` records 16 passing tests covering actual goods/money/basis, multiline order, over-slot stock, funded bids, atomic settlement, exhaustive replenishment, complete-world accounting and exact checkpoint continuation. `phase-hook-baseline-proof.log` independently compares ordinary calls with preserved HEAD phase source over four ticks/all phases: every world array and cost/equipment sinks match. Later arbitrary-cap solver regression passed separately. No live process was reset or deployed.

Remaining: compiled industrial and T1 adapters; complete request/shortfall observations, recorder and UI integration; batch-first comparison; defensible valuation/information models; fairness and strategic fixtures; full-population performance and long-run campaigns; rollout decision. Reference full-world execution is a milestone, not completion of the master-plan goal.

Final combined regression for this continuation: `industrial-integration-final-tests.log`, 32 tests passed in 14.256 seconds across adapter, settlement, funding, replenishment, industrial oracle/search, and retail/world continuation modules. Local documentation links and `git diff --check` pass. This is a targeted suite, not full Python discovery. The existing SciPy/NumPy warning persists without dependency changes.

## T1 reference integration and both-tier screening

The preceding continuation was progress: it added complete reference T2 execution and 32 passing targeted tests. This continuation adds T1 joint wholesale procurement, atomic settlement, actual lot constraints, original-incumbent single fees, and whole-demand preference qualification. The combined reference engine now executes both industrial purchasing tiers. Its runner accepts explicit policy choices and archives the exact treatment.

`refinery-reference-tests.log`: four tests passed for split lots/fees/preference, incumbent availability, atomic rejection and shared company resources. `both-industrial-reference-tests.log`: nine tests passed, including complete-world accounting and exact continuation for the T2-only and both-industrial reference engines. `refinery-hook-baseline-proof.log`: four default T1 purchase phases match every world array against independently loaded HEAD source. No production default changed.

The archived run `20261012-both-industrial-reference-screen-137` completed 30 ticks with 300 manufacturers and 1,000 distributors, seed 137. Maximum company/money/goods tolerance ratios: 0.00032349 / 0.00020417 / 0.0. Minimum cash was approximately $0.1103, minimum stock zero, and price-bound contact counts zero. Runtime was 34.46 seconds; warm median approximately 1,130 ms. This demonstrates why compiled population execution is the next priority; reference speed fails the absolute adoption budget even at this reduced population. It does not establish long-run health.

Request semantics remain incomplete: industrial supplier request/reliability counters currently capture positive delivery legs, while failed empty-stock attempts need explicit treatment. The purchase observation sidecar remains retail only, labelled in the runner manifest. Do not use it to claim industrial observation coverage. No live processes were reset or deployed. The goal remains active, including valuation, full observation/UI work and all remaining master-plan gates.

## Compiled industrial populations

The prior turn was progress: both reference tiers executed and their accounting passed, but speed failed. This continuation ports joint funding and exact binding-storage search to typed arrays, then integrates compiled T1 and T2 company purchasing through optional callbacks in the existing production loops. The experimental loop compilation uses the source-aware v2 cache. Ordinary production buying remains default.

`compiled-funding-tests.log`: 500 reference funding comparisons and 400 independent exhaustive allocation cases passed. `compiled-funding-specialization-tests.log`: expanded to 1,000 decimal-price/cash funding cases and complete-world reference/compiled comparisons, including 4,200 manufacturers so both upstream C3 and downstream C4 phases execute. The earlier `compiled-industrial-regressions.log` records 18 passing tests including existing fallback, stock-access and performance/reference contracts. Additional final guard/book-builder regressions are recorded separately.

At the reduced population, the preserved 30-tick compiled run exactly matches all 210 archived arrays and checkpoint/metric data from the reference run (`industrial-compilation-world-proof.json`). Warm median fell from 1,129.98 to 12.69 ms. Full-population seed-137 screening completed 30 ticks with invariant checks passing: initial compiled median 499.02 ms, then 435.29 ms after a behavior-preserving reference-funding specialization. `industrial-funding-specialization-world-proof.json` verifies exact full-population recorded-state equality across that optimization.

Warm profiling identifies manufacturer purchasing and Python supplier-book construction as the main remaining costs. The latest compiled path selects the existing vectorized book builder; baseline callers retain the ordinary builder. Compiled callbacks now explicitly reject fractional owned input stock before transfers, aligning with reference validation. Performance remains an open gate, and industrial request observations, UI, economic valuation, fairness/stress/long-run campaigns and rollout remain unfinished.

Final evidence for this continuation: `compiled-industrial-final-regressions.log` records 19 targeted tests passing in 57.394 seconds, including fractional-input rejection before transfers and unchanged production fallback/stock-access/performance contracts. `20261012-industrial-compiled-vector-book-137` completed 30 full-population ticks with all recorded invariants passing; warm median 400.20 ms. `industrial-vector-book-world-proof.json` confirms exact equality of all 210 recorded arrays, checkpoint JSON and tick invariant histories against the preceding funding-fast run. These screening times remain above the relative budget; p95 and memory gates are not yet established. No experiment remains intentionally running. Next: reduce remaining compiled purchasing overhead, complete industrial request/observation semantics, and proceed with the unresolved D3–D5 comparison/valuation work without treating the current storage-refill comparator as the final economic model.

## Industrial observation integration

The preceding turn was progress: compiled execution and exact optimization proofs reached both tiers. This continuation adds typed industrial decision observations, reference/compiled recording hooks, a version-2 purchase-recording envelope and period JSON projections with explicit units, denominator definitions and null missing values.

Inspection refined the earlier “failed request” concern: the current optimizer sees stock before selecting its basket. Empty discovered offers are not automatically submitted orders. The new metrics distinguish funded availability checks from positive transaction legs and legacy quote remainders; they expose empty supply without creating incoming demand. Existing reliability, pricing and all financial behavior are unchanged. A different inquiry/request protocol remains a separately testable model choice.

Initial observation tests passed eight cases, including all-array reference/compiled equality. `industrial-observation-integration-tests.log` subsequently passed 15 targeted tests in 67.619 seconds: reducer semantics, zero/missing-history projections, instrumentation enabled/disabled state equality, posted purchase/fee reconciliation, checkpoint metric continuation and compiled/reference agreement including C3/C4 and multiline ownership. An additional available-stock/no-purchase boundary test is included in the final module run.

The full-population measurement-only run and strict comparison with the preserved uninstrumented run are the next verification step. `verify_measurement_addition.py` permits only the explicitly added industrial array and additive schema envelope; it still requires every previously recorded state array, checkpoint, configuration and tick invariant to match.

The full-population run `20261012-industrial-observed-fullpop-137` completed ticks 1–30 with all recorded invariants passing. `industrial-observation-world-proof.json` verifies exact equality of all 210 pre-existing arrays, checkpoint JSON, config and tick invariants against `20261012-industrial-compiled-vector-book-137`, while separately validating the added 54-row industrial history. Warm median was 410.92 ms; the single-run difference from 400.20 ms is screening evidence, not an isolated overhead bound or a passed relative timing gate.

`industrial-purchase-summary-137.json` is the reproducible period projection. T1/T2 recorded 322,900,000 / 182,030,925 purchased items and 42,958 / 488,667 positive legs. These are transactions, not distinct firms. T2 recorded 12,209,644 below-one-lot stock checks among 14,540,349 positive funded quote checks; this is a sampled availability diagnostic, not unique unmet demand or a causal estimate. No fees were paid in this short startup window; forced-fee fixtures remain the relevant settlement evidence.

`industrial-observation-final-tests.log` passes all eight observation/projection tests, including the added available-stock/no-purchase case. Local documentation links and `git diff --check` pass. No experiment remains intentionally running. Still open: deterministic per-decision samples, rendered dashboard integration, an explicit inquiry/request information-model comparison, D3 batch-first comparison, industrial valuation, the relative performance gate and long-run/stress/fairness/adoption requirements. The full goal remains active; production defaults are unchanged.

## Procurement objectives and conditional buffer value

The previous turn made progress by adding measurement-only evidence with exact state equality. This continuation returns to the economic model. `policy_comparison.py` compares storage units, actual batch-first production and explicit scenario return with independently enumerated small allocations. Each policy funds its own coupled intentions. The counterexamples show item-maximization exhausting complement/conversion cash and batch-first production buying unsellable output. The old-basis production gate remains binding for every objective.

Added `continuation_oracle.py`, a small two-period delayed-receipt benchmark with actual basis, cash, storage, lots and production. It establishes when a missing-complement buffer is useful and demonstrates that its value depends on future liquidity and complement arrival. Initial actions cannot depend on which supply state will later occur; later actions cannot see future demand. It explicitly excludes fees/rent and is not a population-ready world model.

Evidence: `industrial-objective-counterexamples-v2.json`, `industrial-continuation-counterexamples.json`, and eight passing tests in `industrial-continuation-information-tests.log`. The first objective-report JSON is preserved as an invalid partial artifact after serialization failed; the successful v2 report is the evidence. The [value-model implementation contract](buying-behavior-v2-value-model.md) records the numerical cases, recommends expected realizable return over quantity/production objectives, and specifies the remaining timing, information and valuation requirements. No forecasting defaults or live purchasing policy changed.

Final continuation evidence: `industrial-value-contract-final-tests.log` passes eight tests in 1.754 seconds. The oracle additionally merges observationally identical supply states before optimizing hidden demand/terminal values, closing a potential scenario-label information leak. The successful final report is `industrial-continuation-counterexamples-v2.json`; report parsing, local document links and `git diff --check` pass. No simulation is intentionally running. Next required work is a phase-accurate, fee/rent-aware continuation contract and versioned local/market/hybrid forecast collectors; the current additive value-table solver must not be claimed to implement the coupled future-value model. Dashboard, performance and long-run/adoption gates also remain open.

## Phase-specific seller observations

Implemented a versioned read-only seller-history collector and connected it to both experimental engines. It records T0 wholesale, retail, and each actual manufacturing input-book phase separately, including live discovery/funded/short checks. Same-phase production cannot erase a stock constraint observed earlier. Stable numeric identities support appended lines; reassignment, incompatible lots/catalogs, stale ticks and corrupted history require rejection or explicit migration. See the [seller-history contract](buying-behavior-v2-seller-history.md).

Persistence uses one exclusive NPZ artifact containing its metadata. Rolling histories preserve measured zero sales, absent offers and zero discovery as distinct observations. No forecast consumes these arrays yet. The runner accepts an explicit `--seller-history-window`; zero remains the default. Production purchasing, reliability, accounting and checkpoint schemas are unchanged by this collector.

The first connected test exposed a missing NumPy import in reference settlement, which was fixed before the successful run. The subsequent two connected tests passed in 41.746 seconds, covering whole-lot snapshots, reference/compiled history equality, every world array against an uninstrumented control, C3/C4, appended ownership lines, posted sales and history reload between ticks. Container tests cover corruption, exclusive writes, validation before record mutation, and ring continuation.

Preserved full-population run: `20261012-industrial-seller-history-fullpop-137`, seed 137, ticks 1–30, explicit 32-tick retention. Its invariant gate passes. `seller-history-world-proof.json`, reproduced by `verify-seller-history-addition.py`, confirms equality of all 211 previously recorded arrays, checkpoint JSON, schemas/config and tick invariants with `20261012-industrial-observed-fullpop-137`. Only the declared new history sidecar is excluded from equality; every tick's industrial sales/discovery/funded counts and retail sales/discovery reconcile to independently recorded purchase totals.

Retained history arrays use 242,621,824 bytes; the compressed sidecar is 5,658,447 bytes. Warm median was 459.58 ms, but this run overlapped regression work and cannot estimate instrumentation overhead or pass the timing gate. Total process memory and isolated tail latency remain unmeasured. The 32-tick choice is a collection fixture, not an adopted forecast parameter.

Next: candidate local/market/hybrid estimators with explicit information boundaries and no-history/stock-censoring assumptions; phase-accurate continuation with fees/rent; coupled value optimization. Forecast validation, decision traces, UI integration, performance, multi-generation/shock/fairness experiments and rollout gates remain open. The full implementation goal remains active.

Final verification: `seller-history-final-tests.log` records 26 passing targeted tests in 79.149 seconds across history, connected worlds, compiled procurement, retail settlement/continuation and industrial observations. Local documentation links and `git diff --check` pass. The existing SciPy/NumPy compatibility warning remains nonfatal; dependencies were not changed. No experiment from this continuation remains running.

## Explicit local, market and hybrid forecast candidates

The prior turn made verified progress: phase-specific histories matched the complete recorded world and persisted correctly. This continuation implements a reference empirical scenario model with completed-tick publication, distinct missing/measured-zero/constrained rows, explicit quote-response and cold-start assumptions, a product-level equal-share market comparator, and a probability-mixture hybrid. Existing finished inventory consumes prospective sales before new output receives value. Every calibration parameter is required; no parameter set or purchasing policy is adopted. The [forecast contract](buying-behavior-v2-forecast-contract.md) states the equations, inquiry-information assumption, finite-tail limitation and remaining validation.

`forecast_screen.py` provides reproducible retrospective calibration scoring with source/specification hashes and fixed tick-1 seller samples. `forecast-calibration-spec.json` was saved before scoring. The first attempt failed a selected-channel coverage check before scoring and remains preserved; the corrected `20261012-forecast-calibration-137-v2` completed in 12.093 seconds. Its data are historical seed-137 ticks 2–30, not new held-out evidence. Predictions are conditioned on actual phase-entry stock/quotes; scores do not estimate latent-demand accuracy or counterfactual buying-policy performance.

The screen exposes limited identification: only 244 of 6,090 sampled retail seller-phase observations had nonempty inventory, and 234 of those had stock-constraint markers. A larger assumed tail reduces MAE but increases the C3 local positive bias. No winner or calibrated tail is selected. More diagnostic information/probes and actual closed-loop evaluation remain necessary; completing this reference forecast does not complete the industrial value model.

Next required work: phase-accurate continuation with real receipt timing, D1/D2 fees and rent; controlled forecast probes and an explicit transaction-only feedback comparison; joint supply/sales scenarios and scalable coupled value optimization. Decision traces, runtime/UI integration, performance and full economic/adoption gates remain open. The goal remains active and production defaults remain unchanged.

Final verification for this continuation: `forecast-final-regressions.log` passes 30 targeted tests in 1.875 seconds across forecasts, scoring, seller history and the independent procurement/continuation counterexamples. Added checks prevent unrelated products from inflating a market forecast and reject valuing a distribution at a different quote without reforecasting. Local documentation links and `git diff --check` pass. The existing SciPy/NumPy warning is unchanged. The successful calibration source is archived independently of subsequent validation-only guard additions. No new simulation or live adoption occurred, and no process from this continuation remains running.

## Phase-aware ledger and non-anticipating event-tree oracle

The preceding continuation made progress on explicit forecast distributions and demonstrated why historical stock-constrained sales cannot identify their tails. This continuation implements the broader timing/accounting oracle required before integrating those forecasts into purchasing. See the [phase-oracle contract](buying-behavior-v2-phase-oracle.md).

`phase_ledger.py` freezes phase-opening stock, basis and quotes; excludes same-phase new production from those sales; settles receipts at the declared event; capitalizes input/conversion costs; carries D1/D2 preference/fee transitions; and applies actual rent eligibility, unpaid liabilities and transfer-EMA timing. It checks posted earnings independently against equity and reconciles cash after every event. Reopening a completed company phase, billing twice, trading after rent within a tick and ending with an unsettled book are rejected. The production helper's inaccurate T1-before-procurement docstring was corrected to match code/canon; no production behavior changed.

`phase_oracle.py` enumerates full small allocations across a common observed event tree. Hidden future sales and terminal values cannot select a current action; later realized receipts/supply may legitimately change later actions. It canonicalizes supplier order, rejects scenario-label/calendar information channels, and derives frozen demand vectors through a mandatory current-information funding callback. An explicit node limit never returns an approximation. Exactness is conditional on that funding rule and the supplied external scenarios: it does not complete the endogenous joint value-model funding design.

Worked evidence is `phase-continuation-examples-v2.json`, with complete fixture inputs, event traces and source hashes. The previous report is preserved; v2 makes tick boundaries explicit in its rent example after stronger calendar guards were added. Complementary-buffer fixtures reproduce the $11/two-A/two-B case: certain arrival yields $1 return; 50% arrival selects no initial purchase; 75% arrival selects two A for expected return $0.25. A full optimal split A2+B6 remains admissible, incurs one fee and keeps its incumbent. The hidden-sale fixture rejects the clairvoyant $0.375 average in favor of the correct no-purchase value of zero.

Verification: `phase-continuation-final-regressions.log` passes 38 targeted tests in 3.209 seconds covering ledger/oracle, previous continuation counterexamples and reference settlement/refinery contracts. Nine rent threshold/cash/rate cases agree with executed rent settlement. `phase-ledger-book-parity.log` separately passes the added comparison against actual input-book settlement after intervening production. These are small-contract checks, not world-policy or performance validation. Existing SciPy/NumPy warning remains nonfatal; no dependencies changed.

Next required work: derive and test joint endogenous funded intentions for the same continuation objective, add self-supply/ownership and conditional future-supply contracts where required, run controlled forecast/information probes, and build a scalable candidate checked against the oracle. Runtime/checkpoint/UI integration, decision traces, fair-market/held-out/stress/performance evidence and rollout decisions remain required. The full goal remains active; no new economy run, live reset or adoption occurred in this continuation.

## Endogenous joint continuation funding

The previous turn made verified progress on phase timing, fees, rent and non-anticipating planning. This continuation adds a funding mode that uses that same conditional continuation objective rather than a fixture-specific callback. Current quote queries relax supplier stock, omit current fees and hold hypothetical incumbent identities fixed; future orders keep real fees/preferences and their own joint funding. Actual selection still enforces stock, budget, conversion, storage, lot and funded-fallback constraints. The [continuation-funding contract](buying-behavior-v2-continuation-funding.md) states this candidate boundary and its limitations.

A structural counterexample rejected the first reference-only decomposition. Fixing other inputs to their incumbent quotes funded only one A even when a cheap B quote made two kits affordable. The source is preserved in `continuation-funding-reference-v1.py` and the rejected mode remains executable for comparison. The default continuation candidate now fixes only the queried input's quote and retains all discovered quotes for other inputs. In the worked $5 case, it buys two kits for $5 return rather than one for $2.50. This is not a change to the existing replenishment treatment.

The exact planner also exposes a cash-truncation fee incentive. With $7, A at $1 now, B later at incumbent $5/outside $1, $0.25 conversion and a $3 fee, buying two A leaves insufficient cash to turn the incumbent's goods into output. Its own-quote funded intention becomes zero and the fee is waived. One A remains unused, but return is $6.75 versus $4.75 for one A with the fee. With fees removed the model buys one A and returns $7.75. This is an unresolved strategic consequence, not an endorsed behavior or a reason to silently change accepted D1/D2 or remove unmatched buffers.

Two failed hand expectations are preserved: the heterogeneous-lot optimum splits (two cheap units plus one higher-price unit) rather than buying a four-unit lot; and a zero-conversion fee fixture encountered the retained epsilon cash guard at exactly zero cash. Normalized world configuration requires positive conversion, so the final fee counterexample explicitly uses $0.25 and does not rely on that synthetic edge. No production parameter was changed.

`continuation-funding-positive-conversion-tests.log` passes 42 targeted tests in 0.613 seconds. Coverage includes 100 independent exhaustive two-input cases, coupled conversion cash, old basis/finished stock, quote flexibility, hidden demand, conditional supply, real future fees/rent, receipt timing, lots and explicit node-limit failure. The old explicit-callback oracle remains compatible.

`20261012-continuation-funding-examples` preserves complete fixtures, outcomes, source hashes and a self-contained source package. Its archived code was replayed outside the repository working directory and produced byte-identical results (`reproduction-proof.json`). No full-world buying treatment or live adoption was run. Remaining work includes a justified response to the fee incentive, controlled information/forecast probes, conditional/self-supply behavior, scalable execution and every outstanding runtime/UI/performance/economic/rollout gate. The full implementation goal remains active.


## Fee-boundary sensitivity and an explicit alternative

The prior turn made progress by deriving joint intentions and exposing a strategic fee consequence. This continuation implements an opt-in transfer-neutral funding comparator: only its hypothetical intention calculation removes future switching transfers; actual selection/settlement still charges and pays them under D1/D2. Existing finance-aware and callback behavior remain covered by regressions. See the [fee-incentive study](buying-behavior-v2-fee-incentives.md).

The frozen `fee-boundary-spec.json` defines 100 cash/fee/input-limit microcases per model and five probabilities for a useful transfer-financed buffer. Finance-aware continuation buys extra inputs versus its matched zero-fee control in 14 cases; transfer-neutral funding does so in none. A separate direct cash/payment calculation matches every one of those 100 choices and returns. The alternative nevertheless misses useful contingent production: at a 50% chance of a later $2 fee receipt, finance-aware planning buys a buffer for $5.375 expected return while the alternative buys none for $5.00. It cannot be promoted as a general fix merely because it suppresses the first incentive.

`20261012-fee-boundary-sensitivity-v2` preserves the specification, outcomes, code hashes and self-contained source. It adds explicit tick boundaries between early and later procurement; every scored choice, return and account outcome matches the preserved original study. Both archives reproduce byte-identical results outside the repository directory. These are deliberately threshold-focused small cases, not incidence estimates, held-out experiments or whole-economy evidence.

`fee-boundary-final-tests.log` passes 38 targeted tests in 2.747 seconds, including all previous joint-funding/oracle/ledger checks and the independent grid. After the explicit calendar addition, `fee-boundary-calendar-tests.log` passes four targeted tests in 2.099 seconds. No production default or live run changed.

A focused D4 preference question was sent to the user: whether fee-avoiding inventory accumulation is intrinsically disqualifying or should be judged by its economic effects. D1/D2 were not reopened. No answer is assumed and no model was adopted. Independent verification, bounded decision traces and observability work can continue while that choice remains open; all runtime/UI/scaling/long-run and rollout gates remain required. The full implementation goal stays active.

## Bounded industrial decision reconstruction

The preceding goal turn only restated already-recorded D1/D2 decisions and made no implementation progress. This continuation implements optional bounded samples at the shared reference/compiled pre-commit validation boundary. The [trace contract](buying-behavior-v2-decision-traces.md) specifies deterministic sampling, complete coupled input snapshots, stable identities, missing-callback semantics, bounds and reconstruction. Default tracing is off. The isolated runner saves versioned per-tick traces and separates export timing from kernel capture.

The reference verifier reconstructs intentions and allocation from each snapshot and independently checks D1/D2, remaining requests, lots, stock, cash and storage. Sixteen targeted tests pass (`decision-trace-tests.log`, 73.358 seconds), covering instrumented reference/compiled equality against an uninstrumented control, corrupted snapshots, split preference/fee semantics, missing callbacks, zero offers, and existing settlement/refinery contracts.

Full-population run `20261012-industrial-traces-fullpop-137` (seed 137, ticks 1–30, eight samples per industrial phase) passes conservation and exact comparison of all 211 previously recorded arrays, checkpoint JSON, schemas/config and tick invariants with the preserved uninstrumented run. All 720 sample identities verify; 484 captured decisions reconstruct, and 236 explicitly unobserved callbacks remain distinct from zero orders. Source hashes, reconstruction proof and run comparison are preserved.

A separate three-pair full-population screen reports 1.29–2.74% median kernel overhead and 0.28–0.30 ms JSON encoding time with exact economic-state equality every tick. Detailed trace arrays use 1,056,384 bytes. This does not establish mature-state latency or total process-memory/adoption gates. No production buying policy or live run was changed.

The pending D4 fee-incentive question remains unanswered; no preference is assumed. Distributor traces, rendered inspection, production runtime integration, the unresolved industrial value/forecast contracts, scalable execution, long-run/stress/held-out economic evidence and rollout gates remain required. The full implementation goal remains active.

Additional verification: `decision-trace-continuation-tests.log` passes four tests in 17.461 seconds after extending the connected case with sampled multi-line firms and a checkpoint reload between ticks. The recreated engine produces identical subsequent samples, decisions and world state. `decision-trace-baseline-tests.log` passes eight unchanged baseline fallback, stock-access and distributor-preference tests in 5.681 seconds. Modified-document links and `git diff --check` pass. The existing SciPy/NumPy warning remains nonfatal. All experiments and test processes started in this continuation have completed.

## Distributor samples and reference precision

The previous goal turn made verified progress by adding reconstructible industrial samples. This continuation extends optional sampling to Distributor clearing, including explicit inactive, zero-potential and captured states. Captured empty-stock attempts remain distinct from fee/valuation rejection and from no-offer decisions. See the [Distributor trace contract](buying-behavior-v2-retail-traces.md). All observations are bounded, versioned and default-off; no Distributor cash constraint or new quantity rule is introduced.

The first controlled test unintentionally sampled products absent from its reduced manufacturer fleet. Those failed expectations are preserved; the corrected purchase fixture explicitly routes to an existing product and retains a separate absent-product case. That fixture then exposed a genuine Python reference precision mismatch: NumPy float32 scalar promotion affected latent/inverse-curve calculations relative to compiled double arithmetic. Explicit double conversion aligns the reference path. Tests do not relax allocation, fee, preference, request or world-state equality; only diagnostic surplus has a 1e-12 relative floating-point tolerance.

`retail-trace-final-tests.log` passes nine targeted tests in 42.771 seconds across connected Distributor traces, the independent exhaustive retail solver, and industrial traces/checkpoint continuation. Earlier failed fixture/precision logs remain preserved. The full-population `20261012-all-buyer-traces-fullpop-137` run (seed 137, ticks 1–30, sample 32) passes invariants and exact comparison of all 211 recorded arrays, checkpoint data, schemas/config and tick invariants against the original uninstrumented comparison. This directly verifies that the compiled trajectory is unchanged by the precision correction and trace hooks for that window.

All trace files reconstruct: 1,926 captured industrial plans, 954 unobserved industrial callbacks, 111 Distributor decisions and 849 inactive Distributors. Zero potential is exercised by the controlled test, not observed in this run. The first reconstruction proof had an incorrect textual reference to the industrial-only comparison proof; it is preserved as `trace-reconstruction-proof-v1.json`, with the corrected proof and verifier pointing to `all-buyer-trace-world-proof.json`.

Three separate alternating-order full-population timing pairs show combined sample-32 kernel overhead of 2.86%, 5.32% and 5.17%; JSON encoding takes 1.08–1.28 ms median, excluding disk writes. Trace buffer/lookup arrays use 9,432,320 bytes, excluding small identity/metadata objects and export temporaries. These startup measurements do not establish total process memory, mature-state tail latency or the overall policy performance budget.

Remaining work includes rendered inspection and production runtime/projection integration, resolving the industrial value/forecast contract and pending D4 incentive question, scalable value-model execution, long-run/held-out/stress/fairness evidence, and rollout gates. The full implementation goal stays active. No live process was reset and no production buying policy was activated.

Final verification: four existing full-world retail tests pass in `retail-trace-world-regressions.log` (2.504 seconds), covering actual postings, split-order fees/preferences and policy-checked checkpoint continuation. Modified-document links and `git diff --check` pass. The pre-existing SciPy/NumPy compatibility warning remains nonfatal; dependencies were not changed. All test, simulation and benchmark sessions started in this continuation have completed.

## Rendered recorded-data inspector

The preceding continuation made progress on Distributor traces and fixed the reference precision mismatch with preserved compiled-world parity. This continuation adds a standalone [recorded buying-decision inspector](buying-behavior-v2-inspector.md). Its builder validates completed windows and accounting gates and replays all captured decisions before writing an exclusive self-contained HTML artifact. It keeps whole-window industrial totals separate from deterministic samples and preserves missing-data states, units, stable IDs and source attribution.

The artifact `20261012-buying-inspector/verified.html` displays the existing full-population seed-137/ticks-1–30 recording: 120 phase documents, 3,840 samples and 2,037 captured plans. Actual browser inspection verified filters, pagination, empty results, inactive/unobserved explanations, purchases, stockout requests and desktop/narrow layouts. A mobile overflow was fixed. All 54 rendered aggregate rows match the recorded projection, including 30 undefined rates rendered as unavailable. Screenshots and `rendered-totals-proof.json` preserve the evidence.

File download observation timed out in the in-app browser; no successful file download is claimed. Export now also exposes full-precision JSON directly. The rendered export was verified to contain exactly the three captured T3 buyers at tick 30, without duplicating sibling trace documents. This limitation remains explicit. Two targeted Python report tests, JavaScript projection checks and syntax checks pass. No simulation was run or changed for this interface work.

The standalone inspector advances recorded-data observability; it does not complete live runtime/projection/control integration or the master plan. Industrial value/forecast decisions, scalable execution, long-run/held-out/stress/fairness validation, overall performance gates and rollout remain open. The D4 question is still unanswered; no answer is assumed. Goal remains active.

Final handoff: source archive and `build-and-ui-proof.json` are saved beside the report; modified documentation links and `git diff --check` pass. The read-only preview server remains intentionally available on `127.0.0.1:8879` (exec session 52291) for the delivered browser tab. It serves only the inspector artifact directory. All build/test processes completed; no simulation process was started. The temporary desktop viewport override was reset after responsive inspection.

## Profile-guided exact procurement shortcuts

The previous continuation delivered a rendered inspector with verified recorded data. This continuation returns to the unresolved performance gap. A warm tick-32–41 profile from the saved corrected-policy tick-30 checkpoint locates roughly two-thirds of time in manufacturing and 30% in retail clearing (`corrected-buying-warm-profile.*`). No live simulation was operated.

The compiled D3 replenishment path now reuses reference-funded quantities for exactly unchanged reference quotes and bypasses allocation search when no offered whole lot can be purchased. Funding/discovery measurements still run. The original one-offer fee-free hypothetical and sequential cash arithmetic make reference-quote reuse exact; no future-value-model identity-independence is assumed. Search-limit exceptions remain explicit, including zero-node requests with heterogeneous tied-price caps. See the [industrial contract](buying-behavior-v2-industrial-contract.md#exact-procurement-shortcuts).

Evidence is preserved in `20261012-procurement-shortcuts`. Forty-six source files were archived before editing. All 1,926 recorded industrial cases match every baseline result array/scalar; five alternating-order compiled microbenchmarks improve by 20.8–26.3%. This sample has only reference-priced offers and does not represent mature heterogeneous quotes. Twelve targeted tests pass in 58.946 seconds, including 1,000 reference comparisons, 400 exhaustive allocation cases, search-limit boundaries and multi-line worlds.

Three alternating-order full-population pairs resume the identical corrected checkpoint, warm tick 31 and measure ticks 32–41. Kernel median improves by 8.17–8.49%, with exact equality of all 168 world arrays, observation counters, supplier history, checked ledgers and runtime economic state every tick. Fresh recorded run `20261012-industrial-shortcuts-fullpop-137` additionally matches all 211 archived arrays/checkpoint/schema/invariant fields for ticks 1–30 and passes its accounting gate. No production default changed.

The relative budget still fails. A separate original-policy comparison uses the same frozen config, catalog and seed, with each policy's own trajectory to tick 30. Corrected/original median ratios are 3.72–3.78 and p95 ratios 3.67–3.86, above the master plan's 2×/2.5× thresholds. These are kernel-only startup screens, not mature-state, recording/UI or memory validation. The optimization is useful but does not establish a performance-gate pass.

The first microbenchmark report failed to serialize a NumPy integer after completing its comparisons/timings. Its incomplete report and script are retained; corrected serialization produces the complete proof. The intermediate candidate's reconstructed source hash matches the identity in that failed report. The final empty-lot guard also retains zero-node search failure for heterogeneous tied-price cases; a dedicated regression covers it. No golden economic evidence was regenerated to hide a difference.

Remaining work still includes the industrial objective/information contracts, scalable value-model execution, further manufacturing/retail cost reductions, live runtime/UI integration and long-run/stress/held-out/fairness/rollout gates. The unanswered D4 question is not treated as a decision. The full goal remains active.

Final verification: modified documentation links and `git diff --check` pass. Benchmark/test processes from this continuation are complete. The existing SciPy/NumPy warning remains nonfatal; no dependency changes were made. The earlier read-only inspector preview was not operated or replaced by this work.

## Exact retail valuation shortcut

D1 and D2 remain accepted as specified in the decision register. Stale wording calling the D2 fixture boundary proposed has been corrected; no new user choice is inferred. This continuation completes the retail performance work begun after the manufacturing profile: compute only the reachable marginal-value prefix, reuse identical-quote quantities within an order, and bypass an empty allocation search while preserving all request/reliability/exposure reporting. The [retail contract](buying-behavior-v2-retail-contract.md#reachable-value-optimization) records the reasoning and boundaries.

`20261012-retail-prefix-optimization` preserves independently archived pre-edit source and hashes. The initial randomized fixture failed before comparison because it assigned 40 active buyer values to a million-slot capacity array. The failed script/log are preserved; the corrected fixture slices active buyers explicitly. All 90 cases then match every world array, return value, observation, supplier history and sampled decision field exactly, covering empty/limited/ample stock, equal/unequal quotes, heterogeneous demand/elasticity and incumbent/fee combinations.

Ten targeted tests pass in 37.598 seconds (`targeted-tests.log`): the independent exhaustive retail solver, both world execution paths, actual postings, D1/D2 split behavior, checkpoint continuation and sampled traces. A new permanent regression verifies that empty/limited stock preserves the full own-quote request, latent potential, original preference, and actual fee/payment amounts.

Three alternating-order full-population timing pairs resume the same corrected checkpoint, warm tick 31 and measure ticks 32–41. Before/after medians are 453.51/427.20, 460.59/432.41 and 456.09/424.51 ms: 5.80%, 6.12% and 6.92% improvement. All 168 world arrays, checked ledgers, observations, supplier history and runtime economic state match each tick. Before/after p95 values are 523.92/473.90, 499.82/448.10 and 470.29/450.51 ms. The benchmark checks warm kernels only; it does not establish the original-policy relative budget, mature-state behavior, recording/UI overhead or memory gate.

Fresh full-population run `20261012-retail-prefix-fullpop-137` passes its accounting gate and exactly matches all 211 archived arrays, checkpoint JSON, schemas/config and tick invariants against `20261012-industrial-observed-fullpop-137` over ticks 1–30. Comparison proof, scripts, source identities and failed fixture evidence are preserved. Production defaults and live runs remain unchanged.

Remaining requirements include the industrial value/information contracts and pending D4 incentive question, scalable execution, overall performance validation, live runtime/UI integration, held-out/long-run/stress/fairness evidence and rollout gates. The full implementation goal remains active. All test and experiment processes started in this continuation completed; the earlier read-only inspector preview was not operated. The existing SciPy/NumPy compatibility warning remains nonfatal, with no dependency changes.

## Transaction-only forecast comparison

The previous turn made verified progress on retail execution cost. This continuation advances the industrial information contract instead of treating the temporary replenishment objective as the final model. Forecast version 2 adds explicit transaction-only feedback alongside the unchanged inquiry-informed candidate. Transaction-only publications exclude all inquiry arrays, use stocked phases as sales observations, preserve empty-stock missingness, and mark depletion at the wholesale-lot boundary. The [forecast contract](buying-behavior-v2-forecast-contract.md#transaction-only-feedback-comparison) states what cannot be inferred without inquiries.

The paired screen specification was saved before scoring in `20261012-forecast-feedback-proof`; original forecast and evaluator source were independently copied before editing. `20261012-forecast-feedback-screen-137` preserves the frozen specification, three source files and hashes, complete results and successful manifest. Both modes use the same historical calibration seed, seller sample and stock-conditional targets. All 18 inquiry score rows and sample identities exactly reproduce the archived earlier screen; no historical result was replaced.

Transaction-only local MAE is lower in this sample for both tail profiles: retail 4.997/4.815 versus inquiry 24.451/12.244, C3 564.981/564.981 versus 710.187/612.235, and C4 257.237/215.983 versus 909.439/456.510 items per seller-phase. These are descriptive results on 244, 820 and 451 scored observations respectively, not economic or causal improvements. Substantial bias and excluded empty-stock observations remain. The feedback rule changes historical inclusion as well as censoring diagnostics. No parameter or information regime is adopted from this calibration screen.

Seventeen forecast/evaluator tests pass (`tests.log`), including physical removal of inquiry fields, zero-sales and empty-stock distinctions, wholesale lots, lag and history reload, paired scoring and invalid feedback rejection. Forecast diagnostics identify version and feedback; seller-history schema is unchanged. No world engine or production defaults changed, and no live run was operated. D1/D2 remain accepted; the separate D4 incentive question remains unanswered.

Remaining work includes controlled availability/quote probes, conditional supply and self-supply scenarios, scalable coupled planning, actual world consumption of forecasts, live runtime/UI integration, full economic/performance/fairness and rollout gates. The full implementation goal stays active.

## Shared sales opportunities in the continuation oracle

The preceding turn made progress by adding and verifying transaction-only forecasts. This continuation addresses a separate obstacle to consuming forecasts in coupled company planning: independent per-line sales limits can count one product's demand twice. The new explicit `SharedSettleBook` scenario event groups interchangeable outputs and subtracts previous group sales from each line's whole own-quote demand. It preserves frozen stock/quotes/basis, accounting, future-information boundaries and the accepted actual fee contract. Existing independent-demand events retain their semantics.

A two-route hand case changes from two purchased inputs/$3.50 return under independent sales opportunities to one input/$1.75 return under a shared one-unit opportunity. With existing finished stock covering that opportunity, the planner buys no additional input. Shared demand is supplied jointly across lines; this implementation does not infer independence or grant knowledge of future realizations. It remains an explicit allocation assumption, not actual world search/loyalty clearing or a calibrated forecast.

Forty-four targeted shared-sales, phase-ledger, phase-oracle, continuation-funding and transfer-neutral tests pass in 2.705 seconds. Tests cover hidden future demand, old stock, frozen unequal quotes, A2+B6 fallback, original-basis COGS, group validity, separate groups and neutral-funding fee removal with actual fee posting. `20261012-shared-sales` preserves before-edit source and tests; its examples archive preserves full scenario inputs, results and self-contained sources/hashes. A replay outside the repository is byte-identical. No production default or live run changed; the existing SciPy/NumPy warning remains nonfatal.

The full goal remains active. Joint forecasts still need an explicit calibrated scenario generator and price/stock probes; residual supplier depletion, self-supply, scalable coupled optimization, world/runtime/UI integration and all remaining economic/performance/fairness/rollout gates are unresolved. The unanswered D4 question is not treated as a decision.

## Controlled actual-retail stock and quote probes

The preceding turn added shared-demand settlement with verified coupled purchasing effects. This continuation tests the forecast candidates against controlled actual retail clearing before connecting them to industrial purchasing. `forecast_probe.py` records paired histories and target outcomes under explicitly fixed buyer parameters, stock treatments and quotes. It computes forecasts before target outcomes, validates fixture storage and reconciles actual stock, cash, revenue and COGS per phase. It does not run a whole economy or operate a live process.

The frozen specification in `20261012-forecast-probe-proof` uses historical seeds 137/271/811, 500 buyers, eight training phases, empty/limited/ample focal stock and three target quotes. The two existing parameter profiles are unchanged. `20261012-forecast-probes-137-271-811` preserves 27 target phases, all forecasts/diagnostics, nine history archives/configurations, full source hashes/archive and a complete manifest. Independent cheapest-offer/rounded-quantity calculations match every target; target outcomes are identical across training histories under paired target conditions.

The evidence changes the next action: the current empirical forecast is not ready for world industrial use. With ample-stock training at $10, both feedback modes predict 2,500 focal sales at $20, while actual sales are zero because rivals remain at $12/$14. At $5, seed-137 actual sales are 6,669 versus a 10,000 prediction. After empty-stock training, transaction-only forecasts revert to the arbitrary cold-start prior. Neither lower historical error nor one coincidentally accurate half-tail result establishes a suitable demand model. Competitive price/share response, re-entry and joint scenarios must be addressed explicitly; no parameter is tuned or adopted here.

Nineteen targeted forecast/probe/evaluator tests pass in 3.552 seconds, including actual reference/compiled clearing agreement, stock limits, target pairing and observation lag. An initial expectation for the market forecast omitted its mean-quote adjustment; the failed test log is preserved, and the corrected independent expectation includes that factor. The initial specification is also preserved before adding explicit fixture storage. The specification used for the study was saved before scoring. `verification.json` records the independent 27-phase check. Existing SciPy/NumPy warnings remain nonfatal; dependencies and production defaults are unchanged.

The full implementation goal remains active. These controlled probes advance model rejection/requirements, not industrial-policy adoption. Remaining work includes a suitable joint forecast and supply model, scalable coupled planning, runtime/UI integration and the full economic, performance, fairness and rollout gates. The D4 incentive question remains unanswered; no decision is inferred.

## Persistent supplier stock in the small planner

The preceding turn produced controlled evidence against promoting the current empirical forecast. This continuation advances another prerequisite for coupled industrial planning: conditional supplier inventory after the company's own purchases. The event-tree oracle now supports an explicit persistent-arrival mode, subtracting actual purchases from later appearances of each supplier/material and validating nondecreasing cumulative supply totals. The legacy independent-snapshot mode retains its old semantics and is identified in results.

Stock-relaxed funding treats extra hypothetical stock as current additions, not as early use of a future arrival. Only real stock consumed is deducted from future totals. Later actual fee eligibility and discovery see remaining stock. Future arrivals stay hidden until their observation phase; candidate branches do not mutate caller scenarios. The [supply contract](buying-behavior-v2-phase-oracle.md#persistent-supplier-inventory-and-explicit-arrivals) states these assumptions and the remaining outside-withdrawal/self-supply limitations.

Thirty-six targeted oracle, continuation-funding, shared-sales and transfer-neutral tests pass in 2.535 seconds. New checks include 18 independent two-action enumeration cases, one item bought only once without replenishment, explicit replenishment, incumbent-depletion fee waivers, hidden arrival states, hypothetical-stock boundaries and invalid totals. `20261012-persistent-supply` preserves before-edit source, test logs and complete reproducible examples. The no-arrival example returns $1.75, versus $2.50 under repeated independent stock snapshots; adding a later item restores $2.50. The archived report package reproduces byte-identical results outside the repository.

No production default, live run or D1/D2 decision changed. The full goal remains active. Competitive/joint forecasting, outside supply responses and self-supply, scalable optimization, actual world/runtime/UI integration and the outstanding economic/performance/fairness/rollout gates remain incomplete. The D4 incentive question remains unanswered.

## Authoritative ownership audit corrects speculative scope

The preceding turn implemented supplier-stock carry-over. This continuation inspected self-supply before adding new ledger mechanics and found that earlier open-work notes assumed unsupported ownership. The actual installation API restricts each company to its own sector, enforces capability and rejects duplicate product installations. The full authoritative 269-product catalog has 255 manufactured recipes and 160 manufactured-input edges; none is same-sector. Fourteen such edges are in the current 105-product selection, also all cross-sector.

`ownership_audit.py` records every edge and source identity. Three tests pass in 0.191 seconds: full/selected catalog agreement, detection of an intentionally changed same-sector dependency, and actual API rejection of cross-sector input ownership and duplicate products with a successful valid distinct-product installation. `20261012-ownership-scope` preserves result/source/catalog hashes, tests and byte-identical replay outside the repository.

This is a scope correction supported by code and exhaustive catalog evidence. No self-transfer mechanic should be introduced under current rules. The previously added shared-demand event is retained as a hypothetical scenario utility; duplicate same-product company lines are not evidence of a current defect. The master plan and current contracts now distinguish that hypothetical capability from required supported ownership. Historical progress entries remain as history, superseded by this finding.

The goal remains active with its original supported scope: coupled distinct-product multiple-line planning, repeated/shared inputs, cash/storage/phase timing, competitive joint forecasts, scalable execution, runtime/UI integration and full economic/performance/fairness/rollout validation. These remain required. No production rule, live run or catalog changed. The D4 incentive question remains unanswered.

## First-year corrected-mechanics evidence

The preceding continuation corrected unsupported ownership assumptions with exhaustive catalog evidence. This continuation fills the combined-mechanics observation gap beyond tick 30. A specification was saved before the full-population seed-137/ticks-1–360 run `20261012-corrected-year-137`. The matching original-policy baseline remains independently preserved. Configs, catalog identities, initial accounts and complete recording windows match; product totals reconcile against separately recorded company accounts.

All invariants pass and there are no price guardrail contacts. Corrected retail units are 99.8567% of the original baseline for the year and 99.9218% for the final 90 ticks. No previously active product has zero sales in either comparison window; negative annual-earner shares are zero for every reported producer tier/route in both runs. Manufacturer earnings nevertheless decline 5.1106%, refinery earnings rise 13.2227% and extractor earnings decline 0.4851%. Combined-treatment attribution remains unresolved; these results do not guarantee healthy mature companies or acceptable generation-scale trade.

The performance gap remains explicit: corrected median/p95 522.71/552.55 ms versus historical baseline 124.96/145.12 ms, or 4.18×/3.81×. The runs are not paired timing trials, but the corrected observed median also exceeds the 500 ms ceiling. No performance pass is claimed. The [industrial contract](buying-behavior-v2-industrial-contract.md#first-year-full-population-mechanics-screen) includes tier/route sold-unit and posted-earnings totals with company denominators and interpretation limits.

`20261012-corrected-year-screen` preserves the preregistered specification, process log, comparison script, detailed financial/unit distributions, ratio definitions and source-linked verification. Analysis replay is byte-identical. The run preserves its source archive, final checkpoint, per-period product/company records and procurement observations. The simulation process completed normally; no live service was reset or changed. The existing SciPy/NumPy warning is nonfatal. Documentation links and whitespace checks pass.

The full goal remains active. This is historical calibration-year evidence for the corrected replenishment comparator, not completion of D3–D6, the price-sensitive industrial policy, held-out generations, stress/recovery/fairness, live integration or rollout gates. The D4 incentive question remains unanswered.

## Year-end supplier-discovery optimization

The previous turn completed the first-year combined-mechanics comparison and confirmed its performance failure. This continuation profiles the saved year-end state and makes a verified behavior-preserving discovery optimization. The profile locates about 69% of warm kernel time in manufacturing and 28% in retail. A 2,049-decision bounded industrial sample contains no all-offers-unaffordable order; this evidence does not support prioritizing an empty-wallet shortcut. Most sampled manufacturing decisions instead face heterogeneous quotes. Tracing leaves all economic arrays and observed counters unchanged in the compared continuation.

Supplier discovery now uses an in-place insertion sort for its bounded selected IDs. RNG draws, eligible suppliers, incumbent handling, ascending-ID order and policy semantics are unchanged. `20261012-discovery-sort` preserves independently archived pre-edit source, the final source, hashes and comparisons. All 4,500 discovery cases match the archived compiled implementation exactly in current reference and compiled paths. Eight connected retail/industrial tests pass in 58.673 seconds, and the strengthened ordering check passes separately in 0.200 seconds.

Three alternating-order full-population comparisons warm tick 361 and measure ticks 362–371 from the same corrected checkpoint. Median kernel time improves by 13.33–14.20%, from 532.66–547.46 ms to 461.69–473.01 ms. All 168 world arrays, checked ledgers, histories, observations and runtime state match each tick. Details and p95 values are in the [industrial contract](buying-behavior-v2-industrial-contract.md#year-end-profiling-and-exact-discovery-sort). No relative-to-original, memory or full runtime/UI gate pass is claimed.

`20261012-year-end-profile` retains the profile, checkpoint hashes, sample data and state-preservation proof. The first profile failed because its filename shadowed the standard profiling module; the failed source/log are preserved and the renamed script completed. All processes launched in this continuation finished. The pre-existing SciPy/NumPy warning remains nonfatal; dependencies, production defaults and live services were unchanged.

The full goal remains active. Competitive/joint forecasting, scalable coupled industrial value planning, production runtime/UI integration and the outstanding long-run/held-out/stress/fairness/performance/rollout gates remain required. D4 remains unanswered; no answer is inferred.

## Demand-informed replenishment comparator

The previous turn improved year-end execution while preserving state. This continuation implements the master plan's missing explicitly labeled demand-informed replenishment comparator. It calculates forecast residual sales after existing finished stock within each outcome, rounds up to production batches, aggregates shared/repeated recipe inputs across installed lines and clips to existing slots. Existing coupled replenishment funding, lots, actual production and D1/D2 settlement are retained. This is a small reference comparator, not a new production policy or a willingness-to-pay model.

The comparison preserves known failures instead of hiding them: forecast targets can spend all conversion liquidity, favor cheap isolated complements under scarce cash, buy inventory blocked by historical basis, or omit a valuable future buffer. It matches the coupled scenario-return choice for the one-sale weak-demand fixture. Wholesale targets smaller than a lot remain unfilled under the retained rule. A high input price still permits an affordable target purchase even when the production gate blocks it, demonstrating why demand targets alone are not the required industrial solution.

Fifteen targeted tests pass in 1.804 seconds, including multiple lines/repeated inputs, yield rounding, uncertain demand with old finished stock, zero demand, pricing/production failures, wholesale boundaries and invalid forecasts. `20261012-demand-target-comparator` preserves initial/final test logs and complete four-policy/five-case reports, with source archives and all manifest hashes checked. Stronger input validation leaves the five report outcomes byte-identical. The [value-model contract](buying-behavior-v2-value-model.md#implemented-demand-informed-replenishment-comparator) records equations, scoring semantics and limitations.

No production default or live run changed; no forecast or target parameters were adopted. The full goal remains active. Required next work remains suitable competitive/joint forecasting, scalable coupled expected-return execution, world/runtime/UI integration and the outstanding economic/performance/fairness/rollout gates. D4 remains unanswered and is not inferred from these comparator results.

## Combined verification and observed-history correction

The preceding turn implemented the missing demand-target comparator. This continuation ran all 27 `test_buying_v2*.py` modules together: 161 tests passed in 121.369 seconds at the preserved source identity. That is the buying-v2 subset, not the full repository suite. Source hashes remained unchanged throughout that run.

An additional analytical counterexample then exposed a gap absent from those tests: the small event-tree planner merged paths with identical current balances but different observed sales timing. Because that timing predicts future demand in the supplied fixture, remembering it supports an expected $2.375 return; the old planner returned $2.00. The original source, executable case and output are preserved in `20261012-combined-v2-verification`.

The oracle now groups by remembered observable history as well as current state/offers. It records inspected purchase terms even without a transaction and retains actual own outcomes, while excluding unobserved settlement demand and funding diagnostic values. This preserves access to legitimate past signals without revealing hidden future or censored demand. New regressions cover converged balances, inspected quotes, and empty-stock hidden demand under both ordinary and shared sales settlement.

Fifty-three relevant post-fix tests pass in 2.940 seconds, including existing continuation funding, persistent stock, shared sales and transfer-neutral cases. The archived corrected standalone source reproduces the repaired counterexample byte-identically outside the repository. The earlier 161-test result is explicitly pre-fix evidence; no post-fix full-repository claim is made. See the [information-history contract](buying-behavior-v2-phase-oracle.md#remembered-information-after-current-states-converge).

No production policy, live service or model parameter changed. The full goal remains active. Calibrated competitive/joint forecasts, scalable industrial expected-return execution, runtime/UI integration and the remaining economic/performance/fairness/rollout gates are incomplete. The D4 question remains unanswered. All test/replay processes launched here completed; the existing SciPy/NumPy warning remains nonfatal.

## Explicit joint forecast construction

The small planner can now compare independent and common-quantile demand scenarios across distinct owned products without an implicit independence default. Both constructions retain the supplied marginal distributions; scenario budgets and floating-point loss fail explicitly. The event-calendar helper exposes sales only at settlement, allowing later purchases to react to actual receipts.

An independent analytical financing example has identical $2 expected initial receipts under both assumptions but total expected incremental cash of $2.375 versus $2.25. The difference comes from the probability of funding a later profitable batch. Twenty-four targeted tests pass in 0.050 seconds; source archives, hashes, coupling tables and initial/final logs are preserved in `20261012-joint-forecast`. See the [joint forecast contract](buying-behavior-v2-forecast-contract.md#explicit-joint-forecast-assumptions) for assumptions and caller obligations.

D1 and D2 remain accepted exactly as recorded: split fills retain the incumbent unless one supplier alone fills its whole funded own-quote demand; qualifying outside delivery incurs one fee for the product order. No production default or live run changed. The full goal remains active: calibrated competitive and temporal forecasts, scalable coupled industrial planning, runtime/UI integration and economic/performance/fairness/rollout gates remain incomplete. D4 remains unanswered.

## Competitive price-rank candidate and retained failures

The previous turn supplied explicit joint dependence scenarios. This continuation implements a market-publication comparator that matches fully informed, unconstrained historical product books by supplier count and relative price rank, then selects the nearest observed quote. Rival quotes persist from the latest publication; peer exchangeability and quote elasticity are explicit assumptions. Unsupported or censored markets use a caller-supplied fallback and report that fact.

Against the 27 previously examined controlled targets, ample-training MAE falls from 1,942.44 to 1,109.11 items because the $20 seller correctly predicts zero against cheaper rivals. Large price cuts remain overpredicted, while empty/limited training still falls back and retains its failures. This is partial evidence for a competitive feature, not an adopted estimator or a passing forecast gate. The [forecast contract](buying-behavior-v2-forecast-contract.md#competitive-peer-rank-comparator) states all assumptions, test scope and retained counterexamples.

Twenty-seven targeted tests pass; the initial floating-point assertion failure is preserved. The evaluator replays byte-identically with verified source/input hashes in `20261012-competitive-peer-forecast`. No production or live-state change occurred. The full goal remains active: suitable forecasting, scalable coupled expected-return execution, runtime/UI integration and all remaining long-run, held-out, stress, fairness, performance and rollout gates are still required. D4 remains unanswered.

## Exact scalar funding optimization

The preceding turn added a competitive forecast comparator and documented its retained failures. This continuation advances the independent performance gate. Nonbinding-storage hypothetical quote funding now computes only the queried material's quantity from the exact preceding offer traversal, preserving reverse-index price ties, sequential cash subtraction and lots. Binding storage retains the prior solver.

Ten thousand archived-baseline cases agree in Python and compiled execution. Six targeted funding tests pass, including existing independent allocation/reference checks and new explicit cash-boundary/tie cases. Three full-population alternating-order continuations preserve all 168 arrays and checked ledgers, histories, observations and runtime state. Warm median ticks improve by 3.49–4.67%, from 453.24–457.46 ms to 436.12–437.44 ms. Source, checkpoint hashes and evidence are preserved in `20261012-scalar-funding`; see the [industrial contract](buying-behavior-v2-industrial-contract.md#scalar-funding-extraction-without-changed-decisions).

All launched test/benchmark processes completed. No live service or production default changed. The full goal remains active: forecasting and scalable coupled expected-return planning remain incomplete, as do production integration and the remaining economic, held-out, stress, fairness, overall performance and rollout gates. D4 remains unanswered.

## Isolated preference qualification comparison

The last turn improved funding runtime with exact parity. This continuation begins mechanism attribution using two full-population 30-tick historical-seed runs. The accepted whole-demand rule and a last-positive-industrial-delivery control differ only in the T1/T2 preference conditions; discovery, fees, funding, retail and production are fixed. An exact source audit verifies the two substitutions, and all first-tick world arrays agree except industrial preference entries.

Both treatments pass conservation, cash and storage checks. Whole-demand qualification yields 178 true industrial preference changes versus 11,927, and 3,909,425 retail units versus 3,804,044. No switching fees occur, so the experiment does not test fee-active preference dynamics. T2 total sold units and earnings move in the opposite direction from final retail units; the [industrial contract](buying-behavior-v2-industrial-contract.md#isolated-industrial-preference-rule-startup-control) reports every tier/route, denominators and interpretation limits rather than equating retail improvement with universal company benefit.

`20261012-preference-ablation` preserves source/configuration identity, original and control packages, actual records, verified first-tick differences and byte-identical analysis replay. All processes completed. This does not explain the annual combined-treatment result or complete mechanism attribution: mature windows, discovery/fee/partial-eligibility controls and interactions remain required. The full implementation goal remains active, including the unresolved forecast/planner, integration and adoption gates. D1/D2 remain accepted and D4 remains unanswered.

## Year-end preference control with active fees

The previous turn's startup preference comparison made progress but had no fee-bearing orders. This continuation repeats the isolated control from the identical saved corrected-policy tick-360 checkpoint through tick 390. Both treatments preserve all first-tick world arrays except manufacturer preferences; configurations and opening company accounts are identical, and the two source substitutions remain verified.

Both pass accounting, goods, cash and storage checks. Whole-demand versus partial qualification yields 224 versus 556 industrial fee-bearing orders, $1,440.01 versus $3,584.69 fees, and 4,047 versus 5,584 preference changes. Final retail units differ by only 421 out of roughly 48 million, reversing the much larger startup direction. The whole-demand treatment has more stock-limited delivery legs; the [industrial contract](buying-behavior-v2-industrial-contract.md#preference-qualification-with-year-end-fees-active) reports all tiers/routes and carefully distinguishes legs, replenishment shortfall and final demand.

`20261012-preference-yearend` preserves the verified source/archive, checkpoint hashes, explicitly labeled ticks 361–390, reconciled producer accounts/industrial fees and byte-identical analysis replay. All processes completed. D1 is not reopened. Remaining work includes the other mechanism controls and interactions, suitable forecasts/scalable coupled planning, integration and every outstanding long-run, held-out, stress, fairness, performance and rollout gate. The full goal remains active; D4 remains unanswered.

## Forecast values connected to coupled allocation

The preceding turn completed the fee-active preference control. This continuation connects explicit forecasts to the exact industrial allocator through a one-closing-sales comparator. It constructs incremental expected sales plus residual finished-stock values after existing finished stock, without double counting, and preserves the solver's shared cash/input/space, split/lot, conversion and historical-cost constraints. Frozen funded caps are mandatory; the adapter does not resurrect the rejected reference-only funding decomposition or claim dynamic continuation support.

Thirty-two targeted tests pass, including 120 independent exhaustive shared-input/two-line scenario comparisons, price responsiveness, old-stock coverage, conversion liquidity, historical basis, forecast validation and explicit solver limits. Five complete examples and byte-identical replay are preserved with verified source hashes/archive in `20261012-forecast-allocation`. The [value-model contract](buying-behavior-v2-value-model.md#forecast-valued-coupled-allocation-adapter) gives equations, timing and caller obligations.

The full goal remains active. This is useful integration of the forecast and allocation components, but does not close suitable forecast calibration, endogenous continuation funding, scalable phase-aware planning, world/runtime/UI integration or economic/performance/fairness/rollout gates. All launched checks completed; production/live state is unchanged. D4 remains unanswered.

## Exact transition reuse in the phase-aware planner

The previous turn connected marginal forecasts to the closing-sales allocator. This continuation improves the phase-aware oracle's cost by caching only identical pure ledger transitions in a bounded per-solve cache. Full state/event/allocation keys preserve funding/fee distinctions; policies, posterior groups and remembered observations are not cached together. Enumeration budgets retain their exact meaning, and caller-visible trace mappings are isolated.

Fifty-five relevant tests pass, followed by two cache tests with a strengthened aliasing assertion. Six alternating-order analytical benchmarks preserve complete semantic outputs against independently archived source and improve median runtime by 24.2–36.5%. Source, tests and results are preserved in `20261012-transition-cache`; the [phase-oracle contract](buying-behavior-v2-phase-oracle.md#bounded-reuse-of-pure-ledger-transitions) records precise scope and memory limits.

All launched work completed. This is progress toward tractable continuation evaluation, not a population-scale solver or completion of the goal. Suitable forecasts, scalable phase-aware funding/planning, world/runtime/UI integration and remaining economic/performance/fairness/rollout gates stay open. Production/live state is unchanged; D4 remains unanswered.

## Exact pruning of cash/slot-infeasible baskets

The preceding turn added bounded pure-transition reuse. This continuation adds optional prefix pruning while retaining exhaustive search as the default comparison. Only mathematically necessary current cash and input-slot constraints eliminate branches; allocation order and the full remaining ledger/continuation checks are preserved. A separate explicit prefix-work budget prevents an incomplete search from returning a plan.

Twenty-three targeted tests pass, including 400 exact-order comparisons against independent Cartesian filtering, full endogenous-funding outcome parity, observed-history and persistent-supply cases. In a deliberately scarce-cash four-offer fixture, evaluated allocations fall from 14,641 to three with identical decisions/accounts/value; median runtime falls from 484.773 to 0.713 ms. This is an analytical best-use case, not a population performance claim. Evidence is preserved in `20261012-prefix-search` and described in the [phase-oracle contract](buying-behavior-v2-phase-oracle.md#optional-exact-prefix-pruning).

All checks completed; production/live state is unchanged. The full goal remains active. Affordable multi-phase state spaces, suitable forecasts, funding incentives, world/runtime/UI integration and remaining economic/performance/fairness/rollout gates are still incomplete. D4 remains unanswered.

## Phase-planner scaling gate remains failed

The preceding turn verified exact prefix pruning on a scarce-cash example. This continuation tests the missing affordable-basket and future-scenario dimensions with a frozen 32-row screen. Eighteen rows finish exactly and fourteen reach explicit budgets. A capacity-two, two-supplier, two-period case with endogenous funding fails in both search modes. Prefix pruning helps smaller cases but does not make the current event-tree implementation suitable for population execution.

Two analytical fixture tests pass; complete semantic results agree whenever both modes finish. The archived standard-library source runs outside the repository and reproduces all 32 outcomes and case inputs exactly, excluding elapsed timings. `20261012-phase-scaling` and its replay preserve the evidence. The [phase contract](buying-behavior-v2-phase-oracle.md#scaling-screen-oracle-remains-unsuitable-for-population-execution) and master plan now explicitly classify the current planner as a verification oracle and require a structurally different continuation search/representation before stage 6.

This is progress because the measured failure changes the implementation priority; it is not a completed scalability gate or an impossibility proof. All processes completed. Production/live state is unchanged. The full goal remains active, including suitable forecasts, scalable full-scope planning/funding, integration and all outstanding adoption gates. D4 remains unanswered.

## Conditional funding subproblems can be shared, but scale still fails

The previous turn established a concrete scalability failure. This continuation prototypes complete funding-query reuse keyed by full state and the weighted remaining scenario distribution, including physical supplier stock and fee-neutral mode. It defaults off and preserves the independent exhaustive reference. Common past histories are not mistaken for evidence of equal futures; different posterior scenarios remain distinct.

Thirty-seven targeted tests pass with full policy/trace parity, persistent stock/arrival coverage and observed-history counterexamples. The unchanged bounded screen still completes 18 of 32 rows and fails 14, so no scalability pass is claimed. A separate larger-budget case reduces allocation evaluations from 19,848 to 11,148 and funding solves from 995 to 410, with identical $6.50 value and tested trace parity. That demonstrates structural sharing but remains far from population execution. Details and evidence paths are in the [phase contract](buying-behavior-v2-phase-oracle.md#optional-reuse-of-complete-conditional-funding-queries).

All launched checks completed. The full goal remains active: search over distinct affordable states still needs a different bound/representation, alongside suitable forecasts, D4 resolution, production integration and outstanding validation/rollout gates. Production/live state is unchanged.

## Optimistic future-return envelope implemented separately

The previous turn established that sharing identical funding subproblems does not close scaling. This continuation implements a future-return envelope that can eventually eliminate distinct inferior branches. It relaxes future costs and production inputs, preserves open-book stock/quote timing, includes explicit future fee income, handles cash/arrears correctly and maximizes supplied terminal tables. It remains disconnected from pruning pending validation and numerical-boundary checks.

Eleven targeted tests pass, including exhaustive comparison for every feasible first basket in a two-period fixture, frozen-book timing, fees, arrears, nonmonotone terminal values and unsupported bounds. Complete examples and byte-identical replay are preserved in `20261012-continuation-bound`; the [phase contract](buying-behavior-v2-phase-oracle.md#first-optimistic-continuation-value-envelope) states the relaxation, numerical cushion and integration limits. The examples also expose substantial bound slack; no scalability improvement is claimed yet.

All checks completed. The full goal remains active: the envelope still needs safe integration and evidence of useful pruning, alongside suitable forecasts, D4 resolution, full world/runtime/UI implementation and outstanding adoption gates. Production/live state is unchanged.

## Exact shadow audit of continuation envelopes

The previous turn introduced an optimistic bound separately from search. This continuation adds an optional shadow audit that checks every evaluated candidate envelope against its exact continuation while preserving all decisions, traces and work counters. Thirteen targeted tests pass, including fee/supply modes and monetary-scale boundaries; no covered bound violation occurs.

The eight-row report identifies the limitation hidden by aggregate cut counts: the larger two-period case has 6,329 potentially prunable candidates, but only five have another purchase ahead. Most cuts therefore avoid only closing-ledger work. This evidence directs the next bound toward conservative future-production costs and inventory reuse constraints rather than prematurely enabling the loose envelope. The [phase contract](buying-behavior-v2-phase-oracle.md#shadow-audit-measures-bound-safety-and-useful-depth) records the counts and limits; complete inputs, source and byte-identical replay are in `20261012-bound-audit`.

All checks completed; no production/live-state change occurred. The goal remains active with its full scope: scalable continuation search, suitable forecasting, D4 resolution, world/runtime/UI integration and outstanding economic/performance/fairness/rollout gates remain incomplete.

## Future production costs tighten the continuation envelope

The previous shadow audit showed that the gross envelope mostly rejected terminal work. This continuation adds a reference fractional cost relaxation with single-use existing finished stock, optimistic cheapest future input prices, conversion costs and independent access to shared owned inputs. Exact rational breakpoints prevent rounding the internal relaxed optimization downward; the final numerical cushion remains explicit. It is used only by the optional shadow audit, not actual pruning.

Sixty shared-input/multiple-line comparisons, full policy/trace audits and monetary-scale tests pass. In the larger two-period case, potentially rejectable candidates with further purchasing rise from five to 69 and maximum bound slack halves from roughly $9 to $4.50. Complete inputs and byte-identical replay are preserved in `20261012-cost-envelope`. The [phase contract](buying-behavior-v2-phase-oracle.md#cost-aware-envelope-improves-early-decision-discrimination) explains the relaxation and exact verification scope.

All checks completed. This supports the next optional pruning experiment but is not a speed or scalability pass. The full goal remains active, including suitable forecasts, D4 resolution, full-scope scalable planning/funding, world/runtime/UI integration and all remaining adoption gates. Production/live state is unchanged.

## Continuation pruning implemented and measured without a scalability pass

The previous turn tightened the cost-aware envelope. This continuation connects it to optional real pruning, guarded by full static calendar/offer checks and ordinary state-dependent ledger validation. Unavailable/overflowing bounds never prune, and arbitrary funding callbacks remain on the exhaustive reference path. The switch defaults off.

Forty-two targeted tests preserve complete policies/traces across funding/supply modes and monetary scales while rejecting malformed future contracts. The unchanged 32-row scaling screen still has 18 exact outcomes and 14 work limits. The capacity-four one-period prefix case still enumerates 750 leaves despite skipping 656 terminal continuations: bounding after a full allocation is too late to eliminate that enumeration cost. The [phase contract](buying-behavior-v2-phase-oracle.md#optional-continuation-pruning-correct-in-tests-scaling-gate-still-fails) documents this failed performance result and prioritizes allocation-box pruning or verified compiled final-decision specialization next.

Evidence is preserved in `20261012-continuation-pruning` and `20261012-phase-scaling-pruned`; an outside-repository archived-source replay reproduces all 32 semantic rows exactly, excluding elapsed timing. All launched checks completed. The full goal remains active with no production/live-state change; scalable full-scope planning, suitable forecasts, D4 resolution, integration and outstanding adoption gates remain required.

## Closing-allocation reduction implemented; compiled fee summation corrected

The preceding goal turn only reconfirmed accepted decisions, so it added no implementation progress. This continuation implements an experimental final-purchase adapter to the existing compiled basket solver and verifies it against the full event ledger. It retains split suppliers, shared inputs, multiple installed lines and explicit correlated scenarios. Unsupported calendars remain on the general planner; the adapter is not yet enabled in that planner.

A targeted boundary audit exposed and fixed a compiled cash-feasibility defect: adding fees directly to goods rejected an exactly affordable $0.35 basket. Both compiled evaluation and the box bound now use the ledger's goods-plus-summed-fees order. Forty-one targeted tests pass, including 160 random two-line allocation/settlement comparisons and the formerly failing exact-cash regression. An eight-unit/three-supplier closing fixture obtains the analytical $44 return in about 0.315 ms warm median while the exhaustive event tree reaches its unchanged 4,000-node budget. This is frozen-funding adapter evidence, not a pass for general continuation or population performance.

The [phase contract](buying-behavior-v2-phase-oracle.md#compiled-closing-allocation-adapter-and-an-exact-cash-counterexample) records equations, scope, numerical limitations and verification. `20261012-closing-allocation` preserves complete inputs, source, before-fix solver files, tests and archived-source replay evidence. Next work is staged-versus-combined numerical boundary validation and safe planner substitution, then the unchanged endogenous/multi-period scaling screen. The full goal remains active: suitable forecasting, D4 resolution, scalable complete planning/funding, world/runtime/UI integration and outstanding economic/performance/fairness/rollout gates remain incomplete. No production or live-world activation occurred.

## Storage boundary fixes and endogenous closing-solver shadow audit

The preceding turn made implementation progress with the closing adapter and fee-summation correction. This continuation found and fixed two independent compiled/reference storage-reduction defects, preserving the existing model: purchase space now aggregates by material, and production applies the summed net space change. Both captured regressions failed before the fixes.

A staged-versus-combined fractional-storage counterexample returns $9 in the full ledger but zero through the unguarded adapter, even though replaying its chosen zero basket passes. Adapter eligibility now rejects fractional or excessively large spatial sums so the general planner preserves that behavior. An optional shadow audit then compares eligible compiled candidates with actual exhaustive conditional solves, including endogenous funding and frozen hypothetical incumbents.

Forty-four targeted tests pass. Four two-period funding/supply combinations contribute 2,308 matching closing solves with unchanged complete policies, traces and original work counters. The [phase contract](buying-behavior-v2-phase-oracle.md#closing-decision-boundary-audit-inside-endogenous-funding) and `20261012-closing-boundaries` record the counterexamples, fixes, scope and audit. The adapter still does not replace planner enumeration; remaining numerical decision boundaries must be considered before substitution and the unchanged scaling screen. The full goal remains active with production integration and economic/performance/forecast/rollout gates unfinished. No live-world operation occurred.

## Ledger-order closing path integrated as an optional oracle accelerator

The preceding turn fixed storage reductions and added a shadow audit. This continuation found an ordinary-balance near-tie counterexample where the algebraic closing optimizer chooses a different basket despite integer storage. The audit detects it. A new compiled batch evaluator preserves the actual cash/settlement/horizon arithmetic and posterior reduction, and a bounded selector preserves lexicographic comparison order.

`closing_search='compiled-exhaustive'` now optionally substitutes this ledger-order closing calculation inside the event-tree planner and its endogenous funding queries. Actual ledger replay still supplies final accounts and traces; unsupported calendars/spatial cases fall back. It defaults off and counts every enumerated basket against the explicit budget. Forty-two targeted tests pass, including per-basket/per-scenario equality over 60 random two-line markets and full-policy funding/supply comparisons; a focused fallback check also passes.

The unchanged 32-row screen still has 18 exact results and 14 limits. Three warm alternating pairs reduce a capacity-four endogenous case from about 91.5 ms to 8.7–9.4 ms with identical policies/traces. This is a verified evaluation-cost improvement, not a scalability pass. All 32 screen rows replay from archived source with the original repository excluded from imports. Details and artifacts are in the [phase contract](buying-behavior-v2-phase-oracle.md#ledger-order-compiled-closing-enumeration).

Next work is allocation-range pruning compatible with ledger arithmetic and lexicographic decisions. The full goal remains active: scalable complete planning/funding, suitable forecasts, remaining economic decisions, production/runtime/UI integration and all economic/performance/fairness/rollout gates remain required. No live-world activation occurred.

## Closing allocation ranges can now be pruned without changing tested policies

The preceding turn implemented ledger-order compiled closing enumeration. This continuation adds an optional lexicographic box search with outward-rounded ledger-value bounds, explicit infeasibility checks and a shared budget for boxes and outer prefixes. Unsupported calendars still use the full planner. It skips only proved inferior/infeasible ranges and retains the original scan order for near ties.

Broader three-input/three-line testing also identified and corrected a compensated-summation mismatch with the supported Python 3.12 reference. Archived pre-fix code fails the constructed three-line sales regression; current code matches the staged ledger. A 46-test targeted run passes, followed by nine closing-box/prefix tests after tightening the dynamically shared budget. Random range checks use actual staged-ledger values and complete-policy comparisons preserve funding/supply behavior.

The original 32-case budgets still produce 18 successes and 14 explicit limits. A capacity-four endogenous closing problem drops from 1,750 evaluated baskets to 110, but needs 1,126 box visits and shows no clear timing improvement over compiled enumeration. All 32 final rows replay from archived source; the [phase contract](buying-behavior-v2-phase-oracle.md#lexicographic-closing-box-pruning-with-outward-ledger-bounds) records proof boundaries, counters, failures and artifacts. All launched checks completed.

This is correctness and search-structure progress, not a scalability pass. Next work is a tighter production/input-cost bound and less repeated bound overhead. The full goal remains active, including suitable forecasts, scalable complete planning/funding, unresolved economic choices, production/runtime/UI integration and outstanding economic/performance/fairness/rollout gates. No production or live-world activation occurred.

## Conditional production costs improve bounded search from 18 to 23 cases

The preceding turn added correct but loose closing-box pruning. This continuation implements a conditional-output bound with relaxed cheapest input requirements, explicit conversion payments and conservative allowance for merchandise rounding. Exact rational arithmetic establishes the reference minimum input cost; actual allocation, production, funding and settlement remain unchanged. The new optional mode is `closing_search='compiled-cost-boxes'`.

The unchanged 32-row screen now completes 23 cases rather than 18. It newly solves both outer-search variants of the eight-unit/three-supplier frozen and endogenous one-period cases, plus the exhaustive-outer two-period capacity-two endogenous case. Nine cases still hit explicit limits. Eleven targeted bound/solver tests and an eighteen-test integration run pass (one repeated case), and every final screen row replays from archived source. The [phase contract](buying-behavior-v2-phase-oracle.md#conditional-production-cost-bound-completes-five-more-screen-cases) records formulas, units, proof boundaries, counts, failures and artifact locations.

This is a real expansion of budgeted solvable scope, but not a population-performance pass: rational bounds make individual calculations expensive, and earlier-phase branching remains. Next work is a conservatively rounded compiled bound checked against this rational reference. Suitable forecasting, full-scope scalable planning/funding, unresolved economic choices, world/runtime/UI integration and economic/performance/fairness/rollout gates remain unfinished. All launched checks completed; no live-world activation occurred. The full goal remains active.

## Compiled cost bounds preserve decisions and reduce evaluation time

The preceding turn expanded budgeted solvable scope to 23 of 32 cases using an expensive rational cost bound. This continuation adds a conservatively rounded compiled counterpart while retaining the rational calculation for verification. Minimum costs round downward, error allowances upward, and actual ledger selection/settlement remain unchanged. The optional mode is `closing_search='compiled-fast-cost-boxes'`; default production behavior is untouched.

Thirteen targeted tests and a subsequent eighteen-test integration run pass, including rational-bound dominance, staged-ledger checks, monetary extremes, lots/yields and full funding/supply policies. All 32 screen rows match the rational results and work counters, and reproduce from archived source. The frontier remains 23 successes and nine explicit limits. Three alternating warm pairs reduce the larger one-period median from 363.7 to 73.6 ms and the two-period median from 849.6 to 444.6 ms, with identical complete policies/traces.

The [phase contract](buying-behavior-v2-phase-oracle.md#compiled-conservative-cost-bound-preserves-the-23-case-frontier) records numerical scope, samples and reproducible artifacts. These are toy-company planning times, not full-world performance; remaining branching/repeated solves, suitable forecasts, economic decisions, full integration and adoption gates are still open. All launched checks completed, no live-world activation occurred, and the full goal remains active.

## Profiled duplicate closing preparation removed

The preceding goal turn reconfirmed saved decisions and verification but made no implementation change. This continuation profiles the current planner, removes repeated preparation of the same validated closing problem, and packs fixed evaluator arrays once per solve. Public validation and actual accounting/selection order are retained.

Thirty targeted tests pass. All 32 scaling rows preserve values, decisions, statuses and work counters (23 exact, nine limits). Independently captured complete pre-edit results match after the change. Five warm samples per version show local medians of 73.4→70.9 ms and 423.6→381.5 ms for the two measured synthetic cases; these sequential before/after samples are not a full-population benchmark. Evidence and precise scope are in the [phase contract](buying-behavior-v2-phase-oracle.md#reuse-validated-preparation-within-each-closing-solve).

All launched processes completed. This reduces repeated setup cost but does not resolve combinatorial limits. The gross range bound remains a measured cost; earlier-phase branching and repeated funding solves remain candidates for deeper work. Suitable forecasts, full-scope scalable planning, unresolved economic choices, world/runtime/UI integration and adoption gates remain incomplete. The full goal remains active, and production/live state is unchanged.

## Exact closing reuse expands the bounded screen to 24 cases

The preceding turn reduced duplicate preparation cost. This continuation measures repeated complete closing inputs and adds optional bounded reuse of their completed selections. It preserves full state, event, posterior, neutral and hypothetical flags in the key, replays the selected purchase through the ledger, and charges actual remaining work. No economic state reduction or approximate solution is introduced.

Twenty-eight targeted tests pass, and the newly completed case matches the ordinary event tree's full policy and final accounts. The unchanged screen budgets now complete 24 cases with eight explicit limits; all 32 rows replay from archived source. The measured two-period median improves from 386.7 to 353.0 ms over three alternating warm pairs; the one-period control is effectively unchanged. The [phase contract](buying-behavior-v2-phase-oracle.md#exact-closing-memo-completes-a-twenty-fourth-screen-case) records keys, accounting/budget semantics, memory limits, test scope and artifacts.

All launched checks completed. The cache defaults off. The full goal remains active: remaining combinatorial limits, suitable forecasting, unresolved economic choices, full world/runtime/UI integration and adoption gates are not yet satisfied. No production or live-world activation occurred.

## Combined planner options verified; screen reaches 25 cases

The preceding turn implemented exact closing memoization. This continuation classifies the remaining failures and verifies its interaction with the existing continuation-pruning path. Three new regression tests cover complete policies/accounts, fee and supply variants, calendar rejection and the larger case's original work budget; ten targeted tests pass in total.

The unchanged 32-case screen now has 25 completed results and seven explicit limits. The new capacity-four/two-period endogenous case returns $13 in 3,660 nodes and 15,936 boxes. Its complete policy and final accounts match the existing closing solver with continuation pruning and closing memoization disabled under a larger verification budget. A separate ordinary event-tree attempt hit 500,000 nodes and is preserved as failed evidence, not claimed as a successful comparison. All screen rows replay from archived source. The [phase contract](buying-behavior-v2-phase-oracle.md#combined-continuation-pruning-and-closing-reuse) records scope, flags, counts and limitations, and the master plan now links this current status.

All launched processes completed. This establishes a verified combination for further experiments; seven limits and full-population suitability remain unresolved. Suitable forecasts, remaining economic decisions, world/runtime/UI integration and all adoption gates still require work. The full goal remains active with no production or live-state activation.

## Strict closing certificates implemented; screen reaches 28 cases

The preceding turn verified combined pruning and reuse. This continuation implements a strict ledger-value certificate for a fast closing proposal. It covers every other whole-lot allocation with conservative bounds; inconclusive proofs retain the complete lexicographic fallback. Proposal eligibility does not narrow supported ownership or buffers. All proposal/proof work is charged, and the new mode remains optional.

Sixteen integration tests pass after initial proof checks, plus focused tie and multiple-line fallback extensions. Forty seeded markets are compared with the independent event tree, and the newly completed larger cases preserve the previous solver's complete policies/accounts under expanded reference budgets. The unchanged screen now completes 28 of 32 cases, with four explicit allocation limits. All rows replay from archived source. Three alternating warm pairs reduce the one-period median from 73.0 to 4.8 ms and the two-period median from 515.6 to 405.8 ms. The [phase contract](buying-behavior-v2-phase-oracle.md#strict-closing-certificates-expand-the-screen-to-28-cases) states proof conditions, accounting of work, failures, scope and artifacts; the master plan reflects the current status.

All launched checks completed. The full goal remains active: earlier-phase scaling, full-population practicality, suitable forecasts, remaining economic choices, world/runtime/UI integration and adoption gates remain unfinished. No production or live-world activation occurred.

## Explicit temporal forecast adapter implemented and verified

The preceding turn accelerated exact closing decisions. This continuation addresses the distinct temporal-scenario requirement: an adapter now joins supplied per-period joint forecasts using explicit independence or user-supplied transition matrices. It preserves period marginals, requires one information date, validates quote/tick calendars, counts all positive paths and rejects underflow or excessive scenario trees. It does not estimate a transition model or select a production forecast.

Thirty targeted tests pass. Controlled identical-marginal examples yield $3.00, $2.25 and $5.50 horizon returns under independence, persistence and alternation, with different conditional procurement decisions. A stockless first book preserves hidden-state uncertainty and produces identical next purchases on both paths. All four complete examples replay byte-identically from archived source outside repository imports. The [forecast contract](buying-behavior-v2-forecast-contract.md#explicit-temporal-coupling-and-observed-information-checks) records equations, assumptions, counterexamples, scope and artifacts.

All checks completed. The full goal remains active: temporal probabilities still need empirical calibration and economic validation; the four larger planner limits, suitable complete forecasts, remaining economic decisions, world/runtime/UI integration and adoption gates remain unfinished. No production or live-state activation occurred.

## Temporal calibration evidence audited before fitting

The preceding turn implemented the explicit temporal scenario adapter. This continuation adds and runs an audit of consecutive seller observations, excluding empty stock, recorded stock constraints and changed quotes while preserving product/seller denominators and observed-information timing. Twelve targeted tests pass; ten preserved histories yield thirteen channel reports, all reproduced byte-identically from archived source.

The startup full-population history has only 0.093% qualifying retail pairs and 0.389% qualifying input-C3 pairs. Input C4 has 9.460% qualifying pairs, but only seven seller columns show both zero and positive origin states. The controlled probes also lack within-seller coverage of both binary states. These findings prevent treating pooled counts as a calibrated population zero/positive transition kernel; positive-quantity dynamics remain a separate possible study. The [forecast contract](buying-behavior-v2-forecast-contract.md#temporal-history-coverage-audit-do-not-fit-a-population-kernel-from-pooled-counts) records exact counts, exclusions, scope and next evidence requirements.

All checks completed. No kernel was fitted and no saved evidence or live behavior changed. The full goal remains active, with suitable calibrated forecasts, remaining planner limits, economic decisions, integration and adoption gates still unfinished.

## Bounded price-response candidate addresses one measured forecast failure

The preceding turn audited temporal-data limitations. This continuation implements a bounded, fitted quote-response comparator using multiple positive-sales quotes in eligible peer-rank books. Unsupported fits retain an explicit fallback. The candidate reads lagged published observations and does not change world purchasing or pricing.

Thirty targeted tests pass. A preregistered controlled quote-variation screen over historical seeds produces 54 target phases. Ample-stock MAE falls from 716.221 to 10.583 items across 18 targets, while limited/empty histories retain their prior errors. All outputs replay byte-identically from archived source; actual target sales match across training treatments, and 15 seed-137 reference/compiled phases agree with accounting checks. The [forecast contract](buying-behavior-v2-forecast-contract.md#bounded-quote-response-comparator-with-explicit-identification-requirements) documents equations, units, support rules, residual assumptions and the correctly specified synthetic-family limitation.

All checks completed. The full goal remains active: this is not held-out or heterogeneous-market validation, and scarcity, re-entry, industrial forecasting, temporal calibration, remaining planner limits, integration and adoption gates remain unfinished. No production or live-world activation occurred.

## Unchanged forecast stressed against heterogeneous response families

The preceding turn implemented a fitted bounded quote response. This continuation adds a controlled heterogeneous-buyer stress harness and tests the unchanged forecaster under four frozen profiles. Seven targeted tests pass; all 180 training/target phases match declared-curve/rounding calculations, and all 72 target rows replay byte-identically from archived source. The homogeneous control exactly reproduces the preceding experiment.

The bounded candidate improves the two mixed-buyer profiles but worsens MAE on a steeper response: 400.313 items versus 367.359 for the older peer model. This counterexample prevents treating the homogeneous improvement as a general replacement result. The [forecast contract](buying-behavior-v2-forecast-contract.md#response-family-stress-the-bounded-curve-is-not-a-universal-replacement) records profiles, denominators, source identity, errors and the next requirement: check model adequacy using published training observations before selecting a response family.

All launched checks completed. The full goal remains active: no universally suitable forecast or adoption gate is established; remaining scarcity/re-entry, industrial/temporal forecasting, planner scaling, economic decisions and world/runtime/UI integration work remains. No production or live-world behavior changed.


## Published quote validation added to the experimental forecast

The response-family counterexample now has an explicit selection comparator: leave each complete observed quote level out, score both fits against capped published sales, and choose bounded only for a strict improvement. Insufficient support or a fold-budget limit retains the peer path. Selection uses no target outcome and does not modify the publication.

Fifteen targeted tests pass. All 72 prior raw screen rows are unchanged, and the complete new result replays byte-identically from archived source. Selection keeps the bounded improvements in the first three profiles and retains the lower-error peer model in the steeper profile. The [forecast contract](buying-behavior-v2-forecast-contract.md#published-quote-validation-for-response-selection) records the equation, cap-dependent counterexample, work limit, preserved initial test failure and artifact location. This is retrospective calibration on previously inspected profiles, not a passed adoption gate.

D1 and D2 remain accepted exactly as the user specified: whole-demand qualification and one fee per product order under frozen incumbent availability. The full implementation goal remains active. Forecast suitability, four planner scaling limits, population performance, unresolved economic choices, integration and rollout gates remain incomplete; no production activation occurred.


## Population support checked before further response tuning

The prior turn completed the historical quote selector. This continuation implements a structural coverage audit and applies it to ten preserved histories. At tick 31 of the full-population seed-137 startup run, none of the latest offered seller columns meets the selector's necessary support conditions; retail and input-C4 have no eligible whole books. This is a concrete population-coverage failure despite the controlled calibration gains. The [forecast contract](buying-behavior-v2-forecast-contract.md#full-population-quote-support-audit) gives channel/product denominators, exclusions and limits.

Eight targeted tests pass and all thirteen channel reports replay byte-identically from archived source. The evidence changes the next forecast priority to incomplete-discovery and censored-observation modeling; further tuning of the bounded family alone cannot close coverage. Production is unchanged. The full goal remains active, with model suitability, planner scaling, economic decisions, integration and adoption gates outstanding.


## Censored-history identification limit made executable

The preceding support audit showed that whole-book coverage is absent in the saved startup window. This continuation tests whether relaxing that filter could by itself recover demand. A new paired-world probe demonstrates identical complete seller histories, with positive constrained sales and changing prices, but different replenished sales. At seed 137/$3, the targets differ by 2,847 items, forcing at least 1,423.5 items of worst-case error for any common point prediction. The [forecast contract](buying-behavior-v2-forecast-contract.md#identical-censored-histories-can-conceal-different-replenished-demand) defines the information boundary and acceptance condition: replenishment extrapolation must expose its additional assumptions and sensitivity.

Six targeted tests pass, paired reference/compiled fixtures agree, all 30 target phases match independent demand calculations, and the 15-pair archived result replays byte-identically. The initial large fixture's storage-capacity failure is preserved and corrected in the final specification. No new calibrated forecast, prior or production policy is claimed. The full goal remains active; forecast uncertainty, planner scaling, economic choices, integration and adoption gates remain unfinished.


## Forecast assumptions connected to purchasing consequences

The preceding turn proved that identical censored histories can conceal different replenished sales. This continuation implements an explicit forecast-sensitivity adapter for the existing closing-decision optimizer. It solves each named model, cross-evaluates selected baskets with the independent reference evaluator, checks unchanged physical execution, and reports return/regret without inventing model probabilities or a robust-policy default.

In the controlled example, changing an explicit tail assumption changes optimal purchases from one input to four, with endpoint cross-model regrets of $4.50 and $7.50. Cash and existing-finished-stock controls preserve conversion feasibility and baseline valuation. Nine targeted tests pass, including shared-input multiple lines and prior allocation-oracle comparisons. The [forecast contract](buying-behavior-v2-forecast-contract.md#purchasing-sensitivity-to-explicit-forecast-alternatives) records equations, scope and reproducible artifacts.

The full goal remains active. This diagnostic exposes the economic consequences of uncertain forecasts; it does not infer a calibrated tail, solve multi-phase forecast uncertainty, remove the remaining planner limits or complete world integration and adoption gates. Production behavior is unchanged.


## Combined integration checkpoint after forecast sensitivity work

Ran the complete Python discovery set in two disjoint groups: 305 `test_buying*.py` tests passed in 221.973 seconds; the remaining 95 discovered tests passed in 18.178 seconds. All 61 buying test modules were included. No failure or skip was reported. This verifies the accumulated reference/compiled buying, solver, accounting, forecast, history and persistence tests together; coverage remains bounded by the assertions in those tests.

`node tests/js/test_buying_inspector.js`, `node tests/js/test_formatting.js`, `node tests/js/test_profitability.js` and `node --check web/app.js` pass. No new browser rendering check or performance benchmark was performed. The two Python runs overlapped briefly, so their durations are test execution timings, not isolated simulation performance measurements. The existing NumPy/SciPy compatibility warning is unchanged and nonfatal.

`stats/buying-implementation/20261012-buying-suite-integration/` preserves logs, the disjoint-discovery runner, source/runtime identity, JavaScript check results and documentation link checks. Every hashed source file was unchanged at completion. The progress document's opening summary now distinguishes current implemented experimental components from historical starting-state entries; the seller-history document now correctly distinguishes experimental forecast consumers from production purchasing. Fifty-five local documentation links resolve and `git diff --check` passes.

The full goal remains active. Passing all current tests does not supply the missing economic model, eliminate the four planner scaling limits, establish population performance, finish production integration, or satisfy held-out long-run/rollout requirements. No production activation or live-world operation occurred.


## Remaining planner failures now retain work diagnostics

Following the combined integration checkpoint, exact phase-search failures now expose a typed diagnostic snapshot without returning a partial policy. The unchanged screen reproduces all 28 exact results and four limits. The endogenous cases fail in the first purchase's hypothetical funding search; the frozen controls fail in a later closing subsolve while exploring that first decision. Completed work and interrupted-subsolver exclusions are stated separately.

Eight targeted tests pass, and the archived screen replays with timing excluded. The [phase contract](buying-behavior-v2-phase-oracle.md#search-limit-diagnostics-locate-the-remaining-scaling-work) gives counts and identifies the next optimization target: safe bounds on groups of earlier purchase baskets. Existing closing reuse already saves work, so merely increasing that cache does not resolve the observed enumeration limit. No solver budget, feasible action, economic parameter or production policy was changed. The full goal remains active.


## Initial-basket prefix bound implemented independently

The search-limit diagnostics identified earlier basket enumeration as the next target. A new standalone prefix-continuation envelope fixes compulsory purchases, relaxes the remaining procurement/production calendar, and returns an optimistic value for all completions. It preserves the current action space and does not yet alter planner traversal.

Ten targeted prefix/continuation tests pass in the worktree and archived-source replay, including exhaustive matching completions, two-period recourse, shared-input multiple lines, fees, historical basis and terminal values. The [phase contract](buying-behavior-v2-phase-oracle.md#standalone-bound-for-an-initial-allocation-prefix) records the relaxation, numerical treatment, unavailable cases and next integration checks. No scaling improvement is claimed before that integration and the unchanged screen. The full implementation goal remains active.


## Prefix envelope integrated with explicit work accounting

The standalone bound is now an optional endogenous `feasible-prefix` mode. It preserves traversal order, charges each scenario-bound evaluation, retains unsupported branches and rejects incomplete searches. Fourteen targeted tests preserve complete policy/account results, including multiple funding/supply modes and fee counterexamples; all 32 screen rows replay from archived source.

The first attempt redundantly bounded complete baskets and exhausted combined work. The revised mode bounds groups only and prunes useful subtrees, but still finishes 28/32: the four scaling limits remain. Both attempted versions and the corrected small-fixture test expectation are preserved. The [phase contract](buying-behavior-v2-phase-oracle.md#optional-prefix-pruning-integrated-scaling-limits-remain) records counters, comparisons and limitations. The mode stays off by default; no population performance benefit or production readiness is claimed. The full goal remains active.


## Common first-production decision added to a tighter bound

The integrated prefix bound still grants separate first-period production choices to hidden future scenarios. A new standalone two-book relaxation requires one common first production choice and then averages optimistic future returns. It retains advance-buffer possibilities through optimistic current/future input prices and falls back to infinity outside its stated calendar/work support.

The capacity-two correlated-demand example tightens to the exact $6.50 optimum plus numerical cushion. Fourteen targeted bound tests pass in the worktree and archived-source replay, including all small prefix completions, changing input-price opportunities, basis, fee income and terminal values. The [phase contract](buying-behavior-v2-phase-oracle.md#shared-first-production-relaxation-closes-one-information-gap) records the equation, assumptions and required integration. The primitive is not enabled in traversal, so the four scaling failures remain open. The full goal stays active.


## Shared-first relaxation integrated; expanded diagnostic completes

The tighter bound is now optional in endogenous prefix traversal, with worst-case work reserved before use and actual state/scenario work charged afterward. Twelve targeted tests preserve full policies/accounts across funding and supply variants. All untreated controls and both archived screens reproduce.

The original screen remains 28/32. The largest treated case reduces allocation work but reaches its closing combined-work limit. A separately labeled larger-budget diagnostic completes with value $26, first basket `(8,0,0,8,0,0)`, 4,908 allocations and 41,148 combined work units. Those exceed the original 4,000/16,000 thresholds; they are not counted as a passed gate. The [phase contract](buying-behavior-v2-phase-oracle.md#shared-first-bound-integrated-with-reserved-work) gives the work breakdown and remaining optimization target. Production/default planner behavior is unchanged; the full goal remains active.


## Shared-bound cache separates reusable profit from sunk cash

Added optional bounded reuse of exact shared-first relaxed profit, applying each caller's cash/arrears/prefix-payment offset and numerical allowance afterward. This retains full input validation and actual planner execution. The initial complete-value cache and its limited benefit are preserved; the revised key removes only mathematically additive offsets.

Seven targeted tests pass. The expanded capacity-eight comparison preserves complete policies, traces, accounts and non-prefix search diagnostics, while saving 17,649 shared-bound work units. Combined work drops to 23,499 and allocations remain 4,908, so the original acceptance screen remains 28/32. All screen rows and the expanded full comparison replay from archived source. The [phase contract](buying-behavior-v2-phase-oracle.md#exact-relaxed-profit-reuse-reduces-shared-bound-work) records keys, charging, scope and artifacts. Remaining scaling, forecasts, integration and adoption gates stay open; the full goal remains active.


## Fresh closing proofs with cached hints expand the screen to 29 cases

Added optional allocation-hint reuse, with fresh strict ledger proof for every hit and complete fallback for invalid, infeasible or unproved hints. Hints deliberately relax key fields; they are never cached policies or certificates. Shared-first prefix bounds now run before the ordinary bound when enabled, avoiding duplicate work on already rejected groups.

The original screen now completes 29/32. The newly passing capacity-eight endogenous-prefix case uses 3,192 allocations and 15,281 combined work units, inside the unchanged 4,000/16,000 limits. Its full result matches preserved expanded-budget policies, traces, accounts and non-work diagnostics. Eleven targeted tests pass and all screen rows replay from archived source. Earlier narrow-key, broader-hint and invalid-hint-failure evidence is retained.

The [phase contract](buying-behavior-v2-phase-oracle.md#fresh-proofs-around-reusable-hints-reach-29-of-32-cases) records the proof boundary and work breakdown. Frozen/exhaustive, frozen/prefix and endogenous/exhaustive variants still fail at the largest dimensions. Population practicality, forecast calibration, remaining economic choices, production integration and adoption gates remain open. The full goal stays active.


## Pure frozen comparator moves the screen to 30 cases

Added the explicit `slot-deficit-v1` rule, identical to the former pure callback, allowing validated pruning without accepting arbitrary callbacks. It remains an experimental replenishment comparator. Nine targeted tests pass and all 32 screen rows replay. All endogenous rows are unchanged; the largest frozen-prefix case newly completes with 466 allocations and 4,823 combined units under original limits.

A larger-budget unpruned callback reference completes at 81,538 allocations and matches the new case's full policies, traces, states and accounts. The [phase contract](buying-behavior-v2-phase-oracle.md#explicit-slot-deficit-comparator-enables-safe-frozen-path-pruning) records the formula, metadata distinction, guard-message test update and artifacts. The screen stands at 30/32; its two remaining limits are exhaustive comparison modes. Broader ownership/calendar scalability, population performance, calibrated forecasts, economic choices, production integration and adoption gates remain open. The full goal stays active.


## Multi-line scaling tested explicitly: nine of sixteen complete

Broadened the harness to two distinct installed lines sharing one input, including a repeated-input recipe, shared slots/cash/storage and fixed sequential production. The original one-line fixtures are independently unchanged. Four targeted tests verify structure, analytical returns and full ordinary/optimized policy/account agreement in small cases; all 16 new screen rows replay from archived source.

The same work budgets finish 9/16 two-line configurations. Larger one-period cases already fail in closing search, and most larger two-period cases also fail. This prevents generalizing the single-line 30/32 result to supported ownership. The [phase contract](buying-behavior-v2-phase-oracle.md#two-line-shared-input-screen-exposes-closing-search-limits) gives the complete matrix and identifies joint-line closing bounds/proposals as the next solver target. No line ownership restriction, economic parameter change or production adoption was introduced. The full goal remains active.

## Joint-line hints implemented; no scaling gate improvement

Implemented a bounded joint-batch proposal that sums shared-input requirements before procurement. Every hint still needs a fresh strict ledger dominance proof; otherwise the complete sequential-production search runs. Fifteen targeted tests pass, including independent event-tree comparisons and adversarial cash, basis, fee and cached-hint cases.

The same two-line screen remains 9/16. Values and first allocations agree with the earlier screen, but speculative work increases overall allocations in all nine completed cases. The new `compiled-joint-certified-boxes` mode is therefore explicit opt-in; the existing certified mode keeps its previous behavior. The [phase contract](buying-behavior-v2-phase-oracle.md#joint-line-proposal-experiment-proof-bounds-remain-the-bottleneck) records the equation, work charges, failed improvement and preserved evidence. A joint-line proof bound remains the next target. The full goal is active, and production purchasing is unchanged.

## Joint-line proof bound implemented independently

Added a bounded reference closing relaxation that conserves aggregate input use across installed lines and charges all lines' conversion expenses. It includes every feasible sequential output vector while relaxing fees, production gates and physical constraints. Insufficient state budgets return an unavailable bound, never a partial finite estimate.

Seven targeted tests pass, including exhaustive ledger comparisons in sampled boxes, shared/repeated inputs, lots, output yields, posterior demand, basis, fees and monetary boundaries. In the capacity-eight reference fixture, the upper value tightens from approximately $140 to $104, matching the known optimum plus outward-rounding allowance. The [phase contract](buying-behavior-v2-phase-oracle.md#standalone-joint-line-closing-bound) records equations, numerical treatment and archived evidence. This standalone primitive does not yet change traversal or the 9/16 scaling result. Compiled integration with explicit state/scenario charging remains next; the full implementation goal stays active.

## Joint-line bound compiled with conservative arithmetic

Added a compiled counterpart that never understates the rational reference in the tested boxes and preserves batch-state accounting. Shared input packing leaves the existing compiled closing-cost algorithm unchanged. Eight targeted tests pass, including independent ledger checks, rational/compiled comparisons, extreme prices, integer budget limits and existing policy parity cases.

The [phase contract](buying-behavior-v2-phase-oracle.md#compiled-joint-line-bound-verified-against-the-rational-reference) records numerical safeguards and archived evidence. Search integration with explicit work charging is still required; this change alone does not improve the 9/16 scaling screen or establish population performance. Production behavior is unchanged, and the full goal remains active.

## Joint proof integrated: multi-line screen advances to thirteen cases

The experimental joint-certified mode now uses the compiled bound inside strict proofs, reserves worst-case state/scenario work and charges actual work separately. Failed proofs retain complete fallback with all spent work deducted. Ordinary certified mode and production purchasing are unchanged.

The unchanged two-line screen improves from 9/16 to **13/16** under 4,000 allocations and 16,000 combined work units. All one-period cases now complete, plus capacity-two endogenous and capacity-four frozen two-period cases. Seventeen targeted tests pass; every archived screen row replays except timing. The [phase contract](buying-behavior-v2-phase-oracle.md#joint-proof-integration-completes-thirteen-of-sixteen-cases) records the complete matrix and work totals. The remaining three limits are dominated by repeated joint evaluation, making conservative reuse or reduced joint work the next optimization target. Broader model, integration and adoption requirements remain open; the full goal stays active.

## Exact joint-bound cache reduces repeated evaluation

Added an optional bounded cache for exact joint-bound inputs and box endpoints. It retains cash and all value-affecting data, excludes only fields the bound already relaxes, never caches unavailable results, and charges one work unit per hit. Twelve targeted tests pass, including invalidation and full policy/account comparisons.

The screen remains 13/16, with completed values and first allocations unchanged. Capacity-two/two-period endogenous joint work falls from 6,614 to 4,256; frozen cases offer less reuse. The [phase contract](buying-behavior-v2-phase-oracle.md#exact-joint-bound-reuse-reduces-work-without-clearing-another-limit) documents the key, charging, preserved evidence and remaining limits. This is useful work reduction, not a completed scalability or adoption gate. The full goal remains active.

## Box-specific joint budgeting verified; bottleneck remains

Joint proof evaluation can now serve a cached value with one work unit or reserve the actual box's Cartesian state count before a fresh evaluation. Fourteen targeted tests pass. The screen remains 13/16 with identical completed counters, and failing searches reach the same completed allocation counts. The [phase contract](buying-behavior-v2-phase-oracle.md#joint-bound-budgeting-now-uses-the-current-box-and-cache-result) records this negative scaling result and preserved evidence. Earlier-purchase pruning across multiple lines remains a candidate route to reducing repeated closing proofs. The full goal remains active.

## Multi-line common-first prefix bound tested; kept off by default

Implemented the joint first-production relaxation, bounded memo reuse and optional prefix integration with explicit scenario/line work charging. Fifteen targeted tests pass, including independent continuation comparisons and complete policies/accounts. Cheaper-bound-first ordering and fixed-input batch caps were also tested, with all attempts retained.

The enabled screen remains a regression at 12/16: fewer allocations in capacity-two cases do not offset bound cost in capacity-four frozen. Disabled behavior reproduces every prior screen row and remains 13/16. The [phase contract](buying-behavior-v2-phase-oracle.md#joint-first-production-prefix-bound-correct-but-not-a-scaling-improvement) records equations, scope, counts and evidence. Capacity-eight endogenous fails before prefix pruning can run, directing further work back to cheaper closing proofs. The experimental option stays off; the full goal remains active.

## Cash-relaxed reference bound separates reusable return from funding cash

Added a standalone normalized-cash joint bound with exact offset translation and an explicit allowance for leaf and posterior floating-point operations. Cash scarcity is relaxed only inside the bound; purchasing and production still execute with actual cash. Seven targeted tests pass, including independent feasible baskets, large/tight cash, weighted posterior arithmetic, fees, basis and signed terminal values.

The [phase contract](buying-behavior-v2-phase-oracle.md#standalone-cash-relaxed-closing-bound-for-future-reuse) records equations, numerical conditions and preserved evidence. The next work is verified normalized-return reuse and compilation/integration; this reference alone does not change the 13/16 screen result. The full goal remains active.

## Normalized closing reuse integrated with fresh caller allowances

Added compiled normalized joint evaluation and bounded reuse across cash/arrears offsets, with a fresh caller-specific rounding allowance on every hit. Optional phase integration preserves actual ledger execution and strict proof/fallback. An extreme-cash translation test exposed a work-accounting boundary: completed enumeration is now charged even if its translated bound is unavailable.

Seventeen targeted tests pass, including complete policy/account and combined-prefix checks. The screen stays 13/16 but joint work falls materially, and two remaining failures now reach prefix/allocation limits rather than their former closing bottleneck. Combining the joint-first bound recovers the capacity-four frozen case lost by that option alone, but still completes only 13/16. The [phase contract](buying-behavior-v2-phase-oracle.md#normalized-cash-reuse-integrated-remaining-failure-types-change) records keys, results, distinct failure types and preserved experiments. The full implementation goal remains active; production purchasing is unchanged.


## Full integration checkpoint and structural planner handoff

A fresh full Python discovery passes all 469 tests in 269.739 seconds. The buying-inspector, formatting and profitability JavaScript tests pass, and `web/app.js` passes syntax checking. All 217 recorded source hashes are unchanged at completion. Forty-two links in the master plan and new architecture document resolve. Logs, commands, source identity, current event-field extraction and results are preserved in `20261012-current-suite-audit`. The existing NumPy/SciPy warning remains nonfatal; no dependency or live-runtime changes were made.

The requirements review confirms that the Python event tree is a verification oracle, not a demonstrated population planner. The [compiled continuation implementation contract](buying-behavior-compiled-continuation-plan.md) now defines the next structural work: lossless typed calendars, independent compiled transitions, observed-information grouping, explicit funding/decision stacks, exact policy replay and representative population validation. Its field-level coverage matrix is checked against current ledger declarations. No approximation or reduced ownership scope is adopted. The next implementation artifact is the typed calendar compiler. The full goal remains active.


## Typed continuation calendars implemented

Implemented a schema-versioned, lossless typed calendar compiler and validating decoder for every current ledger event. Integer identities remain int64, monetary arrays remain float64, and immutable independent buffers prevent data aliasing. Invalid types, offsets, payloads, calendars and out-of-range/lossy conversions fail explicitly.

Twenty-seven targeted tests pass, including an independently specified payload layout and complete oracle outcomes before/after decoding. The [compiled continuation contract](buying-behavior-compiled-continuation-plan.md#implemented-schema-1-and-verification) records schema, field coverage and preserved example/source evidence. This completes the representation step, not compiled execution or the population planner. The preceding 469-test full-suite checkpoint predates this compiler; this turn ran the relevant 27 tests. Compiled ledger transitions are next. The full goal remains active.

## Compiled non-purchase ledger transitions implemented

Compiled execution now covers books, ordinary/shared settlements, quotes, rent and tick-end updates. Thirty-one targeted tests pass, including complete reference state/detail parity across 80 varied cases and opening-book inventory/basis checks. Archived-source replay also passes all 31 tests, with source hashes verified. The initial compilation failure and corrected evidence are preserved.

The [transition implementation record](buying-behavior-compiled-continuation-plan.md#compiled-non-purchase-transitions-verified) states the boundary: this is a per-event verification adapter; Purchase explicitly remains unsupported, and the resident compiled state arena and planner are still required. No full discovery was repeated for this step. D1 and D2 remain accepted as recorded in the purchasing contract. The full implementation goal remains active.

## Compiled purchasing and production added

The [compiled purchase transition](buying-behavior-compiled-continuation-plan.md#compiled-purchase-transition-with-resolved-funding) extends the verification executor to all seven event kinds. Thirty-three targeted tests pass, including 2,592 allocation comparisons, full state/account/detail parity and a complete calendar exercising accepted D1/D2 rules, lots and multiple production lines. Unresolved funding fails explicitly.

This does not complete the population planner: resident typed state, funding and conditional decision execution remain open. Production defaults are unchanged. The full implementation goal remains active.

## Resident compiled calendar replay implemented

The [resident replay implementation](buying-behavior-compiled-continuation-plan.md#resident-typed-replay-implemented) executes supplied decisions without per-event Python state repacking. Thirty-six targeted tests pass, including complete/segmented reference parity, independent forks and atomic failure. A warm 12-event microbenchmark measures 57.9 microseconds median per resident replay; funding and search are excluded, so this does not establish population feasibility.

Observed-information grouping, endogenous funding and exact policy execution remain required. The full implementation goal remains active; production defaults are unchanged.

## Exact information-grouping component verified

Added compiled complete-state/current-offer equality and stable grouping, with a collision-free observed-history verification adapter. Twenty-four targeted tests pass, including the existing information-history counterexamples. The [grouping contract](buying-behavior-compiled-continuation-plan.md#observed-information-grouping-verification-component) records exactly which fields identify a decision and which remain hidden.

Resident observation emission and decision/funding-stack integration remain open; the history adapter still consumes Python trace records. The full implementation goal remains active and production defaults are unchanged.

## Resident replay now emits observations in compiled execution

Added optional typed observation records for all seven events, with exact reference-field comparisons and tests that hidden demand stays hidden. Twenty-seven targeted tests pass; atomic failure and fork isolation include the observation buffers. The [observation contract](buying-behavior-compiled-continuation-plan.md#compiled-realized-observation-emission) records schema scope and partial-history restrictions.

Numeric history interning, funding and policy search remain open. The full implementation goal remains active; production defaults are unchanged.

## Numeric histories now feed decision grouping

Added a bounded compiled history interner and direct grouping from resident observation records, without decoding Python trace dictionaries. Thirty-two targeted tests pass, including all-event equivalence and capacity-failure behavior. The [history contract](buying-behavior-compiled-continuation-plan.md#bounded-numeric-histories-connected-to-grouping) documents allocation limits, incomplete-prefix rejection and remaining scalability limits.

The next structural work is the explicit decision/funding stack and exact conditional search. The full implementation goal remains active; production defaults are unchanged.

## Resumable compiled action enumeration verified

Added the [typed action frame](buying-behavior-compiled-continuation-plan.md#resumable-action-frame-implemented), preserving complete lexicographic enumeration with safe cash/slot pruning and explicit work limits. Seventeen targeted tests pass, including 60 independent enumeration comparisons and interruption/resume equivalence.

The frame does not choose a policy. Conditional continuation and funding frames remain required, along with later world/economic/performance gates. The full implementation goal remains active; production defaults are unchanged.

## Explicit-stack conditional search matches supplied-funding oracle

Connected action enumeration, resident transitions and numeric history grouping into a complete supplied-funding conditional search. Nineteen targeted tests pass, comparing full selected policies, observations, states and accounting with the independent oracle. The [search contract](buying-behavior-compiled-continuation-plan.md#supplied-funding-conditional-search-connected) documents limits and unsupported integration stages.

Python control frames remain to be lowered into typed storage. Endogenous funding and persistent supply remain open, followed by representative performance and economic validation. The full implementation goal remains active; production defaults are unchanged.

## Persistent stock integrated into conditional search

Connected cumulative-arrival supply to resident execution, grouping and action search. Twenty-three targeted tests pass, including full oracle parity, live-stock fee eligibility and a nine-case arrival grid. The [persistent-supply record](buying-behavior-compiled-continuation-plan.md#persistent-supply-connected-to-resident-search) documents branch isolation, atomic failure and the remaining hypothetical-funding boundary.

Endogenous funding and fully typed control remain next. The full implementation goal remains active; production defaults are unchanged.

## Typed own-quote query execution verified

Added the [funding-query boundary](buying-behavior-compiled-continuation-plan.md#typed-own-quote-funding-boundary-implemented): typed offer selection, slot-relaxed stock, zero current fees, fixed incumbents and real-versus-phantom persistent-supply accounting. Fifteen targeted tests pass against independently constructed ledger queries.

Query optimization, future funding and bid assembly still need explicit frames and search integration. The full implementation goal remains active; production defaults are unchanged.

## Endogenous funding connected through explicit frames

The [continuation-v2 search](buying-behavior-compiled-continuation-plan.md#endogenous-continuation-v2-funding-connected) now optimizes own-quote queries, assembles actual bids and handles future funding decisions without recursive Python calls. Twenty-one targeted tests pass, including detailed oracle comparisons of each selected query's quantities, goods cost and conditional value, as well as complete policies and accounts.

Fully typed control/storage, broader differential verification and representative feasibility remain required. The full implementation goal remains active; production defaults are unchanged.

## Connected continuation integration checkpoint: 518 tests

A [24-case seeded differential campaign](buying-behavior-compiled-continuation-plan.md#connected-search-differential-and-integration-checkpoint) matches complete endogenous-funding policies, observations, accounting and query results against the oracle across varied economic boundaries. Archived-source replay also passes after correcting a preserved missing-catalog packaging failure.

Fresh full Python discovery passes all **518 tests in 287.023 seconds**. All 229 recorded source/catalog hashes remain unchanged. No JavaScript/browser or population/economic gate is claimed by this checkpoint. The master plan's current-state summary now reflects connected endogenous funding; fully typed control and bounded branch/result storage remain the next structural work. The full implementation goal remains active.

## Bounded typed branch storage verified

Added a [typed state/supply pool](buying-behavior-compiled-continuation-plan.md#typed-branch-state-supply-pool-implemented) with compiled event stepping, independent forks, generation-checked handles and explicit capacity diagnostics. Ten targeted tests pass, including complete resident comparisons and failed-step isolation.

Search integration, typed control and policy/result storage remain open. The full implementation goal remains active; production defaults are unchanged.

## Arena-backed search integrated and branch reuse verified

The [arena search path](buying-behavior-compiled-continuation-plan.md#branch-arena-integrated-with-conditional-search) now executes actual and funding branches with explicit release. Ten targeted tests pass, including all 24 seeded oracle comparisons. A diagnostic search reuses ten peak-live slots across 2,630 allocations and ends with zero live rows; capacity exhaustion returns no partial policy.

Python controls, observations and policy/result storage still need replacement or explicit bounds. The full implementation goal remains active; production defaults are unchanged.

## Copied policy dictionaries replaced by bounded numeric prefixes

Both search paths now retain [numeric policy-prefix IDs](buying-behavior-compiled-continuation-plan.md#bounded-numeric-policy-prefixes-integrated), reconstructing dictionaries only for selected final leaves. Fifteen targeted tests pass, including 24 seeded oracle comparisons and exact-capacity replay. Policy capacity failures return diagnostics and no partial solution.

Observation/funding-result storage and fully typed control remain open. The full implementation goal remains active; production defaults are unchanged.

## Growing search observation tuples replaced by numeric history IDs

Search now interns observations after every event and reconstructs traces only for selected final leaves. Fifteen targeted tests pass, including 24 seeded oracle comparisons and exact-capacity replay. The [history-storage record](buying-behavior-compiled-continuation-plan.md#search-observations-retained-only-in-bounded-numeric-history) states capacity and result-storage boundaries.

Funding-detail/result storage and fully typed control remain open. The full implementation goal remains active; production defaults are unchanged.

## Retained funding results now use bounded numeric prefixes

Search branches now retain funding-node IDs rather than copied funding dictionaries. Fifteen targeted tests pass, including 24 seeded oracle comparisons and exact-capacity replay. The [funding-record contract](buying-behavior-compiled-continuation-plan.md#retained-funding-details-moved-into-numeric-storage) records data coverage, limits and remaining Python storage.

Transient query answers, control frames and leaf results still need typed storage/integration. The full implementation goal remains active; production defaults are unchanged.

## Transient funding-query answers now use typed bounded scratch

Replaced answer dictionaries and query-key lists with typed arrays, preserving exact query reuse and ordering. Fifteen targeted tests pass, including 24 seeded oracle comparisons and exact-peak-budget replay. The [query-scratch record](buying-behavior-compiled-continuation-plan.md#transient-query-answers-moved-into-typed-scratch-arrays) documents the aggregate live-array limit and remaining storage boundaries.

Control frames and leaf results still need typed storage/integration, followed by representative validation. The full implementation goal remains active; production defaults are unchanged.

## Terminal leaf snapshots replaced by compact numeric results

Candidate leaves now store numeric identifiers and terminal values. Final selected policies are replayed, with every observation and final value checked before exposing the reconstructed state. Fifteen targeted tests pass, including 24 seeded oracle comparisons and exact result-capacity replay. The [terminal-result record](buying-behavior-compiled-continuation-plan.md#terminal-results-compacted-selected-policies-replayed) states memory and orchestration boundaries.

Typed control and its branch/group/result-ID lists remain the next structural work, followed by representative validation. The full implementation goal remains active; production defaults are unchanged.

## Scalar control metadata now uses bounded typed arrays

The [control-frame storage](buying-behavior-compiled-continuation-plan.md#scalar-control-frames-moved-into-typed-storage) now retains stages, positions, flags and monetary scalars in typed arrays with generation-checked views. Fifteen targeted tests pass, including 24 seeded oracle comparisons and a direct Python-control comparison.

Python dispatch and frame references to branch/group/result lists remain to be replaced or explicitly bounded. Representative performance, economic validation and integration gates remain open. The full implementation goal remains active; production defaults are unchanged.

## Selected leaf identifiers and group sums have fixed capacity

Search now uses [bounded numeric leaf-row buffers and group totals](buying-behavior-compiled-continuation-plan.md#selected-leaf-ids-and-group-totals-use-bounded-arrays), sized from each frame's scenario branches and information groups. Seventeen targeted tests pass, including all 24 seeded independent oracle comparisons, direct control-adapter comparison and atomic capacity checks. The original summation and traversal order are preserved.

Python branch/group objects and dispatch still need structural work. Population performance, economic validation and full integration remain open; the full implementation goal remains active.

## Information groups retain numeric membership instead of branch lists

The [stable numeric partition](buying-behavior-compiled-continuation-plan.md#information-group-membership-uses-numeric-partitions) replaces each frame's nested group lists with offsets and member indices. Eighteen targeted tests pass, including 100 independently checked partitions and all 24 seeded complete-search oracle comparisons. Group views retain original branch identity and preserve the established ownership/release rules.

Original branch sequences, Python adapters and dispatch remain. The full implementation goal remains active, with representative performance, economic validation and integration still open.

## Search metadata now follows typed branch ownership

History IDs, recorded-event counts and funding-record IDs now occupy [three typed columns per branch arena row](buying-behavior-compiled-continuation-plan.md#search-history-and-funding-ids-belong-to-branch-arena-rows). Fork copies the metadata, release clears it, and stale handles reject reads and writes. Nineteen targeted tests pass, including 24 seeded complete-search oracle comparisons and explicit metadata lifecycle checks.

Original branch sequences and Python dispatch remain. Full-world integration, representative performance and economic validation are still open; the full implementation goal remains active.

## Arena search retains numeric branch rows

Root, child and funded branch sequences now use [bounded numeric IDs and arena handles](buying-behavior-compiled-continuation-plan.md#arena-search-retains-numeric-branch-sequences). Temporary adapters recover metadata from the arena. Pending observations must be interned before retention, and stale generations cannot alias reused rows. Twenty-two targeted tests pass, including the four imported arena lifecycle tests and all 24 seeded complete-search oracle comparisons.

Transient Python adapters, control dispatch and action scratch remain to be integrated into the compiled planner. Population performance, economic validation and full-world integration remain open; the full implementation goal remains active.

## Full Python integration audit after bounded-storage changes

Full discovery passes **551 tests in 329.884 seconds**. Archived-source replay passes 23 selected tests, including all 24 seeded complete-search oracle cases, and 249 source/catalog hashes remain unchanged. The [checkpoint record](buying-behavior-compiled-continuation-plan.md#bounded-storage-integration-checkpoint) states scope and evidence.

The grouping kernel now uses the research source-aware JIT wrapper, and a test fixture import no longer duplicates discovery. Current master-plan summaries reflect the numeric retained storage now implemented. A compiled driver, representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Observed-information grouping executes directly over arena rows

The [compiled arena grouping kernel](buying-behavior-compiled-continuation-plan.md#information-grouping-reads-arena-rows-directly) now compares numeric branch rows without materializing copied states or a temporary typed list. Nineteen targeted tests pass, including all 24 seeded complete-search oracle comparisons, neutral/current-offer cases, state immutability and stale-handle validation.

The Python driver remains. No measured performance improvement, economic adoption or full-world integration is claimed; the full implementation goal remains active.

## Non-purchase segments execute and record history inside one compiled loop

Arena search now [advances non-purchase segments and interns observations](buying-behavior-compiled-continuation-plan.md#non-purchase-advancement-and-history-interning-share-a-compiled-loop) without per-branch Python dispatch. Nineteen targeted tests pass, including all 24 seeded complete-search oracle comparisons, segmented replay, capacity diagnostics and a finite-observation guard.

Purchase/funding traversal, scratch management and remaining Python orchestration still require integration into the compiled driver. Representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Terminal capture executes directly over arena rows

The [compiled terminal-capture loop](buying-behavior-compiled-continuation-plan.md#terminal-capture-reads-arena-state-and-writes-result-buffers-in-one-loop) now reads state views and writes bounded numeric results without per-branch Python dispatch. Eighteen targeted tests pass, including independent ledger terminal values, state immutability, capacity/error boundaries and all 24 seeded complete-search oracle comparisons. Final selected-policy replay remains unchanged.

The purchase/funding driver and scratch management remain to be compiled. Representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Actual funded branches are resolved in a compiled batch

The [funding-resolution batch](buying-behavior-compiled-continuation-plan.md#actual-funded-branches-are-cloned-and-recorded-in-a-compiled-batch) clones numeric arena groups, assigns funded demands and interns funding records in branch order. Fifteen integration tests and three lifecycle tests pass, including all 24 seeded complete-search oracle cases.

Query/detail construction and the outer search driver remain Python. Representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Funding detail assembly now uses compiled numeric encoding

Arena search now [encodes completed funding records directly from query arrays](buying-behavior-compiled-continuation-plan.md#completed-funding-records-are-encoded-directly-from-numeric-answers). Twenty integration tests and an additional empty-offer test pass, including all 24 seeded complete-search oracle cases. The resident comparison path retains dictionary assembly.

Query traversal, scratch management and the outer driver still require compilation. Representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Connected solver screen identifies dispatch and search-work limits

The [16-case connected scaling screen](buying-behavior-compiled-continuation-plan.md#connected-candidate-scaling-screen-exposes-two-independent-bottlenecks) completes 7 cases; nine hit the 4,000-allocation limit. Three repeats per case preserve full result/failure fingerprints. Profiling identifies repeated Python purchase-history insertion and typed-list construction as a substantial dispatch cost. The candidate also lacks the earlier solver's validated search reductions.

Next work should lower that measured history boundary and integrate proved pruning/reuse, preserving complete-policy oracle checks. Fully compiling dispatch alone cannot eliminate allocation exhaustion. Representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Measured history-insertion overhead removed without changing search results

The [single-observation compiled insertion path](buying-behavior-compiled-continuation-plan.md#single-observation-history-insertion-avoids-python-typed-list-construction) eliminates repeated Python typed-list construction while retaining validation, copies and exact history semantics. Twenty-one targeted tests pass. All 16 scaling-screen fingerprints match the captured baseline. Local median case speed ratios range from 1.24× to 1.48× (median 1.40×).

Completion remains 7/16: all nine allocation-limit failures remain. Proven pruning/reuse is now the priority alongside remaining compiled orchestration. Representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Funding-query reuse verified but no additional scaling case completes

The [opt-in exact reuse prototype](buying-behavior-compiled-continuation-plan.md#exact-funding-query-reuse-prototype-does-not-clear-another-scaling-case) preserves complete cached/uncached results across 24 seeded cases and explicit key-boundary checks. It reduces allocation work in two small cases but leaves scaling completion at 7/16, with no hits in limited cases.

The bounded Python cache remains disabled by default and is not a compiled/population-ready implementation. Validated closing bounds are the next search-work priority. Economic adoption/validation and full-world integration remain open; the full implementation goal remains active.

## Certified closing integration clears four additional scaling cases

The [opt-in certified closing bridge](buying-behavior-compiled-continuation-plan.md#certified-closing-bridge-advances-connected-scaling-to-eleven-cases) preserves complete results across 24 seeded cases and retains general-search fallback. The unchanged fixtures now complete 11/16 cases, up from 7/16, with closing proof work explicitly charged alongside action prefixes. All previously completed results remain identical.

Five cases still hit closing allocation/work limits. This remains a Python integration bridge, disabled by default; fully compiled orchestration, representative performance, economic adoption/validation and full-world integration remain open. The full implementation goal remains active.

## Exact closing reuse reduces charged work; completion remains eleven cases

The [opt-in closing memo](buying-behavior-compiled-continuation-plan.md#exact-closing-selection-reuse-reduces-work-without-clearing-a-further-case) preserves complete results across the seeded campaign and all eleven completed scaling cases. Eighteen targeted tests pass. The newly solved two-period case drops from 3,708 to 2,304 allocations, but completion remains 11/16 and five cases still reach limits.

Earlier-decision bounds and distinct closing-state work remain bottlenecks. The cache is a bounded Python prototype, disabled by default. Fully compiled orchestration, representative performance, economic adoption/validation and full-world integration remain open; the full implementation goal remains active.


## Handoff checkpoint prepared

The user requested durable progress and a handoff for another AI if the token limit is reached. The [handoff](buying-behavior-handoff.md) records accepted decisions, implementation boundaries, preservation requirements, verification scope, reproduction commands and next work. The closing-memo archived replay exited successfully: all 16 fingerprints match and all 265 source hashes match both archive and working files. The full goal remains active and incomplete.

## Connected continuation bound tested

The connected solver now has an opt-in post-purchase continuation envelope, with evaluation work charged to the shared budget and pruned arena branches released. Six targeted tests pass, including 24 seeded full-result comparisons and independent-oracle coverage. All eleven completed synthetic scaling results remain unchanged; completion stays 11/16. The bound prunes some single-line suffixes but none of the screened two-line searches. Evidence is preserved under `stats/buying-implementation/20261012-connected-continuation-bound/`. Stronger prefix/shared-resource bounds, full compilation and the economic/integration gates remain open.

Archived continuation-bound replay verification completed: all 16 fingerprints match; all 266 source hashes match current and archived files. See `20261012-connected-continuation-bound/verification.json`.

## Prefix proofs advance connected completion to twelve cases

Resumable compiled action traversal now supports opt-in subtree pruning by the existing prefix and common-first-production bounds. Proof work is charged to the shared budget; unsupported or unbudgeted proofs cannot restrict actions. Ten targeted tests pass, plus four diagnostic-counter checks. The screen completes 12/16. Newly completed case 6 matches the larger-budget connected closing search's entire public result, reducing allocations from 12,270 to 1,353 at value 13. Cases 7 and 13–15 remain limited.

Evidence, source snapshot and reproduction script: `stats/buying-implementation/20261012-connected-prefix-bound/`. Final archived replay confirmation belongs in `verification.json`. The [handoff](buying-behavior-handoff.md) records this checkpoint. Joint closing proof work, fully compiled orchestration, representative performance and all outstanding economic/world/adoption gates remain open.

## Proof reuse advances connected completion to thirteen cases

Existing normalized bound and proposal-hint caches are now available to the connected search, alongside an opt-in cash-relaxed joint proof. Defaults remain off. Ten targeted tests pass; all twelve previously completed public screen results are unchanged. Case 13 now completes and matches the larger-budget connected closing search's complete result: value 17, 9,957 versus 1,292 allocations. Cases 7, 14 and 15 remain limited. Evidence: `stats/buying-implementation/20261012-connected-proof-memo/`.

The user asked whether work ends at 16/16. It does not: the small synthetic screen is only a solver checkpoint, and all model, population, full-world integration, economic validation and rollout requirements remain. The [handoff](buying-behavior-handoff.md) preserves this scope.


## Purchasing scope audit and corrected documentation

The user's explicit restriction forbids outside parameter or logic changes. The [scope audit](buying-behavior-scope-audit.md) verifies the active backend/browser model (57,960 T2 firms, 105 C3/C4 products), unchanged core/catalog files and retained production bodies. README old population/C5 claims and execution ordering were corrected; historical 60,000-company timing remains labeled historical. Plan and handoff now explicitly exclude outside model amendments.

Expanded diagnostic budgets complete the remaining three synthetic cases, but the original screen remains 13/16. Combined work is 20,890 for case 7, 34,234 for case 14 and 447,075 for case 15. This exposes the largest closing-proof cost without changing production parameters or claiming success at the original limits. Full-discovery terminal verification is recorded in `20261012-connected-integration-checkpoint/verification.json` when complete.


Integration checkpoint completed: 587 Python tests pass in 388.463 seconds; JavaScript checks pass; all 273 source hashes verify. No run from this checkpoint remains active.

## Dominant proof work measured and unsuccessful ordering restored

The case-15 diagnostic reproduced the complete expanded result and identifies 270,558 prefix-bound work units versus 164,876 closing units. A cheaper-bound-first experiment passed seven targeted tests and replayed all 16 screen fingerprints, but increased work in both large two-line cases without reducing allocations. It was rejected and the prior module restored. All 273 source hashes match the 587-test integration checkpoint again.

Evidence: `20261012-closing-proof-diagnosis/` and `20261012-prefix-proof-order/` under `stats/buying-implementation/`. Original-screen completion remains 13/16. Shared-proof evaluation and expensive fallback calls remain investigation targets; the full purchasing-only implementation goal remains active.

## Exact per-line recourse cache verified

An opt-in cache now avoids identical per-line continuation-envelope recomputation inside shared multi-line proofs. The complete numerical key is retained, and existing work charges remain unchanged. Twelve targeted tests pass; all sixteen screen result/failure payloads equal the prior version except the new cache statistics. Completion stays 13/16. Evidence: `stats/buying-implementation/20261012-shared-recourse-memo/`; warm paired timing and archived replay verification are recorded there when terminal. No outside economic parameter or logic changed.

Warm interleaved case-15 timing completed: median 15.5389 seconds without recourse cache versus 12.0806 seconds with it (22.3% lower; three measured samples each). Every public result and existing work counter matches. Each cached solve has 140,436 hits and 2,832 misses. This supports retaining the opt-in cache, not a population or tail-latency claim. See `20261012-shared-recourse-memo/timing.json`.

## Joint closing fallback reduces work without clearing another screen case

The opt-in fallback now applies the existing joint upper bound while preserving lexicographic traversal and strict pruning. Ten targeted tests pass. Original completion stays 13/16, but expanded case 15 drops from 23,749 to 12,124 allocations and 447,075 to 406,175 work units; case 14 also improves. All three expanded results match completely. Evidence: `stats/buying-implementation/20261012-joint-closing-fallback/`. No outside parameter or logic changed; the full implementation remains unfinished.

## Recorded order sizes expose the gap beyond the synthetic screen

The [recorded search-size audit](buying-behavior-recorded-search-geometry.md) verifies 30 archived trace files and measures 484 captured company-phase decisions without changing the economy. T1 median per-material-slot-feasible grid is 18,564; the largest C3 grid is 1,460,317,392,681,147. These are exact stock/lot/slot grid counts, not solver work, profitable-policy counts or population estimates. The systematic startup sample and missing callbacks are explicitly separated.

Three tests and complete archived-source replay pass. Evidence: `stats/buying-implementation/20261012-recorded-search-geometry/`. This makes recorded quantity ranges and complete pre-purchase state capture the next representative-scaling priority. The original synthetic screen remains 13/16; neither those cases nor this grid analysis establish production readiness.

## 2026-10-12 scope re-audit

Rechecked the current workspace at the user’s request. Evidence is in `stats/buying-implementation/20261012-scope-reaudit/`: `audit_scope.py`, `scope-audit.json`, `browser.json`, `source-hashes.json`, `working.patch` and `tests.log`. Backend and effective browser metadata both retain 57,960 manufacturers and 105 C3/C4 products. The four retained reference/compiled phase bodies still match the base commit after removing explicit purchasing/observation hooks. Protected core, catalog, runtime, scheduler, recording, projections, service and browser catalog files remain unchanged. Production runtime has no experimental purchasing import.

Fresh targeted verification passed: **14 tests in 58.463 seconds**, covering D1/D2 contracts, transaction/accounting and checkpoint-policy checks, plus reference/compiled world equality with multiple-line ownership. Command: `PYTHONPATH=.pydeps:.:tests/py /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m unittest test_buying_contract test_buying_v2_world test_buying_v2_compiled_world`. This is a targeted suite, not a new full discovery or population-economics validation. The existing NumPy/SciPy compatibility warning was nonfatal; dependencies were unchanged.

README’s current settings and the canon’s superseding notice are correct; historical C5/60,000 measurements remain explicitly historical. Older source-hash statements were clarified to mean their checkpoint’s working tree, not all later source. No implementation or outside economic parameter was changed in this re-audit. The checkpoint-policy mismatch guard remains the documented compatibility change. No live process was operated. The implementation goal remains unfinished; the next implementation step remains the representative pre-purchase-state capture/adapter contract, with unresolved forecasts and production integration kept explicit.

## 2026-10-12 raw pre-purchase state capture

Added opt-in `tools/buying_v2/prepurchase_state.py:capture_t2` for sampled reference purchasing callbacks. It preserves every installed line in production order, all held input materials (including fractional quantities and inactive-phase holdings), input/output slot and total storage quantities, current quotes/bases, sampled offers with stable supplier/owner IDs, opening/current seller books, deferred seller receipts and switching income, and the caller-supplied phase-entry overhead snapshot. Config is copied for provenance. It neither changes the world nor evaluates a purchasing policy.

This resolves a necessary adapter boundary: the world’s finished inventory still contains stock sold through the phase book until settlement. Pending book transactions must remain separate, and overhead must not be recomputed at buyer entry. This raw capture is not a complete continuation-state projection or checkpoint; forecasts, horizon and terminal valuation remain explicitly missing. It is reference-only diagnostic code, not a population hot-path implementation. Existing production kernels and economic parameters are unchanged.

Four tests passed in 2.016 seconds, including fractional holdings, independent copies, all world/book array nonmutation, installed/active phase distinction, missing-snapshot and wrong-book rejection, and actual reference-phase capture on/off equality for every world array and cost sinks under the same D3 comparator. Evidence and copies of the two added sources: `stats/buying-implementation/20261012-prepurchase-state/`. This is a small fixture test, not full-population or economic validation; source copies are not a standalone replay archive.

Next: collect bounded real pre-purchase samples through this callback in an isolated identified run, audit their reconciliation with phase-end settlements, and define the continuation projection against those records. Keep future forecast/terminal assumptions unresolved until supported and adopted; do not substitute synthetic own-quote values as the real model.

## 2026-10-12 isolated raw-state runs and settlement reconciliation

Added `prepurchase_run.py` with an opt-in `CaptureEngine` subclass of the unchanged D3 reference engine, plus `prepurchase_audit.py` for persisted-record checks. It captures before purchases and reconciles sampled firms and their discovered suppliers against phase-end settlement: cash receipts, stock movements and book value. These tools do not activate a new policy or change outside economic rules. The runner refuses an existing output directory and archives source/configuration/hashes.

Runs (all seed 137, fresh isolated worlds, no checkpoint):

| Evidence directory under stats/buying-implementation | Configuration/window | Findings |
| --- | --- | --- |
| `20261012-prepurchase-sample-137` | 300 manufacturers, 1,000 distributors, ticks 1–6, sample 12/phase | 72 captures, 72 callback-not-observed; own-line settlement had no positive sales |
| `20261012-prepurchase-sample-4200-137` | 4,200 manufacturers, 1,000 distributors, ticks 1–30, sample 32/phase | 963 captures, 957 callback-not-observed; own-line settlement still had no positive sales |
| `20261012-prepurchase-suppliers-137` | 300 manufacturers, 1,000 distributors, ticks 1–6, sample 12/phase; added supplier reconciliation | 72 captures; 65 positive supplier/phase records, 332,000 units; all sampled cash/units/book-value checks pass |

The first two runs exposed a coverage limitation: checking only buyers’ own lines did not exercise upstream seller receipts. They remain preserved, and the last run explicitly covers discovered counterparties. The 332,000 figure sums full-phase sales for selected suppliers, including sales to unsampled buyers; it is not purchases by the 72 captured buyers or a whole-economy total. Sampling is systematic with hash rotation and missing callbacks are explicit; none of these counts is a population estimate. Population overrides are isolated experiment inputs, not changed defaults.

Five tests pass in 5.133 seconds: capture nonmutation and identity validation, real-phase and full-tick capture on/off world-array/state/observation equality, persisted reconciliation, and rejection of a deliberately corrupted cash total. An earlier test failed because it assumed the first phase had an active sampled buyer; the test now selects a nonempty settlement. The failed log is retained. The latest `verification.json` verifies all archived/current source hashes and the capture-file hash. No archived runtime replay is claimed. All run/test handles exited successfully.

Reproduce: `PYTHONPATH=.pydeps:.:tests/py /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m tools.buying_v2.prepurchase_run --output NEW_DIRECTORY --ticks 6 --sample 12 --cfg '{"t2FirmCount":300,"distributorCount":1000,"seed":137}'`. Tests: `-m unittest test_buying_v2_prepurchase_state test_buying_v2_prepurchase_run`. Import `prepurchase_audit.audit` with the captures.jsonl path for offline checks.

Next implement and independently test the raw-record-to-continuation-state projection with explicit phase-frozen overhead and pending settlements. Raw records still lack an adopted forecast/horizon/terminal valuation and must not be presented as complete solver inputs. Full population, performance, model adoption and rollout gates remain open.

## 2026-10-12 frozen phase overhead in the reference planner

Raw-state mapping exposed a timing mismatch: the reference ledger’s `before` gate recomputed overhead at buyer entry, while the real T2 engine freezes overhead at phase entry. Earlier transactions can change equity, so these are not interchangeable. Added optional `Purchase.frozen_overhead` to the research reference ledger and scenario validation. Finite negative values are valid (switching-income forecasts can offset rent); boolean/nonfinite inputs and ambiguous `after` timing reject. The value changes only the production gate; it posts no rent, fee or cash entry. Existing events default to `None` and retain their previous behavior. Production kernels and parameters are unchanged.

The independent event-tree oracle includes an explicitly supplied snapshot in its observed purchase history. The final-purchase adapter uses the same frozen input; independent event-tree versus compiled basket results agree for negative, zero, intermediate and prohibitive overhead values. The unchanged compiled calendar schema cannot yet carry this field: `compile_calendar` now explicitly rejects it instead of silently losing it. This is an intentional incomplete integration boundary, not a production-ready fix. Do not remove that rejection until encoding, queries, execution and observations preserve the snapshot.

Evidence: `stats/buying-implementation/20261012-frozen-overhead-reference/`. **33 tests pass in 17.383 seconds**, running `test_buying_v2_frozen_overhead test_buying_v2_phase_ledger test_buying_v2_continuation_program test_buying_v2_closing_allocation` with the established Python 3.12 interpreter/PYTHONPATH. The boundary fixture produces zero units with recomputed overhead 100 and five with frozen overhead 0, with no rent posting. Six changed source/test files are copied and hashed. This is not a complete standalone archive or archived replay. All handles exited.

Next: version the compiled calendar to preserve frozen overhead through hypothetical own-quote queries, actual purchases, observation/history decoding and closing/prefix adapters; compare complete connected results with the independent oracle. Then finish raw-record state projection, including pending book settlements. The recorded sample does not supply adopted forecasts or terminal values, and all broader master-plan gates remain open.

## 2026-10-12 compiled frozen-overhead integration

Completed the research compiled path for `Purchase.frozen_overhead`. Legacy events retain schema 1 and their original byte layout; explicit snapshots use calendar schema 2 and timing code 2 with an appended float. Decode rejects schema mismatch. Own-quote queries preserve the snapshot, compiled production applies it without posting a transfer, grouping distinguishes observed snapshots, and numeric observations/history retain it. Closing/prefix adapters preserve the event field. The previous explicit compiled rejection is superseded by this verified support. Production kernels, defaults and outside economic rules remain unchanged.

**30 tests passed in 44.863 seconds**, covering frozen reference behavior, complete connected-vs-independent-oracle comparison in resident and arena execution (including endogenous funding and observations), differing scenario snapshots, combined closing/pruning/memo options, calendar corruption/round trips, history/query/observation regressions, and the existing 24-case seeded arena/oracle campaign. Command modules: `test_buying_v2_frozen_overhead test_buying_v2_continuation_observation test_buying_v2_continuation_history test_buying_v2_continuation_program test_buying_v2_continuation_query test_buying_v2_continuation_arena_search`.

Evidence: `stats/buying-implementation/20261012-frozen-overhead-compiled/`. All **300** source files match their hashes in both workspace and snapshot. Running `test_buying_v2_frozen_overhead` from `/tmp` with the archived source/test paths in PYTHONPATH passed **8 tests in 38.542 seconds**. Archive and working test handles exited successfully. This is not full discovery, full population timing, or an economic validation. The frozen-overhead wire contract is appended to the compiled continuation plan.

Next finish the raw-record-to-planner projection, preserving all installed lines/materials, fractional-state handling and deferred book stock/basis/receipt timing. The captures still do not supply adopted forecasts, horizon or terminal values. Solver scaling, full-world integration, economic gates and rollout remain unfinished.

## 2026-10-12 captured-company projection

Added `prepurchase_projection.py:project`, mapping raw capture records into the research Company/State/Purchase types. It retains all materials and installed lines in actual execution order, validates recipe/catalog identity, derives physical slot/capacity limits from the captured configuration, carries phase-frozen overhead and existing switching state, and records previously completed lower-complexity phases. The purchase event leaves funded demand empty for the explicit funding mechanism; it does not invent demand or a sales forecast. Placeholder line value tables are used only by the mechanical ledger, not as terminal valuation or a production policy.

The projected state retains the phase-opening sell-side book and buyer-entry live inventory separately. Committed sales and pending switching income remain deferred. `Projection.settlement(additional_sales, additional_fee_income)` requires explicit further deliveries, adds prior commitments once and rejects future sales beyond remaining opening stock. Pending cash must reconcile to committed revenue plus switching income before projection. This preserves the real book’s mixed old/new cost basis and prevents early financing or double sales. Ledger accounts track flows from this projection boundary, not the company’s earlier whole-tick earnings.

**9 tests pass in 6.511 seconds** (`test_buying_v2_prepurchase_projection test_buying_v2_prepurchase_state`): reference and compiled settlement equal the actual InputMarket settlement for positive committed sales/fees and mixed basis; zero-purchase production equals the actual phase’s output, input holdings, cash and basis; multiple installed lines/materials/order are retained; invalid receipts, fractional holdings and over-cap finished stock reject explicitly.

Evidence: `stats/buying-implementation/20261012-prepurchase-projection/`. `audit_records.py` verifies both original capture hashes and projects all **1,035 captures** (72 from the final 300-company supplier run, 963 from the 4,200-company run). Cash, equity, physical room, installed IDs and frozen overhead reconcile; no captured record is unsupported. Source is copied and hashed; no archived execution replay is claimed. All commands exited. No production code or external parameter changed.

Limits remain material: the integer planner cannot yet represent fractional held goods or finished stock above a reallocated output slot. The adapter raises `ProjectionUnsupported` instead of rounding quantities or enlarging slots. These cases remain implementation requirements, not a narrowed accepted model. The samples do not prove those states never occur. Forecasts, horizon/terminal choices, full-world solver integration and population performance remain unresolved. Next address those state-domain gaps, then use projected records for faithful scaling tests with explicitly supplied diagnostic continuation scenarios rather than claiming those scenarios are adopted forecasts.

## 2026-10-12 finished stock above a reallocated slot

The reference ledger and compiled resident planner now retain existing finished goods above their nominal output slot, provided total physical storage remains valid. Production uses `max(0, min(machine_batches, floor((slot-stock)/yield)))`; after sales bring stock below the original slot, production resumes only up to that same slot. No inventory is removed and no capacity is enlarged. The raw-state adapter now accepts these states. Production kernels and configuration are unchanged.

Updated ordinary continuation and shared-production bounds to include existing above-slot stock in terminal-table coverage and optimistic inventory envelopes. The closing adapter clamps production and includes above-slot inventory in numeric range/table checks. This is necessary for correctness: valuing only the smaller slot can underestimate the value of goods already owned and wrongly prune a policy. The older standalone two-period `continuation_oracle.py` is not this connected phase planner and retains its earlier contract.

Evidence: `stats/buying-implementation/20261012-overcap-finished/`. **46 regression tests pass in 46.539 seconds**, covering ledger, projection, connected reference/compiled comparisons, closing search, ordinary/shared bounds, and terminal-value spikes above slot limits. One additional actual-engine phase test passes: both the real phase and projected ledger retain above-slot goods with matching cash and basis. The initial run exposed a remaining compiled resident resource rejection; it was removed while physical-storage checking remains. Initial failure logs are preserved. Ten changed source/test files are copied and hashed; no archived replay is claimed. All test handles exited successfully.

Command modules: `test_buying_v2_overcap_finished test_buying_v2_prepurchase_projection test_buying_v2_phase_ledger test_buying_v2_continuation_bound test_buying_v2_shared_first_bound test_buying_v2_shared_joint_first_bound test_buying_v2_closing_allocation`, plus the separately added `test_actual_phase_preserves_overallocated_finished_goods` method.

Next address fractional holdings without rounding or silently changing the production gate, then run faithful projected-state scaling with explicitly labeled diagnostic scenarios. Above-slot finished inventory is no longer a projection gap; fractional quantities, adopted forecasts/terminal valuation, population practicality and broader master-plan gates remain unfinished.

## 2026-10-12 native fractional production arithmetic

Baseline world arrays and checkpoints retain fractional inventory. Whole-quantity purchasing does not authorize truncating pre-existing holdings. Added `native_inventory.py`, an isolated compiled production primitive retaining float64 quantities in original item units and the real recipe-operation order. It accepts whole production batches, retains fractional inputs/finished goods, and preserves the existing basis, cash, overhead and gate arithmetic. No production kernel or configuration was modified.

Two tempting representations are demonstrably unsafe: (1) scaling quantities by two and unit prices/costs by one half changes the fixed 1e-9 gate tolerance—one fixture changes from zero to one production batch; (2) holding a fixed fractional residue differs from native floating arithmetic: `(0.1+3)-3 != 0.1`. Do not use either shortcut to claim exact parity. The new primitive preserves native subtraction rather than canonicalizing the residue.

Evidence: `stats/buying-implementation/20261012-native-fractional-production/`. **4 tests pass in 0.655 seconds**. Three fractions (0.1, 0.5, 0.999999999) match the real reference phase exactly for all held materials, cash, finished units/basis and production. Tests also preserve fractional quantities through the ordinary save/load path and capture the two representation counterexamples. Source copies/hashes are preserved; no archived replay is claimed. All commands exited.

This is a primitive for the required integration, not completed fractional planner support. The current connected ledger/resident inventory buffers, state serialization, observation/history encodings, funding caps, terminal-value lookup and exact bounds still assume integer holdings. Their redesign must retain native quantities and explicit valuation domains; the raw projection must continue rejecting unsupported fractions until those paths support them. Do not change terminal-value semantics implicitly or infer forecasts from this arithmetic work. Next implement the native-float state/valuation contract with the independent reference before wiring it through compiled search.

## 2026-10-12 native fractional reference ledger and valuation domain

The independent phase ledger now retains fractional held/finished inventory and fractional input slots. Purchases and sales remain whole units; selling an opening book floors available stock and leaves its fractional residue. Production retains native float subtraction, and a no-purchase input’s native basis remains unchanged rather than being recomputed as quantity×basis/quantity. Integer paths retain their earlier normalization behavior for exact regression compatibility. Structural validation uses a rounded-up copy only to reuse recipe/offer validation; execution quantities and slots are never rounded.

Added explicit `LinearQuantityValue(quantities, values)` for caller-declared piecewise-linear terminal values in native item units, with immutable copied knots and no extrapolation. Ordinary integer tables continue working at integer quantities and explicitly reject fractional lookups. This is a representational capability, not an adopted interpolation/calibration/terminal-value model; callers must deliberately supply a native curve. Mechanical phase transitions use zero internal terminal values only, independently of actual horizon valuation.

Evidence: `stats/buying-implementation/20261012-native-reference-ledger/`. **29 tests passed in 29.454 seconds** across native ledger, existing phase ledger, calendar, and seeded connected arena/oracle regressions. After adding explicit optimization guards, **6 native-ledger tests passed in 0.610 seconds**. Tests cover fractional slots with whole purchases, weighted basis, native production at three fractions against the previously real-engine-verified primitive, whole sales leaving residues, explicit value domains, rejection of silent integer compilation, and safe bound/closing fallback. Source copies/hashes and logs are preserved; no archived replay is claimed. All handles exited.

Integration is intentionally incomplete: compiled calendar/state and event-tree search now explicitly reject fractional resources, rather than truncating them. Integer-only closing search returns unavailable; ordinary/shared upper bounds return infinity for fractional state so they cannot prune from an invalid integer approximation. The raw projector still rejects fractions until connected support exists. No production kernel or configuration changed.

Next implement native-float planner state and quantity-domain valuation in the compiled wire format, numeric observations/history, funding/allocation traversal and terminal evaluation. Preserve the new rejection boundaries until complete differential tests cover those paths. Forecast adoption, realistic scaling, runtime/persistence/UI integration and economic/rollout gates remain open.

## 2026-10-12 compiled native terminal valuation

Schema 3 now carries explicit terminal valuation modes and native quantity knots, supporting mixed integer tables and caller-declared piecewise-linear curves. Schema 1/2 bytes remain unchanged when no native curve is present. Compiled binary-search interpolation agrees exactly with the independent Python valuation at tested fractional points; missing integer values and native extrapolation reject. Canonical decoding rejects version/mode/coordinate corruption. Frozen overhead is compatible with schema 3. Both resident and arena terminal/result paths now use the new representation.

The event-tree reference can use native terminal curves with integer state. Integer-only bounds and closing adapters decline these curves rather than interpreting knot positions as inventory indices. General exact connected search remains available and its complete public result is unchanged when optional bounds are requested. No forecast or terminal-value calibration has been adopted.

Evidence: `stats/buying-implementation/20261012-native-terminal-schema/`. Initial **16 tests passed in 27.417 seconds** (native curves, calendar, results and terminal regressions). An expanded **8 tests passed in 8.703 seconds** (five native tests plus existing arena cases, including the 24-case seeded oracle campaign). These counts overlap and are not a summed unique-suite count. Archived source execution from `/tmp` passed all **5 native tests in 27.568 seconds**. All **308** working and archived source hashes verify. Logs, source snapshot and verification.json are preserved. All handles exited.

Full comparisons cover decisions, endogenous funding, final states, values and observations against the independent oracle in resident/arena execution, plus mixed legacy/native values, frozen overhead and safe optimization fallback. This is not full discovery or population performance. Production kernels and economic parameters remain unchanged.

Next integrate float64 held/finished inventory and input slots into compiled state, actual/hypothetical purchases, whole-sale settlement, observations/history and action bounds. Keep fractional-state compiler/projector guards until those paths pass differential tests. The valuation representation is ready, but fractional connected state and broader integration/forecast/economic/performance requirements remain unfinished.

## 2026-10-12 native compiled resident execution

Schema 4 marks fractional initial resources/input slots and retains native float64 held/finished/book quantities and slots in Resident/ArenaResident. Snapshots and forks no longer cast these quantities to integers. Prescribed purchases and production match the independent native ledger, preserving no-purchase basis and whole-unit sales. Opening-book observations containing fractional stock use observation schema 3 with their quantity vector in the float payload; history validation retains it without truncation. The wire details are appended to the compiled continuation plan.

Evidence: `stats/buying-implementation/20261012-native-resident/`. Initial **17 tests passed in 33.188 seconds** across native execution/ledger and legacy resident/observation/seeded arena-search regressions. Expanded **17 tests passed in 11.819 seconds**, adding native arena, own-quote query and failed-purchase atomicity, plus history/calendar checks. Counts overlap; do not sum them as unique tests. Archived execution from `/tmp` passed the **4 native resident tests in 14.648 seconds**. All **309** current and archived source hashes verify. All test handles exited successfully.

Step-by-step comparisons cover cash, inventory, bases, preferences, accounts, pending books, rent, tick-end state, decoded observations and final terminal value. Native arena own-quote execution also agrees with an independently constructed reference query. No production kernel, live process, economic parameter or forecast calibration changed.

Fractional allocation optimization is still not enabled: connected and event-tree search retain explicit rejection guards. The older per-event Executor adapter rejects schema 4 and directs native execution to Resident. The raw projector remains guarded until full search support. Next audit action ranges and funding caps for native float arithmetic, then enable exhaustive independent and connected search with differential tests. In particular, subtraction-based remaining-space calculations need boundary checks against the actual addition-based inventory constraint; do not silently truncate fractional resources. Larger integration, model/forecast, population-performance and economic/rollout gates remain unfinished.

## Implementation and documentation audit after native Resident support

Refreshed the user-requested purchasing-only audit. Evidence: `stats/buying-implementation/20261012-scope-docs-final-audit/`. Backend/browser checks confirm 57,960 T2 companies and 105 C3/C4 products; four retained production phase bodies remain AST-identical after explicit purchasing/observer hooks are removed, and protected model/catalog/runtime paths remain unchanged. All nine prior scope-audit manifest files match, including four production files and three test modules. The prior 14-test result is retained as historical evidence; this refresh did not rerun tests or claim a new full suite.

Corrected a handoff documentation defect: superseded “Latest” sections and old “Next” instructions could misdirect another AI. A current status section now takes precedence and older milestones are explicitly historical. Native Resident/ArenaResident prescribed execution is supported; fractional search and raw projection remain guarded pending allocation/funding boundary audits. Production defaults and outside rules were not changed. Full implementation remains unfinished; 16/16 synthetic cases would still be only an intermediate solver gate.

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

## Captured-state connected search diagnostic

`tools/buying_v2/captured_search.py` verifies the source capture hash, selects the minimum/maximum stock-only offer grid in each phase, projects the full company state and runs bounded connected continuation funding. It preserves actual cash, holdings, slots, installed lines, offers, prices and frozen overhead. The explicit diagnostic calendar is one purchase phase, settlement of already committed sales, then a later book with either zero sales or full clearance at captured quotes, with zero terminal values and no new arrivals. Neither scenario is an adopted forecast. These selected extremes are not a population-representative sample.

Evidence: `stats/buying-implementation/20261012-captured-search/`, using 963 preserved records from the 4,200-company seed-137 ticks 1–30 capture run. Four selected states produced eight diagnostics. **All eight hit the 4,000-allocation limit in the first funding query**, before a funded decision completed; the combined prefix/proof budget remained 16,000. No partial policy or approximate value was returned. The original small synthetic screen is not rerun or redefined by this diagnostic.

| Case | Phase | Tick | Firm | Offers | Actual stock-grid size |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0, minimum C3 | 3 | 1 | 4111 | 10 | 268213632705433400832 |
| 1, maximum C3 | 3 | 22 | 4032 | 12 | 731361510717578505039231123019863673938241278158001 |
| 2, minimum C4 | 4 | 1 | 0 | 10 | 1 |
| 3, maximum C4 | 4 | 26 | 5 | 12 | 278645043572459319606953080468039209 |

Grid sizes are products of available whole-lot offer ranges before cash, slot, fee and production constraints. They are not predicted runtime. Notably, case 2 has no positive actual stock but still exhausts the first hypothetical funding query: continuation funding intentionally derives demand with own-quote stock relaxation. Capping those queries to actual stock would change the model and is not a valid performance fix.

Single observed case times range roughly 0.50–17.15 seconds and include specialization/compilation where encountered; they are not warm median/p95 results. The first case reports about 68.7 MB allocated history buffers alone, with separate policy/funding/result/branch buffers in its diagnostics; this is not total process RSS. Source snapshots, selected raw records, per-case results, fingerprints, specification and failures are preserved. Two diagnostic construction/selection tests pass; full real-state correctness is not inferred from those two tests.

Next investigate exact native-resource funding bounds or a more scalable exact search representation using these preserved failures. Do not reduce line/supplier scope, cap hypothetical demand to live stock, adopt approximate answers, increase acceptance budgets to hide failure, or change production rules. Forecast adoption, full-world integration, population performance and economic/rollout gates remain open.

Reproduce with the established Python 3.12 interpreter and `PYTHONPATH=.pydeps:.:tests/py`: `-m tools.buying_v2.captured_search --captures stats/buying-implementation/20261012-prepurchase-sample-4200-137/captures.jsonl --output NEW_DIRECTORY`. Default diagnostic limits are 4,000 allocations and 16,000 combined work. The output directory must not exist.

Archived replay from `/tmp` reproduces all eight complete failure payload fingerprints. All 314 source hashes match working and archived files (`verification.json`). Both runs and tests exited; no milestone process remains active. Production kernels, parameters and live runs were untouched.

## Native-resource continuation envelope

`continuation_bound.py` now accepts fractional resources with explicit piecewise-linear terminal curves. Its relaxed value is current cash minus initial cash, plus the initial/current arrears difference, optimistic future sales and specified fee income, plus global terminal-curve knot maxima. It retains optimistic book timing and capacity, ignores procurement/conversion/rent costs, and applies the existing numerical cushion. Native resources deliberately skip the integer-only cost refinement. Missing valuation-domain coverage returns infinity, so it cannot prune. This adds no forecast calibration or economic rule.

The native bound is used only through existing optional proof/pruning modes. `captured_search.py --prune-prefix` measures it without changing default search or acceptance budgets. Evidence: `stats/buying-implementation/20261012-captured-native-bound/`. Twenty-four targeted tests pass in 13.236 seconds, including exhaustive feasible allocations/suffixes, multiple lines/periods, terminal peaks and complete optimized/unoptimized search comparisons. Ten archived native-bound/search tests pass from `/tmp`; final source hashes verify. The initial experiment snapshot differs from `final-source/` only in the subsequently expanded native-bound test; both are preserved.

At the same 4,000-allocation/16,000-work limits, **one of eight captured diagnostics completes**, versus zero previously. Case 3/full-clearance returns value 6,211.440000000002, a zero-purchase policy, 14 allocations, 2,700 prefixes and 2,592 bound-work units. Its full state and value replay exactly through the independent ledger (`completed-case-check.json`). This is feasibility/result replay, not a separate exhaustive optimum check. A simpler attempted global no-purchase certificate was insufficient (positive-purchase upper 6,227.56 exceeds the returned value); that failed shortcut is preserved rather than used as proof.

The other seven cases still hit limits. Zero-sale cases 0/2 and full-clearance case 2 now need only one completed allocation but still spend 8,005 prefix and 7,995 bound-work units. Case 0/full-clearance completes 202 allocations before the same work limit. Case 1 still hits 4,000 allocations under both scenarios; case 3/zero-sales reaches 136 allocations before the work limit. Observed single-run times are about 6.50–30.47 seconds, including specialization/compilation and local test overlap; they are not a population latency benchmark or an improvement claim.

Next address exact native prefix feasibility and interval-level pruning so a proven unprofitable range need not be checked one quantity at a time. Do not infer monotonicity from one pruned allocation: future production and valuation can change with quantity. Preserve full supplier/line scope, own-quote funding semantics, tie-breaking and explicit work limits. The option remains off by default, the original 16-case screen was not rerun, and full model/integration/performance/economic/rollout gates remain open. Production code and outside parameters are unchanged.

All milestone commands exited; no process remains active. All 315 final working/archive source hashes match. No full archived replay of the eight-case diagnostic is claimed.

## Native slot feasibility during action traversal

`AllocationFrame` now keeps native per-material inventory plus a saved value per search depth. It adds each whole-lot quantity in the same offer order as the ledger and rejects a prefix once inventory exceeds `max(opening held, slot)`. Higher quantities at that same prefix cannot restore feasibility, so that infeasible tail is skipped. Backtracking, external pruning, resume and fork restore the saved floating value directly, never by subtraction. Stock/cash limits, lexicographic order and the full ledger's fee/production/physical-storage checks remain in place. This is a feasibility proof, not an assumption that economic value is monotone in quantity.

Verification: **15 targeted tests passed in 26.424 seconds**, including 50 seeded comparisons with independent native-addition Cartesian filtering, one-prefix budget resume, fork isolation and externally pruned branches. **Nine archived-source tests passed from `/tmp` in 27.963 seconds**. Evidence: `stats/buying-implementation/20261012-native-action-slots/tests.log` and `stats/buying-implementation/20261012-captured-native-slots/`. All 316 working/archive source hashes match. The earlier test expecting the entire stock grid was updated to require exactly the native-slot-feasible grid; complete search remains checked against the independent exhaustive oracle.

The same eight captured diagnostics, with the existing optional bound and unchanged 4,000-allocation/16,000-work budgets, still complete **one of eight**. Case 1 under both sales assumptions drops from 4,000 completed allocations to 239, but now exhausts combined work (8,134 prefixes + 7,866 bound work). Other cases retain their previous completion status. The sole completed case's full public result—policies, funding, state, observations and value—is identical to the preceding version after excluding diagnostics. This is not a broad performance success; single-run timings overlap archived tests and are not warm/population measurements.

Next develop justified interval-level economic bounds and/or cheaper bound evaluation to reduce repeated feasible-prefix checks. Preserve the saved native arithmetic, existing budgets, full supplier/line scope and own-quote funding semantics. No production code or outside economic parameter changed. All milestone commands exited; no process remains active. Full model/integration/performance/economic/rollout gates remain open.

## Optional whole-range gross-return proof

`continuation_range.py` caches a relaxed gross-return ceiling for each observed decision/query and conditional future distribution. The ceiling ignores purchase/conversion/rent costs, retains optimistic sales-book/capacity bounds and terminal maxima, and uses the established rounding cushion. For a fixed prefix, downward-rounded mandatory goods payment is a lower bound for every nonnegative suffix and every larger final coordinate. Therefore `gross ceiling − minimum goods payment + rounding allowance` bounds that entire tail. Only strict inferiority to the incumbent permits skipping it; this does not assume that actual production, profit or terminal value is monotone in quantity. The existing prefix proof remains the fallback when the tail cannot be certified.

The opt-in `prune_ranges=True` requires prefix pruning; defaults remain off. `AllocationFrame` accepts an explicit tail certificate and restores the saved inventory before exhausting that coordinate. `ControlStack` owns and releases one additional optional reference slot for the cached proof. Initial integration errors from using dictionary membership on the typed frame are preserved in `stats/buying-implementation/20261012-range-proof/tests.log`; the final implementation uses the declared reference field and mapping accessor.

Final verification: **15 targeted tests pass in 58.519 seconds**, including complete-result comparisons for all 24 seeded search fixtures, native supplied/endogenous cases, limits, native backtracking and control-frame checks. Evidence: `stats/buying-implementation/20261012-range-proof/final-tests.log`. The seeded comparisons cover policies, funding, terminal states, values and observations, not just objective values.

Captured diagnostic evidence: `stats/buying-implementation/20261012-captured-range-proof/`, same four preserved states, explicit scenarios and 4,000-allocation/16,000-work limits. Completion improves from **one to three of eight**:

| Case/scenario | Allocations | Prefixes | Bound work | Result |
| --- | ---: | ---: | ---: | --- |
| 0 / zero sales | 12 | 156 | 88 | Complete |
| 0 / full clearance | 4,000 | 4,212 | 8,304 | Allocation limit |
| 1 / zero sales | 1,482 | 6,111 | 9,889 | Work limit |
| 1 / full clearance | 1,482 | 6,111 | 9,889 | Work limit |
| 2 / zero sales | 12 | 150 | 81 | Complete |
| 2 / full clearance | 66 | 5,385 | 10,615 | Work limit |
| 3 / zero sales | 763 | 6,256 | 9,744 | Work limit |
| 3 / full clearance | 14 | 810 | 1,310 | Complete |

`verify_completed.py` independently replays all three completed states/values using recorded funded demands. The two new zero-sales cases additionally pass the coarse global certificate: every positive purchase has upper value below zero, while no purchase returns zero. The old case 3/full-clearance result remains unchanged; its simple coarse certificate is insufficient and is labeled false. These checks do not establish an adopted forecast or population readiness. Timings include specialization and concurrent tests and are not a warm latency claim.

Reproduce the diagnostic with the previous captured-search command plus `--prune-prefix --prune-ranges`, using a fresh output directory. Next address tighter cost/production-aware range bounds and the remaining feasible-basket combinatorics. Retain full line/supplier scope, query semantics, tie-breaking and explicit budgets; do not convert the remaining failures to approximate policies. The original 16-case screen was not rerun, and full implementation/economic/performance/rollout gates remain open. Production code and outside parameters are unchanged.

Archived-source execution from `/tmp` reproduces all eight complete result/failure fingerprints. All 318 working/archive source hashes match. The previously completed case retains its full public result. All milestone commands exited, and no process remains active (`verification.json`).

## Native cost-aware continuation envelope

The existing per-line relaxed profit envelope now converts held quantities, finished stock, production allowance and sales-tranche quantities to exact rational values before calculating resource breakpoints. The integer-numerator shortcut is removed. This permits native fractional resources in the existing optional `include_costs` refinement without truncating holdings or failing on fractional `Fraction(numerator, denominator)` arguments. The final value still rounds upward and receives the established continuation cushion.

The relaxation remains optimistic: fractional production, unlimited cheapest observed future input supply, independently reusable owned inputs for each line, relaxed gates/cash/rent/fees, and favorable allocation across sales opportunities. It subtracts minimum conversion and missing-input costs from relaxed sales profit; terminal maxima remain separate and optimistic. This is a solver bound, not a change to production costs, accounting, prices, gates or available information. The cached whole-range ceiling deliberately remains gross-only, since subtracting mandatory prefix payments from a cost-aware ceiling could double-count input costs.

Evidence: `stats/buying-implementation/20261012-native-cost-envelope/tests.log` records **20 tests passing in 63.816 seconds**. Coverage includes exhaustive native feasible allocations/suffixes, multi-line/multi-period oracle optima, an analytical fractional-profit case, complete native searches and all 24 seeded range-pruning comparisons. Native cost-aware bounds are finite and strictly tighter on the tested fixture; integer behavior remains covered.

At unchanged captured diagnostic budgets, completion rises from **three to four of eight** (`stats/buying-implementation/20261012-captured-native-cost/`). New case 1/full-clearance completes with value 216.64000000001397, 14 allocations, 864 prefixes and 1,418 bound-work units. Previously completed cases 0/zero-sales, 2/zero-sales and 3/full-clearance remain complete. Case 0/full-clearance drops from 4,000 completed allocations before failure to 40, but still exhausts work (5,367 prefixes + 10,633 bound work). Cases 1/zero-sales, 2/full-clearance and 3/zero-sales remain limited. No approximate result is returned.

All four completed final states/values replay through the independent reference ledger (`verify_completed.py`, `completed-case-checks.json`). Only the two zero-sales cases pass the simpler global no-purchase certificate; the new full-clearance optimum is not claimed to have an independent exhaustive captured-state proof. Single-run timings include specialization/concurrent testing and are not warm population latency measurements. The scenarios remain explicit diagnostics, not adopted forecasts.

Next address the four remaining cases through stronger interval/box proofs or equivalent exact search improvements, retaining multiple-line/shared-input support and historical-cost production gates. Do not restrict quantities to immediate recipe needs without a proof: excess cheap inputs can affect the weighted basis and gate. Full model adoption, integration, performance and economic/rollout gates remain open; the full goal remains active. Production code and outside parameters are unchanged.

All eight archived-source result/failure fingerprints match execution from `/tmp`. All 318 working/archive source hashes verify, and all three previously completed public results are unchanged. Every milestone command exited; no process remains active (`verification.json`).

## Conversion-aware whole-range ceiling

The optional range certificate now includes relaxed conversion costs while giving every input with an eligible purchase offer zero price inside the bound. Materials unavailable throughout the remaining calendar still have only their owned quantities. The per-line rational envelope maximizes sales proceeds minus conversion expense over relaxed fractional production and favorable sale opportunities; shared held inputs remain independently reusable across lines. Because purchase inputs are free in this ceiling, deducting the prefix's mandatory goods-payment lower bound does not double-count acquisition costs. Existing actual prices, purchases and production gates are untouched. Ordinary cost-aware bounds retain actual cheapest-offer costs; `free_inputs=True` requires `include_costs=True` explicitly.

Evidence: `stats/buying-implementation/20261012-conversion-range/tests.log` records **21 passing tests in 68.907 seconds**. The new check exhaustively verifies that the free-input ceiling minus actual goods payments bounds every feasible tested native allocation. It is tighter than gross return and no tighter than the fully priced envelope on the fixture. Existing exhaustive native/multi-period tests, complete native searches and all 24 seeded range-pruning comparisons also pass.

At unchanged 4,000-allocation/16,000-work budgets, the captured diagnostic remains **four of eight complete** (`stats/buying-implementation/20261012-captured-conversion-range/`). Cases 1 and 3/full-clearance both now use 14 allocations, 216 prefixes and 122 bound-work units: combined work falls from 2,282 and 2,120 respectively to 338. The two completed zero-sale cases remain unchanged. Case 0/full-clearance still exhausts work after 41 allocations, case 2/full-clearance after 74, and cases 1/3 zero-sales remain limited. This is a measured work reduction in selected diagnostics, not population readiness or a warm latency claim.

Next investigate ceilings conditioned on already fixed earlier offer coordinates. A decision-wide free-input ceiling can still allow inputs whose offers have all been fixed to zero; that weakens the proof for later quantity ranges. Any conditional certificate must preserve native arithmetic, account for prefix payment exactly once, maintain full resource/terminal coverage, and fall back conservatively when unsupported. Do not replace funded-demand semantics, shrink supplier/line scope, force immediate-use quantities, or increase the acceptance budgets. Full integration, model adoption, performance and economic/rollout gates remain unfinished; production code and outside parameters are unchanged.

Archived-source replay from `/tmp` reproduces all eight complete result/failure fingerprints. All 318 working/archive source hashes match; all four previously completed public results remain identical. Every milestone command exited, with no process left active (`verification.json`).

## Parent-conditioned range candidate rejected after measurement

Tested a conditional ceiling that adds the already fixed earlier allocations to relaxed owned inputs, removes their offers from the remaining decision, keeps cash untouched inside the ceiling, and deducts all mandatory prefix payments once afterward. It used one cached parent/ceiling per depth and returned an unavailable bound for unsupported physical-resource relaxations. The direct test verified removal of a fixed-zero complementary input, reuse across sibling quantities, and invalidation for a changed parent.

Candidate evidence: `stats/buying-implementation/20261012-parent-range/` and `20261012-captured-parent-range/`. Fifteen regression tests passed in 73.055 seconds, including all 24 seeded complete-result comparisons; the additional parent/cache test passed in 0.187 seconds. The candidate source, test and eight-case diagnostic are preserved under `20261012-captured-parent-range/source/`.

The candidate **does not improve captured completion: four of eight still complete**. Completed case 0/zero-sales rises from 244 to 308 combined work, case 2/zero-sales from 231 to 290, and both completed full-clearance cases from 338 to 432. Case 0/full-clearance now visits 974 allocations before the work limit, case 1/zero-sales 1,363, case 2/full-clearance 974 and case 3/zero-sales 638; none completes. Single-run timing is not a controlled speed comparison.

The candidate was therefore **not adopted**. Restored only the two changed research files, `continuation_range.py` and its range-pruning test module, from the preceding verified conversion-range snapshot. All 318 working source hashes match that snapshot (`restored-source-verification.json`); no production or outside-model file was changed. `restoration.json` records the exact action. Existing verified 4/8 behavior remains current; this does not restore an older economic model.

Next investigate bounded reuse of numerically equivalent conditional ceilings before reconsidering parent conditioning. A full allocation prefix can differ while producing the same relaxed owned resources; additionally, owned quantities of inputs still freely purchasable may not affect the bound. Any reduced cache key must be derived from all actual numerical/calendar dependencies and verified against complete results, with bounded memory and honest work charging. Preserve the failed candidate and keep full supplier/line scope and funding semantics. The full implementation goal remains active, with integration/model/performance/economic/rollout gates still open.

Archived candidate replay from `/tmp` reproduces all eight result/failure fingerprints; candidate source hashes match its archive, and all four completed public results match the retained version. Current working source deliberately matches the prior conversion-range snapshot, not the rejected candidate. All milestone commands exited, with no active process (`verification.json`).
