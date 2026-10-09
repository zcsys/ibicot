# Robotic Space Generation — economy kernel

An **emergent, fair-market simulation of a physical-goods supply chain**, run by
autonomous agents and entered by players on equal footing. This repository is
the authoritative server-side **economy kernel** in **Python (NumPy + Numba)**
with a browser dashboard.

The design rulebook is [`docs/design_canon.md`](docs/design_canon.md) — it is the
single source of truth for *what* the economy is. Everything else here implements
it.

## Quickstart

```sh
./run.sh serve            # start the Python backend AND open the browser dashboard
./run.sh run --ticks 360  # headless run (write a checkpoint with --out /tmp/ckpt)
./run.sh test             # run the Python test suite
```

`serve` starts FastAPI + WebSocket on `http://127.0.0.1:8000`, serves the
dashboard at `/index.html`, and opens it in the browser. Edit parameters and use
**Run / Run Max / Pause / Step / Reset / Apply Params** — the Python kernel is the
world. The first load resets to full population (~6 s).

The launcher requires Python 3.12 with NumPy (Numba and FastAPI are installed to
`.pydeps/`, which is git-ignored). See the install hint the launcher prints if
`.pydeps/` is missing.

## Layout

```
economy/                  # the Python kernel
  core/                   #   catalogue + canon parameters, config, RNG, WorldState
  kernel/                 #   the 9-phase tick (tick.py) + Numba fast path (fast.py)
  server/                 #   runtime, FastAPI/WebSocket service, persistence
  cli/                    #   headless `run` / `serve` entry point
web/                      # the browser dashboard (served by the backend)
  index.html  app.js  catalogue.js  bridge.js
docs/design_canon.md      # the design rulebook (single source of truth)
tests/                    # Python tests (RNG, determinism, invariants)
tools/dump_catalogue.js   # one-time catalogue extractor (web/catalogue.js -> JSON)
run.sh                    # launcher
```

The dashboard (`web/app.js`) talks to the backend over WebSocket through
`web/bridge.js`, which re-implements the browser `Worker` interface so the UI
code is unchanged.

## Settled parameters

These are the target parameters (see [`docs/design_canon.md`](docs/design_canon.md)
for the full rationale). The demand-side *scale* is calibration, not frozen.

| Area | Value |
| --- | --- |
| **Tiers** | T0 extraction → T1 refining → T2 manufacturing → T3 consumers |
| **Elements** | Water, Earth, Fire, Air |
| **T0 firms** | 20 (element-coverage spectrum: 2 all / 4 three / 6 two / 8 single) |
| **T1 products / firms** | 10 (4 C-1 basic + 6 C-2 compound) × 100 = 1,000 firms |
| **T2 products** | 200 invented: 2 C-3 + 6 C-4 + 12 C-5 per sector × 10 sectors |
| **T2 firms** | **60,000 single-machine firms** (reverse 6:3:1 ratio) |
| ↳ C-3 | 36,000 = 20 products × **1,800 firms/product** |
| ↳ C-4 | 18,000 = 60 products × **300 firms/product** |
| ↳ C-5 | 6,000 = 120 products × **50 firms/product** |
| **Consumers** | 1,000,000 |
| **Equity** | T0 = $75m ($22m license + $49m machinery + $1m reserve + $3m cash); every T1/T2 firm = $1.5m = $1m license + machinery + cash |
| ↳ T1 | license $1m + machinery $15k + cash $485k |
| ↳ T2 C-3 / C-4 / C-5 | $1m + $75k/$375k/$420k + $425k/$125k/$80k |
| **Machinery** | T1 flat $15k; T2 $75k / $375k / $420k |
| **Capacity** (per machine/tick) | T0 = 1,000,000; C-1/C-2 = 2,000; C-3 = 30; C-4 = 20; C-5 = 10 |
| **Recipes** | count-preserving (N inputs → N outputs) |
| **Material cost** | $1.25 (T1) / $1.875 (T2), flat per item (each already includes the upstream 0.25 markup) |
| **Conversion** | $0.25 × max(1, complexity−1) → 0.25 / 0.25 / 0.50 / 0.75 / 1.00 |
| **Unit cost** | $1.50 / $1.50 / $2.375 / $2.625 / $2.875 |
| **Storage** | T0 50,000,000 (fill to brim); T1/T2 20,000 firm-level pool; machinery footprint 1k/1k/3k/4k/5k; goods `G = 20,000 − machinery`; fill `G`; raw:finished = 1:1 |
| **Demand valuation** | `V = unit cost`; choke = `V × [1.8, 3.0]`; elasticity `η = 2` |
| **Latent demand** | `qmax = 15` fixed per consumer |
| **Markup** | flat 0.25 first-guess everywhere; the equilibrium markup is discovered by the pricer |
| **Input demand** | elastic (reversed T3 curve): `q = need × max(0, 1 − (cost/price)^η)`; 0 at/above break-even |
| **Loyalty / M** | switching charge `M × unit_cost × (1 + reliability)`: T1 = 500, T2 = 125, T3 = 0.5 |
| **Reliability** | `0.5 × price-stability + 0.5 × availability`, EMA `α = 0.15`, monthly |

**Deferred** (documented, not implemented): storage rent, machinery-as-good,
financing, advertising. **Calibration** (not frozen): the demand scale and
offer-sampling counts.

## How it runs

- **Deterministic**: SplitMix32 32-bit RNG; same `(seed, config, commands)` ⇒
  identical state every run.
- **9-phase tick** per tick: reset → environment (difficulty) → T0 extraction →
  T1 input purchase → T1 manufacture → pricing → T2 buy/make/price → end-user
  clearing → observe/reliability. Monthly reliability and the calendar follow the
  canon's 30-tick month.
- **Numba + vectorized RNG**: the hot phases (T1 purchase, T2 buy/make/price,
  end-user clearing, observation) are `@njit` in `kernel/fast.py`, and the
  SplitMix32 RNG has a bit-exact vectorized form (`rng.random_vec`); full-population
  steady state is ~0.14 s/tick.
- **Checkpoints**: `.npz` + JSON sidecar, byte-identical round-trip.

## Tests

```sh
./run.sh test
# tests/py/test_rng.py      SplitMix32 vs known outputs
# tests/py/test_kernel.py   determinism (byte-identical) + invariants (no
#                           negatives, conservation, atomic orders)
```
