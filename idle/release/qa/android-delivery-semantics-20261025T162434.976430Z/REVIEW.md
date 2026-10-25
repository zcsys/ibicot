# Android delivery teardown and observer overlap

Recommend a prospective **operator-only refinement**, with no harness, production or Flutter SDK change: finish the observed launcher hierarchy/image capture before tapping the current Tideglass icon; after that tap, do not open another UiAutomation session until the native/framework/driver run is terminal. Use raw screencap, read-only activity/PID/notification receipts and native lifecycle/result observations during this interval. Keep the exact existing completion and semantics leak gates.

## Preserved actual outcome

`integration-android-20261025T161006684764Z` remains failed, report SHA `96e56315397749e294f1c03e7c0fb2c61a978118c8d5648b2566fad6a03da9fb`, checkpoint `693b28281dee21f5a397d6e8510e7a3244f176c3995a6b704abb63fe2a5f11fc`. Native result `completed=true` records actual delivered ID 77101 with the exact Focus body, actual background/return, 601,745 ms since scheduling, empty callback failures, and empty pending/active notifications after cancellation. I viewed the actual notification-shade image: it shows Tideglass's lighthouse reminder in the Silent group. The visible body is truncated; the full matching body comes from the native API/raw OS records, not an invented full visual reading.

The final Flutter invariant failed with `A SemanticsHandle was active at the end of the test`, from `WidgetTester._verifySemanticsHandlesWereDisposed`. Strict host verification correctly rejects this despite successful body assertions. The pure archived verifier failure was independently reproduced; no log filtering, result relabeling or assertion bypass is proposed.

## Concrete ownership and timing

Pinned Flutter is 3.47.7, revision `abaf9c523780a608bd46686fd5e53740a07077f8` (source paths and hashes in verification). `widget_tester.dart:178–180` records outstanding handles before creating the test-owned handle; the handle is disposed after the callback. Its end guard at 1063–1090 compares the final binding/pipeline counts to the original baseline. The web-only exception does not apply to this Android run. `binding.dart:1953–1969` executes that guard after the body and widget cleanup.

`SemanticsBinding._handleSemanticsEnabledChanged` at `semantics/binding.dart:160–168` separately obtains and releases an SDK-owned handle in response to actual `platformDispatcher.semanticsEnabled`. Android's pinned `AccessibilityBridge.java:398–407` forwards system accessibility enable/disable to `AccessibilityChannel`, whose methods call `FlutterJNI.setSemanticsEnabled(true/false)`. The archived reminder harness itself contains no explicit `ensureSemantics` call. Disposing arbitrary production/platform handles would violate this ownership and is unnecessary.

[Android 15 r1 DumpCommand](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-15.0.0_r1/cmds/uiautomator/cmds/uiautomator/src/com/android/commands/uiautomator/DumpCommand.java) opens a UiAutomation connection for hierarchy inspection and disconnects in `finally`; its source is archived with a digest. Thus a hierarchy dump is an active accessibility observer even though it makes no app data change.

Actual current-icon tap command completed at **16:21:01.702783 UTC**. A new `uiautomator dump` began at **16:21:01.741498** and had completed by the next command at **16:21:05.153560**. Actual native return/result at **16:21:02.570** falls inside that observer command interval. The screenshot after that dump was black and XML empty during terminal teardown; neither is a successful restored-game visual claim. The pre-action current-icon image/hierarchy hashes are valid and remain required.

Together the source ownership and exact overlap strongly support an external accessibility-session race with the test's end invariant. There is no captured allocation-level handle trace, so this is a bounded causal diagnosis, not proof that every possible handle had that origin. A fresh run with the observer overlap removed must still pass the original guard; a repeated failure would need additional ownership evidence rather than suppression.

## Minimal prospective procedure

1. Preserve actual background scheduling, unchanged real-time/deadline bounds, raw OS alarm/delivery records, exact ID/body and the observed notification. Do not increase the delivery window or inject a notification.
2. While still on the launcher, capture the current icon's unique hierarchy and screenshot and wait for that capture command to finish. Ground the subsequent tap in that actual observation.
3. After the icon tap, use only non-UiAutomation read-only observations until the exact run's framework and driver have terminated. Do not toggle accessibility, dispose handles, alter semantics flags or edit the SDK. Native lifecycle/delivered/pending/active/result and strict final log checks remain mandatory.
4. Only after terminal completion may another hierarchy inspection begin. Keep any failure intact and do not claim success from `completed=true` alone.

The method already permits screenshot/native evidence for post-state; it does not require a new accessibility session during test teardown. This refinement preserves observed-action grounding and is compatible with the separately authored revoked-restart protocol; no shared harness delta is needed. QA performed 83 read-only checks and pinned 81 files. No Flutter/device invocation, production/canonical edit, source patch, acceptance update or successful native classification occurred in this review. Earlier failures remain sealed.
