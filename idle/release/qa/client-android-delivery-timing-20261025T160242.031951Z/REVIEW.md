# Android delivery timing review

The failed run remains failed. Its empty delivered-record list proves that no matching reminder was active at the observed return. It does not establish a production scheduling defect or prove that the alarm would have delivered later. Returning only 44.951 seconds after the requested due time was too early to use non-delivery as a failure of Android's inexact delivery contract.

## Exact observed result

Candidate 3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59, native run v3b00-r20261025-android-delivery, PID 5708. The failed verifier 38a60e7e… and all 32 indexed native files plus 7 diagnostic files rehash correctly. Production-difference/source-difference lists are empty in that verifier. This review makes no new runtime observation.

| Observation | Actual value |
|---|---:|
| Production schedule observed |2026-10-25 15:49:44.680 UTC|
| Requested due |2026-10-25 15:55:00.000 UTC|
| Actual resume/record start |2026-10-25 15:55:44.951 UTC|
| Schedule→due |315,320 ms|
| Schedule→return, monotonic |360,267 ms|
| Due→return |44,951 ms|
| Whole delivery watch elapsed on return |402,161 ms|
| Unused portion of 720s watch at return |317,839 ms|
| Actual active records before production cancellation |empty|

The cancelled-alarm history at 18:55:44.976 local names Tideglass's ScheduledNotificationReceiver and matches the return. It is a post-cancellation snapshot. It supplies neither the missing pre-return queue/window nor proof of why the alarm had not fired. Granted permission, a manifest receiver, and a saved pending record are necessary evidence; none proves actual delivery. Final verifier errors about missing completion/preferences digest/actual-background completion follow the delivered-record assertion stopping the test; they must remain in the failed report and are not independently diagnosed defects here.

## Source trace and timing contract

`NativeNotificationGateway.schedule` uses `AndroidScheduleMode.inexactAllowWhileIdle`. Installed flutter_local_notifications 22.3.2 converts the timezone date to epoch time, then calls `AlarmManagerCompat.setAndAllowWhileIdle` with RTC_WAKEUP. Its `pendingNotificationRequests` enumerates persisted scheduled definitions; its `getActiveNotifications` queries actual Android NotificationManager records. The harness samples those actual records before production `ReminderLifecycle.returned` cancels pending and active reminders. All original save identity, body/id, actual lifecycle, real 5-minute minimum and cancellation checks remain mandatory.

Android documents that this API does not fire before its trigger, and on Android 12+ may take up to an hour without battery restrictions; restrictions can defer it further. Consequently due+45 seconds is not an upper delivery guarantee. This is distinct from the 10-minute `setWindow` rule, which this plugin branch does not use. [Official Android alarm scheduling](https://developer.android.com/develop/background-work/services/alarms).

## Feasible next native run: unchanged code and bounds

1. Preserve this failed run and diagnostic packet. The native owner establishes a fresh runID, actual PID/device/artifact identity and observed permission state; after a revoked case, permission restoration uses only the approved actual Settings/dialog UI procedure.
2. Follow the same actual Home marker. While the app remains backgrounded, archive a read-only AlarmManager snapshot immediately after the schedule marker, plus relevant actual NotificationManager state. Bind package/receiver/alarm identity and requested due to this run. This resolves whether an alarm is actually registered and exposes its OS window/policies without assuming the plugin's persisted pending list is the OS queue.
3. Keep the existing 720-second combined watch. After the due time, make bounded read-only OS observations for an active dev.tideglass.game notification 77101 with the exact Focus body. Preserve timestamped raw records. If using the notification shade for visual confirmation, use observed UI and do not tap or dismiss the reminder. Importance.low/silent means a heads-up banner is not the required signal.
4. Only after that actual receipt and before the unchanged deadline, return via the observed launcher icon with sufficient time for the return observations. The harness must independently observe the same actual ID/body before cancellation and pass every current check. An OS receipt alone cannot replace that assertion, and a saved request or alarm queue is not delivery.
5. If no receipt appears with time remaining for return, capture the pre-return queue/notification/idle evidence and preserve an unqualified or failed outcome. Do not increase the deadline silently, reset the clock, shorten production scheduling, inject delivery, relax records, or add exact-alarm access. A later bounded protocol change can be reviewed only if the newly observed OS window shows the existing bound cannot meaningfully cover this platform; 720 seconds is not a platform-wide delivery SLA.

This is an operator observation refinement, not a code repair: the marker says not_before and the current handoff already permits an OS delivery margin. No assertion requires returning at nominal due+45 seconds. The harness retains 720 seconds combined, 15-minute outer test; the driver and runner retain their own existing limits. The prior procedure's actual-UI, identity, evidence and no-direct-mutation restrictions still apply.

## Quiet-hours guarantee boundary

Original design line 309 says reminders respect quiet hours; M3-05/S26 retain opt-in quiet-hour notifications. The current planner moves requested due times out of the quiet interval and the settings explain that plan. Existing copy also explicitly discloses that the device may delay or suppress delivery, and that the plan uses the timezone when leaving. Installed native receiver code posts on actual dispatch without rechecking the game's quiet interval. Therefore current source supports quiet-hour **planning** and does not establish an absolute exclusion of delayed delivery inside quiet hours: for example, a permitted 21:59 due could be dispatched after a 22:00 quiet start. This is a source-backed guarantee limit, not an observed violation in this 18:55 local run. Do not promote a planning test into proof of dispatch-time exclusion. If the original requirement is applied to actual display time absolutely, a deliberate production receiver-time policy would be needed; no such change is authorized or authored in this review. Changing to exact alarms merely for test success is not recommended.

## Independence and scope

This is a read-only source/evidence timing investigation. The reviewer previously authored the callback-observation harness repair; its different-author root review remains the code approval, and this report does not substitute self-approval. No device, Flutter, source, scope, program, clock, permission or old-report writes occurred. No M3-05/S26 acceptance, physical-device outcome, later delivery or root cause is asserted.
