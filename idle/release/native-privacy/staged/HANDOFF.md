# Advertising privacy options — staged implementation handoff

Scope: M5-03 / S39 and the original optional-ad consent requirements. This is an authored implementation, not an accepted native/provider integration. No live app files were changed. `promotion.json` pins the four promotion files and five unchanged baseline inputs; `privacy-options.patch` preserves the exact proposed diff.

## Production behavior

- `RewardedGateway` is unchanged. The optional `AdPrivacyGateway` adds `readAdPrivacyState()`, `updateAdPrivacyState()`, and `showAdPrivacyOptions()`. Existing test/adapters without the capability remain compatible.
- `NativeServicesManager` exposes `adPrivacyAvailable`, `adPrivacyRequirement`, `adPrivacyBusy`, `adPrivacyError`, `refreshAdPrivacyOptions()`, `updateAdPrivacyOptions()`, and `showAdPrivacyOptions()`.
- Opening configured Account & cloud settings reads only local SDK status. Initialization and an unconfigured guest launch invoke none of these SDK methods. No privacy control appears for an unconfigured/sample-ID adapter. Device-level choices remain accessible after sign-out when a real adapter is configured.
- Unknown status presents **Check advertising privacy options**. That explicit action requests fresh UMP consent information, with a 30-second SDK update wait plus a 5-second status read; the manager bounds the total at 35 seconds. It does not initialize/load ads or automatically display a consent form. Successful required status presents the separate options action; errors retain a retry. Not-required status hides the entry.
- Required options call the actual SDK privacy-options form. A visible form is not timed out while the player is interacting; new ad requests remain blocked until it returns. Status and error feedback use new external English copy through the existing pseudolocale presentation boundary.
- Starting any privacy read/update/form invalidates uncompleted optional-ad work synchronously. Continuations also require the exact session object, session generation, account intent and local save seed. A late response after account replacement cannot publish manager state or authorize old work.
- Once an earned ad display has completed, later privacy interaction does not cancel that display's subsequent server-ledger receipt lookup. Account/seed/slot guards still apply. No code in this patch awards a token directly or mutates an already persisted Support slot. New requests still require fresh SDK permission. No free/ad reward arithmetic changed.

## Authored verification, not yet executed

Seventeen emitted focused tests cover:

1. Unconfigured/default initialization and compatible legacy gateway; zero privacy network/SDK calls.
2. Configured initialization makes no query; explicit local status does not update consent, load ads or show forms.
3. Cold unknown → explicit update → required options, without an ad.
4. Update failure/retry and stale response after account creation.
5. A stalled explicit update times out; late success cannot publish.
6. Privacy invalidates delayed consent.
7. Privacy invalidates loaded/configuring but unshown ads and disposes them.
8. Privacy invalidates unfinished display and blocks new requests while the form remains open.
9. Completed display retains its server-confirmed synthetic receipt through later privacy changes.
10. Same-account reauthentication invalidates prior continuations and a late form response.
11. Status/form errors retain safe retry; status failure cannot load an ad.
12. Unknown requirement cannot authorize an ad even with stale `canRequestAds=true`.
13. Real `SdkRewardedGateway` method-channel calls: cold status, explicit consent-info update, options form, update/form errors; exact allowed method set excludes automatic consent forms, reset and MobileAds initialization.
14–15. Settings hide the action without configuration and when not required.
16–17. Actual Settings action at 320×720 and 200% text: required flow plus cold unknown/update failure/retry/options. Button bounds and hit testing are asserted; the same tests are intended for English and the compile-time pseudolocale.

Dart formatting parsed all four staged sources. All five live baseline hashes still matched at handoff. No Flutter test, analyzer, native command, device or external provider request was executed by this lane. No passing test count is claimed. Root owns the exclusive Flutter/native lane and should retain actual English/pseudo/analyzer logs after promotion.

Suggested focused commands after baseline-checked promotion, from `game/mobile`:

```sh
../../tool/flutter test test/ad_privacy_test.dart test/native_services_test.dart test/service_settings_test.dart
../../tool/flutter test --dart-define=TIDEGLASS_PSEUDO=true test/ad_privacy_test.dart
../../tool/flutter analyze
```

The SDK method-channel test deliberately imports the pinned SDK's internal UMP wire codec, solely to encode/decode real `ConsentRequestParameters`. Its source hash is recorded. This is host-side adapter verification; it is not evidence that a real configured native UMP message exists or that a physical-device revocation flow has passed. Required provider message configuration, native execution, physical accessibility and regional policy qualification remain open.

## Primary references and boundaries

Implementation was checked against Google's current [Flutter privacy guide](https://developers.google.com/admob/flutter/privacy) and [GDPR/privacy options guide](https://developers.google.com/admob/flutter/privacy/gdpr), and pinned `google_mobile_ads 9.1.0` source. The guide requires checking privacy-options status after consent-info update; the explicit Check path fixes cold-launch unknown status without starting an ad. No production `reset()`, cached custom consent decision, obsolete native measurement flag, fabricated ad ID, extra dependency or economy change was added.

The browser deletion review and its corrected documentation remain separate evidence under `release/qa/client-web-deletion-20261021T134443512157Z`; this staged work does not qualify hosting/publication or production account services.
