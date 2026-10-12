"""Exact observed-state comparison for same-policy optimization runs."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def compare(before, after):
    before, after = Path(before), Path(after)
    manifests = [json.loads((p / 'manifest.json').read_text()) for p in (before, after)]
    errors = []
    for m in manifests:
        if m['status'] != 'complete' or not m.get('invariantGate'):
            errors.append('incomplete run or failed invariant gate')
    for field in ('treatment', 'window', 'configOverrides', 'seed'):
        if manifests[0]['specification'][field] != manifests[1]['specification'][field]:
            errors.append('different specification: ' + field)
    names = [{p.name for p in path.glob('*.npz')} for path in (before, after)]
    if names[0] != names[1]:
        errors.append('different archive file sets')
    arrays = 0
    hashes = {}
    for name in sorted(names[0] & names[1]):
        hashes[name] = [hashlib.sha256((path/name).read_bytes()).hexdigest() for path in (before, after)]
        with np.load(before/name, allow_pickle=False) as left, np.load(after/name, allow_pickle=False) as right:
            if set(left.files) != set(right.files):
                errors.append('different array keys: ' + name)
            for key in sorted(set(left.files) & set(right.files)):
                arrays += 1
                if not np.array_equal(left[key], right[key], equal_nan=True):
                    errors.append(name + ':' + key)
    for name in ('config.json', 'purchase-schema.json', 'measurement-schema.json'):
        if json.loads((before/name).read_text()) != json.loads((after/name).read_text()):
            errors.append(name)
    for name in sorted(p.name for p in before.glob('checkpoint-*.json')):
        if not (after/name).exists() or json.loads((before/name).read_text()) != json.loads((after/name).read_text()):
            errors.append(name)
    histories = [[json.loads(x) for x in (p/'ticks.jsonl').read_text().splitlines()] for p in (before, after)]
    for rows in histories:
        for row in rows:
            row.pop('stepMs', None)
            row.pop('traceWriteMs', None)
    if histories[0] != histories[1]:
        errors.append('tick histories excluding timing')
    return dict(status='pass' if not errors else 'fail', differences=errors,
                before=str(before.resolve()), after=str(after.resolve()), comparedArrays=arrays,
                fileHashes=hashes, scope='All NPZ arrays, checkpoint JSON, schemas/config and tick invariants; timings excluded.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('before', type=Path)
    p.add_argument('after', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = compare(a.before, a.after)
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != 'fileHashes'}))
    if result['differences']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
