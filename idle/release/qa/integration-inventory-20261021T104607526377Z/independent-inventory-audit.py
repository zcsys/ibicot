"""Independent read-only forward/reverse inventory audit on immutable inputs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
root=Path(a.source);checks=[]
def check(ok, label):
 checks.append(label)
 if not ok:raise AssertionError(label)
def read(path):return json.loads((root/path).read_text())
def digest(path):return hashlib.sha256((root/path).read_bytes()).hexdigest()
manifest=read('implementation/content/launch_manifest.json');contract=read('implementation/art/production_contract.json')
base=read('release/content-evidence/inventory-baseline-manifest.json');forward=read('release/content-evidence/inventory-assets.json');reverse=read('release/content-evidence/inventory-reverse.json');index=read('release/content-evidence/inventory-index.json')
ids=[r['asset_id'] for r in contract['assets']];check(len(ids)==len(set(ids))==164,'164 original unique assets')
check([r['id'] for r in manifest['assets']]==[r['id'] for r in base['assets']]==ids,'original asset order and identity retained')
check([r['asset_id'] for r in forward['assets']]==ids,'exhaustive forward identity/order')
check(not manifest['release_ready'] and not contract['release_ready'],'no release promotion')
check(Counter(x['delivery_status'] for x in manifest['assets'])=={'in_production':162,'unproduced':2},'162 authored/in production, two unproduced')
check(all(x['verification_evidence'] is None for x in manifest['assets']),'no asset marked accepted')
allowed={'production_evidence','production_status','delivery_status','source_path','copy_status','implementation_status','runtime_source','inventory_evidence','scope_policy','status','fulfillment_status'}
changes=[]
def diff(x,y,path='$'):
 if type(x)!=type(y):changes.append(path);return
 if isinstance(x,dict):
  for k in sorted(x.keys()|y.keys()):
   if k not in x or k not in y:changes.append(path+'.'+k)
   else:diff(x[k],y[k],path+'.'+k)
 elif isinstance(x,list):
  check(len(x)==len(y),f'unchanged list size {path}')
  for i,(l,r) in enumerate(zip(x,y)):diff(l,r,f'{path}[{i}]')
 elif x!=y:changes.append(path)
diff(base,manifest)
check(len(changes)==378,'actual manifest leaf-difference count')
check(all(path.rsplit('.',1)[-1] in allowed for path in changes),'all changes restricted to declared inventory/status fields')
check(changes==sorted((x['path'] for x in read('release/content-evidence/inventory-manifest-diff.json'))),'reported manifest diff exact')
check(hashlib.sha256(json.dumps(index['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==index['fingerprint'],'author index fingerprint')
for path,want in index['files'].items():check(digest(path)==want,'author index bytes '+path)
rev={r['path']:r for r in reverse['files']};check(len(rev)==len(reverse['files'])==669,'669 unique reverse files')
for path,row in rev.items():
 check(row['exists'] and digest(path)==row['sha256'],'reverse file bytes '+path)
 check(set(row['asset_ids'])<=set(ids),'reverse references original IDs '+path)
 check(set(row['scope_ids'])<=set(f'S{i:02}' for i in range(1,45)),'reverse known scope IDs '+path)
actual_bundle={str(p.relative_to(root)) for folder in reverse['declared_asset_directories'] for p in (root/'game/mobile'/folder).rglob('*') if p.is_file()}
check(len(actual_bundle)==41,'41 actual files in declared mobile directories')
check(actual_bundle<=set(rev),'all actual bundle files reverse-mapped')
# Verify that the declared packaging list itself agrees with the real pubspec.
text=(root/'game/mobile/pubspec.yaml').read_text();block=text.split('  assets:',1)[1]
dirs=[]
for line in block.splitlines():
 if line and not line.startswith('    '):break
 m=re.fullmatch(r'\s+- (assets/[^ ]+/)\s*',line)
 if m:dirs.append(m.group(1))
check(dirs==reverse['declared_asset_directories'],'packaging directory list matches pubspec')
for folder in ['core','progression','events','persistence','platform','mobile']:
 for path in (root/'game'/folder/'lib').rglob('*.dart'):
  check(str(path.relative_to(root)) in rev,'all project Dart runtime sources reverse-mapped '+str(path.relative_to(root)))
for path in reverse['internal_release_files']:
 check(path not in actual_bundle,'internal operating/season documents not mobile asset files '+path)
missing=[];provenance_count=0;unreviewed=[];stale=[];verification_present=[]
for original,row,entry in zip(contract['assets'],forward['assets'],manifest['assets']):
 aid=original['asset_id'];check(row['entity_ids']==original['manifest_entity_ids'],'original entity bindings '+aid)
 for field in ['category','method','initial_delivery_work_item','initial_delivery_batch','delivery_channel','required_variants']:
  check(row['original_contract'][field]==original[field],'original contract '+aid+'/'+field)
 absent=[]
 for field in ['source_descriptor_path','export_descriptor_path','provenance_path','verification_path']:
  path=original[field];descriptor=row['original_contract']['paths'][field]
  check(descriptor['path']==path and descriptor['exists']==(root/path).is_file(),'original required path '+aid+'/'+field)
  if descriptor['exists']:check(descriptor['sha256']==digest(path),'original path digest '+aid+'/'+field)
  elif field!='verification_path':absent.append(field)
 if absent:missing.append({'asset_id':aid,'missing':absent})
 if (root/original['verification_path']).is_file():verification_present.append(aid)
 for field in ['authored_sources','runtime_or_download_bundle','integration_sources']:
  for source in row[field]:
   check(source['exists']==(root/source['path']).is_file(),'source existence '+aid+'/'+field)
   if source['exists']:
    check(digest(source['path'])==source['sha256'],'source digest '+aid+'/'+field)
    check(source['path'] in rev,'forward source reverse entry '+aid+'/'+field)
    check(aid in rev[source['path']]['asset_ids'],'forward/reverse reciprocal asset '+aid+'/'+field)
 provpath=root/original['provenance_path']
 if provpath.is_file():
  provenance_count+=1;prov=json.loads(provpath.read_text());check(prov['asset_id']==aid,'provenance own identity '+aid)
  if not prov.get('reviewer') or not prov.get('review_evidence'):unreviewed.append(aid)
  for field in ['source_media_sha256','exported_sha256']:
   for path,want in prov.get(field,{}).items():
    if not (root/path).is_file() or digest(path)!=want:stale.append({'asset_id':aid,'path':path,'recorded':want,'actual':digest(path) if (root/path).is_file() else None})
check(len(missing)==37,'37 original descriptor/provenance registration gaps')
check(provenance_count==len(unreviewed)==127,'127 existing provenance records need bounded independent review attribution')
check(len(stale)==36 and {s['path'] for s in stale}=={'game/mobile/lib/cosmetic_art.dart'},'36 cosmetic renderer provenance hashes are stale; no other hash discrepancy')
check(not verification_present,'no original per-asset verification path populated')
# Narrative and event payloads: counts and byte parity are checked directly,
# separate from proof of runtime reachability or editorial quality.
for relative in ['progression/campaign.json','progression/archive.en.json']:
 check((root/'game/content'/relative).read_bytes()==(root/'game/mobile/assets'/relative).read_bytes(),'narrative bundle identity '+relative)
campaign=read('game/content/progression/campaign.json');check(len(campaign['chapters'])==6 and campaign['ending']['allows_continued_play'],'six chapters/continued ending data')
check(campaign['chapters'][2]['objectives']==[{'kind':'stat_min','stat':'surveys_collected','value':12},{'kind':'stat_min','stat':'unique_calibrations','value':3}],'pre-remedy chapter3 calibration gate captured')
for i in range(1,13):
 for category,file in [('calibrations',f'calibration.{i:02}.pattern.json'),('challenges',f'challenge.{i:02}.json')]:
  check((root/'game/content'/category/file).read_bytes()==(root/'game/mobile/assets'/category/file).read_bytes(),'pattern/dossier byte identity '+file)
result={'source_assertion_count':len(checks),'checks':checks,'asset_count':164,'reverse_files':669,'mobile_bundle_files':41,'actual_manifest_leaf_changes':len(changes),'missing_registrations':missing,'provenance_count':provenance_count,'unreviewed_provenance_count':len(unreviewed),'stale_provenance':stale,'canonical_verification_records':len(verification_present),'release_accepted':False,'native_runtime_executed':False,'new_visual_acceptance':False,'boundary':'Inventory reconciliation at pre-calibration-remedy snapshot only; existence/hashes are not finished content, rights or variants.'}
Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['source_assertion_count','asset_count','reverse_files','mobile_bundle_files','actual_manifest_leaf_changes','unreviewed_provenance_count','canonical_verification_records','release_accepted']}))
