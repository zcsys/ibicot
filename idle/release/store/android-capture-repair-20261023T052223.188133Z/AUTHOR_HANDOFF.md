# Staged Android gallery repair — author handoff

The three staged files are ready for different-author review. No live source has been promoted. The change is limited to test/capture orchestration. Native validation, Dart formatting/analysis and visual confirmation of the repaired Android recording remain pending the lead's clearance and the native verifier's exclusive lane.

## Finding and bounded inference

The first Android gallery `integration-android-20261023T051309.900497Z` fails the unchanged 15–30-second raw-media gate: actual video duration is 30.4743556 seconds; fixture gameplay elapsed is 30.135 seconds. The native assertions and four screenshots otherwise completed. The lead's full decode has only 19 frames, last presentation time 23.9763556. I inspected the actual decoded sample at 7.5298889 seconds: it still shows the initial harbor, whereas the fixture had already performed its real purchase action.

The pinned Flutter SDK `_callback_io.dart` sets `_isSurfaceRendered` and converts the surface once, registering its revert only at teardown. Its Android `FlutterDeviceScreenshot.captureView` invokes `acquireLatestImageViewFrame()` while taking a still. The gallery calls the conversion before its first still and retains it throughout video recording. These sources and the observed video support the image-view freeze diagnosis; a fresh native run must verify the repair. SDK files are untouched and their hashes are in `baseline.json`.

## Exact staged change

- `platform_smoke_test.dart`: Android gallery alone skips surface conversion and requests four ordered raw screenshots from the host. Each request binds candidate/harness/verification/run/platform/scenario identity, exact private directory, exact screen name, sequence, dimensions and actual elapsed time. The app waits for an atomic acknowledgement carrying raw-byte SHA-256. iOS delegates to the same binding screenshot calls. Original production widget/seed, hit-tested gesture helper, pointer routing, one-purchase assertion and real 4/8/14/20/25-second schedule remain unchanged. Android keeps the final screen visible until the host acknowledges recorder termination, then tears down; real endpoint time is reported explicitly.
- `native_recording.py`: the host validates the drive command against the pinned harness and exact evidence directory, then accepts only this run's four ordered requests. `adb exec-out screencap -p` bytes are written unchanged and exclusively, structurally CRC-checked and compared to actual view dimensions. Invalid returned bytes remain as failure evidence. Acknowledgements are written into a fresh private temporary file and atomically linked to a previously absent final name; no acknowledgement is overwritten. The recorder shell reports its launched child PID. Before signalling, the host checks `/proc/PID/stat` start ticks before and after the command-line observation and requires exactly `screenrecord --time-limit 27 <this unique remote MP4>`. It rechecks this identity at stop, uses only `kill -2 <that PID>`, and waits for normal completion. No pidof/pkill/broad kill is used. The raw duration gate stays 15–30 seconds. The capture manifest cross-checks all four receipts against the saved bytes and host recording report. Binding failures produce a failed report before launch.
- `native_integration_driver.dart`: Android gallery uses only those four exact host-captured filenames; the driver rechecks regular-file status and each raw-byte hash before emitting screenshot paths. Failed receipt/hash handling saves a partial result with an explicit error, then rethrows. The existing binding-screenshot collection loop is byte-identical. `crypto` is already a declared mobile dependency; no lock or dependency change is required.

This does not change time speed, game state simulation, callbacks, production code, the frozen candidate, image pixels, SDK source, or the native verification runner. It does not claim that the new native footage already succeeds. It does not relax any duration or store criterion.

## Reproduction and evidence

From `/Users/csys/Desktop/ibicot/idle`, reproduce the focused synthetic orchestration checks without a native command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 release/store/android-capture-repair-20261023T052223.188133Z/test_staged_recording.py
```

The final exact staged recorder passes Python compilation and 36 focused unit tests. The suite mocks every process launch/run, uses temporary synthetic files, and supplies no native/media qualification. Cases cover the complete four-capture flow, exact bytes, cumulative polling, duplicate/history/order/name/time errors, all identity fields, unsafe directories, stale/existing/symlink outputs, PNG CRC/truncation/geometry failures, screencap error/timeout, atomic-ack failure, exact recorder argv and PID/start-tick changes, premature recorder exit, existing video protection, altered/missing receipts, command-binding failure reports, and 14.99/30/30.474-second duration controls. Tests also retain the iOS command-binding no-op.

`python-tests-first.log` and `test_staged_recording.first.py` preserve the initial author test error: the mock helper accidentally overrode unittest.TestCase.run before setUp. It was renamed to `fake_run`; no product assertion was weakened. `python-tests-second.log` records the first 31 passing cases; final hardening/additional cases are in `python-tests-final-sealed.log` (36 pass). Intermediate source is preserved separately.

`preservation-checks.json` confirms all three live baseline files, five SDK/runner pins and all 15 first-gallery failure files remain unchanged. It also checks exact harness bytes outside the gallery function, seed/production widget bytes, hit-test helper, timeline, original assertions, iOS screenshot delegate and old driver loop. No Flutter, Dart SDK, mobile/device or adb command was executed during authoring; only pure Python syntax/tests and read-only source/media inspection were performed.

## Promotion boundary

Use only the three entries in `staged-pins.json`; require their exact live-before hashes before promotion. `android-capture.patch` is the exact three-file unified diff. Do not promote author scripts, tests, historical snapshots or Python caches into runtime paths. Root review and native-lane formatting/analysis come before a separately pinned gallery retry. Any analyzer-driven edit needs new hashes; preserve this handoff. A successful retry still needs actual raw-frame decoding to establish moving production UI, real purchase/transition/season endpoints, no pointer overlay, four matching stills, exact source preservation and the unchanged duration gate. No whole release scope is accepted here.
