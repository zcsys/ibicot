# Exact old-day rejection discriminator

Independent QA correctly noted that the first passing test supplied an invalid source string while asserting only generic old-day rejection. The collision/event/reward assertions were valid; that one assertion did not isolate the rejection reason.

The sole test change now uses the actual old-day briefing source for unused slot1, asserts `support_account_day_mismatch`, and compares the entire returned state with the original post-collision state. The first passing test/logs/author verification remain intact. Four focused direct-core Dart cases and scoped analysis pass again. No production files changed. This addendum supersedes only the live test pin in the original author packet; it does not rewrite first-run evidence or accept a package.
