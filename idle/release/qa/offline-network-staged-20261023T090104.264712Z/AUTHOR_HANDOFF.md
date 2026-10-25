# Staged S02 Android offline guest qualification — 25 October 2026

This packet is **staged, not executed native proof**. The paused draft `paused-harness.dart` is preserved byte-for-byte (68629c6c…). No production, candidate, device, network setting, canonical scope or program file was changed. No listener/socket, Flutter, Dart analyzer or device command was executed by this author. The 27 passing Python methods use synthetic in-memory receipts; they do not prove airplane-mode behavior.

Original S02 asks for “Airplane-mode guest flow and localized-layout tests; fresh network services are separate dependencies.” This packet addresses the missing actual guest offline flow. Existing independent localization evidence is separate. It adds no paid-provider, public Internet, physical-device or human-study prerequisite to this local clause.

## Exact executable pieces

- `platform_smoke_offline_test.dart`: staged copy of current `platform_smoke_test.dart` 1c8ed846…, with only the natural scenario instrumented and an appended helper. It retains absent-save bootstrap, 35 real seconds of earnings, actual hit-tested Skiff purchase, durable save, same isolated run ID and new native PID reload, all original economic/restore assertions. The fixed wait becomes a minimum 35-second wait with repeated actual socket probes. No seeded shortcut.
- `offline_support.py`: a nonce-bound TCP challenge listener on **127.0.0.1 only**, independent TCP health client, strict pure validator, read-only OS snapshots and checkpoint export. The app addresses the listener through **10.0.2.2**, Android Emulator’s host-loopback alias. No DNS or external destination. Three online round trips establish an app-to-host clock offset; uncertain alignment is rejected. Listener health must bracket every app outage. A dead listener, invalid protocol reply, missing health receipt, reachable endpoint, retained Wi-Fi/default network or ambiguous OS dump cannot qualify.
- `verify_offline_native.py`: narrow wrapper derived from the current native verifier. It retains frozen snapshot and 482 production-input pre/post checks, candidate lock, archived exact harness/driver/source hashes, native framework **and** driver completion, failure precedence, explicit process stop and save export. It adds exact profile/predecessor binding, read-only network snapshots, immutable listener prefix, actual checkpoint export/hash and final offline validation. The archived native regular-file probe uses `adb shell`, not the historically faulty `exec-out` boolean transport. `exec-out` is used only to read file bytes.
- `harness.patch` / `runner.patch`: full exact deltas; `before/` preserves all originals.
- `test_offline_protocol.py`: 27 pure methods including a complete synthetic start/reload and negative controls for target/nonce/source/marker/sample identity, path tokens, retained network, protocol errors, dead listener, missing/altered receipts, missing operation coverage, short earnings window, wrong purchase, same PID, checkpoint mismatch and missing restoration. These fixtures are explicitly synthetic.

The first run had one test-fixture failure: app/server receipt dictionaries were aliased, so the negative mutation changed both. `test_offline_protocol.first.py` and `host-tests-first.log` preserve it. Only the fixture now copies the app receipt. The final 27 methods pass; Python syntax compilation passes. No production repair was indicated.

## Review and execution sequence (not yet performed)

1. Different-author review of this packet, then scoped Dart format/analyze of the staged harness in an isolated package configuration. Do not change shared pub artifacts or live harnesses. If diagnostics require a staged correction, preserve this seal and add the exact delta.
2. Native owner reserves the candidate lane after reminder work and boots only owned **emulator-5556 / API35**. Root inspects actual network settings and records baseline UI. No resets, permission grants, host-network changes or protected simulator access.
3. Start the listener with a fresh pair ID and new evidence directory. It remains running across both native processes. Example, from repository root (replace UNIQUE with a fresh alphanumeric token):

   ```sh
   python3 release/qa/offline-network-staged-20261023T090104.264712Z/offline_support.py --directory release/native-proof/offline-listener-UNIQUE --harness release/qa/offline-network-staged-20261023T090104.264712Z/platform_smoke_offline_test.dart --run-id v3b00-offline-UNIQUE
   ```

4. Native owner runs the staged verifier, specifying exact frozen candidate, device, profile and pair ID:

   ```sh
   python3 release/qa/offline-network-staged-20261023T090104.264712Z/verify_offline_native.py .tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122 --device emulator-5556 --platform android --label android-offline --scenario natural-start --run-id v3b00-offline-UNIQUE --network-profile release/native-proof/offline-listener-UNIQUE/profile.json
   ```

5. On the **bound `request-disable` marker**, root uses actual emulator Settings/Quick Settings to enable airplane mode and disable Wi-Fi if Android retains it, preserving before/action/after UI evidence. Return to the actual app. The harness requires three failed app socket attempts while resumed, then verifies offline bootstrap, real earnings, purchase and save. The runner snapshots airplane/Wi-Fi/data/default network/routes/API at entry and completion. If a virtual Ethernet/default network remains or the endpoint remains reachable, preserve a failed/unqualified attempt; do not substitute a visible icon or change the verifier.
6. After a passed start, keep the same listener/profile/run ID and radios disabled. Launch `natural-reload` with the same command plus `--predecessor ABSOLUTE_PATH_TO_START/verification.json`. It requires the same actual checkpoint hash and a different native PID, reopens the saved fleet, and probes offline before/after restore assertions. It emits **`request-restore`** only after the offline flow completes.
7. Root restores baseline radio settings by actual UI and returns to the app. Three successful nonce challenges and actual OS restoration are required. The final wrapper compares airplane/Wi-Fi/mobile-data settings against the start’s baseline. Stop the listener only after the report and prefix archive exist. Root/native should restore the original settings on any failed or interrupted attempt as explicit cleanup, preserving the failure.
8. Independent review must replay receipts, actual operator captures, checkpoints, save files and source pins before recommending S02. No current pass is claimed.

Each operator transition has a two-minute bound; the integration/driver test has an eight-minute bound. Background polling does not wait on a paused Flutter frame. Only exact native markers cause read-only OS snapshots; they never toggle connectivity. A new app process is mandatory for reload.

## Limits and source basis

A local socket failure alone is not proof of broad Internet absence. Qualification is the conjunction of app-local-path failure, continuously healthy listener, actual airplane/Wi-Fi/default-network state, actual gameplay and subsequent recovery. Android API35 is the runtime target; API36 remains a build target, not a claimed runtime test. The listener health check is independent of the app but uses the same local listener. The executable verifier is deliberately fail-closed on unrecognized OS output.

The emulator alias is documented by [Android’s official address-space reference](https://developer.android.com/studio/run/emulator-networking-address). The strict `Active default network: none` parser follows [AOSP ConnectivityService](https://android.googlesource.com/platform/packages/modules/Connectivity/%2B/e58b20025b/services/core/java/com/android/server/ConnectivityService.java); raw dumps are retained so a format difference is diagnosable rather than silently accepted.

This packet cannot qualify iOS offline disconnection. It does not disable macOS networking, alter host routes, claim simulator airplane isolation, or infer physical-device behavior. If isolated simulator disconnection is unavailable, that target’s exact unexecuted condition remains explicit; an Android result must not be relabeled as iOS evidence. No new external condition is invented for the original S02 text.
