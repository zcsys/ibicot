# Quiet-hour notification guarantee clarification

The current implementation supports opt-in quiet-hour **scheduling** with disclosed device delivery uncertainty. I do not find an explicit original dispatch-time blackout guarantee that would independently require a receiver rewrite. This is a bounded interpretation of the original wording, not evidence that no delayed notification can appear during quiet hours. M3-05 and S26 remain open for the separately identified Android runtime outcomes.

## Exact original wording

`TIDEGLASS_DESIGN.md:309` says notifications are opt-in, can be bundled, and “respect quiet hours.” Original M3-05 requires text scale, notation, motion/audio controls, input navigation and opt-in quiet-hour notifications to function across targets. S26 retains that notification requirement; its verification clause addresses large text, reduced motion, non-color cues and critical controls on named targets. None explicitly defines an absolute actual-dispatch exclusion, an exact alarm guarantee, or a requirement to bypass system delivery policy. No original criterion or dependency is changed by this clarification.

## What existing source and evidence establish

`notification_service.dart:173–229` rounds requested readiness forward, enforces a five-minute minimum, moves a due instant out of the chosen local quiet interval, handles overnight/DST windows by elapsed-minute scanning, groups due reminders, and bounds old plans. The actual Android quiet/cancel case independently reviewed in the sealed current reminder batch establishes a real pending plan at the quiet window's end and actual cancellation. It uses direct production lifecycle methods with synthetic Focus state; it does not itself demonstrate an actual OS background/return transition or eventual dispatch.

The real Settings screen binds the quiet-hour switch and editable bounds to persisted preferences and renders both relevant disclosures: `quietHint` says reminders falling in quiet hours wait until the interval ends; `bounded` says the device may delay or suppress delivery; `zoneHint` says the plan uses the device time zone when leaving and refreshes on return/settings changes. See `notification_copy.dart:31–48` and `notification_settings.dart:112–150`. Thus the supported behavior is a requested schedule outside the chosen quiet interval using the disclosed planning time zone. The current native adapter requests silent, low-importance Android notifications and silent iOS reminders; silence does not imply absence from the notification list.

## Explicit limit and disposition

The Android adapter uses `inexactAllowWhileIdle`. Installed flutter_local_notifications 22.3.2 calls `setAndAllowWhileIdle`, and its `ScheduledNotificationReceiver.onReceive` posts the persisted notification when dispatched without consulting Tideglass quiet-hour preferences. A due time just before quiet hours can therefore, in principle, be delivered after quiet hours begin. No such event was observed in the failed 18:55 local delivery run; that run had no active matching delivered record before cancellation and remains failed.

The phrase “respect quiet hours” is broad, so final product documentation and acceptance must preserve this scheduling-versus-dispatch distinction. Existing delay/suppression and planning-zone disclosures support the bounded scheduling interpretation; they do not establish an absolute display blackout. I recommend treating the already proven quiet-hour scheduling/control subclause as supported within that disclosed contract, without introducing an unrequested absolute-dispatch or physical-device gate. If the director chooses an absolute actual-display policy, that would require a deliberate implementation and verification decision; this report neither silently assumes it nor declares it implemented.

There is no newly observed production defect or specific conflict with an explicit original dispatch-time requirement. This clarification does not accept the whole package/scope, waive actual Android delivery/revocation outcomes, amend the original wording, or replace the director's product decision. Preserve all failed attempts and use fresh terminal native evidence for remaining outcomes.

## Review provenance

This is a read-only exact-clause/source review. The reviewer previously authored some verification probes; their separate root reviews remain their code approvals. No production receiver, preference, UI copy, economic source, canonical metadata or sealed earlier evidence was modified. No runtime, device, Flutter or network tests were executed for this clarification. Existing native and Settings evidence is reused through its sealed hashes.
