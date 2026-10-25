# English externalization and pseudolocale author review

Date: 2026-10-19. Owner: client_native. Scope: M5-02; S02, S09, S17 and S26. Status: author implementation and host checks complete; independent QA/native acceptance remains separate.

## Delivered behavior

`strings.dart` holds English labels, sentences, accessibility announcements, error-facing copy and protected dynamic templates for the designated UI. Existing authored campaign/archive/dossier/season content and the 36-item cosmetic catalogue remain their own English content sources. Notification text remains in `notification_copy.dart`.

`--dart-define=TIDEGLASS_PSEUDO=true` activates the real presentation boundary, accents Latin vowels, adds approximately 35% expansion padding, and visibly marks strings. Dynamic templates expand surrounding copy before inserting values. Recovery material, exports, IDs, native store prices, numeric values and filesystem/environment identifiers remain exact. Authored prose is expanded only on display; saved state, gameplay assets, hashes, rules and authored source content are unchanged by the mode. The Tideglass proper-name heading is intentionally unmodified.

Large-text repairs include scrolling confirmation content/actions together, measuring/wrapping secondary headings, expanded harbor header/navigation space, and semantic/input labels using the same presentation helper. These repairs retain real controls and original economic commands. Replay failure messages, audio warnings, duration units and art semantics were also moved into the English catalogue. Diagnostic details themselves remain protected technical data.

The AST tool is now a read-only inventory command. It does not rewrite code. Manual audit specifically verified paths, environment keys, regex validation, widget keys, protocol identifiers, recovery/export values and dynamic prices. A real bootstrap regression opens the default native support directory, loads an existing audio preference file, updates it, writes an actual save, and proves the paths are identical in both build modes.

## Verification

| Check | Result | Evidence |
|---|---:|---|
| Complete mobile English suite | 255 passed | `localization-english-tests.log` |
| Actual pseudo critical flows and captures | 13 passed | `localization-pseudo-tests.log` |
| Mobile analyzer | No issues | `localization-analyze.log` |
| Narrow viewport / text scale | 320 logical px, 200% | Same two test suites; five captures per mode |
| Actual bootstrap path/preferences/save test | Pass in both modes | Included in both suites |
| Gameplay/bundled content verification | Included in full suite | English suite |

The 13 pseudo checks comprise template protection plus actual first purchase/navigation, Rechart cancel/confirm, offline return/settings, calibration completion, campaign/dossier purchase, season automation/free claim, account consent/recovery retention, a fixture native-price purchase callback, Support/automation, notification explicit opt-in/quiet time, actual filesystem bootstrap, and a production-widget capture test. The purchase/recovery fixtures are clearly local test adapters; they do not claim a store or cloud transaction.

Five reviewed host images per mode are in `release/localization-proof/`: harbor, Rechart, calibration, store-price and quiet-time. Captures use Flutter's bundled Roboto/MaterialIcons and real widgets, with seeded states where needed. The preview store price is a test fixture. Final pseudo images were inspected: headings wrap, formatted 1.0K/320 output remains intact, the USD 9.99 fixture remains exact, and long dialog/form content scrolls. Buttons below the captured viewport are exercised by interaction tests. Two former arrow glyphs now use plain English words/punctuation to avoid a host-font missing glyph in review images.

## Remaining literal inventory

The complete AST scan contains 7,464 literal occurrences. Its 1,606 English candidates comprise 698 occurrences in `strings.dart`, 79 in the cosmetic catalogue, 44 in notification copy, 766 vector-data values, and 19 technical candidates. `localization-remaining-literals.json` records each technical candidate and its disposition.

| Deliberate exclusion | Why it stays exact |
|---|---|
| Digest strings, vector hex values, regexes | Content integrity and validation data |
| K/M/B/T numeric suffixes | Protected number-format contract |
| UTC/GMT, notification copy-key composition | Scheduling/data identifiers |
| Pseudo algorithm alphabet/padding/font identifiers | Presentation engine inputs |
| Content-integrity and explicit-opt-in guard diagnostics | Technical diagnostics rather than authored player instructions |
| 68 diagnostic/pattern-classified AST occurrences | Includes serialized-data validation failures and regular expressions; retained for precise diagnostics |
| Native prices, user data, recovery/export material, protocol/asset keys and paths | Must never be translated or expanded |

No unmigrated prose candidate remains in the designated screen/announcement files after manual disposition. This is not a blanket claim that all exception text across every dependency has been externalized. Some technical diagnostics can appear inside a recovery/error detail; their surrounding player-facing instruction is externalized while detail stays exact. Future translations, RTL layout, localized plural rules and native OS permission-sheet language are outside this English/pseudo checkpoint.

## Scope and independent changes

No economic or notification-timing behavior was changed by this lane. The final shared source also includes root-owned telemetry lifecycle work, native-service updates, and the QA014 exhausted-dossier discovery fix; hashes include them so this evidence cannot be confused with the earlier native candidate. The Support test now centers the actual visible control before tapping after header expansion; it still invokes and verifies real shared-ledger commands. QA independently replaced an obsolete simulator-gap assertion with repaired parity expectations before the final full-suite pass.

Host widget tests do not establish VoiceOver/TalkBack quality, physical-device text rendering, keyboard/OS-sheet behavior, notification delivery, real store prices/purchases or native thermal/performance acceptance. The existing older immutable native build does not qualify this later localization source. A fresh pinned native build and independent review remain required.

## Reproduce

From `game/mobile`:

```sh
../../tool/flutter test --reporter expanded
../../tool/flutter test test/localization_test.dart test/localization_capture_test.dart --dart-define=TIDEGLASS_PSEUDO=true --reporter expanded
../../tool/flutter analyze
```

From the repository root, run the read-only AST inventory using the bundled analyzer configuration:

```sh
.tooling/flutter/bin/cache/dart-sdk/bin/dart --packages=.tooling/flutter/packages/flutter_tools/.dart_tool/package_config.json tool/localization_inventory.dart inventory game/mobile/lib/*.dart
```

`localization-author-evidence.json` records exact source/test/dependency and evidence hashes. Source ownership is released to the lead; later edits require a new evidence pin.
