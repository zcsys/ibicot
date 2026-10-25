#!/usr/bin/env python3
"""Isolated simulator runtime qualification. Never treats killed preparation as a pass."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

import build_native
import verify_native
import study_native_diagnostics
import study_adjudicate
import study_report

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = 'dev.tideglass.game'
PROTECTED_DEVICE = 'F103390E-7B7C-4F0B-9404-5E029C7131FF'
STAGES = ('beforeWrite', 'afterFlush', 'afterRename')
KILLED = {*(f'runtime-save-hold-{s}' for s in STAGES), 'runtime-study-crash-hold'}
PREDECESSORS = {**{f'runtime-save-recover-{s}': f'runtime-save-hold-{s}' for s in STAGES},
                'runtime-transition-reopen': 'runtime-transition-start',
                'runtime-study-restart': 'runtime-study-enroll',
                'runtime-study-crash-reopen': 'runtime-study-crash-hold',
                'runtime-study-withdraw-reopen': 'runtime-study-storage-withdraw'}
STUDY_FILES = {
    'study-raw.json': ('support/tideglass-study.json', 2 * 1024 * 1024),
    'study-eligibility.json': ('support/tideglass-study-eligibility.json', 4096),
    'study-withdrawn.marker': ('support/tideglass-study.json.withdrawn', 4096),
}
SCENARIOS = frozenset(KILLED | set(PREDECESSORS) | set(PREDECESSORS.values()) | {
    'runtime-lock-exclusion', 'runtime-study-default', 'runtime-study-capacity', 'runtime-cache-grace'})
MARKER = re.compile(r'^(?:flutter:|I/flutter\s*\(\s*\d+\):)\s*TIDEGLASS_RUNTIME_KILL_READY (\{[^\n]+\})\s*$', re.M)
HEX = re.compile(r'^[a-f0-9]{64}$')
SAFE = re.compile(r'^[A-Za-z0-9_-]+$')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError('JSON object required: ' + str(path))
    return value


def require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


def validate_request(device: str, label: str, scenario: str, run_id: str) -> str:
    require(device.upper() != PROTECTED_DEVICE, 'Protected tablet is never an execution target')
    require(scenario in SCENARIOS, 'Scenario is not allowlisted')
    require(bool(SAFE.fullmatch(label)) and bool(SAFE.fullmatch(run_id)), 'Unsafe label or run ID')
    # Deliberately simulator-only. No physical-device qualification is implied.
    platform = verify_native.native_platform(device, None)
    require(platform in ('ios', 'android'), 'Only iOS simulators and Android emulators are supported')
    return platform


def group_for(scenario: str) -> str:
    if scenario.startswith('runtime-save-'):
        return 'save-' + scenario.rsplit('-', 1)[1]
    if scenario.startswith('runtime-transition-'):
        return 'transition'
    if scenario.startswith('runtime-study-'):
        return 'study'
    return 'save-lock' if scenario == 'runtime-lock-exclusion' else 'cache'


def fixture_path(path: str, context: dict, data_container: str | None = None) -> Path:
    """Only the exact declared support fixture, never app save or shared cache."""
    relative = Path('native-current-verification') / (context['label'] + '-' + context['run_id']) / group_for(context['scenario'])
    actual = Path(path)
    require(actual.is_absolute() and '..' not in actual.parts, 'Unsafe fixture path')
    if context['platform'] == 'ios':
        require(bool(data_container), 'Actual iOS app data container is required')
        base = Path(data_container).resolve() / 'Library/Application Support'
        expected = base / relative
        lexical = Path(data_container) / 'Library/Application Support' / relative
        require(actual in (expected, lexical) and actual.resolve() == expected and expected.is_relative_to(Path(data_container).resolve()), 'Fixture is not within this simulator app container')
        actual = expected
    else:
        expected = Path('/data/user/0') / BUNDLE / 'files' / relative
        require(actual == expected, 'Fixture is not the exact Android private support directory')
    return actual


def identities(context: dict) -> dict:
    return {'verification_id': context['verification_id'], 'candidate_fingerprint': context['candidate_fingerprint'],
            'harness_sha256': context['harness_sha256'], 'scenario': context['scenario'],
            'run_id': context['run_id'], 'device_label': context['label'], 'platform': context['platform']}


def marker_from_log(log: str, context: dict) -> dict:
    matches = MARKER.findall(log)
    require(len(matches) == 1, 'Exactly one anchored native kill checkpoint marker is required')
    marker = json.loads(matches[0])
    for key in ('verification_id', 'candidate_fingerprint', 'harness_sha256', 'scenario'):
        require(marker.get(key) == context[key], 'Kill marker identity mismatch: ' + key)
    require(type(marker.get('process_id')) is int and marker['process_id'] > 1, 'Invalid native PID')
    require(bool(HEX.fullmatch(marker.get('checkpoint_sha256', ''))), 'Invalid checkpoint hash')
    require(context['scenario'] in KILLED, 'This scenario cannot be intentionally killed')
    before = log[:MARKER.search(log).start()]
    real_failures = [e for e in verify_native.native_log_errors(before) if not e.startswith('No successful')]
    require(not real_failures, 'Native failure occurred before the expected interruption: ' + str(real_failures))
    return marker


def native_observation_errors(value, platform, native_pid):
    expected = {'version': 1, 'status': 'available', 'source': 'native_process_observation_v1',
                'native_pid': native_pid, 'platform': platform, 'application_id': BUNDLE,
                'application_version': '0.1.0', 'application_build': '1'}
    if not isinstance(value, dict) or set(value) != set(expected) | {'observed_start_utc_ms'}:
        return ['Missing exact native process observation fields']
    errors = [f'Native observation mismatch: {key}' for key, item in expected.items()
              if type(value[key]) is not type(item) or value[key] != item]
    stamp = value['observed_start_utc_ms']
    if type(stamp) is not int or not 0 <= stamp < 2**53:
        errors.append('Invalid native observation time')
    return errors


def validate_checkpoint(raw: bytes, context: dict, pid: int) -> dict:
    require(0 < len(raw) <= 65536, 'Checkpoint size exceeds limit or is empty')
    checkpoint = json.loads(raw)
    require(isinstance(checkpoint, dict), 'Checkpoint must be an object')
    for key, expected in [('candidate_fingerprint', context['candidate_fingerprint']), ('harness_sha256', context['harness_sha256']),
                          ('device_label', context['label']), ('run_id', context['run_id']),
                          ('preparation_verification_id', context['verification_id']), ('native_process_id', pid)]:
        require(type(checkpoint.get(key)) is type(expected) and checkpoint.get(key) == expected, 'Checkpoint identity mismatch: ' + key)
    scenario = context['scenario']
    if scenario.startswith('runtime-save-hold-'):
        require(checkpoint.get('stage') == scenario.rsplit('-', 1)[1], 'Checkpoint commit stage mismatch')
    if scenario in ('runtime-study-enroll', 'runtime-study-crash-hold'):
        require(bool(checkpoint.get('study_process_id')), 'Missing synthetic logical study process link')
        require(not native_observation_errors(checkpoint.get('native_process_observation'), context['platform'], pid), 'Checkpoint lacks matching actual native process observation')
        require(bool(HEX.fullmatch(checkpoint.get('first_record_sha256', ''))), 'Missing retained study record hash')
    return checkpoint


def payload_errors(payload: dict, context: dict, prior: dict | None = None) -> list[str]:
    errors = [f'Payload identity mismatch: {key}' for key, expected in identities(context).items() if payload.get(key) != expected]
    if payload.get('completed') is not True:
        errors.append('Harness did not complete')
    if type(payload.get('process_id')) is not int or payload.get('process_id', 0) <= 1:
        errors.append('Missing real native process ID')
    if payload.get('fixture_kind') != 'INTERNAL SYNTHETIC QUALIFICATION ONLY':
        errors.append('Synthetic provenance is absent')
    if not isinstance(payload.get('checks'), list) or not payload['checks'] or not all(isinstance(x, str) and x for x in payload['checks']):
        errors.append('No concrete completed checks')
    if payload.get('expected_interruption'):
        errors.append('Interrupted preparation cannot be passed')
    scenario = context['scenario']
    expected = {}
    if scenario.startswith('runtime-study-'):
        expected['native_study_samples'] = 0 if scenario in ('runtime-study-default', 'runtime-study-withdraw-reopen') else 1
        if expected['native_study_samples'] == 1:
            errors.extend(native_observation_errors(payload.get('native_study_process_context'), context['platform'], payload.get('process_id')))
        elif any(key in payload for key in ('native_study_process_context', 'native_study_logical_process_id')):
            errors.append('Zero-sample scenario contains native study context or logical process identity')
    if scenario.startswith('runtime-save-recover-'):
        stage = scenario.rsplit('-', 1)[1]
        expected.update(recovered_stage=stage, save_loaded_amount=1 if stage == 'afterRename' else 0, save_after_recovery_amount=2)
    if scenario.startswith('runtime-transition-'):
        start = scenario.endswith('-start')
        expected.update(lifetime_micros='90000000' if start else '91000000', default_predecessor_registration=not start, same_cursor_reopen_checked=not start)
    if scenario in ('runtime-study-restart', 'runtime-study-crash-reopen'):
        expected.update(study_identity_and_chain_retained=True, new_study_process_recorded=True, invented_terminal_count=0)
    if scenario == 'runtime-study-capacity':
        expected['study_capacity_gap'] = True
        for key, cap in [('study_capacity_records', 8), ('study_capacity_bytes', 32768)]:
            if type(payload.get(key)) is not int or not 0 < payload[key] <= cap:
                errors.append('Invalid capacity evidence: ' + key)
    if scenario == 'runtime-study-storage-withdraw':
        expected.update(storage_failure_visible=True, withdrawal_durable=True)
    if scenario == 'runtime-study-withdraw-reopen':
        expected['withdrawal_durable'] = True
    if scenario == 'runtime-cache-grace':
        expected['cache_limits'] = {'exports': 3, 'bytes': 192 * 1024 * 1024, 'grace_seconds': 86400}
    for key, value in expected.items():
        if payload.get(key) != value or type(payload.get(key)) is not type(value):
            errors.append('Missing or incorrect scenario evidence: ' + key)
    if scenario in PREDECESSORS:
        if prior is None:
            errors.append('Recovery requires validated predecessor evidence')
        else:
            for key, value in [('preparation_verification_id', prior['verification_id']),
                               ('preparation_checkpoint_sha256', prior['checkpoint_sha256']),
                               ('previous_native_process_id', prior['native_process_id'])]:
                if payload.get(key) != value:
                    errors.append('Recovery predecessor mismatch: ' + key)
            if payload.get('process_id') == prior['native_process_id']:
                errors.append('Recovery reused the previous native process')
    return errors


def negative_native_errors(log: str) -> list[str]:
    return [e for e in verify_native.native_log_errors(log) if not e.startswith('No successful')]


def bind_pre_kill_prefix(raw: bytes, context: dict, evidence: Path, ledger: dict):
    prefix = raw.decode(errors='replace')
    marker_from_log(prefix, context)
    require(not negative_native_errors(prefix), 'Native failure in the complete host-observed pre-kill log')
    require('All tests passed' not in prefix, 'Preparation completed before process kill')
    (evidence / 'pre-kill.log').write_bytes(raw)
    ledger.update(pre_kill_log_bytes=len(raw), pre_kill_log_sha256=digest(raw), pre_kill_observed_monotonic_ns=time.monotonic_ns())


def interrupted_errors(log: str, context: dict, marker: dict, ledger: dict, raw_log: bytes | None = None) -> list[str]:
    errors = []
    try:
        require(marker_from_log(log, context) == marker, 'Final log marker changed')
        raw = raw_log if raw_log is not None else log.encode()
        size = ledger.get('pre_kill_log_bytes')
        require(type(size) is int and 0 < size <= len(raw), 'Missing exact pre-kill log boundary')
        prefix = raw[:size]
        require(digest(prefix) == ledger.get('pre_kill_log_sha256'), 'Pre-kill log prefix hash mismatch')
        require(marker_from_log(prefix.decode(errors='replace'), context) == marker, 'Marker was not observed before kill')
        require(not negative_native_errors(prefix.decode(errors='replace')), 'Native failure in host-observed pre-kill log')
        # A native error buffered after the byte boundary may still have been
        # emitted before SIGKILL. App/framework errors anywhere invalidate the
        # preparation; ordinary driver lost-connection cleanup is not one.
        require(not negative_native_errors(log), 'Native failure in interrupted preparation log')
        require(ledger.get('identity_validated') is True and ledger.get('termination_observed') is True, 'No host-observed process termination')
        require(ledger.get('native_process_id') == marker['process_id'], 'Killed PID differs from checkpoint PID')
        require(ledger.get('device') == context['device'], 'Killed device differs from declared device')
        require(ledger.get('action') == 'SIGKILL' and ledger.get('signal_sent') is True, 'No actual host SIGKILL action')
        require(ledger.get('after_alive') is False and ledger.get('before_alive') is True, 'Process did not change from alive to absent')
        require(isinstance(ledger.get('observations'), list) and len(ledger['observations']) >= 2, 'Missing host process observations')
        require(not re.search(r'All tests passed[!.]', log), 'Killed preparation unexpectedly reports completion')
    except (ValueError, KeyError, TypeError) as error:
        errors.append(str(error))
    return errors


def validate_predecessor(path: Path, context: dict) -> dict:
    prior = read_json(path)
    require(context['scenario'] in PREDECESSORS, 'Unexpected predecessor for standalone scenario')
    require(prior.get('scenario') == PREDECESSORS[context['scenario']], 'Incorrect predecessor scenario')
    for key in ('candidate_fingerprint', 'harness_sha256', 'device', 'label', 'platform', 'run_id'):
        require(prior.get(key) == context[key], 'Predecessor identity mismatch: ' + key)
    require(prior.get('production_input_differences_after_run') == [] and prior.get('source_snapshot_unchanged') is True, 'Predecessor source integrity failed')
    require(prior.get('verification_errors') == [], 'Predecessor had verification errors')
    hashes = prior.get('evidence_sha256', {})
    for required in ('run.log', 'checkpoint.json', 'harness.dart', 'runner.py', 'build_native.py', 'verify_native.py', 'driver.dart'):
        require(required in hashes, 'Predecessor omitted evidence: ' + required)
    for name, sha in hashes.items():
        require(Path(name).name == name and name != 'verification.json', 'Unsafe evidence name')
        require((path.parent / name).is_file() and digest((path.parent / name).read_bytes()) == sha, 'Predecessor evidence changed: ' + name)
    require(hashes['harness.dart'] == context['harness_sha256'], 'Predecessor archived harness mismatch')
    require(hashes['runner.py'] == digest(Path(__file__).read_bytes()), 'Predecessor requires the same reviewed runner revision')
    raw = (path.parent / 'checkpoint.json').read_bytes()
    require(digest(raw) == prior.get('checkpoint_sha256'), 'Predecessor checkpoint hash mismatch')
    validate_checkpoint(raw, prior, prior['native_process_id'])
    raw_log = (path.parent / 'run.log').read_bytes()
    log = raw_log.decode(errors='replace')
    if prior['scenario'] in KILLED:
        require(prior.get('status') == 'expected-interrupted' and prior.get('passed') is False, 'Killed preparation cannot be a passed test')
        require(not interrupted_errors(log, prior, prior.get('kill_marker', {}), prior.get('native_kill', {}), raw_log), 'Invalid interrupted predecessor')
        require('pre-kill.log' in hashes, 'Predecessor omitted pre-kill boundary')
        require((path.parent / 'pre-kill.log').read_bytes() == raw_log[:prior['native_kill']['pre_kill_log_bytes']], 'Archived pre-kill prefix differs from native log')
    else:
        require(prior.get('status') == 'passed' and prior.get('passed') is True and prior.get('exit_code') == 0, 'Predecessor did not pass')
        require('result.json' in hashes, 'Predecessor omitted driver result')
        require(not verify_native.native_log_errors(log), 'Predecessor native/driver completion failed')
        require(not payload_errors(read_json(path.parent / 'result.json'), prior), 'Predecessor harness result is invalid')
        require(prior.get('native_process_stop', {}).get('termination_observed') is True, 'Predecessor process termination was not observed')
    if prior['scenario'].startswith('runtime-save-hold-') or prior['scenario'] == 'runtime-transition-start':
        require(prior.get('generations') and any(v.get('size', 0) > 0 for v in prior['generations'].values()), 'Predecessor omitted retained save generations')
    for name, record in prior.get('generations', {}).items():
        require(name in ('generation-0.json', 'generation-1.json'), 'Unexpected retained generation name')
        if record.get('size', 0):
            require(name in hashes, 'Retained generation missing from evidence pins')
            data = (path.parent / name).read_bytes()
            require(len(data) == record['size'] and digest(data) == record['sha256'], 'Retained generation metadata mismatch')
    if prior['scenario'].startswith('runtime-study-'):
        require(prior.get('study_artifacts') is not None, 'Missing actual synthetic study artifacts')
        for name, record in prior['study_artifacts'].items():
            require(name in STUDY_FILES, 'Unexpected study artifact')
            if record['present']:
                require(name in hashes, 'Study artifact missing from evidence pins')
        inspect_study_artifacts(path.parent, prior, prior['study_artifacts'])
    return prior


class NativeHost:
    """Every destructive operation is bound to the selected simulator and bundle."""
    def __init__(self, context: dict):
        validate_request(context['device'], context['label'], context['scenario'], context['run_id'])
        self.context = context
        self.observations = []
        self.adb = str(ROOT / '.tooling/android-sdk/platform-tools/adb')
        self.data_container = None
        self.app_container = None
        if context['platform'] == 'ios':
            self.data_container = self.command(['xcrun', 'simctl', 'get_app_container', context['device'], BUNDLE, 'data']).decode().strip()
            self.app_container = self.command(['xcrun', 'simctl', 'get_app_container', context['device'], BUNDLE, 'app']).decode().strip()
            require(Path(self.data_container).is_absolute() and Path(self.app_container).is_absolute(), 'Invalid simulator containers')

    def command(self, command: list[str], *, allow_failure=False) -> bytes:
        result = subprocess.run(command, capture_output=True, timeout=20)
        self.observations.append({'command': command, 'exit_code': result.returncode,
                                  'stdout': result.stdout.decode(errors='replace'), 'stderr': result.stderr.decode(errors='replace'),
                                  'observed_monotonic_ns': time.monotonic_ns()})
        require(allow_failure or result.returncode == 0, 'Host command failed: ' + str(command))
        return result.stdout

    def adb_command(self, *parts: str) -> list[str]:
        return [self.adb, '-s', self.context['device'], *parts]

    def identity(self, native_pid: int) -> bool:
        require(type(native_pid) is int and native_pid > 1, 'Unsafe native PID')
        if self.context['platform'] == 'ios':
            actual = self.command(['ps', '-p', str(native_pid), '-o', 'comm='], allow_failure=True).decode().strip()
            return actual == str(Path(self.app_container) / 'Runner')
        pids = self.command(self.adb_command('shell', 'pidof', BUNDLE), allow_failure=True).decode().split()
        if str(native_pid) not in pids:
            return False
        raw = self.command(self.adb_command('exec-out', 'run-as', BUNDLE, 'cat', f'/proc/{native_pid}/cmdline'))
        return raw.split(b'\0', 1)[0] == BUNDLE.encode()

    def read_fixture(self, directory: str, relative: str, *, optional=False, limit=2 * 1024 * 1024 + 65536) -> bytes | None:
        base = fixture_path(directory, self.context, self.data_container)
        require(relative in {'checkpoint.json', 'progress.0.json', 'progress.1.json', 'game/progress.0.json', 'game/progress.1.json'} | {entry[0] for entry in STUDY_FILES.values()}, 'Unexpected fixture file')
        path = base / relative
        if self.context['platform'] == 'ios':
            require(path.resolve() == path and path.is_relative_to(base), 'Fixture file is a symlink')
            if optional and not path.exists():
                return None
            require(path.is_file() and path.stat().st_size <= limit, 'Fixture file absent or too large')
            return path.read_bytes()
        # Check every component below the OS-owned app directory before head.
        # /data/user/0 itself may be a platform alias; fixture components may
        # not be symlinks, FIFOs or unreadable directories. These are stopped
        # synthetic fixtures, not a hostile concurrent-writer security claim.
        def probe(flag: str, target: Path) -> bool:
            self.command(self.adb_command('exec-out', 'run-as', BUNDLE, 'test', flag, str(target)), allow_failure=True)
            observation = self.observations[-1]
            require(observation['exit_code'] in (0, 1) and not observation['stderr'] and not observation['stdout'],
                    'Could not establish native fixture type/access')
            return observation['exit_code'] == 0

        app_base = Path('/data/user/0') / BUNDLE
        cursor = app_base
        for part in path.relative_to(app_base).parts:
            cursor = cursor / part
            require(not probe('-L', cursor), 'Native fixture component is a symlink')
            if not probe('-e', cursor):
                require(optional, 'Required native fixture file is absent')
                return None
            require(probe('-f' if cursor == path else '-d', cursor), 'Native fixture component has unexpected type')
            require(probe('-r', cursor), 'Native fixture component is unreadable')
            if cursor != path:
                require(probe('-x', cursor), 'Native fixture directory is not traversable')
        # Bound bytes before moving anything from the device. All path components
        # are fixed or safe-token validated; adb's shell is never given user text.
        data = self.command(self.adb_command('exec-out', 'run-as', BUNDLE, 'head', '-c', str(limit + 1), str(path)))
        require(len(data) <= limit, 'Fixture file exceeds byte limit')
        return data

    def kill(self, native_pid: int, record: dict | None = None, *, before_signal=None) -> dict:
        before = self.identity(native_pid)
        require(before, 'Native PID is not the declared simulator app executable')
        if record is None:
            record = {}
        record.update(device=self.context['device'], native_process_id=native_pid, identity_validated=True,
                      before_alive=before, action='SIGKILL', signal_sent=False)
        require(before_signal is not None, 'Pre-kill log boundary callback is required')
        before_signal(record)
        if self.context['platform'] == 'ios':
            os.kill(native_pid, signal.SIGKILL)
            self.observations.append({'action': 'os.kill', 'pid': native_pid, 'signal': 'SIGKILL', 'observed_monotonic_ns': time.monotonic_ns()})
        else:
            self.command(self.adb_command('shell', 'run-as', BUNDLE, 'kill', '-9', str(native_pid)))
        record['signal_sent'] = True
        record['after_alive'] = self.wait_absent(native_pid)
        record['termination_observed'] = not record['after_alive']
        record['observations'] = list(self.observations)
        require(record['termination_observed'], 'Native process termination was not observed')
        return record

    def wait_absent(self, native_pid: int) -> bool:
        deadline = time.monotonic() + 10
        while self.identity(native_pid):
            if time.monotonic() >= deadline:
                return True
            time.sleep(.1)
        return False

    def stop(self, native_pid: int) -> dict:
        require(self.identity(native_pid), 'Completed native process identity no longer matches')
        command = (['xcrun', 'simctl', 'terminate', self.context['device'], BUNDLE] if self.context['platform'] == 'ios'
                   else self.adb_command('shell', 'am', 'force-stop', BUNDLE))
        self.command(command)
        absent = not self.wait_absent(native_pid)
        return {'command': command, 'termination_observed': absent, 'observations': list(self.observations)}


def archive_fixture(host: NativeHost, directory: str, context: dict, evidence: Path) -> dict:
    result = {'generations': {}}
    if context['scenario'].startswith('runtime-save-') or context['scenario'].startswith('runtime-transition-'):
        prefix = 'game/' if context['scenario'].startswith('runtime-transition-') else ''
        for slot in (0, 1):
            data = host.read_fixture(directory, prefix + f'progress.{slot}.json', optional=True)
            name = f'generation-{slot}.json'
            if data:
                (evidence / name).write_bytes(data)
            result['generations'][name] = {'size': len(data) if data is not None else 0, 'sha256': digest(data) if data else None}
        require(any(v['size'] for v in result['generations'].values()), 'No retained native save generation was captured')
    if context['scenario'].startswith('runtime-study-'):
        require(type(context.get('native_process_id')) is int and context['native_process_id'] > 1, 'Native study capture requires observed host PID')
        artifacts = {}
        for name, (relative, limit) in STUDY_FILES.items():
            data = host.read_fixture(directory, relative, optional=True, limit=limit)
            if data is not None:
                (evidence / name).write_bytes(data)
            artifacts[name] = {'present': data is not None, 'size': len(data) if data is not None else 0, 'sha256': digest(data) if data is not None else None}
        result['study_artifacts'] = artifacts
        result['study_structure'] = inspect_study_artifacts(evidence, context, artifacts)
    return result


def inspect_study_artifacts(evidence: Path, context: dict, artifacts: dict) -> dict:
    """Structural decoding only; no cohort, participant or crash acceptance."""
    require(set(artifacts) == set(STUDY_FILES), 'Study file presence inventory is incomplete')
    for name, record in artifacts.items():
        path = evidence / name
        require(type(record.get('present')) is bool, 'Missing artifact presence observation')
        if record['present']:
            require(path.is_file() and path.stat().st_size == record['size'] and digest(path.read_bytes()) == record['sha256'], 'Study artifact bytes differ from capture')
            require(record['size'] <= STUDY_FILES[name][1], 'Study artifact exceeds native capture bound')
        else:
            require(not path.exists() and record.get('size') == 0 and record.get('sha256') is None, 'Absent artifact has contradictory evidence')
    scenario = context['scenario']
    if scenario == 'runtime-study-default':
        require(all(not row['present'] for row in artifacts.values()), 'Default study path produced collector files')
        return {'default_files_absent': True, 'scope': 'Synthetic structural qualification only'}
    require(artifacts['study-raw.json']['present'], 'No actual native study document was captured')
    raw = read_json(evidence / 'study-raw.json')
    registry = raw.get('registry')
    withdrawn = scenario in ('runtime-study-storage-withdraw', 'runtime-study-withdraw-reopen')
    if withdrawn:
        require(registry is None and raw.get('records') == [] and raw.get('status') == 'withdrawn', 'Native erasure tombstone is incomplete')
        require(not artifacts['study-eligibility.json']['present'] and artifacts['study-withdrawn.marker']['present'], 'Native withdrawal sidecar state is incorrect')
        study_adjudicate.decode_records(raw, None, 0)
        return {'withdrawal_tombstone_verified': True, 'scope': 'Synthetic structural qualification only'}
    require(isinstance(registry, dict) and registry.get('synthetic') is True and registry.get('acquisition') == 'internal_test', 'Refusing non-synthetic study data')
    require(registry.get('baseline', {}).get('candidate_sha256') == context['candidate_fingerprint'], 'Native study configuration differs from candidate')
    require(artifacts['study-eligibility.json']['present'] and not artifacts['study-withdrawn.marker']['present'], 'Active study sidecar state is incorrect')
    wrapper = {'schema_version': 1, 'raw': raw, 'eligibility_evidence': read_json(evidence / 'study-eligibility.json')}
    study_adjudicate.wrapper_evidence(wrapper, {registry['install_id']: registry})
    cutoff = max(event['at'] for event in raw['records'])
    sessions, gaps, erased = study_adjudicate.decode_records(raw, registry, cutoff)
    require(not erased and not any(event['kind'] == 'terminal' for event in raw['records']), 'Unobserved terminal or erasure in active fixture')
    if 'native_process_id' in context:
        require(raw.get('schema_version') == 2, 'Current native fixture requires schema2 context')
        starts = [r for r in raw['records'] if r['kind'] == 'app_start']
        require(bool(starts) and not native_observation_errors(starts[-1]['payload'].get('native_context'), context['platform'], context['native_process_id']), 'Captured raw context differs from host native process')
    if scenario == 'runtime-study-capacity':
        require(len(raw['records']) <= 8 and artifacts['study-raw.json']['size'] <= 32768 and raw['status'] == 'exhausted' and raw['records'][-1]['payload']['reason'] == 'capacity', 'Native capacity evidence differs from reported bound')
    return {'records': len(raw['records']), 'logical_processes': len({r['process_id'] for r in raw['records']}),
            'decoded_sessions': len(sessions), 'gaps': len(gaps), 'scope': 'Synthetic structural qualification only; no native crash adjudication or cohort acceptance'}


def source_differences(candidate: Path, production: dict) -> list[str]:
    return [p for p, sha in production.items() if not (candidate / 'workspace' / p).is_file()
            or digest((candidate / 'workspace' / p).read_bytes()) != sha]


def run(args) -> int:
    platform = validate_request(args.device, args.label, args.scenario, args.run_id)
    observe_privacy = getattr(args, 'observe_privacy', False)
    require(not observe_privacy or args.scenario in ('runtime-study-default', 'runtime-study-enroll'), 'Privacy observation only allowed for default/enroll cases')
    require(bool(args.predecessor) == (args.scenario in PREDECESSORS), 'Supply predecessor exactly for recovery/reopen scenarios')
    candidate = args.candidate.resolve()
    manifest = read_json(candidate / 'manifest.json')
    require(build_native.source_hashes(candidate / 'source') == manifest['source_sha256']
            and build_native.fingerprint(manifest['source_sha256']) == manifest['source_fingerprint'], 'Frozen candidate differs from manifest')
    production = verify_native.production_inputs(manifest['source_sha256'])
    harness_path = ROOT / 'game/mobile/integration_test/current_runtime_test.dart'
    require(harness_path.is_file(), 'Harness is still staged; lead must release analysis window and install reviewed source first')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    name = 'current-runtime-' + args.label + '-' + stamp
    context = {'verification_id': name, 'candidate_fingerprint': manifest['source_fingerprint'], 'harness_sha256': digest(harness_path.read_bytes()),
               'device': args.device, 'label': args.label, 'platform': platform, 'scenario': args.scenario, 'run_id': args.run_id}
    prior = validate_predecessor(args.predecessor.resolve(), context) if args.predecessor else None
    with (candidate / '.native-verification.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not source_differences(candidate, production), 'Candidate workspace production source differs')
        evidence = ROOT / 'release/native-proof' / name
        evidence.mkdir()
        sources = {'runner.py': Path(__file__), 'harness.dart': harness_path, 'driver.dart': ROOT / 'tool/native_integration_driver.dart',
                   'build_native.py': Path(build_native.__file__), 'verify_native.py': Path(verify_native.__file__),
                   'study_adjudicate.py': Path(study_adjudicate.__file__), 'study_report.py': Path(study_report.__file__),
                   'study_native_diagnostics.py': Path(study_native_diagnostics.__file__)}
        for dest, source in sources.items():
            shutil.copy2(source, evidence / dest)
        pins = {dest: digest((evidence / dest).read_bytes()) for dest in sources}
        app = candidate / 'workspace/game/mobile'
        target = app / 'integration_test' / ('current_evidence_' + context['harness_sha256'][:12] + '_test.dart')
        driver = app / 'test_driver' / ('current_evidence_' + pins['driver.dart'][:12] + '.dart')
        target.parent.mkdir(exist_ok=True)
        driver.parent.mkdir(exist_ok=True)
        shutil.copy2(evidence / 'harness.dart', target)
        shutil.copy2(evidence / 'driver.dart', driver)
        command = [str(ROOT / 'tool/flutter'), 'drive', '--driver=' + str(driver.relative_to(app)), '--target=' + str(target.relative_to(app)), '-d', args.device]
        for key, value in [('DEVICE_LABEL', args.label), ('SCENARIO', args.scenario), ('RUN_ID', args.run_id), ('VERIFICATION_ID', name),
                           ('CANDIDATE_FINGERPRINT', context['candidate_fingerprint']), ('HARNESS_SHA256', context['harness_sha256'])]:
            command.append('--dart-define=TIDEGLASS_' + key + '=' + value)
        if observe_privacy:
            command.append('--dart-define=TIDEGLASS_PRIVACY_OBSERVATION=true')
        command += ['--keep-app-running', '--timeout=180', '--no-pub']
        report = dict(context, privacy_observation_enabled=observe_privacy, command=command, candidate_path=str(candidate), status='failed', passed=False, verification_errors=[],
                      provenance='INTERNAL SYNTHETIC QUALIFICATION ONLY; simulator native execution; no participant, crash-free metric, physical power-loss, store, or receiving-app claim')
        if prior:
            report['predecessor'] = {'path': str(args.predecessor.resolve()), 'sha256': digest(args.predecessor.read_bytes()), 'verification_id': prior['verification_id']}
        errors = report['verification_errors']
        process = None
        host = None
        print('Evidence: ' + str(evidence), flush=True)
        try:
            with (evidence / 'run.log').open('w') as log:
                process = subprocess.Popen(command, cwd=app, env=dict(os.environ, TIDEGLASS_NATIVE_EVIDENCE=str(evidence)), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                deadline = time.monotonic() + 300
                killed = False
                host = None
                while process.poll() is None:
                    content = (evidence / 'run.log').read_text(errors='replace')
                    if args.scenario in KILLED and MARKER.search(content) and not killed:
                        marker = marker_from_log(content, context)
                        host = NativeHost(context)
                        native_dir = str(Path(marker['checkpoint']).parent)
                        require(Path(marker['checkpoint']).name == 'checkpoint.json', 'Unexpected native checkpoint filename')
                        raw = host.read_fixture(native_dir, 'checkpoint.json', limit=65536)
                        require(digest(raw) == marker['checkpoint_sha256'], 'Checkpoint differs from native marker')
                        validate_checkpoint(raw, context, marker['process_id'])
                        (evidence / 'checkpoint.json').write_bytes(raw)
                        report.update(checkpoint_sha256=digest(raw), native_process_id=marker['process_id'], kill_marker=marker,
                                      fixture_directory=native_dir)
                        report['native_kill'] = {}
                        host.kill(marker['process_id'], report['native_kill'], before_signal=lambda ledger: bind_pre_kill_prefix((evidence / 'run.log').read_bytes(), context, evidence, ledger))
                        report.update(archive_fixture(host, native_dir, report, evidence))
                        killed = True
                        deadline = time.monotonic() + 45
                    if time.monotonic() >= deadline:
                        require(killed, 'Native test/marker timeout')
                        # Only the host driver process group we created; native kill already independently observed.
                        report['driver_cleanup_after_expected_kill'] = True
                        os.killpg(process.pid, signal.SIGTERM)
                        break
                    time.sleep(.2)
                try:
                    report['exit_code'] = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    report['exit_code'] = process.wait(timeout=10)
            content = (evidence / 'run.log').read_text(errors='replace')
            if args.scenario in KILLED:
                errors.extend(interrupted_errors(content, context, report.get('kill_marker', {}), report.get('native_kill', {}), (evidence / 'run.log').read_bytes()))
                if not errors:
                    report['status'] = 'expected-interrupted'
            else:
                payload = read_json(evidence / 'result.json')
                errors.extend(verify_native.native_log_errors(content))
                errors.extend(payload_errors(payload, context, prior))
                if report['exit_code'] != 0:
                    errors.append('Native driver exit code was nonzero')
                if not errors:
                    host = NativeHost(context)
                    report['native_process_id'] = payload['process_id']
                    report['native_process_stop'] = host.stop(payload['process_id'])
                    require(report['native_process_stop']['termination_observed'], 'Native process stop not observed')
                    if args.scenario in set(PREDECESSORS.values()) or args.scenario in PREDECESSORS:
                        raw = host.read_fixture(payload['fixture_directory'], 'checkpoint.json', limit=65536)
                        if prior:
                            require(digest(raw) == prior['checkpoint_sha256'], 'Recovery changed predecessor checkpoint')
                        else:
                            validate_checkpoint(raw, context, payload['process_id'])
                            require(payload.get('checkpoint_sha256') == digest(raw), 'Driver checkpoint hash mismatch')
                        (evidence / 'checkpoint.json').write_bytes(raw)
                        report['checkpoint_sha256'] = digest(raw)
                    report.update(archive_fixture(host, payload.get('fixture_directory', ''), report, evidence))
                    report['status'] = 'passed'
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
            errors.append(type(error).__name__ + ': ' + str(error))
        finally:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            if host is not None:
                report['host_observations'] = host.observations
            report['production_input_differences_after_run'] = source_differences(candidate, production)
            report['source_snapshot_unchanged'] = build_native.source_hashes(candidate / 'source') == manifest['source_sha256']
            report['source_pins'] = pins
            report['source_changes_during_run'] = [dest for dest, source in sources.items() if not source.is_file() or digest(source.read_bytes()) != pins[dest]]
            if report['production_input_differences_after_run'] or not report['source_snapshot_unchanged'] or report['source_changes_during_run']:
                errors.append('Source integrity changed during native verification')
            if prior and digest(args.predecessor.read_bytes()) != report['predecessor']['sha256']:
                errors.append('Predecessor report changed during recovery')
            if errors:
                report['status'] = 'failed'
            report['passed'] = report['status'] == 'passed'
            report['evidence_sha256'] = {p.name: digest(p.read_bytes()) for p in evidence.iterdir() if p.is_file()}
            (evidence / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(report['status'] + ': ' + str(evidence / 'verification.json'), flush=True)
        return 0 if report['status'] in ('passed', 'expected-interrupted') else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--device', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--scenario', required=True, choices=sorted(SCENARIOS))
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--predecessor', type=Path)
    parser.add_argument('--observe-privacy', action='store_true', help='Optional bounded default/enroll observation window; separate collector required')
    args = parser.parse_args()
    return run(args)


if __name__ == '__main__':
    sys.exit(main())

