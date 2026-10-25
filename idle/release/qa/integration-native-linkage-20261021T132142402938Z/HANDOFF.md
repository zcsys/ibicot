# Native process linkage — staged implementation handoff

This is measurement preparation for M5-01/S30. It is not evidence of observed player sessions, a crash-free rate, store acceptance, actual consent, or native execution. All supplied reports, native binary structures, installation records and enrollment examples are explicitly synthetic. No live runtime files were edited by this lane; promotion is subject to the lead's source window and independent review.

## Changes ready for review

| Area | Implemented behavior |
|---|---|
| Consent | Actual visible disclosure precedes consent controls. Sampling happens only after agreement or restoration of the exact disclosed-information hash. Empty provision does no study/native I/O. Legacy information hash restores old records without collecting a PID. Exhausted/withdrawn state does not sample. |
| Native channel | Dedicated `dev.tideglass/study_process`, method `observe`; public PID, package/version/build and current UTC observation. Registration does not sample. No diagnostic collection, crash handler, upload, clipboard read, device ID or uptime collection. |
| Typed context | Available schema has nine exact fields; PID, strings and integer time are bounded. Unavailable schema has only version/status/reason from a fixed allowlist. Dart and Python reject fractional versions, unknown fields and the removed uptime field. |
| Atomicity | One CAS commits `app_start` plus context. An unavailable context commits its explicit zero-duration instrumentation gap in the same CAS. Enrollment followed by `beginProcess` is idempotent. |
| Migration | Schema1 stays readable. Schema2 appends onto the exact legacy registry/event chain without changing previous canonical bytes or hashes. New schema2 starts cannot omit availability or downgrade to old start payloads. |
| Withdrawal | Schema2 withdrawal erases all PID/context records even when the legacy minimal-registry option is requested. Existing sidecar stop-marker/erasure handling remains. |
| Failed restart | A failed restart exposes the last committed process identity. On retry its storage gap belongs to that committed process, followed by the new start. Capacity/clock-failure starts likewise never attribute a gap to an uncommitted process. |
| Adjudication | Legacy boolean-only crash reviews remain unknown. Actual supported native fatal reports require exact release app-code bytes, independent installation provenance, one process interval and one session interval. Gaps, withdrawal, missing fields, unsupported reports, ambiguity and hash changes fail closed. |

The native observation time is when the consented adapter was called, **not kernel launch time**. It is checked within five seconds of the event timestamp. Device UTC is not authenticated. The external diagnostic must independently provide launch/uptime and crash time. PID alone is never sufficient. Logical inactivity sessions can share a native process.

## Exact contracts

Available context (stored only in schema2 `app_start.payload.native_context`):

```json
{"version":1,"status":"available","source":"native_process_observation_v1","native_pid":123,"platform":"ios","application_id":"dev.tideglass.game","application_version":"1.0.0","application_build":"1","observed_start_utc_ms":100000}
```

Unavailable context is `{"version":1,"status":"unavailable","reason":"native_unavailable"}`. Other allowed reasons: `unsupported_platform`, `invalid_native_context`, `not_requested`, `consent_not_granted`. A native unavailable result records an instrumentation gap; it does not invent a fatal report. PID is 2..2147483647; UTC milliseconds are integer 0..2^53−1; context is at most 2048 serialized bytes. No uptime is retained or exported.

Legacy registry fields and envelope wrapper version remain unchanged. Raw document version becomes2 only when a native-availability start is appended. The fixed-cohort decoder strips internal native context from aggregate session output. Raw exports remain restricted consented study material.

A new `native_crashes` review row has exactly `install_id`, `report_sha256`, `manifest_sha256`, `provenance_sha256`. Evidence is a fixed `<sha256>.evidence` file, not a caller-controlled path. Regular files, hashes and bounded sizes are checked before parsing. A copied boolean-only legacy row is retained as `unknown_native_diagnostics` reason `legacy_boolean_review_has_no_native_link`; its assertion is never trusted.

Release manifest exact keys:

- `schema_version:1`, `kind:tideglass_native_release_manifest`, `candidate_sha256`, `build_mode:release`, `code_mode:aot`, `artifact_sha256`, `build_provenance_sha256`, `binaries` (1..32).
- Each binary: `platform`, `application_id`, `application_version`, `application_build`, `binary_role:dart_aot_app_code`, `binary_path`, `binary_name`, `binary_id_kind`, `binary_id`, `binary_sha256`.
- iOS accepts only `App`, `macho_uuid`, and `[Payload/]NAME.app/Frameworks/App.framework/App`. Android accepts only `libapp.so`, `elf_build_id`, and `[base/]lib/{arm64-v8a,armeabi-v7a,x86_64}/libapp.so`.
- Exact bytes must be present once inside the hashed ZIP/AAB and equal the separate hashed app-code file. UUID/GNU build-ID is extracted from the actual Mach-O/ELF bytes, not trusted from manifest text. Launcher/engine identity, debug/JIT/profile or a conflicting candidate remain unlinked.
- Build provenance exact keys: `schema_version:1`, `kind:native_release_build_provenance`, `candidate_sha256`, `artifact_sha256`, `build_mode:release`, `code_mode:aot`, `build_log_sha256`. The referenced build log is independently hashed. Hashes establish reproducibility, **not truthfulness of a supplied build receipt**; independent build/source review remains required.

Installation provenance exact keys: `schema_version:1`, `kind:native_installation_provenance`, `install_id`, `platform`, `application_id`, `application_version`, `application_build`, `candidate_sha256`, `report_sha256`, `raw_document_sha256`, `observed_from_ms`, `observed_through_ms`, `source_evidence_sha256` (1..16 unique independent references). The raw hash is canonical UTF-8 JSON, matching the production recorder export. Report/app/build/candidate and observed interval must agree; the reference list cannot merely reference its own proof, report or manifest. Independent provenance cannot be replaced by `linkage_reviewed:true`.

Supported Apple input is the two JSON objects of an IPS crash report with bug_type309, actual `pid`, `procLaunch`, `captureTime`, `bundleInfo`, incident, supported fatal exception and app-code image UUID. Metadata timestamp is ignored. OS termination namespaces, simulated reports and SIGKILL are refused. Supported Android input is a narrow text tombstone with PID/package, absolute timezone-qualified timestamp, integer process uptime, supported fatal signal and a backtrace containing the app-code BuildId. Integer uptime yields an interval; it is not silently treated as an exact launch time. An engine-only tombstone cannot identify Dart app code and remains unknown.

## Actual author verification

| Check | Result and evidence |
|---|---|
| Pure Dart regression | 36 passed: `dart-minimized-final.log` (15 new +21 preserved legacy). |
| Python clean copied workspace | 39 passed: `python-clean-tool-replay.log` (22 native diagnostics +17 migrated adjudicator tests), default imports, no staging overrides, all 24 copied inputs unchanged. See `clean-tool-replay.json`. |
| Actual Dart → Python schema examples | `fixtures/migration-v3`: generated by the staged recorder, exact old registry/event comparison, available/unavailable starts and full erasure; verified by Python. Internal synthetic IDs/PID only. |
| Consent widget tests | Four authored in `game/mobile/test/study_native_consent_test.dart`; **not run or analyzer-qualified**. |
| Swift/Kotlin and actual channel | Implemented, **not compiled or run** in this lane. |
| Actual release-crash binding | **Unqualified**. Parser fixtures are constructed binary/report bytes, not a compiled release or an observed fatal. |

Prior prototype logs and `fixtures/migration-v2` are retained. The early v2 Dart compile attempt failed nullable promotion; the preserved `dart-restart-failure.log` reproduced the retry gap defect before repair. Old prototype positive parser fixtures used weaker launcher-only identity; final app-code/archive rules supersede that result. `dart-fixtures.log` is the earlier failed compile; `dart-fixtures-final.log` is the minimized successful generator. Do not promote historical fixture-v2 containing removed uptime metadata.

## Promotion and follow-up

Use only `promotion-manifest.json`; check each baseline target hash first. Do not copy the entire staging directory. New root matcher/tool tests are already in `tool/`; they default to integrated modules. Before integration their author override is explicit, never autodetected. Promote `fixtures/migration-v3` to captured `release/study/fixtures/native-linkage-v2`. No real study exports or diagnostics belong in candidate inputs. The existing synthetic collection-v1 fixture stays unchanged; updated tests correctly classify its old boolean crash claim as unknown.

After promotion, run focused consent tests in English/pseudolocale, existing study tests and whole mobile analysis; then full host gates. New dependency work is separate. The old18-scenario current-runtime harness remains unchanged and does not prove these new native fields. Add source-pinned actual iOS/Android checks for default no channel calls, explicit consent, returned PID matching host/Dart PID, app/build/UTC bounds, restart continuity, unavailable failure, exhaustion and full withdrawal. Source/build/run/report identities must remain bound.

Debug simulator runs can qualify context and persistence behavior. They do not qualify release AOT diagnostic binding. A supported real AOT fatal report with independent install/build provenance is still required for positive binding qualification. A controlled fatal probe, if later authorized, is separate from host SIGKILL, app lifecycle, power loss and real observed-session rates. The user currently has no store accounts, physical devices, hosting or human participants; these resource gates remain open. No canonical release acceptance changed.

## Primary-source basis

- [Apple IPS JSON format](https://developer.apple.com/documentation/xcode/interpreting-the-json-format-of-a-crash-report): launch/crash/body metadata and binary images, rather than metadata timestamp.
- [Android native crash diagnostics](https://source.android.com/docs/core/tests/debug/native-crash): PID, signal and backtrace/build identity.
- [Android Process.myPid](https://developer.android.com/reference/android/os/Process#myPid()) and [PackageInfo version code](https://developer.android.com/reference/android/content/pm/PackageInfo#getLongVersionCode()).
- [Apple required-reason API categories](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacyaccessedapitypes/nsprivacyaccessedapitype): existing35F9.1 does not permit exporting raw boot-time readings. This lane removed its unused uptime observation entirely; it did not modify the existing ownership clock or privacy manifest.
