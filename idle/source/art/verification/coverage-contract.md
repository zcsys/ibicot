# Catalogue variant verification boundary

The executable authority is `game/mobile/test/art_catalogue_variants_test.dart`. This work adds host widget evidence for the existing 68 registered visual IDs. It does not change art, inventory counts, economic behavior, original asset variants, rights records or canonical acceptance. Run results are recorded separately; this document is not a pass certificate.

## Matrix

| Existing asset group | IDs | Display conditions per ID | Expected behavioral rows |
|---|---:|---:|---:|
| Harbor: unrestored plus six restoration states | 7 | 12 | 84 |
| Five producers at five milestone stages | 25 | 12 | 300 |
| Chapter, decoration, free pass, premium pass and shop cosmetics | 36 | 12 | 432 |
| Total | 68 | 12 | 816 |

The twelve conditions per presentation mode cross 320×720 phone and 1024×768 tablet logical viewports, 100/150/200% linear text scaling, and normal/reduced motion. These are deterministic host viewports, not claims about physical devices. The harness now supports English (`en-US`, default) and expanded pseudolocale (`qps-ploc`, actual `TIDEGLASS_PSEUDO=true` compile-time define). Each run has 816 rows; actual passing run status belongs in the author report. Pseudolocale is a stress presentation, not a shipped translation or complete original variant acceptance.

Harbor cases use the actual `TideglassApp` and exact campaign restoration prefix, check actual renderer state and image semantics, and observe whether decorative animation changes or remains static. Producer cases use actual purchase cards, exact renderer tier/stage, adjacent names, reachable semantic purchase buttons with at least 48×48 logical-pixel boxes, and unchanged core state. Initially unavailable producers must show a lock icon and requirement text with no purchase button.

Cosmetic cases use the actual `CosmeticsScreen`, full preview dialog, ownership/equip callback and actual app harbor. Each ID passes locked → owned → equipped. Paid ownership is an explicit in-memory verifier fixture; invoking the purchase callback alone must not grant ownership. Free pass appearance ownership uses the existing free reward claim, while chapter/decoration ownership is seeded. Presentation and equip must leave the complete economic state unchanged relative to their ownership fixture. Actual harbor, five producer card and first purchase button rectangles must remain identical when the item is removed and re-equipped. The same ID is checked at each consumer. Equipped status is expressed as text, not color alone.

The 160-pixel cosmetic thumbnail is the real `CosmeticPreview` component in a labeled test scaffold. The product does not currently expose a separate thumbnail route. The extra 600 producer selected/locked combinations also use the real renderer in a labeled component scaffold. High-stage locked saves and a selected-producer product route are not asserted to be reachable. These fixtures cover rendering branches without inventing product flows or production semantics.

## Supplemental checks

The actual app is dispatched through inactive, hidden, paused and resumed lifecycle states, then OS reduced motion and disposal. The test checks animation phase changes/stops and zero retained transient callbacks after unmounting. It uses a fixed synthetic clock and does not measure platform power use, real interruption timing, long-session memory, or native device scheduling.

Declared opaque foreground/background text pairs and the actual build button color composite are checked against 4.5:1. [WCAG 2.2 contrast minimum](https://www.w3.org/TR/WCAG22/#contrast-minimum) specifies 4.5:1 for normal text and 3:1 for large text, subject to its exceptions. [Non-text contrast](https://www.w3.org/TR/WCAG22/#non-text-contrast) specifies 3:1 for relevant UI/graphical boundaries against adjacent colors, with exceptions. This matrix does not assert every composited pixel, focus indicator, border, icon or decorative illustration has received a full contrast audit. Decorative artwork and disabled components are not silently treated as required text pairs. Palette calculations do not certify WCAG conformance, native screen readers or human readability.

## Original scope relationship

| Original work | This evidence contributes | Still outside this host matrix |
|---|---|---|
| M1-07 / S04 | Real typography reflow and producer control states in selected routes | All slice routes; final font/distribution rights and native import qualification |
| M2-05 / S18 | Base silhouettes, complete first-family milestones and both motion settings | Physical visual quality, native performance and memory budgets |
| M3-09 / S19 | All 25 stage IDs, real initial locks, labeled component state variants | Daily-loop icon/status matrix and every queue/error state |
| M4-07 / S22–S23 | Seven harbors, 36 cosmetic identities, appearance/ownership consistency | Seasonal presentation coverage, audio packages, actual provider delivery, soundtrack rights/fulfillment |
| M5-02 / S26 | Scaled host layout, actionable semantics and hitbox checks on tested routes; same routes under the runtime pseudolocale when that run passes | Complete original localized variants, full native accessibility, screen-reader traversal and human/physical qualification |

No original required variant or acceptance gate is removed. Existing capture artifacts may support separate visual review but are not replaced by behavioral JSON. Static exports and current-source host tests are not frozen native candidate evidence.

## Execution and evidence integrity

The designated exclusive platform/release lane owner alone invokes Flutter. Each invocation uses a fresh absolute `TIDEGLASS_ART_REPORT_DIR`, captures commands/exits/log hashes and frozen input copies, and records any source drift. Filtered smoke runs intentionally emit an incomplete row set. A full-run report is only eligible for bounded host review when all 50 tests pass, all 816 unique ID/condition pairs are present, all supplemental conditions are present, and the evidence checker passes `--full` against that exact platform proof directory.

Schema 2 reports identify the presentation locale and actual pseudo boolean at report, condition and row levels, and prefix condition IDs by locale. The checker compares those fields to the executed Flutter define. Historical schema 1 English evidence is preserved unchanged and may only validate against a command without pseudo enabled. English and pseudo runs retain separate source pins, log/report hashes and directories. Exact selectors use the actual `Presentation.text`/`Presentation.authored` display boundary, while catalogue IDs and economic data remain unmodified. Synthetic component captions are visibly localized in their clearly labeled scaffolds, not claimed as production routes.

`check_matrix.py` reads the original contract IDs, actual test report and platform proof. It validates identity coverage, settings, required states, log hashes, frozen source hashes and successful command exits. It rejects filtered commands in full mode and never writes manifest, provenance or reviewer fields. Author checks require a different agent's review before any bounded review acknowledgement. Even that acknowledgement cannot imply external rights, commercial delivery or physical acceptance.
