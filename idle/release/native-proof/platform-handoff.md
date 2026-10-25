# Native platform handoff — frozen 152 candidate

Completed 21October2026. Candidate `152805bf9e269f49d14486286656ac0174a808384d10e6623533a4f92690dc11` now has three debug exports, two unsigned release exports and22 passing native scenarios. This is local engineering evidence for independent review. Finished-v1 and public-release acceptance remain open.

Start with the [qualification summary](20261021T101953.650199Z/local-qualification-summary.json), [final integrity check](20261021T120204.582776Z-152-final-verification/final-verification.json), [exact runtime index](20261021T120204.582776Z-152-final-verification/runtime-matrix.json) and [42-log superseding audit](20261021T120204.582776Z-152-final-verification/native-log-audit.json). Historical d85 documentation is [preserved unchanged](20261016T112921.896155Z/platform-handoff-d85-preserved.md), along with every original candidate and failed attempt.

## Source and build evidence

The immutable candidate lives at `.tooling/build-candidates/20261021T101953.650199Z-152805bf9e26`. It derives from 667 solely by the reviewed help copy correction about saved daily offset/backward-clock protection; it makes no promise of authenticated forward-clock time. The [source manifest](20261021T101953.650199Z/candidate-manifest.json) and [host ancestry](20261021T101953.650199Z/host-gate-chain.json) identify the exact change.

| Gate | Observed result | Evidence |
|---|---|---|
| Parent667 host checks |705 tests pass: core176, persistence19, progression27, events31, platform41, simulation14, mobile300, base Python50, providers32, native tools15; seven analyzers clean |[Parent report](20261021T101431.356858Z/build-report.json) |
| Final152 copy checks | Fresh6English and6expanded pseudolocale help tests pass; whole mobile analyzer clean |[Final copy gate](final-copy-gate-20261021T102032.868811Z/verification.json) |
| Debug exports | iOS simulator, Android APK, internal macOS app pass |[Debug report](20261021T102112.746555Z/build-report.json) |
| Unsigned release exports | iOS device bundle and Android AAB pass |[Release report](20261021T103632.486357Z/build-report.json) |
| Signature absence | No iOS signature/provisioning profile; AAB reports unsigned and has no signature entries |[iOS inspection](20261021T103632.486357Z/ios-unsigned-inspection.json), [Android inspection](20261021T103632.486357Z/android-unsigned-inspection.json) |
| Final integrity | Frozen source, production inputs and dependency locks match; all five artifact hashes match;22 required runtime cells accepted |[Final check](20261021T120204.582776Z-152-final-verification/final-verification.json) |

The 705 tests were executed on the explicitly unchanged parent source, followed by the fresh final-copy checks; they were not all rerun on 152. The debug workspace matches every captured input. The release workspace differs only in the pinned SDK's generated Android plugin registrant, which excludes the development integration-test plugin. No signing fallback or manual generated plugin list was used. Artifact hashes and exact commands are in the linked reports. Reproducibility covers this host's pinned source, locks, recipes and recorded outputs; it does not establish a second-host or byte-identical rebuild.

## Native runtime matrix

| Actual scenario | iPhone17Pro / iOS26.3.1 | Android15 API35 / arm64 | Dedicated iPad mini / iPadOS26.3.1 |
|---|---:|---:|---:|
| Seeded purchase/Rechart and native disk reload | Pass | Pass | Pass |
| Fresh save,35 actual seconds and UI purchase | Pass | Pass | — |
| Separate-process natural-save reload | Pass | Pass | — |
| Seeded24h worker, cosmetic collection,25producer stages and native audio | Pass | Pass | Pass |
| Separate-process session reload | Pass | Pass | — |
| Actual monotonic clock and OS Home/reopen | Pass | Pass | — |
| Separate-process clock scope | Pass | Pass | — |
| Actual native share sheet and cancellation | Pass | Pass | Pass |
| Four raw production screens and gameplay footage | Pass | Pass | Pass |
| Total |9|9|4|

The [runtime index](20261021T120204.582776Z-152-final-verification/runtime-matrix.json) records every device identifier, exact harness hash, result, log and run ID. Natural scenarios start with an absent isolated save and a free Skiff, wait real time, buy through the UI and restore the second Skiff in a different native process. Worker/cosmetic fixtures explicitly seed 24 hours of absence, Notes and earned chapter appearance; they execute production replay, collection, spending and disk paths. They do not establish natural pacing or retention.

Clock probes use actual MethodChannel samples. Home/reopen was performed through the OS, not injected Flutter lifecycle callbacks. Android retained its same-boot epoch across process restart; Apple received a new process epoch. Android's guest wall clock differed from the host, and no authenticated UTC claim is made. Native clock deltas are preserved without exporting private raw uptime/epochs.

All eleven bundled AAC assets decoded with positive duration and the playback clock advanced on each platform. Production audio switched all three music tracks and exercised foreground cue gating. Android audio output was disabled. These are decoder/playback-state checks, not audible-quality, headphone, mute-switch or interruption qualification. Debug simulator worker/startup samples are not physical p95 or battery results.

Share tests invoked the production export function with a test-only download substitution and a synthetic 201-byte ZIP. The actual iOS popover/Android chooser was observed, captured and cancelled without choosing a recipient. This proves sheet invocation/cancellation; paid ownership, hosted download and receiving-app delivery remain unproven.

## Raw screenshots and footage

| Device | Raw pixels | Actual silent video duration | Source-pinned manifest and review |
|---|---|---:|---|
| iPhone |1206×2622|25.275s|[Manifest](integration-ios-phone-20261021T112255.702927Z/capture-manifest.json), [visual review](integration-ios-phone-20261021T112255.702927Z/visual-review.json) |
| Android |1080×2400|29.3351s|[Manifest](integration-android-20261021T114929.560297Z/capture-manifest.json), [visual review](integration-android-20261021T114929.560297Z/visual-review.json) |
| Dedicated iPad |1488×2266|25.5633s|[Manifest](integration-ios-tablet-20261021T115934.504362Z/capture-manifest.json), [visual review](integration-ios-tablet-20261021T115934.504362Z/visual-review.json) |

Each set contains actual main, chapter, challenge and season UI. Footage contains a real scripted purchase and navigation from explicitly seeded progression. Raw files were not edited; video decoding and representative-frame inspection are recorded separately. Integration-test pointer overlays can appear during taps. These are engineering drafts, not promotion-ready material or representations of the later working-tree build. S43 requires final shipped-source captures after the outstanding changes.

Original ordinary-main apps were restored after harness runs. The [dedicated tablet launch](main-launch-tablet-20261021T1201Z/main-launch.json) shows fresh onboarding; the [Android retry](main-launch-android-retry-20261021T112658.548926Z/main-launch.json) shows its existing guest save/offline dialog. The first Android ordinary launch timed out under concurrent resource load; its failure remains preserved. The successful retry used the same APK. An earlier externally changed tablet session was not attributed to test actions and was left untouched.

## Failures and audit repairs

Five 152native attempts remain failed/invalid: an overly short playback wait; two double-disposal teardown runs; an invalid gallery lifetime/Charts fixture; and Android's static screenshot waiting for a frame after surface conversion. Harness fixes used bounded playback polling, exactly-once audio cleanup, valid lifetime entitlement and the SDK-required frame pump. Successful retries use the same frozen production source and separately pinned harnesses.

The old verifier incorrectly accepted the two teardown failures because the driver printed success and returned zero. Its replacement requires a positive native completion count plus driver completion and rejects framework/uncaught errors, including Android E/flutter output. The [independent review](../qa/lead-native-completion-20261021T113003923748Z/REVIEW.md) reproduced counterexamples and repairs. The final 42-log audit preserves original reports and explicitly supersedes exactly those two false passes; d85's 12accepted native runs remain valid under this stricter log check. Legacy d85 payloads predate some152identity fields, which the audit reports without inventing them.

## Check against original v1 scope

| Scope | Evidence contributed here | Acceptance still open |
|---|---|---|
| S01 native phones/tablets/public launch | Native phone and dedicated tablet checks; ordinary app launches; internal macOS export | Final source, physical usability, signed install/update and both public store launches |
| S12 saves/recovery | Frozen persistence suite, actual native disk reopen and seeded worker/cosmetic retention | Newer native file-lock and economic migration repair, broader physical interruption/upgrade/cloud recovery matrix |
| S23 audio/supporter soundtrack | Eleven native AAC decodes, production music controls/gating, synthetic export sheet cancellation | Physical audible quality/interruption and verified purchased soundtrack delivery |
| S24 commerce | Native package links and synthetic export boundary | Both store sandbox purchases, restore/pending/retry/refund/revocation and verified delivery |
| S31 performance | Debug simulator worker execution and individual samples | Named physical 60/30fps, startup p95 ≤5s,24h replay≤3s,30-minute battery/thermal measurements |
| S36 platform/store acceptance | Unsigned packages and reviewable raw screen drafts | Current submission review, configured products/reviewer access and final store acceptance |
| S40 builds/configuration | Pinned SDK/locks, five exports, immutable ancestry and integrity; actual native probes | Newer complete candidate including S14/native locking, independent full-candidate review |
| S43 polish/store assets | Twelve raw screen captures and three 15–30second clips inspected | Newer final-source capture, human content/usability findings, store-ready material and publication |

Newer soundtrack cache, campaign optionality/content migration, opt-in study recorder/UI, art catalogue tests, backend operations, S14 transition and native file-lock work are excluded from152. Future build tooling now explicitly captures synthetic study fixtures and runs nested provider/operations/study suites; those later tooling gates do not retroactively change152host evidence.

The user has no developer accounts, physical devices, hosting or human testers. [External dependencies](external-dependencies.md) remain open. No work-package or public-release acceptance is added by this handoff.

The iPhone, Android emulator and dedicated Verification tablet were shut down after restoring ordinary main apps. The protected Development tablet `F103390E-7B7C-4F0B-9404-5E029C7131FF` remains untouched. Root owns the Flutter lane again; the repaired current-source art sample awaits root/gameplay stability. See [runtime inventory](20261021T101953.650199Z/runtime-state-at-handoff.json).
