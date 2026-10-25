#!/usr/bin/env python3
"""Bounded S39 archive review; no device, provider, process or production writes."""
import copy
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
EXECUTION=ROOT/'release/native-proof/execution-3b00-20261023T040612.562001Z'
CANDIDATE=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
PINS={};CHECKS=[];NEG=[];ROWS=[];OBS=[]
sys.dont_write_bytecode=True;sys.path.insert(0,str(HERE/'review-tools'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
 path=Path(path);raw=path.read_bytes();value=sha(raw)
 assert str(path) not in PINS or PINS[str(path)]==value
 PINS[str(path)]=value;return raw
def doc(path):return json.loads(read(path))
def check(ok,why):
 CHECKS.append({'check':why,'passed':bool(ok)});assert ok,why
def reject(why,fn):
 try:outcome=fn()
 except (ValueError,AssertionError,KeyError,TypeError):outcome=True
 check(bool(outcome),'Negative control: '+why);NEG.append(why)
def blocked(*a,**kw):raise AssertionError('External execution forbidden during read-only review')
def main():
 v=importlib.import_module('runner');n=importlib.import_module('verify_native');o=importlib.import_module('collector')
 for f in (HERE/'review-tools').glob('*.py'):read(f)
 for f in (HERE/'inputs').iterdir():read(f)
 manifest=doc(CANDIDATE/'manifest.json');check(sha(read(CANDIDATE/'manifest.json'))=='b4322606cd0207425b801feacc0bf4084ac9c460b23a028576204b766eeaeada','Exact frozen candidate manifest')
 for rel in ['game/mobile/lib/study_gate.dart','game/platform/lib/study_recorder.dart','game/mobile/lib/study_native_context.dart','game/mobile/lib/bootstrap.dart','game/persistence/lib/tideglass_persistence.dart']:
  check(sha(read(CANDIDATE/'source'/rel))==manifest['source_sha256'][rel]==sha(read(ROOT/rel)),'Relevant frozen/current production unchanged: '+rel)
 androidpath=EXECUTION/'sealed-android-socket-reobservations-20261023T075804.701127Z/checkpoint.json';android=doc(androidpath)
 withdrawalpath=EXECUTION/'sealed-withdrawal-four-20261023T080212.023065Z/checkpoint.json';withdrawal=doc(withdrawalpath)
 check(sha(read(androidpath))=='c83dc345e05240b3be90b4e67dfa176056f0fb4769ca2966caa3ca54eaf3e58c','Exact full Android checkpoint')
 check(sha(read(withdrawalpath))=='542b4c69a9ba32e1d70602e4d29c040bd3d7570988a7c567679c400b59fcb52e','Exact four withdrawal rows')
 check(Counter(c['status'] for c in android['cells'])==android['counts']=={'passed':23,'failed':4,'expected-interrupted':4},'Full Android statuses preserved; not all pass')
 failures=[];selected=[];canonical_saves=0
 # Rehash full sealed Android ledger without requalifying unrelated gameplay cells.
 for c in android['cells']:
  p=Path(c['verification']);r=doc(p)
  check(sha(read(p))==c['verification_sha256'],'Sealed Android report '+p.parent.name)
  check(r.get('status', 'passed' if r.get('passed') is True else 'failed')==c['status'],'Recorded Android status '+p.parent.name)
  for name,digest in c['native_evidence_sha256'].items():
   raw=read(p.parent/name);check(sha(raw)==digest,'Sealed Android archive '+p.parent.name+'/'+name)
   if name.startswith('native-save-') or name in ('generation-0.json','generation-1.json'):
    data=json.loads(raw);e=data['envelope'];check(data['checksum']==sha(json.dumps(e,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()),'Canonical archived game-save checksum '+p.parent.name+'/'+name);canonical_saves+=1
  if c['status']=='failed':failures.append({'scenario':c['scenario'],'verification':str(p),'errors':c['errors']})
  if c['scenario'].startswith('runtime-study-'):selected.append(c)
 # Fresh withdrawal evidence includes explicit new test-only harness pin.
 check(len(withdrawal['rows'])==4 and all(c['status']=='passed' for c in withdrawal['rows']),'Four fresh terminal withdrawal passes')
 for c in withdrawal['rows']:
  c=dict(c);c['native_evidence_sha256']=c['evidence_sha256'];selected.append(c)
 for p in [withdrawal['independent_review'],Path(withdrawal['independent_review']).parent/'verification.json']:
  if Path(p).exists():read(p)
 check(sha(read(withdrawal['old_phone_failed_report']))==withdrawal['old_phone_failed_sha256']=='d18dee13def9fbc4e892741ed1f235ed33464dae859a29398dbbcb0da5ab2616','Original failed iPhone withdrawal retained')
 oldfailed=doc(withdrawal['old_phone_failed_report']);check(oldfailed['status']=='failed' and oldfailed['passed'] is False,'Failed precondition remains failure')
 for name,digest in oldfailed['evidence_sha256'].items():check(sha(read(Path(withdrawal['old_phone_failed_report']).parent/name))==digest,'Old failed withdrawal archive '+name)
 oldh=read(Path(withdrawal['old_phone_failed_report']).parent/'harness.dart');newh=read(Path(withdrawal['rows'][0]['verification']).parent/'harness.dart')
 start=newh.index(b'      // The settings pointer queues');end=newh.index(b'      // Deliberately create',start)
 check(newh[:start]+newh[end:]==oldh,'997e harness is exactly reviewed queue-barrier insertion')
 check(sha(newh)=='997e7510aaef0dcebfa6505fc0dcde7d136a25e8a76abea78ede8602b0a4fef9','Fresh withdrawal exact harness')
 for c in selected:
  p=Path(c['verification']);folder=p.parent;r=doc(p);scenario=r['scenario']
  check(sha(read(p))==c['verification_sha256'],'Focused report pin '+p.parent.name)
  check(r['candidate_fingerprint']==manifest['source_fingerprint'] and r['source_snapshot_unchanged'] is True and r['production_input_differences_after_run']==r['source_changes_during_run']==r['verification_errors']==[],'Focused production source/verification clean '+p.parent.name)
  for name,digest in c['native_evidence_sha256'].items():check(sha(read(folder/name))==digest==r['evidence_sha256'][name],'Focused archive '+p.parent.name+'/'+name)
  for name,digest in r['source_pins'].items():check(r['evidence_sha256'][name]==digest,'Source identity '+p.parent.name+'/'+name)
  rawlog=read(folder/'run.log');log=rawlog.decode(errors='replace');prior=v.validate_predecessor(Path(r['predecessor']['path']),r) if 'predecessor' in r else None
  if prior:check(sha(read(r['predecessor']['path']))==r['predecessor']['sha256'],'Predecessor verification exact '+p.parent.name)
  if scenario in v.KILLED:
   marker=v.marker_from_log(log,r);check(not v.interrupted_errors(log,r,marker,r['native_kill'],rawlog),'Actual expected interruption ledger '+p.parent.name)
   check(read(folder/'pre-kill.log')==rawlog[:r['native_kill']['pre_kill_log_bytes']],'Prekill prefix '+p.parent.name)
   payload=None
  else:
   payload=doc(folder/'result.json');check(not n.native_log_errors(log) and not v.payload_errors(payload,r,prior),'Actual strict completion and scenario payload '+p.parent.name)
   check(r['passed'] is True and r['exit_code']==0 and r['native_process_stop']['termination_observed'] is True,'Normal completion plus observed stop '+p.parent.name)
   bad=copy.deepcopy(payload);bad['completed']=False;reject('incomplete '+p.parent.name,lambda:v.payload_errors(bad,r,prior))
   reject('late native exception '+p.parent.name,lambda:n.native_log_errors(log+'\nflutter: Unhandled Exception: review-only\n'))
   if prior:
    bad=copy.deepcopy(payload);bad['previous_native_process_id']+=1;reject('wrong predecessorPID '+p.parent.name,lambda:v.payload_errors(bad,r,prior))
  structure=v.inspect_study_artifacts(folder,r,r['study_artifacts']);check(structure==r['study_structure'],'Decode actual private study files '+p.parent.name)
  for name,info in r['study_artifacts'].items():
   if info['present']:
    raw=read(folder/name);check(len(raw)==info['size'] and sha(raw)==info['sha256'],'Private study bytes exact '+p.parent.name+'/'+name)
    if r['platform']=='android':
     basename=v.STUDY_FILES[name][0].split('/')[-1]
     reads=[c for c in r['host_observations'] if 'head' in c.get('command',[]) and c['command'][-1].endswith('/'+basename)]
     check(reads and reads[-1]['exit_code']==0 and reads[-1]['stdout'].encode()==raw,'Actual stopped-app Android read matches archive '+p.parent.name+'/'+name)
  if scenario in ['runtime-study-storage-withdraw','runtime-study-withdraw-reopen']:
   raw=doc(folder/'study-raw.json');check(raw=={'records':[],'registry':None,'schema_version':1,'status':'withdrawn'},'Exact erasure tombstone '+p.parent.name)
   check(read(folder/'study-withdrawn.marker')==b'stop' and not (folder/'study-eligibility.json').exists(),'Stop marker and absent eligibility '+p.parent.name)
   if scenario.endswith('-reopen'):
    check(payload['native_study_samples']==0 and payload['process_id']!=payload['previous_native_process_id'],'No context sampling in distinct withdrawn process '+p.parent.name)
   else:check(payload['storage_failure_visible'] is True and payload['withdrawal_durable'] is True,'Refusal-visible then UI withdrawal '+p.parent.name)
  ROWS.append({'scenario':scenario,'platform':r['platform'],'status':r['status'],'verification':str(p),'pid':r['native_process_id'],'previous_pid':payload.get('previous_native_process_id') if payload else None,'structure':structure})
 # Keep older partials; independently replay exact fresh collector/window data.
 fresh=0;timeouts=0
 for item in android['observations']:
  evidence=Path(item['native_verification']).parent;out=EXECUTION/('observation-'+evidence.name)
  for name,digest in item['all_files_sha256'].items():check(sha(read(out/name))==digest,'Observation archive '+evidence.name+'/'+name)
  final=doc(out/'finalization.json');observation=doc(out/'observation.json')
  check(final==item['finalization'],'Sealed exact observation result '+evidence.name)
  check(final['status']=='finalized-partial-observation' and final['paired_socket_storage_samples']==0 and final['traffic_absence_claim'] is False and final['release_acceptance'] is False,'Strict partial classification '+evidence.name)
  if final['collector_sha256']!='f6ae5e4a715b5ffc37999daa2919999e9a463f8ebd3ad238017be193ec47a438':
   OBS.append({'native_verification':item['native_verification'],'status':final['status'],'classification':'prior partial retained, not fresh timeout evidence'});continue
  fresh+=1;source=o.validate_source_binding(observation,out)
  rawlog=read(evidence/'run.log');log=rawlog.decode(errors='replace');payload=doc(evidence/'result.json');report=doc(evidence/'verification.json')
  check(not o.archived_completion_errors(source,log),'Pinned completion function confirms fresh observation app success '+evidence.name)
  opened,closed=o.window_pair(log,observation['context'])
  check(payload['privacy_observation_window']==final['window']=={'opened':opened,'closed':closed} and observation['opened']==opened,'Exact observed native interval '+evidence.name)
  check(rawlog.startswith(read(out/'open-prefix.log')) and sha(read(out/'open-prefix.log'))==observation['open_prefix_sha256'],'Observer captured prefix retained '+evidence.name)
  check(report['native_process_id']==payload['process_id']==observation['process_identity']['pid']==opened['process_id'],'Actual selected PID consistent '+evidence.name)
  for key,path in [('observation_sha256',out/'observation.json'),('native_verification_sha256',evidence/'verification.json'),('native_payload_sha256',evidence/'result.json'),('native_log_sha256',evidence/'run.log')]:check(final[key]==sha(read(path)),'Finalization input '+key+' '+evidence.name)
  for sample in observation['samples']:
   o.validate_sample_window(sample,opened,closed,observation['opened_observed_ns'],observation['process_identity'])
   check(sample['sockets']['status']=='unavailable' and 'timed out after 2 seconds' in sample['sockets']['reason'],'Actual-app socket timeout at2s '+evidence.name+str(sample['index']));timeouts+=1
   check(sample['storage']['status']=='unavailable' and 'descriptor-anchored' in sample['storage']['reason'],'No qualified concurrent Android storage '+evidence.name+str(sample['index']))
   check('rows' not in sample['sockets'] and 'files' not in sample['storage'],'Unavailable has no fabricated socket/storage inventory '+evidence.name+str(sample['index']))
  for command in observation['commands']:check(sha(command['stdout'].encode())==command['stdout_sha256'],'Archived observation stdout hash '+evidence.name)
  bad=copy.deepcopy(observation['samples'][0]);bad['finished_utc_ms']=closed['native_utc_ms']+1
  reject('late sample '+evidence.name,lambda:o.validate_sample_window(bad,opened,closed,observation['opened_observed_ns'],observation['process_identity']))
  bad=copy.deepcopy(observation['samples'][0]);bad['process_identity']['pid']+=1
  reject('wrong observation PID '+evidence.name,lambda:o.validate_sample_window(bad,opened,closed,observation['opened_observed_ns'],observation['process_identity']))
  OBS.append({'native_verification':item['native_verification'],'status':final['status'],'pid':report['native_process_id'],'samples':len(observation['samples']),'socket_timeouts':3,'qualified_storage_samples':0,'classification':'actual-app timeout; prior helperexit72 is not attributed here'})
 check(fresh==2 and timeouts==6,'Exactly six current actual-app timeouts across two fresh windows')
 # Pin independent approval of collector correction; this does not transfer helper results.
 for name in ['REVIEW.md','verification.json']:read(ROOT/'release/qa/lead-socket-transport-20261023T075414.187988Z'/name)
 after={p:sha(Path(p).read_bytes()) for p in PINS};check(after==PINS,'All inspected immutable and runtime inputs unchanged')
 summary={'candidate':str(CANDIDATE),'checks':len(CHECKS),'negative_controls':len(NEG),'input_files':len(PINS),'full_android_checkpoint':android['counts'],'focused_lifecycle_cells':dict(Counter(r['status'] for r in ROWS)),'fresh_withdrawal_passes':4,'actual_app_socket_timeouts':timeouts,'qualified_android_concurrent_storage_samples':0,'independently_recomputed_archived_game_save_checksums':canonical_saves,'native_commands_run':False,'host_suites_rerun':False,'production_or_status_edits':False,'input_drift':[],'full_S39_accepted':False,'provider_packages_accepted':False,'release_acceptance':False}
 for name,data in [('verification.json',summary),('checks.json',CHECKS),('negative-controls.json',NEG),('focused-cells.json',ROWS),('observation-results.json',OBS),('preserved-failures.json',failures),('inputs-before.json',PINS),('inputs-after.json',after)]: (HERE/name).write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 with patch.object(subprocess,'run',blocked),patch.object(subprocess,'Popen',blocked),patch.object(os,'kill',blocked),patch.object(os,'killpg',blocked):main()
