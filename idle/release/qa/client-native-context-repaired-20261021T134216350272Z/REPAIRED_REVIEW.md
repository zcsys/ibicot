# Native context harness/runner — repaired independent review

**Recommendation: the repaired staged source is ready for lead integration, analysis and actual native qualification.** CTX001–003 from the initial independent review are repaired and reproduced. This is not native compile/run acceptance or release-AOT diagnostic qualification.

## Exact final inputs

| Source | SHA-256 |
|---|---|
| Staged harness | `85f859b2ddd84cdfa1c4130277f03e49e0d060c550969576759d194f3d88b4a4` |
| Staged runner | `34239f373943381ecaaa07c071f7e8f3f518f08a32eb17f7f7f1a22ce90637fe` |
| Author runner tests | `fde639aaefdc017503a5b0042300d50b9bca6f75dafddb07abcbc7bd42fd9c6f` |
| Independent probe | `ba98eb7cbf5abe61a3fced0ea92cfba1f713b57327446feee8bab1c0371804a6` |

Lead repair source: `release/native-proof/native-context-harness-staging/repair-20261021T134119.016528Z/after.json`. All four declared pins matched before review; harness/runner/tests in the copied Python workspace match staging. Exact commands, all imported tool pins, before/after stability and raw output hashes are in this directory's `verification.json`. No reviewed input changed during execution.

## Reproduced results

- Original author suite with two added repairs: **31/31 passed** (`author31.log`).
- Different-author rejection/control suite: **14/14 passed** (`review14.log`). This includes the original three failures, retained iOS/Android positive controls and raw schema2/archive/host PID/time/erasure cases.
- The zero-sampling probe was expanded from the original default/context case to both default and withdrawn reopen, testing either retained native context or logical process identity. Valid withdrawn-reopen predecessor metadata passes before the contradictions are added. This expansion remains within the same 14 test methods.
- No Flutter, simulator, device, Swift/Kotlin compiler or native channel command was invoked. No staged/live implementation was edited by this reviewer.

The initial **29 passed author /11 passed +3 failed reviewer** checkpoint and original probe remain intact in `release/qa/client-native-context-20261021T133429576369Z/`. Its `NATIVE_CONTEXT_REVIEW.md` retains findings and the full boundary analysis; this separate report records their closure, not a replacement of the failures.

## Repair assessment

| Finding | Inspected repair | Independent result |
|---|---|---|
| CTX001: fractional top-level checkpoint PID | The checkpoint identity loop now requires exact types and values for every identity. The independently validated host integer PID cannot be matched by `123.0`; nested context remains strict. | Valid integer passes; fractional top-level and nested values reject. |
| CTX002: zero-sample result with collected context | Both zero-sample scenarios reject presence of either context or logical identity, including null. Count checks and active-observation requirements remain unchanged. | Valid default/withdrawn results pass; populated contradictory fields reject in both scenarios. Author cases also cover null presence. |
| CTX003: missing transitive source pin | Runner directly imports and includes the actual diagnostics module in `sources`, so existing copy/hash/drift/evidence loops cover it. The adjudicator imports the same module. | AST/source inspection confirms the new entry. Entire repaired runner and transitive module source are captured here. |

The Dart harness delta changes only consent readiness. Instead of waiting for an unbuilt lazy-list checkbox, it wraps the actual `StudyRecorder.open(store)` and sets a readiness flag after completion. Capacity still uses the actual recorder with the exact original 8-record/32768-byte bounds. No store is mocked. The existing `until` loop yields/pumps; existing consent text is then scrolled into view and hit-tested/tapped. Zero calls before consent, absence of the game directory, one active observation, all raw PID/app/build/time assertions, restart continuity, withdrawal and all 18 scenario names are retained. Exact initial-to-final source diffs are alongside this report.

## Limits retained

The future simulator/emulator execution can qualify production context/persistence behavior. It does not qualify release-AOT app-code identity, supported fatal diagnostic linkage, physical power loss, human consent, real participant metrics or crash-free rates. Observation UTC is not kernel launch time or authenticated time. SIGKILL preparation remains expected interruption, not a passed test or supported fatal report.

Capacity is tested in the same process; exhausted fresh-process no-sampling remains host coverage. Native unavailable-channel injection is not present in the unchanged 18 scenarios. Raw legacy decoder fixtures without a native host PID remain structural only; actual archive calls require the observed host PID. The source counter covers the injected production sampling seam, not an OS-wide channel monitor.

No original acceptance record or scope criterion was changed. Root retains the exclusive Flutter/native lane and must analyze/build/run the integrated source before claiming those outcomes.
