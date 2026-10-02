# Midbridge Economy — multi-file source project

Robots operate Midbridge, an Earth colony, as a consumer behavior experiment with exactly
one million immortal humans. Its residents are selected individuals who sought
immortality and worked their way toward sealing the Infinity contract. Under
that contract, robots satisfy their needs and receive their consumerism in return.
Most humans elsewhere work in many roles for robots under poor conditions.
Inside this experimental colony, robots extract resources and manufacture goods.
Immortality Treatment is a purchasable healthcare product, with no additional
health or demographic simulation.

This directory contains the editable Phase 0 simulator.

**Run**

Double-click the launcher for your operating system. Each starts the local
server and opens the simulator in your browser. Keep its terminal window open;
press Ctrl+C there to stop it.

| Operating system | Launcher |
| --- | --- |
| macOS | **Start Phase 0.command** |
| Windows | **Start Phase 0.bat** |
| Linux | **Start Phase 0.sh** |

On Linux, make the launcher executable once if your file manager does not
offer to run it: `chmod +x 'Start Phase 0.sh'`. Then double-click it and choose
“Run” when prompted.

From a terminal on any platform with Python 3:

```bash
python3 serve.py
```

Use the HTTP address printed by the launcher. Opening the HTML directly as a
`file:` URL cannot run browser workers.

**Dashboard**

The overview reports the whole economy, followed by the Earth environment, extraction (T0),
materials (T1), finished goods (T2), and consumers (T3). Each producing tier
keeps its summary, markets, cohorts where applicable, and company details
together. Consumer purchases and spending count final sales once; producer
sales and revenues include intermediate transactions. Holdings are current
balances; production, sales, costs, and revenue are per tick.

Overview graphs compare all producing tiers. Use Chart scope to inspect one
tier on its own scale. Market price graphs show individual elements or a
selected T1 product; T2 graphs can follow one industry. Hover trend graphs for
exact values. Company graphs begin when a T0/T1 row is expanded or a T2 firm is
selected, retain up to 240 reported ticks, and restart on reset. Undefined
ratios display as an em dash. T0 revenue less extraction spending is operating
cash flow; T1/T2 gross profit deducts the cost of goods sold.

**Edit**

Start with `engine/model.js` and `engine/reference_kernel.js` for the economic
model, then use `phase0_economy_engine_worker.js` for orchestration and
`phase0_economy_engine_app.js` for the UI.

The complete simulation is source-controlled. Its rules and invariants are
documented in [the economic contract](spec/economy_contract.md), and covered
by the tests in `tests/`.

**Live Tier 2 economy**

The default world contains 20 Tier 0 extractors, 1,000 Tier 1 material firms,
50,000 Tier 2 manufacturers, and 1,000,000 individually modeled Tier 3 consumers.
Tier 0 extracts Water, Earth, Fire and Air. Tier 1 refines ten
materials exclusively for downstream fabricators. Tier 2 purchases
all ingredients from Tier 1; it never bypasses refineries to buy raw resources.
The 60 consumer products span exactly ten sectors: 20 C-3, 20 C-4
and 20 C-5. Every sector has six products, two in each complexity band.
Each product has a distinct name, input recipe and expanded elemental composition.
Every product consumes its sector's required material:

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

Sector adjacency follows related human needs and manufacturing inputs. Robot
companies operate resource works, material refineries and consumer-goods factories.
The ten Tier 1 material codes remain usable in controls. Each Tier 2 product has
one fresh code, T2-001 through T2-060. See the [complete product
map](spec/product_catalogue.md) for all recipes and elemental compositions.

In **Selected company control**, choose **Tier 2 consumer goods** and enter a
company number, or click a Tier 2 company row. Select **PLAYER**, choose an
installed product, enter its price, and apply control. Procurement and production
remain automatic. Use **Buy equipment** to add an eligible neighboring-sector
product line, subject to cash, capability, and the five-line portfolio limit.
Turning a firm offline preserves its player prices; returning it to BOT resumes
automatic pricing and monthly expansion.

The Tier 2 company table searches all 50,000 firms in the worker, transmitting
only a 50-row page. Consumers have persistent 2–5-sector baskets and earned
supplier relationships; their unlimited cash is a deliberate source of retail
revenue. Price sensitivity and availability still limit completed purchases.

**Verify**

Run the complete quality gate with `node tests/economy_quality.js`, or use
`node tests/economy_quality.js --quick` for contracts and shock scenarios.
The complete gate adds two full-population 3,600-tick runs (seeds 12345 and
31415), checking market survival, firm participation, inventory coverage,
profitability, cash conservation, and variable-cost boundary trading in all 74
markets. Boundary concentration is recorded rather than automatically rejected:
competitive break-even prices are different from a forced profit floor. Behavioral
tests also check price discovery, independent values, recipe purchasing, missed
orders, actual undercuts and stockout alternatives. Detailed reports and
individual check logs are saved under `reports/`.

From the project directory with Node.js:

```sh
node tests/model_contract.test.js
node tests/colony_catalogue.test.js
node tests/pricing_model.test.js
node tests/price_audit.test.js
node tests/tier_boundaries.test.js
node tests/compound_consumers.test.js
node tests/inventory_limits.test.js
node tests/calibration_contract.test.js
node tests/source_engine.test.js
node tests/tier2_contract.test.js
node tests/ui_actions.test.js
node tests/scheduler.test.js
node tests/dashboard.test.js
node tests/comparisons.test.js
node tests/tier2_analytics.test.js
node tests/live_scenarios.test.js
node tests/market_shocks.test.js
node tests/market_competition.test.js
node tests/market_scarcity.test.js
node tests/player_strategy.test.js
SCENARIO_TICKS=3600 node tests/live_scenarios.test.js
SCENARIO_SEEDS=31415,27182 node tests/live_scenarios.test.js
node tests/long_run_balance.test.js
BALANCE_TICKS=7200 node tests/long_run_balance.test.js
BALANCE_SEED=31415 node tests/long_run_balance.test.js
node tests/price_bound_audit.js
```

The live scenarios always run the actual 50,000-firm / 1,000,000-consumer
population. They check every product in rolling 360-tick windows, prices,
portfolios, cash-flow accounting, and prolonged market health. The shock scenario
tests a material outage, recovery, and price elasticity. The contract tests cover
takeover, machinery validation, intermediate transactions, consumer baskets,
atomic orders, reset determinism, and scheduler equivalence.

The long-run balance audit also checks cumulative cash conservation, hard
inventory bounds, continued production in all material/final markets, trading
firm counts, realized margins, and installed-capacity utilization. It reports
360-tick windows so that passing solvency tests is not confused with balanced
capital or realistic stock coverage. `BALANCE_T0_CASH` compares Tier 0 cash
endowments without changing the production, inventory or consumer parameters.

The price-bound audit runs 3,600 ticks at full population and records actual
traded quantities at each market's variable-cost boundary over the
final 360 ticks. It uses the quotes paid during Tier 0 procurement and actual delivered
COGS for downstream sales. Reports include exact and within-1% volume shares,
boundary-trading tick counts and all 74
markets individually, saved under `reports/`. Override `PRICE_AUDIT_TICKS`,
`PRICE_AUDIT_WINDOW`, `PRICE_AUDIT_SEED`, or `PRICE_AUDIT_OUTPUT` as needed.
Set `PRICE_AUDIT_ENFORCE=1` to enforce the same per-market pricing gates.

**Pricing, purchasing and inventories**

Sellers discover prices through small local experiments: continue an experimental
direction if realized total gross profit improves, reverse it if profit falls.
Stocked sellers with no sales reduce their quotes. The default observation
interval is 30 ticks, staggered across sellers. There is no normal-markup target
or consumer-derived seller ceiling. Starting markups initialize offers only;
variable costs provide a break-even reservation, without a guaranteed margin.

Scarcity enters through observed orders exceeding delivered units plus closing
stock. This can make even a sold-out seller try a higher quote. When all business
suppliers are empty, affordable requests reach a known posted supplier instead
of being silently dropped. Price experiments shrink on directional reversals;
no quality, location, service or required positive margin has been added.

Manufacturers' input demand is derived from downstream orders, recipes and
inventory deficits. Complete recipes are checked against the output quote before
new inputs are purchased, and actual costs are checked before manufacture.
Replenishment forecasts include requested units that could not be served, while
reported sales and stock/sales coverage use distinct realized-sales observations.

Consumers' value scales are specified independently of seller costs and markups.
Consumers compare five sampled posted offers plus a previous successful supplier,
choose according to prices and switching friction, and try discovered alternatives
on a stockout. An undercut can attract buyers, but finite stock/capacity still
limits deliveries. A cheaper price can improve volume without guaranteeing higher
profit. Trading happens at actual offers, not at an imposed curve intersection.

See [the full economic contract](spec/economy_contract.md) for quantities,
information sets, tick order, startup assumptions and all buyer/seller rules.
[The research and selection notes](spec/pricing_research.md) link the primary
literature and explain the adaptations. The earlier
[cost-and-stock repair](reports/economy-pricing-repair.md) is historical: it
avoided the old floor trap but prescribed margins, and has been superseded.

[Current scarcity and pricing validation](reports/scarcity-aware-repair.md)
checks prices starting at cost, input stockouts, constrained workshop supply,
and two full-population 3,600-tick runs.
[Earlier validation results](reports/market-learning-repair.md) include two
3,600-tick runs and actual undercut/stockout comparisons. They explicitly report
remaining break-even concentration and the model's limits.

The performance status reports actual browser tick duration, typed-array state
memory, active consumers, and product-line counts. Run Max and Step use the same
canonical kernel. Initial warm-up is slower than established operation.

**Demand-led calibration**

The earlier audit found a solvent but poorly calibrated economy: 1.274%
Tier 2 utilization, 155 ticks of finished stock, and only 4,919 trading firms
in its final 360-tick window. A paired $1 million/$5 million Tier 0 cash test
had the same production and stock, so the original $1 million was restored.

The new reset defaults are authoritative in `engine/model.js` and shared by
the worker and browser. Tier 0 throughput is 20,000 units per company per tick,
with 60,000 desired and 120,000 maximum warehouse units. Tier 1 C-1/C-2
throughput is 160/240; finished-stock desired/max ceilings are 600/1,200 per
line. Wholesale transactions retain funded lot-sized clearing, with 10-unit
lots instead of 1,000-unit lots. Tier 2 workshop capacity is 3/2/1 units per
C-3/C-4/C-5 line. These are simulation-scale operating assumptions, not
empirical industry estimates.

Both manufacturing tiers target three ticks of their own observed orders, bounded
by finished-stock ceilings and a small bootstrap stock. Procurement and
production now follow the same target. Unsold firms do not continually fill
warehouses to nameplate-capacity limits. Capital reserves depend on operating
costs rather than expensive machinery book values. There are no privileged
player output, supplier, demand or cash multipliers: player advantage must come
from pricing, portfolios and successful customer relationships. Spare capacity
and unmet demand remain valid outcomes; the population is not assigned to firms
to manufacture a perfect fit. The unlimited-consumer-cash injection and the
absence of recurring fixed costs remain explicit simplifications.

The calibration audit reports 360-tick windows for stock coverage, utilization,
trading firm participation and margins, as well as accounting and market health.
Current initial typed-array state is approximately 121.4 MB, including separate
order/sales forecasts and price-learning observations. Performance observations are
not device-independent guarantees.

Historical calibration reports used earlier catalogues and do not verify the
current 60-product model. Current checks cover distinct recipes and elemental
compositions, sector dependencies, public purchases, price controls, equipment,
market competition, inventory limits and full-population balance.
The current 720-tick run (seed 12345) passed with all 60 product markets
active and all 50,000 Tier 2 firms trading in the final window. Desired-unit
fulfillment was 82.34%, utilization 15.00%, and gross margin 23.62%. The
maximum cash-ledger residual was $0.000012. See
[the current catalogue audit](reports/distinct-colony-catalogue-12345-720.json).

**Tier and product category comparisons**

The overview includes a sortable current-tick producer table for T0, T1 and T2,
with cash, equity, inventory, production, sales, revenue, cost and profit figures,
plus cash and revenue per firm. Extraction spending and operating cash flow remain
separate from manufacturing COGS and gross profit because their cost bases differ.

A C-1 through C-5 comparison adds machinery cost and capacity per line, installed
lines, posted prices and unit costs, utilization, stock, sales, margins and consumer
fulfillment. Its chart can compare totals or sales and profit per line. Category
activity follows installed products, including expanded portfolios; prices and unit
costs are weighted by installed lines. C-1 and C-2 serve companies exclusively; public demand is zero and public
fulfillment is unavailable. Tier 2 product markets
also show direct recipes and support combined
sector, complexity and recipe search filters.

**Tier 2 industry and company analytics**

The manufacturing dashboard includes sortable industry-market tables, home-sector
company cohorts, and complexity bands. Product markets show recipes (hover the
name), average costs, gross margins, capacity utilization and unmet consumer demand.
Industry charts can follow all Tier 2 goods or one sector; sector comparisons can
show revenue, profit, sales, utilization or fulfillment. Economy inventory and
marked-equity charts also include Tier 2.

Select a Tier 2 company to inspect its balance sheet, installed recipes, per-line
performance, input consumption and last upstream suppliers. Company charts track
output, revenue/COGS/profit and cash/marked equity from selection onward. Histories
retain up to 240 reported ticks, replace repeated samples of the same tick, and
restart when the selected company changes. No histories or individual records for
the million consumers are transferred. Company tables remain 50-row worker pages;
financial and operational sorting applies across the full filtered population.

Utilization means production / installed capacity, not sales / capacity. Gross
margin is realized gross profit / revenue, and input coverage uses full installed
capacity (not a forecast). Bot companies are labeled Automated; online/offline is
player-session status and does not suspend automatic procurement or production.
The dashboard additionally reports finished stock / sales EMA and the number
of firms with a successful sale in the latest 360 ticks, including inactive
companies in the population denominator. These metrics distinguish spare
capacity from commercially stranded firms.

**Complexity, machinery, and initial capital**

Machinery uses one global rule: $15,000 × 5^(C−1). C-1 refinery lines cost
$15,000; C-2 substance factories cost $75,000; Tier 2 C-3/C-4/C-5 lines
cost $375,000/$1,875,000/$9,375,000 and can make 3/2/1 units per tick.
Tier 1 bulk throughput is 160/240 units per tick for C-1/C-2.
Starting equipment is granted, with future purchases deducted from cash.
With $5,000 cash and no inventory, the 400 C-1 Tier 1 firms start at
$20,000 equity each, and the 600 C-2 firms at $80,000 each: $56 million total.

Tier 2 capabilities 3/4/5 contain 30,000/15,000/5,000 firms, starting with
2/3/4 related lines respectively (125,000 lines total). Core allocation uses
explicit sector/product need priors plus seeded ±20% variation, not product-ID
weight cycling or a fitted normal distribution. Tier 2 working cash covers
30 ticks of estimated full-capacity Tier 1 input/conversion cost plus a small
C-1 material buffer, rounded up to $50 with a $500 minimum. Starting equity is this cash
plus the granted portfolio's equipment book value. Human consumers buy only Tier 2 C-3–C-5 finished goods. Tier 1 C-1 and C-2
public demand is zero; all ten materials are business inputs. Every activated
need selects a product within the consumer's Tier 2 sector basket. Each tick
manufacturers purchase and produce before consumers shop finished stock.

The tier comparison includes actual bought units: Tier 0 extraction counts as
buying from Gaia, Tier 1 buys raw resources from Tier 0, and Tier 2 buys processed
materials from Tier 1. Tier 0 has no separate manufactured-output entry. Buying
from Gaia is the existing extraction cost sink, not an additional cash transfer.
Refresh and reset an open simulator to apply the new demand topology.

Tier 2 starting cash and equity are recomputed from each seeded portfolio's
actual Tier 1 input costs and granted machinery. The dashboard reports these
values; machinery book value does not set the operating reserve.
Equipment remains an intentionally steep
capital purchase; these operating/solvency tests do not guarantee a particular
machinery payback period or a player investment return.

**Recipe identity and immortality**

Each of the 60 products has one code and its own inventory, price, machinery,
demand and analytics. Ingredient order cannot create another product: F + WA
and WA + F both describe Yoga Pants. No two catalogue products share either
an unordered Tier 1 recipe or an expanded Water/Earth/Fire/Air composition.
The model rejects either kind of duplicate when loading the catalogue.

Immortality Treatment belongs to Healthcare & Wellness and consumes Thermal
Compounds, Semiconductor Substrate and Chemical Feedstock (WF + EF + A, C-5).
It uses the same stock, price, consumer demand, receipts and COGS rules as every
other good. All colony humans are immortal by story premise, including when
an order is missed. There are no mortality, health, aging, birth, migration or
contract-state mechanics. Default colony population remains exactly 1,000,000;
smaller populations are used only by configurable test scenarios.
