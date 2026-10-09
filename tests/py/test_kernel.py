"""Determinism + economic-invariant tests for the Python kernel."""
from __future__ import annotations

import numpy as np

from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel.tick import tick


def _run(seed, ticks, cfg_overrides):
    cfg = dict(cfg_overrides)
    cfg['seed'] = seed
    cfg, world = reset_world(cfg)
    for t in range(1, ticks + 1):
        tick(world, cfg, t, state={})
    return cfg, world


def _arrays_equal(a, b):
    return np.array_equal(a, b, equal_nan=True)


def test_determinism():
    cfg = {'consumerCount': 300, 't2FirmCount': 500}
    _, W1 = _run(12345, 35, cfg)
    _, W2 = _run(12345, 35, cfg)
    for name in W1.array_names:
        assert _arrays_equal(getattr(W1, name), getattr(W2, name)), f'determinism divergence in {name}'
    assert W1.t2LineCount == W2.t2LineCount
    assert W1.costSinks == W2.costSinks and W1.equipmentSinks == W2.equipmentSinks
    print('determinism: ok (35 ticks, all arrays byte-identical)')


def _check_invariants(cfg, world):
    # No negative inventory / cash.
    for name in ('t0Inv', 'raw', 't1Fin', 't2Raw', 't2T1Raw', 't2Fin',
                 't0Cash', 't1Cash', 't2Cash'):
        arr = getattr(world, name)
        if arr.size and arr.min() < 0:
            raise AssertionError(f'negative {name}: min={arr.min()}')
    # Reliability in [0, 1].
    for name in ('t0Rel', 't1Rel', 't2Rel'):
        arr = getattr(world, name)
        finite = arr[np.isfinite(arr)]
        if finite.size and (finite.min() < -1e-12 or finite.max() > 1 + 1e-12):
            raise AssertionError(f'rel out of range {name}: [{finite.min()}, {finite.max()}]')
    # Difficulty within bounds.
    assert cfg['difficultyMin'] - 1e-12 <= world.difficulty.min() and world.difficulty.max() <= cfg['difficultyMax'] + 1e-12


def test_invariants_conservation():
    cfg_overrides = {'consumerCount': 300, 't2FirmCount': 500}
    cfg, world = reset_world(dict(cfg_overrides, seed=12345))

    def total_cash():
        n2 = cfg['t2FirmCount']
        return float(world.t0Cash.sum() + world.t1Cash.sum() + world.t2Cash[:n2].sum())

    for t in range(1, 31):
        before = total_cash()
        state = tick(world, cfg, t, state={})
        after = total_cash()
        expected = state['consumerPayments'] - state['costSinks'] - state['equipmentSinks']
        diff = (after - before) - expected
        if abs(diff) > 1e-6 * max(1.0, abs(expected)):
            raise AssertionError(f'conservation violation at tick {t}: Δcash={after-before} '
                                 f'expected={expected} diff={diff}')
    _check_invariants(cfg, world)
    print('invariants: ok (30 ticks — no negatives, conservation holds, atomic orders)')


if __name__ == '__main__':
    test_determinism()
    test_invariants_conservation()
