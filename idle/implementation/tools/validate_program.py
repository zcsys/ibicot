"""Audit AI-program traceability; passing does not certify the game for release."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def audit(program, scope, original):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)

    roles = {r['id']: r for r in program['logical_delivery_roles']}
    items = {t['id']: t for t in program['items']}
    batches = {b['id']: b for b in program['batches']}
    requirements = {s['id']: s for s in scope['requirements']}
    originals = {t['id']: t for t in original['items']}
    require(len(items) == len(program['items']), 'Duplicate work item ID')
    require(len(batches) == len(program['batches']), 'Duplicate batch ID')
    require(len(requirements) == len(scope['requirements']), 'Duplicate scope ID')
    require(len(roles) == 6, 'Six delivery roles required')
    require(program['concurrency_limit_including_director'] == 4, 'Concurrency must respect four available slots')
    require(set(originals) <= set(items), 'Original backlog items missing')
    for name, expected in program['source_fingerprints'].items():
        path = ROOT / name
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                f'Source drift: {name}; reconcile the scope before updating its fingerprint')

    ancestors = {}
    visiting = set()
    def walk(key):
        if key in ancestors:
            return ancestors[key]
        if key in visiting:
            errors.append(f'Batch dependency cycle at {key}')
            return set()
        visiting.add(key)
        found = set()
        for dep in batches[key]['depends_on']:
            if dep not in batches:
                errors.append(f'Unknown batch dependency {dep}')
                continue
            found.add(dep)
            found.update(walk(dep))
        visiting.remove(key)
        ancestors[key] = found
        return found
    for key in batches:
        walk(key)

    assigned = []
    for b in batches.values():
        require(b['lead'] in roles, f'{b["id"]}: unknown lead')
        require(bool(b['steps']) and bool(b['outputs']) and bool(b['acceptance']),
                f'{b["id"]}: missing executable steps, outputs or acceptance')
        for key in b['work_items']:
            assigned.append(key)
            require(key in items, f'{b["id"]}: unknown work item {key}')
            if key in items:
                require(items[key]['batch'] == b['id'], f'{key}: inconsistent batch mapping')
        if b['status'] == 'accepted':
            require(all(items.get(key, {}).get('status') == 'accepted' for key in b['work_items']),
                    f'{b["id"]}: batch accepted with unfinished work')
            require(all(batches.get(dep, {}).get('status') == 'accepted' for dep in b['depends_on']),
                    f'{b["id"]}: batch accepted before its entry gate')
    require(len(assigned) == len(set(assigned)) and set(assigned) == set(items),
            'Every work item must be assigned to exactly one batch')

    for key, t in items.items():
        require(t['owner'] in roles and t['reviewer'] in roles, f'{key}: missing role')
        require(t['owner'] != t['reviewer'], f'{key}: author cannot be sole reviewer')
        require(t['status'] in program['execution_policy']['status_flow'], f'{key}: invalid status')
        require(t['batch'] in batches, f'{key}: unknown batch')
        require(bool(t['scope_ids']), f'{key}: no scope justification')
        for sid in t['scope_ids']:
            require(sid in requirements, f'{key}: unknown scope ID {sid}')
            if sid in requirements:
                require(key in requirements[sid]['work_items'], f'{key}/{sid}: reverse mapping missing')
        if t['status'] in ('verified', 'accepted'):
            require(bool(t['evidence']), f'{key}: completion without evidence')
            for evidence in t['evidence']:
                require((ROOT / evidence).is_file(), f'{key}: evidence file absent: {evidence}')
        if key in originals:
            require(t['source_acceptance'] == originals[key]['acceptance'], f'{key}: changed original acceptance')
            require(t['source_acceptance_dependencies'] == originals[key]['dependencies'],
                    f'{key}: changed original dependency contract')
        for dep in t['source_acceptance_dependencies']:
            require(dep in items, f'{key}: unresolved work dependency {dep}')
            if dep in items and t['batch'] in ancestors:
                db = items[dep]['batch']
                require(db == t['batch'] or db in ancestors[t['batch']],
                        f'{key}: prerequisite {dep} is not in this batch or an ancestor batch')
                if t['status'] == 'accepted':
                    require(items[dep]['status'] == 'accepted', f'{key}: accepted before prerequisite {dep}')

    for sid, s in requirements.items():
        require(bool(s['source']) and bool(s['verification']), f'{sid}: missing source or verification')
        require(bool(s['work_items']), f'{sid}: unmapped scope requirement')
        require(s['delivery_status'] in ('not_verified', 'verified'), f'{sid}: invalid delivery state')
        if s['delivery_status'] == 'verified':
            require(bool(s.get('evidence')), f'{sid}: verified without evidence')
            for evidence in s.get('evidence', []):
                require((ROOT / evidence).is_file(), f'{sid}: missing evidence {evidence}')
        for key in s['work_items']:
            require(key in items, f'{sid}: unknown work item {key}')
            if key in items:
                require(sid in items[key]['scope_ids'], f'{sid}/{key}: forward mapping missing')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true', help='Also require completed production and scope evidence')
    parser.add_argument('--self-test', action='store_true', help='Check that broken mappings and claims are rejected')
    args = parser.parse_args()
    program = json.loads((ROOT / 'implementation/program.json').read_text())
    scope = json.loads((ROOT / 'implementation/scope_requirements.json').read_text())
    original = json.loads((ROOT / 'v1_backlog.json').read_text())
    errors = audit(program, scope, original)
    if args.self_test:
        mutations = [
            lambda p: p['items'][0].update(reviewer=p['items'][0]['owner']),
            lambda p: p['items'][0].update(scope_ids=[]),
            lambda p: p['items'][0].update(source_acceptance='Different acceptance'),
            lambda p: p['batches'][0]['depends_on'].append(p['batches'][-1]['id']),
            lambda p: p['items'][0].update(status='accepted', evidence=[]),
            lambda p: p['batches'][-1]['work_items'].append(p['items'][0]['id']),
        ]
        for i, mutate in enumerate(mutations, 1):
            changed = copy.deepcopy(program)
            mutate(changed)
            if not audit(changed, scope, original):
                errors.append(f'Rejection test {i} failed to reject invalid program')
        print(f'Rejection tests: {len(mutations)} checked')

    original_ids = {t['id'] for t in original['items']}
    incomplete = [t['id'] for t in program['items']
                  if t['id'] in original_ids | {'OPS-14'} and t['status'] != 'accepted']
    unverified_scope = [s['id'] for s in scope['requirements'] if s['delivery_status'] != 'verified']
    if args.release:
        if incomplete:
            errors.append(f'Unaccepted production/support work: {len(incomplete)} items')
        if unverified_scope:
            errors.append(f'Unverified product requirements: {len(unverified_scope)}')
    if errors:
        for error in errors:
            print('FAIL:', error)
        raise SystemExit(1)
    print(f'PASS: {len(original_ids)} original packages preserved; '
          f'{len(program["items"])} work items; {len(scope["requirements"])} scope requirements; '
          f'{len(program["batches"])} dependency-checked batches.')
    print('PASS: scope-to-work and work-to-scope mappings agree; source fingerprints match.')
    print(f'Product completion: {len(incomplete)} production/support items unaccepted; '
          f'{len(unverified_scope)} scope requirements unverified. Plan coverage is not release readiness.')


if __name__ == '__main__':
    main()
