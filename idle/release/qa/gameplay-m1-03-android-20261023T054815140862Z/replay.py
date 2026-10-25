#!/usr/bin/env python3
"""M1-03 Android appendix: archived evidence replay, no native execution."""
import copy
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRIOR=ROOT/'release/qa/gameplay-m1-03-20261023T051511165683Z'
CANDIDATE=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
PACKET=ROOT/'release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-m1-03-20261023T054217.678143Z/checkpoint.json'
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE/'review-tools'))
v=importlib.import_module('runner')
n=importlib.import_module('verify_native')
PINS={}; CHECKS=[]; NEG=[]; ROWS=[]; ENVELOPES=[]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
    path=Path(path);raw=path.read_bytes();value=sha(raw)
    assert str(path) not in PINS or PINS[str(path)]==value
    PINS[str(path)]=value
    return raw
def doc(path):return json.loads(read(path))
def check(ok,why):
    CHECKS.append({'check':why,'passed':bool(ok)})
    assert ok,why
def reject(why,fn):
    try: outcome=fn()
    except (AssertionError,ValueError,KeyError,TypeError):outcome=True
    check(bool(outcome),'Negative control: '+why);NEG.append(why)
def blocked(*args,**kwargs):raise AssertionError('Native or subprocess operation prohibited')
def entry(x,ident):
    if isinstance(x,dict):
        if x.get('id')==ident:return x
        for val in x.values():
            result=entry(val,ident)
            if result:return result
    elif isinstance(x,list):
        for val in x:
            result=entry(val,ident)
            if result:return result

def main():
    priorseal=doc(PRIOR/'seal.json')
    check(sha(read(PRIOR/'seal.json'))=='5af4da0081814d84f10acda3bc1be58f4168eb1eddc7e668642159974bed5629','Earlier review seal unchanged')
    for name,digest in priorseal['output_sha256'].items():check(sha(read(PRIOR/name))==digest,'Earlier review retained: '+name)
    # Preserve exact criteria/current status, never mutate them.
    for name in ['implementation/program.json','implementation/scope_requirements.json','v1_backlog.json']:
        raw=read(ROOT/name);(HERE/'inputs'/Path(name).name).write_bytes(raw)
    current=entry(doc(ROOT/'implementation/program.json'),'M1-03');original=entry(doc(ROOT/'v1_backlog.json'),'M1-03')
    check(current['source_acceptance']==original['acceptance'],'Original exact acceptance retained')
    check(current['source_acceptance_dependencies']==original['dependencies']==['M1-02'],'Original sole dependency retained')
    check(current['reviewer']=='gameplay' and current['scope_ids']==['S12'],'Original reviewer/scope retained')
    check(entry(doc(ROOT/'implementation/program.json'),'M1-02')['status']=='accepted','M1-02 accepted')
    check(current==entry(doc(PRIOR/'inputs/program.json'),'M1-03'),'Complete M1-03 record unchanged since prior review')
    manifest=doc(CANDIDATE/'manifest.json');check(sha(read(CANDIDATE/'manifest.json'))=='b4322606cd0207425b801feacc0bf4084ac9c460b23a028576204b766eeaeada','Frozen candidate manifest')
    oldpins=doc(PRIOR/'inputs-before.json')
    for path,digest in oldpins.items():
        if path.startswith(str(CANDIDATE/'source')):
            check(sha(read(path))==digest,'Relevant frozen source unchanged: '+path)
            live=ROOT/Path(path).relative_to(CANDIDATE/'source')
            check(sha(read(live))==digest,'Relevant production source unchanged: '+str(live))
    for file in (HERE/'review-tools').glob('*.py'):read(file)
    packet=doc(PACKET);check(sha(read(PACKET))=='eb1f40c77da66ce4c1910c0c76a1085c1abb05f029e68eba005cd44593270256','Exact sealed Android/iOS packet')
    check(packet['candidate_fingerprint']==manifest['source_fingerprint'],'Packet candidate')
    check(Counter(c['status'] for c in packet['cells'])=={'passed':12,'expected-interrupted':6}==packet['counts'],'18 actual cells:12 pass6 interrupted')
    # Original iOS records retain their exact previously reviewed pins.
    for cell in packet['cells']:
        if cell['label']=='ios-phone':
            check(cell['verification_sha256']==oldpins[cell['verification']]==sha(read(cell['verification'])),'Earlier iOS verification retained: '+cell['scenario'])
            for name,digest in cell['native_evidence_sha256'].items():
                path=Path(cell['verification']).parent/name
                check(oldpins[str(path)]==digest==sha(read(path)),'Earlier iOS archive retained: '+cell['scenario']+'/'+name)
    adoption=packet['android_tool_adoption'];check(sha(read(adoption['path']))==adoption['sha256'],'Explicit runner adoption pinned')
    adopted=doc(adoption['path'])
    for review in adopted['reviews']:check(sha(read(review['path']))==review['sha256'],'Different-author tool review pinned')
    rootreview=ROOT/'release/qa/lead-android-probe-review-20261023T0524Z'
    for name,digest in doc(rootreview/'verification.json')['pins'].items():check(sha(read(rootreview/name))==digest,'Tool review evidence '+name)
    oldrunner=read(ROOT/'release/native-proof/current-runtime-ios-phone-20261023T043347563069Z/runner.py')
    newrunner=read(HERE/'review-tools/runner.py')
    oldcall=b"self.adb_command('exec-out', 'run-as', BUNDLE, 'test', flag, str(target))"
    newcall=b"self.adb_command('shell', 'run-as', BUNDLE, 'test', flag, str(target))"
    check(oldrunner.count(oldcall)==1 and oldrunner.replace(oldcall,newcall)==newrunner,'Exact one-line boolean probe transport change; binary reads preserved')
    check(sha(newrunner)=='d1ea6d05085f05a0a3bb6c768531ef7659272e41993858c0551618f74ce5c847','Adopted corrected runner bytes')
    failed=packet['preserved_failed_original_android_preparation'];f=Path(failed['verification']);report=doc(f)
    check(sha(read(f))==failed['verification_sha256'] and report['status']=='failed' and report['passed'] is False,'Original Android preparation remains failed')
    check(report['verification_errors']==['ValueError: Native fixture component is a symlink'],'Original transport failure retained exactly')
    for name,digest in report['evidence_sha256'].items():check(sha(read(f.parent/name))==digest,'Original failed archive '+name)
    rows=[c for c in packet['cells'] if c['label']=='android'];check(len(rows)==9,'Exact nine new Android cells')
    for cell in rows:
        path=Path(cell['verification']);folder=path.parent;r=doc(path);scenario=r['scenario']
        check(sha(read(path))==cell['verification_sha256'],'Native report pin '+scenario)
        check(r['platform']=='android' and r['device']=='emulator-5556' and r['candidate_fingerprint']==manifest['source_fingerprint'],'Android candidate identity '+scenario)
        check(r['source_snapshot_unchanged'] is True and r['production_input_differences_after_run']==r['source_changes_during_run']==r['verification_errors']==[],'Native source/verification clean '+scenario)
        check(r['evidence_sha256']==cell['native_evidence_sha256'] and r['source_pins']==cell['source_pins'],'Sealed source/evidence maps exact '+scenario)
        for name,digest in cell['native_evidence_sha256'].items():check(sha(read(folder/name))==digest,'Archive '+scenario+'/'+name)
        expectedrunner=sha(oldrunner) if scenario=='runtime-lock-exclusion' else sha(newrunner)
        check(r['source_pins']['runner.py']==expectedrunner and r['harness_sha256']=='102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5','Correct per-cell runner and unchanged harness '+scenario)
        prior=v.validate_predecessor(Path(r['predecessor']['path']),r) if 'predecessor' in r else None
        if prior:
            check(sha(read(r['predecessor']['path']))==r['predecessor']['sha256'],'Exact predecessor pin '+scenario)
            check(prior['source_pins']['runner.py']==r['source_pins']['runner.py'],'Pair uses same reviewed runner '+scenario)
        rawlog=read(folder/'run.log');log=rawlog.decode(errors='replace');payload=None
        if scenario in v.KILLED:
            marker=v.marker_from_log(log,r);ledger=r['native_kill']
            check(r['status']=='expected-interrupted' and r['passed'] is False,'Interrupted not passed '+scenario)
            check(not v.interrupted_errors(log,r,marker,ledger,rawlog),'Actual interruption validator '+scenario)
            check(read(folder/'pre-kill.log')==rawlog[:ledger['pre_kill_log_bytes']],'Exact complete prekill prefix '+scenario)
            raw=read(folder/'checkpoint.json');v.validate_checkpoint(raw,r,marker['process_id'])
            check(sha(raw)==marker['checkpoint_sha256']==r['checkpoint_sha256'],'Marker/checkpoint hash '+scenario)
            observations=ledger['observations'];pid=str(marker['process_id'])
            kills=[x for x in observations if x.get('command',[])[-3:]==['kill','-9',pid]]
            check(len(kills)==1 and kills[0]['exit_code']==0,'Recorded actual Android kill -9 '+scenario)
            moment=kills[0]['observed_monotonic_ns']
            before=[x for x in observations if x.get('command',[])[-2:]==['pidof','dev.tideglass.game'] and x['observed_monotonic_ns']<moment]
            after=[x for x in observations if x.get('command',[])[-2:]==['pidof','dev.tideglass.game'] and x['observed_monotonic_ns']>moment]
            check(before and before[-1]['stdout'].strip()==pid and after and after[0]['exit_code']==1 and not after[0]['stdout'].strip(),'Recorded alive-to-absent native PID '+scenario)
            commandlines=[x for x in observations if x.get('command',[])[-2:]==['cat','/proc/'+pid+'/cmdline']]
            check(commandlines and commandlines[-1]['exit_code']==0 and commandlines[-1]['stdout'].split('\0')[0]=='dev.tideglass.game','Recorded package commandline identity '+scenario)
            bad=copy.deepcopy(ledger);bad['pre_kill_log_sha256']='0'*64
            reject('wrong interrupted prefix '+scenario,lambda:v.interrupted_errors(log,r,marker,bad,rawlog))
            reject('manufactured preparation completion '+scenario,lambda:v.interrupted_errors(log+'\nAll tests passed!\n',r,marker,ledger,rawlog+b'\nAll tests passed!\n'))
        else:
            payload=doc(folder/'result.json')
            check(r['status']=='passed' and r['passed'] is True and r['exit_code']==0,'Normal completion '+scenario)
            check(not n.native_log_errors(log),'Actual native and driver success, no late error '+scenario)
            check(not v.payload_errors(payload,r,prior),'Actual scenario and predecessor validator '+scenario)
            check(r['native_process_stop']['termination_observed'] is True,'Recorded native stop '+scenario)
            if prior:
                bad=copy.deepcopy(payload);bad['previous_native_process_id']+=1
                reject('wrong previous native PID '+scenario,lambda:v.payload_errors(bad,r,prior))
            bad=copy.deepcopy(payload);bad['completed']=False
            reject('incomplete result '+scenario,lambda:v.payload_errors(bad,r,prior))
            reject('late native exception '+scenario,lambda:n.native_log_errors(log+'\nI/flutter ( 1234): Unhandled Exception: review-negative\n'))
            if scenario.startswith('runtime-save-recover-'):
                bad=copy.deepcopy(payload);bad['save_loaded_amount']=bool(bad['save_loaded_amount'])
                reject('bool masquerades as integer amount '+scenario,lambda:v.payload_errors(bad,r,prior))
        generations=[]
        for name,metadata in r['generations'].items():
            if not metadata['size']:
                check(metadata['sha256'] is None and not (folder/name).exists(),'Absent generation '+scenario+'/'+name);continue
            raw=read(folder/name);container=json.loads(raw);e=container['envelope'];generations.append(e)
            check(len(raw)==metadata['size'] and sha(raw)==metadata['sha256'],'Actual generation length/hash '+scenario+'/'+name)
            canonical=json.dumps(e,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
            check(container['checksum']==sha(canonical),'Independent recursive save checksum '+scenario+'/'+name)
            # Android archived host read must contain the exact captured bytes.
            source_name='progress.'+name[len('generation-'):]
            reads=[o for o in r['host_observations'] if 'head' in o.get('command',[]) and o['command'][-1].endswith('/'+source_name)]
            check(reads and reads[-1]['exit_code']==0 and reads[-1]['stdout'].encode()==raw,'Actual private-storage read equals archive '+scenario+'/'+name)
            if scenario.startswith('runtime-save-'):
                amount=e['gameplay_state']['payload']['amount'];check(type(amount) is int and amount in [0,1,2],'Exact integer saved amount '+scenario+'/'+name)
            else:
                core=e['gameplay_state']['payload']['core'];expected='90000000' if scenario.endswith('-start') else '91000000'
                check(core['wallet_micros']==core['lifetime_micros']==expected,'Actual persisted exact transition earnings '+scenario+'/'+name)
                check(e['settled_through_utc']==('2026-10-21T12:01:00.000Z' if scenario.endswith('-start') else '2026-10-21T12:01:01.000Z'),'Exact persisted transition cursor '+scenario+'/'+name)
            ENVELOPES.append({'scenario':scenario,'file':name,'revision':e['revision'],'checksum':container['checksum']})
        generations.sort(key=lambda e:e['revision'])
        if len(generations)==2:
            old,new=generations;check(new['revision']==old['revision']+1 and new['parent']=={'save_id':old['save_id'],'branch_id':old['branch_id'],'revision':old['revision']},'Actual rolling lineage '+scenario)
        if scenario.startswith('runtime-save-recover-'):check(generations[-1]['gameplay_state']['payload']=={'amount':2},'Latest recovery generation exactly2 '+scenario)
        ROWS.append({'scenario':scenario,'verification':str(path),'status':r['status'],'process_id':r['native_process_id'],'previous_process_id':payload.get('previous_native_process_id') if payload else None,'loaded_amount':payload.get('save_loaded_amount') if payload else None,'lifetime_micros':payload.get('lifetime_micros') if payload else None,'os_version':payload.get('os_version') if payload else None})
    check(Counter(x['status'] for x in ROWS)=={'passed':6,'expected-interrupted':3},'Android exact6passed3expectedinterrupted')
    for name in ['REVIEW.md','verification.json']:read(ROOT/'release/qa/director-m1-08-20261023T054139.868139Z'/name)
    after={p:sha(Path(p).read_bytes()) for p in PINS};check(after==PINS,'All source/evidence inputs unchanged')
    summary={'candidate':str(CANDIDATE),'sealed_packet':str(PACKET),'checks':len(CHECKS),'negative_controls':len(NEG),'input_files':len(PINS),'android_cells':dict(Counter(x['status'] for x in ROWS)),'android_saved_envelopes':len(ENVELOPES),'whole_packet_cells':packet['counts'],'previous_review':str(PRIOR/'REVIEW.md'),'input_drift':[],'native_commands_run':False,'host_suites_rerun':False,'production_or_status_edits':False,'recommendation':'M1-03 original clause satisfied with accepted M1-02 prerequisite; S12 runtime verification satisfied. Director adoption remains metadata owner action.','release_acceptance':False}
    for name,value in [('checks.json',CHECKS),('negative-controls.json',NEG),('android-cells.json',ROWS),('save-envelopes.json',ENVELOPES),('inputs-before.json',PINS),('inputs-after.json',after),('verification.json',summary)]:
        (HERE/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    with patch.object(subprocess,'run',blocked),patch.object(subprocess,'Popen',blocked),patch.object(os,'kill',blocked),patch.object(os,'killpg',blocked):main()
