"""Source-aware JIT cache for all replacement and production dependencies."""
import hashlib
from pathlib import Path
from threading import RLock
from numba import njit as _njit, config
from economy.core.jit import _source_version

_root = Path(__file__).resolve().parent
_hash = hashlib.sha256(_source_version().encode())
for _path in sorted(_root.glob('*.py')):
    _hash.update(_path.name.encode())
    _hash.update(_path.read_bytes())
VERSION = _hash.hexdigest()[:24]
_lock = RLock()


def njit(func):
    with _lock:
        previous = config.CACHE_DIR
        config.CACHE_DIR = str(_root / '__pycache__' / VERSION)
        try:
            return _njit(cache=True)(func)
        finally:
            config.CACHE_DIR = previous
