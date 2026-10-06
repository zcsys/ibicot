<!-- Current rebalance: 200 invented markets, 220 reserved recipes; capital calibration in progress. -->
# Robotic Space Generation — multi-file source project

The Robotic Space Generation is humanity's industrial vessel in a far-future society preparing for a major galactic war. Robotic industry supplies fleet readiness and sustains civilian life through shelter, food production, healthcare equipment, learning hardware, transport and communications. The 420 distinct manufacturing routes contain 200 invented physical goods markets and 220 reserves. One million external procurement agents represent the wider economy; every traded output is a physical good.

This directory contains the editable Phase 0 simulator.

Application parameters remain uncalibrated. The active [calibration status](spec/economy_calibration_status.md) distinguishes completed diagnostics, fixed-rule revisions and pending actual-Age validation. One Age is 480 years, or 172,800 actual ticks; a short-window result does not establish doubling.

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

The overview reports the whole economy, followed by the extraction environment, extraction (T0),
materials (T1), finished goods (T2), and external procurement (T3). Each producing tier
keeps its summary, markets, cohorts where applicable, and company details
together. External procurement purchases and spending count final sales once; producer
sales and revenues include intermediate transactions. Holdings are current
balances; production, sales, costs, and revenue are per tick.

Overview graphs compare all producing tiers. Use Chart scope to inspect one
tier on its own scale. Market price graphs show individual elements or a
selected T1 product; T2 graphs can follow one industry. Hover trend graphs for
exact values. Company graphs begin when a T0/T1 row is expanded or a T2 firm is
selected, retain up to 240 reported ticks, and restart on reset. Undefined
ratios display as an em dash. Every tier displays COGS at the acquisition basis of units sold and gross profit as revenue minus COGS. Tier 0 separately shows extraction spending and operating cash flow, which is revenue minus extraction spending. Unsold extraction remains inventory; it does not reduce sold-cost gross profit.

**Edit**

Start with `engine/model.js` and `engine/reference_kernel.js` for the economic
model, then use `phase0_economy_engine_worker.js` for orchestration and
`phase0_economy_engine_app.js` for the UI.

The complete simulation is source-controlled. Its rules and invariants are
documented in [the economic contract](spec/economy_contract.md), and covered
by the tests in `tests/`.

**Live Tier 2 economy**

The default world contains 20 Tier 0 extractors, 1,000 Tier 1 material firms,
61,950 Tier 2 manufacturers, and 1,000,000 individually modeled external Tier 3 procurement agents.
Tier 0 extracts Water, Earth, Fire and Air. Tier 1 refines ten
materials exclusively for downstream fabricators. Tier 2 purchases
all ingredients from Tier 1; it never bypasses refineries to buy raw resources.
The complete C-3–C-5 pool contains 420 recipes. Each sector starts with 2 C-3, 6 C-4 and 12 C-5 invented goods; 220 recipes remain reserved. Sectors organize galactic applications independently of input materials. Every good has a unique market code and a distinct processed-input recipe.

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

See the [complete product map](spec/product_catalogue.md) for all goods, physical forms, processed inputs and raw ancestry.

The planned game casts the player as a human investor in the Robotic Space Generation, competing with opportunist human investors and robotic executive agents. Its future alpha player scope is Tier 1; Tier 2 is planned as a later playable tier. This is story and release intent, not a restriction on the economy-core simulator's admin tools.

In **Selected company control · Admin**, choose either Tier 1 or Tier 2. Select **Human investor**, an installed product and its price, then **Apply control**. Cash, inventory, equipment and trading relationships carry over. Procurement and production continue automatically. **Buy equipment** installs an eligible product line under the normal cash, sector and portfolio constraints. Returning to **Robotic executive** resumes bot pricing and expansion. Admin controls remain available for both tiers regardless of planned player release scope.

The economy operates under bots independently of takeover. Initial investment describes future entry into an existing business; acquisition pricing, onboarding, investor wallets and multiplayer are outside the current economic-core work. Takeover adds no artificial capital or preferred customers.

The Tier 2 company table searches all 61,950 firms in the worker, transmitting
only a 50-row page. Consumers have persistent 2–5-sector baskets and earned
supplier relationships; their unlimited cash is a deliberate source of retail
revenue. Price sensitivity and availability still limit completed purchases.

**Verify**

Run the complete quality gate with `node tests/economy_quality.js`, or use
`node tests/economy_quality.js --quick` for contracts and shock scenarios.
The complete gate adds two full-population 0xE10-tick runs (seeds 12345 and
31415), checking market survival, firm participation, inventory coverage,
profitability, cash conservation, and variable-cost boundary trading in all 214 active
markets. Boundary concentration is recorded rather than automatically rejected:
competitive break-even prices are different from a forced profit floor. Behavioral
tests also check price discovery, independent values, recipe purchasing, missed
orders, actual undercuts and stockout alternatives. Detailed reports and
individual check logs are saved under `reports/`.

From the project directory with Node.js:

```sh
node tests/model_contract.test.js
node tests/galactic_catalogue.test.js
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

The live scenarios always run the actual 61,950-firm / 1,000,000-consumer
population. They check every product in rolling 0x168-tick windows, prices,
portfolios, cash-flow accounting, and prolonged market health. The shock scenario
tests a material outage, recovery, and price elasticity. The contract tests cover
takeover, machinery validation, intermediate transactions, consumer baskets,
atomic orders, reset determinism, and scheduler equivalence.

The long-run balance audit also checks cumulative cash conservation, hard
inventory bounds, continued production in all material/final markets, trading
firm counts, realized margins, and installed-capacity utilization. It reports
0x168-tick windows so that passing solvency tests is not confused with balanced
capital or realistic stock coverage. `BALANCE_T0_CASH` compares Tier 0 cash
endowments without changing the production, inventory or consumer parameters.

The price-bound audit runs 0xE10 ticks at full population and records actual
traded quantities at each market's variable-cost boundary over the
final 0x168 ticks. It uses the quotes paid during Tier 0 procurement and actual delivered
COGS for downstream sales. Reports include exact and within-1% volume shares,
boundary-trading tick counts and all 214 active
markets individually, saved under `reports/`. Override `PRICE_AUDIT_TICKS`,
`PRICE_AUDIT_WINDOW`, `PRICE_AUDIT_SEED`, or `PRICE_AUDIT_OUTPUT` as needed.
Set `PRICE_AUDIT_ENFORCE=1` to enforce the same per-market pricing gates.

**Pricing, purchasing and inventories**

Sellers discover prices through small local experiments: continue an experimental
direction if realized total gross profit improves, reverse it if profit falls.
Stocked sellers with no sales reduce their quotes. The default observation
interval is 0x1E ticks, staggered across sellers. There is no normal-markup target
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
and two full-population 0xE10-tick runs.
[Earlier validation results](reports/market-learning-repair.md) include two
0xE10-tick runs and actual undercut/stockout comparisons. They explicitly report
remaining break-even concentration and the model's limits.

The performance status reports actual browser tick duration, typed-array state
memory, active consumers, and product-line counts. Run Max and Step use the same
canonical kernel. Initial warm-up is slower than established operation.

**Demand-led calibration**

The earlier audit found a solvent but poorly calibrated economy: 1.274%
Tier 2 utilization, 0x9B ticks of finished stock, and only 4,919 trading firms
in its final 0x168-tick window. A paired $1 million/$5 million Tier 0 cash test
had the same production and stock, so the original $1 million was restored.

The new reset defaults are authoritative in `engine/model.js` and shared by
the worker and browser. Tier 0 throughput is 10,000 units per company per tick,
with 500,000 desired and 1,000,000 maximum warehouse units. Tier 1 C-1/C-2
throughput is 320/240; finished-stock desired/max ceilings are 600/1,200 per
line. C-1 throughput rose from 160 to 320 for the complete catalogue: all four
basic-material markets were saturated at 160, lowering fulfillment and failing
the healthy-baseline supply-shock check. Tier 0-to-Tier 1 wholesale transactions clear in funded 1,000-unit lots. Tier 2 factory capacity is six units per tick, shared across its one to four
routes. Inventory includes ingredients and finished goods, with compounds occupying one unit each. These are simulation-scale operating assumptions, not
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

The calibration audit reports 0x168-tick windows for stock coverage, utilization,
trading firm participation and margins, as well as accounting and market health.
Current initial typed-array state is approximately 122.1 MiB, including separate
order/sales forecasts and price-learning observations. Performance observations are
not device-independent guarantees.

Historical reports describe earlier catalogues. Current checks verify 420 catalogue recipe identities and 200 invented markets, zero service markets, input dependencies, large product IDs, external galactic procurement, comparisons and market balance. The historical, all-invented [0x2D0-tick full-population audit](reports/robotic-space-generation-12345-720.json) passed with all 420 goods and all ten Tier 1 material markets producing and trading. The final 0x168 ticks fulfilled 99.46% of desired units, purchased 61,420.71 units per tick and had 49,977 Tier 2 firms trading. Utilization was 18.84%, realized gross margin was 11.76%, and maximum cash-ledger residual was below $0.000014. These are observed results for this seed and window, not demand targets or guarantees.

**Tier and product category comparisons**

The overview includes a sortable current-tick producer table for T0, T1 and T2,
with cash, equity, inventory, production, sales, revenue, cost and profit figures,
plus cash and revenue per firm. Tier 0 extraction is reported as Made, with Bought shown as not applicable. Its COGS uses the acquisition basis of elements sold. Gross profit reconciles to book-equity change, while operating cash flow reconciles to cash change. Tier 0 company rows, expanded details, element markets and charts also show extraction spending and use these same definitions.

A C-1 through C-5 comparison adds machinery cost and capacity per line, installed
lines, posted prices and unit costs, utilization, stock, sales, margins and customer
fulfillment. Its chart can compare totals or sales and profit per line. Category
activity follows installed products, including expanded portfolios; prices and unit
costs are weighted by installed lines. C-1 and C-2 serve companies exclusively: customer desired units are funded company input orders, fulfilled units are actual deliveries, stock unmet is desired minus delivered, and fill is delivered/desired. C-3–C-5 customer metrics refer to external galactic procurement agents. Zero-price latent demand is not measured for company buyers. Population demand for C-1/C-2 remains zero. Tier 2 product markets
also show direct recipes and support combined
sector, complexity and recipe search filters.

**Tier 2 industry and company analytics**

The manufacturing dashboard includes sortable industry-market tables, home-sector
company cohorts, and complexity bands. Product markets show recipes (hover the
name), average costs, gross margins, capacity utilization and unmet consumer demand.
Industry charts can follow all Tier 2 goods or one sector; sector comparisons can
show revenue, profit, sales, utilization or fulfillment. Economy inventory and
book-equity charts also include Tier 2.

Select a Tier 2 company to inspect its balance sheet, installed recipes, per-line
performance, input consumption and last upstream suppliers. Company charts track
output, revenue/COGS/profit and cash/book equity from selection onward. Histories
retain up to 240 reported ticks, replace repeated samples of the same tick, and
restart when the selected company changes. No histories or individual records for
the million consumers are transferred. Company tables remain 50-row worker pages;
financial and operational sorting applies across the full filtered population.

Utilization means production / installed capacity, not sales / capacity. Gross
margin is realized gross profit / revenue, and input coverage uses full installed
capacity (not a forecast). Bot companies are labeled Automated; online/offline is
player-session status and does not suspend automatic procurement or production.
The dashboard additionally reports finished stock / sales EMA and the number
of firms with a successful sale in the latest 0x168 ticks, including inactive
companies in the population denominator. These metrics distinguish spare
capacity from commercially stranded firms.

**Complexity, machinery, and initial capital**

Tier 1 C-1/C-2 machinery costs $15,000/$75,000, with 320/240 units per tick.
The current Tier 2 draft grants one $300,000 shared factory per company;
adding a route costs $1,000 and shares that factory's six-unit output budget.
These capital assumptions are under review and have not been validated against the Age target.

Each of ten sectors has one firm for each unordered portfolio of one to four of
its twenty active goods: 20 + 190 + 1,140 + 4,845 = 6,195 firms per sector,
61,950 total. There are 232,000 starting routes; each product has 1,160 suppliers.
All routes stay within the company's sector. The factory's 60-unit warehouse
includes raw inputs, compound inputs and finished products; each compound unit
counts as one storage unit. Starting working cash covers estimated operating
costs, with a $2,500 minimum. Capital values do not determine the cash grant.

Tier 0 extraction is reported under Made; Bought is zero. Its extraction spending
is included in COGS. Tier 1 buys from Tier 0; Tier 2 buys processed materials from
Tier 1. All ten Tier 1 products have company customers only.

The accepted calibration target is comparable return on equity across **all three
producer tiers**, including Tier 0, and roughly doubled equity after one Age.
An Age is 0x2A300 ticks; Age is decimal and tick counts use a 0x hexadecimal prefix.
The [research protocol](spec/market_logic_research.md) separates market-rule
experiments from subsequent demand/supply calibration. No automatic payout or
guaranteed return implements this target. Current defaults are a research draft.

**Final customer demand — accepted baseline**

One million external procurement agents independently activate with 10% probability
per tick and attempt at most one purchase. Persistent baskets contain 2–5 sectors;
60% of shopping occasions select the primary sector. Products have authored
selection weights, a 65% repeat-product preference after a considered need,
complexity-scaled quantities and individual price sensitivity. Consumers have
unlimited money, sample five seller offers plus a previous supplier, and require
complete delivery from one seller. Public demand is exclusively for Tier 2.

The [consumer demand contract](spec/economy_contract.md#tier-3-consumers) documents
the formula, default selection shares, supplier discovery, demand metrics and
current limitations. Reported latent demand uses the same stochastic whole-unit
rounding draw as priced orders, and products share a repeat-purchase mechanism without
ownership, replacement schedules or accumulated unmet needs.

Invention, creation of new products, and a marketing and visibility layer are
planned future ways to expand demand. Their design and implementation are deferred
to a later phase; the current demand model remains the accepted baseline.

**Recipe identity and galactic demand**

All 420 recipes have distinct catalogue codes and names; 200 currently have active market inventory, quotes, demand and analytics. WF + A and A + WF describe one recipe. W + FA has different processed inputs despite matching raw ancestry. Ingredient order is ignored; processed intermediates retain identity. The independent pool and complete catalogue recipe keys are equal; active markets form a 200-recipe subset.

The story is metadata in WORLD_STORY. Demand records represent procurement for civilian settlements, industrial operations and fleets. They aggregate the needs of a human society through purchasing agents; the million-agent count is not a demographic population. Agent count stays at 1,000,000 in the default world; smaller populations remain available for tests. No demographic, immortality, health, fleet installation or service mechanics are present. Future invention and marketing are deferred.
