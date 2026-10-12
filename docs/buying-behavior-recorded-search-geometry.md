# Recorded purchasing search sizes

The small 16-case continuation screen does not yet cover the quantity ranges found in recorded company orders. A verified startup sample contains much larger allocation grids, even after enforcing each input's aggregate slot limit. This is evidence for expanding feasibility tests, not a runtime estimate or proof that every grid must be enumerated.

## Run and measurement

Input: `stats/buying-implementation/20261012-industrial-traces-fullpop-137/`, seed 137, ticks 1–30, full configured population, isolated D3 replenishment policy. The existing reconstruction proof verifies the captured plans. The new analysis rechecks all 30 trace file hashes and duplicate identities/tick coverage. It processes 720 systematic sampled company-phase identities: 484 captured decisions and 236 explicit callback-not-observed rows. Missing callbacks are not zero demand.

For each offer, divide opening stock and the recorded input-slot deficit by the common purchasing lot, rounding down. The independently capped grid is the product of `(cap + 1)` across offers. The slot-feasible grid additionally enforces that the sum purchased across suppliers of each material cannot exceed that material's recorded slot deficit. Its exact bounded-composition count uses inclusion/exclusion and multiplies across materials.

These counts include zero purchases. They do **not** apply shared cash, fees, total physical space, actual production gates, supplier preferences, forecast values or continuation decisions. They are therefore not counts of profitable/fully feasible policies or measurements of solver work. They use recorded slot limits from the D3 treatment; they do not infer an approved industrial objective or alter any parameter.

## Captured sample results

Quantiles use nearest rank among captured rows within the indicated tier/phase. Counts refer to sampled decisions, not distinct companies or estimated population frequencies.

| Tier and procurement phase | Captured / sampled | Grid equals one | Grid above 4,000 | Median slot-feasible grid | 95th percentile | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T1, all refinery procurement | 240 / 240 | 2 | 169 | 18,564 | 853,776 | 11,262,160 |
| T2, C3 phase | 159 / 240 | 126 | 32 | 1 | 7,621,359,583,761 | 1,460,317,392,681,147 |
| T2, C4 phase | 85 / 240 | 82 | 0 | 1 | 1 | 1,089 |

A grid of one means every recorded quantity coordinate is fixed to zero under stock/slot limits. It does not imply no possible production from owned inputs. The many zero-only C3/C4 samples can conceal the much larger active decisions; neither the median nor this startup sample establishes mature-state behavior.

The largest captured grid is seed 137, tick 22, T2 C3 phase, firm index 11,776: two materials, ten offers, nine positive-quantity offers, and up to 531 choices for an individual offer. Its independent stock/slot grid is 3,111,342,230,352,504,753; coupling each material's supplier quantities reduces that to 1,460,317,392,681,147. These are exact integer counts under the stated constraints, not simulation timing estimates.

## Consequences for implementation

Keep the 16-case screen as a correctness/work-budget regression. Even reaching 16/16 would not demonstrate configured-population practicality. Further scaling fixtures must cover recorded offer counts and lot/slot ranges, including rare large decisions and zero-only orders, rather than only increasing capacity within small artificial examples.

The traces do not contain a complete continuation problem: line execution state, an approved future-event/forecast model and all terminal-value inputs still need to be supplied or captured under an explicit contract. Do not invent them to turn this grid audit into a supposedly representative end-to-end timing benchmark. The next integration step is an adapter/capture contract connecting recorded pre-purchase state to the full solver inputs while retaining the purchasing-only boundary. Population scheduling, shared inventory, actual forecasts and multi-line ownership remain separate validation requirements.

Do not multiply these grid sizes by company counts to predict runtime. Existing pruning and decomposition may skip large regions; that must be measured on fully specified problems. Conversely, a small grid does not bound the work of endogenous multi-period funding.

## Reproduction and verification

Analysis tool: `tools/buying_v2/trace_search_geometry.py`.

```sh
PYTHONPATH=.pydeps:. /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m tools.buying_v2.trace_search_geometry --run stats/buying-implementation/20261012-industrial-traces-fullpop-137 --output /tmp/buying-search-geometry-UNIQUE.json
```

The output must be a new file. Evidence: `stats/buying-implementation/20261012-recorded-search-geometry/`. Three tests pass, including an independent Cartesian enumeration of small bounded compositions, shared-material lots, empty offers, missing callbacks and invalid quantities. An archived-source replay from `/tmp` matches the complete output; source hashes and all input trace hashes verify. `replay.json` is an additional workspace run; `archived-replay.json` is the actual outside-workspace replay. No economy run, production setting or outside logic was changed.

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
