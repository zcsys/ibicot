# Android capture acknowledgement repair

This staged, two-file repair is ready for different-author review. No live source is promoted. It changes test/capture synchronization only; all 482 production inputs still match frozen candidate `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`. The existing driver `ec880d16153b1ac577a221a46f81e7c309dd5417fbba8aae4ce68f7acbcfb668` is unchanged.

## Actual failure

The real run `release/native-proof/integration-android-20261023T080508.861496Z` obtained its first unmodified 1080×1920 raw screencap, then failed its app-private hard-link acknowledgement with `Permission denied`. It never obtained the synchronized start marker or a video and correctly reports `passed:false`. This establishes an unsupported hard-link publication operation on that actual target; it does not establish the kernel/security subsystem responsible. All nine files from that failed run remain unchanged. No failed capture is reused as successful media.

## Publication protocol

The host keeps the existing JSON payload filename. It refuses any existing payload or completion path (including dangling symlinks), enables shell noclobber, and writes the payload with `cat > payload`. Only after successful cat completion and close does it execute `mkdir payload.complete`. The creation of that empty directory is the atomic readiness event. No hard link, rename, unchecked move, overwrite or source-image modification occurs.

The harness checks both paths are absent before emitting the request. It waits for a real completion directory using `FileSystemEntity.typeSync(..., followLinks: false)`, then requires the payload to be a real regular file before reading it. Mere JSON-file existence is never considered ready. The existing receipt identity, raw-byte hash, byte-count and recorder-stop assertions remain. This same protocol handles each of the four screenshot receipts and the final recorder-stop receipt. The driver requires no protocol change.

If writing is interrupted or reports failure, the payload remains as evidence and no completion directory is created. If publication fails, the complete payload remains unpublished. Neither state is retried in place or deleted. Two cooperative publishers targeting the same fresh payload compete through noclobber creation; only the successful writer can proceed to publish. Existing payload, directory, FIFO or symlink paths fail closed. The strict command/request/private-directory binding, newly created fixture directory, exact run/verification/candidate/harness identities and app-private access remain the protocol boundary.

The guarantee is atomic readiness and no replacement for this app-private, single-run cooperative protocol. It is not a power-loss durability/fsync promise or protection against an arbitrary malicious process running under the app UID that can mutate the fixture after the checks. The host tests exercise POSIX shell behavior on this host; actual Android shell/filesystem success remains to be observed by the native verifier. No device diagnostic was needed to author this change, and none was run here.

## Checks and preservation

- Thirteen real host `/bin/sh` tests execute the exact shell extracted from the staged recorder in temporary directories. They cover exact-byte completion, repeat refusal, partial existing payloads, directories/FIFOs, live/dangling payload and marker symlinks, partial-open writers, interruption, writer failure, publication failure, concurrent writers, quoted paths and unsafe-name rejection. They execute no adb/Flutter/device command.
- The existing 36 focused mocked recorder orchestration methods pass against this staged recorder. The only inherited test edit replaces the former hard-link expectation with the completion-directory expectation and checks absence of hard links/moves. Identity, PNG integrity, receipt equality, PID/start/argv targeting, failure preservation and 15–30-second duration assertions are retained.
- Python source compilation succeeds without changing source. `preservation-checks.json` records all 16 baseline pins, including the nine failed native files, unchanged live harness/recorder/driver and program/scope metadata. All 482 production inputs match the frozen candidate. The full unified patch regenerates exactly from the before/staged snapshots.

`host-publication-first.log` and `test_ack_publication.first.py` preserve an initial test-only setup error: a quoted private capture directory was also used as the recorder evidence basename, so the existing evidence-name validation correctly rejected setup. The final test uses a distinct valid evidence basename while retaining the quoted private directory for shell-escaping checks. No production or safety validation was weakened.

Run the two focused author checks from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 release/store/android-ack-repair-20261023T081049.643189Z/test_ack_publication.py
PYTHONDONTWRITEBYTECODE=1 python3 release/store/android-ack-repair-20261023T081049.643189Z/test_staged_recording.py
```

## Promotion and remaining qualification

Promote only the two entries of `staged-pins.json` after matching their expected live-before hashes. `ack-publication.patch` is the exact diff. No production code, callback, game speed, action schedule, route readiness predicate, recorder ceiling, PID targeting, video gate, image bytes or SDK file changed. This repair applies only to the Android receipt path; iOS capture behavior remains the already reviewed prior harness behavior.

Scoped Dart analysis and a fresh Android native gallery are pending the exclusive native lane. The fresh row must demonstrate successful acknowledgement publication, genuine continuous UI motion, correct four screens including the settled Season landmark, real purchase/actions, exact receipts and preserved raw files, no painted test pointer, and raw duration within 15–30 seconds. Do not infer success from these host checks. Any analyzer-driven edit or actual failure needs separately retained evidence and new hashes. The later media reviewer must rely on the lead's independent source review for this author's repair, rather than self-approve it. No whole scope, native release, store ingestion or public submission is accepted.

Source writes are stopped; this handoff is sealed.
