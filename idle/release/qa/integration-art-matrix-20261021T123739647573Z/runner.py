"""QA-only pinned representative host art reproduction, never a full-run claim."""
import datetime, hashlib, json, pathlib, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
ev=ROOT/'release/qa'/f'integration-art-matrix-{stamp}';ev.mkdir(parents=True)
seed=ROOT/'release/native-proof/root-art-pseudo-full-20261021T122636.246158Z/source-before.json'
paths=sorted(json.loads(seed.read_text()))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
before={p:sha(ROOT/p) for p in paths}
for p in paths:
 dest=ev/'source'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dest)
(ev/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
shutil.copy2(__file__,ev/'runner.py')
(ROOT/'game/qa/current_art_matrix_review.json').write_text(json.dumps({'evidence':str(ev)},indent=2)+'\n')
results=[]
print(ev,flush=True)
for locale in ['en-US','qps-ploc']:
 proof=ev/locale;proof.mkdir();report=proof/'report';report.mkdir()
 command=[str(ROOT/'tool/flutter'),'test','test/art_catalogue_variants_test.dart','--plain-name','phone-100-normal','--reporter=expanded','--timeout=12m',f'--dart-define=TIDEGLASS_ART_REPORT_DIR={report}']
 if locale=='qps-ploc':command.append('--dart-define=TIDEGLASS_PSEUDO=true')
 log=proof/'art.log';print('START',locale,flush=True)
 with log.open('w') as f:process=subprocess.run(command,cwd=ROOT/'game/mobile',stdout=f,stderr=subprocess.STDOUT)
 after={p:sha(ROOT/p) for p in paths}
 item={'name':'art','command':command,'exit_code':process.returncode,'log_sha256':sha(log)}
 verification={'scope':'Independent four phone groups only; not full matrix/native/asset acceptance','source_differences':[p for p in paths if before[p]!=after[p]],'results':[item],'art_report_sha256':sha(report/'matrix-results.json') if (report/'matrix-results.json').exists() else None}
 (proof/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
 (proof/'source-before.json').write_text(json.dumps(before,indent=2)+'\n');(proof/'source').symlink_to(ev/'source',target_is_directory=True)
 (proof/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
 results.append({'locale':locale,**verification});print('END',locale,process.returncode,flush=True)
 if process.returncode or verification['source_differences']:break
(ev/'representative-results.json').write_text(json.dumps(results,indent=2)+'\n')
sys.exit(int(any(r['source_differences'] or any(x['exit_code'] for x in r['results']) for r in results)))
