# Preregistered buying-behavior research protocol

Frozen initial protocol: 2026-10-11, before candidate evaluation. Amendments must
state their date, reason and whether relevant results were already examined.
Baseline is clean commit `f2b9b47`; saved profile and source are under
`stats/buying-behavior-research/20261011-baseline-f2b9b47/`.

## Hypotheses and falsification

H1: storage-deficit procurement sustains upstream demand even when downstream
expected incremental returns are negative. Compare price-sensitive procurement
with that baseline while preserving production and pricing.

H2: incumbent/fee/full-fill mistakes explain some purchases but not all price
drift. Isolate fee/preference semantics, supplier sampling and sell-side anchor.

H3: own requested quantities outperform sales-only demand learning after a
shortage. Market priors improve cold starts but can synchronize ordering.
Hybrid must earn selection through measured recovery, viable trade and errors;
it is not assumed to win.

H4: fixed fees and complementary inputs require joint selection. Average-cost
ranking, sequential ingredient purchases and fixed fallback quantities can be
falsified on small exhaustive fixtures before any economic calibration.

## Units, invariants and gates

- Whole goods, lot counts, stock allocations, sampled IDs, preference transitions
  and checkpoint continuation: exact equality. No negative inventory/cash, no
  slot or whole-company storage excess caused by a purchase.
- Floating objective/reference comparisons: absolute `1e-9` dollars plus `1e-12`
  times the larger magnitude. Tie rules are part of the algorithm, not widened
  tolerances. Keep integer prices in cents where possible; fixed fees retain the
  baseline float formula. Do not quantize postings merely to satisfy a check.
- Accounting: per-company per-tick equity reconciliation <= `1e-6` dollars
  plus `1e-12 * max(abs(opening equity), abs(closing equity))`; aggregate cash
  residual <= `1e-4` dollars plus `1e-12 * cash total`. These allow accumulated
  binary64 rounding at the world's scale. Embodied-goods residual is exactly zero.
- Correctness: all required loyalty/stock/cash/lot/tie microcases plus independent
  exhaustive oracle agreement; no unresolved structural counterexample in the
  stated supported action space. Document restricted action spaces explicitly.
- Performance budget: candidate warm full observed tick median <= 2 times matched
  baseline, p95 <= 2.5 times, and median <= 500 ms on this host. Record compilation,
  recording, snapshots and encoding separately. Peak memory <= 2 times baseline
  plus 256 MiB. Budget is a research acceptance choice, not a promise of live TPS.
- Practical economic gates for a rollout: held-out final generation retail units
  >= 90% of paired baseline; no previously active product permanently loses all
  trade; each route's negative annual-earner share <= baseline + 5 percentage
  points; no price guardrail contacts; no unexplained price drift > 10% between
  final two years with collapsing units. No equal-profit or target-margin gate.
- Recovery: after a temporary demand/supply shock, compare 360-tick trailing
  trade to a matched no-shock run. Require >= 90% within 720 ticks, or reject the
  recovery claim. Report overshoot and company distributions, not just totals.
- Fairness: rotate/reverse buyer priority in controlled runs; flag route mean
  earnings or fulfillment changes > 5% and tail changes > 10%. Exact equality is
  not required for contested sequential stock, but systematic identity advantage
  cannot be silently called fair.

## Design and inference

Calibration seeds: 137 and 271. Held-out validation seeds: 811, 1597 and 2027.
Use paired initial states and counter-based random roles. Three held-out seeds
provide a small replication check, not precise population inference; give all
paired results, range and a seed-level mean/standard error. Ticks are correlated
and are never counted as independent replicates. Increase horizons if drift is
still visible. Do not tune to held-out results; label any later change and rerun
with new held-out seeds if necessary.

Stages: analytic and oracle fixtures; short calibration worlds; single-factor
ablations (sampling, fees, inventory feedback, curve calibration, joint basket,
sell-side anchor); one full generation for each surviving finalist/seed; at least
two full generations for the selected candidate and matched baseline; temporary
demand increases/collapse, outages/recovery, quote shocks, low cash, large fees,
no-history/re-entry, heterogeneous firms; dependency-closed expanded catalogs.
Reject early candidates with mathematical or invariant failures and preserve the
failures. An explicit rejection is a result; an unperformed requirement is not.

No production adoption occurs during this research. A recommendation must name
the exact code/configuration, supported ownership/catalog scope, recording and
checkpoint schema, migration strategy, staged rollout and rollback checkpoint.

## Amendment A: continuous extraction in the actual baseline

2026-10-11, during baseline recording and before any candidate evaluation:
`operate_tier0.make` retains fractional output when profitability/storage/cash
allocation leaves a fractional deficit. Thus the initial assumption that **all**
world goods are integers is false for the current T0 model. Purchases, manufactured
units, lots and allocations still require exact integer checks. Preserve continuous
T0 output in every treatment. For the global embodied-goods identity, use an
arithmetic error bound of `32 * spacing(max(abs(opening goods), abs(closing goods)))`
for the fixed handful of total reductions; separately verify every transaction's
integer stock decrement exactly. First 1,080 baseline ticks show at most
`1.5832483768463135e-7` of aggregate reduction residual. This is not an inventory
write-off and does not authorize fractional purchases or rounded-away loss.

## Amendment B: additional falsification after short calibration

2026-10-11, after seed 137's first 360 ticks and seed 271's first 1,080 ticks,
before inspecting held-out results. The default R1 parameters remain unchanged.

- Add a local/hybrid estimator that floors own first-request observations by own
  actual sales. First requests can omit a seller's fallback sales; ignoring both
  would be an unfairly narrow characterization of all local-information policies.
  This explicit alternative does not add sales to requests or inflate the market
  ledger. Forecast errors retain the common first-request target and are labeled.
- Distinguish stopping extraction from closing supplier offers. Add a temporary
  raw-water wholesale-market closure during ticks 181–360, retaining physical
  inventory in a settlement escrow. This tests unavailable suppliers even when
  stores contain a large buffer. Check posted accounting and goods after each tick.
- H5, derived analytically rather than fitted to a target margin: with exact
  expected daily demand D, no finished/owned inventory, no fees or hard bounds,
  and total marginal input/conversion cost c, R1 chooses
  `y = H*D*log(P/c)`. At `P/c=1.25`, a three-tick horizon permits only
  `0.66943*D` output. Replacing D at that markup requires `H>=4.48142`.
  Equivalently, at H=3, continuous replacement of D requires
  `P/c>=exp(1/3)`, an implied operating margin about 28.35% before fees.
  This is not a promised equilibrium or a literal pricing rule, but it exposes
  a hidden service-level consequence of the zero-terminal-value return model.
  The already planned H=1/H=6 ablations test this prediction. Do not tune H to
  conceal it or describe the return function as an empirically derived optimum.

The 59-run main campaign, including long runs and held-out seeds, is frozen in
`stats/buying-behavior-research/main-campaign-plan.json`. Additional supplier
closure, local-sales-floor and expanded-catalog tests are in
`supplement-plan.json`. Concurrent campaign latency is not an isolated benchmark.

Implementation repair during the campaign: the singular T3 rounding endpoint
now applies `u_eff=max(u,1e-12)` consistently to canonical quantity and marginal
values. The existing utility code already capped its first denominator. The
retained counterexample exposed their inconsistency at a $1e9 quote. Exact RNG
inversion confirms no activated `u=0` in seed 137/271 runs through 14,400 or the
held-out 1,080-tick windows, including all seed-137 shock scenarios. Therefore
this repair leaves campaign outcomes unchanged; it is not parameter tuning to
held-out outcomes. Each run still archives its actual source. The final contract
and regression tests explicitly state the common endpoint convention.

## Amendment C: extend the alternative local estimator, without retuning

2026-10-11, after the seed-137 sales-floor run completed 1,080 ticks. In its
final year it sold 1,459,250 retail units/tick versus 1,020,818 for local first
requests and 1,456,904 for market information. This calibration result shows
that a narrow first-request signal would be an inadequate test of all local
experience. Meanwhile the original three regimes' year-ten windows show large
trade losses, reversing their startup ranking. No parameters are changed and
no held-out outcomes are used to select new values.

Add fresh, full-population 7,200-tick local-sales-floor and hybrid-sales-floor
runs at seed 137, recorded in `sales-floor-long-plan.json`. These extend the
already declared alternative's observation horizon; they do not amend the
frozen 59-run main plan or replace failed original regimes. The analysis plan
grows from 80 to 82 runs, with `analysis-plan-original80.json` preserved.
Mature timing waits for all research workers, including these additional runs.
There is no qualified rollout finalist merely because one short window looks
better; ownership, model, performance and long-run gates remain unchanged.

## Amendment D: user-confirmed fallback quantities

2026-10-11, during the campaign. The user explicitly specifies: if A's quote
implies total demand 10 but A has only 2 items, buy 2; if B's quote implies total
demand 8, request `8 - 2 = 6` from B. If B is short, repeat at the next quote,
subtracting **all units already bought**. For a supplier s:

`remaining_s = max(0, q(price_s) - cumulative_purchased)`;
`take_s = min(available_stock_s, remaining_s)`.

This quantity rule is now a user decision, not a candidate hypothesis. Keep
the price-dependent demand curve and its parameters distinct from the fallback
calculation. For ascending prices and nonincreasing demand, stop on a complete
fill or zero remaining demand. A later quote cannot increase the amount still
needed. Candidate-specific quantities use the same rounding draw.

The production T3 reference and compiled loops already contain this subtraction.
The isolated executable specification is `tools/buying_research/fallback.py`;
`tests/py/test_buying_fallback.py` checks the exact example, further partial
fills, empty stock, actual production settlement, and 500 small fee-free markets
against the independent exhaustive allocation oracle. R1's fee-free retailer
is equivalent under ascending prices, ample cash, the same demand curve and
tie conventions (away from numerical near-ties). Its utility formulation is
not needed to explain the user's rule.

This amendment does not silently adopt R1's canonical bid for preference or
fees. The user has specified quantities, not whether a later supplier's complete
remaining fill qualifies as a preference change. That separate clarification
is pending. Preserve existing campaign sources/results as R1 evidence; no
production defaults, live run, or recorded treatment is changed by this note.

The rule also exposes an industrial scope failure. With a single complementary
input and unconstrained derived demand 10 at A's quote and 8 at B's, stock `[2,20]`
allows the requested split `[2,6]`. R1's one-supplier restriction instead chooses
`[0,8]` and pays more for the same eight planned outputs. Independent enumeration
in `industrial_fallback_case.py` verifies this witness. Record R1 as failing the
confirmed industrial fallback requirement; do not turn its historical restricted
action set into user authorization. A future coupled split-basket implementation
must preserve shared cash, recipe lots, storage and separate loyalty semantics.

## Amendment E: complete the preserved baseline's measurement coverage

2026-10-12 local date, after the two-generation R1 run completed. The original
14,400-tick baseline predates normalized per-tick tolerance ratios, price-bound
contact counters, opening company arrays and two production-cost recording
fields. Its absolute residuals and exact legacy-transaction replay remain valid
evidence, but cannot retroactively prove the newer normalized gate at every tick.

Run the identical seed-137 baseline for 14,400 ticks in a new directory,
`20261012-baseline-measurement-replay-137`, using the current recorder. This is
a measurement replay, not a new economic treatment, replacement of the preserved
baseline, or parameter retuning. Require exact final world-array/state agreement
and comparison of all common recorded product/accounting fields, reconstructing
the already documented historical T0 net allocation before comparison. Only
after those checks may its additional measurements support claims about the
preserved baseline trajectory. If it differs, retain both and investigate.

The frozen 82-run economic analysis plan remains unchanged. Audit this replay
separately and include it in the final source/coverage audit. Isolated timing
already waits for every research worker, so it will also wait for this replay.
Cost snapshots at tick 7,200 remain independently useful: they distinguish last
batch cost, COGS and a clearly labeled current-quote input-bill comparator.

## Amendment F: sustained adverse-stock performance coverage

2026-10-12, after inspecting the small-cash economic scenario and before any
final isolated timing profile started. Ordinary startup has initially empty
stocks but rapidly fills them; it does not measure a sustained empty downstream
market. Add a fresh matched baseline/market pair of 360 ticks with the existing
`small-cash` scenario (initial cash ×0.001). This is a combined cash-starved,
empty-stock workload, not an isolated estimate of either mechanism's causal
cost. The scenario and its economic outcomes are already part of the frozen
82-run plan; these two additional runs measure isolated performance only.

The six-job fresh-profile plan preserves the previous four-job plan as
`adverse-benchmark-plan-before-stock-profile.json`. Together with four mature
profiles there are ten final timing runs. The combined evidence audit has 93
runs (82 economic, one exact measurement replay, ten timing), retaining its
former 91-row plan separately. The numerical median/p95/memory budgets remain
unchanged; no favorable result has been selected or threshold relaxed.
