# Native platform handoff — frozen d85 candidate

Completed local packaging on 16 October 2026; source, artifact hashes, signature absence and native evidence integrity reverified on 19 October after the interrupted turn. This is an engineering handoff for independent review, **not finished-v1 or public-release acceptance**.

Candidate: `d85bdf74433d96d2f6ea6a58a8481290942d526a7cdb8ec14b55e57537e9dced`, under `.tooling/build-candidates/20261016T112921.896155Z-d85bdf74433d`.

Start with the [qualification summary](20261016T112921.896155Z/local-qualification-summary.json), [final integrity/signature checks](20261019T135402.439115Z-d85-final-verification/final-verification.json) and [source manifest with exact parent overlays](20261016T112921.896155Z/candidate-manifest.json). The candidate derives from frozen 344 by the approved iOS audio-context repair, its regression test and a declared native harness. Later harness revisions are captured and hashed separately for every native run.

## Delivered checks and artifacts

| Check | Result | Evidence |
|---|---|---|
| Exact candidate host gate | Six analyzers clean; core 176, persistence 18, progression 25, events 31, platform 6, mobile 135, Python services 48, candidate-integrity 3 pass (442 tests) | [Debug/host report](20261016T112947.203869Z/build-report.json) |
| Native debug exports | iOS simulator app, Android APK and internal macOS app pass | Same report; all artifact hashes reverified 19 October |
| iPhone native scenarios | Five pass: seeded purchase/Rechart, real-clock purchase, separate-process reload, seeded 24h worker/collection/audio session and its cold reload | [Exact scenario index](20261016T112921.896155Z/local-qualification-summary.json) |
| Android native scenarios | Same five pass | Same scenario index |
| iPad native scenarios | Two pass: seeded purchase/Rechart and worker/collection/audio session | Same scenario index |
| Unsigned iOS device export | Pass; `codesign` confirms no signature; iOS 16 floor, development identity `dev.tideglass.game`, version 0.1.0 | [iOS export](20261016T115204.670734Z/build-report.json) |
| Unsigned Android AAB | Pass after exporter repair; `jarsigner` reports unsigned and archive has no signature entries | [Successful AAB export](20261016T115658.068642Z/build-report.json) |
| Ordinary main app | Original debug artifacts installed and launched on iPhone/Android after harness runs; onboarding/harbor screenshots inspected | [Main launch report](main-launch-20261016T115329.506624Z/main-launch.json) |
| Packaging regression | Four integrity/export-command checks pass on 19 October | [Tool test log](20261019T135402.439115Z-d85-final-verification/packaging-tool-tests.log) |

The natural scenarios begin with an absent isolated save, zero Radiance and the free Skiff, wait 35 actual seconds and purchase through the UI. Observed scenario elapsed time was 36.595s on iPhone and 37.648s on Android; each cold reload ran in a different native process and retained the second Skiff and earned currency. These are scripted real-clock checks, not human pacing observations.

Seeded tests explicitly prepare the 24h absence, Notes and earned chapter. They execute the actual native replay worker, finalize salvage receipts, spend exactly 50 Notes for a decoration, equip the chapter appearance and decoration together, and verify retention across a process restart. Boundary fixtures verify the 33.6 R purchase, 26.4 R remainder, Rechart cancellation and confirmation, 10 Charts, reset fields and retained lifetime earnings. All 25 producer-stage renderings and phone/tablet screenshots were inspected; see [visual review](20261016T112921.896155Z/native-visual-review.json).

Actual native audio checks switch all three music tracks, exercise the production foreground-gating API, decode all eleven bundled AAC assets with positive duration, advance the native playback clock and pause. Android ran with emulator audio output disabled. These checks do not establish audible quality, physical mute/headphone/interruption behavior or OS background lifecycle qualification. Single seeded-worker bootstrap samples (iPhone 532 ms, Android 1476 ms) are debug/emulator observations, not physical-device p95 results.

## Repairs and preserved failures

The previous 344 candidate exposed a real iOS audio configuration failure: the plugin rejects respect-silence plus explicit mix-with-others. Root repaired production with an explicit ambient context, whose mixing behavior is implicit. The [original finding](integration-ios-phone-20261016T112519.267147Z/audio-finding.json) remains; d85 native audio checks passed.

Three d85 runtime attempts remain failed in the index. They exposed harness waits on continuously scheduled audio position frames and asynchronous audio cleanup. The harness now uses bounded UI waits and awaits `audio.close()` before removing its owning widget. No failed run is counted as a pass. Earlier candidate host failures from stale portable-recovery assertions and omitted fixture/service test inputs also remain preserved; the d85 host gate passed independently.

The first Android release export failed because `--no-pub` skips Flutter 3.47.7's release-specific plugin registration. Its generated Java registrant referenced the dev-only integration-test plugin while release Gradle excluded that plugin. The exporter now first enforces the dependency lock, lets the pinned SDK regenerate Android release registration, and verifies all captured dependency locks remain unchanged. No generated plugin list was edited by hand. The [failure and diagnosis](20261016T115204.670734Z/android-packaging-finding.json) and failed matrix are retained; the separate retry produced the successful AAB. The successful runner is copied and hashed in its evidence directory.

Frozen source and debug workspace match every captured file hash. The release workspace differs only in the SDK-generated Android `GeneratedPluginRegistrant.java`; all dependency locks match. Tooling now supports immutable candidate reuse, explicit parent overlays, separate debug/release workspaces and per-candidate locking. Reproducibility evidence covers pinned source/locks/recipes and recorded outputs on this host; no second-host or byte-identical rebuild is claimed.

## Comparison with assigned v1 scope

| Scope | Local evidence delivered | Acceptance still required |
|---|---|---|
| S01 — native phones/tablets and public launch | Both native phone runtimes, iPad scenarios, debug install/launch and unsigned exports | Newer complete candidate, physical usability, signed install/update and both public store launches |
| S12 — saves and recovery | Frozen persistence suite; native disk save/reopen and worker/appearance retention | Later privacy cleanup, interrupted cloud-import recovery and physical storage/power-loss/upgrade matrix |
| S31 — performance | Actual native worker execution and single startup samples | Named physical 60/30 fps, repeated startup p95 ≤5s, 24h replay ≤3s, 30-minute battery/thermal observations |
| S40 — native build and configuration feasibility | Pinned tools, exact manifests/overlays, clean host gate, debug and unsigned exports, repaired release registration | Independent complete-candidate review and qualification of later native services/plugins/configuration |

Newer root service integration, secure storage/provider extension, notification plugins/configuration, client localization, bounded math cache and later persistence changes are **not in d85**. Root will capture a new complete candidate after those handoffs stabilize. No new candidate was captured during this handoff.

The user has no developer accounts, physical devices, hosting or human testers. [External dependencies](external-dependencies.md) remain open: store sandbox commerce, real rewarded-ad/consent delivery, hosted cloud operations, signed distribution, minimum-OS/physical performance and human usability. No work-package or release acceptance was added here.

## Runtime state at handoff

The ordinary main applications were restored on 16 October, and test saves remain isolated. On 19 October no iOS simulator was listed as booted and no Android device was attached; there is no live build process. Earlier emulator process handles are stale. Reuse device IDs from the [recorded environment](20261016T112921.896155Z/device-environment.json) only after checking current availability. The prior ce465 and 344 reports remain indexed in `qualification.json` and retain their original outcomes.
