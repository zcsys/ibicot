#!/usr/bin/env python3
"""Execute the lead-approved test-only promotion after original observer completion."""
import argparse,datetime,hashlib,json,pathlib,shutil
from execute_cells import ROOT,EVIDENCE,cell
OLD='102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5'
NEW='997e7510aaef0dcebfa6505fc0dcde7d136a25e8a76abea78ede8602b0a4fef9'
LIVE=ROOT/'game/mobile/integration_test/current_runtime_test.dart'
STAGED=ROOT/'release/qa/native-withdraw-barrier-staged-20261023T044951.387640Z/current_runtime_test.dart'
REVIEW=ROOT/'release/qa/lead-withdraw-barrier-20261023T045309.713695Z/verification.json'
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert pin(REVIEW)=='1bb1e8dcde71b1cee55651405d59b61534909d6ca4e2c12cb0040698f36465c1'
assert pin(LIVE)==OLD and pin(STAGED)==NEW
parser=argparse.ArgumentParser();parser.add_argument('--android-default',type=pathlib.Path,required=True);parser.add_argument('--android-enroll',type=pathlib.Path,required=True);args=parser.parse_args()
rows=[json.loads(x) for x in (EVIDENCE/'cells.jsonl').read_text().splitlines() if x.strip()]
# Keep failed raw rows in the ledger; promotion requires one completed entry
# for every original Android scenario except the two deferred withdrawal cells.
raw_android=[x for x in rows if x['label']=='android' and x['scenario'].startswith('runtime-')]
android=[x for x in raw_android if x['status'] in ('passed','expected-interrupted') and (x['run_id'].startswith('v3b00-android-probe-fixed-') or x['run_id']=='v3b00-android-lock')]
assert len(android)==16 and len({x['scenario'] for x in android})==16
assert all(x['status']==('expected-interrupted' if '-hold' in x['scenario'] else 'passed') for x in android)
observations=[]
for label in ['ios-phone','android']:
 for scenario in ['runtime-study-default','runtime-study-enroll']:
  matches=[x for x in rows if x['label']==label and x['scenario']==scenario]
  if label=='android':
   exact=args.android_default if scenario=='runtime-study-default' else args.android_enroll
   matches=[x for x in matches if pathlib.Path(x['verification']).resolve()==exact.resolve()]
  assert len(matches)==1
  row=matches[0];assert row['finalize_exit_code']==0
  report=pathlib.Path(row['verification']);assert pin(report)==row['verification_sha256']
  assert json.loads(report.read_text())['harness_sha256']==OLD
  command=row['observer_command'];folder=pathlib.Path(command[command.index('--output')+1]);final=folder/'finalization.json';value=json.loads(final.read_text())
  if label=='android':
   observation=json.loads((folder/'observation.json').read_text());assert observation['collector_sha256']=='f6ae5e4a715b5ffc37999daa2919999e9a463f8ebd3ad238017be193ec47a438'
  expected_status='finalized-partial-observation' if label=='android' else 'finalized-sampled-observation'
  assert value['status']==expected_status and value['traffic_absence_claim'] is False and value['release_acceptance'] is False
  observations.append({'path':str(final),'sha256':pin(final),'native_verification':str(report)})
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=EVIDENCE/('withdraw-barrier-promotion-'+stamp);out.mkdir()
shutil.copyfile(LIVE,out/'before-current_runtime_test.dart');shutil.copyfile(STAGED,out/'after-current_runtime_test.dart')
record={'scope':'Lead-approved test-only serialized no-op barrier; frozen candidate and all production inputs remain untouched','review':str(REVIEW),'review_sha256':pin(REVIEW),'live':str(LIVE),'before_sha256':OLD,'after_sha256':NEW,'finalized_original_observations':observations,'promotion_completed':False}
(out/'promotion.json').write_text(json.dumps(record,indent=2)+'\n')
shutil.copyfile(STAGED,LIVE);assert pin(LIVE)==NEW
record['promotion_completed']=True;(out/'promotion.json').write_text(json.dumps(record,indent=2)+'\n')
print('PROMOTION '+str(out),flush=True)
for label in ['ios-phone','android']:
 run_id='v3b00-'+label+'-withdraw-barrier'
 prior=cell(label,'runtime-study-storage-withdraw',run_id)
 cell(label,'runtime-study-withdraw-reopen',run_id,prior)
