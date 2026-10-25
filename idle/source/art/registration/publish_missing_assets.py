#!/usr/bin/env python3
"""Register existing authored content with exact exports; never grant acceptance.

Run from any directory after the separately queued host capture harness completes.
--check is read-only. Actual game logic, manifest states and reviewer fields are
not edited. Host PNGs are review exports; the native client uses original widgets.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = 'source/art/registration'
DATE = '2026-10-21'


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def build():
    contract = read('implementation/art/production_contract.json')
    contracts = {a['asset_id']: a for a in contract['assets']}
    inventory = {a['asset_id']: a for a in read('release/content-evidence/inventory-assets.json')['assets']}
    capture = read(f'{HERE}/capture-manifest.json')
    help_extract = read(f'{HERE}/help-runtime-extract.json')
    season = read('game/events/content/season.01.json')
    assert sha('game/events/content/season.01.json') == sha('game/mobile/assets/events/season.01.json')
    outputs = {}
    registrations = []

    def put(path, value):
        assert path not in outputs, path
        outputs[path] = value if isinstance(value, str) else dump(value)

    def output_sha(path):
        return hashlib.sha256(outputs[path].encode()).hexdigest() if path in outputs else sha(path)

    def register(aid, source, exported, actual_sources, selector, routes, exports=(), extra=None):
        c = contracts[aid]
        original = inventory[aid]
        put(c['source_descriptor_path'], source)
        # Existing canonical Season 2 brief is the root-owned export: compare only.
        if aid == 'asset.support.season02_brief':
            assert (ROOT / c['export_descriptor_path']).read_text() == exported
        else:
            put(c['export_descriptor_path'], exported)
        source_paths = list(dict.fromkeys([c['source_descriptor_path'], *actual_sources]))
        exported_paths = list(dict.fromkeys([c['export_descriptor_path'], *exports]))
        provenance = {
            'asset_id': aid,
            'author_or_tool': 'Tideglass AI art/content delivery owner; registration of original project-authored source',
            'creation_date': DATE,
            'source_media_paths': source_paths,
            'source_media_sha256': {p: output_sha(p) for p in source_paths},
            'source_kind': 'original_code_native_composition' if c['category'] in ['harbor', 'season_presentation'] else 'original_project_authored_text',
            'license_or_authorship_basis': 'Existing original Tideglass code/text listed here, registered without external artwork or quoted source prose. This is authorship traceability, not independent rights or release approval.',
            'license_evidence_paths': source_paths,
            'allowed_uses': ['local_project_development_and_review'],
            'distribution_terms_approval': {'status': 'not_recorded', 'owner': None, 'evidence': None},
            'attribution_text': 'Original Tideglass project artwork and prose; dependency/font notices remain separately required.',
            'reference_asset_permissions': [],
            'export_tool_and_version': 'publish_missing_assets.py v1; UTF-8 source/data; PNGs from separately logged Flutter host capture of actual widgets',
            'exported_paths': exported_paths,
            'exported_sha256': {p: output_sha(p) for p in exported_paths},
            'reviewer': None,
            'review_evidence': None,
            'author_report': f'{HERE}/AUTHOR_REPORT.md',
            'bounded_host_capture_evidence': {'verification_path': 'release/native-proof/root-art-registration-20261021T111004.738637Z/verification.json', 'verification_sha256': sha('release/native-proof/root-art-registration-20261021T111004.738637Z/verification.json'), 'source_pin_path': 'release/native-proof/root-art-registration-20261021T111004.738637Z/source-before.json', 'source_pin_sha256': sha('release/native-proof/root-art-registration-20261021T111004.738637Z/source-before.json'), 'scope': 'Exact current widget PNGs and HelpContent extraction only; no native/device or full variant acceptance'} if (exports or aid.startswith('asset.support.') and aid not in ['asset.support.operations_runbooks', 'asset.support.season02_brief']) else None,
            'status': 'in_production',
            'original_required_variants': c['required_variants'],
            'variant_acceptance': {v: 'open_independent_complete_variant_acceptance' for v in c['required_variants']},
            'production_acceptance': False,
        }
        if extra:
            provenance.update(extra)
        put(c['provenance_path'], provenance)
        registrations.append({
            'asset_id': aid, 'entity_ids': original['entity_ids'], 'scope_ids': original['scope_ids'],
            'source_descriptor_path': c['source_descriptor_path'],
            'export_descriptor_path': c['export_descriptor_path'], 'provenance_path': c['provenance_path'],
            'canonical_verification_path': c['verification_path'], 'canonical_verification_created': False,
            'actual_sources': [{'path': p, 'sha256': sha(p)} for p in actual_sources],
            'selector': selector, 'runtime_routes': routes,
            'registered_exports': [{'path': p, 'sha256': output_sha(p)} for p in exported_paths],
            'delivery_channel': c['delivery_channel'], 'required_variants': c['required_variants'],
            'variants_remaining_open': c['required_variants'], 'status': 'authored_registered_not_verified',
        })

    for i in range(7):
        entity = 'harbor.unlit' if i == 0 else f'harbor.restored.{i:02d}'
        aid = f'asset.{entity}'
        relevant = [x for x in capture['captures'] if x['inputs'].get('asset_id') == aid]
        assert len(relevant) == 4
        scene = {
            'schema_version': 1, 'id': entity, 'asset_id': aid, 'implementation': 'existing_code_native_vector',
            'original_contract_method': contracts[aid]['method'],
            'view_box': [0, 0, 640, 388], 'geometry_source': 'game/mobile/lib/harbor_art.dart',
            'widget': 'HarborArt', 'painter': '_HarborPainter.paint', 'selector': {'restoration': i},
            'dynamic_parameters': ['counts', 'phase', 'decoration'],
            'main_binding': 'game.story.campaign.restoredHarbor',
            'state_geometry': {'dawn_interpolation': i / 6, 'constellation_groups_drawn': i, 'quay_lamps_drawn': i},
            'layer_order': ['dawn_gradient', 'fixed_star_field', 'crescent_halo', 'restored_constellations', 'islands', 'ocean_waves', 'lighthouse_beam_and_reflection', 'lighthouse', 'five_base_fleet_silhouettes', 'restored_quay_lamps', 'optional_earned_decoration'],
            'reduced_motion': {'phase': 0, 'same_restoration_information': True, 'complete_native_acceptance': False},
            'notes': 'This descriptor binds the actual shared painter; it is not a replacement painting. The unlit ID means unrestored: lighthouse and base stars remain visible. Harbor miniatures use earlier base silhouettes, not the separate 25-stage card renderer.',
        }
        exported = {
            'schema_version': 1, 'id': entity, 'asset_id': aid,
            'renderer_source': 'game/mobile/lib/harbor_art.dart', 'widget': 'HarborArt',
            'restoration': i, 'view_box': [0, 0, 640, 388],
            'runtime_is_code_native': True, 'descriptor_loaded_by_client': False,
            'registration_purpose': 'Maps source and representative raster exports; client renders original widget directly.',
            'host_exports': relevant, 'production_status': 'in_production', 'verification_evidence': None,
            'original_required_variants': contracts[aid]['required_variants'],
        }
        register(aid, scene, exported, ['game/mobile/lib/harbor_art.dart', 'game/mobile/lib/palette.dart', 'game/mobile/lib/strings.dart', 'game/mobile/lib/app.dart', 'game/mobile/lib/story_screen.dart'],
                 f'HarborArt(restoration: {i})', ['TideglassApp harbor / game.story.campaign.restoredHarbor', 'StoryScreen decoration previews'], [x['path'] for x in relevant])

    for reward in season['rewards']:
        if reward['kind'] != 'archive_fragment':
            continue
        aid = f"asset.{reward['content_id']}"
        body = f"# {reward['title']}\n\n{reward['body']}\n\n"
        body += f"Content ID: `{reward['content_id']}`. Free pass level {reward['level']}; reward `{reward['id']}`.\n"
        exported = {'schema_version': 1, 'locale': 'en-US', 'content_id': reward['content_id'], 'season_id': season['id'], 'reward_id': reward['id'], 'level': reward['level'], 'track': reward['track'], 'title': reward['title'], 'body': reward['body'], 'economic_effects': reward['economic_effects'], 'runtime_source': 'game/events/content/season.01.json', 'runtime_bundle': 'game/mobile/assets/events/season.01.json', 'descriptor_loaded_by_client': False}
        register(aid, body, exported, ['game/events/content/season.01.json', 'game/mobile/assets/events/season.01.json', 'game/mobile/lib/season_screen.dart', 'game/mobile/lib/story_state.dart', 'game/events/lib/src/pass.dart'], f"rewards[content_id={reward['content_id']}]", ['SeasonScreen Pass tab / level expansion / free reward claim and retained archive text'])

    for aid, data in help_extract.items():
        source = f"# {data['handbook_title']}\n\n{data['handbook_intro']}\n\n{data['development_notice']}\n"
        for article in data['articles']:
            source += f"\n## {article['title']}\n\n{article['summary']}\n"
            for section in article['sections']:
                source += f"\n### {section['title']}\n\n" + '\n\n'.join(section['paragraphs']) + '\n'
            if article['actions']:
                source += '\nAvailable actions: ' + '; '.join(x['label'] for x in article['actions']) + '.\n'
        data = {**data, 'descriptor_loaded_by_client': False, 'export_role': 'Exact current HelpContent values; runtime consumes its code-native externalized HelpContent source.'}
        register(aid, source, data, ['game/mobile/lib/help_content.dart', 'game/mobile/lib/help_screen.dart', 'game/mobile/lib/app.dart', 'game/mobile/lib/presentation.dart', f'{HERE}/help-runtime-extract.json'], ', '.join(data['runtime_selector']), ['Logbook / harbor handbook / HelpScreen topic', *[x['topic'] for x in data['articles']]])

    ops_sources = ['release/runbooks/README.md', 'release/runbooks/LAUNCH_HANDOVER.md', 'release/runbooks/launch-coverage-template.json', 'services/docs/OPERATIONS.md', 'services/docs/FULFILLMENT.md', 'services/docs/PRIVACY.md']
    ops = '''# Tideglass internal operating package\n\nThis is an index to the actual local operating instructions, not a hosted service, staffed shift or public policy. No rollout or 14-day support acceptance is recorded.\n\n| Document | Operator use |\n|---|---|\n| [Launch handover](../../release/runbooks/LAUNCH_HANDOVER.md) | Authority, preflight, escalation, stop conditions and actual 14-day evidence required before launch. |\n| [Coverage template](../../release/runbooks/launch-coverage-template.json) | Fourteen unassigned daily records; fill only with actual approved coverage and observations. |\n| [Operations](../../services/docs/OPERATIONS.md) | Exact local health, backup, retention and disposable restore commands and limits. |\n| [Fulfillment](../../services/docs/FULFILLMENT.md) | Provider reconciliation, retained keys and ownership boundaries. |\n| [Data inventory](../../services/docs/PRIVACY.md) | Implemented collection/export/deletion behavior; not the absent public policy. |\n\nRead the source document's version-specific limitations before executing anything. Missing deployment, primary/secondary contacts, public support/privacy, provider qualification and real operational coverage remain unresolved. This internal package is excluded from the mobile asset bundle. Initial preparation is distinct from observed launch-support completion.\n'''
    register('asset.support.operations_runbooks', ops, ops, ops_sources, 'Internal operating package index with source-specific procedures', ['Internal release package only; no client route'])
    brief = (ROOT / 'release/season-2-brief.md').read_text()
    register('asset.support.season02_brief', brief, brief, ['release/season-2-brief.md'], 'Initial B21/M7-01 brief; later M7-08/OPS-14 update remains separate', ['Internal release package only; no client route'])

    source = '# ' + season['title'] + '\n'
    for key, value in season['copy'].items():
        source += f'\n## {key}\n\n{value}\n'
    source += '\n## Milestone copy\n'
    for milestone in season['milestones']:
        source += f"\n### {milestone['title']}\n\n{milestone['body']}\n"
    source += '\n## Reward copy\n'
    for reward in season['rewards']:
        source += f"\n### {reward['id']} — {reward['title']}\n\n{reward['body']}\n"
    exported = {'schema_version': 1, 'locale': 'en-US', 'content_id': season['id'], 'title': season['title'], 'copy': season['copy'], 'milestones': [{k: v for k, v in x.items() if k in ['id', 'title', 'body']} for x in season['milestones']], 'rewards': [{k: v for k, v in x.items() if k in ['id', 'content_id', 'level', 'track', 'title', 'body']} for x in season['rewards']], 'runtime_source': 'game/events/content/season.01.json', 'runtime_bundle': 'game/mobile/assets/events/season.01.json', 'descriptor_loaded_by_client': False}
    register('asset.season.01.copy', source, exported, ['game/events/content/season.01.json', 'game/mobile/assets/events/season.01.json', 'game/mobile/lib/season_screen.dart', 'game/mobile/lib/story_state.dart'], 'title, copy, milestone titles/bodies, reward titles/bodies', ['Logbook / SeasonScreen / Fleet, Pass and Contracts tabs'])

    aid = 'asset.season.01.presentation'
    season_captures = [x for x in capture['captures'] if x['inputs'].get('asset_id') == aid]
    assert len(season_captures) == 5
    scene = {
        'schema_version': 1, 'id': 'season.01.presentation', 'asset_id': aid,
        'implementation': 'existing_code_native_scene_composition', 'widget': 'SeasonScreen',
        'source': 'game/mobile/lib/season_screen.dart', 'route': 'TideglassApp._openSeason',
        'tabs': [{'index': 0, 'method': '_fleet', 'parts': ['lifecycle_copy', 'HarborArt', 'seasonal_wallet', 'StagedProducerArt', 'milestone_cards', 'synergy_panel']}, {'index': 1, 'method': '_pass', 'parts': ['pass_selection', 'level_expansions', 'CosmeticPreview', 'fragment_copy', 'verified_ownership_projection']}, {'index': 2, 'method': '_contracts', 'parts': ['same_daily_slot_bindings', 'claim_controls']}],
        'harbor_binding': {'counts': 'season.fleet.counts', 'restoration': 'season.claimedMilestones.length', 'phase': 0},
        'reuse': ['HarborArt', 'StagedProducerArt', 'CosmeticPreview', 'LocalizedText'],
        'season_new_unique_cosmetics': 0, 'economic_logic_in_art': False,
        'limitations': ['The season is a screen composition, not an additional equipable cosmetic.', 'The new thumbnail is an exact host component export; no runtime thumbnail route is implemented.', 'Original equipped/preview/thumbnail/native/viewport variants remain open; host captures do not waive them.'],
    }
    exported = {**scene, 'descriptor_loaded_by_client': False, 'host_exports': season_captures, 'original_required_variants': contracts[aid]['required_variants'], 'production_status': 'in_production', 'verification_evidence': None}
    register(aid, scene, exported, ['game/mobile/lib/season_screen.dart', 'game/mobile/lib/harbor_art.dart', 'game/mobile/lib/producer_art.dart', 'game/mobile/lib/cosmetic_art.dart', 'game/mobile/lib/palette.dart', 'game/mobile/lib/presentation.dart', 'game/mobile/lib/app.dart', 'game/events/content/season.01.json'], 'SeasonScreen Fleet, Pass and Contracts composition', ['TideglassApp._openSeason / SeasonScreen', 'SeasonScreen initialTab 0, 1, 2'], [x['path'] for x in season_captures])
    assert len(registrations) == 35
    assert len({r['asset_id'] for r in registrations}) == 35
    index = {
        'schema_version': 1, 'date': DATE,
        'purpose': 'Register 35 existing local assets; does not change manifest, original contract, economic rules or reviewer acceptance.',
        'registrations': registrations,
        'blocked_public_assets': [
            {'asset_id': 'asset.support.privacy_page', 'status': 'unproduced', 'public_url': None, 'owner': None, 'reason': 'Actual operator/data behavior, approved public policy and functioning endpoint absent; internal privacy inventory is not a replacement.'},
            {'asset_id': 'asset.support.support_page', 'status': 'unproduced', 'public_url': None, 'contact': None, 'reason': 'Actual public endpoint, responsible owner/contact and response process absent; no mailbox or public policy invented.'},
        ],
        'release_ready': False,
    }
    put(f'{HERE}/registration-index.json', index)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = build()
    mismatches = []
    for path, data in outputs.items():
        dest = ROOT / path
        if args.check:
            if not dest.exists() or dest.read_text() != data:
                mismatches.append(path)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(data)
    if mismatches:
        print('Registration drift: ' + ', '.join(mismatches), file=sys.stderr)
        return 1
    print(f'{"Checked" if args.check else "Wrote"} {len(outputs)} exact registration outputs for 35 local assets; two public pages remain unproduced; no verification promoted.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
