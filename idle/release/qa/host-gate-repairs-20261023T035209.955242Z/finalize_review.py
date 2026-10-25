from pathlib import Path
import hashlib,json,re,shutil
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((O/'inputs-before.json').read_text());after={p:sha(R/p) for p in before};assert before==after
(O/'inputs-after.json').write_text(json.dumps(after,indent=2)+'\n')
for p in before:
 out=O/'source'/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,out)
C=R/'.tooling/build-candidates/20261023T032609.052120Z-a052a4405347/source'
a=(C/'game/simulation/lib/supplemental_run.dart').read_text();b=(R/'game/simulation/lib/supplemental_run.dart').read_text();noncomment=lambda s:[l for l in s.splitlines() if not l.strip().startswith('//')];assert noncomment(a)==noncomment(b)
old=(C/'game/mobile/test/qa_integration_simulation_test.dart').read_text();new=(R/'game/mobile/test/qa_integration_simulation_test.dart').read_text()
pattern=re.compile(r"//[^\n]*|/\*.*?\*/|'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|\s+|.",re.S)
def tokens(s):return [m.group() for m in pattern.finditer(s) if not (m.group().isspace() or m.group().startswith('//') or m.group().startswith('/*'))]
def blocks(s):
 found=list(re.finditer(r"test\(\s*'([^']+)'",s));return [(m.group(1),s[m.start():found[i+1].start() if i+1<len(found) else len(s)]) for i,m in enumerate(found)]
x=blocks(old);y=blocks(new);assert len(x)==len(y)==6
def without_trailing_commas(t):return [v for i,v in enumerate(t) if not(v==',' and i+1<len(t) and t[i+1]==')')]
for i in [0,1,2,4,5]:assert without_trailing_commas(tokens(x[i][1]))==without_trailing_commas(tokens(y[i][1])),i
assert 'greaterThanOrEqualTo(BigInt.from(12))' in y[3][1]
assert "contains('chapter.03')" in y[3][1]
assert 'focusBefore - 3' in y[3][1]
assert 'BigInt.from(1800000000)' in y[3][1]
assert 'game.story.campaign.toJson(), campaignBefore' in y[3][1]
assert 'game.state.surveyNotes, notesBefore' in y[3][1]
original_report=R/'release/native-proof/20261023T032749.977866Z/build-report.json';original=json.loads(original_report.read_text());assert original['host_test_gate']=='failed' and original['results']=={}
assert set(original['failed_host_checks'])=={'mobile-test','operations-test'}
manifest=json.loads((C.parent/'manifest.json').read_text());assert all(sha(C/p)==h for p,h in manifest['source_sha256'].items())
flutter=json.loads((O/'flutter-results.json').read_text());assert all(x['exit_code']==0 for x in flutter)
for name,n in [('focused-35',35),('actual-operations-59',59)]:
 log=(O/(name+'.log')).read_text();assert f'Ran {n} tests' in log and log.rstrip().endswith('OK')
assert '+6: All tests passed!' in (O/'calibration-six.log').read_text()
env=json.loads((O/'actual-lock-19.log').read_text());assert len(env['pins'])==19 and not env['mismatches']
negative=json.loads((O/'independent-environment-probes.json').read_text());assert len(negative)==3 and all(x['passed'] for x in negative)
review={'reviewer':'/root/qa_release','authors':{'calibration':'/root','service_host_gate':'/root/native_verifier'},'source_pins':before,'source_unchanged':True,'locks_unchanged':True,'calibration_tests':6,'calibration_analysis_clean':True,'five_unrelated_regression_token_streams_identical_ignoring_formatter_trailing_commas':True,'supplemental_non_comment_lines_identical':True,'focused_runner_tests':35,'actual_operations_tests':59,'actual_package_versions':19,'independent_actual_checker_negative_cases':negative,'exploratory_expectation_failure':'Identical duplicate exact pin accepted by preexisting checker. This is not a version mismatch and no original requirement forbids identical duplication. Preserved initial probe/log; no production change requested. Malformed pin tested separately.','failed_a052_still_failed':True,'a052_frozen_inputs_unchanged':len(manifest['source_sha256']),'native_or_device_executions':0,'approve_bounded_repairs':True,'release_ready':False,'original_failed_report_sha256':sha(original_report),'files_sha256':{str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file() and p.name!='verification.json'}}
(O/'verification.json').write_text(json.dumps(review,indent=2)+'\n');print('verification_sha256',sha(O/'verification.json'))
