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
Step / Reset / Apply Params** — the Python kernel is the world, and the first load
resets to full population (~6 s).

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
- **Margin-ramp input demand** — a producer throttles purchases by gross margin
  (`productionMarginBand = 0.05`): full output at ≥ 5 % margin, tapering to 0 at
  break-even, never producing at a loss.
- **Adaptive loyalty charge** — switching suppliers costs
  `M × unit_cost × (1 + reliability)`; `M` is re-derived once per year from an EMA of the
  observed average order value (`loyaltyEmaAlpha = 0.01`) so the charge tracks ~10 % of
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

## Tests

```sh
./run.sh test
# tests/py/test_rng.py      SplitMix32 against known reference outputs
# tests/py/test_kernel.py   determinism (byte-identical re-runs) + invariants
#                           (no negatives, conservation holds, atomic orders)
```
