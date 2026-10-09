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


def save_checkpoint(path, cfg, tick, W, scalars=None):
    """Save ``cfg``/``tick``/``W`` to ``path`` (a ``.npz`` stem, e.g. ``/x/ckpt``)."""
    scalars = scalars or {}
    arr = {name: getattr(W, name) for name in W.array_names}
    np.savez(path + '.npz', **arr)
    meta = {
        'format': 'economy-checkpoint',
        'version': 1,
        'tick': int(tick),
        'cfg': cfg,
        'scalars': {'t2LineCount': int(W.t2LineCount),
                    'costSinks': float(W.costSinks),
                    'equipmentSinks': float(W.equipmentSinks),
                    **{k: v for k, v in scalars.items()}},
    }
    with open(path + '.json', 'w') as f:
        json.dump(meta, f)
    return path


def load_checkpoint(path):
    """Return ``(cfg, tick, W, scalars)``, rebuilding a WorldState with exact arrays."""
    with open(path + '.json') as f:
        meta = json.load(f)
    assert meta['format'] == 'economy-checkpoint', 'unsupported checkpoint format'
    cfg = meta['cfg']
    tick = meta['tick']
    scalars = meta['scalars']
    W = WorldState(cfg)
    with np.load(path + '.npz') as data:
        for name in W.array_names:
            getattr(W, name)[:] = data[name]
    W.t2LineCount = int(scalars['t2LineCount'])
    W.costSinks = float(scalars['costSinks'])
    W.equipmentSinks = float(scalars['equipmentSinks'])
    return cfg, tick, W, scalars


def checkpoint_roundtrip_identical(cfg, W):
    """Helper: verify save→load reproduces every array byte-for-byte."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'ckpt')
        save_checkpoint(p, cfg, 0, W)
        cfg2, tick2, W2, _ = load_checkpoint(p)
    assert tick2 == 0
    for name in W.array_names:
        if not np.array_equal(getattr(W, name), getattr(W2, name), equal_nan=True):
            return False
    return W2.t2LineCount == W.t2LineCount and W2.costSinks == W.costSinks and W2.equipmentSinks == W.equipmentSinks
