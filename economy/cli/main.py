"""Headless entry point: run N ticks from a seed/config and dump state, or serve.

Usage:
  python -m economy.cli.main run --seed 137 --ticks 360 \
      --cfg '{"consumerCount":500,"t2FirmCount":1000}' --out /tmp/ckpt
  python -m economy.cli.main serve --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from ..core.config import normalize_config
from ..core.model import MONTH
from ..core.state import reset_world
from ..kernel.tick import tick
from ..server.persistence import save_checkpoint
from ..server.runtime import stats_row


def _summary(world, cfg, t):
    n2 = cfg['t2FirmCount']
    print(f'tick {t}: t2LineCount={world.t2LineCount} '
          f't0Cash={float(world.t0Cash.sum()):.2f} t1Cash={float(world.t1Cash.sum()):.2f} '
          f't2Cash={float(world.t2Cash[:n2].sum()):.2f} '
          f'costSinks={world.costSinks:.4f}')


def run_headless(seed, ticks, cfg_overrides, out, stats_path=None):
    cfg = dict(cfg_overrides)
    cfg['seed'] = seed
    cfg, world = reset_world(cfg)
    state = {}
    stats_f = None
    if stats_path:
        Path(stats_path).parent.mkdir(parents=True, exist_ok=True)
        stats_f = open(stats_path, 'w')
    # Warm the Numba JIT with one throwaway tick before timing, so the reported
    # rate is steady-state rather than dominated by first-tick compilation.
    tick(world, cfg, 1, state=state)
    if stats_f is not None:
        stats_f.write(json.dumps(stats_row(world, cfg, 1, 1 // MONTH)) + '\n')
    t0 = time.time()
    for t in range(2, ticks + 1):
        tick(world, cfg, t, state=state)
        if stats_f is not None:
            stats_f.write(json.dumps(stats_row(world, cfg, t, t // MONTH)) + '\n')
        if ticks <= 20 or t % 30 == 0 or t == ticks:
            _summary(world, cfg, t)
    if stats_f is not None:
        stats_f.close()
        print(f'stats written to {stats_path}')
    elapsed = time.time() - t0
    timed = max(1, ticks - 1)
    print(f'ran {ticks} ticks in {timed / elapsed:.2f} ticks/s (steady-state, JIT warmed)')
    if out:
        save_checkpoint(out, cfg, ticks, world, state)
        print(f'checkpoint written to {out}.npz / {out}.json')
    return cfg, world


def main():
    ap = argparse.ArgumentParser(prog='economy')
    sub = ap.add_subparsers(dest='cmd', required=True)

    r = sub.add_parser('run', help='run N ticks headless')
    r.add_argument('--seed', type=int, default=137)
    r.add_argument('--ticks', type=int, default=1)
    r.add_argument('--cfg', type=str, default='{}')
    r.add_argument('--out', type=str, default=None)
    r.add_argument('--stats', type=str, default=None, metavar='PATH',
                   help='write per-tick economy stats as JSONL (optional)')

    s = sub.add_parser('serve', help='run the FastAPI/WebSocket service')
    s.add_argument('--host', default='127.0.0.1')
    s.add_argument('--port', type=int, default=8000)

    args = ap.parse_args()
    if args.cmd == 'run':
        run_headless(args.seed, args.ticks, json.loads(args.cfg), args.out, args.stats)
        return
    # serve
    import uvicorn
    from ..server.service import app
    # Warm the Numba JIT on a tiny bootstrap world (one-time ~10 s) so the first
    # browser connect / reset / run doesn't stall on compilation.  Numba compiles
    # on array dtype (not length), so this covers the full population too.
    from ..server.runtime import KernelRuntime
    print('Warming up the JIT (one-time)…', flush=True)
    KernelRuntime({'consumerCount': 100, 't2FirmCount': 200}).step()
    print('JIT ready.', flush=True)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
