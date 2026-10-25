# Android reminder batch and M3-05/S26 readiness addendum

**Keep M3-05 in_progress and S26 not_verified.** The current Android batch independently supports default opt-out, actual denial and quiet-hour scheduling/cancellation. Actual delivery and permission revocation are still unqualified because their fresh attempts failed. Existing actual Settings/input/presentation/audio evidence and all five iPhone scenarios remain supported; they were not rerun.

| Android scenario | Independent disposition | Exact native report prefix |
|---|---|---|
| Default opt-out | Supported by the earlier sealed current review; no automatic prompt or pending request. | 3c5e1c53 |
| Actual denial | Supported: fresh task/PID, actual current dialog, observed deny-button tap, resumed app, disabled preference and no pending request. Both earlier timeout attempts remain failed. | 8888701c |
| Quiet-hour cancellation | Supported: separately observed actual Settings permission enablement; production lifecycle method calls, native scheduling at the exact next local quiet-hour end, durable payload equality and native cancellation. Synthetic Focus/quiet inputs and absence of an actual Home transition in this particular fixture remain explicit. | a8f362dc |
| Real delivery | Failed: actual Home and current-icon return after nominal due, 360,267 ms since scheduling, but delivered_records was empty before return cancellation. Inexact OS lateness is under investigation, not a proven cause or eventual-delivery guarantee. | 38a60e7e |
| Actual revocation | Failed: Settings opened/drew and the app returned still allowed before any recorded operator gesture. A Back-preview event and close are recorded, but their origin is unestablished. Successful revoke/refusal/cancellation is absent. | 3526106f |

The separate Settings allow precondition is independently supported by five actual screens, unique uppercase Tideglass/lighthouse identity, current installed APK label/package and exact-package POST_NOTIFICATIONS false/USER_FIXED→true. It is not called a fresh permission prompt. Compose Settings hides intent extras; no visible package URI is invented.

All new UI actions are explicitly recorded automated Android SDK events under the prospectively approved procedure, not human clicks, CUA events, shell permission grants or synthetic lifecycle callbacks. The denial event stays inside the unchanged 150-second bound. The delivery case preserves the real minimum scheduling interval. The initial and later failures remain immutable. Success means native/API behavior on the owned API35 emulator; it does not imply physical reliability, human banner visibility, lock-screen behavior, usability, store qualification or API36 runtime coverage.

## Exact original clause decision

M3-05's original requirement is “Text scale, number notation, motion/audio controls, input navigation and opt-in quiet-hour notifications function across targets.” Its original M1-05 and M3-01 dependencies are accepted. The already-reviewed real Settings actions, native audio, English/pseudo layouts, large text, non-color cues, reduced motion, help and input evidence supply their existing portions. The iPhone default/denied/quiet/delivery/revocation packet remains valid. No additional physical or human-comprehension gate is added to this implementation criterion.

S26's original verification is “Large text/reduced motion/non-color cues and critical controls work on named targets.” The existing target-control evidence remains supported. This previously established across-target reminder qualification remains open until the actual Android delivery and revocation portions are demonstrated under a reviewed procedure. Neither a scheduled request nor a Settings screen alone satisfies the missing behavior.

The five new review probes total 242 read-only checks: denial 52, Settings precondition 65, quiet 30, delivery-failure classification 60 and revocation-failure classification 35. Ten malformed success payloads and two late exceptions are rejected in the denial/quiet reviews. Those are verifier checks, not additional native runs. The actual source, result, UI, operation, timestamp, saved-state and failure evidence is pinned. QA ran no Flutter, device, network or broad test suite and changed no production/status file.

This is an append-only update to the sealed final forward audit at d259ba03/b215b2cb, subject to its separate S08 physical-return-budget correction. The source contracts and original package dependencies remain unchanged. The local reminder remainder is now specifically successful actual Android delivery and revocation, rather than all four prior pending scenarios. S02 is being executed separately and has no outcome in this reminder review. No finished-v1 or release-ready claim follows.

Authorship remains explicit: this reviewer authored earlier focused Settings and ID protocol probes; root separately reviewed and reproduced their essential behavior. Current native execution is authored by native_verifier; actual-UI method was independently reviewed by client_asset_review. This review assesses terminal evidence and does not self-approve a new repair. Later retries or protocol changes require their own versioned review and evidence; these failed attempts must stay retained.
