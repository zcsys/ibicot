# Design canon — Robotic Space Generation kernel

> **Status:** settled by review. This is the authoritative design rulebook: it states
> *what must be true* of the economy kernel and the game's entry into it. It supersedes
> the earlier "essential core" discussion and, where it conflicts with the current
> implementation, the canon wins and the implementation is to be brought into line.
>
> **Companion documents:**
> - [`economy_contract.md`](economy_contract.md) — the economic *intent, rationale and acceptance criteria*.
> - [`language_agnostic_contract.md`](language_agnostic_contract.md) — the *as-is* machine transcription of the current JavaScript kernel (state, config, RNG, tick order, commands). It stays valid until the kernel is re-implemented against this canon.
> - [`technology_strategy.md`](technology_strategy.md) — stack and deployment; [`economy_calibration_status.md`](economy_calibration_status.md) — calibration progress (parameters are not yet frozen).

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

---

## 3. Fixed topology & identity

- **Four tiers, fixed demarcation:** T0 extraction → T1 refining → T2 manufacturing →
  T3 external consumers. No tier bypass. C-1/C-2 belong exclusively to Tier 1;
  C-3/C-4/C-5 exclusively to Tier 2.
- **Four raw elements:** Water, Earth, Fire, Air.
- **Ten Tier 1 products:** four basic C-1 + six compound C-2, with their current identities.
- **Twenty Tier 0 firms**, including their **element-coverage spectrum** (2 all-element,
  4 three-element, 6 two-element, 8 single-element extractors).
- **The eight single-element extractors are also special-purpose**: the two Water
  extractors produce **machinery**; the two Earth extractors collect **storage-unit
  rent**; the two Fire extractors provide **financing**; the two Air extractors provide
  **advertising**. These activate the storage, capital-goods, credit, and
  visibility layers (mechanics TBD).
- Tier 0 companies are **significantly larger** than Tier 1 or Tier 2 companies.

---

## 4. Firm-scale model

- **Tier 0 has the most capital of all tiers.** It is the largest by design, despite
  having no "product complexity."
- **Tier 1 machinery is uniform:** every T1 product line's machinery is **$15K**
  (equity structure in §6). Within Tier 1, complexity differs only in *operations* —
  throughput falls (C-1 320 vs C-2 240), markup rises (compound premium), demand falls —
  never in capital.
- **Tier 2 machinery grows exponentially with complexity** (C-3 < C-4 < C-5). The size
  gradient lives here: higher complexity ⇒ much larger machinery capital and equity. The
  exact exponential formula is calibration.
- **Throughput falls with complexity** within a tier (C-1 > C-2; C-3 > C-4 > C-5).
  There is no global C-1…C-5 capital ladder: T0 is largest, Tier 1 is flat, Tier 2 rises.
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
- **Storage rent:** Tier 0 is fully subsidized (no storage or machinery costs). Tier 1
  and Tier 2 pay a minuscule per-tick fee per storage space, collected by the two Earth
  extractors.
- **Desired inventory = fill `G`:** the whole allocation is paid for, so empty space is
  pure waste. Companies fill the goods space to the brim (bounded by cash and capacity),
  rather than merely covering demand.
- **Balanced pipeline:** within `G`, raw and finished are held in the recipe's own
  `N : 1` ratio (each input unit = 1 space, each output unit = 1 space). For a recipe
  with `N` input units: `finished = G/(N+1)`, `raw = G·N/(N+1)`.

---

## 5. Product gradient

Higher complexity ⇒ **lower demand volume** and **higher unit markup**. The direction is
canon; the exact demand/markup curves are calibration.

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
| Tier 2 — C-5 | $1m | $1.875m | $1.625m | $4.5m |

The machinery ladder is `$15k × 5^max(0, c−2)`. Tier 0 ($10m) remains the largest single
company; C-5 ($4.5m) is the largest Tier 2 company.

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

- the §6 starting-equity table is the current working proposal (license `$1m`,
  machinery ladder `$15k × 5^max(0,c−2)`, residual cash, Tier 0 `$10m`) — final values
  from calibration;
- per-line throughput capacity by complexity;
- the demand-volume and markup curves by complexity;
- the storage standard (20,000), machinery-space footprint, and per-space rent;
- all prices, costs, activation rates, and offer-sampling counts.

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

A new kernel satisfies this canon when it implements §2–§8, passes the invariants in
[`economy_contract.md`](economy_contract.md), and reaches the fairness target in §8 under
its own determinism — with the performance and replay gates of
[`technology_strategy.md`](technology_strategy.md). The current JavaScript kernel remains
the executable oracle until then.
