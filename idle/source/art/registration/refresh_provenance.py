#!/usr/bin/env python3
"""Refresh exactly proven cosmetic label + chapter03 copy pins; preserve history.
No reviewer, rights or acceptance field is filled by this author-side refresh.
"""
from pathlib import Path
import difflib
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
HISTORY=ROOT/'source/provenance/history/20261021-registration'
HISTORY.mkdir(parents=True,exist_ok=True)
REPORT=ROOT/'source/art/registration/provenance-refresh-proof.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def relative(path):return str(path.relative_to(ROOT))
def archive(path):
 target=HISTORY/path.name
 if not target.exists():target.write_bytes(path.read_bytes())
 return target

comparison_path=ROOT/'release/qa/integration-inventory-20261021T104607526377Z/cosmetic-renderer-comparison.json'
comparison=load(comparison_path)
prior=ROOT/comparison['prior_source']
current=ROOT/'game/mobile/lib/cosmetic_art.dart'
assert sha(prior)==comparison['prior_sha256']
assert sha(current)==comparison['current_sha256']
prior_text=prior.read_text();current_text=current.read_text()
expected="import 'presentation.dart';\nimport 'strings.dart';\n"+prior_text.replace("    label: '${cosmeticById(id).title}, harbor appearance preview',", "    label: UiEnglish.cosmeticCosmeticByIdIdTitleHarborAppearancePreview(\n      Presentation.authored((cosmeticById(id).title).toString()),\n    ),")
assert expected==current_text,'Cosmetic source differs beyond the independently recorded imports/semantics label.'
patch=''.join(difflib.unified_diff(prior_text.splitlines(True),current_text.splitlines(True),fromfile=relative(prior),tofile=relative(current)))
patch_path=ROOT/'source/art/registration/cosmetic-renderer-refresh.patch';patch_path.write_text(patch)
refreshed=[]
for path in sorted((ROOT/'source/provenance').glob('asset.cosmetic.*.json')):
 historic=archive(path);record=load(path);old=load(historic)
 assert old['source_media_sha256']['game/mobile/lib/cosmetic_art.dart']==comparison['prior_sha256']
 assert record['reviewer'] is None and record['review_evidence'] is None
 for f,h in old['source_media_sha256'].items():
  if f!='game/mobile/lib/cosmetic_art.dart':assert sha(ROOT/f)==h,(f,'unrelated cosmetic source drift')
 for f,h in old['exported_sha256'].items():assert sha(ROOT/f)==h,(f,'cosmetic export drift')
 record['source_media_sha256']['game/mobile/lib/cosmetic_art.dart']=sha(current)
 record['author_pin_refresh']={'date':'2026-10-21','historical_record':relative(historic),'historical_record_sha256':sha(historic),'old_renderer_sha256':sha(prior),'new_renderer_sha256':sha(current),'exact_diff_path':relative(patch_path),'exact_diff_sha256':sha(patch_path),'independent_bounded_source_comparison':relative(comparison_path),'independent_bounded_comparison_sha256':sha(comparison_path),'scope':'Only two localization imports and the Semantics label differ; remaining bytes including drawing geometry are identical. Existing PNG hashes are retained.','new_png_rendered':False,'independent_complete_asset_acceptance':False}
 dump(path,record);refreshed.append({'asset_id':record['asset_id'],'path':relative(path),'sha256':sha(path),'historical_path':relative(historic),'historical_sha256':sha(historic)})
assert len(refreshed)==36

path=ROOT/'source/provenance/asset.chapter.03.copy.json';historic=archive(path);old=load(historic);record=load(path)
prior_source=ROOT/'game/qa/workspaces/integration-inventory-20261021T104607526377Z/source/content/en-US/chapter.03.copy.md'
prior_export=ROOT/'release/balance/supplemental-source-394da363f5598c9b4d6ad84be7c85dee351daf3897f5c758a714db5eb6e3e1fb/game/content/locales/en-US/chapter.03.copy.json'
assert sha(prior_source)==old['source_media_sha256'][0]
assert sha(prior_export)==old['exported_sha256'][0]
current_source=ROOT/old['source_media_paths'][0];current_export=ROOT/old['exported_paths'][0]
before=load(prior_export);after=load(current_export)
assert set(before)==set(after)
assert all(before[k]==after[k] for k in before if k!='hints')
assert before['hints'][0]==after['hints'][0]
assert after['hints'][1]=='Calibration patterns are an optional discovery; accessible completion gives the same result.'
assert len(before['hints'])==len(after['hints'])==2
campaign=load(ROOT/'game/content/progression/campaign.json')
chapters=campaign['chapters'];chapter=next(c for c in chapters if c['id']=='chapter.03')
for field in ['title','intro','completion','hints']:assert after[field]==chapter[field],field
expected_source=after['title']+'\n\n'+after['intro']+'\n\n'+after['completion']+'\n\n'+'\n'.join('- '+h for h in after['hints'])+'\n'
assert current_source.read_text()==expected_source
chapter_patches=[]
for name,old_path,new_path in [('chapter03-source',prior_source,current_source),('chapter03-export',prior_export,current_export)]:
 dest=ROOT/f'source/art/registration/{name}.patch'
 dest.write_text(''.join(difflib.unified_diff(old_path.read_text().splitlines(True),new_path.read_text().splitlines(True),fromfile=relative(old_path),tofile=relative(new_path))))
 chapter_patches.append({'path':relative(dest),'sha256':sha(dest),'before_path':relative(old_path),'before_sha256':sha(old_path),'after_path':relative(new_path),'after_sha256':sha(new_path)})
assert record['reviewer'] is None and record['review_evidence'] is None
record['source_media_sha256']=[sha(current_source)];record['exported_sha256']=[sha(current_export)]
record['author_pin_refresh']={'date':'2026-10-21','historical_record':relative(historic),'historical_record_sha256':sha(historic),'diffs':chapter_patches,'current_campaign_path':'game/content/progression/campaign.json','current_campaign_sha256':sha(ROOT/'game/content/progression/campaign.json'),'scope':'Only second hint changed in this copy/export; title, intro, completion and Survey hint unchanged. New hint matches current campaign and describes calibration as optional. Economic/objective acceptance belongs to separate lead/QA review.','independent_complete_asset_acceptance':False}
dump(path,record)
report={'schema_version':1,'date':'2026-10-21','purpose':'Author-side exact source/provenance repair, not blanket independent review or rights approval','cosmetic_source_comparison':{'prior':relative(prior),'prior_sha256':sha(prior),'current':relative(current),'current_sha256':sha(current),'exact_expected_localization_diff':True,'geometry_unchanged':True,'patch':relative(patch_path),'patch_sha256':sha(patch_path),'independent_comparison':relative(comparison_path),'independent_comparison_sha256':sha(comparison_path)},'cosmetic_records':refreshed,'cosmetic_pngs_regenerated':False,'chapter03':{'provenance_path':relative(path),'provenance_sha256':sha(path),'historical_path':relative(historic),'historical_sha256':sha(historic),'copy_changes':chapter_patches,'current_campaign_sha256':sha(ROOT/'game/content/progression/campaign.json'),'copy_matches_current_campaign':True},'reviewer_fields_modified':False,'acceptance_promoted':False}
dump(REPORT,report)
print('Refreshed36 cosmetic renderer pins and chapter03 copy/export pins with exact diff proof; preserved37 historical provenance records; reviewer fields unchanged.')
