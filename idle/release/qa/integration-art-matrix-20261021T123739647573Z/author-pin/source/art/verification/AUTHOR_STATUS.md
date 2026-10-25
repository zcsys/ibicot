# Author status: both full matrices passed; independent review pending

The active test is frozen at SHA-256 `b918a61005548a0d31fc155732f5b0ef3b02f474218ad32cc5efffa4556573e4` (`game/mobile/test/art_catalogue_variants_test.dart`) and the evidence checker at `d770eb41d3aa9556053eb30e6b55547e707cb0b7799f405e4aa5a1ab63898443`. The English full run passed on the previous exact test `716c13defe491390c8eeee92e5f8921433629bb79b6386318027812902a0c1d0`. Its source archive and results remain unchanged. The lead agent executed both full matrices through the exclusive Flutter lane; both passed with clean analyzers and no source drift. No original gate is promoted by these author checks.

## Actual execution history

| Platform evidence | Observed result | Meaning |
|---|---|---|
| `release/native-proof/root-art-lifecycle-20261021T114719.496224Z` | Lifecycle test passed; analyzer reported one deprecated semantics API | Actual pause/resume/reduced-motion/disposal behavior passed on the earlier frozen test. The analyzer issue was repaired in the owned test. This bundle is not a clean full run. |
| `release/native-proof/root-art-phone-sample-20261021T115102.916252Z` | Analyzer clean; one of four representative tests passed | Harbor assertions emitted seven rows but failed leaked SemanticsHandle cleanup. Producer/cosmetic setup failed the existing wallet≤lifetime guard. Selected/locked component test passed. Four core files also changed during execution, so this bundle has no consistent runtime snapshot. |
| Historical `913fc783…` repair | Repairs authored before subsequent sample | In-body try/finally disposes semantics before test completion. Both seeded wallets now have matching lifetime income. Actual harbor/producer/purchase rectangles are compared across equip/remove/re-equip. |
| `release/native-proof/root-art-sample-20261021T121345.799157Z` | Analyzer clean; three of four representative groups passed; zero source drift | Harbor, all producer cards and selected/locked component cases passed on `913fc783…`. Cosmetic fixture created a store offer for a free item and correctly failed the offer constructor. No runtime defect established. |
| Historical `d6958638…` repair | Paid-offer fixture repaired before subsequent sample | Construct the explicit synthetic offer only for paid IDs; omit it for free items and guard the purchase branch by actual non-null offer. Complete remaining cosmetic flow inspected against current runtime constructors and callbacks. |
| `release/native-proof/root-art-sample-20261021T121819.056028Z` | Three groups passed; cosmetic chapter-3 seed triggered real discovery normalization at first equip | Direct story seeding left daily discovery availability stale. The existing equality check caught revision/discovery refresh. An analyzer null-aware element info also remained. |
| Historical `716c13de…` repair | Fixture normalization before owned baseline | The public `equipCosmetic(null)` path normalizes ownership/discovery; a repeat clear must be core-state-idempotent. All later economic comparisons retain every field. Null-aware offer syntax fixed. |
| `release/native-proof/root-art-sample-20261021T121948.772875Z` | Clean analyzer, four representative groups passed, zero drift | 68 behavioral rows; checker passed against 524 frozen inputs. |
| `release/native-proof/root-art-full-20261021T122040.006324Z` | Clean analyzer, all 50 tests passed in 2m37s, zero drift | 816 rows: 84 harbor, 300 producer, 432 cosmetic; full supplements; checker passed against 524 frozen inputs. Report SHA-256 `717e94848f53ad47fbfe1355e2228144e309bee7cf1a921bcb33477d49d47b91`. |
| Active `b918a610…` extension | Actual runtime pseudo selectors and mode attribution added | Schema 2 records en-US/qps-ploc with the actual `Presentation.pseudoEnabled` flag; the checker binds that to the executed define. No runtime edit. |
| `release/native-proof/root-art-pseudo-sample-20261021T122435.459880Z` | Clean analyzer, four representative groups passed, zero drift | 68 qps-ploc rows; updated checker passed executed-define/report-mode binding. |
| `release/native-proof/root-art-pseudo-full-20261021T122636.246158Z` | Clean analyzer, all 50 tests passed in 2m18s, zero drift | 816 qps-ploc rows; full checker passed against 524 frozen inputs. Report SHA-256 `d132e5e2862b280e885acf870a78267d98b117fa1deef705a9dab2b09aa187f2`. |

The read-only evidence checker correctly rejects the failed earlier bundles as acceptance evidence. Their logs and results remain unchanged; emitted rows alone do not establish a passed test.

## Independent review handoff

Both full runs are complete. `release/art/catalogue-variants/AUTHOR_REPORT.md` summarizes observed coverage, preserved failures and the remaining original obligations. `per-id-evidence.json` links every ID to both exact reports. Run `python3 source/art/verification/build_handoff.py` to repeat both full evidence checks and reproduce that author index. The only cross-run source changes were the test and checker; all production inputs are identical.

Preserve `source-before.json`, frozen source copies under `source/`, command/exits/log hashes, `source_differences`, the absolute report directory and `art_report_sha256` in the platform proof. Run `source/art/verification/check_matrix.py <matrix-results.json> --proof <platform-proof-dir> --full` only for the successful unfiltered run. A different agent must review the actual sources and evidence. No canonical verification, original variant, rights, physical, native or program gate is promoted by this harness.

The parallel local public-page review is separately complete in `release/public-pages/INDEPENDENT_REVIEW.md` and JSON. Its only concrete finding, JPEG captures mislabeled as PNG, was corrected by the author and independently verified with unchanged bytes in `rename-followup-probe.json`.

The applied pseudolocale extension uses the actual `--dart-define=TIDEGLASS_PSEUDO=true` presentation boundary, qualifies displayed text with `Presentation.text`/`Presentation.authored` as appropriate, and emits exact English versus pseudo conditions. It does not rewrite the English run or treat synthetic labels as runtime content. Staging history is retained under `staged-pseudo/`. The updated checker also revalidated the unchanged full English evidence; `release/art/catalogue-variants/english-author-check.json` records that check.
