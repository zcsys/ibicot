# Midbridge Colony

An economic simulation of a manufacturing colony in 4263. Extractors, refineries, and manufacturers trade physical inventory; one million simulated distributors provide final demand. Companies share finite cash and storage across their machines, choose suppliers, and adjust prices from trading results.

The Python backend owns the simulation. The browser is a dashboard and control surface. This README describes the running system; the [design canon](docs/design_canon.md) specifies its calculations from the implementation.

## The economy

**Tier is a business role; complexity is a product's raw ancestry and storage footprint.** Every recipe produces one item. A C4 item occupies four storage units, even when its immediate recipe has only two ingredients.

| Tier | Role | Default population | Activity |
| --- | --- | ---: | --- |
| T−1 | Gaia | 1 identity | Origin of four raw resources; no trading agent |
| T0 | Extraction | 20 companies, 40 element machines | Extract Organics, Inorganics, Metals, and Radioactives; sell raw to T1 |
| T1 | Refining | 1,008 companies | 72 per material; make four C1 and ten C2 materials directly from raw |
| T2 | Manufacturing | 57,960 companies | Make 36 invented C3 and 69 invented C4 products; buy T1 materials and, for some C4 recipes, C3 goods |
| T3 | Distribution | 1,000,000 buyers | Buy and consume invented T2 goods; external spending funds the economy |

The full catalog contains 269 recipes: 14 T1 materials and 255 T2 products. Only 105 T2 products are invented and tradable; 150 remain catalog entries. C5 is inactive. Bots start with one machine each in T1/T2 and do not automatically expand.

A tick updates extraction difficulty, extracts raw, buys T1 inputs, refines, updates T0/T1 quotes, clears distributor purchases, then buys and manufactures C3 followed by C4. It ends with observation, reliability, switching-fee adaptation, rent, and earnings. Distributors buy **opening T2 stock**; C4 factories can buy **fresh C3 production** in the same tick. There are 30 ticks per month and 360 per year.

## Core calculations

| Mechanism | Implemented rule |
| --- | --- |
| Storage | T1/T2 goods space = storage − installed machinery footprint. Half is allocated to recipe-weighted inputs, half equally to output lines. |
| T1 buying | Fill raw-input slots in lots of 1,000, capped by cash, stock, and space. |
| T2 buying | Input request = min(slot shortage, space, `slot / (1 + (price / reference cost)²)`), then whole-unit cash/stock limits. |
| Production | Whole batches bounded by capacity, finished-stock target, ingredients, conversion cash, and estimated net margin. T0 has its own proportional extraction allocator. |
| Conversion | `$0.25 × max(1, complexity − 1)` per output item. |
| Sales | Posted seller quote × delivered units; seller recognizes inventory book cost as COGS. |
| Distributor demand | `20 / (1 + (price / buyer halving-price)^elasticity)`, stochastically rounded; five sampled offers plus the incumbent by default. |
| Switching | A fixed transfer to the former supplier when it can fill the relevant order; actual-fill savings must justify switching. |
| Prices | Staggered observation windows; shortages, market quotes, then changes in realized gross profit determine movement. |
| Earnings | Sales − COGS + switching income − switching expense − accrued rent. |

The [canon](docs/design_canon.md) defines reference costs, exact rounding, supplier selection, settlement order, production gates, allocation, and exceptions. A reference cost is a calibration value; it is neither the live purchase quote nor the inventory book cost.

## Run

Use Python 3.12 and Node.js for the browser-side checks. Install the local Python dependencies once:

```sh
python3.12 -m pip install --target .pydeps 'numpy<2.5' numba fastapi uvicorn
./run.sh serve
```

The launcher prefers the macOS framework Python 3.12, falling back to `python3`; set `ECONOMY_PY` to choose another interpreter. It sets the local dependency path, warms the compiler, and opens [the dashboard](http://127.0.0.1:8000/index.html). One server owns one shared world; reconnecting a browser does not reset it.

```sh
# Full-population headless month and checkpoint pair (.npz + .json).
./run.sh run --seed 137 --ticks 30 --out /tmp/midbridge

# Small execution fixture, not a proportionally scaled economy.
./run.sh run --ticks 30 --cfg '{"distributorCount":500,"t2FirmCount":1000}'

# Per-tick statistics and company history in a chosen output directory.
./run.sh run --ticks 360 --stats /tmp/midbridge-run/ticks.jsonl

# Configure a dashboard world at startup.
ECONOMY_CFG='{"distributorCount":500,"t2FirmCount":1000}' ./run.sh serve
```

Reduced T2 populations take a prefix of the product allocation; distributor routing still covers the full invented set. Use reduced worlds for execution tests, not conclusions about market balance. Unknown configuration keys are ignored: use `distributorCount`, not historical buyer-count aliases.

The server pauses at 7,200 ticks by default (one generation); `ECONOMY_MAX_TICK=0` removes that limit. Checkpoints can be saved/loaded through `/checkpoint/save` and `/checkpoint/load`; incompatible catalog revisions are rejected. The dashboard supports company inspection, manual prices, and eligible equipment purchases.

## Repository map

| Location | Responsibility |
| --- | --- |
| [economy/core](economy/core) | Catalog adapter, configuration, state, recipes, randomness, supplier selection, accounting |
| [economy/kernel](economy/kernel) | Tick sequence, markets, production, Python reference and Numba execution paths |
| [economy/server](economy/server) | Shared runtime, scheduling, snapshots, recording, checkpoints, HTTP/WebSocket service |
| [web](web) | Dashboard, company controls, financial presentation, generated catalog |
| [catalogs/midbridge-4263](catalogs/midbridge-4263) | Recipe universe, fixed invented selection, names, runtime metadata, calibration data |
| [tests](tests) | Economic invariants, execution parity, storage, procurement, accounting, persistence, and UI calculations |
| [tools](tools) | Catalog validation/generation, run review, recovery, and performance measurement |

Configuration defaults are in [config.py](economy/core/config.py), with topology and derived economics in [model.py](economy/core/model.py). Catalog template fields do not override those runtime calculations. Rebuild the browser catalog with `python3 tools/build_midbridge_web.py` after changing its inputs.

## Verify

```sh
./run.sh test

# Broader Python discovery, including recursive demand and catalog tests.
PYTHONPATH=.pydeps:. python3.12 -W ignore -m unittest discover -s tests/py -p 'test_*.py'

# Validate the complete recipe universe without rewriting it.
python3.12 tools/build_recursive_catalog.py
```

`./run.sh test` runs a selected Python suite and both JavaScript checks; it is not full Python discovery. Performance tooling is available through `./run.sh bench --help`.

Read the [design canon](docs/design_canon.md) for implemented economic rules, [CONTRIBUTING.md](CONTRIBUTING.md) for contributor workflow, and [versioning](docs/versioning.md) for version policy. The [LandLord Alchemy archive](docs/landlord-alchemy/README.md) preserves earlier source material; it does not define current mechanics.
