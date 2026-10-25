# Client accessibility layout author handoff

The strengthened critical-flow helper and bounded season/reminder layout repairs are complete at this source pin. All twelve requested host display/language conditions pass. The Flutter lane was explicitly released to the lead after the final command. No further source edit is planned.

This is author evidence for M5-02 / S02, S09, S17 and S26; it is not an acceptance-status edit, a substitute for independent review, or physical-device accessibility qualification.

## Actual repaired behavior

1. The season automation explanation and notification permission explanation now occupy full-width scroll content before their titled SwitchListTile. The whole titled row remains the same toggle action with its existing key and callback. Long explanations no longer make that action too tall to fit the visible body.
2. At text scales above 150%, the season page's full heading moves into the scrolling body with header/named-route semantics, while the AppBar retains navigation. This follows the previously reviewed calibration pattern. No title is truncated or scaled down.
3. The full reward title remains in the pass ExpansionTile header. Its status icon and collection/XP text now sit in a separate row above it, giving the actionable title more horizontal space. The actual key, expansion, free claim, premium ownership display and original full-title selectors are preserved. This additional defect became observable only after the toggle was reachable.

No economic rule, reward amount, clock, permission timing, entitlement, content catalogue, key or callback changed. No new dependency or UI string was added. The source diffs and preserved action/key checks are retained alongside this report; presence checks support source inspection and are not represented as a formal behavioral proof.

## Helper repair and retained assertions

The helper resolves actual Material controls rather than their text/icon labels. SwitchListTile/CheckboxListTile use the SDK's genuinely tappable, merged-semantic ListTile; standalone Switch/Checkbox still measure themselves. ExpansionTile uses its actual header, never the entire expanded panel. The SDK's default `testWidgets` semantics lifetime is used, avoiding a second handle disposed too late.

Every tapped action must be at least 48×48 logical pixels, fully inside the intersection of screen bounds, every ancestor scroll viewport and paint clip (0.5px rounding tolerance), hit-testable at center and four inset edges, and expose a real semantic tap action and nonempty label or tooltip name. The pinned SDK exposes IconButton text through SemanticsData.tooltip. Arbitrary widget text does not substitute for semantics. These assertions were retained through every product repair.

All 11 original critical interaction callbacks and the pure template test remain unchanged except the explicitly approved stale bootstrap-directory assertion: it now expects exactly the unordered harbor directory and separately implemented soundtrack-export cache directory, checks that the cache is empty, and retains exact save/audio path assertions. Arbitrary additional or pseudolocalized paths do not pass.

## Executed checks

| Language | Viewport | Text scale | Result |
| --- | --- | --- | --- |
| English | phone | 100% | 12/12 |
| English | phone | 150% | 12/12 |
| English | phone | 200% | 12/12 |
| English | tablet | 100% | 12/12 |
| English | tablet | 150% | 12/12 |
| English | tablet | 200% | 12/12 |
| Pseudo | phone | 100% | 12/12 |
| Pseudo | phone | 150% | 12/12 |
| Pseudo | phone | 200% | 12/12 |
| Pseudo | tablet | 100% | 12/12 |
| Pseudo | tablet | 150% | 12/12 |
| Pseudo | tablet | 200% | 12/12 |

Phone means 320×720 logical pixels; tablet means 1024×768. Each condition runs the same 11 widget interactions plus one pure template test. The full matrix therefore contains 144 test invocations (132 widget invocations and 12 pure invocations), not144 distinct test definitions. Both phone 200% representatives also passed 12/12 before the full matrix. The unchanged existing season/reminder UI suites passed 17/17 afterward. Analyzer passed. Across representatives, matrix and targeted checks, 185 test invocations passed; repeated checks are explicitly included in that count.

The interactions cover actual first purchase/navigation, Rechart cancellation/confirmation, return acknowledgement/settings, calibration completion, campaign/dossier opening, isolated seasonal automation/free reward, cloud consent/recovery-code retention, localized native-price display, Support briefing/automation plan, reminder opt-in/time selection, and actual bootstrap/save/audio paths. Fixture account/store/permission adapters remain fixtures; these tests do not claim real-provider acceptance. Protected numbers, prices, codes and identifiers remain exact.

Every command records its precise arguments, exit, count, log hash and before/after source comparison in `verification.json`; no command saw source drift. Source copies are in `source/`. `run_author_matrix.py` is captured and reproducible, but must only run while holding the exclusive Flutter lane.

## Preserved failures and repair history

- `release/qa/client-localization-bounds-20261021T130624611979Z`: initial installed helper, 8 pass / 4 fail in each mode, plus one redundant-import lint. Composite/name resolution and the known cache-path assertion were corrected; the failures were not discarded.
- `release/qa/client-localization-bounds-repaired-20261021T130858259423Z`: corrected helper, 10 pass / 2 fail each mode; analyzer clean. Both over-tall toggle controls were measured and remained failures.
- `release/qa/client-localization-layout-20261021T131440556436Z`: explanation move made English 12 pass; pseudo 11 pass / 1 fail exposed the fixed season header consuming 342px of vertical space. Full matrix was correctly not started.
- `release/qa/client-localization-layout-final-20261021T131636586972Z`: scrolling the season heading made the toggle reachable, exposing a different over-tall pass expansion header; English 12 pass, pseudo 11 pass / 1 fail. Full matrix again did not start.
- This final pin moves pass status outside that header and passes all representative/full/targeted checks without loosening assertions.

The original unrun staged helper 81c79d... and metadata remain in `release/accessibility-current/staged/localization-control-bounds/initial-stage/`. QA separately inspected helper 74a51e... and reported no static helper defect; final production review remains the independent reviewer's decision.

## Exact final pins and limits

- `game/mobile/lib/season_screen.dart`: `caed42e2bf64a32e501034822a5982bc53e9879035cd37059896b2665e495ff9`.
- `game/mobile/lib/notification_settings.dart`: `f135edc13f54379f32d87aef22e1f028d2320bc147b4307b0002cd087bf857be`.
- `game/mobile/test/localization_test.dart`: `74a51e160d15c2e13cf7716a2b9555b46fa996c1e89a9672f0ccba244c2d4b0f`.

These are Flutter host-widget results at the stated logical sizes/scales and English/pseudo modes. They do not establish actual VoiceOver/TalkBack delivery, physical touch ergonomics, OS keyboard variations, all screen combinations, native performance, translated-language quality or public-release readiness. Reduced motion was not a separate dimension of this twelve-condition run. The separately executed calibration/art matrices and original remaining acceptance requirements retain their own evidence and limits.
