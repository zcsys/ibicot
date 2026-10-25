"""Run one explicitly targeted daily condition after the lead grants Flutter.

This is never presented as the full 137-row content matrix. The existing
independently reviewed row validator is reused for the five daily rows.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
sys.path.insert(0, str(ROOT / 'release/content-presentation/staged/tool'))
from check_content_report import validate, require

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, indent=2) + '\n')

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
p.add_argument('--viewport', choices=['phone','tablet'], required=True)
p.add_argument('--text-percent', type=int, choices=[100,150,200], required=True)
p.add_argument('--pseudo', choices=['true','false'], required=True)
a = p.parse_args()
output = a.output.resolve()
output.mkdir(parents=True, exist_ok=False)
promoted = [str(x.relative_to(STAGE)) for x in (STAGE/'game').rglob('*.dart')]
for path in promoted:
    require((ROOT/path).read_bytes() == (STAGE/path).read_bytes(), 'Promoted source differs: '+path)

def inventory():
    paths = set()
    for package in ['mobile','core','progression','events','persistence','platform']:
        base = ROOT/'game'/package
        for folder in ['lib','assets','content']:
            paths.update(x for x in (base/folder).rglob('*') if x.is_file())
        for name in ['pubspec.yaml','pubspec.lock']:
            if (base/name).is_file(): paths.add(base/name)
    for path in ['game/mobile/test/daily_icons_test.dart', 'game/mobile/test/content_presentation_test.dart',
                 'game/mobile/test/content_presentation_probe.dart','economy.json','tool/flutter','tool/dart',
                 'release/content-presentation/staged/expected-rows.json',
                 'release/content-presentation/staged/tool/check_content_report.py',
                 'release/content-presentation/staged/tool/content_contract.py',
                 str(Path(__file__).resolve().relative_to(ROOT))]: paths.add(ROOT/path)
    return {str(x.relative_to(ROOT)):sha(x) for x in sorted(paths)}

before = inventory()
for path in before:
    target = output/'source'/path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT/path).read_bytes())
condition = {'viewport':a.viewport,'text_percent':a.text_percent,'pseudo':a.pseudo=='true'}
command = [str(ROOT/'tool/flutter'), 'test', '--reporter=json',
           'test/daily_icons_test.dart', 'test/content_presentation_test.dart', '--name', 'daily ',
           f'--dart-define=TIDEGLASS_TEST_VIEWPORT={a.viewport}',
           f'--dart-define=TIDEGLASS_TEST_TEXT_PERCENT={a.text_percent}',
           f'--dart-define=TIDEGLASS_PSEUDO={a.pseudo}',
           f'--dart-define=TIDEGLASS_CONTENT_REPORT={output/"observations.json"}']
with (output/'test.jsonl').open('w') as log:
    result = subprocess.run(command, cwd=ROOT/'game/mobile', stdout=log, stderr=subprocess.STDOUT)
after = inventory()
record = {'scope':'targeted_daily_only_not_full_content_matrix','command':command,'condition':condition,
          'exit_code':result.returncode,'source_before':before,'source_after':after,
          'output_hashes':{name:sha(output/name) for name in ['test.jsonl','observations.json'] if (output/name).exists()}}
write(output/'run.json',record)
require(result.returncode == 0, 'Actual widget command failed')
require(before == after, 'Source drift during run')
for path, pin in before.items(): require(sha(output/'source'/path)==pin, 'Archived bytes differ: '+path)
events = []
for line in (output/'test.jsonl').read_text().splitlines():
    try: events.append(json.loads(line))
    except json.JSONDecodeError: pass
done = [v for v in events if v.get('type')=='done']
require(len(done)==1 and done[0].get('success') is True and events[-1] is done[0], 'No final successful completion')
require(not any(v.get('type')=='error' for v in events), 'Actual test errors')
finished = [v for v in events if v.get('type')=='testDone' and not v.get('hidden',False)]
require(len(finished)==4 and len({v['testID'] for v in finished})==4, 'Exactly four daily tests required')
require(all(v.get('result')=='success' and not v.get('skipped',False) for v in finished), 'Failed/skipped test')
names = {v['test']['id']:v['test']['name'] for v in events if v.get('type')=='testStart'}
expected = ['daily icons retain complete labels, states and actual controls',
            'content daily pending reroll and status',
            'content daily ready backlog claims and empty state',
            'content daily timers queued ready and emptied by actual collection']
require(sorted(names[v['testID']] for v in finished)==sorted(expected), 'Wrong four actual cases')
contract = json.loads((ROOT/'release/content-presentation/staged/expected-rows.json').read_text())
rows = [v for v in contract['rows'] if v['id'].startswith('flow.daily.')]
require(len(rows)==5, 'Original five daily rows required')
validate(json.loads((output/'observations.json').read_text()), {'rows':rows,'rows_per_condition':5}, condition)
summary = {'scope':'targeted_daily_only_not_full_content_matrix','condition':condition,'tests':4,'rows':5,
           'source_inputs':len(before),'source_drift':False,'host_only':True,'release_acceptance':False}
write(output/'verification.json',summary)
print(json.dumps(summary))
