#!/usr/bin/env python3
"""Independent read-only replay of sealed native evidence; no device operations."""
import ast
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE = ROOT / '.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
FIRST = ROOT / 'release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-completed-phone-20261023T044235.533865Z/checkpoint.json'
TERMINAL = ROOT / 'release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-phone-terminal-20261023T044845.379377Z/checkpoint.json'
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / 'review-tools'))
v = importlib.import_module('verify_current_runtime')
n = importlib.import_module('verify_native')
o = importlib.import_module('runtime_observation')
PINS = {}
CHECKS = []
ROWS = []
NEGATIVES = []

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    path = Path(path)
    raw = path.read_bytes()
    value = sha(raw)
    if str(path) in PINS:
        assert PINS[str(path)] == value, 'Input changed during replay: ' + str(path)
    PINS[str(path)] = value
    return raw

def doc(path):
    return json.loads(read(path))

def check(ok, reason, **details):
    CHECKS.append({'check': reason, 'passed': bool(ok), **details})
    assert ok, reason

def reject(name, fn):
    try:
        outcome = fn()
    except (ValueError, KeyError, TypeError, AssertionError) as error:
        NEGATIVES.append({'probe': name, 'rejected': True, 'reason': str(error)})
        return
    check(bool(outcome), 'Negative control must reject: ' + name)
    NEGATIVES.append({'probe': name, 'rejected': True, 'reason': outcome})

def blocked(*args, **kwargs):
    raise AssertionError('External command or native process operation forbidden in this review')

def pin_tree(mapping, base, report_mapping=None):
    for name, expected in mapping.items():
        check(Path(name).name == name, 'Safe archived evidence name', name=name)
        check(sha(read(base/name)) == expected, 'Archived bytes match sealed pin', path=str(base/name))
        if report_mapping is not None:
            check(report_mapping.get(name) == expected, 'Native report and checkpoint agree on evidence hash', path=str(base/name))

def save_envelope(path):
    raw = doc(path)
    check(raw.get('format') == 'tideglass-checksummed-save', 'Captured save format', path=str(path))
    envelope = raw['envelope']
    canonical = json.dumps(envelope, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    check(raw['checksum'] == sha(canonical), 'Independent canonical save checksum', path=str(path))
    check(envelope['format'] == 'tideglass-save-envelope' and envelope['schema_version'] == 1,
          'Versioned actual captured save envelope', path=str(path))
    check(type(envelope['revision']) is int and envelope['revision'] >= 0, 'Nonnegative save revision', path=str(path))
    return envelope

def review_observer(cell, report, payload, log):
    folder = Path(cell['observer_directory'])
    pin_tree(cell['observer_sha256'], folder)
    observation = doc(folder/'observation.json')
    final = doc(folder/'finalization.json')
    check(final == cell['observer_finalization'], 'Sealed observer finalization exactly matches actual bytes')
    check(observation['status'] == 'collected-pending-native-completion' and not observation['errors'], 'Observation collection completed before finalization')
    source = o.validate_source_binding(observation, folder)
    check(not o.archived_completion_errors(source, log), 'Exact archived completion function accepts real observer log')
    opened, closed = o.window_pair(log, observation['context'])
    check(payload['privacy_observation_window'] == {'opened': opened, 'closed': closed} == final['window'], 'One exact window in log, payload and finalization')
    check(opened == observation['opened'], 'Recorded window open unchanged')
    check(report['native_process_id'] == payload['process_id'] == opened['process_id'] == observation['process_identity']['pid'], 'Native observer actual PID bound to result')
    check(report['privacy_observation_enabled'] is True and '--dart-define=TIDEGLASS_PRIVACY_OBSERVATION=true' in report['command'], 'Explicit runtime observation enabled')
    check(report['candidate_path'] == observation['candidate'] == str(CANDIDATE), 'Observer exact candidate path')
    for key, expected in observation['context'].items():
        check(report.get('label' if key == 'device_label' else key) == payload.get(key) == expected, 'Observer identity field', field=key)
    for name, expected in observation['source_binding']['native_source_sha256'].items():
        check(report['source_pins'][name] == report['evidence_sha256'][name] == expected, 'Observer candidate/source pin', file=name)
    prefix = read(folder/'open-prefix.log')
    check(log.encode().startswith(prefix) and sha(prefix) == observation['open_prefix_sha256'], 'Native final log retains exact observed opening prefix')
    expected_hashes = {'observation_sha256': sha(read(folder/'observation.json')),
        'native_verification_sha256': sha(read(cell['verification'])),
        'native_payload_sha256': sha(read(Path(cell['verification']).parent/'result.json')),
        'native_log_sha256': sha(read(Path(cell['verification']).parent/'run.log'))}
    for key, expected in expected_hashes.items():
        check(final[key] == expected, 'Finalization input hash', field=key)
    paired = 0
    for sample in observation['samples']:
        o.validate_sample_window(sample, opened, closed, observation['opened_observed_ns'], observation['process_identity'])
        check(sample['sockets']['status'] == sample['storage']['status'] == 'observed', 'iOS sample socket/storage observed')
        check(set(sample['storage']['files']) == set(o.FILES), 'Seven fixed fixture files only')
        paired += 1
        commands = [x for x in observation['commands'] if sample['started_ns'] <= x['started_ns'] <= x['finished_ns'] <= sample['finished_ns']]
        preceding = [x for x in observation['commands'] if x['argv'][0] == '/bin/ps' and x['finished_ns'] <= sample['started_ns']]
        identities = preceding[-1:] + [x for x in commands if x['argv'][0] == '/bin/ps']
        check(len(identities) == 2, 'Each sample has two captured identity brackets')
        for command in identities:
            parsed = o.parse_ios_identity(command['stdout'].encode(), opened['process_id'], Path(observation['process_identity']['executable']))
            check(parsed == sample['process_identity'], 'Actual captured ps output parses to same PID/start/executable')
        sockets = [x for x in commands if x['argv'][0] == '/usr/sbin/lsof']
        check(len(sockets) == 1 and o.parse_lsof(sockets[0]['stdout'].encode(), opened['process_id']) == sample['sockets']['rows'], 'Captured lsof output reproduces socket rows')
        workers = [x for x in commands if 'storage-worker' in x['argv']]
        check(len(workers) == 1, 'One bounded storage worker per sample')
        worker = json.loads(workers[0]['stdout'])
        check(worker['files'] == sample['storage']['files'] and worker['collector_sha256'] == observation['collector_sha256'], 'Actual worker bytes reproduce fixed inventory')
    for command in observation['commands']:
        check(sha(command['stdout'].encode()) == command['stdout_sha256'], 'Captured observer command stdout hash')
    check(final['paired_socket_storage_samples'] == paired == final['samples'] == len(observation['samples']), 'Finalization exact paired sample count')
    check(final['status'] == 'finalized-sampled-observation' and final['traffic_absence_claim'] is False and final['release_acceptance'] is False, 'Bounded observation classification preserved')
    sample = copy.deepcopy(observation['samples'][0]); sample['process_identity']['pid'] += 1
    reject('observer wrong PID', lambda: o.validate_sample_window(sample, opened, closed, observation['opened_observed_ns'], observation['process_identity']))
    sample = copy.deepcopy(observation['samples'][0]); sample['finished_utc_ms'] = closed['native_utc_ms'] + 1
    reject('observer sample extends one millisecond past close', lambda: o.validate_sample_window(sample, opened, closed, observation['opened_observed_ns'], observation['process_identity']))
    broken = copy.deepcopy(observation); broken['collector_sha256'] = '0'*64
    reject('observer wrong collector hash', lambda: o.validate_source_binding(broken, folder))
    reject('observer late native exception despite prior success', lambda: o.archived_completion_errors(source, log+'\nflutter: Unhandled Exception: injected-review-only\n'))
    return {'samples': paired, 'status': final['status'], 'process_id': opened['process_id'], 'elapsed_us': closed['native_elapsed_us']-opened['native_elapsed_us'], 'traffic_absence_claim': False}

def review_cell(cell, candidate_hash):
    path = Path(cell['verification']); folder=path.parent
    report=doc(path)
    check(sha(read(path)) == cell['verification_sha256'], 'Verification bytes match sealed checkpoint', path=str(path))
    check(report['candidate_fingerprint'] == candidate_hash, 'Exact reviewed frozen candidate')
    check(report['source_snapshot_unchanged'] is True and report['production_input_differences_after_run'] == [], 'Frozen production inputs unchanged during native cell')
    check(report.get('source_changes_during_run', report.get('harness_source_differences_during_run')) == [], 'Native runner/harness source unchanged during cell')
    check(report['verification_errors'] == cell.get('errors', []), 'Sealed cell retains exact native verification errors')
    pin_tree(cell['native_evidence_sha256'], folder, report['evidence_sha256'])
    check(set(report['evidence_sha256']) <= set(cell['native_evidence_sha256']), 'Sealed checkpoint includes every native report evidence pin')
    scenario=cell['scenario']; current=scenario.startswith('runtime-')
    rawlog=read(folder/'run.log'); log=rawlog.decode(errors='replace')
    row={'scenario':scenario,'status':cell['status'],'verification':str(path),'platform':report['platform'],'device':report['device'],'save_envelopes':[]}
    if cell['status'] == 'failed':
        check(report['passed'] is False and report['status'] == 'failed' and report['exit_code'] != 0, 'Original failed native status is preserved')
        payload=doc(folder/'result.json')
        check(bool(n.native_log_errors(log)) and bool(v.payload_errors(payload,report)), 'Independent actual completion and payload checks reject original failed cell')
        check(payload.get('completed') is not True and 'withdrawal_durable' not in payload and 'storage_failure_visible' not in payload, 'Failed precondition provides no completed fault injection or withdrawal evidence')
        check('current_evidence_102be09eb804_test.dart:845:7' in log and 'Expected: false' in log and 'Actual: <true>' in log, 'Actual failure located at hash-named harness copy guard absence precondition')
        row.update(errors=report['verification_errors'],disposition='Preserved failed precondition before injected guard or withdrawal; no production fault attribution from this alone.')
        ROWS.append(row)
        return
    for name in cell['native_evidence_sha256']:
        if name.startswith('native-save-') or name in ('generation-0.json','generation-1.json'):
            envelope=save_envelope(folder/name)
            row['save_envelopes'].append({'file':name,'revision':envelope['revision'],'checksum':doc(folder/name)['checksum'],'payload':envelope['gameplay_state'].get('payload') if current and scenario.startswith('runtime-save') else None})
    if current:
        for name, source_hash in report['source_pins'].items():
            check(report['evidence_sha256'][name] == source_hash, 'Actual current runner sources pinned', name=name)
        prior=v.validate_predecessor(Path(cell['predecessor']), report) if cell['predecessor'] else None
        if prior:
            check(report['predecessor']['sha256'] == sha(read(cell['predecessor'])) and report['predecessor']['path'] == cell['predecessor'], 'Current predecessor exact report hash and path')
        if scenario in v.KILLED:
            check(cell['status'] == report['status'] == 'expected-interrupted' and report['passed'] is False, 'Killed preparation is not a pass')
            marker=v.marker_from_log(log,report)
            check(not v.interrupted_errors(log,report,marker,report['native_kill'],rawlog), 'Actual complete interruption ledger accepted')
            check(read(folder/'pre-kill.log') == rawlog[:report['native_kill']['pre_kill_log_bytes']], 'Exact pre-kill prefix retained')
            checkpoint=read(folder/'checkpoint.json')
            v.validate_checkpoint(checkpoint,report,marker['process_id'])
            check(sha(checkpoint) == marker['checkpoint_sha256'] == report['checkpoint_sha256'], 'Native checkpoint hash linked to kill marker')
            row['process_id']=marker['process_id']
            reject('interrupted preparation cannot contain completion',lambda:v.interrupted_errors(log+'\nflutter: 00:00 +1: All tests passed!\nAll tests passed.\n',report,marker,report['native_kill'],rawlog+b'\nflutter: 00:00 +1: All tests passed!\nAll tests passed.\n'))
            ledger=copy.deepcopy(report['native_kill']);ledger['pre_kill_log_sha256']='0'*64
            reject('wrong pre-kill prefix hash',lambda:v.interrupted_errors(log,report,marker,ledger,rawlog))
        else:
            payload=doc(folder/'result.json')
            check(report['passed'] is True and report['status'] == cell['status'] == 'passed' and report['exit_code']==0, 'Actual normal current completion status')
            check(not n.native_log_errors(log), 'Actual native framework and driver completion')
            check(not v.payload_errors(payload,report,prior), 'Actual scenario payload and predecessor constraints')
            check(report['native_process_stop']['termination_observed'] is True, 'Actual host observed native process stopped')
            row.update(process_id=payload['process_id'],os_version=payload.get('os_version'),checks=payload['checks'])
            if prior:
                bad=copy.deepcopy(payload);bad['previous_native_process_id']+=1
                reject('wrong recovery predecessor PID',lambda:v.payload_errors(bad,report,prior))
            bad=copy.deepcopy(payload);bad['completed']=False
            reject('incomplete harness result',lambda:v.payload_errors(bad,report,prior))
            if 'observer_directory' in cell:
                row['observer']=review_observer(cell,report,payload,log)
        for name, metadata in report.get('generations',{}).items():
            if metadata['size']:
                check(len(read(folder/name)) == metadata['size'] and sha(read(folder/name)) == metadata['sha256'], 'Actual generation metadata')
            else:
                check(not (folder/name).exists() and metadata['sha256'] is None,'Captured absent generation remains absent')
        if 'study_artifacts' in report:
            structure=v.inspect_study_artifacts(folder,report,report['study_artifacts'])
            check(structure==report['study_structure'],'Actual synthetic study structure independently decoded')
            row['study_structure']=structure
    else:
        payload=doc(folder/'result.json')
        check(cell['status']=='passed' and report['passed'] is True and report['exit_code']==0,'Actual normal baseline completion status')
        check(not n.native_log_errors(log),'Actual baseline native framework and driver completion')
        for key,expected in [('verification_id',folder.name),('candidate_fingerprint',candidate_hash),('harness_sha256',report['harness_sha256']['harness.dart']),('device_label',report['label']),('platform',report['platform']),('scenario',scenario),('run_id',report['run_id'])]:
            check(payload[key]==expected,'Baseline payload identity',field=key)
        check(report['native_process_stop']['exit_code']==0,'Explicit baseline process termination command succeeded')
        row.update(process_id=payload.get('process_id'),os_version=payload.get('os_version'),checks=payload.get('checks'),payload_keys=list(payload))
    if cell['status']=='passed':
        reject('late exception invalidates previous completion',lambda:n.native_log_errors(log+'\nflutter: Unhandled Exception: review-only\n'))
        missing=re.sub(r'(?m)^.*(?:flutter:|I/flutter\s*\(\s*\d+\):).*All tests passed!.*$','',log)
        reject('driver completion alone cannot pass',lambda:n.native_log_errors(missing))
    ROWS.append(row)

def main():
    checkpoint=doc(FIRST)
    check(sha(read(FIRST))=='d7c82bab429c67e26fb2d546ce791b2b70891a54a7e266101cd098d4b6d232f0','Native author sealed first batch pin')
    manifest=doc(CANDIDATE/'manifest.json')
    check(checkpoint['candidate_fingerprint']==manifest['source_fingerprint'],'Sealed batch bound to frozen candidate')
    # Exact source points used by this audit, rather than repeating all1190 export checks.
    production=['game/persistence/lib/tideglass_persistence.dart','game/persistence/lib/src/posix_writer_lock.dart','game/persistence/lib/src/economic_transition.dart','game/mobile/lib/bootstrap.dart','game/mobile/lib/client_economic_transition.dart','game/mobile/lib/offline_replay.dart','game/core/lib/src/engine.dart','game/core/lib/src/daily_engine.dart','game/core/lib/src/support_engine.dart','game/mobile/lib/study_gate.dart','game/platform/lib/study_recorder.dart','game/mobile/lib/study_native_context.dart','game/mobile/lib/ownership_clock.dart','game/mobile/lib/notification_service.dart','game/mobile/lib/reminder_lifecycle.dart','game/mobile/lib/notification_settings.dart','game/mobile/lib/app.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/help_screen.dart','game/mobile/lib/audio_settings.dart','game/mobile/lib/number_format.dart']
    for rel in production:
        check(sha(read(CANDIDATE/'source'/rel))==manifest['source_sha256'][rel]==sha(read(ROOT/rel)), 'Reviewed production source matches frozen candidate and live',path=rel)
    for p in (HERE/'review-tools').glob('*.py'): read(p)
    for p in (HERE/'inputs').iterdir(): read(p)
    for rel in ['release/native-proof/next-candidate-protocol.md','release/native-proof/current-runtime-preparation/PROTOCOL.md','docs/quality/V1_QUALITY_PROTOCOL.md','V1_ROADMAP.md','docs/release-contract.md']: read(ROOT/rel)
    terminal=doc(TERMINAL)
    check(sha(read(TERMINAL))=='e6ed8e685ba0fd9d697261ffa02354def41be377588c03bbe649bfaa39b3a303','Second sealed terminal batch pin')
    for old, new in zip(checkpoint['cells'], terminal['cells']):
        check({k:value for k,value in old.items() if k!='observer_finalization'} == {k:value for k,value in new.items() if k!='errors'}, 'Terminal checkpoint retains original cell identity/status/file pins; redundant embedded observer summary omitted')
        check(new['errors']==[], 'Terminal checkpoint added explicit empty errors to earlier nonfailed cells')
        if 'observer_finalization' in old:
            new['observer_finalization']=old['observer_finalization']
    for cell in terminal['cells']: review_cell(cell,manifest['source_fingerprint'])
    check(dict(Counter(row['status'] for row in ROWS))=={k:v for k,v in terminal['counts'].items() if v},'Independent cell status totals match terminal sealed batch')
    cache_path=ROOT/'release/native-proof/current-runtime-ios-phone-20261023T045232665362Z/verification.json'
    cache=doc(cache_path)
    review_cell({'scenario':cache['scenario'],'run_id':cache['run_id'],'status':cache['status'],'verification':str(cache_path),
                 'verification_sha256':'b26d39d5411d75df070bd2c7ddc6dba74f8c2a771999e794202d534afb10b348',
                 'native_evidence_sha256':cache['evidence_sha256'],'predecessor':None},manifest['source_fingerprint'])
    for path,expected in terminal['failure_inspection'].items():
        check(sha(read(path))==expected,'Separate failed fixture inspection pin')
    for line in checkpoint['operator_links'].splitlines():
        entry=json.loads(line);check(sha(read(entry['operator_evidence']))==entry['sha256'],'Clock/share operator evidence pin')
    pins_after={path:sha(Path(path).read_bytes()) for path in PINS}
    check(pins_after==PINS,'All exact reviewed input bytes unchanged after replay')
    result={'reviewed_utc':datetime.now(timezone.utc).isoformat(),'candidate':str(CANDIDATE),'sealed_checkpoints':[str(FIRST),str(TERMINAL)],'separately_sealed_cache_report':str(cache_path),'checks':len(CHECKS),'negative_controls':len(NEGATIVES),'cells':dict(Counter(row['status'] for row in ROWS)),'pending_at_terminal_checkpoint':terminal['not_executed'],'pending_after_cache_append':['runtime-study-storage-withdraw repair and fresh completion','runtime-study-withdraw-reopen','Android baseline/current/observer','iPad baseline','native reminder permission/scheduling/delivery/revocation'],'input_files':len(PINS),'native_commands_run':False,'flutter_run':False,'release_acceptance':False,'all_checks_passed':all(c['passed'] for c in CHECKS)}
    for name,value in [('checks.json',CHECKS),('negative-controls.json',NEGATIVES),('cell-replay.json',ROWS),('inputs-before.json',PINS),('inputs-after.json',pins_after),('verification.json',result)]:
        (HERE/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    with patch.object(subprocess,'run',blocked),patch.object(subprocess,'Popen',blocked),patch.object(os,'kill',blocked),patch.object(os,'killpg',blocked):
        main()
