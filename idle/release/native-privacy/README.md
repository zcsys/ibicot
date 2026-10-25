# Native SDK and data-flow qualification

This folder records preparation and actual artifact inventories separately. A dependency declaration, privacy manifest, mocked Dart gateway or absence of an application-level SDK call does not prove that a compiled SDK emits no traffic.

The native dependency review identified a missing privacy-options entry point for changing a previously granted advertising choice. That entry point and an explicit cold-start consent-info refresh are now integrated. Author host checks and independent review passed; the independent report is `../qa/integration-ad-privacy-20261021T141749224307Z/PRIVACY_REVIEW.md` (49 English and22 pseudolocalized cases, including five added boundary probes). The default configuration still disables rewarded ads and service connections. This implementation does not establish configured-provider or native consent qualification.

| Surface | Local inspection | Remaining evidence |
|---|---|---|
| Flutter plugins | Exact versions in captured pubspec.lock; native plugin inventory | Current compiled candidate and vendor-transitive versions |
| Apple privacy | App SystemBootTime reason35F9.1 for local elapsed-time calculation; SDK manifests in actual app archive | Current archive aggregation and observed default/opt-in behavior |
| Android privacy | App manifest and transitive SDK components/permissions | Current merged manifest and actual packaged manifest inspection |
| Guest startup | Dart does not intentionally initialize billing/ads from unconfigured services | Current simulator/emulator process-attributed traffic and private-storage samples |
| Optional ads | Consent refresh, canRequestAds, explicit user trigger and independently reviewed change-options host flow | Current native behavior; actual configured CMP/provider remains external |
| Optional study | Explicit consent; process PID/build/UTC; no uptime export or automated diagnostic upload | Current actual channel/persistence scenarios; no human enrollment evidence |
| External public pages | Explicit system-browser action; no account data appended | Configured approved endpoint and native handoff |

Official references checked21October2026:

- [Google Flutter privacy](https://developers.google.com/admob/flutter/privacy): refresh consent and expose the SDK-required privacy-options action. This is a technical integration reference, not an approved regional policy.
- [Google Android data disclosure](https://developers.google.com/admob/android/privacy/play-data-disclosure): the current vendor disclosure includes IP-derived location, interactions, diagnostics and identifiers. Exact collected data depends on the shipped SDK and configuration; do not label the ads SDK as collecting no data merely because Tideglass defers the Dart initialization call.
- [Apple privacy manifest structure](https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk): inspect actual app and third-party manifests in their bundle locations.
- [Apple aggregate privacy report](https://developer.apple.com/documentation/BundleResources/describing-data-use-in-privacy-manifests): an archive privacy report aggregates the linked manifests; it does not replace runtime verification or final store disclosures.

The deprecated Android DELAY_APP_MEASUREMENT_INIT key was considered but not added based on old examples. The current SDK must be assessed from its actual versions and behavior. No Firebase analytics/crash collector is deliberately added by Tideglass. Native SDK transitive behavior remains subject to inspection.

No physical device, provider account, signed store installation, published policy or submitted Data Safety/Privacy Nutrition Label is available. Local observations must retain those limits.

## Artifact collector

`inspect_artifacts.py` verifies a frozen candidate and five exported artifacts, records packaged Apple privacy/Info plists and Android SDK version properties, and decodes the exact release AAB manifest. Raw member bytes and command output remain available. `collector-author-20261021T142158.887991Z/` has11 parser/source checks and an actual collector run against the five **historical candidate152** artifacts. This is tooling qualification; no current native or traffic evidence is inferred.

The release-manifest decoder is Google's [bundletool1.18.3](https://github.com/google/bundletool/releases/tag/1.18.3), downloaded from that official release and matched to its published SHA-256. Tool provenance is in `.tooling/bundletool/download.json`. The SDK's aapt2 handles the debug APK. The collector neither installs builds nor uploads artifacts. Individual Apple manifests remain distinct from an Xcode-generated aggregate privacy report.
