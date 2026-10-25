# QA018: numeric review correction and scenario-cache repair

This addendum **supersedes the broad recommendation to retain the original memoization implementation** in `integration-numeric-20261019T135534237861Z/NUMERIC_REVIEW.md`. That review's exact base-engine arithmetic, eviction and serialization evidence remains valid. It omitted derived engines whose virtual producer rules read different parameters or state, so its compatibility conclusion was incomplete. The immutable old report is retained as history; this correction must accompany it.

The old static total-rate cache used only five counts and Charts. Actual `ChallengeEconomy` and the season fleet override synergy/prestige rules but inherited this cache. Main, challenge and season calls with the same key could return whichever fleet's rate was cached first. The permanent gameplay regression reproduced this against the exact old engine from QA's numeric snapshot: main warmed at counts [25,25,25,25,25] and zero Charts, then dossier 03 returned 8421050000000000000000000000000 instead of 11341050000000000000000000000000 raw units. No mock cache or test-only production edit was involved.

The director's repair limits memoization to the exact baseline `TideglassEngine` runtime type. Derived engines execute the same uncached producer summation. This conservatively covers both different rule parameters within one subclass and additional state read by an override. Using only runtime type as a cache key would not cover those cases. The other three caches are private baseline cumulative-price, count-logarithm and prestige-root functions; their immutable arguments completely identify those formulas. The rate path was different because it calls virtual producer/synergy/prestige/milestone behavior.

| Evidence independently rerun from copied inputs | Result |
|---|---|
| Gameplay's unchanged all-scenario probe against old engine |Fails on actual dossier rate, as expected|
| Same probe against repaired engine |2,658 assertions pass; 26 exact online/offline traces|
| New QA extra-state/parameter probe against old engine |Fails when wallet changes under an unchanged base-rate key|
| Same extra probe against repaired engine |512 assertions pass|
| Repaired core library analysis |Clean|

The gameplay probe checks all 12 dossiers, main and season across 28 rotated forward/reverse call orders and three controlled count vectors, then 1,300 distinct states to churn the 512-entry rate cache. It compares production rates to preserved pre-memoization arithmetic, and compares 26 reachable scenario/season traces through 73 hours (online and carried-offset offline) to direct producer summation. Controlled rate vectors intentionally exceed some dossier caps; the serialized traces use valid fleets. QA's additional probe checks 64 wallet states omitted from the base key, 64 differently parameterized instances of one runtime type, both call orders, unchanged base rates and shared fixed prices. Combined, 3,170 assertions pass. These are host tests, not physical-device performance measurements.

Repaired engine SHA256: `a87e4d6f5fdcb5a169befadba9824df42d792ff4b5cd8d5cf3dfee849c6577d4`.
Old engine SHA256: `99a5c90fd7e893b8c777eaf60e64b7212117b50b0adf60ed0c9fcf1135905150`.
Copied repaired/context source fingerprint: `62fe19032935516675b13874696a15c04a8128bbd96e9f4fa897ed494ad57538`. `snapshot.json` pins original comparison source separately; both trees remain unchanged through the runs. The extra QA runner is separately pinned. A first extra-state fixture incorrectly assigned 25 Charts without earned lifetime and failed validation before reaching the cache. Its source/logs are preserved; the corrected fixture adds sufficient lifetime and then reproduces the actual old-cache mismatch. This harness error is not counted as a production defect or passing regression.

Retain the **repaired guard** at this narrow arithmetic integration level. This does not accept M5-01, beta, full scenarios or balance. The initial 88, v2, v3 and interrupted supplemental v1 simulation conclusions were invalidated by the director and are preserved in `release/balance/INVALIDATED.md` and `invalidated-cache-results.json`. Previously demonstrated main-only algebra remains useful; scenario-sensitive pacing, challenge completion and main outcomes influenced by those scenarios must be regenerated. New v4 and supplemental v2 reports are outside this review and require independent input, feasibility, ledger and trajectory review after completion.

The fresh two-way scope audit covers all 44 requirements and 65 original packages, unchanged source acceptance/dependencies and all four baseline fingerprints. Narrow mappings are S03/S08/S14/S16/S20/S31/S33. Four already-accepted original packages remain separate from three bootstrap items. No additional package or release gate is accepted, and no store, hosting, human cohort, elapsed season or physical-device result is implied.
