# Native observation repair — staged implementation handoff

Author: `/root/observation_repair`, 23 October 2026. Scope: repair the two independent findings in `release/qa/native-observation-20261023T025313.166881Z/REVIEW.md`. **Independent retest and lead integration remain required.** No live source, Flutter, native device, build candidate, provider, account, work-item acceptance, or scope status was changed.

## Result and evidence

The final author run passes **41 methods: all 21 original author methods plus 20 repair regression methods**, including their adversarial subcases. The original methods received only fixture provisioning changes: canonical temporary paths and the exact candidate/source/archive records now required by finalization. Their assertions remain intact. The process observation test uses only its own disposable loopback-listening macOS child; storage tests use disposable files and child Python readers. None observes Tideglass.

`test-execution.json` records the exact commands, exits, timestamps and output hashes. `final-test-source-before.json` and `final-test-source-after.json` are identical. `inputs-before.json` and `inputs-after.json` preserve hashes of the untouched original staged packet, independent review, and live completion verifier. `baseline-live-checks.json` confirms all three relevant live baselines still match their copies at handoff preparation. `repair.patch` shows the changes from the original staged collector and test fixtures.

The preserved independent nine-probe suite was first rerun with fixture provisioning adjustments only. It reports **8 passes, 1 failure**, retained under `reviewer-probe-reproduction/reproduction.log`. That failing symlink probe patches `Path.open`; the repaired storage implementation never calls that API, so its replacement never executes. Its retained sentinel record explicitly shows `outside_bytes_read: false`. The FIFO probe also misses its original injection boundary in this first rerun and is not counted as new FIFO qualification.

A **separate author adaptation** retargets both race injections to the actual `os.open` boundary and asserts that injection occurred. It also provisions the root identity and real timed worker required by the stronger Host contract. All **9 author-retargeted probes pass**. `boundary-adaptation.patch` documents every change. This is an author reproduction of independent findings, **not a new independent acceptance**. The original review source and failures remain unchanged.

## OBS-001 repair

| Mechanism | Implemented behavior |
|---|---|
| Root and component traversal | Open `/` and every directory component with retained descriptors, `O_DIRECTORY`, `O_NOFOLLOW`, `O_NONBLOCK`, and `O_CLOEXEC`. Compare the pre-open entry with the opened descriptor and verify the full retained chain before returning. |
| Selected file read | Only the seven fixed paths remain eligible. Open relative to the anchored parent with no-follow/nonblocking flags; reject non-regular files, hard links, over-2-MiB files, changed identity, changed size/mtime/ctime/UID/link count, and replacement of the named file. |
| Metadata and hash | SHA256, byte count, inode, device, UID and mtime come from the same opened file descriptor. No file content is included in observation output. |
| Time bound | The production iOS per-sample storage traversal/hash runs in a dedicated Python subprocess through the existing `Host.command` timeout of at most two seconds and the remaining collector command budget. The reader also checks a two-second deadline between bounded reads. A real stalled disposable worker is killed by the timeout test. |
| Constructor-to-worker identity | The Host stores the anchored root's device/inode/type. The worker must re-open that exact identity and returns it with the exact collector hash. A root replacement becomes unavailable storage. |
| Android | `Host.storage` immediately raises the explicit unavailable reason: no descriptor-anchored native reader is qualified. It performs **no** Android storage shell command. Socket sampling can still be retained; finalization reports partial observation when no paired available storage sample exists. |

Regression cases cover leaf replacement with symlink/FIFO/regular file before open, component replacement, root/component/leaf replacement after open, same-inode mutation, hard links, actual worker timeout, actual worker success, root replacement before the actual worker, missing root anchor, and Android no-command behavior. Evidence/archive reads also reject symlinks, FIFOs and non-regular or changing files. Only the actively growing native log permits same-inode append; its exact observed prefix is still pinned and compared to the final completed log.

This is a bounded selected-file observation, not an atomic filesystem snapshot. It detects lasting changes at checked boundaries; privileged mutation-and-restore, filesystem adversaries, and all other SDK/private storage are outside its claims. Host construction and source/evidence validation use ordinary local filesystem operations; the hard subprocess timeout specifically bounds the per-sample storage worker. Android storage remains unqualified until a separate native reader is implemented and reviewed.

## OBS-002 repair

| Binding | Requirement |
|---|---|
| Running collector | Capture the source bytes once at module load. Before and after collect/finalize, require the file to match those bytes. Archive exactly those bytes as `collector.py`; finalization requires that archive to exist and match the collecting/finalizing revision. |
| Candidate | Verify the manifest fingerprint and frozen source map. Require exact candidate entries for `tool/verify_native.py`, `tool/verify_current_runtime.py`, and `game/mobile/integration_test/current_runtime_test.dart`. |
| Runner archives | Require `verify_native.py`, `runner.py`, and `harness.dart` in native evidence to equal the candidate sources. Finalization additionally requires the native runner's `source_pins` and `evidence_sha256` entries to match, and its candidate path to match the collection. |
| Preserved observation sources | Archive the full completion verifier, native runner, candidate manifest and collector. Bind all hashes in `source_binding`. Revalidate archives, candidate, collector and native evidence at finalization before publishing a result. |
| Completion function | Parse the pinned full verifier source and compile the exact undecorated `native_log_errors` function AST with its required `re` module. No `sys.path` modification, arbitrary-root import, `sys.modules` verifier substitution, or import of unrelated build/recording code occurs. Full verifier SHA256 is reported. |
| Final decision stability | Re-read observation, final runner report, result and log after the decision, recheck all source bindings, then write a fresh finalization file. Existing output cannot be overwritten. |

All earlier requirements remain: exact OPEN/CLOSE context, matching native PID and process identity, the normal positive-count framework and driver completions, no negative/late native errors, actual observed interval containment, stable candidate source assertions, and the exact opted-in observation flag. Synthetic missing/changed collector/verifier/runner/manifest archives, changed runner pins, changed candidate verifier, changing collector revision, mid-finalization replacement, and a forged import/cache cannot finalize.

These are local consistency records, not external authentication or proof against a privileged actor rewriting all evidence. Full source hashes identify the reviewed implementation; the AST extraction deliberately executes only its strict completion function, not the runner module's CLI.

## Integration prerequisites and execution

1. Different-author reviewer replays the 41 methods and the nine boundary-adapted probes, inspects the code and original failures, and writes a separate decision.
2. Lead verifies unchanged baseline pins before promoting the unchanged optional two-file hook from `source/` and the repaired collector. The original `observation-hook.patch` remains byte-identical; this repair does not expand the Dart or runner delta.
3. Run scoped Flutter analysis in the serialized lane, then freeze the combined current candidate. The frozen candidate **must contain this exact harness/runner/completion verifier revision**; a historical candidate whose test tooling differs is deliberately refused.
4. Use the original staged handoff's five-export/58-cell protocol and approved devices. Start this collector against the matching current runtime evidence directory with `collect`; use `finalize` only after ordinary native completion. For a staged path, the executable is `release/native-privacy/runtime-observation-repaired/runtime_observation.py`.
5. Preserve Android unavailable storage and any inaccessible sockets as partial evidence. No whole-app traffic absence, startup coverage, physical-device, provider, privacy release approval, store approval, or M5-03/S39 acceptance follows from this repair.

The user has no external release resources. This handoff creates no account, submits nothing, and makes no external release claim.
