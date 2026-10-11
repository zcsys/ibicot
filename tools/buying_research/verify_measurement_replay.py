"""Verify that added recording observes exactly the preserved baseline trajectory.

Compare actual state and all common product/company accounts; do not compare
wall-clock timing. Preserve the old raw T0 net allocation, reconstructing net
from posted accounts on both sides, as documented by the legacy recorder audit.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify(before, after, tick):
    before, after = Path(before), Path(after)
    failures = []
    manifests = [json.loads((p / 'manifest.json').read_text()) for p in (before, after)]
    if any(m['status'] != 'complete' for m in manifests):
        raise ValueError('Both runs must be complete')
    source_keys = set().union(*(m['sourceHashes'] for m in manifests))
    runtime_catalogs = {'catalogs/midbridge-4259-recursive/'+name for name in
                        ('catalog.json', 'naming.json', 'starting-selection.json', 'consumption-calibration.json')}
    production_keys = sorted(k for k in source_keys if k.startswith('economy/') or k in runtime_catalogs)
    if not runtime_catalogs.issubset(source_keys):
        failures.append('missing runtime catalog provenance')
    changed_production = [k for k in production_keys
                          if manifests[0]['sourceHashes'].get(k) != manifests[1]['sourceHashes'].get(k)]
    if changed_production:
        failures.append('production sources/catalog')
    for name in ('config.json', 'initial-snapshot.json'):
        if json.loads((before / name).read_text()) != json.loads((after / name).read_text()):
            failures.append(name)
    schemas = [json.loads((p / 'measurement-schema.json').read_text()) for p in (before, after)]
    if schemas[0]['products'] != schemas[1]['products']:
        failures.append('product metadata')
    common = [f for f in schemas[0]['fields'] if f in schemas[1]['fields']]
    product_ticks = 0
    company_fields = 0
    company_periods = 0
    field_mismatches = {f: 0 for f in common}
    field_max_error = {f: 0.0 for f in common}
    expected_tick = 1
    for old_file in sorted(before.glob('products-*.npz')):
        new_file = after / old_file.name
        with np.load(old_file) as x, np.load(new_file) as y:
            xt, yt = x['ticks'], y['ticks']
            if not np.array_equal(xt, yt) or xt.tolist() != list(range(expected_tick, int(xt[-1]) + 1)):
                failures.append('coverage:' + old_file.name)
            expected_tick = int(xt[-1]) + 1
            data = [x['data'], y['data']]
            for a, schema in zip(data, schemas):
                ix = {f: i for i, f in enumerate(schema['fields'])}
                a[:, :, ix['net']] = (a[:, :, ix['revenue']] - a[:, :, ix['cogs']]
                                     + a[:, :, ix['switchIncome']] - a[:, :, ix['switchExpense']]
                                     - a[:, :, ix['rent']])
            for f in common:
                a, b = [d[:, :, s['fields'].index(f)] for d, s in zip(data, schemas)]
                field_mismatches[f] += int(np.count_nonzero(a != b))
                field_max_error[f] = max(field_max_error[f], float(np.max(np.abs(a - b))))
            product_ticks += len(xt) * data[0].shape[1]
    if expected_tick != tick + 1:
        failures.append('recording end tick')
    if {f.name for f in before.glob('products-*.npz')} != {f.name for f in after.glob('products-*.npz')}:
        failures.append('product chunk names')
    failures.extend('product:' + f for f, n in field_mismatches.items() if n)
    for old_file in sorted(before.glob('companies-*.npz')):
        with np.load(old_file) as x, np.load(after / old_file.name) as y:
            if set(x.files) != set(y.files):
                failures.append('company schema:' + old_file.name)
            for key in x.files:
                if key not in y or not np.array_equal(x[key], y[key], equal_nan=True):
                    failures.append(old_file.name + ':' + key)
                company_fields += 1
            company_periods += 1
    if {f.name for f in before.glob('companies-*.npz')} != {f.name for f in after.glob('companies-*.npz')}:
        failures.append('company chunk names')
    economic_tick_fields = ('tick', 'lm1', 'lm2', 'lm3', 'aov1', 'aov2', 'aov3', 'feeOrders', 'fees')
    histories = [[json.loads(line) for line in (p / 'ticks.jsonl').read_text().splitlines()]
                 for p in (before, after)]
    for history in histories:
        if [r['tick'] for r in history] != list(range(1, tick + 1)):
            failures.append('tick history coverage')
    for key in economic_tick_fields:
        if [r[key] for r in histories[0]] != [r[key] for r in histories[1]]:
            failures.append('tick history:' + key)
    checkpoints = []
    for old_file in sorted(before.glob('checkpoint-*.npz')):
        with np.load(old_file) as x, np.load(after / old_file.name) as y:
            if set(x.files) != set(y.files):
                failures.append('world array schema:' + old_file.name)
            bad = [k for k in x.files if k not in y or not np.array_equal(x[k], y[k], equal_nan=True)]
            failures.extend(old_file.name + ':' + k for k in bad)
            count = len(x.files)
        a, b = old_file.with_suffix('.json'), (after / old_file.name).with_suffix('.json')
        exact_json = json.loads(a.read_text()) == json.loads(b.read_text())
        if not exact_json:
            failures.append('world JSON:' + a.name)
        checkpoints.append(dict(file=old_file.name, worldArrays=count, exactArrays=not bad,
            exactJSON=exact_json, beforeSHA256=digest(old_file), afterSHA256=digest(after / old_file.name)))
    return dict(status='pass' if not failures else 'fail', before=str(before.resolve()),
        after=str(after.resolve()), window=[1, tick], productTicks=product_ticks,
        commonProductFields=common, productFieldMismatches=field_mismatches,
        maximumAbsoluteProductError=field_max_error, companyPeriods=company_periods,
        companyArrayComparisons=company_fields, economicTickFields=list(economic_tick_fields),
        checkpoints=checkpoints, productionAndCatalogSourceFiles=len(production_keys),
        changedProductionSources=changed_production, differences=failures,
        sourceIdentities=[m['sourceIdentity'] for m in manifests],
        verifiedReplayInvariants=manifests[1]['invariants'],
        verifiedReplayInvariantGate=manifests[1]['invariantGate'],
        interpretation='Only a passing exact trajectory comparison permits the replay measurements to supplement the preserved baseline. Historical manifests and raw files remain unchanged. Net product earnings are reconstructed from posted revenue, COGS, fees and rent on both sides. Wall-clock timings and measurement-only fields are not trajectory evidence.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('before', type=Path); p.add_argument('after', type=Path)
    p.add_argument('--tick', type=int, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); result = verify(a.before, a.after, a.tick)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(result))
    if result['status'] != 'pass':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
