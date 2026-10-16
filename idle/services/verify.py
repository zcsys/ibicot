"""Record reproducible author checks without claiming production acceptance."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
commands=[([sys.executable,'-m','unittest','discover','-s','tests/services','-v'],ROOT),
          ([str(ROOT/'tool/dart'),'test'],ROOT/'game/platform'),
          ([str(ROOT/'tool/dart'),'analyze'],ROOT/'game/platform')]
records=[]
for command,cwd in commands:
    result=subprocess.run(command,cwd=cwd,text=True,capture_output=True)
    records.append({'command':command,'cwd':str(cwd.relative_to(ROOT)), 'exit_code':result.returncode,'output':result.stdout+result.stderr})
paths=[]
for folder in ('services/tideglass_service','game/platform/lib','game/platform/test','tests/services'):
    paths += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
paths += [ROOT/'game/platform/pubspec.yaml',ROOT/'game/platform/pubspec.lock',ROOT/'implementation/contracts/save-envelope.schema.json',ROOT/'implementation/tools/validate_save_contract.py']
report={'recorded_at_utc':datetime.now(timezone.utc).isoformat(), 'kind':'author_local_verification',
        'production_packages_accepted':False,'external_provider_transactions_exercised':False,
        'independent_review':'pending','checks':records,
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
out=ROOT/'services/evidence/author-verification.json';out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(out),'checks':[{'command':r['command'],'exit_code':r['exit_code']} for r in records]},indent=2))
raise SystemExit(any(r['exit_code'] for r in records))
