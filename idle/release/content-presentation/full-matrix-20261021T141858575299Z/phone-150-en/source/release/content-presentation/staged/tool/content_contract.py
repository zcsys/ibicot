"""Exact staged expectation inventory, not a report of executed widget tests."""
import hashlib,json,re
from pathlib import Path


def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def write(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def expected(root):
    root=Path(root); result=[]
    campaign=load(root/'game/mobile/assets/progression/campaign.json')['chapters']
    archive=load(root/'game/mobile/assets/progression/archive.en.json')['entries']
    season=load(root/'game/mobile/assets/events/season.01.json')
    def row(id,state,route,fields,assertions,callbacks=0,exact=None,controls=0):
        result.append(dict(id=id,state=state,route=route,fields=fields,assertions=assertions,minimum_callbacks=callbacks,minimum_controls=controls,exact_english=exact or {}))
    for c in campaign:
        aid=f"asset.{c['id']}.copy"
        common=['title','status','intro',*[f'hint-{i}' for i in range(len(c['hints']))],*[f'objective-{i}' for i in range(len(c['objectives']))],'keepsake']
        exact={'title':f"{c['order']}. {c['title']}",'intro':c['intro'],**{f'hint-{i}':f'• {h}' for i,h in enumerate(c['hints'])}}
        for state in ['current','completed']:
            row(aid,state,'StoryScreen/chapters',common+(['completion'] if state=='completed' else []),
                ['prefix_exact','read_only','completion_visibility','actual_header_control'],controls=1,
                exact={**exact,**({'completion':c['completion']} if state=='completed' else {})})
        if c['order']>1: row(aid,'locked','StoryScreen/chapters',['title','status'],['entry_status','read_only'],exact={'title':exact['title']})
    ending=load(root/'game/content/locales/en-US/ending.main.json')
    assert ending['text']==campaign[-1]['completion']
    row('asset.ending.main','ending','StoryScreen/chapters',['title','text'],['ending_unlocked','returned_to_origin','read_only'],1,{'title':ending['title'],'text':ending['text']},1)
    for e in archive:
        row('asset.'+e['id'],'locked','StoryScreen/archive',['title'],['body_hidden','reflection_unavailable','read_only'],exact={'title':e['title']})
        row('asset.'+e['id'],'reflected','StoryScreen/archive',['title','text'],['discovery_once','actual_reflection_control','no_direct_notes_xp_or_radiance'],1,{'title':e['title'],'text':e['text']},2)
    for n in range(1,13):
        d=load(root/f'game/mobile/assets/challenges/challenge.{n:02}.json')
        row('asset.'+d['id']+'.copy','opened','StoryScreen/passages',['title','intro'],['confirmation_before_spend','exact_100_notes','actual_dossier_identity','main_power_unchanged'],2,{'title':d['title'],'intro':d['intro']},2)
        row('asset.'+d['id']+'.copy','completed','StoryScreen/passages',['title','completion','status'],['actual_final_scene_identity','goal_met','read_only'],exact={'title':d['title'],'completion':d['completion']})
    for r in season['rewards']:
        if r['kind']!='archive_fragment':continue
        for state in ['locked','claimed']:
            row('asset.'+r['content_id'],state,'SeasonScreen/pass',['title','locked-placeholder']+(['body'] if state=='claimed' else []),
                ['body_hidden','claim_disabled','read_only'] if state=='locked' else ['actual_fragment_identity','one_claim_only','main_ledger_unchanged','claimed_control_disabled'],
                0 if state=='locked' else 1,{} if state=='locked' else {'body':r['body']},2)
    for state in ['upcoming','live','archived-paused']:
        fields=['title','phase-copy']+(['ended','archive_resume'] if state=='archived-paused' else [])
        exact={'title':season['title'],'phase-copy':season['copy']['archived' if state=='archived-paused' else state]}
        if state=='archived-paused':exact.update({k:season['copy'][k] for k in ['ended','archive_resume']})
        row('asset.season.01.copy',state,'SeasonScreen/fleet',fields,['phase_exact','read_only'],exact=exact,controls=1 if state=='archived-paused' else 0)
    row('asset.season.01.copy','archive-resume-pause','SeasonScreen/fleet',['phase-copy'],['resume_then_pause','no_money_or_xp_grant','retained_wallet'],2,{'phase-copy':season['copy']['archived']},2)
    for state,route in [('pass','pass'),('alternatives','contracts')]:
        field='pass' if state=='pass' else 'alternative'
        row('asset.season.01.copy',state,f'SeasonScreen/{route}',['title',field],['read_only','actual_route_copy'],exact={'title':season['title'],field:season['copy'][field]})
    for name in ['help','recovery_guide','credits','release_notes']:
        h=load(root/f'game/content/locales/en-US/support.{name}.json')
        for a in h['articles']:
            fields=['index-title','index-intro','index-summary','title','summary']
            exact={'index-title':h['handbook_title'],'index-intro':h['handbook_intro'],'index-summary':a['summary'],'title':a['title'],'summary':a['summary']}
            for s in a['sections']:
                fields.append('heading-'+s['id']);exact['heading-'+s['id']]=s['title']
                for i,p in enumerate(s['paragraphs']):fields.append(f"{s['id']}-paragraph-{i}");exact[f"{s['id']}-paragraph-{i}"]=p
            if a['topic']=='releaseNotes':fields.append('development-notice');exact['development-notice']=h['development_notice']
            row(f'asset.support.{name}',a['topic'],f"HelpScreen/{a['topic']}",fields,['all_sections_read','actual_navigation','callbacks_forwarded','game_unchanged'],2+len(a['actions']),exact,2+len(a['actions']))
    # Privacy companion is not the public privacy-page asset. Its full dynamic
    # section set is additionally checked against the actual HelpContent source.
    # No external-page variants are claimed by this companion flow.
    # The original registration does not export this companion; keep an explicit
    # source-derived field contract instead of substituting the public HTML.
    source=(root/'game/mobile/lib/help_content.dart').read_text()
    privacy=source.split('HelpTopic.privacy,',1)[1].split('    HelpArticle(',1)[0]
    section_ids=re.findall(r"HelpSection\(\s*'([^']+)'",privacy)
    fields=['index-title','index-intro','index-summary','title','summary']
    # Paragraph counts use the independently reviewed fixed English source;
    # exact payload strings remain recorded by the actual rendering observation.
    for part in re.split(r'HelpSection\(',privacy)[1:]:
        sid=re.match(r"\s*'([^']+)'",part).group(1)
        body=part.split('[',1)[1].split(']',1)[0]
        paragraphs=re.findall(r"'(?:\\.|[^'\\])*'",body)
        fields.extend(['heading-'+sid,*[f'{sid}-paragraph-{i}' for i in range(len(paragraphs))]])
    assert section_ids
    row('flow.help.privacy-companion','privacy','HelpScreen/privacy',fields,['all_sections_read','actual_navigation','callbacks_forwarded','game_unchanged'],4,controls=4)
    panel=['title','retention','status','account-day']
    # Daily goal IDs include seeded account days. Require exact total/counts and
    # per-slot field pair shapes below, rather than hard-coding a second clock.
    row('flow.daily.contracts','pending-reroll','ContractPanel',panel,['three_pending','reroll_once','no_reward'],1,controls=4)
    row('flow.daily.contracts','ready-backlog','ContractPanel',panel,['seven_days_21_slots','exact_210_notes_5250_xp','claims_once'],21,controls=21)
    row('flow.daily.contracts','empty','ContractPanel',panel+['empty'],['all_21_claimed','no_claim_controls','read_only'])
    row('flow.daily.storage','queued-ready','TideglassApp/journal',['daily-title','focus-label','focus-store','focus-help','focus-queued','survey-label','survey-store','survey-help'],['exact_30_notes','focus_queue_unchanged','storage_consumed'],2,controls=3)
    row('flow.daily.storage','empty','TideglassApp/journal',['survey-store'],['disabled_when_empty','read_only'],controls=1)
    assert len(result)==137,len(result)
    assert len({(r['id'],r['state'])for r in result})==137
    return result


def crosswalk(root):
    root=Path(root);contract=load(root/'implementation/art/production_contract.json');manifest=load(root/'implementation/content/launch_manifest.json');rows=expected(root)
    assert {a['asset_id']for a in contract['assets']}=={a['id']for a in manifest['assets']}
    art='release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md'
    calibration='release/qa/integration-accessibility-20261021T125317256764Z/CALIBRATION_REVIEW.md'
    registration='release/qa/integration-registration-20261021T111626112740Z/REGISTRATION_REVIEW.md'
    out=[]
    for a in contract['assets']:
        aid=a['asset_id']; new=[r for r in rows if r['id']==aid]; prior=[]
        if new: kind='new_production_widget_verification'; remaining='Not run; requires reviewed suite and all 12 passing conditions.'
        elif a['category'] in ['harbor','producer_presentations','cosmetics']:kind='existing_visual_matrix';prior=[art];remaining='Original export/native/rights and canonical asset acceptance remain separate.'
        elif a['category']=='calibration' or '.accessible_copy' in aid:kind='existing_calibration_matrix';prior=[calibration];remaining='Native/human accessibility remains separate.'
        elif a['category']=='audio':kind='separate_audio_evidence';prior=['release/audio/capability-and-rights.json'];remaining='Audio mix/rights/native/fulfillment is not a text-widget obligation.'
        elif a['category']=='season_presentation':kind='existing_visual_exports_plus_new_phase_copy';prior=[registration];remaining='New phase-copy states do not duplicate or accept all seasonal image variants.'
        elif aid.endswith(('privacy_page','support_page')):kind='public_document_and_external_route';prior=[registration,'release/qa/integration-current-ui-20261021T133115456638Z/CURRENT_UI_REVIEW.md'];remaining='Local HTML/browser deletion/public-link review separate; real hosting absent. Internal help cannot verify this asset.'
        else:kind='internal_release_document';prior=[registration];remaining='No game route; document-specific review and original variant disposition remain explicit, not silently waived.'
        out.append({'asset_id':aid,'category':a['category'],'required_variants':a['required_variants'],'source':a['source_descriptor_path'],'export':a['export_descriptor_path'],'provenance':a['provenance_path'],'coverage_kind':kind,'new_states':[r['state']for r in new],'new_routes':sorted({r['route']for r in new}),'existing_evidence':prior,'remaining_boundary':remaining,'canonical_acceptance_changed':False})
    return {'schema_version':1,'asset_count':164,'assets':out,'additional_flows':sorted({r['id']for r in rows if not r['id'].startswith('asset.')}),'scope_ids':['S18','S20','S21','S22','S27'],'work_ids':['M3-09','M4-06','M4-07','M4-08'],'obligation':'Exact original variants retained. Suite covers host rendering and actual callbacks only; not release acceptance.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    rows=expected(a.root);write(a.output/'expected-rows.json',{'schema_version':1,'tests_per_condition':73,'rows_per_condition':137,'conditions':[{'viewport':v,'text_percent':s,'pseudo':q}for v in ['phone','tablet']for s in [100,150,200]for q in [False,True]],'rows':rows})
    write(a.output/'coverage-crosswalk.json',crosswalk(a.root));print(json.dumps({'staged_expectations':137,'tests_per_condition':73,'original_assets':164,'executed_widget_tests':0}))
