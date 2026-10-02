# Phase 0 canonical economic contract

This is the editable contract for the Phase 0 source kernel.

## Authority rule

The source implementation is the single authority for model behavior. New
rules are first specified here, implemented in readable source, and covered by
deterministic tests.

## Fixed topology

- Raw resources: Water, Earth, Fire, Air.
- Tier 1 products: four C-1 refined materials and six C-2 intermediate substances
  (Ceramic Composite, Thermal Compounds, Synthetic Fibers, Semiconductor Substrate, Structural Polymers, and Active Compounds), defined in `engine/model.js`.
- Tier 2 products: 60 unique human consumer products across ten
  sectors. Their expanded elemental recipe complexity is three through five.
- Firms: 20 Tier 0 suppliers and 1,000 Tier 1 firms (100 per product cohort).
- Firms: 50,000 Tier 2 manufacturers with sparse, related product portfolios.
- End users: 1,000,000 immortal human consumers with persistent sector baskets,
  unlimited cash, and no initial supplier attachment.

## Tick order

1. Update each primary-resource extraction difficulty using a bounded mean-reverting deterministic
   process.
2. Produce Tier 0 inventory and update unit extraction cost.
3. Plan Tier 1 input purchases from observed orders, inventory and equipment
   capacity. Check complete-recipe profitability at posted quotes; transact
   purchases subject to cash, lot size and supplier stock.
4. Manufacture finished goods subject to raw inputs, equipment, target stock,
   and manufacturing cash.
5. Price Tier 0 and Tier 1 offers using the functions in `engine/model.js`.
6. Tier 2 firms purchase all processed ingredients from Tier 1, manufacture
   human consumer goods, and price their sparse product lines.
7. Clear the end-user market with atomic orders; record demand, stock loss,
   revenue, COGS, and supplier relationship observations. Public orders target
   Tier 2 only and always clear after manufacturing.
8. Update distinct realized-sales and observed-order EMAs and accumulate
   local pricing observations. Every 30 ticks, update reliability from fulfillment,
   price stability, and availability.

Run, Run Max, and Step all invoke this same tick sequence. Run Max only
executes more ticks between UI updates; it does not use a fast or alternate
economic model.

## Economic invariants

- No inventory, cash, demand quantity, or reliability score may be negative.
- `maxInventory` is a total Tier 0 supplier inventory cap across all elements
  that supplier holds, not a per-element cap.
- Tier 1 finished production is bounded independently by its desired and
  maximum inventory levels per active product line. Lowering a limit never
  destroys existing owned stock; it prevents further manufacture until space
  is available. Worker configuration normalizes maximum >= desired.
- Tier 2 finished production never increases a line's stock above twice that
  line's installed per-tick capacity. This is a capacity-based ceiling, not
  a promise of two ticks of actual consumer sales coverage.
- A transaction transfers equal and opposite cash and inventory value.
- Fulfilled quantity never exceeds desired quantity.
- A retail order is fulfilled completely or not at all.
- Producer quotes have a variable-cost break-even reservation, with a $0.01
  numerical minimum. There is no guaranteed positive markup or price ceiling.
  Quotes are posted; a later cost change does not retroactively alter a trade.
- Machinery in both firm tiers
  uses `15000 * 5^(complexity - 1)`; C-1/C-2 belongs exclusively to Tier 1
  and C-3/C-4/C-5 exclusively to Tier 2.
- Firm-to-firm transactions transfer equal and opposite cash and inventory.
  End-user payments are intentionally external demand injections because end
  users have unlimited, untracked cash.
- Given a seed, configuration, actions, and initial state, a source kernel
  must produce the same state on every run.

## Design decisions

Every Tier 0 supplier divides its warehouse ceiling equally across the elements
it extracts. Extraction replenishes a demand-based order-up-to target, subject
to its shared capacity, warehouse space and available cash. The target uses
three ticks of observed funded orders by default, capped by its element's
share of the desired warehouse. A small bootstrap reserve is the larger of one
wholesale lot and 10% of extraction capacity divided across elements. Initial
order forecasts seed the warehouse; they are not fabricated realized sales.

### Pricing: independent local experiments

The selected rule is derivative-following, based on Kephart, Hanson & Greenwald
(2000), with order-up-to inventory control informed by Eurace@Unibi and the
censored-demand literature. [Research, alternatives and provenance](pricing_research.md)
record the primary sources, adaptations and limitations.

Each supplier-element or manufacturing product line keeps its own experimental
direction and compares its total realized gross profit per tick over completed
observation windows. Default windows contain 30 ticks; repricing phases are
staggered by line index. The first window can be longer to reach its first
phase boundary; its objective is divided by the actual observed tick count.
Directions start deterministically in both directions. Gross profit is actual
transaction revenue minus weighted-average COGS, including extraction inventory
cost bases for Tier 0.

```
G = total window gross profit / observed ticks
available = units sold during the window + stock remaining at its close
if observed requested units > available: direction = +1
else if stocked and no units sold: direction = -1
else if units sold and G < previous G: reverse direction
else: retain direction
if no stock, no sales and no excess demand: hold price
otherwise:
  scale = clamp(scale * (direction reversed ? 0.5 : 1.2), 0.01, 1)
  next quote = max(variable-cost reservation, old quote * exp(direction * k * response * scale))
```

Default `k = 0.35` and `wholesalePriceResponse = 0.05` produce a roughly
1.75% maximum experimental move per window. Reversals halve the experimental
scale; a consistent direction restores it by a factor of 1.2, bounded between
0.01 and 1. These are numerical learning assumptions, not minimum margins.
A downward move blocked by break-even
reverses direction for the next experiment, so a boundary does not freeze the
learner. The rule compares total profit, not profit or revenue per sold unit.
It has no consumer valuation input, market-average price target, prescribed
normal markup, or profit guarantee. Competition affects pricing through each
seller's actual sales and profit; observations do not isolate a causal price
elasticity in a changing market and do not guarantee profit maximization.

Scarcity enters through orders the seller actually receives, including requests
it cannot fulfill. Window deliveries plus closing stock measure the total goods
available during that observation window; no future capacity or imaginary
inventory is added. An excess of requests makes the seller try a higher quote,
even if it delivered nothing. When supply covers its received requests, local
profit experiments resume. This adapts excess-demand price adjustment in Mark I/0
and adaptive derivative-following; it is not the exact algorithm of either paper.

The reservation price covers the larger of held finished-goods unit basis and
the current estimated cost of replenishment, with a numerical $0.01 minimum.
Tier 0 uses extraction and held-inventory costs. This is a cost constraint,
not a positive-profit floor. A competitive market can trade at break-even;
QA records its concentration and checks the behavior that produced it instead
of forcing a margin above the boundary. Initial `markup` (25%) and Tier 1
`compoundMarkupPremium` (15%) only seed new offers and operating cash estimates.
They never pull an established seller toward those margins.

Players select offers subject to the same reservation constraint and receive
no special production, purchasing, stock, cash or customer rules. Going offline
retains ownership and price instructions. An explicit player price resets that
line's experimental observation window; a return to BOT resumes learning.

### Inventory, orders and business purchasing

All producing lines maintain two distinct EMAs: observed requested units for
replenishment, and realized sold units for reporting actual stock/sales coverage.
At the end of the tick, each uses `EMA += alpha * (observation - EMA)`, with
`alpha = 0.15`. Sales start at zero; startup order estimates are explicitly
bootstrap forecasts. Observed business requests count quantities the buyer can
fund; consumer attempts count their desired quantity at the contacted offer.
Missed orders count in the contacted seller's forecast. A consumer can try
several sellers, so the sum of local inquiries can exceed aggregate consumer
need; market fulfilled/unmet/price-suppressed demand counts each consumer once.
Demand that no seller observes is never distributed to firms by an oracle.

Manufacturing order-up-to targets use `ceil(orderEMA * inventoryCoverageTicks)`,
bounded by the established line's target/max stock limits and bootstrap reserve.
Desired output is the nonnegative target deficit, capped by installed capacity.
A shrinking target never destroys owned stock. Tier 1 bootstrap is the larger
of one maximum consumer order and 10% of capacity; Tier 2 bootstrap is one maximum
scaled order, capped by capacity. These reserves allow an idle firm to remain
discoverable without continually filling a large warehouse.

For every installed recipe, the manufacturer evaluates a complete batch using
held-input cost bases for ingredients already in stock and selected upstream
quotes for missing ingredients, plus conversion cost. If the expected unit
cost exceeds its posted output quote, it plans no new input purchases for that
line. A cost increase can therefore pause a batch; repricing can make later
production viable again. Before manufacture, actual input bases and conversion
cost are checked against the output quote as well. This avoids knowingly
manufacturing a loss-making batch after different procurement costs materialize.
Estimates are local, myopic and conditional on current offers, not promises
that customers will buy every planned unit.

Input demand is derived from planned output and recipes, net of shared input
stocks. Business buyers compare stocked upstream offers, retain a preferred
supplier when a cheaper alternative does not compensate for reliability-based
switching friction, and buy only whole permitted lots within cash and stock.
Frictions affect choice, not the seller's invoice. Tier 1 input procurement
rotates cohort/firm priority; Tier 2 procurement rotates firm priority. Wholesale
lot rounding can leave residual inputs. Insufficient cash or a missing ingredient
can still constrain production. C-1/C-2 demand consists exclusively of manufacturing input orders.

If all posted suppliers lack a purchasable lot, a business buyer sends its
affordable intended request to its best known empty offer. It receives no
stock or invoice, and no relationship is created until a purchase succeeds.
This retains a local stockout signal instead of erasing input demand simply
because every supplier is empty. Unaffordable requests do not enter this signal.
Requests remain conditional inquiries, not cash reservations across all ingredients.

T0 quotes change after current T1 resource procurement. T1 quotes change after
refining and before Tier 2 purchases. Tier 2 quotes change after its input and
production decision, before public shopping. Receipts and actual delivered COGS
record the economics of each transaction.

### Demand curves and equilibrium estimates

Firm-specific constants must not independently manufacture upstream demand or
predetermine market prices. At a material juncture, a company's desired input
quantity is its recipe requirement for planned output minus held input stock.
Its willingness to pay is bounded by expected output receipts less conversion
and other recipe costs. Supply consists of owned stock plus feasible production,
with cash and capacity limits. Those limits produce piecewise responses rather
than a universally linear curve.

A linear demand/supply intersection can be an approximation to these changing
responses, not a shared ideal transaction price. Aggregate relationships would
combine different costs, stocks and buyers; estimating slopes from simultaneous
price/quantity observations also mixes supply, demand and competition changes.
This implementation uses actual posted-offer trades and local experiments;
it does not fit or impose a linear equilibrium solver.

## Tier 2 catalogue and portfolios

The catalogue contains exactly 20/20/20 products of complexity 3/4/5.
Each of the ten sectors has two products in every Tier 2 complexity band. C-1/C-2
products are forbidden in Tier 2, including equipment purchases.
Complexity sums ingredient quantities times elemental ancestry: a basic
C-1 processed material counts as one, a Tier 1 compound as two. Recipes, names, stable
IDs, symmetric sector adjacency, demand weights, machinery, and independent consumer
value scales are defined in the model. The 60 outputs have distinct names, ingredient multisets and expanded elemental compositions.

Exactly ten human consumer sectors map one-to-one onto the ten Tier 1 cohorts.
`T2_SECTOR_DEFINITIONS` specifies each required material; every recipe must include
it, enforced at model initialization. All Tier 2 purchases debit Tier 1 stock,
credit Tier 1 cash and sales, and record Tier 1 supplier relationships, including
C-1 materials. There is no direct Tier 0-to-Tier 2 trade.

| Tier 2 sector | Required Tier 1 cohort | C-3 | C-4 | C-5 | Total |
| --- | --- | --- | --- | --- | --- |
| Food & Nutrition | Purified Water | 2 | 2 | 2 | 6 |
| Housing & Furniture | Refined Minerals | 2 | 2 | 2 | 6 |
| Household Energy | Energy Cells | 2 | 2 | 2 | 6 |
| Hygiene & Personal Care | Chemical Feedstock | 2 | 2 | 2 | 6 |
| Home & Kitchen | Ceramic Composite | 2 | 2 | 2 | 6 |
| Healthcare & Wellness | Thermal Compounds | 2 | 2 | 2 | 6 |
| Clothing & Textiles | Synthetic Fibers | 2 | 2 | 2 | 6 |
| Electronics & Communication | Semiconductor Substrate | 2 | 2 | 2 | 6 |
| Mobility & Transport | Structural Polymers | 2 | 2 | 2 | 6 |
| Leisure & Fitness | Active Compounds | 2 | 2 | 2 | 6 |


Capability bands 3/4/5 contain exactly 30,000/15,000/5,000 firms.
Core-product quotas use sector/product need-frequency priors with seeded
0.8–1.2 multiplicative variation and a 100-firm minimum per product at full
scale. This is a documented bootstrap heuristic, not an empirically fitted
normal distribution. Capability 3/4/5 starts with 2/3/4 lines, for exactly
125,000 initial lines. Additional lines are chosen by need weight with a
2:1 home-sector preference. Additional lines are distinct products within the core or an adjacent
sector and never exceed the firm's capability. Initial equipment is granted;
working cash covers 30 ticks of full-capacity estimated operating costs plus one
whole unit per distinct C-1 processed material, rounded up to $50 with a $500 minimum.
Operating estimates use the reset configuration's extraction costs and Tier 1
offers; capital equipment value does not determine the cash grant.

Machinery across both tiers costs $15,000 × 5^(complexity−1): C-1 $15,000,
C-2 $75,000, C-3 $375,000, C-4 $1,875,000, C-5 $9,375,000.
Tier 2 line capacities for C-3/C-4/C-5 are 3/2/1 units per tick.
Conversion costs $0.50 × complexity per unit. Firm inventories share inputs
among their sparse lines; at most 250,000 lines can exist and five can belong
to one firm. Weighted-average input and finished-good bases determine COGS.
Tier 1 refineries buy Tier 0 resources in 10-unit lots by default. Tier 2
purchases from all ten Tier 1 cohorts use whole units and may partially fulfill. Procurement rotates firm
priority each tick, excludes depleted offers, and compares preferred suppliers
with the cheapest stocked alternative using reliability-based switching costs.
Tier 2 funded orders update the supplying Tier 1 market; refinery input orders
transmit demand upstream to Tier 0.

At month close, a bot with at least 75% utilization over the observed month and
1.6 times the next machinery cost in cash can add one distinct eligible line.
Player firms do not auto-expand. Player prices obey the same variable-cost
reservation as bots; going offline does not remove ownership or prices. A return to
BOT resumes automated pricing. Purchase rejection must not change cash,
equipment, or portfolio state.

## Tier 3 consumers

Sector primary preferences follow the model sector demand priors, with all ten
sectors reachable; discretionary baskets remain heterogeneous and unrelated to
firm assignment. One million persistent consumer records have deterministic baskets of two to
five unique sectors, quantities, reservation-price multipliers, elasticities,
and one product/supplier relationship per basket slot. There is no initial
seller attachment. Each consumer activates with probability 0.1 per tick,
chooses the primary basket slot with probability 0.6 and otherwise a
discretionary slot, and issues at most one order. All activated needs select
basket-sector Tier 2 C-3/C-4/C-5 products by their authored need-frequency priors,
with a 65% chance of retaining a previously purchased Tier 2 product. Public demand
for all ten Tier 1 C-1/C-2 materials is exactly zero; only companies purchase them.
Tier 2 procurement and production precede public shopping every tick.

Expected quantity is scaled by 0.45^(complexity−1). Price-sensitive continuous
demand is stochastically rounded to whole units, capped by the ceiling of the
scaled quantity. This keeps rare complexity-5 purchases possible without
creating fractional deliveries or rounding all of their demand to zero.
Consumer value scales are authored independently of recipes, operating costs,
starting markups and seller quotes: Tier 2 C-3/C-4/C-5 uses 8/12/16. Tier 1
materials have no public consumer demand.
The individual scale V multiplies this prior by the buyer's fixed private taste
and, for T2, `1 + tier2ReservationPremium * (complexity - 1)` (default 0.45).
Quantity at price P is `qMax / (1 + (P/V)^eta)`. V halves expected quantity;
it is not a hard choke or maximum willingness to pay. Consumer value never
clamps an offer, and higher production costs cannot rewrite private preferences.
An individual's elasticity exponent is drawn independently between 1 and 2;
quantity, basket and value heterogeneity are also persistent seeded attributes.

Each buyer samples five posted offers by default (duplicates are discarded)
and also considers its previous successful supplier, if any. Sampling is
uniform over this product's installed sellers, independent of price and stock;
consumer records do not receive an assigned seller or guaranteed allocation.
Offers remain visible when empty. The buyer ranks discovered offers by invoice
price plus switching friction for alternatives to a prior supplier. Without a
relationship, there is no differential friction. An undercut can therefore win
a discovered buyer without a common equilibrium-price command.

At each contacted offer, desired quantity is recomputed and stochastically
rounded with the same rounding draw for that consumer across alternatives.
The seller observes the attempted order even if stock is insufficient. Atomic
orders must be served completely; the buyer tries other discovered offers on a
stockout. An unfulfilled need remains unmet when that comparison set contains
no acceptable stocked offer, even if undiscovered inventory exists elsewhere.
There is no omniscient all-seller fallback. Only successful purchases update
relationships; failed orders and non-activation never create attachment.
Market demand accounting counts each buyer once at the successful offer or,
if no purchase is possible, at its initial chosen quote. Price-suppressed units
and stock-unmet units remain distinct. Supply, tastes and portfolios are not
rewritten to match consumer demand to production capacity.

A cheaper seller can gain volume yet lose profit because its unit margin falls.
Its stock and capacity cap deliveries; excess inquiries raise its replenishment
forecast. Rivals' lost sales and altered profit feed their own price experiments.
This is the transmission of an undercut or stockout through actual transactions.

Consumer payments are external cash injections. Extraction, conversion, and
new machinery are external cash sinks. Consequently the per-tick total company
cash change must equal retail payments minus those sinks. Initial balance
sheets and equipment grants are reset-time endowments, not trades.

## Runtime interfaces and scenario gates

The single worker owns economic state. `select`, `player`, and `buyEquipment`
accept a Tier 1 or Tier 2 company identity. `tier2Query` requests a filtered,
sorted 50-row company page. `companyDetail` supports all three firm tiers.
Snapshots expose Tier 2 firms, sector cohorts, 60 product markets, selected
portfolios, consumer aggregates (`endUsers` and `tiers.t3`), and performance
statistics. Individual consumers are never sent to the main thread.

Reset defaults are authoritative in `engine/model.js` (`ECONOMY_DEFAULTS`)
and are used by both the worker and browser controls. Default Tier 0 capacity
is 20,000 per tick, desired inventory 60,000, maximum inventory 120,000,
and initial cash $1,000,000 per company. Tier 1 basic/compound capacities
are 160/240, desired finished-stock ceiling 600, maximum 1,200 per line,
and working cash $5,000. Initial Tier 1 equity is $20,000 per C-1 firm
and $80,000 per C-2 firm, totaling $56,000,000 ($5,000,000 cash plus
$51,000,000 granted equipment).

Both manufacturing tiers plan and purchase toward three ticks of their own
recent observed-order EMA, bounded by their finished-stock ceilings. Tier 1 retains a
bootstrap stock of the larger of consumer quantity maximum or 10% of installed
capacity, bounded by capacity. Tier 2 retains enough bootstrap stock to serve
one maximum scaled consumer order, bounded by capacity. Idle firms do not
keep producing to a large warehouse ceiling. Inventory targets can shrink
without destroying existing stock; player and bot firms use identical input,
manufacturing and inventory rules. No sales or customers are assigned to fit
company capacity. Unmet demand and unused capacity are legitimate outcomes.
Tier 1 market snapshots separate consumer and intermediate sales. Consumer
revenue excludes intermediate transactions. Zero-trade average prices use
posted offers rather than non-finite values.
Population changes require Reset; live pricing and demand parameters preserve
earned relationships. Fixed Run schedules two ticks per second; Run Max
yields after a time-bounded batch, and Step advances precisely one tick.

The full-scale scenario suite requires all products to trade in each rolling
360-tick window, all complexity-5 markets to survive, complex goods to stay
below 20% of total Tier 2 volume, and established consumer unit fulfillment
above 50%. The 3,600-tick scenario validates prolonged operation. Supply-outage
and eightfold-price-shock fixtures must reduce fulfillment/demand and recover
when inputs return. Contract tests validate exact cohort counts, transfers,
atomic purchases, basket eligibility, machinery rejection, player isolation,
monthly expansion, reset determinism, and fixed/max scheduler equivalence.

The full-population balance audit extends to 7,200 ticks and additional seeds.
After startup, default bot-only worlds must retain 10–65% Tier 2 utilization
(trade plus player headroom), at least 60% of firms trading in each 360-tick
window, at most 12 ticks of final-good stock and 10 ticks of upstream/material
stock at realized sales rates, and positive aggregate manufacturing gross
profit. These are explicit calibration regression gates, not empirical laws
or constraints imposed on player behavior. They complement, not replace,
per-tick stock/cash bounds, variable-cost reservations and the cash-conservation ledger.

The quality gate is `node tests/economy_quality.js`. It runs accounting,
reporting and control contracts; behavioral price discovery against known
linear-demand profit optima; different initial quotes and demand/cost/capacity
shifts; independent consumer values; censored orders; complete-recipe purchasing;
supply outage/recovery; consumer price shocks; and market-responsive player
pricing. Full-population 3,600-tick runs use seeds 12345 and 31415. Final
360-tick audits record traded prices and break-even concentration in all 74
markets, with activity, finite prices and cost coverage checks. No arbitrary
positive margin is imposed just to make boundary diagnostics pass. Existing
utilization, participation, inventory coverage and cash conservation gates
remain in force. Reproducible reports retain per-market traded-volume
statistics and rolling 360-tick financial/production windows.

`market_scarcity.test.js` compares affordable and unaffordable input requests
to empty suppliers with zero starting markups, checks their actual price response,
and exhausts/restores extraction capacity in an operating economy. A paired T2
scenario increases only consumer activation: existing workshop capacity binds,
and both posted prices and contribution per unit rise. The pricing fixture also
checks a narrow profitable interval where a coarse fixed step overshoots.
A price above cost is never an
asserted minimum: scarcity must enter through received orders and finite supply.
The default economy can still exhibit competitive break-even trades; audits
report their concentration without making the pricebot obey a required margin.

## Tier 2 reporting and charts

Industry-market summaries group product lines by product sector. Company-cohort
summaries group whole firms by home sector, including adjacent-sector lines. These
are separate aggregations; each independently reconciles to Tier 2 production,
sales, revenue and COGS. Three complexity-band summaries likewise reconcile to the
same totals. Utilization uses produced units / installed capacity; realized gross
margin uses gross profit / revenue; consumer fill uses delivered / desired units.
Zero-denominator ratios report zero. Firm online state is player-session status,
not a suspension of automated procurement or production.

Snapshots expose product costs, recipes, capacity, utilization and unmet demand;
company summaries add input/finished stock, equipment book value, marked equity,
margin and utilization. Detailed selected firms expose each required material,
including depleted stores, its weighted basis, current-tick recipe consumption,
full-capacity requirements and last successful upstream supplier/quote/reliability.
Full-capacity input coverage is not a demand forecast or promised output.

Charts retain at most 240 reported tick samples, never one sample per query or
filter interaction. Repeated reports at a tick replace that tick's sample. Industry
history stores only ten compact sector summaries; selected-company history
starts at selection, resets when the company changes, and is cleared on reset.
No per-consumer history or full 50,000-firm history is transmitted. Reporting has
no authority to modify economic state or change the canonical tick sequence.

## Bought quantities and tier boundaries

Tier 0 buys from Gaia and sells to Tier 1 companies. Its extracted units count
as bought units; extraction spending remains the same external cost sink.
Tier 1 buys from Tier 0 and sells only to Tier 2 companies. Tier 2 buys from
Tier 1 and sells only to human consumers. Bought counters reset each tick
and record completed input transfers rather than requests or recipe consumption.
Tier 0 bought quantity equals extracted quantity; Tier 1 bought equals Tier 0
sold, and Tier 2 bought equals Tier 1 sold. Tier 0 output appears once as bought
in the tier comparison, while internal production records remain available for
inventory and cost accounting.

## Midbridge and the Infinity contract

Midbridge is an Earth colony running a consumer behavior experiment for exactly 1,000,000
immortal humans. Residents are selected individuals who sought immortality and
worked their way toward sealing the Infinity contract. Robots perform all
production in the colony, provide for residents' needs and receive their
consumerism. Most humans elsewhere work in many roles for robots under poor
conditions.

This premise is story metadata in `COLONY_STORY`. Selection, prior work,
outside labor conditions and the contract introduce no additional simulation
mechanics. Colony population is fixed through all ticks; there are no births,
deaths, aging or health-state changes. Smaller configurable populations exist
for test scenarios.

Immortality Treatment is a C-5 Healthcare & Wellness product with the recipe
WF + EF + A. It uses ordinary consumer purchases and stock/COGS accounting.
A failed or unaffordable order cannot change immortality or population.

## Distinct product identity

The catalogue has 60 independently authored products: 20 C-3, 20 C-4 and
20 C-5. Each has exactly one fresh code, T2-001 through T2-060, used by
price controls, equipment, stocks, demand and reporting.
`recipeKey` sorts Tier 1 ingredient codes and retains quantities. Ingredient
order and sector labels cannot create another product for the same multiset.
`elementalComposition` expands each recipe to Water, Earth, Fire and Air totals.
The model rejects duplicate recipes and duplicate expanded compositions at
initialization. Names and codes are also distinct; no alternate codes resolve
to a product. Sector assignment and primary-material dependency are properties
of that product. See [the complete catalogue](product_catalogue.md) for the map.
