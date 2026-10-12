# Demand, pricing, and production — worked decisions

This guide follows the decisions a firm makes during a tick. The [design canon](design_canon.md) remains the mathematical specification; this document explains its consequences through worked examples. Examples are constructed states, not measurements from a simulation run. Unless stated otherwise, they use default settings, one installed line, sufficient cash and supplier stock, no switching charge, and zero switching-income forecast. Book equity determines rent eligibility when the relevant phase evaluates it.

## 1. Three decisions, three different signals

| Decision | Main signal | What it does not establish |
| --- | --- | --- |
| Buy inputs | Storage-slot shortage, supplier quote, cash, stock, and switching cost | Whether making the next output is profitable |
| Produce | Finished-stock deficit, capacity, ingredients, conversion cash, and margin after forecast overhead | Whether a buyer will purchase the output this tick |
| Change price | Observed demand versus sales, market price, then change in gross profit | Whether the firm covers rent and switching expenses |

A reference cost calibrates initial prices, purchase curves, and fees. An inventory basis records what goods actually cost. A replacement estimate values a proposed mix of held and newly bought inputs. These are separate quantities; production uses inventory basis, while the price learner uses realized revenue minus cost of goods sold.

Demand travels upstream through **purchases to replenish inventory**, not through a centralized production plan. Distributors buy T2 goods; T2 replenishes C1/C2 and sometimes C3; T1 replenishes raw resources. Storage buffers, cash limits, and purchase rules interrupt any one-for-one relationship between final demand and current upstream orders.

## 2. Which decisions happen first?

| Phase | Decision and immediate consequence |
| --- | --- |
| T0 extraction | Update environmental difficulty, then add raw stock. T1 can buy it immediately. |
| T1 procurement and production | Buy raw, then refine using the cash and inputs that remain. |
| T0/T1 repricing | T1 has already bought at the old raw quotes. T2 will see updated T1 quotes. |
| Distributor purchases | Consume opening T2 stock and pay T2 firms before their production phase. |
| T2 C3 | Buy inputs, produce, and reprice; settle the input market. |
| T2 C4 | Rebuild offers, including fresh C3 stock and updated C3 quotes; buy and produce. |
| Closing | Record learning observations, update reliability and fee regimes when due, bill rent, and finalize earnings. |

Consequently, fresh C3 can reach C4 this tick, but fresh T2 production cannot reach distributors until a later tick. Supplier proceeds in a T2 input phase settle at that phase's end. Firms and lines share cash and inventory, so execution order matters when either is scarce. See canon §§4 and 11 for traversal and settlement rules.

## 3. T0: extracting against stock targets

T0 does not purchase inputs from Gaia. Difficulty determines extraction cost for each element. A firm's storage is divided equally among its installed element lines, each with its own throughput limit. It extracts toward these stock targets; it does not set output equal to yesterday's sales.

**Example: one line, ample cash.** Storage is 40 million spaces, throughput is 500,000 units/tick, current stock is zero, extraction cost is $1, and the quote is $1.25. The initial deficit is capped at 500,000. Its 20% margin exceeds the 5% production band, so it extracts all 500,000, spends $500,000, and holds inventory at $1 per unit. T0 pays no storage rent.

If cost rises to $1.24 with the same quote, the margin is 0.8%; the margin factor is `0.8% / 5% = 0.16`. Desired extraction falls to 80,000 before shared resource allocation. If cost exceeds $1.25, extraction stops. Existing stock can still sell at the posted price.

For several lines, cash and storage are shared, but unused per-element throughput cannot simply move to another element. The allocator rotates priority, protects small allocations, and distributes remaining capacity proportionally with remainder handling. A cash shortage can therefore reduce several outputs together. Fractional extraction is allowed. The exact allocator is in canon §5 and [operate_tier0](../economy/kernel/tick.py).

T0's recorded demand comes from T1 orders. A funded request can exceed delivery when stock is scarce; that unmet demand can later push its quote upward.

## 4. T1: buy raw in lots, then decide whether to refine

T1 makes C1 from one raw unit or C2 from two raw units. Both default to 6,000 outputs per line/tick, with $0.25 conversion cash per output.

**Storage example.** A single C1 line has 50,000 spaces minus a 1,000-space machine. Of the remaining 49,000, half targets raw and half finished goods: 24,500 units each. For C2, the same output allocation holds only 12,250 finished items. A two-distinct-raw recipe targets 12,250 units of each raw; a repeated-raw recipe targets 24,500 of that raw.

**Procurement example.** The empty C1 firm requests 24,000 raw units: the 24,500 shortage rounds down to 1,000-unit lots. At $1.25 it pays $30,000, provided its selected seller can deliver. A remaining 500-unit shortage cannot trigger another lot. There is one seller transaction per ingredient this tick, with no second-supplier retry after a short fill.

Raw supplier ranking compares order cost plus any fee owed to an incumbent. It first considers sellers with at least one lot, even when the order is much larger; this differs from T2's preference for a seller able to fill the entire requested quantity. Settlement then caps the order by cash and stock, and rechecks switching savings on the actual fill. Canon §§5–6 specify the details.

**Production example.** After buying, the C1 firm holds raw at $1.25 basis and quotes $1.88. Its new output costs `$1.25 + $0.25 = $1.50`. If it is rent-eligible, forecast overhead is $140. For 6,000 feasible outputs:

```text
margin = (1.88 − 1.50 − 140/6,000) / 1.88 ≈ 18.97%
```

It makes all 6,000, consumes 6,000 raw, and spends $1,500 conversion cash. New finished inventory has $1.50 unit basis. Rent stays outside that basis. Until goods sell, their capitalized cost is inventory rather than cost of goods sold.

**A tapered plan can still be rejected.** With only 400 feasible outputs at the same prices and overhead, estimated margin is about 1.60%. Tapering rounds the plan to 128 outputs. Their contribution is only `128 × $0.38 = $48.64`, below the $140 overhead, so the final check rejects production entirely. Procurement may already have happened.

A C2 line follows the same decision sequence, but consumes two raw units per output. At $1.25 raw basis its unit cost is $2.75, its initial quote is $3.44, and 6,000 outputs require 12,000 raw units in the recipe's specified proportions.

## 5. T2: price-sensitive replenishment and rent-sensitive production

### C3: one C1 plus one C2

A single C3 machine leaves `20,000 − 3,000 = 17,000` goods spaces. Each input slot targets `8,500/3 ≈ 2,833.33` items; the C2 input occupies twice the space of C1. The finished target is 2,833 C3 items, while throughput is only 32 per tick.

Starting empty, with chosen quotes of $1.88 for C1 and $3.44 for C2:

| Input | Purchase reference | Slot-based curve before whole-unit settlement | Purchased units |
| --- | ---: | --- | ---: |
| C1 | $1.25 | `(8,500/3) / (1 + (1.88/1.25)²)` ≈ 868.58 | 868 |
| C2 | $2.75 | `(8,500/3) / (1 + (3.44/2.75)²)` ≈ 1,104.71 | 1,104 |

These quantities assume neither cash nor stock binds. C1's purchase reference is $1.25, although its reference production cost is $1.50. The curve uses the **whole target slot**, capped by actual shortage and free space. It is not a permanently reduced storage target: an almost-full firm can buy its entire small shortage. Ingredients are processed sequentially, and early purchases can exhaust conversion cash.

At these purchased bases, actual C3 production costs `$1.88 + $3.44 + $0.50 = $5.82`. Its initial quote is $7.27. With 32 feasible outputs and $56 forecast rent:

```text
contribution before rent = 32 × (7.27 − 5.82) = $46.40
contribution after forecast rent = −$9.60
```

The firm produces nothing. If it is below the $1.5 million rent threshold, the same inputs and quote permit all 32 outputs because their gross margin is about 19.94%. At a hypothetical $8 quote with rent still due, estimated net margin is 5.375%, allowing all 32. These examples explain why rent eligibility can sharply change utilization even when unit selling prices exceed unit costs.

### C4: two different input routes

Both routes have 20,000 total spaces, a 4,000-space machine, a 2,000-item output target, throughput 24, and $0.75 conversion per item.

| Route | Input targets | Actual unit cost at the illustrated initial supplier quotes | Initial output quote |
| --- | --- | ---: | ---: |
| Two C2 | 4,000 of a repeated C2, or 2,000 each of distinct C2 inputs | `2 × 3.44 + 0.75 = $7.63` | $9.53 |
| C1 + C3 | 2,000 of each | `1.88 + 7.27 + 0.75 = $9.90` | $12.36 |

With $56 overhead, the two-C2 route's full 24-unit contribution is $45.60, so it stops. The C1+C3 route contributes $59.04 before rent. Its preliminary net margin is about 1.025%, which tapers 24 to 5 units; five contribute only $12.30, so the final overhead check also stops it. Below the rent threshold, both illustrated plans can run at full throughput.

These are conditional examples using the stated live quotes and bases. C4 actually sees the C3 quote after C3 repricing, and its accumulated input basis may differ from today's quotes. Purchase curves, seller stock, and shared cash can constrain output before the margin gate is reached.

### Why the cheapest seller may not win

T2 first seeks the cheapest offer able to fill the pre-curve request, then a partial supplier, then any offer. It compares a stocked incumbent's total against the challenger including a fixed switching fee. After applying the purchase curve, it rechecks affordability and actual-fill savings.

For example, an incumbent at $3.50 and challenger at $3.44 save $6 on 100 units, enough to justify a $1.50 switching fee. If cash restricts actual delivery to 20 units, savings are only $1.20; settlement returns to the incumbent and recalculates affordable quantity without the fee. The fee goes to the former supplier, not outside the economy. Canon §§6 and 8 cover the reference costs, reliability multiplier, and annual fee adaptation.

## 6. T3: final demand, sampled sellers, and incomplete orders

Each distributor is assigned one product at initialization. Routing uses full-fleet capacity weights after reserving C3 needed for C4. It does not migrate toward current shortages. Each buyer independently activates with probability 0.105 per tick; one million buyers therefore yield 105,000 activations in expectation, not a fixed count.

**C3 buyer example.** Take reference cost $5.8125 and an illustrative choke multiplier 2.4. With the C3 reservation premium, its halving price is:

```text
H = 5.8125 × 2.4 × (1 + 0.25 × 2) = $20.925
D(P) = 20 / (1 + (P/H)²)
```

At a $7.27 quote, continuous demand is about 17.85. It becomes 18 if the buyer's seeded rounding draw is below the fractional part, otherwise 17. At `P = H`, demand is 10; at `P = 2H`, it is 4. The field called “choke” is not a price above which demand becomes zero.

The buyer considers its incumbent plus five sampled offers, with replacement; repeated draws reduce the number of distinct sellers. It does not inspect the entire market. Switching fees can change candidate order, and an insufficient saving on actual delivery can reject a challenger.

**Partial-fill example with no incumbent.** Suppose successive candidates imply rounded demands of 18 and 16. The first delivers only 5. The second is asked for `16 − 5 = 11`, not another 16 or the original remaining 13. If it supplies 11, the final desired quantity is 16 and fulfillment is 16: price-lost demand is `20 − 16 = 4`, stock-unmet demand is zero. Because two sellers supplied the order, neither becomes a new incumbent. If the second supplies only 7 and there are no more candidates, fulfillment is 12 and stock-unmet is 4.

Distributors have no finite wallet or resale inventory. Goods leave the simulation; payments enter producer cash. Final demand is restricted by activation, prices, sampled search, and stock rather than buyer bankruptcy. See canon §7.

## 7. How all producing tiers learn prices

T0, T1, and T2 use the same price decision hierarchy. A line normally needs at least 30 observation ticks and its staggered update turn. Its current tick's trades have not yet entered that learning window.

| Condition, in priority order | Decision |
| --- | --- |
| Recorded demand exceeds sales | Raise, even if another signal would favor lowering |
| Quote above the market anchor by more than 2% | Lower |
| Quote below the anchor by more than 2% | Raise |
| Within the band, average gross profit worsened by more than 2% | Reverse the previous movement direction |
| Within the band, gross profit improved by more than 2% | Continue that direction |
| Within the band, change is within ±2% | Hold |

Without a previous profit baseline, the remaining branch follows its initialized direction. The market anchor weights current quotes by observation-window sales; with no sales, it falls back to mean finite quotes. It is not an average of historical transaction prices.

At default full step, movement multiplies the quote by `exp(±0.35 × 0.05)`. A $10 upward quote becomes $10.18 after cent rounding; a downward quote becomes $9.83. For a window with demand 120 and sales 100, the upward shortage branch wins even if the firm is above the market anchor. With no shortage and an anchor of $10, a $10.50 quote moves downward to $10.32.

The profit signal excludes rent and switching transfers. A loss-making firm can therefore raise its price while responding correctly to its gross-profit signal. Neither stock alone nor a high unit cost directly forces a price change; there is no cost-plus price floor. Production may stop while old inventory continues to sell. Observation resets, manual overrides, optional evidence gates, rounding, and reliability feedback are specified in canon §§8–9.

## 8. Reading an outcome without confusing the decisions

| Observed outcome | Inspect first |
| --- | --- |
| Inputs bought but no production | Conversion cash after buying, missing recipe ingredients, finished target, then the margin and reduced-output overhead check |
| Positive unit margin but idle machinery | Feasible batch size and forecast rent per batch; $140/T1 or $56/T2 can dominate a small batch |
| Plenty of goods but missed sales | Exact product identity, sampled sellers, posted prices, and candidate-specific stock |
| Low-price seller overlooked | Full-order stock preference for T2, switching fees, or absence from a distributor's sample |
| Strong sales but negative earnings | Sold inventory basis, rent charges, and net switching transfers |
| Price rise despite losses | Demand-versus-sales priority and the learner's gross-profit metric |
| Upstream orders differ from final sales | Inventory replenishment, intermediate C3 consumption, purchase curves, lot rounding, and phase timing |

At $2.80 per 1,000 spaces per tick, rent uses full storage capacity. Book equity **at or above $1.5 million** is eligible; below it, both new charges and arrears collection pause. Production forecasts and closing bills can disagree because intervening trades change equity. Income statements deduct new rent charges, while cash flow records payments, including old arrears. Do not infer earnings from purchases or cash changes alone.

For implementation, start with [model.py](../economy/core/model.py) for demand, production gates, and adaptive pricing; [tick.py](../economy/kernel/tick.py) for phase order and decisions; [trading.py](../economy/core/trading.py) for supplier selection and affordability; and [input_market.py](../economy/kernel/input_market.py) for staged supplier settlement. [numba.py](../economy/kernel/numba.py) contains compiled execution paths. The canon links the supporting initialization, accounting, and tests.

## 9. External information used by the decision rules

The implementation reads shared world arrays directly. There is currently no paid information service, access permission, discovery delay, or noisy estimate separating firms from these data. The table distinguishes information used to choose an action from data needed only to settle or report it.

| Activity | External information actually used | Reach and timing |
| --- | --- | --- |
| T0 extraction | Current element difficulty; configured resource and production rules | Environmental cost state each tick; no competitor forecast is consulted |
| T1 raw supplier search | Supplier identities, element coverage, posted quotes, available stock, incumbent reliability, current switching multiple | All eligible T0 suppliers for that raw element; current state when the buyer executes |
| T1 raw tie-breaking | Number of element lines each tied supplier operates | Inverse line-count weights affect equal-cost selection |
| T2 input supplier search | Eligible offers, posted quotes, available stock, incumbent reliability, current switching multiple | All offers for the exact ingredient; phase inventory declines as earlier buyers trade |
| T2 input quantity | Fixed reference cost for that ingredient and chosen supplier quote | Reference is configured/catalog-derived, not a live industry cost estimate |
| T3 purchases | Product supplier directory, sampled quotes and stock, incumbent quote/stock/reliability, switching multiple | Incumbent plus five draws with replacement; no full-market best-price search |
| T0/T1/T2 repricing | Market anchor derived from every eligible seller's current quote and accumulated learning-window sales | One aggregate for the exact output market; includes the firm's own line |
| Optional price-evidence gate | Market-wide order opportunities and, for T2, potential orders; seller/line counts used to allocate them | Off by default; controls when learning is allowed, not the direction of a price move |
| Switching regime | Buyer-class aggregate spending and order counts, smoothed into average order value | Central calculation updates multiples annually; firms use the resulting multiple rather than individually estimating market AOV |
| Replacement-cost reporting | Selected suppliers' quotes; T1 may fall back to current extraction cost | Descriptive estimate; not the production profitability gate |
| Player equipment installation | For T1, lowest finite raw quotes; for T2, recursive reference cost | Seeds the new machine's quote; bots do not autonomously buy equipment |

Supplier reliability is a shared line score combining price stability and availability across its recorded interactions. It is not exclusively the buyer's own experience. Only incumbent reliability enters the switching calculation: candidates are not ranked by their own reliability as a separate quality signal.

The price anchor is especially information-intensive: `sum(current quote × learning-window sales) / sum(learning-window sales)`, with mean finite quote as the no-sales fallback. A firm consumes the aggregate, but producing it requires other sellers' sales quantities. Windows can differ because lines reprice and reset on staggered turns. No competitor profit, inventory basis, cash, equity, future output, or distributor willingness-to-pay distribution enters this price rule.

The production gate itself uses the firm's own cash, inventory, basis, quote, capacity, storage targets, forecast rent, and past net switching income. It does not query rival stock, industry demand, rival margins, or expected future selling prices. External procurement changes its available inputs and costs; external pricing information can change its quote, indirectly changing a later production decision.

Seller records of orders addressed to that seller, successful deliveries, and revenue are its own transaction evidence. The global simulator also holds dashboards, buyer preferences, and complete accounting arrays; that does not mean the autonomous firm uses them as intelligence. Supplier book basis, for example, is needed for seller COGS settlement, not buyer ranking.

### Possible charging boundaries — proposal, not implemented

A supplier-search service could charge T1/T2 per **distinct input market searched per tick or phase**, including quote and availability access. A competitor benchmark service could charge T0/T1/T2 per **output market at an eligible price decision**. A shared reputation service could be bundled with supplier search or priced separately when an incumbent score is consulted. Optional market-opportunity analytics could be a separate subscription if that feature is enabled. T3 sampled searches could be metered per distinct candidate, but distributors currently have no cash ledger from which to collect a fee.

Meter economic information events, not internal array reads: planning and settlement can repeat supplier lookups, and compiled execution may scan or index differently from the reference path. Define whether a failed search, a held price, and several same-market lines share one charge before implementing fees. Static recipe/reference tables and centrally prescribed switching multiples can remain ordinary model rules unless deliberately made paid services.
