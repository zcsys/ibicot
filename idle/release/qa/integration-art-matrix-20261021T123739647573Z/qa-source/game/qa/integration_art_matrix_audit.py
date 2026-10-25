"""Independent scope, source, per-ID and current-host art evidence reconciliation."""
import hashlib,json,pathlib,re,shutil,collections,importlib.util
ROOT=pathlib.Path(__file__).resolve().parents[2]
EV=pathlib.Path(json.loads((ROOT/'game/qa/current_art_matrix_review.json').read_text())['evidence'])
checks=[]
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(label,yes):
 if not yes:raise AssertionError(label)
 checks.append(label)
contract=json.loads((ROOT/'implementation/art/production_contract.json').read_text());assets={a['asset_id']:a for a in contract['assets']}
prior=json.loads((ROOT/'release/art/entry-gates/contract-before.json').read_text());old={a['asset_id']:a for a in prior['assets']}
check('164 original IDs retained',len(assets)==len(old)==164 and set(assets)==set(old))
for aid,a in assets.items():check(aid+' original variants retained',a['required_variants']==old[aid]['required_variants'])
index=json.loads((ROOT/'release/art/catalogue-variants/per-id-evidence.json').read_text());wanted={k for k in assets if any(k.startswith('asset.'+g+'.') for g in ['harbor','producer','cosmetic'])}
check('68 reviewed IDs exactly',len(wanted)==68 and {a['asset_id'] for a in index['assets']}==wanted)
check('no canonical or external promotion',not index['canonical_verification_written'] and not index['original_variant_acceptance_promoted'] and not index['native_physical_rights_or_provider_approval'])
source_maps={};fullrows={};minimum=[]
for locale,run in index['runs'].items():
 proof=ROOT/run['proof_directory'];report=ROOT/run['report_path'];data=json.loads(report.read_text());meta=json.loads((proof/'verification.json').read_text());pins=json.loads((proof/'source-before.json').read_text());after=json.loads((proof/'source-after.json').read_text());source_maps[locale]=pins
 check(locale+' exact report',H(report)==run['report_sha256']==meta['art_report_sha256']);check(locale+' no source drift',pins==after and not meta['source_differences'])
 check(locale+' 524 inputs',len(pins)==524)
 for p,h in pins.items():check(locale+' frozen '+p,H(proof/'source'/p)==h)
 for result in meta['results']:
  check(locale+' actual '+result['name'],result['exit_code']==0 and H(proof/(result['name']+'.log'))==result['log_sha256'])
 check(locale+' fifty tests observed','+50: All tests passed!' in (proof/'art.log').read_text())
 pairs={(r['asset_id'],r['condition_id']) for r in data['rows']};check(locale+' 816 distinct rows',len(pairs)==len(data['rows'])==816)
 fullrows[locale]=data
 for a in index['assets']:
  matching=[r for r in data['rows'] if r['asset_id']==a['asset_id']]
  check(locale+' per-ID '+a['asset_id'],len(matching)==12 and sorted(r['condition_id'] for r in matching)==a['evidence_by_presentation_locale'][locale]['condition_ids'])
  check(locale+' variants '+a['asset_id'],a['original_required_variants']==assets[a['asset_id']]['required_variants'])
 ratios=next(s for s in data['supplemental_cases'] if s['case']=='declared_text_palette')['ratios'];minimum.append(min(ratios.values()));check(locale+' 16 explicit ratios',len(ratios)==16 and min(ratios.values())>=4.5)
 diffs=[]
for p in source_maps['en-US'].keys()|source_maps['qps-ploc'].keys():
 if source_maps['en-US'].get(p)!=source_maps['qps-ploc'].get(p):diffs.append(p)
check('only declared between-run inputs changed',set(diffs)=={'game/mobile/test/art_catalogue_variants_test.dart','source/art/verification/check_matrix.py'})
rep=json.loads((EV/'representative-results.json').read_text());check('two representative modes',len(rep)==2)
for run in rep:
 loc=run['locale'];data=json.loads((EV/loc/'report/matrix-results.json').read_text());check(loc+' independently reproduced 68 rows',len(data['rows'])==68 and {r['asset_id'] for r in data['rows']}==wanted and data['complete_matrix_observed'] is False)
 check(loc+' four test groups',(EV/loc/'art.log').read_text().count('All tests passed!')==1 and '+4: All tests passed!' in (EV/loc/'art.log').read_text())
 check(loc+' representative source fixed',run['source_differences']==[] and run['results'][0]['exit_code']==0)
 check(loc+' representative output bound',H(EV/loc/'report/matrix-results.json')==run['art_report_sha256'])
# Reward -> real catalogue mapping and the lack of a separate supporter art set.
source=(ROOT/'game/mobile/lib/cosmetics.dart').read_text();ids=re.findall(r'CosmeticDefinition\(\s*"([^"]+)"',source);check('catalogue 36 unique IDs',len(ids)==len(set(ids))==36)
counts=collections.Counter(i.rsplit('.',1)[0] for i in ids);check('catalogue 6+6+10+10+4',counts=={'cosmetic.core.chapter':6,'cosmetic.core.decoration':6,'cosmetic.free_pass':10,'cosmetic.premium_pass':10,'cosmetic.shop':4})
season=json.loads((ROOT/'game/events/content/season.01.json').read_text());rewards=[r for r in season['rewards'] if r['kind']=='cosmetic'];check('20 actual pass mappings',len(rewards)==20 and {r['content_id'] for r in rewards}=={i for i in ids if '.free_pass.' in i or '.premium_pass.' in i})
for r in rewards:check(r['id']+' no economic effects',r['economic_effects']==[] and r['level']==int(r['content_id'].rsplit('.',1)[1])*3)
campaign=json.loads((ROOT/'game/content/progression/campaign.json').read_text());check('six actual chapter rewards',set(c['reward_cosmetic_id'] for c in campaign['chapters'])=={i for i in ids if '.chapter.' in i})
# Read the trusted local literal catalogue only; do not contact a provider.
verification=(ROOT/'services/tideglass_service/verification.py').read_text();check('supporter reuses four shop IDs',"'dev.tideglass.supporter': [*[f'cosmetic.shop.{i:02d}' for i in range(1, 5)], 'soundtrack.01']" in verification)
# Independent sRGB contrast arithmetic from the production colors, no assertions derived only from report labels.
palette=(ROOT/'game/mobile/lib/palette.dart').read_text();colors={k:tuple(int(v[j:j+2],16)/255 for j in (2,4,6)) for k,v in re.findall(r'static const (\w+) = Color\(0x([0-9A-Fa-f]{8})\)',palette)}
def lum(rgb):return sum(w*(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4) for w,c in zip([.2126,.7152,.0722],rgb))
def ratio(a,b):a,b=sorted([lum(a),lum(b)]);return (b+.05)/(a+.05)
ratios={f'{f}_on_{b}':ratio(colors[f],colors[b]) for f in ['text','muted','teal','amber','warning'] for b in ['deep','panel','raised']}
# Flutter quantizes the alpha to an 8-bit channel before compositing.
a=round(.14*255)/255;blend=tuple((round(x*255)*round(.14*255)+round(y*255)*(255-round(.14*255)))//255/255 for x,y in zip(colors['teal'],colors['panel']))
ratios['teal_on_actual_build_button']=ratio(colors['teal'],blend)
for label,r in ratios.items():check('independent contrast '+label,r>=4.5)
visuals=['release/art/producer-contact-sheet.png','release/art/cosmetics-contact-sheet.png','source/art/registration/harbor-contact-sheet.png'];additional={}
for p in visuals+['release/art/catalogue-variants/source-snapshot.json','release/art/catalogue-variants/per-id-evidence.json','release/art/catalogue-variants/AUTHOR_REPORT.md','source/art/verification/coverage-contract.md','source/art/verification/staged-pseudo/harness.patch','implementation/art/production_contract.json','release/art/entry-gates/contract-before.json','v1_backlog.json','implementation/program.json','implementation/scope_requirements.json','services/tideglass_service/verification.py']:
 out=EV/'additional-source'/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out);additional[p]=H(out)
result={'independent_checks':len(checks),'check_names':checks,'all_passed':True,'full_author_runs':{'tests':100,'rows':1632,'ids':68,'source_inputs_each':524},'independently_reproduced':{'tests':8,'rows':136,'view':'320x720;100%;normal motion','modes':['en-US','qps-ploc'],'full_matrix_claim':False},'all_164_original_variant_lists_preserved':True,'between_run_changes':sorted(diffs),'production_between_runs_identical':True,'independent_palette_minimum':min(ratios.values()),'reported_palette_minimum':minimum,'images_inspected':visuals,'additional_inputs':additional,'canonical_status_writes':False,'physical_rights_provider_native_claims':False}
(EV/'independent-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['check_names','additional_inputs']},indent=2))
