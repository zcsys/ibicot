"""Reproducible full-population benchmark and exact behavior fingerprints.

Run with the launcher's Python/PYTHONPATH, e.g.:
  python tools/performance.py --ticks 361 --output /tmp/before.json
  python tools/performance.py --ticks 361 --verify /tmp/before.json --output /tmp/after.json

Timing excludes JIT warm-up and fingerprinting. Only wall-clock telemetry is
removed from snapshots; world arrays, scalar ledgers, stats and projections
are compared exactly. Use identical config, ticks and publish cadence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import tempfile
import time
from pathlib import Path

import numpy as np

from economy.server.runtime import KernelRuntime, stats_row


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def fingerprint(rt):
    arrays = {name: hashlib.sha256(value.tobytes()).hexdigest()
              for name, value in vars(rt.world).items() if isinstance(value, np.ndarray)}
    scalars = {name: value for name, value in vars(rt.world).items()
               if isinstance(value, (int, float))}
    snap = dict(rt.lastSnapshot)
    snap.pop('tps')
    snap['performance'] = {k: v for k, v in snap['performance'].items()
                           if k not in ('lastTickMs', 'averageTickMs')}
    return {'arrays': arrays, 'scalars': digest(scalars), 'state': digest(rt.state),
            'stats': digest(stats_row(rt.world, rt.cfg, rt.tick, rt.month)),
            'snapshot': digest(snap)}


def summarize(samples):
    return {'median_ms': statistics.median(samples) * 1000,
            'mean_ms': statistics.mean(samples) * 1000,
            'p95_ms': float(np.percentile(samples, 95)) * 1000}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ticks', type=int, default=60)
    parser.add_argument('--publish-every', type=int, default=1)
    parser.add_argument('--fingerprint-every', type=int, default=0,
                        help='also fingerprint every Nth tick (0: boundary checkpoints only)')
    parser.add_argument('--cfg', default='{}')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.ticks < 2 or args.publish_every < 1 or args.fingerprint_every < 0:
        parser.error('ticks must be >= 2, publish-every >= 1, and fingerprint-every >= 0')
    start = time.perf_counter()
    rt = KernelRuntime(json.loads(args.cfg))
    construction = time.perf_counter() - start
    checkpoints = {0: fingerprint(rt)}
    steps, publishes, serializes = [], [], []
    with tempfile.TemporaryDirectory() as tmp:
        rt.statsPath = Path(tmp) / 'stats.jsonl'
        for tick in range(1, args.ticks + 1):
            start = time.perf_counter()
            rt.step()
            elapsed = time.perf_counter() - start
            if tick == 1:
                first_step = elapsed
            else:
                steps.append(elapsed)
            if tick % args.publish_every == 0 or tick == args.ticks:
                start = time.perf_counter()
                snap = rt.publish()
                publishes.append(time.perf_counter() - start)
                start = time.perf_counter()
                json.dumps(snap)
                serializes.append(time.perf_counter() - start)
            if (tick in (1, 2, 13, 29, 30, 31, 60, 90, 180, 359, 360, 361) or tick == args.ticks
                    or (args.fingerprint_every and tick % args.fingerprint_every == 0)):
                checkpoints[tick] = fingerprint(rt)
            if tick % 30 == 0:
                print(f'tick {tick}: mean step {statistics.mean(steps)*1000:.2f} ms', flush=True)
        queries = {}
        for key in ('id', 'name', 'cash', 'equity', 'inventory', 'reliability'):
            rt.tier2Query['sort'] = key
            samples = []
            for _ in range(3):
                start = time.perf_counter()
                page = rt._tier2_page()
                samples.append(time.perf_counter() - start)
            queries[key] = {**summarize(samples), 'digest': digest(page)}
    result = {'config': rt.cfg, 'ticks': args.ticks, 'publish_every': args.publish_every,
              'fingerprint_every': args.fingerprint_every,
              'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                              'machine': platform.machine()},
              'construction_ms': construction * 1000, 'first_step_ms': first_step * 1000,
              'step': summarize(steps), 'publish': summarize(publishes),
              'json': summarize(serializes), 'queries': queries, 'checkpoints': checkpoints}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    if args.verify:
        before = json.loads(args.verify.read_text())
        after = json.loads(args.output.read_text())
        for key in ('config', 'ticks', 'publish_every', 'fingerprint_every', 'checkpoints'):
            assert before[key] == after[key], f'Behavior changed: {key}; compare {args.verify} and {args.output}'
        for key in queries:
            assert before['queries'][key]['digest'] == queries[key]['digest'], f'Query changed: {key}'
        print('Exact behavior fingerprints match.', flush=True)
    print(json.dumps({k: result[k] for k in ('step', 'publish', 'json', 'construction_ms', 'first_step_ms')}, indent=2))


if __name__ == '__main__':
    main()
