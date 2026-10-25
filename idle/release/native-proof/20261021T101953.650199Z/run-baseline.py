#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parents[3]
plan = json.loads((Path(__file__).parent / 'runtime-plan.json').read_text())
candidate = root / '.tooling/build-candidates/20261021T101953.650199Z-152805bf9e26'
label = sys.argv[1]
rows = [r for r in plan['rows'] if r['label'] == label and r['scenario'] in ['seeded', 'natural-start', 'natural-reload', 'session-start', 'session-reload']]
results = []
for row in rows:
    command = [sys.executable, str(root / 'tool/verify_native.py'), str(candidate), '--device', row['device'], '--label', row['label'], '--scenario', row['scenario'], '--run-id', row['run_id']]
    print('Starting ' + row['label'] + ' ' + row['scenario'], flush=True)
    result = subprocess.run(command, cwd=root)
    results.append(dict(row, exit_code=result.returncode, command=command))
    (Path(__file__).parent / ('baseline-orchestration-' + label + '.json')).write_text(json.dumps(results, indent=2) + '\n')
    if result.returncode:
        sys.exit(result.returncode)
print(str(len(rows)) + ' ' + label + ' baseline scenarios passed.', flush=True)
