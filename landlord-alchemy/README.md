# LandLord Alchemy

An idle/clicker game concept that mixes **land**, **alchemy**, and a **free
market**, pitched as a 16-slide deck (V0).

> **Deck:** [`LandLordAlchemyV0.pdf`](LandLordAlchemyV0.pdf) · by **Dr Muhte**,
> under the **Ibicot** banner · landing page <https://www.landlordalchemy.play>

## Status

**Concept only (V0).** Nothing is implemented. The formulas below are first-pass
design; several constants are explicitly left to be tuned by simulation.

## The core loop

```
Buy Land → click to earn Money → extract Air / Water / Fire / Earth
         → combine them in Alchemy → sell on the Marketplace
```

Six resources drive it:

| Resource | Role |
| --- | --- |
| **Land (Gaia)** | The world's carrying capacity — everything scales off it |
| **Energy** | The "prey" in the energy ↔ work-force loop; powers extraction |
| **Work Force** | The "predator"; performs the extraction |
| **Science Points (`S`)** | Efficiency / unlock currency, earned from the elements you hold |
| **Product** | The elements themselves (Air, Water, Fire, Earth, …) |
| **Money** | Earned by clicking and trading; buys land and marketplace entry |

## Tier 0 — Land

Land is bought with **Money** and is the world's carrying capacity.

- Total land `L = L_B + G_p` — *bought land* `L_B` plus *Gaia Points* `G_p`
  (both start at 0).
- **Clicking** earns money and lowers the price of land:
  `1 click = game tier × (1 + log₁₀(L_p)) $`.
- The price of land `L_p` grows with the land you own (the deck sketches
  `L_p = c·L²`), and the click cost `L_c = c₁ + clicks³` rises with clicks.
  *(The V0 deck's notation here is rough.)*

**Gaia Points — anti pay-to-win.** `G_p` can be bought with **real money**, at
most **3**, and only after you already own **10 land**; points can be banked for
later. To prevent pay-to-win, **the price of land rises with the Gaia Points you
hold**.

## Tier 1 — Energy & Work Force

Unlocks after **10 lands**. A **predator–prey (Lotka–Volterra)** system where
**Energy `E`** is the prey and **Work Force `W`** is the predator, with the land
`L` as carrying capacity.

Three sliders:

- `R_E` — share of land dedicated to energy.
- `R_w` — work-force health rate *(log scale)*.
- `R_q` — energy-quality rate *(log scale)*.

Science starts at `S = 1`. A boolean `n` lets you **click to add energy & work
force**, and **restarts the system if everything goes extinct**.

```text
dE/dt = R_w·R_q·S·E·(1 − E/L) − E·W + n·R_E·L
dW/dt = S·E·W − R_w·R_q·W + n·(1 − R_E)·L
```

### Product extraction

Work Force extracts the four **Tier-1 products** — **Air, Water, Fire, Earth** —
one at a time. Output `P_k`:

- scales with work force `W`, land `L`, science `S`, and the energy rate `dE/dt`;
- **depletes** with the total extracted `P_T` (an exponential decay);
- `P_T` **resets every time you buy new land**.

```text
dP_k/dt = α · e^(−δ·S·P_T) · W · S · L · (dE/dt)      (α, δ to be tuned)
```

## Tier 2 — Alchemy

Unlocks when **all four Tier-1 products have been extracted** (≥100 of each).

- Combine two elements into a new one: `λ·A + λ·B → λ·C`, where `λ` is how many
  copies of each ingredient are consumed.
- New elements feed **further recipes** or get sold on the **Marketplace (Tier 3)**.
- Not every recipe yields a new element, but every attempt **takes time** —
  *"science is hard and expensive."*
- Production **slots are limited by the number of lands you own**.

### Science

```text
S = 1 + Σ_k a_k · log₁₀(P_k)
```

`k` indexes an element, `P_k` is how many of it you hold, and `a_k` is its **tier
constant**. Tier constants are additive across a recipe:

| Tier | Constant | Recipe |
| --- | --- | --- |
| 1 | `a₁ = 1` | Air, Water, Fire, Earth |
| 2 | `a₂ = 2 = a₁ + a₁` | first 6 elements, from two Tier-1 elements |
| 3 | `a₃ = 3 = a₂ + a₁` | Tier 1 + Tier 2 |
| 4 | `a₄ = 4 = a₂ + a₂ = a₃ + a₁` | … |
| 5 | `a₅ = 5 = a₃ + a₂ = a₄ + a₁` | … |
| 6 | `a₆ = 6 = a₃ + a₃ = a₄ + a₂ = a₅ + a₁` | … |

Production time for combining `k₁` and `k₂` scales as `(a_k₁ + a_k₂)² · P_k`
seconds.

### Element universe (every non-self combination)

| Tier | Elements |
| --- | --- |
| 1 | 4 |
| 2 | 6 |
| 3 | 24 |
| 4 | 111 |
| 5 | 588 |
| 6 | 3,294 |
| **Total** | **4,027** |

4,027 is too many to design by hand, so the plan is **live-ops**: recipes are
teased through social media and shipped on a schedule (below).

### Content & launch plan

- **Launch:** ~30 initial elements — 20 from Tier 4, 10 from Tier 5, 2 from Tier 6.
- **Daily:** 1 social-media element.
- **Weekly:** 20 discovered elements.
- **Monthly:** 4 "Super" elements (e.g. Tier 12).
- **Holidays:** special seasonal elements.
- **Sponsors:** temporary branded elements with special effects (e.g. a
  *McDonald's "Happy Meal"* card that halves Chicken production time, with a
  clickable link to the sponsor).

## Vault & LAB

- **Vault** — your element collection. Each card shows its tier, type, and amount,
  and can **produce** a quantity over a timer (e.g. a Tier-12 *Telescope*:
  1,000 in 1 day 16 hr).
- **LAB** — an area in the vault to **test and discover recipes**; when one is
  found, its card is revealed and added to the collection.

## Tier 3 — Marketplace ("the real game")

A **free market** where players trade products and money.

- Sell any amount of any product at **any price**.
- To enter, players **lend money** or **deposit products** to the Bank and trade
  with those banked assets.
- Players are pulled in because **product supply decays over time** (demand for
  new products) and **new land keeps getting more expensive**.
- Money and products can be **withdrawn at any time**.

## Bonus — hard-copy card game

A future physical game: pick **5 cards**, play them face-down, then reveal —
**rock-paper-scissors**, then **higher tier**, then **dice** as tie-breakers.
The winner takes the amounts as points; a weekly **leaderboard pays out Money**,
and play can **discover new recipes**.

## Open questions (from the deck)

- Tune `α`, `δ` (extraction), `c`, `c₁` (land pricing), and the production-time
  constant by simulation.
- Full marketplace economics: pricing, banking, and supply decay.
