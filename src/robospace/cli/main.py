"""Headless entry point: run N ticks from a seed/config and dump state, or serve.

Usage:
  python -m robospace.cli.main run --seed 12345 --ticks 360 \
      --cfg '{"endUserCount":500,"t2FirmCount":1000}' --out /tmp/ckpt
  python -m robospace.cli.main serve --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import argparse
import json
import time

from ..core.config import normalize_config
from ..core.state import reset_world
from ..kernel.tick import tick
from ..server.persistence import save_checkpoint


def _summary(W, cfg, t):
    n2 = cfg['t2FirmCount']
    print(f'tick {t}: t2LineCount={W.t2LineCount} '
          f't0Cash={float(W.t0Cash.sum()):.2f} t1Cash={float(W.t1Cash.sum()):.2f} '
          f't2Cash={float(W.t2Cash[:n2].sum()):.2f} '
          f'costSinks={W.costSinks:.4f}')


def run_headless(seed, ticks, cfg_overrides, out):
    cfg = dict(cfg_overrides)
    cfg['seed'] = seed
    cfg, W = reset_world(cfg)
    state = {}
    t0 = time.time()
    for t in range(1, ticks + 1):
        tick(W, cfg, t, state=state)
        if ticks <= 20 or t % 30 == 0 or t == ticks:
            _summary(W, cfg, t)
    elapsed = time.time() - t0
    print(f'ran {ticks} ticks in {elapsed:.1f}s ({ticks / elapsed:.2f} ticks/s)')
    if out:
        save_checkpoint(out, cfg, ticks, W, state)
        print(f'checkpoint written to {out}.npz / {out}.json')
    return cfg, W


def main():
    ap = argparse.ArgumentParser(prog='robospace')
    sub = ap.add_subparsers(dest='cmd', required=True)

    r = sub.add_parser('run', help='run N ticks headless')
    r.add_argument('--seed', type=int, default=12345)
    r.add_argument('--ticks', type=int, default=1)
    r.add_argument('--cfg', type=str, default='{}')
    r.add_argument('--out', type=str, default=None)

    s = sub.add_parser('serve', help='run the FastAPI/WebSocket service')
    s.add_argument('--host', default='127.0.0.1')
    s.add_argument('--port', type=int, default=8000)

    args = ap.parse_args()
    if args.cmd == 'run':
        run_headless(args.seed, args.ticks, json.loads(args.cfg), args.out)
        return
    # serve
    import uvicorn
    from ..server.service import app
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
