# Production-engine balance experiments

These are deterministic virtual policies, not human cohorts, optimal-strategy proofs or release acceptance. The engines and content come from the same packages shipped in the native client.

The baseline runner uses the repaired v3 policy adapter and writes a **new v4 report**. Earlier initial/v2/v3 outputs are retained and invalidated for scenario conclusions because they ran with a shared fleet-rate cache that omitted rule identity. `policy_run.dart` itself remains unchanged by this supplemental work. Read `release/balance/INVALIDATED.md` and `SCENARIO_CACHE_CROSS_REVIEW.md` before using old output.

The supplemental runner writes **supplemental-v2** and adds:

- Six reset strategies: fixed additional 10/100 Charts, 20% permanent-multiplier gain, and 1/8/24-hour counterfactual production. They share the first 10-Chart reset, ten-minute minimum run, visit opportunities and production purchase policy. Forecast branches never mutate the live run or grant future bonuses.
- Real spending of all 1,750 Notes: 12 dossier entries, 5 extra plans, 6 decorations, in 3 strict spending orders. Dossier/plan/decoration commands use production transitions. One daily visit is compared under Surveys-only, at most 1 contract per visit, and pursuing actual main/season contract goals.
- Three explicit seed/account-day-offset/start-phase tuples. These are paired robustness contexts, not a factorial causal estimate.
- Exact marginal cost/direct-output/cross-tier-output samples from reachable fleets near days 7/30/60/89, plus actual purchase counts by elapsed stage.
- Identical event start/policy for a new and reachable veteran main profile. The event package accepts neither profile's power; online/offline end/archive transitions and main-power injection rejection are checked.

From this directory:

```sh
../../tool/dart pub get
../../tool/dart analyze
../../tool/dart test
../../tool/dart compile exe bin/run_policies.dart -o /tmp/tideglass-policies-v4
../../tool/dart compile exe bin/run_supplemental.dart -o /tmp/tideglass-supplemental-v2
/tmp/tideglass-policies-v4
/tmp/tideglass-supplemental-v2
```

The supplemental runner refuses to replace an existing report. `--resume` requires exactly matching source hashes. It copies every pinned source/content input to a content-addressed archive and checks those inputs again after the run. The baseline runner supports `--resume` with the same source-digest guard; preserve old reports rather than deleting them. Always execute compiled runners from this directory because content paths are explicit and relative.

From repository root after both reports finish:

```sh
python3 release/balance/compare_corrected_matrices.py
python3 release/balance/summarize_supplemental_v2.py
python3 game/qa/run_scenario_memo_probe.py --output release/balance/scenario-cache-current
```

The 14 author tests include the 6 existing policy checks. The independent cache probe separately checks 2,658 assertions against preserved pre-cache arithmetic and no-memo production scenario traces. QA review of each frozen matrix is separate. Recorded chapter/purchase/reconstruction times are upper bounds at action/evaluation boundaries. Human pace, novelty, comprehension, D30 retention, real seasonal observation, real ad fulfillment and physical-device performance remain external acceptance work.
