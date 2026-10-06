<!-- Current rebalance: 200 invented markets, 220 reserved recipes; capital calibration in progress. -->
# Phase 0 canonical economic contract

This is the editable contract for the Phase 0 source kernel.

## Authority rule

The source implementation is the single authority for model behavior. New
rules are first specified here, implemented in readable source, and covered by
deterministic tests.

## Story and administrative scope

The planned player is a human investor taking operational control of an existing Tier 1 or Tier 2 business in the Robotic Space Generation. Competitors include opportunist human investors and robotic executive agents. The future game's alpha player scope is Tier 1. This is release intent only: the economy-core simulator retains administrative inspection, manual pricing, controller changes and equipment purchases for both Tier 1 and Tier 2. Story metadata must not disable admin capabilities.

The simulation advances under bots independently of takeover. Taking control preserves the company's assets, cash, equipment, inventory and trading relationships. Entry is described as an initial investment, without implementing acquisition pricing, onboarding, investor wallets or artificial capital injection. Human competition is the setting; multiplayer is not implemented. Manual control grants no preferred customers, demand, margins or guaranteed profitability. Administrative actions obey the existing economic constraints, including installed-product validity, affordability and same-sector portfolio limits.

## Fixed topology

- Raw resources: Water, Earth, Fire, Air.
- Tier 1 products: four C-1 refined materials and six C-2 intermediate substances
  (Ceramic Composite, Thermal Compounds, Synthetic Fibers, Semiconductor Substrate, Structural Polymers, and Active Compounds), defined in `engine/model.js`.
- Tier 2 catalogue: 420 distinct physical galactic goods recipes across ten sectors,
  with 200 invented markets and 220 reserved recipes. Their expanded elemental recipe complexity is three through five.
- Firms: 20 Tier 0 suppliers and 1,000 Tier 1 firms (100 per product cohort).
- Firms: 61,950 Tier 2 manufacturers with sparse, related product portfolios.
- End users: 1,000,000 external procurement agents with persistent sector baskets,
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
   galactic end-use goods, and price their sparse product lines.
7. Clear the end-user market with atomic orders; record demand, stock loss,
   revenue, COGS, and supplier relationship observations. Public orders target
   Tier 2 only and always clear after manufacturing.
8. Update distinct realized-sales and observed-order EMAs and accumulate
   local pricing observations. Every 0x1E ticks, update reliability from fulfillment,
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
- Tier 2 line targets are bounded by
  `max(1, ceil(tier2InventoryCapacity / (2 * installedRouteCount)))`.
  Inputs and finished goods share the company warehouse, and production shares
  one company capacity. These stock ceilings depend on storage and route count;
  they do not promise a fixed number of ticks of sales coverage. Lower targets
  prevent replenishment without destroying existing owned stock.
- A transaction transfers equal and opposite cash and inventory value.
- Fulfilled quantity never exceeds desired quantity.
- A retail order is fulfilled completely or not at all.
- Producer quotes have a variable-cost break-even reservation, with a $0.00001
  numerical minimum. There is no guaranteed positive markup or price ceiling.
  The reservation applies when the tier's offers are priced. Quotes are posted;
  a later cost change does not retroactively alter a trade. Tier 0 input clearing
  precedes its pricing phase, so a new extraction cost or inventory basis can
  exceed the earlier posted quote on an actual raw delivery. The resulting loss
  remains in sold-cost profit and book equity.
- Tier 1 C-1/C-2 machinery costs $15,000/$75,000 respectively
  (`15000 * 5^(complexity - 1)`). Each Tier 2 firm owns its C-3/C-4/C-5
  routes outright; a paid route costs $1,000 and uses the firm's capacity.
  There is no shared factory asset. C-1/C-2 belongs exclusively to Tier 1
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

The 4 October user clarification is an acceptance requirement for every market:
buyers seek lower purchase costs and sellers seek higher profitable selling
prices. A buyer may compare posted offers, availability and its own switching
costs or willingness to pay. A seller may respond to its own costs, orders,
stocks and realized profit, including cutting a quote when lost sales make that
profitable. Neither side may be guided toward a shared optimum, common target
quote, prescribed margin or return target. A mutually accepted transaction price
may emerge from their competing decisions; it must not be supplied by a central
pricing objective. Offline calibration criteria never enter either decision.

Fixed buyer valuation and demand data must remain independent of sellers'
current quotes and requested markups. Seller opening quotes are initial offers,
not attractors for later price search. Human price instructions must face the
same purchase, demand, stock, funding and reservation constraints as bot offers,
with no compensating customer preference, target-price correction or promised
profit. Calibration acceptance includes a source and mechanical review of these
boundaries in raw, intermediate and final markets.

The selected rule is derivative-following, based on Kephart, Hanson & Greenwald
(2000), with order-up-to inventory control informed by Eurace@Unibi and the
censored-demand literature. [Research, alternatives and provenance](pricing_research.md)
record the primary sources, adaptations and limitations.

Each supplier-element or manufacturing product line keeps its own experimental
direction and compares its total realized gross profit per tick over completed
observation windows. Default windows contain 0x1E ticks; repricing phases are
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
the current estimated cost of replenishment, with a numerical $0.00001 minimum.
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

Tier 0 extraction currently uses the demand-based target, cash, shared capacity
and warehouse constraints without this expected-proceeds check. It replenishes
and pays the current extraction cost before Tier 1 purchases clear at its
existing posted quote; its cost reservation is then applied in the pricing
phase. A known cost increase can therefore produce and deliver raw goods below
their new weighted acquisition basis for that tick. This is the current raw
production policy, distinct from the Tier 1/Tier 2 complete-recipe gate; the
reservation is not a guarantee that every production batch or earlier trade
was profitable.

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

The complete catalogue contains 44/116/260 distinct recipes at C-3/C-4/C-5. Its invented subset contains 20/60/120 markets, totaling 200. The remaining 220 are reserved and cannot be installed or traded. There are no services or unnamed recipes. Galactic sectors organize applications independently of manufacturing materials.

Complexity counts ingredient quantities times elemental ancestry. Every Tier 2 input is bought from Tier 1, including basics. There is no direct Tier 0-to-Tier 2 trade. C-1/C-2 products cannot be installed in Tier 2.

| Galactic sector | C-3 | C-4 | C-5 | Markets |
| --- | --- | --- | --- | --- |
| Power & Energy | 2 | 6 | 12 | 20 |
| Propulsion & Navigation | 2 | 6 | 12 | 20 |
| Spacecraft & Hulls | 2 | 6 | 12 | 20 |
| Habitats & Life Support | 2 | 6 | 12 | 20 |
| Robotics & Automation | 2 | 6 | 12 | 20 |
| Computing & Communications | 2 | 6 | 12 | 20 |
| Science & Diagnostics | 2 | 6 | 12 | 20 |
| Mining & Industry | 2 | 6 | 12 | 20 |
| Logistics & Provisioning | 2 | 6 | 12 | 20 |
| Defence & Rescue | 2 | 6 | 12 | 20 |
| **Total invented** | **20** | **60** | **120** | **200** |

Each sector starts with 20 invented goods; its remaining authored recipes are reserved. This equal market count is a presentation choice, not a rule requiring one material per sector. Invented complexity mixes match across sectors; material sourcing follows each recipe. Physical-form tags are Consumables, Components, Assemblies and Systems; they do not alter trading mechanics.

Each sector has twenty active goods. Its unordered portfolios of one to four
products total 20 + 190 + 1,140 + 4,845 = 6,195. One company starts with each
portfolio, giving 61,950 firms and 232,000 initial product routes. Each good has
1,160 suppliers. Every route remains within its company's sector. All firms
can manufacture C-3–C-5 recipes; there are no separate initial capability bands.
Initial equipment is granted. Working cash covers thirty ticks of estimated
operating costs, rounded up to $50 with a $2,500 minimum.

Each Tier 2 firm owns its product routes outright; there is no shared factory.
Initialization grants each firm its opening routes at $1,000 each as equipment.
A later route addition costs $1,000 and uses the firm's existing capacity.
Capacity is six units per tick, pooled across one to four routes. The
60-unit warehouse includes all ingredients and finished goods, with each compound
unit occupying one unit regardless of ancestry. Opening capital is fixed by
the calibration constraints; downstream capacity remains permitted supply data.
The current default capacity has not been validated against the Age/ROE target.
C-1/C-2 Tier 1 machinery costs $15,000/$75,000. Conversion costs remain
$0.50 × complexity × `tier2ConversionCostScale` per finished Tier 2 unit,
with a default scale of one. Weighted-average input and
finished-good bases determine cost of sales.
Tier 1 refineries buy Tier 0 resources in 1,000-unit lots by default.
Requests round up to whole lots; funded quantities and deliveries round down
to whole lots. A supplier with fewer than 1,000 units cannot deliver a fraction,
and a buyer must afford a whole lot. The remainder stays in refinery raw inventory
for later production. Tier 0 bootstrap stock already reserves at least one lot
per element; its 10,000-unit capacity and 500,000/1,000,000 warehouse settings cover
these lots. Default Tier 1 starting cash of $5,000 covers two initial 1,000-unit
ingredient lots at $1.25 per unit plus conversion cash for a C-2 refinery.

Tier 0 integer production uses proportional apportionment within each firm's
shared capacity. Feasible positive deficits which would otherwise round to zero
receive a one-unit machine quantum before bulk allocation; scarce capacity and
cash use the same rule across all active routes. Remaining units follow
proportional quotas with rotating material-neutral remainder ties. Every unit
still requires real funding and warehouse space and carries its extraction cost
into inventory basis. This prevents a line needing one or two units to complete
a wholesale lot from being permanently stranded by large sibling deficits.

Tier 2 purchases from all ten Tier 1 cohorts use whole units and may partially
fulfill. Procurement rotates firm
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

The current final-customer demand model is accepted as the baseline for
the Robotic Space Generation. Final agents have unlimited purchasing money: price affects desire and
quantity, while income, savings and constrained operating budgets are not simulated.
Default activation produces approximately 100,000 shopping occasions per tick
from the fixed population of 1,000,000, before price suppression and stockouts.

Sector primary preferences follow the model sector demand priors, with all ten
sectors reachable; discretionary baskets remain heterogeneous and unrelated to
firm assignment. One million persistent consumer records have deterministic baskets of two to
five unique sectors, quantities, reservation-price multipliers, elasticities,
and one product/supplier relationship per basket slot. There is no initial
seller attachment. Each consumer activates with probability 0.1 per tick,
chooses the primary basket slot with probability 0.6 and otherwise a
discretionary slot, and issues at most one order. All activated needs select
basket-sector Tier 2 C-3/C-4/C-5 products by their authored need-frequency priors,
with a 65% chance of retaining a previously considered Tier 2 product, even when
that need produced no whole-unit order or was unfulfilled. Public demand
for all ten Tier 1 C-1/C-2 materials is exactly zero; only companies purchase them.
Tier 2 procurement and production precede public shopping every tick.

Every active good has fresh selection weight 1/20 within its sector. The equal
sector priors and the 2/6/12 product mix give fresh C-3/C-4/C-5 selection shares
of 10%/30%/60%. Repeat choices, prices and stock alter realized shares.

Let R be a good's fixed engineering cost at nominal extraction/refinery conditions
and m = procurementBaseMarkup + procurementMarkupPremium × (complexity−3)
(default 0.25 + 0.05 × (complexity−3)). Latent quantity is the buyer's base quantity
multiplied by `tier2DemandFactor × 0.25 / (R × m)`. The valuation benchmark is
`2 × R × (1+m) / 1.25`, multiplied by private taste and the optional complexity
reservation premium (default zero). Seller cost shocks and desired markups do not
rewrite this benchmark. The formula compensates cost and nominal margin in the
starting purchasing profile; it does not compensate realized company losses.

Continuous demand at quote P is `latentQuantity / (1 + (P/V)^eta)`. Demand is
stochastically rounded into whole atomic orders, capped at the ceiling of latent
quantity. V is a half-quantity price scale, not a hard willingness-to-pay ceiling.
The [neutrality test](../tests/procurement_neutrality.test.js) verifies equal
benchmark gross-profit opportunity across all active recipes and decreasing mean
unit quantities with complexity. Equal benchmark opportunity does not establish
equal realized ROE under stock limits, learning and supply-chain bottlenecks.

Each buyer samples five posted offers by default (duplicates are discarded)
and also considers its previous successful supplier, if any. Sampling weights each route by the reciprocal of its firm's route count,
dividing one firm discovery budget among its products, independently of price and stock;
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

Demand reporting distinguishes the following quantities:

| Metric | Definition |
| --- | --- |
| Latent demand | Sum of stochastically rounded zero-price quantities for activated product choices |
| Desired demand | Whole units requested at the successful offer, or the initial chosen quote if unfilled |
| Fulfilled demand | Units actually delivered and paid for |
| Price loss | Reported latent units minus desired units |
| Stock unmet | Desired units that could not be purchased from discovered offers |

Latent and priced quantities use the same rounding draw. Every non-negative quote
therefore yields desired units no greater than latent units, and reported price
loss measures suppression of the same realized physical wishlist. Over repeated
observations latent units estimate the continuous zero-price expectation, including
fractional needs. A shopping occasion with no whole-unit need retains product
memory but skips supplier comparison; it creates no order or supplier relationship.

Tier 2 conversion costs can be multiplied by `tier2ConversionCostScale`; the
separate authored procurement benchmark uses `procurementConversionReferenceScale`.
Both default to one. Basic and compound benchmark input costs are also separate
from live supplier prices. Benchmark values are frozen on reset; changing supply
costs during a run does not automatically raise demand or willingness to pay.
Per-unit quotes support five decimal places, including admin controls; cash and
equity retain their usual monetary display. This permits fractional-cent bulk
inputs without making a one-cent numerical floor an artificial profit source.

All goods use the same repeat-purchase mechanism, from consumable cartridges to spacecraft hulls and reactor systems. Product differences enter through selection weights, complexity and valuation. Installed fleets, capital replacement schedules, physical consumption depletion and accumulated unmet needs are not simulated. Each demand agent has a permanent basket of 2–5 sectors; all ten sectors are represented across the aggregate. Historical human-catalogue reports cannot validate this galactic catalogue.

The historical, all-invented [0x2D0-tick full-population audit](../reports/robotic-space-generation-12345-720.json) passed with all 420 goods and all ten Tier 1 material markets producing and trading. The final 0x168 ticks fulfilled 99.46% of desired units, purchased 61,420.71 units per tick and had 49,977 Tier 2 firms trading. Utilization was 18.84%, realized gross margin was 11.76%, and maximum cash-ledger residual was below $0.000014. These are observed results for this seed and window, not demand targets or guarantees.

### Future demand extensions

Invention and creation of new products are intended future ways to expand demand.
A marketing and visibility layer is also planned to influence product discovery
and demand. Their rules, costs, effects on preferences and interaction with the
existing catalogue remain to be designed in a later phase. The current model has
no invention, dynamic product creation, marketing or visibility-based seller
sampling; current offer discovery divides equal firm discovery weight among
its installed routes.

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
Snapshots expose Tier 2 firms, sector cohorts, 200 invented goods markets, selected
portfolios, consumer aggregates (`endUsers` and `tiers.t3`), and performance
statistics. Individual consumers are never sent to the main thread.

Reset defaults are authoritative in `engine/model.js` (`ECONOMY_DEFAULTS`)
and are used by both the worker and browser controls. Default Tier 0 capacity
is 10,000 per tick, desired inventory 500,000, maximum inventory 1,000,000,
and initial cash $1,000,000 per company. Tier 1 basic/compound capacities
are 320/240, desired finished-stock ceiling 600, maximum 1,200 per line,
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
0x168-tick window, all complexity-5 markets to survive, mean unit orders per market to decline
as complexity rises, and established consumer unit fulfillment
above 50%. The 0xE10-tick scenario validates prolonged operation. Supply-outage
and eightfold-price-shock fixtures must reduce fulfillment/demand and recover
when inputs return. Contract tests validate exact cohort counts, transfers,
atomic purchases, basket eligibility, machinery rejection, player isolation,
monthly expansion, reset determinism, and fixed/max scheduler equivalence.

The full-population balance audit extends to 0x1C20 ticks and additional seeds.
After startup, default bot-only worlds must retain 10–65% Tier 2 utilization
(trade plus player headroom), at least 60% of firms trading in each 0x168-tick
window, at most 0xC ticks of final-good stock and 0xA ticks of upstream/material
stock at realized sales rates, and positive aggregate manufacturing gross
profit. These are explicit calibration regression gates, not empirical laws
or constraints imposed on player behavior. They complement, not replace,
per-tick stock/cash bounds, variable-cost reservations and the cash-conservation ledger.

The quality gate is `node tests/economy_quality.js`. It runs accounting,
reporting and control contracts; behavioral price discovery against known
linear-demand profit optima; different initial quotes and demand/cost/capacity
shifts; independent consumer values; censored orders; complete-recipe purchasing;
supply outage/recovery; consumer price shocks; and market-responsive player
pricing. Full-population 0xE10-tick runs use seeds 12345 and 31415. Final
0x168-tick audits record traded prices and break-even concentration in all 214 active
markets, with activity, finite prices and cost coverage checks. No arbitrary
positive margin is imposed just to make boundary diagnostics pass. Existing
utilization, participation, inventory coverage and cash conservation gates
remain in force. Reproducible reports retain per-market traded-volume
statistics and rolling 0x168-tick financial/production windows.

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
summaries group whole firms by home sector; every installed route remains in that
same sector. These
are separate aggregations; each independently reconciles to Tier 2 production,
sales, revenue and COGS. Three complexity-band summaries likewise reconcile to the
same totals. Utilization uses produced units / installed capacity; realized gross
margin uses gross profit / revenue; customer fill uses delivered / desired units.
Zero-denominator ratios report zero. Firm online state is player-session status,
not a suspension of automated procurement or production.

Snapshots expose product costs, recipes, capacity, utilization and unmet demand;
company summaries add input/finished stock, equipment book value, book equity,
margin and utilization. Detailed selected firms expose each required material,
including depleted stores, its weighted basis, current-tick recipe consumption,
full-capacity requirements and last successful upstream supplier/quote/reliability.
Full-capacity input coverage is not a demand forecast or promised output.

Charts retain at most 240 reported tick samples, never one sample per query or
filter interaction. Repeated reports at a tick replace that tick's sample. Industry
history stores only ten compact sector summaries; selected-company history
starts at selection, resets when the company changes, and is cleared on reset.
No per-consumer history or full 61,950-firm history is transmitted. Reporting has
no authority to modify economic state or change the canonical tick sequence.

## Bought quantities and tier boundaries

Tier 0 conceptually acquires from Gaia through extraction, but reports its extracted units as Made, never as Bought. Its snapshot bought counter is zero and the comparison displays Bought as not applicable. Extraction remains the same cash cost sink and inventory acquisition used by calculations.

Every producing tier reports COGS at the weighted-average acquisition basis of units actually sold. Gross profit is revenue minus COGS. Tier 0 summaries, element markets, company rows, per-element details, comparisons and chart histories reconcile to this same definition.

Tier 0 separately reports `extractionSpending`, the current cost paid for all units made this tick, and `operatingCashFlow`, revenue minus extraction spending. With no administrative cash change, operating cash flow reconciles to the change in Tier 0 cash; gross profit reconciles to the change in Tier 0 book equity. Gross profit minus operating cash flow equals the change in inventory acquisition value. Selling previously held inventory can therefore produce cash flow above gross profit, while building unsold stock can produce cash flow below gross profit. No extraction cash payment, inventory basis, price-learning observation, production or transaction rule changes. Tier 1 and Tier 2 retain their existing sold-basis COGS; no new cash-flow definition is inferred for them.

Tier 1 buys from Tier 0 and sells only to Tier 2 companies. Tier 2 buys from Tier 1 and sells to external galactic procurement agents. Bought counters record completed input transfers, rather than requests or recipe consumption. Tier 1 bought equals Tier 0 sold, and Tier 2 bought equals Tier 1 sold.

## Customer demand across product complexities

C-1/C-2 customer metrics describe company input purchases; C-3–C-5 metrics describe external galactic purchases. The shared columns are Customer desired, Customer fill and Stock unmet. For each Tier 1 material, desired is the sum of funded received requests across its suppliers (`t1Demand`); fulfilled is actual intermediate delivery (`t1IntermediateSold`); stock unmet is max(0, desired minus fulfilled), and fill is fulfilled/desired. Orders unaffordable at the quoted price are not classified as stock shortages. These metrics describe current purchases, not input consumption or an unfunded full-capacity plan.

Material-market rows and complexity summaries reconcile to Tier 1 totals. Expanded Tier 1 product lines report their own received orders and deliveries. Zero-price latent demand is unmeasured for business buyers and displayed as not applicable. No activity displays an em dash for fill. Final procurement demand for all ten Tier 1 materials remains zero in the end-user arrays and consumer-volume fields. Final-demand spending and fulfillment still include only Tier 2 purchases.

## Robotic Space Generation

The Robotic Space Generation is humanity's industrial vessel in a far-future society preparing for a major galactic war. Robots extract, refine and manufacture for both fleet readiness and civilian continuity: shelter, nutrition, healthcare equipment, learning hardware, communications, transport and industry. WORLD_STORY contains this setting, the final-demand scope and the default million-agent count. Snapshots expose it as world metadata. The fixed population counts demand agents, rather than a demographic population or a count of installed fleets.

Humans are part of the setting, including investors and the people sustained by robotic production. The story introduces no war events, mobilisation multipliers, demographic changes, health-state mechanics or service markets. Nutrition, care, education, defence and repairs are represented by physical goods and equipment using ordinary stock-backed purchases. Agent population stays fixed through ticks; smaller counts are configurable for tests.

## Complete recipe identity and catalogue

| Complexity | Basic-only recipes | One C-2 intermediate | Two C-2 intermediates | Total |
| --- | --- | --- | --- | --- |
| C-3 | 20 | 24 | 0 | 44 |
| C-4 | 35 | 60 | 21 | 116 |
| C-5 | 56 | 120 | 84 | 260 |
| **Total** | **111** | **204** | **105** | **420** |

These are all unordered multisets of the ten Tier 1 materials with ancestry
complexity 3, 4 or 5, including repeated inputs. The test suite independently
counts coefficients of (1-x)^(-4) * (1-x^2)^(-6) through degree five. Unique
valid recipe keys plus the exhaustive count establish complete coverage.

The pool is independently enumerated as weighted multisets. T2-001 through T2-420 identify distinct catalogue recipes. Only invented codes can be traded or installed. Pool recipe codes are internal identifiers, not market aliases; the catalogue displays each good once. Ingredient permutation does not create a second market. Different processed intermediates remain distinct even with equal raw ancestry. The new galactic catalogue replaces earlier human product-code meanings.

Galactic application sectors have no required material. All input dependencies come from each good's recipe. The model rejects duplicate names, duplicate recipe keys, non-goods, missing pool coverage or recipes outside C-3–C-5. Tests independently count the generating-function coefficients and compare complete pool keys with catalogue keys, and check the active subset.

The accepted C-1 capacity increase from 160 to 320 remains; C-2 stays 240 and wholesale lots stay 1,000. Prices respond to funded scarcity, unsold stock and changing costs through local experiments. They do not automatically restore physical capacity or guarantee a perfect fit. Fulfillment must be read alongside quantities, prices and price-suppressed demand.

Product IDs use Uint16 storage to accommodate the full 420-recipe catalogue. The default retains 61,950 Tier 2 firms and 232,000 starting Tier 2 routes. See [the complete goods catalogue](product_catalogue.md).

## Age and profitability calibration

One Age is 480 years × 12 months × 0x1E ticks = 0x2A300 ticks.
Age displays in decimal; tick counts display in hexadecimal with a 0x prefix.
The accepted target is similar percentage equity growth for standard bots in
Tier 0, Tier 1 and Tier 2, with roughly doubled opening book equity in one Age.
This is a calibration objective, not an automatic return or payment rule.
First establish market behavior by research and experiments; then hold those
rules fixed while adjusting demand and supply. See the [research protocol](market_logic_research.md)
and [rebalance status](age_rebalance.md). Current defaults are not validated
against the full-Age target.


### Opening ties and procurement need persistence

At opening, Tier 1 suppliers have no earned Tier 0 relationship. Tied effective raw offers are selected through seeded capacity-share weighting, rather than lowest company ID; prices, stock and earned switching friction retain precedence. A multi-element extraction firm's exposure is divided over its shared production capacity.

Procurement need repetition remembers the considered product independently of unit orders. Only successful fulfillment earns a supplier relationship. This prevents high-quantity products from capturing an unintended extra need-choice weight through the repeat mechanism. Physical quantities still follow each product's exogenous profile and the posted-price demand curve.

Company names reflect human industrial enterprises operated by robotic executives. Tier 0 names identify extraction businesses, Tier 1 names identify material suppliers, and Tier 2 names identify manufacturers spanning fleet supply and civilian continuity. Numbered company names identify distinct firms; they do not denote extra products or change market behavior.
