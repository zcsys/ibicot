#!/usr/bin/env python3
"""Read-only production inventory; writes only this staged review directory."""
from pathlib import Path
import collections, datetime, difflib, hashlib, json

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
PREFIX = STAGE.relative_to(ROOT).as_posix()
INPUTS = {}
RAW = {}
DIFFS = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, data):
    out = STAGE / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def pin(path):
    path = str(path)
    if path not in INPUTS:
        f = ROOT / path
        data = f.read_bytes() if f.is_file() else None
        rec = {'path': path, 'exists': data is not None, 'sha256': sha(data) if data is not None else None}
        if data is not None:
            # Preserve exact reviewable text inputs. Media remain hash-bound in place;
            # no new render or converted audio is manufactured by this bridge.
            if len(data) < 2_000_000 and b'\0' not in data:
                try:
                    data.decode('utf-8')
                    dest = STAGE / 'snapshot' / path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    rec['snapshot_path'] = str(dest.relative_to(ROOT))
                except UnicodeDecodeError:
                    pass
            RAW[path] = data
        INPUTS[path] = rec
    return dict(INPUTS[path])


def read(path):
    pin(path)
    return json.loads(RAW[path])


def hash_pairs(p, paths_key, hashes_key):
    paths, values = p.get(paths_key, []), p.get(hashes_key, {})
    return list(zip(paths, values)) if isinstance(values, list) else list(values.items())


def delta(path, expected, old_path=None):
    now = pin(path)
    result = {'path': path, 'recorded_sha256': expected, 'current_sha256': now['sha256'],
              'relation': 'byte_identical' if now['sha256'] == expected else 'changed' if now['exists'] else 'missing'}
    if result['relation'] == 'changed' and old_path:
        before = pin(old_path)
        if before['sha256'] == expected:
            result['historical_source'] = before
            key = sha((path + expected + now['sha256']).encode())[:20]
            dp = f'diffs/{key}.diff'
            if key not in DIFFS:
                try:
                    text = ''.join(difflib.unified_diff(RAW[old_path].decode().splitlines(True), RAW[path].decode().splitlines(True), fromfile=old_path, tofile=path))
                    (STAGE/'diffs').mkdir(exist_ok=True)
                    (STAGE/dp).write_text(text)
                    DIFFS[key] = {'path': path, 'historical_source_path': old_path, 'before_sha256': expected, 'after_sha256': now['sha256'], 'diff_path': PREFIX+'/'+dp, 'diff_sha256': sha(text.encode())}
                except UnicodeDecodeError:
                    DIFFS[key] = {'path': path, 'historical_source_path': old_path, 'before_sha256': expected, 'after_sha256': now['sha256'], 'binary_comparison_only': True}
            result['difference_id'] = key
    return result


CONTRACT = 'implementation/art/production_contract.json'
MANIFEST = 'implementation/content/launch_manifest.json'
INVENTORY = 'release/content-evidence/inventory-assets.json'
contract, manifest, inventory = read(CONTRACT), read(MANIFEST), read(INVENTORY)
cm = {a['asset_id']: a for a in contract['assets']}
mm = {a['id']: a for a in manifest['assets']}
im = {a['asset_id']: a for a in inventory['assets']}
assert len(cm) == len(mm) == 164 and set(cm) == set(mm) == set(im)

ART_REVIEW = 'release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md'
CAL_REVIEW = 'release/qa/integration-accessibility-20261021T125317256764Z/CALIBRATION_REVIEW.md'
PUBLIC_REVIEW = 'release/qa/integration-public-pages-refresh-20261021T141933905061Z/PUBLIC_REFRESH_REVIEW.md'
REG_REVIEW = 'release/qa/integration-registration-20261021T111626112740Z/REGISTRATION_REVIEW.md'
INV_REVIEW = 'release/qa/integration-inventory-20261021T104607526377Z/INVENTORY_REVIEW.md'
HELP_REVIEW = 'release/qa/integration-content-descriptor-20261021T141301217842Z/REVIEW.md'
PUBLIC_DIR = 'release/qa/integration-public-pages-refresh-20261021T141933905061Z'
REG = 'release/native-proof/root-art-registration-20261021T111004.738637Z'

versions = {}
for name, run, folder, report, review in [
 ('art_en', 'root-art-full-20261021T122040.006324Z', 'release/art/catalogue-variants', 'matrix-results.json', ART_REVIEW),
 ('art_pseudo', 'root-art-pseudo-full-20261021T122636.246158Z', 'release/art/catalogue-variants', 'matrix-results.json', ART_REVIEW),
 ('calibration_en', 'root-calibration-full-20261021T125314.174315Z', 'release/accessibility-current', 'calibration-matrix.json', CAL_REVIEW),
 ('calibration_pseudo', 'root-calibration-pseudo-full-20261021T125549.278518Z', 'release/accessibility-current', 'calibration-matrix.json', CAL_REVIEW),
]:
    base = f'release/native-proof/{run}'
    pins = read(base+'/source-before.json')
    rows = read(f'{folder}/{run}/{report}')
    verify = read(base+'/verification.json')
    changes = [delta(p, h, base+'/source/'+p) for p,h in pins.items() if pin(p)['sha256'] != h]
    versions[name] = {'source_index': pin(base+'/source-before.json'), 'report': pin(f'{folder}/{run}/{report}'),
        'runner_verification': pin(base+'/verification.json'), 'independent_review': pin(review),
        'archive_root': base+'/source', 'archived_input_count': len(pins),
        'current_changed_input_count': len(changes), 'changed_inputs': changes,
        'source_pin_map': pins, 'rows': rows['rows'], 'conditions': rows['conditions'],
        'meaning': 'Reviewed actual host execution at archived bytes. Unchanged component inputs are individually identified; changed consumers/dependencies do not inherit integrated current or native acceptance.'}
    for r in verify['results']:
        p = base+'/'+r['name']+'.log'
        if (ROOT/p).exists(): pin(p)

# Evidence entries carry explicit immutable hashes and scope, never an inferred reviewer field.
evidence = {
 'inventory_prior': {'files': [pin(INVENTORY), pin(INV_REVIEW)], 'scope': 'Historical 164-ID inventory; 37 original registration gaps then remained. Current existence is recomputed here.'},
 'registration': {'files': [pin(REG_REVIEW), pin(REG+'/source-before.json'), pin(REG+'/verification.json'), pin('source/art/registration/AUTHOR_REPORT.md')], 'scope': 'Different-reviewer source/sample closure for 35 registrations + bounded cosmetic/chapter03 repins; historical 33 PNG captures, not all-variant/native approval.'},
 'art': {'files': [pin(ART_REVIEW), pin('source/art/verification/check_matrix.py'), pin('release/art/catalogue-variants/per-id-evidence.json')], 'scope': '68 IDs, two complete 12-condition host matrices. ART001 checker repair independently closed at 2bbf0a53; no blanket 164-asset rights acceptance.'},
 'calibration': {'files': [pin(CAL_REVIEW)], 'scope': 'Twelve actual patterns and equal-value crew paths, 432 state rows per language; static route, fixed-clock host evidence.'},
 'help_descriptor': {'files': [pin(HELP_REVIEW), pin('release/qa/integration-content-descriptor-20261021T141301217842Z/verification.json'), pin('release/qa/integration-content-descriptor-20261021T141301217842Z/source-before.json'), pin('release/content-presentation/help-descriptor-refresh-20261021T141049.467500Z/refresh.json')], 'scope': 'CONTENT002 closed for actual four HelpContent descriptor correspondences. Prior mismatched matrix stays rejected; new complete content matrix remains pending.'},
 'public_refresh_author': {'files': [pin('release/public-pages/evidence/refresh-20261021T134412.822191Z/REPAIR.md'), pin('release/public-pages/evidence/refresh-20261021T134412.822191Z/author-verification.json'), pin('release/public-pages/publication.json')], 'scope': 'Author-local Chrome 12 configurations/28 links; current privacy documentation delta under independent review. No public URL/operator/native policy approval.'},
 'public_prior': {'files': [pin('release/public-pages/INDEPENDENT_REVIEW.md'), pin('release/public-pages/INDEPENDENT_REVIEW.json')], 'scope': 'Earlier page source only, including corrected JPEG filenames. No automatic transfer to refreshed HTML/CSS.'},
 'public_metadata_refresh': {'files': [pin('release/public-pages/evidence/documentation-pin-refresh-20261021T143040.492826Z/verification.json'), pin('release/public-pages/evidence/documentation-pin-refresh-20261021T143040.492826Z/asset.support.privacy_page.json'), pin('release/public-pages/evidence/documentation-pin-refresh-20261021T143040.492826Z/asset.support.support_page.json')], 'scope': 'Lead applied the different-reviewer-permitted documentation-only provenance pin refresh. Historical records are preserved; HTML/CSS/export bytes and all reviewer/acceptance fields unchanged.'},
 'story_final_source': {'files': [pin('release/content-presentation/story-heading-repair-20261021T142446.966463Z/final.json'), pin('release/content-presentation/story-heading-repair-20261021T142446.966463Z/story_screen-final.dart'), pin('release/native-proof/root-current-runtime-analyze-20261021T143040.537924Z/verification.json')], 'scope': 'Final StoryScreen 13c917f5 source identity and bounded author73case phone200pseudo result only; independent full content12 remains pending. Intermediate failed runs are not adopted.'},
 'public_refresh_review': {'files': [pin(PUBLIC_REVIEW), pin(PUBLIC_DIR+'/verification.json'), pin(PUBLIC_DIR+'/browser.json'), pin(PUBLIC_DIR+'/privacy-inventory.diff')], 'scope': 'Different-reviewer actual Chrome 12 conditions/28 links/13291 rectangles; HTML/export equality and current study disclosure/doc delta supported. Provenance documentation pins remain stale; no pseudo/OS/publication/operator acceptance.'},
 'audio': {'files': [pin('release/audio/capability-and-rights.json'), pin('release/audio/playback-report.json'), pin('release/audio/IMPLEMENTATION_HANDOFF.md')], 'scope': 'Original authored synthesis/export facts and explicitly bounded host/historical candidate evidence; no fresh current native listening/route/store/standalone distribution approval.'},
 'chapter03': {'files': [pin('source/art/registration/chapter03-source.patch'), pin('source/art/registration/chapter03-export.patch'), pin('release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md')], 'scope': 'Optional calibration hint source/export change and independent campaign remedy; no changed natural pacing or full copy variants inferred.'},
 'cosmetic_renderer': {'files': [pin('source/art/registration/cosmetic-renderer-refresh.patch'), pin('release/qa/integration-inventory-20261021T104607526377Z/cosmetic-renderer-comparison.json')], 'scope': 'Exact old-to-new renderer patch: two localization imports and semantic label only; 72 historical exports unchanged, no new render claimed.'},
}
for p in ['V1_ROADMAP.md','TIDEGLASS_DESIGN.md','v1_backlog.json','implementation/scope_requirements.json','implementation/team/EXECUTION_CHECKPOINT.md','source/art/style-guide.md']:
    pin(p)
backlog = read('v1_backlog.json')
scopes = read('implementation/scope_requirements.json')

ARCHIVES = [REG+'/source', PUBLIC_DIR+'/source', 'release/qa/integration-content-descriptor-20261021T141301217842Z/source',
 'game/qa/workspaces/integration-inventory-20261021T104607526377Z',
 'game/qa/workspaces/integration-registration-20261021T111626112740Z',
 'release/qa/client-web-deletion-20261021T134443512157Z/source',
 'release/qa/integration-art-matrix-20261021T123739647573Z/source'] + [v['archive_root'] for v in versions.values()]


def find_old(path, expected):
    for base in ARCHIVES:
        old = base+'/'+path
        f = ROOT/old
        if f.is_file() and sha(f.read_bytes()) == expected: return old
    return None


def binding(version, paths):
    v = versions[version]
    comparisons = []
    for p in sorted(set(paths)):
        if p in v['source_pin_map']:
            comparisons.append(delta(p, v['source_pin_map'][p], v['archive_root']+'/'+p))
        else:
            comparisons.append({'path': p, 'relation': 'not_in_this_run_input_index', 'current_sha256': pin(p)['sha256']})
    return {'version': version, 'relevant_inputs': comparisons,
            'same_relevant_inputs': all(x['relation']=='byte_identical' for x in comparisons),
            'whole_runtime_is_current': v['current_changed_input_count']==0,
            'interpretation': 'Only listed equal hashes preserve exact component identity. Other changed archived inputs and unindexed new inputs are not covered by that equality.'}


registration_pins=read('source/art/registration/source-snapshot.json')['files_sha256']
public_verification=read(PUBLIC_DIR+'/verification.json')
public_browser=read(PUBLIC_DIR+'/browser.json')
assets = []
proposals = []
for idx,a in enumerate(contract['assets']):
    aid = a['asset_id']; m=mm[aid]; inv=im[aid]; prov=read(a['provenance_path'])
    provenance_bindings=[]
    for group, pk,hk in [('source','source_media_paths','source_media_sha256'),('export','exported_paths','exported_sha256')]:
        for path,h in hash_pairs(prov,pk,hk):
            row=delta(path,h,find_old(path,h) if pin(path)['sha256']!=h else None)
            row['group']=group;provenance_bindings.append(row)
    for p in prov.get('license_evidence_paths',[]):
        if (ROOT/p).is_file():pin(p)
    paths={k:pin(a[k]) for k in ['source_descriptor_path','export_descriptor_path','provenance_path','verification_path']}
    runtime={k:[pin(x['path']) for x in inv.get(k,[])] for k in ['authored_sources','runtime_or_download_bundle','integration_sources']}
    # Actual registrations add runtime dependencies beyond the older inventory.
    runtime['registered_source_media']=[pin(p) for p in prov['source_media_paths']]
    prior_inventory=[]
    for old in list(inv['original_contract']['paths'].values()) + inv.get('authored_sources',[]) + inv.get('runtime_or_download_bundle',[]) + inv.get('integration_sources',[]):
        if old.get('sha256'):prior_inventory.append(delta(old['path'],old['sha256'],find_old(old['path'],old['sha256'])))
    reg_relations=[delta(path,registration_pins[path],find_old(path,registration_pins[path])) for path in set(prov['source_media_paths']+prov['exported_paths']+[a['provenance_path']]) if path in registration_pins]
    relations=[];refs=['inventory_prior']; tests=[]
    if any(x['path']=='game/mobile/lib/story_screen.dart' for x in runtime['integration_sources']+runtime['registered_source_media']):refs+=['story_final_source']
    host='no_complete_all_id_variant_matrix_claimed'
    variant_notes={v:'Original requirement remains; no canonical per-asset verification written.' for v in a['required_variants']}
    category=a['category'];
    if category in ['harbor','producer_presentations','cosmetics']:
        refs+=['art'];host='reviewed_archived_host_matrix_with_explicit_current_component_lineage'
        paths_to_compare=['game/mobile/lib/app.dart','game/mobile/lib/presentation.dart','game/mobile/lib/palette.dart','game/mobile/lib/game_controller.dart']
        if category=='harbor':paths_to_compare+=['game/mobile/lib/harbor_art.dart','game/mobile/lib/story_state.dart']
        elif category=='producer_presentations':paths_to_compare+=['game/mobile/lib/producer_art.dart','game/mobile/lib/producer_art_data.dart','game/mobile/lib/season_screen.dart']
        else:paths_to_compare+=['game/mobile/lib/cosmetic_art.dart','game/mobile/lib/cosmetics.dart','game/mobile/lib/cosmetics_screen.dart']
        # Nonexistent guessed consumer paths are not manufactured as requirements.
        paths_to_compare=sorted(set(paths_to_compare + [x['path'] for x in inv['integration_sources']]))
        assert all((ROOT/p).is_file() for p in paths_to_compare)
        for version in ['art_en','art_pseudo']:
            selected=[(i,r) for i,r in enumerate(versions[version]['rows']) if r.get('asset_id')==aid]
            assert len(selected)==12
            tests.append({'version':version,'row_indices':[i for i,r in selected],'condition_ids':[r['condition_id'] for i,r in selected], 'rows':12,'claim':'passed_bounded_host_case_at_archived_version'})
            relations.append(binding(version,paths_to_compare))
        for v in variant_notes:variant_notes[v]='Reviewed 12 conditions per language at archived host version; see row indices and explicit current input relations. Native/export/rights gates separate.'
        if category=='producer_presentations':
            variant_notes['selected']='Supplemental selected renderer fixture only; no nonexistent production selected route is claimed.'
            variant_notes['locked']='Actual initial locked cards plus supplemental high-stage locked component fixtures; not unreachable save-state acquisition.'
        if category=='cosmetics':
            refs+=['cosmetic_renderer']
            variant_notes['thumbnail']='160px real-component fixture plus historical PNG; no dedicated integrated thumbnail route is claimed.'
    if aid.startswith('asset.calibration.'):
        refs+=['calibration'];host='reviewed_archived_calibration_host_matrix_with_exact_text_graph_relation'
        pattern='.'.join(aid.split('.')[1:3]); pp=f'game/content/calibrations/{pattern}.pattern.json'
        bp=f'game/mobile/assets/calibrations/{pattern}.pattern.json'
        compare=[pp,bp,'game/mobile/lib/calibration_screen.dart','game/mobile/lib/calibration_pattern.dart','game/mobile/lib/game_controller.dart','game/mobile/lib/presentation.dart','game/mobile/lib/daily_panel.dart']
        compare=sorted(set(compare + [x['path'] for x in inv['integration_sources']]))
        assert all((ROOT/p).is_file() for p in compare)
        for version in ['calibration_en','calibration_pseudo']:
            selected=[(i,r) for i,r in enumerate(versions[version]['rows']) if r['pattern_id']==pattern]
            assert len(selected)==36
            tests.append({'version':version,'row_indices':[i for i,r in selected],'condition_ids':sorted(set(r['condition_id'] for i,r in selected)), 'states':sorted(set(r['state'] for i,r in selected)), 'rows':36, 'claim':'shared_pattern_execution_not_additional_tests_for_copy'})
            relations.append(binding(version,compare))
        if aid.endswith('accessible_copy'):
            source=read(a['export_descriptor_path']); graph=read(pp)
            fields=['title','intro','instructions','accessible_label','accessible_description']
            assert all(source[k]==graph[k] for k in fields)
            tests.append({'type':'exact_copy_to_tested_pattern_relation','fields':fields,'all_equal':True,'copy_export':pin(a['export_descriptor_path']),'pattern':pin(pp),'not_an_independent_render_run':True})
        for v in variant_notes:variant_notes[v]='Reviewed calibration host rows support this pattern/route; accessible copy relation is exact field equality to tested loaded graph, not extra independent test cases.'
    if a['status']=='unproduced' and aid not in ['asset.support.privacy_page','asset.support.support_page'] or category=='cosmetics' or aid=='asset.chapter.03.copy':refs+=['registration']
    if aid=='asset.chapter.03.copy':refs+=['chapter03']
    if aid in ['asset.support.help','asset.support.recovery_guide','asset.support.release_notes','asset.support.credits']:
        refs+=['help_descriptor'];host='current_descriptor_correspondence_reviewed_complete_content_matrix_pending'
    if aid in ['asset.support.privacy_page','asset.support.support_page']:
        refs+=['public_prior','public_refresh_author','public_refresh_review','public_metadata_refresh'];host='current_local_html_independently_reviewed_documentation_only_provenance_refresh_preserved'
        page='privacy.html' if aid.endswith('privacy_page') else 'index.html'
        selected=[(i,r) for i,r in enumerate(public_browser['rows']) if r['page']==page]
        assert len(selected)==6 and all(r['issues']==[] for i,r in selected)
        tests.append({'type':'reviewed_public_browser_rows','review_evidence':'public_refresh_review','page':page,'row_indices':[i for i,r in selected],'conditions':[{'width':r['width'],'height':r['height'],'percent':r['percent']} for i,r in selected],'rows':6,'pseudolocalized':False,'native':False})
        for v in ['text_scale_100','text_scale_150','text_scale_200']:variant_notes[v]='Current local HTML/CSS independently executed at320x720/1024x768 and100/150/200% root font; six rows for this page. No pseudo/OS/public URL qualification.'
        variant_notes['pseudolocalized']='Still open: public HTML was not pseudolocalized in either browser matrix.'
    if category=='audio':refs+=['audio'];host='existing_bounded_audio_components_only_no_new_execution'
    if aid.startswith('asset.archive.season01.') or aid.startswith('asset.chapter.') or aid.startswith('asset.challenge.') or aid.startswith('asset.archive.main.') or aid in ['asset.ending.main','asset.season.01.copy','asset.season.01.presentation']:
        pending='New current content 12-condition matrix is in progress; partial/rejected earlier results are not adopted. Existing descriptors and archived evidence remain individually pinned.'
    else:pending=None
    internal=a.get('exclude_from_client_packaging',False)
    changed=[x for x in provenance_bindings if x['relation']!='byte_identical']
    missing_fields=[k for k in contract['provenance_record_required_fields'] if k not in prov]
    supplied=all(paths[k]['exists'] for k in ['source_descriptor_path','export_descriptor_path','provenance_path']) and all(x['current_sha256'] for x in provenance_bindings)
    preserved={k:prov[k] for k in ['reviewer','review_evidence','distribution_terms_approval','production_acceptance','status','variant_acceptance','author_pin_refresh','revision_history','bounded_host_capture_evidence','documentation_pin_refresh'] if k in prov}
    applicable_gates=['ART-V01','ART-V07'] if category=='narrative_and_support' else ['ART-V01','ART-V02','ART-V03','ART-V04']
    if category=='audio':applicable_gates=['ART-V01','ART-V02','ART-V05','ART-V06']
    if category in ['cosmetics','season_presentation']:applicable_gates+=['ART-V06']
    if category=='calibration':applicable_gates+=['ART-V07']
    if internal:applicable_gates=['ART-V01','ART-V07']
    remaining=[]
    if changed:remaining.append({'kind':'provenance_version','requirement':'Review exact current source deltas; preserve old pins and append scoped version bridge before any canonical update.','paths':[x['path'] for x in changed]})
    remaining.append({'kind':'per_asset_review','requirement':'Designated client/QA and AI director may perform original editorial/visual/authorship reviews. No generic human sign-off is added. Canonical verification/reviewer fields remain untouched in this stage.','criterion_refs':applicable_gates})
    if pending:remaining.append({'kind':'host_content_variants','requirement':pending})
    if not internal and category!='audio':remaining.append({'kind':'native_and_accessibility','requirement':'Current target imports/rendering/input and applicable native accessibility/performance remain distinct; historical candidate152 is not transferred.','criterion_refs':['ART-V02','ART-V03','ART-V04'] if category!='narrative_and_support' else ['variant_contract.text','ART-V07']})
    if category=='audio':remaining.append({'kind':'audio_native_and_delivery','requirement':'Both-target decode/playback, seamless/no-click mix, independent controls, headphone/interruption/resume, no stale cue burst, standalone download rights and actual provider/host fulfillment remain separately qualified. Listening is a device/audio requirement; no invented universal human asset approval.','criterion_refs':['ART-V05','ART-V06','audio_delivery']})
    if category in ['cosmetics','season_presentation']:remaining.append({'kind':'commerce_or_route','requirement':'Synthetic paid ownership and component thumbnails do not establish real purchase/restore authenticity or an absent runtime route. Original same-appearance and cosmetic-only obligations remain.','criterion_refs':['ART-V06','variant_contract.cosmetics']})
    if internal:remaining.append({'kind':'internal_review','requirement':'Review actual internal document completeness with original assigned owner; exclude from client packaging. Operational launch coverage and Season 2 postlaunch update require their own real records.','criterion_refs':['acceptance_stages.B21','acceptance_stages.B23']})
    if aid in ['asset.support.privacy_page','asset.support.support_page']:remaining.append({'kind':'operator_publication','requirement':'Real operator/contact/live endpoint and approved factual policy configuration are absent; local author browser checks do not discharge them. Pseudo/native/screen-reader work remains explicit.','evidence':'public_refresh_author'})
    rights={'authorship_basis_recorded':prov.get('license_or_authorship_basis'), 'source_kind':prov.get('source_kind'), 'allowed_uses_recorded':prov.get('allowed_uses'), 'license_evidence':[pin(p) for p in prov.get('license_evidence_paths',[]) if (ROOT/p).is_file()], 'reference_permissions_recorded':prov.get('reference_asset_permissions'), 'approval_inferred':False, 'review_actor':'Designated independent AI reviewer/director may assess original authorship and actual licenses. A missing authorized operator distribution decision stays missing; no human-only reviewer requirement is inferred.', 'status':'recorded_authorship_evidence_needs_scoped_review'}
    if 'distribution_terms_approval' in prov: rights['explicit_distribution_terms_state']=prov['distribution_terms_approval']
    human={'asset_human_signoff_inferred':False,'separate_original_program_requirements':['M2-06: at least 15 genuinely new testers','M6-07: real 28-day pass and mature D30 cohort','B23: actual first 14 days support'], 'meaning':'These are explicit product observation/calendar obligations, not a reason to demand a human signature on every authored asset.'}
    entry={'asset_id':aid,'original_contract':a,'manifest_record':m,'scope_ids_from_prior_inventory':inv['scope_ids'], 'current_paths':paths,'public_documentation_pin_lineage':delta(a['provenance_path'],pin('release/public-pages/evidence/documentation-pin-refresh-20261021T143040.492826Z/'+aid+'.json')['sha256'],'release/public-pages/evidence/documentation-pin-refresh-20261021T143040.492826Z/'+aid+'.json') if aid in ['asset.support.privacy_page','asset.support.support_page'] else None,'prior_inventory_lineage':prior_inventory,'registration_snapshot_lineage':reg_relations,'original_scope_requirements':[x for x in scopes['requirements'] if x['id'] in inv['scope_ids']], 'source_selector_from_inventory':inv['source_selector'],'current_implementation_paths':runtime,'source_delivery':{'registered_source_export_provenance_and_children_present':bool(supplied),'missing_provenance_fields':missing_fields,'authored_source_complete_claim':'registered_files_present_not_full_asset_acceptance','descriptors_loaded_by_client_not_assumed':True},'provenance_version_bindings':provenance_bindings,'preserved_provenance_fields':preserved,'evidence_refs':list(dict.fromkeys(refs)),'host_variant_status':host,'host_tests':tests,'reviewed_version_relations':relations,'required_variants':a['required_variants'],'variant_review_notes':variant_notes,'rights':rights,'operator_gates_applicable':aid in ['asset.support.privacy_page','asset.support.support_page','asset.support.operations_runbooks','asset.support.season02_brief','asset.audio.soundtrack'],'pacing_or_human_observation':human,'remaining_requirements':remaining,'canonical_verified':False,'canonical_updates_applied':False}
    assets.append(entry)
    if a['status']=='unproduced' or not a['source_exists'] or not a['export_exists']:
        proposals.append({'asset_id':aid,'target':CONTRACT,'json_pointer':f'/assets/{idx}','expected_record_sha256':sha(json.dumps(a,sort_keys=True).encode()),'proposed_changes':{'status':'in_production','source_exists':paths['source_descriptor_path']['exists'],'export_exists':paths['export_descriptor_path']['exists']}, 'reason':'Registered current files now exist; this repairs only lagging authoring/existence metadata after reviewer approval, never verified/readiness/variants/reviewer fields.','applied':False})
    if changed:proposals.append({'asset_id':aid,'target':a['provenance_path'],'kind':'append_only_lineage_candidate','changed_bindings':changed,'proposed_changes':{},'reason':'Review before appending explicit current-version delta. Preserve historical hashes/captures and all current null approvals; do not silently repin.','applied':False})

# Keep the original definitions, named owners and acceptance/dependency text in the review packet.
criteria={'original_validation_gates':contract['validation_gates'],'original_variant_contract':contract['variant_contract'],'original_artist_items':contract['original_artist_work_items'],'original_shared_narrative':contract['shared_narrative_obligations'],'original_audio_delivery':contract['audio_delivery'],'original_provenance_rules':contract['provenance_rules'],'original_acceptance_stages':contract['acceptance_stages'],'original_backlog_items':[x for x in backlog['items'] if x['id'] in ['M3-09','M4-06','M4-07','M5-06','M2-06','M6-07','M5-03','M7-05']]}
put('criteria.json',criteria)
# Do not duplicate the full runtime pin map or rows per ID; all are hash-bound original evidence.
for v in versions.values():
    v.pop('source_pin_map');v.pop('rows')
summary={'asset_count':len(assets),'category_counts':dict(collections.Counter(a['original_contract']['category'] for a in assets)), 'registered_complete_count':sum(a['source_delivery']['registered_source_export_provenance_and_children_present'] for a in assets),'provenance_drift_asset_count':sum(any(x['relation']!='byte_identical' for x in a['provenance_version_bindings']) for a in assets),'provenance_drift_paths':sorted({x['path'] for a in assets for x in a['provenance_version_bindings'] if x['relation']!='byte_identical'}),'original_verification_paths_present':sum(a['current_paths']['verification_path']['exists'] for a in assets),'canonical_verified_count':0,'cosmetic_count':sum(a['original_contract']['category']=='cosmetics' for a in assets),'supporter_reuse':'Only existing cosmetic.shop.01-.04 and audio.soundtrack; no extra assets.','complete_content12_adopted':False,'public_refresh_independent_review_adopted':True}
bridge={'schema_version':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'author':'/root/art_content_engineer','status':'staged_for_different_reviewer_not_applied','root':str(ROOT),'original_contract':pin(CONTRACT),'current_manifest':pin(MANIFEST),'summary':summary,'assets':assets,'review_boundary':'Exact per-ID source/evidence lineage; no blanket transfer, no current native replay, no publication, no null approval filled.'}
put('bridge.json',bridge);put('evidence-index.json',{'evidence':evidence,'versions':versions});put('differences.json',DIFFS);put('proposed-updates.json',{'applied':False,'updates':proposals,'forbidden_updates':['required_variants','verification_evidence','reviewer','review_evidence','release_ready','production_acceptance']})
# Capture input drift after collecting everything; a changed authoring source invalidates this snapshot.
drift=[]
for p,record in INPUTS.items():
    f=ROOT/p;now=sha(f.read_bytes()) if f.is_file() else None
    if now!=record['sha256']:drift.append({'path':p,'before':record['sha256'],'after':now})
put('inputs.json',{'inputs':INPUTS,'input_count':len(INPUTS),'source_drift_during_build':drift,'snapshot_media_policy':'UTF-8 inputs under 2MB copied exactly; media and large artifacts hash-bound in place.','stage_only':True})
print(json.dumps({'summary':summary,'inputs':len(INPUTS),'diffs':len(DIFFS),'staged_proposals':len(proposals),'source_drift':drift},indent=2))
assert not drift
