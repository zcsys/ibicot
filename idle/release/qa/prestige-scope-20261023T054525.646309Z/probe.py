"""Read-only S05 evidence bridge; writes only beside this script, no subprocesses."""
import hashlib
import json
import math
from pathlib import Path

R = Path('/Users/csys/Desktop/ibicot/idle')
O = Path(__file__).resolve().parent
pins = {}
checks = []
def read(path):
    p = R / path
    b = p.read_bytes()
    pins[str(p.relative_to(R))] = hashlib.sha256(b).hexdigest()
    return b
def js(path):
    return json.loads(read(path))
def check(name, value):
    checks.append({'name': name, 'pass': bool(value)})
def digest(path):
    return hashlib.sha256(read(path)).hexdigest()
def save(name, value):
    (O / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

C = '.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
M = js(C + '/manifest.json')
program = js('implementation/program.json')
scope = js('implementation/scope_requirements.json')
items = {x['id']: x for x in program['items']}
reqs = {x['id']: x for x in scope['requirements']}
save('original-clauses.json', {'requirements': [reqs[x] for x in ['S05', 'S40', 'S41']], 'items': [items[x] for x in ['M1-01', 'M1-02', 'M2-02', 'BOOT-CORE', 'M0-01', 'M0-02', 'M0-03', 'M0-04', 'M0-06', 'M0-07', 'M0-08', 'M1-04']]})
for x in reqs['S05']['work_items']:
    check('S05 linked item accepted ' + x, items[x]['status'] == 'accepted')
check('exact S05 criterion', reqs['S05']['requirement'] == 'Lifetime-based 0.65-exponent Rechart, entitlement subtraction, retained-state preview and permanent power')
check('exact S05 verification', reqs['S05']['verification'] == 'Exact award boundary and repeated-reset tests; preview matches retained/reset state.')

N = 'release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json'
n = js(N)
for path, expected in n['core_inputs'].items():
    check('historic exact core ' + path, digest(path) == expected)
    check('candidate exact core ' + path, M['source_sha256'][path] == expected and digest(C + '/source/' + path) == expected)
for entry in n['numeric_evidence'].values():
    check('retained numeric evidence ' + entry['path'], digest(entry['path']) == entry['sha256'])
rows = js(n['numeric_evidence']['current-numeric-62.json']['path'])
power_rows = [x for x in rows if 'prestige' in x]
for i, row in enumerate(power_rows):
    check('independent integer sqrt on recorded power row ' + str(i), int(row['prestige']) == 10**24 + math.isqrt(int(row['charts']) * 10**48 // 10))
save('recorded-power-recheck.json', {'total_recorded_numeric_rows': len(rows), 'power_rows_checked': len(power_rows), 'method': 'Python math.isqrt on archived actual Dart result; no Dart execution', 'charts': sorted(set(int(x['charts']) for x in power_rows))})

sources = [
 'game/core/test/economy_test.dart', 'game/core/test/daily_test.dart', 'game/core/test/support_test.dart',
 'game/mobile/lib/app.dart', 'game/mobile/lib/strings.dart', 'game/mobile/lib/game_controller.dart',
 'game/mobile/lib/rechart_estimate.dart', 'game/mobile/lib/rechart_forecast_task.dart', 'game/mobile/lib/rechart_copy.dart',
 'game/mobile/lib/presentation.dart', 'game/mobile/lib/help_content.dart', 'game/mobile/lib/help_screen.dart',
 'game/mobile/test/client_test.dart', 'game/mobile/test/qa_client_shell_clauses_test.dart',
 'game/mobile/test/qa_rechart_forecast_review_test.dart', 'game/mobile/test/content_presentation_probe.dart',
 'game/mobile/lib/bundled_content.dart', 'game/mobile/lib/bundled_hashes.g.dart', 'game/mobile/lib/content_compatibility.dart',
 'game/mobile/lib/bootstrap.dart', 'game/mobile/lib/native_services.dart', 'game/mobile/lib/client_economic_transition.dart',
 'game/mobile/test/bundled_content_test.dart', 'tool/package_content.py',
 'game/mobile/pubspec.yaml', 'game/mobile/pubspec.lock', 'game/core/pubspec.yaml', 'game/core/pubspec.lock',
 'implementation/fixtures/economy_reference.json', 'TIDEGLASS_DESIGN.md', 'V1_ROADMAP.md', 'v1_backlog.json',
]
for path in sources:
    h = digest(path)
    if path in M['source_sha256']:
        check('selected frozen source ' + path, h == M['source_sha256'][path] and digest(C + '/source/' + path) == h)
    else:
        check('non-build original document separately pinned ' + path, path in ['TIDEGLASS_DESIGN.md', 'V1_ROADMAP.md', 'v1_backlog.json'])

S = 'release/qa/integration-client-clauses-20261021T143635184485Z'
s = js(S + '/verification.json')
runs = js(S + '/final/runs.json')
for row in s['matrix']:
    label = row['condition']
    logpath = S + '/final/' + label + '.jsonl'
    check('shell log pin ' + label, digest(logpath) == row['log_sha256'])
    events = [json.loads(x) for x in read(logpath).decode().splitlines() if x.startswith('{')]
    check('shell actual terminal success ' + label, any(x.get('type') == 'done' and x.get('success') is True for x in events))
    run = next(x for x in runs if x['label'] == label)
    check('shell no source drift ' + label, run['exit_code'] == 0 and run['source_before'] == run['source_after'])
for path in ['game/mobile/lib/strings.dart', 'game/mobile/lib/game_controller.dart', 'game/mobile/test/qa_client_shell_clauses_test.dart']:
    check('shell retained source ' + path, digest(S + '/final/source/' + path) == digest(path))
read(S + '/CLAUSE_RECOMMENDATIONS.md')

Q = 'release/qa/qa-reset-20261023T025256.370588Z'
q = js(Q + '/verification.json')
qbefore = js(Q + '/qualified-source-before.json')
qafter = js(Q + '/qualified-source-after.json')
check('reset independent before/after equality', qbefore == qafter)
for path in ['game/mobile/lib/game_controller.dart', 'game/mobile/lib/strings.dart', 'game/mobile/lib/rechart_estimate.dart', 'game/mobile/lib/rechart_forecast_task.dart', 'game/mobile/lib/rechart_copy.dart', 'game/mobile/test/qa_rechart_forecast_review_test.dart']:
    check('reset exact relevant source ' + path, digest(path) == qbefore[path])
oldapp = read(Q + '/qualified-source/game/mobile/lib/app.dart').decode()
app = read('game/mobile/lib/app.dart').decode()
def reset_section(text):
    return text.split('  Future<void> _confirmRechart(BuildContext context) {', 1)[1].split('  Widget _journal(', 1)[0]
check('actual reset dialog byte-identical through daily icon delta', reset_section(oldapp) == reset_section(app))
read(Q + '/post-review-app-diff.patch')
reset_summary = []
for condition in ['phone-english', 'phone-pseudo', 'tablet-english', 'tablet-pseudo']:
    d = js(Q + '/' + condition + '.json')
    actions = [x for x in d['observations'] if x['type'] == 'actual-actions']
    check('independent actual reset actions ' + condition, len(actions) == 1 and all(actions[0][k] for k in ['opening_unchanged', 'snapshot_stable', 'cancel_keeps_new_income', 'confirm_current_state']))
    check('reset source result pin ' + condition, hashlib.sha256(read(Q + '/' + condition + '.json')).hexdigest() == q['evidence_sha256'][condition + '.json'])
    reset_summary.append({'condition': condition, 'scale': d['scale'], 'actions': actions})
save('dialog-evidence-summary.json', reset_summary)
read(Q + '/RESET_REVIEW.md')

B = 'release/native-proof/20261023T040548.338966Z'
build = js(B + '/build-report.json')
check('current 28 host gates passed', len(build['host_checks']) == 28 and build['host_test_gate'] == 'passed' and not build['failed_host_checks'] and all(x['exit_code'] == 0 for x in build['host_checks'].values()))
for path in ['core-test.log', 'mobile-test.log']:
    text = read(B + '/' + path).decode()
    check('current host terminal ' + path, 'All tests passed!' in text)
for path in ['flutter-version.log', 'candidate-manifest.json']:
    read(B + '/' + path)
release = js('release/native-proof/20261023T041555.017412Z/build-report.json')
check('five reported exports succeeded', len(build['results']) + len(release['results']) == 5 and all(x['build_succeeded'] and x['exit_code'] == 0 for b in [build, release] for x in b['results'].values()))

P = 'release/native-proof/integration-ios-phone-20261023T042048.993537Z'
v = js(P + '/verification.json')
result = js(P + '/result.json')
check('native seeded qualified report', v['passed'] and v['exit_code'] == 0 and not v['verification_errors'] and v['source_snapshot_unchanged'] and v['production_inputs_match_snapshot'])
for path, h in v['evidence_sha256'].items():
    actualpath = path if (R / path).is_file() else P + '/' + path
    check('native actual evidence pin ' + path, digest(actualpath) == h)
state = result['restored_core_state']
check('actual native durable reset result', state['counts'] == [1,0,0,0,0] and state['charts'] == '10' and state['wallet_micros'] == '0' and state['lifetime_micros'] == '1000000000000000')
check('native exact candidate and harness', result['candidate_fingerprint'] == M['source_fingerprint'] and result['harness_sha256'] == M['source_sha256']['game/mobile/integration_test/platform_smoke_test.dart'])
harness = read(C + '/source/game/mobile/integration_test/platform_smoke_test.dart').decode()
liveharness = read('game/mobile/integration_test/platform_smoke_test.dart').decode()
def seeded_body(text):
    return text.split('    final threshold = GameState(', 1)[1].split('\nvoid ', 1)[0]
check('executed seeded reset body unchanged by gallery-only harness repair', seeded_body(harness) == seeded_body(liveharness))
save('native-seeded-summary.json', {'candidate': result['candidate_fingerprint'], 'harness_executed': result['harness_sha256'], 'harness_live': pins['game/mobile/integration_test/platform_smoke_test.dart'], 'checks': result['checks'], 'restored_state': state, 'limits': result['provenance']})

references = [
 'release/qa/current-native-20261023T044903.849353Z/REVIEW.md',
 'release/qa/current-native-20261023T044903.849353Z/verification.json',
 'release/qa/onboarding-clause-20261023T040451.613635Z/M2_02_RECOMMENDATION.md',
 'release/qa/onboarding-clause-20261023T040451.613635Z/verification.json',
 'release/qa/current-exports-20261023T043341.519824Z/EXPORT_REVIEW.md',
 'release/qa/current-exports-20261023T043341.519824Z/verification.json',
 'release/qa/current-exports-20261023T043341.519824Z/source-lock-binding.json',
 'release/qa/gameplay-config-clause-20261021T141342461007Z/M1-04_RECOMMENDATION.md',
 'release/qa/gameplay-config-clause-20261021T141342461007Z/verification.json',
 'docs/decisions/execution-costs.md', 'docs/decisions/engine-and-number-selection.md',
 'docs/decisions/native-toolchain.md', 'docs/decisions/numbers-and-event-order.md',
 'docs/release-contract.md', 'docs/quality/V1_QUALITY_PROTOCOL.md',
 'docs/quality/PLAYER_STUDY_PROTOCOL.md', 'release/device-matrix.json',
 'implementation/reports/director-foundation-review.md',
]
for path in references:
    read(path)
save('source-before.json', pins)
after = {p: hashlib.sha256((R / p).read_bytes()).hexdigest() for p in pins}
save('source-after.json', after)
check('all pinned inputs unchanged', pins == after)
save('verification.json', {'scope': 'S05 exact clause and brief existing-evidence S40/S41 assessment', 'recommendations': {'S05': 'verify', 'S40': 'existing evidence sufficient for exact local scope', 'S41': 'existing evidence sufficient for exact planning scope'}, 'new_runtime_tests': 0, 'flutter_or_device_commands': 0, 'production_or_status_mutations': False, 'source_count': len(pins), 'checks': checks, 'all_passed': all(x['pass'] for x in checks), 'failed_checks': [x['name'] for x in checks if not x['pass']]})
print(json.dumps({'checks': len(checks), 'files': len(pins), 'failures': [x['name'] for x in checks if not x['pass']]}, indent=2))
