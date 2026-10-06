# Proposal — Collective Demand Vector (replacing the 1M procurement agents)

Status: **proposal** (not implemented). This is a cardinal change; it replaces the
agent-based end-user demand layer with a deterministic aggregate demand vector.

## 1. Motivation

The economy has 1,000,000 end-users, of which 10 % (100k) activate each tick. Each active
user exists to do exactly four things, all in the `clear_end_users` phase:

1. pick a **product** (basket → sector → `t2SectorProductWeight` search),
2. pick **firms** (sample `consumerSearchOffers=5`, plus a preferred supplier),
3. compute a **quantity** `q(P)` from the demand curve, and
4. **buy**, splitting across suppliers in whole units.

These four steps are a *Monte Carlo sampler* of a demand distribution. The 1M agents are
not doing anything the model needs beyond producing, each tick, three aggregate objects:

- a **product demand vector** `D[p]` — how many units each good wants,
- a **per-firm demand vector** `d[f]` — how that demand splits across the firms of each
  product (the price-competition outcome), and
- the **feedback** those two feed into reliability, demand-EMA forecasts and the
  derivative-following pricer.

The proposal is to compute those objects **directly and deterministically** instead of
sampling them one consumer at a time.

**Why:**

- **Speed.** The consumer loop is ~half the tick cost (≈0.08 s of ~0.14 s). A vector form
  is O(products + firms) and vectorisable, not O(active consumers × offers).
- **Determinism / no noise.** The RNG is already seeded (so runs are reproducible), but the
  per-tick demand still carries Monte Carlo noise. The collective vector is the *exact
  expectation*, so trajectories are smooth and the "noise vs signal" question disappears.
- **Inspectability.** A demand vector is a first-class object you can read and calibrate
  directly (`D[p]` per good), instead of inferring demand from 100k random walks.
- **Separation of concerns.** Demand (a vector) and its allocation to firms (a competition
  rule) become two explicit, testable stages rather than one entangled loop.

## 2. The two stages

### Stage A — product demand vector (uncontroversial)

For each of the 200 Tier-2 products `p`:

```
D[p] = N_p · q̄(P̄_p)
```

- `N_p` = deterministic consumer count routed to `p` =
  `activation · population · sectorShare(s_p) · productWeight(p)`.
  `productWeight ∝ firms × capacity` (the 108:12:1 shape) — **already how routing works**,
  just made deterministic instead of per-draw.
- `q̄(P̄_p)` = expected per-consumer quantity at the product's effective price:
  `q̄ = E[baseQty] · quantityFactor / (1 + (P̄_p / V_p)²)`, with `V_p = 2 · cost_p`.
  The consumer heterogeneity (`baseQty ∈ 1..10`, `choke ∈ 0.9..1.5`, `η = 2`) collapses to
  its expectation (mean, or a closed-form integral if we want the tail).

`P̄_p` (the "effective price" of product `p`) is the one genuinely new knob — see §4.

### Stage B — firm allocation (the hard part)

Distribute `D[p]` across the `firms_p` firms of product `p` by a **competition rule**.
This stage must reproduce what the offer-sampling currently does: cheaper firms get more
demand, but not all of it — every firm keeps a non-zero chance of being sampled.

Candidates:

1. **Merit-order (clearing price).** Sort firms by effective price; allocate `D[p]` in
   price order up to each firm's stock/capacity; the marginal firm sets the clearing price.
   — Deterministic and interpretable, but *harsher* than today: only the cheapest firms
   sell, so prices collapse to marginal cost and competition is cutthroat.
2. **Logit / choice model.** Firm `i`'s share ∝ `exp(−price_i / τ)`, with `τ` a temperature
   matching the current "softness". — Smooth, cheap, differentiable; but `τ` is a new
   parameter and it discards the "sample 5" bounded-rationality structure.
3. **Analytic cheapest-of-k.** Keep the current semantics exactly: firm `i` (price rank
   `r`) is the cheapest of a uniform 5-sample with probability
   `P(i sampled) · P(all other sampled firms are pricier)` — computable in closed form.
   — Preserves today's competition intensity *exactly* and removes only the noise; the
   most faithful, at the cost of a slightly more involved formula.

The sales are then `min(allocated, stock)` per firm, rounded to **whole units**, preserving
the "no fractional fill" rule — the allocation is real-valued (a vector), the sales are
whole numbers.

## 3. What is preserved vs changed

**Preserved** (the economics we care about):

- the demand curve `q(P) = qmax / (1 + (P/V)^η)`;
- routing ∝ supply (108:12:1);
- price competition (cheaper → more demand);
- whole-unit sales and the derivative-following pricer (it reads per-firm sales/demand,
  which Stage B still produces);
- reliability / demand-EMA / forecast feedback (also per-firm, from Stage B).

**Changed / lost** (and what we do about it):

- **Per-consumer heterogeneity** (baseQty, choke, basket) → collapsed to an expectation in
  Stage A. If the tail matters, keep a small set of *consumer types* (a handful of
  (baseQty, choke, sector) classes) and sum their vectors — still O(types), not O(agents).
- **Sampling noise** → gone (intended).
- **Preferred-supplier stickiness** (the switching-cost relationship) → the hardest loss.
  It is a *per-buyer* memory, which a vector has no room for. Options: (a) drop it and keep
  the switching-cost as a *ranking* friction in Stage B only; (b) replace it with an
  aggregate loyalty matrix (previous-allocated → current-allocated) so a fraction of each
  firm's demand persists before re-allocation.
- **Whole-number split** (an individual buyer filling from 2+ sellers) → becomes a Stage-B
  allocation with rounding; the *observable* outcome (a buyer's units come from possibly
  more than one firm) is preserved in aggregate.

## 4. Key design decisions (open)

1. **`P̄_p` (effective price).** Min price, volume-weighted mean, or the clearing price from
   Stage B (which makes A and B mutually consistent but couples them)? Recommended: compute
   A and B *together* as one clearing — `D[p]` and the firm allocation are solved jointly.
2. **Allocation rule.** Recommendation: **analytic cheapest-of-k** (option 3) to keep the
   competition intensity identical, falling back to logit if the closed form is too heavy.
3. **Stickiness.** Recommendation: keep the switching cost as a Stage-B ranking friction,
   and add a small aggregate loyalty term (a fraction of last tick's allocation persists).
   Full per-buyer memory is dropped.
4. **Heterogeneity.** Recommendation: mean-field first (`E[baseQty]`, `E[choke]`), with an
   escape hatch to a few consumer types if the loss proves material.
5. **T0/T1 B2B demand.** This proposal only concerns the *end-user* (T2) demand. The T1→T2
   and T0→T1 input purchases are already vectorised (they're firm-to-firm, not agent-to-firm);
   they stay as-is.

## 5. Risks

- **Calibration drift.** The agent model's emergent competition/stickiness has been part of
  why prices settle where they do. A deterministic allocation will settle *slightly*
  differently; expect a re-tune of `tier2DemandFactor`, `taumin/taumax`, and possibly `τ`.
- **Over-determinism.** Removing all noise can expose limit-cycles that the noise used to
  mask (e.g. firms in a product perfectly synchronising their price steps). May need a
  small deterministic tie-break or a tiny residual random draw per firm.
- **Scope creep.** Stage A is cheap and safe; Stage B is the risky half. They should be
  landed and validated separately.

## 6. Recommendation

Do it in two steps, validating each before the next:

1. **Stage A only** — replace the per-consumer *activation/quantity* with the product demand
   vector `D[p] = N_p · q̄(P̄_p)`, but keep the existing offer-sampling for Stage B
   (i.e. feed `D[p]` to the current firm loop as a *budget*). Verifies the vector against
   the agent baseline (demand totals, utilisation, prices) at a fraction of the risk.
2. **Stage B** — replace offer-sampling with the analytic cheapest-of-k allocation + an
   aggregate loyalty term, then re-run the equivalence/behaviour gates.

This gives the speed and determinism of the vector while de-risking the competition layer —
and it is the change most likely to make the 1-generation runs fast enough to iterate on.
