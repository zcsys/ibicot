# Market pricing and purchasing validation

2 October 2026. Historical validation, superseded by the
[scarcity-aware repair](scarcity-aware-repair.md). This superseded the earlier
cost-and-stock pricing repair. The measurements below describe that earlier
implementation, including its 12.9% T2 break-even concentration.

Transactions now occur at competing posted offers. No shared ideal price,
prescribed established markup, or consumer-derived seller ceiling sets prices.
Sellers experiment with small price changes and compare their own realized
gross profit. Consumers' value scales are independent of production costs.
Manufacturers derive input orders from recipes, observed downstream orders,
held inventories, cash and the profitability of complete production batches.

The selected building blocks come from derivative-following pricing,
comparison shopping and order-up-to inventory control. The
[research notes](../spec/pricing_research.md) identify the primary papers,
alternatives, adaptations and limitations. The
[economic contract](../spec/economy_contract.md) specifies equations, information
sets, transaction order, stockouts, switching and accounting.

## Price competition and stockouts

Consumers compare five sampled posted offers plus a previous successful supplier.
A cheaper discovered offer attracts buyers when switching friction does not
outweigh the saving. If that seller cannot fill the order, consumers try their
other discovered offers. Unfilled need remains unmet if none can serve it.
Businesses compare stocked input offers and retain cash, lot and recipe limits.

Attempted orders, including stockout refusals, feed the contacted seller's
inventory forecast. Actual sales have a separate EMA. A failed search does not
give every seller knowledge of that consumer's demand. Local attempts across
several sellers can exceed aggregate needs; fulfilled/unmet consumer totals
count each consumer once.

The isolated consumer-clearing comparison used identical preferences and random
streams, 1,000 firms, 20,000 consumers and 60 clearing phases. Inventory was
replenished by the fixture to isolate purchasing, not to test production.

| Chosen product line | Units sold | Units requested locally | Gross profit |
| --- | ---: | ---: | ---: |
| Ordinary offer, 1.5 × cost | 50 | 50 | $165.00 |
| Cheaper offer, 1.2 × cost | 245 | 267 | $323.40 |
| Same cheaper offer, no stock | 0 | 201 | $0.00 |

Other sellers continued fulfilling orders when the cheap seller was empty.
Some needs stayed unmet because search is bounded. Underpricing is not a
guarantee of higher profit: quantity, capacity and margin all matter.

A separate full-population paired production test warmed identical economies
for 120 ticks, then compared company 5 under BOT control with ordinary PLAYER
control for 180 ticks. The player refreshed offers every 30 ticks to 8% below
observed market-average offers, subject to the same cost constraint. It received
no additional cash, equipment, stock, production or customers. BOT sold 385
units and earned $392.06 gross profit; PLAYER sold 1,053 and earned $650.14,
a 65.83% profit improvement in this scenario.

## Full-population results

Both runs used the actual worker kernel, 50,000 T2 firms, 125,000 installed
lines and 1,000,000 consumers, for 3,600 ticks. The table shows the final
360-tick window. All 134 markets traded in that window; all material and final
markets continued producing and trading throughout the recorded windows.

| Metric | Seed 12345 | Seed 31415 |
| --- | ---: | ---: |
| Consumer desired-unit fulfillment | 99.9204% | 99.9198% |
| T2 firms trading in the window | 49,999 / 50,000 | 49,992 / 50,000 |
| T2 installed-capacity utilization | 19.5924% | 19.5869% |
| T2 finished stock / realized units sold per tick | 4.701 ticks | 4.682 ticks |
| T2 realized gross margin | 1.1707% | 1.1635% |
| Maximum cumulative cash-ledger residual | $0.000362 | $0.000493 |
| T0 traded units at variable cost | 0% | 0% |
| T1 traded units at variable cost | 4.7863% | 5.7273% |
| T2 traded units at variable cost | 12.8982% | 12.9067% |
| T2 traded units within 1% of variable cost | 53.5445% | 53.7742% |

There are no seller price ceilings. Exact break-even trades occurred in nine
of ten T1 markets and all 120 T2 markets. These results **do not satisfy a
requirement that no market ever trades at a floor**. The remaining boundary
covers variable costs, rather than the old guaranteed positive markup. The
learner attempts upward moves after a downward experiment reaches this boundary;
competition can bring it back. QA records this concentration rather than
forcing profitable margins to eliminate it.

Thin margins are consistent with homogeneous competing suppliers, substantial
spare capacity and the absence of recurring fixed expenses. These tests do not
establish that this is an empirically realistic long-run industrial structure.
The economy still has external unlimited-consumer-cash injections and excludes
labor, rent, depreciation and financing. Local profit experiments are noisy
and can cycle; no equilibrium or global optimum is guaranteed.

## Reproducible quality assurance

`node tests/economy_quality.js` runs 15 contract/behavior/UI tests and two
full-population 3,600-tick audits. `--quick` omits the two long runs. Checks
cover accounting, stock bounds, tier boundaries, reporting, Run/Run Max,
independent preferences, cost/demand/capacity responses, missed orders,
complete recipes, supply outages/recovery, actual undercuts and player control.
The existing utilization, participation and stock-coverage checks remain.

This validation ran the 15 checks together and the two long runs concurrently
as separate processes. All 17 passed their stated checks. A forecast-variable
correction in the inventory-limit fixture was rerun successfully afterward;
the economic sources did not change. The combined
[manifest](market-learning-quality-full.json) records source SHA-256 hashes,
execution arrangement and raw logs. Per-market price and rolling-window data:
[seed 12345](market-learning-12345-3600.json) and
[seed 31415](market-learning-31415-3600.json).

Browser verification initialized the full population, stepped, ran at maximum
throughput, switched back to normal Run, and paused at tick 71. The updated
parameters and overview rendered without captured console errors or warnings.
The overview compares all producing tiers and counts final consumer spending
once. [Verified dashboard screenshot](market-learning-browser.png).
