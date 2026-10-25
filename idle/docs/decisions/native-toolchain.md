# Native toolchain qualification

Status: **provisional implementation candidate; B02 is not accepted**. Observed 16 October 2026. This record covers M0-02, M0-03 and M0-08 / S01, S36 and S40. An export, SDK link or simulator launch does not prove a sandbox purchase, production ad consent, cloud recovery, physical-device performance or signed distribution.

## Candidate and decision

Use Flutter stable 3.47.7 with a pure Dart economy package and independent persistence package. It fits Tideglass's interactive two-dimensional harbor, extensive accessible controls and shared deterministic simulation without introducing a game-engine dependency into economic rules. iOS and Android remain public targets; macOS is an internal development host. The client is not a browser wrapper.

Flutter is provisional until the required native and service probes pass. The [official archive](https://docs.flutter.dev/install/archive) recommends stable releases for production. The official tag was resolved to the full commit below; a detached checkout deliberately prevents an implicit upgrade. The host's pre-existing Android Java link was broken. A verified project-local JDK repairs development without changing shell profiles or system Java settings.

| Component | Pin / current observation | Evidence |
|---|---|---|
| Flutter | 3.47.7; `abaf9c523780a608bd46686fd5e53740a07077f8` | Official Git tag and local version command |
| Flutter engine | `deb287481e3ce9468f3434937ced4240a70539ca` | SDK engine pin |
| Dart | 3.13.5 | Bundled SDK |
| JDK | Eclipse Temurin 17.0.20.1+1, macOS ARM64 | Archive SHA-256 `196d13ba5f10414bef7f6a05a9b3f00edacb18ebacef2b99485db9e2ee18f0e8` |
| Xcode | 27.1 / 27A9275 | Existing host installation |
| iOS deployment target | 16.0 (product floor; SDK supports older) | Native project settings |
| Simulator runtime available | iOS 26.3.1 | `simctl list runtimes`; this is not minimum-OS hardware coverage |
| Android minimum / compile / target | 29 / 36 / 36 | Product floor Android 10; Flutter API 36 compile/target pin; recheck before submission |
| CMake | 3.22.1 in the local Android SDK; required by native integration-test dependencies | Installed during candidate build using existing accepted SDK license records |
| Android NDK | 28.2.13676358 | Flutter SDK pin |
| Android Gradle plugin | 9.1.0 | Native settings |
| Kotlin Gradle plugin | 2.4.0 | Native settings |
| Gradle | 9.3.1 | Wrapper distribution |
| Native purchases | `in_app_purchase` 3.3.1 | Direct dependency; transitive versions in app lockfile |
| Optional rewarded ads | `google_mobile_ads` 9.1.0 | Direct dependency; sample test app identifiers only |
| Apple plugin integration | Swift Package Manager | Both selected plugins supply native Swift packages |
| Application identity | `dev.tideglass.game` | Provisional development ID; ownership not asserted |

The Android source SDK is read through project-local links to the existing command-line tools, emulator, API 35 image, build tools and platform tools. Additional platform/NDK packages, Java, Flutter, pub cache and Gradle cache live in `.tooling`. Existing accepted Android SDK license records are copied into that local SDK. The bootstrap does not enroll an account or accept new account terms.

## Repeatable local commands

From the `idle` directory on this macOS ARM64 host:

```sh
python3 tool/bootstrap_native.py
tool/android 'platforms;android-36' 'build-tools;36.0.0' 'ndk;28.2.13676358'
cd game/mobile
../../tool/flutter pub get
../../tool/flutter analyze
../../tool/flutter test
cd ../..
python3 tool/build_native.py ios android macos
```

`tool/flutter`, `tool/dart` and `tool/android` apply isolated environment settings. Do not substitute the broken global Java configuration. The bootstrap verifies the Flutter commit and JDK archive; it refuses an unexpected existing Flutter checkout. On another host, provide an existing official Android SDK with `--android-sdk-source`. This bootstrap does not claim Windows/Linux support.

`build_native.py` takes a verified, immutable source snapshot under `.tooling/build-candidates/<UTC>-<fingerprint>/source`. It hashes the working tree before and after copying and rejects a mixed copy. A separate `workspace` is allowed to contain build-generated files. The candidate includes game packages/content/assets, integration tests, tool configuration and economic configuration. An exact manifest and a reviewable compressed source archive accompany the build evidence. Dependencies resolve with `--enforce-lockfile` inside the candidate; the original absolute tool wrapper supplies the pinned SDK and local caches. Concurrent development can continue without changing that candidate.

The wrapper captures commands, tool version, logs and exit results in a timestamped `release/native-proof` directory, preserving successful exports in its ignored `artifacts` subdirectory. Its iOS export is an unsigned **simulator** build and its Android export is a **debug** APK. Runtime launch remains unproven until separately exercised. The manifest distinguishes the tested candidate from the evolving working tree. Release signing is unconfigured; Android's generated debug-key release fallback was removed. `--snapshot-only` prepares a candidate without building it. Native integration tests run from the candidate workspace with the original absolute Flutter wrapper and the copied test driver.

## Native adapter requirements

The [official purchase plugin](https://pub.dev/packages/in_app_purchase) supplies StoreKit and Google Play adapters. Listen for interrupted transactions from startup; pending or unverified results do not grant cosmetics. Validate purchases and restored transactions independently of gameplay saves, commit delivery idempotently, then finish the platform transaction. Native account and test-product configuration are still needed. No sandbox purchase has been performed by this setup.

The [official ads integration guide](https://developers.google.com/admob/flutter/quick-start) requires app identifiers in Android's manifest and Apple's property list. Only Google's sample identifiers are present. Ads must remain behind the eventual privacy/consent and explicit reward flow, with the identical free briefing route. Package linkage is not consent verification or ad delivery evidence. The ad plugin supports iOS/Android, so internal desktop builds must use the free route and never invoke an unsupported ad adapter.

The launch probe demonstrated that a missing Google app ID can crash iOS during native startup even when the Dart app has not requested an ad. The failure and corrected build are preserved; the real app already uses the sample ID. Do not infer absence of SDK startup behavior from absence of a Dart initialization call. The [SDK team explains](https://groups.google.com/g/google-admob-ads-sdk/c/73Vk7nADtbk) that the old Android `DELAY_APP_MEASUREMENT_INIT` mechanism concerned a deprecated SDK and app measurement is no longer invoked by current GMA. We have not substituted that obsolete flag for a current traffic/consent audit.

The app's Android OS backup is disabled while branch-aware recovery is implemented. Core progress remains local and offline-capable; trusted commerce and future cloud conflict handling cannot be implemented by merging OS-restored wallets. `INTERNET` is declared for the eventual optional service adapters. No production credential is embedded.

## Evidence boundaries and remaining gates

The native compile and launch evidence is recorded separately in `release/native-proof/qualification.json` when each attempt finishes. Source code compilation must be distinguished from game behavior verification.

Still required before B02/service acceptance:

- Actual purchase/reset interaction on both native targets, matched to the headless economy results.
- StoreKit and Play sandbox purchase, pending, duplicate, restore, interruption and revocation/acknowledgement scenarios using authorized test products.
- Native rewarded-ad test delivery and refusal/no-fill behavior through the equal free allowance ledger.
- A real staging cloud revision conflict, both recoverable branches and independent entitlements.
- Named physical-device, minimum-OS, performance and accessibility coverage; current simulator coverage is insufficient.
- Approved app identity, developer account authority and signed install/update evidence before distribution.

No spending, signing-secret access, store enrollment, external testing distribution or public release is performed by these scripts.


## Native verification commands and runner safeguards

Run `python3 tool/verify_native.py <candidate-directory> --device <simulator-UUID-or-emulator-serial> --label <label>` to exercise the seeded purchase, preview/cancel/confirm Rechart and native disk reload. The exact test harness and driver are copied into the evidence directory and fingerprinted. The production libraries/assets/content must still match the frozen candidate. This permits QA-harness repairs without silently replacing the production code under test.

For a fresh real-clock run, add `--scenario natural-start --run-id <unique-id>`; then repeat against the same device, label and run ID with `--scenario natural-reload`. The first starts without any save or seeded progress, waits an actual 35 seconds, purchases the second Skiff through the UI and writes a checkpoint. The second asserts a distinct native process ID and restores the saved fleet/progress through the real bootstrap. Save slots are exported from the isolated native verification directory for inspection.

Two Flutter driver behaviors were observed and are guarded explicitly. Its startup retry can run a previous binary after a compilation failure; an exit code of zero is therefore insufficient. Each passing result must match the expected runtime verification ID, candidate fingerprint, harness fingerprint, scenario, device label and run ID, and its log must contain a clean build/start and successful assertions. Also, its default cleanup uninstalls the app and removes its sandbox. The wrapper instead keeps the installation and explicitly terminates the native process, preserving storage for a meaningful reload. The failed/invalid attempts remain in evidence and are not counted as passes.

Candidate `ce46598c4b51` compiled successfully for all three native targets and passed seeded native interaction checks on iPhone, Android and iPad. Its independent host-test gate failed because a negative test still expected supported schema version 2 to be rejected; subsequent working-tree fixes do not retroactively repair that candidate. These native checks do not make it a release candidate.
