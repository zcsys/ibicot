# Capture overlay correction: author handoff

**Implemented and author-checked; independent review and fresh native capture remain required.** The only shared source changed is `game/mobile/integration_test/platform_smoke_test.dart`. Before hash `7622fd5997fff4d1e23f1a2facc66694e6a81741ddfbce4a3062fd7e61e1f647`; final hash `071635c01ed508077b467462bac279107a8716861ac97a5b657a5401b2cc3506`. The exact final source is archived as `platform_smoke_test.final.dart`; the minimal before/after change is `capture-overlay.final.patch` (SHA-256 `68aec308472a3ea5f45e7713e8fdcb902893116f0dc734562615e81492f08c3d`). The earlier stage pins and patch remain preserved as intermediate author evidence.

## Evidence and cause

The existing current-candidate phone preview contains Flutter's painted test-pointer circle/cross. The new read-only raw-video probe confirms it is already present in the native source: requested source time 5.233333333 seconds resolves to actual held frame 5.213333333 seconds, with the crosshair over Build 1. That corresponds to preview frame 1 at 4.733333333 seconds plus its 0.5-second source offset. The later held source frame at 6.045 seconds has faded the pointer. `raw-frame-inspection/metadata.json` records actual/requested times, dimensions and source path; original footage and failed draft evidence remain unchanged.

The pinned cached SDK paints the circle/cross when LiveTestWidgetsFlutterBinding receives a test-sourced pointer. Its propagated device-source branch forwards the unchanged event through GestureBinding without creating a painted pointer record. `SDK-pointer-evidence.txt` retains the relevant implementation and hash-bound SDK paths. No SDK source was edited.

## Smallest capture-only correction

A `CaptureGalleryBinding` subclass enables `shouldPropagateDevicePointerEvents` during binding construction and routes automated events through that existing propagated branch. It preserves the event object, coordinates and view ID; it neither invokes UI callbacks directly nor edits captured pixels. The capture scenario alone chooses this subclass. Every other scenario retains the original IntegrationTestWidgetsFlutterBinding initialization.

The capture scenario asserts the intended binding and propagation state, records that the inputs remain automated, and requires a positive routed-event count. Existing hit-test warnings remain fatal, and the production purchase assertion still requires the fleet count to increase by exactly one. All `tester.tap`, `pageBack`, visibility commands and screenshot calls remain. Seeded core/story data, the production app/controller, recorder handshake, real Stopwatch and the 4/8/14/20/25-second schedule are unchanged. There is no time compression, callback substitution, screenshot composition or physical/human-input claim.

## Author checks

- Scoped Flutter analysis of the owned harness: **no issues**. Initial analysis reported one unnecessary `gestures.dart` import; that source and diagnostic are retained, and only the redundant import was removed.
- One focused host test using the actual subclass: **passed**. A pointer hit activates the target once; a pointer miss does not activate it. The listener receives unchanged hit/miss coordinates with down/up/down/up order through the device dispatch source, and the binding records four automated events. Probe source SHA-256 `dd6dd57569842ba38853bb4e6a95fd74f05949c822d2df8283f40be4622a3404`. This is host routing evidence, not a native screenshot or human test.
- Source and evidence preservation: all pinned SDK files, dependency lock/config, mobile production sources, verification/recording/driver tools, old raw captures and failed draft files are unchanged. The exact checks and hashes are in `final-pins.json`. The first preservation diagnostic accidentally compared from an earlier unrelated Stopwatch; its failure and corrected capture-only diagnostic are retained. No behavior was changed in response to that diagnostic error.

Commands and output are archived in `author-command-results.initial.json`, `author-command-results.final.json` and their logs. The native verifier explicitly transferred the brief Flutter lane; all my Flutter commands have finished, and the lane has been explicitly returned to root. No device/native operation or baseline-suite rerun was performed for this correction. The only Swift execution decoded existing source footage on the host.

## Independent handoff and remaining gate

Root can independently review the exact final patch, SDK path and focused host probe. The same frozen production candidate `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59` remains the intended native source; the revised test harness must be separately pinned by the existing runner. The root's separate production-input audit is not replaced by this author handoff.

Retry the capture against that unchanged production candidate after independent review, retain its own recorder/identity/timing manifests, and visually inspect both raw and exported footage for absence of test markers and for preserved UI behavior. The correction is not visually qualified until that fresh native evidence exists. Keep the old failed draft and this author evidence. No store-ingestion, publication, original package completion, audio-capture or physical-device claim is made.
