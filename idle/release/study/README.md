# Tideglass player-study instrument

This is a working local analysis tool and an unfilled preregistration template. There are **no observed participants or mature player cohorts** in this directory. Every runnable example is synthetic. It prepares M5-05/M6-01/M6-02 and S34/S35; session accounting supports S30. It does not close recruitment, actual 28-day season, D30, device-quality or release gates.

## Run and interpret

```sh
python3 tool/study_report.py --protocol release/study/fixtures/synthetic-protocol.json --data release/study/fixtures/synthetic-data.json
python3 -m unittest discover -s tool -p test_study_report.py -v
```

The CLI reads explicit local JSON files, writes aggregate JSON to standard output, and never contacts a service. It returns 0 for a valid descriptive report and 2 for invalid input. A 0 exit is not study approval. It rejects duplicate installs/sessions, unknown installs, unregistered exclusions, mixed baseline configurations, future timestamps, malformed intervals, duplicate JSON keys and test platforms in real-study inputs. Input size and row counts are bounded. Error output omits records and raw exception text. Do not commit real participant records, even when pseudonymous.

A report pins both exact input files and the analyzer by SHA-256. Preserve these with the preregistration approval and the independent provenance audit. An input hash establishes which file was analyzed; it does not establish that the file is truthful or complete. The fixed registry is independent of the session table, so an install with no return remains in the denominator. Current service telemetry requires an optional consenting account and therefore cannot supply an all-install first-launch registry. No new collection or privacy consent is enabled by this tool.

## Definitions fixed before enrollment

| Variable | Definition |
|---|---|
| Population | Explicitly declared all-eligible first-launch registry or opt-in study; never silently generalize the latter to all players |
| Eligibility | First launch in the preregistered half-open enrollment interval; one opaque study ID per eligible install |
| Exclusions | Staff, automation, known-invalid installs under rules fixed before enrollment; leaving onboarding is not an exclusion |
| Primary outcome | Descriptive D7, matching the existing player protocol; D1/D30 are required secondary outcomes |
| Dn window | `[first_launch + n × 86,400, first_launch + (n + 1) × 86,400)` UTC seconds; a session exactly at the upper boundary is outside |
| Maturity | Include an install for Dn only when the whole age window has elapsed; report immature counts separately |
| Return | At least one adjudicated valid session starting in that window with interactive foreground harbor and activity; repeated sessions count once |
| Coverage | Union of positive observable intervals; missing telemetry is not evidence of absence |
| Missingness | Keep the fixed eligible denominator; report observed returns and unknown-return bounds |
| Baseline | Exact candidate, economy and content hashes plus config; mixed initial configs are rejected |
| Experience changes | Sessions on another config are disclosed and remain in the primary denominator; a material revision needs a separate preregistered cohort |
| Quality | Explicit crashes, completed sessions without reported crash, and unknown outcomes are distinct; missing ends are never declared crash-free |

Complete `protocol-template.json` before enrollment. Its null fields intentionally fail validation. Dates in the synthetic fixture are artificial arithmetic inputs, not elapsed study evidence. The protocol's `registry_source`, `session_definition` and `missing_data_rule` must describe the actual approved collection pipeline. Reviewer approval must establish population completeness, lawful retention/deletion, source clock validity, reinstall/duplicate handling, bot/staff identification, recording gaps and version assignment. Observable intervals must come from that audit; do not fill the whole follow-up interval merely because consent was once granted. Withdrawal/deletion must be honored, with any lawfully retained aggregate missingness reported honestly.

The full registered enrollment window is labeled D30-mature only after enrollment end plus 31 days. Individual mature-window summaries may appear earlier and are explicitly provisional while enrollment remains open or part of the cohort lacks opportunity. The tool does not wait for elapsed time or generate observations.

## Uncertainty and decisions

For `k` observed returns among `n` mature eligible installs, the reported observed fraction is `k/n`. If `u` installs have neither an observed return nor full observation coverage, the missing-data identification bounds are `[k/n, (k+u)/n]`. These bounds are not confidence intervals. They describe what remains unidentified under the supplied coverage record.

Two-sided 95% Wilson score intervals use `z = 1.959963984540054`. The [NIST description of binomial proportion intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) supports the calculation. Those intervals quantify binomial sampling uncertainty in the observed fraction; they do not repair consent, recruitment, measurement or missing-data bias. A descriptive sample of 500 with 35 observed D30 returns has approximately a 5.1%–9.6% Wilson interval. Five hundred starts is a planning target, not a power guarantee.

D1 ≥35%, D7 ≥15%, D30 ≥7% remain review hypotheses. No threshold automatically authorizes launch. Platform/device and acquisition strata are exploratory, without multiplicity adjustment, and may be too small for useful comparison. This instrument preserves the [existing player protocol](../../docs/quality/PLAYER_STUDY_PROTOCOL.md): first launch precedes loading/onboarding, valid returns need interactive harbor plus activity, and sessions restart after 30 minutes of inactivity or process restart. The supplied `return_eligible` field must come from qualified adjudication against those rules; this analyzer cannot manufacture missing activity signals. It intentionally rejects a causal-experiment design: an A/B study additionally needs a preregistered allocation method, primary estimand, MDE, power/precision, stopping rule and analysis plan before enrollment.

The 10,000 observed sessions / 99.5% crash-free requirement additionally needs qualified native crash reporting and critical-flow review. The conservative completed-session fraction here cannot establish that requirement on its own. First-prestige reachers/non-reachers, moderated comprehension, welfare interviews, campaign outcomes and commercial operating costs still require the separate [study instrument](../qa/study-instrument.json) and real observations.

## Input contract

The executable synthetic files show every allowed field. All timestamps are integer UTC seconds. Install `id` and session `session_id` are opaque study tokens; device/acquisition/config fields are categorical codes, not names or contact information. `observable_intervals` is a list of `[start,end]` pairs; overlapping and adjacent coverage is unioned. Data/report schema version 2 separates record validity from return eligibility. Session `end` can be null; `crashed`, `valid` and `return_eligible` are explicit booleans. `valid` means an authentic, adjudicated session record, including a startup crash before the harbor appears. `return_eligible` additionally requires interactive harbor and foreground activity; an invalid record cannot be return-eligible. All valid records count for crash/unknown-outcome and changed-config exposure reports, even when they are not eligible returns. A valid session whose end is absent has an unknown outcome unless a crash is explicitly recorded. Invalid records do not produce returns but remain counted as rejected records. The native collector must actually observe startup failures; this offline tool cannot create them. Extra record fields are rejected to avoid accidentally feeding raw account/contact/receipt data into this analyzer.

## Current evidence

Thirteen author cases pass, including exact D30 cutoff/boundaries, missing observations, exclusion rules, config changes, interval union/gaps, unknown/crashed sessions, Wilson reference values, empty registries, invalid inputs and the actual CLI. `synthetic-report.json` demonstrates three eligible synthetic installs: one observed D30 return, one unresolved return, bounds 1/3–2/3. One automation record is excluded under the declared rule. Independent review remains required and is recorded separately; this directory is not empirical player evidence.

Independent finding STUDY001 corrected the initial conflation of record validity and return eligibility. The initial schema-1 counterexample and failure remain in the independent review archive. The current schema-2 example is synthetic; this change does not migrate or reinterpret any real participant data.
