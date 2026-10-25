# Real OS reminder qualification handoff

Implemented only three new files: native reminder integration harness, standalone native runner and focused verifier tests. Production notification, lifecycle, economy, app, permission and save code is unchanged. No shared native harness was edited.15 focused Python verifier tests pass. Scoped Flutter analysis passes with no issues; its first eight import/nullability diagnostics and pre-fix source are preserved. Eight dependency/tool lock checks match the previously frozen source. Flutter lane was released before this handoff. No emulator, simulator, native test, OS permission or delivery operation has been performed by this author turn.

## Exact implemented scenarios

| Scenario | Preconditions and actual assertions |
|---|---|
| default | Fresh isolated preferences; OS permission may already be allowed or denied. Real pre/post permission unchanged; default initialization leaves foreground, preferences, and pending requests untouched except production cancellation of the three owned reminder IDs. No OS action is requested. The test rejects an observed initialization departure from foreground. |
| denied | Actual explicit production opt-in, with OS denial. If a real prompt appears, use its deny control. Assert native denied state, durable disabled preference and no queued requests. An already denied state is not evidence of a newly shown prompt. |
| quiet-cancel | Actual OS allowed state/explicit opt-in. One synthetic Focus phase with four minutes remaining, real clock and durable SaveRepository-backed GameController. Production ReminderLifecycle schedules through the actual planner/plugin; a one-hour current-local quiet interval defers the plan to its end. Real pending IDs then disappear on production return cancellation. |
| delivery | Actual OS allowed state. Use OS Home/background after the exact action marker. An actual paused callback runs production ReminderLifecycle, saves and schedules a single Focus reminder through the five-minute minimum and real timezone. Wait until the marker's UTC due time plus a practical delivery margin; return with the app icon, never by tapping the notification. Assert real delivered OS record with matching ID/body before cancellation, actual paused/resumed callbacks and elapsed monotonic/wall-clock evidence. Then assert native pending and delivered records canceled by production return. Unsupported or delayed delivery fails; it is never converted to a skipped pass. |
| revoked | Start allowed, actually schedule, then use the real OS app-notification settings opened by the gateway to disable permission. Return by the app icon. Assert denied permission and cancellation, then retry explicit opt-in and deny again if a new prompt appears; persist disabled preference. Require actual Settings departure/return. |

All gameplay snapshots are isolated synthetic fixtures, never ordinary player saves. The actual gateway is NativeNotificationGateway, preferences use FileNotificationPreferences, persistence uses SaveRepository and lifecycle uses ReminderLifecycle. No mock plugin/channel/gateway, injected clock, time compression or direct short-delay adapter scheduling is used. No additional production or UI feature is introduced.

## Native operator procedure and evidence limits

The lead must first finish independent source/verifier review and coordinate the exclusive native lane. Use the newly frozen candidate; the runner pins this independently versioned test harness against its unchanged production inputs. A device must already be booted and ready. The reserved tablet F103390E-7B7C-4F0B-9404-5E029C7131FF is refused, as are physical devices and ambiguous target strings. Do not erase a previous fixture or reinstall merely to reset permission; every invocation needs a fresh run ID.

Example command (replace the three concrete operator-selected values):

```sh
python3 tool/verify_native_reminders.py /absolute/frozen/candidate --device SIMULATOR_OR_EMULATOR_ID --label ios-phone --scenario default --run-id fresh-run-id
```

Run default before opt-in when qualifying first-entry behavior. For the first actual opt-in, capture real OS prompt and action using native UI tools during the run and retain the screenshots/observations against the exact verification ID. **A printed action marker is an instruction for the operator, not evidence that a person clicked. An existing allowed/denied state proves only that observed path, not presentation of a fresh permission prompt.** If no fresh prompt can be observed without deleting existing evidence, preserve that limitation. iOS simctl `privacy` has no notifications service; its `reminders` service is unrelated and must not be used. No adb permission grant/revoke bypass is implemented.

The delivery scenario requires a real five-to-six-minute minimum window (plus OS scheduling delay), actual background/resume and an OS delivered-notification API record. Android's inexact scheduling may delay it; the runner/harness bounds are20/15minutes, and an unsupported or late run stays failed/unqualified. These simulator/emulator APIs do not qualify physical-device delivery, battery, lock-screen privacy, accessibility of OS Settings, or whether a person saw a banner. OS UI captures remain a separate native-lane evidence obligation.

## Evidence and failure handling

The runner locks the frozen candidate, verifies production inputs before/after, archives/hash-pins harness, driver and validator helpers, checks identity-bound native action log records, requires both native-framework and driver completion, and rejects teardown/uncaught errors. Actual native artifacts are hashed before/after. Android installed APK must match the host APK hash; iOS installed bundle files must match the actual host bundle. Source/harness drift, missing records, shortened timing, clock-only delivery, stale lifecycle callbacks and merely pending notifications cannot pass.

Final source/hash observations and app-stop command timeouts are recorded as errors in the final failed report; they do not escape final observation handling. The native driver process group is bounded and terminated on timeout. Only the specified test app is stopped. The real harness teardown cancels its production reminder IDs; a crashed/timeout test does not assert that cancellation happened, so its own pending reminders must be inspected before later qualification. No account, purchase, provider, study or public deployment operation is part of these checks.

This handoff is authored implementation plus host validation, not completed M3-05/S26 qualification or independent approval. Expected next step is lead review of these exact files and later real native execution under the coordinated lane. No new production freeze is needed for a later test-only repair; retain the failed evidence and pin the repaired harness separately.
