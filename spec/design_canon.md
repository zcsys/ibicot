# Design canon — Robotic Space Generation kernel

> **Status:** settled by review. This is the **single source of truth**: it states
> *what must be true* of the economy kernel and the game's entry into it, and now also
> records the settled parameters and the machine contract (§12) so the whole economy is
> specified in one document. Where it conflicts with any implementation, the canon wins.

---

## 1. The anchor

> A **simulated, emergent, fair market** in a **physical-goods supply chain**, run by
> **autonomous agents** and entered by **players on equal footing** — where prices,
> relationships, and firm fates *emerge* rather than being prescribed, and "sound"
> means the emergent outcome is **fair and viable** by a measurable standard.

Every section below is a consequence of, or a requirement for, that sentence.

---

## 2. Core axioms (non-negotiable)

1. **Conservation & accounting.** Money and goods are conserved; only *defined* external
   flows change the system total (consumer spend in; extraction, conversion, capital, and
   dividend-destruction out). Every firm is a double-entry entity: cash + license +
   inventory-at-acquisition-basis + machinery = equity. **Cash and equity are the only
   first-class financial quantities; net profit is derived** (revenue − COGS) and is
   reporting, not a fairness target and not a score.

2. **Decentralized emergence.** Prices, supplier choices, market shares, and firm
   survival emerge from many self-interested local agents with private information and
   bounded sampling. **In no market do buyers and sellers converge on a shared ideal
   price.** No central price solver, no market-average target, no demand oracle, no
   "assign demand to fit capacity." Unmet demand and stranded firms are legitimate
   outcomes.

3. **Agency.** Two actor kinds: **autonomous bots** deciding independently from local
   information only (own orders, stock, cost, profit — no shared optimum), and the
   **player**, an investor who acquires an existing firm and operates it under the
   *identical* rules with no privilege, no preferred customers, no guaranteed margin.

4. **Determinism.** Given (seed, configuration, command sequence) the world reproduces.
   Deterministic within an implementation — *not* required to be bit-identical across
   languages.

5. **Fairness.** See §8. The binding form: **equal opportunity for players who join at
   any time.**

6. **Prices settle on their own equilibrium — never on a bound.** The market dynamics
   (adaptive pricing, bounded sampling, switching friction) must find an *interior*
   price equilibrium: prices must not top out at a ceiling or bottom out at a floor.
   A price pinned at a bound is a misspecification symptom — the cost curve, demand
   curve, or markup is wrong — not a sound steady state.

---

## 3. Fixed topology & identity

- **Four tiers, fixed demarcation:** T0 extraction → T1 refining → T2 manufacturing →
  T3 external consumers. No tier bypass. C-1/C-2 belong exclusively to Tier 1;
  C-3/C-4/C-5 exclusively to Tier 2.
- **Four raw elements:** Water, Earth, Fire, Air.
- **Ten Tier 1 products** (four basic C-1 + six compound C-2) made by **1,000 firms**
  (100 per product cohort).
- **Twenty Tier 0 firms**, including their **element-coverage spectrum** (2 all-element,
  4 three-element, 6 two-element, 8 single-element extractors).
- **200 invented Tier 2 products** across ten sectors — 2 C-3 + 6 C-4 + 12 C-5 per sector
  (the Hamilton apportionment of the 44/116/260 complete pool) — made by **60,000
  single-machine firms** in the reverse 6:3:1 ratio: **C-3 = 36,000** (20 × 1,800),
  **C-4 = 18,000** (60 × 300), **C-5 = 6,000** (120 × 50).
- **1,000,000 Tier 3 consumers** (external procurement agents).
- **The eight single-element extractors are also special-purpose**: the two Water
  extractors produce **machinery**; the two Earth extractors collect **storage-unit
  rent**; the two Fire extractors provide **financing**; the two Air extractors provide
  **advertising**. These four service layers (storage rent, machinery-as-good, credit,
  and visibility) are **deferred for the PoC** — documented, not active (mechanics TBD).
- Tier 0 companies are **significantly larger** than Tier 1 or Tier 2 companies.

---

## 4. Firm-scale model

- **Tier 0 has the most capital of all tiers.** It is the largest by design, despite
  having no "product complexity."
- **Tier 1 machinery is uniform:** every T1 product line's machinery is **$15K**
  (equity structure in §6). Within Tier 1, complexity differs only in *operations* —
  throughput is flat at 500, markup rises (compound premium), demand falls — never in
  capital.
- **Tier 2 machinery rises with complexity:** C-3 = **$75K**, C-4 = **$375K**, C-5 =
  **$420K** (Tier 1 flat at $15K). The size gradient lives in Tier 2; higher complexity ⇒
  larger machinery.
- **Throughput (per machine, per tick):** Tier 1 is flat — C-1 = C-2 = **500**. Tier 2
  falls with complexity — C-3 = **300**, C-4 = **200**, C-5 = **100**. One machine = one
  product line = this capacity; there is no separate "line" concept.
- **Per-line machinery:** each installed product line owns its own **machinery capital**
  and its own **throughput capacity**, both keyed to the product's complexity, and both
  **summed per company**. A firm's size is the sum of its lines. **At start every company
  owns exactly one machine (one line);** additional lines are acquired through expansion.
- **No uniform factory/capacity spec across companies.** There is no shared factory, no
  pooled capacity, and no "every company gets the same $300K / 6 units" constant — each
  company's capital and capacity are its own, derived from its lines.
- **Storage (working standard 20,000):** one firm-level pool shared by raw, finished,
  and machinery. Machinery footprint is fixed — C-1/C-2 = 1,000, C-3 = 3,000,
  C-4 = 4,000, C-5 = 5,000 — leaving goods space `G = 20,000 − machinery` for raw and
  finished.
- **Storage rent (deferred for PoC):** Tier 0 is fully subsidized (no storage or
  machinery costs). Tier 1 and Tier 2 would pay a minuscule per-tick fee per storage
  space, collected by the two Earth extractors.
- **Desired inventory = fill `G`:** the whole allocation is paid for, so empty space is
  pure waste. Companies fill the goods space to the brim (bounded by cash and capacity),
  rather than merely covering demand.
- **Balanced pipeline:** recipes preserve item count (N inputs → N outputs), so the raw
  to finished split within `G` is always **1 : 1** — `finished = raw = G/2`.
- **Cost ladder (count-preserving):** material cost is flat per unit — $1 (T1), $1.25
  (T2). Conversion cost is `$0.25 × max(1, complexity−1)`: C-1/C-2 $0.25, C-3 $0.50,
  C-4 $0.75, C-5 $1.00. Unit cost: $1.25 / $1.25 / $1.75 / $2.00 / $2.25.

---

## 5. Product gradient (demand side)

Higher complexity ⇒ **lower demand volume** and **higher unit markup**.

- **Valuation (choke price):** `V = 2 × unit cost` (cost from §4) — the price at which
  demand halves. No complexity gradient needed; the rising cost lifts `V` automatically.
- **Latent quantity:** `qmax = baseQty × quantityFactor`, with
  `quantityFactor ∝ 1 / (cost × benchmark markup)` — equal benchmark gross-profit
  opportunity per purchase. One global `tier2DemandFactor` scales the overall level.
- **Demand curve:** `q(P) = qmax / (1 + (P/V)^η)`, elasticity `η = 2`.
- **Utilization target:** ~50–70%; the demand scale is calibrated to hit it.
- **First-guess markup curve:** Tier 1 flat 0.25; Tier 2 `0.25 × 5^(c−3)` (C-3 0.25,
  C-4 1.25, C-5 6.25), `tier2DemandFactor = 1`. This makes `quantityFactor` fall ~32× from
  C-3 to C-5; steepen the markup (or weight selection) to reach the ~108× supply match.

The benchmark **markup gradient** is the key calibration lever: it must be steep enough
that demand per product falls to match supply (firms × capacity = 108:12:1 across
C-3/C-4/C-5). The formulas above are canon; the exact demand scale, markup curve, and
elasticity are calibration.

---

## 6. Initial condition: one converged scenario

The "full-on simulation" and the "game start" are the **same thing** — there is no
separate mature stage reached later. The simulation's initial state *is* the game's
starting point: fully populated (all tiers, all complexity levels, all invented markets),
with **every company starting on a single machine** (one product line) — Tier 1 and
Tier 2 alike. Multi-line companies arise only later, through expansion (§7).

This convergence removes the portfolio-width fairness problem from the starting state:
no company begins richer by owning several product lines.

**Starting equity (working values).** Every Tier 1 and Tier 2 company holds a **$1m
license** as an equity asset. Total equity = license + machinery + working cash, with
cash as the residual:

| Entity | License | Machinery | Working cash | Total equity |
| --- | ---: | ---: | ---: | ---: |
| Tier 0 (×20) | — | — (extraction) | $10m | $10m |
| Tier 1 (all 10 types) | $1m | $15k | $485k | $1.5m |
| Tier 2 — C-3 | $1m | $75k | $425k | $1.5m |
| Tier 2 — C-4 | $1m | $375k | $125k | $1.5m |
| Tier 2 — C-5 | $1m | $420k | $80k | $1.5m |

The machinery ladder is $15k (T1 flat) / $75k / $375k / $420k. Every Tier 1 and Tier 2
company starts at $1.5m; only Tier 0 ($10m) is larger.

**Fairness is carried by the rate, not the stake.** Equity (stake) and capital
(machinery) are different things, and the tiers differ in *size* by design. What must be
equal is the **rate of return — ROI, the percentage incrementality the player feels** —
not the absolute equity.

---

## 7. Entry model & expansion

- All firms exist at tick 0.
- A player **starts as a single firm** — Tier 1 or Tier 2 — operating that company's own
  balance sheet (license + machinery + working cash, §6). There is no holding company at
  start.
- **Subscriptions (real money, annual):** Tier 1 is free during alpha, ~$5/year later;
  Tier 2 is $15/year.
- **Two routes to Tier 2:** (a) buy the Tier 2 subscription, or (b) buy the cheaper Tier 1
  subscription and work up in-game — either **apply for the Tier 2 license** ($1m, which
  becomes an equity asset) or **found a holding company** (~$200k) and purchase a Tier 2
  company through it.
- **Expansion (later):** a player may form a **holding company** to acquire and own
  additional firms. This is how multi-machine companies come to exist.
- Bot-run Tier 2 companies pay annual **dividends that are destroyed** (a pure money
  sink), so their equity can grow only ~one year at a time. This bounds each company's
  listing value and keeps the real-money value of an in-game dollar stable (mechanics
  TBD).

---

## 8. Fairness metric

- The fairness target is **sustained equal profitability measured as equity ROI**
  (percentage return on equity), **not** equal net profit and **not** equal absolute
  equity. Companies start at different sizes; the player must feel the **same
  incrementality** (percentage growth rate) whichever company they acquire and at
  whatever stage of the game.
- The ROI distribution must be **tight** (no structural winners or losers) **and stable
  over time** (no systematic drift like the observed T0-accelerates/T1-T2-decelerates
  pattern). The ~2× opening-equity-per-Age multiple is the *derived aggregate check*,
  not the primary metric.
- Net profit is derived reporting; cash and equity are the only first-class financials.
  There is no score.

---

## 9. Canon vs. calibration

Everything in §2–§8 is **canon** (design law). The following are **calibration**
(numbers to be determined, not design):

- the supply side is pinned as working values — uniform $1.5m equity (license `$1m` +
  machinery + residual cash), machinery $15k/$75k/$375k/$420k, capacity 500/500/300/200/100,
  conversion `$0.25 × max(1,c−1)`, count-preserving recipes, storage 20,000 — final values
  from calibration;
- the demand-volume and markup/valuation curves by complexity (the demand side);
- all prices, activation rates, and offer-sampling counts.

No parameter is frozen until calibration adopts it.

---

## 10. Deferred / reserved directions

Tracked, explicitly **not** canon yet:

- **Buy-storage mechanic** — expanding a company's warehouse capacity *beyond* the 20k
  standard by purchase (a possible future capital lever; the base 20k is rented, not owned).
- **Spatial presentation** — a possible isometric 2D hex-grid map. This is a
  presentation/UX layer, decoupled from the economic model.
- **T1 vs. T2 steady-state size divergence** — game-start sizes are fixed (§6); their
  later divergence is emergent, not prescribed.

---

## 11. Acceptance for a reimplementation

A new kernel satisfies this canon when it implements §2–§8, holds the invariants in §10
(no negative inventory/cash/demand/reliability; conservation; atomic orders), and reaches
the fairness target in §8 under its own determinism, at the performance and replay gates
of §12.

---

## 12. Settled parameters & machine contract

The machine-level specifics, consolidated here so the whole economy is specified in one
place. Everything in §2–§8 is **canon**; the supply-side numbers below are pinned **working
values**; the demand-side *scale* is **calibration** (not frozen).

### 12.1 Topology (canon, fixed)

| Quantity | Value |
| --- | --- |
| Tiers | 4 — T0 extraction → T1 refining → T2 manufacturing → T3 consumers (no bypass) |
| Elements | 4 — Water, Earth, Fire, Air |
| T0 firms | 20 — 2 all-element, 4 three-element, 6 two-element, 8 single-element |
| T1 products | 10 — 4 basic C-1 + 6 compound C-2 |
| T1 firms | 1,000 — 100 per product cohort |
| T2 products | 200 invented — 2 C-3 + 6 C-4 + 12 C-5 per sector × 10 sectors |
| T2 firms | **60,000 single-machine firms** (reverse 6:3:1 ratio) |
| T2 firms per product | C-3 = **1,800**, C-4 = **300**, C-5 = **50** |
| Consumers | 1,000,000 |

### 12.2 Scale (working values)

| Entity | License | Machinery | Working cash | Total equity |
| --- | ---: | ---: | ---: | ---: |
| Tier 0 (×20) | — | — (extraction) | $10m | $10m |
| Tier 1 (all types) | $1m | $15k | $485k | $1.5m |
| Tier 2 C-3 | $1m | $75k | $425k | $1.5m |
| Tier 2 C-4 | $1m | $375k | $125k | $1.5m |
| Tier 2 C-5 | $1m | $420k | $80k | $1.5m |

- Machinery ladder: T1 flat **$15k**; T2 **$75k / $375k / $420k**.
- Capacity (per machine, per tick): C-1/C-2 **500**, C-3 **300**, C-4 **200**, C-5 **100**.
  One machine = one product line = this capacity.
- Count-preserving recipes: **N inputs → N outputs**.
- Cost ladder: material flat **$1 (T1) / $1.25 (T2)** per item; conversion
  **$0.25 × max(1, complexity−1)** → C-1/C-2 $0.25, C-3 $0.50, C-4 $0.75, C-5 $1.00.
  Unit cost: **$1.25 / $1.25 / $1.75 / $2.00 / $2.25**.
- Storage: **20,000** firm-level pool (raw + finished + machinery). Machinery footprint
  C-1/C-2 **1,000**, C-3 **3,000**, C-4 **4,000**, C-5 **5,000**; goods space
  `G = 20,000 − machinery`. Desired inventory = **fill G**, split **1:1**
  (`finished = raw = G/2`).

### 12.3 Demand (structure canon, scale calibration)

- Valuation: `V = 2 × unit cost` (cost from §12.2).
- Latent quantity: `qmax = baseQty × quantityFactor`, `quantityFactor ∝ 1/(cost × markup)`.
- Demand curve: `q(P) = qmax / (1 + (P/V)^η)`, `η = 2`.
- First-guess markup: T1 flat **0.25**; T2 **`0.25 × 5^(c−3)`** = 0.25 / 1.25 / 6.25;
  `tier2DemandFactor = 1`.
- Utilization target ~50–70% (the demand scale is calibrated to hit it).

### 12.4 Determinism, RNG, tick, runtime

- **RNG**: 32-bit SplitMix32. `mix(u)`, `random(seed, tick, stream) = mix(seed ⊕ (tick+1)·0x9e3779b1 ⊕ (stream+1)·0x85ebca6b) / 2^32`,
  `normal(·)` (Box-Muller), `hashSeed(seed, k) = mix(seed ⊕ (k+1)·0x9e3779b1)` (u32).
- **Determinism**: same `(seed, config, command sequence)` ⇒ identical state. All iteration
  rotations (`tick*37`, `tick*137`, `(tick+index)%N`, seed draws) are part of state.
- **9-phase tick** (per tick): reset scratch → environment (difficulty mean-reversion) →
  T0 extraction (order-up-to + proportional apportionment) → T1 input purchase
  (whole-lot) → T1 manufacture → pricing (derivative-following) → T2 buy/make/price →
  end-user clearing (atomic orders) → observe/reliability (monthly).
- **Calendar**: 30 ticks/month, 12 months/year, 20 years/generation, 24 generations/age.
- **Commands** (FastAPI/WebSocket): `init`, `reset`, `run`, `pause`, `step`,
  `applyConfig`, `select`, `companyDetail`, `watchCompanies`, `player`,
  `buyEquipment`, `tier2Query`, `buyLicense`, `foundHouse`. Reads are projections;
  per-consumer state is never sent to clients.

### 12.5 Deferred / calibration

- **Deferred (not implemented)**: storage rent, machinery-as-good, financing, advertising.
- **Calibration (not frozen)**: the demand scale (`tier2DemandFactor` and the `∝`
  constant), the markup curve, `baseQty` range, and offer-sampling counts.

### 12.6 Pricing (per tick, derivative-following)

All three producer tiers price their output each tick with one **derivative-following
adaptive pricer**, plus a player/admin override. There is a hard **floor** (unit cost)
and **no ceiling** — per axiom 6, a healthy price settles at an interior equilibrium,
never pinned to a bound (`MIN_UNIT_PRICE = 1e-5` is only a numerical guardrail).

**Initial price (tick 0)** — the first-guess markup from §5:
`P₀ = unitCost × (1 + markup)`, with markup = `markup` (T0), `t1Markup` (T1),
`t2MarkupBase × t2MarkupExponent^(c−3)` (T2).

**Observation cadence.** A price is re-evaluated only when
`(tick + index) % priceObservationTicks == 0` and it has been observed at least once
(`priceObservationTicks = 30`). On all other ticks the price is simply held at
`max(floor, price)`.

**Decision (at a cadence tick), from the average realized profit/tick accumulated since
the last observation:**
1. **Scarce** — demand exceeded sales + stock → raise price.
2. **No sales, stock remains** → lower price.
3. **Profit fell** vs the previous observation → reverse direction.
4. Otherwise → continue the current direction.

**Step size** adapts: ×1.2 on continuation, ×0.5 on reversal, clamped to `[0.01, 1]`.
The price moves multiplicatively: `P ← max(floor, P × exp(± k × response × scale))`.
After each observation the profit/sales/demand/opportunity accumulators and the age
counter reset.

**Per-tier floor (unit cost):**
- T0 — `max(extraction cost = baseCost × difficulty, inventory basis)`.
- T1 — `max(MIN_UNIT_PRICE, finished-goods basis | unit cost, replacement cost)`.
- T2 — same as T1.

**Player/admin override.** A player-controlled firm quotes `max(playerPrice, floor)` and
its adaptive state is reset, so the set price takes effect on the next tick. This is
uniform across T0, T1 and T2.

**Parameters.** `k` (0.35, aggressiveness), `wholesalePriceResponse` (0.05, base step
fraction), `priceObservationTicks` (30, cadence), `researchPriceMinimumOpportunities`
(0, minimum traffic before repricing; 0 = repriced at cadence). `switchingStableBand`
(0.025) drives the price-stability *metric*, not the price itself.
