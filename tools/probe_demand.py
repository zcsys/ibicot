#!/usr/bin/env python3
"""Calibration probe for the demand scale (``tier2DemandFactor``).

The live generation showed *collapse-to-cogs*: ``tier2DemandFactor = 23`` is so
weak that T2 has no pricing power, its realised margin is squeezed to ~0 by
rising T1 input prices, the production gate idles ~99% of lines, and utilisation
sits at ~1.4% against the canon §5 target of 50–70%.

This script sweeps candidate values in short headless runs and reports, for each,
the equilibrium check the canon demands:

  * **utilisation** settles in the **50–70%** band (made / capacity), and
  * **prices plateau ABOVE unit cost** — no collapse-to-cogs (markup ≈ 1) and
    no spiral (monotonic ×N run-up).

Each candidate writes per-tick stats to a temp dir
(``/tmp/economy_probes/probe_factor<f>.jsonl``) and a summary there.

Usage (via ``./run.sh probe``):
  ./run.sh probe --factors 23,40,70,120,200 --ticks 720
  ./run.sh probe --factors 40 --ticks 360 --cfg '{"demandQtyMax":20}'
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

import numpy as np

from economy.core.config import default_cfg
from economy.core.state import reset_world
from economy.kernel.tick import tick as run_tick
from economy.server.runtime import stats_row

OUTDIR = Path(tempfile.gettempdir()) / 'economy_probes'
MONTH = 30

# Canon cost ladder: unit_cost = t2MaterialCost ($1.25) + conversion (0.25 × max(1, c−1)).
UNIT_COST = {3: 1.75, 4: 2.00, 5: 2.25}


def run_one(factor: float, ticks: int, seed: int, overrides: dict) -> tuple[list, float, Path]:
    cfg = default_cfg()
    cfg.update(overrides or {})
    cfg['seed'] = seed
    cfg['tier2DemandFactor'] = factor
    _, W = reset_world(cfg)
    state = {}
    rows = []
    t0 = time.time()
    for t in range(1, ticks + 1):
        run_tick(W, cfg, t, state=state)
        rows.append(stats_row(W, cfg, t, t // MONTH))
    elapsed = time.time() - t0
    path = OUTDIR / f'probe_factor{factor:g}.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')
    return rows, elapsed, path


def summarize(rows: list, factor: float) -> dict:
    r = rows[-1]
    active = r['consumersActive'] or 0
    s = {
        'factor': factor, 'tick': r['tick'], 'year': r['year'], 'month': r['month'],
        't0Price': r['t0Price'], 't1Price': r['t1Price'],
        'consumersActive': r['consumersActive'], 'consumersFulfilled': r['consumersFulfilled'],
        'fillRate': round((r['consumersFulfilled'] / active) if active else 0.0, 4),
    }
    half = max(1, len(rows) // 2)
    for c in (3, 4, 5):
        price = r.get(f'c{c}Price')
        util = r.get(f'c{c}Util')
        s[f'c{c}Price'] = price
        s[f'c{c}Util'] = util
        s[f'c{c}Markup'] = round(price / UNIT_COST[c], 3) if price else None
        early = [x[f'c{c}Price'] for x in rows[:half] if x.get(f'c{c}Price') is not None]
        late = [x[f'c{c}Price'] for x in rows[half:] if x.get(f'c{c}Price') is not None]
        s[f'c{c}Trend'] = round(float(np.mean(late) - np.mean(early)), 3) if early and late else None
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description='Sweep tier2DemandFactor and check equilibrium.')
    ap.add_argument('--factors', type=str, default='23,40,70,120,200',
                    help='comma-separated tier2DemandFactor candidates (default %(default)s)')
    ap.add_argument('--ticks', type=int, default=720, help='ticks per run; 720 = 2 years')
    ap.add_argument('--seed', type=int, default=12345)
    ap.add_argument('--cfg', type=str, default='{}', help='extra config JSON applied to every run')
    args = ap.parse_args()

    factors = [float(x) for x in args.factors.split(',') if x.strip() != '']
    overrides = json.loads(args.cfg)
    summaries = []
    print(f'{"factor":>8} {"tick":>6} {"t1P":>7} {"c3P":>7} {"c3M":>6} {"c3U":>7} {"c3Δ":>7} '
          f'{"c4P":>7} {"c4M":>6} {"c4U":>7} {"c5P":>7} {"c5M":>6} {"c5U":>7} {"fill":>7} {"s/tick":>8}')
    first = True
    for f in factors:
        if first:
            print(f'  (first run compiles the Numba JIT — ~10 s one-time)')
            first = False
        rows, elapsed, path = run_one(f, args.ticks, args.seed, overrides)
        s = summarize(rows, f)
        summaries.append(s)
        rate = args.ticks / elapsed if elapsed > 0 else float('nan')
        def g(k, w=7):
            v = s.get(k)
            return (f'{v:>{w}.3f}') if isinstance(v, (int, float)) else (f'{v!s:>{w}}')
        print(f'{s["factor"]:>8g} {s["tick"]:>6} {g("t1Price")} {g("c3Price")} {g("c3Markup", 6)} {g("c3Util")} '
              f'{g("c3Trend")} {g("c4Price")} {g("c4Markup", 6)} {g("c4Util")} {g("c5Price")} {g("c5Markup", 6)} {g("c5Util")} '
              f'{g("fillRate")} {rate:>8.3f}')
        print(f'    -> {path}')

    OUTDIR.mkdir(parents=True, exist_ok=True)
    with open(OUTDIR / 'summary.json', 'w') as f:
        json.dump(summaries, f, indent=2)
    print(f'\nsummary: {OUTDIR / "summary.json"}')
    print('Legend: cNM = price / unit cost (1.00 = collapse-to-cogs); '
          'cNU = made/capacity (target 0.50–0.70); cNΔ = price change 2nd-vs-1st half (≈0 = plateau).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
