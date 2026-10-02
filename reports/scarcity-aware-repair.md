# Scarcity-aware pricing validation

2 October 2026. Supersedes [the previous pricing validation](market-learning-repair.md).

Positive margins are not required by the model. No quality, location, service,
minimum positive markup, shared ideal price or seller ceiling was introduced.
The existing cost reservation remains. Buyers still compare actual offers;
undercuts, switching friction, stock availability, cash and complete recipes
determine actual transactions. Default demand and capacity parameters are unchanged.

## What was wrong and what changed

The earlier learner used fixed price steps and realized profit. A step could
jump across a narrow profitable interval, land on cost, and repeat this cycle.
Also, when every business supplier was empty, supplier selection returned no
supplier. Affordable input requests disappeared before reaching any seller.
The seller could not distinguish absent demand from demand it could not serve.

Business buyers now contact a known eligible posted supplier even when all
eligible suppliers are empty. Only affordable quantities enter that supplier's
requested-demand observation. Failed inquiries do not transfer goods or cash,
and do not establish a successful supplier relationship. Stocked offers remain
preferred for actual procurement.

Each seller compares received requests with units delivered plus its closing
inventory over its observation window. Excess requests prompt an upward price
experiment, including when the seller has no stock or sales. Otherwise, it
continues or reverses its experiment using realized total gross profit. Price
experiments shrink on reversals and grow on a consistent direction. This gives
the learner finer resolution without enforcing a positive margin or a target
price. Each seller observes its own orders and inventory, not a global demand
curve. Local attempts can exceed aggregate needs when buyers try several sellers.

The [economic contract](../spec/economy_contract.md) gives the exact rules.
[Research notes](../spec/pricing_research.md) document derivative-following,
excess-demand pricing and the adaptations; this is not an exact implementation
of either published algorithm or a guarantee of optimal pricing.

## Controlled tests

These use the actual worker kernel with matched random streams, except the
explicit synthetic price-learning fixture. Scenario values are diagnostic
changes, not new defaults.

| Comparison | Result |
| --- | --- |
| Empty input suppliers; zero starting markups; funded requests | Sum of 40 T0 quotes rises from 40 to 41.2937 after 120 ticks |
| Identical empty suppliers; buyers cannot afford requests | No received requests; the same quote sum remains 40 |
| Operating economy; extraction halted versus normal supply | T0 mean posted quotes finish 3.803% higher with constrained supply |
| Extraction restored | 550,200 T0 units trade over the next 120 ticks |
| Same T2 workshops; consumer activation 0.1 versus 1 | Mean posted quote rises from 9.0367 to 10.1940; mean quote minus held-stock unit cost rises from 2.0422 to 3.3921 |
| Synthetic cost 10, value 10.1; known best quote 10.05 | Mean profit in the last 100 observations is 0.249811 versus optimum 0.25; one at-cost trial is allowed |

The T2 comparison observes 240 ticks after a 120-tick warm-up. Higher activation
makes existing capacity bind: desired-unit fulfillment is 56.61%, versus
99.99% in the ordinary-demand control. It demonstrates a scarcity price response;
it does not establish that this demand shock clears in those eight price windows.
Mean quoted contribution is an unweighted line-level diagnostic, not a traded
gross margin. No stock or production was granted to either operating world.

The paired input tests use 1,000 T2 firms and 20,000 consumers. Their raw output,
including the T2 comparison, is in
[the scenario log](scarcity-aware-paired-scenario.log).

## Full-population verification

Both seeded 3,600-tick runs passed. Each uses 50,000 T2 firms, 125,000 lines and
1,000,000 consumers. The table describes the final 360-tick window. All 134
markets traded; all material and final markets produced and traded in every
recorded 360-tick window.

| Metric | Seed 12345 | Seed 31415 |
| --- | ---: | ---: |
| Consumer desired-unit fulfillment | 99.9627% | 99.9618% |
| T2 firms trading | 50,000 / 50,000 | 50,000 / 50,000 |
| T2 installed-capacity utilization | 18.5019% | 18.5269% |
| T2 finished stock / realized units sold per tick | 4.987 ticks | 4.984 ticks |
| T2 realized gross margin | 15.4734% | 15.1483% |
| Maximum cumulative cash-ledger residual | $0.000329 | $0.000318 |
| T0 / T1 / T2 traded units exactly at cost | 0% / 0% / 0% | 0% / 0% / 0% |
| T0 / T1 / T2 traded units within 1% of cost | 0% / 0% / 0% | 0% / 0% / 0% |

There are no seller ceilings. The previous approximately 12.9% T2 break-even
concentration was not reproduced. QA does not demand a positive margin to make
this diagnostic pass; these zero shares are measured outcomes of these runs,
not a guarantee for every parameter setting or future tick. The default economy
has substantial spare capacity, so these results alone do not prove that all
its margins originate in physical capacity scarcity. Both the missing scarcity
signal and coarse experiment resolution changed; their separate contributions
to this full-run improvement were not isolated.

Raw reports retain per-market prices, traded volume and all ten financial windows:
[seed 12345](scarcity-aware-12345-3600.json) and
[seed 31415](scarcity-aware-31415-3600.json).
The [validation manifest](scarcity-aware-quality-full.json) records 18 passed
checks, source SHA-256 fingerprints, execution arrangement and the strengthened
scarcity fixture rerun. Economic sources stayed unchanged throughout the runs.

Browser verification reloaded the actual app, stepped, used Run Max, switched
to Run and paused at tick 49. The overview rendered with the source engine active
and 121.4 MB of state. The scheduler's automated tests verify the mode switch.
[Dashboard preview](scarcity-aware-browser.png).

## Reproduction and limits

`node tests/economy_quality.js` runs 16 contract, behavior and UI checks plus
two full-population 3,600-tick audits. `--quick` omits the long runs.
`node tests/market_scarcity.test.js` runs the matched scarcity scenarios.
Checks retain cash conservation, physical inventory limits, all-market activity,
participation, stock coverage, actual undercuts, supply recovery and Run/Run Max
behavior. They verify stated mechanics, not empirical economic realism.

Local profit observations remain noisy; no global optimum, stable equilibrium
or positive margin for every seller is guaranteed. Consumer cash is still
unlimited; recurring labor, rent, depreciation and financing are absent.
Starting markups still initialize offers, and the tests do not prove eventual
independence from those initial conditions. Existing supplier switching rules
remain; no new differentiation was added.
