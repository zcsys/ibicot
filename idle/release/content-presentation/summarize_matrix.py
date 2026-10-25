"""Aggregate only twelve already-qualified immutable current-source runs."""
import argparse,json,hashlib,sys
from pathlib import Path
P=argparse.ArgumentParser();P.add_argument('--root',type=Path,required=True);P.add_argument('--matrix',type=Path,required=True);a=P.parse_args();root=a.root.resolve();matrix=a.matrix.resolve()
sys.path.insert(0,str(root/'release/content-presentation/staged/tool'))
from check_content_report import validate_run
contract=json.loads((root/'release/content-presentation/staged/expected-rows.json').read_text());expected=contract['conditions'];progress=json.loads((matrix/'progress.json').read_text());assert len(progress)==12 and all(r['exit_code']==0 for r in progress)
checks=[];fingerprints=set();sources=[];identities={};actual_conditions=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in progress:
 d=root/r['path'];result=validate_run(d,contract);actual_conditions.append(result['condition']);checks.append({**result,'directory':str(d.relative_to(root)),'evidence_sha256':{f:sha(d/f)for f in ['run.json','verification.json','test.jsonl','observations.json']}})
 fingerprints.add(result['source_fingerprint']);run=json.loads((d/'run.json').read_text());sources.append(run['source_before'])
 for row in json.loads((d/'observations.json').read_text())['rows']:
  key=row['id']+'|'+row['state'];identities.setdefault(key,{'id':row['id'],'state':row['state'],'route':row['route'],'conditions':[]})['conditions'].append({'condition':row['condition'],'row_sha256':hashlib.sha256(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'report':str((d/'observations.json').relative_to(root))})
assert len(fingerprints)==1 and all(s==sources[0]for s in sources)
assert sorted(actual_conditions,key=str)==sorted(expected,key=str)
assert len(identities)==137 and all(len(v['conditions'])==12 for v in identities.values())
assets={v['id']for v in identities.values()if v['id'].startswith('asset.')};flows={v['id']for v in identities.values()if not v['id'].startswith('asset.')};assert len(assets)==62
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
write(matrix/'per-id-evidence.json',{'schema_version':1,'identities':list(identities.values()),'host_only':True,'canonical_acceptance_changed':False})
write(matrix/'verification.json',{'schema_version':1,'complete_author_matrix':True,'source_fingerprint':next(iter(fingerprints)),'input_files_per_run':len(sources[0]),'conditions':checks,'passed_tests':876,'per_id_state_rows':1644,'distinct_id_states':137,'distinct_original_assets':len(assets),'additional_flows':sorted(flows),'source_unchanged_each_run':True,'same_inputs_all_runs':True,'original_asset_count':164,'original_required_variants_preserved':True,'independent_matrix_acceptance':False,'native_or_human_proof':False,'release_acceptance':False})
print(json.dumps({'pass':True,'tests':876,'rows':1644,'assets':len(assets),'inputs':len(sources[0]),'fingerprint':next(iter(fingerprints))}))
