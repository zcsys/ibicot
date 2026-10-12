# Phase-specific seller history

Status: experimental read-only collector for the [value-model work](buying-behavior-v2-value-model.md). It does not estimate latent demand, change purchasing, or adopt forecast parameters. D1/D2 remain the [accepted contract](buying-behavior-contract-decisions.md).

## Information and timing

Each seller column uses a stable numeric identity, product and owner. Quotes and opening inventory are frozen at phase entry; each sampled buyer records live stock and its stock-unconstrained funded quantity at that quote before its own transaction. Closing inventory and posted sales must reconcile. The collector retains these channels separately:

| Channel | Opening snapshot | Closing snapshot | Seller identity |
| --- | --- | --- | --- |
| `t0-wholesale` | After extraction, before refinery purchases | After refinery purchases, before refinery production/pricing | Extractor × raw element |
| `retail` | Before Distributor clearing | After clearing, before manufacturing | Active manufacturer line |
| `input-C{complexity}` | Actual input book at that complexity's entry | Book immediately before settlement | Refinery product slot or manufacturer line |

The input book excludes new output produced within its own phase; the next complexity's book can include it. Observing the book before settlement preserves this distinction. No terminal world-stock snapshot is substituted for a phase observation. Product mappings use raw-element indices for T0 and refined-product indices followed by manufactured-product indices for other channels; the catalog identity guards interpretation. Owners in input books use the book's combined T1/T2 namespace.

## Fields and limits

For every phase/tick/seller, record quote, posted items sold, closing items in inventory, an offered mask, and three counts:

- `discoveries`: sampled offers seen by buyers, including offers with zero funded demand.
- `fundedChecks`: discoveries whose quote-funded quantity is positive.
- `shortChecks`: funded checks where live whole-lot stock is below that quantity.

Counts are observations, not incoming orders. Multiple buyers can check the same inventory. A short check is not causal lost sales: another supplier, fee or resource constraint may determine the purchase. For wholesale comparisons, stock is rounded down to the configured whole lot. Distributor demand has no stored-cash limit in the current model.

Zero realized sales is measured even without discovery; zero discovery supplies no evidence of zero latent demand. A nonoffered seller has an unavailable quote (`NaN`), zero sales/checks, and may still hold inventory. New columns have nonoffered historical rows, never fabricated past quotes. The collector does not alter reliability or pricing counters.

## Retention and persistence

`SellerHistory(window)` retains the latest `window` observations separately for every channel. The window must be explicitly chosen; zero disables collection in the engine/runner. There is no adopted forecast window. It is currently available only when both industrial tiers use the isolated experimental treatment.

A single exclusive NPZ sidecar contains arrays plus version, catalog identity, window and per-channel tick/cursor/lot metadata. Load rejects incompatible schemas/catalogs, unexpected channels, stale checkpoint ticks, invalid arrays, and corrupt ring coverage. It never overwrites an existing artifact. Appending stable lines is supported; deleting/reassigning existing seller identities or changing lots requires an explicit history reset/migration. History is not yet part of the production checkpoint schema. Experimental forecast adapters consume its lagged publications; production purchasing does not.

The experimental runner accepts `--seller-history-window N`, records the choice in provenance, and saves `seller-history-TICK.npz` at each existing purchase-record flush. These are rolling windows ending at the named tick, not complete interval recordings; do not combine overlapping files by summation. The final sidecar can be loaded with the checkpoint's tick and expected channel set. The runner does not yet expose a resume CLI.

Storage scales with active seller columns × retained ticks. Numeric arrays use float64 quotes/quantities, uint32 stored counts, uint8 masks, and int64 identities/ticks; transient counters use uint64. Full-population memory, recording overhead and timing still require measurement before choosing a window or enabling a forecast.

## Verification scope

`test_buying_v2_seller_history.py` covers phase distinction, zero/unobserved cases, ring wrap, append-only identities, invalid-input rejection, exclusive persistence, corruption rejection and exact continuation. `test_buying_v2_seller_history_world.py` compares reference and compiled histories with a history-disabled control, covers C3/C4 and line addition, reconciles posted sales, and reloads history between ticks. These are implementation checks, not forecast calibration or long-run adoption evidence.
