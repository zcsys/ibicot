from pathlib import Path
import hashlib,json,sys,difflib,collections
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).parent
OLD=R/'release/qa/client-reverse-scope-20261023T033233.346454Z'
C=R/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
A=R/'.tooling/build-candidates/20261023T032609.052120Z-a052a4405347'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
write=lambda n,x:(O/n).write_text(json.dumps(x,indent=2)+'\n')
m=load(C/'manifest.json');old=load(A/'manifest.json');prodManifest=m['source_sha256']
assert all(sha(C/'source'/n)==h for n,h in prodManifest.items())
sys.path.insert(0,str(R/'tool'));import verify_native
prod=verify_native.production_inputs(prodManifest)
assert all(sha(R/n)==prodManifest[n] and sha(C/'workspace'/n)==prodManifest[n] for n in prod)
oldContent=load(OLD/'runtime-content-hashes.json')
assert all(sha(R/x['path'])==x['expected_sha256'] and (R/x['path']).stat().st_size==x['expected_bytes'] for x in oldContent)
frozenDeltas=[]
for n in sorted(old['source_sha256'].keys()|prodManifest.keys()):
 a=old['source_sha256'].get(n);b=prodManifest.get(n)
 if a!=b:frozenDeltas.append({'path':n,'before':a,'after':b})
liveDeltas=[{'path':n,'frozen':h,'current':sha(R/n)} for n,h in prodManifest.items() if (R/n).exists() and sha(R/n)!=h]
write('source-identity.json',{'candidate':m['source_fingerprint'],'source_files_rehashed':len(prodManifest),'live_and_workspace_production_input_count':len(prod),'runtime_asset_content_count':len(oldContent),'runtime_asset_content_unchanged':True,'frozen_changes_from_prior_audit':frozenDeltas,'live_test_tool_changes':liveDeltas})
# Reuse prior independently inspected groups only when every source is rehashed;
# changed evidence is explicit, not silently inherited.
rows=load(OLD/'reverse-crosswalk.json');changed=[]
for row in rows:
 for p in row['evidence']:
  file=R/p['path']; now=sha(file)
  p['prior_review_sha256']=p['sha256'];p['sha256']=now;p['location']='current_workspace'
  p['unchanged_from_prior_review']=now==p['prior_review_sha256']
  if not p['unchanged_from_prior_review']:changed.append({'group':row['id'],'path':p['path'],'before':p['prior_review_sha256'],'after':now})
 if row['id']=='R23':row['observation']='Current frozen native build/host dependency gates, source-bound runtime/storage/study probes, explicit native reminder qualification, and independently summed purchase-mode gestures prepare original verification obligations. Test scenarios/seeded states remain separate from player evidence; callback-zone and capture harness corrections are test-only, reviewed by different authors. Native delivery/storage/physical qualification remains bounded by actual outcomes.'
 if row['id']=='R24':row['observation']='Source-bound native screenshot and preview captures/converters prepare original store assets. Phone/tablet current stills and actual19-second silent previews are locally reviewed; Android packet remains pending this audit finalization. Actual low measured bitrates, seeded setup, OS chrome, internal-only local Season previews and absent store ingestion remain disclosed. No public submission follows.'
write('reverse-crosswalk.json',rows);write('changed-crosswalk-evidence.json',changed)
assert {s for row in rows for s in row['scope_ids']}=={f'S{i:02}' for i in range(1,45)}
b=load(R/'v1_backlog.json');p=load(R/'implementation/program.json');s=load(R/'implementation/scope_requirements.json')
orig={x['id']:x for x in b['items']};items={x['id']:x for x in p['items']};assert len(orig)==65
for id,x in orig.items():
 assert items[id]['source_acceptance']==x['acceptance'],id
 assert items[id]['source_acceptance_dependencies']==x['dependencies'],id
beforeScope={x['id']:x for x in load(OLD/'authority/implementation/scope_requirements.json')['requirements']}
for row in s['requirements']:
 for key in ['id','requirement','source','work_items','verification']:assert row[key]==beforeScope[row['id']][key],(row['id'],key)
assert len(s['requirements'])==44 and not p['product_release_ready']
write('contract-check.json',{'original_backlog':65,'scope_requirements':44,'reverse_groups':25,'groups_cover_original_scope_ids':44,'original_acceptance_dependencies_preserved':True,'original_scope_criteria_and_links_preserved':True,'program_count':len(p['items']),'extra_tracking_ids':sorted(items.keys()-orig.keys()),'original_statuses':dict(collections.Counter(items[id]['status'] for id in orig)),'scope_statuses':dict(collections.Counter(x['delivery_status'] for x in s['requirements'])),'product_release_ready':p['product_release_ready'],'metadata_pins':{n:sha(R/n) for n in ['TIDEGLASS_DESIGN.md','V1_ROADMAP.md','v1_backlog.json','implementation/program.json','implementation/scope_requirements.json']}})
manifest=load(R/'implementation/content/launch_manifest.json');season=load(R/'game/mobile/assets/events/season.01.json');campaign=load(R/'game/mobile/assets/progression/campaign.json');economy=load(R/'game/mobile/assets/config/economy.json')
rewardCounts=collections.Counter(x['track']+':'+x['kind'] for x in season['rewards']); assert rewardCounts=={'free:archive_fragment':20,'free:cosmetic':10,'premium:cosmetic':10}
write('actual-content-counts.json',{'economy':economy,'campaign_chapters':len(campaign['chapters']),'campaign_all_economic_rewards_empty':all(not x['economic_rewards'] for x in campaign['chapters']),'campaign_all_paid_requirements_empty':all(not x['paid_requirements'] for x in campaign['chapters']),'challenges':len(list((R/'game/mobile/assets/challenges').glob('*.json'))),'calibrations':len(list((R/'game/mobile/assets/calibrations').glob('*.json'))),'cosmetics':len(manifest['cosmetics']),'producer_families':len(manifest['producer_families']),'harbor_presentations':len(manifest['harbor_presentations']),'assets':len(manifest['assets']),'pass_reward_counts':dict(rewardCounts),'season_days':season['duration_days'],'season_main_power_import':season['main_power_import'],'season_paid_effects':season['paid_effects'],'season_rechart':season['rechart_enabled'],'season_economic_exports':season['economic_exports']})
print(json.dumps({'source':len(prodManifest),'production':len(prod),'crosswalk':len(rows),'scope':44,'original_packages':65,'frozen_deltas':len(frozenDeltas),'live_deltas':len(liveDeltas)},indent=2))
