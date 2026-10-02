# Economy pricing repair and quality assurance

Historical report: this prescribed-markup approach has been superseded by
[market pricing and purchasing](market-learning-repair.md). The results below
describe the earlier implementation, not the current economic rules.

Implemented one cost-and-stock pricing rule across T0, T1 and T2. Prices follow actual unit costs and the configured normal markup, with funded shortages and stock deficits/surpluses adjusting discretionary profit. Cost-plus floors remain; fixed dollar ceilings are removed. Consumer reservation multipliers affect willingness to pay only. Procurement, production and pricing use the same manufacturing stock target, including rounding and bootstrap inventory.

## Before and after

Actual transactions over ticks 3,241–3,600, default seed 12345.

| Measurement | Before | After |
|---|---:|---:|
| T1 C-2 units sold at floor | 99.99% | 0% |
| T1 C-2 units within 1% of floor | 100.00% | 0% |
| T2 units sold at floor | 48.82% | 0% |
| T2 units within 1% of floor | 99.93% | 0% |

## Full-population long runs

| Seed | Ticks | Trading markets | Floor volume | Within 1% of floor | T2 firms trading in last 360 ticks | T2 utilization | T2 realized gross margin |
|---|---:|---:|---:|---:|---:|---:|---:|
| 12345 | 3,600 | 134/134 | 0% | 0% | 48,287/50,000 | 18.34% | 19.94% |
| 31415 | 3,600 | 134/134 | 0% | 0% | 48,724/50,000 | 18.37% | 19.93% |

Each run contains 20 extractors, 1,000 material firms, 50,000 manufacturers and 1,000,000 consumers. All 134 markets traded in the measured window; all 120 final and 10 material markets continued producing and trading in each rolling 360-tick window. All desired consumer units were fulfilled in the final window. Latent zero-price demand remains price-sensitive and is not automatically fulfilled.

Cash conservation, finite/non-negative balances, inventory caps, positive manufacturing gross profit, stock coverage, and firm participation passed. Maximum cumulative cash-ledger residual: $0.000040. T0 throughput uses actual seller transfers rather than the delayed observations used by pricing.

## Repeatable quality gate

```sh
node tests/economy_quality.js
```

Runs 14 deterministic contract/scenario checks, then 3,600 ticks for each of two seeds. For contracts and shocks only, use `node tests/economy_quality.js --quick`. The 16 constituent checks passed. A later full command executes the same checks sequentially; the recorded long runs were executed concurrently.

Coverage includes cost scaling, steady rounded targets, surplus/shortage response, zero-sales stock, expensive intermediate goods, cost-shock floor recovery, exact procurement-phase attribution, failure detection, deterministic reset, cash transfers, inventory limits, takeover/equipment, scheduler equivalence, dashboard reconciliation, outages/recovery, demand elasticity, and ordinary player pricing.

The pricing gates examine traded volume separately in every market: zero exact-floor trades and less than 1% of units within 1% of the floor in the established default bot economy. They also reject inactive markets and implausible cost-relative prices. A player can deliberately set a cost-floor offer; that behavior is tested separately.

## Artifacts

- [Full gate results](economy-quality-full.json)
- [Seed 12345: financial windows and all 134 market audits](economy-quality-12345-3600.json)
- [Seed 31415: financial windows and all 134 market audits](economy-quality-31415-3600.json)
- [Original pricing audit](price-bound-audit-12345-3600.md)

The updated browser app was verified through Run Max, Run and Pause; charts updated without console errors. It is open and paused at tick 74.

These results validate the default model and the specified shocks. Granted starting equipment, unlimited consumer cash, and no recurring fixed costs remain explicit Phase 0 assumptions; the model does not claim empirical calibration of a real-world economy.
