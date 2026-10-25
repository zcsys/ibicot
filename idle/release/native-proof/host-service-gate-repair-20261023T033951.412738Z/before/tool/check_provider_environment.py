#!/usr/bin/env python3
"""Require the captured provider dependency pins without installing anything."""
import importlib.metadata
import json
from pathlib import Path
import sys


def check(lock: Path):
    pins, mismatches = {}, {}
    for line in lock.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.count('==') != 1:
            raise ValueError('Provider lock must contain exact package==version pins')
        name, expected = line.split('==')
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        pins[name] = {'expected': expected, 'installed': actual}
        if actual != expected:
            mismatches[name] = pins[name]
    if not pins:
        raise ValueError('Provider dependency lock is empty')
    return {'python': sys.executable, 'pins': pins, 'mismatches': mismatches}


if __name__ == '__main__':
    result = check(Path(sys.argv[1]))
    print(json.dumps(result, indent=2))
    raise SystemExit(int(bool(result['mismatches'])))
