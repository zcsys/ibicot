#!/usr/bin/env python3
"""Scoped actual Android Home/reopen or observed share-sheet cancellation."""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path('/Users/csys/Desktop/ibicot/idle')
ADB = str(ROOT / '.tooling/android-sdk/platform-tools/adb')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['clock', 'share'])
    parser.add_argument('evidence', type=pathlib.Path)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    assert evidence.parent == ROOT / 'release/native-proof' and evidence.name.startswith('integration-android-')
    marker = 'TIDEGLASS_NATIVE_CLOCK_BACKGROUND_READY' if args.action == 'clock' else 'TIDEGLASS_NATIVE_SHARE_READY'
    prefix = (evidence / 'run.log').read_bytes()
    assert marker.encode() in prefix
    record = {'device': 'emulator-5556', 'action': args.action, 'verification_id': evidence.name,
              'readiness_prefix_sha256': hashlib.sha256(prefix).hexdigest(), 'commands': [],
              'scope': 'Actual OS controls and raw screenshots; no injected Flutter lifecycle or receiving-app delivery'}
    (evidence / ('operator-' + args.action + '-readiness.log')).write_bytes(prefix)
    def run(*arguments, capture_name=None):
        command = [ADB, '-s', 'emulator-5556', *arguments]
        result = subprocess.run(command, capture_output=True, timeout=20)
        entry = {'command': command, 'exit_code': result.returncode,
                 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'stderr': result.stderr.decode(errors='replace')}
        if capture_name:
            (evidence / capture_name).write_bytes(result.stdout)
            entry.update(file=capture_name, bytes=len(result.stdout), sha256=hashlib.sha256(result.stdout).hexdigest())
        else:
            entry['stdout'] = result.stdout.decode(errors='replace')
        record['commands'].append(entry)
        assert result.returncode == 0
        return result.stdout.decode(errors='replace') if not capture_name else ''
    try:
        if args.action == 'clock':
            run('shell', 'input', 'keyevent', 'KEYCODE_HOME')
            time.sleep(1)
            home = run('shell', 'dumpsys', 'activity', 'activities')
            resumed = [line for line in home.splitlines() if 'mResumedActivity' in line or 'topResumedActivity' in line]
            assert any('launcher' in line.lower() for line in resumed), resumed
            record['observed_home_activity'] = resumed
            run('exec-out', 'screencap', '-p', capture_name='operator-clock-home.png')
            run('shell', 'am', 'start', '-n', 'dev.tideglass.game/.MainActivity')
        else:
            shown = run('shell', 'dumpsys', 'activity', 'activities')
            resumed = [line for line in shown.splitlines() if 'mResumedActivity' in line or 'topResumedActivity' in line]
            assert any('intentresolver' in line for line in resumed), resumed
            record['observed_share_activity'] = resumed
            run('exec-out', 'screencap', '-p', capture_name='operator-share-sheet.png')
            run('shell', 'input', 'keyevent', 'KEYCODE_BACK')
            time.sleep(.2)
            after = run('shell', 'dumpsys', 'activity', 'activities')
            record['activities_after_cancel'] = [line for line in after.splitlines() if 'mResumedActivity' in line or 'topResumedActivity' in line]
            assert not any('intentresolver' in line for line in record['activities_after_cancel'])
        record['os_actions_completed'] = True
    finally:
        (evidence / ('operator-' + args.action + '.json')).write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'action': args.action, 'os_actions_completed': record['os_actions_completed']}))


if __name__ == '__main__':
    main()
