#!/usr/bin/env python3
"""Real OS reminder qualification on an explicitly selected disposable simulator.

No permission grants, revocations, booting, resets, or UI automation are hidden
here. Operate the OS prompt/settings/home UI only after the identity-bound action
is printed. Failed/unsupported delivery remains failed, never a skipped pass.
"""
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
import time

import build_native
import verify_native

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = 'dev.tideglass.game'
PROTECTED_DEVICE = 'F103390E-7B7C-4F0B-9404-5E029C7131FF'
SCENARIOS = frozenset({'default', 'denied', 'quiet-cancel', 'delivery', 'revoked'})
HEX = re.compile(r'^[a-f0-9]{64}$')
SAFE = re.compile(r'^[A-Za-z0-9_-]{1,80}$')
MARKER = re.compile(r'^(?:flutter:|I/flutter\s*\(\s*\d+\):)\s*TIDEGLASS_REMINDER_ACTION (\{[^\n]+\})\s*$', re.M)
IDENTITY = ('verification_id', 'candidate_fingerprint', 'harness_sha256', 'scenario', 'run_id', 'device_label', 'platform')
ACTIONS = {
    'default': [],
    'denied': ['deny_permission_if_prompted'],
    'quiet-cancel': ['allow_permission_if_prompted'],
    'delivery': ['allow_permission_if_prompted', 'background_app_now_using_os_home', 'wait_until_due_then_return_via_app_icon'],
    'revoked': ['allow_permission_if_prompted', 'revoke_in_os_settings_then_return_via_app_icon', 'deny_permission_again_if_prompted'],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_request(device, label, scenario, run_id):
    require(device.upper() != PROTECTED_DEVICE, 'Protected tablet is never an execution target')
    require(bool(SAFE.fullmatch(label)) and bool(SAFE.fullmatch(run_id)), 'Explicit safe label and fresh run ID required')
    require(scenario in SCENARIOS, 'Reminder scenario is not allowlisted')
    if re.fullmatch(r'emulator-[0-9]+', device):
        return 'android'
    require(bool(re.fullmatch(r'[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}', device)), 'Simulator/emulator identifier required')
    return 'ios'


def call(command, timeout=30):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, 'OS observation failed: ' + repr(command) + '\n' + result.stderr[-1500:])
    return result.stdout


def device_ready(device, platform):
    if platform == 'android':
        require(call([str(ROOT / '.tooling/android-sdk/platform-tools/adb'), '-s', device, 'get-state']).strip() == 'device', 'Emulator must already be ready')
    else:
        data = json.loads(call(['xcrun', 'simctl', 'list', 'devices', '--json']))
        matches = [d for items in data['devices'].values() for d in items if d['udid'].upper() == device.upper()]
        require(len(matches) == 1 and matches[0]['state'] == 'Booted' and matches[0]['isAvailable'] is True, 'Selected available simulator must already be booted')


def payload_errors(payload, context, log):
    errors = []
    def check(condition, message):
        if not condition:
            errors.append(message)
    if not isinstance(payload, dict):
        return ['Result is not an object']
    for key in IDENTITY:
        check(type(payload.get(key)) is type(context[key]) and payload.get(key) == context[key], 'Identity mismatch: ' + key)
    for key, value in {'completed': True, 'gateway': 'NativeNotificationGateway',
                       'preference_store': 'FileNotificationPreferences',
                       'fixture_kind': 'SYNTHETIC GAMEPLAY SNAPSHOT; REAL OS NOTIFICATION API',
                       'clock': 'actual_utc_and_monotonic_stopwatch', 'default_opted_out': True,
                       'default_preferences_file_absent': True, 'default_pending_ids': []}.items():
        check(type(payload.get(key)) is type(value) and payload.get(key) == value, 'Missing actual evidence: ' + key)
    native_pid = payload.get('process_id')
    check(type(native_pid) is int and native_pid > 1, 'Real native process ID required')
    before = payload.get('permission_before_initialize')
    check(before in {'allowed', 'denied'} and payload.get('permission_after_initialize') == before, 'Initialization changed OS permission or was unsupported')
    events = payload.get('lifecycle_events')
    check(isinstance(events, list) and all(isinstance(e, dict) and set(e) == {'state', 'utc_ms'} and e['state'] in {'resumed', 'inactive', 'hidden', 'paused', 'detached'} and type(e['utc_ms']) is int for e in events), 'Invalid actual lifecycle observations')
    init_events = payload.get('initialization_lifecycle_events')
    check(isinstance(init_events, list) and all(isinstance(e, dict) and e.get('state') == 'resumed' for e in init_events), 'Default initialization left foreground or lacks observation')
    recorded_actions = payload.get('actions')
    try:
        markers = [json.loads(x) for x in MARKER.findall(log)]
    except (TypeError, ValueError):
        return errors + ['Malformed native action log']
    scenario = context['scenario']
    check(isinstance(recorded_actions, list) and markers == recorded_actions, 'Native action log/result mismatch')
    if any(not isinstance(x, dict) for x in markers):
        return errors + ['Native action is not an object']
    check([x.get('action') for x in markers] == ACTIONS[scenario], 'Missing, repeated or out-of-order native OS action')
    for row in markers:
        check(all(row.get(k) == context[k] for k in IDENTITY) and row.get('process_id') == native_pid and type(row.get('utc_ms')) is int, 'Native OS action identity mismatch')
    if scenario != 'default':
        permission = 'denied' if scenario == 'denied' else 'allowed'
        check(payload.get('permission_after_opt_in') == permission, 'Actual opt-in permission not observed')
        prefs = payload.get('preferences_after_opt_in')
        check(isinstance(prefs, dict) and prefs.get('enabled') is (scenario != 'denied'), 'File preference did not preserve actual opt-in result')
        check(bool(HEX.fullmatch(str(payload.get('preferences_sha256', '')))), 'Missing native preferences file hash')
    if scenario == 'denied':
        check(payload.get('denied_pending_ids') == [], 'Denied scenario retained requests')
    if scenario in {'quiet-cancel', 'delivery', 'revoked'}:
        plan = payload.get('plan', {})
        check(isinstance(plan, dict), 'Missing actual scheduled plan')
        if not isinstance(plan, dict):
            plan = {}
        check(plan.get('ids') == [77101] and plan.get('kinds') == ['focus'] and plan.get('production_lifecycle') is True, 'Plan is not exact production lifecycle/Focus request')
        check(isinstance(plan.get('body'), str) and bool(plan.get('body')), 'Missing exact notification body')
        check(bool(HEX.fullmatch(str(plan.get('saved_payload_sha256', '')))) and isinstance(plan.get('saved_snapshot_id'), str) and bool(plan.get('saved_snapshot_id')), 'Missing actual durable save identity')
        for key in ('scheduled_observed_utc_ms', 'due_utc_ms', 'settled_through_utc_ms', 'background_call_utc_ms'):
            check(type(plan.get(key)) is int and plan.get(key, 0) > 0, 'Missing actual plan timestamp: ' + key)
        if all(type(plan.get(k)) is int for k in ('due_utc_ms', 'background_call_utc_ms')):
            check(plan['due_utc_ms'] - plan['background_call_utc_ms'] >= 300000, 'Production five-minute minimum was bypassed')
        if scenario == 'quiet-cancel':
            quiet = payload.get('quiet_window', {})
            check(isinstance(quiet, dict) and type(quiet.get('end_minute')) is int and quiet.get('end_minute') == payload.get('quiet_due_local_minute'), 'Quiet window did not defer actual plan to its end')
            check(payload.get('return_pending_ids') == [], 'Return did not cancel actual queued request')
        if scenario == 'revoked':
            check(payload.get('permission_after_revoke') == 'denied' and payload.get('revoked_opt_in_stays_disabled') is True and payload.get('revoke_pending_ids') == [], 'Actual revocation/denial/cancellation not observed')
            check(actual_departure_return(events, markers, 'revoke_in_os_settings_then_return_via_app_icon', 0), 'No actual Settings departure and return')
        if scenario == 'delivery':
            check(payload.get('actual_background_and_return') is True, 'Delivery lacks actual background and return')
            check(actual_departure_return(events, markers, 'background_app_now_using_os_home', plan.get('due_utc_ms')), 'No native background/resume callbacks after OS action and due time')
            check(payload.get('return_pending_ids') == [] and payload.get('return_active_ids') == [], 'Return did not cancel scheduled/delivered notifications')
            delivered = payload.get('delivered_records')
            check(isinstance(delivered, list) and any(isinstance(d, dict) and d.get('id') == 77101 and d.get('body') == plan.get('body') for d in delivered), 'Scheduled requests are not delivered OS notifications')
            times = [payload.get(k) for k in ('returned_utc_ms', 'returned_elapsed_ms', 'scheduled_elapsed_ms')]
            check(all(type(x) is int for x in times), 'Missing actual wall/monotonic delivery observation')
            if all(type(x) is int for x in times) and type(plan.get('due_utc_ms')) is int and type(plan.get('scheduled_observed_utc_ms')) is int:
                check(times[0] >= plan['due_utc_ms'], 'Returned before real due time')
                check(times[1] - times[2] >= plan['due_utc_ms'] - plan['scheduled_observed_utc_ms'] >= 290000, 'Real elapsed production-minimum window not observed')
    errors.extend(verify_native.native_log_errors(log))
    return errors


def actual_departure_return(events, markers, action, earliest):
    if not isinstance(events, list) or type(earliest) is not int:
        return False
    starts = [x.get('utc_ms') for x in markers if x.get('action') == action]
    if len(starts) != 1 or type(starts[0]) is not int:
        return False
    departed = False
    for e in events:
        if not isinstance(e, dict) or type(e.get('utc_ms')) is not int:
            return False
        if e['utc_ms'] < starts[0]:
            continue
        if e.get('state') == 'paused':
            departed = True
        if e.get('state') == 'resumed' and departed and e['utc_ms'] >= earliest:
            return True
    return False


def production_differences(workspace, production):
    return [p for p, digest in production.items() if not (workspace / p).is_file() or sha(workspace / p) != digest]


def artifact_inputs(app, platform):
    if platform == 'android':
        apk = app / 'build/app/outputs/flutter-apk/app-debug.apk'
        return {str(apk): sha(apk)} if apk.is_file() else {}
    bundle = app / 'build/ios/iphonesimulator/Runner.app'
    return {str(p): sha(p) for p in sorted(bundle.rglob('*')) if p.is_file()}


def installed_artifact_check(app, platform, device, expected):
    require(bool(expected), 'Actual built native artifact missing')
    if platform == 'android':
        adb = str(ROOT / '.tooling/android-sdk/platform-tools/adb')
        paths = call([adb, '-s', device, 'shell', 'pm', 'path', BUNDLE]).splitlines()
        require(len(paths) == 1 and paths[0].startswith('package:/data/app/') and '..' not in paths[0] and not re.search(r'\s', paths[0]), 'Unexpected installed APK identity')
        path = paths[0].removeprefix('package:')
        digest = call([adb, '-s', device, 'shell', 'sha256sum', path]).split()[0]
        require(bool(HEX.fullmatch(digest)) and digest == next(iter(expected.values())), 'Installed APK differs from actual built artifact')
        return {'installed_path': path, 'sha256': digest, 'matches_host_artifact': True}
    installed = Path(call(['xcrun', 'simctl', 'get_app_container', device, BUNDLE, 'app']).strip())
    require(installed.is_absolute() and installed.name.endswith('.app') and installed.is_dir(), 'Actual simulator app container required')
    bundle = app / 'build/ios/iphonesimulator/Runner.app'
    differences = [str(Path(p).relative_to(bundle)) for p, digest in expected.items()
                   if not (installed / Path(p).relative_to(bundle)).is_file()
                   or sha(installed / Path(p).relative_to(bundle)) != digest]
    require(not differences, 'Installed app differs from built artifact: ' + str(differences))
    return {'installed_path': str(installed), 'checked_files': len(expected), 'matches_host_artifact': True}


def finish_observations(report, errors, *, candidate, frozen, workspace, production,
                        sources, pins, target, driver, platform, device):
    """Retain failures even when a post-run file disappears or OS stop times out."""
    def observe(name, operation):
        try:
            value = operation()
            report[name] = value
            return value
        except Exception as error:
            report[name] = {'observation_error': type(error).__name__, 'message': str(error)[:1500]}
            errors.append('Final observation failed: ' + name + ': ' + type(error).__name__)
            return None
    differences = observe('production_differences_after', lambda: production_differences(workspace, production))
    frozen_same = observe('frozen_source_unchanged', lambda: build_native.source_hashes(candidate / 'source') == frozen)
    changed = observe('source_differences_during_run', lambda: [name for name, path in sources.items()
                      if not path.is_file() or sha(path) != pins[name]])
    copies_same = observe('generated_harness_matches', lambda: target.is_file() and driver.is_file()
                          and sha(target) == pins['harness.dart'] and sha(driver) == pins['driver.dart'])
    if differences != [] or frozen_same is not True or changed != [] or copies_same is not True:
        errors.append('Production, frozen source or runner/harness input changed during run')
    # No permission modification or erase. A failed/crashed test may leave its
    # own pending reminders; never assert teardown cleanup from process stop.
    stop = ['xcrun', 'simctl', 'terminate', device, BUNDLE] if platform == 'ios' else [
        str(ROOT / '.tooling/android-sdk/platform-tools/adb'), '-s', device, 'shell', 'am', 'force-stop', BUNDLE]
    def stop_app():
        stopped = subprocess.run(stop, capture_output=True, text=True, timeout=20)
        return {'command': stop, 'exit_code': stopped.returncode, 'stderr': stopped.stderr[-1000:]}
    stopped = observe('stop', stop_app)
    if stopped is None or stopped['exit_code'] != 0:
        errors.append('Exact test application process stop was not confirmed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--device', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--scenario', required=True, choices=sorted(SCENARIOS))
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    platform = validate_request(args.device, args.label, args.scenario, args.run_id)
    candidate = args.candidate.resolve()
    manifest = json.loads((candidate / 'manifest.json').read_text())
    frozen = build_native.source_hashes(candidate / 'source')
    require(frozen == manifest['source_sha256'] and build_native.fingerprint(frozen) == manifest['source_fingerprint'], 'Frozen candidate identity mismatch')
    with (candidate / '.native-verification.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        workspace = candidate / 'workspace'; app = workspace / 'game/mobile'
        production = verify_native.production_inputs(frozen)
        require(not production_differences(workspace, production), 'Candidate production workspace differs from frozen source')
        device_ready(args.device, platform)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        evidence = ROOT / 'release/native-notifications' / ('integration-' + args.label + '-' + stamp)
        evidence.mkdir(parents=True)
        sources = {'harness.dart': ROOT / 'game/mobile/integration_test/native_reminders_test.dart',
                   'driver.dart': ROOT / 'tool/native_integration_driver.dart',
                   'verify_native_reminders.py': Path(__file__),
                   'verify_native.py': Path(verify_native.__file__),
                   'build_native.py': Path(build_native.__file__)}
        pins = {}
        for name, path in sources.items():
            shutil.copyfile(path, evidence / name); pins[name] = sha(evidence / name)
        (evidence / 'candidate-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        target = app / 'integration_test' / ('reminders_' + pins['harness.dart'][:16] + '_test.dart')
        driver = app / 'test_driver' / ('reminders_' + pins['driver.dart'][:16] + '.dart')
        driver.parent.mkdir(exist_ok=True)
        # Test copies only; never delete unrelated existing harnesses or data.
        shutil.copyfile(evidence / 'harness.dart', target); shutil.copyfile(evidence / 'driver.dart', driver)
        context = {'verification_id': evidence.name, 'candidate_fingerprint': manifest['source_fingerprint'],
                   'harness_sha256': pins['harness.dart'], 'scenario': args.scenario, 'run_id': args.run_id,
                   'device_label': args.label, 'platform': platform}
        command = [str(ROOT / 'tool/flutter'), 'drive', '--driver=' + str(driver.relative_to(app)),
                   '--target=' + str(target.relative_to(app)), '-d', args.device,
                   *['--dart-define=TIDEGLASS_' + key + '=' + value for key, value in {
                       'DEVICE_LABEL': args.label, 'SCENARIO': args.scenario, 'RUN_ID': args.run_id,
                       'VERIFICATION_ID': evidence.name, 'CANDIDATE_FINGERPRINT': manifest['source_fingerprint'],
                       'HARNESS_SHA256': pins['harness.dart']}.items()],
                   '--keep-app-running', '--timeout=1000', '--no-pub']
        report = {**context, 'device': args.device, 'source_pins': pins, 'command': command,
                  'production_inputs_before': production, 'artifact_before': artifact_inputs(app, platform),
                  'provenance': 'Real OS plugin with synthetic isolated gameplay state; simulator/emulator only; OS UI operated separately; no automatic permission changes.',
                  'passed': False}
        (evidence / 'started.json').write_text(json.dumps(report, indent=2) + '\n')
        print('Reminder evidence: ' + str(evidence), flush=True)
        errors = []; process = None
        try:
            with (evidence / 'run.log').open('w') as log_file:
                process = subprocess.Popen(command, cwd=app, env=dict(os.environ, TIDEGLASS_NATIVE_EVIDENCE=str(evidence)),
                                           stdout=log_file, stderr=subprocess.STDOUT, start_new_session=True)
                start = time.monotonic(); shown = 0
                while process.poll() is None:
                    time.sleep(0.5)
                    text = (evidence / 'run.log').read_text(errors='replace')
                    matches = MARKER.findall(text)
                    for marker in matches[shown:]:
                        value = json.loads(marker)
                        require(all(value.get(k) == context[k] for k in IDENTITY), 'Live action identity mismatch')
                        print('OS ACTION ' + json.dumps(value, sort_keys=True), flush=True)
                    shown = len(matches)
                    require(time.monotonic() - start < 1200, 'Native qualification exceeded20-minute bound')
                report['exit_code'] = process.returncode
            log = (evidence / 'run.log').read_text(errors='replace')
            result_path = evidence / 'result.json'
            payload = json.loads(result_path.read_text()) if result_path.is_file() else {}
            errors.extend(payload_errors(payload, context, log))
            if process.returncode != 0: errors.append('Native driver exited unsuccessfully')
            report['artifact_after'] = artifact_inputs(app, platform)
            report['installed_artifact'] = installed_artifact_check(app, platform, args.device, report['artifact_after'])
        except BaseException as error:
            errors.append(type(error).__name__ + ': ' + str(error))
        finally:
            try:
                if process is not None and process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try: process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=10)
            except Exception as error:
                report['driver_stop_error'] = type(error).__name__ + ': ' + str(error)
                errors.append('Native driver cleanup was not confirmed')
            finish_observations(report, errors, candidate=candidate, frozen=frozen,
                workspace=workspace, production=production, sources=sources, pins=pins,
                target=target, driver=driver, platform=platform, device=args.device)
            report['errors'] = errors
            output_pins = {}
            for path in evidence.iterdir():
                if path.is_file():
                    try:
                        output_pins[path.name] = sha(path)
                    except Exception as error:
                        errors.append('Evidence hashing failed: ' + path.name + ': ' + type(error).__name__)
            report['evidence_sha256'] = output_pins
            report['passed'] = not errors
            (evidence / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'evidence': str(evidence), 'passed': report['passed'], 'errors': errors}), flush=True)
        return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
