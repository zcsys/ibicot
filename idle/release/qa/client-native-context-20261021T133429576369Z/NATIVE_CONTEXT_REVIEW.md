# Native context harness/runner: independent client review

**Initial decision: three narrow runner repairs required before promotion/native execution.** The actual native adapter path is present and the observed context is meaningfully tested, but the frozen evidence validator accepts two contradictory/mistyped documents and omits a transitive parser source pin. This review did not invoke Flutter, native build tools, simulators, devices, the channel, or a fatal probe. No staged/live implementation was edited.

## Frozen inputs and execution

| Input | SHA-256 |
|---|---|
| Staged `current_runtime_test.dart` | `eb2ce92d6c1c8018791d57a2dd653d512507eb9c9ff6e8827000a29c469ee9ed` |
| Staged `verify_current_runtime.py` | `2e6d09079078b9e7c53460024eec99db5545b2dc235cff5c0f58a68c685e0538` |
| Staged author tests | `c0fdaa8d355766fa92c61836c75cd463ed67f6957e3258c4daf0b860dbc1064b` |
| Independent `game/qa/review_native_context_runtime.py` | `7a5130d661e1db18d043e457cd0dc877e6bd0ea3c4c443f693f29c6b05d0539a` |
| Prospective decoder `study_adjudicate.py` | `ccf31107cced115bb7a417407a2b7cfa1498845ce10899b14a1f3ca533a406e6` |
| Prospective diagnostics `study_native_diagnostics.py` | `325afe73985b414a23ab3858ad4abc656351258bb3c19e49bd6c665761031430` |

The source tree is `release/native-proof/native-context-harness-staging/`; execution used its `python-workspace/`. The runner/tests there are byte-identical to the reviewed staged copies. `verification.json` retains exact commands, source and log hashes, and confirms no source drift. `additional-source-review.json` pins the transitive tools and inspected native/consent source and records the unchanged 18-scenario allowlist. Copies are under this report's `source/` directory.

- Original author suite: **29/29 passed** (`author29.log`).
- New different-author probes: **11/14 passed, three failures** (`review14.log`). Negative cases retain valid positive controls; failures are not replaced with expected-failure assertions.
- Python fixtures are explicitly synthetic. Mocked `read_fixture` tests exercise the real archive/decoder boundary without touching a native device. Legacy author decoder tests lacking a host PID remain structural tests; they do not qualify current native observations.

## Findings

| ID | Severity | Actual accepted failure | Required narrow repair |
|---|---|---|---|
| CTX001 | P2 | `validate_checkpoint` accepts top-level `native_process_id: 123.0` against independently supplied integer `123`. Nested `native_process_observation.native_pid` is correctly strict; the top-level identity loop uses Python equality without type equality. A valid integer checkpoint passes first. | Require an exact bounded integer checkpoint PID and typed identity comparison. Preserve nested strict validation. |
| CTX002 | P2 | `payload_errors` accepts `runtime-study-default` with `native_study_samples: 0` and a populated available `native_study_process_context`. The otherwise identical result without context passes. This contradictory retained observation must not be accepted as no-sampling evidence. | For zero-sample/default/withdrawn-reopen results, reject retained native context (and associated native logical identity if reported). Keep the original sample count strict check. |
| CTX003 | P2 | `run()` archives and drift-checks the adjudicator/report modules but not their new `study_native_diagnostics.py` dependency. The AST probe confirms the missing entry in the actual `sources` dict. The lead disclosed this omission before this independent reproduction. | Capture the actual imported diagnostics module, hash it, include it in source drift detection and the evidence inventory. |

CTX001/002 concern fail-closed evidence validation. The pinned Dart harness emits integer PID values and does not emit an available observation on the default path. These probes are **not** evidence that the production UI samples before consent or that an invalid report has passed on a native device.

## What the source and positive controls establish

- The staged wrapper increments its call count and delegates to actual `NativeStudyProcessContext.sample()`; no mock channel response or synthetic PID replaces it. Swift/Kotlin register handlers without sampling. The handlers read PID, application/version/build and current UTC only when `observe` is invoked. The Dart adapter independently checks platform and `dart:io` PID and refuses unsupported/unavailable/invalid responses.
- Fresh enrollment asserts no game directory and zero calls while the actual consent UI is visible. Default empty provision asserts no recorder opening, no study support directory and zero calls. Withdrawn reopen asserts zero calls, no attached study session, erased registry/records/eligibility and a durable marker. Each active study scenario expects exactly one observation.
- The active harness reads the actual persisted schema2 document, finds this logical process's `app_start`, and checks native PID, platform, `dev.tideglass.game`, version `0.1.0`, build `1`, and observation/event timing within five seconds. Restart checks the retained install/first launch/first record hash, new logical process, one added start, old native PID retained and new PID recorded. Host predecessor checks require the same candidate/harness/run identity and an observed process stop or kill.
- The runner's actual `archive_fixture` requires a typed host PID before any file read. It captures only the three existing allowlisted study paths with fixed bounds. The full raw decoder validates chain/schema/eligibility, then the archive compares the **latest** native start to the host PID. A two-start positive control passes only for the latest PID; matching the first PID is rejected.
- New probes passed both iOS/Android synthetic valid schema2 archives; rejected contextless schema1, wrong native PID, fractional/boolean schema/context values, removed `uptime`, out-of-range timestamp and unavailable current context. The real decoder accepted exactly ±5000ms and rejected ±5001ms after valid hash-chain resealing. Default absence and schema2 full erasure with marker passed; absent withdrawal marker failed.
- The original 18 allowed scenarios are unchanged. There is no expansion to arbitrary test targets or ordinary player saves. Existing identity/protected simulator/fixture checks remain in the runner; the author's 29-test suite retains their regression coverage.

## Boundaries and outstanding execution

This is context/persistence instrumentation qualification preparation. `flutter drive` here is a simulator/emulator debug execution path; matching PID/app/build does not establish an AOT code identity. The harness explicitly says observations do not prove release-AOT fatal matching or a crash-free rate. Host SIGKILL is intentional interruption, not a supported fatal diagnostic and not a passed preparation test. Release-AOT app-code bytes, actual fatal reports and independent installation/build provenance remain separate requirements from the frozen platform handoff.

The capacity scenario proves bounded exhaustion in its current process; it does **not** reopen an exhausted recorder in a fresh native process. Host consent tests cover that no-sampling branch separately. No existing native scenario injects a channel-unavailable response; parser/host failure coverage is not native unavailable-channel execution. Counter assertions cover the supplied sampling seam; they are not an external OS-wide channel monitor. Device UTC is not authenticated and observation time is not kernel launch time.

Staged Dart analysis, Swift/Kotlin compilation, actual channel invocation, source-bound iOS/Android execution, and any physical/device/release diagnostic claims remain pending at this checkpoint. No original scope criterion or acceptance status was changed. The implementation author/lead may repair the three runner findings; this review will retain the initial source/logs and record a separate replay before recommending promotion.
