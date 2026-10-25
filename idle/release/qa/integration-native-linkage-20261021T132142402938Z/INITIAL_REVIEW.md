# Independent native diagnostic linkage review — initial pin

The original 18 promotion inputs match the author manifest `f5018756bbc79401bb46aafd1e177ca27a0bc686aa608bc5405160ae5db000f4`. The isolated promoted workspace adds only explicitly hashed existing test dependencies/fixtures, for 38 inputs, fingerprint `8c2838d79cdcf931c04c7c5b38f0a43157d755e31bb932d5f7efd032bed89587`. Their bytes remained unchanged through review. Original staging and production files were not edited.

## Finding LINK001

The installation-provenance decoder compares `schema_version == 1` without requiring an integer. Python consequently accepts both `true` and `1.0`, producing a positive synthetic native link. The release/build manifests and context decoder correctly require exact integer types. Two independent negatives reproduce the mismatch. A related Dart erased-document early return accepts schema `1.0`/`2.0`, while the Python decoder rejects those tombstones. This is a strict-contract and decoder-consistency defect, not evidence of incorrect attribution of a real crash. Initial failing output and exact sources remain immutable here.

## Review and independent probes

The author suite independently replays 36 pure Dart cases and 52 Python cases (22 native diagnostics, 17 adjudicator, 13 existing report). Ten new Python probes yield eight passes and the two provenance-version failures; its runner also repeats the imported 22 author cases. Seven new Dart probes yield six passes and the fractional-tombstone failure. Do not add repeated executions to unique test counts.

Independent cases check atomic unavailable-start/gap publication in one delayed CAS; byte-identical old registry/events during migration; idempotent process begin; failed restart identity and a retry gap attributed to the previous committed process; immediate withdrawal while capture is queued; full schema2 PID/context erasure even with minimal-retention requested; truncated native-unavailable gap rejection; context version/extra-key/PID/time strictness; actual next-process and post-crash activity boundaries; duplicate packaged binary rows; wrong app-code role; missing native identity; unsupported signal and duplicate JSON. Positive controls use constructed synthetic reports and binary bytes.

The source review confirms that the visible new disclosure is included in the consent information hash. Empty provisioning performs no recorder/native call; legacy information hashes restore without PID sampling; exhausted or pending-withdrawal states avoid sampling. New context is passed into the same durable process-start transition. The actual Flutter consent tests are authored but were not executed as part of this initial review. Swift/Kotlin channel registration is source-only here and does not itself sample a PID. The adapter checks returned platform/PID, enforces a two-second timeout and maps exceptions to explicit unavailable states.

The matcher requires the report, raw document, installation provenance and release manifest identities to agree. It hashes actual archive/app-code bytes, extracts Mach-O UUID or ELF build-ID, excludes launcher/engine-only identity, checks one eligible process and session interval, and rejects gaps/terminal ambiguity. Android integer uptime creates a launch interval rather than a fabricated exact instant. Apple metadata timestamp is not substituted for process launch/crash time. A missing report is never inferred to be a crash. Legacy boolean reviews remain unknown.

## Limits and required next evidence

All observations here are host tests with synthetic fixtures. Hashes cannot establish truthful operator-supplied build/installation records or lawful consent. Actual iOS/Android channel values, native lifecycle/restart behavior and release AOT fatal-report linkage are not qualified. A debug simulator may qualify the observation channel but cannot establish release AOT crash binding. No participants, crash-free rate, D30, physical hardware, store/provider deployment or release acceptance follows from this review. Aggregate output removes internal context; raw study export remains restricted, expressly consented material.

The initial failed `dart run test:test` invocation lacked a package working directory; a second probe creation used the wrong relative output directory. Both are reviewer harness errors, not product failures. Corrected invocations compiled and produced the results above. The later strict-type overlay must be pinned and run against unchanged negative assertions before LINK001 closure.
