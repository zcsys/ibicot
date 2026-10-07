# Generation 1 — Simulation Analysis

Run: full population, **Max** mode, 7,200 ticks (1 generation = 20 years × 12 months × 30 ticks).
Raw per-tick log: `stats/generation_run.jsonl` (7,200 lines). Kernel as of commit `138f3aa`
(demand function fitted to supply, flat first-guess markup, derivative-following pricer).

## 1. Verdict

The run **did not reach an economic equilibrium**. Prices compounded upward for the full
20 years (≈ ×1.2 per year), while utilisation decayed to ≈ 1 % of capacity and consumer
demand collapsed 118×. The market never settled; it drifted into a low-volume, high-price
husk. This is a **demand-model bug**, not a slow-convergence issue.

## 2. Results

### 2.1 Prices rose monotonically (×20–35 over 20 years)

| series | tick 0 | year 1 | year 5 | year 10 | year 15 | year 20 | × total |
|---|---|---|---|---|---|---|---|
| T0 (extraction) | 1.25 | 1.49 | 2.51 | 4.35 | 8.65 | 19.18 | **15×** |
| T1 (C-1/2) | 1.56 | 1.84 | 3.56 | 8.38 | 20.2 | 45.19 | **29×** |
| T2 C-3 | 2.19 | 2.65 | 6.15 | 17.6 | 42.0 | 61.77 | **28×** |
| T2 C-4 | 2.50 | 3.04 | 7.05 | 19.4 | 44.5 | 60.78 | **24×** |
| T2 C-5 | 2.81 | 3.41 | 7.88 | 22.2 | 48.8 | 64.00 | **23×** |

As markup over unit cost, the T2 complexities moved together — ~1.5× cost in year 1, ~10× by
year 10, ~35× by year 20 — i.e. **one shared, roughly exponential price path** for the whole
economy, driven upward at ~1.8 % per 30-tick observation.

### 2.2 Utilisation stayed at ~1 %

| series | peak utilisation | peak tick | final |
|---|---|---|---|
| C-3 | 2.14 % | 1,728 | 0.83 % |
| C-4 | 6.21 % | 559 | 1.27 % |
| C-5 | 11.21 % | 478 | 1.28 % |

Capacity is ~15M units/tick across all T2; realised demand peaked at ~2–11 % of that in the
first two years and then decayed to ~1 % as prices climbed.

### 2.3 Consumer demand collapsed 118×

- Desired quantity (`consumersActive`): **17.9M** at tick 1 → peak 18.3M → **152k** at tick 7,200.
- Fulfilment ratio: 1.0 % early → 94 % at the end (of a much smaller pie — the remaining
  consumers are being served only because almost everyone priced out).
- Total T2 equity: $90.0B → $94.3B (essentially flat; the "growth" is just unsold
  inventory booked at inflated basis, not profit).

## 3. Root cause

### 3.1 The demand scale was applied to the wrong knob

`procurement_profile` (`core/model.py`) sets, for each product,

```python
quantityFactor = tier2DemandFactor * (firms × capacity) / 5000   # = 302 for C-3
```

`quantityFactor` is a **per-consumer** multiplier: `qmax = baseQty × quantityFactor`, and
each consumer's request is `min(qmax, qmax / (1 + (P/V)²))`. Making it proportional to
*firms × capacity* (108:12:1) blew `qmax` up by ~130×:

| | old (∝ 1/(cost·markup)) | new (∝ supply) |
|---|---|---|
| C-3 `quantityFactor` | 2.29 | 302 |
| C-3 `qmax` (baseQty=5.5) | 12.6 | **1,663** |
| C-3 request at P₀=2.19 | ~9 | **~1,196** |

The supply-proportionality belongs in **how many consumers choose each product**
(the `demandWeight` used in market selection), *not* in the per-consumer quantity. Shaping
per-consumer `qmax` instead of consumer counts is the primary error.

### 3.2 All-or-nothing purchase turns it into phantom scarcity

`clear_end_users` (`kernel/tick.py:807`) only buys when a firm can satisfy the **entire**
request — there is no partial fill:

```python
if stock[candidate] >= requested:      # no partial fill
    seller = candidate; desired = requested; break
```

With `requested ≈ 1,196` and a firm's per-tick stock of ~300 (fill-to-target ≈ 9,500), a
firm can almost never satisfy one consumer's full request, so it **sells nothing** while
still logging the full `requested` into `t2Demand`. Instrumented at tick 30, one C-3 line
showed `demand 52,651 / sales 0 / stock 0`.

That makes the pricer's scarcity test (`adaptive_price`, `core/model.py`) fire falsely:

```python
scarce = demand > available          # available = sales + stock
if scarce: next_direction = +1       # raise price
```

`52,651 > 0 + 0` → `scarce=True` → raise. Every 30 ticks the price ratchets up ~1.8 %, and
the "profit fell → reverse" brake never engages because there is no profit signal at all
(sales = 0). 7,200 ticks / 30 = 240 observations → ×28.

### 3.3 Secondary cascade: production stalls

With every tier's price spiralling, T2 replacement cost outpaces its sale price and input
purchases stop. Firm 0 through the first 60 ticks: `made=0, raw=0, cash` frozen at
$425,000. The aggregate still shows some output only because a minority of firms are
transiently profitable; the modal firm idles. This is why utilisation decays toward 1 %.

## 4. What this tells us about the design

The **derivative-following pricer itself is sound**: in a reduced run (500 consumers,
1,000 firms) it correctly lowered prices on the "no sales → lower" rule. It only spirals
when fed a false "scarce" signal from the demand/purchase mismatch. The failure is the
**demand-shaping mechanism**, not the pricing rule.

## 5. Recommended fixes (in order)

1. **Revert `quantityFactor` to a small per-consumer value** (flat, or the old
   `1/(cost·markup)` shape) so a single request stays ~1–15 units — small enough that
   firms with a tick of stock can actually sell.
2. **Move the supply-proportionality into market selection**: set each product's
   `demandWeight ∝ firms × capacity` (108:12:1), so *more consumers* are routed to C-3
   than C-5, keeping total demand ∝ supply while `qmax` stays small.
3. **Re-derive `tier2DemandFactor`** against the *actual* consumer distribution. The
   earlier back-of-envelope (`N=500` consumers/product, `baseQty=5.5`) was ~50× too low —
   realised utilisation was ~1 % against a 60 % target.
4. **Harden the scarcity signal** (defensive): allow partial fills, or cap a consumer's
   request at the firm's expected stock, so `scarce` reflects a genuine stock-out rather
   than an all-or-nothing rejection.
5. Re-run a short (1–2 year) probe before another full generation, checking that
   utilisation settles in the 50–70 % band and prices plateau.

## Appendix — key numbers

- Auto-pause at tick 7,200 (1 generation). 7,200 JSONL rows written.
- T2 equity: $90.0B at reset → $94.3B at tick 7,200.
- `consumersActive`: 17.9M (tick 1) → 152k (tick 7,200); fulfilment 1.0 % → 94 %.
- Utilisation peaks: C-3 2.14 % (tick 1,728), C-4 6.21 % (tick 559), C-5 11.21 % (tick 478).
- Instrumentation showing phantom scarcity: `tick 30 → demand 52,651, sales 0, stock 0, scarce=True`.
