"""RNG unit tests — reproduce known JS SplitMix32 outputs.

Run with the bundled/system Python and PYTHONPATH=src.
"""
from __future__ import annotations

import math

from robospace.core import rng

# Known outputs captured from the canon (spec/design_canon.md) / the worker.
MIX_KNOWN = [(0, 0), (1, 1364076727), (0xFFFFFFFF, 2180083513)]
RANDOM_KNOWN = [
    (12345, 0, 0, 0.22878044145181775),
    (12345, 0, 1, 0.4922519912943244),
    (12345, 10, 0, 0.1413302756845951),
    (12345, 360, 2000000, 0.9110971931368113),
]
HASH_KNOWN = [
    (12345, 0, 2679938182),
    (12345, 8000000, 2300826879),
    (12345, 9000000, 457148917),
    (12345, 10000000, 975972688),
]
NORMAL_KNOWN = [
    (12345, 0, 0, -1.7155171828879556),
    (12345, 0, 4, 1.4050627417483728),
    (12345, 5, 8, -0.9415581312973661),
    (12345, 360, 12, 0.5104708199948276),
]


def test_mix():
    for x, expected in MIX_KNOWN:
        assert rng.mix(x) == expected, f'mix({x}) = {rng.mix(x)} != {expected}'


def test_random():
    for seed, tick, stream, expected in RANDOM_KNOWN:
        got = rng.random_(seed, tick, stream)
        assert got == expected, f'random_({seed},{tick},{stream}) = {got!r} != {expected!r}'


def test_hash_seed():
    for seed, k, expected in HASH_KNOWN:
        assert rng.hash_seed(seed, k) == expected, f'hash_seed({seed},{k}) = {rng.hash_seed(seed,k)} != {expected}'


def test_normal():
    for seed, tick, stream, expected in NORMAL_KNOWN:
        got = rng.normal_(seed, tick, stream)
        assert math.isclose(got, expected, rel_tol=1e-12, abs_tol=1e-12), \
            f'normal_({seed},{tick},{stream}) = {got!r} != {expected!r}'


if __name__ == '__main__':
    test_mix()
    test_random()
    test_hash_seed()
    test_normal()
    print('rng tests: ok')
