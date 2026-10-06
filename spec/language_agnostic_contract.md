# Language-agnostic kernel contract — Phase 0 (as-is)

> **Status:** captures the *current* source kernel as of the October 2026 calibration
> freeze. This is the pivot artifact that lets the economy kernel move from the current
> JavaScript implementation to a Python/NumPy/Numba implementation without re-deriving
> the machine-level rules. It is a **computational** contract; the *economic* intent,
> rationale and acceptance criteria live in [`economy_contract.md`](economy_contract.md).
>
> **As-is caveat.** Economic calibration is ongoing and no parameter standard is
> adopted ([`economy_calibration_status.md`](economy_calibration_status.md)). The
> defaults below are the authoritative runtime defaults in
> [`engine/model.js`](../engine/model.js) `ECONOMY_DEFAULTS` and
> [`phase0_economy_engine_worker.js`](../phase0_economy_engine_worker.js) `defaultCfg()`,
> not validated calibration endpoints. This document describes **how the machine runs**;
> parameter values are subject to the calibration outcome.

---

## 1. Purpose and authority

This contract defines, language-independently:

1. the **portability model** (what must be bit-exact vs. tolerance-based);
2. the **canonical random streams and arithmetic rules**;
3. the **configuration schema** (`cfg`);
4. the **world-state schema** (`W`) as a record of typed arrays;
5. the **canonical tick order**;
6. the **runtime interface** (commands and read projections).

Authority rule: the source implementation is the single authority for *current*
behavior. A new rule is first specified in `economy_contract.md`, implemented in
readable source, and covered by deterministic tests. This document does not invent
rules; it transcribes the existing machine rules into a portable specification.

Source files referenced throughout:

- [`engine/model.js`](../engine/model.js) — static catalogue, pricing/demand primitives, `ECONOMY_DEFAULTS`.
- [`engine/reference_kernel.js`](../engine/reference_kernel.js) — the economic tick and its rules.
- [`phase0_economy_engine_worker.js`](../phase0_economy_engine_worker.js) — world-state layout, configuration, initialization, runtime interface, scheduler.

---

## 2. Portability model

"Porting to Python" is **not** required to reproduce the JS floating-point trace.
The contract distinguishes two fidelity classes.

### 2.1 Exact class (must reproduce identically across languages)

These are **categorical or integer** decisions. A single different result changes
*which* entity is sampled, *how many* whole units move, or *which* line is installed —
a structural divergence, not a rounding one. Reproduce bit-for-bit:

- the 32-bit integer RNGs (§3.1);
- all `floor` / `ceil` / `round` / remainder operations that produce **whole units,
  whole lots, integer quantities, integer ticks, indices, or counts**;
- the Tier 0 proportional-apportionment and its remainder/tie rules (§8.2);
- whole-lot (1,000-unit) and whole-unit rounding of purchases/production;
- portfolio enumeration, recipe enumeration, and the invented-market selection (§4);
- iteration/sort orders that determine tie-breaking and rotation (§7, §8).

### 2.2 Tolerance class (IEEE-754 double required, last-ulp allowed)

Float64 arithmetic where the *contract* must match but bit-identical libm results are
not guaranteed across runtimes. Required: IEEE-754 double semantics, the same formulas,
the same epsilon guards, and a declared tolerance. Includes:

- weighted-average cost bases and EMA updates;
- the demand curve `q / (1 + (P/V)^eta)` and `exp`/`pow` price moves;
- `sqrt`, `log`, `cos` (Box-Muller), and aggregate summations.

Declared tolerance: individual scalar floats agree to `1e-9` relative (or absolute,
whichever is larger), and **no** structural difference (counts, indices, directions,
selected suppliers) results from a last-ulp float difference. If a float difference
could flip an integer decision, that decision must be anchored to the exact class
(e.g., compare against `+1e-9`/`-1e-12` guards as specified, using the same guard constants).

### 2.3 Determinism contract (single implementation)

Given `(seed, cfg, initial state, exact command sequence)`, **one** implementation must
reproduce identical state on every run. This requires:

- a deterministic RNG (§3.1) with no hidden non-deterministic source;
- deterministic iteration order (the rotations in §7 and §8 are part of state);
- no dependence on wall-clock, hash-map enumeration order, or floating-point
  summation order where a tie-break could change a categorical decision.

Replay within a build is strict; cross-language replay follows §2.1/§2.2.

---

## 3. Canonical random streams and arithmetic

### 3.1 Integer RNG primitives (exact)

All RNG is 32-bit unsigned integer arithmetic. `imul32(a, b)` denotes the low 32 bits
of the product `a·b` re-read as unsigned 32-bit (JS `Math.imul(a,b) >>> 0`); `>>> n`
is an unsigned right shift; `^` is bitwise xor.

SplitMix32 finalizer:

```
mix(u):
  x = u            (u is u32)
  x = imul32(x ^ (x >>> 16), 0x85ebca6b)
  x = imul32(x ^ (x >>> 13), 0xc2b2ae35)
  return (x ^ (x >>> 16))        as u32
```

Tick-stream uniform:

```
random(seed, tick, stream) =
  mix( (seed ^ imul32(tick + 1, 0x9e3779b1) ^ imul32(stream + 1, 0x85ebca6b)) )
  / 4294967296                   → Float64 in [0, 1)
```

All of `seed`, `tick`, `stream` are treated as u32 (`x >>> 0`).

Box-Muller normal (used only for extraction-difficulty shocks):

```
normal(seed, tick, stream) =
  sqrt(-2 * ln(max(1e-12, random(seed, tick, stream))))
  * cos(2 * π * random(seed, tick, stream + 1))
```

Consumer-initialization hash (worker `hashSeed`, no stream term):

```
hashSeed(seed, k) =
  mix( seed ^ imul32(k + 1, 0x9e3779b1) ) / 4294967296   (where k is u32)
```

The stream offsets used by each consumer of the RNG are part of the exact contract and
are listed inline in §8 and §9.1. (The `RNG` xorshift class in the worker is defined but
not referenced by the current path; it is not part of this contract.)

### 3.2 Float64 arithmetic and price quantization

- All money, prices, costs, quantities-in-basis, EMAs, reliabilities are **IEEE-754 double**
  (Float64), except the compact end-user taste fields (§6.5) which are Float32.
- Price quantization (posted quotes and player-price inputs):

  ```
  quantW(x, floor) = max( round(x * 1e5) / 1e5,  ceil((floor - 1e-12) * 1e5) / 1e5 )
  quantR(x, floor) = quantW(x, floor)
  ```

  Five-decimal price granularity; a numerical floor of `MIN_UNIT_PRICE = 0.00001`.
- Epsilon guards in comparisons use the literal constants `1e-9` and `1e-12` exactly as
  written in the kernel; do not substitute a different epsilon.
- Negative inventory, cash, demand or reliability is a contract violation (§10).

---

## 4. Static topology and catalogue

Summary only; the authoritative data is `engine/model.js`. A reimplementation must
reproduce these objects **exactly** (counts, order, codes, recipes, selection).

| Constant | Value |
| --- | --- |
| Elements `NE` | 4 — Water, Earth, Fire, Air (order fixed) |
| Tier 1 products `NP` | 10 — 4 basic C-1 + 6 compound C-2 (order fixed) |
| Tier 0 firms `N0` | 20, with fixed element profiles (`T0P`) |
| Tier 1 firms `N1` | 1,000 — 100 per product cohort |
| Tier 2 firms `N2_FIRMS` | 61,950 |
| Tier 2 max lines `MAX_T2_LINES` | 247,800 (`N2_FIRMS × 4`) |
| End users `N_END_USERS` | 1,000,000 |
| Time | 30 ticks/month, 12 months/year, 20 years/Generation, 24 Generations/Age, 172,800 ticks/Age |
| Tier 2 catalogue | 420 recipes: 44 C-3, 116 C-4, 260 C-5 |
| Invented markets | 200 (20/60/120), 220 reserved |

- **Recipe keys** are unordered multisets of Tier 1 material codes, canonicalized by
  `recipeKey(inputs)` (sorted `code:qty` joined by `|`). Ingredient permutation does
  not create a new market; processed intermediates retain distinct identity.
- **Complexity** = sum over ingredients of `qty × elemental ancestry` (basic = 1,
  compound C-2 = 2). C-1/C-2 belong to Tier 1; C-3–C-5 to Tier 2.
- **Invented-market selection** is the deterministic Hamilton-like balancing pass in
  `engine/model.js` (2/6/12 per sector, 20 per sector); reproduce it exactly.
- **Portfolios**: per sector, all unordered 1–4-product subsets of its 20 invented
  goods (`portfolioOptions`), enumerated in ascending-index order → 6,195 firms/sector,
  232,000 initial routes. Each good has 1,160 suppliers.
- Machinery: Tier 1 C-1/C-2 = `15000 × 5^(complexity−1)` → $15,000/$75,000;
  each Tier 2 route is owned outright by its firm at $1,000 (no shared factory).

---

## 5. Configuration schema (`cfg`)

Authoritative defaults in `defaultCfg()`; normalization invariants in `normalizeConfig()`.
A reimplementation must apply the **same normalization** before use (this is part of
determinism). `N2 = N2_FIRMS`, `NU = N_END_USERS`.

| Key | Default | Normalization / constraint |
| --- | ---: | --- |
| `seed` | `12345` | `floor(v) >>> 0` (u32) |
| `dbar` | `1` | clamp to `[dmin, dmax]` |
| `theta` | `0.15` | clamp `[0,1]` |
| `sigma` | `0.005` | `>= 0` |
| `dmin` / `dmax` | `0.7` / `1.4` | `dmin >= 0.01`; `dmax >= dmin` |
| `capacity` (T0, per firm/tick) | `10000` | `>= 0` |
| `targetInventory` / `maxInventory` (T0) | `500000` / `1000000` | `>= 0`; `maxInventory >= targetInventory` |
| `initialCash` (T0 per firm) | `1000000` | `>= 0` |
| `baseCost` | `1` | `>= 0` |
| `manufacturingCostPerUnit` (T1) | `0.25` | `>= 0` |
| `minWholesaleLot` | `1000` | integer `>= 1` |
| `inventoryCoverageTicks` | `3` | integer `[1,30]` |
| `retailTargetInventory` / `retailMaxInventory` (T1) | `600` / `1200` | `>= 0`; max >= target |
| `retailInitialCash` (T1 per firm) | `5000` | `>= 0` |
| `basicEquipmentCapacity` / `compoundEquipmentCapacity` | `320` / `240` | integer `>= 1` |
| `tier1InventoryCapacity` | `6000` | integer `>= 2 × minWholesaleLot` |
| `k` (price step) | `0.35` | clamp `[0,1]` |
| `wholesalePriceResponse` | `0.05` | clamp `[0.001,1]` |
| `alpha` (EMA) | `0.15` | clamp `[0,1]` |
| `markup` / `compoundMarkupPremium` | `0.25` / `0.15` | `>= 0` |
| `priceObservationTicks` | `30` | integer `[1,360]` |
| `researchPriceMinimumOpportunities` | `0` | clamp `[0,1000]` |
| `researchPriceMinimumPotentialOrders` | `0` | clamp `[0,1000]` |
| `researchPriceMaxObservationTicks` | `3600` | integer `>= 1` |
| `consumerSearchOffers` | `5` | integer `[1,20]` |
| `vmin` / `vmax` (taste) | `0.9` / `1.5` | `vmin >= 0.01`; `vmax >= vmin` |
| `demandQtyMin` / `demandQtyMax` | `1` / `10` | integer `[1,100]`; max >= min |
| `elasticityMin` / `elasticityMax` | `1` / `2` | `[0.05,10]`; max >= min |
| `taumin` / `taumax` (switching) | `0.05` / `0.2` | `>= 0`; max >= min |
| `reliabilityAlpha` | `0.15` | clamp `[0,1]` |
| `switchingStableBand` | `0.025` | `>= 1e-9` |
| `endUserCount` | `NU` | integer `[1, NU]` |
| `t2FirmCount` | `N2` | integer `[1, N2]` |
| `initialDemandForecastScale` | `0` | clamp `[0,100]` |
| `procurementMaterialBalance` / `tier2MaterialBalance` | `Array(NP).fill(0)` | per-element clamp `[-5,5]` |
| `tier2WorkingCashTicks` | `30` | integer `[1,360]` |
| `tier2MinimumCash` | `2500` | `>= 0` |
| `tier2MarkupPremium` | `0.05` | `>= 0` |
| `tier2BaseMarkup` | `-1` | `>= -1` (fallback to `markup`) |
| `procurementBaseMarkup` / `procurementMarkupPremium` | `0.25` / `0.05` | base `>= 1e-6`; premium `>= 0` |
| `procurementBasicReferenceCost` | `1.875` | `>= MIN_UNIT_PRICE` |
| `procurementCompoundReferenceCost` | `3.85` | `>= MIN_UNIT_PRICE` |
| `tier2ConversionCostScale` | `1` | `>= 1e-9` |
| `procurementConversionReferenceScale` | `1` | `>= 1e-9` |
| `tier2CompoundStandardization` / `tier2ComplexitySpecialization` | `0` / `0` | clamp `[0,5]` |
| `procurementCompoundStandardization` / `procurementComplexitySpecialization` | `0` / `0` | clamp `[0,5]` |
| `tier2CompanyCapacity` | `6` | integer `>= 1` |
| `tier2InventoryCapacity` | `60` | integer `>= 5` |
| `consumerActivation` | `0.1` | clamp `[0,1]` |
| `tier2DemandFactor` | `1` | clamp `[0.01,10]` |
| `tier2ReservationPremium` | `0` | `>= 0` |

Population changes (`endUserCount`, `t2FirmCount`) require a full `reset`; they cannot
be applied live. Live parameter changes preserve earned relationships and learned state.

---

## 6. World-state schema (`W`)

`W` is a flat record of typed arrays plus two scalars (`t2LineCount`, and the transient
`sinks` set per tick). Element types: **F64** = Float64, **F32** = Float32, **U8/U16/U32**
= unsigned int8/16/32, **I8/I16/I32** = signed int8/16/32.

Length shorthand: `N0=20`, `NE=4`, `N1=1000`, `NP=10`, `N2=61950`, `NU=1000000`,
`ML=247800` (= `MAX_T2_LINES`), `M4=4` (= `T2_MAX_PRODUCTS_PER_FIRM`).
**"per-tick"** fields are zeroed by `resetTick` at the top of every tick.

### 6.1 Environment and global

| Field | Type | Length | Meaning | Reset |
| --- | --- | ---: | --- | --- |
| `difficulty` | F64 | `NE` | bounded mean-reverting extraction difficulty | — |
| `costSinks` | scalar | 1 | total extraction+conversion cash sinks this tick | per-tick |
| `equipmentSinks` | scalar | 1 | equipment cash sinks during a kernel tick | per-tick |

### 6.2 Tier 0 (index `supplier×NE + element`)

| Field | Type | Length | Meaning | Reset |
| --- | --- | ---: | --- | --- |
| `t0Cash` | F64 | `N0` | supplier cash | — |
| `t0Inv` | F64 | `N0×NE` | element stock | — |
| `t0InvBasis` | F64 | `N0×NE` | weighted-average acquisition basis | — |
| `t0Price` | F64 | `N0×NE` | posted quote | — |
| `t0Cost` | F64 | `N0×NE` | current unit extraction cost | — |
| `t0PrevPrice` | F64 | `N0×NE` | prior posted quote | — |
| `t0Rel` | F64 | `N0×NE` | reliability score | monthly |
| `t0Stability` | F64 | `N0×NE` | last price stability (0–1) | — |
| `t0DemandEMA` | F64 | `N0×NE` | observed-order EMA (replenishment) | — |
| `t0SalesEMA` | F64 | `N0×NE` | realized-sales EMA | — |
| `t0Sold` / `t0Revenue` / `t0COGS` / `t0Demand` | F64 | `N0×NE` | per-tick sales / revenue / COGS / funded demand | per-tick |
| `t0Req` / `t0FundedReq` / `t0Ful` | F64 | `NE` | per-element requests / funded / fulfilled | per-tick |
| `t0Opportunities` | U32 | `NE` | per-element funded-lot opportunities | per-tick |
| `t0RelAttempts` / `t0RelFulfilled` / `t0RelChecks` / `t0RelAvailable` | F64 | `N0×NE` | reliability counters | monthly |
| `t0RelPriceSum` | F64 | `N0×NE` | Σ price stability | monthly |
| `t0RelPriceSamples` | U32 | `N0×NE` | stability sample count | monthly |
| `t0Learn*` (see §6.6) | — | `N0×NE` | derivative-following learner | per-window |

### 6.3 Tier 1 (per `company×NP` product and `company×NE` element)

| Field | Type | Length | Meaning | Reset |
| --- | --- | ---: | --- | --- |
| `t1Cash` | F64 | `N1` | refinery cash | — |
| `t1EqBook` | F64 | `N1` | equipment book value | — |
| `t1Controller` | U8 | `N1` | 1 = player-controlled | — |
| `t1Operates` | U8 | `N1×NP` | installed product line | — |
| `raw` / `rawBasis` | F64 | `N1×NE` | raw-element stock / basis | — |
| `t1Fin` / `t1FinBasis` | F64 | `N1×NP` | finished stock / basis | — |
| `t1Price` / `t1PrevPrice` | F64 | `N1×NP` | posted / prior quote | — |
| `t1PriceStability` | F64 | `N1×NP` | last price stability | — |
| `t1Rel` | F64 | `N1×NP` | reliability | monthly |
| `t1UnitCost` / `t1ReplacementCost` | F64 | `N1×NP` | last unit cost / replacement estimate | — |
| `t1DemandEMA` / `t1SalesEMA` | F64 | `N1×NP` | observed-order / realized-sales EMA | — |
| `t1Sold` / `t1Rev` / `t1COGS` / `t1Demand` | F64 | `N1×NP` | per-tick sales / revenue / COGS / funded demand | per-tick |
| `t1Bought` | F64 | `N1` | per-tick raw units bought | per-tick |
| `t1IntermediateSold` / `t1IntermediateRevenue` | F64 | `NP` | per-market intermediate delivery / revenue | per-tick |
| `t1InputNeed` / `t1PurchaseReq` | F64 | `N1×NE` | per-tick derived need / lot request | per-tick |
| `t1LastBuy` | F64 | `N1×NE` | last paid raw quote | — |
| `preferredWholesale` | I32 | `N1×NE` | earned T0 supplier | — |
| `playerPrice` | F64 | `N1×NP` | player price instruction | — |
| `t1Opportunities` | U32 | `NP` | per-market funded opportunities | per-tick |
| `t1RelAttempts` / `t1RelFulfilled` / `t1RelAvailChecks` / `t1RelAvailable` | F64 | `N1×NP` | reliability counters | monthly |
| `t1RelPriceSum` / `t1RelPriceSamples` | F64 / U32 | `N1×NP` | stability accumulator / count | monthly |
| `t1Learn*` (see §6.6) | — | `N1×NP` | derivative-following learner | per-window |

### 6.4 Tier 2 (sparse line records; firms indexed 0..`N2`−1)

Sparse line arrays have length `ML = N2 × M4`. `t2LineCount` is the active-line count
(scalar). Firm-owning arrays have length `N2`; material stores use `N2×NE` (basics) and
`N2×NP` (all T1 materials).

| Field | Type | Length | Meaning | Reset |
| --- | --- | ---: | --- | --- |
| `t2Cash` / `t2EqBook` | F64 | `N2` | firm cash / equipment book value | — |
| `t2Bought` | F64 | `N2` | per-tick input units bought | per-tick |
| `t2LastSaleTick` | U32 | `N2` | last tick with a sale | — |
| `t2Raw` / `t2RawBasis` | F64 | `N2×NE` | basic-material stock / basis | — |
| `t2T1Raw` / `t2T1Basis` | F64 | `N2×NP` | all-material stock / basis | — |
| `t2Controller` | U8 | `N2` | player-controlled | — |
| `t2Capability` | U8 | `N2` | max installable complexity (5) | — |
| `t2Sector` | U8 | `N2` | home sector | — |
| `t2Online` | U8 | `N2` | player online status | — |
| `t2FirmLines` | I32 | `N2×M4` | line ids per firm slot | — |
| `t2FirmLineCount` | U8 | `N2` | active slots per firm | — |
| `t2Preferred` | I32 | `N2×NP` | earned T1 supplier per material | — |
| `t2LineFirm` / `t2LineProduct` | U16 | `ML` | line → firm / product id | — |
| `t2Fin` / `t2FinBasis` | F64 | `ML` | finished stock / basis | — |
| `t2UnitCost` / `t2ReplacementCost` | F64 | `ML` | last unit cost / replacement estimate | — |
| `t2Price` / `t2PlayerPrice` | F64 | `ML` | posted / player price | — |
| `t2SalesEMA` / `t2DemandEMA` | F64 | `ML` | realized / observed EMA | — |
| `t2Sold` / `t2Revenue` / `t2COGS` / `t2Made` / `t2Demand` | F64 | `ML` | per-tick | per-tick |
| `t2Rel` | F64 | `ML` | reliability | monthly |
| `t2RelAttempts` / `t2RelFulfilled` / `t2RelAvailable` / `t2RelPriceSamples` | U32 | `ML` | reliability counters | monthly |
| `t2RelPriceSum` | F64 | `ML` | Σ stability | monthly |
| `t2MonthSold` / `t2MonthlyCapacity` | F64 | `ML` | monthly accumulators | monthly |
| `t2ReferenceCost` | F64 | 420 | frozen engineering reference cost | reset |
| `t2SectorProducts` | U16 | `10×200` | product ids per sector | reset |
| `t2SectorProductWeight` | F64 | `10×200` | cumulative selection weight | reset |
| `t2SectorCount` | U8 | `10` | active products per sector | reset |
| `t2LineCount` | scalar | 1 | active line count | reset |
| `t2Opportunities` | U32 | 200 | per-market order opportunities | per-tick |
| `t2PotentialOrders` | U32 | 200 | per-market latent orders | per-tick |
| `t2Learn*` (see §6.6) | — | `ML` | derivative-following learner | per-window |

### 6.5 End users (never sent to clients; server-side demand state)

| Field | Type | Length | Meaning |
| --- | --- | ---: | --- |
| `endBasketCount` | U8 | `NU` | 2–5 sectors per consumer |
| `endBasket` | U8 | `NU×5` | sector per basket slot |
| `endNeedProduct` | I16 | `NU×5` | last considered product (T2 id + `NP` offset) |
| `endPreferredProduct` | I16 | `NU×5` | last successful product |
| `endPreferredSupplier` | I32 | `NU×5` | last successful supplier (line id) |
| `endLastMarket` | I16 | `NU` | last chosen market |
| `endLastSupplier` | I32 | `NU` | last contacted supplier |
| `endLastQ` / `endLastFulfilled` | U8 | `NU` | last desired / fulfilled units |
| `endPrimarySector` / `endSecondarySector` | U8 | `NU` | primary / first secondary sector |
| `endQMax` | F32 | `NU` | base quantity |
| `endChoke` | F32 | `NU` | private taste multiplier |
| `endEta` | F32 | `NU` | price elasticity |
| `endPotential` / `endActive` / `endFulfilled` / `endPriceLost` / `endStockUnmet` | F64 | `NP + 200` | per-market demand ledger |

Legacy per-market aggregates `active`, `potential`, `fulfilled`, `priceLost`,
`stockUnmet` (length `NP`) remain in state and are zeroed per tick; the authoritative
demand ledger is the `end*` set.

### 6.6 Derivative-following learner arrays (per tier)

For each tier prefix `t ∈ {t0, t1, t2}` (lengths `N0×NE`, `N1×NP`, `ML`):

| Field | Type | Meaning |
| --- | --- | --- |
| `{t}LearnProfit` | F64 | Σ window gross profit |
| `{t}LearnSales` | F64 | Σ window units sold |
| `{t}LearnTicks` | U32 | window length in ticks |
| `{t}LearnPrevious` | F64 | prior average profit |
| `{t}LearnDemand` | F64 | Σ observed demand (requests) |
| `{t}LearnStock` | F64 | closing stock snapshot |
| `{t}LearnStep` | F64 | experimental scale (0.01–1) |
| `{t}LearnDirection` | I8 | ±1 experimental direction |
| `{t}LearnOpportunity` | F64 | opportunity-weighted traffic (research) |
| `{t}LearnPotentialOpportunity` | F64 | potential-order weighted traffic (research) |

### 6.7 Ephemeral tick result (`state`)

Returned from one tick, also cached for the snapshot:

| Field | Meaning |
| --- | --- |
| `activatedConsumers` | consumers activating this tick |
| `consumerPayments` | total retail cash injected this tick |
| `costSinks` | total extraction + conversion cash destroyed |
| `equipmentSinks` | equipment cash destroyed within the kernel tick |
| `activeOrders` | orders issued this tick |
| `fulfilledOrders` | orders fully delivered this tick |

---

## 7. Canonical tick order

One tick advances the world through **nine** phases, in this exact order. Run, Run Max
and Step all invoke the identical sequence (`advanceSimulationTick`); they differ only
in scheduling/rendering. The concrete phase order in the kernel is:

1. **Reset per-tick scratch** — zero the "per-tick" fields (§6), set `costSinks` and
   `equipmentSinks` to 0.
2. **Environment** — update each element's `difficulty` by the bounded mean-reverting
   process (§8.1).
3. **Tier 0 extraction** (`produceTier0`) — order-up-to replenishment with shared
   capacity/warehouse/cash and proportional apportionment (§8.2).
4. **Tier 1 input purchase** (`planAndBuyInputs`) — derive need from planned output,
   check complete-recipe profitability, buy whole 1,000-unit lots (§8.3).
5. **Tier 1 manufacture** (`manufacture`) — refine raw into finished goods subject to
   inputs, capacity, cash, and the posted-quote gate (§8.4).
6. **Price T0 + T1** (`priceMarkets`) — derivative-following offers with cost
   reservation (§8.5).
7. **Tier 2 purchase / manufacture / price** (`tier2BuyMakePrice`) — buy T1 materials,
   manufacture, price (§8.6).
8. **Clear end users** (`clearEndUsers` = `clearRetail`) — atomic retail orders (§8.7).
9. **Observe, reliability, expand** — update EMAs and learner accumulators
   (`observeMarkets`), monthly reliability (`updateReliability`), monthly bot expansion
   (`expandTier2Bots`), and set the tick-result fields (§8.8).

`tick` (the world tick index) increments by one per phase sequence. The calendar is
`month = floor(tick / 30) % 12 + 1`, `year = floor(tick / 360) % 20 + 1`,
`generation = floor(tick / 7200)`, `age = floor(tick / 172800)`. Ticks, months and
years display in decimal; the Generation displays in hexadecimal with a `0x` prefix;
Age is not explicitly displayed but remains 24 Generations.

---

## 8. Phase rules (machine anchors)

The economic narrative and rationale live in `economy_contract.md`. This section records
only the machine-level anchors a reimplementation must match. **Rotations are part of
determinism** — reproduce the exact modulo/ordering expressions.

### 8.1 Environment (difficulty)

```
difficulty[e] = clamp(difficulty[e] + theta*(dbar - difficulty[e])
                      + sigma*normal(seed, tick, e*4), dmin, dmax)
```

### 8.2 Tier 0 extraction

- `targetPerElement = targetInventory / |elements|`; target via `finishedStockTarget`
  with `bootstrapStock = max(minWholesaleLot, ceil(capacity*0.1/|elements|))`.
- `deficit[e] = max(0, target[e] - t0Inv[e])`; shared capacity and warehouse cap
  (`maxInventory`) apply across all elements of the firm; cash caps each route by
  `floor(cash / cost)`.
- Machine-quantum reservation first, then **proportional apportionment with largest
  fractional remainders**; ties broken by the rotating priority order
  `start = (seed + tick + supplier) % |positive|`. Every produced unit carries its
  extraction cost into `t0InvBasis` by weighted average.
- `t0Cost[e] = max(1e-9, baseCost * difficulty[e])`; initial/fallback
  `t0Price = quantW(cost*(1+markup))`.

### 8.3 Tier 1 input purchase

- Process order interleaves cohorts and firms:
  `firstCohort = tick % NP`, `firstFirm = (tick*37) % 100`.
- Per product: `desired = clamp(target - t1Fin, 0, cap)`; compute replacement cost from
  held basis + selected supplier quotes; if `replacement > t1Price + 1e-9`, skip input
  purchase for that line.
- Raw need per element rounds up to whole `minWholesaleLot` lots; funded and delivered
  quantities round down to whole lots. A supplier with < 1,000 units cannot deliver.
- Supplier choice `tier0Supplier`: ranked by `quote + switchingCost(preferred reliability)`;
  ties broken by capacity-share weighting `1/|elements|` with draw
  `random(seed, tick, buyer + 12000000 + e*1300000)`.
- On purchase: cash and inventory move equal-and-opposite; `t0COGS += bought*t0InvBasis`;
  `preferredWholesale` updates on success.

### 8.4 Tier 1 manufacture

- `made = min(cap, target - t1Fin)`, then reduced by available raw per recipe ratio and
  by `floor(cash / manufacturingCostPerUnit)`.
- If `inputCost + manufacturingCostPerUnit > t1Price + 1e-9`, `made = 0`.
- Finished basis updated by weighted average; raw decremented; conversion cost is a cash
  sink.

### 8.5 Pricing (T0 + T1)

Derivative-following (`adaptivePrice`), anchored to a cost reservation:

```
floor = max(MIN_UNIT_PRICE, unitCost)
G     = Σ window gross profit / observed ticks
available = sold + closing stock
scarce = demand > available + 1e-9
if scarce:            direction = +1
else if sold == 0:    (stock <= 0 → hold) else direction = -1
else if G < prevG:    direction = -direction
scale = clamp(step * (reversed ? 0.5 : 1.2), 0.01, 1)
next  = max(floor, price * exp(direction * clamp(k,0,1) * response * scale))
```

- `k = 0.35`, `response = wholesalePriceResponse = 0.05` for all tiers.
- Repricing occurs when `ages[index] >= priceObservationTicks` **and**
  `(tick + index) % priceObservationTicks == 0`; the window's profit is divided by its
  actual tick count (the first window may be longer).
- T0 reservation = `max(t0Cost, t0InvBasis)`; T1/T2 = `max(finBasis || unitCost,
  replacementCost)`; player price = `max(playerPrice, reservation)`.
- `stability = 1 - min(1, |next-prev| / max(1e-9, prev) / max(1e-9, switchingStableBand))`.

### 8.6 Tier 2 purchase / manufacture / price

- Firm order rotates: `firm = (order + tick*137) % t2FirmCount`; line slots rotate
  `(order + tick) % lineCount`.
- Sorted T1 market offers are built once per tick; a depleted offer is skipped at
  transaction time; ties rotate by rank.
- Per line: capacity share `= tier2CompanyCapacity / lineCount`; stock target bounded by
  `max(1, ceil(tier2InventoryCapacity/2/lineCount))`; desired reduced until the whole
  input bundle fits warehouse room.
- Complete-recipe gate: if `replacement > t2Price + 1e-9`, `desired = 0`; manufacture
  re-checks actual bases + conversion cost against the quote.
- Procurement profile (frozen, independent of live quotes):
  `markup = (procurementBaseMarkup + procurementMarkupPremium*(complexity-3)) * recipeMarginFactor`;
  `quantityFactor = tier2DemandFactor * 0.25 / (referenceCost * markup)`;
  `valuation = 2 * referenceCost * (1+markup) / 1.25`.
- `conversionCost = 0.5 * complexity * tier2ConversionCostScale`.

### 8.7 End-user clearing (atomic retail)

- Activation: `random(seed, tick, buyer + 2000000) < consumerActivation`.
- Slot: `random(seed, tick, buyer + 3000000) < 0.60 ? 0 : 1 + floor(random(seed, tick, buyer + 3100000) * (basketCount-1))`.
- Need persistence: keep previous product with probability 0.65
  (`random(seed, tick, buyer + 5100000) < 0.65`); else select by cumulative sector
  weights (`random(seed, tick, buyer + 6000000)`).
- `latentQuantity = endQMax * quantityFactor`; `qmax = ceil(latentQuantity)`;
  stochastic whole-unit rounding uses `rounding = random(seed, tick, buyer + 7000000)`.
- Demand at quote `P`: `continuous = latent / (1 + (P/choke)^eta)`,
  `desired = min(qmax, floor(continuous) + (rounding < frac(continuous) ? 1 : 0))`;
  `choke = valuation * endChoke * (1 + tier2ReservationPremium*(complexity-1))`.
- Discovery samples `consumerSearchOffers` (=5) offers weighted by
  `1/routeCount`, via `random(seed, tick, buyer + 8000000 + sample*1100000)`, plus the
  previous supplier; candidates ranked by `price + switching friction`; duplicates
  discarded. A stockout advances to the next acceptable stocked offer; otherwise the
  need is `stockUnmet`. Orders are atomic: complete or not at all.
- A sale injects `desired * price` of external cash into the seller's firm; updates
  `t2Sold/Revenue/COGS` and the earned relationship.

### 8.8 Observation, reliability, expansion

- EMAs (end of tick, per producing line): `EMA += alpha * (obs - EMA)`, `alpha = 0.15`.
  Forecast uses `max(demand, sold)`; realized-sales EMA uses `sold`.
- Learner accumulates `profit += revenue - cogs`, `sales += sold`, `ages++`,
  `demand += max(demand, sold)`, `stock = held`.
- Reliability (monthly, `tick % 30 == 0`): score
  `0.5*fulfillment + 0.3*priceStability + 0.2*availability`, then
  `rel = clamp(rel + reliabilityAlpha*(score - rel), 0, 1)`; counters reset.
- Bot expansion (monthly): a non-player firm with `sold/capacity >= 0.75` and cash
  `>= 1.6 × routePrice` adds one distinct eligible line (`product = eligible[(firm+tick) % |eligible|]`).

---

## 9. Runtime interface

The kernel is a **single owner of economic state**. All mutation flows through commands;
all reads flow through projections. Clients never mutate world state directly.

### 9.1 Commands (language-agnostic operations)

| Operation | Effect |
| --- | --- |
| `init(cfg)` | Normalize config, allocate `W`. |
| `reset(cfg)` | Rebuild `W` from config and static catalogue; `tick = 0`; reinitialize Tier 0/1/2/consumers; publish. |
| `run(mode)` | Start the scheduler (`fixed` = 2 ticks/s with 500 ms delay, `max` = time-bounded batch). |
| `pause()` | Stop the scheduler. |
| `step()` | Advance exactly one tick (only when not running). |
| `applyConfig(patch)` | Merge + normalize live parameters (population keys rejected). |
| `select(tier, id)` | Set the selected company (T1 or T2). |
| `companyDetail(tier, id)` | Read-only per-company projection. |
| `watchCompanies({T0,T1})` | Set the expanded-detail watch set. |
| `tier2Query(query)` | Filter/sort/paginate Tier 2 firms (50 rows/page). |
| `player(tier, id, code, price, online, controller)` | Take/release control; set a player price (bounded by reservation). |
| `buyEquipment(tier, id, code)` | Purchase an eligible product line/route (player-controlled only). |

Determinism note: commands are applied **between** ticks (admin actions) or enqueue
player instructions consumed by later ticks; they do not advance the world.

### 9.2 Read projection (`snapshot`)

The projection published each report contains: world metadata, `tick`/`month`/`calendar`,
tier aggregates (`t0`/`t1`/`t2`/`endUsers`), per-element and per-product stats, Tier 2
industry/cohort/complexity summaries, the 50-row Tier 2 page, T0/T1 company summaries,
analytics history (≤240 ticks), and the selected company detail. **Individual consumers
are never transmitted**; firm tables are paginated; charts retain ≤240 samples. The
projection has no authority to mutate state.

### 9.3 Scheduler

- `fixed`: one tick then publish, `setTimeout(..., 500)` → nominal 2 ticks/s, wall-clock
  period = 500 ms + compute.
- `max`: loop ticks within a 45 ms wall budget, then publish and yield.
- `step`: exactly one tick. All modes use the identical kernel; only scheduling differs.

---

## 10. Invariants

Enforced at the machine level; the full list and rationale are in
[`economy_contract.md`](economy_contract.md) §"Economic invariants":

- No inventory, cash, demand quantity, or reliability may be negative.
- Every firm-to-firm transaction transfers equal-and-opposite cash and inventory;
  end-user payments are external injections; extraction/conversion/machinery are external
  sinks. Per-tick total company cash change = retail payments − those sinks.
- `maxInventory` is a firm-wide Tier 0 cap, not per-element; Tier 1/Tier 2 finished
  targets are bounded by their own ceiling expressions.
- A retail order is all-or-nothing; fulfilled ≤ desired.
- Producer quotes carry a variable-cost reservation with a `0.00001` numerical minimum;
  there is no guaranteed margin or ceiling.
- Determinism: same seed + config + command sequence ⇒ same state (§2.3).

Validation gates (language-independent, re-targetable to the new kernel): the test
suites in [`tests/`](../tests/) encode cohort counts, atomic orders, conservation,
machinery rejection, player isolation, monthly expansion, reset determinism, scheduler
equivalence, and full-population 0xE10-tick runs.

---

## 11. Acceptance for the Python kernel

A new implementation satisfies this contract when:

1. **Exact-class equivalence (§2.1)** holds against the JS kernel on identical
   `(seed, cfg, command sequence)`: same RNG streams, same whole-unit/lot quantities,
   same supplier/firm/consumer selections, same line/portfolio structures.
2. **Tolerance-class equivalence (§2.2)** holds: Float64 aggregates agree within
   `1e-9` relative/absolute and never produce a structural divergence.
3. **Economic invariants (§10)** hold, and the economic contract
   ([`economy_contract.md`](economy_contract.md)) — including the calibration targets —
   is satisfied by the new implementation on its own terms (not by matching JS numbers).
4. **Performance gate** (from [`technology_strategy.md`](technology_strategy.md)):
   p99 kernel time ≤ 400 ms and total committed tick normally within 769.23 ms at full
   population, validated on the target Linux host with a 24-hour soak.
5. **Replay** of ≥3,600 full-population ticks plus takeover/equipment/shock scenarios
   reproduces conservation, atomic orders, and constraints within tolerance.

The JS kernel remains the executable **oracle** until (1)–(5) pass; it is then retired.
