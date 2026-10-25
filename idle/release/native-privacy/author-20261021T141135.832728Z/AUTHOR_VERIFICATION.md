# Privacy options author verification — M5-03 / S39

The integrated production privacy implementation passes its focused host gate. This is author evidence for independent review, not native/provider acceptance. Root promoted the four staged files byte-for-byte at `release/native-privacy/integration-20261021T141019.696970Z` after five baseline checks. This author lane exclusively owned Flutter while running the commands below; it ran no native/device command or broad matrix.

| Final exact-source check | Result | Raw evidence |
|---|---:|---|
| Whole-mobile Flutter analyzer | Clean | `final/analyzer.log` |
| New privacy tests plus existing native-services and service-settings tests, English | 44 / 44 pass | `final/english.log` |
| New privacy tests, compile-time pseudolocale | 17 / 17 pass | `final/pseudo.log` |

`final/runs.json` records exact commands, start/end times, return codes and all eight before/after input hashes. Every command had unchanged inputs. `final/source/` contains the final source copies. The three production files remained byte-identical to integration; only the new test changed during author verification.

## Preserved failures and repairs

The initial English run was 43 / 44 and pseudo 16 / 17; initial analyzer was clean. Both failures were the same cold unknown → Check → update failure → retry widget flow. Error prose pushed the lazy-list button outside the built viewport; calling `ensureVisible` on that unbuilt child raised `StateError: No element`. Initial raw logs, source copies and pins are preserved at this report's parent directory.

The repair uses actual scroll gestures to return through the list, locates the real keyed button again, and repeats >=48px dimensions, full bounds inside the actual scroll viewport, and five hit points before every subsequent action. It preserves all consent, retry, counter and state assertions. `repaired/test-repair.diff` records the change. That source passed 44 English and 17 pseudo tests. Formatting exposed one brace lint in the SDK mock's one-line condition; the final change encloses that same return statement in braces without changing behavior (`final/lint-repair.diff`). Final analyzer and both focused suites were then repeated at the final pin and passed.

## What the tests establish

The 17 emitted privacy tests cover no unsolicited SDK calls from default or configured initialization; configured settings local status reads without sign-in; legacy fake-gateway compatibility; cold unknown status resolving through explicit information update; update/error/timeout retry and late response rejection; delayed consent/load/configuration/display cancellation across privacy changes; same-account reauthentication identity guards; disposal of abandoned ads; preservation of an earned, server-confirmed synthetic receipt after display completion; and refusal of new loads without current SDK permission. The real SDK gateway is invoked through its actual pinned UMP method channel/codec, with synthetic channel responses; only status, explicit information update and requested privacy form calls are allowed. No reset, automatic consent form or ad initialization is permitted in that probe.

Actual Settings interactions run at 320×720 and 200% text in both English and pseudolocale, including the cold update failure and retry. The surrounding existing suites also verify account recovery, cloud choice/CAS, retained-code acknowledgement, optional telemetry and actual local-loopback HTTP account creation.

## Limits

There was no real configured provider, native UMP form, physical-device revocation, regional consent-message validation, OS screen-reader/touch qualification or public deployment. The channel probes are host-side SDK adapter evidence. Existing free/ad economy and Support token arithmetic were not edited; this run does not independently requalify that broader balance contract. Production privacy queries remain absent from guest initialization; entering configured settings performs a local SDK read, and only the explicit Check button performs the bounded information update. Required options remain a separate player action. A visible provider form is intentionally not given a timer that would permit new ads while it is open.

The reviewed primary references remain Google's [Flutter privacy guide](https://developers.google.com/admob/flutter/privacy) and [GDPR/privacy options guide](https://developers.google.com/admob/flutter/privacy/gdpr); dependency API version is `google_mobile_ads 9.1.0`. Original staged evidence remains unchanged; the final live test pin below supersedes its unrun test source for review.

## Final pins

- `game/mobile/lib/native_services.dart`: `f56a6a8ac2ce6fe583b859d1c65336ea4d858711456bf4243ba9d1fa24eb0e73`
- `game/mobile/lib/service_settings.dart`: `ff3a5b61c50a4239a943da85dd652ce81d3ff18e69c96d2b90ae367fcd571115`
- `game/mobile/lib/ad_privacy_copy.dart`: `e7b00d968f6f9b32f4e9688565a3b71972df318a417c0fc4a79f77395920bc79`
- `game/mobile/test/ad_privacy_test.dart`: `82efc50ebdc39444e6c50262d2d78eb17448d51709416c6e58dc148b7ce5c720`

The Flutter lane is released after final logs and hashes were recorded. No subsequent source edits are pending in this author lane.
