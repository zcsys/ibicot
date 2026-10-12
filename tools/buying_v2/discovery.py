"""Bounded distinct discovery from an eligible, stable-ID sorted offer book."""
import numpy as np
from economy.core.rng import random_
from .jit import njit


@njit
def sample_distinct(ids, incumbent, seed, tick, buyer, market, count=5):
    # Floyd sampling has O(count**2) work rather than scanning each market.
    pos = np.searchsorted(ids, incumbent)
    has_inc = pos < len(ids) and ids[pos] == incumbent
    n = len(ids) - int(has_inc)
    k = min(count, n)
    draws = np.empty(k, dtype=np.int64)
    for step in range(k):
        end = n - k + step
        stream = (buyer * 1009 + market * 1000003 + step * 10000019 + 43000001) & 0xffffffff
        chosen = int(random_(seed, tick, stream) * (end + 1))
        for prior in range(step):
            if draws[prior] == chosen:
                chosen = end
                break
        draws[step] = chosen
    answer = np.empty(k + int(has_inc), dtype=np.int64)
    for step in range(k):
        index = draws[step]
        if has_inc and index >= pos:
            index += 1
        answer[step] = ids[index]
    if has_inc:
        answer[k] = incumbent
    # At most five alternatives plus the incumbent in production. Keep the
    # same ascending-ID order without a general sort and another array copy.
    for i in range(1,len(answer)):
        value=answer[i];j=i-1
        while j>=0 and answer[j]>value:
            answer[j+1]=answer[j];j-=1
        answer[j+1]=value
    return answer
