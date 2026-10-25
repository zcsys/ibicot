from pathlib import Path
import subprocess,json,hashlib,shutil
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
paths=sorted(set(p for pat in ['game/core/lib/**/*.dart','game/mobile/lib/*.dart','game/mobile/test/qa_rechart_forecast_review_test.dart','game/mobile/test/qa_font_licenses_review_test.dart','game/mobile/test/font_licenses_test.dart','game/mobile/test/content_presentation_probe.dart','game/mobile/pubspec*','game/mobile/assets/licenses/*','source/art/ui/font-manifest.json'] for p in root.glob(pat) if p.is_file()))
def pins():return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=pins();(out/'qualified-source-before.json').write_text(json.dumps(before,indent=2)+'\n');runs=[]
for name,viewport,pseudo in [('font-phone-english-qualified','phone',False),('font-phone-pseudo-qualified','phone',True),('font-tablet-pseudo-qualified','tablet',True)]:
 cmd=[str(root/'tool/flutter'),'test','test/qa_font_licenses_review_test.dart','--dart-define=TIDEGLASS_TEST_VIEWPORT='+viewport,'--dart-define=TIDEGLASS_TEST_TEXT_PERCENT=200','--dart-define=TIDEGLASS_PSEUDO='+str(pseudo).lower(),'--dart-define=QA_FONT_REPORT='+str(out/(name+'.json')),'--reporter','expanded']
 with (out/(name+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=root/'game/mobile',stdout=log,stderr=subprocess.STDOUT)
 runs.append({'name':name,'command':cmd,'exit_code':result.returncode,'runtime_unchanged':pins()==before,'log_sha256':hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest()});(out/'font-final-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
 if result.returncode or pins()!=before:raise SystemExit(1)
cmd=[str(root/'tool/flutter'),'analyze','lib/rechart_copy.dart','lib/rechart_estimate.dart','lib/rechart_forecast_task.dart','lib/font_licenses.dart','lib/main.dart','test/qa_rechart_forecast_review_test.dart','test/qa_font_licenses_review_test.dart','test/font_licenses_test.dart']
with (out/'scoped-analysis.log').open('w') as log:result=subprocess.run(cmd,cwd=root/'game/mobile',stdout=log,stderr=subprocess.STDOUT)
runs.append({'name':'scoped-analysis','command':cmd,'exit_code':result.returncode,'runtime_unchanged':pins()==before});(out/'font-final-runs.json').write_text(json.dumps(runs,indent=2)+'\n');(out/'qualified-source-after.json').write_text(json.dumps(pins(),indent=2)+'\n')
for p in paths:
 q=out/'qualified-source'/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
raise SystemExit(result.returncode)
