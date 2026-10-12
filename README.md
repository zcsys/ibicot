# Midbridge Colony — Economy Kernel

A deterministic, fair-market simulation of a physical-goods supply chain, driven
by autonomous firms and entered by players on equal footing. This repository is
the authoritative server-side **economy kernel** in **Python (NumPy + Numba)**,
with a live browser dashboard.

The [design canon](docs/design_canon.md) is the source of truth for mechanics;
read it alongside [Midbridge integration](docs/midbridge-integration.md) for the
current model. The [versioning & milestones note](docs/versioning.md) pins the
PoC, prototype, and MVP gates and the MVP product checklist.

**Naming.** Display names follow the approved [complete naming catalog](docs/midbridge_complete_naming_catalog.md)
and [JSON source](docs/midbridge_complete_naming_catalog.json). Every T1/T2 company
uses its sector's activity-based stem and its existing global hexadecimal number.
Regenerate runtime names with `python3 tools/build_naming_metadata.py`, then browser
metadata with `PYTHONPATH=.pydeps:. python3 tools/build_midbridge_web.py`.
See [naming integration](docs/naming-integration.md) for compatibility and verification.

## Quickstart

```sh
./run.sh serve             # start the Python backend AND open the browser dashboard
./run.sh run --ticks 360   # headless run (append --stats path to write a JSONL log)
./run.sh test              # run the curated Python test subset
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

The current fresh-world defaults use the invented-recipe catalog below. Runtime
population overrides must be read from the particular run's configuration.

| Tier | Who | Default count |
| --- | --- | --- |
| **T0 — Resource Companies** | extract the four raw elements | 20 companies |
| **T1 — Refineries** | 14 refined materials (4 C1 basic + 10 C2 compound) | 1,008 firms |
| **T2 — Manufacturers** | 105 invented products, complexity C3 / C4 | 57,960 firms |
| **T3 — Distributors** | buy final goods | 1,000,000 firms |

Time is a **30-tick month**, a **360-tick year**, and a **7,200-tick generation**
(20 years). The active T2 catalog contains 36 C3 and 69 C4 products. Reversed
product-count shares give 38,088 C3 companies (1,058 per product) and 19,872 C4
companies (288 per product). **C5 is inactive.** The full recipe universe and
invented selection are distinct; see [current integration rules](docs/midbridge-integration.md).

## Key mechanisms

- **Deterministic** — SplitMix32 RNG; identical `(seed, config)` ⇒ byte-identical state.
- **Execution order** — reset/environment → T0 extraction → T1 purchase/production →
  T0/T1 pricing → Distributor purchases from opening T2 inventory → T2 C3 then C4
  buying/production/pricing → observation/reliability → expansion/loyalty → rent/earnings.
- **Derivative-following pricing** — firms walk their price against realised profit and
  hold at the flat optimum; a 2 % dead band prevents overshoot.
- **Margin-ramp production** — a producer throttles manufacturing by estimated net margin, including eligible storage expense and forecast switching income/expense
  (`productionMarginBand = 0.05`): full output at ≥ 5 % margin, tapering to 0 at
  break-even; reduced batches must cover allocated overhead. Purchasing is
  price-sensitive: latent demand is "fill to brim" (the input slot, half the goods
  space divided among distinct inputs), and the actual request follows the Tier 3
  curve with the input's reference cost as the halving price (elasticity 2), so a
  firm buys less as the quoted price rises past reference.
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
    tick.py               #   tick orchestration and reference execution
    numba.py              #   @njit fast path, byte-identical to tick.py
  server/
    runtime.py            #   KernelRuntime (step/pause/publish, stats)
    service.py            #   FastAPI + WebSocket service
    scheduler.py          #   tick scheduling for the dashboard
    persistence.py        #   checkpoint save/load (byte-identical round-trip)
  cli/main.py             #   headless `run` / `serve` entry point
web/                      # the browser dashboard (served by the backend)
  index.html  app.js  transport.js  catalog.js
docs/design_canon.md      # the design rulebook (source of truth)
docs/landlord-alchemy/    # sibling "Landlord Alchemy" design artefact
tools/dump_catalog.js     # one-time catalog extractor (web/catalog.js → JSON)
tests/                    # Python tests (RNG + determinism + invariants)
run.sh                    # launcher
```

The dashboard (`web/app.js`) speaks WebSocket to the backend through `web/transport.js`.

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

The benchmark uses the current defaults of 57,960 manufacturers and 1,000,000 distributors by
default. It measures steps, snapshot construction, JSON encoding, and company
queries separately. Compilation and state fingerprinting are excluded from the
steady-state timings. Comparison checks every world array, scalar ledger,
per-tick stats, snapshot, and sampled query result exactly; only elapsed-time
telemetry is excluded. Use `--cfg` for another population or parameter set.

The optimized kernel preserves sequential trade order, seeded draws, supplier
tie-breaks, and floating-point reduction order. It uses indexed stock searches,
direct uniform offer sampling, bounded storage planning, compiled refinery loops,
and shared snapshot projections. Manufacturer pages project only the requested
sort column. Broadcasts encode each message once, and the browser reuses locale
number formatters.

Compiled functions are cached under `economy/__pycache__/numba/` (or the configured
`NUMBA_CACHE_DIR`). The cache is keyed by all economy Python source and the
catalog, so dependency edits invalidate compiled callers as well. The first run
after a source change still compiles; later processes reuse the cache. Numba
remains optional, with Python/NumPy fallbacks.
