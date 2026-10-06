# Economy calibration handoff — paused 3 October 2026

This is the historical stop record. Work has resumed; the current state and new
evidence are in [economy_calibration_status.md](economy_calibration_status.md).

## Stop state and first reading

The user requested that work stop for transfer to another model. The goal is **paused**, not complete. All four native calibration processes were terminated with SIGTERM and their tool sessions returned exit 143. No calibration processes remain running. Existing edits and completed reports were preserved; no commit or revert was performed during the handoff.

Read this file first, then `spec/economy_contract.md`, `reports/calibration-protocol-annual-v1.json`, `spec/market_logic_research.md`, and `spec/age_rebalance.md`. The latter two contain chronological research notes; references to experiments “running” describe their earlier status and are superseded by this stop record. `reports/research-running-state.json` now records the interruption.

The workspace has substantial uncommitted changes from many earlier turns. **Preserve the unrelated `spec/technology_strategy.md`.** Inspect the diff before committing; do not treat every untracked report as a new source requirement. This is a plain JavaScript project without a package.json. The active runtime is `engine/model.js`, `engine/reference_kernel.js`, and `phase0_economy_engine_worker.js`; UI files are `phase0_economy_engine.html` and `phase0_economy_engine_app.js`.

## Objective and scope

Establish defensible market behavior, freeze that logic, then calibrate physical supply and ultimate demand so standard bots in **all three producer tiers** earn comparable percentage returns and approximately double simulation-opening **book equity in one actual Age**. Individual Tier 0 giants should remain substantially larger than individual downstream firms. Aggregate tier sizes are a separate comparison.

This is an **economy core**, not game onboarding or a restricted player experience. The simulation runs independently of a human takeover. Human investors may eventually assume operations of Tier 1 or Tier 2 firms; the future alpha is Tier 1. Admin capabilities for both tiers remain enabled. No purchase wallet, takeover valuation, or onboarding mechanic is requested now.

The current story is the Robotic Space Generation: robotic industry is a human vessel in a far-future society preparing for a major galactic war and sustaining society during it. The catalogue includes civilian and military physical goods across ten sectors, rather than exclusively weapons or infrastructure. The earlier Midbridge immortality/consumer-experiment story is superseded. Final purchasers represent the **wider galactic economy**, not necessarily households and not another simulated profit-making tier.

## Fixed user decisions

- **Counts:** 20 Tier 0, 1,000 Tier 1, 61,950 Tier 2 firms; one million external procurement agents. Never shrink or change these to calibrate returns. Small fixtures are permitted for regression testing only.
- **Calendar:** 30 ticks/month, 12 months/year, 480 years/Age. One Age is **0x2A300 actual ticks**. Display Age in decimal and tick counts with a `0x` prefix. No compressed simulation time.
- **Tier 0:** $1,000,000 opening cash per firm; shared capacity 10,000/tick; target inventory upper cap 500,000; shared maximum warehouse 1,000,000. Firms cover one through four raw elements. The implemented stock policy uses an adaptive three-day target under the upper cap.
- **Tier 1:** four C-1 basics W/E/F/A and six unordered C-2 pairs. All buyers are companies; external procurement demand for both basic and compound Tier 1 goods is zero. Each material market starts with 100 firms.
- **Wholesale:** Tier 1 purchases of Tier 0 raw elements use minimum 1,000-unit lots. Tier 1-to-Tier 2 processed-component transfers use individual units; do not impose a 1,000-unit lot on Tier 2's 60-unit warehouse.
- **Recipe identity:** immediate operand order is commutative, while grouping/manufacturing ancestry is retained. Do not collapse distinct intermediate structures merely because ultimate raw ancestry matches. The complete final recipe pool has **44 C-3 / 116 C-4 / 260 C-5 = 420** distinct recipes, codes and names.
- **Catalogue:** 200 active products, 220 reserved for later invention. Each of ten sectors has 20 active products: **2 C-3 / 6 C-4 / 12 C-5**. The earlier proposed 6:10:14 allocation was explicitly withdrawn. All catalogue entries are physical products; no service sector.
- **Portfolios:** every unordered subset of one to four of a sector's 20 active products has exactly one initial firm. Per sector: 20 + 190 + 1,140 + 4,845 = **6,195** portfolios. Across ten sectors: **61,950** firms. Initial width counts are 200 / 1,900 / 11,400 / 48,450; 232,000 production routes; 1,160 initial suppliers per product. Every portfolio stays within its sector. Bots may subsequently add paid routes within that sector under existing rules.
- **Shared limits:** capacity and inventory are totals per firm, not per product. Warehouses count raw inputs and finished goods; a compound intermediate counts as one inventory unit.
- **Complexity:** higher complexity should receive fewer unit orders per market and support higher unit markups. Compare per-market volumes rather than imposing an arbitrary aggregate C-5 share: 120 of 200 active products are C-5.
- **Symmetry:** sectors, materials, products and initial portfolio widths should have comparable expected opportunities; a starting product choice should not confer a statistically meaningful built-in advantage. Real competition, learned relationships and individual outcomes may differ.
- **Future invention:** reserved products need a modest eventual demand place, but invention activation, marketing and visibility are deferred. Do not create those systems during this calibration.

Current fixed opening book equity is $1m/T0, $20k/basic-T1, $80k/compound-T1, and $3.5k–$6.5k/T2 (one to four routes). Tier 1 includes paid plant plus $5k cash; Tier 2 owns its routes at $1,000 each plus $2.5k working cash. There is no shared factory asset. Do not inflate asset values or alter opening capital to make return ratios look correct. Per-company size must satisfy Tier 0 > Tier 1 > Tier 2; aggregate size is Tier 2 > Tier 1 > Tier 0 because of company counts.

## Principles and market protocol

Use research, controlled counterfactuals, full-population experiments and actual accounting. Separate a structural regression, a short numerical fit, an observed equity trajectory, and full-Age validation. Literature motivates market rules; it does not prove this simulator's equal-return target.

The working **annual-v1 protocol is frozen for demand/supply experiments**, but no calibrated candidate has been adopted as the application's standard defaults. Its file specifies all fixed fields and the 19 permitted supply/demand fields. In particular, observation interval 360, response .05, confidence gates off, price search, switching, elasticity, activation, and learning settings are fixed. A behavioral rule change requires a separately recorded protocol version and justification; it must not be smuggled into parameter calibration.

The Age target must never enter buyer valuation, supplier selection, price learning, transfers or profit crediting. Book equity uses cash, paid machinery and actual inventory acquisition basis; unsold asking-price changes do not create equity. Preserve cash conservation, real production/input consumption and warehouse constraints. Tier 0 UI gross profit includes current extraction spending; the research sold-cost profit bridge additionally accounts for unsold inventory basis. Explain that distinction when reconciling displayed profit with equity.

With constant productive capital, the reference average earnings needed to add the opening equity over an Age are $5.787037/T0 firm, $0.115741/basic-T1, $0.462963/compound-T1 and $0.020255–$0.037616/T2 (one to four routes). These are **offline references, never payouts**. Constant-profit doubling and compounded reinvestment are different assumptions; inspect actual trajectories instead of treating a stationary extrapolation as proof.

Fixed runtime SHA-256 fingerprints:

| File | SHA-256 |
| --- | --- |
| engine/model.js | 9f5b2a07fe32fbf5f18f383b7ad1aa5e4c7cd5d7547871f18311d8a35d568d03 |
| engine/reference_kernel.js | f445277b204430a9733a60ab6106f98d9a490d0f541870e496a0868bf4bfbb2e |
| phase0_economy_engine_worker.js | 55bfaccc3fa9090c24cc2e43471156a554d52f9118b5910b160b7fdb2ee574ea |

## Completed work and evidence

Wartime/civilian product and company nomenclature is implemented, including the latest company-name request. Examples include Atlas Resources, Haven Habitat Systems and Sentinel Defence and Rescue Systems. All 420 catalogue names match documented recipes; names/codes/recipes are distinct. Exact company-name search is covered by regression checks. The authorized nomenclature subagent completed; no calibration delegation was authorized.

The full startup audit `reports/current-economy-goal-audit.json` verifies catalogue allocation, all portfolios, company counts, initial routes, shared limits, calendar, and checked UI/admin/accounting surfaces. It does **not** establish profitability symmetry.

Core fairness/accounting corrections include local Tier 1 supplier tie rotation, neutral initial price directions, no fictitious demand history, purchase-independent need-product memory, earned supplier relationships, fair remaining-capacity extraction allocation, acquisition-cost equity, physically rounded demand accounting and a $0.00001 unit-price floor. Two execution optimizations have parity evidence; an unused-material-mask optimization had no measured speed benefit and was rejected.

The current **32-check quick suite passes** with matching runtime fingerprints (`reports/scarcity-aware-quality-quick.json`). A stale one-cent assumption in the price verifier was corrected to the engine's unit floor, with profitable fractional-cent and below-cost regressions. The newest cost-shock extensions to the long-run instrument were syntax checked and executed into the shock phase, but their interrupted runs did not reach the final gate.

The leading experimental config is `reports/parameter-candidates/processing-value-capacity-95.json`. It preserves capacities, capital and nominal physical raw flows while reallocating raw-versus-processing value through allowed cost/demand data. Its fixed-protocol audit is `reports/processing-value-capacity-fixed-protocol-audit.json`. Do not mistake it for an adopted configuration.

Two full-population ten-year runs completed for that candidate:

| Actual mean book-equity gain over 0xE10 ticks | Seed 12345 | Seed 31415 |
| --- | ---: | ---: |
| Tier 0 | 1.8401% | 1.7702% |
| Tier 1 | 2.0568% | 2.0809% |
| Tier 2 | 2.0657% | 2.0684% |

The constant-profit reference over ten years is 2.0833%, not a promised return. Seed 12345 report: `reports/economy-research-processing-value-capacity-95-3600.json`. Seed 31415 report: `reports/processing-value-capacity-95-balance-31415-3600.json`; it passes all 214 active-market accounting, stock, participation and transaction-price gates and reconciles every firm's equity with cumulative profit. Cross-seed comparison: `reports/processing-value-capacity-cross-seed-comparison.json`. These are finite-horizon results; narrow versus broad portfolios and Tier 0 width cohorts still differ.

## Interrupted experiments and preservation limits

All four were deliberately stopped at user request, not failed validation. Tool terminal tails are saved in `reports/stopped-session-<sessionId>-terminal-tail.log`. Those files contain only previously undelivered terminal tails, not every earlier output.

| Former session | Experiment | Last saved/observed tick | Outcome |
| --- | --- | --- | --- |
| 5058 | Actual Age, original all-tier-utilization-95 reference, seed 12345 | Checkpoint 0x8430 | Incomplete; stopped |
| 8949 | Actual Age, processing-value-capacity-95 candidate, seed 12345 | Checkpoint 0x25F8 | Incomplete; stopped |
| 50696 | Temporary extraction-cost shock, candidate, seed 31415 | Annual output through 0x870 | Incomplete; stopped |
| 31863 | Matching normal control, candidate, seed 31415 | Annual output through 0x870 | Incomplete; stopped |

The two Age checkpoint files preserve normalized config, counts, runtime hashes, actual aggregate book equity and recent earnings. **They are observation checkpoints, not serialized worlds. There is no resume implementation; the terminated simulation states are lost.** Do not poll the closed handles or present these as completed Age reports.

At the original reference checkpoint (0x8430), tier aggregate book equity was $26,292,947.87 / $65,593,705.64 / $22,368,845,360.19; last-60-tick profits were $218.2873 / $255.0710 / $106,991.4221 per tier per tick. At the processing-value checkpoint (0x25F8), equity was $21,209,729.46 / $58,975,342.79 / $19,785,277,695.24; recent profits $138.8674 / $300.1434 / $107,522.9447. Nominal tier-total references are $115.7407 / $324.0741 / $108,448.3507. **The drift shows that the early short-window fit has not established steady all-tier harmony.**

The shock instrument changes extraction cost only, by 1.3× at 0x5A1, then restores it at 0x871. It asserts unchanged book equity, clock, portfolio count, engineering references, buyer private values, need memory and supplier relationships at each admin transition; every other normalized setting stays fixed. It records annual actual raw/intermediary transaction prices and profits. Execution reached the shocked annual outputs without an assertion failure, but restoration/recovery and final reconciliation are unverified. At 0x870, raw market prices were approximately .002437/.002441/.002440/.002460 in the shock case versus .002334/.002332/.002380/.002371 in control. Both retained about 99.997% final unit fill. This indicates some price response, not proof of sufficient or timely cost pass-through. No final shock/control report was produced before interruption.

## All unfinished and open work

1. **Resolve settled return gaps before adopting defaults.** Diagnose the upward Tier 0 and downward Tier 1 earnings drift in longer corrected-core runs. Separate acquisition-basis inventory accumulation, actual sold margins, demand-learning dynamics and physical utilization. Adjust only allowed demand/supply fields under the frozen protocol unless new evidence justifies a separately versioned rule correction.
2. **Establish company/cohort fairness, not merely tier averages.** Evaluate every Tier 1 material, every Tier 2 product/recipe/sector, initial portfolio widths one through four, Tier 0 focus widths, percentiles, persistently unprofitable firms and cross-seed variation. Completed candidate results still show broad/narrow differences; startup symmetry alone does not settle this. Define a defensible tolerance for “somewhat similar” and distinguish structural advantage from finite-run competition noise.
3. **Finish actual one-Age evidence.** No actual Age run completed. Re-running from initialization is necessary with current instruments unless reliable world serialization is implemented and validated. Test the eventual selected parameters over actual 0x2A300 ticks, inspect actual opening-to-final equity multiples and cohort distributions, and verify Tier 0's individual scale advantage. Do not claim doubling from short-window extrapolation.
4. **Complete disruption and multi-seed robustness.** Finish a paired temporary-cost-shock/control experiment including restoration, recovery, actual pass-through, stock fill, working cash and all firm-level accounting. Test other relevant demand/supply disturbances as warranted by the selected calibration. The old completed stress/quick tests do not prove final candidate robustness.
5. **Decide whether the observed economic magnitudes are plausible.** The candidate reports roughly 99% final gross margins and approximately 12% final-factory utilization. A verifier pass is not itself a convincing economic explanation. Explain why these values are justified or revise allowed cost/demand/capacity data while preserving counts/capital and complexity policy.
6. **Adopt and verify final standard parameters.** The app's normal defaults are still uncalibrated (including a different observation interval); candidate-only success would not finish the task. Once a candidate is justified, install the exact selected parameters coherently in defaults, presets/reset/config/UI/specs, then rerun appropriate checks on that adopted configuration. Never quietly change market logic to manufacture equality.
7. **Complete the final standard full gate and UI consistency review.** The quick suite passes; the final adopted-default long-run suite does not yet exist as completed evidence. Verify all active market price/accounting/stock/activity gates across seeds, full equity bridges, decimal Age/hex tick display, shared raw-plus-finished storage, B2B demand/fill/unmet reporting, Tier 0 extraction-in-COGS/made reporting, admin access and company search against the final version. Do not repeat unrelated passed checks absent changes.
8. **Consolidate documentation and deliverable state.** Once calibration is actually finished, replace chronological “promising/running” notes with a clear current account, retain historical fingerprints, explicitly distinguish defaults from experiments, update the audit and explain tested limits. Review the large accumulated diff, preserve unrelated files and commit only the authorized coherent work. This handoff does not mark that completion or perform that commit.

Deferred rather than incomplete current implementation: marketing/visibility, active invention, onboarding, takeover purchase mechanics, war gameplay, and new demographic/immortality dynamics. Do not add them to the calibration scope.

## Restart commands and instrument cautions

Run from `/Users/csys/Desktop/ibicot`. These are commands for the successor, not processes left running:

```sh
node tests/economy_quality.js --quick
RESEARCH_TICKS=172800 RESEARCH_CONFIG=reports/parameter-candidates/processing-value-capacity-95.json RESEARCH_CHECKPOINT=reports/restarted-age-candidate-progress.json RESEARCH_OUTPUT=reports/restarted-age-candidate.json node tests/economy_research.js
BALANCE_TICKS=3600 BALANCE_SEED=31415 BALANCE_CONFIG=reports/parameter-candidates/processing-value-capacity-95.json BALANCE_COST_SHOCK=1.3 BALANCE_OUTPUT=reports/restarted-cost-shock.json node tests/long_run_balance.test.js
BALANCE_TICKS=3600 BALANCE_SEED=31415 BALANCE_CONFIG=reports/parameter-candidates/processing-value-capacity-95.json BALANCE_OUTPUT=reports/restarted-cost-control.json node tests/long_run_balance.test.js
```

Do not overwrite historical reports when launching new experiments. Native Age runs take many hours at full population; consider exact-parity execution improvements or validated serialization if they materially help, without reducing agents or changing tick semantics. `tests/economy_research.js` reads its own instrument fingerprint at completion, so do not edit it while an experiment is running. Other instruments record launch hashes; preserve unambiguous versions anyway. Avoid starting many heavy experiments simultaneously. No further calibration work was performed after the stop request beyond preservation and this handoff.
