#!/usr/bin/env python3
"""Run the independent scenario-cache probe against current or archived core.

From repo root:
 python3 game/qa/run_scenario_memo_probe.py --output release/balance/scenario-cache-current
 python3 game/qa/run_scenario_memo_probe.py --original-core release/balance/supplemental-source-63786005ca749aec6fbc3c15913dff43e01fae1bdfd4fcb931ce2f712ca80e53/game/core --expect-failure --output release/balance/scenario-cache-original
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--original-core', type=Path)
parser.add_argument('--expect-failure', action='store_true')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
core = (root / args.original_core).resolve() if args.original_core else root / 'game/core'
output = root / args.output
output.parent.mkdir(parents=True, exist_ok=True)
config_path = root / 'game/simulation/.dart_tool/package_config.json'
config = json.loads(config_path.read_text())
for package in config['packages']:
    package['rootUri'] = urllib.parse.urljoin(config_path.as_uri(), package['rootUri'])
    if package['name'] == 'tideglass_core':
        package['rootUri'] = core.as_uri() + '/'
paths = [root / 'game/qa/integration_scenario_memo.dart', Path(__file__),
         root / 'game/simulation/pubspec.yaml', root / 'game/simulation/pubspec.lock']
for directory in [core / 'lib', root / 'game/progression/lib', root / 'game/events/lib',
                  root / 'release/performance/numeric-baseline-source']:
    paths += list(directory.rglob('*.dart'))
paths += list((root / 'game/content/challenges').glob('*.json'))
paths.append(root / 'game/events/content/season.01.json')
hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(set(paths))}
with tempfile.TemporaryDirectory(prefix='tideglass-scenario-probe-') as tmp:
    config_file = Path(tmp) / 'package_config.json'
    config_file.write_text(json.dumps(config))
    command = [str(root / 'tool/dart'), 'run', f'--packages={config_file}',
               str(root / 'game/qa/integration_scenario_memo.dart')]
    result = subprocess.run(command, cwd=root / 'game/simulation', text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output.with_suffix('.stdout').write_text(result.stdout)
output.with_suffix('.stderr').write_text(result.stderr)
unchanged = all(hashlib.sha256((root / p).read_bytes()).hexdigest() == value
                for p, value in hashes.items())
expected = (result.returncode != 0 and 'Bad state: rate order' in result.stderr
            if args.expect_failure else result.returncode == 0)
report = {'status': 'passed' if expected and unchanged else 'failed',
          'expected_original_failure': args.expect_failure,
          'core_source': str(core.relative_to(root)), 'process_exit_code': result.returncode,
          'sources_unchanged': unchanged, 'source_sha256': hashes,
          'source_digest': hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
          'stdout_sha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
          'stderr_sha256': hashlib.sha256(result.stderr.encode()).hexdigest(),
          'assertion_result': json.loads(result.stdout) if result.returncode == 0 else None}
output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: report[key] for key in ['status', 'expected_original_failure',
    'process_exit_code', 'sources_unchanged', 'source_digest']}))
raise SystemExit(0 if report['status'] == 'passed' else 1)
