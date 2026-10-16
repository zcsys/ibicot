#!/usr/bin/env python3
"""Run seeded native UI and disk checks against a captured build candidate."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--device', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--scenario', choices=['seeded', 'natural-start', 'natural-reload', 'session-start', 'session-reload'], default='seeded')
    parser.add_argument('--run-id', default='')
    args = parser.parse_args()
    if not args.label.replace('-', '').replace('_', '').isalnum():
        parser.error('Label may contain only letters, digits, underscores and hyphens')
    candidate = args.candidate.resolve()
    manifest = json.loads((candidate / 'manifest.json').read_text())
    app = candidate / 'workspace/game/mobile'
    candidate_lock = (candidate / '.native-verification.lock').open('w')
    fcntl.flock(candidate_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    production = {path: digest for path, digest in manifest['source_sha256'].items()
                  if path.startswith('game/content/') or path == 'economy.json'
                  or (path.startswith('game/') and ('/lib/' in path or '/assets/' in path))}
    mismatches = [path for path, digest in production.items()
                  if hashlib.sha256((candidate / 'workspace' / path).read_bytes()).hexdigest() != digest]
    if mismatches:
        raise RuntimeError('Production inputs differ from frozen source: ' + ', '.join(mismatches))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    evidence = ROOT / 'release/native-proof' / ('integration-' + args.label + '-' + stamp)
    evidence.mkdir()
    if args.scenario != 'seeded' and not args.run_id:
        parser.error('Start/reload scenarios require the same explicit --run-id')
    if args.run_id and not args.run_id.replace('-', '').replace('_', '').isalnum():
        parser.error('Run id may contain only letters, digits, underscores and hyphens')
    # Test code can evolve independently while the production application input
    # remains frozen. Capture and hash this exact harness beside its evidence.
    sources = {'harness.dart': ROOT / 'game/mobile/integration_test/platform_smoke_test.dart',
               'driver.dart': ROOT / 'tool/native_integration_driver.dart'}
    harness_hashes = {}
    for name, source in sources.items():
        shutil.copy2(source, evidence / name)
        harness_hashes[name] = hashlib.sha256((evidence / name).read_bytes()).hexdigest()
    target = app / 'integration_test' / ('evidence_' + harness_hashes['harness.dart'][:12] + '_test.dart')
    driver = app / 'test_driver' / ('evidence_' + harness_hashes['driver.dart'][:12] + '.dart')
    driver.parent.mkdir(exist_ok=True)
    # These generated copies are preserved in prior evidence directories.
    # Avoid stale failed harnesses entering later whole-workspace analysis.
    for previous in (app / 'integration_test').glob('evidence_*_test.dart'):
        previous.unlink()
    for previous in driver.parent.glob('evidence_*.dart'):
        previous.unlink()
    shutil.copy2(evidence / 'harness.dart', target)
    shutil.copy2(evidence / 'driver.dart', driver)
    env = dict(os.environ, TIDEGLASS_NATIVE_EVIDENCE=str(evidence))
    command = [str(ROOT / 'tool/flutter'), 'drive', '--driver=' + str(driver.relative_to(app)),
               '--target=' + str(target.relative_to(app)), '-d', args.device,
               '--dart-define=TIDEGLASS_DEVICE_LABEL=' + args.label,
               '--dart-define=TIDEGLASS_SCENARIO=' + args.scenario,
               '--dart-define=TIDEGLASS_RUN_ID=' + args.run_id,
               '--dart-define=TIDEGLASS_VERIFICATION_ID=' + evidence.name,
               '--dart-define=TIDEGLASS_CANDIDATE_FINGERPRINT=' + manifest['source_fingerprint'],
               '--dart-define=TIDEGLASS_HARNESS_SHA256=' + harness_hashes['harness.dart'], '--keep-app-running', '--timeout=180', '--no-pub']
    report = {'candidate_fingerprint': manifest['source_fingerprint'], 'device': args.device,
              'label': args.label, 'started_utc': stamp, 'command': command,
              'scenario': args.scenario, 'run_id': args.run_id, 'harness_sha256': harness_hashes,
              'production_inputs_match_snapshot': not mismatches,
              'provenance': 'Real elapsed native bootstrap and separate-process reload; isolated test save directory' if args.scenario.startswith('natural-') else 'Seeded native boundary/presentation test; no natural pacing or physical-device claim'}
    print(f'Native checks for {args.label}; evidence: {evidence}', flush=True)
    with (evidence / 'run.log').open('w') as log:
        result = subprocess.run(command, cwd=app, env=env, stdout=log, stderr=subprocess.STDOUT)
    report['exit_code'] = result.returncode
    errors = []
    payload = json.loads((evidence / 'result.json').read_text()) if (evidence / 'result.json').is_file() else {}
    for key, expected in [('device_label', args.label), ('scenario', args.scenario), ('run_id', args.run_id), ('verification_id', evidence.name), ('candidate_fingerprint', manifest['source_fingerprint']), ('harness_sha256', harness_hashes['harness.dart'])]:
        if payload.get(key) != expected:
            errors.append(f'{key}: expected {expected!r}, received {payload.get(key)!r}')
    log_text = (evidence / 'run.log').read_text()
    for marker in ['BUILD FAILED', 'Failed to build', 'Could not build the application', 'Application failed to start']:
        if marker in log_text:
            errors.append('Compilation/startup failure in log: ' + marker)
    if 'All tests passed.' not in log_text:
        errors.append('No successful test completion in native log')
    # flutter drive's default cleanup uninstalls the application and erases
    # its sandbox. Preserve installation, then perform an explicit process stop.
    if payload.get('platform') == 'ios':
        stop_command = ['xcrun', 'simctl', 'terminate', args.device, 'dev.tideglass.game']
    else:
        stop_command = [str(ROOT / '.tooling/android-sdk/platform-tools/adb'), '-s', args.device,
                        'shell', 'am', 'force-stop', 'dev.tideglass.game']
    stopped = subprocess.run(stop_command, capture_output=True, text=True)
    report['native_process_stop'] = {'command': stop_command, 'exit_code': stopped.returncode,
                                     'output': stopped.stdout + stopped.stderr}
    if stopped.returncode:
        errors.append('Explicit native process termination failed')
    save_directory = payload.get('save_directory', '')
    if '/native-verification/' in save_directory:
        for slot in (0, 1):
            name = f'progress.{slot}.json'
            if payload.get('platform') == 'ios' and f'/Devices/{args.device}/' in save_directory:
                source = Path(save_directory) / name
                data = source.read_bytes() if source.is_file() else b''
            elif payload.get('platform') == 'android':
                exported = subprocess.run([str(ROOT / '.tooling/android-sdk/platform-tools/adb'), '-s', args.device,
                    'exec-out', 'run-as', 'dev.tideglass.game', 'cat', save_directory + '/' + name], capture_output=True)
                data = exported.stdout if exported.returncode == 0 else b''
            else:
                data = b''
            if data and len(data) <= 1024 * 1024:
                (evidence / ('native-save-' + name)).write_bytes(data)
    report['verification_errors'] = errors
    report['passed'] = result.returncode == 0 and not errors
    report['evidence_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence.iterdir() if p.is_file()}
    (evidence / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'{args.label}: exit {result.returncode}', flush=True)
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
