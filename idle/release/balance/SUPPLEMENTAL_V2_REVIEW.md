# Supplemental balance experiments — author evidence

Source digest: `394da363f5598c9b4d6ad84be7c85dee351daf3897f5c758a714db5eb6e3e1fb`. The complete report contains **90 virtual 30/90-day trajectories**, 2 paired season checks and 225 sampled reachable fleet states. No economic constants were changed. Original initial/v2/v3 reports, interrupted supplementalv1, and `policy_run.dart` were preserved. Those cache-era scenario outputs are invalidated by the shared fleet-rate cache defect. This run uses the repaired production core; see the independent scenario-cache regression and invalidation note.

This supplements roadmap §7 and packages M5-05/M6-03, informing S07/S18/S25/S29/S33/S44/S34. It does not accept those packages: observed novice behavior, actual learning/decision burden, human pacing, real season observation and D30 retention remain unavailable. Independent review remains separate from this author report.

The tested winner depends on horizon: the 24-hour forecast has the highest lifetime income in each 30-day cadence group, while the 20% multiplier-gain rule leads each 90-day group. At three visits/day over 90 days, that rule makes 18 resets versus 271 for the fixed 10-Chart rule, which earns 84.56% as much lifetime Radiance. These bounded comparisons support evaluating advice around multiplier gain and forecast horizon; they do not establish a universal reset optimum.

Optional spending order matters more to the ending than the full collection total suggests. With one daily visit and Surveys only, campaign-first reaches the ending by day 20.17; plans-first by day 29.17; decorations-first by day 39.17. Buying all 23 items takes 29–30 days when pursuing actual contracts, 44 days with at most one contract per visit, and 59 days with Surveys only. These are virtual purchase/evaluation bounds, excluding human learning. The model should therefore keep optional spending clearly distinguishable from mandatory campaign costs; no prices are changed here.

## Reset comparisons

All strategies share the first 10-Chart reset, the ten-minute minimum run, purchase policy, visit cadence and minimal three required calibrations. Fixed policies request 10 or 100 additional Charts. The multiplier policy requests a 20% increase in actual permanent output multiplier. Forecast policies compare real-engine immutable retain/reset branches over 1/8/24 hours and reset only when newly generated Radiance exceeds the retained branch by more than 1%. They include rebuilding cost and retained-boost expiry, with no hypothetical future bonuses, claims or further resets. Decisions happen at matching action opportunities, not continuously between visits.

The ratio below is lifetime income divided by the best tested strategy at the same horizon and cadence. It is not a proof of a globally optimal policy. Reconstruction observations are upper bounds at evaluation boundaries (up to four-hour offline chunks); they are not exact recovery times.

| Days | Visits/day | Reset strategy | Recharts | Lifetime / matched best | Ending day ≤ |
|---:|---:|---|---:|---:|---:|
| 30 | 1 | fixed-10-charts | 31 | 0.9731 | 10.17 |
| 30 | 1 | fixed-100-charts | 30 | 0.9612 | 10.17 |
| 30 | 1 | multiplier-20-percent | 11 | 0.9819 | 11.17 |
| 30 | 1 | forecast-1h-output-1percent-margin | 8 | 0.8931 | 11.17 |
| 30 | 1 | forecast-8h-output-1percent-margin | 11 | 0.9720 | 10.17 |
| 30 | 1 | forecast-24h-output-1percent-margin | 14 | 1.0000 | 11.17 |
| 30 | 3 | fixed-10-charts | 91 | 0.9014 | 10.17 |
| 30 | 3 | fixed-100-charts | 90 | 0.8971 | 10.17 |
| 30 | 3 | multiplier-20-percent | 15 | 0.9874 | 10.17 |
| 30 | 3 | forecast-1h-output-1percent-margin | 10 | 0.9014 | 10.503 |
| 30 | 3 | forecast-8h-output-1percent-margin | 16 | 0.9722 | 10.503 |
| 30 | 3 | forecast-24h-output-1percent-margin | 22 | 1.0000 | 10.503 |
| 30 | 6 | fixed-10-charts | 181 | 0.8478 | 11.167 |
| 30 | 6 | fixed-100-charts | 180 | 0.8454 | 11.167 |
| 30 | 6 | multiplier-20-percent | 17 | 0.9898 | 11.167 |
| 30 | 6 | forecast-1h-output-1percent-margin | 12 | 0.8985 | 11.167 |
| 30 | 6 | forecast-8h-output-1percent-margin | 20 | 0.9791 | 11.167 |
| 30 | 6 | forecast-24h-output-1percent-margin | 30 | 1.0000 | 11.167 |
| 90 | 1 | fixed-10-charts | 91 | 0.9319 | 10.17 |
| 90 | 1 | fixed-100-charts | 90 | 0.9283 | 10.17 |
| 90 | 1 | multiplier-20-percent | 15 | 1.0000 | 11.17 |
| 90 | 1 | forecast-1h-output-1percent-margin | 9 | 0.8443 | 11.17 |
| 90 | 1 | forecast-8h-output-1percent-margin | 13 | 0.9647 | 10.17 |
| 90 | 1 | forecast-24h-output-1percent-margin | 17 | 0.9905 | 11.17 |
| 90 | 3 | fixed-10-charts | 271 | 0.8456 | 10.17 |
| 90 | 3 | fixed-100-charts | 270 | 0.8443 | 10.17 |
| 90 | 3 | multiplier-20-percent | 18 | 1.0000 | 10.17 |
| 90 | 3 | forecast-1h-output-1percent-margin | 11 | 0.8584 | 10.503 |
| 90 | 3 | forecast-8h-output-1percent-margin | 18 | 0.9471 | 10.503 |
| 90 | 3 | forecast-24h-output-1percent-margin | 24 | 0.9907 | 10.503 |
| 90 | 6 | fixed-10-charts | 541 | 0.7914 | 11.167 |
| 90 | 6 | fixed-100-charts | 540 | 0.7907 | 11.167 |
| 90 | 6 | multiplier-20-percent | 20 | 1.0000 | 11.167 |
| 90 | 6 | forecast-1h-output-1percent-margin | 13 | 0.8836 | 11.167 |
| 90 | 6 | forecast-8h-output-1percent-margin | 22 | 0.9624 | 11.167 |
| 90 | 6 | forecast-24h-output-1percent-margin | 32 | 0.9898 | 11.167 |

## Real Note spending

Each purchase invokes production transitions: 12 dossiers × 100 Notes, five extra plans × 50 Notes, and six decorations × 50 Notes. The simulation spends the full 1,750 Notes when affordable; it does not merely reserve an arithmetic budget. Orders are strict wish lists: campaign-first buys six mandatory and then six optional dossiers before plans/decorations; plans-first buys plans, mandatory dossiers, decorations and optional dossiers; decorations-first buys decorations, plans and all dossiers. An unavailable first remaining item waits. Dossier execution is sequential. Extra plan capacity is bought but does not silently improve the chosen automation policy.

Each row spans three paired context tuples: seed-a / UTC+00:00 / midnight UTC start; seed-b / UTC+03:00 / 23:55 UTC start; seed-c / UTC−07:00 / 05:30 UTC start. These varied tuples test robustness; they do not isolate causal seed, offset and phase effects. All Note runs use one visit/day. Partial contracts claim at most one per visit; pursuing contracts uses actual reflections and seasonal alternatives, with no invented completion or 60-Note/day assumption.

| Horizon | Contract policy | Spending order | Ending day ≤ range | All 23 purchases day ≤ range |
|---:|---|---|---:|---:|
| 30 | oneReadyPerVisit | campaignFirst | 15.17–15.17 | Unreached |
| 30 | oneReadyPerVisit | decorationsFirst | 29.17–29.17 | Unreached |
| 30 | oneReadyPerVisit | plansFirst | 21.17–21.17 | Unreached |
| 30 | pursueWithSeason | campaignFirst | 10.17–10.17 | 29.00–29.00 (2 unreached) |
| 30 | pursueWithSeason | decorationsFirst | 20.17–20.17 | 29.00–29.00 (2 unreached) |
| 30 | pursueWithSeason | plansFirst | 14.17–15.17 | 29.00–29.00 (2 unreached) |
| 30 | surveysOnly | campaignFirst | 20.17–20.17 | Unreached |
| 30 | surveysOnly | decorationsFirst | Unreached | Unreached |
| 30 | surveysOnly | plansFirst | 29.17–29.17 | Unreached |
| 90 | oneReadyPerVisit | campaignFirst | 15.17–15.17 | 44.00–44.00 |
| 90 | oneReadyPerVisit | decorationsFirst | 29.17–29.17 | 44.00–44.00 |
| 90 | oneReadyPerVisit | plansFirst | 21.17–21.17 | 44.00–44.00 |
| 90 | pursueWithSeason | campaignFirst | 10.17–10.17 | 29.00–30.00 |
| 90 | pursueWithSeason | decorationsFirst | 20.17–20.17 | 29.00–30.00 |
| 90 | pursueWithSeason | plansFirst | 14.17–15.17 | 29.00–30.00 |
| 90 | surveysOnly | campaignFirst | 20.17–20.17 | 59.00–59.00 |
| 90 | surveysOnly | decorationsFirst | 39.17–39.17 | 59.00–59.00 |
| 90 | surveysOnly | plansFirst | 29.17–29.17 | 59.00–59.00 |

All trajectories conserve Notes: surveys + contract Notes = remaining Notes + all actual sinks. No economic reward was imported from challenge or seasonal fleets.

## Low-tier relevance and isolation

The exact one-unit marginal ranking places Tier 1 or Tier 2 first in **41/225** sampled states. Cross-tier output contributes positively in **450/450** low-tier marginal observations. Both low tiers are purchased after day 30 in **45/45** long trajectories. Those purchases include reconstruction after resets; they alone do not prove interesting human choices. The raw report separates direct output from synergy externality and includes exact cost/rate integers and late purchase counts.

New and reachable veteran profiles have byte-identical event states under matched continuous-online and daily-offline schedules through the 28-day end, paused archive and resumed day 31. Main profiles remain unchanged; injecting main Charts into the event fleet is rejected. Event initialization accepts no main-profile or paid-power input. This verifies engine separation, not actual account-service or UI identity binding.

## Reproduction and limits

From `game/simulation`: run `../../tool/dart analyze`, `../../tool/dart test`, compile `bin/run_supplemental.dart` with the project launcher, then execute the compiled binary from that directory. The runner refuses to overwrite an existing report; `--resume` requires an identical source digest. Every pinned input is copied into the content-addressed source archive and unchanged input hashes are checked after the full run. From repository root, run `python3 release/balance/summarize_supplemental_v2.py` to regenerate these tables.

Author checks cover eight supplemental tests plus six unchanged v3 harness tests. The shared decoration extraction has independent 49/50-Note boundary, duplicate, invalid-ID and unrelated-state conservation checks here. Model tests, exact trajectories and host execution do not replace human onboarding comprehension, D30 cohorts, physical-device performance, real store/ad delivery, sustained live operations or a mature seasonal study. No product acceptance threshold was reduced.

Raw report SHA256: `16aa9e488af37cf91489d75c53aadb4617117cd0013f2cb866eec24610005ff8`.
