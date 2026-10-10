"""Optional Numba with a disk cache invalidated by all economy source inputs.

Numba's default cache tracks only the function's own source file; compiled
callers also embed imported helpers and catalog constants. Namespace their
cache by the complete economy source so edits to those dependencies cannot
silently reuse an older simulation. Compiler/CPU signatures remain Numba's
responsibility.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
from threading import RLock

from numba import config, njit as _njit

_LOCK = RLock()


@lru_cache(maxsize=1)
def _source_version():
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    paths = sorted(root.rglob('*.py')) + [root / 'core' / 'catalog.json']
    for path in paths:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:24]


def njit(func=None, **options):
    def decorate(fn):
        with _LOCK:
            previous = config.CACHE_DIR
            base = Path(previous) if previous else Path(__file__).resolve().parents[1] / '__pycache__' / 'numba'
            # Numba captures the cache location when decorating the function.
            # Restore the global setting immediately for other users of Numba.
            config.CACHE_DIR = str(base / _source_version())
            try:
                return _njit(cache=True, **options)(fn)
            finally:
                config.CACHE_DIR = previous
    return decorate if func is None else decorate(func)
