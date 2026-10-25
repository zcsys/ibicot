"""Bounded read-only reconciliation of original S18/S22; never invokes Flutter."""
from pathlib import Path
import collections, hashlib, json, re, struct, difflib, importlib.util

ROOT = Path('/Users/csys/Desktop/ibicot/idle')
OUT = Path(__file__).resolve().parent
checks, evidence = [], {}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    p = ROOT / p
    evidence[str(p.relative_to(ROOT))] = h(p)
    return json.loads(p.read_text())
def check(label, value):
    checks.append({'check': label, 'passed': bool(value)})
    if not value: raise AssertionError(label)
def pin(p):
    p = ROOT / p
    evidence[str(p.relative_to(ROOT))] = h(p)
    return p

pins = json.loads((OUT/'source-before.json').read_text())
manifest = read('implementation/content/launch_manifest.json')
scope = read('implementation/scope_requirements.json')
clauses = [r for r in scope['requirements'] if r['id'] in ['S18', 'S22']]
(OUT/'original-clauses.json').write_text(json.dumps(clauses, indent=2)+'\n')
candidate = read('.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/manifest.json')
current_bridged = []
for p, digest in pins.items():
    if p.startswith(('game/','services/')) and p in candidate['source_sha256']:
        check('current candidate binding '+p, h(ROOT/p)==digest==candidate['source_sha256'][p])
        check('archived candidate bytes '+p, h(Path(candidate['source_directory'])/p)==digest)
        current_bridged.append(p)

archive = read('game/content/narrative/archive.en.json')['entries']
check('18 unique main archive identities', len(archive)==18 and {x['id'] for x in archive}=={f'archive.main.{i:02}' for i in range(1,19)})
check('runtime archive is packaged exact source', pin('game/mobile/assets/progression/archive.en.json').read_bytes()==pin('game/content/narrative/archive.en.json').read_bytes())
for i, entry in enumerate(archive,1):
    row = next(x for x in manifest['main_archive'] if x['id']==entry['id'])
    check(entry['id']+' reachable chapter mapping',entry['chapter_id']==row['chapter_id']==f'chapter.{(i-1)//3+1:02}')
    check(entry['id']+' authored readable content', bool(entry['title'].strip()) and len(entry['text'].split())>=20)
campaign = read('game/content/progression/campaign.json')
check('campaign packaged exact source',pin('game/mobile/assets/progression/campaign.json').read_bytes()==pin('game/content/progression/campaign.json').read_bytes())
check('campaign has six ordered chapters', len(campaign['chapters'])==6)
for c in campaign['chapters']:
    check(c['id']+' no paid or economic reward', c['paid_requirements']==[] and c['economic_rewards']==[])
    check(c['id']+' optional purchases absent from objectives', all(g['kind'] in ['owned_min','stat_min','challenge_family_min'] for g in c['objectives']) and 'decoration' not in json.dumps(c['objectives']))

source=pin('game/mobile/lib/cosmetics.dart').read_text()
ids=re.findall(r'CosmeticDefinition\(\s*"([^"]+)"',source)
check('36 unique actual runtime IDs',len(ids)==len(set(ids))==36)
check('runtime matches manifest identities',{c['id'] for c in manifest['cosmetics']}==set(ids))
check('exact 6 chapter +6 decoration +10 free +10 premium +4 shop',collections.Counter(i.rsplit('.',1)[0] for i in ids)=={'cosmetic.core.chapter':6,'cosmetic.core.decoration':6,'cosmetic.free_pass':10,'cosmetic.premium_pass':10,'cosmetic.shop':4})
check('all manifest cosmetics have empty power effects',all(x['economic_effects']==[] for x in manifest['cosmetics']))
decorations=[x for x in manifest['cosmetics'] if '.decoration.' in x['id']]
check('six optional 50 Note decorations',len(decorations)==6 and all(x['unlock']=={'kind':'note_purchase','currency':'survey_notes','amount':50} for x in decorations))
check('six campaign rewards match catalogue',{c['reward_cosmetic_id'] for c in campaign['chapters']}=={i for i in ids if '.chapter.' in i})
season=read('game/events/content/season.01.json')
check('season packaged exact source',pin('game/mobile/assets/events/season.01.json').read_bytes()==pin('game/events/content/season.01.json').read_bytes())
rewards=[r for r in season['rewards'] if r['kind']=='cosmetic']
check('20 unique actual pass reward bindings',len(rewards)==20 and {r['content_id'] for r in rewards}=={i for i in ids if '_pass.' in i})
for r in rewards:
    mr=next(x for x in manifest['pass'][r['track']+'_rewards'] if x['id']==r['id'])
    check(r['id']+' exact runtime/manifest mapping',mr['reward']=={'kind':'cosmetic','content_id':r['content_id']} and mr['level']==r['level']==int(r['content_id'].rsplit('.',1)[1])*3 and r['economic_effects']==[])
spec=importlib.util.spec_from_file_location('reviewed_local_product_catalogue',ROOT/'services/tideglass_service/verification.py')
module=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=module
spec.loader.exec_module(module)
shop={f'cosmetic.shop.{i:02}' for i in range(1,5)}
check('four direct products map exact shop IDs',all(module.PRODUCTS[f'dev.tideglass.cosmetic.{i:02}']==[f'cosmetic.shop.{i:02}'] for i in range(1,5)))
check('supporter grants same four shop IDs and soundtrack only',set(module.PRODUCTS['dev.tideglass.supporter'])==shop|{'soundtrack.01'})
check('manifest supporter creates no art/power',set(manifest['supporter_bundle']['cosmetic_ids'])==shop and manifest['supporter_bundle']['new_unique_cosmetics']==0 and manifest['supporter_bundle']['economic_effects']==[])
png_hashes=[]
for identity in ids:
    desc=read('game/assets/cosmetics/'+identity+'.presentation.json')
    scene=read('source/art/cosmetics/'+identity+'.scene.json')
    check(identity+' actual renderer selector',desc['id']==scene['id']==scene['selector']==identity and desc['renderer_source']==scene['geometry_source']=='game/mobile/lib/cosmetic_art.dart' and desc['economic_effects']==[])
    for key in ['exported_overlay','exported_full_harbor_preview']:
        data=pin(desc[key]).read_bytes()
        check(identity+' actual PNG '+key,data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(640,388))
    png_hashes.append(h(ROOT/desc['exported_overlay']))
check('36 distinct exported overlays',len(set(png_hashes))==36)

artbase='release/qa/integration-art-matrix-20261021T123739647573Z'
artpins=read(artbase+'/source-before.json')
stable_art=[p for p in pins if p in artpins and p.startswith(('game/','services/')) and p not in ['game/mobile/lib/app.dart','game/mobile/lib/story_screen.dart','game/mobile/lib/season_screen.dart']]
for p in stable_art: check('unchanged art dependency '+p,pins[p]==artpins[p])
art_rows=0
for run in ['root-art-full-20261021T122040.006324Z','root-art-pseudo-full-20261021T122636.246158Z']:
    meta=read('release/native-proof/'+run+'/verification.json')
    p='release/art/catalogue-variants/'+run+'/matrix-results.json'
    report=read(p)
    check(run+' exact report digest',h(ROOT/p)==meta['art_report_sha256'])
    for result in meta['results']:
        log=pin('release/native-proof/'+run+'/'+result['name']+'.log')
        check(run+' completed '+result['name'],result['exit_code']==0 and h(log)==result['log_sha256'])
    rows=[r for r in report['rows'] if r['group']=='cosmetic']
    check(run+' 36 IDs across 12 display conditions',len(rows)==432 and len({(r['asset_id'],r['condition_id']) for r in rows})==432 and {r['asset_id'] for r in rows}=={'asset.'+i for i in ids})
    for r in rows:
        check(run+' '+r['asset_id']+' '+r['condition_id'],r['result']=='passed_bounded_host_case' and r['same_id_across_consumers'] and r['economic_state_unchanged_by_presentation_and_equip'] and r['actual_harbor_producer_and_purchase_bounds_unchanged'] and r['states']==['locked','owned','equipped'] and r['layout_exception'] is False)
    art_rows+=len(rows)

base=ROOT/'release/content-presentation/full-matrix-repaired-20261021T143209447416Z'
content_rows=0
content_pinmap=None
for d in sorted(base.iterdir()):
    if not (d/'run.json').exists(): continue
    run=read(str((d/'run.json').relative_to(ROOT)))
    check(d.name+' stable historical inputs',run['exit_code']==0 and run['source_before']==run['source_after'])
    if content_pinmap is None:content_pinmap=run['source_before']
    else:check(d.name+' same content input map',content_pinmap==run['source_before'])
    for path,digest in run['output_hashes'].items():check(d.name+' exact output '+path,h(pin(str((d/path).relative_to(ROOT))))==digest)
    events=[json.loads(x) for x in (d/'test.jsonl').read_text().splitlines() if x.startswith('{')]
    check(d.name+' terminal test stream success',events[-1]['type']=='done' and events[-1]['success'] is True and not any(x['type']=='error' for x in events))
    report=read(str((d/'observations.json').relative_to(ROOT)))
    rows=[r for r in report['rows'] if r['id'].startswith('asset.archive.main.') or r['id']=='asset.ending.main']
    check(d.name+' 18 locked +18 reflected + ending',len(rows)==37 and len({(r['id'],r['state']) for r in rows})==37)
    for r in rows:
        check(d.name+' exact assertions '+r['id']+' '+r['state'],all(v is True for v in r['assertions'].values()))
        check(d.name+' readable '+r['id']+' '+r['state'],all(t['complete_text'] and t['untruncated'] and t['all_lines_in_viewport'] for t in r['texts']))
    content_rows+=len(rows)
check('12 conditions with 444 relevant content rows',content_rows==444)
content_stable=[]
for p in pins:
    if p in content_pinmap and p.startswith(('game/','services/')) and p!='game/mobile/lib/app.dart':
        check('unchanged content dependency '+p,pins[p]==content_pinmap[p]);content_stable.append(p)
oldapp=base/'phone-100-en/source/game/mobile/lib/app.dart'
newapp=ROOT/'game/mobile/lib/app.dart'
(OUT/'app-bridge.patch').write_text(''.join(difflib.unified_diff(oldapp.read_text().splitlines(True),newapp.read_text().splitlines(True),fromfile=str(oldapp),tofile=str(newapp))))
for anchor in ['Widget _settings', 'Widget _harbor']:
    # Informational anchors only; the full archived diff is manually reviewed.
    pass
core_paths=['game/mobile/lib/game_controller.dart','game/mobile/lib/story_state.dart','game/mobile/lib/cosmetics.dart','game/mobile/lib/cosmetic_art.dart','game/mobile/lib/cosmetics_screen.dart','game/mobile/lib/harbor_art.dart','game/mobile/lib/service_cosmetics.dart','game/events/lib/src/pass.dart','game/progression/lib/tideglass_progression.dart']
check('ownership/render/claim inputs all unchanged from reviewed art',all(p in stable_art for p in core_paths))
for p in ['release/qa/lead-content-matrix-20261021T144134.921859Z/verification.json',artbase+'/verification.json','release/qa/integration-optional-calibration-20261021T110210355242Z/verification.json','release/qa/integration-optional-calibration-20261021T110210355242Z/pure-reproductions.json','release/balance/optional-calibration-current-integration.json','release/qa/qa-provenance-version-20261023T031648.974649Z/PROVENANCE_REVIEW.md','release/qa/qa-reset-20261023T025256.370588Z/RESET_REVIEW.md','release/qa/lead-daily-icons-20261023T031715.308630Z/REVIEW.md','release/native-proof/20261023T040548.338966Z/build-report.json']:
    pin(p)
bridge=read('release/balance/optional-calibration-current-integration.json')
for p in ['game/content/progression/campaign.json','game/mobile/lib/story_state.dart','game/mobile/lib/game_controller.dart','game/progression/test/progression_test.dart']:
    check('reviewed optional ending bridge '+p,h(ROOT/p)==bridge['source_sha256'][p])
events=[json.loads(x) for x in (OUT/'focused-dart.jsonl').read_text().splitlines() if x.startswith('{')]
check('independent focused run terminal success',events[-1]['type']=='done' and events[-1]['success'] is True and not any(x['type']=='error' for x in events))
tests=[x for x in events if x['type']=='testDone' and not x.get('hidden',False)]
check('exact three independent focused test cases',len(tests)==3 and all(x['result']=='success' and not x['skipped'] for x in tests))
after={p:h(ROOT/p) for p in pins}
(OUT/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
check('review did not alter pinned source or canonical metadata',pins==after)
(OUT/'evidence-pins.json').write_text(json.dumps(evidence,indent=2)+'\n')
(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
result={'reviewer':'/root/qa_release','all_passed':True,'checks':len(checks),'source_inputs':len(pins),'evidence_inputs':len(evidence),'current_candidate_bound_files':len(current_bridged),'unchanged_art_inputs':len(stable_art),'unchanged_content_inputs':len(content_stable),'historical_cosmetic_rows_reconciled':art_rows,'historical_archive_ending_rows_reconciled':content_rows,'new_direct_Dart_tests':3,'new_Flutter_or_native_runs':0,'canonical_edits':False,'recommended_scope':['S18','S22'],'package_asset_native_provider_or_release_acceptance':False}
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
