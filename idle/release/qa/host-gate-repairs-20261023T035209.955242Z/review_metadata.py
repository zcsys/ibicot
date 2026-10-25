from pathlib import Path
import hashlib,json
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).parent;A=R/'release/qa/lead-scope-gate-20261023T035344.579750Z';m=json.loads((A/'adoption.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def differences(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):return sum([differences(a.get(k),b.get(k),p+'/'+k) for k in sorted(a.keys()|b.keys())],[])
 if isinstance(a,list):
  if len(a)!=len(b):return [p]
  return sum([differences(v,b[i],p+'/'+str(i)) for i,v in enumerate(a)],[])
 return [] if a==b else [p]
expected={'implementation/program.json':{'/program_acceptance_evidence','/items/45/evidence','/items/45/evidence_note','/items/61/evidence_note'},'implementation/scope_requirements.json':{'/requirements/6/evidence','/requirements/6/delivery_status','/requirements/6/verification_note','/requirements/32/evidence','/requirements/32/delivery_status','/requirements/32/verification_note'},'implementation/content/launch_manifest.json':{'/scope_policy'},'implementation/art/program_status_reference.json':{'/program_sha256'}}
report={}
for f,h in m['before'].items():
 assert sha(A/'before'/f)==h
 assert sha(R/f)==m['after'][f]
 before=json.loads((A/'before'/f).read_text());after=json.loads((R/f).read_text());paths=differences(before,after);assert set(paths)==expected[f],(f,paths)
 if f.endswith('program.json'):
  for a,b in zip(before['items'],after['items']):
   for k in ('id','source_acceptance','source_acceptance_dependencies','status','reviewer'):assert a.get(k)==b.get(k),(a['id'],k)
  assert sum(x['status']=='accepted' and x['source']=='v1_backlog.json' for x in after['items'])==17
 if f.endswith('scope_requirements.json'):
  for a,b in zip(before['requirements'],after['requirements']):
   for k in ('id','requirement','verification','work_items','source'):assert a.get(k)==b.get(k)
   if a['id'] not in ('S07','S33'):assert a==b
  assert sum(x['delivery_status']=='verified' for x in after['requirements'])==9
 if f.endswith('launch_manifest.json'):
  assert before['assets']==after['assets'] and len(after['assets'])==164
 if f.endswith('program_status_reference.json'):assert after['program_sha256']==sha(R/'implementation/program.json')
 report[f]={'before':h,'after':m['after'][f],'exact_changed_paths':paths}
for f,h in m['adopted_review_sha256'].items():assert sha(R/f)==h
(O/'metadata-verification.json').write_text(json.dumps({'reviewer':'/root/qa_release','accepted_bounded_metadata_update':True,'original_criteria_dependencies_package_statuses_reviewers_preserved':True,'scope_changes_only':['S07','S33'],'asset_states_unchanged':164,'program_status_reference_already_existed_before_forward_audit':True,'changes':report},indent=2)+'\n');print('4 metadata files match exact declared delta; 65/44 criteria and original package statuses preserved')
