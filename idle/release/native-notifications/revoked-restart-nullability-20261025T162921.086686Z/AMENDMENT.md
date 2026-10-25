# Nullable notification-ID projection

The native scoped analyzer rejected the sealed helper because `ActiveNotification.id` is nullable. This amendment changes exactly `.map((item) => item.id)` to `.map((item) => item.id!)` in `activeReminderIds`, after its existing `ReminderPlanner.ids.contains(item.id)` filter. The filter admits only the three non-null owned integer IDs, so the assertion expresses the established invariant and preserves the observed values.

The sealed original stage and failed analyzer evidence remain untouched. The runner, restart verifier and tests retain their original sealed bytes. No production source, live harness, Flutter or device operation changed. Native scoped analysis must rerun before promotion/execution. The original 43 host-test result is unchanged evidence for the original Python bytes; it is not a new Dart-analysis pass.
