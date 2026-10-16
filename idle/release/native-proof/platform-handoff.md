# Native platform handoff — 16 October 2026

## Delivered implementation

Project-local Flutter 3.47.7 / Dart 3.13.5, Java 17.0.20.1+1, Android SDK prerequisites and pinned native dependency setup. Actual iOS/Android/macOS projects use development identity `dev.tideglass.game`; product floors are iOS 16 and Android API 29. No signing secrets or global Java settings were changed. Swift Package Manager links the real purchase and ad SDKs; official sample ad app IDs prevent the native startup crash found during the probe. Release signing is intentionally unconfigured and Android has no debug-key release fallback.

`tool/build_native.py` snapshots verified immutable source, builds a separate workspace and preserves source manifest/archive, logs, artifact hashes and outputs. Future snapshots include the fixture/validator/contract files required by host tests and avoid recursively copying QA workspaces. `--mode release ios android` now selects an unsigned iOS device bundle and Android release AAB; that new release mode has not yet been executed. Root requested waiting for story/Support integration and QA fixes before the next candidate.

`tool/verify_native.py` checks unchanged production inputs and captures the exact harness. Runtime verification ID, candidate/harness fingerprints, scenario, label and run ID must all match; compile/start failure markers invalidate the result even when Flutter exits zero. The driver keeps the installation, explicitly stops its native process and exports isolated native save slots. A per-candidate lock prevents concurrent verification runs from overwriting test builds.

Original lighthouse/star SVG and 1024 PNG are in `game/client/art/`; all native launcher catalogs and launch screens now use original assets. Source is generated reproducibly by `tool/generate_native_icons.py`. XML parsing and Apple icon dimensions/opaque RGB checks passed. These assets are newer than the tested candidate and need the next native build plus final visual approval.

## Native evidence

Tested production candidate: `ce46598c4b513477c643f0dff4f5160400ac800b4ee76579c48ca2a5e08e1ffd`.

| Evidence | Result | Location under `release/native-proof/` |
|---|---|---|
| iOS simulator, Android debug APK, macOS debug exports | All compile; source snapshot unchanged | `20261016T095427.771900Z/build-report.json` |
| iPhone seeded UI purchase, Rechart cancel/confirm and disk reload | Pass | `integration-ios-phone-20261016T095946.013088Z/` |
| Android equivalent seeded fixture | Pass | `integration-android-phone-20261016T100111.069907Z/` |
| iPad equivalent seeded fixture | Pass | `integration-ios-tablet-20261016T100227.506479Z/` |
| iPhone fresh real-clock first purchase | Pass; 36.131 seconds; PID 75638 | `integration-ios-phone-20261016T100825.809052Z/` |
| iPhone new-process reload | Pass; PID 76465; 2 Skiffs and time-away credit retained | `integration-ios-phone-20261016T101005.788792Z/` |
| Android fresh real-clock first purchase | Pass; 37.719 seconds; PID 5138 | `integration-android-phone-20261016T101059.120074Z/` |
| Android new-process reload | Pass; PID 5292; 2 Skiffs and time-away credit retained | `integration-android-phone-20261016T101211.206142Z/` |
| Independent controller/persistence regression | 3 pass; fractional cursor bug fixed by persistence owner | `controller-review.md`, `controller-review-test.log` |

Seeded tests start from explicitly prepared 60 R or prestige-threshold states; they assert the exact 33.6 R purchase, 26.4 R remainder, 10 Charts, reset boundary and lifetime preservation. They are not natural pacing evidence. Natural tests start from an absent save with zero currency, use the actual native clock/timer, buy through the UI and exercise the real application bootstrap. Native save paths, exported slot files, process IDs, source identities, screenshots and logs are retained in each run directory. Screenshots were visually inspected on phone/tablet, including purchase and confirmation/reset states.

The candidate's independent host-test gate **failed**: its old negative test expected the now-supported schema version 2 to be rejected. Later working-tree fixes are not inherited by this candidate. The candidate is therefore not accepted for release despite the native passes.

Two failed/invalid harness attempts remain visible: `100415.147682Z` compiled an incorrect import and Flutter reused a previous binary; that result was explicitly invalidated. `100648.818501Z` could not reload because Flutter's default cleanup uninstalled the app and its sandbox; the corrected wrapper preserves the installation. Neither attempt is counted as a pass.

## Active runtimes and next actions

- Android emulator: `emulator-5556`, local AVD `Tideglass_API_35`, Pixel 6 / API 35 ARM64. Long-running execution handle **43501** remains active. It can be reused; close with the SDK emulator command when no longer needed.
- iPhone simulator: `F05BE4B0-52C1-4CA1-B721-BD64AE559E3F` (iPhone 17 Pro, iOS 26.3.1).
- iPad simulator: `F103390E-7B7C-4F0B-9404-5E029C7131FF` (iPad mini A17 Pro, iOS 26.3.1).
- Verification app processes are stopped after successful checks; test installations and isolated save data remain. The latest installed test harness is not the ordinary playable entrypoint. Install/launch the next stable main-app artifact for user review.
- Root should signal stable integration, then run a new immutable candidate with native debug/QA checks and the new local release packaging mode. Recheck the latest candidate, icons and source-specific test results.

No store sandbox purchase, real rewarded-ad delivery, hosted cloud conflict, signed distribution, physical-device performance, minimum-OS runtime coverage or human playtest is accepted. Exact account/device/hosting/tester dependencies and locally possible follow-ups are listed in `external-dependencies.md`. The user confirmed none are presently available. B02 remains unaccepted; this does not block continuing local development.
