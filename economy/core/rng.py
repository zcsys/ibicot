"""SplitMix32 RNG primitives — bit-exact with the JS oracle.

All arithmetic is 32-bit unsigned.  ``MASK = 0xFFFFFFFF`` replaces
``Math.imul``/``>>> 0``.  See ``docs/design_canon.md`` §3.1 and
``docs/design_canon.md`` §5.

The pure-Python path is exact (arbitrary-precision integers).  The optional
Numba path uses explicit ``uint64`` for the multiply steps so it also wraps
mod 2^64 (and therefore yields the correct low 32 bits) with no reliance on
signed-overflow behaviour.
"""
from __future__ import annotations

import math

import numpy as _np

MASK = 0xFFFFFFFF


def _mix_impl(x: int) -> int:
    x &= MASK
    x = ((x ^ (x >> 16)) * 0x85EBCA6B) & MASK
    x = ((x ^ (x >> 13)) * 0xC2B2AE35) & MASK
    return (x ^ (x >> 16)) & MASK


def _random_impl(seed: int, tick: int, stream: int) -> float:
    x = ((seed & MASK) ^ (((tick + 1) & MASK) * 0x9E3779B1 & MASK)
         ^ (((stream + 1) & MASK) * 0x85EBCA6B & MASK)) & MASK
    return _mix_impl(x) / 4294967296.0


def _normal_impl(seed: int, tick: int, stream: int) -> float:
    r = _random_impl(seed, tick, stream)
    return math.sqrt(-2.0 * math.log(max(1e-12, r))) * math.cos(2.0 * math.pi * _random_impl(seed, tick, stream + 1))


def _hash_seed_impl(seed: int, k: int) -> int:
    # NB: the JS worker's hashSeed returns the raw u32 (NOT divided by 2**32).
    # The contract/design-doc text that shows a `/ 4294967296` is superseded by
    # the executable oracle (the canon machine contract (docs/design_canon.md §12) `hashSeed`).
    return _mix_impl((seed & MASK) ^ (((k + 1) & MASK) * 0x9E3779B1 & MASK))


mix = _mix_impl
random_ = _random_impl
normal_ = _normal_impl
hash_seed = _hash_seed_impl


# --------------------------------------------------------------------------
# Vectorized SplitMix32 (bit-exact with the scalar forms, for matrix work).
# --------------------------------------------------------------------------
_U64 = _np.uint64
_M64 = _U64(MASK)
_K1 = _U64(0x85EBCA6B)
_K2 = _U64(0xC2B2AE35)
_K3 = _U64(0x9E3779B1)


def mix_vec(x):
    x = _np.asarray(x, dtype=_np.uint64)
    with _np.errstate(over='ignore'):
        x = ((x ^ (x >> _U64(16))) * _K1) & _M64
        x = ((x ^ (x >> _U64(13))) * _K2) & _M64
    return (x ^ (x >> _U64(16))) & _M64


def random_vec(seed, tick, streams):
    streams = _np.asarray(streams, dtype=_np.uint64)
    x = (_U64(seed) & _M64) ^ (((_U64(tick) + _U64(1)) * _K3) & _M64) \
        ^ (((streams + _U64(1)) * _K1) & _M64)
    x &= _M64
    return mix_vec(x).astype(_np.float64) / 4294967296.0


def hash_seed_vec(seed, ks):
    """Vectorized ``hash_seed`` — returns the raw u32 (not divided by 2**32),
    bit-exact with ``_hash_seed_impl`` for every element of ``ks``."""
    ks = _np.asarray(ks, dtype=_np.uint64)
    x = (_U64(seed) & _M64) ^ (((ks + _U64(1)) * _K3) & _M64)
    x &= _M64
    return mix_vec(x)


try:  # optional acceleration
    import numpy as _np
    from numba import njit as _njit
    _U = _np.uint64
    _M64 = _np.uint64(MASK)
    _K1 = _np.uint64(0x85EBCA6B)
    _K2 = _np.uint64(0xC2B2AE35)
    _K3 = _np.uint64(0x9E3779B1)


    @_njit(cache=False)
    def _mix_u64(x):
        x = x & _M64
        x = ((x ^ (x >> 16)) * _K1) & _M64
        x = ((x ^ (x >> 13)) * _K2) & _M64
        return (x ^ (x >> 16)) & _M64


    @_njit(cache=False)
    def _random_u64(seed, tick, stream):
        x = (_U(seed) & _M64) ^ (((_U(tick) + 1) & _M64) * _K3 & _M64) ^ (((_U(stream) + 1) & _M64) * _K1 & _M64)
        return float(_mix_u64(x & _M64)) / 4294967296.0


    @_njit(cache=False)
    def _normal_u64(seed, tick, stream):
        r = _random_u64(seed, tick, stream)
        return math.sqrt(-2.0 * math.log(max(1e-12, r))) * math.cos(2.0 * math.pi * _random_u64(seed, tick, stream + 1))


    @_njit(cache=False)
    def _hash_seed_u64(seed, k):
        return _mix_u64((_U(seed) & _M64) ^ (((_U(k) + 1) & _M64) * _K3 & _M64))

    mix = _mix_u64
    random_ = _random_u64
    normal_ = _normal_u64
    hash_seed = _hash_seed_u64
except Exception:  # pragma: no cover - numba optional
    pass
