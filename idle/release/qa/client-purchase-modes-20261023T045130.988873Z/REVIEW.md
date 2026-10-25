# Independent S04 purchase-control review

**Pass; no blocking finding.** The new actual-mode UI evidence closes the identified control-connection gap. Together with the exact current arithmetic bridge and accepted producer-art evidence, it supports a lead decision to verify original S04's local functional requirement. This report changes no scope, package status or acceptance prerequisite and does not establish native, physical-device, retention, accessibility-wide or release acceptance.

Original S04: “Single, milestone and maximum purchase controls and whole-tier 2x milestones at 25/50/75/100.” Original verification: “Bulk/max spending cannot overspend; tier output and displayed transformation agree.” Original linked packages remain M1-02, M1-05 and M3-09; all are accepted at their own recorded criteria. The complete unmodified scope record is retained in `scope-and-evidence-chain.json`.

## Exact review and execution

Reviewed root-authored test SHA-256 `e770614a09fa9517fcf9d59f49617e6a19d85885787cc9fc8c9804e7c629cc36`; author verification SHA-256 `e2a2200f4000d9333766bb2e5b4de98f57cca1f5d402bc7cff1a45a0c11f6971`. The author ran all 16 cases successfully and a scoped analyzer; I inspected those logs and all assertions. I independently executed exactly these four cases, selected by an anchored exact-name regular expression:

| Reproduced case | Count transition | Spend, micro-R | Wallet afterward, micro-R | Rendered stage |
|---|---|---:|---:|---:|
| single | 24→25 | 455358868 | 0 | 1 |
| milestone100 | 98→100 | 4234706712538 | 0 | 4 |
| max-tier0-exact | 23→26 | 1371931218 | 0 | 1 |
| max-tier 4-one-micro-short | 23→25 | 137908685747765 | 81600309151884 | 1 |

All four passed. Their original test assertions verify the production state and rendered painter fields; the amounts in this table were separately recomputed with Python rational sums. In the tier 4 one-micro-short case, the residual 81600309151884 is exactly one micro-R below the next price 81600309151885. The independently executed command and complete log are retained. All six source pins remained unchanged before/after. No other Flutter suite or device command was run, and the lane was explicitly returned to native_verifier immediately after terminal completion.

The initial author selector failure is preserved in its own evidence. The exact correction wraps the already computed price in the production complete Radiance label, retaining the independent price arithmetic and all other action/state/art assertions. `author-selector-correction.diff` records that change; the shared production sources were not edited.

## Actual implementation and test connection

The app's real SegmentedButton selects the controller's single/milestone/maximum mode. The producer card reads that mode's quantity and full price, then its real FilledButton invokes the normal purchase coordinator. The test reaches those real controls through `ContentProbe.checkControl` and `tester.tap`, with fatal hit-test warnings, whole-control bounds, named semantics and five hit points. It does not call a controller mode setter or purchase callback directly. Even the single-mode case first selects maximum, then selects single through its real control.

The rational oracle iteratively sums the original 30-R base and 20× tier steps with 28/25 price growth, then takes differences of rounded cumulative costs. It does not call the engine's geometric closed form. Full producer-count vectors, exact wallet subtraction, nonnegative balance, unchanged lifetime/Charts/Notes, and independently summed unboosted output are asserted. Initial Charts and bonuses are absent so this isolates tier/milestone behavior; synergy and prestige remain covered by their separate mathematical evidence. Maximum purchases additionally exhaust affordability, disable the real button and leave complete economic JSON unchanged when tapped again. Mode changes and disabled initial purchases also preserve complete economic JSON.

The author cases cross all four milestones and exercise exact/one-micro-short maximum budgets for all five tiers. Rendered `StagedProducerArt` count/tier and the actual `ProducerStagePainter` stage must agree with the post-purchase count. The independent output oracle doubles the whole owned tier at 25/50/75/100, capped at stage 4; it does not award the multiplier only to the new buildings. The production implementation and painter selection match that rule.

## Existing evidence retained

All eight current core inputs match the repaired transition/numeric bridge, including current engine `0fbc3f3dfbb54df8a0cef41a8b8c788baef473d0bbffe643301a3d9c9d9eade6`. That bridge preserves the existing 62 exact numeric rows and 15,365 assertions at the current core pin; no obsolete cache-era result is promoted.

The previous independent producer/contact-sheet, actual 25-stage matrix and later M3-09 recommendation remain the art basis. I additionally rehashed 103 producer-related source/export/renderer/provenance entries from the later current asset review; all match current files. This is version reconciliation, not a newly executed art matrix. M1-05's independently reviewed actual wallet/output and milestone-purchase shell checks remain separate context. The new tests supply their missing genuine single/milestone/max control connection, rather than repeating those full numeric/art/layout suites.

This review covers seeded host UI at the named default phone condition and the exact reviewed code. No human pacing, physical input, native frame budget, provider purchase, new asset approval, or store-completion claim is inferred. Ordinary read-only pins, referenced review hashes and exact original S04 are retained in the evidence chain. Only this new review directory was written.
