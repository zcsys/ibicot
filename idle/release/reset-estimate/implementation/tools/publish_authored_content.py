#!/usr/bin/env python3
"""Export authored text/patterns to the existing production paths.

This is authoring, not asset acceptance. All outputs remain in production until
runtime, layout, provenance and independent review evidence are complete.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    manifest = read('implementation/content/launch_manifest.json')
    contract = read('implementation/art/production_contract.json')
    campaign = read('game/content/progression/campaign.json')
    archive = read('game/content/narrative/archive.en.json')
    records = {}
    for chapter in campaign['chapters']:
        records[chapter['id']] = {
            'title': chapter['title'], 'intro': chapter['intro'],
            'completion': chapter['completion'], 'hints': chapter['hints'],
        }
    records['ending.main'] = {'title': campaign['ending']['title'], 'text': campaign['ending']['text']}
    for entry in archive['entries']:
        records[entry['id']] = {'title': entry['title'], 'text': entry['text']}
    challenges, patterns = {}, {}
    for path in sorted((ROOT / 'game/content/challenges').glob('*.json')):
        challenge = json.loads(path.read_text())
        challenges[challenge['id']] = challenge
        records[challenge['id']] = {k: challenge[k] for k in ['title', 'intro', 'completion']}
    for path in sorted((ROOT / 'game/content/calibrations').glob('*.pattern.json')):
        pattern = json.loads(path.read_text())
        patterns[pattern['id']] = pattern
        records[pattern['id']] = {k: pattern[k] for k in ['title', 'intro', 'instructions', 'accessible_label', 'accessible_description']}
    updated_assets = {}
    for asset in contract['assets']:
        entities = asset['manifest_entity_ids']
        if len(entities) != 1 or entities[0] not in records:
            continue
        entity = entities[0]
        if asset['category'] == 'calibration':
            exported = patterns[entity]
            write(asset['source_descriptor_path'], exported)
        elif asset['method'] == 'authored_localized_text':
            exported = {'schema_version': 1, 'locale': 'en-US', 'content_id': entity, **records[entity]}
            source = ROOT / asset['source_descriptor_path']
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text('\n\n'.join(
                str(v) if not isinstance(v, list) else '\n'.join('- ' + line for line in v)
                for v in records[entity].values()) + '\n')
        else:
            continue
        write(asset['export_descriptor_path'], exported)
        provenance = {
            'asset_id': asset['asset_id'], 'author_or_tool': 'Codex development lead; original authored content',
            'creation_date': '2026-10-16', 'source_media_paths': [asset['source_descriptor_path']],
            'source_media_sha256': [digest(asset['source_descriptor_path'])],
            'source_kind': 'original_authored_text_or_graph',
            'license_or_authorship_basis': 'Original text and graph data authored in this project; no external media or quoted source text.',
            'license_evidence_paths': [asset['source_descriptor_path']],
            'allowed_uses': ['in_game_distribution', 'marketing_excerpt', 'modification'],
            'attribution_text': 'Tideglass original narrative and constellation designs.',
            'reference_asset_permissions': [],
            'export_tool_and_version': 'publish_authored_content.py v1; UTF-8 JSON',
            'exported_paths': [asset['export_descriptor_path']],
            'exported_sha256': [digest(asset['export_descriptor_path'])],
            'reviewer': None, 'review_evidence': None,
        }
        write(asset['provenance_path'], provenance)
        asset.update(status='in_production', source_exists=True, export_exists=True)
        updated_assets[asset['asset_id']] = asset
    for asset in manifest['assets']:
        if asset['id'] in updated_assets:
            authored = updated_assets[asset['id']]
            asset.update(delivery_status='in_production', source_path=authored['export_descriptor_path'],
                         license_evidence=authored['provenance_path'])
    for chapter in manifest['chapters']:
        chapter.update(production_status='in_production', objectives_status='in_production',
                       objective_spec={'source_path': 'game/content/progression/campaign.json', 'chapter_id': chapter['id']})
    for challenge in manifest['challenges']:
        challenge.update(production_status='in_production', rules_status='in_production',
                         rule_spec={'source_path': f"game/content/challenges/{challenge['id']}.json"})
    for pattern in manifest['calibrations']:
        pattern.update(production_status='in_production', pattern_status='in_production',
                       pattern_spec={'source_path': f"game/content/calibrations/{pattern['id']}.pattern.json"})
    for entry in manifest['main_archive'] + [manifest['ending']]:
        entry.update(production_status='in_production', copy_status='in_production')
    manifest['status'] = 'partial_authored_content_runtime_verification_pending'
    manifest['scope_policy'] = ('Baseline counts preserved. Some text and pattern data are authored; '
        'the per-item production/verification fields distinguish these from integrated accepted content. '
        'Unfinished assets remain explicitly unproduced. No registry count proves launch readiness.')
    contract['status'] = 'production_in_progress'
    contract['meaning'] = 'Production paths and budgets remain binding. Per-asset flags record authored files; runtime acceptance and independent evidence remain required.'
    write('implementation/content/launch_manifest.json', manifest)
    write('implementation/art/production_contract.json', contract)
    print(f'Exported {len(updated_assets)} authored asset packages; none marked verified.')


if __name__ == '__main__':
    main()
