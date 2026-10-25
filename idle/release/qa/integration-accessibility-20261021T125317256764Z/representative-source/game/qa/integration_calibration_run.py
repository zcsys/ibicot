"""Exclusive-lane representative runner; no whole-suite or analyzer claim."""
import datetime, hashlib, json, pathlib, shutil, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
EV=pathlib.Path(json.loads((ROOT/'game/qa/integration_calibration_current.json').read_text())['evidence'])
reference=ROOT/'release/native-proof/root-calibration-full-20261021T125314.174315Z/source-before.json'
paths=list(json.loads(reference.read_text()))+[
    'game/qa/integration_calibration_navigation_test.dart',
    'game/qa/integration_calibration_run.py',
    'game/qa/integration_calibration_focus_test.dart',
]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={p:h(ROOT/p) for p in paths}
pin=EV/'representative-source';pin.mkdir()
for p in paths:
    out=pin/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
(EV/'representative-source-before.json').write_text(json.dumps(before,indent=2)+'\n')
results=[]
for mode,pseudo in [('en-US',False),('qps-ploc',True)]:
    folder=EV/'representative'/mode;folder.mkdir(parents=True)
    for name,test in [('navigation','../qa/integration_calibration_navigation_test.dart'),
                      ('matrix','test/calibration_accessibility_matrix_test.dart')]:
        cmd=[str(ROOT/'tool/flutter'),'test',test,'--reporter=expanded','--timeout=120s']
        if pseudo:cmd+=['--dart-define=TIDEGLASS_PSEUDO=true']
        if name=='matrix':cmd+=['--name',r'^calibration\.(01|12) exact routes earned practice (en-US|qps-ploc)-phone-200-(normal|reduced)$',f'--dart-define=TIDEGLASS_ACCESSIBILITY_REPORT_DIR={folder}/report']
        start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (folder/(name+'.log')).open('w') as out:
            code=subprocess.run(cmd,cwd=ROOT/'game/mobile',stdout=out,stderr=subprocess.STDOUT,timeout=300).returncode
        print(mode,name,code,flush=True)
        results.append({'locale':mode,'name':name,'command':cmd,'exit_code':code,
                        'started_utc':start,'log_sha256':h(folder/(name+'.log'))})
after={p:h(ROOT/p) for p in paths}
(EV/'representative-source-after.json').write_text(json.dumps(after,indent=2)+'\n')
(EV/'representative-results.json').write_text(json.dumps({'source_differences':[p for p in paths if before[p]!=after[p]],'results':results},indent=2)+'\n')
if any(r['exit_code'] for r in results):raise SystemExit(1)
if before!=after:raise SystemExit('source changed during independent execution')
