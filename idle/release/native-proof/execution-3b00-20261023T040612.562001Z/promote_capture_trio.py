import datetime,hashlib,json,pathlib,shutil,subprocess
from execute_cells import ROOT,EVIDENCE
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
stage=ROOT/'release/store/android-capture-repair-season-20261023T054210.236050Z'
review=ROOT/'release/qa/lead-capture-repair-20261023T053647.917618Z/verification.json'
assert pin(review)=='1e37fbdb65c30ff7f699348d8527fe13e42bc06e20c232578607ac48de8f47da'
metadata=json.loads((stage/'verification.json').read_text())
rows=metadata['staged_sources'];assert len(rows)==3
for relative,row in rows.items():
 assert pin(ROOT/relative)==row['expected_live_before_sha256']
 assert pin(ROOT/row['staged_path'])==row['staged_sha256']
out=EVIDENCE/('capture-trio-adoption-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir()
for relative,row in rows.items():
 before=out/'before'/relative;before.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,before)
 after=out/'after'/relative;after.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/row['staged_path'],after)
for relative,row in rows.items():
 shutil.copyfile(ROOT/row['staged_path'],ROOT/relative);assert pin(ROOT/relative)==row['staged_sha256']
record={'review':str(review),'review_sha256':pin(review),'staged_verification_sha256':pin(stage/'verification.json'),'sources':rows,'scope':'Approved capture-only harness/driver/recorder correction; no production or frozen source writes','promoted':True}
(out/'adoption.json').write_text(json.dumps(record,indent=2)+'\n')
workspace=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/workspace/game/mobile'
checks={'integration_test/capture_stage_1925106cb014_test.dart':'game/mobile/integration_test/platform_smoke_test.dart','test_driver/capture_stage_5fa7f526f10a.dart':'tool/native_integration_driver.dart'}
for target,source in checks.items():
 destination=workspace/target;destination.parent.mkdir(parents=True,exist_ok=True);assert not destination.exists();shutil.copyfile(ROOT/source,destination)
command=[str(ROOT/'tool/flutter'),'analyze','--no-pub',*checks]
result=subprocess.run(command,cwd=workspace,capture_output=True,text=True)
record['scoped_analysis_test_copies_sha256']={target:pin(workspace/target) for target in checks}
(out/'scoped-analysis.stdout').write_text(result.stdout);(out/'scoped-analysis.stderr').write_text(result.stderr)
record['scoped_analysis']={'command':command,'exit_code':result.returncode,'stdout_sha256':pin(out/'scoped-analysis.stdout'),'stderr_sha256':pin(out/'scoped-analysis.stderr')}
record['post_analysis_sha256']={rel:pin(ROOT/rel) for rel in rows}
assert all(record['post_analysis_sha256'][rel]==row['staged_sha256'] for rel,row in rows.items())
(out/'verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'adoption':str(out/'adoption.json'),'adoption_sha256':pin(out/'adoption.json'),'verification':str(out/'verification.json'),'verification_sha256':pin(out/'verification.json'),'analysis_exit':result.returncode}),flush=True)
print(result.stdout+result.stderr,flush=True)
assert result.returncode==0
