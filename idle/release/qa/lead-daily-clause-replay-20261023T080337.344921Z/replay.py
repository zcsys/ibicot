#!/usr/bin/env python3
"""Read-only evidence replay for the original platform reviewer clauses.

No Dart/Flutter/native runtime is invoked. Arithmetic below is an independent
reference calculation compared with already executed, hash-pinned evidence.
"""
import difflib
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.kill', 'os.posix_spawn'}:
        raise PermissionError('This reviewer cannot execute or signal processes')
    if event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
        if writing and (not isinstance(path, (str, bytes, os.PathLike)) or
                        not Path(path).resolve().is_relative_to(OUT)):
            raise PermissionError('Review output must stay inside the review folder')


sys.addaudithook(audit)
pins = {}
checks = []


def data(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    key = str(path.relative_to(ROOT))
    if key in pins and pins[key] != digest:
        raise RuntimeError('Input changed within review: ' + key)
    pins[key] = digest
    return raw


def doc(path):
    return json.loads(data(path))


def check(label, condition, details=None):
    checks.append({'id': len(checks) + 1, 'check': label, 'passed': bool(condition),
                   **({'details': details} if details is not None else {})})


def digest(path, expected, label=None):
    actual = hashlib.sha256(data(path)).hexdigest()
    check(label or ('SHA-256 ' + str(path)), actual == expected)
    return actual


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def seal_outputs(directory):
    seal = doc(directory / 'seal.json')
    for rel, expected in seal['output_sha256'].items():
        digest(directory / rel, expected)
    return len(seal['output_sha256'])


candidate = ROOT / '.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
fingerprint = '3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59'
digest(candidate / 'manifest.json', 'b4322606cd0207425b801feacc0bf4084ac9c460b23a028576204b766eeaeada')
manifest = doc(candidate / 'manifest.json')
check('Frozen candidate identity', manifest['source_fingerprint'] == fingerprint)

current_qa = ROOT / 'release/qa/current-native-20261023T044903.849353Z'
prior_pins = doc(current_qa / 'clause-inputs-before.json')
check('All 76 current clause bridge inputs are enumerated', len(prior_pins) == 76)
harness = ROOT / 'game/mobile/integration_test/current_runtime_test.dart'
promotion = doc('release/native-proof/execution-3b00-20261023T040612.562001Z/withdraw-barrier-promotion-20261023T075803.523183Z/promotion.json')
digest(promotion['review'], '1bb1e8dcde71b1cee55651405d59b61534909d6ca4e2c12cb0040698f36465c1')
promotion_review = doc(promotion['review'])
data('release/qa/lead-withdraw-barrier-20261023T045309.713695Z/REVIEW.md')
check('Unrelated current-runtime harness delta was independently reviewed and promoted',
      promotion['promotion_completed'] and promotion_review['single_insertion_only'] and
      promotion['before_sha256'] == '102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5' and
      promotion['after_sha256'] == '997e7510aaef0dcebfa6505fc0dcde7d136a25e8a76abea78ede8602b0a4fef9')
for path, expected in prior_pins.items():
    if Path(path) == harness:
        check('Old clause bridge still records original frozen harness', expected == promotion['before_sha256'])
        digest(path, promotion['after_sha256'], 'Declared current harness delta matches reviewed promoted bytes')
    else:
        digest(path, expected)
old_harness = data(candidate / 'source/game/mobile/integration_test/current_runtime_test.dart').decode()
new_harness = data(harness).decode()
delta_ops = [op for op in difflib.SequenceMatcher(None, old_harness.splitlines(), new_harness.splitlines()).get_opcodes() if op[0] != 'equal']
check('Reviewer independently confirms sole 28-line harness insertion',
      len(delta_ops) == 1 and delta_ops[0][0] == 'insert' and delta_ops[0][4] - delta_ops[0][3] == 28)
for rel, expected in promotion_review['production_implementation_pins'].items():
    digest(rel, expected)
    check('Unrelated recorder production remains frozen ' + rel, manifest['source_sha256'][rel] == expected)
for finalized in promotion['finalized_original_observations']:
    digest(finalized['path'], finalized['sha256'])
qa_sealed_outputs = seal_outputs(current_qa)
check('Current QA clause bridge reports no input drift',
      doc(current_qa / 'clause-inputs-after.json') == prior_pins)

bridge = doc('release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json')
for rel, expected in bridge['core_inputs'].items():
    digest(rel, expected)
    digest(candidate / 'source' / rel, expected)
    check('Candidate manifest binds core ' + rel, manifest['source_sha256'][rel] == expected)
for proof in bridge['numeric_evidence'].values():
    digest(proof['path'], proof['sha256'])

selected = [
    'game/core/test/economy_test.dart', 'game/core/test/daily_test.dart',
    'game/core/test/support_test.dart', 'game/core/test/contract_bridge_test.dart',
    'game/core/test/receipt_sequence_test.dart', 'game/core/test/persistence_integration_test.dart',
    'game/mobile/lib/game_controller.dart', 'game/mobile/test/qa_integration_session_test.dart',
    'game/mobile/test/daily_flow_test.dart', 'docs/decisions/numbers-and-event-order.md',
]
for rel in selected:
    actual = hashlib.sha256(data(rel)).hexdigest()
    check('Current source equals candidate ' + rel, actual == manifest['source_sha256'][rel])
    digest(candidate / 'source' / rel, actual)

hostdir = ROOT / 'release/native-proof/20261023T040548.338966Z'
host = doc(hostdir / 'build-report.json')
check('Host report binds frozen unchanged candidate',
      host['candidate_fingerprint'] == fingerprint and host['source_snapshot_unchanged'] and host['host_test_gate'])
host_counts = {'core': 206, 'persistence': 28, 'mobile': 640}
for suite, count in host_counts.items():
    run = host['host_checks'][suite + '-test']
    log = data(hostdir / (suite + '-test.log')).decode()
    check(suite + ' unfiltered test command exited zero',
          run['exit_code'] == 0 and run['command'][1:] == ['test'])
    check(suite + ' complete successful terminal count',
          re.search(r'\+' + str(count) + r': All tests passed!', log) is not None)

midnight = ROOT / 'release/qa/midnight-rechart-20261023T050752.410870Z'
midnight_sealed_outputs = seal_outputs(midnight)
midnight_verification = doc(midnight / 'verification.json')
check('Four separate current-core collision cases actually executed',
      midnight_verification['named_tests'] == 4 and midnight_verification['test_exit_code'] == 0
      and midnight_verification['skipped'] == 0 and midnight_verification['errors'] == 0)
digest('game/core/test/qa_midnight_rechart_test.dart', midnight_verification['final_test_sha256'])
for rel in midnight_verification['frozen_candidate_core_bridge']:
    digest(midnight / 'source' / rel, manifest['source_sha256'][rel])
    digest(rel, manifest['source_sha256'][rel])
records = doc(midnight / 'records.json')
check('Collision case coverage is exactly offsets 0/180 times online/offline',
      {(r['offset_minutes'], r['offline']) for r in records} == {(0, False), (0, True), (180, False), (180, True)}
      and len(records) == 4)
event_order = ['focus_expired', 'support_expired', 'focus_generated', 'survey_completed', 'account_day_advanced', 'rechart']
with localcontext() as ctx:
    ctx.prec = 100
    raw_r = Decimal(35) * (Decimal(1) + Decimal(10).sqrt()) * Decimal('1.45') * 1000000
    exact_floor = int(raw_r)
check('Independent collision Radiance floor', exact_floor == 211235591)
for row in records:
    label = str((row['offset_minutes'], row['offline']))
    check('Collision full ordered events ' + label, [e['kind'] for e in row['events']] == event_order)
    check('Collision simultaneous exact elapsed and account day ' + label,
          all(e['elapsed_micros'] == '600000000' for e in row['events']) and
          row['events'][4]['details'] == {'account_day': 20743, 'materialized_online': not row['offline']})
    check('Collision independent arithmetic and award ' + label,
          int(row['earned_before_reset_micros']) == exact_floor and row['events'][5]['details']['awarded_charts'] == '5'
          and (row['charts'], row['notes'], row['pass_xp']) == ('105', '10', '250'))
    check('Collision return/online snapshot and exactly-once evidence ' + label,
          row['new_contract_snapshot'] == ('return_after_reset' if row['offline'] else 'midnight_before_reset')
          and row['whole_split_equal'] and row['receipt_replay_rejected'])

historical = ROOT / 'release/qa/integration-final-20261016T105843545492Z'
old_index = doc(historical / 'evidence-index.json')
for rel in ['snapshot.json', 'independent-boundaries.json', 'INTEGRATION_REVIEW.md']:
    digest(historical / rel, old_index['files'][rel])
old_snapshot = doc(historical / 'snapshot.json')
old_workspace = Path(old_snapshot['workspace'])
for rel in ['game/core/lib/src/daily.dart', 'game/core/lib/src/daily_engine.dart']:
    digest(old_workspace / rel, old_snapshot['files'][rel])
old_daily = data(old_workspace / 'game/core/lib/src/daily.dart')
current_daily = data('game/core/lib/src/daily.dart')
check('Historical daily ledger bytes are unchanged', old_daily == current_daily)
old_engine = data(old_workspace / 'game/core/lib/src/daily_engine.dart').decode()
current_engine = data('game/core/lib/src/daily_engine.dart').decode()
guard = '    _requireRules(state);\n'
check('Historical daily rules differ only by eight fail-closed rules guards',
      current_engine.count(guard) == 8 and current_engine.replace(guard, '') == old_engine)
(OUT / 'daily-history-bridge.patch').write_text(''.join(difflib.unified_diff(
    old_engine.splitlines(keepends=True), current_engine.splitlines(keepends=True),
    fromfile='historical/daily_engine.dart', tofile='current/daily_engine.dart')))
observed = doc(historical / 'independent-boundaries.json')
expected_daily_micro_r = (86400 + 12 * 600 * 20 // 100 + 6 * 1200 * 25 // 100) * 1000000
check('Independent Focus/Support day arithmetic matches executed parity observation',
      int(observed['route_parity_24h_lifetime_micros']) == expected_daily_micro_r == 89640000000)
check('Accelerated contract claim ledger arithmetic matches observed 60 claims',
      observed['free_pass']['contracts_claimed'] == 20 * 3 and observed['free_pass']['xp'] == str(20 * 3 * 250))

# Independent rational offline envelope: no game library is imported.
offline = {str(h): min(h, 24) * 3600 + max(0, min(h, 72) - 24) * 3600 // 4
           for h in [2, 8, 24, 48, 72, 168]}
check('Independent 24/72-hour envelope table', list(offline.values()) == [7200, 28800, 86400, 108000, 129600, 129600])
check('Quarter-rate tail expires Focus in real time', (600 * 120 + 3000 * 100) // 400 == 930)
check('Additive Focus/Support does not compound', 600 * 145 // 100 + 600 * 125 // 100 + 1 == 1621)
check('Backlog bounded at seven account days times three slots', len(range(20743 - 6, 20743 + 1)) * 3 == 21)

adoption_path = 'release/qa/lead-persistence-fixtures-adoption-20261023T055444.443133Z/adoption.json'
digest(adoption_path, 'bc17ff116f3bb3138918e269bec4ff50430789e5fdfc45e8792a9e0f5cc61450')
adoption = doc(adoption_path)
digest(OUT / 'inputs/program.json', adoption['program_after_sha256'])
digest(OUT / 'inputs/scope_requirements.json', adoption['scope_after_sha256'])
program = doc(OUT / 'inputs/program.json')
backlog = doc(OUT / 'inputs/v1_backlog.json')
roles = doc(OUT / 'inputs/roles.json')
live = doc('implementation/program.json')
items = {i['id']: i for i in program['items']}
originals = {i['id']: i for i in backlog['items']}
check('All 65 original package acceptance clauses and prerequisites preserved',
      len(originals) == 65 and all(items[k]['source_acceptance'] == v['acceptance'] and
      items[k]['source_acceptance_dependencies'] == v['dependencies'] for k, v in originals.items()))
check('Intake metadata still equals live metadata', live == program)
check('Saved gameplay role requires platform reviewer', next(r for r in roles['roles'] if r['id'] == 'gameplay')['reviewer'] == 'platform')
for package in ['M3-01', 'M3-02']:
    check(package + ' owner/reviewer preserved', items[package]['owner'] == 'gameplay' and items[package]['reviewer'] == 'platform')
check('M3-01 exact accepted prerequisites', items['M3-01']['source_acceptance_dependencies'] == ['M2-01', 'M1-03'] and
      all(items[k]['status'] == 'accepted' for k in items['M3-01']['source_acceptance_dependencies']))
check('M3-02 exact prerequisites require M3-01 adoption first',
      items['M3-02']['source_acceptance_dependencies'] == ['M3-01', 'M1-06'] and items['M1-06']['status'] == 'accepted')
digest('release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-m1-03-20261023T054217.678143Z/checkpoint.json',
       'eb1f40c77da66ce4c1910c0c76a1085c1abb05f029e68eba005cd44593270256')
for rel in [
    'release/qa/gameplay-m1-03-android-20261023T054815140862Z/REVIEW.md',
    'release/qa/gameplay-m1-03-android-20261023T054815140862Z/verification.json',
    'release/qa/gameplay-m1-03-android-20261023T054815140862Z/seal.json',
    'release/qa/lead-daily-scope-acceptance-20261023T050809.251467Z/DECISIONS.md',
    'release/qa/client-daily-scope-adoption-20261023T051037.123712Z/REVIEW.md',
    'TIDEGLASS_DESIGN.md', 'V1_ROADMAP.md', 'economy.json',
]:
    data(rel)

# Verify that falsified evidence would not satisfy our comparison predicates.
negative = {
    'one_micro_R_inflation_rejected': str(exact_floor + 1) != records[0]['earned_before_reset_micros'],
    'reversed_boundary_order_rejected': list(reversed(event_order)) != [e['kind'] for e in records[0]['events']],
    'flat_full_speed_after_24h_rejected': 72 * 3600 != offline['72'],
    'twenty_four_slot_backlog_rejected': 8 * 3 != 21,
}
for label, passed in negative.items():
    check('Evidence comparison negative control: ' + label, passed)

before = dict(pins)
drift = [rel for rel, sha in before.items() if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != sha]
check('All read inputs remain unchanged at completion', not drift, drift)
write('input-sha256.json', before)
write('checks.json', checks)
write('arithmetic.json', {
    'kind': 'Independent Python/Decimal calculations against pinned existing runtime observations; no new game run',
    'collision_unfloored_micro_R': str(raw_r), 'collision_floor_micro_R': str(exact_floor),
    'offline_hours_to_equivalent_full_rate_seconds': offline,
    'daily_focus_support_micro_R_at_base_one': str(expected_daily_micro_r),
    'twenty_day_contract_claim_count': 60, 'twenty_day_notes': 600, 'twenty_day_pass_xp': 15000,
    'negative_controls': negative,
})
write('source-bridge.json', {
    'candidate_fingerprint': fingerprint,
    'current_QA_clause_inputs_unchanged': len(prior_pins) - 1,
    'current_QA_clause_inputs_declared_test_only_delta': {
        'game/mobile/integration_test/current_runtime_test.dart': {
            'before_sha256': promotion['before_sha256'], 'after_sha256': promotion['after_sha256'],
            'delta': 'Exactly one 28-line serialized queue barrier insertion before unrelated withdrawal guard injection',
            'root_review': promotion['review'],
            'limits': 'No new withdrawal/native acceptance; old frozen harness and failed proof remain preserved',
        }},
    'current_QA_sealed_outputs_verified': qa_sealed_outputs,
    'historical_numeric_core_pins_unchanged': len(bridge['core_inputs']),
    'historical_numeric_evidence_files_verified': len(bridge['numeric_evidence']),
    'selected_current_test_and_controller_files_match_candidate': selected,
    'current_host_successful_terminal_counts': host_counts,
    'collision_sealed_outputs_verified': midnight_sealed_outputs,
    'collision_cases': len(records),
    'collision_test_is_post_candidate': True,
    'historical_daily_ledger_unchanged': True,
    'historical_daily_engine_only_delta': 'Eight inserted _requireRules(state) fail-closed checks; see patch',
    'historical_20_day_observation_is_accelerated': True,
})
verification = {
    'reviewer_agent': '/root/art_audio_native', 'assigned_review_role': 'platform',
    'completed_utc': datetime.now(timezone.utc).isoformat(),
    'checks_passed': sum(c['passed'] for c in checks), 'checks_failed': sum(not c['passed'] for c in checks),
    'unique_input_files_rechecked': len(before), 'input_drift': drift,
    'new_runtime_executions': 0, 'flutter_device_native_commands': 0,
    'production_or_status_edits': False,
    'recommendations': {'M3-01': 'Accept unchanged original criterion; M2-01 and M1-03 accepted',
                        'M3-02': 'Accept unchanged original criterion after M3-01 adoption; M1-06 accepted'},
    'release_acceptance': False,
    'residuals': ['S08 p95 return performance', 'Full M3-10 dependencies and trajectory coverage',
                  'Physical-device qualification', 'Provider/store/cloud gates', 'Human retention and elapsed-season evidence'],
}
write('verification.json', verification)
print(json.dumps(verification, indent=2))
if verification['checks_failed']:
    print(json.dumps([c for c in checks if not c['passed']], indent=2))
    raise SystemExit(1)
