# Staged localization control-bound assertions

Ready for lead inspection and exclusive Flutter execution. The live mobile test has not been edited. Apply `localization-control-bounds.patch` only to base SHA `d301261ca00f97ad4fe9a7eedcba9b4fd8d2a388ceaefea1689fbb63e199f262`, or copy the adjacent staged `localization_test.dart` after confirming that base. `git apply --check` passed. The current 11 widget interactions and one pure-template test remain byte-identical from the existing `Finder key` declaration onward; no reward, secret, purchase, consent or gameplay assertion changed.

The helper now resolves labels/tooltips to the nearest actual Material action: ButtonStyleButton, IconButton, ListTile, NavigationDestination, chip, Switch or Checkbox. ExpansionTile/CheckboxListTile/SwitchListTile keys resolve to the header/action ListTile, not their entire expanded content. An unknown tap target fails instead of silently becoming a container-sized touch target. Noninteractive recovery-code reveal remains a reveal, without pretending it is a button.

Before tapping, the actual action must have width and height at least 48 logical pixels. Its complete global rectangle must lie inside the screen intersected with every ancestor scroll viewport and actual ancestor paint clip, allowing only 0.5px layout rounding. Center-only visibility cannot satisfy these bounds. Center and four inset edge hit tests must reach the actual action. Its semantics must have a nonempty accessible label and tap action. A semantics handle is enabled for every existing display fixture and disposed at teardown. The scroll/reveal alignment uses the action rather than its label. Disabled controls that are only revealed still have their bounds checked; tapping continues to require an enabled semantic action.

No Flutter/analyzer/widget/native run was performed in this lane. The direct pinned Dart formatter passed after replacing an attempted while-pattern syntax with an ordinary nullable RenderObject ancestor loop; the initial formatter diagnostic is preserved. Host behavior is unqualified until the lead installs and runs it. The full-bounds assertions deliberately may reveal genuine layouts that the previous center tap missed; do not loosen them to fit those layouts.

Run the existing same test file for each phone/tablet × 100/150/200 × English/pseudo combination through the lead's source-pinned runner:

```
../../tool/flutter test test/localization_test.dart \
  --dart-define=TIDEGLASS_TEST_VIEWPORT=phone \
  --dart-define=TIDEGLASS_TEST_TEXT_PERCENT=200 \
  --dart-define=TIDEGLASS_PSEUDO=true
```

No new copies of the 11 critical interactions were added. Expected per combination: 11 widget tests plus one pure test; 12 display/mode combinations total. Physical touch and actual OS screen-reader behavior remain separate external checks.

## Separate current-runtime lint delta review

`current-runtime-lint-only.diff` records the staged harness `99d961e87b100ade13dc3ddda2be059a28b3e75fa979bc5b5a9ef0df598cd50f` against installed harness `40c885f740a17695ffcce62e90d1f8dea3da4f54949d40c4b47c51c5e94a571a`. I inspected all three hunks: the intentional native checkpoint print has an explanatory `avoid_print` ignore; two cache loops gained braces. Marker contents, control flow and assertions are unchanged. Root's separate `root-current-runtime-analyze-20261021T130030.476507Z/verification.json` reports analyzer exit 0 with no source differences. This is a static delta review and existing-log inspection, not native execution or acceptance of the pending runtime scenarios.
