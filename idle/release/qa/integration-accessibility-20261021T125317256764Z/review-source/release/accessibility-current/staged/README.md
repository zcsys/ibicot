# Staged calibration and critical-flow accessibility qualification

Scope: M5-02 / M3-04, S02 / S09 / S17 / S26. Status: **authored, not executed**. All changes remain under this staging directory; no production source or current mobile test was edited. The lead owns the exclusive Flutter lane and must copy/run these after the current source freeze.

## Calibration matrix

`calibration_accessibility_matrix_test.dart` registers 144 widget cases per build: all 12 actual patterns × phone 320×720 / tablet 1024×768 × 100/150/200% text × normal/reduced motion. Every case mounts the full 12-pattern selector and exercises:

1. A new pattern: solve via actual star controls with Undo and Restart, then claim; independently choose the crew completion from the same starting state.
2. An already earned pattern: repeat both routes from a state created by the real core completion command; verify the visible earned marker and no duplicate collectible.
3. No stored Focus: both reward controls stay disabled before and after solving, while the entire route, Undo and Restart remain usable. Core/story state and save-call count remain unchanged.

The first two compare **every core field, every story field and the captured persisted session**, including the exact settlement cursor. They also explicitly assert one charge consumed, 600 seconds queued, 20% active production, one discovery sequence, retained collectible set and unchanged wallet/lifetime/Charts/Notes/pass XP/fleet. Disabled controls cannot dispatch a second reward. This is the real `GameController.completeCalibration` path with the real loaded story catalogue, not a callback-only reward mock.

Starting states come from six hours of actual core advancement, a fixed initialized account seed, a real prior completion, and a real all-charge activation for practice. Core JSON round trips validate the earned fixtures. The graph solver reads nodes and edges, not the authored solution. A fixed clock and stopped ticker keep exact comparisons valid.

All selected chips, star choices, Undo, Restart and both completion controls are scrolled into view, checked against the viewport, hit-tested, checked for minimum 48×48 logical-pixel bounds and named semantics. Buttons must expose a tap action exactly when enabled. The diagram has an image description. Successful claims visibly update the earned marker. Both MediaQuery text scaling and reduced-motion input are asserted to be active. The calibration painter is static, so this does not claim animated behavior.

On execution, the suite emits `calibration-matrix.json` to the configured report directory. Expected coverage is 432 state rows per language mode (864 across both). Rows are appended only after their assertions and unmount checks succeed. Matrix row count **and test process exit status** are both required; partial rows do not establish completion. Source/content hashes and exact before/after state digests accompany the rows.

## Minimal existing-suite parameterization

`localization-display-parameterization.patch` changes only the existing `localization_test.dart` viewport helper and one formerly fixed-200% test name. It adds:

- `TIDEGLASS_TEST_VIEWPORT=phone|tablet`
- `TIDEGLASS_TEST_TEXT_PERCENT=100|150|200`

The defaults remain phone/200%, unsupported values fail, and all 11 widget interactions plus the pure template test remain unchanged. This reuses the existing purchase, Rechart, return/settings, calibration, campaign/dossier, season/pass, account, store-price, Support/automation, notification and actual bootstrap checks. There is no duplicate interaction suite. Existing reduced-motion settings in these critical flows are preserved; normal/reduced motion coverage belongs to the new calibration matrix and the separately authored art/app matrix.

## Lead-only integration and execution

First check the staged source hashes against `stage-evidence.json`. Apply the patch only if its recorded base hash still matches. From the repository's `idle` directory:

```sh
cp release/accessibility-current/staged/calibration_accessibility_matrix_test.dart game/mobile/test/calibration_accessibility_matrix_test.dart
patch -p1 < release/accessibility-current/staged/localization-display-parameterization.patch
```

From `game/mobile`, run sequentially, preserving logs and source pins:

```sh
../../tool/flutter test test/calibration_accessibility_matrix_test.dart --reporter=expanded --timeout=120s --dart-define=TIDEGLASS_ACCESSIBILITY_REPORT_DIR=../../release/accessibility-current/calibration-english
../../tool/flutter test test/calibration_accessibility_matrix_test.dart --reporter=expanded --timeout=120s --dart-define=TIDEGLASS_PSEUDO=true --dart-define=TIDEGLASS_ACCESSIBILITY_REPORT_DIR=../../release/accessibility-current/calibration-pseudo
```

Run the existing localization suite once for each of the six viewport/scale combinations, then repeat with `--dart-define=TIDEGLASS_PSEUDO=true`. Example:

```sh
../../tool/flutter test test/localization_test.dart --reporter=expanded --timeout=120s --dart-define=TIDEGLASS_TEST_VIEWPORT=tablet --dart-define=TIDEGLASS_TEST_TEXT_PERCENT=150
```

The 12 critical-flow runs are 132 widget invocations plus 12 repeated pure-template checks. Run the mobile analyzer after staging. Investigate any actual overflow, unavailable semantics or small target before production changes; do not remove assertions to obtain a pass. The 120-second limit applies to each test, not an assumption about total runtime.

## Checks already performed and limits

I read the requested calibration, localization, help and study suites plus the production APIs. The direct Dart formatter accepted the new test syntax. `patch --dry-run -p1` accepted the parameterization against its recorded current base. A separate Python graph traversal found a valid all-node route for every current pattern without using the authored solutions. Exact input and staged hashes are in `stage-evidence.json`.

**No Flutter test, analyzer, emulator or native build was run in this lane. There are no runtime pass claims or confirmed production defects yet.** The staged suite needs compilation and execution by the lead, followed by independent inspection. These host fixtures do not establish human pacing, natural unlock timing, real file/cloud durability, physical screen-reader announcements, real touch reachability, device rendering/performance, or original v1 acceptance. Physical VoiceOver/TalkBack, touch and human-comprehension checks remain explicit external obligations.
