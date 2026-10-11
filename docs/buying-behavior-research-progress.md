# Buying-behavior research execution record

**Final status, 2026-10-12: complete; reject historical R1.** The entries below
preserve the chronology, including earlier incomplete counts and superseded
plans. The final entry, [report](buying-behavior-research-report.md) and
[completion audit](buying-behavior-requirements-audit.md) establish delivery status.

Research began 2026-10-11, branch `new-recipes`, clean commit `f2b9b47`.
The [brief](buying-behavior-research-brief.md) is the scope authority. No production
defaults or watched run may change. Final rollout is a separate user decision.

## Work ledger

- Completed initial code/data audit and primary-source review; detailed findings
  and limitations are in the contract and source-review documents.
- Baseline archive and 361-tick benchmark:
  `stats/buying-behavior-research/20261011-baseline-f2b9b47/`.
- Baseline full Python discovery: 93 tests passed. The curated launcher and its
  JS checks also passed; it is not the full discovery suite.
- Completed baseline 14,400 ticks (two generations), seed 137. Per-product and
  company-period accounts are preserved in `20261011-baseline-137-two-generations`.
- Implemented isolated recorder, preregistered gates, exact restricted basket
  model, independent exhaustive oracle and compiled settlement. Research
  tests pass, including 1,500 retail oracle cases, 500 industry oracle cases,
  3,000 decimal-boundary comparisons, reference settlement, checkpoint continuation
  and unchanged production/price behavior. These do not establish model validity.
- Added reconstructed-decision traces, unique funded intentions, separate retry
  units and cash losses, and normalized accounting residuals. Validate the saved
  traces before using them as evidence.
- In progress: matched local/market/hybrid experiments and ablations; held-out seeds,
  complete generations and multigeneration drift, stress and expanded catalogs.
- Final: report, model contract, evidence decision table, rollout/rollback artifact.

## Audit observations (not yet a final conclusion)

1. T1 searches all eligible T0 sellers. T2 selects over complete price-sorted
   supplier books. T3 uses five draws with replacement and deduplicates afterward.
   Thus none implements five distinct alternatives plus incumbent consistently.
2. `select_offer` favors a full-fill supplier over cheaper partial stock. Both
   T1 and T2 update preference after any positive fill. The brief disallows this.
3. Company desired orders are storage-slot deficits independent of price, output
   demand and profitability. The later production gate is a separate decision.
4. T3 demand is reevaluated at each quote, but fee/quantity ordering is a heuristic,
   not an exact basket solution. Fee settlement depends on primary seller and
   incumbent availability at its own quote. Split semantics need explicit tests.
5. Supplier demand is funded/attempted quantity; retail retries can appear at
   several suppliers. It is not a deduplicated product-demand intelligence series.
6. Sell-side learning prioritizes unmet demand, then movement toward the observed
   market rate, then gross-profit change. Zero-sales anchors use mean quotes.
   This is a feedback mechanism to ablate, not proof of a profit optimum.
7. Annual T1 AOV counts buying **companies**, not ingredient transactions
   (`count_nonzero(t1Bought)`), despite the prose saying successful purchases.
   Preserve actual baseline and identify any correction as a separate treatment.
8. Fresh defaults are rent-free, 20 T0, 1,008 T1, 57,960 T2 and 1,000,000 T3;
   current catalog has 105 invented outputs. README/canon historical values are
   superseded by integration rules. Earlier local-only-information restrictions
   do not prevent the brief's explicitly authorized intelligence experiments.
9. No live economy process found at inspection. Preserved replay intervals are
   1–1,145 and 1,146–7,200. Independent comparison now matches all 885,600
   product/tick records after correcting the research T0 product-net allocation.
10. Bots do not buy additional machinery. Player-controlled T1/T2 firms can add
    installations; cash is exchanged for equipment book assets and an external
    equipment sink, not an immediate operating expense. The experimental engine
    rejects multiple installed routes; the small general oracle covers shared
    inputs, but scalable multiple-route execution remains a rollout blocker.

Experimental files live under `tools/buying_research/`; these are not imported by
production. Numerical and economic acceptance criteria were frozen before
candidate results. Full-population profile 05 reached 387 ms median observed tick;
this was a short profile, not a mature-world benchmark. Allocation reuse later
measured 427 ms median over 360 ticks in isolation, still exceeding the paired
relative performance budget. Mature checkpoint benchmarks remain to be completed.
No rollout is approved. The main, supplement and anchor campaign plans are frozen
JSON files under the research statistics directory. Stable-ID tie bias, the
zero-terminal-value service-level restriction, and the unmatched-buffer
counterexample are retained as negative findings, not tuned away.

Execution checkpoint: 16 research tests passed in `research-tests20.log`.
Supplier-closure trace replay passed for 72 T1, 2,124 T2 and 377 retail decisions
in each of the market and local runs. The mature benchmark runner's restored
market world matches all 6,150 recorded product-field observations at ticks
1,081–1,082 of the uninterrupted run exactly. Its two-tick smoke latencies are
not performance evidence. Four alternating baseline/market 360-tick benchmarks
from tick 14,400 are queued to start only after the three campaigns finish.
The amended 82-run `analysis-plan.json` then feeds `final-study/` and `final-diagnostics/`.
The queue logs and plan result files distinguish pending, failed and completed
work; these directories must not be mistaken for complete until their jobs end.
Amendment C adds full-generation local/hybrid sales-floor runs. The first
seed-137 sales-floor calibration almost matches market-information trade, while
the original regimes' year-ten windows all suffer large trade losses. Preserve
that change in ranking and distinguish estimator quality from the shared
industrial return function. A repeated split-fill fixture also verifies an
incumbent can collect fees with no goods sales under the chosen split protocol.

Concurrent workspace work: a separate naming cleanup changed README/naming
documentation and removed obsolete duplicate catalog exports/generators during
the campaign. These are not research edits and must be preserved. Inspection
confirmed no changes to `economy/`, `web/`, or the runtime catalog, naming,
starting-selection and consumption-calibration JSON files. Research archives
retain their original files; the evidence audit distinguishes omitted unused
catalog exports from a changed runtime source. Do not sweep the naming cleanup
into a research commit or restore its deleted files.

Archive reproducibility check passed in a fresh `/tmp` checkout: exact source
identity and all 6,150 full-population product-field observations at ticks 1–2
matched the original market-control run. The historical provenance helper
requires Git metadata, so the extracted, hash-verified source received a local
snapshot commit in that temporary checkout only. Commands and verification are
saved. An interim audit of 24 completed runs verified 1,297 archived source files
and 37,080 recorded tick windows with no source or coverage mismatch. The final
82-run audit still remains. The sales-floor signal/continuation test also passed
in `sales-floor-checkpoint-test21.log`, in addition to the prior 16-test suite.

The 12 held-out short runs are complete and analyzed in `heldout-study/`:
third-year paired retail ratios average 63.90% local, 93.43% market and 85.98%
hybrid across seeds 811/1597/2027. These are not complete-generation held-out
gates. Both sales-floor calibration seeds are complete; local-sales-floor is
within +0.16%/−0.70% of market trade in their third years. Full-generation
sales-floor runs remain active. First-generation route tables and local
zero-sales/earnings distributions are now in the report.

Additional analysis checks: all 119 single-product T1/T2 company groups reconcile
to independently recorded product sales, earnings and counts for the local final
year. Baseline two-generation balance changes use its saved initial tier snapshot
because the historical recorder lacks opening company arrays; no missing
company-level opening data is invented. The metric glossary clarifies that
`unfundedUnits` is total cash-unconstrained planned quantity, not a loss count.

`adverse-benchmark-plan.json` adds sequential baseline/market 360-tick measurements
with initial fees multiplied by ten. Its queue starts after mature benchmarks
and the 82-run final analyses finish, to avoid CPU contention. These measurements
address the brief's adverse-fee performance requirement; they change neither the
economic study plan nor the preregistered budget. Queue session 14637 writes
`adverse-benchmark-queue.log` and the campaign's normal plan-results marker.
`compare_results.py` prepares ablation, recovery, fairness and isolated-timing
comparisons from completed evidence; execute it after those inputs are complete.

Timing review found that the optimized 360-tick allocation-proof profile and the
earlier 120-tick baseline have different windows. Their roughly threefold ratio
is preliminary evidence, not the final matched-window gate. Before its queue
starts, the isolated profile plan now also includes fresh baseline/market
360-tick ordinary-startup runs. The original two-job adverse plan is retained as
`adverse-benchmark-plan-initial.json`; the active four-job plan includes ordinary
startup and large-fee pairs. This resolves a measurement limitation rather than
relaxing the budget or retuning behavior.

Additional protocol counterexample: `bid_semantics.py` independently verifies
that Q=2 at the incumbent quote can qualify a three-unit challenger delivery,
although the cheap-quote intended order was twenty. Preference changes at 15%
intention fulfillment. `canonical-versus-intended-bid.json` preserves this case.
The report, contract and code review now explicitly distinguish the frozen-bid
convention from an interpretation requiring full funded intention. Passing the
four loyalty-table cases does not approve that interpretation.

## User clarification: quantity at each fallback price

The user confirmed `remaining=max(0,q(price)-all units already bought)`. The exact example buys A=2 and B=6. The production reference and compiled paths already do this quantity calculation. Three dedicated tests passed, including actual stock/cash/revenue/COGS posting and 500 independent exhaustive-oracle comparisons of fee-free allocations. Added `fallback.py` as an isolated readable specification; no production behavior changed. Evidence: `stats/buying-behavior-research/user-fallback-verification.json` and its test log. The protocol, model and report now distinguish this user decision from the historical R1 canonical-bid policy. A focused question about whether B's complete remaining fill qualifies for preference is pending; no fee or preference interpretation has been inferred from the quantity example.

## Fallback scope, metric audit and completed expanded catalogs

The fallback clarification applies to a same-product purchase across suppliers. A new one-input derived-demand fixture independently enumerates split purchases and shows historical R1 industry fails this requirement: `[2,6]` costs $68.634653 versus R1 `[0,8]` at $71.892634 for the same eight outputs. The result and executable are `industrial-fallback-scope-counterexample.json` and `industrial_fallback_case.py`; the report/model/review/protocol now state the failed requirement. A separate two-engine baseline audit buys `[2,3,0]` at quote demands `[10,8,5]`, but retains LastQ=8 and stock-unmet=3. Its executable replay reproduces the original JSON exactly. Demand-loss denominators are therefore explicitly protocol-specific; actual transactions and posted earnings are used for policy comparisons.

All 12 supplement runs completed, including both expanded catalogs. The 255-product final-year pair records baseline/R1 market retail of 1,579,685/1,478,097 units per tick, T2 net margins 37.27%/30.35%, and no zero-trade product. `interim-expanded-all/` preserves full distributions. Enhanced expanded-all trace replay passes for every retained sample. The report now includes both expansion pairs and their changed allocations. Horizon-one and horizon-six ablations complete: 332,861 versus 1,562,099 retail units/tick, compared with 1,456,904 at H=3. Higher horizon also increases closing input stocks; this is a three-year calibration result, not long-run approval. One/five/twenty search alternatives yield 1,245,807/1,456,904/1,392,501 retail units/tick; the final report records total earnings and the non-nested sample/economic-history caveat.

Current campaign status: {'complete': 48, 'running': 6, 'queued': 28}. Main and full-generation sales-floor process handles were polled live in this goal turn. Final study, diagnostics, isolated timing and complete evidence audit remain pending. All seven research documents passed local-link validation after these updates.

## Requirement audit and verification scope

Added `buying-behavior-requirements-audit.md`, mapping the full brief to evidence, research completion and adoption consequences. The audit is explicitly unfinished: it does not turn a demonstrated model failure into a passing replacement requirement. It identifies the missing final decision table and all pending study, stress, fairness, profile and archive checks. Inspected scenario and recorder code again: cash-endowment changes occur before opening accounts, per-tick recording checks cash/stock/equity/goods, and the independent storage validator scans at 360-tick/final boundaries. Report and code review now state that exact verification scope.

A matched year-17 comparison (ticks 5,761–6,120) shows baseline/market/local-sales-floor/hybrid-sales-floor retail at 1,293,776/253,806/180,252/288,737 units per tick. Full distributions and exact summed accounts are in `sales-floor-year17-comparison/`. This is a completed annual interval inside still-running generations, not a final-generation result. An initial analysis-print typo used p50 instead of the actual median key; the corrected extraction reused the unchanged baseline aggregate, with no recording overwritten.

All eight research-document local links validate. Main and floor campaigns were confirmed live by sessions and OS processes. Mature-profile, final-analysis and startup/adverse-profile queue sessions were also confirmed live, waiting on their explicit dependencies; they have not yet run the final profiles. Current counts: {'complete': 49, 'running': 6, 'queued': 27}.

## Completed sales-floor generations

Both full-population floor variants completed 7,200 ticks with passing recorded invariants. The saved queue script `floor-generation-analysis-queue.py` produced whole-generation and final-year comparisons against baseline and market, plus eight explicit tier/route tables. Full-period local/hybrid retail is 682,353/769,385 units per tick; final-year retail is 110,036/228,056, only 8.75%/18.14% of matched baseline. Local final-year zero-sales manufacturers fall from the original local policy's 28.26% to 11.27% (6,531 companies), but trade still contracts sharply. Hybrid has five zero-sales manufacturers. Report and requirement audit now record completed rather than pending floor evidence.

`figures-sales-floor-generation/economy.png` was visually inspected: four complete labeled series, clear axes/units and no clipping. The SVG and raw plotted accounts are preserved. This render used Matplotlib 3.10.8 and the inherited vendored NumPy 2.5.3, as recorded in its render-environment JSON; the isolated plotting environment remains intact. A display-only summary extraction initially used a nonexistent negativeEarningsShare key; the stored summaries were intact and inspecting their schema identified negativeShare. No source recordings changed.

Enhanced full-generation decision replay passed for each floor variant: 480 T1, 14,160 T2 and 2,552 T3 decisions, checking allocations, objective, fees, availability and preference. Newly completed window-five/window-ninety/lower-valuation ablations are preserved in `interim-ablations/`. The 20% industrial resale-value reduction produces 136,529 retail units/tick in year three; it does not alter consumer demand curves. Current campaign counts: {'complete': 53, 'running': 4, 'queued': 25}. All research-document links pass.

## Two generations, completed ablations and baseline measurement replay

The market run completed 14,400 ticks. Its second-generation retail average is 152,434 units/tick, versus baseline's 1,210,333; the final year is 145,349 versus 1,190,612 (12.21%). T2 realized price is $91.09 versus $20.71 in that final year. Positive earnings and nearly flat final price/volume do not rescue trade suitability. `two-generation-study/` contains full/annual/second-generation/final-year accounts, product/company distributions and explicit tier/route tables. `figures-two-generations/economy.png` was visually checked. Enhanced full-run trace replay passes 960 T1, 28,320 T2 and 5,046 T3 decisions.

All 16 ablations now have matched year-three accounts and an explicit-options summary. The sales-only signal contracts to 11,206 retail units/tick; the capacity proxy gives 1,117,043. Report explanations distinguish quote-first supplier restriction from removal of every joint-complementary calculation, and industrial resale-value scaling from consumer-demand changes. Priority reversal breaches fairness flags: T0 mean earnings change +13.66%, with larger tail shifts in T0/C2. Saved configuration/source comparison identifies only the prior zero-rounding endpoint repair among active decision files; the independently audited seed does not hit that endpoint.

Added `cost_snapshots.py`: checkpoint-derived means separate last successful batch cost (potentially stale), realized COGS and a current-mean-quote recipe bill. Independent stable-catalog-ID arithmetic verifies all 119 products in six tick-7,200 states, including 14 repeated-input recipes each. Tick-14,400 baseline/market snapshots also pass that check. Raw historical recordings remain untouched.

Protocol Amendment E starts a fresh, identical baseline measurement replay at seed 137 for 14,400 ticks. The original baseline predates normalized invariant/price-contact counters, opening company arrays and two cost fields. Its missing fields are not retroactively claimed. `verify_measurement_replay.py` requires unchanged production/catalog sources and initialization, exact world arrays/JSON, all common product fields (net reconstructed from posted accounts), all recorded company arrays and loyalty/fee histories before using added measurements. The frozen economic plan remains 82 runs; `complete-evidence-plan.json` adds this one replay for an 83-run provenance audit. Mature timing waits for it automatically. Current economic counts are 64 complete, four running and 14 queued; replay, final diagnostics, isolated profiles and final audit remain in progress.

## Final regressions, transient phases and queued evidence checks

The combined research suite passed all 20 tests in 32.054 seconds (`final-research-regression-tests.log`), covering the 13 basket/property cases, four world/continuation cases and three fallback cases. Existing full baseline discovery passed 93 tests; the report links it separately from the curated launcher/JS checks. The nonfatal SciPy/NumPy version warning is preserved, with dependencies unchanged. An early measurement-replay comparison reproduces all 23 common product fields exactly through 2,520 ticks, reconstructing net from posted accounts on both sides. This is partial evidence, not the final world/checkpoint proof.

`stress_summary.py` adds four explicit transient calendar windows and same-policy controls. Its partial output lists 12 completed comparisons and 13 pending runs/controls. The one-time T1 quote doubling causes zero market-policy retail sales in ticks 361–540 and only 21,225 units/tick in year three (1.46% of its control), versus baseline's 99.32% control ratio. The shock is not reversed by fiat. Temporary demand and raw-supply interventions are analyzed separately from permanent initial endowments and this one-time price jump. The quote-shock figure was rendered and visually checked; zero-revenue margins are gaps, not zeros. The report now records these completed transient findings while labeling the overall stress consolidation unfinished.

`audit_evidence.py` now handles both fresh and resumed observation windows and also verifies saved patch hashes, tick histories and benchmark source checkpoints. `all-delivery-evidence-plan.json` contains 91 distinct runs: 82 economic treatments, one measurement replay and eight isolated profiles. The final proof queue (session 24218, saved `final-proof-queue.py`) waits until both isolated profile plans finish, then executes exact baseline replay verification, all-91 source/coverage audit and final comparisons in order, stopping on failure. The final comparison keeps the original baseline's missing normalized counters distinct from its proven supplementary replay and labels which recovery ratios are applicable to temporary shocks. Full stress-phase consolidation still needs a fresh final output after every scenario/control completes.

## Sustained empty-market timing and checkpoint milestone

Protocol Amendment F expands the still-queued fresh timing plan from four to six profiles by adding the existing small-cash scenario for baseline and market. This supplies sustained empty-downstream-stock coverage; ordinary startup alone only has a brief initial shortage. Budgets are unchanged. Previous plans are preserved as `adverse-benchmark-plan-before-stock-profile.json` and `all-delivery-evidence-plan-initial91.json`. The active all-delivery plan now has **93 runs: 82 economic, one measurement replay and ten final timing profiles**. The final proof queue reads these plans only after the profile markers, so its final audit will cover the updated plan.

The completed low-cash pair has final-year retail/output/earnings zero in both policies, T1 opening cash $485 and final T1/T2 finished inventory zero. The minimum initial raw lot costs $1,250. The large-fee market case has 1,250,238 retail units/tick and $4.130m T2 earnings versus baseline's 1,570,712 and $8.324m. `interim-stress-additional/` preserves these accounts. An exploratory checkpoint read used an incorrect raw-array name; inspecting the actual archive corrected the inspection, and all saved analysis/recording files were preserved. T0 raw-product denominator labels now explicitly mean allocated company equivalents rather than unique raw-product owners; actual company distributions remain the 20 extractor portfolios. This changes labels only, not recorded accounts or numerical aggregates.

The measurement replay crossed tick 7,200. All **168 world arrays and complete checkpoint JSON match the preserved baseline exactly** at that tick (`baseline-measurement-replay-first-generation.json`). The full 14,400-tick proof is still pending; current replay tick is 7,560. Economic campaign counts are 73 complete, four running, five queued. The final proof queue is alive and waiting on isolated profiles. All eight research documents pass 107 local-link checks. The report now also distinguishes supported, conditional and unidentifiable preregistered hypotheses; it remains a working report pending final consolidation and the closing decision table.

## Closing decision draft and explicit measurement coverage

The report now ends with a working decision table covering all evidence gates and known failures, with pending recovery/timing/audit rows explicitly unfinished. It recommends rejecting historical R1 and names market requests only as a conditional next-study comparator based on the held-out short-run criterion; hybrid's better full-generation retail share and universal generation failures are stated alongside it. The requirements audit now records the table as drafted, not finalized.

Live sessions 23629 (main campaign), 86780 (baseline replay) and 24218 (final proof queue) were polled successfully in the next goal turn. Current economic counts are 77 complete, four running, one queued; baseline replay is at tick 10,080. All completed explicit accounting/goods/stock gates pass. A manifest-coverage inspection identified one additional reporting limitation: the three early 360-tick seed-137 local/market/hybrid calibration runs have normalized conservation counters but predate price-floor/ceiling contact counters. Their later complete-generation counterparts are directly instrumented. Do not claim every early calibration has historical price-bound coverage or infer it from a snapshot. `compare_results.py` now lists missing run IDs per invariant metric. This is separate from the original baseline's larger measurement gap addressed by the exact replay.

## Final completion, 2026-10-12

All 82 economic runs, all 82 corresponding diagnostics, the complete full/final-year/annual study, and all 25 stress-phase comparisons are complete. All 14 temporary demand/supply shocks reach the 90% same-policy trailing-trade threshold at the first eligible endpoint, tick 720, and remain above it through tick 1,080. Three forecast re-entry controls also pass that limited recovery check. The quote-shock, low-cash and generation-scale failures remain explicit; asymmetric starting cash is a favorable R1 case and is reported without suppressing it.

Ten isolated profiles cover startup, initial fees ×10, sustained empty downstream stock under low cash, and two mature repetitions. All five matched pairs fail both relative median/p95 budgets; absolute median below 500 ms and the memory budget pass. Candidate median ratios range from 2.683 to 3.436. Both mature repetitions have exactly equal world arrays/JSON, product/company records and R1 sidecars. Recording and publication/encoding costs are reported separately; browser rendering is unmeasured.

The complete baseline measurement replay matches all 23 common product fields over 1,771,200 product/tick observations, 40 company periods/1,280 array comparisons, economic tick histories, and both 7,200/14,400 checkpoints with all 168 world arrays and JSON exactly. Its separately recorded normalized counters supplement only this verified trajectory. Maximum equity/money/goods tolerance ratios across direct records plus the supplement are 0.06628/0.001127/0.06885. Three early calibration runs still lack historical price-contact counters. No original manifest or raw data was rewritten.

The final evidence audit passes 93 runs, 5,706 archived source-file instances and 155,520 run-tick windows. Final comparisons require an exact match between the 82 study and diagnostic identities. All queue result records report successful completion. The event report now distinguishes true supplier changes from first assignments using a source-checked, fixed-market endpoint identity for the three ordinary R1 controls. The `preference_event_audit.py` audit passes and preserves its assumptions and source hashes.

The report, rejected experimental contract, source review, code review, protocol and requirement audit are finalized. The report ends with 20 explicit decisions, distinguishing a completed negative finding from a passing adoption requirement. Market requests are the conditional next-study comparator on the three held-out short-run seeds; hybrid's better first-generation trade and all candidates' generation failures prevent a universal or production-regime endorsement. The unresolved preference qualification is a future contract decision, not a reason to hide the finished rejection.

Final research regressions remain 20 passing tests; earlier full baseline discovery is 93 passing tests, separately from curated launcher/JS coverage. Final document/code/evidence checks and SHA-256 hashes are recorded in `delivery-manifest.json`, produced by the read-only delivery auditor. Production and runtime catalog files remain unchanged. Unrelated naming cleanup is preserved. No repository commit, live service reset or deployment was performed.
