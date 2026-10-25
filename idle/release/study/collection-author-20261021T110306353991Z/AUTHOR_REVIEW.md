# Study collection and raw adjudication — author handoff

Author verification completed against the copied source snapshot on 21 October 2026. Independent review is pending. No participant was recruited or observed, and no release/package gate is promoted.

**Source-map fingerprint:** `7a4f2ec7fc782d412161bf68fca3e126ef670b56f247792350a3cefbcae6605f`. `verification.json` records every source hash, exact command, output hash, copied-source drift and current-source drift. Both drift lists are empty. The fingerprint is SHA-256 of the sorted compact JSON source hash map.

## Implemented result

- `game/platform/lib/study_recorder.dart`: explicitly enrolled study storage independent of operational account telemetry. Enrollment atomically persists immutable registry plus earliest app-start before harbor bootstrap. Restarts/inactivity create sessions; short resume/background never implies completion. Actual foreground harbor and activity are separate observations. Exact config identity, capacity/storage/clock gaps, full/minimal withdrawal, canonical hash chain and atomic compare-and-swap storage are implemented.
- `tool/study_adjudicate.py`: validates restricted raw envelopes or the actual Flutter export wrapper against a separately supplied fixed registry, eligibility review and evidence hashes; emits schema-2 analyzer input and provenance audit. Missing streams preserve the denominator. Missing config remains an authentic unknown-outcome session but cannot establish a return. No clean end or crash is invented: explicit terminal/native-crash linkage and matching external evidence files are required.
- `release/study/COLLECTION.md`: exact API, collection/adjudication schema, local storage/withdrawal limits, reproducible commands and original scope mapping. `fixtures/collection-v1/` contains only synthetic data generated through the real recorder.

Root-owned `game/mobile/lib/study_gate.dart` and bootstrap/UI changes are **not** covered by this source pin. Their reviewed API ordering matches this component, but their Flutter tests and native qualification require separate evidence. The module is imported directly; no platform barrel, economic rule, service telemetry, program status or original acceptance contract was edited here.

## Recorded verification

| Check | Result |
|---|---|
| Offline dependency setup in copied snapshot | Passed; copied lockfiles unchanged. |
| Focused recorder suite | 15/15 passed. Covers off-by-default, eligibility guard, startup departure/restart, exact inactivity boundary, foreground proof, missing config, failed/lost writes, capacity/clock gap, withdrawal, tamper, stale writer and actual file/symlink/size faults. |
| Scoped Dart analysis | No issues in recorder, tests or fixture generator. |
| Python suites | 30/30 passed: 17 new raw-adjudication cases plus 13 unchanged descriptive-analyzer cases. |
| Real Dart fixture regeneration | Protocol, registry, raw exports and labels match the captured synthetic inputs byte for byte. |
| Actual adjudicator CLI | Passed on the copied Dart-generated fixture; schema-2 output matches the preserved expected data. |
| Actual descriptive analyzer CLI | Passed on that newly adjudicated output. |

A prior live-workspace full platform run passed 63 tests before this freeze. It is contextual regression evidence, not an additional 63 distinct checks in the pinned component suite; this snapshot's focused evidence is the table above. Early development fixture/path/enum failures and the capacity-test adjustment were resolved before this pin; they are not claimed as passing first attempts.

The fixture preserves three registered installs: one synthetic startup-crash report, one synthetic interactive D30 return (two sessions: reviewed terminal then unknown ending), and one entire raw stream absent. Output has three observed sessions: one crash, one reviewed completion and one unknown. D30 has one observed return and two unresolved return statuses. No complete observation interval is inferred. There are **zero real native crash reports, real clean-exit observations, participants or elapsed D30 cohorts** in this example.

Reproduce from `source/game/platform` with the repository's absolute `tool/dart` path: `pub get --offline`, `test test/study_recorder_test.dart`, and the scoped `analyze` command in the manifest. From `source/`, run `python3 -m unittest discover -s tool -p 'test_study*.py' -v`. The remaining manifest commands regenerate the raw fixture and both actual CLIs using explicit new output directories. `release/study/verify_collection.py` creates a new timestamped verification directory rather than overwriting this evidence.

## Two-way scope audit and remaining gates

| Original work/scope | Narrow contribution | Still open |
|---|---|---|
| M5-04 / S30,S39 | Separate opt-in session/event collection and bounded storage/withdrawal | Approved collection, actual startup/native crash coverage, real quality denominator and deployment/native qualification. |
| M5-05 / S30,S34 | Exact raw-to-schema-2 qualification, conservative missingness and evidence provenance | Actual economic/player study interpretation, truthful observations, independently validated clocks/cohorts and original human gates. |
| M6-01 / S30,S34,S39 | Concrete pre-bootstrap enrollment/eligibility workflow and study audit inputs | Actual recruitment, consent/retention authority, fixed registry administration, physical devices and independent review. |

Reverse mapping: recorder/state/file code serves collection; adjudicator/strict schema serves evidence qualification; fixture generator and tests serve verification; COLLECTION.md serves the study operator/privacy handover. No new gameplay or monetization scope is introduced.

Keep these limits explicit:

1. The local `eligibleFreshInstall` guard and directory probe are supporting implementation evidence, not proof of first-ever install or lawful participant eligibility. Independent review is mandatory. The fixed registry must be maintained separately from returning-player exports.
2. Hash chains and SHA-256 provenance detect captured-data alteration and mismatches, not a malicious complete rewrite, false wall time or forged reviewer assertions. Native clocks/forward jumps, actual device state and evidence truth require qualified audit.
3. Pre-Dart, pre-consent and failed-before-first-write starts cannot be observed by this Dart component. Startup failures are retained only after a successful enrolled app-start write. The population claim is opt-in study, never all-install retention.
4. External report bytes are required and hashed, but a generic CLI cannot authenticate an OS report's meaning. Native process/session/time linkage and clean-terminal adjudication remain explicit independent decisions. Absent terminal evidence stays unknown.
5. Coverage comes only from explicit reviewed evidence. Missing streams, capacity/storage gaps and withdrawal remove it. Default withdrawal erases local identifiers; it cannot recall prior clipboard/shared/exported copies. Retention of even a minimal external registry needs actual approved policy.
6. Default 4,096-record/2 MiB capacity stops with a visible open gap. A real longitudinal study must qualify capacity, retention, storage permissions/backup exclusion and power-loss behavior; no upload, pruning service or remote storage was installed.

No source/package acceptance or external requirement is waived by this author handoff.
