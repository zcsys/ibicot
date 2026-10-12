# Design canon — implemented economy

This canon is reconstructed from the executable model, catalog, state initialization, trading kernels, and accounting. It specifies current behavior, including asymmetries and limits. Default values describe a fresh world; formulas apply to normalized configuration unless stated otherwise. Source links identify the implementation behind each group of rules. For worked examples and information-access boundaries, see the [decision walkthrough](decision_walkthrough.md).

## 1. Vocabulary, units, and scope

**Tier** identifies an actor's role. **Complexity** `c` is the number of raw ancestry units in one product, and therefore its occupied storage space. **Line** means one installed recipe machine. **Firm** owns shared cash, inputs, storage, and one or more lines. **Market** trades one exact resource or recipe, never interchangeable products of the same complexity.

| Tier | Operation | Default population |
| --- | --- | ---: |
| T−1 | Gaia: named raw-resource origin, no simulated supplier ledger | 1 identity |
| T0 | Extraction of raw Organics / Inorganics / Metals / Radioactives | 20 firms, 40 machines |
| T1 | Direct raw refining into C1 or C2 | 1,008 firms, 72 per recipe |
| T2 | Manufacturing C3 and C4 from lower-complexity products | 57,960 firms |
| T3 | Final purchase and consumption of T2 output | 1,000,000 distributors |

Money is floating-point dollars. Quotes are rounded to cents, half away from zero, and guarded to `[0.01, 10⁹]`; costs, fees, rent, and balances retain fractional cents. Prices may fall below cost. T1/T2 production and purchases use whole units; T0 inventory/extraction may be fractional. Raw items occupy one space; products occupy `c` spaces. Machines occupy configured fixed footprints. There is no depreciation, interest, ordinary credit, automatic insolvency exit, or spoilage in the tick. No new operating-cost liabilities are created; saved historical rent arrears remain a legacy liability only.

One month = 30 ticks; year = 360; generation = 7,200 (20 years); age = 172,800 (24 generations). Initialization is tick 0; ordinary execution begins at tick 1. Calendar month and year are one-based within their cycles; generation and age are zero-based.

Source: [model.py](../economy/core/model.py), [state.py](../economy/core/state.py), [runtime-defaults.json](../catalogs/midbridge-4263/runtime-defaults.json).

## 2. Recipes and population allocation

The structural symbols `W,E,F,A` map respectively to Organics, Inorganics, Metals, and Radioactives. They identify recipe ancestry independently of display names.

| Complexity | Immediate recipe | Full universe | Invented/active | Firms per active recipe | Capacity per line/tick |
| --- | --- | ---: | ---: | ---: | ---: |
| C1 | One raw → one refined basic | 4 | 4 | 72 | 6,000 |
| C2 | Two raw → one refined compound | 10 | 10 | 72 | 6,000 |
| C3 | One C1 + one C2 → one good | 40 | 36 | 1,058 | 32 |
| C4 | One C1 + one C3 → one good | 160 | 14 | 288 | 24 |
| C4 | Two C2 → one good | 55 | 55 | 288 | 24 |

Input order does not matter; repeated inputs are allowed and combined into their integer quantity. Nested recipes retain their identity: equal raw ancestry does not imply equal products. Counts follow `C2=4×5/2`, `C3=4×10`, `C4=4×40+10×11/2`. All recipes yield exactly one output. For ingredient quantities `aₚₘ` and ingredient space `sₘ`, `Σₘ aₚₘsₘ=cₚ`: production conserves goods space.

The active subset is the explicit list in [starting-selection.json](../catalogs/midbridge-4263/starting-selection.json), closed over its dependencies. It includes 105 T2 products; the other 150 have no active lines, demand, or purchasable machinery. C5 configuration slots remain for compatibility but have no active recipes. T2's input market contains 50 products: 14 T1 materials plus 36 invented C3 goods. Its first four input indices are **refined C1**, despite the internal `t2Raw` array name.

There are 14 material sectors paired with 14 manufacturing sectors. Each T2 recipe's sector is anchored to one direct T1 ingredient; sector sizes need not be equal. T0's extraction coverage comprises eight one-element, six two-element, four three-element, and two four-element firms.

T2 firm shares reverse the active product counts: C3:C4 firms = `69:36`, yielding 38,088 C3 firms and 19,872 C4 firms. Within each complexity, firms are apportioned equally over recipes. Integer apportionment floors each weighted share and distributes remainders by descending fractional remainder, then ascending key. A reduced `t2FirmCount` takes a prefix of this catalog-ordered allocation; it does not rescale every product cohort.

For product `p`, let default gross output capacity be `gₚ = firmCountₚ × defaultCapacityₚ`. Final-demand weight is

```text
wₚ = gₚ − Σ downstream T2 products j (aⱼₚ × gⱼ)
```

All active weights are positive. Gross T2 capacity totals 1,695,744 items/tick; intermediate C3 use reserves 96,768; final-output weights total 1,598,976. These are capacity weights, not promised sales. Recursively expanding final demand reconstructs gross capacity: `xₚ=wₚ+Σⱼaⱼₚxⱼ`, evaluated from C4 down to C3. T1 requirements are `rₘ=Σₚaₚₘxₚ`; they are not equal across materials.

Distributor assignment uses midpoint-stratified draws `(k+½)Σw/N`, mapped into cumulative product weights, with buyers ordered by seeded hash. Each product gets within one buyer of its ideal share. Assignment is fixed at initialization and uses **default full-fleet capacities**, even when live capacities or population are changed. It does not follow shortages.

Source: [catalog adapter](../economy/core/midbridge.py), [model allocation](../economy/core/model.py), [initialization](../economy/core/state.py), [catalog validator](../tools/build_recursive_catalog.py).

## 3. Starting capital and reference costs

| Quantity | T0 | T1 C1 / C2 | T2 C3 | T2 C4 |
| --- | ---: | ---: | ---: | ---: |
| Starting equity per firm | $75,000,000 | $1,500,000 | $1,500,000 | $1,500,000 |
| License book asset | $22,000,000 | $1,000,000 | $1,000,000 | $1,000,000 |
| Machinery per line | $12,250,000 | $15,000 | $75,000 | $375,000 |
| Other reserved asset | $1,000,000 | — | — | — |
| Starting cash | `$52m − $12.25m × machines` | $485,000 | $425,000 | $125,000 |
| Firm storage | 40,000,000 | 50,000 / 50,000 | 20,000 | 20,000 |
| Machinery footprint/line | No deduction from T0 storage | 1,000 / 1,000 | 3,000 | 4,000 |
| Capacity/line/tick | 500,000 | 6,000 / 6,000 | 32 | 24 |

Firms start with zero inventory and no preferred suppliers. T1/T2 start with one line; active-line reliability starts at `0.5`. License, machinery, and the T0 reserve are assets, not operating expenses. The T0 reserve is excluded from spendable cash.

Define conversion per output item `v(c)=conversionFactor×max(1,c−1)`, with factor `0.25`. Thus C1/C2 cost `0.25`, C3 `0.50`, C4 `0.75`. Define reference production cost `Uₚ` and initial quote `Pₚ⁰`:

```text
T0: Uₑ⁰ = baseCost × difficultyTarget;                 Pₑ⁰ = cent(Uₑ⁰ × (1+t0Markup))
T1: Uₚ  = Σₑ aₚₑ × t1MaterialCost + v(cₚ);           Pₚ⁰ = cent(Uₚ × (1+t1Markup))
T2: Uₚ  = Σₘ aₚₘ × Uₘ × (1+t1Markup) + v(cₚ);       Pₚ⁰ = cent(Uₚ × (1+t1Markup))
```

Both markups default to `0.25`; `baseCost=1`, `t1MaterialCost=1.25`. The latter is an independent configuration value, not automatically tied to live extraction cost or quotes. Recursive reference costs use unrounded ingredient references plus markup; each displayed starting quote is rounded only after its own calculation.

| Route | Reference cost | Starting quote |
| --- | ---: | ---: |
| Raw at difficulty 1 | $1 | $1.25 |
| C1 | $1.50 | $1.88 |
| C2 | $2.75 | $3.44 |
| C3 = C1 + C2 | $5.8125 | $7.27 |
| C4 = C1 + C3 | $9.890625 | $12.36 |
| C4 = C2 + C2 | $7.625 | $9.53 |

These seed costs calibrate quotes, demand, and switching. Actual production uses purchased inventory's weighted book basis. Before buying, a separate replacement estimate uses planned output `d`, held inputs `Rₘ`, their basis `bₘ`, and planning quotes `Qₘ`:

```text
heldₘ = min(d×aₚₘ,Rₘ)
replacement = v(c) + Σₘ (heldₘ×bₘ + (d×aₚₘ−heldₘ)×Qₘ)/d   when d>0
replacement = v(c) + Σₘ aₚₘQₘ                              when d=0
```

T1's `d` is its capacity-capped target deficit; T2 also floors it. T1 planning uses the selected raw quote, or last-buy quote if no supplier exists; a nonfinite quote falls back to current extraction cost for positive plans, or held basis for zero plans. T2 uses the selected input quote, falling back to held basis with no offer. This estimate is descriptive; it does not drive the production gate.

Source: [config.py](../economy/core/config.py), [cost helpers](../economy/core/model.py), [reset_world](../economy/core/state.py).

## 4. Storage allocation and production

For a T1/T2 firm with storage `S`, installed lines `L`, and line footprints `fₗ`:

```text
G = S − Σₗ fₗ                              goods space
H = G / (2 × max(1,L))                     space allocated per output line
Fₗ* = floor(H / cₗ)                        finished-item target
Rₘ* = Σ installed lines l (H × aₗₘ / cₗ)  target input items of type m
occupied = Σ inputs m (Rₘ × sₘ) + Σ outputs l (Fₗ × cₗ)
```

Recipe weighting ensures `ΣₘRₘ*sₘ=G/2`. Repeated inputs accumulate into one slot; shared inputs accumulate across lines. Actual purchases are capped by total free space and their own slot shortage. Firms cannot borrow another input's unused slot. Conversion releases exactly the space occupied by its output, so no extra production-space cap is necessary.

For single default lines, finished targets are C1 `24,500`, C2 `12,250`, C3 `2,833`, C4 `2,000`. A C3 `C1+C2` machine targets `8,500/3` units of each ingredient (weighted space 1:2). A C4 `2×C2` machine targets 4,000 C2 inputs; `C1+C3` targets 2,000 of each. Input targets can be fractional; purchases are floored. T1 storage capacity follows the firm's original C1/C2 cohort even after it installs other machines.

For each T1/T2 line, with cash `C`, ingredient basis `bₘ`, inventory `Rₘ`, capacity `K`, and quote `P`:

```text
B = min(floor(min(K, max(0,F*−F))), minₘ floor(Rₘ/aₚₘ), floor(max(0,C)/v(c)))
u = Σₘ aₚₘbₘ + v(c)                       actual cost per new output
h = (paid firm rent + paid intelligence − switchingNetEMA) / installed lines
m = (P − u − h/B) / max(P,10⁻⁹)             if B > 0
z = clamp(m / productionMarginBand, 0, 1)
B' = floor(B×z + ½)
```

`productionMarginBand=0.05`. Return zero if `B≤0`, if `u>P+10⁻⁹`, if `B'≤0`, or if `(P−u)B'−h<−10⁻⁹`. Otherwise make `B'` outputs, consume `B'aₚₘ`, pay `B'v(c)`, and add their cost to finished inventory. The reduced-output recheck prevents fixed overhead from making a tapered plan loss-making. Switching income cannot override the `u≤P` test. At a 5% or larger estimated net margin, all feasible batches are made; below it, output tapers with rounding.

`switchingNetEMA` starts at zero and updates after settlement using `alpha=0.15`. Rent and intelligence are prepaid before procurement, using opening equity and cash. Production uses the actual paid charges for that tick, so crossing the exemption threshold after payment does not erase overhead. Overhead affects planning, never inventory basis. Input replenishment proceeds independently of production profitability for operating companies. Sales/demand EMAs do not set storage targets.

T1 production runs firm-major, then product-major. T2 firms rotate by `(order+137×tick) mod firmCount`; plans rotate line traversal by tick, but production executes in installed-slot order. All lines share actual remaining inputs and cash. T2 completes C3 before C4, rebuilding its supplier book between phases. A phase's supplier inventory only decreases; newly produced goods become inputs at the next complexity phase. Supplier proceeds and inventory deltas settle at phase end, so those proceeds are not available for the seller's earlier operations in that phase.

Source: [storage helpers](../economy/core/state.py), [production_batches](../economy/core/model.py), [tick production](../economy/kernel/tick.py), [InputMarket](../economy/kernel/input_market.py), [compiled kernels](../economy/kernel/numba.py).

## 5. T0 extraction and T1 raw buying

### Extraction

Each element has shared environmental difficulty, updated before extraction:

```text
dₑ' = clamp(dₑ + theta×(difficultyTarget−dₑ) + sigma×Zₑ, difficultyMin, difficultyMax)
kₑ = max(10⁻⁹, baseCost×dₑ')
```

Defaults are target `1`, `theta=0.15`, `sigma=0.005`, bounds `[0.7,1.4]`. A firm's `n` element lines each target `t0Storage/n`; each owns its own throughput `K=t0Capacity`. Idle capacity cannot be reassigned to another element.

For line deficit `Dₑ=min(max(0,S/n−stockₑ),K)`, extraction is suppressed when `kₑ>Pₑ+10⁻⁹`. Otherwise multiply `Dₑ` by `clamp((Pₑ−kₑ−h/max(Dₑ,1))/max(Pₑ,10⁻⁹)/marginBand,0,1)`. T0 overhead is solely `−switchingNetEMA/n`; it pays no storage rent. Unlike T1/T2, T0 does not repeat the net-margin test after allocation.

Positive deficits rotate priority by `(seed+tick+firm) mod positiveLineCount`. Allocation shares the remaining `nK` capacity, storage headroom, and cash. When cash may bind or the initial budget is smaller than the number of positive lines, each gets up to one unit in priority order first. Otherwise, up to four passes reserve up to one unit for lines whose proportional quota would be below one.

Up to six further passes compute `feasibleₑ=min(remainingDeficitₑ,floor(max(0,cash)/kₑ))` and `budget=max(0,min(remainingCapacity,freeSpace,Σfeasible))`. If the budget covers all feasible deficits, use them; if below one, split it proportionally; otherwise floor proportional quotas of `floor(budget)` and allocate remaining units by largest remainder, breaking ties by rotated priority. Each actual make is recapped by its deficit, shared capacity, space, and cash. Fractional extraction can survive tapering/allocation; cash is charged `made×kₑ` and inventory basis is averaged.

### Raw procurement

T1 firms alternate material cohorts and firms within cohorts: first cohort `tick mod 14`, first firm `(37×tick) mod 72`, then 72 rounds through all 14 cohorts. Within a firm, inputs are processed in element-index order. Each positive slot shortage requests `L×floor(shortage/L)`, where `L=minWholesaleLot=1,000`.

T0 supplier ranking minimizes `quote×max(request,L)+switchingFee`, first among suppliers holding at least one lot; only if none qualify does it consider empty suppliers. It does **not** require full-order stock for this ranking. An incumbent tied on a positive request is retained. Other equal-cost ties use seeded random weights `1/supplierElementCount`.

The order is recapped to whole lots fitting both total free storage and the input slot, then funded and filled using §6. There is one supplier transaction per input per tick, without a second-supplier retry. Demand credited to the seller is the funded request before its stock cap; availability asks whether it held the original lot-rounded request. Successful purchase updates the preferred supplier even on a partial fill. Sub-lot stock and slot shortages wait.

Source: [operate_tier0 / plan_and_buy_inputs](../economy/kernel/tick.py), [compiled raw buying](../economy/kernel/numba.py).

## 6. T2 input buying and producer-order settlement

T2 buys C1/C2 from T1 and invented C3 from T2. For each required ingredient `m`, calculate the whole-unit request `r` as the nonnegative floor of the minimum of slot shortage and free goods space divided by `sₘ`.

Offers are sorted by quote. T1 equal-quote ties rotate by `(marketRank+tick) mod marketSize`; T2 ties use `(lineIndex+37×tick) mod totalT2Lines`. Select the cheapest seller able to fill `max(1,r)`; failing that, the cheapest with at least one unit; failing that, the first offer. Retain a stocked incumbent if its total for that common quantity is no greater than the challenger's total including switching. A zero-request planning lookup is price-only.

Price then reduces the order:

```text
Vₘ = t1MaterialCost                 for refined C1 (default 1.25)
   = refinery reference cost Uₘ    for C2 (default 2.75)
   = recursive reference cost Uₘ   for C3 (default 5.8125)
buyRequest = min(r, Rₘ* / (1 + (chosenQuote/Vₘ)²))
```

The C1 reference deliberately differs from its `$1.50` production reference. This input curve always uses exponent `2`, independent of distributor `elasticity`. Its latent quantity is the **entire input slot**, not the shortage. There is one transaction per required ingredient per complexity phase; inputs are processed in index order. Purchases can consume cash subsequently needed for conversion.

Both producer buying tiers settle with the same function. For selected seller `s`, incumbent `i`, requested quantity `q`, lot size `L`, cash `C`, and stock `I`:

```text
fee = M×U×(1+clamp(reliabilityᵢ,0,1)) if s≠i, i exists, and Iᵢ≥q; otherwise 0
funded = L × floor(min(q, max(0,C−fee)/Pₛ) / L)
filled = L × floor(min(funded,Iₛ) / L)
```

If the fee is positive and `filled×(Pᵢ−Pₛ)≤fee`, revert to the incumbent and recompute funded/filled without a fee. Charge a fee only for a positive fill. For T1, `L=1,000`; for T2, `L=1`. T2 ranks on the pre-curve request, applies the curve at that chosen quote, then performs this settlement check; switching back does not recalculate the curve. The incumbent's capacity test therefore can differ between ranking and settlement.

A purchase moves `filled×quote` from buyer to seller, goods in the opposite direction, and a fee from buyer to the **former** supplier. Buyer input basis includes the goods payment only. A T2 supplier book holds original saleable basis; settlement removes sold value at that basis and recomputes residual finished basis after any production: `remainingBasis=((remainingUnits+soldUnits)×postProductionBasis−soldUnits×originalBasis)/remainingUnits`, or zero if depleted. This prevents fresh stock from retroactively changing COGS on earlier stock. Offer selection does not exclude another eligible line owned by the buyer's own firm.

Source: [trading.py](../economy/core/trading.py), [transfer_tier2_input](../economy/kernel/tick.py), [input_market.py](../economy/kernel/input_market.py).

## 7. Distributor demand and selling

Each distributor has a fixed invented product, `Qmax=20`, a seeded choke multiplier `z∈[1.8,3.0)`, and elasticity `eta=2`. Independently each tick it activates with probability `0.105`. Its price scale is a **halving price**, despite the field name “choke”: demand is positive above it.

```text
H = Uₚ × z × (1 + t2ReservationPremium×(cₚ−1)),  premium=0.25
D(P) = Qmax / (1 + (P/H)^eta)
q(P) = min(ceil(Qmax), floor(D(P)) + 1[u < fractionalPart(D(P))])
```

One seeded uniform `u` is reused for that buyer's potential quantity and every candidate quote in the tick. Potential is the same stochastic rounding of `Qmax` (exactly 20 by default). Distributors have no finite cash balance, stock, production, or resale: their purchases are external spending and the goods leave the modeled economy.

The buyer includes its incumbent, if any, plus five uniform offer draws **with replacement**. Duplicate candidates are removed, so five draws need not mean five distinct suppliers. Offers include empty sellers. Incumbency is stored per buyer/product and survives product reassignment via sparse history.

Let `qᵢ=q(Pᵢ)`. If the incumbent can supply `qᵢ>0`, challengers are sorted on `Pₛ+fee/qᵢ`; the incumbent on `Pᵢ`. Otherwise sorting uses quotes alone. Stable equal-price order follows candidate insertion order (incumbent first, then sampled sellers).

Traverse candidates once, maintaining cumulative `bought`:

1. Set `want=max(0,q(Pₛ)−bought)`; stop if zero. Set `totalDesired=q(Pₛ)`.
2. Tentative delivery is `min(want,floor(stockₛ))`. Before the first positive purchase, skip a challenger if the incumbent can fulfill and `delivery×(Pᵢ−Pₛ)≤fee`. A skipped quote is not a failed availability attempt.
3. Record `want` as seller demand and one availability attempt. Deliver at the seller's posted quote, recognize its book-basis COGS, and mark availability successful only if delivery covers `want`.
4. Stop when cumulative purchases reach demand at the current seller's quote. Otherwise continue; demand is recalculated at each candidate price, so a cheap empty seller does not set the entire order's quantity.

The first seller delivering goods is `primary`. A new incumbent is recorded only when exactly one seller supplies the complete final desired order; split or incomplete purchases retain the old incumbent. If `primary` differs from an incumbent that could fulfill its own quote-dependent quantity, pay that incumbent one fixed switching fee, even if preference was not replaced.

For each buyer, `active=totalDesired`, `fulfilled=bought`, `priceLost=potential−totalDesired`, `stockUnmet=max(0,totalDesired−bought)`. An active order has positive desired quantity; a purchase order has positive delivery; a filled order reaches its final desired quantity. Potential orders count activated buyers with positive potential. These are separate from seller attempts, which can include several candidates.

Source: [clear_distributors](../economy/kernel/tick.py), [compiled clearing](../economy/kernel/numba.py), [initialize_distributors](../economy/core/state.py).

## 8. Switching and reliability

The fixed fee is `M×U×(1+r)`, using incumbent reliability `r` clamped to `[0,1]`. The reference `U` is `baseCost` for T1 raw buyers, the unweighted mean of all 14 refinery reference costs for T2 input buyers, and the purchased product's recursive reference cost for distributors. T2 uses the complexity of its **first installed line** to choose its fee regime, including on mixed-complexity firms.

Initially `M₁=50/(baseCost×1.5)`, `M₂,C3=M₂,C4=1.5/(meanRefineryCost×1.5)`, and `M₃=1.5/(weightedMeanT2Cost×1.5)`. The T2 mean is `$2.392857…`; the T3 routing-weighted mean is `$6.490228…`. At reliability `0.5`, initial T1 and T2 fees are `$50` and `$1.50`; distributor fees vary with the purchased product's reference cost. The unused C5 multiple starts at zero. Configured `loyaltyMultiple` overrides these initial values.

Each tick with positive order count, average order value updates as `AOV←0.01×observedAOV+0.99×AOV`; with no orders it holds. Initialization is `AOV=M×classReference×1.5/0.05`. Observed values are:

| Regime | Spend numerator | Count denominator |
| --- | --- | --- |
| T1 raw | Total T0 goods revenue | Number of T1 firms buying any raw that tick, **not** individual input transactions |
| T2, separately C3/C4 | Input goods spend for that buyer class | Positive ingredient purchase transactions |
| T3 | Distributor payments excluding switching fees | Buyers with any positive delivery, including partial orders |

Every 360 ticks, **after trading**, set `M=0.05×AOV/(classReference×1.5)`. Class references are `baseCost`, mean refinery cost, and final-demand-weighted mean T2 cost respectively. Between yearly boundaries, multiples hold. Thus the regime aims for a fee of 5% of a typical order at reliability 0.5; per-product T3 fees scale relative to the class mean.

For each seller price update, stability sample is

```text
stability = 1 − clamp(max(0,Pnew−Pold) / max(10⁻⁹,Pold×switchingStableBand), 0, 1)
```

`switchingStableBand=0.025`. Only increases reduce stability. Every 30 ticks:

```text
score = ½×clamp(meanStability,0,1) + ½×clamp(successfulAvailabilityChecks/checks,0,1)
r ← clamp(r + reliabilityAlpha×(score−r),0,1), reliabilityAlpha=0.15
```

Missing price samples or availability checks contribute `1`. Monthly accumulators then clear. T0 availability uses original T1 lot requests; T1 and intermediate T2 sales use the storage/space request before T2's price curve; distributor checks use each candidate's remaining `want`. T2 combines intermediate and distributor attempts. Reliability is line-specific, even when firms have several lines.

Source: [loyalty helpers](../economy/core/model.py), [regime initialization](../economy/core/state.py), [reliability and yearly updates](../economy/kernel/tick.py).

## 9. Price learning

At the end of each tick, each active line accumulates gross profit `revenue−COGS`, sales, `max(recordedDemand,sales)`, and one observation tick. Sales and demand EMAs update with `alpha=0.15`; price learning uses window totals, not these EMAs. Rent, intelligence, and switching transfers are excluded from learned gross profit.

A line can reprice when its observation age is at least `priceObservationTicks=30` and `(tick+lineIndex) mod priceObservationTicks=0`. Current-tick trades have not yet entered its learning window. Manual finite quotes on player-controlled lines override learning at that line's pricing phase. Setting a manual quote clears its observation window, baseline, and step history; the T2 command also changes its live quote immediately, while T0/T1 apply it at their pricing phase. The online flag does not gate automated buying or production.

The market anchor is `ΣPᵢ×windowSalesᵢ/ΣwindowSalesᵢ`, falling back to the mean finite quote with no sales, or zero with no quotes. Prices are current quotes weighted by accumulated sales, not historical transaction-price averages. Given average window profit `π`, previous observed average `πprev`, stored direction `d∈{−1,+1}`, and step scale `s`:

1. If accumulated demand exceeds accumulated sales by more than `10⁻⁹`, choose `d'=+1`.
2. Otherwise, if the quote is above/below the market anchor's `±marketAnchorBand` (default 2%), choose down/up respectively.
3. Otherwise, with finite `πprev`, compute `δ=(π−πprev)/max(|πprev|,10⁻⁹)`. If `δ<−0.02`, reverse direction; if `δ>0.02`, retain it; otherwise hold the quote and step. Without a baseline, retain the initial direction.
4. On movement, `s'=clamp(s×(1 if direction changed else 1.2),0.01,1)` and `P'=cent(clamp(P×exp(d'×pricingAggressiveness×wholesalePriceResponse×s'),0.01,10⁹))`. Defaults are `0.35` and `0.05`, so a full upward step is about 1.765% before cent rounding. If a downward step rounds back to the same price, store upward direction for the next attempt.

Steps initialize at 1; initial direction alternates by `(firm+seed)` parity. With the current update rule a default step stays at 1; changing direction does not shrink it. After an eligible learning decision, including a hold, save `π` as the baseline and reset the window accumulators.

Optional research gates default off. If `researchPriceMinimumOpportunities>0`, a due quote waits until its allocated opportunity count reaches that minimum or stale evidence is sufficient. For T2 with positive `researchPriceMinimumPotentialOrders`, stale evidence means that potential-opportunity threshold; otherwise it means age ≥ `researchPriceMaxObservationTicks` (default 3,600). Opportunity totals are shared within a market by line weight: T0 `1/firmElementCount`, T1 `1`, T2 `1/firmLineCount`, normalized across sellers. Potential opportunity allocation is accumulated only when the minimum-opportunities feature is enabled.

T0/T1 quotes update after T1 production: T1 raw purchases used the old T0 quote, while T2 input purchases see the new T1 quote. T2 retail and production use pre-update quotes; each T2 line reprices after its production attempt. Later C4 input books see updated C3 quotes.

Source: [adaptive_price](../economy/core/model.py), [learned_quote / price_markets / observe_markets](../economy/kernel/tick.py).

## 10. Accounting, rent, and equipment

For existing quantity `Q` at unit basis `b` and newly purchased/produced quantity `q` worth `V`, weighted basis becomes `(Qb+V)/(Q+q)`. Production value is consumed-input book value plus conversion cash; extraction value is paid extraction cost. Selling `q` units at `P` posts revenue `qP` and COGS `qb`. Unsold inventory is not expensed. Switching, rent, and intelligence never enter inventory basis.

```text
firm net earnings = Σ lines (revenue−COGS) + switchingIncome − switchingExpense − rentCharge − intelligenceCharge
T1/T2 equity = cash + license + machineryBook + inputBookValue + finishedBookValue − legacyRentArrears
T0 equity = cash + license + machineryBook + reserve + rawInventoryBookValue
```

Company-period switching/rent/intelligence items are allocated equally across installed lines for reporting. Net margin is net earnings/revenue when revenue is positive; otherwise unavailable. Shared-company balances are split across installed line complexities in complexity reports, avoiding duplicate firm cash/equity. Purchases exchange cash for inventory; making goods capitalizes conversion; neither is an immediate operating loss. Profits are posted from transactions, not inferred from equity changes.

Storage rent defaults to **$2.80 per 1,000 storage spaces per tick**. Per-tick rent is `fullStorageCapacity/1000×storageRentPerThousandPerTick`: $140 for default T1 and $56 for default T2, regardless of occupied space.

**Market intelligence** means only the sales-weighted market price benchmark in §9. Supplier quotes, availability, and reliability are company communication, not separately billed intelligence. The subscription is `t1IntelligencePerTick=$2,000` per T1 company or `t2IntelligencePerTick=$20` per T2 company per tick. It is independent of installed line count, trading volume, manual pricing, and whether repricing is due. T0 and T3 are uncharged.

**Shared small-company exemption and payment gate:** before company activity each positive tick, snapshot book equity. Below $1.5 million, the Colony subsidizes both services by waiving their charges; no cash is injected and no simulated provider is paid. Exactly $1.5 million is eligible. An eligible company must pay the combined bill in full from opening cash. If it cannot, collect nothing, post no expense or new debt, and stop its buying, production, sales, and repricing for that tick. Its cash, installed machines, and inventories remain intact. Recheck next tick; there is no permanent closure or automatic asset liquidation.

Default combined bills are $2,140/T1 and $76/T2. Deduct payment before procurement and retail trading; destroy that cash, crediting no company. A company cannot fund the current bill with sales later that tick. Split actual paid overhead equally across installed lines for production decisions and reporting. Both services share the same opening eligibility, and a payment taking equity below the threshold does not refund either charge. Tick 0 has no billing. Existing rent arrears in an imported legacy checkpoint are preserved; an eligible company must also pay them in full to operate. No new run creates arrears, and legacy debt repayment is not a new expense.

Net earnings, equity, dashboard margins, and recorded product/company accounts include intelligence; gross profit and inventory basis do not. Price learning still uses gross profit, not net earnings. Procurement curves and static reference costs remain unchanged, but buying can be constrained by reduced cash or stopped operation. Stopped sellers are excluded from offers and market price anchors; saved preferences cannot bypass the stop. The production gate uses paid rent/intelligence, while a standalone pre-billing forecast uses current eligibility.

Goods and producer switching payments transfer cash internally. Distributor goods/fee payments inject cash. Extraction, conversion, paid rent, and paid intelligence are operating cash sinks; machinery purchases are equipment sinks. For ordinary ticks without administrative equipment transactions:

```text
Δ(total producer cash) = distributorPayments − extractionCosts − conversionCosts − rentPaid − intelligencePaid
```

Equipment purchase moves its configured price from firm cash into machinery book value, preserving equity. T1 player firms may add any uninstalled refinery recipe if cash and physical space suffice. T2 player firms may add an invented recipe only within their sector/capability, without duplication, with enough cash/space, and at most four lines per firm. Bots never add lines automatically. New machines repartition storage targets without moving or deleting existing goods. A new T1 quote uses the lowest finite wholesale quote for each ingredient (falling back to `baseCost`) plus conversion and markup; a new T2 quote uses its recursive reference cost and markup. T0 has no runtime equipment-buying path.

Progression is separate from company finance: T1 player access starts held; T2 access costs `$1m` in the ownership-spend record; founding a house records `$200,000`; T0 access is not sold. These commands record progression spending without debiting a simulated player wallet or company cash. They are not acquisitions of company equity.

Source: [accounting.py](../economy/core/accounting.py), [rent settlement](../economy/kernel/tick.py), [equipment installation](../economy/core/state.py), [runtime controls](../economy/server/runtime.py), [profit presentation](../web/profitability.js).

## 11. Tick contract, randomness, and configuration

The authoritative order in `tick()` is:

1. Clear per-tick trading/earnings scratch; apply the shared exemption and full-payment operation gate; update difficulty.
2. Extract T0 raw stock.
3. Buy T1 raw inputs; produce T1 output.
4. Update T0 and T1 prices and stability samples.
5. Clear T3 distributors against opening T2 stock.
6. Buy/produce/reprice C3; settle its supplier book. Then do C4 and settle.
7. Accumulate observations; update monthly T0/T1 and T2 reliability.
8. Update AOV EMAs and yearly switching multiples.
9. Finalize net earnings and switching forecasts for future production.

There is no random global shuffle. Rotated processing orders and stateless seeded draws make the order explicit. Randomness uses unsigned 32-bit arithmetic (`mask=2³²−1`):

```text
mix(x): x=((x xor (x>>16))×0x85EBCA6B)&mask
        x=((x xor (x>>13))×0xC2B2AE35)&mask
        return (x xor (x>>16))&mask
random(seed,t,stream) = mix(seed xor (((t+1)×0x9E3779B1)&mask)
                               xor (((stream+1)×0x85EBCA6B)&mask)) / 2³²
hash(seed,k) = mix(seed xor (((k+1)×0x9E3779B1)&mask))
normal(seed,t,s) = sqrt(−2 ln(max(10⁻¹²,random(seed,t,s)))) × cos(2π random(seed,t,s+1))
```

Seed and initial mixer input are masked too. Difficulty uses streams `4×elementIndex`; raw tie-breaking uses `buyer+12,000,000+1,300,000×element`; distributor activation uses `buyer+2,000,000`, rounding `buyer+7,000,000`, and offer sample `buyer+8,000,000+1,100,000×sample`. Initial routing hashes `buyer+7,000,000`; choke hashes `buyer+9,000,000`, divided by `2³²`. The Python and compiled paths share these rules; Numba stock indexes accelerate offer lookup without changing ranking. Seed 137 is the default.

`normalize_config` ignores unknown fields, replaces nonfinite recognized numeric values with defaults, and applies bounds. Rates `theta`, activation, aggressiveness, alpha, and reliability alpha lie in `[0,1]`; loyalty EMA alpha in `[0.0001,1]`; distributor elasticity in `[0.05,10]`; margin band in `[0.001,1]`; market-anchor band and price response in `[0.001,1]`. Search draws are floored/clamped to `1…20`; price observation ticks to `1…360`; research thresholds to `0…1000`; maximum research age is floored to at least one tick. Seed is floored and masked to 32 bits.

T0 equity/license/machinery/reserve/capacity/storage/base cost/minimum lot have lower bound `1`. T1 equity/license/machinery/capacities/material reference and T2 equity/license/conversion factor have lower bound `10⁻⁶`; T2 machinery/capacities and all storage capacities have lower bound `1`. Footprints, rent, intelligence rates, markups, reservation premium, loyalty multiples, and sigma are nonnegative. Difficulty minimum is at least `0.01`, maximum at least minimum, and target is clamped between them. Choke minimum is at least `0.01`, maximum at least minimum; stability band is at least `10⁻⁹`. These bounds do not guarantee that configured starting equity covers all starting assets.

Distributor and T2 populations are integers bounded to `1…1,000,000` and `1…57,960`; a zero value selects the full-population default. Legacy `t1Capacity` without a C2 override applies to both; legacy `storage` without T1 overrides applies to both T1 cohorts. Integer-keyed configuration maps also accept string keys from JSON. Live population changes require Reset. Storage/footprint changes reject occupied-space overflow; live changes refresh references and distributor choke/elasticity, but do not redistribute firms/buyers, rewrite inventory basis, reset learned quotes, or immediately replace adaptive loyalty multiples.

Checkpoints store arrays in `.npz` and config, tick, scalar regimes, supplier history, and runtime metadata in a `.json` sidecar. The current format is version 10 and catalog revision `midbridge-invented-105-reverse-v7`; incompatible catalog revisions/numbering are rejected. Older checkpoints convert annual per-space rent once on load to the per-1,000-space, per-tick rate; new checkpoints store only the direct tick rate. Pre-version-10 checkpoints default missing intelligence rates and ledgers to zero and operation flags to enabled. Upon advancing, the new full-payment gate applies to rent too; historic rent debt is retained. Statistics version 3 records intelligence expense, cumulative payments, and stopped-company counts; product rows and company archives include intelligence expense separately. Global hexadecimal company identities reserve full-population ranges in order Gaia, T0, T1, T2, T3, even in reduced worlds.

Source: [tick.py](../economy/kernel/tick.py), [rng.py](../economy/core/rng.py), [config.py](../economy/core/config.py), [runtime.py](../economy/server/runtime.py), [persistence.py](../economy/server/persistence.py).

## 12. Verification and boundaries

The following tests exercise the implemented contract:

| Rule | Tests |
| --- | --- |
| Catalog, counts, costs, recursive demand | [midbridge](../tests/py/test_midbridge.py), [recursive demand](../tests/py/test_recursive_demand.py), [naming catalog](../tests/py/test_naming_catalog.py) |
| Extraction/refinery throughput | [extraction capacity](../tests/py/test_extraction_capacity.py), [refinery capacity](../tests/py/test_refinery_capacity.py) |
| Storage, recipe-weighted slots, live resizing | [storage slots](../tests/py/test_storage_slots.py), [C2 storage](../tests/py/test_c2_storage.py) |
| Price-sensitive inputs, available stock, distributor preferences | [buying](../tests/py/test_buying_price_sensitive.py), [production stock access](../tests/py/test_production_stock_access.py), [preferences](../tests/py/test_distributor_preferences.py) |
| Earnings, rent, intelligence, complexity balances | [net earnings](../tests/py/test_net_earnings.py), [rent](../tests/py/test_storage_rent.py), [intelligence](../tests/py/test_intelligence.py), [balances](../tests/py/test_complexity_balances.py), [browser profitability](../tests/js/test_profitability.js) |
| Randomness, execution, persistence/recording | [RNG](../tests/py/test_rng.py), [kernel](../tests/py/test_kernel.py), [review fixes](../tests/py/test_review_fixes.py), [recording](../tests/py/test_recording.py) |

Catalog weights calibrate a possible common-utilization flow; they do not guarantee equilibrium, equal material demand, profitability, or full-capacity operation. Cash, prices, purchase curves, rounded lots, sampled search, storage, and production gates determine realized outcomes. No runtime invention, C5 manufacturing, autonomous expansion, or distributor budget model should be inferred from dormant fields or older design material.
