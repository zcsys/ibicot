"""Read-only archive/coverage verification for a fresh production baseline."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path
import numpy as np


def audit(path):
    path = Path(path)
    manifest = json.loads((path / 'manifest.json').read_text())
    issues = []
    if manifest['status'] != 'complete' or not manifest.get('invariantGate'):
        issues.append('run incomplete or invariant gate failed')
    spec = manifest['specification']
    if spec['treatment'] != 'baseline' or spec['scenario'] != 'none':
        issues.append('not an unmodified baseline scenario')
    start, end = spec['window']
    expected = list(range(start, end + 1))
    hashes = manifest['sourceHashes']
    identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    if identity != manifest['sourceIdentity']:
        issues.append('source identity mismatch')
    if hashlib.sha256((path / 'starting.patch').read_bytes()).hexdigest() != manifest['patchSHA256']:
        issues.append('patch mismatch')
    with tarfile.open(path / 'source.tar.gz') as archive:
        members = [m for m in archive.getmembers() if m.isfile()]
        if len(members) != len(hashes) or {m.name for m in members} != set(hashes):
            issues.append('archive member mismatch')
        for member in members:
            if hashlib.sha256(archive.extractfile(member).read()).hexdigest() != hashes.get(member.name):
                issues.append('source mismatch: ' + member.name)
    ticks = []
    for file in sorted(path.glob('products-*.npz')):
        with np.load(file, allow_pickle=False) as data:
            ticks.extend(data['ticks'].tolist())
    if ticks != expected:
        issues.append('product coverage mismatch')
    company_ticks = []
    for file in sorted(path.glob('companies-*.npz')):
        with np.load(file, allow_pickle=False) as data:
            company_ticks.extend(range(int(data['startTick']), int(data['endTick']) + 1))
    if company_ticks != expected:
        issues.append('company coverage mismatch')
    history = [json.loads(line) for line in (path / 'ticks.jsonl').read_text().splitlines()]
    if [row['tick'] for row in history] != expected:
        issues.append('tick history mismatch')
    for row in history:
        for key in ('maxCompanyToleranceRatio', 'maxMoneyToleranceRatio', 'maxGoodsToleranceRatio'):
            if not 0 <= row[key] <= 1:
                issues.append(f'invariant failed: {row["tick"]} {key}')
        if row['minStock'] < 0 or row['minCash'] < 0:
            issues.append(f'negative resources: {row["tick"]}')
    config = json.loads((path / 'config.json').read_text())
    checkpoint = json.loads((path / f'checkpoint-{end:06}.json').read_text())
    if checkpoint['tick'] != end or checkpoint['cfg'] != config or config['seed'] != spec['seed']:
        issues.append('checkpoint/config mismatch')
    with np.load(path / f'checkpoint-{end:06}.npz', allow_pickle=False) as data:
        arrays = len(data.files)
    return dict(status='pass' if not issues else 'fail', issues=issues,
                run=str(path.resolve()), commit=manifest['commit'],
                sourceIdentity=identity, archivedFiles=len(hashes), window=[start, end],
                recordedTicks=len(ticks), checkpointArrays=arrays,
                population=dict(manufacturers=config['t2FirmCount'],
                                distributors=config['distributorCount']),
                limitation='Archive, coverage and recorded invariant audit; not an economic adoption or independent replay proof.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    if result['issues']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
