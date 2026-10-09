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
    cfg = meta['cfg']
    tick = meta['tick']
    scalars = meta['scalars']
    world = WorldState(cfg)
    with np.load(path + '.npz') as data:
        for name in world.array_names:
            getattr(world, name)[:] = data[name]
    world.t2LineCount = int(scalars['t2LineCount'])
    world.costSinks = float(scalars['costSinks'])
    world.equipmentSinks = float(scalars['equipmentSinks'])
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
