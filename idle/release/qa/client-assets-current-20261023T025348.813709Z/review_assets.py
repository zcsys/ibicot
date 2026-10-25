#!/usr/bin/env python3
"""Independent read-only asset/source review. Writes only this review directory."""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, subprocess, zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PINS = {}
CHECKS = []

def raw(path):
    p = ROOT / path
    value = p.read_bytes()
    PINS[str(path)] = hashlib.sha256(value).hexdigest()
    return value

def read(path):
    return json.loads(raw(path))

def check(value, name):
    CHECKS.append({'check': name, 'passed': bool(value)})

contract = read('implementation/art/production_contract.json')
manifest = read('implementation/content/launch_manifest.json')
check(len(contract['assets']) == 164, 'Original asset count')
check({r['asset_id'] for r in contract['assets']} == {r['id'] for r in manifest['assets']}, 'Exact original asset IDs')
records = []
for asset in contract['assets']:
    aid = asset['asset_id']
    for field in ('source_descriptor_path', 'export_descriptor_path'):
        check(bool(raw(asset[field])), aid + ': nonempty ' + field)
    p = read(asset['provenance_path'])
    check(p['asset_id'] == aid, aid + ': provenance identity')
    check(all(k in p for k in contract['provenance_record_required_fields']), aid + ': required provenance fields')
    drift = []
    for path_key, hash_key in [('source_media_paths', 'source_media_sha256'), ('exported_paths', 'exported_sha256')]:
        hashes = p[hash_key]
        if isinstance(hashes, list):
            check(len(p[path_key]) == len(hashes), aid + ': complete ordered ' + hash_key)
            hashes = dict(zip(p[path_key], hashes))
        check(set(p[path_key]) == set(hashes), aid + ': complete ' + hash_key)
        for path in p[path_key]:
            actual = hashlib.sha256(raw(path)).hexdigest()
            if actual != hashes[path]:
                drift.append({'path': path, 'recorded': hashes[path], 'actual': actual})
    for path in p['license_evidence_paths']:
        check(bool(raw(path)), aid + ': present authorship/license evidence ' + path)
    records.append({'asset_id': aid, 'source_kind': p['source_kind'],
                    'authorship_basis': p['license_or_authorship_basis'],
                    'allowed_uses': p['allowed_uses'], 'reference_asset_permissions': p['reference_asset_permissions'],
                    'provenance_drift': drift, 'reviewer': p['reviewer'], 'review_evidence': p['review_evidence']})

# Execute only the pure geometry functions, not the generator's writing main().
spec = importlib.util.spec_from_file_location('producer_source', ROOT / 'tools/assets/export_producers.py')
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)
raw('tools/assets/export_producers.py')
scenes = []
for tier in range(5):
    previous = None
    for stage in range(5):
        ident = f'producer.{tier+1:02d}.stage.{stage}'
        src = read(f'source/art/producers/{ident}.scene.json')
        export = read(f'game/assets/producers/{ident}.presentation.json')
        check(src == producer.scene(tier, stage), ident + ': exact regenerated pure geometry')
        check(raw(f'game/assets/producers/{ident}.svg').decode() == producer.svg(src), ident + ': exact SVG export')
        check(src['ownership_threshold'] == [0, 25, 50, 75, 100][stage], ident + ': original milestone')
        check(export['stage_threshold'] == src['ownership_threshold'], ident + ': runtime descriptor threshold')
        if previous:
            check(src['shapes'][:len(previous['shapes'])] == previous['shapes'] and len(src['shapes']) > len(previous['shapes']), ident + ': additive distinct stage')
        previous = src
        scenes.append(src)
data = raw('game/mobile/lib/producer_art_data.dart').decode()
encoded = data[data.index('['):].strip().removesuffix(';')
check(json.loads(encoded) == scenes, 'Actual Dart renderer data exactly equals all 25 source scenes')
for path in ['game/mobile/lib/producer_art.dart', 'game/mobile/lib/app.dart', 'game/mobile/lib/daily_panel.dart',
             'game/mobile/lib/calibration_screen.dart', 'game/mobile/lib/palette.dart',
             'game/mobile/test/content_presentation_test.dart', 'game/mobile/test/art_catalogue_test.dart']:
    if (ROOT / path).exists(): raw(path)

matrix = Path('release/content-presentation/full-matrix-repaired-20261021T143209447416Z')
ids = read(str(matrix / 'per-id-evidence.json'))
daily = []
for r in ids['identities']:
    if not r['id'].startswith('flow.daily.'): continue
    check(len(r['conditions']) == 12, r['id'] + '/' + r['state'] + ': 12 actual conditions')
    for item in r['conditions']:
        observation = read(item['report'])
        matches = [v for v in observation['rows'] if (v['id'], v['state'], v['route']) == (r['id'], r['state'], r['route'])]
        check(len(matches) == 1, r['id'] + ': exact actual row')
        row = matches[0]
        check(hashlib.sha256(json.dumps(row, ensure_ascii=False, separators=(',',':')).encode()).hexdigest() == item['row_sha256'], r['id'] + ': bound row hash')
        run = read(str(Path(item['report']).parent / 'run.json'))
        check(run['exit_code'] == 0, r['id'] + ': actual successful command')
        for path in ['game/mobile/lib/app.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/calibration_screen.dart']:
            if path.endswith('/app.dart'):
                archived = raw(str(Path(item['report']).parent / 'source' / path)).decode()
                current = raw(path).decode()
                def daily_region(text):
                    return text[text.index('  Widget _journal('):text.index('  bool get _hasAccountActions')]
                check(daily_region(archived) == daily_region(current), r['id'] + ': unchanged exact Journal and daily region; unrelated Rechart dialog changed')
            else:
                check(run['source_before'][path] == PINS[path], r['id'] + ': unchanged current UI source ' + path)
        daily.append({'id': r['id'], 'state': r['state'], 'condition': item['condition'], 'report': item['report'], 'flags': row.get('flags', row.get('assertions'))})

font = read('source/art/ui/font-manifest.json')
icon = font['runtime_icon_font']
check(hashlib.sha256(raw(icon['sdk_source'])).hexdigest() == icon['sdk_font_sha256'], 'Exact cached Material icon font')
notice = raw(icon['sdk_notice'])
check(hashlib.sha256(notice).hexdigest() == icon['sdk_notice_sha256'], 'Exact cached Material icon license')
check(raw(icon['bundled_notice']) == notice, 'Bundled notice is byte-identical to supplied SDK notice')
check('Attribution 4.0 International' in notice.decode(), 'Actual supplied license title recorded')
for path in ['game/mobile/lib/font_licenses.dart','game/mobile/lib/main.dart','game/mobile/pubspec.yaml',
             'game/mobile/test/font_licenses_test.dart','source/audio/score/tideglass.score.json',
             'tools/audio/render_score.py','source/audio/CREDITS.txt','release/audio/capability-and-rights.json']:
    raw(path)
check('registerFontLicenses();' in raw('game/mobile/lib/main.dart').decode(), 'Actual startup registers extra license')
check('    - assets/licenses/\n' in raw('game/mobile/pubspec.yaml').decode(), 'Actual bundle declares supplied notice directory')

soundtrack = read('game/assets/audio/audio.soundtrack/package.json')
package = ROOT / soundtrack['download_path']
check(hashlib.sha256(raw(soundtrack['download_path'])).hexdigest() == soundtrack['download_sha256'], 'Exact supporter soundtrack ZIP')
with zipfile.ZipFile(package) as z:
    zip_members = z.namelist()
    check(len(zip_members) == len(set(zip_members)), 'Soundtrack unique ZIP members')
    for name in ['harbor','current','dawn']:
        candidates = [p for p in zip_members if name in p and p.endswith('.wav')]
        check(len(candidates) == 1, name + ': one WAV soundtrack member')
        if candidates: check(z.read(candidates[0]) == raw(f'source/audio/masters/{name}.wav'), name + ': exact ambient master reused')
    credits = [p for p in zip_members if p.endswith('CREDITS.txt')]
    check(len(credits) == 1 and z.read(credits[0]) == raw('source/audio/CREDITS.txt'), 'Actual soundtrack carries authored credits')

source_drift = [p for p,h in PINS.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != h]
result = {'reviewer':'/root/client_asset_review','checks':CHECKS, 'source_pins':PINS, 'source_drift_during_review':source_drift,
          'asset_records':records,'source_kind_counts':dict(collections.Counter(p['source_kind'] for p in records)),
          'daily_rows':daily,'soundtrack_members':zip_members,
          'provenance_drift_assets':[r['asset_id'] for r in records if r['provenance_drift']],
          'host_flutter_executed':False,'native_exports_or_public_distribution_approved':False}
(HERE/'asset-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':len(CHECKS),'failed':[c for c in CHECKS if not c['passed']], 'source_drift_during_review':source_drift,
                  'provenance_drift_assets':len(result['provenance_drift_assets']),'source_kind_counts':result['source_kind_counts'],'daily_rows':len(daily)},indent=2))
