# Invented catalog and weighted Distributor demand

Current experiment: storage rent is disabled (`storageRentPerUnitYear = 0`).
The zero-rent run starts from tick zero, records per-tick statistics in its own
`stats/zero-rent-one-generation-*` directory, and pauses at tick 7,200.
Paid-rent calculations elsewhere in this document describe the prior $2.80 per
1,000 storage spaces per tick setting, not the current experiment.

### Profitability recording

Producer comparison includes complexity subrows with actual company cash, equity,
inventory and purchases, in addition to production and P&L. The single-line
starting fleet groups each company's full balances into its complexity. Companies
with multiple complexities share common balances equally across installed lines,
matching overhead allocation. Complexity totals reconcile to their parent tier;
cash per firm uses the distinct company count of that row. The projection uses
NumPy reductions and `bincount` and does not change simulation state.

Statistics schema 2 adds `productProfitability` to every tick: revenue, COGS,
units sold, gross profit, rent, switching income/expense, posted net earnings,
and gross/net margins for each T0/T1/T2 product. Stable product, complexity and
sector labels allow C1, C2, C3 and the two C4 routes to be compared separately.
Period margins must be computed from summed earnings divided by summed revenue;
zero-revenue margins are null. Company overhead is allocated equally among its
installed lines, following the accounting/UI policy. Product allocations reconcile
to posted company earnings; earnings are not defined as equity changes.

Both browser and headless runs with stats produce a separate `company-history-*`
directory. Compressed company archives contain annual P&L/units-sold totals,
ending cash/equity and line ownership. Pausing flushes partial periods with explicit
start/end ticks; those intervals can be summed without losing company distributions.
The directory preserves configuration, catalog labels and hexadecimal ID ranges.
Automatic end-of-generation pauses also save a full checkpoint. Headless runs with
stats save a checkpoint on completion. Aggregation uses NumPy reductions/bincount,
not Python loops over companies. Ordinary UI snapshots remain unchanged.

Legacy logs lack these details. `tools/recover_run_statistics.py RUN_DIRECTORY`
replays the saved initial configuration into a separate output directory and
checks every original recorded field on every tick. It stops on a mismatch;
only successfully verified replay intervals can be treated as recovered history.

## Current selection

The recipe universe remains 269 outputs: 14 T1 recipes and 255 possible T2 recipes. `catalogs/midbridge-4259-recursive/starting-selection.json` is the authoritative list of initially invented T2 recipe IDs. It activates **105** and leaves **150 uninvented**:

| Route | Invented | Uninvented |
|---|---:|---:|
| C3: C1+C2 | 36 | 4 |
| C4: C1+C3 | 14 | 146 |
| C4: C2+C2 | 55 | 0 |

All fourteen T1 materials and all fourteen T2 sectors are represented. Every selected C4 dependency is invented. No formula, sector assignment, preferred material, raw ancestry or recipe yield is changed. The full catalog remains available for naming/reference; uninvented recipes have no initial companies, Distributor orders, supplier markets or purchasable installations. Automatic research/unlocking is not introduced by this change.

Runtime product IDs are compact array indices, with invented products first; stable recipe IDs such as C3-001 remain unchanged. The live input market contains 14 T1 materials and 36 invented C3 intermediates (50 markets). Uninvented records retain their full `ingredientCatalogIds` and formulas but have no executable compact `ingredients` array.

## Demand and production

The main-branch allocation principle is restored: reverse product-count shares
across complexities to obtain company shares, then divide companies equally among
products within each complexity. With 36 C3 and 69 C4 products, product shares are
12:23 and company shares are 23:12. The two C4 recipe routes receive the same
per-product treatment. There is no longer a 4:1:8 final-demand policy.

Distributor weights are per-product **default output capacity minus intermediate
use**. Each C4 unit requires its recipe's inputs; the C3 quantity required at full
C4 capacity is reserved before routing final purchases. Thus back-propagating
weighted final demand recovers each product's gross capacity exactly. A C3 product
without a downstream customer has weight 33,856; one supplying a C4 product has
weight 26,944. C4 weights are 6,912. All uninvented weights remain zero.
This is a nominal flow calibration, not a physical inventory reservation.

One million Distributors still activate at **10.5% per tick**, approximately
105,000 buyers. With 20 latent units each, expected latent demand is 2.1 million
items/tick before price attenuation. Total final-output weight is 1,598,976;
96,768 of gross manufacturing capacity supplies intermediate C3 use. Routing is
vectorized and stratified at initialization. Weights use the default full starting
fleet, not live utilization or shortages; custom machine-capacity settings do not
automatically rebalance them. **Refined-material demand remains unequal.** The
independent recipe-flow check in `tools/calibrate_recursive_consumption.py` verifies
capacity coverage and space conservation; its JSON report lists material demand.

At the default seed (137), the million actual Distributor assignments are:

| Product group | Products | Assigned Distributors | Per product | Expected retail demand / final capacity |
| --- | ---: | ---: | ---: | ---: |
| C3 without a C4 customer | 22 | 465,818 | 21,173–21,174 | 116.45–116.52% |
| C3 supplying C4 | 14 | 235,911 | 16,850–16,851 | 116.42–116.56% |
| C4 basic + C3 | 14 | 60,519 | 4,322–4,323 | 120.02–120.20% |
| C4 compound + compound | 55 | 237,752 | 4,322–4,323 | 119.97–120.19% |

These are permanent buyer assignments, with 10.5% expected to activate each tick.
The one-buyer differences are integer rounding of proportional shares. Using each
buyer's initialized price sensitivity at the starting quotes gives approximately
1,879,707 final units/tick of expected demand versus 1,598,976 final capacity.
Every individual product has sufficient expected demand; C4's slightly larger
coverage follows its existing reservation premium. No new demand multiplier is
needed. This checks potential demand, not guaranteed purchases: stock, supplier
search, changing prices and production profitability still constrain sales.
`test_default_distributor_cohorts_cover_every_products_final_capacity` independently
reserves full-capacity intermediate consumption and checks all 105 actual cohorts.

## Company allocation

There are **1,008 refineries**, 72 per material: 288 C1 and 720 C2. Both C1 and
C2 machines have a nominal throughput of **6,000 items/tick**. The common rate
needed to cover the largest material requirement is 332,352 / 72 = 4,616;
6,000 preserves the existing C1 rate and gives that material 99,648 headroom.
Nominal installed capacity is 6,048,000: C1 1,728,000 and C2 4,320,000, with
432,000 per material. Full starting T2 production requires 1,315,584 C1 and
1,979,136 C2. All individual material requirements fit the installed rates.

Both C1 and C2 refinery cohorts have **50,000 storage spaces**
(`t1C1Storage` and `t1C2Storage`); T2 manufacturers retain **20,000** (`storage`). Pool size is
attached to the firm's native material cohort, so buying additional machinery
does not silently grant more storage. Total refinery storage is 50,400,000.
A single-line C1 refinery has 24,500 finished-item spaces and 24,500 raw-input
spaces, supporting a 24,500-unit finished target (4.08 full production ticks).
For a single-line C2 refinery: 1,000 machinery spaces leave 49,000 goods spaces,
24,500 each for ingredients and finished goods. The finished target is 12,250
items; mixed recipes have 12,250 spaces per raw ingredient and repeated recipes
24,500 for their one ingredient. Even with 1,000-unit wholesale lots, both
routes can replenish enough to run the 6,000-unit machine at full capacity.
Cash, stock, prices and profitability still constrain actual production.

Rent keeps its existing per-space rate and equity exemption: an eligible C1 or C2
refinery pays $140/tick, while T2 remains at $56. Forecast production
costs, settlement, accounting, storage validation and company reporting use the
same cohort-specific pool. The T1 rent summary displays $140/tick (or a range if the class settings differ). Compiled
procurement and production index a cached, read-only NumPy firm-capacity array;
rent and validation remain vectorized. Cache keys include both storage settings.
Legacy configurations supplying only `storage` preserve that shared value;
fresh defaults use the split above. Live storage reductions must pass occupied
space validation before any settings change.

`t1Capacity` controls C1 and `t1CapacityC2` controls C2 in configuration and UI.
Legacy configurations supplying only `t1Capacity` retain that value for both
classes. Fresh defaults use the equal rates above. Procurement and production share
the same class capacities; the compiled path caches a 14-product capacity array
by both settings, with indexed reads inside hot loops. Dashboard capacities
sum installed lines at their own class rates. Company counts, prices, storage and loyalty remain independent of these
capacity settings. Scaling both T2 rates equally scales all default demand weights
equally, leaving normalized Distributor routing unchanged.

There are **57,960 manufacturers**. Reversed product counts preserve the 23:12
C3:C4 company ratio, with an equal number of companies per product within each
complexity. Exact allocations require multiples of 28,980 total firms:
36*x : 69*y = 23:12 implies x:y = 529:144. Two blocks (57,960) are the
nearest feasible total to 50,000. All 36 C3 products have **1,058 companies**;
all 69 C4 products have **288 companies**. The default has no remainder firms.
The general apportionment helper retains stable-ID remainder handling for other
population/catalog configurations.

| Route | Invented products | Total companies | Gross capacity/tick |
|---|---:|---:|---:|
| C3: C1+C2 | 36 | 38,088 | 1,218,816 |
| C4: C1+C3 | 14 | 4,032 | 96,768 |
| C4: C2+C2 | 55 | 15,840 | 380,160 |
| **Total** | **105** | **57,960** | **1,695,744** |

Machine capacities are 32 for C3 and 24 for C4. Per-product capacity is 33,856
for C3 and 6,912 for C4, about 4.9 times higher for simpler products. Total
capacity is calibrated to approximately 1.7 million units per tick. The 32:24 per-machine throughput ratio is exactly 4:3. Company allocation is
unchanged; final-demand weights are recomputed from the new capacities and
intermediate requirements.
`T2_PRODUCT_FIRM_COUNTS` drives initialization, sector offsets, option weights and
exports. Allocation and demand-weight computation run once at import; tick loops
keep their existing compiled arrays. Changing a live capacity does not reassign
companies or Distributors automatically.

## Identity and compatibility

Gaia remains 0x0. Global company ranges remain contiguous and are generated from the tier populations. T2 now contains 57,960 companies, shifting the start of T3. The creative brief and generated browser metadata publish the updated ranges.

Checkpoint version 8 now requires catalog revision `midbridge-invented-105-reverse-v7`. Previous allocations are rejected rather than reinterpreted with different array indices and company assignments. Existing running processes and saved results are not reset or migrated by editing code. A fresh process/world activates this configuration.

## Preserved mechanics and performance

T1 buys raw elements from T0; T2 buys refined inputs and invented C3 intermediates. Repeated ingredients consume their explicit quantities. Every recipe yields one item. Raw/C1 occupy one space and C2/C3/C4 occupy two/three/four. Half of storage after machinery is reserved for finished goods; the other half supports equal batch counts of ingredients, weighted by quantity times space.

Distributors clear opening T2 finished inventory **before manufacturing**. Their
availability checks, stockout waivers and reliability attempts therefore use
carried inventory, never fresh production. Manufacturing then runs in ascending
complexity phases (C3, then C4). Each phase rebuilds its supplier book after the
previous phase settles: downstream companies can buy fresh upstream output plus
any old inventory left by Distributors, in the same tick. This gives Distributors
first access to opening stock and Manufacturers access to fresh output. Unsold new
output becomes Distributor inventory on the next tick. No physical stock pool is
reserved by buyer tier, and no product bypasses finished inventory or storage.

Within each complexity, suppliers' offered quantities only decrease. This retains
the indexed compiled purchase loops without company-order dependence for access
to new inputs. Multi-line companies retain their whole-company storage budgets;
only the current phase's lines procure and produce, each once per tick. Phase
settlement preserves sales, COGS, cash, transfers and inventory cost bases. Price
learning runs once per line after its phase's production, now after retail clearing.
Availability observations from both buyer groups still feed seller reliability;
the Distributor observations specifically measure opening stock. Rent and machinery
prices are unchanged.

Allocation and dependency propagation run once at import/startup. Trading remains compiled flat-array code. No Python callback is added to the tick kernels. Cache invalidation includes the selection file. Stats retain actual input consumption and intermediate sales. Snapshot invention counts distinguish 255 possible, 105 invented and 150 reserved.

## Handoff and verification

The naming brief and JSON/CSV attachments retain all 269 formulas, add explicit invention flags, and assign zero companies to uninvented recipes. All naming-only constraints remain intact. Run `tools/export_naming_brief.py` and `tools/build_midbridge_web.py` after metadata changes. The accepted naming source does not control mechanics; see `naming-integration.md`.

Tests check weighted material consumption, dependency closure, uninvented-installation rejection, weighted routing, full-population allocation, sector identity, reference/Numba parity, storage, rent, accounting and checkpoints. Remaining calibration concerns are overall demand scale and realized price/stock-dependent flows, including unequal refined-material demand under the simpler-product capacity concentration.

### Product-specific Distributor loyalty

An activated Distributor orders one product type per tick, potentially several
units from several suppliers. Refineries and Manufacturers can procure multiple
inputs per tick; their incumbents are already keyed by buyer and input market.
Distributor incumbents now also belong to a buyer–product pair. Changing a
Distributor's `distributorProduct` cannot carry a supplier or switching obligation
into another product market. Returning to a previously purchased product restores
that product's incumbent. Existing stockout waivers and split-order loyalty rules
are unchanged. This does not enable automatic product switching or multi-product
orders; it makes the relationship state ready for future routing changes.

`distributorPreferredSupplier` remains the flat, compiled-loop cache, tagged by
`distributorPreferredMarket`. Both clearing entry points synchronize this cache
before purchases. A NumPy comparison identifies reassigned buyers; only those
buyers touch the sparse `(buyer, market) -> production-line ID` history. The
fixed-product case needs an additional 2 MB of market tags for a million buyers,
not a dense million-by-catalog supplier matrix. History grows only with previous
buyer–product relationships. Checkpoint v8 preserves both the active cache and
sparse history, including a route change pending at save time. Older compatible
checkpoints bind their existing incumbent to their assigned product on first use.

### Independent extraction-machine capacity

`t0Capacity` is 500,000 output units per installed element machine per tick.
It is not a shared company throughput budget: four installed machines can each
produce 500,000 units, while an idle machine cannot lend capacity to another.
The 20 Extractors own 40 machines, ten for each raw element, giving nominal
capacity of 5,000,000 per element and 20,000,000 overall. Company cash, storage,
equal element storage targets, and production profitability gates still constrain
realized extraction. The common T0 kernel caps each line's feasible production
before allocating shared cash and storage, so both execution modes use the same
rule. Dashboard company capacity sums installed machines; aggregate capacity and
utilization use all 40 machines. Existing saved runs retain their saved numeric
`t0Capacity`; the new default applies to fresh configurations.

Each Extractor has a subsidized 40,000,000-space storage pool, divided equally
among its installed element machines. A four-machine firm has 10,000,000 spaces
per element, enough for twenty ticks of its nominal 500,000-per-machine output
from empty storage. The 20-company T0 fleet has 800,000,000 storage spaces.

Manufacturing reference costs are derived recursively from recipes, the refinery
raw-input reference, upstream markups and conversion cost. There is no separate
flat manufacturing-material cost parameter. Configuration normalization accepts
only current schema fields, dropping obsolete keys from older saves and patches.

### Provisional loyalty starting charges

At reliability 0.5, initial switching charges are **$50 for T1 buyers** and
**$1.50 for T2 buyers and the routing-weighted average T3 buyer**. These are starting guesses to revisit, not flat
permanent charges. `initial_loyalty_multiples` divides each target by its buyer
class reference cost times 1.5. Reliability scaling and stockout waivers remain:
at reliability zero the charges are $33.333333 / $1; at reliability one they are
$66.666667 / $2. Both C3 and C4 input buyers have the same starting charge.

Distributor switching retains its existing product-specific reference cost for
ranking and payment. Therefore the unchanged scalar T3 multiple gives $1.50 at
reliability 0.5 on the routing-weighted average, with different individual charges
by product. Only the initial multiples change; valuation, reference-cost scaling,
reliability, stockout waivers and annual recalibration retain their existing rules.

The AOV EMA starts at $1,000 for T1 and $30 for T2/T3, consistent with the 5%
calibration. Observed AOV updates every tick using the existing 0.01 EMA; annual
recalibration still targets 5% of observed merchandise order value. T1 counts
successful purchases. T2 uses merchandise spend; Distributor payments exclude
switching charges. Explicit multiple overrides remain supported. C5 is inactive.
Existing saved worlds retain their recorded multiples and AOV state; fresh worlds
use these provisional seeds. No transaction or tick-loop Python callbacks are added.
