import datetime,hashlib,json,shutil,subprocess
from execute_cells import ROOT,EVIDENCE
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=ROOT/'release/qa/lead-android-ack-20261023T081709.354596Z/verification.json'
assert pin(review)=='9c313631bed1ab011e9ccf9ad7fd7f083aeaba468fe5aec8578b3b90a909c3bc'
rows=json.loads(review.read_text())['approved_staged_sources'];assert len(rows)==2
assert pin(ROOT/'tool/native_integration_driver.dart')=='ec880d16153b1ac577a221a46f81e7c309dd5417fbba8aae4ce68f7acbcfb668'
for rel,row in rows.items():
 assert pin(ROOT/rel)==row['expected_live_before_sha256'];assert pin(ROOT/row['staged_path'])==row['staged_sha256']
out=EVIDENCE/('ack-protocol-adoption-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir()
for rel,row in rows.items():
 for kind,source in [('before',ROOT/rel),('after',ROOT/row['staged_path'])]:
  dest=out/kind/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
for rel,row in rows.items():shutil.copyfile(ROOT/row['staged_path'],ROOT/rel)
record={'review':str(review),'review_sha256':pin(review),'sources':rows,'scope':'Exact reviewed Android receipt payload/complete-directory protocol only. Prior hard-link failure preserved. Frozen and production source unchanged.','promotion_completed':True}
(out/'adoption.json').write_text(json.dumps(record,indent=2)+'\n')
workspace=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/workspace/game/mobile'
copy=workspace/'integration_test/capture_ack_a427de5995a6_test.dart';assert not copy.exists();shutil.copyfile(ROOT/'game/mobile/integration_test/platform_smoke_test.dart',copy)
command=[str(ROOT/'tool/flutter'),'analyze','--no-pub',str(copy.relative_to(workspace))]
r=subprocess.run(command,cwd=workspace,capture_output=True,text=True);(out/'analysis.stdout').write_text(r.stdout);(out/'analysis.stderr').write_text(r.stderr)
record['analysis']={'command':command,'cwd':str(workspace),'exit_code':r.returncode,'test_copy_sha256':pin(copy),'stdout_sha256':pin(out/'analysis.stdout'),'stderr_sha256':pin(out/'analysis.stderr')}
record['live_after_sha256']={rel:pin(ROOT/rel) for rel in rows};assert all(record['live_after_sha256'][rel]==row['staged_sha256'] for rel,row in rows.items())
(out/'verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'adoption':str(out/'adoption.json'),'adoption_sha256':pin(out/'adoption.json'),'verification':str(out/'verification.json'),'verification_sha256':pin(out/'verification.json'),'analysis_exit':r.returncode}),flush=True);print(r.stdout+r.stderr,flush=True);assert r.returncode==0
