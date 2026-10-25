"""Run only with lead-granted exclusive Flutter lane; preserve exact host evidence."""
from pathlib import Path
from datetime import datetime, timezone
import difflib
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
DEST = ROOT / 'release/qa' / ('client-localization-complete-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
DEST.mkdir()
paths = set()
for folder in ['game/mobile/lib', 'game/mobile/test', 'game/mobile/integration_test', 'game/core/lib', 'game/progression/lib', 'game/persistence/lib', 'game/events/lib', 'game/platform/lib']:
    paths.update((ROOT / folder).rglob('*.dart'))
paths.update((ROOT / 'game/mobile/assets').rglob('*.json'))
paths.update((ROOT / 'game').glob('*/pubspec.*'))
paths.update([ROOT / 'tool/flutter', ROOT / 'tool/dart', ROOT / '.tooling/flutter/packages/flutter_test/lib/src/widget_tester.dart', Path(__file__)])
paths = sorted(paths)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
source = {str(p.relative_to(ROOT)): sha(p) for p in paths}
for path in paths:
    target = DEST / 'source' / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(path.read_bytes())
(DEST / 'source-before.json').write_text(json.dumps(source, indent=2) + '\n')
print('EVIDENCE', DEST, flush=True)
checks = []


def check(name, command, kind, condition=None):
    print('START', name, flush=True)
    with (DEST / f'{name}.log').open('w') as log:
        result = subprocess.run(command, cwd=ROOT / 'game/mobile', stdout=log, stderr=subprocess.STDOUT)
    after = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    differences = [p for p in source if after[p] != source[p]]
    contents = (DEST / f'{name}.log').read_text()
    counts = re.findall(r'\+(\d+): All tests passed!', contents)
    count = int(counts[-1]) if counts else None
    passed = result.returncode == 0 and not differences
    if kind in {'representative', 'matrix'}:
        passed = passed and count == 12
    checks.append({'name': name, 'kind': kind, 'condition': condition, 'command': command,
                   'exit_code': result.returncode, 'completed_test_count': count,
                   'source_differences': differences, 'passed': passed,
                   'log_sha256': sha(DEST / f'{name}.log')})
    (DEST / 'verification.json').write_text(json.dumps({
        'source_before': source, 'checks': checks,
        'scope': 'Author host localization and targeted UI checks; no native/physical qualification',
    }, indent=2) + '\n')
    print('END', name, result.returncode, 'tests', count, 'drift', len(differences), flush=True)
    return passed


def command(viewport, scale, pseudo):
    return ['../../tool/flutter', 'test', 'test/localization_test.dart',
            f'--dart-define=TIDEGLASS_TEST_VIEWPORT={viewport}',
            f'--dart-define=TIDEGLASS_TEST_TEXT_PERCENT={scale}',
            f'--dart-define=TIDEGLASS_PSEUDO={str(pseudo).lower()}', '--reporter=expanded']


passed = check('analyzer', ['../../tool/flutter', 'analyze'], 'analyzer')
for pseudo in [False, True]:
    passed = check(f'representative-{str(pseudo).lower()}-phone-200', command('phone', 200, pseudo), 'representative',
                   {'viewport': 'phone', 'text_percent': 200, 'pseudo': pseudo}) and passed
if not passed:
    print('STOP: representative gate failed; full matrix not started', flush=True)
    sys.exit(1)
for pseudo in [False, True]:
    for viewport in ['phone', 'tablet']:
        for scale in [100, 150, 200]:
            passed = check(f'matrix-{str(pseudo).lower()}-{viewport}-{scale}', command(viewport, scale, pseudo), 'matrix',
                           {'viewport': viewport, 'text_percent': scale, 'pseudo': pseudo}) and passed
passed = check('targeted-ui', ['../../tool/flutter', 'test', 'test/season_ui_test.dart', 'test/notification_settings_test.dart', '--reporter=expanded'], 'targeted-ui') and passed
print('COMPLETE', DEST, 'PASS', passed, flush=True)
sys.exit(0 if passed else 1)
