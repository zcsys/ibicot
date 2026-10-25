# Midnight and Rechart collision — author handoff

The new `game/core/test/qa_midnight_rechart_test.dart` covers the exact missing M3-10 reset/day-boundary collision with four production-core cases: UTC offsets 0/+180 minutes, online/offline. No production code changed.

At account midnight, the synthetic fixture aligns the 600-second automatic Rechart threshold, Focus and Support expiry, a Focus generation, and Survey completion. It verifies all six events at the same exact microsecond in the documented order, five new Charts, reset wallet/counts, retained lifetime earnings and previously claimed Notes/XP, expiration of the old Support token, rejection of duplicate or old-day claims, and exactly one new Survey reward. Whole two-second advance equals a split at 999,999 microseconds plus one microsecond plus one second, excluding revision/event identifiers. Zero-duration replay produces no new events.

The expected pre-boundary income uses the explicit 1.45 Focus-plus-Support factor. Online midnight contracts snapshot the pre-reset rate; offline return contracts snapshot the post-reset rate. The test deliberately checks this difference. The initial state/time is synthetic, not elapsed-calendar, device clock, native lifecycle, human, or real season evidence.

Author validation: direct pinned Dart (core-only; no Flutter/device commands) ran the four named tests successfully and the scoped analyzer reports no issues. The first shell launch used a wrong relative output path and failed before Dart ran; `launch-path-error.txt` preserves that launch error. The corrected absolute-path invocation passed on its first actual test execution. No test assertions or production code were changed after that execution.

Independent review must inspect the fixture and real event order, reproduce the four tests using direct core Dart only, and decide what exact original M3-10 clause this adds. It does not itself accept M3-10 or other packages/dependencies. Existing evidence and original criteria remain necessary.
