# Design canon — Star Business kernel

> **Status:** settled by review. This is the **single source of truth**: it states
> *what must be true* of the economy kernel and the game's entry into it, and records
> the machine contract (§12) so the whole economy is specified in one document.
> Where it conflicts with any implementation, the canon wins.

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
   flows change the system total (distributor spend in; extraction, conversion, capital, and
   dividend-destruction out). Every firm is a double-entry entity: cash + license +
   inventory-at-acquisition-basis + machinery − liabilities = equity. Gross profit is
   sales revenue minus COGS. **Net earnings are independently totaled from income and
   expense postings**, including switching receipts/expenses and storage expense.
   With no owner contributions, distributions, or other direct-to-equity entries,
   those earnings must equal the change in book equity. Reconciliation verifies the
   books; it must never set earnings from the equity change or hide a residual.
   Capitalized inventory and machinery purchases exchange assets rather than create
   an immediate expense. These financial quantities are not a separate game score.

2. **Decentralized emergence.** Prices, supplier choices, market shares, and firm
   survival emerge from many self-interested local agents with private information and
   bounded sampling. **In no market do buyers and sellers coordinate on — or jointly
   steer toward — a common target price.** Equilibrium is not an input: no central price
   solver, no shared ideal price the parties converge on by design, no demand oracle, no
   "assign demand to fit capacity." A single firm may observe the *realized* going rate of
   its own market (a sales-weighted average of competitors' actual prices, §12.2) and
   position *itself* relative to it — individual competitive behavior on local information,
   not a shared target; the equilibrium still emerges from independent choices, never from
   a goal held in common. Unmet demand and stranded firms are legitimate outcomes.

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
   (adaptive pricing, bounded sampling, loyalty charge) must find an *interior*
   price equilibrium: prices must not top out at a ceiling or bottom out at a floor.
   A price pinned at a bound is a misspecification symptom — the cost curve, demand
   curve, or markup is wrong — not a sound steady state. A floor and a ceiling may be
   defined as **numerical guardrails** (`MIN_UNIT_PRICE`/`MAX_UNIT_PRICE`, see §12.2),
   but they are degenerate-value protection only; a healthy simulation never settles
   there.

---

## 3. Fixed topology & identity

- **Four tiers, fixed demarcation:** T0 extraction → T1 refining → T2 manufacturing →
  T3 external distributors. No tier bypass. C-1/C-2 belong exclusively to Tier 1;
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
- **1,000,000 Tier 3 distributors** (resident distributors).
- **The six two-element extractors are special-purpose**: Mudrock Machinery Co.
  (machinery), Steam Ridge Financial Inc. (financial services), Dustline Spatial Solutions
  Corp. (warehouses, land, and industrial space — the Storage Concession Fee), Flare
  Basin Advertising Incorporated (advertising), Cloudline Games & Entertainment
  Corporation (games and entertainment), and Hotrock Utility Company (utilities). The
  single-element extractors are pure extractors. These service layers are **deferred for
  the PoC** — documented, not active (mechanics TBD), except the machinery maker, which
  is active in the Machinery Market.
- Tier 0 companies are **significantly larger** than Tier 1 or Tier 2 companies.

---

## 4. Firm-scale model

- **Tier 0 has the most capital of all tiers.** It is the largest by design, despite
  having no "product complexity."
- **Tier 1 machinery is uniform:** every T1 product line's machinery is **$15K**
  (equity structure in §6). Within Tier 1, complexity differs only in the *recipe* —
  throughput is flat at **2,000** and markup is flat (**0.25**) — never in capital,
  throughput, or markup.
- **Tier 2 machinery rises with complexity:** C-3 = **$75K**, C-4 = **$375K**, C-5 =
  **$420K** (Tier 1 flat at $15K). The size gradient lives in Tier 2; higher complexity ⇒
  larger machinery.
- **Throughput (per machine, per tick):** Tier 0 extraction is **200,000** per firm per tick
  (extraction, not a machine line). Tier 1 is flat — C-1 = C-2 = **2,000**. Tier 2 falls with
  complexity — C-3 = **30**, C-4 = **20**, C-5 = **10**. One machine = one product line =
  this capacity; there is no separate "line" concept.
- **Tier 0 extraction cost & lot:** raw costs **`$1 × difficulty`** (`baseCost`; difficulty
  mean-reverts to `difficultyTarget = 1`), sold in whole lots of **1,000** minimum.
  Extraction is **profit-gated like T1/T2 manufacture**: no extraction while
  `cost > price` (hard gate), tapering to zero as the extraction margin
  `(price − cost)/price` falls below 5 % (`productionMarginBand`).
- **Tier 0 extraction quantity:** per element, `made = min(deficit, capacity, headroom,
  ⌊cash ÷ cost⌋)`, where `deficit = target − inventory` (the element's even share of the
  fill-to-brim 500,000 pool) and `headroom = storage − total inventory` (free space). When
  the firm's capacity or cash cannot cover every element's deficit, the budget is
  **apportioned across elements proportionally to their deficits**, so no single element
  starves the others.
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
  finished. **Tier 0 storage is a separate, fully-subsidized raw pool of 500,000 per firm**
  (no machinery footprint; extraction equipment is an equity asset, not a storage cost).
- **Storage Royalty (deferred for PoC):** Tier 0 is fully subsidized (no storage or
  machinery costs). Tier 1 and Tier 2 would pay a minuscule per-tick fee per storage
  space, collected by the two Earth houses.
- **Desired inventory = fill `G`:** the whole allocation is paid for, so empty space is
  pure waste. Companies fill the goods space to the brim (bounded by cash and capacity),
  rather than merely covering demand.
- **Manufacture quantity (T1/T2):** `desired = min(capacity, G / (2 × installed_lines) − finished)`, rounded down to
  whole batches (`⌊desired ÷ output_qty⌋`), then capped by (a) the raw/materials on hand
  (`⌊stock ÷ recipe ratio⌋` per input) and (b) cash for conversion
  (`⌊cash ÷ (conversion × output_qty)⌋`). The economic gates (margin ramp, break-even) are
  in §12.2.
- **Balanced pipeline:** recipes preserve item count (N inputs → N outputs), so the raw
  to finished allocation within `G` is **1 : 1**. Each distinct input gets
  `G / (2 × distinct_inputs)` and each installed output line gets
  `G / (2 × installed_lines)`. Shared inputs get one company-wide slot. Purchases
  refill their own slots independently of production margin, output deficits, or
  current demand, subject to cash, supply, switching fees, and total storage. T1
  rounds down to whole wholesale lots; T2 rounds down to whole units. Existing
  over-slot stock is retained and blocks further purchases of that input until
  consumed. Changes to equipment rebalance allocations without deleting stock.
- **Cost ladder (count-preserving):** material cost is flat per unit — $1.25 (T1), $1.875
  (T2). Each tier's material cost already includes the upstream tier's 0.25 markup, so the
  realized markup is a true 25 % at every tier. Conversion cost is
  `$0.25 × max(1, complexity−1)`: C-1/C-2 $0.25, C-3 $0.50, C-4 $0.75, C-5 $1.00.
  Unit cost: $1.50 / $1.50 / $2.375 / $2.625 / $2.875.

### Per-tick storage rent

The UI rate is **$2.80 per 1,000 allocated storage units per tick**. An eligible
company with 20,000 storage pays $56/tick, equivalent to $20,160 over 360 ticks.
The whole allocation is charged, including machinery and empty space; occupancy
and product complexity do not change the rate. T0 remains subsidized and exempt.

For each T1/T2 company, after trading and before billing:

1. Compute book equity = cash + license + machinery book value + raw and finished
   inventory at cost − existing rent arrears.
2. If equity is below $2,000,000, set this tick's charge and collection to zero.
   At exactly $2,000,000 the company is eligible. Eligibility is rechecked every
   tick; a charge can take an eligible company below the threshold.
3. For eligible companies, add `storage / 1000 * rate` to arrears, then collect
   up to available nonnegative cash. The unpaid remainder stays a liability.

Tick zero is not billed. Exemption freezes existing arrears rather than forgiving
or collecting them. Eligible companies still repay old arrears when the new-rent
rate is zero. Payments leave the economy through `costSinks`; rent never enters
inventory cost basis or COGS. There is no interest, eviction or automatic bankruptcy.
Rate and exemption changes apply to future ticks only; no retroactive rebilling or refunds occur.
On 2026-10-11, the user raised the active exemption from $1.5M to $2M.
The earlier 24-generation growth target is not enforced by this fixed policy.

**Reporting.** `t1RentCharge`/`t2RentCharge` store actual current-tick expenses;
`RentPaid` is cumulative cash paid and `RentArrears` is the unpaid balance. Snapshot
`storageRentExpense` is expense, while `storageRentPayment` includes cash collected
against older debt. Net profit = gross profit + switching income − switching
expense − current storage expense; net margin = net profit / sales revenue,
undefined when revenue is zero. Use the recorded expense, not an
eligibility check against post-bill equity, to avoid reversing the crossing tick's
charge in the UI. Each company's expense is split over its own installed lines.
Product sectors group those lines; company cohorts group home sectors. Zero-line
companies retain expense in company/cohort/tier totals without inventing a product.

**Configuration and checkpoints.** The UI converts the per-1,000-per-tick rate to
the legacy persisted `storageRentPerUnitYear` key: `rate * 360 / 1000` (default
1.008), and converts back for display. Settlement divides this legacy annual rate
by 360 once per tick; there is no annual payment cycle. Checkpoints preserve rates,
paid totals, arrears and current charges. Pre-rent checkpoints without a rate load
with zero rent. Older checkpoints missing only current-charge arrays initialize
them to zero; the next tick records the new charge normally. Version 4 also
preserves per-company switching income/expense and net-transfer forecast EMAs.
Version 5 restores gross-profit price learning. Loading a pre-v5 checkpoint clears
its learning windows to avoid mixing objectives. Pre-v4 checkpoints also mark
current net earnings unavailable until the next complete tick. Historical
switching postings cannot be reconstructed from equity; no such plug is used.

**Performance.** Billing uses NumPy masks, row reductions and `bincount`, without
Python loops over companies. T2 inventory work is limited to active firms and
installed lines. Both Python and Numba trading paths call the same settlement.
`project_storage_rent` in `economy/server/aggregates.py` groups charges with NumPy
reductions; catalog complexity/sector labels are cached at module load. Each
snapshot computes these groups once, then attaches scalars to the small display
row collections. The browser formats supplied expenses and ratios for rendered
rows; it does not scan all 60,000 companies to determine exemptions. Legacy
snapshots have a rate-based fallback and cannot reconstruct missing charge history.

Validation covers threshold equality/crossing, inventory valuation, frozen debt,
zero rates, both engines' cash conservation, checkpoint loading, zero-revenue
margins, repeated rendering, and differential multi-line/group allocations.
The full-population benchmark in `tools/performance.py` checks world arrays,
ledgers, statistics and snapshot fingerprints as well as timings. Use identical
seed/configuration and tick counts when comparing results; exclude JIT warm-up. The
2026-10-10 full-population 30-tick comparison matched all behavior fingerprints.
An interleaved 100-sample allocation check (after 10 warm-ups) measured median
1.132 ms before and 1.045 ms after (~8% reduction); this is the allocation stage,
not an overall tick-speed claim. Local evidence: `stats/storage-performance-before.json`,
`stats/storage-performance-after.json`, `stats/storage-allocation-performance.json`.
These files are run artifacts, not portable timing guarantees.

---

### Pending smart-rent reserve proposal (updated 2026-10-11)

**Not active: the content tariffs and revised settlement await the requested final
user green light.** The user selected a **$2,000,000 equity threshold** for
all T1/T2 companies: $1,500,000 starting capital plus **$500,000 retained earnings**.
This supersedes the earlier $1,560,000 proposal. The active flat-rent exemption
uses the new threshold; the surplus cap below remains a separate pending proposal.
The user also selected **$2.80 per 1,000 empty storage units per tick** for the
future content tariff. Other item rates still need calibration.
T0 remains subsidized. Published tariffs remain universal by stored substance
complexity and machinery class; the exemption does not introduce company-specific
prices.

The proposed assessed expense is
`min(nominal_content_tariff_bill, max(precharge_book_equity - 2_000_000, 0))`.
A company at or below the threshold incurs no new charge; a company just above it
pays only from its equity surplus. This replaces the existing full-bill cliff so
that rent itself cannot consume the protected reserve. Exempt amounts never become
deferred debt. Actual operating losses can still consume the reserve. Collection
of existing arrears remains suspended below the threshold; paying a liability
reduces cash and the liability equally, with no second expense or equity loss.

**Rent-free evidence.** An isolated replay used the old run's seed 137 and full
configuration for 7,203 ticks, covering all 1,000 T1 and 60,000 T2 companies. It
exactly reproduced all **155 saved world arrays** at the old checkpoint. Research
instrumentation posted switching income/expense beside each transfer; net earnings
were sales revenue minus COGS plus switching receipts minus switching expense.
No earnings were obtained by subtracting equity endpoints. Those independently
posted earnings reconciled to assets less liabilities every tick, with a maximum
per-company full-run residual of **$0.002196** from floating-point arithmetic.

| Complexity | Largest cumulative earnings drawdown | Longest consecutive losing streak | Longest spell below a previous earnings peak |
|---|---:|---:|---:|
| C-1 | $138.22 | 1 ticks | 65 ticks |
| C-2 | $193.78 | 1 ticks | 73 ticks |
| C-3 | $13.57 | 1 ticks | 46 ticks |
| C-4 | $6.84 | 2 ticks | 118 ticks |
| C-5 | $2.59 | 2 ticks | 127 ticks |

Drawdown includes all intervening gains and losses before recovery; it is not
cash tied up in purchased inventory or equipment. The longest recovery spells
above all completed within the replay; maxima in different columns need not refer
to the same company or episode. No firm fell below starting book equity or had
negative earnings over a rolling 360-tick year (using $0.000001 noise tolerance).
The $500,000 buffer is about 2,580 times the largest observed drawdown. This buffer
is the user's policy choice, not a statistical guarantee for other seeds or the
24-generation target. Neither duration nor average daily cost is multiplied into
the drawdown again: it already measures the accumulated loss.

Evidence and reproducible scripts are in `stats/smart-rent-proposal/`:
`audit_no_rent.py`, `no-rent-audit/results.json`, `no-rent-audit/per-company.npz`,
`summarize_risk.py`, `finalize_reserve.py`, `reserve-proposal.json`, and
`proposal.json`. Run `audit_no_rent.py`, then `finalize_reserve.py` to incorporate
the completed evidence into the proposal. These tools operate on isolated worlds
and proposal files; they do not reset or reconfigure the live server. The audit
uses the accelerated kernel with additional transaction-site ledger postings;
company risk statistics use NumPy reductions and masks, not Python company loops.

**The previous tariff table is withdrawn.** It combined arbitrary empty/material
rates with machinery tariffs fitted to a 360-tick mature continuation. That does
not establish equal long-term earnings. The obsolete table is preserved only in
`stats/smart-rent-proposal/withdrawn-360-tick-rates.json`;
`proposed-rates.json` now explicitly marks the withdrawal. The user-selected
$2,000,000 equity threshold supersedes its earlier $1,560,000 assumption.

The proper starting evidence is independently posted company earnings over the
entire rent-free run. The target is $1,500,000 / (24 × 7,200) = $8.680556 per tick.

| Complexity | Mean full-run earnings per company | Mean earnings per company per tick | Static charge budget per company per tick |
|---|---:|---:|---:|
| C-1 | $40,199,000.09 | $5,580.87 | $5,572.19 |
| C-2 | $21,678,455.45 | $3,009.64 | $3,000.96 |
| C-3 | $906,755.71 | $125.89 | $117.21 |
| C-4 | $900,295.66 | $124.99 | $116.31 |
| C-5 | $606,537.49 | $84.21 | $75.53 |

The budget column is observed mean earnings minus the target. It assumes
unchanged earnings and an always-assessable charge, so it is **not an item rate
card or a prediction after the exemption**. It includes switching income and
expense. Source: `stats/smart-rent-proposal/full-run-earnings-baseline.json` and
`rebuild_earnings_baseline.py`. Earnings are not stationary: C-1 averaged
$1,045.28/tick in its first 360 ticks and $9,383.46 in its last complete year;
C-3 rose from $24.16 to a yearly peak of $205.91, then ended near $99.42.

Item-rate calibration must use accumulated **storage-unit-ticks** in disjoint
empty, machinery and material bins for each company across the full run, not
final stock quantities. `capture_no_rent_exposure.py` produces that evidence in
`full-run-exposure/`, checks it against the original checkpoint and audited P&L,
and operates on an isolated world. Universal rates, ordering constraints and the
fit objective must be explicit; a short-window fit or arbitrary allocation among
categories is not evidence of long-term equality. The $2M exemption, actual
collection, changes in inventory/prices and out-of-period results must then be
tested separately before approving a rate card.

The completed exposure replay exactly matches all 155 original world arrays and
the earlier independent earnings audit. Whole-run mean finished stock per company
was **2,073.73 / 5,071.56 / 1,393.64 / 193.29 / 88.49 units** for C-1 through C-5.
The endpoint quantities are not interchangeable with these exposure averages.

`full-run-fit-diagnostics.json` tests the eight shared rates for empty space,
common machinery and C-0 through C-5 substances. On the recorded trajectory,
requiring `empty <= machinery <= C0 <= C1 <= ... <= C5` cannot satisfy all five
class-average charge budgets. Even allowing any nonnegative rates, while keeping
machinery no dearer than substances, the five class means do not uniquely identify
eight tariffs. An explicit company-dispersion objective can select a historical
fit, but that fit is not itself a policy validation.

The exemption is material: an unconstrained-by-reserve historical fit can match
every class mean by offsetting winners against large negative company earnings.
The reserve prevents those rent-induced losses. `full-run-cap-diagnostic.json`
rejects this shortcut; even a lower-bound reserve adjustment on unchanged source
trajectories pushes C-1 mean earnings to $826.76/tick, far above the $8.68 target.
That is a diagnostic bound under unchanged behavior, not a simulated outcome.

`fit_long_horizon_projection.py` also solves an explicitly limited analytical
model: every company repeats its observed full-run mean income and occupancy for
172,800 ticks, with the $1.56M threshold and surplus cap applied each tick. Its
closed-form settlement was checked against a literal per-tick loop. The model
can match group means, but one feasible fit leaves 397/400 C-1 and 594/600 C-2
companies at only $60,000 accumulated earnings while rare outliers determine the
mean. This is not a simulation of future market behavior, nor evidence of similar
company growth. Results in `long-horizon-projection.json` are a diagnostic seed,
not an approved tariff. No claim of global dispersion optimality is made for its
local constrained optimizer. Those historical diagnostics used the superseded
$1.56M threshold; they have not been rerun for the $2M exemption or the selected
$2.80 empty-space rate and do not validate those new settings.

After approval, implement native per-tick tariffs, complete posted net earnings
and net margins, vectorized settlement, and isolated generation-scale validation
before any new live smart-rent run. The active flat-rent behavior above already
uses the $2M exemption; content tariffs and the surplus cap await activation.

## 5. Product gradient (demand side)

Higher complexity ⇒ **lower demand volume**; the unit markup starts flat and is
discovered by the derivative-following pricer.

- **Valuation (choke price):** `V = unit cost × (1 + t2ReservationPremium × (complexity − 1))`
  (cost from §4) — the price at which demand halves. Each distributor's choke is
  `V × [1.8, 3]` (a per-distributor draw), so the choke is a band, not a point.
  `t2ReservationPremium = 0.25` gives more complex goods a higher reservation value
  (C-3 ×1.5, C-4 ×1.72, C-5 ×2.0), so they clear at higher prices.
- **Latent quantity:** `qmax = 20` (fixed per distributor, `DISTRIBUTOR_QMAX`). The
  per-distributor request therefore stays small (whole units), never exceeding a firm's
  fill-G stock.
- **One product per distributor, supply-scaled:** each distributor is assigned exactly one
  product (`distributorProduct`) for its lifetime, drawn weighted by supply — `firms ×
  capacity` (the **108 : 12 : 1** ratio across C-3 / C-4 / C-5), so higher-supply
  products attract more distributors (~**36,000 / 4,000 / 333** per product). No renewals,
  no sector routing. The per-distributor quantity stays small.
- **Activation:** each tick only a fraction `distributorActivation = 0.2` of the 1,000,000
  distributors activate (a fresh random draw per buyer per tick), so ~200,000 buy per tick —
  matching the supply scale and keeping service fair (no buyer is permanently starved).
- **Demand curve:** `q(P) = qmax / (1 + (P/V)^η)`, elasticity `η = 2`.
- **First-guess markup is flat** (`t1Markup = 0.25` for T0/T1/T2): the complexity
  gradient lives in demand volume/routing *and* the reservation valuation
  (`t2ReservationPremium`), not the seed price.
- **Equilibrium markup** is set by the fixed demand level (`qmax = 20`) — a larger
  quantity is a tighter market ⇒ a higher discovered markup.

The flat first-guess markup is canon. Each distributor samples offers — currently **5**
(`distributorSearchOffers`); the sampling count is calibration, not frozen. Purchase is
**marginal-value** (§12.2): the distributor walks its sampled sellers in total-cost order and
buys `want = q_at − bought` whole units at each, so the quantity is pinned to the marginal
seller's price.

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
| Tier 0 (×20) | $22m | $12.25m × systems (≤4) | $3m–$39.75m (+$1m reserve) | $75m |
| Tier 1 (all 10 types) | $1m | $15k | $485k | $1.5m |
| Tier 2 — C-3 | $1m | $75k | $425k | $1.5m |
| Tier 2 — C-4 | $1m | $375k | $125k | $1.5m |
| Tier 2 — C-5 | $1m | $420k | $80k | $1.5m |

The machinery ladder is $15k (T1 flat) / $75k / $375k / $420k. Every Tier 1 and Tier 2
company starts at $1.5m; only Tier 0 ($75m) is larger.

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
- Net earnings are reported from income and expense postings and independently
  reconciled to equity as specified in §2. There is no separate score. The
  dashboard includes posted switching income and expense in net profit (§4).

---

## 9. Canon vs. calibration

Everything in §2–§8 is **canon** (design law). The **supply-side numbers** in §4 and §6
(equity, machinery, capacity, storage, conversion) are pinned **working values**; the
**demand-side scale** (offer-sampling counts, valuation curves) and **all prices** are
**calibration** (not frozen) until calibration adopts them.

---

## 10. Deferred / reserved directions

Tracked, explicitly **not** canon yet:

- **Buy-storage mechanic** — expanding a company's warehouse capacity *beyond* the 20k
  standard by purchase (a possible future capital lever; the base 20k is rented, not owned).
- **Spatial presentation** — a possible isometric 2D hex-grid map. This is a
  presentation/UX layer, decoupled from the economic model.
- **T1 vs. T2 steady-state size divergence** — game-start sizes are fixed (§6); their
  later divergence is emergent, not prescribed.
- **New product invention** — the dynamic introduction of new T2 products over time
  (innovation). The PoC uses a fixed 200-product catalog; how new products enter the
  market — and what happens to the supply-scaled distributor assignment, firm lines, and
  supply when one appears — is deferred, mechanics TBD.

---

## 11. Acceptance for a reimplementation

A new kernel satisfies this canon when it implements §2–§8, holds the machine invariants
(no negative inventory/cash/demand/reliability; conservation per §2; atomic orders per
§12.1), and reaches the fairness target in §8 under its own determinism, at the
performance and replay gates of §12.

---

## 12. Machine contract

The machine-level specifics — determinism/RNG/tick/runtime and the derivative-following
pricing algorithm. Topology, scale, demand and the deferred/calibration lists are canon
in §3–§10 above and are not repeated here.

### 12.1 Determinism, RNG, tick, runtime

- **RNG**: 32-bit SplitMix32. `mix(u)`, `random(seed, tick, stream) = mix(seed ⊕ (tick+1)·0x9e3779b1 ⊕ (stream+1)·0x85ebca6b) / 2^32`,
  `normal(·)` (Box-Muller), `hashSeed(seed, k) = mix(seed ⊕ (k+1)·0x9e3779b1)` (u32).
- **Determinism**: same `(seed, config, command sequence)` ⇒ identical state. All iteration
  rotations (`tick*37`, `tick*137`, `(tick+index)%N`, seed draws) are part of state.
- **9-phase tick** (per tick): reset scratch → environment (difficulty mean-reversion) →
  T0 extraction (order-up-to + proportional apportionment) → T1 input purchase
  (whole-lot) → T1 manufacture → pricing (derivative-following) → T2 buy/make/price →
  distributor clearing (atomic orders) → observe/reliability (monthly).
- **Calendar**: 30 ticks/month, 12 months/year, 20 years/generation, 24 generations/age.
- **Environment**: extraction difficulty mean-reverts to `difficultyTarget = 1` (`theta = 0.15`,
  `sigma = 0.005`, bounded `[0.7, 1.4]`). Demand/sales EMA `alpha = 0.15`.
- **Reliability** (EMA, `reliabilityAlpha = 0.15`): score =
  `0.5·price-stability + 0.5·availability`. The price-stability component is
  **asymmetric — only upward price moves penalize it**; a price drop never reduces
  reliability. The availability component is `RelAvailable ÷ RelChecks` and **defaults to
  1.0** when there are no checks (`RelChecks == 0`), so a firm never asked for stock looks
  perfectly available.
- **Commands** (FastAPI/WebSocket): `init`, `reset`, `run`, `pause`, `step`,
  `applyConfig`, `select`, `companyDetail`, `watchCompanies`, `player`,
  `buyEquipment`, `tier2Query`, `buyLicense`, `foundHouse`. Reads are projections;
  per-distributor state is never sent to clients.

### 12.2 Pricing (per tick, derivative-following)

All three producer tiers price their output each tick with one **derivative-following
adaptive pricer**, plus a player/admin override. Prices are **unbounded economically**:
they may go below unit cost (sell at a loss) and there is no ceiling or unit-cost floor —
per axiom 6, a healthy price settles at an interior equilibrium. Two **numerical
guardrails** only prevent degenerate values, and the simulation must never settle at them:
`MIN_UNIT_PRICE = 0.01` (floor) and `MAX_UNIT_PRICE = 1e9` (ceiling). Every price is
quoted in **whole cents** (rounded half away from zero via `round_to_cent`).

**Initial price (tick 0)** — the flat first-guess markup from §5:
`P₀ = unitCost × (1 + t1Markup)`, with `t1Markup = 0.25` for every tier.

**Observation cadence.** A price is re-evaluated only when
`(tick + index) % priceObservationTicks == 0` and it has been observed at least once
(`priceObservationTicks = 30`). On all other ticks the price is simply held, clamped to
the guardrails.

**Decision (at a cadence tick), from the average realized gross profit/tick accumulated since
the last observation.** This is line sales revenue minus COGS. Rent and switching
transfers remain in net financial reporting and production forecasts, but do not
adjust the price-learning signal. In order:
1. **Scarce** (unmet demand: `demand > sales`) → raise, *regardless of the profit baseline*,
   so a lively downstream market is transmitted upstream (the incumbent supplier's 500k
   inventory buffer no longer hides demand pressure).
2. **Market anchor** (leaked going rate): the firm compares its price to its market's
   sales-weighted average price. Above `going_rate × (1 + marketAnchorBand)` → lower
   (expensive → contest); below `going_rate × (1 − marketAnchorBand)` → raise (cheap →
   capture value). `marketAnchorBand = 0.02`. This lets a small, expensive seller drift
   down to the going rate without a symmetric race to the bottom. The going rate is
   `Σ(sales_i × price_i) / Σ(sales_i)` over the sellers of that good (element / material /
   product), falling back to the simple average of their finite prices when a market has
   no sales in the window. This is the firm's own positioning against observed competitor
   prices, not a shared target: no seller aims at the average as a goal, and no buyer is
   steered by it (axiom 2).
3. **Profit baseline available** (a prior observation's realized profit exists) → pure
   derivative-following with a **2 % dead band**: reverse when profit fell ≥ 2 %, continue
   when it rose > 2 %, and **hold inside the band**. The change is
   `(current_gross - previous_gross) / max(abs(previous_gross), 1e-9)`, including
   negative and zero baselines. A shrinking loss is an improvement. Flat profit
   within this local rule is treated as the profit-maximum,
   so the walk stops there instead of overshooting the flat peak and drifting past it.

**Production & purchase gates (the quantity side of discovery).** A producer manufactures
only while its feasible output covers material cost at inventory basis, conversion,
and allocated forecast period overhead (eligible rent minus net switching forecast).
T1/T2 apply the 5% net-margin ramp to actual feasible whole batches after input and
cash constraints, including production from already-owned inputs. After rounding,
they recheck total contribution against the fixed overhead and reject a reduced
plan that would lose money. The variable-cost floor also remains in force.
Procurement has no margin gate. It refills the bounded input allocations above;
production assesses its own feasible plan after purchasing.
Rent remains a period expense, never inventory cost. These planning estimates do
not guarantee realized net profit: actual sales and end-of-tick rent eligibility
can differ. Existing finished goods can still sell.
Tier 0 extraction obeys the same hard gate against its *extraction* cost —
`if baseCost × difficulty > raw price`, extraction is 0.

T1/T2 throttle manufacturing, and Tier 0 throttles extraction, with the
**margin-ramp**. Input restocking is independent of this gate. Production quantity
is scaled by

`factor = clamp( margin / productionMarginBand , 0, 1 )`,

where producers use **estimated net margin** (2026-10-11):

`margin = 1 − (current_unit_production_cost + allocated_period_cost / planned_units) / price`,

`allocated_period_cost = forecast_line_rent - forecast_line_net_switching_income`.

`current_unit_production_cost = conversion + Σ (recipe ratio ÷ output) × inventory
cost basis`. The denominator is the feasible **unthrottled** production plan,
in finished units (T2 batch count × recipe output), not the reduced result or last
tick's sales. A zero plan stays zero; the implementation guards its denominator at
one unit. The fixed storage bill is split equally across the company's installed
lines, matching expense reporting. Eligibility uses a vectorized equity snapshot
at that tier's production phase entry (before procurement for combined T2): below $2M the estimated rent is zero. Each tier
computes this projection once; the Python and Numba planners consume the same
per-company line-expense array. Actual rent is still assessed after trading, when
equity can differ. The forecast never posts expense or changes inventory cost basis.
Arrears repayments are not new expenses and are excluded. Switching transfers
are posted as buyer expense and incumbent income at the cash transfer in both
engines. Producers' net-transfer forecasts use an EMA with `alpha` (default 0.15),
updated after the tick from actual income minus expense, and initialized at zero.
These are estimates of future transfers, not foreknowledge or guaranteed income;
an unforeseen first switching fee is still included in actual earnings. The $2M
exemption applies only to storage rent, never to switching expense. Expected net
switching income/expense is divided across installed lines like storage overhead.

T0 is storage-subsidized but includes forecast switching receipts in its net
margin; extraction cost is `baseCost × difficulty`. Its planned units are capped
at extraction capacity before allocating the period item. `productionMarginBand = 0.05`:
full planned quantity at net margin ≥ 5%, half at 2.5%, zero at or below
break-even. T1/T2 production additionally rejects a reduced batch plan if it no
longer covers allocated period overhead. Existing finished stock can still be sold.
Price learning uses **actual gross profit**, revenue minus COGS. Financial net
earnings additionally include posted switching income minus switching expense
minus actual rent. Company-period items are allocated over installed lines for
reporting; planning forecasts never replace actual postings.

**Pricing/demand audit.** Supplier ranking and order affordability already use
the delivered order's total cost including the payable fixed switching fee; its
stock-availability waiver and cash/lot caps remain. Consumer demand is a willingness-
to-pay curve `qmax / (1 + (effective_price / choke)^elasticity)`, with switching
friction in effective price. It is not based on producers' margins and should not
be changed to one. Market-price anchoring, shortage-driven price increases, and
initial markups are distinct from realized profit and remain unchanged. The
below-unit-cost production guard is a variable-cost feasibility rule, not a net
margin target: fixed rent is not capitalized or charged again there. Displayed
gross margins remain explicitly gross; displayed net margins use all posted items.

Validation: 49 Python tests and JavaScript profitability/formatting checks passed.
An isolated 30-tick probe from the stopped tick-5,159 checkpoint covered 61,020
companies. Maximum independent per-company earnings/equity residual was below
$0.000001. Separate forced-switch fixtures exercised all three buyer tiers in
both engines, including counterpart postings, exemptions, signed profit learning,
and checkpoint migration. Earlier calibration artifacts describe the old decision
rules and are not validation of this revised pricing/procurement policy.

**Step size** adapts: ×1.2 on continuation, no halving on reversal (×1.0), clamped to `[0.01, 1]`.
The price moves multiplicatively: `P ← clamp(P × exp(± pricingAggressiveness × response × scale))`, where
`clamp` is the guardrail interval `[MIN_UNIT_PRICE, MAX_UNIT_PRICE]`, then rounded to
whole cents (`round_to_cent`). If the rounded quote is unchanged and the direction is
*down*, the direction flips *up* (`if nxt == price and next_direction < 0: next_direction = 1`),
so a walk cannot wedge frozen at a cent boundary. After each
observation the profit/sales/demand/opportunity accumulators and the age counter reset.

**Distributor purchase is split across suppliers in whole units** (no fractional fill, no
all-or-nothing from one seller). Demand is **marginal-value**: the distributor walks its
sampled sellers in total-cost order (incumbent first; the loyalty charge below applies),
and at each seller computes `q_at = demand(price)` then buys `want = max(0, q_at − bought)`
whole units (capped by that seller's `⌊stock⌋`), stopping once `bought ≥ q_at`. The total
quantity is therefore pinned to the *marginal* seller's price — a rogue cheap seller
cannot inflate demand. The unsatisfied remainder is recorded as `endStockUnmet`. An order counts as fulfilled
only when its entire requested quantity was delivered; partial seller fills do not count
as full availability for reliability.

**Loyalty charge (real, paid to the incumbent).** A buyer's sampled offers are ranked by the total
cost of filling its order `q` from each seller alone. Staying with the incumbent
(`preferred`) costs `P_inc × q`; sourcing from a
challenger costs `P_chal × q + loyaltyCharge`, where

`loyaltyCharge = M × unit_cost × (1 + reliability_inc)`.

`unit_cost` is the product's canonical cost-ladder unit cost (§4) — a *fixed*
reference, independent of the current market price, so a price drop does not shrink the
barrier — and `reliability_inc` is the incumbent's reliability (0–1), so the
`(1 + reliability)` factor makes sourcing away from a reliable supplier cost up to 2× more. `M` is a **per-complexity** multiple, sized so the charge equals ~5 % of a typical
order: **41.665** for the T1 raw buyer (C-1/C-2, equal), **{3: 0.605, 4: 0.325, 5: 0.13}**
for T2 intermediate buyers by the buying firm's complexity, and **0.485** for T3 distributors.
The charge is **fixed per disloyal purchase** (independent of order size, so
a 1-unit order cannot dodge it) and is **paid to the incumbent**: deducted from the buyer's cash and credited to the incumbent — a
transfer, not a sink.

**Adaptive regime.** The per-complexity values above are *bootstrap seeds*, not constants.
Each tick, after the tiers operate, the kernel folds the observed **average order value**
(AOV) per buyer class — T1 raw (`raw revenue ÷ purchase events`), T2 material by buying
complexity (`material spend ÷ purchases`), T3 distributor (`distributor payments ÷ purchase
events`, including partial fills) — into an EMA (`α = loyaltyEmaAlpha`, default 0.01). Once per **year**
(every `ticksPerYear` ticks) it re-derives

`M = 0.05 × AOV / (unit_cost × 1.5)`,

so the charge keeps tracking ~5 % of a typical order as prices and margins drift, with no
per-generation bookkeeping. `unit_cost` here is the same canonical reference ($1 raw,
$1.50 material, mean T2 unit cost).

The buyer sources from a challenger only when `P_chal × q + loyaltyCharge < P_inc × q`, i.e. a challenger
must undercut the incumbent by more than `loyaltyCharge / q` per unit. The winner fills the
whole order in whole units; a split across suppliers is a fallback only when the winner
cannot fill `q` (and the charge is then incurred once, on the first non-incumbent unit).
**Stock-out exception:** the charge applies only to a *discretionary* purchase — if the
incumbent cannot fulfill the order (stock below `q`), the buyer sources from a challenger for free, no
charge.

**The relationship is sticky.** `endPreferredSupplier` (next tick's incumbent) changes **only
when a single seller filled the entire `q`**. If the demand was split across sellers, the
relationship stays with the old incumbent — even if a challenger sold the first unit and the
loyalty charge was paid. To take the customer, a challenger must therefore be a full
substitute: cheap enough to win the ranking *and* stocked enough to fill 100%.

**Player/admin override.** A player-controlled firm quotes the set price, clamped to the
same guardrails, and its adaptive state is reset, so the price takes effect on the next
tick. Uniform across T0, T1 and T2.

**Parameters.** `pricingAggressiveness` (0.35), `wholesalePriceResponse` (0.05, base step
fraction), `priceObservationTicks` (30, cadence), `researchPriceMinimumOpportunities`
(0, minimum traffic before repricing; 0 = repriced at cadence). `loyaltyMultiple`
(per-complexity *bootstrap*: C-1/C-2 **41.665**, C-3 **0.605**, C-4 **0.325**, C-5 **0.13**,
T3 **0.485**, × `unit_cost` × `(1 + reliability)` — the loyalty charge) and
`loyaltyEmaAlpha` (**0.01**, the AOV-EMA smoothing driving the adaptive regime above).
`switchingStableBand` (0.025) drives the
price-stability *metric*, not the price itself.
