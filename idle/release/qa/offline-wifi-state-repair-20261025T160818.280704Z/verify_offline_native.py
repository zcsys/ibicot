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
import re
import shutil
import subprocess
import sys
STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
sys.path.insert(0, str(ROOT / 'tool'))
import build_native
import native_recording
import offline_support




def production_inputs(files: dict[str, str]) -> dict[str, str]:
    """Include native entrypoints/config and locks, not only Dart libraries."""
    generated = {'GeneratedPluginRegistrant.java', 'GeneratedPluginRegistrant.m',
                 'GeneratedPluginRegistrant.h', 'GeneratedPluginRegistrant.swift',
                 'generated_plugin_registrant.cc', 'generated_plugin_registrant.h',
                 'generated_plugins.cmake'}
    return {path: digest for path, digest in files.items()
            if Path(path).name not in generated and
            (path.startswith('game/content/') or path == 'economy.json'
             or (path.startswith('game/') and ('/lib/' in path or '/assets/' in path
                 or Path(path).name in {'pubspec.yaml', 'pubspec.lock'}))
             or path.startswith(('game/mobile/android/', 'game/mobile/ios/', 'game/mobile/macos/')))}


def native_platform(device: str, supplied: str | None) -> str:
    if supplied:
        return supplied
    if device.startswith('emulator-'):
        return 'android'
    if re.fullmatch(r'[A-Fa-f0-9]{8}(?:-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12}', device):
        return 'ios'
    raise ValueError('Specify --platform for a non-simulator device identifier')


def native_log_errors(log_text: str) -> list[str]:
    errors = []
    native_prefix = r'(?:flutter:|I/flutter\s*\(\s*\d+\):)'
    for marker in ['BUILD FAILED', 'Failed to build', 'Could not build the application',
                   'Application failed to start', 'Some tests failed.',
                   'EXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK',
                   'One or more uncaught errors occurred']:
        if marker in log_text:
            errors.append('Native build/test failure in log: ' + marker)
    if re.search(r'^' + native_prefix + r'.*\s\[E\](?:\s|$)', log_text, re.MULTILINE):
        errors.append('Native test or teardown error marker in log')
    # Dart reports late asynchronous failures outside test-runner status lines.
    # Anchor to actual stderr/native logging forms so quoted UI text is harmless.
    error_prefix = r'(?:flutter:|[IE]/flutter\s*\(\s*\d+\):)'
    uncaught = (r'^(?:' + error_prefix + r'\s*)?'
                r'(?:\[ERROR:flutter/[^\]\n]+\]\s*)?'
                r'(?:Unhandled Exception|Uncaught (?:Exception|Error)):' )
    if re.search(uncaught, log_text, re.MULTILINE):
        errors.append('Uncaught Dart/native exception in log')
    # integration_test_driver can print success and exit0 after the native test
    # body succeeds but tearDown fails. Negative evidence must take precedence.
    if not re.search(r'^' + native_prefix + r'\s+\d+(?::\d+){1,2}\s+\+[1-9]\d*:\s+All tests passed!\s*$',
                     log_text, re.MULTILINE):
        errors.append('No successful native framework completion marker')
    if not re.search(r'^All tests passed\.\s*$', log_text, re.MULTILINE):
        errors.append('No successful driver completion marker')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--device', required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--platform', choices=['ios', 'android'])
    parser.add_argument('--scenario', choices=['natural-start', 'natural-reload'], required=True)
    parser.add_argument('--run-id', default='')
    parser.add_argument('--network-profile', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path)
    args = parser.parse_args()
    if args.platform != 'android' or args.device != offline_support.DEVICE:
        parser.error('This staged qualification admits only emulator-5556 / Android API35')
    if (args.scenario == 'natural-reload') != (args.predecessor is not None):
        parser.error('Only reload requires an exact successful predecessor report')
    profile = offline_support.read_profile(args.network_profile, args.run_id, args.device,
        offline_support.digest(STAGE / 'platform_smoke_offline_test.dart'))
    predecessor = offline_support.load_predecessor(args.predecessor, args, profile) if args.predecessor else None
    platform = native_platform(args.device, args.platform)
    if not args.label.replace('-', '').replace('_', '').isalnum():
        parser.error('Label may contain only letters, digits, underscores and hyphens')
    candidate = args.candidate.resolve()
    manifest = json.loads((candidate / 'manifest.json').read_text())
    frozen = build_native.source_hashes(candidate / 'source')
    if frozen != manifest['source_sha256'] or build_native.fingerprint(frozen) != manifest['source_fingerprint']:
        raise RuntimeError('Frozen candidate no longer matches its manifest')
    if manifest['source_fingerprint'] != offline_support.CANDIDATE:
        raise ValueError('Wrong frozen candidate')
    app = candidate / 'workspace/game/mobile'
    candidate_lock = (candidate / '.native-verification.lock').open('w')
    fcntl.flock(candidate_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    production = production_inputs(manifest['source_sha256'])
    mismatches = [path for path, digest in production.items()
                  if not (candidate / 'workspace' / path).exists()
                  or hashlib.sha256((candidate / 'workspace' / path).read_bytes()).hexdigest() != digest]
    if mismatches:
        raise RuntimeError('Production inputs differ from frozen source: ' + ', '.join(mismatches))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    evidence = ROOT / 'release/native-proof' / ('integration-' + args.label + '-' + stamp)
    evidence.mkdir()
    shutil.copy2(Path(__file__), evidence / 'verify_native.py')
    shutil.copy2(STAGE / 'offline_support.py', evidence / 'offline_support.py')
    shutil.copy2(args.network_profile, evidence / 'network-profile.json')
    if args.predecessor:
        (evidence / 'predecessor.json').write_text(json.dumps({'path': str(args.predecessor.resolve()),
            'sha256': offline_support.digest(args.predecessor)}, indent=2) + '\n')
    if args.scenario != 'seeded' and not args.run_id:
        parser.error('Start/reload scenarios require the same explicit --run-id')
    if args.run_id and not args.run_id.replace('-', '').replace('_', '').isalnum():
        parser.error('Run id may contain only letters, digits, underscores and hyphens')
    # Test code can evolve independently while the production application input
    # remains frozen. Capture and hash this exact harness beside its evidence.
    sources = {'harness.dart': STAGE / 'platform_smoke_offline_test.dart',
               'driver.dart': ROOT / 'tool/native_integration_driver.dart'}
    if args.scenario == 'capture-gallery':
        sources.update({'native_recording.py': ROOT / 'tool/native_recording.py',
                        'native_video_metadata.swift': ROOT / 'tool/native_video_metadata.swift'})
    sources['offline_support.py'] = STAGE / 'offline_support.py'
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
               '--dart-define=TIDEGLASS_HARNESS_SHA256=' + harness_hashes['harness.dart'], '--keep-app-running', '--timeout=480', '--no-pub',
               '--dart-define=TIDEGLASS_OFFLINE_NONCE=' + profile['nonce'],
               '--dart-define=TIDEGLASS_OFFLINE_SERVER_ID=' + profile['server_id'],
               '--dart-define=TIDEGLASS_OFFLINE_PORT=' + str(profile['port']),
               '--dart-define=TIDEGLASS_PREDECESSOR_CHECKPOINT_SHA256=' + (predecessor['offline_network']['checkpoint_sha256'] if predecessor else '')]
    report = {'candidate_fingerprint': manifest['source_fingerprint'], 'device': args.device,
              'label': args.label, 'platform': platform, 'started_utc': stamp, 'command': command,
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'candidate_validation_runner_sha256': hashlib.sha256(Path(build_native.__file__).read_bytes()).hexdigest(),
              'scenario': args.scenario, 'run_id': args.run_id, 'harness_sha256': harness_hashes,
              'production_inputs_match_snapshot': not mismatches,
              'provenance': 'Real elapsed native bootstrap and separate-process reload; isolated test save directory' if args.scenario.startswith('natural-') else 'Seeded native boundary/presentation test; no natural pacing or physical-device claim'}
    if args.scenario.startswith('clock-'):
        report['provenance'] = 'Actual native clock and OS lifecycle/process scope; no paid ownership or physical-device security qualification. Epoch remains in private device checkpoint.'
    if args.scenario == 'share-cancel':
        report['provenance'] = 'Synthetic local ZIP and test-only download substitution; production export function and actual native sheet cancellation. No commerce or delivery proof.'
    if args.scenario == 'capture-gallery':
        report['provenance'] = 'Seeded production screen set and real-time UI actions in unedited silent simulator footage; no natural progression, human playtest or paid ownership claim.'
    print(f'Native checks for {args.label}; evidence: {evidence}', flush=True)
    if args.scenario == 'capture-gallery':
        recorder = native_recording.GalleryRecorder(ROOT, evidence, platform, args.device, args.label, args.run_id)
        exit_code, recording = native_recording.run_with_gallery(command, app, env, recorder)
        report['recording'] = recording
    else:
        expected = {**{key: profile[key] for key in offline_support.IDENTITY},
            'verification_id': evidence.name, 'device_label': args.label, 'scenario': args.scenario, 'platform': 'android'}
        exit_code = offline_support.run_command(command, app, env, evidence, ROOT, args, expected)
    report['exit_code'] = exit_code
    errors = []
    if args.scenario == 'capture-gallery' and not recording['passed']:
        errors.extend(recording['errors'])
    payload = json.loads((evidence / 'result.json').read_text()) if (evidence / 'result.json').is_file() else {}
    for key, expected in [('platform', platform), ('device_label', args.label), ('scenario', args.scenario), ('run_id', args.run_id), ('verification_id', evidence.name), ('candidate_fingerprint', manifest['source_fingerprint']), ('harness_sha256', harness_hashes['harness.dart'])]:
        if payload.get(key) != expected:
            errors.append(f'{key}: expected {expected!r}, received {payload.get(key)!r}')
    capture = None
    if args.scenario == 'capture-gallery' and not errors:
        try:
            capture = native_recording.capture_manifest(evidence, payload, recording, args.device)
            capture['runner_sha256'] = report['runner_sha256']
            capture['capture_helper_sha256'] = harness_hashes
        except (OSError, ValueError, KeyError) as error:
            errors.append('Capture manifest: ' + str(error))
    log_text = (evidence / 'run.log').read_text()
    errors.extend(native_log_errors(log_text))
    after_mismatches = [path for path, digest in production.items()
                        if not (candidate / 'workspace' / path).is_file()
                        or hashlib.sha256((candidate / 'workspace' / path).read_bytes()).hexdigest() != digest]
    report['production_input_differences_after_run'] = after_mismatches
    if after_mismatches:
        errors.append('Production input changed during native verification')
    report['source_snapshot_unchanged'] = build_native.source_hashes(candidate / 'source') == manifest['source_sha256']
    if not report['source_snapshot_unchanged']:
        errors.append('Frozen source changed during native verification')
    changed_harness = [name for name, source in sources.items()
                       if hashlib.sha256(source.read_bytes()).hexdigest() != harness_hashes[name]]
    report['harness_source_differences_during_run'] = changed_harness
    if changed_harness:
        errors.append('Harness or recorder helper changed while this verification was running')
    # flutter drive's default cleanup uninstalls the application and erases
    # its sandbox. Preserve installation, then perform an explicit process stop.
    if platform == 'ios':
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
    if not errors and exit_code == 0:
        try:
            report['offline_qualification'] = offline_support.finish(evidence, args, profile, predecessor)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            errors.append('Offline qualification: ' + str(error))
    report['verification_errors'] = errors
    report['passed'] = exit_code == 0 and not errors
    if capture is not None:
        capture['native_verification_passed'] = report['passed']
        (evidence / 'capture-manifest.json').write_text(json.dumps(capture, indent=2) + '\n')
    report['evidence_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence.iterdir() if p.is_file()}
    (evidence / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'{args.label}: exit {exit_code}', flush=True)
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
