#!/usr/bin/env python3
"""Read-only M1-03 evidence checks; writes only this review directory.
No external modules, subprocesses, native commands, process signals or network.
This revalidates existing execution evidence, not a fresh runtime test suite.
"""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
QA = ROOT / 'release/qa/current-native-20261023T044903.849353Z'
CANDIDATE = ROOT / '.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
CHECKPOINT = ROOT / 'release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-phone-terminal-20261023T044845.379377Z/checkpoint.json'
PINS, CHECKS, ROWS, ENVELOPES = {}, [], [], []

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    path = Path(path)
    raw = path.read_bytes()
    value = digest(raw)
    assert str(path) not in PINS or PINS[str(path)] == value
    PINS[str(path)] = value
    return raw

def doc(path):
    return json.loads(read(path))

def check(value, label):
    CHECKS.append({'check': label, 'passed': bool(value)})
    assert value, label

def entry(value, ident):
    if isinstance(value, dict):
        if value.get('id') == ident:
            return value
        for child in value.values():
            found = entry(child, ident)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = entry(child, ident)
            if found:
                return found

def valid_checksum(container):
    encoded = json.dumps(container['envelope'], sort_keys=True,
                         separators=(',', ':'), ensure_ascii=False,
                         allow_nan=False).encode()
    return digest(encoded) == container['checksum']

# Prior independent QA seal is immutable; no reexecution of its broad suite.
seal = doc(QA/'seal.json')
for name, expected in seal['output_sha256'].items():
    check(digest(read(QA/name)) == expected, 'Prior QA sealed output: '+name)
check(seal['input_drift'] == [] and seal['native_commands_run'] is False,
      'Prior independent QA declared read-only with no input drift')

program_bytes = read(ROOT/'implementation/program.json')
(HERE/'inputs/program.json').write_bytes(program_bytes)
program = json.loads(program_bytes)
backlog_bytes = read(ROOT/'v1_backlog.json')
(HERE/'inputs/v1_backlog.json').write_bytes(backlog_bytes)
backlog = json.loads(backlog_bytes)
original, current = entry(backlog, 'M1-03'), entry(program, 'M1-03')
check(current['source_acceptance'] == original['acceptance'], 'Exact original M1-03 acceptance retained')
check(current['source_acceptance_dependencies'] == original['dependencies'] == ['M1-02'], 'Exact original sole prerequisite retained')
check(current['reviewer'] == 'gameplay' and current['scope_ids'] == ['S12'], 'Original gameplay reviewer and S12 retained')
check(entry(program, 'M1-02')['status'] == 'accepted', 'Original prerequisite M1-02 accepted')
check(current == entry(doc(QA/'inputs/program.json'), 'M1-03'), 'M1-03 unchanged since earlier sealed review despite unrelated metadata updates')

manifest = doc(CANDIDATE/'manifest.json')
check(PINS[str(CANDIDATE/'manifest.json')] == 'b4322606cd0207425b801feacc0bf4084ac9c460b23a028576204b766eeaeada', 'Exact candidate manifest pin')
source_paths = [
 'game/persistence/lib/tideglass_persistence.dart',
 'game/persistence/lib/src/posix_writer_lock.dart',
 'game/persistence/lib/src/economic_transition.dart',
 'game/persistence/test/save_repository_test.dart',
 'game/persistence/test/economic_lock_test.dart',
 'game/persistence/test/transition_repository_test.dart',
 'game/core/test/persistence_integration_test.dart',
 'game/core/test/receipt_sequence_test.dart',
 'game/core/lib/src/state.dart', 'game/core/lib/src/support.dart',
 'game/mobile/lib/bootstrap.dart', 'game/mobile/lib/client_economic_transition.dart',
 'game/mobile/lib/offline_replay.dart',
]
for name in source_paths:
    expected = manifest['source_sha256'][name]
    check(digest(read(CANDIDATE/'source'/name)) == expected == digest(read(ROOT/name)), 'Relevant candidate/current source identical: '+name)

# Pin and retain attribution for components historically authored by this reviewer.
prior = ROOT/'release/qa/integration-transition-repaired-20261021T121351672733Z'
for name in ['TRANSITION_REVIEW.md','verification.json','host-source-before.json','host-source-after.json','evidence-index.json']:
    read(prior/name)
bridge = doc(QA/'clause-source-bridge.json')
check(bridge['host_suite_terminal_counts']['persistence'] == 28, 'Prior QA inspected current host persistence28; not rerun here')
host_log = read(ROOT/'release/native-proof/20261023T040548.338966Z/persistence-test.log').decode()
check('All tests passed!' in host_log and '+28' in host_log, 'Actual current persistence host log terminal28 success')

checkpoint = doc(CHECKPOINT)
check(PINS[str(CHECKPOINT)] == 'e6ed8e685ba0fd9d697261ffa02354def41be377588c03bbe649bfaa39b3a303', 'Exact immutable iPhone terminal checkpoint pin')
selected = [c for c in checkpoint['cells'] if c['scenario'].startswith(('runtime-lock-', 'runtime-save-', 'runtime-transition-'))]
check(len(selected) == 9, 'Narrow nine-cell set: flock plus three kill/recover pairs plus transition/reopen')
reports, results = {}, {}
for cell in selected:
    path = Path(cell['verification']); folder = path.parent
    report = doc(path); scenario = cell['scenario']; reports[scenario] = report
    check(digest(read(path)) == cell['verification_sha256'], 'Sealed native report pin: '+scenario)
    check(report['candidate_fingerprint'] == manifest['source_fingerprint'] == checkpoint['candidate_fingerprint'], 'Candidate identity: '+scenario)
    check(report['platform'] == 'ios' and report['source_snapshot_unchanged'] is True and report['source_changes_during_run'] == [], 'Platform and source stability: '+scenario)
    for name, expected in cell['native_evidence_sha256'].items():
        check(digest(read(folder/name)) == expected == report['evidence_sha256'][name], 'Native archived pin: '+scenario+'/'+name)
    generations = []
    for name, metadata in report['generations'].items():
        if metadata['sha256'] is None:
            continue
        container = doc(folder/name)
        check(valid_checksum(container), 'Independent recursive canonical checksum: '+scenario+'/'+name)
        damaged = copy.deepcopy(container)
        damaged['envelope']['revision'] += 1
        check(not valid_checksum(damaged), 'One-field corruption control rejected: '+scenario+'/'+name)
        envelope = container['envelope']; generations.append(envelope)
        check(envelope['format'] == 'tideglass-save-envelope' and envelope['schema_version'] == 1, 'Versioned envelope: '+scenario+'/'+name)
        ENVELOPES.append({'scenario':scenario,'file':name,'revision':envelope['revision'],'checksum':container['checksum']})
    generations.sort(key=lambda e:e['revision'])
    if len(generations) == 2:
        old, new = generations
        check(new['parent'] == {'save_id':old['save_id'],'branch_id':old['branch_id'],'revision':old['revision']} and new['revision'] == old['revision']+1, 'Exact rolling-generation lineage: '+scenario)
    interrupted = scenario.startswith('runtime-save-hold-')
    check(report['status'] == ('expected-interrupted' if interrupted else 'passed') and report['passed'] == (not interrupted), 'Honest interrupted/pass status: '+scenario)
    if interrupted:
        check(not (folder/'result.json').exists(), 'Interrupted preparation has no manufactured completion: '+scenario)
        kills = [o for o in report['host_observations'] if o.get('action') == 'os.kill']
        check(len(kills) == 1 and kills[0]['signal'] == 'SIGKILL' and kills[0]['pid'] == report['native_process_id'], 'Actual recorded kill bound to native PID: '+scenario)
        prefix = read(folder/'pre-kill.log'); log = read(folder/'run.log')
        check(log.startswith(prefix), 'Postkill log retains exact prekill prefix: '+scenario)
    else:
        result = doc(folder/'result.json'); results[scenario] = result
        check(result['completed'] is True and report['exit_code'] == 0 and report['verification_errors'] == [], 'Native normal completion: '+scenario)
        check(result['process_id'] == report['native_process_id'] and report['native_process_stop']['termination_observed'] is True, 'Native completion PID and stop: '+scenario)
    ROWS.append({'scenario':scenario,'status':report['status'],'verification':str(path),'generations':len(generations)})

for stage in ['beforeWrite','afterFlush','afterRename']:
    hold = reports['runtime-save-hold-'+stage]
    recovery = reports['runtime-save-recover-'+stage]
    result = results['runtime-save-recover-'+stage]
    check(recovery['predecessor']['verification_id'] == hold['verification_id'] and recovery['predecessor']['sha256'] == PINS[recovery['predecessor']['path']], 'Recovery sealed predecessor identity: '+stage)
    check(result['previous_native_process_id'] == hold['native_process_id'] != result['process_id'], 'Recovery occurs in different process: '+stage)
    check(result['save_loaded_amount'] == (1 if stage == 'afterRename' else 0) and result['save_after_recovery_amount'] == 2, 'Old/old/new recovery then one committed2: '+stage)
    check(result['preparation_checkpoint_sha256'] == hold['checkpoint_sha256'] == recovery['checkpoint_sha256'], 'Recovery checkpoint binding: '+stage)
start, reopen = results['runtime-transition-start'], results['runtime-transition-reopen']
check(start['lifetime_micros'] == '90000000' and reopen['lifetime_micros'] == '91000000' and reopen['same_cursor_reopen_checked'] is True, 'Synthetic old60sec=90R then new1sec=1R and no same-cursor duplicate')
check(reopen['previous_native_process_id'] == start['process_id'] != reopen['process_id'], 'Transition reopen is separate native process')

# All source/evidence reads are rehashed at the end. Program is snapshotted;
# unrelated changes after capture are reported separately, not silently adopted.
after = {path:digest(Path(path).read_bytes()) for path in PINS}
drift = {p:{'before':v,'after':after[p]} for p,v in PINS.items() if after[p] != v}
check(not drift, 'All inspected inputs unchanged during this focused replay')
(HERE/'inputs-before.json').write_text(json.dumps(PINS,indent=2)+'\n')
(HERE/'inputs-after.json').write_text(json.dumps(after,indent=2)+'\n')
(HERE/'checks.json').write_text(json.dumps(CHECKS,indent=2)+'\n')
summary = {'candidate':str(CANDIDATE),'checks':len(CHECKS),'unique_input_files':len(PINS),'native_cells':ROWS,'save_envelopes':ENVELOPES,'drift':drift,'host_suites_rerun':False,'native_commands_run':False,'android_evidence_accepted':False,'production_or_status_edits':False,'authorship_limit':'Transition/flock source was historically authored by this gameplay reviewer. Independent prior QA and current sealed native QA are cited, not replaced by self-review.'}
(HERE/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'checks':len(CHECKS),'files':len(PINS),'cells':len(ROWS),'envelopes':len(ENVELOPES),'drift':drift}))
