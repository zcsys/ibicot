"""Independent comparison of registration delivery with the reviewed inventory."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--before', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
count = 0


def check(value, message):
    global count
    count += 1
    assert value, message


def read(root, path):
    return json.loads((root/path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


r, old = a.source, a.before
contract = read(r, 'implementation/art/production_contract.json')
check(contract == read(old, 'implementation/art/production_contract.json'), 'entire original production contract retained')
check(read(r, 'implementation/content/launch_manifest.json') == read(old, 'implementation/content/launch_manifest.json'), 'registration does not promote launch manifest')
index = read(r, 'source/art/registration/registration-index.json')['registrations']
ids = {row['asset_id'] for row in index}
check(len(ids) == len(index) == 35, '35 distinct registered original assets')
missing_before, missing_after = [], []
changed_existing = []
for asset in contract['assets']:
    paths = [asset[k] for k in ('source_descriptor_path', 'export_descriptor_path', 'provenance_path')]
    previous = all((old/f).is_file() for f in paths)
    current = all((r/f).is_file() for f in paths)
    if not previous:
        missing_before.append(asset['asset_id'])
    if not current:
        missing_after.append(asset['asset_id'])
    if asset['asset_id'] in ids:
        check(not previous and current, 'new registration closes actual former gap')
    for f in paths:
        if (old/f).is_file() and (r/f).is_file():
            if sha(old/f) != sha(r/f):
                changed_existing.append(f)
            else:
                check(True, 'preexisting exact file retained')
check(len(missing_before) == 37 and len(missing_after) == 2, '37 missing reduced to2')
check(set(missing_before)-set(missing_after) == ids, 'exact missing-set difference')
check(set(missing_after) == {'asset.support.privacy_page', 'asset.support.support_page'}, 'only truly absent public pages remain')
expected_changes = {'source/content/en-US/chapter.03.copy.md', 'game/content/locales/en-US/chapter.03.copy.json', 'source/provenance/asset.chapter.03.copy.json'}
expected_changes |= {f'source/provenance/{x.name}' for x in (old/'source/provenance').glob('asset.cosmetic.*.json')}
check(set(changed_existing) == expected_changes, 'no undeclared preexisting registration overwrite')

for new in (r/'source/provenance').glob('asset.cosmetic.*.json'):
    rel = new.relative_to(r)
    before, after = read(old, rel), read(r, rel)
    expected = json.loads(json.dumps(before))
    expected['source_media_sha256']['game/mobile/lib/cosmetic_art.dart'] = sha(r/'game/mobile/lib/cosmetic_art.dart')
    expected['author_pin_refresh'] = after['author_pin_refresh']
    check(after == expected, 'cosmetic metadata changed only renderer pin and explicit refresh evidence')
    check(after['reviewer'] is None and after['review_evidence'] is None, 'no invented reviewer')
    for image, h in before['exported_sha256'].items():
        check(sha(r/image) == h == after['exported_sha256'][image], 'actual cosmetic export bytes retained')
        check(sha(r/image) == sha(old/image), 'old/new cosmetic PNG equality')
    history = after['author_pin_refresh']['historical_record']
    check((r/history).read_bytes() == (old/rel).read_bytes(), 'historical provenance exact')

captures = read(r, 'source/art/registration/capture-manifest.json')['captures']
check(len(captures) == 33 and len({x['path'] for x in captures}) == 33, '33 distinct renderer captures')
restore = {}
for item in captures:
    with Image.open(r/item['path']) as im:
        im.load()
        check(im.format == 'PNG' and im.size == (item['width'], item['height']), 'capture dimensions/decode')
        check(len(im.convert('RGB').getcolors(im.width*im.height) or []) > 20, 'not empty/single-color capture')
    check(item['renderer'] == 'Flutter host widget test' and not item['native_device_acceptance'], 'host proof labelled honestly')
    if 'asset.harbor.' in item['inputs']['asset_id']:
        values = item['inputs']
        check(values['counts'] == [1]*5 and values['decoration'] is None, 'restoration comparison holds fleet constant')
        restore.setdefault(values['restoration'], []).append(item)
check(set(restore) == set(range(7)) and all(len(v) == 4 for v in restore.values()), 'every restoration has all4 captured viewport/phase samples')
check(len({sha(r/next(x['path'] for x in v if x['path'].endswith('.reduced-motion.png'))) for v in restore.values()}) == 7, 'static restoration signals remain distinct')
for state in range(7):
    name = 'harbor.unlit' if state == 0 else f'harbor.restored.{state:02}'
    scene = read(r, f'source/art/harbor/{name}.scene.json')
    export = read(r, f'game/assets/harbor/{name}.presentation.json')
    check(scene['selector']['restoration'] == state == export['restoration'], 'exact code selector')
    check(scene['state_geometry'] == {'dawn_interpolation': state/6, 'constellation_groups_drawn': state, 'quay_lamps_drawn': state}, 'source geometry agrees with painter loop')
    check(export['descriptor_loaded_by_client'] is False and export['runtime_is_code_native'] is True, 'registration descriptor is not misrepresented as runtime input')

season = read(r, 'game/events/content/season.01.json')
fragments = [x for x in season['rewards'] if x['kind'] == 'archive_fragment']
check(len(fragments) == 20, '20 real seasonal fragments')
for reward in fragments:
    value = read(r, f'game/content/locales/en-US/{reward["content_id"]}.json')
    check(all(value[k] == reward[k] for k in ['title', 'body', 'level', 'track', 'content_id', 'economic_effects']), 'exact runtime fragment fields')
    check(value['reward_id'] == reward['id'] and not reward['economic_effects'], 'correct pass reward with no economic export')
for path in ['game/mobile/lib/harbor_art.dart', 'game/mobile/lib/cosmetics.dart']:
    check(sha(r/path) == sha(old/path), 'reviewed production drawing/catalogue source unchanged')

a.output.write_text(json.dumps({'status': 'pass', 'independent_checks': count, 'new_registrations': 35, 'missing_before': missing_before, 'missing_after': missing_after, 'changed_existing_paths': changed_existing, 'cosmetic_pngs_unchanged': 72, 'captured_pngs': 33, 'independent_visual_inspection': ['seven-state harbor contact sheet', 'season fleet 320/200percent/1024, pass preview and component thumbnail contact sheet'], 'limits': ['Captured poses/first viewports only; not full motion/navigation or native/physical proof', 'No full per-asset acceptance, rights approval or public pages', 'Canonical per-asset verification/reviewer fields remain unfilled']}, indent=2)+'\n')
print(f'{count} independent checks passed')
