# Content presentation verification — author stage

This is executable verification for uncovered **M3-09/M4-06/M4-07/M4-08**, bounded to **S18/S20/S21/S22/S27**. It does not change game content, balance, ownership authority, original variants, asset approval, program status or release gates. The author is the QA agent for this assignment; a different agent must review this suite and its reports.

The staged two-file Flutter suite mounts the actual production widgets and expects **73 cases / 137 ID-state rows per condition**. Conditions are phone 320×720 and tablet 1024×768, each at 100/150/200% system text, in English and actual compile-time pseudolocalization: **12 conditions, 876 invocations, 1,644 expected rows**. These are expectations, not executed evidence. Reduced animation is used for deterministic text observation; existing motion/calibration matrices are retained rather than duplicated.

| New observations | ID-state rows per condition | Real transitions and limits |
|---|---:|---|
| Six chapters current/completed, five later locked, ending | 18 | Persisted prefix fixtures; actual expansion and ending route pop. Does not replay campaign completion. |
| Eighteen main archive accounts locked/reflected | 36 | Actual reflection callback and one discovery-sequence increment; no direct currency/XP. Identity is bound by the real per-ID control and source; reflection content IDs are not a persistent ownership receipt. |
| Twelve dossier introductions/opened and final scenes | 24 | Actual confirmation spends exactly 100 Notes and owns the requested dossier; valid goal-complete fixtures present each distinct completion. No challenge pacing claim. |
| Twenty seasonal fragments locked/claimed | 40 | Zero-XP disabled claims, 15,000-XP earned fixture and actual free claim; exact fragment identity and duplicate rejection; main ledger unchanged. |
| Season upcoming/live/archived, resume/pause, pass/alternative prose | 6 | Actual schedule boundaries and archive callbacks. No hosted/live-ops claim. |
| Eight help articles | 8 | Actual index/article/index navigation, every section/paragraph, injected host callback spies and real license route. Internal privacy help is not the public-page asset. |
| Daily contract/storage states | 5 | Production assignment generator; pending reroll; seven-day 21-slot ready fixture, all actual claims, resulting empty state; queued Focus and three Surveys with actual 30-Note collection. |

`coverage-crosswalk.json` maps all **164 original IDs and unchanged required variants**. Exactly 62 narrative/support IDs receive new widget rows. The 68 existing visual IDs and 24 calibration visual/copy IDs retain their reviewed evidence. Five audio assets, one seasonal presentation asset, two public pages and two internal documents retain separate proof obligations. Do not infer missing files or missing all-asset verification from null canonical approval fields.

## Observation integrity

`content_presentation_probe.dart` reads the actual `RenderParagraph`, requires exact complete text and no exceeded lines, selects every non-whitespace UTF-16 range, unions their actual boxes per rendered line, scrolls that line into the actual clipped ancestor viewport, and records its global and visible rectangles. A long paragraph cannot pass simply because its first line exists. Flutter selection boxes include invisible trailing wrapping spaces; four executable helper counterexamples qualify excluding only those spaces, while clipped visible words and truncated paragraphs still fail. Every visible range must occur in the recorded line observations. All control measurements resolve actual Material controls; expansion panels are measured at their action header. The helper requires full visible control bounds, 48×48 minimum, five hit-test points, actual accessible label/tooltip and enabled tap semantics. Disabled controls must expose no tap action. Rows are emitted only after asserted transitions and contain complete before/after main+story ledgers and checksums.

`expected-rows.json` binds exact identities/states/routes, required fields/assertions and authored paragraphs. `check_content_report.py` rechecks geometry, every line observation, exact source-bound copy, callbacks, ledger deltas, case totals, unfiltered command/condition agreement, output hashes and immutable archived source hashes. It requires the Flutter JSON completion event and 73 successful non-hidden cases. Partial reports deliberately retain `complete:false`; the independent verification file is the only whole-condition result. The 26 synthetic checker cases establish checker behavior only.

## Execution

Only the lead may promote the two new test files into `game/mobile/test`; staged and installed bytes must match. Obtain the exclusive Flutter lane first. Do not edit production to silence a failing probe. Freeze and diagnose test-fixture failures separately from actual runtime/layout failures. Record original failures before repairs.

From the repository root, one full condition is:

```sh
python3 release/content-presentation/staged/tool/run_content_condition.py --root . --output release/content-presentation/run-phone-100-en --viewport phone --text-percent 100 --pseudo false
```

The runner creates a fresh output directory, snapshots production/data/test inputs, executes only this suite without name/tag filters, saves raw JSON events and report, checks source stability and invokes the checker. A lead-approved partial diagnostic should use a separate directory and must never be submitted as full-condition proof. Do not rerun all 12 conditions until the first author condition and different-author contract review are satisfactory.

No physical screen-reader traversal, real player comprehension, public hosting, store/provider fulfillment, rights approval, elapsed retention or finished-release acceptance is established here.

The pure source relationship checker currently checks 239 exact copy/bundle relations and hashes 510 referenced inputs. This is identity/provenance linkage only; it does not establish rendering, rights or publication. `content_presentation_helper_test.dart` is a separate four-case author helper qualification, outside the 73-case content matrix.
