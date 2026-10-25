# Independent native observation review

Decision: **return the staged collector for repair before promotion or native execution**. The optional two-file harness/runner delta has no additional finding from static inspection. This review does not establish Flutter compilation, native execution, provider behavior, privacy release acceptance, or completion of M5-03/S39.

Reviewer: `/root/native_verifier`, independently inspecting the prior platform author’s staged implementation. No staged or production files were edited. No Flutter command, simulator/device operation, app launch, provider call, or packet capture was performed. The only live process observation was the author test’s disposable macOS loopback-listening child, created and terminated by that test.

## Reproduction and scope

- All 21 author tests pass, including the actual owned-process `ps`/`lsof` test. All eight staged source hashes and all nine declared live input hashes match the author’s verification record.
- Nine new reviewer probes initially yield four passes and five failed expected-rejection checks, grouped into the two findings below. The original failures and the outside-fixture sentinel hash are preserved; they concern only reviewer-created disposable files.
- Scope remains process-attributed snapshots during an optional synthetic window. It is never proof that no traffic occurred, an audit of all SDK storage, a release/physical-device audit, or participant consent.
- The exact two-file patch preserves unflagged behavior. The flag is guarded to `runtime-study-default`/`runtime-study-enroll`, is recorded by the runner, and inserts the window before normal completion. The default observed game is separately isolated and unprovisioned. The native loop intends 15 seconds and rejects elapsed time above 20 seconds; finalization retains the ordinary positive-count native framework and driver completion requirement.
- Process validation binds approved device, exact installed iOS executable/PID/start/host UID or Android package/PID/start ticks/UID/boot identity. Every sample compares process identity before and after. Android endpoint output is filtered on device by both package UID and PID-owned descriptor inode. Protected-device rejection is reproduced before any candidate input is read.
- Parser tests reject another socket UID/inode and missing namespace tables. Default refusal/unconfigured-service guards are unchanged. The tool explicitly limits its claims to point-in-time sockets, fixed study fixture files, and unauthenticated UTC alignment.

## OBS-001 — storage opens can leave the selected fixture and evade the time bound

Location: staged `runtime_observation.py:197` (`local_storage`), reached from `Host.storage` at line 305.

The code checks each path with `lstat`, then independently opens the final path with `Path.open`. The base directory was checked only during `Host` construction. A replacement between those operations is followed. The reviewer replaces only disposable fixtures at that boundary and proves:

1. A regular allowed file changed to a symlink immediately before `Path.open` causes the returned SHA256 to equal a sentinel outside the selected fixture. See `accepted-outside-fixture-read.json`.
2. Replacing the fixture root with a symlink after the constructor’s validation also returns a successful storage inventory for the outside directory.
3. Replacing the final regular file with a FIFO at the same boundary blocks the collector in `open`, outside the `Host.command` deadline. The reviewer’s one-second subprocess timeout terminates the disposable child; there is no writer that could unblock the FIFO. This is a blocking syscall, not a slow hash or native-window result.

Repair should make directory traversal and the final read use securely anchored descriptors, reject symlinks/special files without first blocking, and collect metadata/hash from the same opened regular file. Retain a bounded read and verify relevant identity/size consistency. Android storage uses a similar path-check-then-`stat`/`sha256sum` sequence; its selected-file guarantees require separate qualification or an explicit unavailable status until a safe reader is available. Merely performing another pre-open `lstat` leaves the same race.

## OBS-002 — finalization does not verify its preserved collector

Location: staged `runtime_observation.py:426` (`finalize`), especially result construction repeating `report['collector_sha256']`.

The finalizer accepts a collection whose `collector.py` is absent, and accepts one whose `collector.py` has different bytes, then emits `finalized-sampled-observation` and repeats the claimed collector hash. Both outcomes are reproduced independently using the otherwise-valid author fixture. That disconnect prevents the preserved source from proving which collector produced the accepted evidence.

Repair should require and hash the exact preserved collector, bind it to the collection record, and ensure the collection/finalization source identity remains stable across the relevant operation. Similarly, the imported completion verifier should be explicitly bound to the archived reviewed verifier source used for the runner; inserting a module search path and merely reporting whichever module was imported is not a source pin. The existing final log/result/harness and native completion checks must remain intact.

## Retest required

Keep the original author and reviewer failures immutable. After repair, reproduce all 21 author tests, rerun these nine independent probes with only fixture provisioning updates required by stronger integrity requirements, and inspect the repaired implementation. Promotion still requires the lead’s integration decision, Flutter analysis in the serialized lane, and a separately authorized source freeze before the five native exports and 58-cell protocol.

No work-item or scope status was changed by this review.
