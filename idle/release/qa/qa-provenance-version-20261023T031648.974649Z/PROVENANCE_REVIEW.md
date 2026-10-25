# Independent provenance version and existence review

**Recommend integrating the exact34 proposed provenance records as source-version bookkeeping.** The previously applied37 existence-only contract updates also match their reviewed proposals exactly. No live file was edited and no Flutter/device execution occurred during this review.

`review.py` is an independently written read-only reconciliation. It passes3,087 checks and eight deliberately altered in-memory records, retained in `probe.json`, `checks.json` and `probe.log`. These counts are metadata assertions, not game tests.

- Exactly34 canonical records have42 historical source-hash bindings across App, StoryScreen, SeasonScreen and `services/docs/PRIVACY.md`. Every old source is present at the recorded hash in its original historical location and the new explicit archive. Every new archived source matches the current live bytes. Recomputing each unified diff reproduces the exact supplied patch.
- Each proposed JSON differs only at its declared source hashes plus `author_source_version_update_20261023`. Removing that field and restoring those hashes reconstructs the original JSON exactly. All IDs, lists of required variants, exports, rights/authorship declarations, historical capture fields, reviewer/null approvals and production acceptance are preserved. The original provenance backup is byte-identical to the canonical before record.
- All164 asset records were scanned; there is no omitted source mismatch or unsolicited proposal. All297 declared export bindings still match their original bytes. All1,077 files in the prior frozen handoff retain their declared hashes, and the handoff itself matches the new proposal's pin. Historical capture evidence paths/hashes remain valid.
- Eight counterexamples—approval grant, reviewer replacement, extra variant, dropped capture, changed export, invented native qualification, omitted binding and changed ID—are rejected by the independent structural checker.
- Reapplying the original37 JSON-pointer proposals to the preserved old production contract reproduces both the prepared contract and the current canonical contract exactly. Each old whole-record digest and stable ID matches the prior independently reviewed packet; each source/export descriptor exists. The only changed fields are `status: in_production`, `source_exists: true`, and `export_exists: true`. No verification, variant, rights, reviewer or acceptance field changes.

## Evidence version relationships

`cross_reference.py`/`cross-reference.json` recheck the relevant actual records and archived source endpoints without rerunning their matrices:

| Source | Evidence relationship |
|---|---|
| StoryScreen13c917f5… | Matches the independently adopted12-condition content matrix after the large-text heading repair. That matrix remains876 tests/1,644 rows for its actual scope. |
| SeasonScreencaed42e2… | Matches both that content matrix and the independent season/localization repair source. |
| App620908e8… | The prior whole-App c26efd… is preserved. The independently reviewed reset version b5cb9918… is the exact daily-icon promotion baseline, whose new App matches the proposal. The current12-condition targeted daily evidence and root's two independent conditions/combined reset are separately pinned. No prior capture is relabeled as this App. |
| PRIVACY.md30e01d26… | The exact two-paragraph native study-context documentation delta and preserved previous version match the separately reviewed documentation bridge. This is an engineering inventory, with consent/native study limits retained. |

The appended record explicitly says no new PNG was rendered, no whole asset was approved and no combined current native qualification occurred. Those limits are appropriate. Source-to-provenance correspondence does not itself approve old PNGs at a new version, complete164 asset variants, establish public rights or qualify native imports.

## Separate status cross-reference observation

All eight `original_artist_work_items` still say `not_started`; their original statuses were intentionally preserved by the37 existence-only updates. The separately authoritative program already records accepted/in-progress work. `status-cross-reference-observation.json` captures the exact current pairings. An explicit program-status cross-reference would clarify this duplication at the final scope gate. It should identify package progress as a separate dimension and retain per-asset variants, verification and rights/approval fields unchanged. This recommendation does not authorize silently converting any asset or work-item criterion to accepted. No reconciliation was applied here.
