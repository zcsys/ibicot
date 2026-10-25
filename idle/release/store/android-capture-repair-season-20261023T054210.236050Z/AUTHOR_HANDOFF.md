# Capture repair — season readiness addendum

The three exact staged files are ready for the lead's different-author review. No live file has been promoted. The recorder and driver are byte-identical to the prior reviewed stage. This addendum changes the gallery harness only and deliberately strengthens capture readiness on both Android and iOS. Dart formatting/scoped analysis and actual native qualification remain pending the native lane.

## Evidence and diagnosis

The preserved tablet run `release/native-proof/integration-ios-tablet-20261023T052742.168623Z` passed its technical native verifier, but its `ios-tablet-capture-season.png` visibly contains the Logbook. That filename is not proof of seasonal content. The previous native run and all four images remain unchanged. The first Android failure and its overlong, sparse video likewise remain intact.

Inspection of the production `_openSeason` implementation shows an immediate `Navigator.push` of `SeasonScreen`; soundtrack start is unawaited. The existing tap helper already calls `pumpNativeUi`. Thus an omitted pump is not an established cause, and no production navigation defect is claimed here. The prior capture script did not verify the returning route or the destination route before accepting a screenshot. Route readiness is the concrete missing guard; the exact timing of the original failed tap has not been proved.

## Exact addendum

After returning from the chapter/challenge route, the harness waits at most four seconds for the unique real `open-season` control, ensures that control is visible, and waits at most four seconds for its current route to have completed its primary animation and dismissed its secondary animation. The landmark must also be hit-testable. It then performs exactly one ordinary hit-tested tap through the existing helper.

Before the seasonal screenshot, it waits at most four seconds for the actual `SeasonScreen` descendant `season-tab-0` landmark on the current settled route, asserts the screen and hit-testable selected Fleet ChoiceChip, and records the landmark, route animation state and actual gameplay elapsed milliseconds. No tap retry, callback invocation, fixed extra delay or screenshot substitution is added. A wrong route now fails with evidence rather than silently acquiring a mislabeled still.

The actual real-time stopwatch and 4/8/14/20/25-second action schedule are unchanged; all readiness waiting counts naturally. The 15–30-second raw video gate and the stage-one exact recorder PID/start/argv checks remain unchanged. The 27-second Android recorder ceiling still needs native observation: if startup and actual UI waits overrun it, that failure must be preserved, not accepted by relaxing the gate.

`season-addendum.patch` is the prior-stage-to-current harness diff. `complete-capture.patch` is the complete three-file live-baseline-to-staged diff. `staged-pins.json` is the promotion contract, including exact expected live-before hashes. Only its three staged source files are candidates for promotion.

## Validation and limits

The unchanged recorder passed 36 authored pure-Python orchestration tests in the prior stage and the lead independently reproduced all 36 in `release/qa/lead-capture-repair-20261023T053647.917618Z/reproduced-host-tests.log`. Those results cover the exact recorder bytes retained here; they do not qualify the new Dart route guard or actual native footage. No new Flutter/Dart/mobile/device/adb command was run for this addendum, and no new synthetic source-string test is presented as native proof.

The preservation pass rehashed all 28 addendum baseline files (including the 16 tablet native files), all 15 first Android gallery files, and all 23 sealed prior-stage evidence files. All match. The three live baseline files remain unchanged; current `before`, `prior-stage`, and `staged` hashes match their contracts. Both unchanged tooling files match stage one exactly, and regenerating the full unified diff from the snapshots matches `complete-capture.patch` exactly. Details are in `preservation-checks.json`.

The native verifier must run scoped Dart formatting/analysis after coordinated promotion and report any resulting new hash. A fresh Android gallery must demonstrate continuous actual production display, expected purchase/route changes, four matching raw stills, absence of test pointer paint, valid real endpoints, and the unchanged duration gate. A fresh iOS seasonal capture must show the actual Season screen. No release scope, current store creative or store/public approval is accepted by this author handoff.

Source writes are stopped. The prior stage and this addendum are preserved separately; future repairs must not rewrite this evidence.
