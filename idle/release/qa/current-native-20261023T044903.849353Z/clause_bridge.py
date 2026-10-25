from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
CANDIDATE=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
manifest=json.loads((CANDIDATE/'manifest.json').read_text())
pins={};checks=[];harness_deltas={}
def take(path):
    path=Path(path);raw=path.read_bytes();pins[str(path)]=hashlib.sha256(raw).hexdigest();return raw
def check(ok,name):
    checks.append({'check':name,'passed':bool(ok)})
    assert ok,name
paths=['game/core/test/economy_test.dart','game/core/test/daily_test.dart','game/core/test/support_test.dart','game/core/test/receipt_sequence_test.dart','game/core/test/contract_bridge_test.dart','game/core/test/persistence_integration_test.dart','game/persistence/test/save_repository_test.dart','game/persistence/test/economic_lock_test.dart','game/persistence/test/transition_repository_test.dart','game/mobile/test/qa_integration_session_test.dart','game/mobile/test/qa_integration_save_boundaries_test.dart','game/mobile/test/offline_replay_test.dart','game/mobile/test/qa_integration_ownership_clock_test.dart','game/mobile/test/reminder_lifecycle_test.dart','game/mobile/test/qa_integration_reminders_test.dart','game/mobile/test/notification_service_test.dart','game/mobile/test/notification_settings_test.dart','game/mobile/lib/game_controller.dart','game/core/lib/src/daily.dart','game/core/lib/src/daily_engine.dart','game/core/lib/src/engine.dart','game/core/lib/src/state.dart','game/core/lib/src/support_engine.dart','docs/decisions/numbers-and-event-order.md','game/mobile/integration_test/platform_smoke_test.dart','game/mobile/integration_test/current_runtime_test.dart']
for relative in paths:
    raw=take(CANDIDATE/'source'/relative)
    check(hashlib.sha256(raw).hexdigest()==manifest['source_sha256'][relative],relative+' exact candidate source')
    live=take(ROOT/relative)
    if '/integration_test/' in relative:
        harness_deltas[relative]={'candidate':hashlib.sha256(raw).hexdigest(),'live':hashlib.sha256(live).hexdigest(),'equal':raw==live,'scope':'Current report uses archived original harness; later root-owned test-only changes do not rewrite that result.'}
    else:
        check(raw==live,relative+' exact candidate and current source')
proofs=['release/persistence-review.md','release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md','release/qa/integration-transition-repaired-20261021T121351672733Z/verification.json','release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json','release/qa/integration-final-20261016T105843545492Z/INTEGRATION_REVIEW.md','release/qa/integration-reminders-initial-20261016T115431767720Z/REMINDERS_REVIEW.md','release/qa/qa-reset-20261023T025256.370588Z/RESET_REVIEW.md','release/qa/lead-content-matrix-20261021T144134.921859Z/MATRIX_REVIEW.md','release/qa/lead-daily-icons-20261023T031715.308630Z/REVIEW.md','release/qa/lead-withdraw-barrier-20261023T045309.713695Z/REVIEW.md','release/qa/lead-withdraw-barrier-20261023T045309.713695Z/verification.json','release/native-proof/20261023T040548.338966Z/build-report.json','release/qa/current-exports-20261023T043341.519824Z/EXPORT_REVIEW.md']
for relative in proofs:take(ROOT/relative)
old=json.loads((ROOT/'release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json').read_text())
bridge={}
for relative,expected in old['core_inputs'].items():
    actual=hashlib.sha256(take(CANDIDATE/'source'/relative)).hexdigest()
    bridge[relative]={'historical':expected,'current':actual,'equal':actual==expected}
for name,item in old['numeric_evidence'].items():
    check(hashlib.sha256(take(ROOT/item['path'])).hexdigest()==item['sha256'],'Historical independent numeric evidence '+name)
report=json.loads((ROOT/'release/native-proof/20261023T040548.338966Z/build-report.json').read_text())
check(report['candidate_fingerprint']==manifest['source_fingerprint'] and report['source_snapshot_unchanged'] and report['host_test_gate'],'Current host report exact frozen candidate and successful gate')
counts={}
for name in ['core','persistence','mobile']:
    raw=take(ROOT/f'release/native-proof/20261023T040548.338966Z/{name}-test.log').decode()
    found=re.findall(r'\+(\d+): All tests passed!',raw)
    check(bool(found),name+' actual terminal success')
    check(not re.search(r'\+\d+ -\d+:.*All tests passed!',raw),name+' no failed-count terminal')
    counts[name]=int(found[-1]);check(report['host_checks'][name+'-test']['exit_code']==0,name+' recorded exit0')
post={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in pins}
check(post==pins,'Clause source/evidence pins unchanged after reads')
result={'bridge':bridge,'all_eight_equal':all(x['equal'] for x in bridge.values()),'host_suite_terminal_counts':counts,'attribution':'Existing native author fullhost execution inspected here; not rerun by QA','checks':checks,'test_only_harness_deltas':harness_deltas,'prior_attempt':'The first ad-hoc bridge attempted a whole-live-source equality assertion and stopped at the known root-owned platform_smoke capture-harness repair. This script explicitly preserves its original/live hashes; production equality remains required.'}
for name,value in [('clause-inputs-before.json',pins),('clause-inputs-after.json',post),('clause-source-bridge.json',result)]:
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'files':len(pins),'checks':len(checks),'eight_core_inputs_match':result['all_eight_equal'],'host_terminal_counts':counts,'changed_bridge_files':[p for p,x in bridge.items() if not x['equal']],'harness_deltas':harness_deltas},indent=2))
