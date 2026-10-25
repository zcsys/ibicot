import argparse, datetime, hashlib, json, pathlib, shutil, subprocess, sys
ROOT=pathlib.Path('/Users/csys/Desktop/ibicot/idle')
p=argparse.ArgumentParser();p.add_argument('kind',choices=['transition','art-sample','art-full']);a=p.parse_args()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
name='root-'+a.kind+'-'+stamp
proof=ROOT/'release/native-proof'/name;proof.mkdir(parents=True)
art=ROOT/'release/art/catalogue-variants'/name
seed=ROOT/'release/native-proof/root-art-phone-sample-20261021T115102.916252Z/source-before.json'
paths={ROOT/x for x in json.loads(seed.read_text()) if (ROOT/x).is_file()}
for package in (ROOT/'game').iterdir():
    if package.is_dir():
        paths.update((package/'lib').rglob('*.dart'))
        paths.update(x for x in package.glob('pubspec.*') if x.is_file())
paths.update((ROOT/'game/mobile/test').glob('*.dart'))
paths.update((ROOT/'game/core/test/support').rglob('*'))
paths.update((ROOT/'game/core/test/fixtures/economic_transition').rglob('*'))
paths.update([ROOT/'tool/flutter',ROOT/'tool/dart',ROOT/'source/art/verification/check_matrix.py',ROOT/'implementation/art/production_contract.json'])
paths={x for x in paths if x.is_file()}
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
before={str(f.relative_to(ROOT)):sha(f) for f in sorted(paths)}
for f in sorted(paths):
    dest=proof/'source'/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
(proof/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
shutil.copy2(__file__,proof/'runner.py')
commands=[('analyzer',[str(ROOT/'tool/flutter'),'analyze'])]
if a.kind=='transition':
    commands.append(('transition',[str(ROOT/'tool/flutter'),'test','test/bootstrap_economic_transition_test.dart','test/bootstrap_test.dart','test/offline_replay_test.dart','test/qa_integration_replay_test.dart','--reporter=expanded','--timeout=5m']))
else:
    commands.append(('art',[str(ROOT/'tool/flutter'),'test','test/art_catalogue_variants_test.dart',*(['--plain-name','phone-100-normal'] if a.kind=='art-sample' else []),'--reporter=expanded','--timeout=12m',f'--dart-define=TIDEGLASS_ART_REPORT_DIR={art}']))
report={'scope':f'Current-source host {a.kind}; not candidate152/native/human qualification','source_differences':[], 'results':[]}
if a.kind.startswith('art'):report['art_report_directory']=str(art)
print(proof,flush=True)
for label,cmd in commands:
    log=proof/f'{label}.log';print('START',label,flush=True)
    with log.open('w') as out: result=subprocess.run(cmd,cwd=ROOT/'game/mobile',stdout=out,stderr=subprocess.STDOUT)
    report['results'].append({'name':label,'command':cmd,'exit_code':result.returncode,'log_sha256':sha(log)})
    print('END',label,result.returncode,flush=True)
    if result.returncode: print(log.read_text()[-11000:],flush=True)
after={str(f.relative_to(ROOT)):sha(f) for f in sorted(paths) if f.exists()}
report['source_differences']=[x for x in sorted(before) if before[x]!=after.get(x)]
(proof/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
if (art/'matrix-results.json').exists():report['art_report_sha256']=sha(art/'matrix-results.json')
(proof/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
sys.exit(1 if report['source_differences'] or any(r['exit_code'] for r in report['results']) else 0)
