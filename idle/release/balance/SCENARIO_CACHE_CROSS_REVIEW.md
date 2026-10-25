# Scenario cache cross-review and evidence correction

The previous broad conclusion that numeric memoization preserved the complete game was unsupported. Earlier checks established main-engine arithmetic parity; they did not establish compatibility across subclasses with different economy rules. Those valid main-only observations remain evidence, but they cannot validate challenge or seasonal outcomes.

While authoring the supplemental balance experiments, the gameplay engineer independently found that the static fleet-rate cache used only five producer counts and Charts. `ChallengeEconomy` and the seasonal fleet inherit `outputPerSecond` while changing synergy rules. Main, challenge and event calculations therefore reused one another's output. The wrong rate could affect purchase order and accrued currency; matched runs could agree because they shared the same defect.

At `[25,25,25,25,25]` and zero Charts, priming the main engine made challenge.05 return raw output `8421050000000000000000000000000`, whereas the sum of that challenge's producer outputs was `11381050000000000000000000000000`. The permanent all-rules probe finds an earlier conflict in challenge.03: expected `11341050000000000000000000000000` after the same main rate was cached.

Root authored the repair: only the exact baseline `TideglassEngine` type may use the shared fleet-rate cache. Derived rule engines compute their own output. No price, multiplier, timing or reward constant changed. The gameplay engineer authored the separate regression; QA independently reran it in a copied dependency workspace and reproduced original failure and repaired success.

## Permanent regression

`game/qa/integration_scenario_memo.dart` executes **2,658 assertions**:

- Main, all 12 dossier rule sets and Season1 run in 28 rotated forward/reverse orders over three controlled count vectors. Their output is compared with the preserved pre-cache arithmetic engine and the published matrices.
- 1,300 main fleet states exceed the rate-cache capacity; every scenario is rechecked after eviction.
- All 12 dossiers run valid reachable online and offline traces against an explicitly uncached production scenario oracle. Whole persisted states agree across the 24-hour and 72-hour boundaries.
- Two seasonal traces compare economic fields with the same published matrix in an uncached oracle. Main queues are excluded because seasonal state intentionally does not contain them.

Controlled rate vectors may exceed some dossier berth limits; these are pure formula probes. Separate timeline traces use legal initial fleets and actual purchase constraints. The no-cache timeline oracle shares production price/timeline implementation, so this is a focused test of rule isolation, complemented by the independent preserved pre-cache rate reference—not a wholly independent implementation of every game rule.

`game/qa/run_scenario_memo_probe.py` runs either the current or archived core and records source hashes, process exit, output hashes and unchanged-through-run checks. The original core fails on the expected rate mismatch; the repaired core passes. Exact evidence is in `scenario-cache-original.json/.stderr` and `scenario-cache-current.json/.stdout` beside this report.

## Consequences for balance evidence

Preserve the initial/v2/v3 matrix outputs and the interrupted supplementalv1 report as historical defect evidence. Do not use them to accept scenario isolation, full-game balance, campaign/challenge timing or season pacing. The corrected original matrix is written separately as `long-horizon-v4-policies.json`; the corrected supplemental matrix is `supplemental-v2.json`. Each must finish and receive its own independent review before its conclusions can be relied on. Native candidates containing the defective optimization also need qualification against the repair; a host arithmetic result does not transfer automatically to a native build.

No actual player behavior, retention, beta readiness or release acceptance follows from this repair. Original roadmap gates remain intact.
