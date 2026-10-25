#!/usr/bin/env python3
"""Capture actual responsive UI at store-compatible resolution; restore prior override."""
import datetime
import json
import re
import subprocess

from execute_cells import EVIDENCE, ROOT, cell


def main():
    record = {'device': 'emulator-5556', 'scope': 'Gallery only; raw device output, no image resizing', 'commands': []}
    def run(*args):
        command = [str(ROOT / '.tooling/android-sdk/platform-tools/adb'), '-s', 'emulator-5556', 'shell', 'wm', *args]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        record['commands'].append({'command': command, 'exit_code': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr,
                                   'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        if result.returncode:
            raise RuntimeError('Display command failed')
        return result.stdout
    original = run('size')
    matches = re.findall(r'^Override size: (\d+x\d+)\s*$', original, re.M)
    assert len(matches) <= 1 and re.search(r'^Physical size: \d+x\d+\s*$', original, re.M)
    record['original_wm_size'] = original
    record['original_override'] = matches[0] if matches else None
    try:
        run('size', '1080x1920')
        changed = run('size')
        assert 'Override size: 1080x1920' in changed
        record['capture_wm_size'] = changed
        record['verification'] = str(cell('android', 'capture-gallery', 'v3b00-android-gallery'))
    finally:
        try:
            run('size', matches[0] if matches else 'reset')
            record['restored_wm_size'] = run('size')
            record['restored_exact_original'] = record['restored_wm_size'] == original
            assert record['restored_exact_original']
        finally:
            (EVIDENCE / 'android-gallery-display.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
