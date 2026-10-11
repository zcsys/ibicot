"""Separate first assignments from supplier changes in fixed-market R1 controls.

This is an endpoint identity, not an inference of unrecorded event times. In the
reviewed settlement code, preferences start at -1, can only be assigned a
nonnegative supplier, and are never cleared in these intervention-free runs.
Distributor markets are fixed. Consequently each occupied final preference
slot accounts for exactly one initial assignment; all other counted changes
are transitions between suppliers. Reject other scenarios and source versions.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from economy.server.runtime import KernelRuntime


def audit(root, study):
    repo = Path(__file__).resolve().parents[2]
    ids = ['20261011-recovery-none-local-137', '20261011-control-market-137',
           '20261011-recovery-none-hybrid-137']
    sources = ['economy/core/state.py', 'tools/buying_research/engine.py',
               'tools/buying_research/settlement.py']
    hashes = {s: hashlib.sha256((repo / s).read_bytes()).hexdigest() for s in sources}
    cfg = json.loads((root / ids[0] / 'config.json').read_text())
    world = KernelRuntime(cfg).world
    slots = {'T1': 'preferredWholesale', 'T2': 't2Preferred',
             'T3': 'distributorPreferredSupplier'}
    if any(np.any(getattr(world, a) >= 0) for a in slots.values()):
        raise ValueError('The opening state already has preferences')
    results = []
    for name in ids:
        path = root / name
        manifest = json.loads((path / 'manifest.json').read_text())
        spec = manifest['specification']
        if manifest['status'] != 'complete' or spec['scenario'] != 'none' or spec['window'] != [1, 1080]:
            raise ValueError('Only complete, intervention-free 1..1080 controls are supported')
        if json.loads((path / 'config.json').read_text()) != cfg:
            raise ValueError('Opening configurations differ')
        if any(manifest['sourceHashes'][s] != h for s, h in hashes.items()):
            raise ValueError('A reviewed monotone-preference source changed')
        meta = json.loads((path / 'checkpoint-001080.json').read_text())
        if meta['distributorSupplierHistory']:
            raise ValueError('The fixed-market proof does not cover sparse history')
        events = json.loads((study / (name + '-all.json')).read_text())['requests']['events']
        rows = {}
        with np.load(path / 'checkpoint-001080.npz', allow_pickle=False) as z:
            if not np.array_equal(z['distributorProduct'], world.distributorProduct):
                raise ValueError('Distributor market assignments changed')
            for tier, key in slots.items():
                assignments = int(np.count_nonzero(z[key] >= 0))
                changes = int(events[tier]['preferenceChanges'])
                if changes < assignments:
                    raise ValueError('Event count cannot cover first assignments')
                rows[tier] = dict(storedPreferenceChanges=changes,
                    initialAssignments=assignments,
                    changesBetweenPreviouslySelectedSuppliers=changes - assignments)
        results.append(dict(id=name, window=[1, 1080], tiers=rows))
    return dict(status='pass', reviewedSourceHashes=hashes, runs=results,
        scope='Exact aggregate decomposition for three fixed-market, no-intervention controls. '
              'No event-time reconstruction or claim about arbitrary resets, ownership changes, '
              'product reassignment or other source versions.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--study', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = audit(a.root, a.study)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
