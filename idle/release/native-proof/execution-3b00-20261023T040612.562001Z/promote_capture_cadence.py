import datetime,hashlib,json,shutil,subprocess
from execute_cells import ROOT,EVIDENCE

def pin(p): return hashlib.sha256(p.read_bytes()).hexdigest()
review=ROOT/'release/qa/lead-android-cadence-20261023T083724.231954Z/verification.json'
assert pin(review)=='e9150553d240f18efe1ff25df2b0707a85103ffd3cdbb916bcefb33257001187'
v=json.loads(review.read_text());live=ROOT/'game/mobile/integration_test/platform_smoke_test.dart';stage=ROOT/'release/store/android-cadence-repair-20261023T083558.585235Z/proposed/platform_smoke_test.dart'
assert pin(live)==v['source_before'];assert pin(stage)==v['source_after'];assert pin(ROOT/'tool/native_recording.py')=='77ddd47079b1373e8dc4b99b239b03f1ac8cd8200d125b777c4d0adaa3fe5d18'
assert pin(ROOT/'tool/native_integration_driver.dart')=='ec880d16153b1ac577a221a46f81e7c309dd5417fbba8aae4ce68f7acbcfb668'
out=EVIDENCE/('capture-cadence-adoption-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir();shutil.copyfile(live,out/'before.dart');shutil.copyfile(stage,out/'after.dart')
workspace=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/workspace/game/mobile';copy=workspace/'integration_test/capture_cadence_1c8ed846_test.dart';assert not copy.exists();shutil.copyfile(stage,copy)
command=[str(ROOT/'tool/flutter'),'analyze','--no-pub',str(copy.relative_to(workspace))];r=subprocess.run(command,cwd=workspace,capture_output=True,text=True);(out/'analysis.stdout').write_text(r.stdout);(out/'analysis.stderr').write_text(r.stderr)
record={'review':str(review),'review_sha256':pin(review),'source_before':v['source_before'],'source_after':v['source_after'],'analysis':{'command':command,'cwd':str(workspace),'exit_code':r.returncode,'source_copy_sha256':pin(copy),'stdout_sha256':pin(out/'analysis.stdout'),'stderr_sha256':pin(out/'analysis.stderr')},'scope':'Four Android capture action lower-bounds only; iOS values, stopwatch, actual actions, ACKs, final25 and raw15-30 gates unchanged. Prior failed report retained. Frozen source untouched.','promoted':False}
if r.returncode==0:
 assert pin(live)==v['source_before'];shutil.copyfile(stage,live);assert pin(live)==v['source_after'];record['promoted']=True
(out/'adoption.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'path':str(out/'adoption.json'),'sha256':pin(out/'adoption.json'),'analysis_exit':r.returncode,'promoted':record['promoted']}),flush=True);print(r.stdout+r.stderr,flush=True);assert r.returncode==0
