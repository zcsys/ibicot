# Reminder callback-zone repair — author handoff

Author: `/root/client_asset_review`. Staged only; production and live reminder harness were not modified. Root must independently review and promote before native retry.

## Observed failure and bounded diagnosis

The preserved iOS delivery run `release/native-notifications/integration-ios-phone-20261023T081652314287Z` failed with `OutsideTestException` after real Home and return. The old harness rethrew its stored exception at line 363 and discarded the originating stack. Its native callback called `recordPlan`, which executed package:test matchers. In the actual locked dependencies, matcher 0.12.20 reads `TestHandle.current`; test_api 0.7.12 throws `OutsideTestException` when the callback has no test-zone invoker. The new negative control reproduces this exact exception from even a passing matcher in `Zone.root` and catches it in the observer. This establishes the mechanism, not successful native notification delivery or an assertion that this was the only native issue.

`baseline.json` retains every original failed-run file and the initially inspected alternate cached test_api 0.7.15 source. `actual-dependency-pins.json` pins the actual locked test_api 0.7.12 and matcher 0.12.20 files, lockfile and package configuration. Neither dependency version was changed.

## Minimal test-only correction

Native lifecycle callbacks now collect actual plan/save/clock/pending/delivered/cancel observations, without invoking test matchers. Assertions run in the main test zone. Callback errors retain original object, stack, lifecycle state and UTC timestamp; all captured failures remain in report data. Rethrow uses the original stack. A plan's future due time is validated against its captured scheduling observation, which avoids comparing it to a test body that may resume after six real minutes.

Observation polling uses a real monotonic stopwatch and asynchronous timer without `tester.pump()`. The pinned live binding's pump awaits a rendered frame, so it is unsuitable as a prerequisite for observing paused lifecycle state. This does not synthesize frames, advance time, fake lifecycle events or promise timer execution while the OS suspends the app. The two delivery phases share the prior 720-second observation budget; elapsed seconds are rounded upward before computing the second phase's remainder, so truncation cannot add nearly a second. Polling remains at the existing 100ms cadence; the external runner timeout remains authoritative for a stalled native process.

## Preserved strict gates

| Gate | Result |
|---|---|
| Real `NativeNotificationGateway`, plugin, file preferences and production lifecycle | Unchanged; no mock channel/gateway |
| Default opt-out, explicit opt-in, denied/revoked paths and quiet cancellation | Preserved |
| No warning, exactly one planned reminder, actual pending `[77101]` | Main-zone validators preserve assertions |
| Committed payload and settlement boundary equal current game state | Preserved; explicit non-null snapshot assertion |
| Planned due time is in the future | Compared to actual captured scheduling UTC |
| Real paused/resumed lifecycle and completed schedule/return | Preserved |
| Actual delivered record with ID 77101 and exact focus body | Preserved; scheduled request alone still fails |
| Delivery observation at or after due time | Preserved |
| Actual pending and active reminder IDs empty after return | Preserved; actual active IDs now stored rather than hardcoded empty output |
| Five-minute production minimum and real >=290000ms elapsed verifier gate | Unchanged verifier and production source |
| Original callback failure must fail main test | Preserved with original stack; raw error report retained |
| OS permission state/prompt provenance | Unchanged; prior permission state cannot prove a fresh prompt |

## Author checks

Scoped analyzer: exit 0, no issues. Host checks: 23 passed. These are synthetic observation/validator controls, not OS delivery evidence. They cover root-zone observation, the old matcher failure mechanism, retained callback stack, frame-independent polling, finite absent-condition rejection, valid plan/delivery contracts, ten invalid-plan inputs and six invalid-delivery inputs. First proposed staged bytes are retained in `before-host-refinements/`; no failed host test run was discarded (the first executed analyzer and 23-case run both passed).

The staged harness was copied unchanged to `game/mobile/integration_test/author_reminder_callback_zone_20261023.dart`. The staged test was copied to `game/mobile/test/author_reminder_callback_zone_20261023_test.dart` with only its relative harness import changed to that temporary name. Exact temporary hashes and the import replacement are in `temporary-copies.json`. Both owned copies were removed after terminal completion; the original live harness still hashes `272fa3495fee356a98256c09ecfa983ef1f7af1ffb1c2c4885db97e74905fd76`.

Commands, from `game/mobile`:

```sh
../../tool/flutter analyze --no-pub integration_test/author_reminder_callback_zone_20261023.dart test/author_reminder_callback_zone_20261023_test.dart
../../tool/flutter test --no-pub --reporter expanded test/author_reminder_callback_zone_20261023_test.dart
```

The exact absolute argv, working directory, exits and elapsed times are in `command-results.json`. Format used the repository cached Dart SDK, on staged files only. Root received the exclusive Flutter lane after both commands terminated; no device calls were made. All 482 mapped production inputs still match frozen candidate `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`, both in live source and candidate workspace. All baseline/failed evidence and actual dependency pins remain unchanged.

## Promotion and remaining qualification

Promote only the reviewed staged harness to the existing integration-test path; the host probe may remain as retained evidence or be independently copied for reproduction. `callback-zone.patch` and `staged-pins.json` identify exact reviewed bytes. No production change, scope status, store approval or provider readiness is claimed. A fresh, separately pinned real native delivery run must still satisfy the unchanged permission, minimum elapsed time, actual delivery, lifecycle, save and cancellation gates. Original failed native evidence remains intact.
