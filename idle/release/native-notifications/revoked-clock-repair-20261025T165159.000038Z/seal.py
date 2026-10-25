from pathlib import Path
import hashlib,json,tempfile,shutil,subprocess,ast
base=Path(__file__).resolve().parent;root=base.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['reminder_restart.py','test_reminder_restart.py','test_reminder_clock.py']
baseline=json.loads((base/'baseline.json').read_bytes())
assert all(sha(root/p)==v for p,v in baseline.items())
assert 'Ran 67 tests' in (base/'final-tests.log').read_text() and (base/'final-tests.log').read_text().rstrip().endswith('OK')
# Reconstruct the actual three intended files, never touching live tools.
with tempfile.TemporaryDirectory(prefix='patch-control-',dir=base) as temp:
    t=Path(temp);(t/'tool').mkdir()
    for n in names[:2]:shutil.copyfile(base/'before'/n,t/'tool'/n)
    result=subprocess.run(['git','apply',str(base/'clock-protocol.patch')],cwd=t,capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert all(sha(t/'tool'/n)==sha(base/'staged/tool'/n) for n in names)
# Original strict native/checkpoint/permission/recovery/log/fixture predicates unchanged.
a=ast.parse((base/'before/reminder_restart.py').read_text());b=ast.parse((base/'staged/tool/reminder_restart.py').read_text())
unchanged=['checkpoint','permission','interrupted_errors','switch','recovery_errors','fixture','file_name']
for n in unchanged:
    old=next(x for x in a.body if isinstance(x,ast.FunctionDef) and x.name==n)
    new=next(x for x in b.body if isinstance(x,ast.FunctionDef) and x.name==n)
    assert ast.dump(old)==ast.dump(new),n
intended={str(Path('tool')/n):sha(base/'staged/tool'/n) for n in names}
inputs=json.loads((base/'preservation-and-diagnostic.json').read_bytes())
report={'status':'author-host-checks-pass; independent review and fresh native pair required','intended_files':intended,'unchanged_live_baseline':baseline,
        'patch_reconstruction':'git apply in new disposable author directory reproduced all three intended hashes',
        'original_assertions_ast_unchanged':unchanged,'test_methods':67,'existing_methods':43,'new_clock_causal_methods':24,
        'test_command':'PYTHONPATH=release/native-notifications/revoked-clock-repair-20261025T165159.000038Z/staged/tool:tool python3 -m unittest -v test_reminder_restart test_native_reminders test_reminder_clock',
        'test_cwd':str(root),'preservation_checks':len(inputs['checks']),'preserved_input_count':len(inputs['input_pins']),
        'old_packet_disposition':inputs['old_packet_rejected'],'changes':['Test-only helper clock/causal protocol','Updated synthetic fixture timing','Focused clock/causal controls'],
        'limits':['No live source promotion','No Dart or runner change','No Flutter/device/native execution','No recovery from rejected f8d460 packet','No production/scope/status change'],
        'output_pins':{str(p.relative_to(base)):sha(p) for p in [base/'clock-protocol.patch',base/'baseline.json',base/'OPERATOR_PROTOCOL.md',base/'preservation-and-diagnostic.json',base/'author-verify.log',base/'initial-tests.log',base/'clock-tests-first.log',base/'final-tests.log',base/'author_verify.py',*[base/'staged/tool'/n for n in names]]}}
(base/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
text=f'''# Clock-protocol repair: author handoff

The staged test-only repair addresses all three mixed-clock predicates. It captures prospective same-run raw clock brackets, validates host wall/monotonic consistency, replays the hash-pinned raw model on recovery, and binds pre-kill exports through actual live → export → live observations before the actual UI tap. Permission-change death may follow command completion; its measured interval must be consistent with the actual tap → OFF observation interval and independent fresh PID/UI/reason evidence. The original native180s, save/source/permission/pending and framework gates remain intact.

Only these files are proposed for promotion after independent review:

| File | SHA-256 |
|---|---|
'''
for p,h in intended.items():text+=f'| `{p}` | `{h}` |\n'
text+=f'''
`clock-protocol.patch` SHA-256 `{sha(base/'clock-protocol.patch')}` reconstructs these exact files against the preserved baseline; a disposable git-apply control passed. `verification.json` SHA-256 `{sha(base/'verification.json')}` pins all author evidence. `OPERATOR_PROTOCOL.md` contains the exact fresh packet additions and measurement boundaries.

Validation: **67 host methods passed** (43 existing,24 focused clock/causal methods), with exact command and working directory in verification. Existing checkpoint/permission/recovery/log/fixture predicates are unchanged at AST level. **42 preservation/arithmetic checks** pin37 input files; the actual post-event diagnostic integer arithmetic reproduces, but it is not retroactive calibration. The rejected f8d460 packet is explicitly refused for its absent clock model and remains untouched.

The live helper, runner, Dart harness and existing test remained at baseline hashes. No live files, Flutter, device, production, metadata or scope changed. This handoff is author evidence only; QA/root review and a fresh preparation/recovery remain necessary. The old failures and all previous stage seals remain preserved.

Reproduce from `{root}`:

```sh
{report['test_command']}
python3 release/native-notifications/revoked-clock-repair-20261025T165159.000038Z/author_verify.py
```

The second command is read-only against live/prior inputs, writes only this author folder, and is unnecessary if reviewers prefer to replay the same checks in their own independent folder. Source writes are stopped.
'''
(base/'AUTHOR_HANDOFF.md').write_text(text)
print(json.dumps({'verification_sha256':sha(base/'verification.json'),'handoff_sha256':sha(base/'AUTHOR_HANDOFF.md'),'intended_files':intended,'patch_sha256':sha(base/'clock-protocol.patch')}))
