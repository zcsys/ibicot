# Distributor decision traces

Status: optional observation in the isolated buying-v2 engine. This extends the [industrial trace contract](buying-behavior-v2-decision-traces.md) to the existing [Distributor buying model](buying-behavior-v2-retail-contract.md); it does not introduce industrial demand, change consumer demand, or adopt a new policy.

## Recorded boundary and units

The runner's `--trace-sample N` now selects up to N Distributor identities per tick in addition to each industrial phase. The same systematic hash-rotation algorithm uses tier 3 and phase 0. It consumes no simulation randomness and samples from all buyers, including inactive buyers. It is not a representative incidence estimator. The active-population lookup costs eight bytes per Distributor; detailed storage is bounded by N and six discovered offers. Default tracing remains off.

A Distributor document has schema 1 and kind `distributor-decision`. Each selected buyer is explicitly `inactive`, `zero-potential`, or `captured`. Inactive rows carry no invented demand or offer observations. Zero-potential rows identify the active buyer's rounded potential quantity without pretending a supplier search occurred. A captured row may have no offers, empty stock, a rejected basket, or actual purchases. These are distinct recorded outcomes.

The capture point is after selection and before settlement. Buyer inputs include stable buyer/product indices, latent item quantity, fixed rounding draw, half-price and elasticity, original incumbent line, incumbent-quote quantity, formula fee, chosen fee/preference, surplus and goods cost. Each offer contains its stable line index, unit quote, opening item stock, quantity at that quote, selected items and actual remaining request. No stored Distributor cash constraint is invented. Empty-stock attempts remain actual requests even with zero purchases; fee/valuation rejections do not create requests.

The order identity is `(tick, buyer, product)`. Supplier IDs are active T2 production-line indices, interpreted with the run's archived catalog and ownership. Surplus is the selection objective, not company earnings or a posted cash balance. The snapshot records a chosen basket, not independent proof of its settlement; world/accounting comparisons remain required.

## Persistence and reconstruction

The per-tick trace JSON list now contains the three existing industrial phase documents and the Distributor document. Historical industrial-only trace files remain valid; readers distinguish Distributor documents by `kind`. The manifest's trace byte count includes both collectors. Detailed arrays retain only the current tick; persistence writes every tick to an exclusive file in the fresh experiment directory.

`tools.buying_v2.retail_traces.verify_export` checks deterministic sample identities, activation and rounding roles, quote-sensitive quantities, incumbent bid, and a replay of the existing basket solver. Separate arithmetic checks cover remaining requests, available stock, goods payment, one-fee D2 settlement and D1 preference qualification. Replay is not an independent optimality proof; the existing exhaustive small-allocation solver tests remain necessary.

Connected tests compare Python and compiled retail paths, all world arrays and economic state against an uninstrumented compiled control. Diagnostic surplus permits a relative floating-point tolerance of 1e-12; allocations, quantities, requests, fees, preferences and world accounts require exact equality. Tests separately exercise inactive buyers, zero potential, no offers, empty-stock attempts and altered trace fields.

The controlled purchase fixture exposed NumPy scalar promotion in the Python inverse quantity calculation: float32 latent/elasticity arrays produced a different intermediate precision from native compiled arithmetic. The adapter now explicitly uses double precision for latent quantity and the inverse-curve exponent. This aligns the reference calculation; preserved-world comparisons must establish that the compiled economic trajectory remains unchanged. Failed fixture and precision-check logs are retained rather than overwritten.

The [recorded-data inspector](buying-behavior-v2-inspector.md) now provides rendered sample inspection. Remaining gates include production projection/control integration, mature-state overhead and memory measurements, and the master plan's economic and adoption checks.

## Preserved full-population evidence

`20261012-all-buyer-traces-fullpop-137` preserves seed 137, ticks 1–30, sample 32 per buyer tier/phase, and source identity `6b61b3b3ab0e864f44e5f3974b2dad359c1a5b3adfe82b15e998d0ab63d4d4c5`. The conservation gate passes. `all-buyer-trace-world-proof.json` confirms exact agreement of all 211 recorded arrays, checkpoint JSON, schemas/configuration and tick invariants with the preserved uninstrumented compiled run. Thus the explicit-precision correction and measurement hooks do not change that compiled trajectory.

All 30 trace files reconstruct. The industrial sample contains 1,926 captured plans and 954 explicitly unobserved callbacks. The Distributor sample contains 111 captured decisions and 849 inactive buyers; no zero-potential buyer occurs in this window, so that boundary is covered by the controlled test instead. These sample counts are diagnostics, not prevalence estimates. Detailed arrays, including membership lookups, use 9,432,320 bytes.

`retail-trace-final-tests.log` passes nine targeted tests in 42.771 seconds: connected retail traces, independent exhaustive retail-solver checks, and industrial traces including checkpoint continuation. Earlier failed fixture and precision checks remain in `retail-trace-tests.log`, `retail-trace-connected-tests.log` and `retail-trace-connected-v2-tests.log`. Failed expectations were investigated; no economic-result golden files were replaced.

`all-buyer-trace-overhead.json` records three alternating-order matched full-population pairs, seed 137, ticks 2–11 after warm-up, sample 32 for each industrial phase and Distributor clearing. Kernel medians increase by 2.86%, 5.32% and 5.17%; encoding both trace types takes median 1.08–1.28 ms. Every world array and economic runtime state matches each tick. Disk writing is excluded from the paired encoding measurement. This short startup screen does not establish mature-state tail latency or total process-memory limits, and it does not pass the master plan's total policy performance gate.
