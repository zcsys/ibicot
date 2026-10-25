# Tideglass v1 quality protocol

Version 1, 16 October 2026. Author: QA/release agent. Director must independently review this protocol for M0-06. This is an executable test and evidence specification; unrun scenarios are not results.

## Candidate and evidence rules

Every test record names the immutable source fingerprint, economic digest, state/event-order versions, content manifest digest, test harness hash, target device and exact OS, build type, clock/data seed, steps, expected/observed values, logs and reviewer. Keep the original failed record when repairing a defect. A source change invalidates the relevant prior result until its changed path is tested again; it does not erase unrelated evidence.

Build success is separate from launch, gameplay, physical performance, store acceptance and human observation. A zero process exit code alone is insufficient: compile logs must be clean, the fresh artifact must be installed and launched, and results must identify the intended scenario, device and run. `integration-ios-phone-20261016T100415.147682Z` is explicitly excluded: it used a previous binary after a failed compilation. An emulator never supplies physical thermal, battery or human-study evidence.

## Severity and triage

| Severity | Definition | Disposition |
|---|---|---|
| P0 critical | Save loss without recoverable copy, repeatable duplicate economic/ownership grant, negative wallet, or undelivered verified purchase | Stop release/affected rollout; preserve evidence; repair and independently rerun transaction fault matrix |
| P1 major | Required progression or access flow blocked, crash on a critical flow, broken equivalent-value accessibility path, or materially incorrect reset/reward behavior | Blocks release; author repairs; QA reproduces original case and nearby boundaries |
| P2 moderate | Incorrect non-blocking forecast/explanation, unverified required integration, reproducibility/test-provenance failure, or a material coverage gap | Blocks the affected package/gate until fixed or requirement remains explicitly open; cannot waive a hard gate |
| P3 minor | Cosmetic issue with no loss of information, access, ownership or economic correctness | Only director can accept, with owner and dated repair; record in final candidate evidence |

Incomplete scoped features are tracked as gaps, not manufactured defect incidents. Severity describes impact, not how easily a bug can be fixed. Every finding has candidate, reproducible steps, expected/actual result, owner, status and independent retest evidence.

## Reference device execution

`release/device-matrix.json` names iPhone 8, iPhone SE (3rd generation), iPhone 13, Pixel 4a, Pixel 7, iPad 9 and Galaxy Tab A8. Physical availability was confirmed **none** by the user. An iPhone 8 target covers older hardware permitted by the iOS 16 floor; Apple's [iOS 16 compatibility list](https://support.apple.com/en-ie/103267) includes it. A simulator running a newer OS cannot validate iOS 16 compatibility. Record exact installed OS and hardware before execution; do not assume downgrade availability.

For every physical target, run fresh install, upgrade from each supported released schema, first purchase, Rechart cancel/commit, short and 24/48/72-hour return, recovery/import, airplane mode, interrupted saves and storage pressure. Repeat critical flows at maximum supported accessibility text size, reduced motion, screen reader, non-color cues, keyboard where supported, and portrait/tablet layouts. Record semantics and actual discoverability of the equal-value calibration route. Tablets must have usable controls and reading order, not merely a stretched launch screen.

Performance uses a release/profile candidate with instrumentation overhead stated. Disable debugger, fix brightness at 50%, record power-save state, OS, battery health/charge, ambient temperature and networking. Allow thermal recovery between runs. Use the heaviest shipped harbor/cosmetic state and the documented baseline automation policy. Record all runs, including failures.

| Measure | Procedure | Gate |
|---|---|---|
| Frame delivery | Three 10-minute foreground sessions after warm-up; record frame timings and p95 by device | Reference target 60 fps (p95≤16.67 ms); minimum target 30 fps (p95≤33.33 ms); identify jank clusters |
| Cold startup | At least 30 process-cold launches per minimum/reference target; separate first install from ordinary cold starts | p95≤5 s to interactive saved harbor; use nearest-rank percentile and report raw observations |
| 24 h replay | At least 30 fresh runs of each declared supported baseline policy and saved state; reset input every run | p95≤3 s; exactly matching state/cursor; stress replay has visible progress and no dropped time |
| Thermal/battery | Three 30-minute sessions per minimum target under fixed conditions; log thermal state, frame time, battery delta and background CPU | No sustained thermal collapse or required busy background loop; report usability, no invented universal battery threshold |
| Lifecycle | Interrupt at pre-write, post-flush, post-rename, post-grant/pre-ack, suspend/resume and process termination | Latest committed state or retained prior generation; no second claim; failed writes visible |

Thirty repeated timings are engineering coverage, not proof of all-device reliability. The independent 10,000-session crash-free requirement remains a real observation gate with platform/device denominators and confidence intervals.

## Reproducible fixtures and failure paths

| Fixture source | Cases and oracle | Evidence purpose |
|---|---|---|
| `implementation/fixtures/economy_reference.json` | Frozen bounded blueprint price/output/prestige/first-run sequence | Reference conformance; not a production number implementation |
| `game/qa/numeric_oracles.json` | Seed 561230; Python Fraction sums, independent integer binary searches, 90-digit Decimal sqrt/log | Non-author economic comparison; 474 checks in `numeric_probe.dart`, zero tolerance on discrete decisions |
| `game/core/test/persistence_integration_test.dart` | Real core exact values, fractional cursor, stale writer, interruption after rename, chosen branch import | Combined runtime state/storage invariants |
| `game/persistence/test/save_repository_test.dart` | Corrupt latest/both slots, three write boundaries, checksum, untrusted commerce cache, clock reversal | Local failure recovery, not cloud or native power-loss certification |
| `game/mobile/test/bootstrap_test.dart` | Native client envelope, actual temporary files, recovery notice, explicit import/archive | Client/repository integration on host |
| `tool/verify_native.py` and its recorded `harness.dart` | Native purchase, Rechart and separate-process reload harness when present | Native lifecycle evidence only when manifest and fresh artifact match |

Preserve failing fixtures as non-production data. Do not inject test balances into actual player saves. Local checksum validity never proves purchase entitlement. Migrations must use genuinely supported old schemas and record every preserved field; incompatible newer versions fail closed without overwriting.

## Release evidence checklist

1. All 44 scope IDs map to implemented paths and current evidence; reverse audit explains every delivery's scope IDs and flags unrequested additions.
2. All 65 production package acceptances, their original prerequisites and independent reviewers are satisfied; bootstrap acceptance is not product acceptance.
3. Frozen source/config/content/build provenance; iOS/Android installation/update and exact candidate flows; remaining minor issues carry owner/date.
4. Economic boundary, timeline, save/fault, cloud conflict, receipt/refund/revocation and equal free/ad route evidence; zero critical or major blockers.
5. Full six-chapter ending, 12 dossiers, 12 calibrations, 18 archives, 36 cosmetics, 25 producer states, 7 harbor states, actual audio, first season/pass and support pages checked in client.
6. Physical performance/accessibility, 15-novice study, mature D30, 10,000 observed sessions and real 28-day seasonal lifecycle. Each has raw records, population and limitations.
7. Current store/SDK/privacy/account-lifecycle review, authorized signed builds, working URLs/products and actual store acceptance.
8. Monitoring, feature disable/recovery/forward-repair drills, 14 actual days of launch support, owners/costs and Season 2 brief.

Track unavailable resources in `release/external-dependencies.json`; continue independent local implementation. No checklist, simulation or compiled adapter closes an unexecuted gate.
