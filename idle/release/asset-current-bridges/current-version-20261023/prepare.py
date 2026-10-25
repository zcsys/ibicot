"""Prepare explicit current source records, preserving prior provenance/captures.

This changes no canonical asset. A different reviewer and integration are needed.
"""
from pathlib import Path
import copy
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'release/asset-current-bridges/staged'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def relative(path):
    return str(path.relative_to(ROOT))


assert not (OUT / 'proposal.json').exists(), 'Preserve an existing proposal'
contract = json.loads((ROOT / 'implementation/art/production_contract.json').read_text())
proposals = json.loads((OLD / 'proposed-updates.json').read_text())['updates']
known = {(b['path'], b['recorded_sha256']): b
         for p in proposals for b in p.get('changed_bindings', [])}
differences, records = {}, []
for asset in contract['assets']:
    target = asset['provenance_path']
    before_raw = (ROOT / target).read_bytes()
    before = json.loads(before_raw)
    after = copy.deepcopy(before)
    changed = []
    for key, list_key in [('source_media_sha256', 'source_media_paths'),
                          ('exported_sha256', 'exported_paths')]:
        original = before[key]
        pins = dict(zip(before[list_key], original)) if isinstance(original, list) else original
        for name, prior in pins.items():
            current = sha(ROOT / name)
            if current == prior:
                continue
            assert key == 'source_media_sha256', 'An export change needs separate review'
            identity = (name, prior)
            if identity not in differences:
                candidates = [OLD / 'snapshot' / name]
                binding = known.get(identity)
                if binding and binding.get('historical_source'):
                    history = binding['historical_source']
                    candidates += [ROOT / history['path'], ROOT / history['snapshot_path']]
                historical = next((p for p in candidates if p.is_file() and sha(p) == prior), None)
                assert historical is not None, ('No exact historical source', identity)
                old_copy = OUT / 'source-before' / name
                new_copy = OUT / 'source-after' / name
                for p, raw in [(old_copy, historical.read_bytes()),
                               (new_copy, (ROOT / name).read_bytes())]:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(raw)
                patch = OUT / 'diffs' / (hashlib.sha256(name.encode()).hexdigest()[:16] + '.patch')
                patch.parent.mkdir(parents=True, exist_ok=True)
                patch.write_text(''.join(difflib.unified_diff(
                    old_copy.read_text().splitlines(True), new_copy.read_text().splitlines(True),
                    fromfile=name + ' (recorded version)', tofile=name + ' (proposed version)')))
                differences[identity] = {
                    'path': name, 'prior_sha256': prior, 'current_sha256': current,
                    'prior_source': relative(old_copy), 'current_source': relative(new_copy),
                    'historical_source': relative(historical),
                    'diff_path': relative(patch), 'diff_sha256': sha(patch),
                }
            changed.append(differences[identity])
            if isinstance(original, list):
                after[key][before[list_key].index(name)] = current
            else:
                after[key][name] = current
    if not changed:
        continue
    saved = OUT / 'provenance-before' / Path(target).name
    saved.parent.mkdir(parents=True, exist_ok=True)
    saved.write_bytes(before_raw)
    assert 'author_source_version_update_20261023' not in after
    after['author_source_version_update_20261023'] = {
        'author': '/root', 'historical_record': relative(saved),
        'historical_record_sha256': sha(saved), 'changed_source_bindings': changed,
        'scope': 'Explicit source-version bookkeeping. Existing exported PNGs, capture records, '
                 'reviewer fields and approval states retain their original versions and limits.',
        'new_png_rendered': False,
        'whole_asset_approval': False,
        'combined_current_native_qualified': False,
        'independent_source_version_review_pending': True,
    }
    proposed = OUT / 'proposed' / target
    write(proposed, after)
    records.append({'asset_id': asset['asset_id'], 'target': target,
                    'before_sha256': sha(ROOT / target), 'proposed_path': relative(proposed),
                    'proposed_sha256': sha(proposed), 'changed_bindings': changed})

assert len(records) == 34 and len(differences) == 4, (len(records), len(differences))
for record in records:
    assert sha(ROOT / record['target']) == record['before_sha256']
for delta in differences.values():
    assert sha(ROOT / delta['path']) == delta['current_sha256']
write(OUT / 'proposal.json', {
    'author': '/root', 'applied': False, 'independent_review_pending': True,
    'original_assets': 164, 'records': records, 'source_differences': list(differences.values()),
    'prior_reviewed_packet': relative(OLD / 'HANDOFF.json'),
    'prior_reviewed_packet_sha256': sha(OLD / 'HANDOFF.json'),
    'original_provenance_and_capture_fields_preserved_except_declared_source_hashes': True,
    'rights_or_variant_or_package_acceptance_added': False,
})
print(f'Prepared {len(records)} explicit records from {len(differences)} source deltas; no canonical writes.')
