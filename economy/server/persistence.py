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


def save_checkpoint(path, cfg, tick, world, scalars=None, runtime_metadata=None):
    """Save ``cfg``/``tick``/``world`` to ``path`` (a ``.npz`` stem, e.g. ``/x/ckpt``)."""
    scalars = scalars or {}
    arr = {name: getattr(world, name) for name in world.array_names}
    np.savez(path + '.npz', **arr)
    meta = {
        'format': 'economy-checkpoint',
        'version': 5,
        'tick': int(tick),
        'cfg': cfg,
        'runtime': runtime_metadata or {},
        'extras': {name: getattr(world, name).tolist() for name in
                   ('t2MatSpend', 't2MatOrders', 'loyaltySwitches', 'loyaltyPenalties')},
        'scalars': {**scalars, 'netEarningsAvailable': bool(world.netEarningsAvailable),
                    't2LineCount': int(world.t2LineCount),
                    'costSinks': float(world.costSinks),
                    'equipmentSinks': float(world.equipmentSinks),
                    'lm1': float(world.lm1),
                    'lm2': [float(x) for x in world.lm2],
                    'lm3': float(world.lm3),
                    'aov1': float(world.aov1),
                    'aov2': [float(x) for x in world.aov2],
                    'aov3': float(world.aov3)},
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
    # A pre-rent checkpoint keeps its original economics until explicitly changed.
    if meta.get('version', 1) < 3 and 'storageRentPerUnitYear' not in meta['cfg']:
        cfg['storageRentPerUnitYear'] = 0.0
    tick = meta['tick']
    scalars = meta['scalars']
    world = WorldState(cfg)
    with np.load(path + '.npz') as data:
        for name in world.array_names:
            if name not in data and meta.get('version', 1) < 4 and 'Switching' in name:
                continue
            if name not in data and meta.get('version', 1) < 3 and name in (
                    't1RentArrears', 't1RentPaid', 't2RentArrears', 't2RentPaid'):
                continue
            if name not in data and name in ('t1RentCharge', 't2RentCharge'):
                continue
            target, saved = getattr(world, name), data[name]
            if target.shape == saved.shape:
                target[:] = saved
            elif meta.get('version', 1) == 1 and name.startswith('t2') and (
                    name.startswith('t2Learn') or name in ('t2Demand', 't2DemandEMA')
                    or name.startswith('t2Line') or name in (
                        't2Fin', 't2FinBasis', 't2Price', 't2PlayerPrice', 't2UnitCost',
                        't2ReplacementCost', 't2SalesEMA', 't2Made', 't2Sold', 't2Revenue',
                        't2COGS', 't2Rel', 't2RelPriceSum', 't2RelPriceSamples',
                        't2RelAttempts', 't2RelAvailable', 't2MonthlyCapacity', 't2MonthSold')):
                count = min(len(target), len(saved))
                if count < int(scalars['t2LineCount']):
                    raise ValueError('Checkpoint does not contain all active production lines.')
                target[:count] = saved[:count]
            else:
                raise ValueError(f'Checkpoint array shape mismatch: {name}')
    world.t2LineCount = int(scalars['t2LineCount'])
    world.netEarningsAvailable = bool(scalars.get('netEarningsAvailable', False)) if meta.get('version', 1) >= 4 else False
    if meta.get('version', 1) < 5:
        # Earlier checkpoints may contain net or partially rent-adjusted learning
        # windows. Start a clean gross-profit baseline without altering accounting.
        for tier in ('t0', 't1', 't2'):
            for suffix in ('LearnProfit', 'LearnSales', 'LearnTicks', 'LearnDemand',
                           'LearnOpportunity', 'LearnPotentialOpportunity'):
                getattr(world, tier + suffix).fill(0)
            getattr(world, tier + 'LearnPrevious').fill(np.nan)
    world.costSinks = float(scalars['costSinks'])
    world.equipmentSinks = float(scalars['equipmentSinks'])
    # adaptive loyalty regime (backward-compatible with pre-EMA checkpoints)
    world.lm1 = float(scalars.get('lm1', world.lm1))
    world.lm2[:] = [float(x) for x in scalars.get('lm2', world.lm2)]
    world.lm3 = float(scalars.get('lm3', world.lm3))
    world.aov1 = float(scalars.get('aov1', world.aov1))
    world.aov2[:] = [float(x) for x in scalars.get('aov2', world.aov2)]
    world.aov3 = float(scalars.get('aov3', world.aov3))
    for name, values in meta.get('extras', {}).items():
        if name in ('t2MatSpend', 't2MatOrders', 'loyaltySwitches', 'loyaltyPenalties'):
            getattr(world, name)[:] = values
    scalars['runtimeMetadata'] = meta.get('runtime', {})
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
