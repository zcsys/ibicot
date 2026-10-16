# Independent daily and automation integration review

QA reviewer: `/root/qa_release_native`. Product implementation/repair owner: director. Initial snapshot `6d131f25eb6761acfee835ee2e38520a4550a36a82fd57deab7bae0920babbf5`; repaired snapshot `c72586b4be58a033b99c3f541445ea31a914b6e54507009dd1eac7c8e529a261`. Both are stable host-source snapshots, distinct from the earlier exported native candidate.

**Five independent checks pass after two author repairs.** No expected result was relaxed. Source hashes, original failures and retests are retained in `daily-snapshot.json`, `daily-repair-snapshot.json`, `daily-findings.json`, `daily-independent.log` and `daily-independent-retest.log`.

| Check | Initial result | Independent retest |
|---|---|---|
| Reopen after clock rollback, then cross the next actual account midnight | QA-006 P2: daily calendar anchor rewound despite preserved settlement cursor; next three contracts delayed | Pass: calendar refresh uses at least the accepted settlement boundary; day advances and six contracts are retained |
| Claim a completed daily contract, persist through actual repository, reopen and attempt another claim | Pass | Pass: exactly 10 Notes and 250 XP, second claim rejected |
| Return after 90 days and submit an expired contract command | Pass | Pass: backlog capped at 21, slots within seven-day window, no expired reward or duplicate slot |
| Open an imported valid 90-second automation plan and save without edits | QA-007 P2: display rounding changed the rule to 120 seconds | Pass: editor uses exact integer seconds; 90 seconds remain 90 |
| Contract reroll at 320-pixel width and 200% text | Pass | Pass: one reroll recorded and no layout exception |

The reusable non-author tests are `game/qa/daily_review_test.dart`; they run against a copied app and its actual core/repository, not a simplified fake economic model. These results establish the tested controller and view behavior. They do not complete native daily rollover, all target screen-reader/input checks, paid-pass delivery, service authority, notifications, long-term balance or the original human daily-habit gates.

The full scope audit remains open on those requirements. A new native candidate must include the repaired source before it can inherit either repair result.

Full repaired host snapshot regression also passed: core 160/160 with clean analysis, and mobile 40/40 (35 supplied tests plus the five independent tests). Mobile analysis findings are recorded separately in `current-mobile.log`; analysis must not be called clean if any finding remains. These source results do not qualify a later or earlier native export.
