# Local reminders — author handoff

Status: implemented and host-tested; root integration, a new native build, independent review, and physical-device delivery checks remain separate gates. This feature is not in the frozen `d85bdf74433d` native candidate.

## Scope comparison

| v1 requirement | Implemented behavior | Evidence / remaining qualification |
| --- | --- | --- |
| S26 / M3-05 optional quiet-hour notifications | Preferences default off. Only `enableByPlayer()` requests OS permission. No startup, scheduling, settings-build, or lifecycle prompt. | Pure/service tests plus actual plugin method-channel argument tests. |
| State-derived readiness | Next Focus transition uses the saved 2-hour phase and 12-charge capacity; next Survey uses the saved 8-hour phase and 3-Survey capacity. The storage reminder marks 24 hours at full rate and states quarter-rate continuation until 72 hours away. | Exact core-state fixtures, comparison with actual core advancement, and read-only serialization comparison. |
| Quiet hours and player controls | Default 22:00–08:00; editable start/end, individual reminder kinds, master off, permission recheck, and OS settings link. No streaks or repeated daily schedule. | All 24 departure-hour cases, both DST directions, user-control widgets, invalid/equal time rejection. |
| Bounded, bundled notices | At most three one-shot identifiers. Reminders shifted to the same instant are combined. Minimum five-minute lead; never round readiness earlier; never schedule at/after the 72-hour horizon. | Planner tests and native request assertions. |
| Return / preference / clock handling | Serialized cancellation and rescheduling; return clears the old plan; explicit clock-change handling cancels; unknown time zone or clock rollback yields no new plan. A later confirmed plan clears a transient warning. | Race, revoked permission, invalid zone, clock-change, and subsequent recovery tests. Root owns lifecycle wiring. |
| Save isolation | Versioned strict preference file, 4 KiB read bound, temporary-file write and rename. Invalid input is preserved and defaults off. No preference or notification state is placed in the economic payload. | Actual temporary filesystem tests; failed-save and failed-schedule tests. |
| M5-02 language/layout readiness | All new reminder, permission, channel, and settings copy lives in `NotificationCopy`. Expanded pseudo copy is supported. Time entry is a scrollable 24-hour form. | 320 × 720 logical pixels, 200% text, expanded-copy interaction tests. This externalizes this feature only; it is not a claim that the whole game is localized. |
| Notification rewards | None. Taps only open the application; no reward payload, economic mutation, recurring schedule, or collection receipt. | Native adapter argument assertions and pure planner tests. |

## Public integration interface

```dart
final reminders = NotificationService.native(applicationSupportDirectory);
await reminders.initialize(); // reads settings and cancels stale notices; no prompt
// Existing settings scroll view:
NotificationSettings(service: reminders);

await reminders.onReturn(); // on resumed, before gameplay resumes
await reminders.onClockChanged(); // when the host detects a clock/zone discontinuity
await reminders.scheduleForAbsence(
  state: newestSavedCoreState,
  settledThrough: newestSavedSettlementCursor,
); // only after true background departure and successful settlement/save
```

Do not schedule for transient `inactive` events such as the OS permission dialog; use actual `paused` / `detached` departure. Await return cancellation before a later departure schedule. The service itself serializes asynchronous operations so a slow schedule followed by return cannot leave a late notice queued. Call `dispose()` at host teardown; it does not remove a legitimate absence plan.

Constructor injection is available for `NotificationGateway`, `NotificationPreferenceStore`, UTC clock, and `ReminderPlanner`. Listenable fields are `preferences`, `permission`, `planned`, `zoneName`, `warningKey`, and `busy`. `ReminderPreferences` is immutable and has a strict JSON schema. `enableByPlayer()`, `updatePreferences(...)`, and `openDeviceSettings()` support the settings component. `updatePreferences` cannot silently turn opt-in on.

## Native and dependency configuration

Pinned dependencies: `flutter_local_notifications` 22.3.2, `flutter_timezone` 5.1.1, and `timezone` 0.11.2. The lockfile records the complete resolved tree.

Android adds `POST_NOTIFICATIONS`, the plugin's non-exported scheduled receiver, desugaring 2.1.4, and an original lighthouse notification vector with an explicit resource-shrinker keep entry. Scheduling uses `inexactAllowWhileIdle`, a low-importance private channel, no sound/vibration/badge, and only the three owned IDs. There is no exact-alarm permission, full-screen intent, wake-screen access, boot receiver, or background service. Existing minimum Android 29, development AdMob IDs, and disabled OS backup remain unchanged.

iOS assigns the `UNUserNotificationCenter` delegate and initializes the plugin with all permission requests disabled. Explicit player opt-in asks for alerts only. Scheduled notices specify no sound or badge. Existing minimum iOS 16 is unchanged; no remote push entitlement or external service is involved. macOS's generated registrant changed through dependency resolution; the service deliberately reports unsupported outside iOS/Android.

## Verification

Author command from `game/mobile`: `../../tool/flutter test test/notification_service_test.dart test/notification_settings_test.dart` — **17 passed** (12 planner/service/adapter, 5 settings/copy). Full output: `release/notifications-tests.log`.

Targeted analysis of all five new source/test files: **no issues**. Exact file hashes and command metadata are in `release/notifications-author-evidence.json`.

The iOS/Android adapter tests execute the real Flutter plugin API against a mocked method channel. They establish the native request shape and permission boundary; they do **not** establish OS delivery. Earlier test defects found and repaired: the time-zone package requires explicit UTC alias handling, and Flutter's standard time dialog overflowed at narrow 200% text; the custom scrollable editor preserves text size.

## Device proof limits and next checks

- Compile a new Android and iOS candidate containing the new plugins and configuration. The earlier immutable native build does not qualify these changes.
- On physical iOS and Android devices, confirm default-off launch, explicit permission acceptance/denial, no sound/vibration, cancellation on return, OS revocation, and delivery with real application suspension and power-management policies.
- Quiet hours control the requested schedule. The OS may delay/suppress inexact delivery; delivery itself is not an exact-time guarantee. A device time-zone change while the process is terminated cannot be observed by this Dart service until the application next runs. The UI explains which device time zone the plan uses and that it refreshes on return/settings changes.
- Android reboot intentionally drops pending alarms because no boot-rescheduling receiver is installed. A new plan is made after the next return/departure. This avoids reviving stale plans; reboot rescheduling is not claimed.
- The IANA database is bundled with the pinned time-zone package; future civil-time rule updates require a dependency/content maintenance release. Unknown zones fail closed rather than scheduling at a guessed time.

## Official implementation references

- [flutter_local_notifications package and native setup](https://pub.dev/packages/flutter_local_notifications)
- [Current zonedSchedule API](https://pub.dev/documentation/flutter_local_notifications/latest/flutter_local_notifications/FlutterLocalNotificationsPlugin/zonedSchedule.html)
- [iOS permission and settings API](https://pub.dev/documentation/flutter_local_notifications/latest/flutter_local_notifications/IOSFlutterLocalNotificationsPlugin-class.html)
- [Device time-zone identifier package](https://pub.dev/packages/flutter_timezone)
- [IANA time-zone data and conversion package](https://pub.dev/packages/timezone)

Source requirements reviewed: `V1_ROADMAP.md` daily systems and M3, `AI_IMPLEMENTATION_PROGRAM.md` B08/M3-05 and B15/M5-02, and `TIDEGLASS_DESIGN.md` opt-in bundled quiet-hour notifications. No change to account-day reward rules or currency mathematics is required.
