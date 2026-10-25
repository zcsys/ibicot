"""Freeze and verify local operating tools; output is author evidence, not acceptance."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence = ROOT/'services/evidence'/('operations-'+stamp)
    source = evidence/'source'
    source.mkdir(parents=True)
    paths = [path for folder in ('services/tideglass_service', 'tests/services')
             for path in (ROOT/folder).rglob('*.py')]
    paths += [ROOT/path for path in (
        'services/verify_operations.py', 'services/requirements-providers.lock',
        'services/docs/OPERATIONS.md', 'services/docs/FULFILLMENT.md', 'services/docs/PRIVACY.md',
        'release/runbooks/README.md', 'release/runbooks/LAUNCH_HANDOVER.md',
        'release/runbooks/launch-coverage-template.json',
        'implementation/tools/validate_save_contract.py',
        'implementation/contracts/save-envelope.schema.json',
        'implementation/scope_requirements.json', 'implementation/program.json',
        'release/downloads/tideglass-original-soundtrack.zip')]
    sources = {}
    for original in sorted(set(paths)):
        relative = original.relative_to(ROOT)
        target = source/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        sources[str(relative)] = sha(target)
    fingerprint = hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    records = []
    for name, directory in [('operations', 'tests/services/operations'), ('base-services', 'tests/services'), ('providers', 'tests/services/providers')]:
        command = [sys.executable, '-m', 'unittest', 'discover', '-s', directory, '-v']
        result = subprocess.run(command, cwd=source, text=True, capture_output=True, timeout=120)
        log = result.stdout+result.stderr
        output = evidence/(name+'.log'); output.write_text(log)
        tests = re.findall(r'^(test_\S+ \([^\n]+\)) \.\.\.', log, flags=re.M)
        records.append({'name': name, 'command': command, 'cwd': 'source', 'exit_code': result.returncode,
                        'log': output.name, 'log_sha256': sha(output),
                        'test_invocations': len(tests), 'distinct_test_ids': len(set(tests))})
    # Executable operator rehearsal uses temporary synthetic local data. All
    # successful commands run against the frozen source; no live data is read.
    scenario = r'''
import hashlib,json,os,subprocess,sys,tempfile,time,uuid
from pathlib import Path
from services.tideglass_service.api import Application
from services.tideglass_service.storage import Database
with tempfile.TemporaryDirectory(prefix='tideglass-ops-author-') as folder:
 p=Path(folder); live=p/'service.sqlite3'; backup=p/'backup.sqlite3'
 database=Database(live); app=Application(database)
 account=app.dispatch('POST','/v1/accounts',{'consent_cloud':True})[1]
 database.backup(backup)
 before=hashlib.sha256(backup.read_bytes()).hexdigest()
 records=[]
 for label,path,tail,expected in [('healthy_structure_no_samples',live,['health','--backup',str(backup)],3),('missing_path',p/'absent',['health'],2),('isolated_restore',backup,['restore-drill'],0)]:
  r=subprocess.run([sys.executable,'-m','services.tideglass_service.ops','--database',str(path),*tail],capture_output=True,text=True)
  assert r.returncode==expected,(label,r.returncode)
  records.append({'scenario':label,'exit_code':r.returncode,'output':json.loads(r.stdout)})
 with database.transaction() as db:
  db.execute('INSERT INTO purchases VALUES(?,?,?,?,?,?,?,?,?,?)',('google',str(uuid.uuid4()),account['account_id'],'dev.tideglass.cosmetic.01','purchased',1,'synthetic_operator_rehearsal',str(uuid.uuid4()),0,int(time.time())-601))
 r=subprocess.run([sys.executable,'-m','services.tideglass_service.ops','--database',str(live),'health','--backup',str(backup)],capture_output=True,text=True)
 assert r.returncode==2
 records.append({'scenario':'old_pending_acknowledgement','exit_code':r.returncode,'output':json.loads(r.stdout)})
 assert before==hashlib.sha256(backup.read_bytes()).hexdigest()
 assert not (p/'absent').exists()
 output=json.dumps({'synthetic_local_data_only':True,'unchanged_backup_sha256':before,'records':records},indent=2)
 assert account['account_id'] not in output and account['session_token'] not in output and account['recovery_code'] not in output
 print(output)
'''
    rehearsal_script = evidence/'rehearse.py'; rehearsal_script.write_text(scenario)
    command = [sys.executable, '-c', scenario]
    result = subprocess.run(command, cwd=source, capture_output=True, text=True, timeout=120)
    output = evidence/'rehearsal.json'
    output.write_text(result.stdout)
    (evidence/'rehearsal.stderr.log').write_text(result.stderr)
    records.append({'name': 'cli-rehearsal', 'command': [sys.executable, '-c', '<contents of ../rehearse.py>'],
                    'cwd': 'source', 'exit_code': result.returncode, 'output': output.name,
                    'output_sha256': sha(output), 'script_sha256': sha(rehearsal_script)})
    drift = [path for path, digest in sources.items() if sha(ROOT/path) != digest]
    report = {'format': 'tideglass-local-operations-author-v1', 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
              'source_snapshot': 'source', 'source_sha256': sources, 'source_fingerprint': fingerprint,
              'fingerprint_recipe': 'SHA256(UTF8(JSON(source_sha256, sort_keys=True, separators=(comma,colon))))',
              'runtime': sys.version, 'checks': records, 'live_source_drift_during_checks': drift,
              'source_scope': {'M5-04': ['S27','S30','S37'], 'M6-08': ['S21','S37'], 'M7-04': ['S37'], 'M7-08': ['S37','S38']},
              'reverse_mapping': {'health.py': ['M5-04'], 'recovery.py': ['M5-04','M6-08(service-only)','M7-04'],
                                  'ops.py': ['M5-04','M6-08(service-only)','M7-04'], 'release/runbooks/': ['M7-04','M7-08']},
              'independent_review': 'pending', 'production_packages_accepted': False,
              'external_provider_transactions': False, 'hosted_or_live_recovery': False,
              'alert_delivery_or_scheduler_installed': False, 'actual_launch_coverage_days': 0,
              'limits': ['No native season/pass/migration behavior verified by the service drill.',
                         'No complete independent deletion/consent/revocation journal; restored copy never eligible for live activation.',
                         'No provider freshness/key availability/actual-store proof from synthetic entitlement rows.',
                         'No elapsed support coverage, hosted capacity, configured alert delivery or empirical quality denominator.']}
    (evidence/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'evidence': str(evidence.relative_to(ROOT)), 'source_fingerprint': fingerprint,
                      'checks': [{'name': r['name'], 'exit_code': r['exit_code']} for r in records], 'drift': drift}, indent=2))
    return int(any(record['exit_code'] for record in records) or bool(drift))


if __name__ == '__main__':
    raise SystemExit(main())
