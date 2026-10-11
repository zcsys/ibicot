"""Research JIT namespace includes all experimental and production source."""
import hashlib
from pathlib import Path
from numba import njit as _njit, config
from economy.core.jit import _source_version

_root=Path(__file__).resolve().parent
_hash=hashlib.sha256(_source_version().encode())
for _path in sorted(_root.glob('*.py')):
    _hash.update(_path.name.encode());_hash.update(_path.read_bytes())
VERSION=_hash.hexdigest()[:24]

def njit(func):
    previous=config.CACHE_DIR
    config.CACHE_DIR=str(_root/'__pycache__'/VERSION)
    try:return _njit(cache=True)(func)
    finally:config.CACHE_DIR=previous
