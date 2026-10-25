# Independent current-runtime verifier review

Reviewed 2026-10-21 by the client engineer, a different author from the runtime harness/runner author and root repair author. Scope: M1-03 / M1-04 / M5-01, S13 / S14 / S30. No acceptance state was edited.

## Result

Two concrete verifier findings were reproduced on the frozen initial runner and repaired by the lead. The repaired runner passes all **18 independent Python probes**, including unchanged negative expectations and positive controls, and all **28 original author tests**. The staged Dart harness has not been analyzed, compiled or run by this reviewer. Native execution remains pending; this result does not qualify the current app or supplant frozen native candidate 152.

| Finding | Initial reproduced behavior | Root repair and replay |
|---|---|---|
| RUNTIME-QA-01: buffered native failures could qualify expected interruption | With a valid marker, exact clean pre-kill prefix and observed SIGKILL ledger, a later `E/flutter` unhandled exception, framework exception, or `[E]` teardown marker returned no verification errors. The positive-control driver lost-connection tail was also accepted. | Reject native/build/framework errors across the entire final log, while preserving ordinary driver disconnect cleanup. All three error forms now reject; the cleanup positive control passes. |
| RUNTIME-QA-02: Android fixture copy followed links | The Android reader checked the lexical fixture directory then called `run-as head`. A final-file symlink and a fixture-directory symlink both returned synthetic bytes outside the selected fixture. The same reader accepted the regular-file control; iOS already rejected its symlink control. | Probe every component below the OS-owned app directory for symlink/existence/type/readability and directory traversal before reading. Final, parent and top-fixture links reject. Dangling optional links, FIFO, directory-as-file, unreadable/untraversable parent and oversized file reject; a regular file and genuinely absent optional file still work. |

These were source/host verification defects, not observed defects on a device. The independent Android adapter in the probes implements the inspected `test` and `head` semantics against temporary synthetic local files. It does not run adb, a shell or any device command. Files named “outside” contain synthetic sentinel bytes only.

## Evidence and exact pins

| Source | Initial SHA-256 | Repaired SHA-256 |
|---|---|---|
| `tool/verify_current_runtime.py` | `cf48f89f8c71242b078ba0abda9fe454c3a95a843688091f4ae01e819e934da4` | `f63c8bb1f97e5e486fceb9b5831e416efae0d0f4bc73fe248079ca5e3a7cc834` |
| `tool/test_current_runtime_verification.py` | `bd98aed5dabc8d4c900356efd2efc6756f6deda41aad270449730b64165a5b0a` | Unchanged |
| Staged `current_runtime_test.dart` | `99d961e87b100ade13dc3ddda2be059a28b3e75fa979bc5b5a9ef0df598cd50f` | Unchanged during this review |

- `source/` and `source-before.json`: original inspected runner, harness, protocol, schema and helper bytes.
- `author-python-28.log` / `author-run.json`: original 28 tests pass, source hashes retained.
- `independent-initial.log` / `.json`: initial 15 independent test methods: 12 pass, 3 fail; five failing assertions because the log-tail method includes three independent negative forms. The failed probe source is preserved as `review_current_runtime_boundaries.py` in this evidence directory.
- `repaired/independent-repaired.log`: 18 independent methods pass after root repair and three additional missing/unsafe-path methods. Existing rejection expectations remain intact; the command stub gained support only for the newly implemented `-r`/`-x` probes.
- `repaired/author-28-repaired.log`: original 28 tests pass unchanged.
- `repaired/verification.json` and source copies: exact repaired source, probe and raw-log hashes.
- Live reusable probe: `game/qa/review_current_runtime_boundaries.py`.

The independent probe setup blocks `subprocess.run`, `subprocess.Popen`, `os.kill` and `os.killpg`, preventing accidental native actions. Only the outer Python test launcher runs a host subprocess. Tests against the initial implementation use its archived module path; repair tests use the current exact pin.

## Inspected boundaries that remain sound in these probes

Protected-tablet rejection occurs before any external call, including lower-case ID input. Invalid PIDs fail before command construction. iOS identity requires the selected simulator app container/executable; Android requires both its selected emulator PID list and exact main-process cmdline. Recovery requires the matching candidate, harness, selected device/label/run, predecessor scenario and checkpoint plus a different PID; altered generation bytes and changed predecessor identities reject.

The native study archive is bounded to three allowlisted files with observed presence, lengths and hashes. Its raw-chain and eligibility decoder rejects altered data, foreign candidate configuration and non-synthetic study metadata. Default absence is distinct from withdrawal: full erasure requires a null registry, empty records, withdrawn status, absent eligibility and present stop marker. An empty marker intentionally remains a valid stop, matching the production store's interrupted-write rule. None of these checks adjudicates a real participant or crash.

The Dart harness uses unique synthetic support/temporary subtrees, fixed scenario allowlists, explicit no-service/no-commerce defines, a no-op notification gateway and a preflight for shared soundtrack-cache side effects. Exact transition/save/study/cache assertions were read. That source inspection is not Dart compile evidence. The protocol's native process kill is correctly labelled an observed interruption, not proof of a fatal native crash or power loss.

## Remaining work and bounded recommendation

The repaired Python verifier is suitable to proceed to the lead's Dart analysis/compilation and isolated native qualification. Refresh the preparation's author-verification source pin from the initial runner before using it as current evidence. Native Android command availability/permissions, actual iOS PID/container matching, callback/FFI/flock behavior, screenshots, study restarts and file copies must still be tested on the declared dedicated devices. Component probes and pre-read checks are not a hostile concurrent-writer/TOCTOU security guarantee.

Production opt-in crash linkage, physical hardware, actual receiving-app reads, participant recruitment/consent, human-study metrics and original v1 acceptance remain separate obligations. No Flutter, emulator, simulator, native-process or device command was executed in this review lane.
