#!/usr/bin/env python3
"""Source/evidence inventory only. No runtime, art, economic or acceptance edits.
Run from repository root. Baseline is captured once and never rewritten here.
"""
import collections, copy, hashlib, json, pathlib, re, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'release/content-evidence'
def read(p): return json.loads((ROOT / p).read_text())
def digest(p):
    p=ROOT/p
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def write(name, data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def file(p): return {'path':p,'exists':(ROOT/p).is_file(),'sha256':digest(p)}
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values(): yield from walk(x)
    elif isinstance(v,list):
        for x in v: yield from walk(x)
M='implementation/content/launch_manifest.json'
C='implementation/art/production_contract.json'
base=read('release/content-evidence/inventory-baseline-manifest.json')
contract=read(C); manifest=copy.deepcopy(base)
contract_hash=digest(C)
contracts={a['asset_id']:a for a in contract['assets']}
assets={a['id']:a for a in manifest['assets']}
assert len(assets)==len(contracts)==164 and set(assets)==set(contracts)
rows=[]
R={
 'integrated':'release/qa/integration-final-20261016T105843545492Z/INTEGRATION_REVIEW.md',
 'help':'release/qa/integration-help-repaired-20261021T101942186162Z/HELP_REPAIRED_REVIEW.md',
 'ownership':'release/qa/integration-native-ownership-repaired-20261019T145035575220Z/NATIVE_OWNERSHIP_REPAIRED_REVIEW.md',
 'producer':'release/art/producer-independent-review.md',
 'story':'release/client-story-review.md',
 'season':'release/client-season-review.md',
 'cosmetic':'release/cosmetics-author-review.md',
 'audio':'release/audio/IMPLEMENTATION_HANDOFF.md',
 'localization':'release/localization-author-review.md',
 'native':'release/native-proof/main-launch-20261021T103014.378318Z/main-launch.json',
 'native_visual':'release/native-proof/main-launch-20261021T103014.378318Z/lead-visual-review.json',
 'store':'release/store/CLIENT_REVIEW.md',
}
common='Original ART-V01–V07 obligations remain binding; evidence cited below supports only its explicitly tested snapshot/cases. No complete per-asset native/variant/performance/editorial approval is recorded.'
campaign=read('game/content/progression/campaign.json'); archive=read('game/content/narrative/archive.en.json'); season=read('game/events/content/season.01.json')
chapters={x['id']:x for x in campaign['chapters']}; entries={x['id']:x for x in archive['entries']}; rewards={x['content_id']:x for x in season['rewards']}
semantic=[]
def equal(label,a,b):
    ok=a==b;semantic.append({'check':label,'passed':ok});assert ok,label
# Bundled content is checked byte-for-byte, not inferred from a matching name.
pairs=[('game/content/progression/campaign.json','game/mobile/assets/progression/campaign.json'),('game/content/narrative/archive.en.json','game/mobile/assets/progression/archive.en.json'),('game/events/content/season.01.json','game/mobile/assets/events/season.01.json'),('economy.json','game/mobile/assets/config/economy.json')]
for pattern, dest in [('game/content/challenges/*.json','game/mobile/assets/challenges'),('game/content/calibrations/*.pattern.json','game/mobile/assets/calibrations')]:
    for p in sorted(ROOT.glob(pattern)): pairs.append((str(p.relative_to(ROOT)),dest+'/'+p.name))
for a,b in pairs: equal('source/bundle bytes '+b,digest(a),digest(b))

def provenance_check(path):
    if not (ROOT/path).is_file():return {'path':path,'present':False,'missing_required_fields':contract['provenance_record_required_fields'],'hashes':[],'independent_reviewer_recorded':False}
    p=read(path); checks=[]
    for paths_key,hash_key in [('source_media_paths','source_media_sha256'),('exported_paths','exported_sha256')]:
        paths=p.get(paths_key,[]); expected=p.get(hash_key,{})
        for i,q in enumerate(paths):
            old=expected.get(q) if isinstance(expected,dict) else expected[i] if i<len(expected) else None
            actual=digest(q);checks.append({'path':q,'recorded_sha256':old,'current_sha256':actual,'matches':bool(old and old==actual)})
    return {'path':path,'present':True,'sha256':digest(path),'missing_required_fields':[k for k in contract['provenance_record_required_fields'] if k not in p], 'hashes':checks,'independent_reviewer_recorded':bool(p.get('reviewer') and p.get('review_evidence')),'basis':p.get('license_or_authorship_basis'),'rights_approval_inferred':False}

for aid,a in assets.items():
    c=contracts[aid]; eid=c['manifest_entity_ids'][0]
    authored=[]; bundle=[]; code=[]; evidence=[]; checks=[]; limits=[]; scopes=[]; selector=eid
    if aid.startswith('asset.chapter.'):
        authored=['game/content/progression/campaign.json'];bundle=['game/mobile/assets/progression/campaign.json'];code=['game/mobile/lib/story_state.dart','game/mobile/lib/story_screen.dart','game/progression/lib/tideglass_progression.dart'];scopes=['S15','S44'];evidence=[R['story'],R['integrated'],R['localization']]
        exported=read(c['export_descriptor_path']);item=chapters[eid]
        for k in ['title','intro','completion','hints']: equal(aid+' export '+k,exported[k],item[k])
        limits=['Current source has six sequential objectives, hints, completion and cosmetic-only restoration rewards. Later-chapter natural 15–30-day pacing and observed strategy viability remain separate human/calendar gates.']
    elif aid=='asset.ending.main':
        authored=['game/content/progression/campaign.json'];bundle=['game/mobile/assets/progression/campaign.json'];code=['game/mobile/lib/story_screen.dart','game/progression/lib/tideglass_progression.dart'];scopes=['S15','S44'];evidence=[R['story'],R['integrated']]
        exported=read(c['export_descriptor_path'])
        for k in ['title','text']:equal(aid+' export '+k,exported[k],campaign['ending'][k])
        limits=['Actual ending and continued play are implemented; observed human pacing and comprehension are unqualified.']
    elif aid.startswith('asset.challenge.'):
        authored=[f'game/content/challenges/{eid}.json'];bundle=[f'game/mobile/assets/challenges/{eid}.json'];code=['game/mobile/lib/story_screen.dart','game/mobile/lib/game_controller.dart','game/progression/lib/tideglass_progression.dart'];scopes=['S16','S44'];evidence=[R['story'],R['integrated'],'release/progression-review.md']
        exported=read(c['export_descriptor_path']);item=read(authored[0])
        for k in ['title','intro','completion']:equal(aid+' export '+k,exported[k],item[k])
        limits=['100-Note first entry, owned free replay, explicit replace/restart and isolated fleet exist. Two policies have deterministic tests; no observed player strategy/pacing claim.']
    elif aid.startswith('asset.calibration.'):
        authored=[f'game/content/calibrations/{eid}.pattern.json'];bundle=[f'game/mobile/assets/calibrations/{eid}.pattern.json'];code=['game/mobile/lib/calibration_pattern.dart','game/mobile/lib/calibration_screen.dart','game/mobile/lib/game_controller.dart','game/core/lib/src/daily_engine.dart'];scopes=['S17','S26'];evidence=[R['integrated'],R['localization']]
        item=read(authored[0]);exported=read(c['export_descriptor_path'])
        if aid.endswith('.accessible_copy'):
            for k in ['title','intro','instructions','accessible_label','accessible_description']:equal(aid+' export '+k,exported[k],item[k])
        else:equal(aid+' complete pattern export',exported,item)
        limits=['Untimed node route and accessible completion use the same controller/core command and Focus reward. Required native input/screen-reader/variant matrix remains open.']
    elif aid.startswith('asset.archive.main.'):
        authored=['game/content/narrative/archive.en.json'];bundle=['game/mobile/assets/progression/archive.en.json'];code=['game/mobile/lib/story_state.dart','game/mobile/lib/story_screen.dart','game/mobile/lib/game_controller.dart'];scopes=['S18'];evidence=[R['story'],R['integrated'],R['localization']]
        exported=read(c['export_descriptor_path'])
        for k in ['title','text']:equal(aid+' export '+k,exported[k],entries[eid][k])
        limits=['All 18 authored entries are guarded by chapter unlock and explicit read callbacks; full per-entry phone/tablet scaling/editorial qualification is not recorded.']
    elif aid.startswith('asset.archive.season01.'):
        authored=['game/events/content/season.01.json'];bundle=['game/mobile/assets/events/season.01.json'];code=['game/mobile/lib/season_screen.dart','game/mobile/lib/story_state.dart','game/events/lib/src/pass.dart'];scopes=['S21'];evidence=[R['season'],R['integrated'],R['localization']]
        equal(aid+' reward kind',rewards[eid]['kind'],'archive_fragment');checks=['Exact content_id exists in the 30-level reward table with nonempty authored title/body.'];assert rewards[eid]['title'] and rewards[eid]['body'];selector='rewards[content_id='+eid+']'
        limits=['Actual claimed fragment reading is integrated. Original separate text source/export/provenance descriptors have not been published; full variant/native editorial coverage remains open.']
    elif aid.startswith('asset.harbor.'):
        authored=['game/mobile/lib/harbor_art.dart'];code=authored+['game/mobile/lib/app.dart','game/mobile/lib/story_screen.dart'];scopes=['S19'];evidence=[R['story'],R['native'],R['native_visual']];selector='HarborArt restoration='+('0' if eid.endswith('unlit') else str(int(eid[-2:])))
        limits=['Code-native seven-state painter changes dawn gradient, constellations and quay lamps for restoration 0–6. Initial state is the unrestored harbor, not an entirely dark canvas. Contract scene/export/provenance descriptors and complete 7-state device/variant/performance qualification remain absent. Native launch evidence shows only observed initial/current states.']
    elif aid.startswith('asset.producer.'):
        authored=[c['source_descriptor_path'],'game/mobile/lib/producer_art.dart','game/mobile/lib/producer_art_data.dart'];code=['game/mobile/lib/app.dart','game/mobile/lib/season_screen.dart','game/mobile/lib/producer_art.dart'];scopes=['S19'];evidence=[R['producer'],R['integrated'],R['audio']]
        limits=['All 25 stage geometries exist at thresholds 0/25/50/75/100; main and seasonal cards integrate staged art. Harbor and challenge miniatures retain base silhouettes. Independent host visual review does not qualify every named target/scale/selected/locked/native performance variant.']
    elif aid.startswith('asset.cosmetic.'):
        authored=[c['source_descriptor_path'],'game/mobile/lib/cosmetics.dart','game/mobile/lib/cosmetic_art.dart'];code=['game/mobile/lib/cosmetics_screen.dart','game/mobile/lib/app.dart','game/mobile/lib/season_screen.dart','game/mobile/lib/service_cosmetics.dart','game/mobile/lib/game_controller.dart'];scopes=['S22'];evidence=[R['cosmetic'],R['ownership'],R['localization']]
        if '.decoration.' in aid:scopes+=['S18']
        if '.free_pass.' in aid or '.premium_pass.' in aid:scopes+=['S21']
        if '.premium_pass.' in aid or '.shop.' in aid:scopes+=['S24']
        equal(aid+' catalogue binding',eid in (ROOT/'game/mobile/lib/cosmetics.dart').read_text(),True)
        limits=['Preview and equipped overlay invoke the same drawCosmetic geometry; six Note decorations coexist with one earned/verified appearance. Author render/host tests and source integration are present; full independent 36-item per-variant/native/performance/rights approval is not. Paid entries additionally require actual store/provider qualification; local verified-lease fixtures are not purchases.']
    elif aid.startswith('asset.audio.'):
        authored=[a['source_path']];p=read(c['provenance_path']);authored+=p['source_media_paths'];code=['game/mobile/lib/audio_bus.dart','game/mobile/lib/audio_settings.dart','game/mobile/lib/game_controller.dart','game/mobile/lib/app.dart'];scopes=['S23'];evidence=[R['audio'],R['integrated'],'release/audio/capability-and-rights.json','release/qa/integration-repair-20261016T105414563144Z/audio-independent-integrity.json']
        exported=p['exported_paths']
        if eid=='audio.soundtrack':
            code+=['game/mobile/lib/service_cosmetics.dart','game/platform/lib/soundtrack_delivery.dart'];bundle=['release/downloads/tideglass-original-soundtrack.zip'];evidence+=[R['ownership']];scopes+=['S24']
        else:
            for q in exported:
                if q.endswith('.m4a'):
                    target='game/mobile/assets/audio/'+pathlib.Path(q).name;bundle.append(target);equal(aid+' audio bundle bytes '+target,digest(q),digest(target))
        limits=['Original score/synthesis and real masters/exports are present, with independent host decode/hash checks. Human speaker/headphone listening, actual both-platform decoder/interruption qualification, owner distribution terms and full package performance remain open. Soundtrack adds configured authenticated fixture delivery, not a hosted service or real store transaction.']
    elif aid=='asset.season.01.copy':
        authored=['game/events/content/season.01.json'];bundle=['game/mobile/assets/events/season.01.json'];code=['game/mobile/lib/season_screen.dart','game/mobile/lib/story_state.dart'];scopes=['S20','S21'];evidence=[R['season'],R['integrated'],R['ownership'],R['localization']];selector='title, copy, milestones, rewards'
        limits=['Authored lifecycle/pass/premium/archive copy is used by the real screen. Source/export/provenance descriptors are not yet published at original paths; actual 28-day observation and public rollout are absent.']
    elif aid=='asset.season.01.presentation':
        authored=['game/mobile/lib/season_screen.dart'];code=authored+['game/mobile/lib/harbor_art.dart','game/mobile/lib/producer_art.dart','game/mobile/lib/cosmetic_art.dart'];scopes=['S20','S21','S19'];evidence=[R['season'],R['cosmetic']];selector='SeasonScreen fleet, milestone harbor and real reward previews'
        limits=['Actual season composition is authored using the shared harbor, staged fleet and appearance previews. No distinct registered scene/export/provenance descriptor exists for this presentation, and required equipped/preview/thumbnail/native variants are not independently accepted. Reuse is not a new unique cosmetic.']
    elif aid.startswith('asset.support.'):
        scopes=['S27'];purpose=eid.split('.')[-1]
        if purpose in ['help','recovery_guide','release_notes','credits']:
            authored=['game/mobile/lib/help_content.dart'];code=['game/mobile/lib/help_screen.dart','game/mobile/lib/app.dart'];evidence=[R['help'],'release/help-author-review.md',R['localization']];selector={'help':'HelpCopy: play/rechart/away/notes','recovery_guide':'HelpTopic.recovery','release_notes':'HelpTopic.releaseNotes','credits':'HelpTopic.credits'}[purpose]
            limits=['Current handbook is integrated; repaired Away clock wording has independent pure/source review. Original separate source/export/provenance documents are absent. Actual physical accessibility/comprehension and full native topic matrix remain open. Credits do not establish legal exclusivity or owner distribution terms.']
        elif purpose=='operations_runbooks':
            authored=['release/runbooks/README.md','release/runbooks/LAUNCH_HANDOVER.md','release/runbooks/launch-coverage-template.json','services/docs/OPERATIONS.md','services/docs/FULFILLMENT.md','services/docs/PRIVACY.md'];scopes+=['S37','S38'];selector='Internal runbook package';limits=['Internal instructions, local recovery/rehearsal and blank 14-day coverage template are authored. No named coverage, live alerts, qualified host, operator approval or actual 14-day operations; original descriptor/provenance and independent document acceptance pending.']
        elif purpose=='season02_brief':
            authored=['release/season-2-brief.md'];scopes+=['S37','S38'];selector='Initial B21/M7-01 internal brief';limits=['Initial prelaunch brief is authored, not Season 2 game content. Separate B23/M7-08/OPS-14 update requires actual 14-day launch findings. Original source/provenance record and independent initial document acceptance pending.']
        else:
            limits=['No configured/publicly hosted '+('privacy policy' if purpose=='privacy_page' else 'support page')+' exists. Internal services/docs/PRIVACY.md and handbook limitations are related implementation information, not this deliverable. Public ownership/contact, actual provider/data behavior and working URL review remain required.'];checks=['Manifest remains unproduced with null source and verification; no substitute public page invented.']
    else:raise AssertionError('Unmapped asset '+aid)
    assert all((ROOT/p).is_file() for p in code), (aid,code)
    assert all((ROOT/p).is_file() for p in authored+bundle), (aid,authored,bundle)
    if authored:
        a['delivery_status']='in_production'
        if not a.get('source_path'):a['source_path']=authored[0]
    a['verification_evidence']=None
    if aid.startswith('asset.harbor.') or aid=='asset.season.01.presentation':a['runtime_source']=authored[0]
    a['production_evidence']='release/content-evidence/inventory-assets.json'
    desc={k:file(c[k]) for k in ['source_descriptor_path','export_descriptor_path','provenance_path','verification_path']}
    prov=provenance_check(c['provenance_path'])
    incomplete=[k for k,v in desc.items() if not v['exists']]
    if incomplete:limits.append('Original contract paths absent: '+', '.join(incomplete)+'. Actual implementation paths are recorded without silently waiving or rewriting the contract.')
    drift=[x['path'] for x in prov['hashes'] if not x['matches']]
    if drift:limits.append('Provenance hash drift/missing export: '+', '.join(drift)+'. Re-pin/regenerate and independently review before verification.')
    if not prov['independent_reviewer_recorded']:limits.append('Per-asset provenance independent reviewer/review evidence is not recorded.')
    evidence=[p for p in evidence if (ROOT/p).is_file()]
    row={'asset_id':aid,'entity_ids':c['manifest_entity_ids'],'scope_ids':sorted(set(scopes)),'kind':a['kind'],'before_status':base['assets'][list(assets).index(aid)]['delivery_status'],'after_status':a['delivery_status'],'original_contract':{'category':c['category'],'method':c['method'],'initial_delivery_work_item':c['initial_delivery_work_item'],'initial_delivery_batch':c['initial_delivery_batch'],'delivery_channel':c.get('delivery_channel','client_package'),'required_variants':c['required_variants'],'paths':desc},'source_selector':selector,'authored_sources':[file(p) for p in dict.fromkeys(authored)],'runtime_or_download_bundle':[file(p) for p in dict.fromkeys(bundle)],'integration_sources':[file(p) for p in dict.fromkeys(code)],'provenance':prov,'review_evidence':[file(p) for p in dict.fromkeys(evidence)],'source_checks':checks,'remaining_obligations':limits+[common],'verification_decision':'Not verified: original per-asset acceptance is not completely satisfied.','reviewed_as':'Inventory reconciliation, not authoring rights approval or asset acceptance.'}
    rows.append(row)

# Authored content IDs and reward tables are checked against the fixed manifest.
equal('chapter IDs', list(chapters), [x['id'] for x in manifest['chapters']])
equal('main archive IDs', list(entries), [x['id'] for x in manifest['main_archive']])
equal('season fragment IDs', [x['content_id'] for x in season['rewards'] if x['kind']=='archive_fragment'], [x['id'] for x in manifest['season_fragments']])
for slot in manifest['pass']['free_rewards']+manifest['pass']['premium_rewards']:
    item=next(x for x in season['rewards'] if x['id']==slot['id'])
    equal(slot['id']+' authored level', item['level'], slot['level'])
    equal(slot['id']+' authored reward', {'kind':item['kind'],'content_id':item['content_id']}, slot['reward'])

# All status propagation is descriptive. No economic/ID/reward mutation.
for rec in walk(manifest):
    if 'production_status' in rec and 'asset_refs' in rec:
        if any(assets[x]['delivery_status']=='in_production' for x in rec['asset_refs']):rec['production_status']='in_production'
        if rec.get('copy_status')=='not_authored' and rec['production_status']=='in_production':rec['copy_status']='in_production'
for r in manifest['producer_families']:r['production_status']='in_production'
manifest['season']['production_status']='in_production';manifest['pass']['production_status']='in_production'
for r in manifest['pass']['free_rewards']+manifest['pass']['premium_rewards']:r['production_status']='in_production'
manifest['supporter_bundle']['production_status']='in_production';manifest['supporter_bundle']['fulfillment_status']='in_progress'
ui_map={
'harbor_and_producers':(['app.dart','harbor_art.dart','producer_art.dart'],['S19']),
'purchase_modes_and_network_value':(['app.dart','game_controller.dart'],['S03','S04','S07']),
'rechart_preview':(['app.dart','game_controller.dart'],['S05']),
'automation_plans':(['daily_panel.dart','game_controller.dart'],['S06']),
'forecasts':(['app.dart','number_format.dart'],['S07','S26']),
'offline_return':(['app.dart','offline_replay.dart'],['S08','S12']),
'calibration_accessible_choice':(['calibration_screen.dart','calibration_pattern.dart'],['S09','S17','S26']),
'surveys':(['app.dart','game_controller.dart'],['S10']),
'contracts_and_backlog':(['daily_panel.dart','game_controller.dart'],['S11']),
'archive_and_challenges':(['story_screen.dart','game_controller.dart'],['S16','S18','S44']),
'season_start_end_archive':(['season_screen.dart','game_controller.dart'],['S20','S21']),
'pass_selection_and_claims':(['season_screen.dart','game_controller.dart'],['S21']),
'shop_preview_and_purchase':(['cosmetics_screen.dart','service_cosmetics.dart','native_services.dart'],['S22','S24']),
'purchase_restore_and_pending':(['service_cosmetics.dart','native_services.dart','soundtrack_export.dart'],['S23','S24']),
'save_conflict_and_recovery':(['bootstrap.dart','service_settings.dart'],['S02','S12','S13','S27','S39']),
'settings_and_notifications':(['app.dart','notification_settings.dart','audio_settings.dart'],['S26']),
'help_and_support':(['help_screen.dart','help_content.dart'],['S27'])}
uis=[]
for r in manifest['ui_flows']:
    key=r['id'].removeprefix('ui.');paths,scope=ui_map[key];paths=['game/mobile/lib/'+p for p in paths if (ROOT/('game/mobile/lib/'+p)).is_file()]
    partial=key in ['shop_preview_and_purchase','purchase_restore_and_pending','help_and_support']
    r['production_status']='in_production';r['implementation_status']='in_progress' if partial else 'implemented';r['production_evidence']='release/content-evidence/inventory-records.json'
    # Acceptance fields remain null; implemented code does not imply accepted UI.
    r['acceptance_evidence']=None;r['verification_evidence']=None
    uis.append({'ui_id':r['id'],'scope_ids':scope,'implementation_status':r['implementation_status'],'sources':[file(p) for p in paths],'remaining':'Real provider/public support delivery and target qualification remain open.' if partial else 'Host implementation present; original complete target/accessibility/acceptance requirements remain open.'})
manifest['status']='authored_inventory_reconciled_acceptance_pending'
manifest['scope_policy']='All original IDs, counts and economic rules are preserved. Source-backed authored content is in_production; no item is promoted to verified by file existence or host tests. Public privacy/support pages remain unproduced. Original per-asset native, variant, provenance, rights, editorial and release gates remain binding.'
manifest['inventory_evidence']='release/content-evidence/inventory-assets.json';manifest['release_ready']=False
# Economics / IDs and other substantive content must be identical, recursively.
ignored={'production_status','delivery_status','source_path','verification_evidence','license_evidence','runtime_source','production_evidence','status','scope_policy','inventory_evidence','copy_status','implementation_status','acceptance_evidence','fulfillment_status'}
def invariant(v):
    if isinstance(v,dict):return {k:invariant(x) for k,x in v.items() if k not in ignored}
    if isinstance(v,list):return [invariant(x) for x in v]
    return v
equal('all non-inventory manifest fields unchanged',invariant(base),invariant(manifest))
equal('asset IDs/order/count unchanged',[a['id'] for a in base['assets']],[a['id'] for a in manifest['assets']])
equal('production contract untouched',contract_hash,digest(C))
(ROOT/M).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
write('inventory-assets.json',{'schema_version':1,'review_date':'2026-10-21','purpose':'Exhaustive forward reconciliation of 164 launch assets; no asset acceptance inferred.','manifest':file(M),'contract':file(C),'status_counts':dict(collections.Counter(a['after_status'] for a in rows)),'assets':rows})
write('inventory-records.json',{'ui_flows':uis,'records':[{'entity_id':r['id'],'production_status':r['production_status'],'asset_refs':r.get('asset_refs',[]),'verification_evidence':r.get('verification_evidence')} for r in walk(manifest) if 'production_status'in r], 'supporter_bundle':{'source_files':[file(p) for p in ['game/mobile/lib/service_cosmetics.dart','game/mobile/lib/native_services.dart','game/mobile/lib/soundtrack_export.dart','game/platform/lib/soundtrack_delivery.dart'] if (ROOT/p).is_file()],'implemented':'Verified ownership projection, configured offer gating and authenticated fixture download/export are authored.','open':'Actual stores/provider transactions, public host and human/native/rights acceptance remain unproven.'}})
write('inventory-source-checks.json',{'assertions':semantic,'count':len(semantic),'all_passed':all(x['passed'] for x in semantic),'contract_sha256':contract_hash,'baseline_manifest':file('release/content-evidence/inventory-baseline-manifest.json'),'new_manifest':file(M)})

# Reverse: every declared runtime asset, project Dart source, content export,
# native app-icon member and store creative is classified (not SDK binaries).
reverse={}
def add(path,role,ids=(),scopes=(),note=''):
    if not (ROOT/path).is_file():return
    v=reverse.setdefault(path,dict(file(path),roles=[],asset_ids=[],scope_ids=[],notes=[]))
    if role not in v['roles']:v['roles'].append(role)
    v['asset_ids']=sorted(set(v['asset_ids'])|set(ids));v['scope_ids']=sorted(set(v['scope_ids'])|set(scopes))
    if note and note not in v['notes']:v['notes'].append(note)
for r in rows:
    for key,role in [('authored_sources','authoring_source'),('runtime_or_download_bundle','runtime_bundle_or_external_soundtrack'),('integration_sources','compiled_integration')]:
        for f in r[key]:add(f['path'],role,[r['asset_id']],r['scope_ids'])
    for k,v in r['original_contract']['paths'].items():
        if k!='verification_path' and v['exists']:add(v['path'],'original_contract_'+k,[r['asset_id']],r['scope_ids'])
    if r['provenance']['present']:
        for f in r['provenance']['hashes']:add(f['path'],'provenance_source_or_export',[r['asset_id']],r['scope_ids'])
for u in uis:
    for f in u['sources']:add(f['path'],'ui_flow_implementation',scopes=u['scope_ids'],note=u['ui_id'])
asset_dirs=re.findall(r'^    - (assets/[^\n]+)',(ROOT/'game/mobile/pubspec.yaml').read_text(),re.M)
for d in asset_dirs:
    for p in sorted((ROOT/'game/mobile'/d).rglob('*')):
        if p.is_file():
            rel=str(p.relative_to(ROOT));add(rel,'declared_mobile_bundle')
            if not reverse[rel]['asset_ids']:add(rel,'supporting_configuration',scopes=['S02','S03','S20'],note='Frozen economy, content digests/schedule or configuration; supporting data, not an additional unique launch asset.')
package_scope={'core':['S03','S04','S05','S06','S07','S08','S09','S10','S11','S14','S25'],'persistence':['S02','S12','S13','S27','S39'],'progression':['S15','S16','S18','S44'],'events':['S20','S21'],'platform':['S02','S23','S24','S25','S27','S39'],'mobile':['S02','S26','S27','S39']}
for package,scope in package_scope.items():
    for p in sorted((ROOT/f'game/{package}/lib').rglob('*.dart')):
        rel=str(p.relative_to(ROOT));add(rel,'project_runtime_dart',scopes=scope,note='Supporting implementation; package-level reverse scope classification is not independent acceptance of every function.')
for pattern in ['game/mobile/ios/Runner/Assets.xcassets/**','game/mobile/android/app/src/main/res/mipmap*/**','game/mobile/macos/Runner/Assets.xcassets/**','release/store/creative/**','game/client/art/app-icon*']:
    for p in sorted(ROOT.glob(pattern)):
        if p.is_file():add(str(p.relative_to(ROOT)),'app_identity_or_store_creative',scopes=['S43'],note='App identity/store supporting creative is outside the fixed 164 content IDs; no new cosmetic or content reward is counted. macOS is internal only.')
internal=[str(p.relative_to(ROOT)) for p in (ROOT/'release/runbooks').rglob('*') if p.is_file()]+['release/season-2-brief.md']
bundled=[p for p,v in reverse.items() if 'declared_mobile_bundle' in v['roles']]
equal('internal operations/Season2 absent from declared client assets',not any('runbook' in p.lower() or 'season-2' in p.lower() or 'season02_brief' in p.lower() for p in bundled),True)
write('inventory-reverse.json',{'boundary':'Every file under declared app asset directories; all project Dart runtime files in six packages; all original per-asset source/export/provenance members; native app-icon catalogs and store creative. Generated framework/plugin/SDK binaries are dependency components, not new original content assets. This is a source/bundle declaration audit, not final signed-app binary extraction.','declared_asset_directories':asset_dirs,'declared_mobile_asset_count':len(bundled),'reverse_file_count':len(reverse),'internal_release_files':internal,'files':[reverse[p] for p in sorted(reverse)]})

# Compare exact previously pinned files to this source tree. A matching file alone
# never carries an old report's entire behavioral acceptance to newer integration.
pins=['release/qa/integration-final-20261016T105843545492Z/snapshot.json','release/qa/integration-native-ownership-repaired-20261019T145035575220Z/snapshot.json','release/qa/integration-help-repaired-20261021T101942186162Z/snapshot.json']
comparisons=[]
for p in pins:
    j=read(p); records=[]
    for path,sha in j['files'].items():
        if path not in reverse:continue
        records.append({'path':path,'pinned_sha256':sha,'current_sha256':digest(path),'exact_match':sha==digest(path)})
    comparisons.append({'snapshot':file(p),'matching':sum(x['exact_match'] for x in records),'changed_or_missing':sum(not x['exact_match'] for x in records),'files':records,'limit':'Exact file equality only. Changed integration is not retested here; read the original report limitations.'})
write('inventory-evidence-binding.json',{'reviews':[file(p) for p in R.values() if (ROOT/p).is_file()],'comparisons':comparisons,'new_tests_run':'Only Python inventory assertions and existing manifest validator modes. No Flutter/native build or behavior suite rerun in this lane.'})
# Persist final assertions including reverse packaging check.
write('inventory-source-checks.json',{'assertions':semantic,'count':len(semantic),'all_passed':all(x['passed'] for x in semantic),'contract_sha256':contract_hash,'baseline_manifest':file('release/content-evidence/inventory-baseline-manifest.json'),'new_manifest':file(M)})
print(json.dumps({'assets':len(rows),'status_counts':dict(collections.Counter(a['after_status'] for a in rows)),'source_checks':len(semantic),'reverse_files':len(reverse),'declared_bundle_files':len(bundled),'provenance_present':sum(r['provenance']['present'] for r in rows),'provenance_hash_drift_assets':sum(any(not x['matches'] for x in r['provenance']['hashes']) for r in rows),'descriptor_missing_assets':sum(any(not f['exists'] for k,f in r['original_contract']['paths'].items() if k!='verification_path') for r in rows)},indent=2))
