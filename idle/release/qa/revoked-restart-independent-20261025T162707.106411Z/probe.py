"""Independent pure protocol probes; no native or Flutter calls."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import sys
from tempfile import TemporaryDirectory

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
STAGE = ROOT / 'release/native-notifications/revoked-restart-repair-20261025T161340.874385Z'
sys.path[:0] = [str(STAGE / 'staged/tool'), str(ROOT / 'tool')]
import reminder_restart as protocol
import test_reminder_restart as fixtures
import verify_native_reminders as runner

checks = []
def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})
    assert value, name

def reject(name, call):
    try:
        call()
    except ValueError:
        check(name, True)
    else:
        check(name, False)

before = (STAGE / 'before/native_reminders_test.dart').read_text()
after = (STAGE / 'staged/game/mobile/integration_test/native_reminders_test.dart').read_text()
reversed_source = after[:after.index('\n\nFuture<String> fileDigest')]
reversed_source = reversed_source.replace("const scenarios = {'default', 'denied', 'quiet-cancel', 'delivery', 'revoked',\n  'revoked-prepare', 'revoked-recover'};", "const scenarios = {'default', 'denied', 'quiet-cancel', 'delivery', 'revoked'};")
reversed_source = reversed_source.replace("    if (scenario.startsWith('revoked-')) expect(Platform.isAndroid, isTrue);\n", '')
reversed_source = reversed_source.replace("    if (scenario == 'revoked-recover') {\n      await recoverRevoked(tester, support);\n      return;\n    }\n", '')
start = reversed_source.index("        } else if (scenario == 'revoked-prepare') {")
end = reversed_source.index("        } else if (scenario == 'revoked') {", start)
reversed_source = reversed_source[:start] + reversed_source[end:]
check('removing only new branches restores all original Dart bytes', reversed_source == before)

old_ast = ast.parse((STAGE / 'before/verify_native_reminders.py').read_text())
new_ast = ast.parse((STAGE / 'staged/tool/verify_native_reminders.py').read_text())
select = lambda tree, name: next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
for name in ('payload_errors', 'actual_departure_return', 'production_differences', 'artifact_inputs', 'installed_artifact_check', 'finish_observations', 'device_ready'):
    check('original runner function unchanged: ' + name, ast.dump(select(old_ast, name)) == ast.dump(select(new_ast, name)))

for mutation in ('no_kill_log', 'late_file_capture', 'wrong_helper_revision', 'UI_still_enabled', 'wrong_raw_checkpoint'):
    with TemporaryDirectory(dir=OUT) as tmp:
        base = Path(tmp)
        prior, checkpoint, context, pins, operator = fixtures.world(base)
        if mutation == 'no_kill_log':
            (base / 'death-logcat.txt').write_text('unrelated ActivityManager log\n')
            prior['evidence_sha256']['death-logcat.txt'] = protocol.digest((base / 'death-logcat.txt').read_bytes())
        elif mutation == 'late_file_capture':
            rows = protocol.read_json(base / 'restart-host-receipts.json')
            for row in rows:
                if 'head' in row['argv']:
                    row['started_utc_ms'] = prior['restart_death']['kill_utc_ms'] + 1
                    row['finished_utc_ms'] = row['started_utc_ms'] + 1
            (base / 'restart-host-receipts.json').write_bytes(fixtures.encode(rows))
            prior['evidence_sha256']['restart-host-receipts.json'] = protocol.digest((base / 'restart-host-receipts.json').read_bytes())
        elif mutation == 'wrong_helper_revision':
            pins = {**pins, 'reminder_restart.py': 'f' * 64}
        elif mutation == 'UI_still_enabled':
            (operator.parent / 'after.xml').write_text(fixtures.xml(True))
            packet = protocol.read_json(operator)
            packet['files_sha256']['after.xml'] = protocol.digest((operator.parent / 'after.xml').read_bytes())
            operator.write_bytes(fixtures.encode(packet))
        elif mutation == 'wrong_raw_checkpoint':
            raw = json.loads((base / 'revoke-checkpoint.json').read_bytes())
            raw['preparation']['process_id'] = 777
            (base / 'revoke-checkpoint.json').write_bytes(fixtures.encode(raw))
            prior['evidence_sha256']['revoke-checkpoint.json'] = protocol.digest((base / 'revoke-checkpoint.json').read_bytes())
        (base / 'verification.json').write_bytes(fixtures.encode(prior))
        reject(mutation, lambda: protocol.validate_predecessor(base / 'verification.json', context, pins, operator, runner.verify_native.native_log_errors))

with TemporaryDirectory(dir=OUT) as tmp:
    prior, checkpoint, context, pins, operator = fixtures.world(Path(tmp))
    actual = protocol.validate_predecessor(Path(tmp) / 'verification.json', context, pins, operator, runner.verify_native.native_log_errors)
    check('complete synthetic predecessor remains admitted', actual == (prior, checkpoint))

inputs = json.loads((OUT / 'input-pins.json').read_text())
for name, expected in inputs.items():
    check('unchanged input ' + name, hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected)
check('43 focused author tests independently passed', 'Ran 43 tests' in (OUT / 'tests.log').read_text() and (OUT / 'tests.log').read_text().rstrip().endswith('OK'))
(OUT / 'probe-verification.json').write_text(json.dumps({'checks': checks, 'check_count': len(checks), 'new_native_execution': False, 'production_edits': False}, indent=2) + '\n')
print(json.dumps({'checks': len(checks), 'all_passed': True}))
