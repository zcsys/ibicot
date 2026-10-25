#!/usr/bin/env python3
"""Author-side checks for new asset registration, export parity and source pins.
These checks deliberately do not populate independent reviewer/acceptance fields.
"""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'source/art/registration'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
checks=[]
def check(condition,message):
 if not condition:raise AssertionError(message)
 checks.append(message)

contract=read('implementation/art/production_contract.json')
cmap={a['asset_id']:a for a in contract['assets']}
index=read('source/art/registration/registration-index.json')
manifest=read('implementation/content/launch_manifest.json')
assets={a['id']:a for a in manifest['assets']}
records=index['registrations']
expected={f'asset.harbor.restored.{i:02d}' for i in range(1,7)}|{'asset.harbor.unlit'}|{f'asset.archive.season01.{i:02d}' for i in range(1,21)}|{f'asset.support.{x}' for x in ['help','recovery_guide','release_notes','credits','operations_runbooks','season02_brief']}|{'asset.season.01.copy','asset.season.01.presentation'}
check(len(records)==35 and {a['asset_id'] for a in records}==expected,'Exactly35 scoped local registrations')
for r in records:
 aid=r['asset_id'];c=cmap[aid]
 check(r['required_variants']==c['required_variants'] and r['variants_remaining_open']==c['required_variants'],f'{aid}: original variants preserved/open')
 for key in ['source_descriptor_path','export_descriptor_path','provenance_path']:
  check(r[key]==c[key] and (ROOT/r[key]).is_file(),f'{aid}: exact original {key} exists')
 check(not r['canonical_verification_created'] and not (ROOT/c['verification_path']).exists(),f'{aid}: no invented canonical acceptance')
 for a in r['actual_sources']+r['registered_exports']:
  check(sha(a['path'])==a['sha256'],f'{aid}: current registered hash {a["path"]}')
 p=read(r['provenance_path'])
 check(p['reviewer'] is None and p['review_evidence'] is None and p['production_acceptance'] is False,f'{aid}: independent acceptance remains absent')
 check(p['distribution_terms_approval']=={'status':'not_recorded','owner':None,'evidence':None},f'{aid}: no unapproved rights claim')
 for field in ['source_media_sha256','exported_sha256']:
  for path,digest in p[field].items():check(sha(path)==digest,f'{aid}: provenance pin {path}')

missing=[]
for aid,c in cmap.items():
 if any(not (ROOT/c[k]).is_file() for k in ['source_descriptor_path','export_descriptor_path','provenance_path']):missing.append(aid)
check(sorted(missing)==['asset.support.privacy_page','asset.support.support_page'],'Only two public-page registrations remain missing')
for aid in missing:
 check(assets[aid]['delivery_status']=='unproduced',f'{aid}: public page remains unproduced')
check(len(assets)==164 and not manifest['release_ready'],'Manifest scope count and release-not-ready preserved')
check(not any(a['delivery_status']=='verified' for a in assets.values()),'No asset verification promotion')
canonical=list((ROOT/'source/provenance').glob('asset.*.json'))
check(len(canonical)==162,'162 authored asset provenance records exist')
for p in canonical:
 value=json.loads(p.read_text())
 check(value['reviewer'] is None and not value['review_evidence'],f'{p.name}: reviewer fields remain unfilled')

season=read('game/events/content/season.01.json')
check(sha('game/events/content/season.01.json')==sha('game/mobile/assets/events/season.01.json'),'Season source/bundle exact bytes')
for reward in season['rewards']:
 if reward['kind']=='archive_fragment':
  value=read(f'game/content/locales/en-US/{reward["content_id"]}.json')
  for field in ['content_id','level','track','title','body','economic_effects']:
   check(value[field]==reward[field],f'{reward["content_id"]}: current runtime {field}')
  check(value['reward_id']==reward['id'],f'{reward["content_id"]}: pass identity retained')
copy=read('game/content/locales/en-US/season.01.copy.json')
check(copy['copy']==season['copy'] and copy['title']==season['title'],'Complete season lifecycle copy exact')
check(len(copy['rewards'])==40 and len(copy['milestones'])==3,'Season copy includes all40 rewards and3 authored milestone texts')
help_extract=read('source/art/registration/help-runtime-extract.json')
for aid,original in help_extract.items():
 value=read(cmap[aid]['export_descriptor_path'])
 for field in original:check(value[field]==original[field],f'{aid}: exact Dart runtime extraction {field}')

native='release/native-proof/root-art-registration-20261021T111004.738637Z'
pins=read(f'{native}/source-before.json');verification=read(f'{native}/verification.json')
for path,digest in pins.items():check(sha(path)==digest,f'Host render source remains exact {path}')
check(verification['passed'] and verification['exit_code']==0 and verification['source_differences_during_run']==[],'Shared-lane host run passed with stable source')
for path,digest in verification['outputs_sha256'].items():check(sha(path)==digest,f'Host export hash {path}')
captures=read('source/art/registration/capture-manifest.json')['captures']
check(len(captures)==33,'33 actual host raster exports')
for c in captures:
 with Image.open(ROOT/c['path']) as image:
  check(image.format=='PNG' and image.size==(c['width'],c['height']),f'PNG dimension/decode {c["path"]}')
  image.load()
check(len({sha(c['path']) for c in captures if c['path'].endswith('.reduced-motion.png')})==7,'All seven fixed-phase restoration exports distinct')

pubspec=(ROOT/'game/mobile/pubspec.yaml').read_text()
bundles=re.findall(r'^    - (assets/[^\n]+)',pubspec,re.M)
for internal in ['release/runbooks/index.md','release/season-2-brief.md','source/operations/runbooks.md','source/planning/season-2-brief.md']:
 check(not any((ROOT/internal).resolve().is_relative_to((ROOT/'game/mobile'/b).resolve()) for b in bundles),f'Internal document excluded from declared client bundle {internal}')
check((ROOT/'source/planning/season-2-brief.md').read_bytes()==(ROOT/'release/season-2-brief.md').read_bytes(),'Initial Season2 source matches untouched root-owned export')
for doc in ['source/operations/runbooks.md','release/runbooks/index.md']:
 for link in re.findall(r'\]\(([^)]+)\)',(ROOT/doc).read_text()):check((ROOT/doc).parent.joinpath(link).is_file(),f'Internal runbook link resolves {doc}: {link}')

proof=read('source/art/registration/provenance-refresh-proof.json')
check(len(proof['cosmetic_records'])==36 and proof['reviewer_fields_modified'] is False and proof['acceptance_promoted'] is False,'Bounded pin refresh scope retained')
for r in proof['cosmetic_records']:
 check(sha(r['path'])==r['sha256'] and sha(r['historical_path'])==r['historical_sha256'],f'{r["asset_id"]}: before/after provenance history exact')
for path in ['source_media_sha256','exported_sha256']:
 current=read('source/provenance/asset.chapter.03.copy.json')
 paired=current['source_media_paths'] if path=='source_media_sha256' else current['exported_paths']
 for filename,digest in zip(paired,current[path]):check(sha(filename)==digest,f'Chapter03 refreshed {filename}')

report={'schema_version':1,'date':'2026-10-21','check_count':len(checks),'checks':checks,'result':'pass_author_checks_only','scope':'35 new registrations, exact exports, current source pins,37 bounded provenance repairs; no independent or whole-asset acceptance','remaining_missing_registrations':missing,'reviewer_fields_unfilled':len(canonical),'release_ready':False}
(HERE/'author-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(f'{len(checks)} author checks passed;35 registrations;33 actual PNGs;162 reviewer records remain unapproved;2 public pages blocked.')
