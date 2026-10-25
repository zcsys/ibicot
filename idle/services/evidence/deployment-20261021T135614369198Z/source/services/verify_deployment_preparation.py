#!/usr/bin/env python3
"""Freeze narrow serving/delivery inputs and replay only this new local preparation."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OWNED = [
    'services/tideglass_service/operating_config.py',
    'services/tideglass_service/deployment.py',
    'services/tideglass_service/alert_transport.py',
    'services/tideglass_service/operator_cycle.py',
    'services/rehearse_deployment.py', 'services/verify_deployment_preparation.py',
    'services/requirements-deployment.lock', 'services/docs/DEPLOYMENT_PREPARATION.md',
    'tests/services/operations/test_operating_delivery.py',
]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    python = ROOT/'.tooling/deployment-venv/bin/python'
    if not python.is_file():raise SystemExit('Create the pinned isolated deployment virtual environment first.')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=ROOT/'services/evidence'/('deployment-'+stamp);output.mkdir()
    source=output/'source';source.mkdir()
    paths=set(OWNED)
    for base in ['services/tideglass_service','services/deployment']:
        paths.update(str(path.relative_to(ROOT)) for path in (ROOT/base).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts)
    paths.update(['implementation/tools/validate_save_contract.py','implementation/contracts/save-envelope.schema.json'])
    inventory=[]
    for name in sorted(paths):
        original=ROOT/name;target=source/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(original,target)
        inventory.append({'path':name,'sha256':sha(target),'ownership':'new-preparation' if name in OWNED or name.startswith('services/deployment/') else 'unchanged-runtime-context'})
    source_digest=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    report={'format':'tideglass-serving-preparation-author-v1','source_sha256':source_digest,
            'source_files':inventory,'python':str(python),'host':platform.platform(),
            'synthetic_only':True,'release_gate_verified':False,'commands':[]}
    (output/'source-manifest.json').write_text(json.dumps(inventory,indent=2)+'\n')
    def run(label,arguments,deadline):
        log=output/(label+'.log');start=time.monotonic()
        with log.open('wb') as stream:
            try:
                child=subprocess.run(arguments,cwd=source,stdout=stream,stderr=subprocess.STDOUT,
                    timeout=deadline,check=False,env={**os.environ,'PYTHONPATH':str(source)})
                code=child.returncode
            except subprocess.TimeoutExpired:code=124
        report['commands'].append({'label':label,'command':arguments,'cwd':str(source),
            'exit_code':code,'seconds':time.monotonic()-start,'log_sha256':sha(log)})
        (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        if code:raise RuntimeError(label+' failed; evidence preserved.')
    try:
        run('dependency-pins',[str(python),'-c',
            "import importlib.metadata as m,json; from services.tideglass_service.deployment import VERSIONS; actual={n:m.version(n) for n in VERSIONS}; print(json.dumps(actual,sort_keys=True)); assert actual==VERSIONS"],10)
        run('author-tests',[str(python),'-m','unittest','discover','-s','tests/services/operations','-p','test_operating_delivery.py','-v'],45)
        run('actual-http-tls-rehearsal',[str(python),'services/rehearse_deployment.py','--output',str(output/'rehearsal')],90)
        actual=json.loads((output/'rehearsal/report.json').read_text())
        if actual.get('status')!='passed':raise RuntimeError('Rehearsal report failed.')
        report['rehearsal_report_sha256']=sha(output/'rehearsal/report.json')
        report['source_drift']=[row['path'] for row in inventory if sha(source/row['path'])!=row['sha256'] or sha(ROOT/row['path'])!=row['sha256']]
        if report['source_drift']:raise RuntimeError('Source changed during verification.')
        report['status']='passed'
    except Exception as error:
        report['status']='failed';report['failure']=str(error)
        raise
    finally:
        (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        print(output)


if __name__=='__main__':main()
