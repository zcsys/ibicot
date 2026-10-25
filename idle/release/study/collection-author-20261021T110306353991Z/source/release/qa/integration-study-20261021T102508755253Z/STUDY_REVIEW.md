# Independent descriptive study instrument review

**STUDY001 is repaired in the pinned schema-2 analyzer.** Twelve independent synthetic cases and all thirteen author cases pass. The tool is suitable as a bounded, offline analysis component after its inputs have been independently qualified. It does not collect data, establish cohort provenance or accept a study/release gate.

The 19-input review fingerprint is `4f3e4a50a2aa3f2718359f910501e32ed27ed0cc557173d21e0401f7652c59fd`. Analyzer SHA256: `7109d2e53a8c07b8f00299b749a4c758530e51f38a2d444f4600ae6ef94e7462`. The author manifest hash is `270c7d68a987d8879aeb4da606d774ba4de66bff88eba592d6e4cd7299ce2dd3`. Live source, copied inputs and regenerated synthetic report still match at closure. All runnable records are synthetic; **zero real participants were observed**.

| Independent check | Result |
|---|---|
| Legitimate startup crash without interactive return | Counts one crash and changed-candidate exposure, zero returns; denominator retained |
| Schema contract | Requires separate boolean `valid` and `return_eligible`; rejects invalid-but-return-eligible records |
| Maturity and endpoints | Exact lower endpoint included, upper excluded; per-install maturity and repeated-return deduplication match |
| Missingness | Sparse observed returns remain known; unresolved nonreturns remain in the fixed denominator and widen identification bounds |
| Observation coverage | 800 deterministic interval unions match an independent integer-set oracle, including overlaps, adjacency and gaps |
| Wilson calculation | Numerical inversion of the binomial score inequality using 70-digit Decimal arithmetic matches within `10^-14` across counts 1–100,000 and zero/full/intermediate successes |
| Session outcomes and strata | Explicit crashes, completed sessions and unknown outcomes remain distinct; platform strata reconcile to overall counts |
| Config changes | Do not discard installs; disclose legitimate changed-config records before a window ends, including non-return sessions |
| Actual CLI/privacy failures | Rejects duplicate/nested keys, nonfinite data, malformed/private extra records and oversized input; no private sentinel, identifier or traceback leaked in tested outputs |
| Protocol and release behavior | D7 primary preserved, D30 required; empty/unfilled template rejects; no threshold or maturity flag sets release readiness |

STUDY001 arose because the original documented `valid` field meant a qualified foreground return, and the original analyzer filtered that same field before counting crashes and version exposure. Its synthetic confirmed startup crash therefore disappeared from both summaries. The original source, failed expectations, input and output remain preserved under `integration-study-20261021T102122141873Z` with fingerprint `47c65fb9ef618ffaaf63d4761492d330f7c3a840275abd4046f923f1b352bea8`.

The repair versions data and reports to schema 2. `valid` now identifies an authentic, adjudicated session record; `return_eligible` independently identifies an interactive harbor plus foreground activity. All valid records contribute to crash/unknown outcome and version exposure; only return-eligible starts contribute to Dn. The repaired counterexample explicitly migrates its synthetic schema and semantics, retaining the same expected crash/exposure/return counts. It is not a claim that the old schema-1 input passed unchanged, and no real data was reinterpreted.

The instrument aligns with the existing player protocol's **D7 descriptive primary** and D1/D30 secondary outcomes. First launch precedes loading/onboarding; startup failures and onboarding departures must stay in the independent registry. The analyzer assumes the collector has adjudicated session validity, activity and the 30-minute/process-restart boundary. Current optional account telemetry cannot supply a complete first-launch registry or prove startup crash capture. The implementation does not silently enable such collection.

Dn uses `[first_launch + n days, first_launch + (n+1) days)` and includes only installs with the entire window available at cutoff. Installs that are not yet mature are reported separately. Coverage is the union of supplied positive intervals. An observed qualified return can be known despite incomplete coverage; a missing return with incomplete coverage remains unresolved. For `k` observed returns, `u` unresolved installs and `n` mature eligible installs, identification bounds are `[k/n, (k+u)/n]`. These are missing-data bounds, not confidence intervals. The Wilson interval describes the observed fraction under the stated binomial model and cannot correct missingness, consent or recruitment bias.

The full registered-window D30 flag is an arithmetic check of the supplied cutoff against enrollment end plus 31 days. It cannot prove wall-clock passage, truthful timestamps, complete registry coverage or actual 28-day seasonal observation. Candidate/economy/content hashes identify declared inputs; equal config labels are not proof that a collector recorded the right build. Material version changes still require the original preregistration/cohort decision. Source hashes protect reproducibility, not truthfulness.

The CLI is local and read-only, bounds JSON bytes and record counts, rejects extra record fields and emits aggregate summaries. Install/session IDs and the tested private values do not appear in output. However, categorical-code syntax cannot establish that a label is non-identifying, and small exploratory strata have no cell suppression. This is an internal analysis artifact, not automatically safe public data; actual provenance, consent, withdrawal/deletion, retention and disclosure review remain required before real collection or publication. No human record or external message was created here.

`verification.json`, `qa-inputs.json`, the independent/author logs and regenerated synthetic CLI output contain exact evidence. Reproduce with `STUDY_REVIEW_TOOL=<pinned-tool-path> python3 game/qa/integration_study_test.py`, and run the unchanged author tests from the copied workspace. No Flutter, native build, network service or participant workflow was used.

`scope-audit.json` reconciles all 44 scope requirements and 65 original packages in both directions. Source acceptance/dependencies and the four baseline fingerprints remain unchanged; the four accepted foundation packages stay distinct from three bootstrap items. This review supports preparatory S30/S34/S35 and M5-05/M6-01/M6-02 work. Qualified crash/session capture, 10,000 observed sessions, 500 eligible starts, mature D30, actual season observation, human outcomes and a director release decision remain open. No package or release acceptance is granted by this instrument review.
