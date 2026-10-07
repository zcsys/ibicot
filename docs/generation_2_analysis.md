# Generation 2 — Collapse-to-Cogs Analysis

Run: full population, **Run Max**, stopped early at **tick 2,370** (~7 years of 20, per
request — no need to finish). Raw per-tick log: `stats/generation_run.jsonl`
(2,370 rows). Kernel as of commit `3eece87` with `tier2DemandFactor = 23`.

## 1. Verdict

This run did **not** reach equilibrium. It is the **mirror image of Generation 1**: instead of
prices spiralling upward, **Tier-2 prices collapsed toward — and then below — their realized
input cost (COGS)**, while upstream T0/T1 prices marched up ~80 %. Tier-2 utilization idled
at ~1–3 % and Tier-2 gross margin collapsed to ~0. This is the known **"collapse to cogs"**
failure mode, and its cause is a **supply-side capacity-ladder imbalance** (T0/T1 ~30–50×
undersized vs T2), not a pricer bug.

## 2. Results

### 2.1 Upstream prices rose ~80 %, downstream prices barely moved

| series | tick 1 | tick 2,370 | × total |
|---|---|---|---|
| T0 (extraction) | 1.25 | 2.27 | **1.82×** |
| T1 (refining) | 1.56 | 2.68 | **1.72×** |
| T2 C-3 | 2.19 | 2.28 | **1.04×** |
| T2 C-4 | 2.50 | 2.74 | **1.10×** |
| T2 C-5 | 2.81 | 3.02 | **1.08×** |

The asymmetry is the whole story: the two upstream tiers repriced upward by ~70–80 % over
seven years, while all three T2 complexities moved only 4–10 %.

### 2.2 The C-3 market went underwater — finished goods now sell below their input

The cleanest single metric is the **input/output price ratio** (average T1 price, which is
T2's raw-material input, over average T2 output price):

| ratio | tick 1 | tick 2,370 | crossed 1.0 |
|---|---|---|---|
| T1 / C-3 | 0.71 | **1.18** | **tick 1,476 (year 5)** |
| T1 / C-4 | 0.62 | 0.98 | approaching |
| T1 / C-5 | 0.56 | 0.89 | — |

At tick 1,476 the average C-3 manufacturer began selling its finished good for **less than
the average T1 material it consumes** — i.e. below COGS before conversion is even counted.
The nominal markup ("1.30× unit cost") is misleading: `unitCost = $1.75` is a static catalogue
number, but the *realized* input cost is the live T1 price, which tripled past the C-3 sale price.

### 2.3 Margin concentrated upstream, vanished downstream

Realized gross margin (revenue − COGS)/revenue at stop:

| tier | firms | realized gross margin |
|---|---|---|
| T0 | 20 | **62.9 %** |
| T1 | 1,000 | **24.3 %** |
| T2 | 60,000 | **≈ 0 %** (C-3 negative) |

Pricing power follows concentration — 20 extractors capture the most, 60,000 manufacturers
capture none — and the fragmented tier gets its margin bid away to cogs.

### 2.4 Utilization idled at ~1–3 % (target 50–70 %)

| series | peak utilization | peak tick | final |
|---|---|---|---|
| C-3 | 1.74 % | 104 | 0.89 % |
| C-4 | 5.05 % | 205 | 2.70 % |
| C-5 | 9.27 % | 347 | 1.30 % |

Capacity is 15 M units/tick; realized output was ~200 k/tick. Every peak occurs inside the
first two years and then decays as the margin squeeze tightens.

### 2.5 Consumers did *not* collapse (unlike Generation 1)

- Desired (`consumersActive`): **9.84 M → 9.81 M** (stable — not the 118× collapse of G1).
- Fulfilled: 18 k → 201 k, fill rate steady at **~2 %**.
- T2 equity: $90.00 B → $90.32 B (flat; the "growth" is unsold inventory booked at basis).

The demand-side is *there* but starved: ~9.8 M units are desired and only ~200 k clear, because
T2 firms cannot profitably produce at cogs-or-below prices.

## 3. Root cause

The demand factor was a red herring: the probe (`./run.sh probe`) showed that sweeping
`tier2DemandFactor` 23 → 200 changes only latent demand (`consumersActive` 9.8 M → 85 M) while
utilization stays ~0.7 % and T2 price stays pinned. The real cause is a **capacity-ladder
imbalance** — the upstream tiers are ~30–50× too small to feed the downstream:

| tier | capacity (per tick) | needed to feed T2 at ~60 % |
| --- | ---: | ---: |
| T0 extraction | 20 × 10,000 = **0.2 M** | ~9 M raw |
| T1 refining | 1,000 × 500 = **0.5 M** | ~9 M processed |
| T2 manufacturing | 60,000 × ~300 = **15 M** | (capacity; demand ≈ 9.8 M) |

With only ~0.2–0.5 M of raw/processed inputs available against 15 M of T2 appetite, the economy
is hard-capped near T0's throughput (~0.2 M/tick). Starvation makes T1 (the scarce intermediate)
raise its price — correctly — and T1's price *is* T2's input cost. T2 can't pass that cost
through (fragmented 60,000-firm tier, elastic consumer demand, "no sales → lower" on the idle
~99 %), so T2's **margin** collapses to cogs while its absolute price barely moves. This is the
mechanism behind "collapse to cogs": the scarcity signal inflates T0/T1, but cannot force
pass-through on the tier with no pricing power.

## 4. What this tells us about the design

The derivative-following pricer is behaving as specified — it is **not** the failure point. The
failure is the supply-side scale: the canon's T0/T1 capacity numbers are mis-scaled by ~30–50×
against T2 capacity and consumer demand. (T1 compounds are already "2 raw → 2 processed", i.e.
count-preserving, via `outputQty = sum(inputs)` — necessary, but it only halves compound raw
consumption; it does not change T1's output capacity.)

## 5. Fix applied

Rescale the upstream capacity ladder in `core/config.py`:

- T0 `capacity` 10,000 → **500,000** (target/max inventory 0.5 M / 1 M → 5 M / 10 M).
- T1 `t1Capacity` 500 → **10,000**.

**Verified over 720 ticks**: utilization C-3 **44 %**, C-4 **57 %**, C-5 **66 %** (was 1–3 %),
fill rate **74 %** (was 2 %), T1/C-3 ratio **0.77** (stays < 1 — no collapse-to-cogs). C-3 sits
just under the 50–70 % band; sweeping `t1Capacity` 10,000 → 12,000 shows no further gain, so the
remaining C-3 gap is the consumer-routing / material-mix side, not upstream capacity.

## Appendix — key numbers

- Stopped at tick 2,370 (~year 7); 2,370 JSONL rows written.
- T0/T1 price drift: ×1.82 / ×1.72 over the run; C-3/C-4/C-5: ×1.04 / ×1.10 / ×1.08.
- T1/C-3 input-price ratio crossed 1.0 at **tick 1,476** (start of year 5).
- Realized gross margin at stop: T0 **62.9 %**, T1 **24.3 %**, T2 **≈ 0 %**.
- Utilization peaks: C-3 1.74 % (tick 104), C-4 5.05 % (tick 205), C-5 9.27 % (tick 347).
- T2 equity: $90.00 B → $90.32 B; T2 cash: $18.03 B → $18.35 B.
- `consumersActive`: 9.84 M → 9.81 M (stable); fulfilment ≈ 2 %.
