# Star Business — Economy Kernel

A deterministic, fair-market simulation of a physical-goods supply chain, driven
by autonomous firms and entered by players on equal footing. This repository is
the authoritative server-side **economy kernel** in **Python (NumPy + Numba)**,
with a live browser dashboard.

The rulebook is [`docs/design_canon.md`](docs/design_canon.md) — it is the single
source of truth for *what* the economy is. Everything here implements it.

**Naming.** All display names (materials, companies, sectors, equipment, and
goods) follow the **Star Business** naming catalog, and house style is
**American English**. See the *House Style* section of `docs/design_canon.md`.

## Quickstart

```sh
./run.sh serve             # start the Python backend AND open the browser dashboard
./run.sh run --ticks 360   # headless run (append --stats path to write a JSONL log)
./run.sh test              # run the Python test suite
```

`serve` starts a FastAPI + WebSocket service on `http://127.0.0.1:8000`, serves the
dashboard at `/index.html`, and opens it in a browser. Use **Run / Run Max / Pause /
Step / Reset / Apply Params** — the Python kernel owns the world. Browsers attach
to its current state; only **Reset** starts a new world. The server defaults to full
population and accepts `ECONOMY_CFG` for its initial configuration.

The launcher needs Python 3.12 with NumPy; Numba and FastAPI are vendored into
`.pydeps/` (git-ignored). If `.pydeps/` is missing, run the `pip install` line the
launcher prints.

## The economy

A four-tier physical supply chain, calibrated to be *supply-consistent* (every tier
can actually feed the next):

| Tier | Who | Count |
| --- | --- | --- |
| **T0 — Resource Companies** | extract the four raw elements (Water, Earth, Fire, Air) | 20 companies |
| **T1 — Refineries** | 10 refined materials (4 C-1 basic + 6 C-2 compound) | 1,000 firms |
| **T2 — Manufacturers** | 200 manufactured goods, complexity C-3 / C-4 / C-5 | 60,000 firms |
| **T3 — Consumers** | resident consumers | 1,000,000 |

Time is a **30-tick month**, a **360-tick year**, and a **7,200-tick generation**
(20 years). The T2 firm count follows a reverse 6:3:1 ratio — 36,000 C-3, 18,000 C-4,
6,000 C-5 — so more complex goods have fewer, higher-capacity producers.

## Key mechanisms

- **Deterministic** — SplitMix32 RNG; identical `(seed, config)` ⇒ byte-identical state.
- **9-phase tick** — reset → environment (difficulty) → T0 extraction → T1 purchase →
  T1 manufacture → pricing → T2 buy/make/price → consumer clearing → observe/reliability.
- **Derivative-following pricing** — firms walk their price against realised profit and
  hold at the flat optimum; a 2 % dead band prevents overshoot.
- **Margin-ramp production** — a producer throttles manufacturing by estimated net margin, including eligible storage expense and forecast switching income/expense
  (`productionMarginBand = 0.05`): full output at ≥ 5 % margin, tapering to 0 at
  break-even; reduced batches must cover allocated overhead. Purchasing instead
  refills bounded input slots regardless of margin: half the goods space is for
  finished output and half is divided equally among distinct inputs.
- **Adaptive loyalty charge** — switching suppliers costs
  `M × unit_cost × (1 + reliability)`; `M` is re-derived once per year from an EMA of the
  observed average order value (`loyaltyEmaAlpha = 0.01`) so the charge tracks ~5 % of
  a typical order as prices drift.
- **Reliability** — `0.5 × price-stability + 0.5 × availability`, EMA-smoothed monthly.

## Repository layout

```
economy/                  # the Python kernel
  core/                   #   catalog + canon parameters, config, RNG, WorldState
    config.py             #   every tunable parameter (single place to change them)
    model.py              #   catalog, cost ladder, pricing/loyalty primitives
    state.py              #   WorldState (NumPy arrays) + world construction
    rng.py                #   SplitMix32 (scalar + vectorised, bit-exact)
  kernel/
    tick.py               #   the 9-phase tick (pure-Python reference)
    numba.py              #   @njit fast path, byte-identical to tick.py
  server/
    runtime.py            #   KernelRuntime (step/pause/publish, stats)
    service.py            #   FastAPI + WebSocket service
    scheduler.py          #   tick scheduling for the dashboard
    persistence.py        #   checkpoint save/load (byte-identical round-trip)
  cli/main.py             #   headless `run` / `serve` entry point
web/                      # the browser dashboard (served by the backend)
  index.html  app.js  bridge.js  catalog.js
docs/design_canon.md      # the design rulebook (source of truth)
docs/landlord-alchemy/    # sibling "Landlord Alchemy" design artefact
tools/dump_catalog.js   # one-time catalog extractor (web/catalog.js → JSON)
tests/                    # Python tests (RNG + determinism + invariants)
run.sh                    # launcher
```

The dashboard (`web/app.js`) speaks WebSocket to the backend through `web/bridge.js`,
which re-implements the browser `Worker` interface so the UI code runs unchanged
against the Python kernel.

## Configuration

All parameters live in `economy/core/config.py` (see `default_cfg()`), organized by
tier, demand, and market behavior. Override them per-run:

```sh
./run.sh run --cfg '{"consumerCount": 500, "t2FirmCount": 1000, "seed": 137}'
ECONOMY_CFG='{"consumerCount": 500, "t2FirmCount": 1000}' ./run.sh serve
```

Notable knobs: `productionMarginBand`, `loyaltyMultiple` (bootstrap) +
`loyaltyEmaAlpha`, `elasticity`, `pricingAggressiveness`, `switchingStableBand`,
`priceObservationTicks`. The exact settled values and their rationale live in
`docs/design_canon.md`.

Storage rent is **$2.80 per 1,000 allocated storage units per tick**: an eligible
20,000-unit company pays $56 per tick. T0 is exempt. T1/T2 companies below
$2M book equity immediately before billing pay nothing that tick, including
no collection of old arrears. Existing debt is retained; eligibility is checked
every tick; exactly $2M is eligible. The UI uses per-1,000-per-tick units; the compatible persisted key
`storageRentPerUnitYear = 1.008` represents the same rate over 360 ticks/year.
Changes apply prospectively, without retroactive bills or refunds.

Price learning uses line **gross profit (sales minus COGS)**. Rent and switching
transfers do not adjust its observations; production retains its net-margin gate
and transfer forecast. T1/T2 production also gates existing inputs on feasible
net margin, including eligible rent, and rejects reduced plans that cannot cover
the allocated overhead. Checkpoint v5 clears older learning windows on load.

Net profit is gross profit **plus switching income, minus switching expense,
minus actual current-tick storage expense**. Net margin divides that result by
sales revenue, or shows “—” for zero revenue or unavailable legacy postings. Product views
allocate each company's charge across its own installed lines; company cohorts
use the company's home sector. See [storage accounting and performance](docs/design_canon.md#per-tick-storage-rent)
for formulas, checkpoint compatibility, and the vectorized implementation.

## Tests

```sh
./run.sh test
# tests/py/test_rng.py      SplitMix32 against known reference outputs
# tests/py/test_kernel.py   determinism (byte-identical re-runs) + invariants
#                           (no negatives, conservation holds, atomic orders)
# tests/py/test_performance.py  exact ranking, storage planning, reductions,
#                               sort order, and WebSocket serialization
# tests/js/test_formatting.js   unchanged locale formatting
```

## Performance validation

```sh
./run.sh bench --ticks 361 --fingerprint-every 1 --output /tmp/before.json
# Make changes, then run the same seed/config and compare:
./run.sh bench --ticks 361 --fingerprint-every 1 --output /tmp/after.json --verify /tmp/before.json
```

The benchmark uses the full 60,000 manufacturers and 1,000,000 distributors by
default. It measures steps, snapshot construction, JSON encoding, and company
queries separately. Compilation and state fingerprinting are excluded from the
steady-state timings. Comparison checks every world array, scalar ledger,
per-tick stats, snapshot, and sampled query result exactly; only elapsed-time
telemetry is excluded. Use `--cfg` for another population or parameter set.

The optimized kernel preserves sequential trade order, seeded draws, supplier
tie-breaks, and floating-point reduction order. It uses indexed stock searches,
direct uniform offer sampling, bounded storage planning, compiled refinery and
research loops, and shared snapshot projections. Manufacturer pages project only
the requested sort column. Broadcasts encode each message once, and the browser
reuses locale number formatters.

Compiled functions are cached under `economy/__pycache__/numba/` (or the configured
`NUMBA_CACHE_DIR`). The cache is keyed by all economy Python source and the
catalog, so dependency edits invalidate compiled callers as well. The first run
after a source change still compiles; later processes reuse the cache. Numba
remains optional, with Python/NumPy fallbacks.

The 2026-10-10 measurements and validation coverage are recorded in
[`docs/performance-validation-2026-10-10.json`](docs/performance-validation-2026-10-10.json).

On the local arm64/Python 3.12 host, the 361-tick full-population comparison gave:

| Operation | Before | After | Speedup |
| --- | ---: | ---: | ---: |
| Tick, mean | 176.46 ms | 88.86 ms | 1.99× |
| Snapshot, mean | 41.63 ms | 14.19 ms | 2.93× |
| Sort 60,000 firms by cash, median | 839.05 ms | 8.60 ms | 97.56× |
| Sort 60,000 firms by equity, median | 858.09 ms | 12.84 ms | 66.85× |

All 155 world arrays, ledgers, stats and snapshots matched the pre-pass working
tree at tick zero and every one of the 361 ticks. Separate checks covered live
configuration, player controls, multiple machines, checkpoint resume, research
pricing and the no-Numba fallback. These are local measurements; results vary
with hardware, configuration and machine load.
