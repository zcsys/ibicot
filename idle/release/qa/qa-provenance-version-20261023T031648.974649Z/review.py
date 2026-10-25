from pathlib import Path
import copy,difflib,hashlib,json
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
INPUT=ROOT/'release/asset-current-bridges/current-version-20261023';OLD=ROOT/'release/asset-current-bridges/staged';EX=ROOT/'release/asset-current-bridges/existence-integration-prepared-20261023T030808.744226Z'
reads={};checks=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 raw=p.read_bytes();reads[str(p.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest();return raw
def load(p):return json.loads(read(p))
def sha(p):return hashlib.sha256(read(p)).hexdigest()
def require(ok,label):
 assert ok,label
 checks.append(label)
def pins(rec,key,paths):
 v=rec[key]
 if isinstance(v,list):
  require(len(v)==len(rec[paths]),'parallel hash length');return dict(zip(rec[paths],v))
 require(set(v)==set(rec[paths]),'exact named hash bindings');return v

def check_record(before,after,declared,asset):
 key='author_source_version_update_20261023'
 require(key not in before,'version field newly explicit')
 expected=copy.deepcopy(before)
 for b in declared:
  value=expected['source_media_sha256']
  if isinstance(value,list):
   idx=expected['source_media_paths'].index(b['path']);require(value[idx]==b['prior_sha256'],'exact old list hash');value[idx]=b['current_sha256']
  else:
   require(value[b['path']]==b['prior_sha256'],'exact old mapping hash');value[b['path']]=b['current_sha256']
 require(set(after)==set(before)|{key},'only one added metadata field')
 require(after.get('asset_id')==asset,'unchanged stable asset ID')
 metadata=after[key]
 require(metadata['author']=='/root','explicit author identity')
 require(metadata['changed_source_bindings']==declared,'exact complete changed bindings')
 for flag in ['new_png_rendered','whole_asset_approval','combined_current_native_qualified']:
  require(metadata[flag] is False,'no '+flag)
 require(metadata['independent_source_version_review_pending'] is True,'review status remains pending')
 stripped=copy.deepcopy(after);stripped.pop(key)
 require(stripped==expected,'only declared source hash replacements')
 restored=copy.deepcopy(stripped)
 for b in declared:
  values=restored['source_media_sha256']
  if isinstance(values,list):values[restored['source_media_paths'].index(b['path'])]=b['prior_sha256']
  else:values[b['path']]=b['prior_sha256']
 require(restored==before,'exact reverse structural restoration')
 return metadata

proposal=load(INPUT/'proposal.json');contract=load('implementation/art/production_contract.json')
require(len(contract['assets'])==164,'164 original assets')
require(len(proposal['records'])==34,'34 version records')
require(len(proposal['source_differences'])==4,'four source versions')
require(proposal['applied'] is False and proposal['independent_review_pending'] is True,'proposal remains unapplied/pending')
require(sha(proposal['prior_reviewed_packet'])==proposal['prior_reviewed_packet_sha256'],'old handoff unchanged')
handoff=load(OLD/'HANDOFF.json')
for name,digest in handoff['files_sha256'].items():require(sha(OLD/name)==digest,'prior frozen packet '+name)
source_versions={}
for delta in proposal['source_differences']:
 require(sha(delta['path'])==delta['current_sha256'],'live source matches new pin '+delta['path'])
 require(sha(delta['current_source'])==delta['current_sha256'],'archived new source matches')
 require(sha(delta['prior_source'])==delta['prior_sha256'],'archived previous source matches')
 require(sha(delta['historical_source'])==delta['prior_sha256'],'original historical source exists exactly')
 require(sha(delta['diff_path'])==delta['diff_sha256'],'source patch hash')
 old=read(delta['prior_source']).decode();new=read(delta['current_source']).decode()
 patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=delta['path']+' (recorded version)',tofile=delta['path']+' (proposed version)'))
 require(patch.encode()==read(delta['diff_path']),'reproduced exact actual source diff')
 source_versions[delta['path']]=delta
records={r['asset_id']:r for r in proposal['records']};require(len(records)==34,'unique version record IDs')
asset_ids=[];export_count=0;source_changes=0;capture_paths=set();examples=[]
for asset in contract['assets']:
 asset_id=asset['asset_id'];rec=load(asset['provenance_path']);current=pins(rec,'source_media_sha256','source_media_paths');exports=pins(rec,'exported_sha256','exported_paths')
 actual_changes={p:(v,sha(p)) for p,v in current.items() if sha(p)!=v}
 for p,v in exports.items():require(sha(p)==v,'unchanged exact exported bytes '+p);export_count+=1
 if not actual_changes:
  require(asset_id not in records,'no unsolicited proposal for unchanged asset');continue
 require(asset_id in records,'all current mismatched source bindings proposed')
 r=records[asset_id];require(r['target']==asset['provenance_path'],'canonical record mapping')
 require(sha(r['target'])==r['before_sha256'],'canonical before untouched')
 require(sha(r['proposed_path'])==r['proposed_sha256'],'proposed exact hash')
 after=load(r['proposed_path']);metadata=check_record(rec,after,r['changed_bindings'],asset_id)
 require(sha(metadata['historical_record'])==metadata['historical_record_sha256']==r['before_sha256'],'original provenance exact backup')
 require(load(metadata['historical_record'])==rec,'original provenance record unchanged')
 declared={b['path']:(b['prior_sha256'],b['current_sha256']) for b in r['changed_bindings']}
 require(declared==actual_changes,'complete exact mismatch coverage')
 for b in r['changed_bindings']:require(b==source_versions[b['path']],'shared source delta exact')
 for p,v in pins(after,'source_media_sha256','source_media_paths').items():require(sha(p)==v,'all proposed source pins current')
 capture=rec.get('bounded_host_capture_evidence')
 if capture:
  for k,v in capture.items():
   if k.endswith('_path') and k[:-5]+'_sha256' in capture:
    require(sha(v)==capture[k[:-5]+'_sha256'],'historical capture evidence exact');capture_paths.add(v)
 require(after.get('original_required_variants')==rec.get('original_required_variants'),'variant requirements unchanged')
 asset_ids.append(asset_id);source_changes+=len(declared);examples.append((rec,after,r['changed_bindings'],asset_id))
require(set(asset_ids)==set(records),'all 34 records independently covered')
# Adversarial in-memory changes must fail this separate structural checker.
negatives=[]
for name,mutate in [
 ('grant approval',lambda r:r.__setitem__('production_acceptance',True)),
 ('change reviewer',lambda r:r.__setitem__('reviewer','invented reviewer')),
 ('change variant',lambda r:r['original_required_variants'].append('invented variant')),
 ('drop old capture',lambda r:r.__setitem__('bounded_host_capture_evidence',None)),
 ('change exported hash',lambda r:r['exported_sha256'].__setitem__(next(iter(r['exported_sha256'])),'0'*64)),
 ('claim native qualification',lambda r:r['author_source_version_update_20261023'].__setitem__('combined_current_native_qualified',True)),
 ('remove binding',lambda r:r['author_source_version_update_20261023']['changed_source_bindings'].pop()),
 ('change asset ID',lambda r:r.__setitem__('asset_id','invented.asset')),
]:
 before,after,bindings,asset=examples[0];mutated=copy.deepcopy(after);mutate(mutated)
 try:check_record(before,mutated,bindings,asset)
 except AssertionError:negatives.append(name)
 else:raise AssertionError('accepted mutation '+name)
# Reproduce the integrated 37 existence-only changes from the original packet.
applied=load(EX/'applied.json');prepared=load(EX/'integration.json');old_contract=load(EX/'production_contract.before.json');proposed_contract=load(EX/'production_contract.proposed.json');old_updates=load(OLD/'proposed-updates.json');independent=load('release/qa/lead-asset-bridge-20261021T143903.779189Z/independent-proposals.json')
require(sha(OLD/'proposed-updates.json')==applied['proposal_sha256']==independent['proposals_sha256'],'existence packet matches prior independent review')
require(sha(EX/'production_contract.before.json')==applied['expected_live_sha256'],'exact original contract')
require(sha(EX/'production_contract.proposed.json')==applied['proposed_sha256']==sha('implementation/art/production_contract.json'),'applied exact reviewed proposed contract')
expected=copy.deepcopy(old_contract);updates=[r for r in old_updates['updates'] if r['target']=='implementation/art/production_contract.json'];require(len(updates)==37,'37 original existence proposals')
actual_rows=[]
for u in updates:
 idx=int(u['json_pointer'].removeprefix('/assets/'));row=expected['assets'][idx]
 require(row['asset_id']==u['asset_id'],'pointer and stable ID exact')
 require(hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()==u['expected_record_sha256'],'previous whole-record digest exact')
 require(u['proposed_changes']=={'status':'in_production','source_exists':True,'export_exists':True},'only existence/inproduction changes')
 before={k:row[k] for k in u['proposed_changes']};row.update(u['proposed_changes']);actual_rows.append({'asset_id':u['asset_id'],'index':idx,'before':before,'after':u['proposed_changes']})
 require((ROOT/row['source_descriptor_path']).is_file() and (ROOT/row['export_descriptor_path']).is_file(),'actual source/export descriptors exist')
require(expected==proposed_contract==contract,'reverse full contract structure has no other changes')
require(actual_rows==applied['changes']==prepared['changes'],'all37 exact application records')
# Rehash every consumed file after review. Never repin a changing input.
changed=[p for p,v in reads.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=v];require(not changed,'all reviewed inputs stable')
result={'reviewer':'/root/qa_release','scope':'source-version bookkeeping and existence-only integration','proposal_sha256':sha(INPUT/'proposal.json'),'version_records':len(records),'source_versions':list(source_versions.values()),'source_bindings_changed':source_changes,'all_asset_source_exports_inspected':164,'export_bindings_unchanged':export_count,'prior_handoff_files_unchanged':len(handoff['files_sha256']),'prior_capture_paths_unchanged':sorted(capture_paths),'structural_mutation_rejections':negatives,'existence_changes_reproduced':len(updates),'existence_qualification':'existence/in_production only; no verification or approval','provenance_integration_recommended':True,'asset_approval_recommended':False,'native_or_new_capture_qualified':False,'checks':len(checks),'input_sha256':reads}
(OUT/'probe.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['input_sha256','source_versions','prior_capture_paths_unchanged']},indent=2))
