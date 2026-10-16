# Design canon — implemented economy

This canon is reconstructed from the executable model, catalog, state initialization, trading kernels, and accounting. It specifies current behavior, including asymmetries and limits. Default values describe a fresh world; formulas apply to normalized configuration unless stated otherwise. Source links identify the implementation behind each group of rules. For worked examples and information-access boundaries, see the [decision walkthrough](decision_walkthrough.md).

## 1. Vocabulary, units, and scope

**Tier** identifies an actor's role. **Complexity** `c` is the number of raw ancestry units in one product, and therefore its occupied storage space. **Line** means one installed recipe machine. **Firm** owns shared cash, inputs, storage, and one or more lines. **Market** trades one exact resource or recipe, never interchangeable products of the same complexity.

| Tier | Operation | Default population |
| --- | --- | ---: |
| T−1 | Gaia: named raw-resource origin, no simulated supplier ledger | 1 identity |
| T0 | Extraction of raw Organics / Inorganics / Metals / Radioactives | 20 firms, 40 machines |
| T1 | Direct raw refining into C1 or C2 | 1,000 firms: 500 C1 and 500 C2 |
| T2 | Manufacturing C3 and C4 from lower-complexity products | 57,960 firms |
| T3 | Final purchase and consumption of T2 output | 1,000,000 distributors |

Money is floating-point dollars. Quotes are rounded to cents, half away from zero, and guarded to `[0.01, 10⁹]`; costs, fees, rent, and balances retain fractional cents. Prices may fall below cost. All realized physical quantities—extraction, production, purchases, sales and inventory—use whole units. Continuous targets and pre-rounding plans may be fractional; money and cost bases remain fractional. Raw items occupy one space; products occupy `c` spaces. Machines occupy configured fixed footprints. There is no depreciation, interest, ordinary credit, automatic insolvency exit, or spoilage in the tick. No new operating-cost liabilities are created; saved historical rent arrears remain a legacy liability only.

One month = 30 ticks; year = 360; generation = 7,200 (20 years); age = 172,800 (24 generations). Initialization is tick 0; ordinary execution begins at tick 1. Calendar month and year are one-based within their cycles; generation and age are zero-based.

Source: [model.py](../economy/core/model.py), [state.py](../economy/core/state.py), [runtime-defaults.json](../catalogs/midbridge-4263/runtime-defaults.json).

### Designated T0 roles (inactive)

The approved role roster replaces the earlier auxiliary assignments. Each company has one designated role, stored in `naming-source.json` and propagated to runtime and browser metadata. These assignments do not activate services, transfers, or exclusive extraction rights: all 20 firms retain their existing extraction coverage. Rent and intelligence remain cash sinks.

| Company | Designated role |
| --- | --- |
| Raw Materials Corp. | Raw materials |
| Elements Inc. | Raw materials |
| General Resources Corporation | Policy making |
| Integrated Extraction Corp., Inc. | Colony administration |
| Planetary Industries, Inc. | Market intelligence |
| Federated Supply Incorporated | Company marketplace |
| Standard Fiber & Mineral, Inc. | Automotive & machinery |
| Advanced Materials, Inc. | Finance |
| The People's Extraction Co., Inc. | Games & entertainment |
| Premier Harvest, Inc. | Research & inventions |
| Universal Material Extraction Corp. | Storage & logistics |
| The Oligarch | Finance |
| Organic Material Extraction Assoc., Inc. | Community |
| Old Toby & Daughters, Inc. | Community |
| Planetary Salt Corporation | Advertisement |
| Associated Silica, Incorporated | Advertisement |
| The Metal Mining Co., Inc. | Automotive & machinery |
| The Union Metal, Inc. | Storage & logistics |
| Amalgamated Isotopes Corp. | Bots & assistants |
| United Radioactives Company | Bots & assistants |

## 2. Recipes and population allocation

The structural symbols `W,E,F,A` map respectively to Organics, Inorganics, Metals, and Radioactives. They identify recipe ancestry independently of display names.

| Complexity | Immediate recipe | Full universe | Invented/active | Firms per active recipe | Capacity per line/tick |
| --- | --- | ---: | ---: | ---: | ---: |
| C1 | One raw → one refined basic | 4 | 4 | 97–99 | 6,000 |
| C2 | Two raw → one refined compound | 10 | 10 | 53–63 | 6,000 |
| C3 | One C1 + one C2 → one good | 40 | 36 | 1,058 | 32 |
| C4 | One C1 + one C3 → one good | 160 | 14 | 288 | 24 |
| C4 | Two C2 → one good | 55 | 55 | 288 | 24 |

Input order does not matter; repeated inputs are allowed and combined into their integer quantity. Nested recipes retain their identity: equal raw ancestry does not imply equal products. Counts follow `C2=4×5/2`, `C3=4×10`, `C4=4×40+10×11/2`. All recipes yield exactly one output. For ingredient quantities `aₚₘ` and ingredient space `sₘ`, `Σₘ aₚₘsₘ=cₚ`: production conserves goods space.

The active subset is the explicit list in [starting-selection.json](../catalogs/midbridge-4263/starting-selection.json), closed over its dependencies. It includes 105 T2 products; the other 150 have no active lines, demand, or purchasable machinery. C5 configuration slots remain for compatibility but have no active recipes. T2's input market contains 50 products: 14 T1 materials plus 36 invented C3 goods. Its first four input indices are **refined C1**, despite the internal `t2Raw` array name.

There are 14 material sectors paired with 14 manufacturing sectors. Each T2 recipe's sector is anchored to one direct T1 ingredient; sector sizes need not be equal. T0's extraction coverage comprises eight one-element, six two-element, four three-element, and two four-element firms.

T2 firm shares reverse the active product counts: C3:C4 firms = `69:36`, yielding 38,088 C3 firms and 19,872 C4 firms. Within each complexity, firms are apportioned equally over recipes. Integer apportionment floors each weighted share and distributes remainders by descending fractional remainder, then ascending key. A reduced `t2FirmCount` takes a prefix of this catalog-ordered allocation; it does not rescale every product cohort.

For product `p`, let default gross output capacity be `gₚ = firmCountₚ × defaultCapacityₚ`. Uncalibrated final-demand weight is

```text
wₚ = gₚ − Σ downstream T2 products j (aⱼₚ × gⱼ)
```

All active weights are positive. Gross T2 capacity totals 1,695,744 items/tick; intermediate C3 use reserves 96,768; final-output weights total 1,598,976. These are capacity weights, not promised sales. Recursively expanding final demand reconstructs gross capacity: `xₚ=wₚ+Σⱼaⱼₚxⱼ`, evaluated from C4 down to C3. T1 requirements are `rₘ=Σₚaₚₘxₚ`; they are not equal across materials.

Current final routing weight is `vₚ = wₚ × k_complexity`, with C3 `k=1` and C4 `k=0.80`. This static calibration targets closer late-run mean net earnings per company; equal unit demand and guaranteed profits are not model rules. C3/C4 buyer shares change from 70.17%/29.83% to 74.62%/25.38%; total T3 count and all T0/T1/T2 company counts stay fixed, while T3 counts assigned to each complexity change. Intermediate reservations in `w` remain capacity-based; only final-consumer routing is multiplied. Recursive calibrated demand therefore no longer reconstructs nominal capacity.

T3 distributors are companies. The multiplier reallocates those companies between product markets at fresh-world initialization; it does not change T2 producer counts. Normalize each product weight as `shareₚ = vₚ / Σⱼvⱼ`, then assign the fixed `distributorCount` population by stratified midpoint sampling of the cumulative product weights. Each product receives within one company of its ideal share; group totals below reflect the actual integer assignment for the default one-million-company population.

| T3 companies assigned to | Original multiplier 1.00 | Current multiplier 0.80 | Change |
| --- | ---: | ---: | ---: |
| C3 products | 701,729 | 746,245 | +44,516 |
| C4 products | 298,271 | 253,755 | −44,516 |
| Total T3 | 1,000,000 | 1,000,000 | 0 |

Uncalibrated group weights are `W3=1,122,048` and `W4=476,928`. Thus C4's ideal share is `0.80×W4/(W3+0.80×W4)=25.375421…%`. Multiplying its weight by 0.80 reduces its assigned company count by approximately 14.92%, rather than 20%, because both groups are normalized back to the same total. T2 remains 38,088 C3 and 19,872 C4 companies. Assigned T3 companies are potential customers, not guaranteed sales; activation, price sensitivity, stock and switching still govern transactions. These assignments stay fixed during a run. The original and 0.80 initial checkpoints verify the counts above.

The first trial used C4 multiplier 0.61. It completed 7,200 ticks with final-year C3/C4 earnings $211.84/$143.44 per company/tick, versus $162.37/$323.72 in the multiplier-1 baseline. Its full-generation absolute earnings gap grew and final-year C4 losses rose from 23 to 2,279 firms, so it did not achieve the target. Linear interpolation of the final-year C4-minus-C3 earnings gap against the multiplier gives 0.726118; the second fixed trial used 0.73. Completed evidence is in `stats/t3-calibration061-1generation-20261013-173640/experiment-report.md` and `next-calibration.json`.

The second trial (0.73) completed with final-five-year C3/C4 net earnings $226.77/$185.38 per company/tick, a ratio of 0.8175, consistently below equality across those five years. Interpolating that period’s earnings gap against the multiplier-1 baseline gives 0.785289; the third trial used 0.79. The user-confirmed comparison target is a C4/C3 mean earnings ratio of 0.90–1.10 over the final five years, with annual trends and other tiers reported. Evidence: `stats/t3-calibration073-1generation-20261013-181422/experiment-report.md` and `next-calibration.json`.

The completed 0.79 trial supplied the calibration evidence. The user subsequently rounded the current multiplier to 0.80; its earnings balance is not established by the 0.79 result. Final-five-year C3/C4 net earnings were $254.29/$262.64 per company/tick: ratio 1.0329, versus 1.9786 in the baseline. Annual ratios in years 16–20 stayed between 1.0195 and 1.0439. Final-year earnings were $250.20/$255.49 (ratio 1.0211); whole-generation earnings were $229.04/$203.74, so startup earnings were not equalized. All 7,200 ticks, 20 annual archives, checkpoints, source hashes and income/payment reconciliations passed; no prepayment stops or new arrears occurred. Tradeoffs include lower final-five-year C2 earnings ($4,479.91 → $2,237.26/company/tick) and consumer fulfillment (99.966% → 99.683%). This met the user-confirmed late-run target at 0.79 for one seed and one generation, not universal or indefinite equality. Evidence: [completed comparison](../stats/t3-calibration079-1generation-20261013-190034/experiment-report.md).

The subsequent 0.80 run already diverged from that result: in ticks 5,761–6,120, C3/C4 net earnings were $161.47/$232.02 per company/tick, a 43.70% C4 advantage. This is an interim annual observation, not a completed-generation comparison. Source: `stats/t3-calibration080-1generation-20261014-140140/generation_run.jsonl`. The static allocation does not enforce equal earnings.

Original calibration evidence is seed-137 balanced-T1 ticks 3961–4320: net earnings averaged $179.72/C3 company/tick and $331.37/C4 company/tick. Holding prices, unit gross contributions, charges and fill rates fixed, and scaling C3 intermediate sales with C4, gives a C4 multiplier estimate 0.61024, rounded to 0.61. C3 is near capacity, so additional demand may change prices or remain unfilled. This is an experimental starting point, not an equilibrium prediction. Reproduction: `stats/balanced-t1-1generation-20261013-165926/calibrate_t3.py`, with period totals in `t3-calibration-data.json`.

Specifically, let `b` be the old C3 buyer share; `A` and `I` be C3 retail and intermediate gross profit per company/tick; `G` be C4 gross profit per company/tick; and `ΔH` be C3 minus C4 net overhead (rent + intelligence + switching expense − switching income). Approximate C3 intermediate gross profit using its share of C3 sold units. For relative C4 weight `m`, normalized demand scales are `x3=1/[b+(1−b)m]` and `x4=m/[b+(1−b)m]`. Solving `A×x3+I×x4−H3=G×x4−H4` gives `m=(A−ΔH×b)/(G−I+ΔH×(1−b))`. No live feedback or earnings transfer is introduced.

Distributor assignment uses midpoint-stratified draws `(k+½)Σv/N`, mapped into cumulative product weights, with buyers ordered by seeded hash. Each product gets within one buyer of its ideal share. Assignment is fixed at initialization and uses **default full-fleet capacities and the fixed complexity multipliers**, even when live capacities or population are changed. It does not follow shortages.

Source: [catalog adapter](../economy/core/midbridge.py), [model allocation](../economy/core/model.py), [initialization](../economy/core/state.py), [catalog validator](../tools/build_recursive_catalog.py).

### Refinery population allocation

There are **1,000 T1 firms: 500 C1 / 500 C2**, distributed equally within each complexity: **125 companies for each of four C1 products**, and **50 for each of ten C2 products**. This user-selected allocation is being researched over six generations; equal counts do not imply equal demand or earnings per company. The research comparison uses actual net earnings per company at exact tick 43,200, without averaging or adding back fixed costs.

Nominal recipe demand remains available as a diagnostic: `Dₘ = Σₚ T2FirmCountₚ × nominalCapacityₚ × ingredientQuantityₚₘ` over direct T1 ingredients of active T2 products. C3 capacity already includes C4 intermediate use, so do not recursively double-count it. T2 populations, T3 routing and economic rates are unchanged.

Native cohort maps govern names, storage and firm traversal. Runtime config changes do not reallocate companies. Catalog revision v17 rejects older checkpoints rather than reinterpreting their holdings. Global company-number blocks follow the new population. Existing experiments retain their frozen sources and populations.

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

Define conversion per output item `v(c)=conversionFactor×max(1,c−1)`, with factor `0.25`. Thus C1/C2 cost `0.25`, C3 `0.50`, C4 `0.75`. Keep the existing base production-cost ladder `Uₚ` separate from the overhead-inclusive decision reference `Vₚ`:

```text
T0: Uₑ⁰ = baseCost × difficultyTarget
T1: Uₚ = Σₑ aₚₑ × t1MaterialCost + v(cₚ)
T2: Uₚ = Σₘ aₚₘ × Uₘ × (1+t1Markup) + v(cₚ)
Hc = nominal company storage / 1000 × storageRentPerThousandPerTick + intelligencePerTick
hc = Hc / nominal per-line output capacity
multiplier(B,c) = 1 + hc/B
adjusted reference = B × multiplier(B,c) = B + hc
Vₚ = Uₚ + hc
starting quote = cent(Vₚ × (1 + starting markup))
```

T0 has no rent/intelligence bill, so its reference and initial quote remain unchanged. For T1 use `t1C1Storage`/`t1C2Storage` and `t1Capacity`/`t1CapacityC2`; for T2 use `storage` and `t2Capacity[c]`. Each is a stable one-line-company calibration, independent of current equity, exemption, sales, utilization, or additional installed lines. Actual company bills are still shared across installed lines for the production gate. The allowance adds only the product producer's own overhead; it does not recursively add upstream overhead to `U`. C4 recipe routes therefore retain distinct bases and multipliers.

Both markups default to `0.25`; `baseCost=1`, `t1MaterialCost=1.25`. The latter is an independent configuration value. The unadjusted recursive ladder uses unrounded ingredient bases plus markup. Only each final starting quote is rounded.

| Route | Base U | Own overhead/item h | Pricing reference V | Starting quote |
| --- | ---: | ---: | ---: | ---: |
| Raw at difficulty 1 | $1 | $0 | $1 | $1.25 |
| C1 | $1.50 | $0.3566667 | $1.8566667 | $2.32 |
| C2 | $2.75 | $0.3566667 | $3.1066667 | $3.88 |
| C3 = C1 + C2 | $5.8125 | $2.375 | $8.1875 | $10.23 |
| C4 = C1 + C3 | $9.890625 | $3.1666667 | $13.0572917 | $16.32 |
| C4 = C2 + C2 | $7.625 | $3.1666667 | $10.7916667 | $13.49 |

Starting quotes and T2/distributor price-sensitivity references include this allowance. T2's C1 purchase reference retains its distinct base of $1.25 and adds $0.3566667, giving $1.6066667. C2 and C3 input references become $3.1066667 and $8.1875. T1 raw sensitivity still uses the T0 reference ($1): the producer of that input pays no rent/intelligence. Switching-fee reference costs remain unadjusted. Updating configuration refreshes derived demand references and compiled caches, without resetting learned quotes or revaluing inventory. New player-installed lines seed quotes with the same own-overhead allowance.

Actual production uses purchased inventory's weighted book basis. Before buying, a separate replacement estimate uses planned output `d`, held inputs `Rₘ`, their basis `bₘ`, and planning quotes `Qₘ`:

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

For single default lines, finished targets are C1 `24,500`, C2 `12,250`, C3 `2,833`, C4 `2,000`. A C3 `C1+C2` machine targets `8,500/3` units of each ingredient (weighted space 1:2). A C4 `2×C2` machine targets 4,000 C2 inputs; `C1+C3` targets 2,000 of each. Input targets can be fractional; T2 purchases round stochastically to whole units, capped by feasible whole units. T1 purchases round stochastically to 1,000-unit lots. T1 storage capacity follows the firm's original C1/C2 cohort even after it installs other machines.

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

Up to six further passes compute `feasibleₑ=min(remainingDeficitₑ,floor(max(0,cash)/kₑ))` and `budget=max(0,min(remainingCapacity,freeSpace,Σfeasible))`. If the budget covers all feasible deficits, use them; if below one, split it proportionally; otherwise floor proportional quotas of `floor(budget)` and allocate remaining units by largest remainder, breaking ties by rotated priority. Each planned make is recapped by its deficit, shared capacity, space, and cash using a provisional ledger. After all allocation passes, each element's complete feasible quantity `Qₑ` becomes `madeₑ=Qₑ/(1+(kₑ/(baseCost×difficultyTarget))^t0InputElasticity)`. Default eta is 2. The allocator does not redistribute withheld cash, space, or capacity after this reduction. This reduced quantity is stochastically rounded to whole units and capped by `floor(Qₑ)`; only actual integer `madeₑ×kₑ` is charged to cash/cost sinks, and inventory basis is averaged using actual extraction.

### Raw procurement

T1 firms alternate material cohorts and firms within cohorts: first cohort `tick mod 14`, first local firm `(37×tick) mod cohortCount`, then `max(cohortCount)=99` rounds through all 14 cohorts. Skip a cohort once its own number of rounds has elapsed; each company buys exactly once. Its global index is `cohortOffset + ((37×tick+round) mod cohortCount)`. Within a firm, inputs are processed in element-index order. Each positive slot shortage is the preliminary request. Whole-lot rounding happens after price sensitivity, with `L=minWholesaleLot=1,000`.

T0 supplier ranking minimizes `quote×max(request,L)+switchingFee`, first among suppliers holding at least one lot; only if none qualify does it consider empty suppliers. It does **not** require full-order stock for this ranking. An incumbent tied on a positive request is retained. Other equal-cost ties use seeded random weights `1/supplierElementCount`.

The order is capped by total free storage and the input slot, then by cash and seller stock using §6. Apply the final price response with `V=baseCost×difficultyTarget` (default $1), `eta=t1InputElasticity=2`, and round stochastically to whole lots. There is one supplier transaction per input per tick, without a second-supplier retry. Demand credited to the seller is the reduced, lot-rounded feasible order; availability asks whether it held the original shortage request. Successful purchase updates the preferred supplier even on a partial fill. Sub-lot stock and slot shortages wait.

Source: [operate_tier0 / plan_and_buy_inputs](../economy/kernel/tick.py), [compiled raw buying](../economy/kernel/numba.py).

## 6. T2 input buying and producer-order settlement

T2 buys C1/C2 from T1 and invented C3 from T2. For each required ingredient `m`, calculate preliminary request `r` as the nonnegative minimum of slot shortage and free goods space divided by `sₘ`. Whole-unit rounding follows the price response.

Offers are sorted by quote. T1 equal-quote ties rotate by `(marketRank+tick) mod marketSize`; T2 ties use `(lineIndex+37×tick) mod totalT2Lines`. Select the cheapest seller able to fill `max(1,r)`; failing that, the cheapest with at least one unit; failing that, the first offer. Retain a stocked incumbent if its total for that common quantity is no greater than the challenger's total including switching. A zero-request planning lookup is price-only.

After supplier selection, cash, stock and any switching fee establish a feasible order. Price reduces that feasible quantity:

```text
Vₘ = t1MaterialCost + h₁             for refined C1 (default 1.6066667)
   = refinery base Uₘ + h₂          for C2 (default 3.1066667)
   = recursive base Uₘ + h₃         for C3 (default 8.1875)
reduced = feasible / (1 + (chosenQuote/Vₘ)^etaInput)
```

The C1 purchase reference retains a different base from its production-cost ladder; both receive the same per-item overhead allowance. This input curve uses `t2InputElasticity=2`, independent of distributor `elasticity=2`. Lowering this exponent increases permitted orders when quote exceeds reference cost. Its price-curve base quantity is the **feasible purchase**, after shortage, space, cash, stock and fee constraints. At the reference price it halves even a small replenishment order. There is one transaction per required ingredient per complexity phase; inputs are processed in index order. Purchases can consume cash subsequently needed for conversion.

Both producer buying tiers use the same final settlement. For selected seller `s`, incumbent `i`, preliminary request `q`, lot size `L`, cash `C`, and stock `I`:

```text
fee = M×U×(1+clamp(reliabilityᵢ,0,1)) if s≠i, i exists, and Iᵢ≥q; otherwise 0
feasible = max(0, min(q, Iₛ, max(0,C−fee)/Pₛ))
reduced = feasible / (1 + (Pₛ/V)^eta)
x = reduced / L
roundedLots = floor(x) + 1[u < x - floor(x)]
filled = L × min(roundedLots, floor(feasible/L))
```

For T1, `L=1,000`; for T2, `L=1`. Do not lot-round the feasible quantity before applying eta. If the fee is positive and `filled×(Pᵢ−Pₛ)≤fee`, revert to the incumbent, discard the provisional order, and recompute feasibility and one price reduction at the incumbent's quote without a fee. This is a replacement calculation, not a second reduction of already reduced units. Charge a fee only for a positive fill. Do not refill the quantity withheld by eta. Later ingredients use remaining actual cash, as before.

Recorded funded demand and deliveries both equal the final feasible, reduced and rounded order; preliminary need/request and supplier availability checks remain separate. Thus this procurement path no longer reports stock-capped quantities as unfulfilled seller demand. T0/T1 price learning still uses its existing demand/sales inputs, but this changes the input to its shortage branch. T2 still also receives distributor demand through the unchanged retail mechanism.

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

The fixed fee is `M×U×(1+r)`, using incumbent reliability `r` clamped to `[0,1]`. The reference `U` is `baseCost` for T1 raw buyers, the unweighted mean of all 14 unadjusted refinery bases for T2 input buyers, and the purchased product's unadjusted recursive base for distributors. T2 uses the complexity of its **first installed line** to choose its fee regime, including on mixed-complexity firms.

Initially `M₁=50/(baseCost×1.5)`, `M₂,C3=M₂,C4=1.5/(meanRefineryCost×1.5)`, and `M₃=1.5/(weightedMeanT2Cost×1.5)`. The T2 mean is `$2.392857…`; the T3 routing-weighted mean is `$6.389078…`. At reliability `0.5`, initial T1 and T2 fees are `$50` and `$1.50`; distributor fees vary with the purchased product's reference cost. The unused C5 multiple starts at zero. Configured `loyaltyMultiple` overrides these initial values.

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

At the end of each tick, each active line accumulates revenue, gross profit `revenue−COGS`, sales, `max(recordedDemand,sales)`, and one observation tick. Sales and demand EMAs update with `alpha=0.15`; price learning uses window totals, not these EMAs. Rent, intelligence, and switching transfers are excluded from learned gross profit.

A line can reprice when its observation age is at least `priceObservationTicks=30` and `(tick+lineIndex) mod priceObservationTicks=0`. Current-tick trades have not yet entered its learning window. Manual finite quotes on player-controlled lines override learning at that line's pricing phase. Setting a manual quote clears its observation window, baseline, and step history; the T2 command also changes its live quote immediately, while T0/T1 apply it at their pricing phase. The online flag does not gate automated buying or production.

The market anchor is `ΣPᵢ×windowSalesᵢ/ΣwindowSalesᵢ`, falling back to the mean finite quote with no sales, or zero with no quotes. Prices are current quotes weighted by accumulated sales, not historical transaction-price averages. The gross-profit comparison normalizes both periods to the latest observed unit cost. For current window revenue `R`, gross profit `G`, units sold `Q`, and duration `T`, use `c=(R−G)/Q` when `Q>0`. When `Q=0`, use the current inventory cost basis (`t0InvBasis`, `t1FinBasis`, or `t2FinBasis`); the current score is zero. Retain the preceding completed window’s revenue per tick `rprev` and units sold per tick `qprev`. Compute `π=R/T−c×Q/T` and `πprev=rprev−c×qprev`. Both periods use the same `c`, including when their durations differ. A cost-only change with identical revenue and volume therefore yields no score change. This is a gross-profit learning comparison, not an accounting restatement or a causal isolation of demand/availability changes.

Given these comparable scores `π` and `πprev`, stored direction `d∈{−1,+1}`, and step scale `s`:

1. If accumulated demand exceeds accumulated sales by more than `10⁻⁹`, choose `d'=+1`.
2. Otherwise, if the quote is above/below the market anchor's `±marketAnchorBand` (default 2%), choose down/up respectively.
3. Otherwise, with finite `πprev`, compute `δ=(π−πprev)/max(|πprev|,10⁻⁹)`. If `δ<−0.02`, reverse direction; if `δ>0.02`, retain it; otherwise hold the quote and step. Without a baseline, retain the initial direction.
4. On movement, `s'=clamp(s×(1 if direction changed else 1.2),0.01,1)` and `P'=cent(clamp(P×exp(d'×pricingAggressiveness×wholesalePriceResponse×s'),0.01,10⁹))`. Defaults are `0.35` and `0.05`, so a full upward step is about 1.765% before cent rounding. If a downward step rounds back to the same price, store upward direction for the next attempt.

Steps initialize at 1; initial direction alternates by `(firm+seed)` parity. With the current update rule a default step stays at 1; changing direction does not shrink it. After an eligible learning decision, including a hold, save `R/T` and `Q/T` as the next comparison baseline and reset the window accumulators. `LearnPrevious` retains the latest score for diagnostics; it is not the next comparison’s fixed-cost baseline. New lines and manual price overrides clear revenue/volume history. Checkpoint version 14 persists these arrays. Loading an older compatible checkpoint clears its learning windows and baselines because the necessary prior revenue/volume evidence is absent; quotes, direction/step, inventory and accounting are preserved. Shortage priority and competitor-anchor overrides remain unchanged.

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

Net earnings, equity, dashboard margins, and recorded product/company accounts include intelligence; gross profit and inventory basis do not. Price learning still uses gross profit, not net earnings. Billing does not vary the configured procurement reference by current exemption; buying can still be constrained by reduced cash or stopped operation. Stopped sellers are excluded from offers and market price anchors; saved preferences cannot bypass the stop. The production gate uses paid rent/intelligence, while a standalone pre-billing forecast uses current eligibility.

Goods and producer switching payments transfer cash internally. Distributor goods/fee payments inject cash. Extraction, conversion, paid rent, and paid intelligence are operating cash sinks; machinery purchases are equipment sinks. For ordinary ticks without administrative equipment transactions:

```text
Δ(total producer cash) = distributorPayments − extractionCosts − conversionCosts − rentPaid − intelligencePaid
```

Equipment purchase moves its configured price from firm cash into machinery book value, preserving equity. T1 player firms may add any uninstalled refinery recipe if cash and physical space suffice. T2 player firms may add an invented recipe only within their sector/capability, without duplication, with enough cash/space, and at most four lines per firm. Bots never add lines automatically. New machines repartition storage targets without moving or deleting existing goods. A new T1 quote uses the lowest finite wholesale quote for each ingredient (falling back to `baseCost`) plus conversion and its nominal overhead allowance, then markup; a new T2 quote uses its overhead-inclusive reference and markup. T0 has no runtime equipment-buying path.

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

`normalize_config` ignores unknown fields, replaces nonfinite recognized numeric values with defaults, and applies bounds. Rates `theta`, activation, aggressiveness, alpha, and reliability alpha lie in `[0,1]`; loyalty EMA alpha in `[0.0001,1]`; distributor and T0/T1/T2 input elasticity in `[0.05,10]`; margin band in `[0.001,1]`; market-anchor band and price response in `[0.001,1]`. Search draws are floored/clamped to `1…20`; price observation ticks to `1…360`; research thresholds to `0…1000`; maximum research age is floored to at least one tick. Seed is floored and masked to 32 bits.

T0 equity/license/machinery/reserve/capacity/storage/base cost/minimum lot have lower bound `1`. T1 equity/license/machinery/capacities/material reference and T2 equity/license/conversion factor have lower bound `10⁻⁶`; T2 machinery/capacities and all storage capacities have lower bound `1`. Footprints, rent, intelligence rates, markups, reservation premium, loyalty multiples, and sigma are nonnegative. Difficulty minimum is at least `0.01`, maximum at least minimum, and target is clamped between them. Choke minimum is at least `0.01`, maximum at least minimum; stability band is at least `10⁻⁹`. These bounds do not guarantee that configured starting equity covers all starting assets.

Distributor and T2 populations are integers bounded to `1…1,000,000` and `1…57,960`; a zero value selects the full-population default. Legacy `t1Capacity` without a C2 override applies to both; legacy `storage` without T1 overrides applies to both T1 cohorts. Integer-keyed configuration maps also accept string keys from JSON. Live population changes require Reset. Storage/footprint changes reject occupied-space overflow; live changes refresh references and distributor choke/elasticity, but do not redistribute firms/buyers, rewrite inventory basis, reset learned quotes, or immediately replace adaptive loyalty multiples.

Checkpoints store arrays in `.npz` and config, tick, scalar regimes, supplier history, and runtime metadata in a `.json` sidecar. The current format is version 14 and catalog revision `midbridge-invented-105-t1-equal-complexity-500-v17`; incompatible catalog revisions/numbering are rejected. The current 500/500 allocation changes T1 company-to-product identity; checkpoints from other allocations must use their frozen source. Older checkpoints convert annual per-space rent once on load to the per-1,000-space, per-tick rate; new checkpoints store only the direct tick rate. Pre-version-11 checkpoints retain T2 input elasticity 2 when the setting is absent. Missing T0/T1 input elasticities default to 2. Pre-version-14 checkpoints reset learning evidence as described in §9. Pre-version-13 checkpoints recompute the stored T2 demand-reference array with the overhead allowance on load; quotes, inventory basis, cash, and expense ledgers are preserved. Loading an older compatible checkpoint preserves its state but subsequent ticks use the final-feasible-quantity procurement rule; use the original frozen source to reproduce historical trajectories. Pre-version-10 checkpoints default missing intelligence rates and ledgers to zero and operation flags to enabled. Upon advancing, the new full-payment gate applies to rent too; historic rent debt is retained. Statistics version 3 records intelligence expense, cumulative payments, and stopped-company counts; product rows and company archives include intelligence expense separately. Global hexadecimal company identities reserve full-population ranges in order Gaia, T0, T1, T2, T3, even in reduced worlds.

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

The producer comparison shows **Empty / total** beside Inventory · units: remaining empty storage divided by full storage capacity, as a percentage. Empty space excludes installed machinery and inventory weighted by product complexity. T0 has no modeled machinery footprint. Tier ratios divide summed empty space by summed capacity; complexity rows allocate both quantities equally across installed lines. Per-company and totals tables show the same ratio; zero capacity is unavailable.

**Inventory · $** in the producer comparison sums quantity × recorded cost basis for raw inputs, intermediate inputs and finished goods. It excludes machinery and uses no sale-price markup. Tier and complexity allocation follows the inventory-unit rows; per-company figures divide by represented firms.

The dashboard’s **Run · 1 tick / 2 s** mode advances immediately, then schedules one tick every 2 seconds, counting tick processing and publication time within that interval. Max-speed and single-step controls retain their existing behavior.

**Return on Cash · bps** beside Net Profit in the producer comparison is current-tick net profit divided by current cash, multiplied by 10,000 and displayed in basis points to one decimal place (100 bps = 1%). It uses aggregate profit / aggregate cash for both totals and per-company views, not an average of individual company ratios. Zero or missing cash and unavailable profit display “—”. This is a per-tick measure, not an annualized return.


Stochastic quantity rounding uses seeded, stateless draws: T0 extraction stream `100000000 + supplier×NE + element`; T1 purchase stream `110000000 + company×NE + element`; T2 purchase stream `120000000 + firm×NI + material`. Each is keyed by seed and tick; an incumbent recheck reuses its original draw. For `x=n+f`, buy `n+1` units/lots with probability `f`, otherwise `n`, capped by whole feasible units/lots. T3 retains its existing seeded stochastic demand rounding. No fractional physical units are created; historical fractional checkpoints are not silently rounded or revalued. `minWholesaleLot` is normalized to a positive integer.

### T1 market latent-demand telemetry

The material table’s **Latent @ zero price** sums operating T2 buyers’ whole-unit input shortfalls at their actual sequential buying decisions: `floor(max(0, min(input slot − held input, free goods spaces / ingredient complexity)))`. Count each required T1 ingredient once per company per complexity phase, including when no supplier has stock. This measures replenishment need before supplier availability, cash, switching fees and price sensitivity; stopped buyers contribute zero. Earlier purchases in the tick still affect available space. It is not nominal recipe demand, a simultaneous all-prices-zero counterfactual, or the cash/stock-constrained base used by the actual price curve.

The existing `potential` per-material array records this telemetry, resets every tick and is included in checkpoints; older runs did not populate it and cannot supply historical latent demand. The measurement does not alter orders, rounding, learning or settlement. Customer desired remains the actual reduced funded orders; their difference from latent need cannot be attributed solely to price.
