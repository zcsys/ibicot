from pathlib import Path
import json,hashlib,sys
base=Path(__file__).resolve().parent;root=base.parents[2]
sys.path.insert(0,str(root/'tool'));import verify_native
pins={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(rel):
 p=root/rel;pins[rel]=sha(p);return p

def check(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)

def read(rel):return json.loads(pin(rel).read_bytes())
original='release/qa/client-final-reverse-20261025T150454.466933Z/REVERSE_SCOPE_REVIEW.md'
check(sha(pin(original))=='447c3f55ad880745e76c5919d704109d6482bcc3d71443680b75a11576f59ccb','original reverse review preserved')
s08='release/qa/s08-return-budget-clarification-20261025T154226.278440Z/REVIEW.md'
check(sha(pin(s08))=='c1104998aca2aea39eb88b227d25798f010272d0081ef6000c8b13e5a6909e58','mandatory S08 correction preserved')
for folder in ['client-audio-adoption-20261025T152944.392520Z','android-delivery-final-20261025T163933.344789Z','offline-pair-final-20261025T164515.363498Z','playable-phone-handoff-review-20261025T165554.784434Z','quiet-hours-contract-clarification-20261025T161119.038568Z','revoked-clock-independent-20261025T170122.048749Z']:
 for name in ('REVIEW.md','verification.json','seal.json'):
  rel='release/qa/'+folder+'/'+name
  if (root/rel).is_file():pin(rel)
for rel in ['TIDEGLASS_DESIGN.md','V1_ROADMAP.md','v1_backlog.json','docs/quality/android-ui-operator.md','game/mobile/lib/notification_service.dart','game/mobile/lib/notification_copy.dart','game/mobile/lib/notification_settings.dart','game/mobile/lib/reminder_lifecycle.dart']:
 pin(rel)
manifest=read('.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/manifest.json')
production=verify_native.production_inputs(manifest['source_sha256'])
check(len(production)==482,'same original482 production inputs')
for rel,want in production.items():check(sha(root/rel)==want,'unchanged frozen production: '+rel)
candidate=manifest['source_fingerprint'];check(candidate=='3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59','frozen3b00 identity')
def native(folder,expected):
 report=read(folder+'/verification.json');check(pins[folder+'/verification.json']==expected,'exact terminal report '+folder)
 check(report['passed'] is True and report['exit_code']==0,'actual native terminal success '+folder)
 check(report['candidate_fingerprint']==candidate,'exact unchanged production candidate '+folder)
 payload=read(folder+'/result.json');check(pins[folder+'/result.json']==report['evidence_sha256']['result.json'],'result hash bound to native report '+folder)
 return report,payload
r,d=native('release/native-notifications/integration-android-20261025T162843581392Z','0f4f530c677cb4bb1cb9293c23878e3a046e75af68183091181544a68a5c9758')
check(r['errors']==[] and r['production_differences_after']==[] and r['source_differences_during_run']==[] and r['frozen_source_unchanged'],'strict reminder source/failure result')
check(d['process_id']==8885 and d['gateway']=='NativeNotificationGateway' and d['preference_store']=='FileNotificationPreferences','actual Android gateway/source provenance')
check(d['completed'] and d['lifecycle_callback_failures']==[] and d['return_pending_ids']==[] and d['return_active_ids']==[],'actual completed delivery and cleared state')
check(d['returned_elapsed_ms']-d['scheduled_elapsed_ms']==511811,'actual real monotonic elapsed511811ms')
check(len(d['delivered_records'])==1 and d['delivered_records'][0]['id']==77101 and d['delivered_records'][0]['body']==d['plan']['body'],'actual original delivered body/ID')
check(d['plan']['due_utc_ms']-d['plan']['background_call_utc_ms']>=300000,'unchanged production5minute minimum')
r1,p1=native('release/native-proof/integration-android-offline-20261025T163852.724871Z','b77fc2974c7e5a0c5606e80118cc6ebaa031e275b14ef0fce3bc9bd0b6435e5d')
r2,p2=native('release/native-proof/integration-android-offline-20261025T164119.025808Z','9c44fc5645005e16de0988d51d3ee2e70479602f4028a33191923ed6b07730c5')
for report in (r1,r2):check(report['production_input_differences_after_run']==[] and report['harness_source_differences_during_run']==[] and report['verification_errors']==[] and report['source_snapshot_unchanged'],'offline unchanged source/strict completion '+report['scenario'])
check((p1['process_id'],p2['process_id'])==(9280,9798) and p1['save_directory']==p2['save_directory'] and p1['run_id']==p2['run_id'],'actual separate-process same-save offline pair')
check(p1['before_core']['counts']==[1,0,0,0,0] and p1['after_core']['counts']==p2['before_core']['counts']==[2,0,0,0,0],'actual native purchase and restored two-producer count')
check(int(p1['after_core']['lifetime_micros'])-int(p1['after_core']['wallet_micros'])==33600000,'original second producer cost, no new economy')
check(p2['offline_network']['predecessor_checkpoint_sha256']==p1['offline_network']['checkpoint_sha256'],'reload exact predecessor checkpoint')
check(len(p1['offline_network']['samples'])==105 and len(p2['offline_network']['samples'])==66,'actual app socket observation counts')
phone=read('release/native-proof/playable-phone-handoff-20261025T165004.928296Z/handoff-seal.json')
check(phone['candidate_fingerprint']==candidate and phone['archive_sha256']=='53c296abed7f7906a73a11e028852133b6860e449599f4c3dd5763099a62aa07','regular archived phone production-entry build')
check(phone['installed_bundle_files_exact']==124 and phone['android_touched'] is False,'bounded phone-only handoff')
for rel in ['release/native-proof/playable-phone-handoff-20261025T165004.928296Z/installation.json','release/native-proof/playable-phone-handoff-20261025T165004.928296Z/data-reconciliation.json']:
 pin(rel)
for rel in ['implementation/program.json','implementation/scope_requirements.json']:
 p=pin(rel);check(p.read_bytes()==(base/'baseline'/p.name).read_bytes(),'metadata still initial cutoff before final adoption: '+rel)
(base/'known-inputs.json').write_text(json.dumps({'state':'bounded known-input review; fresh revoked outcome/final adoption pending','checks':checks,'pins':pins,'production_fingerprint':candidate,'production_inputs_checked':len(production),'no_runtime_execution':True,'no_source_or_metadata_mutation':True},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'pins':len(pins),'status':'known deltas supported; waiting final outcome/adoption'}))
