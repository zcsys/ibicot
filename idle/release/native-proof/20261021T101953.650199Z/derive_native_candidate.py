#!/usr/bin/env python3
"""Derive a new frozen candidate from a parent plus explicitly named source files."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from build_native import ROOT, source_hashes, fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent', type=Path)
    parser.add_argument('overlays', nargs='+', type=Path)
    args = parser.parse_args()
    parent = args.parent.resolve()
    previous = json.loads((parent / 'manifest.json').read_text())
    hashes = source_hashes(parent / 'source')
    if hashes != previous['source_sha256'] or fingerprint(hashes) != previous['source_fingerprint']:
        raise RuntimeError('Parent source no longer matches its frozen manifest')
    replacements = {}
    for relative in args.overlays:
        if relative.is_absolute() or '..' in relative.parts or str(relative) not in source_hashes(ROOT):
            parser.error(f'Overlay must identify an included working-tree file: {relative}')
        replacements[str(relative)] = (ROOT / relative).read_bytes()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    staging = ROOT / '.tooling/build-candidates' / (stamp + '-deriving')
    source = staging / 'source'
    shutil.copytree(parent / 'source', source)
    changes = {}
    diff = []
    for relative, data in replacements.items():
        target = source / relative
        before = target.read_bytes() if target.exists() else b''
        if target.exists():
            target.chmod(target.stat().st_mode | 0o200)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        changes[relative] = {'parent_sha256': hashlib.sha256(before).hexdigest() if before else None,
                            'derived_sha256': hashlib.sha256(data).hexdigest()}
        try:
            diff.extend(difflib.unified_diff(before.decode().splitlines(keepends=True), data.decode().splitlines(keepends=True), fromfile='parent/' + relative, tofile='derived/' + relative))
        except UnicodeDecodeError:
            diff.append(f'Binary overlay: {relative}\n')
    expected = dict(hashes)
    expected.update({p: hashlib.sha256(data).hexdigest() for p, data in replacements.items()})
    actual = source_hashes(source)
    if actual != expected:
        raise RuntimeError('Derived source differs outside the declared overlays')
    digest = fingerprint(actual)
    candidate = staging.with_name(stamp + '-' + digest[:12])
    staging.rename(candidate)
    source = candidate / 'source'
    workspace = candidate / 'workspace'
    shutil.copytree(source, workspace)
    for file in workspace.rglob('*'):
        if file.is_file():
            file.chmod(file.stat().st_mode | 0o200)
    for file in source.rglob('*'):
        if file.is_file():
            file.chmod(file.stat().st_mode & ~0o222)
    manifest = {'snapshot_utc': stamp, 'source_fingerprint': digest,
                'candidate_directory': str(candidate), 'source_directory': str(source),
                'workspace_directory': str(workspace), 'source_sha256': actual,
                'sdk_wrapper': str(ROOT / 'tool/flutter'),
                'parent_fingerprint': previous['source_fingerprint'],
                'parent_candidate': str(parent), 'declared_overlays': changes,
                'note': 'New immutable candidate derived from a frozen parent plus exactly the listed file bytes. Original candidate remains unchanged.'}
    (candidate / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    evidence = ROOT / 'release/native-proof' / stamp
    (evidence / 'artifacts').mkdir(parents=True)
    (evidence / 'candidate-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (evidence / 'parent-diff.patch').write_text(''.join(diff))
    shutil.copy2(Path(__file__), evidence / 'derive_native_candidate.py')
    with tarfile.open(evidence / 'artifacts/candidate-source.tar.gz', 'w:gz') as archive:
        archive.add(source, arcname='source')
    print(f'Derived candidate: {candidate}\nEvidence: {evidence}')

if __name__ == '__main__':
    main()
