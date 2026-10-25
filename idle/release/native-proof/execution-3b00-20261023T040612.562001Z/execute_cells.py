#!/usr/bin/env python3
"""Evidence-only sequential command coordinator; delegates all verdicts to frozen tools."""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path('/Users/csys/Desktop/ibicot/idle')
CANDIDATE = ROOT / '.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
EVIDENCE = pathlib.Path(__file__).resolve().parent
DEVICES = {'ios-phone': 'F05BE4B0-52C1-4CA1-B721-BD64AE559E3F',
           'ios-tablet': 'C6D76EF5-2DBE-4C7E-BC58-70B2322F4EAB',
           'android': 'emulator-5556'}


def cell(label, scenario, run_id, predecessor=None, observe=False):
    current = scenario.startswith('runtime-')
    command = [sys.executable, str(ROOT / 'tool' / ('verify_current_runtime.py' if current else 'verify_native.py')),
               str(CANDIDATE), '--device', DEVICES[label], '--label', label,
               '--scenario', scenario, '--run-id', run_id]
    if predecessor:
        command += ['--predecessor', str(predecessor)]
    if observe:
        command += ['--observe-privacy']
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    base = EVIDENCE / (label + '-' + scenario + '-' + stamp)
    record = {'command': command, 'scenario': scenario, 'label': label, 'run_id': run_id,
              'predecessor': str(predecessor) if predecessor else None, 'started_utc': stamp}
    log = base.with_suffix('.log')
    observer = None
    observer_log = None
    native_evidence = None
    with log.open('w') as output:
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1)
        for line in process.stdout:
            output.write(line)
            output.flush()
            print(line, end='', flush=True)
            if line.startswith('Evidence: ') or line.startswith('Native checks for '):
                native_evidence = pathlib.Path(line.split('evidence: ', 1)[1].strip() if line.startswith('Native checks for ') else line.split(': ', 1)[1].strip())
                if observe:
                    observation = EVIDENCE / ('observation-' + native_evidence.name)
                    observer_command = [sys.executable, str(ROOT / 'release/native-privacy/runtime_observation.py'),
                                        'collect', '--root', str(ROOT), '--output', str(observation),
                                        '--candidate', str(CANDIDATE), '--evidence', str(native_evidence),
                                        '--device', DEVICES[label]]
                    observer_log = (EVIDENCE / ('collector-' + native_evidence.name + '.log')).open('w')
                    observer = subprocess.Popen(observer_command, cwd=ROOT, stdout=observer_log, stderr=subprocess.STDOUT)
                    record['observer_command'] = observer_command
        record['exit_code'] = process.wait()
    if observer:
        record['observer_exit_code'] = observer.wait(timeout=45)
        observer_log.close()
    if native_evidence is not None:
        report = native_evidence / 'verification.json'
        record['verification'] = str(report)
        if report.exists():
            data = report.read_bytes()
            value = json.loads(data)
            record['verification_sha256'] = hashlib.sha256(data).hexdigest()
            record['status'] = value.get('status', 'passed' if value.get('passed') else 'failed')
            record['errors'] = value.get('verification_errors', [])
            if observe and value.get('passed') is True and record.get('observer_exit_code') == 0:
                command = [sys.executable, str(ROOT / 'release/native-privacy/runtime_observation.py'),
                           'finalize', '--root', str(ROOT), '--output', str(observation)]
                finalized = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                record['finalize_command'] = command
                record['finalize_exit_code'] = finalized.returncode
                (observation / 'finalize-console.log').write_text(finalized.stdout + finalized.stderr)
    record['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    base.with_suffix('.json').write_text(json.dumps(record, indent=2) + '\n')
    with (EVIDENCE / 'cells.jsonl').open('a') as index:
        index.write(json.dumps(record) + '\n')
    print('CELL ' + json.dumps(record), flush=True)
    success = record['exit_code'] == 0 and record.get('status') in ('passed', 'expected-interrupted')
    if observe:
        success = success and record.get('finalize_exit_code') == 0
    if not success:
        raise RuntimeError('Cell failed; preserved evidence, dependent cells are not attempted')
    return native_evidence / 'verification.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('label', choices=DEVICES)
    parser.add_argument('mode', choices=['baseline-auto', 'current', 'single'])
    parser.add_argument('--scenario')
    parser.add_argument('--run-id')
    parser.add_argument('--defer-withdraw', action='store_true')
    args = parser.parse_args()
    prefix = 'v3b00-' + args.label
    if args.mode == 'single':
        cell(args.label, args.scenario, args.run_id)
    elif args.mode == 'baseline-auto':
        cell(args.label, 'seeded', prefix + '-seeded')
        if args.label != 'ios-tablet':
            cell(args.label, 'natural-start', prefix + '-natural')
            cell(args.label, 'natural-reload', prefix + '-natural')
        cell(args.label, 'session-start', prefix + '-session')
        if args.label != 'ios-tablet':
            cell(args.label, 'session-reload', prefix + '-session')
    else:
        if args.label == 'ios-tablet':
            raise ValueError('Current-runtime matrix only covers phone and Android')
        cell(args.label, 'runtime-lock-exclusion', prefix + '-lock')
        for stage in ['beforeWrite', 'afterFlush', 'afterRename']:
            prior = cell(args.label, 'runtime-save-hold-' + stage, prefix + '-save-' + stage)
            cell(args.label, 'runtime-save-recover-' + stage, prefix + '-save-' + stage, prior)
        prior = cell(args.label, 'runtime-transition-start', prefix + '-transition')
        cell(args.label, 'runtime-transition-reopen', prefix + '-transition', prior)
        cell(args.label, 'runtime-study-default', prefix + '-default', observe=True)
        prior = cell(args.label, 'runtime-study-enroll', prefix + '-enroll', observe=True)
        cell(args.label, 'runtime-study-restart', prefix + '-enroll', prior)
        prior = cell(args.label, 'runtime-study-crash-hold', prefix + '-studycrash')
        cell(args.label, 'runtime-study-crash-reopen', prefix + '-studycrash', prior)
        cell(args.label, 'runtime-study-capacity', prefix + '-capacity')
        if args.defer_withdraw:
            record = {'label': args.label, 'scenarios': ['runtime-study-storage-withdraw', 'runtime-study-withdraw-reopen'],
                      'status': 'deferred', 'reason': 'Lead directed separate reviewed test-only queue-barrier repair after both Android observation windows; original failed phone evidence retained.',
                      'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            with (EVIDENCE / 'deferred-cells.jsonl').open('a') as output:
                output.write(json.dumps(record) + '\n')
            print('DEFERRED ' + json.dumps(record), flush=True)
        else:
            prior = cell(args.label, 'runtime-study-storage-withdraw', prefix + '-withdraw')
            cell(args.label, 'runtime-study-withdraw-reopen', prefix + '-withdraw', prior)
        cell(args.label, 'runtime-cache-grace', prefix + '-cache')


if __name__ == '__main__':
    main()
