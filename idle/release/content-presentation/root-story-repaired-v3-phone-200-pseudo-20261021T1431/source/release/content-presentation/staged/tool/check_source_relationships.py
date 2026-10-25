"""Source/descriptor identity checks; no rendered or release claim."""
import argparse,json
from pathlib import Path
from content_contract import load,sha,write
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root;checks=[];files={}
def read(rel):files[rel]=sha(root/rel);return load(root/rel)
def eq(id,key,export,runtime):
    if export!=runtime:raise ValueError(f'{id}: {key} mismatch')
    checks.append({'id':id,'field':key,'equal':True})
campaign=read('game/mobile/assets/progression/campaign.json')['chapters']
for c in campaign:
    d=read(f"game/content/locales/en-US/{c['id']}.copy.json")
    for k in ['title','intro','completion','hints']:eq('asset.'+c['id']+'.copy',k,d[k],c[k])
for n in range(1,13):
    id=f'challenge.{n:02}';d=read(f'game/content/locales/en-US/{id}.copy.json');r=read(f'game/mobile/assets/challenges/{id}.json')
    for k in ['title','intro','completion']:eq('asset.'+id+'.copy',k,d[k],r[k])
archive=read('game/mobile/assets/progression/archive.en.json')['entries']
for r in archive:
    d=read(f"game/content/locales/en-US/{r['id']}.json")
    for k in ['title','text']:eq('asset.'+r['id'],k,d[k],r[k])
season=read('game/mobile/assets/events/season.01.json');original=read('game/events/content/season.01.json');eq('asset.season.01.copy','bundle',season,original)
for r in season['rewards']:
    if r['kind']!='archive_fragment':continue
    d=read(f"game/content/locales/en-US/{r['content_id']}.json")
    for k in ['level','track','title','body','economic_effects']:eq('asset.'+r['content_id'],k,d[k],r[k])
    eq('asset.'+r['content_id'],'reward_id',d['reward_id'],r['id']);eq('asset.'+r['content_id'],'content_id',d['content_id'],r['content_id'])
ending=read('game/content/locales/en-US/ending.main.json');eq('asset.ending.main','text',ending['text'],campaign[-1]['completion'])
contract=read('implementation/art/production_contract.json');manifest=read('implementation/content/launch_manifest.json')
eq('all164','identity_set',sorted(x['asset_id']for x in contract['assets']),sorted(x['id']for x in manifest['assets']))
for x in contract['assets']:
    for field in ['source_descriptor_path','export_descriptor_path','provenance_path']:
        path=x[field];files[path]=sha(root/path)
write(a.output,{'schema_version':1,'kind':'source_relationships_only','checks':checks,'files':files,'rendered_claim':False,'release_acceptance':False,'remaining_runtime_binding':'Help descriptor paragraphs are compared to actual rendered HelpContent by the widget report checker. Non-UI public/internal documents keep separate review obligations. Unconsumed copy keys must not be described as read-through.'});print(json.dumps({'checks':len(checks),'pinned_files':len(files),'rendered_tests':0}))
