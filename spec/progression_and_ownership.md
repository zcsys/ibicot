# Progression and ownership model — working design note

Status: **implemented in the engine** — the license/house data model, gating,
and actions are live in `engine/model.js` and `phase0_economy_engine_worker.js`,
with UI in `phase0_economy_engine.html`/`.js`. The calibrated economy itself is
unchanged by this layer; licenses and holding companies govern *who controls
what* and *what entry costs*, never how the bot economy runs. Enforcement is on
by default and can be disabled with the `setOwnershipEnforcement` admin message
(used by economy/mechanics tests that exercise player control as a test
mechanism rather than as gameplay).

## Implementation

- **Config** — `PROGRESSION_DEFAULTS`: `startingLicenses: ['T1']`,
  `licenseCosts: { T1: 0, T2: 10_000_000, T0: null }` (`null` = not for sale),
  `houseFoundingCost: 50_000_000`. These are reference ownership costs, not
  economy cash flows.
- **State** — `playerLicenses` (Set), `playerHouse` (null | `{ name }`),
  `ownershipAccounting` (`{ licensesSpent, houseSpent }`),
  `ownershipEnforced` (boolean mode flag; reset to `true` on `reset`).
- **Actions** — `buyLicense { tier }`, `foundHouse { name }`,
  `setOwnershipEnforcement { enforced }`.
- **Gating** — the `player` takeover handler requires a license for the tier
  being entered, and requires a house when the takeover would span tiers or
  multiple Tier 2 sectors. Releasing a firm (`controller: 'BOT'`) is never
  gated.
- **Snapshot** — `ownership` exposes `licenses`, `licenseCosts`, `house`,
  `houseFoundingCost`, and `accounting`.

## The three layers

### 1. Economy — a tier *is* a market role

A tier is defined by who the company buys from and who it sells to. This is
already the engine's supply chain and does not change:

| Tier | Buys from | Sells to | Machinery category |
| --- | --- | --- | --- |
| 0 | Gaia (raw) | companies | — (extraction capacity, no book machinery) |
| 1 | companies | companies | $15,000 basic / $75,000 compound |
| 2 | companies | public | $1,000 per product route |

### 2. License — the tier gate (exorbitant)

A **license** grants the right to operate a tier. A Tier 2 license is the right
to *buy from companies and sell to the public*. Licenses are exorbitantly
expensive, at least initially, so moving up a tier is a deliberate, major step
rather than an incidental purchase.

### 3. Machinery — within-tier, within-scope expansion

After a license, a firm grows by buying machinery:

- **Tier 1** — dedicated machinery at $15,000 (basic) / $75,000 (compound).
  A Tier 1 firm may add machinery for **any** material it does not already own;
  it is not material-locked.
- **Tier 2** — product routes at $1,000 each, **but only within the firm's own
  home sector.**

The Tier 2 sector lock is already enforced by the kernel: `addTier2Line`
rejects a product whose sector differs from the firm's `t2Sector`
([reference_kernel.js:470](engine/reference_kernel.js#L470)). A Tier 2 firm
cannot broaden itself into another sector by buying machinery.

### 4. Holding company — the cross-scope gate (exorbitant)

Because a Tier 2 firm is sector-locked, expanding into a different sector
requires founding a **holding company** that owns multiple firms. Tier 1, by
contrast, diversifies across materials directly through machinery and does not
need a house to do so. The holding company is itself another exorbitant step,
making cross-sector (Tier 2) and cross-tier expansion a deliberate strategic
investment.

## Progression ladder

1. **Start** — own one Tier 1 firm (1,000 players ↔ 1,000 Tier 1 firms).
2. **License** (exorbitant) — the right to operate a tier.
3. **Machinery** (within tier/scope) — grow the firm; Tier 2 routes stay
   sector-locked.
4. **Holding company** (exorbitant) — own multiple firms, spanning sectors and
   tiers.

The **20 Tier 0 magnates** remain team-controlled: the visible apex that no
player owns at launch, and the long-term yardstick for every house.

## Working terminology

- **House** — the parent/holding entity that owns firms. Alternates: *Concern*,
  *Conglomerate*, *Dynasty*.
- **Firm** — a single operating company (T0/T1/T2) with its own equipment,
  cash and books. Each firm is of its own; the house is an owner, not a shared
  resource.
- **License** (or **Charter**) — the tier gate.
- **Brand** — optional consumer-facing label for a firm's goods (T2 especially).

## Relationship to the economy and calibration

This layer is orthogonal to the calibrated economy. Firm books, opening equity,
the per-company pyramid (**Tier 0 > Tier 1 > Tier 2**) and the aggregate
ordering (**Tier 2 > Tier 1 > Tier 0**) are all unchanged. Licenses and holding
companies are ownership/entry costs, not changes to the bot economy or to
calibration.

## Decisions

- **Tier 2 is sector-locked** — machinery/routes may be bought only within the
  firm's home sector; cross-sector expansion requires a holding company.
  Already enforced by `addTier2Line`.
- **Tier 1 is not material-locked** — a Tier 1 firm may add machinery for any
  material it does not already own, diversifying across materials directly.
  Locking Tier 1 to one material would leave it no expansion path (each
  material has a single product and the firm already owns it), so that was
  rejected.
- The holding company therefore gates **cross-sector (Tier 2)** and
  **cross-tier** expansion, not Tier 1's cross-material diversification.
