"""Determinism + economic-invariant tests for the Python kernel."""
from __future__ import annotations

import numpy as np

from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel.tick import tick


def _run(seed, ticks, cfg_overrides):
    cfg = dict(cfg_overrides)
    cfg['seed'] = seed
    cfg, W = reset_world(cfg)
    for t in range(1, ticks + 1):
        tick(W, cfg, t, state={})
    return cfg, W


def _arrays_equal(a, b):
    return np.array_equal(a, b, equal_nan=True)


def test_determinism():
    cfg = {'endUserCount': 300, 't2FirmCount': 500}
    _, W1 = _run(12345, 35, cfg)
    _, W2 = _run(12345, 35, cfg)
    for name in W1.array_names:
        assert _arrays_equal(getattr(W1, name), getattr(W2, name)), f'determinism divergence in {name}'
    assert W1.t2LineCount == W2.t2LineCount
    assert W1.costSinks == W2.costSinks and W1.equipmentSinks == W2.equipmentSinks
    print('determinism: ok (35 ticks, all arrays byte-identical)')


def _check_invariants(cfg, W):
    # No negative inventory / cash.
    for name in ('t0Inv', 'raw', 't1Fin', 't2Raw', 't2T1Raw', 't2Fin',
                 't0Cash', 't1Cash', 't2Cash'):
        arr = getattr(W, name)
        if arr.size and arr.min() < 0:
            raise AssertionError(f'negative {name}: min={arr.min()}')
    # Reliability in [0, 1].
    for name in ('t0Rel', 't1Rel', 't2Rel'):
        arr = getattr(W, name)
        finite = arr[np.isfinite(arr)]
        if finite.size and (finite.min() < -1e-12 or finite.max() > 1 + 1e-12):
            raise AssertionError(f'rel out of range {name}: [{finite.min()}, {finite.max()}]')
    # Difficulty within bounds.
    assert cfg['dmin'] - 1e-12 <= W.difficulty.min() and W.difficulty.max() <= cfg['dmax'] + 1e-12


def test_invariants_conservation():
    cfg_overrides = {'endUserCount': 300, 't2FirmCount': 500}
    cfg, W = reset_world(dict(cfg_overrides, seed=12345))

    def total_cash():
        n2 = cfg['t2FirmCount']
        return float(W.t0Cash.sum() + W.t1Cash.sum() + W.t2Cash[:n2].sum())

    for t in range(1, 31):
        before = total_cash()
        state = tick(W, cfg, t, state={})
        after = total_cash()
        expected = state['consumerPayments'] - state['costSinks'] - state['equipmentSinks']
        diff = (after - before) - expected
        if abs(diff) > 1e-6 * max(1.0, abs(expected)):
            raise AssertionError(f'conservation violation at tick {t}: Δcash={after-before} '
                                 f'expected={expected} diff={diff}')
    _check_invariants(cfg, W)
    print('invariants: ok (30 ticks — no negatives, conservation holds, atomic orders)')


if __name__ == '__main__':
    test_determinism()
    test_invariants_conservation()
