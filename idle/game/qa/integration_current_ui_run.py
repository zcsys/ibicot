"""Independent bounded host replay in the explicitly assigned Flutter lane."""
import datetime,hashlib,json,pathlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
EV=ROOT/'release/qa'/('integration-current-ui-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));EV.mkdir()
ref=ROOT/'release/qa/client-localization-complete-20261021T132000553359Z/source-before.json'
paths=set(json.loads(ref.read_text()))
paths.update(['game/mobile/lib/public_links.dart','game/mobile/lib/public_links_model.dart','game/mobile/test/public_links_test.dart','game/mobile/test/help_test.dart','game/qa/integration_localization_navigation_test.dart','game/qa/integration_current_ui_run.py'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={name:sha(ROOT/name) for name in sorted(paths)}
for name in before:
 d=EV/'source'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,d)
(EV/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
print(EV,flush=True)
rows=[]
for pseudo in [False,True]:
 for label,tests in [('public-help',['test/public_links_test.dart','test/help_test.dart']),('critical-phone200',['test/localization_test.dart']),('navigation',['../qa/integration_localization_navigation_test.dart'])]:
  cmd=[str(ROOT/'tool/flutter'),'test',*tests,'--reporter=expanded','--timeout=120s',f'--dart-define=TIDEGLASS_PSEUDO={str(pseudo).lower()}']
  if label=='critical-phone200':cmd+=['--dart-define=TIDEGLASS_TEST_VIEWPORT=phone','--dart-define=TIDEGLASS_TEST_TEXT_PERCENT=200']
  name=f'{label}-{str(pseudo).lower()}';log=EV/(name+'.log');start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with log.open('w') as out:code=subprocess.run(cmd,cwd=ROOT/'game/mobile',stdout=out,stderr=subprocess.STDOUT,timeout=300).returncode
  changed=[n for n,h in before.items() if sha(ROOT/n)!=h]
  rows.append({'name':name,'command':cmd,'started_utc':start,'exit_code':code,'source_differences':changed,'log_sha256':sha(log)})
  (EV/'verification.json').write_text(json.dumps({'source_before':before,'runs':rows,'scope':'Independent bounded host check; no analyzer/native/device/release acceptance'},indent=2)+'\n')
  print(name,code,'drift',len(changed),flush=True)
  if changed:raise SystemExit('source changed')
if any(r['exit_code'] for r in rows):raise SystemExit(1)
