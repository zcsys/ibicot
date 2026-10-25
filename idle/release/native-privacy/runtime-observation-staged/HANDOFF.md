# Staged process observation — preparation only

No Flutter, native build, simulator boot, device operation, installation, provider call or production edit was performed during this preparation. The existing live harness/runner remain unchanged. A different reviewer and the lead must approve the staged delta before promotion. The protected tablet `F103390E-7B7C-4F0B-9404-5E029C7131FF` is refused before external commands.

## Implemented files

- `runtime_observation.py`: separate read-only collector/finalizer. It runs alongside an already-authorized native runner; it never starts or stops Flutter or the app. `collector.py` and the exact opening log prefix are archived with observations.
- `source/game/mobile/integration_test/current_runtime_test.dart`: optional `TIDEGLASS_PRIVACY_OBSERVATION=true` hook for **only** `runtime-study-default` and `runtime-study-enroll`. Existing unflagged behavior is unchanged. The hook prints atomic OPEN/CLOSE checkpoint JSON and pumps for15s, with a20s qualification ceiling. The normal native framework/driver must still finish successfully.
- `source/tool/verify_current_runtime.py`: narrowly adds `--observe-privacy`, a two-scenario guard, the exact Dart define and an archived boolean. It neither changes normal pass conditions nor treats a waiting window as success.
- `baseline/` and `observation-hook.patch`: exact live baseline and proposed two-file delta. No gameplay or production source changes.
- `test_runtime_observation.py`:21 author methods, including real `ps`/`lsof` of a disposable child created by the test with one local loopback listener. This is sampler qualification, **not an observation of Tideglass**. Initial failed string-format assertion is preserved in `author-tests.log`; corrected run `author-tests-r3.log` passes21/21. The changed assertion only accommodates Dart formatter line wrapping.

## Exact evidence and scope

The native checkpoint binds verification ID, candidate fingerprint, harness hash, scenario/run/device label, actual PID, platform, isolated fixture path, default/synthetic-consented mode, unique window ID, maximum duration, process-local elapsed microseconds and UTC milliseconds. Final driver data contains the exact OPEN/CLOSE pair.

Every attributed sample brackets socket/storage commands with exact process identity checks. iOS binds selected simulator app container, Runner executable, PID, host UID and `ps` process start (one-second resolution). Android binds `run-as dev.tideglass.game` UID, exact cmdline, PID, kernel start ticks and boot ID. A changed identity rejects the sample. No global process/network listing, packet capture, root escalation, system logs, clipboard, or arbitrary user PID is requested.

On iOS, `lsof -a -p <PID> -i` samples only that process's Internet sockets. On Android, the device-side shell reads only the selected PID's FD links and filters its network namespace tables by **both** package UID and the selected PID's socket inodes before emitting any endpoint rows to the host. Namespace tables can be inaccessible on Android; that is `unavailable`, never an empty/traffic-free result. The exact commands, returns, output hashes and bounded selected-process output are retained.

Storage covers seven fixed paths under the exact synthetic `native-current-verification/<label>-<run>/study` directory: the three study files and two possible guest/save generations for each fixture layout. It exports presence, size, UID, inode, mtime and SHA256, not file contents. Symlinks, special files and files over2MiB are rejected. The ordinary app save and other SDK storage are not enumerated. Existing runtime proof separately preserves the explicitly synthetic raw study records.

The flagged default case first retains the original no-recorder/no-native-sample/no-support-directory assertions, then opens production Bootstrap in a **separate isolated game directory** with no study provision. The enrolled case uses the existing synthetic consent UI and production app. Audio remains disabled and reminders retain their no-op gateway; these differences are explicit. Observation begins **after** these assertions/bootstrap, so early SDK startup, earlier connections and future activity are not covered.

The collector attempts at most three snapshots with bounded per-command deadlines. It requires unchanged identities and a conservative host monotonic budget; finalization additionally requires each sample's host UTC interval to be fully contained within the native OPEN/CLOSE UTC interval, without tolerance. Host/native clock mismatch leaves qualification failed; clocks are not authenticated. No claim is made that independent native/host monotonic clocks share an epoch.

Collection returns `collected-pending-native-completion`, never passed. Finalization requires the existing strict native completion verifier (positive test count, driver success, no late/native errors), successful matching runner result, exact device/PID/candidate/harness, source integrity, archived flag, hashed final log/result/harness and unchanged opening prefix. Missing CLOSE, hold interruption or failed normal test cannot finalize. A completed proof with no paired available socket/storage sample is explicitly `finalized-partial-observation`. Even a complete result sets `traffic_absence_claim:false` and `release_acceptance:false`.

## Later execution recipe

Only after independent review, promotion, Flutter analysis and the lead's source-freeze signal:

1. Freeze once with `python3 tool/build_native.py --snapshot-only`; preserve the printed candidate path/fingerprint. Run `python3 tool/build_native.py ios android macos --candidate <candidate> --host-checks`, then `python3 tool/build_native.py ios android --candidate <candidate> --mode release`. Host checks and production fixes take precedence over exports. Never modify the candidate's immutable source.
2. Run the existing22 baseline cells from `release/native-proof/next-candidate-protocol.md` and all18 current-runtime cases on iPhone and Android, preserving predecessor run IDs and reports. Expected SIGKILL preparations remain `expected-interrupted`, not passed tests. Current approved test targets are iPhone `F05BE4B0-52C1-4CA1-B721-BD64AE559E3F`, iPad `089884DC-AD2A-4D69-8C60-C50271AC21BF`, and (after live rediscovery) Android `emulator-5556`.
3. The default/enroll cells may include `--observe-privacy`; the precise flag and changed harness hash must be archived. Example after promotion:

   ```sh
   python3 tool/verify_current_runtime.py <candidate> --device F05BE4B0-52C1-4CA1-B721-BD64AE559E3F --label ios-phone --scenario runtime-study-default --run-id final-default-unique --observe-privacy
   ```

4. While that one Flutter runner is building/running, start this independent read-only observer against its printed evidence directory (a separate host Python process is allowed; no second Flutter command). It waits for the OPEN marker for up to300s, so start it as soon as the runner prints the directory:

   ```sh
   python3 release/native-privacy/runtime-observation-staged/runtime_observation.py collect --root /Users/csys/Desktop/ibicot/idle --candidate <candidate> --evidence <printed-native-evidence-directory> --device F05BE4B0-52C1-4CA1-B721-BD64AE559E3F --output <fresh-observation-directory>
   ```

5. After the native runner completes normally, run:

   ```sh
   python3 release/native-privacy/runtime-observation-staged/runtime_observation.py finalize --root /Users/csys/Desktop/ibicot/idle --output <same-observation-directory>
   ```

   Repeat for `runtime-study-enroll` and Android with distinct appropriate run IDs; a failed/missed window needs a fresh attributable attempt, never rewritten evidence. Keep the original18 scenario lineage intact.

6. Fresh artifact inventory uses the reviewed collector `release/native-privacy/inspect_artifacts.py` SHA256 `b9a8e1f993324efd88ceec60f4c0f035141c1c6574020326a351619854f0643b`, the exact new debug/release reports, and these installed paths:
   - Java17: `.tooling/java/jdk-17.0.20.1+1/Contents/Home/bin/java`
   - aapt2: `.tooling/android-sdk/build-tools/36.0.0/aapt2`
   - bundletool: `.tooling/bundletool/bundletool-all-1.18.3.jar` (official release provenance `.tooling/bundletool/download.json`)
   - adb: `.tooling/android-sdk/platform-tools/adb`

   Rehash tools before actual use. Never fall back to an unverified Java or infer current declarations from the historical152 inventory.

## Pending prerequisites

- Lead's final reset-estimate integration/review and explicit source-stable handoff; QA currently owns Flutter.
- Independent inspection of this optional hook, collector and tests; promotion only after baseline hashes match. Staged Dart is formatted but not Flutter-analyzed/compiled.
- Approved-device live discovery after handoff, exact new candidate host checks and all five exports, then the58-cell native protocol and raw galleries/footage. No device was touched for this preparation.
- Actual Android `/proc` access and command availability must be measured; partial observations are retained as partial. Real startup/whole-SDK network coverage, physical-device measurements and actual provider/store behavior remain unqualified.
- Accounts, physical devices, hosting and human observers remain absent. No public launch, store approval, paid transaction, participant consent or observed-session metric is inferred.
