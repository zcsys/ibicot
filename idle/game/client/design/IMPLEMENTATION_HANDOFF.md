# Client implementation handoff — 16 October 2026

Author: client/accessibility implementation agent. Independent native/controller reviewer: platform agent. Director owns `lib/main.dart`, `lib/bootstrap.dart` and persistence; no edits to those files were made by this agent.

## Delivered production slice

- `game/mobile/lib/app.dart`: responsive native Harbor, Atlas and Logbook. All five producer controls, single/milestone/max buying, exact-core purchase eligibility, base marginal network output, conditional forecasts, permanent-power preview, deliberate Rechart confirmation, optional automatic buying, offline-return presentation, Focus/Survey controls, settings, export/import entry points and recovery notice.
- `game_controller.dart`: immutable core command dispatch, lifecycle settlement, serial persistence queue, surfaced write failure/retry, exact real-time cursor callback. No currency math in presentation. Director's bootstrap binds real `SaveRepository` and native application-support storage.
- `palette.dart`, `harbor_art.dart`: original moonlit ocean/lighthouse and five reusable vector producer silhouettes, living waves and constellation links, saved/system reduced-motion handling. `representative-art.json` records the honest asset scope.
- `strings.dart`: shared English copy plus 67 extracted static UI phrases. Dynamic message templates, pseudolocalization and complete launch translation infrastructure remain open.
- Onboarding dismissal now scrolls the first purchase into view. Selected navigation uses a legible color. Singular lightkeeper copy is fixed.
- Corrected an actual return-dialog exit crash: immutable return data is captured before acknowledgement clears the controller report. Rechart lists retained timers, Notes and automation settings as well as Charts/lifetime progress.

## Verification performed

Commands run from `game/mobile` with the pinned project Flutter/Dart wrappers:

- `../../tool/flutter analyze`: passed before the subsequent standalone calibration component; final combined lint is owned by the next integration gate.
- `../../tool/flutter test test/client_test.dart`: **15 passed**, including core purchase, locked controls, Rechart cancellation/confirmation, exact persistence cursor, write failure/retry, serialized saves, lifecycle duplicate-resume defense, actual offline-dialog acknowledgement, first-purchase scrolling, labeled/minimum-size tap targets and 320/1024 logical-pixel layouts at 200% text.
- `../../tool/flutter test test/bootstrap_test.dart`: **4 passed** against actual temporary-file saves. Covers core/preferences reopen, one corrupt slot recovery, preservation of two corrupt slots, and explicit import replacing a branch while preserving readable previous progression.
- `../../tool/flutter test test/calibration_test.dart test/client_test.dart`: **27 passed** at that checkpoint (14 calibration + then-13 client checks); the subsequent two client regressions were verified in the 15-check run above.
- Actual native iPhone/iPad captures produced by the platform engineer: `release/native-proof/client-phone.png`, `client-tablet.png`. Both were viewed and found clean. Captures precede the navigation-color, singular-copy and first-purchase-scroll repairs; fresh native evidence is required for the integrated candidate.

A missing test cleanup produced a SemanticsHandle test failure and was repaired. A mistaken test expectation about the save envelope nesting and recovery archive location was repaired after reading actual storage output. These were test defects; the return-dialog failure and Material ink assertion were real client defects, repaired and rechecked.

## Calibration component (not yet integrated)

The 12 final authored patterns are copied into `game/mobile/assets/calibrations/`; pubspec registers the directory. `calibration_pattern.dart` strictly parses the rules and provides untimed graph traversal. `calibration_screen.dart` offers next-star buttons, undo/restart, collected markers, a normal route and a crew-completion button. Both completion paths call the exact same command callback. One Focus is charged only by the core when a reward is accepted. Practice with zero Focus remains possible.

The 14 tests independently find routes through all twelve graphs without consulting the supplied solution, verify traversal/undo/restart, prove both UI completion paths dispatch the same pattern ID once, and forbid claims with no stored Focus.

**The component is not reachable from the current Logbook yet.** Director instructed the client to hold wiring while the daily core API changes and native candidate testing runs. Next integration: replace direct Focus activation with `CalibrationScreen`, using `engine.completeCalibration(state, patternId)` for both routes; bind `completedCalibrationIds`; retest real collectible/bonus equality, persistence and reachable native UI. Existing `activate-focus` key currently triggers direct Focus activation and its interaction test must change with that integration.

## Independent progression review

The director's `game/progression` 21 tests were reproduced successfully. Source review and `game/client/design/progression_review.dart` separately reproduced four validation defects: unknown construction modes accepted; invalid chapter identity accepted; invalid completion prefix accepted by the direct constructor; nested campaign maps mutable. Director repaired them. The independent probe was expanded to twelve checks and all twelve pass, including actual Note spending, free replay, revision changes and replacement protection. See `release/progression-review.md`. Re-run the probe with:

```
.tooling/flutter/bin/cache/dart-sdk/bin/dart --packages=game/progression/.dart_tool/package_config.json game/client/design/progression_review.dart
```

All twelve booleans are true in `game/client/design/progression_review_result.json`. Current `tool/dart` wrapper adds a flag incompatible with this VM `--packages` invocation, so this probe uses the pinned SDK directly.

The initial dossier test name mentioned persistent 100-Note entry but only validated the catalog. Director added the purchase/owned-dossier ledger transaction and tests; independent probes verify the transaction rules. Do not interpret reachable challenge simulations as proof of a complete main-game entry/payment flow.

## Remaining acceptance limits

This work does not complete v1. It does not prove final seven harbor/25 producer presentations, campaign/challenge integration, all 36 cosmetics, audio, commerce, cloud recovery, complete daily/seasonal systems, pseudolocalization, physical VoiceOver/TalkBack behavior, native device performance or real human comprehension/retention. Native simulator screenshots are not physical-device acceptance. No manifest production item was marked complete merely because a widget or fixture passed.

## Ownership transfer and next integration

At the director's request, ownership of `game/mobile/lib/game_controller.dart` and `app.dart` is handed to `/root` for daily/progression integration while this specialist is idle. Director already owns bootstrap/main. Platform owns native project files and `integration_test/platform_smoke_test.dart`. No further client edits are running.

Stable UI constructors:

```
TideglassApp({required GameController controller,
  ClientPreferences initialPreferences = const ClientPreferences(),
  Future<void> Function(ClientPreferences)? onPreferencesChanged,
  Future<String> Function()? onExport,
  Future<void> Function(String)? onImport,
  String? recoveryNotice})

GameController({GameState? initialState, DateTime? settledThrough,
  Future<void> Function(GameState, DateTime)? onPersist,
  TideglassEngine engine = const TideglassEngine(),
  bool startTicker = true, DateTime Function()? clock})

CalibrationScreen({required List<CalibrationPattern> patterns,
  required int Function() focusCharges,
  required Set<String> Function() collectedIds,
  required bool Function(String patternId) onComplete})
```

`loadCalibrationPatterns()` loads all twelve assets. Build the screen inside a `ListenableBuilder(listenable: controller, ...)` so stored Focus changes remain observable while it is open. Both normal and accessible completion must call the same `completeCalibration` core command. Current route state and `claimed` prevent accidental second-click completion; the core remains authoritative for replay IDs, Focus and collectible deduplication.

Next UI priorities: initialize daily contracts with a stable persisted seed/fixed day offset after offline settlement; wire actual calibration and its saved collectibles; then integrate the reviewed campaign/dossier runtime and atomic state bundle. Revisit first-session hierarchy after these additions rather than stacking every system into one long page. Preserve dialogs' captured return report and deliberate reset/replacement confirmation.
