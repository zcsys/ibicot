# Independent controller/persistence review

Reviewed the real Flutter controller and application bootstrap against the native persistence package on 16 October 2026. This is a code and regression review, not a physical-device acceptance record.

A fractional-second cursor bug was found: the controller advanced production through a microsecond timestamp, while serialization truncated that cursor to whole seconds. Reopening could credit the discarded fraction again. The persistence owner repaired timestamp serialization, validation and cursor-rewind protection. The independent regression now passes for a 1.750123-second boundary and reload at the identical clock time.

Three independent checks pass in `controller_review_test.dart`, recorded in `controller-review-test.log`: fractional save/reload is exact; 48 hours suspended grants the specified 30-hour effective offline credit once and does not run online ticks; a failed write followed by retry saves the current state and cursor together. Application bootstrap separately uses the strict client envelope, durable replay before presentation, and preserves damaged/incompatible files for recovery.

Native process termination/relaunch and UI purchase/reset verification are tracked separately. In-memory controller tests do not by themselves prove those platform boundaries.
