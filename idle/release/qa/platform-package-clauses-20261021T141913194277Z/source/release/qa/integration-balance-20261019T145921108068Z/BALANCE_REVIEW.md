# Independent corrected balance review

**The corrected v4 and supplemental v2 matrices pass this bounded independent review. No new blocking economic defect was found.** All 184 account ledgers conserve Notes, all 12 free/ad fixture pairs match, and 13 selected trajectories reproduce their complete recorded summaries exactly. This accepts the pinned simulation evidence; it does not accept M5-05, M6-03, a beta configuration, native candidate or release.

Review fingerprint: `9da0b37468232ea3f97b42fbd242ec4d5b7ba5507aa873dabcab7287fa153c71` (121 primary inputs, with dependency and shipped-content test context separately recorded). All pinned source/report bytes still match the live tree and isolated workspace at closure. No production source, policy or economic constant was changed by this review.

| Evidence | Independently verified result |
|---|---|
| Baseline v4 | 94 unique cases; full planned 30/90-day, 1/3/6-visit, bonus/reset/purchase/contract grid plus absence cases |
| Supplemental v2 | 90 cases: 36 reset comparisons and 54 actual Note-spending trajectories |
| Python audit | 67,116 passing assertions; all 184 Note ledgers, 1,843 actual purchase transactions, complete grids and timing bounds |
| Dart probe | 5,084 passing checks; 13 exact complete-summary reproductions, 225 marginal states, real purchase boundaries and two season traces |
| Free/ad parity | All 12 matched pairs equal across every economic summary and checkpoint field; a 90-day hourly-reset pair independently reproduced |
| Reset decisions | 6,916 fixed-horizon and 8,142 multiplier comparisons satisfy the exact recorded integer conditions |
| Reconstruction | All 3,506 resets have sampled recovery observations; no final unreported recovery censor in this matrix |
| Mathematical reference | Exact rational telescoping prices and integer rankings; independent 90-digit decimal rate oracle has maximum relative discrepancy `2.892 × 10^-21`, below the review's `10^-20` comparison bound |
| Author tests | 14 distinct unchanged cases pass: 13 in the initial run, plus the one content-equality case after adding omitted test context |
| Static analysis and derived tables | Simulation analysis clean; summary JSON and author review regenerate byte-for-byte |

The baseline's 100 source entries reproduce digest `348a0dcf783353120e0c6b03faf0001879db04ed1ca1127e1727cb9ea47d7319`; the supplemental's 104 entries reproduce `394da363f5598c9b4d6ad84be7c85dee351daf3897f5c758a714db5eb6e3e1fb`. Every entry matches the content-addressed `supplemental-source-394da363…` archive. Raw report hashes are `4722ac55ceabb2dc2bb8ada07d7b701a3337bdfb8a3a7dd38db90f7b98df45cf` and `16aa9e488af37cf91489d75c53aadb4617117cd0013f2cb866eec24610005ff8`, respectively. The initial 88/v2/v3 matrices and interrupted supplemental v1 remain invalidated by QA018; this review does not revive their scenario conclusions.

## Economic findings and their boundaries

The reset winner depends on the objective and horizon. The 24-hour forecast produces the highest lifetime Radiance among the six tested policies in each 30-day cadence group. The 20% permanent-multiplier rule leads each 90-day group. At three visits/day over 90 days it uses 18 resets, versus 271 for the fixed 10-Chart rule, which produces 84.56% of the matched leader's lifetime income. Multiple policies remain viable under this particular objective; this is no proof of a universally optimal reset moment or of human preference.

All strategies share a first 10-Chart reset and subsequent ten-minute minimum runs, and decide at matching visit/action opportunities. The forecast uses immutable production-engine retain/reset branches, normal retained-boost expiry, automatic purchasing and no future bonus claims or further resets. The strict condition is `100 × reset_gain > 101 × retained_gain`. It assumes full-rate production for its 1/8/24-hour horizon. The independent probe also divides a branch at a real Focus-expiry boundary and reproduces its gain. Reconstruction measures recovery of **unboosted fleet output**, sampled at evaluation boundaries that may be four hours apart; it is an upper bound on observed recovery, not an exact first-passage or payback time.

Notes are actually spent, rather than reserved arithmetically: 12 dossier entries at 100, five extra plan slots at 50, and six decorations at 50 total 1,750 Notes across 23 unique purchases. All 27 long Note trajectories buy all 23 items and complete all 12 dossiers. Independent boundaries cover insufficient balance, plan cap and Chart gate, dossier chapter requirement, duplicate/reopened ownership, and no unrelated economic mutation. Buying unused plan capacity does not silently improve the simulated purchase strategy.

| Once-daily policy | Campaign-first ending bound | Plans-first ending bound | Decorations-first ending bound | Full 23-item collection bound |
|---|---:|---:|---:|---:|
| Surveys only | 20.17 days | 29.17 days | 39.17 days | 59 days |
| At most one ready contract per visit | 15.17 days | 21.17 days | 29.17 days | 44 days |
| Purposeful reflection/season alternatives | 10.17 days | 14.17–15.17 days | 20.17 days | 29–30 days |

These are virtual action/evaluation upper bounds, not observed player durations. The 30-day decorations-first/surveys-only cases are correctly censored as unreached; their longer-run ending is not imputed into the shorter report. The baseline required-calibration/ready-contract policy ends in roughly 10.50–11.17 days across the three cadences. That is compatible with the roadmap allowing skilled players to finish early, but cannot establish its 15–30-day human pacing target. Optional spending can delay a low-check-in ending substantially; keep mandatory campaign costs understandable before interpreting that delay as retention.

The true zero-bonus policy deliberately never completes the chapter requiring three calibrations. `requiredCalibrationsOnly` spends exactly three Focus charges and no Support tokens; it is a distinct minimal-completion policy. `allReady` claims only ready contracts and does not manufacture a 60-Note daily income. Purposeful pursuit uses real repeatable archive reflection and bound seasonal alternatives. The three Note context tuples vary seed, UTC offset and start phase together, so their agreement is a robustness comparison, not an isolated causal estimate of any one factor.

Low tiers remain economically connected: Tier 1 or 2 has the best exact one-unit output/cost ratio in 41 of 225 sampled reachable states, and cross-tier output is positive in all 450 low-tier observations. Both tiers are purchased after day 30 in all 45 long trajectories. The audit independently sums changed producer rates, checks direct/external decomposition, exact affordability and payback ceilings, and compares mathematical rates. Rankings include hypothetical purchases that may not yet be affordable. Late purchases also include rebuilding after resets; neither statistic by itself demonstrates interesting human choices.

The free/ad comparison excludes only route labels, host runtime measurements and serialized byte counts caused by receipt text. It includes all economic result fields and checkpoints. The fixture grants assume successful delivery and use the speed-token route; they do not prove actual rewarded-ad completion, no-fill behavior, provider refusal, or the full alternative offline-slice policy. Those service and branch checks have separate evidence and open native/provider gates.

The two season traces reproduce the 28-day end, frozen archive, and resumed day 31. Main profiles remain unchanged, and injected main Charts are rejected. The newcomer/veteran comparison is structural engine isolation: main profiles are intentionally absent from season initialization. It does not test an identity service, paid entitlement binding or an actual 28-day calendar observation.

## Reproduction, preserved failures and scope

`selected-reproduction.json` lists the 13 exact replays: five baseline cases (zero bonus, required calibrations, the 90-day free/ad hourly-reset pair, and a 120-hour absence) plus eight supplemental cases covering the competing reset winners/fixed threshold, optional-first censoring, and purposeful contracts in varied contexts. Every summary field, transaction, decision, marginal sample and checkpoint is compared after removing only runner-added metadata and runtime. The review did not redundantly rerun all 184 trajectories.

The initial independent fixture tried to construct nine already-awarded Charts, which the production state correctly forbids. Its source and failure log are preserved; the gate probe was corrected to the reachable zero-Chart state. The first author-suite run had one missing-file harness error because the isolated snapshot excluded bundled mobile JSON assets. Thirteen tests passed. Fourteen asset files were separately hash-pinned, and that one unchanged content-equality test then passed. Neither harness error required a product repair; neither failed run is reported as a complete passing suite.

Reproduce the matrix audit with `python3 game/qa/integration_corrected_balance_audit.py <isolated-workspace> <new-output.json>`. From the copied `game/simulation`, resolve dependencies, compile `../qa/integration_corrected_balance.dart` using that package configuration, and execute it with a new result path. The copied `game/simulation/test` cases and source analyzer use the same pinned dependencies. `qa-inputs.json`, `snapshot.json`, `mobile-content-context.json`, logs and `verification.json` record the inputs and outcomes.

`scope-audit.json` checks all 44 requirements and 65 original production packages in both directions, and retains every source acceptance sentence and prerequisite. The four already accepted original foundation packages remain distinct from three bootstrap items. This review adds bounded evidence for S07/S15/S18/S25/S29/S33/S34/S44. M5-05 still requires its original prerequisites, a deliberate beta configuration and metric freeze; M6-03 still requires its prerequisites and any needed versioned repairs/cohort separation. No new package is accepted here.

The user has no developer accounts, hosting, physical test devices or human testers. No current native qualification, store/ad transaction, human pace, real D30, 10,000-session crash denominator, 28-day live season or launch-support period is claimed. No Flutter process was used by this review.
