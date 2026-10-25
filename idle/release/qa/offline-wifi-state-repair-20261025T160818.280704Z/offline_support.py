#!/usr/bin/env python3
"""Staged local-only offline qualification support; no device mutation commands."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import socket
import socketserver
import subprocess
import threading
import time

CANDIDATE = '3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59'
DEVICE = 'emulator-5556'
IDENTITY = ('run_id', 'nonce', 'server_id', 'candidate_fingerprint', 'harness_sha256')
PHASES = ('before-online', 'request-disable', 'offline-ready', 'offline-complete', 'request-restore', 'after-restored')
HEX64 = re.compile(r'^[a-f0-9]{64}$')


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regular(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Regular contained input required: ' + str(path))
    return path


def validate_profile(profile):
    if profile.get('device') != DEVICE or profile.get('candidate_fingerprint') != CANDIDATE:
        raise ValueError('Only the exact owned Android target / frozen candidate is admitted')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', profile.get('run_id', '')):
        raise ValueError('Invalid unique pair run ID')
    for key in ('nonce', 'harness_sha256'):
        if not HEX64.fullmatch(profile.get(key, '')):
            raise ValueError('Invalid ' + key)
    if not re.fullmatch(r'[a-f0-9]{32}', profile.get('server_id', '')):
        raise ValueError('Invalid server ID')
    if type(profile.get('port')) is not int or not 1024 <= profile['port'] <= 65535:
        raise ValueError('Invalid local listener port')
    return profile


def challenge(profile, request, receipt_id, now):
    """Pure request validator. Invalid responses can never be outage evidence."""
    validate_profile(profile)
    if not isinstance(request, dict) or any(request.get(k) != profile[k] for k in IDENTITY):
        raise ValueError('Challenge identity mismatch')
    if request.get('kind') not in ('app', 'health'):
        raise ValueError('Unknown probe kind')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,150}', request.get('probe_id', '')):
        raise ValueError('Invalid probe ID')
    if request['kind'] == 'app':
        if request.get('platform') != 'android' or request.get('scenario') not in ('natural-start', 'natural-reload'):
            raise ValueError('Wrong app scenario/platform')
        if not re.fullmatch(r'integration-[A-Za-z0-9_.-]{1,180}', request.get('verification_id', '')):
            raise ValueError('Invalid app verification ID')
        if type(request.get('process_id')) is not int or request['process_id'] < 1:
            raise ValueError('Missing native PID')
    return {**{k: profile[k] for k in IDENTITY}, 'probe_id': request['probe_id'],
            'ok': True, 'receipt_id': receipt_id, 'server_utc': now}


class Journal:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.sequence = 0

    def append(self, value):
        with self.lock:
            self.sequence += 1
            item = {**value, 'sequence': self.sequence, 'host_utc': utc(), 'host_monotonic_ns': time.monotonic_ns()}
            with self.path.open('a') as stream:
                stream.write(json.dumps(item, sort_keys=True) + '\n')
            return item


def serve(args):
    directory = args.directory.absolute()
    if directory.exists() or any(p.is_symlink() for p in directory.parents):
        raise ValueError('Listener evidence directory must be new and nonsymlinked')
    directory.mkdir(parents=False)
    harness_hash = digest(regular(args.harness))
    profile = {'device': DEVICE, 'candidate_fingerprint': CANDIDATE, 'run_id': args.run_id,
               'nonce': secrets.token_hex(32), 'server_id': secrets.token_hex(16), 'harness_sha256': harness_hash, 'port': 1024}
    validate_profile(profile)
    journal = Journal(directory / 'listener.jsonl')

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(3)
            try:
                raw = self.rfile.readline(8193)
                if len(raw) > 8192 or not raw.endswith(b'\n'):
                    raise ValueError('Bounded newline request required')
                request = json.loads(raw)
                response = challenge(profile, request, secrets.token_hex(16), utc())
                journal.append({'type': 'receipt', 'request': request, 'response': response})
                self.wfile.write(json.dumps(response).encode() + b'\n')
                self.wfile.flush()
            except (OSError, ValueError, TypeError) as error:
                journal.append({'type': 'rejected', 'error': str(error)})

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = False

    with Server(('127.0.0.1', 0), Handler) as server:
        profile['port'] = server.server_address[1]
        validate_profile(profile)
        (directory / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
        stop = threading.Event()
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        print(str(directory / 'profile.json'), flush=True)
        number = 0
        try:
            while not stop.wait(1):
                number += 1
                request = {**{k: profile[k] for k in IDENTITY}, 'kind': 'health', 'probe_id': 'health-' + str(number)}
                try:
                    with socket.create_connection(('127.0.0.1', profile['port']), timeout=2) as connection:
                        connection.sendall(json.dumps(request).encode() + b'\n')
                        response = json.loads(connection.makefile('rb').readline(8193))
                    if any(response.get(k) != request[k] for k in IDENTITY + ('probe_id',)) or response.get('ok') is not True:
                        raise ValueError('Host health challenge mismatch')
                    journal.append({'type': 'health', 'ok': True, 'receipt_id': response['receipt_id']})
                except (OSError, ValueError) as error:
                    journal.append({'type': 'health', 'ok': False, 'error': str(error)})
        except KeyboardInterrupt:
            journal.append({'type': 'stopped', 'reason': 'operator'})
        finally:
            stop.set()
            server.shutdown()


def read_profile(path, run_id, device, harness_hash):
    profile = validate_profile(json.loads(regular(path).read_text()))
    if profile['run_id'] != run_id or profile['device'] != device or profile['harness_sha256'] != harness_hash:
        raise ValueError('Profile does not bind this run/target/harness')
    regular(Path(path).parent / 'listener.jsonl')
    return profile


def parse_os(snapshot):
    commands = snapshot.get('commands', {})
    if any(commands.get(k, {}).get('exit_code') != 0 for k in ('airplane', 'wifi', 'data', 'connectivity', 'routes', 'sdk')):
        raise ValueError('Missing or failed read-only OS snapshot')
    out = lambda k: commands[k]['stdout'].strip()
    if out('sdk') != '35':
        raise ValueError('Unexpected emulator SDK; API36 build target is not runtime qualification')
    if out('airplane') not in ('0', '1') or out('wifi') not in ('0', '1', '3') or out('data') not in ('0', '1'):
        raise ValueError('Unknown actual radio settings')
    # Android 15 WifiSettingsStore: 3 is WIFI_DISABLED_APM_ON, not enabled.
    if out('wifi') == '3' and out('airplane') != '1':
        raise ValueError('Airplane-disabled Wi-Fi state without airplane mode')
    matches = re.findall(r'^\s*Active default network: (none|\d+)\s*$', out('connectivity'), re.M)
    if len(matches) != 1:
        raise ValueError('Unknown/ambiguous default-network state; inspect raw dump')
    return {'airplane': out('airplane'), 'wifi': out('wifi'), 'data': out('data'), 'default': matches[0]}


def snapshot_os(root, device, marker):
    adb = str(root / '.tooling/android-sdk/platform-tools/adb')
    commands = {'airplane': ['settings', 'get', 'global', 'airplane_mode_on'],
                'wifi': ['settings', 'get', 'global', 'wifi_on'],
                'data': ['settings', 'get', 'global', 'mobile_data'],
                'connectivity': ['dumpsys', 'connectivity'],
                'routes': ['ip', 'route', 'show', 'table', 'all'],
                'sdk': ['getprop', 'ro.build.version.sdk']}
    result = {'marker': marker, 'device': device, 'started_utc': utc(), 'commands': {}}
    for name, suffix in commands.items():
        command = [adb, '-s', device, 'shell', *suffix]
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=10)
            row = {'command': command, 'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr}
        except subprocess.TimeoutExpired as error:
            row = {'command': command, 'exit_code': None, 'error': str(error)}
        result['commands'][name] = row
    result['completed_utc'] = utc()
    return result


def run_command(command, app, env, evidence, root, args, expected):
    """Only read-only snapshots, triggered by bound native markers; never toggles radios."""
    snapshots = []
    marker_errors = []
    with (evidence / 'run.log').open('w') as log:
        child = subprocess.Popen(command, cwd=app, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            for line in child.stdout:
                log.write(line)
                log.flush()
                if 'TIDEGLASS_OFFLINE ' not in line:
                    continue
                try:
                    # Require an actual native log prefix, not quoted source/command output.
                    match = re.match(r'^I/flutter\s*\(\s*\d+\):\s*TIDEGLASS_OFFLINE (\{.*\})\s*$', line)
                    if not match:
                        raise ValueError('Non-native marker')
                    marker = json.loads(match[1])
                    for key, value in expected.items():
                        if marker.get(key) != value:
                            raise ValueError('Marker identity mismatch: ' + key)
                    if marker.get('phase') not in PHASES:
                        raise ValueError('Unknown marker phase')
                    if marker['phase'] not in ('request-disable', 'request-restore'):
                        snapshots.append(snapshot_os(root, args.device, marker))
                    print(json.dumps({'operator_marker': marker, 'evidence': str(evidence)}), flush=True)
                except (ValueError, KeyError, TypeError) as error:
                    marker_errors.append(str(error))
            code = child.wait()
        except BaseException as error:
            log.write('Offline runner interrupted: ' + repr(error) + '\n')
            log.flush()
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
            code = 130
        finally:
            (evidence / 'os-snapshots.json').write_text(json.dumps({'snapshots': snapshots, 'marker_errors': marker_errors}, indent=2) + '\n')
    return code


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def qualify(payload, profile, journal, snapshots, predecessor=None):
    """Pure fail-closed verifier. Raises on missing provenance or partial evidence."""
    validate_profile(profile)
    offline = payload['offline_network']
    for key in IDENTITY:
        if offline.get(key) != profile[key]:
            raise ValueError('Payload/profile identity mismatch: ' + key)
    for key in ('verification_id', 'platform', 'device_label', 'scenario', 'process_id'):
        if offline.get(key) != payload.get(key):
            raise ValueError('Nested payload identity mismatch: ' + key)
    if payload['platform'] != 'android' or payload['scenario'] not in ('natural-start', 'natural-reload'):
        raise ValueError('Unsupported target/scenario')
    if snapshots['marker_errors']:
        raise ValueError('Malformed or unbound native marker')
    os_rows = snapshots['snapshots']
    expected_phases = ['before-online', 'offline-ready', 'offline-complete'] if payload['scenario'] == 'natural-start' else ['offline-ready', 'offline-complete', 'after-restored']
    if [row['marker']['phase'] for row in os_rows] != expected_phases:
        raise ValueError('Missing, duplicate, or unordered OS snapshots')
    states = {}
    for row in os_rows:
        if row['device'] != DEVICE:
            raise ValueError('OS snapshot target mismatch')
        for key in IDENTITY + ('verification_id', 'platform', 'scenario', 'process_id', 'device_label'):
            if row['marker'].get(key) != offline.get(key):
                raise ValueError('OS marker identity mismatch: ' + key)
        phase = row['marker']['phase']
        state = parse_os(row)
        states[phase] = state
        if phase.startswith('offline-') and (state['airplane'] != '1' or state['wifi'] not in ('0', '3') or state['default'] != 'none'):
            raise ValueError('Airplane alone insufficient: actual default network/wifi still available')
        if phase in ('before-online', 'after-restored') and (state['airplane'] != '0' or state['default'] == 'none'):
            raise ValueError('Before/restored OS network not active')
    if not journal or [row.get('sequence') for row in journal] != list(range(1, len(journal)+1)):
        raise ValueError('Incomplete listener journal sequence')
    receipts = {row['response']['receipt_id']: row for row in journal if row.get('type') == 'receipt'}
    if len(receipts) != sum(row.get('type') == 'receipt' for row in journal):
        raise ValueError('Duplicate listener receipt ID')
    health = []
    for row in journal:
        if row.get('type') == 'health' and row.get('ok') is True:
            receipt = receipts.get(row.get('receipt_id'))
            if not receipt or receipt['request'].get('kind') != 'health' or any(receipt['request'].get(k) != profile[k] for k in IDENTITY):
                raise ValueError('Host health lacks bound successful listener challenge')
            health.append(timestamp(row['host_utc']))
    samples = offline['samples']
    if not samples:
        raise ValueError('No actual app socket samples')
    critical = {'offline-ready', 'bootstrap', 'after-gameplay'}
    critical |= {'elapsed-earnings', 'before-purchase', 'after-save'} if payload['scenario'] == 'natural-start' else {'before-reload-check'}
    if not critical.issubset({row['phase'] for row in samples}):
        raise ValueError('Missing actual offline operation probes')
    # Local and emulator wall clocks are not assumed equal. Three actual
    # online round trips establish a bounded midpoint offset from server UTC.
    reference = samples if payload['scenario'] == 'natural-start' else (predecessor or {}).get('offline_network', {}).get('samples', [])
    online = [x for x in reference if x.get('phase') == 'before-online' and x.get('reachable') is True]
    if len(online) < 3:
        raise ValueError('Missing actual preflight for clock alignment')
    offsets = [timestamp(x['receipt']['server_utc']) - (timestamp(x['started_utc']) + timestamp(x['completed_utc'])) / 2 for x in online[-3:]]
    if max(offsets) - min(offsets) > 1 or any(timestamp(x['completed_utc']) - timestamp(x['started_utc']) > 1 for x in online[-3:]):
        raise ValueError('Clock alignment too uncertain for listener health attribution')
    offset = sorted(offsets)[1]
    last_complete = 0.0
    for index, sample in enumerate(samples):
        for key in IDENTITY + ('verification_id', 'platform', 'device_label', 'scenario', 'process_id'):
            if sample.get(key) != offline.get(key):
                raise ValueError('Socket sample identity mismatch: ' + key)
        if sample['probe_id'] != payload['scenario'] + '-' + str(index):
            raise ValueError('Socket sequence mismatch')
        begin, end = timestamp(sample['started_utc']), timestamp(sample['completed_utc'])
        if not last_complete <= begin <= end or end - begin > 8:
            raise ValueError('Unordered or unbounded socket sample')
        last_complete = end
        if sample['phase'] in critical and sample.get('reachable') is not False:
            raise ValueError('App endpoint remained reachable during gameplay')
        if sample.get('reachable') is True:
            receipt = sample['receipt']
            actual = receipts.get(receipt['receipt_id'])
            if not actual or actual['response'] != receipt or actual['request']['probe_id'] != sample['probe_id']:
                raise ValueError('Successful app probe lacks exact listener receipt')
            for key in IDENTITY + ('verification_id', 'platform', 'scenario', 'process_id'):
                if actual['request'].get(key) != sample.get(key):
                    raise ValueError('Listener request provenance mismatch')
        elif sample.get('reachable') is False:
            if sample.get('error_type') not in ('SocketException', 'TimeoutException'):
                raise ValueError('Protocol assertion/error is not network loss')
            host_begin, host_end = begin + offset, end + offset
            if not any(host_begin-5 <= t <= host_begin-1 for t in health) or not any(host_end+1 <= t <= host_end+5 for t in health):
                raise ValueError('Host listener not independently healthy across app outage')
            if any(row.get('type') == 'health' and row.get('ok') is not True and host_begin-2 <= timestamp(row['host_utc']) <= host_end+2 for row in journal):
                raise ValueError('Listener failure overlaps app outage')
        else:
            raise ValueError('Unknown socket outcome')
    check_hash = offline.get('checkpoint_sha256', '')
    if not HEX64.fullmatch(check_hash):
        raise ValueError('Missing actual checkpoint hash')
    if payload['scenario'] == 'natural-start':
        before = [x for x in samples if x['phase'] == 'before-online']
        if len(before) < 3 or not all(x['reachable'] is True for x in before[-3:]):
            raise ValueError('Missing three actual reachable preflight probes')
        elapsed = [x for x in samples if x['phase'] == 'elapsed-earnings']
        if len(elapsed) < 2 or timestamp(elapsed[-1]['completed_utc']) - timestamp(elapsed[0]['started_utc']) < 30:
            raise ValueError('Missing sustained offline earnings window')
        if payload['before_core']['counts'] != [1,0,0,0,0] or payload['after_core']['counts'] != [2,0,0,0,0]:
            raise ValueError('Natural purchase count not proven')
    else:
        if not predecessor or predecessor['scenario'] != 'natural-start':
            raise ValueError('Exact successful natural-start predecessor required')
        for key in IDENTITY:
            if predecessor['offline_network'][key] != offline[key]:
                raise ValueError('Predecessor run identity mismatch')
        if predecessor['process_id'] == payload['process_id']:
            raise ValueError('Reload must be a separate native process')
        if offline.get('predecessor_checkpoint_sha256') != predecessor['offline_network']['checkpoint_sha256'] or check_hash != offline['predecessor_checkpoint_sha256']:
            raise ValueError('Reload checkpoint does not equal exact predecessor')
        restored = [x for x in samples if x['phase'] == 'after-restored']
        if len(restored) < 3 or not all(x['reachable'] is True for x in restored[-3:]):
            raise ValueError('Missing three actual reconnection probes')
        if payload['before_core']['counts'] != predecessor['after_core']['counts'] or payload['after_core']['counts'] != predecessor['after_core']['counts']:
            raise ValueError('Actual reopened fleet differs')
    return {'qualified_local_network_path': True, 'states': states, 'samples': len(samples), 'app_to_host_clock_offset_seconds': offset,
            'scope': 'Android emulator API35 guest offline path; no Internet, iOS, physical, provider or production-traffic absence claim'}


def load_predecessor(path, args, profile):
    report_path = regular(path)
    report = json.loads(report_path.read_text())
    if report.get('passed') is not True or report.get('scenario') != 'natural-start' or report.get('run_id') != args.run_id or report.get('device') != DEVICE:
        raise ValueError('Predecessor is not a passed exact start')
    if report.get('candidate_fingerprint') != CANDIDATE or report.get('label') != args.label or report.get('runner_sha256') != digest(Path(__file__).parent / 'verify_offline_native.py'):
        raise ValueError('Predecessor candidate/label/reviewer runner differs')
    for name, value in report['evidence_sha256'].items():
        if Path(name).name != name or digest(regular(report_path.parent / name)) != value:
            raise ValueError('Predecessor evidence digest mismatch')
    payload = json.loads(regular(report_path.parent / 'result.json').read_text())
    if any(payload['offline_network'].get(k) != profile[k] for k in IDENTITY):
        raise ValueError('Predecessor/profile mismatch')
    return payload


def finish(evidence, args, profile, predecessor):
    """Archive immutable listener prefix, OS receipts and checkpoint before qualification."""
    source = regular(Path(args.network_profile).parent / 'listener.jsonl')
    # Allow the last independently healthy host sample to follow the last probe.
    time.sleep(3)
    data = source.read_bytes()
    data = data[:data.rfind(b'\n')+1]
    (evidence / 'listener-prefix.jsonl').write_bytes(data)
    journal = [json.loads(line) for line in data.splitlines()]
    payload = json.loads((evidence / 'result.json').read_text())
    snapshots = json.loads((evidence / 'os-snapshots.json').read_text())
    checkpoint_path = payload.get('save_directory', '') + '/native-checkpoint.json'
    expected_path = '/data/user/0/dev.tideglass.game/files/native-verification/natural-' + args.label + '-' + args.run_id + '/native-checkpoint.json'
    if checkpoint_path != expected_path:
        raise ValueError('Unexpected native checkpoint path')
    adb = Path(__file__).resolve().parents[3] / '.tooling/android-sdk/platform-tools/adb'
    # This is a read-only regular-file check. shell preserves false status;
    # do not use exec-out as a boolean probe (historical evidence retained).
    probe = [str(adb), '-s', args.device, 'shell', 'run-as', 'dev.tideglass.game',
             'sh', '-c', '\'test -f "$1" && test ! -L "$1"\'', 'offline-checkpoint', checkpoint_path]
    checked = subprocess.run(probe, capture_output=True, timeout=10)
    exported = subprocess.run([str(adb), '-s', args.device, 'exec-out', 'run-as', 'dev.tideglass.game', 'cat', checkpoint_path], capture_output=True, timeout=10) if checked.returncode == 0 else None
    if exported is None or exported.returncode or not 0 < len(exported.stdout) <= 1024*1024:
        raise ValueError('Actual regular native checkpoint could not be archived')
    (evidence / 'native-checkpoint.json').write_bytes(exported.stdout)
    if hashlib.sha256(exported.stdout).hexdigest() != payload['offline_network']['checkpoint_sha256']:
        raise ValueError('Exported native checkpoint differs from actual app digest')
    result = qualify(payload, profile, journal, snapshots, predecessor)
    if predecessor:
        prior = json.loads(regular(Path(args.predecessor).parent / 'os-snapshots.json').read_text())
        before = parse_os(prior['snapshots'][0])
        after = result['states']['after-restored']
        if any(before[k] != after[k] for k in ('airplane', 'wifi', 'data')):
            raise ValueError('Actual radio settings were not restored to baseline')
    (evidence / 'offline-qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--harness', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    serve(parser.parse_args())
