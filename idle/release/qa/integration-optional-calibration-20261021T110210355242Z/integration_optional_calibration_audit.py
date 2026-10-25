"""Read-only independent audit of the focused optional-calibration change."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--previous', type=Path, required=True)
p.add_argument('--previous-mobile', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
checks = 0


def check(value, message):
    global checks
    checks += 1
    assert value, message


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def differences(left, right, prefix=''):
    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        return [path for key in sorted(left.keys() | right.keys())
                for path in ([f'{prefix}/{key}'] if key not in left or key not in right
                             else differences(left[key], right[key], f'{prefix}/{key}'))]
    if isinstance(left, list):
        if len(left) != len(right):
            return [prefix]
        return [path for index, (x, y) in enumerate(zip(left, right))
                for path in differences(x, y, f'{prefix}/{index}')]
    return [] if left == right else [prefix]


r = a.source
report = read(r / 'release/balance/optional-calibration-2026-10-21T105107709296Z/report.json')
check(report['status'] == 'complete' and len(report['policies']) == 15, 'complete 15 cases')
check(len({(x['visits_per_day'], x['horizon_days'], x['bonus_policy']) for x in report['policies']}) == 15, 'unique cases')
for name, expected in report['source_sha256'].items():
    check(sha(r/name) == expected, f'archived input {name}')

changed = []
for name in report['source_sha256']:
    old = a.previous/name
    if old.exists() and sha(old) != sha(r/name):
        changed.append(name)
check(set(changed) == {'game/content/progression/campaign.json', 'game/content/locales/en-US/chapter.03.copy.json', 'game/simulation/bin/run_policies.dart'}, 'two content inputs and existing runner disclosure change')
old_runner = (a.previous/'game/simulation/bin/run_policies.dart').read_text()
expected_runner = old_runner.replace(
    'The none policy uses no Focus and therefore deliberately does not complete the chapter requiring three calibrations.',
    'The none policy uses no Focus or Support; all campaign goals remain eligible.',
).replace(
    'The minimal policy completes the three required accessible calibrations; it is not zero-Focus.',
    'The legacy-named requiredCalibrationsOnly policy voluntarily completes three accessible calibrations; it is not zero-Focus and they are no longer required.',
)
check((r/'game/simulation/bin/run_policies.dart').read_text() == expected_runner, 'existing runner change is disclosure only')
old = read(a.previous/'game/content/progression/campaign.json')
new = read(r/'game/content/progression/campaign.json')
expected = json.loads(json.dumps(old))
removed = expected['chapters'][2]['objectives'].pop()
check(removed == {'kind': 'stat_min', 'stat': 'unique_calibrations', 'value': 3}, 'remove exactly calibration gate')
expected['chapters'][2]['hints'][1] = 'Calibration patterns are an optional discovery; accessible completion gives the same result.'
check(new == expected, 'all other campaign fields retained')
check(new['chapters'][2]['objectives'] == [{'kind': 'stat_min', 'stat': 'surveys_collected', 'value': 12}], '12 Surveys retained')
old_copy = read(a.previous/'game/content/locales/en-US/chapter.03.copy.json')
new_copy = read(r/'game/content/locales/en-US/chapter.03.copy.json')
old_copy['hints'] = new['chapters'][2]['hints']
check(old_copy == new_copy, 'localized copy change only optional hint')

old_manifest_path = a.previous_mobile/'game/mobile/assets/config/manifest.json'
manifest_path = r/'game/mobile/assets/config/manifest.json'
old_manifest, manifest = read(old_manifest_path), read(manifest_path)
check(sha(old_manifest_path) == '708f083217d4810e8e0a23e4d6519b374ab3c986da08eb001c0dd0a762e5c19c', 'actual old bundle migration identity')
check(sha(manifest_path) == '58c8cac53fa8679447d3f524bdc6979bf0c11127670840bf21c57cfffc2bbc72', 'new bundle identity')
check(len(manifest['files']) == len(old_manifest['files']) == 29, '29 required files')
manifest_diff = differences(old_manifest, manifest)
check(set(manifest_diff) == {'/files/assets/progression/campaign.json/bytes', '/files/assets/progression/campaign.json/sha256'}, 'only campaign descriptor changes')
for name, spec in manifest['files'].items():
    file = r/'game/mobile'/name
    check(sha(file) == spec['sha256'] and file.stat().st_size == spec['bytes'], f'actual packaged file {name}')
check(read(r/'game/mobile/assets/progression/campaign.json') == new, 'simulation/client exact campaign content')

no_bonus = []
for row in report['policies']:
    check(row['chapters_completed'] == 6, 'all cases finish campaign')
    check(row['elapsed_seconds'] == row['horizon_days'] * 86400, 'exact elapsed horizon')
    check(len(row['chapter_seconds_upper_bounds']) == 6, 'all six chapter timestamps')
    check(row['chapter_seconds_upper_bounds']['chapter.06'] <= row['elapsed_seconds'], 'ending within horizon')
    for ledger in [row, *row['checkpoints_at_last_visit'].values()]:
        check(int(ledger['notes_earned']) == int(ledger['notes_unspent']) + int(ledger['notes_spent_dossiers']), 'Note balance')
        check(int(ledger['notes_earned']) == int(ledger['notes_from_surveys']) + int(ledger['notes_from_contracts']), 'Note income attribution')
    if row['bonus_policy'] == 'none':
        check(row['focus_charges_used'] == 0 and row['free_support_tokens_used'] == 0, 'literal zero bonus')
        no_bonus.append({'visits': row['visits_per_day'], 'horizon': row['horizon_days'], 'ending_days': row['chapter_seconds_upper_bounds']['chapter.06']/86400})
check(len(no_bonus) == 6, 'six zero-bonus cases')
pair_differences = []
for visits in [1, 3, 6]:
    free = next(x for x in report['policies'] if x['visits_per_day'] == visits and x['bonus_policy'] == 'focusAndFreeSupport')
    ad = next(x for x in report['policies'] if x['visits_per_day'] == visits and x['bonus_policy'] == 'focusAndAdSupportFixture')
    delta = differences(free, ad)
    check(all(x.split('/')[-1] in ['bonus_policy', 'main_serialized_bytes'] for x in delta), 'free/ad differences confined to route metadata')
    check('/bonus_policy' in delta, 'route labels actually distinct')
    pair_differences.append({'visits': visits, 'exact_diff_paths': delta})

a.output.write_text(json.dumps({'status': 'pass', 'checks': checks, 'old_to_new_existing_source_changes': changed, 'manifest_diff_paths': manifest_diff, 'zero_bonus_endings': no_bonus, 'free_ad_pairs': pair_differences, 'scope': 'Exact content/source diff, all 15 ledger summaries and all three free/ad summary pairs; no human pacing or native migration claim'}, indent=2)+'\n')
print(f'{checks} checks passed')
