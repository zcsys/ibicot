#!/usr/bin/env python3
"""Export one frozen source candidate using the project's pinned native tools."""
from __future__ import annotations

import argparse
import fcntl
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parent.parent
IGNORED_PARTS = {'.dart_tool', '.gradle', 'build', 'ephemeral', 'xcuserdata', '.symlinks', 'Pods', '__pycache__', '.git'}
IGNORED_NAMES = {'local.properties', 'Generated.xcconfig', 'flutter_export_environment.sh', '.flutter-plugins-dependencies', '.DS_Store'}


def input_files(root: Path):
    for folder in ['game', 'tool', 'services', 'tests/services', 'source/schemas', 'implementation/contracts', 'implementation/fixtures', 'implementation/content', 'implementation/tools', 'docs/decisions', 'docs/quality']:
        base = root / folder
        if base.exists():
            for file in sorted(base.rglob('*')):
                relative = file.relative_to(root)
                if relative.parts[:3] == ('game', 'qa', 'workspaces'):
                    continue
                if file.is_file() and not IGNORED_PARTS.intersection(relative.parts) and file.name not in IGNORED_NAMES:
                    yield relative
    if (root / 'economy.json').exists():
        yield Path('economy.json')


def source_hashes(root: Path) -> dict[str, str]:
    return {str(file): hashlib.sha256((root / file).read_bytes()).hexdigest() for file in input_files(root)}


def fingerprint(files: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def native_build_command(wrapper: str, target: str, mode: str) -> list[str]:
    release = mode == 'release'
    commands = {
        'ios': ['build', 'ios', '--release', '--no-codesign'] if release else ['build', 'ios', '--simulator', '--debug', '--no-codesign'],
        'android': ['build', 'appbundle', '--release'] if release else ['build', 'apk', '--debug'],
        'macos': ['build', 'macos', '--' + mode],
    }
    # Flutter 3.47.7 couples release plugin registration to its pub step.
    # --no-pub leaves the debug integration_test Java registrant in place even
    # though Gradle excludes that dev dependency from release. Resolve the lock
    # first, let the SDK generate its mode-specific registrant, then verify every
    # captured dependency lock is unchanged. Never hand-edit generated plugins.
    return [wrapper, *commands[target], *([] if release and target == 'android' else ['--no-pub'])]


def snapshot(stamp: str, evidence: Path) -> tuple[Path, dict]:
    """Reject a changing copy; freeze the reviewed source separately from build outputs."""
    staging = ROOT / '.tooling/build-candidates' / (stamp + '-copying')
    staging.mkdir(parents=True, exist_ok=False)
    for attempt in range(3):
        files = source_hashes(ROOT)
        source = staging / 'source'
        source.mkdir()
        for relative in files:
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        if source_hashes(ROOT) == files and source_hashes(source) == files:
            break
        shutil.rmtree(source)
    else:
        shutil.rmtree(staging)
        raise RuntimeError('Source changed during all three snapshot attempts; no mixed candidate was built')
    digest = fingerprint(files)
    candidate = staging.with_name(stamp + '-' + digest[:12])
    staging.rename(candidate)
    source = candidate / 'source'
    workspace = candidate / 'workspace'
    shutil.copytree(source, workspace)
    # Builds may generate project files, but cannot mutate the frozen original.
    for file in source.rglob('*'):
        if file.is_file():
            file.chmod(file.stat().st_mode & ~0o222)
    manifest = {'snapshot_utc': stamp, 'source_fingerprint': digest,
                'candidate_directory': str(candidate), 'source_directory': str(source),
                'workspace_directory': str(workspace), 'source_sha256': files,
                'sdk_wrapper': str(ROOT / 'tool/flutter'),
                'note': 'Source is frozen. Build-generated files live only in the separate workspace. Concurrent working-tree edits are not included.'}
    (candidate / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (evidence / 'candidate-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    artifacts = evidence / 'artifacts'
    artifacts.mkdir()
    with tarfile.open(artifacts / 'candidate-source.tar.gz', 'w:gz') as archive:
        archive.add(source, arcname='source')
    return candidate, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('targets', nargs='*', choices=['ios', 'android', 'macos'])
    parser.add_argument('--snapshot-only', action='store_true')
    parser.add_argument('--candidate', type=Path,
                        help='Reuse a verified frozen candidate instead of capturing the working tree')
    parser.add_argument('--host-checks', action='store_true',
                        help='Run source-specific package analysis and tests before native exports')
    parser.add_argument('--mode', choices=['debug', 'release'], default='debug',
                        help='debug: simulator/APK; release: unsigned iOS device bundle/Android AAB')
    args = parser.parse_args()
    if not args.targets and not args.snapshot_only:
        parser.error('Choose at least one native target or --snapshot-only')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    evidence = ROOT / 'release/native-proof' / stamp
    evidence.mkdir(parents=True)
    if args.candidate:
        candidate = args.candidate.resolve()
        manifest = json.loads((candidate / 'manifest.json').read_text())
        actual = source_hashes(candidate / 'source')
        if actual != manifest['source_sha256'] or fingerprint(actual) != manifest['source_fingerprint']:
            raise RuntimeError('Frozen candidate no longer matches its manifest')
        (evidence / 'candidate-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (evidence / 'artifacts').mkdir()
    else:
        candidate, manifest = snapshot(stamp, evidence)
    candidate_lock = (candidate / '.native-verification.lock').open('w')
    fcntl.flock(candidate_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    workspace = candidate / ('workspace-release' if args.mode == 'release' else 'workspace')
    if not workspace.exists():
        shutil.copytree(candidate / 'source', workspace)
        for file in workspace.rglob('*'):
            if file.is_file():
                file.chmod(file.stat().st_mode | 0o200)
    app = workspace / 'game/mobile'
    wrapper = str(ROOT / 'tool/flutter')
    report = {'started_utc': stamp, 'purpose': 'local export only; no store, signing or runtime acceptance', 'mode': args.mode,
              'candidate_fingerprint': manifest['source_fingerprint'], 'candidate_directory': str(candidate),
              'workspace_directory': str(workspace),
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_snapshot_unchanged': True, 'results': {}}
    shutil.copy2(Path(__file__), evidence / 'build_native.py')
    report_file = evidence / 'build-report.json'
    report_file.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Frozen candidate: {candidate}\nEvidence: {evidence}', flush=True)
    if args.snapshot_only:
        return 0
    release = args.mode == 'release'
    with (evidence / 'flutter-version.log').open('w') as log:
        subprocess.run([wrapper, '--version'], cwd=app, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (evidence / 'pub-get.log').open('w') as log:
        resolved = subprocess.run([wrapper, 'pub', 'get', '--enforce-lockfile'], cwd=app, stdout=log, stderr=subprocess.STDOUT)
    report['pub_get_exit_code'] = resolved.returncode
    if resolved.returncode:
        report_file.write_text(json.dumps(report, indent=2) + '\n')
        return resolved.returncode
    if args.host_checks:
        report['host_checks'] = {}
        failed_checks = []
        for package in ['core', 'persistence', 'progression', 'events', 'platform', 'mobile']:
            directory = workspace / 'game' / package
            if not (directory / 'pubspec.yaml').exists():
                continue
            runner = wrapper if package == 'mobile' else str(ROOT / 'tool/dart')
            for action in ['pub-get', 'analyze', 'test']:
                command = [runner, 'pub', 'get', '--enforce-lockfile'] if action == 'pub-get' else [runner, action]
                key = package + '-' + action
                with (evidence / (key + '.log')).open('w') as log:
                    checked = subprocess.run(command, cwd=directory, stdout=log, stderr=subprocess.STDOUT)
                report['host_checks'][key] = {'command': command, 'exit_code': checked.returncode}
                report_file.write_text(json.dumps(report, indent=2) + '\n')
                print(f'{key}: exit {checked.returncode}', flush=True)
                if checked.returncode:
                    failed_checks.append(key)
                    if action == 'pub-get':
                        break
        if (workspace / 'tests/services').exists():
            command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/services', '-v']
            with (evidence / 'services-test.log').open('w') as log:
                checked = subprocess.run(command, cwd=workspace, stdout=log, stderr=subprocess.STDOUT)
            report['host_checks']['services-test'] = {'command': command, 'exit_code': checked.returncode}
            if checked.returncode:
                failed_checks.append('services-test')
            print(f'services-test: exit {checked.returncode}', flush=True)
        if (workspace / 'tool/test_native_candidates.py').exists():
            command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tool', '-p', 'test_native_*.py', '-v']
            with (evidence / 'candidate-integrity-test.log').open('w') as log:
                checked = subprocess.run(command, cwd=workspace, stdout=log, stderr=subprocess.STDOUT)
            report['host_checks']['candidate-integrity-test'] = {'command': command, 'exit_code': checked.returncode}
            if checked.returncode:
                failed_checks.append('candidate-integrity-test')
            print(f'candidate-integrity-test: exit {checked.returncode}', flush=True)
        report['host_test_gate'] = 'failed' if failed_checks else 'passed'
        report['failed_host_checks'] = failed_checks
        report_file.write_text(json.dumps(report, indent=2) + '\n')
        if failed_checks:
            return 1
    for target in args.targets:
        command = native_build_command(wrapper, target, args.mode)
        print(f'Building {target}; log: {evidence / (target + ".log")}', flush=True)
        with (evidence / f'{target}.log').open('w') as log:
            result = subprocess.run(command, cwd=app, stdout=log, stderr=subprocess.STDOUT)
        report['results'][target] = {'command': command, 'exit_code': result.returncode,
                                     'build_succeeded': result.returncode == 0, 'runtime_launch_proven': False}
        if result.returncode == 0:
            artifacts = evidence / 'artifacts'
            if target == 'android':
                output = artifacts / ('tideglass-release.aab' if release else 'tideglass-debug.apk')
                source = app / ('build/app/outputs/bundle/release/app-release.aab' if release else 'build/app/outputs/flutter-apk/app-debug.apk')
                shutil.copy2(source, output)
            else:
                if target == 'ios':
                    folder = app / ('build/ios/iphoneos' if release else 'build/ios/iphonesimulator')
                else:
                    folder = app / ('build/macos/Build/Products/Release' if release else 'build/macos/Build/Products/Debug')
                bundles = list(folder.glob('*.app'))
                if len(bundles) != 1:
                    raise RuntimeError(f'Expected one {target} application bundle, found {bundles}')
                output = artifacts / f'tideglass-{target}-{args.mode}.zip'
                subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(bundles[0]), str(output)], check=True)
            report['results'][target]['artifact'] = str(output.relative_to(ROOT))
            report['results'][target]['artifact_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
            report['results'][target]['artifact_bytes'] = output.stat().st_size
        report['source_snapshot_unchanged'] = source_hashes(candidate / 'source') == manifest['source_sha256']
        differences = [path for path, digest in manifest['source_sha256'].items()
                       if not (workspace / path).exists()
                       or hashlib.sha256((workspace / path).read_bytes()).hexdigest() != digest]
        report['workspace_input_differences'] = differences
        report['dependency_locks_unchanged'] = not any(path.endswith('pubspec.lock') for path in differences)
        report['current_working_tree_matches_candidate'] = source_hashes(ROOT) == manifest['source_sha256']
        report_file.write_text(json.dumps(report, indent=2) + '\n')
        print(f'{target}: exit {result.returncode}', flush=True)
    return int(not report['source_snapshot_unchanged'] or not report.get('dependency_locks_unchanged', True)
               or any(x['exit_code'] != 0 for x in report['results'].values()))


if __name__ == '__main__':
    sys.exit(main())
