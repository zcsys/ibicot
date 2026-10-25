#!/usr/bin/env python3
"""Compare baseline JSON/event/arithmetic bytes across the exact pre/post patch sources."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,urllib.parse
root=Path(__file__).resolve().parents[2]
folder=Path(__file__).resolve().parent
before=folder/'before/game/core'
# The four unchanged source files are shared with the original observed hashes.
for p in (root/'game/core/lib').rglob('*.dart'):
    rel=p.relative_to(root/'game/core')
    dest=before/rel
    if not dest.exists():
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(p.read_bytes())
config_path=root/'game/core/.dart_tool/package_config.json'
config=json.loads(config_path.read_text())
for package in config['packages']:
    package['rootUri']=urllib.parse.urljoin(config_path.as_uri(),package['rootUri'])
outputs={}
for label,core in [('before',before),('after',root/'game/core')]:
    selected=json.loads(json.dumps(config))
    for package in selected['packages']:
        if package['name']=='tideglass_core':package['rootUri']=core.as_uri()+'/'
    with tempfile.TemporaryDirectory(prefix='tideglass-baseline-') as temp:
        path=Path(temp)/'packages.json';path.write_text(json.dumps(selected))
        run=subprocess.run([str(root/'tool/dart'),'run',f'--packages={path}',str(folder/'verify_baseline.dart')],capture_output=True,text=True,check=True)
    outputs[label]=run.stdout
    (folder/f'baseline-{label}.json').write_text(run.stdout)
report={'byte_equal':outputs['before']==outputs['after'],
        'cases':len(json.loads(outputs['after'])),
        'before_sha256':hashlib.sha256(outputs['before'].encode()).hexdigest(),
        'after_sha256':hashlib.sha256(outputs['after'].encode()).hexdigest(),
        'before_sources':{str(p.relative_to(before)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(before.rglob('*.dart'))},
        'after_sources':{str(p.relative_to(root/'game/core')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'game/core/lib').rglob('*.dart'))},
        'limits':'Eleven fixed production baseline traces, including exact serialized state/events/rates/prices. Not an exhaustive economic equivalence proof or native performance qualification.'}
(folder/'BASELINE_PARITY.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['byte_equal','cases','before_sha256','after_sha256']}))
raise SystemExit(0 if report['byte_equal'] else 1)
