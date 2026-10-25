"""Read-only final canonical delta comparison. Run only after lead adoption."""
from pathlib import Path
import json,hashlib
base=Path(__file__).resolve().parent;root=base.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((base/'baseline/program.json').read_bytes());new=json.loads((root/'implementation/program.json').read_bytes())
os=json.loads((base/'baseline/scope_requirements.json').read_bytes());ns=json.loads((root/'implementation/scope_requirements.json').read_bytes())
changes=[]
def require(v,m):
 if not v:raise AssertionError(m)
def records(before,after,key,allow):
 require(set(before)==set(after),'top-level keys changed')
 require({k:v for k,v in before.items() if k!=key}=={k:v for k,v in after.items() if k!=key},'top-level metadata changed')
 require([x['id'] for x in before[key]]==[x['id'] for x in after[key]],'record identity/order changed')
 for a,b in zip(before[key],after[key]):
  for field in set(a)|set(b):
   if a.get(field)!=b.get(field) or (field in a)!=(field in b):
    require(a['id'] in allow and field in allow[a['id']],'unapproved delta: '+a['id']+'/'+field)
    changes.append({'id':a['id'],'field':field,'before':a.get(field),'after':b.get(field)})
records(old,new,'items',{'M3-05':{'status','evidence','evidence_note'}})
records(os,ns,'requirements',{'S26':{'delivery_status','evidence'},'S02':{'evidence'},'S08':{'evidence'}})
items={x['id']:x for x in new['items']};scope={x['id']:x for x in ns['requirements']}
require(items['M3-05']['status']=='accepted','M3-05 adoption not complete')
require(scope['S26']['delivery_status']=='verified','S26 adoption not complete')
require(items['M5-02']['status']=='in_progress' and not new['product_release_ready'],'unrelated release/accessibility status changed')
require(scope['S02']['delivery_status']==scope['S08']['delivery_status']=='not_verified','S02 or S08 limit removed')
for row in changes:
 if row['field']=='evidence':
  require(isinstance(row['after'],list) and set(row['before'])<=set(row['after']),'previous evidence removed')
  for rel in row['after']:
   require((root/rel).is_file(),'new evidence path missing: '+rel)
require(len(new['items'])==69 and len(ns['requirements'])==44,'original counts changed')
require(items['M3-05']['source_acceptance_dependencies']==['M1-05','M3-01'] and all(items[x]['status']=='accepted' for x in ['M1-05','M3-01']),'original settings prerequisites absent')
out={'changes':changes,'program_sha256':sha(root/'implementation/program.json'),'scope_sha256':sha(root/'implementation/scope_requirements.json'),'original_criteria_dependencies_and_remaining_fields_unchanged':True,'M3_05_prerequisites_accepted':True,'S02_S08_not_verified':True,'M5_02_in_progress':True,'product_release_ready':False,'production_or_metadata_mutation':False}
(base/'metadata-delta.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'changed_fields':len(changes),'program_sha256':out['program_sha256'],'scope_sha256':out['scope_sha256']}))
