"""Checkpoint save/load — byte-identical round-trip.

A checkpoint is ``(config, tick, WorldState arrays, scalars)``.  Arrays are
stored uncompressed in a NumPy ``.npz`` (raw bytes, so they round-trip exactly);
config/tick/scalars go in a JSON sidecar.  See
``docs/design_canon.md`` §8.
"""
from __future__ import annotations

import json
import os

import numpy as np

from ..core.config import normalize_config
from ..core.state import WorldState


def save_checkpoint(path, cfg, tick, world, scalars=None):
    """Save ``cfg``/``tick``/``world`` to ``path`` (a ``.npz`` stem, e.g. ``/x/ckpt``)."""
    scalars = scalars or {}
    arr = {name: getattr(world, name) for name in world.array_names}
    np.savez(path + '.npz', **arr)
    meta = {
        'format': 'economy-checkpoint',
        'version': 1,
        'tick': int(tick),
        'cfg': cfg,
        'scalars': {'t2LineCount': int(world.t2LineCount),
                    'costSinks': float(world.costSinks),
                    'equipmentSinks': float(world.equipmentSinks),
                    'lm1': float(world.lm1),
                    'lm2': [float(x) for x in world.lm2],
                    'lm3': float(world.lm3),
                    'aov1': float(world.aov1),
                    'aov2': [float(x) for x in world.aov2],
                    'aov3': float(world.aov3),
                    **{k: v for k, v in scalars.items()}},
    }
    with open(path + '.json', 'w') as f:
        json.dump(meta, f)
    return path


def load_checkpoint(path):
    """Return ``(cfg, tick, world, scalars)``, rebuilding a WorldState with exact arrays."""
    with open(path + '.json') as f:
        meta = json.load(f)
    assert meta['format'] == 'economy-checkpoint', 'unsupported checkpoint format'
    # JSON turns the int keys of nested config mappings (t2Machinery, t2Capacity,
    # footprint, loyaltyMultiple) into strings — re-normalize to restore them.
    cfg = normalize_config(meta['cfg'])
    tick = meta['tick']
    scalars = meta['scalars']
    world = WorldState(cfg)
    with np.load(path + '.npz') as data:
        for name in world.array_names:
            getattr(world, name)[:] = data[name]
    world.t2LineCount = int(scalars['t2LineCount'])
    world.costSinks = float(scalars['costSinks'])
    world.equipmentSinks = float(scalars['equipmentSinks'])
    # adaptive loyalty regime (backward-compatible with pre-EMA checkpoints)
    world.lm1 = float(scalars.get('lm1', world.lm1))
    world.lm2[:] = [float(x) for x in scalars.get('lm2', world.lm2)]
    world.lm3 = float(scalars.get('lm3', world.lm3))
    world.aov1 = float(scalars.get('aov1', world.aov1))
    world.aov2[:] = [float(x) for x in scalars.get('aov2', world.aov2)]
    world.aov3 = float(scalars.get('aov3', world.aov3))
    return cfg, tick, world, scalars


def checkpoint_roundtrip_identical(cfg, world):
    """Helper: verify save→load reproduces every array byte-for-byte."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'ckpt')
        save_checkpoint(p, cfg, 0, world)
        cfg2, tick2, W2, _ = load_checkpoint(p)
    assert tick2 == 0
    for name in world.array_names:
        if not np.array_equal(getattr(world, name), getattr(W2, name), equal_nan=True):
            return False
    return W2.t2LineCount == world.t2LineCount and W2.costSinks == world.costSinks and W2.equipmentSinks == world.equipmentSinks
