# Independent review of the initial 88-policy matrix

The recorded matrix is reproducible and its Note/pass ledgers reconcile, but it is not sufficient for a beta balance freeze. One real client defect was reproduced: exhausted dossiers remain advertised as challenge-discovery opportunities. A separate simulator bookkeeping difference omits post-return contract materialization at its final reporting cursor. Neither is an offline earning-cap discrepancy.

The immutable 222-input pin is `1c870326cd1d84559bf5f8e45a0896bf0741018ad27aadbf753a822720eb4212`. It captures the initial 88-row report before the director began the expanded policy runner. All 94 hashes in the report's own source manifest match, as does its source digest `76e961e8c3531fe7e0cf55feb2b79e5dcca9929a9b8cc56ffabc9c2515e25dcd`. Later 94-case work, fixes and moving localization are excluded.

Independent accounting executes 556 assertions over all 88 unique rows. Notes earned equal survey plus contract income and equal dossier spending plus unspent Notes. Contract Notes equal ten per claim; single-pass level equals floor(claims/2), capped at 30. Horizon cursors and checkpoint bounds agree. Twelve full free/ad-fixture trajectory pairs, including checkpoints, match after excluding route labels, runtime and serialized-size differences. Four fresh policy reruns—30-day no-bonus/one visit, 30-day minimal/three visits, 30-day full free Support/six visits/hourly reset, and a 90-day minimal run with a 120-hour break—match all 35 recorded summary fields exactly. These reruns are a sample, not a second execution of all 88 cases.

The five author simulation tests pass independently. Of six new actual-client/worker probes, five pass and one deliberately fails on the reproduced availability defect. Simulation analysis and final QA-test analysis are clean. Earlier QA-only import/diagnostic lint logs are retained; assertions were unchanged. No production source was edited by this review.

| Finding | Evidence and implication | Required action |
|---|---|---|
| **QA014 — unavailable challenge discovery remains offered** | A real GameController with all 12 dossiers completed still includes `challenge` in availableDiscoveries. Reopening and completing challenge.01 again leaves challenge discovery unchanged, its retained goal at zero, and claim rejected. New goals may therefore select a route with no remaining first completion. | Remove this kind from new-assignment availability when no uncompleted dossier remains, across client, offline worker and simulator. Preserve frozen existing goals and their reroll/seasonal escape routes. Re-run the unchanged failing probe. |
| **SIM001 — final contract materialization differs** | After a single 120-hour absence, simulator and native worker match core economics, Support receipt state, dossier state, season and pass. Simulator daily materialization ends at day 20746 with three retained goals; native worker ends at day 20752 with 21. Simulator `advanceTo` does not perform the worker's final daily refresh; visit actions normally do it later. | Align end-of-return bookkeeping, or explicitly label summaries as pre-return-command snapshots. This omission does not retroactively earn Notes and is not evidence of duplicate production. |

The one-absence cap is carried correctly in the tested histories. One-hour and four-hour simulator chunks produce matching core economics, daily state, dossiers, season and pass through 120 hours. With initial one-Skiff/no-autobuy state, 72-hour and 120-hour absences both earn exactly 129,600,000,000 micro-R, while real elapsed time advances to 120 hours and the Focus/Survey queues cap at 12/3. A single typed settlement finalizes once. The native worker comparison uses the shipping worker, not a copied implementation.

The minimal policy consumes exactly three real accessible calibration activations. The no-bonus policy consumes none, and cannot pass chapter three's three-calibration requirement. The actual controller confirms that performing those three completions spends Focus and grants 1,800 seconds of Focus duration. These are distinct baselines: minimal is not zero bonus, and an absent no-bonus ending cannot be treated as an elapsed completion time.

`allReady` claims already complete retained goals. It does not pursue every daily goal, reroll exhausted challenge goals, repeat archive reflections, or bind seasonal alternatives. The actual client allows repeated archive.intro reflections to increment discovery on each deliberate command; the current simulator reads each available archive at most once and only one per action window (two action windows per visit). This is a legitimate conservative policy but cannot stand in for the roadmap's all-contract completion scenario. One-ready-per-visit similarly limits claims, not objective actions.

| Initial 30-day, best-payback / visit-reset policy | One / three / six visits per day |
|---|---|
| Minimal + claim-ready ending upper bounds | 11.17 / 10.50 / 11.17 days |
| Minimal + Surveys-only ending upper bounds | 20.17 / 20.17 / 20.17 days |
| Minimal + claim-ready Notes earned | 1,620 / 1,660 / 1,660 |
| Minimal + Surveys-only Notes earned | 870 / 890 / 890 |

These scripted minimal endings fall below the roadmap's 15–30-day ordinary-play planning range. Perfect policy knowledge, automatic dossier choices, 30-minute onboarding and five-minute visits are modeled assumptions. Resolve the intended pacing envelope before beta freeze; these values do not establish a human pacing distribution or retention rate.

Missing comparisons and qualifications are concrete:

- A purposeful contract policy using actual repeat-archive, reroll and seasonal-alternative commands, sharing the existing claim/XP allowance. Measure one/three/six visits and distinguish partial goals from all goals actually completed.
- Actual spending/availability across the 1,750-Note optional collection budget: mandatory 600 first, all twelve dossiers, and five plans/six decorations. The initial matrix spends only on dossiers and labels the remaining 550-Note budget; affordability is not proof of purchases or acquisition timing.
- Several account seeds, day offsets and seasonal start phases. The initial matrix uses one seed, one UTC offset and one start date; the actual client establishes a random account seed and local fixed day offset.
- Missed-day contract recovery and final-return availability after the bookkeeping repair, including expiration beyond the seven-day backlog. Keep the entire absence's 72-hour earning envelope intact.
- Clear economic comparisons among zero bonus, three required activations, all Focus, free Support and synthetic ad Support. Synthetic receipt parity says nothing about provider delivery, fill or commercial entitlement verification.
- Human learning/playtest and physical-device evidence for ordinary pacing, choice quality, active effort, performance and retention. None is available and none is inferred from these virtual runs.

The scope audit preserves all 44 requirements, 65 original package contracts and dependencies. M5-05 remains in progress; QA014 also maps to S11/M3-02. No beta configuration, metric definition, package or release gate is accepted by this review.
