"""Finite-float sum matching the supported CPython 3.12 reference runtime.

Compensated summation follows the Neumaier recurrence used by builtin sum in
CPython 3.12 (Python/bltinmodule.c). It is not a replacement for math.fsum.
"""
import math
from .jit import njit


@njit
def add(total, correction, value):
    following = total+value
    if abs(total) >= abs(value):
        correction += (total-following)+value
    else:
        correction += (value-following)+total
    return following, correction


@njit
def finish(total, correction):
    return total+correction if correction != 0. and math.isfinite(correction) else total
