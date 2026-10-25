# LandLord Alchemy — Implementation Contributions

Working notes on turning the V0 deck into a buildable game. These are my
implementation contributions; the design itself lives in
[`README.md`](README.md), and the original deck is
[`LandLordAlchemyV0.pdf`](LandLordAlchemyV0.pdf).

## 1. Build shape: simulation-first

Use the same pattern already proven in `robospace/`: a **deterministic,
headless simulation core** with a thin client on top.

- One **Python core** advances the game state on a fixed timestep and is the
  single source of truth for every rule and formula.
- The UI (web first, mobile later) is a dumb renderer that reads state and sends
  player commands; it owns no game logic.
- Keep it **headless + seedable + checkpointable** from day one, because the
  deck's tuning constants (`α`, `δ`, `c`, `c₁`, the production-time factor) are
  explicitly "to be determined by simulation". Batch sweeps are the only sane way
  to tune a chaotic predator–prey loop plus a market.

## 2. World model

Two scopes, split cleanly:

| Scope | Contents | Notes |
| --- | --- | --- |
| **Per-player "garden"** | land `L`, energy `E`, work force `W`, science `S`, money, vault, extraction | the clicker + Lotka–Volterra + alchemy loop is per-player |
| **Shared marketplace** | order book, bank, loans | Tier 3 is the only multi-player surface in V0 |

**Open decision:** keep the garden strictly per-player and make only the market
shared (recommended). A single shared world would make the chaotic E/W loop
unstable under many concurrent players.

### Player garden state

- `L_B` (bought land), `G_p` (Gaia Points), `L = L_B + G_p`.
- `E` (energy), `W` (work force), `S` (science, starts at 1).
- `P_k` per element, `P_T` (total extracted since the last land purchase).
- Money, vault cards (`element_id → amount`), active production slots, and the
  land-purchase click counter.

### Element / recipe graph

- `Element { id, name, type, tier, a_k, recipe: (in_a, in_b, λ) | source }`.
- Tier-1 sources are the four seeds: **Air, Water, Fire, Earth**.
- Every other element is a node in a **recipe DAG**; a recipe `λ·A + λ·B → λ·C`
  is an edge with tier constant `a_C = a_A + a_B`.

## 3. Tick loop

A fixed `dt` loop, in order:

1. **Clicker / land** — apply pending clicks (money + land-price movement), land
   purchases, Gaia-Point caps.
2. **Energy / Work Force** — integrate the ODEs below; clamp `E, W ≥ 0`; handle
   extinction with the deck's `n` reset.
3. **Extraction** — advance `P_k` and `P_T` for the active Tier-1 source.
4. **Alchemy** — advance production timers, mint completed elements, recompute `S`.
5. **Marketplace** — match orders, settle, apply supply decay.
6. **Live-ops** — scheduled recipe drops (daily / weekly / monthly / holiday /
   sponsor).

## 4. Canonical rules to implement

Pulled from the deck (see the README for the narrative):

```text
# clicker
1 click = game_tier × (1 + log₁₀(L_p)) money

# energy / work force (prey E, predator W, carrying capacity L)
dE/dt = R_w·R_q·S·E·(1 − E/L) − E·W + n·R_E·L
dW/dt = S·E·W − R_w·R_q·W + n·(1 − R_E)·L

# extraction (k ∈ {Air, Water, Fire, Earth}); P_T resets on each new land purchase
dP_k/dt = α · e^(−δ·S·P_T) · W · S · L · (dE/dt)

# science
S = 1 + Σ_k a_k · log₁₀(P_k)

# production time for combining k₁ + k₂
Δt = (a_k₁ + a_k₂)² · P_k   seconds
```

## 5. Numerical notes

- The E/W system is a **stiff, chaotic Lotka–Volterra**. Use **semi-implicit
  Euler** or **RK4 with non-negative clamping**, and never let a single tick
  overshoot extinction. The deck's boolean `n` is exactly the escape hatch: when
  everything goes extinct, reset instead of letting `E = W = 0` deadlock.
- `log₁₀(P_k)` in the science formula gives natural diminishing returns and keeps
  `S` from exploding — good, but it makes science growth sub-linear, so content
  pacing should assume that.
- Land pricing `L_p = c·L²` grows quadratically — a deliberate soft cap on land
  accumulation. Treat `c` and `c₁` as the primary balance knobs for the early
  game.

## 6. Anti-pay-to-win

Encode as hard rules in the core, not UI policy:

- Gaia Points `G_p`: max **3**, purchasable only after **10** bought land.
- Land price **increases with `G_p` held** — make this a monotonic multiplier in
  `L_p` so real money can never out-scale organic progress.
- Keep premium currency spendable only through land (no direct market money
  injection); otherwise the marketplace equilibrium is trivially buyable.

## 7. Content pipeline for 4,027 elements

Don't hand-author 4,027 elements. Split into:

- **Procedural skeleton** — generate the recipe DAG and IDs deterministically
  from the combination rule; this guarantees the count math (4/6/24/111/588/3294).
- **Curated layer** — human names, types, and special effects (sponsor/holiday
  cards) as a versioned content pack on top of the skeleton.
- **Discovery feed** — the deck's social-media drops map to a scheduled job that
  flips elements from "undiscovered" → "discoverable" on a cadence; the **LAB**
  is then a client that lets you try known-but-undiscovered recipes.

## 8. Marketplace

- An **order book** (limit orders) is enough for V0: "sell any amount at any
  price" is exactly a limit sell.
- **Bank as escrow**: to enter, a player locks money or products; match against
  locked balances only. Withdraw = release escrow.
- **Supply decay**: decay `P_k` (or its market value) over time to force
  re-engagement; make it gentle and visible so it feels like a living market,
  not a punishment.

## 9. Roadmap (thin vertical slices)

1. **Clicker** — land, money, clicks, Gaia caps (validates the core loop).
2. **Ecology** — E/W integration + Air/Water/Fire/Earth extraction.
3. **Alchemy** — recipe DAG, science, production timers.
4. **Collection** — vault + LAB.
5. **Market** — order book + bank.
6. **Card game** — offline, can ship independently.

## 10. Decisions still needed

- Single garden + shared market vs. a fully shared world.
- Integration method and `dt` for the E/W loop.
- Where the tick runs: server-authoritative vs. client sim with a server market.
- Tuning ranges for `α`, `δ`, `c`, `c₁`, production time, and supply decay.
