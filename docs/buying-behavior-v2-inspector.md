# Recorded buying-decision inspector

Status: read-only inspection of completed experimental recordings. This is not a live policy selector or production dashboard integration. It displays actual archived data and does not start, reset or mutate an economy.

## Build and inspect

Use the launcher's compatible Python interpreter and a fresh output file:

```sh
PYTHONPATH=.pydeps:. "$ECONOMY_PY" -m tools.buying_v2.inspection_report RUN_DIRECTORY --output REPORT.html
```

The builder requires a complete recorded window, passing accounting invariants, compatible purchasing aggregates, consecutive trace files, consistent phase coverage and matching tick/seed identities. It replays every captured industrial and Distributor decision before emitting a standalone HTML file. Embedded JSON escapes script delimiters; labels use DOM text nodes. Output creation is exclusive. Source-run identity, verifier hashes and trace hashes remain embedded for attribution. Neither successful replay nor an accounting gate proves economic suitability or adoption readiness.

`web/buying-inspector.html` and `web/buying-inspector.js` define the presentation. Tier, tick, outcome and exact buyer-ID filters operate on sampled entries; pagination bounds displayed rows. The detail panel distinguishes hypothetical quote quantities, actual requests, purchased goods, formula fees and fees actually paid. Inactive and unobserved entries show explanatory missing-data states, not fabricated zero balances. T1 supplier IDs are company indices; T2 uses input-book indices; T3 uses production-line indices.

Complete-window industrial totals are separate from the sample filters. They use archived product labels, summed quantities/payments and explicit fee-incidence denominators. Undefined rates and uninstrumented rows display “—”. The report makes no unique-demand, per-company-average or sample-prevalence claim. Tables scroll horizontally at narrow widths.

The export control prepares full-precision JSON with source identity, source window, buyer/phase identities and sampling metadata. It exposes the content in a read-only text area for copying and supplies a download link. Filtering clears a stale prepared export. File downloading was not confirmed in the in-app browser: both download observation attempts timed out. Visible JSON generation and its filtered contents were verified; do not describe the file-download path as tested successfully.

## Preserved rendered evidence

The verified artifact is `stats/buying-implementation/20261012-buying-inspector/verified.html`, built from `20261012-all-buyer-traces-fullpop-137`, seed 137, ticks 1–30. It contains 120 phase documents, 3,840 sampled entries and 2,037 captured decisions. Earlier build iterations remain separate files.

Actual browser inspection covered the normal narrow layout and the desktop grid, tier/tick/outcome/buyer filtering, forward/back pagination, inactive and unobserved rows, empty results, recorded purchases and stockout attempts. A narrow-screen overflow was corrected. Screenshots are preserved as `inspector-verified.jpg` and `inspector-narrow.jpg`; browser error logs were empty.

The displayed Distributor example is buyer 274660 at tick 30: 18 items bought for $130.86 from line 5149; line 5113 had no opening stock, so the $1.3434 formula fee was waived and preference changed to the whole-demand supplier. The inspector also showed buyer 180910's positive request with zero purchases. These are recorded examples, not inferred causes from end-of-tick stock.

`rendered-totals-proof.json` verifies every cell in all 54 industrial market rows against the recorded-window projection at displayed precision, including all 30 undefined fee ratios. The displayed JSON export for T3/captured/tick-30 contains precisely buyers 180910, 274660 and 493410.

Two Python tests cover missing/duplicate/wrong-tick evidence, failed accounting gates, exclusive output and embedded-script escaping. The JavaScript projection checks cover filtering, coupled quantities, missing values, empty offers and bounded export structure; syntax checks also pass. These are targeted checks, not the full economy suite.

Remaining work: live runtime/projection/control integration, larger-window report scale, external-browser download confirmation, and the master plan's unresolved industrial-model, performance, economic and rollout gates.
