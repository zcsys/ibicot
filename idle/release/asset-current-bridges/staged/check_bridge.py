#!/usr/bin/env python3
"""Reject incomplete, misbound or overpromoted staged asset bridges. No live writes."""
from pathlib import Path
import argparse, copy, difflib, hashlib, json, sys

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads((STAGE/p).read_text())
def require(v,msg):
    if not v:raise ValueError(msg)
def check(b,e,inputs,diffs,proposals,check_files=True,live=False):
    pins=inputs['inputs'];assertions=0
    def ck(v,msg):
        nonlocal assertions
        assertions+=1;require(v,msg)
    def frozen(p):
        rec=pins[p]
        src=rec.get('snapshot_path',p)
        return json.loads((ROOT/src).read_text())
    c=frozen('implementation/art/production_contract.json');m=frozen('implementation/content/launch_manifest.json')
    ck(b['status']=='staged_for_different_reviewer_not_applied','stage status')
    ck(b['summary']['asset_count']==164 and len(b['assets'])==164,'164 assets')
    ck([a['asset_id'] for a in b['assets']]==[a['asset_id'] for a in c['assets']],'exact original ordered asset IDs')
    ck(b['summary']['canonical_verified_count']==0,'no canonical acceptance count')
    ck(b['summary']['complete_content12_adopted'] is False,'pending content matrix not adopted')
    ck(b['summary']['public_refresh_independent_review_adopted'] is True,'current bounded public review recorded')
    ck('public_refresh_review' in e['evidence'],'public review evidence resolves')
    public_base='release/qa/integration-public-pages-refresh-20261021T141933905061Z'
    pv=frozen(public_base+'/verification.json');pb=frozen(public_base+'/browser.json')
    ck(pv['source_unchanged'] is True and pv['browser_exit_code']==0 and pv['exports_equal'] is True,'public reviewed success')
    ck(pv['publication_approved'] is False and pv['provenance_equal'] is False,'public review limits preserved')
    ck(len(pb['rows'])==12 and all(r['issues']==[] for r in pb['rows']),'public actual twelve rows')
    ck(inputs['source_drift_during_build']==[],'stable captured inputs')
    ck(inputs['stage_only'] is True and proposals['applied'] is False,'stage only')
    cm={a['asset_id']:a for a in c['assets']};mm={a['id']:a for a in m['assets']}
    scope=frozen('implementation/scope_requirements.json')['requirements']
    invmap={x['asset_id']:x for x in frozen('release/content-evidence/inventory-assets.json')['assets']}
    registration=frozen('source/art/registration/source-snapshot.json')['files_sha256']
    ck(m['supporter_bundle']['cosmetic_ids']==['cosmetic.shop.%02d'%i for i in range(1,5)] and m['supporter_bundle']['audio_ids']==['audio.soundtrack'] and m['supporter_bundle']['new_unique_cosmetics']==0 and m['supporter_bundle']['economic_effects']==[],'exact supporter reuse')
    ck(len(m['cosmetics'])==36 and all(x['economic_effects']==[] for x in m['cosmetics']),'36 power-free registered cosmetics')
    ck(m['pass']['levels']==30 and m['pass']['xp_per_level']==500 and len(m['pass']['free_rewards'])==30 and len(m['pass']['premium_rewards'])==10,'original pass counts')
    def match_pin(p):
        ck(p==pins[p['path']],'complete pin equality '+p['path'])
    for x in [b['original_contract'],b['current_manifest']]:match_pin(x)
    matrices={}
    for key,v in e['versions'].items():
        for field in ['report','runner_verification','source_index','independent_review']:match_pin(v[field])
        report=frozen(v['report']['path']);verify=frozen(v['runner_verification']['path']);source=frozen(v['source_index']['path'])
        matrices[key]=report
        ck(report['complete_matrix_observed'] is True,'full source matrix '+key)
        expected=816 if key.startswith('art') else 432
        ck(len(report['rows'])==expected,'source row count '+key)
        ck(all(type(r['exit_code']) is int and r['exit_code']==0 for r in verify['results']),'successful actual runner '+key)
        ck(verify['source_differences']==[],'original source stable '+key)
        reportkey='art_report_sha256' if key.startswith('art') else 'calibration_report_sha256'
        # The art proof's name is report_sha256; preserve the source schema.
        if reportkey not in verify:reportkey='report_sha256'
        ck(verify[reportkey]==v['report']['sha256'],'runner report hash '+key)
        ck(len(source)==v['archived_input_count'],'source count '+key)
        changes=[p for p,h in source.items() if pins[p]['sha256']!=h]
        ck(v['current_changed_input_count']==len(changes),'current change count '+key)
        ck(set(changes)=={x['path'] for x in v['changed_inputs']},'exhaustive changed input list '+key)
    for a in b['assets']:
        aid=a['asset_id'];original=cm[aid];prov=frozen(original['provenance_path'])
        ck(a['original_contract']==original,'preserve complete original record '+aid)
        ck(a['manifest_record']==mm[aid],'preserve manifest record '+aid)
        ck(a['original_scope_requirements']==[x for x in scope if x['id'] in a['scope_ids_from_prior_inventory']],'original scope clauses and existing acceptance retained '+aid)
        ck(a['required_variants']==original['required_variants'],'exact variants '+aid)
        ck(list(a['variant_review_notes'])==original['required_variants'],'every variant noted '+aid)
        ck(a['canonical_verified'] is False and a['canonical_updates_applied'] is False,'no promoted asset '+aid)
        ck(a['rights']['approval_inferred'] is False,'no invented rights '+aid)
        ck(a['pacing_or_human_observation']['asset_human_signoff_inferred'] is False,'no invented human review '+aid)
        for k,p in a['current_paths'].items():
            ck(p['path']==original[k],'original path '+aid);match_pin(p)
        for k,val in a['preserved_provenance_fields'].items():ck(val==prov[k],'preserved approval/history field '+aid+':'+k)
        for field in ['reviewer','review_evidence']:
            ck(field in a['preserved_provenance_fields'],'nullable fields retained '+aid)
        supplied=all(a['current_paths'][k]['exists'] for k in ['source_descriptor_path','export_descriptor_path','provenance_path']) and all(r['current_sha256'] for r in a['provenance_version_bindings'])
        ck(a['source_delivery']['registered_source_export_provenance_and_children_present'] is bool(supplied),'actual presence basis '+aid)
        required_fields=c['provenance_record_required_fields']
        ck(a['source_delivery']['missing_provenance_fields']==[k for k in required_fields if k not in prov],'missing fields accurate '+aid)
        expected=[]
        for group,pk,hk in [('source','source_media_paths','source_media_sha256'),('export','exported_paths','exported_sha256')]:
            hs=prov[hk];pairs=zip(prov[pk],hs) if isinstance(hs,list) else hs.items()
            expected += [(group,p,h) for p,h in pairs]
        ck([(r['group'],r['path'],r['recorded_sha256']) for r in a['provenance_version_bindings']]==expected,'complete provenance pins '+aid)
        for r in a['provenance_version_bindings']:
            ck(r['current_sha256']==pins[r['path']]['sha256'],'current hash '+aid)
            relation='byte_identical' if r['current_sha256']==r['recorded_sha256'] else 'changed' if r['current_sha256'] else 'missing'
            ck(r['relation']==relation,'truthful source relation '+aid)
            if 'difference_id' in r:
                d=diffs[r['difference_id']]
                ck(d['path']==r['path'] and d['before_sha256']==r['recorded_sha256'] and d['after_sha256']==r['current_sha256'],'diff endpoints '+aid)
        inv=invmap[aid]
        old_records=list(inv['original_contract']['paths'].values())+inv.get('authored_sources',[])+inv.get('runtime_or_download_bundle',[])+inv.get('integration_sources',[])
        ck([(x['path'],x['recorded_sha256']) for x in a['prior_inventory_lineage']]==[(x['path'],x['sha256']) for x in old_records if x.get('sha256')],'complete inventory endpoints '+aid)
        ck({x['path']:x['recorded_sha256'] for x in a['registration_snapshot_lineage']}=={path:registration[path] for path in set(prov['source_media_paths']+prov['exported_paths']+[original['provenance_path']]) if path in registration},'complete registration endpoints '+aid)
        public_lineage=a['public_documentation_pin_lineage']
        if aid in ['asset.support.privacy_page','asset.support.support_page']:
            ck(public_lineage['current_sha256']==pins[original['provenance_path']]['sha256'],'public metadata current hash')
            ck(public_lineage['recorded_sha256']==pv['source_before'][original['provenance_path']],'public metadata exact reviewed hash')
            previous=frozen(public_lineage['historical_source']['path']);after=copy.deepcopy(prov)
            after['source_media_sha256']['services/docs/PRIVACY.md']=previous['source_media_sha256']['services/docs/PRIVACY.md']
            refresh=after.pop('documentation_pin_refresh')
            ck(after==previous and refresh['release_acceptance'] is False,'only reviewed doc pin plus explicit bridge added')
            ck(refresh['review_sha256']==pins[refresh['independent_review']]['sha256'],'public reviewer hash bound')
        else:ck(public_lineage is None,'public-specific bridge only applies to two assets')
        for lineage in ['prior_inventory_lineage','registration_snapshot_lineage']:
            ck(lineage in a,'explicit prior lineage '+aid)
            for r in a[lineage]:
                ck(r['current_sha256']==pins[r['path']]['sha256'],'prior lineage current endpoint '+aid)
                ck(r['relation']==('byte_identical' if r['current_sha256']==r['recorded_sha256'] else 'changed' if r['current_sha256'] else 'missing'),'prior lineage relation '+aid)
        for r in a['reviewed_version_relations']:
            v=e['versions'][r['version']];source=frozen(v['source_index']['path'])
            for p in r['relevant_inputs']:
                ck(p['current_sha256']==pins[p['path']]['sha256'],'runtime current pin '+aid)
                if p['path'] in source:
                    ck(p['recorded_sha256']==source[p['path']],'runtime historical pin '+aid)
                    ck(p['relation']==('byte_identical' if p['current_sha256']==source[p['path']] else 'changed'),'runtime relation '+aid)
                else:ck(p['relation']=='not_in_this_run_input_index','unindexed runtime '+aid)
            ck(r['same_relevant_inputs'] is all(x['relation']=='byte_identical' for x in r['relevant_inputs']),'truthful relevant-source equality '+aid)
            ck(r['whole_runtime_is_current'] is (v['current_changed_input_count']==0),'no blanket transfer '+aid)
        for t in a['host_tests']:
            if 'version' in t:
                matrix=matrices[t['version']];rows=matrix['rows']
                ck(t['rows']==len(t['row_indices']),'exact referenced row count '+aid)
                ck(len(t['row_indices'])==len(set(t['row_indices'])),'unique referenced rows '+aid)
                selected=[rows[i] for i in t['row_indices']]
                ck(all(r['result']=='passed_bounded_host_case' for r in selected),'actual passed rows '+aid)
                if t['version'].startswith('art'):
                    ck(len(selected)==12 and all(r['asset_id']==aid for r in selected),'actual art ID '+aid)
                    ck(t['condition_ids']==[r['condition_id'] for r in selected],'exact art conditions '+aid)
                else:
                    pid='.'.join(aid.split('.')[1:3])
                    ck(len(selected)==36 and all(r['pattern_id']==pid for r in selected),'actual calibration ID '+aid)
                    ck(t['condition_ids']==sorted(set(r['condition_id'] for r in selected)),'exact calibration conditions '+aid)
            elif t['type']=='reviewed_public_browser_rows':
                ck('public_refresh_review' in a['evidence_refs'],'per-asset independent public review')
                selected=[pb['rows'][idx] for idx in t['row_indices']]
                ck(len(selected)==6 and all(r['page']==t['page'] and not r['issues'] for r in selected),'public per-ID actual rows')
                ck(t['conditions']==[{'width':r['width'],'height':r['height'],'percent':r['percent']} for r in selected],'public exact conditions')
                ck(t['native'] is False and t['pseudolocalized'] is False,'public no invented modes')
            else:
                ck(t['type']=='exact_copy_to_tested_pattern_relation' and t['not_an_independent_render_run'] is True,'copy is not extra runtime evidence')
                cp=frozen(t['copy_export']['path']);graph=frozen(t['pattern']['path'])
                ck(t['all_equal'] is True and all(cp[k]==graph[k] for k in t['fields']),'copy-to-graph equality '+aid)
        ck(a['remaining_requirements']!=[],'remaining original obligations retained '+aid)
        ck(all(r in e['evidence'] for r in a['evidence_refs']),'resolved evidence refs '+aid)
        if original.get('exclude_from_client_packaging'):
            ck(original['required_variants']==['internal_document_review'],'internal documents not player variants')
    present=sum(a['source_delivery']['registered_source_export_provenance_and_children_present'] for a in b['assets'])
    ck(present==164 and b['summary']['registered_complete_count']==present,'all actual registered files supplied')
    drift_count=sum(any(r['relation']!='byte_identical' for r in a['provenance_version_bindings']) for a in b['assets'])
    ck(b['summary']['provenance_drift_asset_count']==drift_count,'drift summary')
    ck(sum(a['original_contract']['category']=='cosmetics' for a in b['assets'])==36,'exact36 cosmetics')
    for p in proposals['updates']:
        ck(p['applied'] is False,'proposal not applied')
        if p.get('kind')=='append_only_lineage_candidate':ck(p['proposed_changes']=={},'do not silently repin')
        else:
            ck(p['target']=='implementation/art/production_contract.json','only stale contract existence proposed')
            ck(p['proposed_changes']=={'status':'in_production','source_exists':True,'export_exists':True},'no verification promotion in proposal')
    if check_files:
        for p,x in pins.items():
            target=ROOT/x.get('snapshot_path',p)
            actual=digest(target.read_bytes()) if target.is_file() else None
            ck(actual==x['sha256'],'frozen/hash-bound input '+p)
            if live:
                f=ROOT/p;now=digest(f.read_bytes()) if f.is_file() else None
                ck(now==x['sha256'],'LIVE INPUT DRIFT '+p)
        for d in diffs.values():
            if 'diff_path' in d:
                actual=(ROOT/d['diff_path']).read_bytes();ck(digest(actual)==d['diff_sha256'],'diff artifact hash '+d['path'])
                before=pins[d['historical_source_path']];after=pins[d['path']]
                old=(ROOT/before.get('snapshot_path',d['historical_source_path'])).read_bytes()
                new=(ROOT/after.get('snapshot_path',d['path'])).read_bytes()
                ck(digest(old)==d['before_sha256'] and digest(new)==d['after_sha256'],'diff byte endpoints '+d['path'])
                expected=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile=d['historical_source_path'],tofile=d['path']))
                ck(actual==expected.encode(),'exact reproducible diff '+d['path'])
    return {'result':'passed_staged_source_and_lineage_checks','assertions':assertions,'assets':164,'frozen_inputs':len(pins),'live_recheck':live,'canonical_acceptance':False}

def selftest(b,e,i,d,p):
    checks=[]
    mutations=[
        ('drop_asset',lambda b,e,p:b['assets'].pop()),
        ('duplicate_id',lambda b,e,p:b['assets'][0].update(asset_id=b['assets'][1]['asset_id'])),
        ('drop_original_variant',lambda b,e,p:b['assets'][0]['required_variants'].pop()),
        ('fabricate_reviewer',lambda b,e,p:b['assets'][0]['preserved_provenance_fields'].update(reviewer='approved')),
        ('promote_asset',lambda b,e,p:b['assets'][0].update(canonical_verified=True)),
        ('claim_content_complete',lambda b,e,p:b['summary'].update(complete_content12_adopted=True)),
        ('remove_public_review',lambda b,e,p:e['evidence'].pop('public_refresh_review')),
        ('change_source_relation',lambda b,e,p:b['assets'][0]['provenance_version_bindings'][0].update(relation='changed')),
        ('invent_human_requirement',lambda b,e,p:b['assets'][0]['pacing_or_human_observation'].update(asset_human_signoff_inferred=True)),
        ('invent_rights',lambda b,e,p:b['assets'][0]['rights'].update(approval_inferred=True)),
        ('blanket_current_transfer',lambda b,e,p:next(x for x in b['assets'] if x['reviewed_version_relations'])['reviewed_version_relations'][0].update(whole_runtime_is_current=True)),
        ('wrong_row_id',lambda b,e,p:next(x for x in b['assets'] if x['host_tests'])['host_tests'][0].update(row_indices=list(range(12)))),
        ('missing_remaining_requirements',lambda b,e,p:b['assets'][0].update(remaining_requirements=[])),
        ('propose_verified',lambda b,e,p:p['updates'][0]['proposed_changes'].update(status='verified')),
    ]
    check(b,e,i,d,p,False)
    for name,mut in mutations:
        bb,ee,pp=copy.deepcopy(b),copy.deepcopy(e),copy.deepcopy(p)
        mut(bb,ee,pp)
        try:check(bb,ee,i,d,pp,False)
        except (ValueError,KeyError,IndexError):checks.append({'case':name,'rejected':True})
        else:raise ValueError('negative probe failed open: '+name)
    return {'passing_control':True,'negative_cases':checks,'passed':len(checks)}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--live',action='store_true');ap.add_argument('--self-test',action='store_true');args=ap.parse_args()
    b,e,i,d,p=[read(x) for x in ['bridge.json','evidence-index.json','inputs.json','differences.json','proposed-updates.json']]
    try:
        out=check(b,e,i,d,p,live=args.live)
        if args.self_test:out['adversarial']=selftest(b,e,i,d,p)
        print(json.dumps(out,indent=2))
    except (ValueError,KeyError,IndexError) as exc:
        print(json.dumps({'result':'failed','error':str(exc)}));sys.exit(1)
