# Opt-in study collection and evidence adjudication

This is an implemented **local preparation lane**, separate from operational account telemetry. There are zero enrolled people, zero observed player sessions and no approved live study deployment. It supports M5-04/M5-05/M6-01 preparation and S30/S34/S39. It does not establish any empirical denominator, elapsed D30, native quality threshold, ethical/legal approval or release acceptance.

## Enrollment and startup boundary

`game/platform/lib/study_recorder.dart` is a pure-Dart module. Importing/opening it does not enroll or reconstruct events. A new recorder has no registry, no events and makes no writes until an explicit successful `enroll`. The root-owned Flutter wrapper is `game/mobile/lib/study_gate.dart`; it is a separate integration requiring its own widget/native verification. An ordinary build without explicit study provisioning should never open the study store or display enrollment. Operational telemetry retains its separate account/consent semantics.

Before calling `enroll`, the wrapper must present the approved information/contact/retention terms, obtain voluntary study consent, confirm that ordinary game bootstrap has not started and no existing normal-game save is present, and persist the exact local eligibility-check artifact. The artifact is supporting evidence, not proof of first-ever install, reinstall history, cloud restoration or participant eligibility. Those require independent audit before qualification. An already-played harbor cannot be backfilled into a first-launch cohort.

Enrollment atomically writes an opaque random 128-bit install token, the frozen registry and the first `app_start` at the same UTC second. Only after awaiting that durable operation may the wrapper start the harbor bootstrap. The immediately following `beginProcess` is idempotent in the same recorder. Reopening after process death and awaiting `beginProcess` adds a new process/session start before bootstrap; it never assumes the previous process ended cleanly. Thus an enrolled startup departure before an interactive harbor remains visible. OS/native failures before Dart, failures before opt-in, and failures before the first successful store write remain outside this collector's observation. A local registry cannot recreate those missing starts.

The approved study team must maintain the **fixed registry independently of later event exports**. The analysis CLI requires that separate registry and does not infer enrollment from returning players. A missing raw export remains a registry entry with unknown follow-up. This implementation is an opt-in study collector, never an all-install measurement claim.

## Small API and storage contract

| API | Required meaning |
|---|---|
| `StudyRecorder.open(store, clock?, idGenerator?, maximumRecords?, maximumBytes?)` | Load canonical existing data or remain disabled. Corruption fails without replacement. Overrides are for deterministic tests; production uses UTC clock and secure random IDs. |
| `enroll(enrollment, baseline, eligibleFreshInstall: true)` | Explicit consented, pre-bootstrap fresh-save check already performed; the flag alone does not qualify eligibility. Writes registry + first start atomically. |
| `beginProcess(config: StudyConfig?)` | Before eligible bootstrap on each enrolled process; missing current config is recorded explicitly and cannot establish a qualified return. |
| `foreground()` / `background()` | Actual foreground state. A short resume does not create a session or clean terminal. |
| `interactiveHarbor()` | Call after the harbor is actually interactive in foreground, including after a new session's settled resume. Repeated callbacks in an already interactive session are idempotent. |
| `activity(StudyActivity.interaction)` | Actual foreground pointer, key or accessibility action. No automatic simulation/progression notifications. Other enum values can label directly observed actions. |
| `noteGap(reason)` | Record a known collection interruption; never invent missing actions. |
| `terminal(explicitlyObservedCleanExit)` | Only an actually observed clean terminal boundary, not lifecycle background, disposal or an absence of crashes. The adjudicator additionally requires explicit external terminal review to produce an analyzer end. |
| `withdraw()` | Default: erase local study identifiers/records and retain a nonidentifying stop marker. No reenrollment of that registry. Does not erase externally exported copies. |
| `withdraw(retainMinimalRegistry: true)` | Only under explicit approved retention policy. Deletes behavioral history; retains initial start/registry plus erasure gap and withdrawal. It cannot establish a return or complete follow-up. |
| `registry`, `exportRaw()`, `installId`, `sessionId`, `processId` | Restricted local study export/linkage values. Never put them in ordinary account telemetry, public logs or gameplay saves. |

`StudyConfig` contains exact candidate, economy and content SHA-256 plus categorical config label. `StudyEnrollment` records study/protocol/information/consent identity, a local eligibility evidence hash, explicit synthetic marker and restricted platform/device/acquisition categories. There is no account ID, recovery code, receipt, email, free-text activity payload or gameplay balance field.

Sessions begin on process restart or after at least 1,800 seconds of inactivity. An interactive foreground harbor and actual foreground activity must both occur in the same session before it can be return-eligible. A new inactivity session clears the old harbor proof. Background pings do not qualify. UTC timestamps are integer seconds; wall-clock reversal halts collection and records an open gap at the last valid timestamp. Device clock authenticity and forward jumps still need the actual native/operating audit; neither hash chains nor supplied calendar timestamps prove elapsed time.

The default bound is 4,096 records / 2 MiB. At capacity, the recorder preserves the earliest registry/history, records an open gap and stops; it does not evict old starts or silently continue with an incomplete denominator. A maximum 100,000-record / 32 MiB bound is supported for explicitly provisioned tests/approved operation. A 30-day study must qualify its actual event rate and export/retention arrangement before enrollment; the default is not a promise of sufficient capacity. No export acknowledgement or automatic pruning/upload is implemented. Capture failure must be visible while guest gameplay remains available.

`StudyStore` exposes read and compare-and-swap of the entire canonical document. Operations are serialized per recorder; stale writers cannot overwrite newer state. `AtomicStudyFileStore` checks for detected symlinks and oversize files, uses a file lock, writes/flushed bytes in a unique temporary directory and atomically renames into place. It requires an app-private directory; native sandbox, backup exclusion, encryption/erasure, storage permissions and power-loss/directory-metadata durability need device qualification. Hash chaining detects alteration/replay of a captured history; a party capable of rewriting the whole file and recomputing all hashes can forge a history. It is not remote attestation or a signed trusted clock.

## Restricted export and adjudication inputs

A root wrapper export is exactly:

```json
{"schema_version":1,"raw":{"schema_version":1,"registry":{},"records":[],"status":"active"},"eligibility_evidence":{"schema_version":1,"check":"no_prior_game_directory_entries","checked_at":"UTC ISO timestamp","study_id":"categorical_code","candidate_sha256":"64 lowercase hex"}}
```

The abbreviated registry/events above are illustrative, not valid records. Runnable, fully populated synthetic files are in `fixtures/collection-v1/`. The adjudicator verifies the local eligibility artifact's canonical hash, study/candidate binding and timestamp within five minutes before enrollment. A valid artifact still requires the separate eligibility review; the tool cannot verify its underlying device claim.

For a multi-install study, raw input is `{schema_version:1, study_id, synthetic, exports:[wrapper,...]}`. An entry may instead be `{install_id,raw}` when the matching local evidence artifact is supplied separately. Duplicate exports, changed registry data, event replay, unknown fields and broken chains are rejected. Default erased markers have no identity; they are not offered by the app as participant exports. Authorized study staff can record an erased stream against an independently retained lawful registry entry using the explicit `{install_id,raw}` form. If registry retention itself is not lawful, do not preserve it merely to satisfy a denominator: document lawful aggregate losses outside this tool and revise the study disclosure.

The registry file has `{schema_version:1, study_id, synthetic, entries:[registry,...]}`. The review file has exactly:

| Field | Contents |
|---|---|
| `schema_version`, `study_id`, `synthetic`, `cutoff` | Version 1, matched study/population and UTC-second cutoff. |
| `installs` | One decision per fixed registry entry: `install_id`, `eligibility_review: "qualified"`, matching `eligibility_evidence_sha256`, `exclusion` (null/staff/automation/invalid_install), and `coverage`. Unqualified eligibility stops adjudication; dropout is never an exclusion. |
| `coverage` per install | Explicit audited intervals with `start`, `end`, `evidence_sha256`. No intervals are inferred from consent, absence of events or lack of crashes. Missing streams, recorded gaps and withdrawal remove coverage. |
| `native_crashes` | `install_id`, `session_id`, `process_id`, `crash_at`, `report_sha256`, `linkage_reviewed: true`. Actual external report bytes must exist and match the hash; process/session/time linkage must be independently reviewed. Missing terminal events are not crashes. |
| `terminal_reviews` | `install_id`, `session_id`, matching observed `terminal_event_sha256`, `evidence_sha256`. Missing event or review remains unknown; the tool never equates background with completion. |

External artifacts are local regular files named `<sha256>.evidence` in the explicit evidence directory, each bounded to 32 MiB. Their bytes are hashed but never copied into output or printed. The tool cannot determine that an arbitrary report is truthful or that a reviewer was qualified; the explicit review is an operating input, not automatic native certification. The audit therefore retains `native_linkage_independently_verified: false`. Do not substitute a synthetic fixture report for a real report.

All normal JSON inputs are bounded to 32 MiB, duplicate keys/nonfinite numbers/extra fields are rejected, and IDs must be opaque 32-character lowercase hex tokens. Output data is schema 2 for the separately reviewed `study_report.py`. A missing current config keeps an authentic session in the quality/unknown-outcome count with `config: unqualified_config`, but cannot establish a return. Reusing a config label with different exact hashes is rejected. An actual changed config is disclosed and never removes the enrolled install.

## Reproduce the synthetic round trip

Run from the repository root:

```sh
python3 -m unittest discover -s tool -p 'test_study*.py' -v
python3 tool/study_adjudicate.py --protocol release/study/fixtures/collection-v1/protocol.json --registry release/study/fixtures/collection-v1/registry.json --raw release/study/fixtures/collection-v1/raw.json --review release/study/fixtures/collection-v1/review.json --evidence-dir release/study/fixtures/collection-v1/evidence --output-dir /absolute/new-private-output
python3 tool/study_report.py --protocol release/study/fixtures/collection-v1/protocol.json --data /absolute/new-private-output/data.json
```

The output directory must be new; it is created mode 0700 with 0600 data/audit files. Standard output contains counts/hashes, not install/session IDs. `data.json` contains restricted opaque records, while `adjudication.json` pins source/evidence/tool hashes and limits. The downstream analyzer produces descriptive aggregates; none is automatically suitable for public release without a disclosure review.

From `game/platform/`, use `../../tool/dart test test/study_recorder_test.dart`. `../../tool/dart run test/study_fixture_export.dart /absolute/new-fixture-directory` regenerates raw synthetic recorder exports through the real Dart implementation. Its three registries represent a synthetic startup departure, a synthetic interactive return and a completely missing raw stream. The separately labelled synthetic review supplies one crash and one terminal fixture. Expected schema-2 result: three registered installs, three observed sessions (one crash, one reviewed completion, one unknown), one D30 return and two unresolved returns; no full observable interval is asserted. These are counterexamples and code checks, not three people or 30 elapsed days.

## Acceptance and reverse mapping

| Contribution | Original scope contribution | Still required |
|---|---|---|
| Recorder and pre-bootstrap enrollment API | M5-04/S30,S39; M6-01 study preparation | Actual approved recruitment/consent and independent registry/device/startup qualification; no native pre-Dart capture is claimed. |
| Raw adjudication, exact configuration and evidence linkage | M5-05/M6-01, S30/S34 | Independent review, truthful clocks, valid external crash evidence, population/coverage audit and real cohorts. |
| Withdrawal, bounded storage and restricted exports | S39 | Actual retention/deletion authority, native storage/backup qualification and cleanup of previously exported copies. |
| Synthetic generator/tests/provenance | Evidence for these narrow implementations | No S30 quality denominator, S34 retention, human pacing, season or release acceptance. |

Conversely, `study_recorder.dart` serves consented collection; `study_adjudicate.py` serves raw qualification; tests/fixtures serve implementation verification; this document specifies operator and privacy boundaries. They introduce no economic changes, no automatic outbound collection and no new release thresholds. Root-owned Flutter integration has a separate source pin and tests; do not silently extend the pure-Dart author evidence to that UI.
