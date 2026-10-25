# Proposed consented native process linkage

Status: **design proposal only, not implemented or accepted**. No runtime file was changed. Implementation must wait for the lead's art/Flutter window and an agreed interface plus independent review. The frozen harness/runner handoff precedes this document.

## Concrete local gap

`StudyRecorder` currently generates a random logical `process_id` for each enrolled start/restart and persists it in the bounded hash chain. Shipped `main.dart`, `StudyGate`, and native entrypoints do not persist a corresponding OS PID or native process observation. The Python adjudicator can accept a supplied `linkage_reviewed:true` assertion plus logical process ID, but the shipped export alone cannot establish the claimed native diagnostic link. A synthetic harness checkpoint supplies that map only inside qualification fixtures. This is local implementation work, separate from absent physical devices, accounts and real study sessions.

## Smallest production addition

Add one narrow, consent-only `StudyNativeProcessContext` provider, invoked by StudyGate immediately before durable enrollment/app_start and before allowing the child to boot. It returns a bounded typed object:

| Field | Origin and meaning |
|---|---|
| `version` |1, fixed parser version |
| `native_pid` | Actual app OS PID; positive bounded integer |
| `platform` | `ios` or `android`; unsupported platforms remain explicitly unavailable |
| `application_id` | Actual native bundle/package ID |
| `application_version`, `application_build` | Actual packaged metadata, bounded strings |
| `observed_start_utc_ms` | Timestamp of this consented process observation; explicitly **not** a claim of kernel process creation time |
| `observed_elapsed_us` | Paired monotonic observation to detect contradictions within this process |
| `source` | Fixed `native_process_observation_v1` |

Existing `StudyConfig` already carries candidate/economy/content/config identity. Commit the context atomically inside that logical process's `app_start` record, binding OS identity and exact study configuration in the same hash chain. No full-device IDs, device logs, advertising identifiers, keychain identity, network upload, crash-handler interception or native fatal manufacture are needed. Do not reuse the Android ownership-clock method: it opens/creates a keystore key and serves a different purpose.

Use a dedicated method on a small native study channel for PID/package/build and the paired local timing observation. The exact platform implementation must be reviewed against supported public APIs before coding; the public interface is deliberately independent of a particular process-start API. A native report's actual process-launch interval supplies the independent bound described below. Where the platform does not provide enough evidence for that bound, the record remains unlinked rather than guessing.

Default/declined/withdrawn study paths must never invoke the provider or write linkage. Failure to sample does not block the game: it records an explicit bounded unavailable observation/gap and leaves crash linkage unqualified. Capacity retains the existing record/byte limits; atomic app_start/link failure must not open an apparently active collection session. Consent text must mention process identity and optional diagnostic association. Export includes only consented context in the existing bounded bundle. Withdrawal erases context with the registry/events, and preserves only the existing nonidentifying stop marker. A user-shared diagnostic remains outside the app's deletion control and must be identified as such in the study process.

Logical inactivity sessions can share the same actual OS process. Sample/bind context once per enrolled process start, not on each inactivity session. Keep the same process link across its sessions; diagnostic matching first resolves exactly one process and then the unique session interval containing the native event. Ambiguous session intervals remain unqualified.

Use a reviewed raw schema2 codec. Legacy schema1 records remain readable and unlinked. Migration may update the envelope version while preserving every existing registry/event byte and hash; only new process starts carry native context. Never backfill guessed OS identity into prior records. Both Dart validation and Python decoding must accept the explicit legacy/new forms without silently treating legacy starts as qualified.

## Conservative independent diagnostic matching

Apple IPS crash reports have metadata followed by a separate report object. Require the appropriate crash report type, then use the report's actual `pid`, `procLaunch`, `captureTime`, bundle/build and exception/termination information; the metadata timestamp is not the process interval. Reports marked simulated are not native crashes. [Apple's format documentation](https://developer.apple.com/documentation/xcode/interpreting-the-json-format-of-a-crash-report)

Android native diagnostics expose PID/TID, process name, signal/abort information and binary/backtrace evidence. An arbitrary log line or recoverable Flutter exception cannot substitute for that diagnostic. [Android native crash documentation](https://source.android.com/docs/core/tests/debug/native-crash)

Add a separate offline evidence parser/matcher with bounded inputs, keeping native diagnostics independently supplied and hashed. It must:

1. Require the consented study export and its existing chain/registry/eligibility verification. Require an independent operator provenance record connecting the supplied diagnostic to that enrolled app installation; filenames alone are insufficient.
2. Parse the report using a recognized, versioned format. Retain exact report bytes/hash and normalized required fields, without pulling broad device logs into the application.
3. Match platform, app ID, packaged version/build, OS PID, and candidate artifact identity. Maintain an external release manifest mapping exact candidate/binary hashes and native UUID/build IDs where the report provides them. Identical marketing/build strings alone cannot disambiguate two candidates.
4. Require the report's process-launch bound to precede the consented native observation, and the native event to fall after that observation and within the independently reviewed process/observation interval. Reject clock-discontinuity/unknown-clock windows and conflicting process or lifecycle intervals. A recorded observation is not an invented process-launch timestamp. If an Android report omits sufficient launch/interval evidence, require separately hashed same-process launch evidence or return `unlinked`; do not match by PID alone.
5. Require exactly one matching logical process. Reject reused PIDs, duplicate incident/report hashes, conflicting candidate/build evidence, multiple eligible mappings, incomplete fields and reports outside the consented interval. A manually supplied `linkage_reviewed:true` must not bypass these checks.
6. Classify the diagnostic itself before assigning a crash. Host SIGKILL/force-stop, lifecycle callbacks, low-memory/OS-requested termination, simulated reports and recoverable Flutter errors cannot be labeled native fatal crashes merely because a process disappeared. Unknown classifications remain unqualified for a crash numerator.

The matcher produces either one supported link with source hashes/reasons, or a specific rejection/unlinked reason. It does not invent a clean terminal for sessions without a diagnostic. Missing diagnostics cannot by themselves establish crash-free coverage.

## Implementation and independent review sequence

1. Lead agrees interface, schema migration and conservative classification rules. Keep current runtime/art source frozen until that boundary.
2. Collector owner implements typed optional context, atomic new-start persistence, consent copy, export and withdrawal; platform owner adds narrow native adapters with no default-path side effects; Python owner adds schema2 decoder/matcher and candidate binary identity inputs. Separate ownership avoids concurrent shared edits.
3. Pure tests cover legacy preservation, unavailable sampling, bounded growth, default absence, consent/withdrawal races, PID reuse, contradictory clocks, duplicate reports, wrong app/build/candidate, unsupported diagnostics, and no-diagnostic uncertainty. Synthetic parser fixtures are conspicuously synthetic and cannot satisfy field evidence.
4. Independent QA replays code and negative fixtures before integration. New native candidate verifies actual provider PID/package/build values against host observations and tests native restart/withdrawal. A deliberately killed fixture still qualifies only interruption behavior.
5. After implementation and independent review, a separately authorized controlled simulator fatal probe may qualify actual OS diagnostic parsing and linkage. Record the deliberately induced fault, exact app/process/build and raw OS report; it is separate from SIGKILL recovery and cannot count toward real observed-session crash rates. Later independently supplied genuine diagnostics can test linkage under the agreed protocol. The original requirement for10,000 observed sessions, real cohort retention/coverage and physical-device release gates remains unchanged. Neither this proposal nor synthetic native tests supply those observations.
