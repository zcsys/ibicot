from pathlib import Path
import ast,json,hashlib,sys,difflib,copy,tempfile
R=Path(__file__).resolve().parents[3];O=Path(__file__).parent;S=R/'release/native-notifications/revoked-clock-repair-20261025T165159.000038Z';pins={};checks=[];negative=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=sha(b);return b
def j(p):return json.loads(read(p))
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
v=j(S/'verification.json');check('exact author seal',sha(read(S/'verification.json'))=='9174d82701ce127801c11210ec901a77df3823fb63302c896098d4d29568bdaa')
check('exact handoff',sha(read(S/'AUTHOR_HANDOFF.md'))=='1e4397708cdc07d94ff76588d29a0fcb1f3cd3837b88df7aa584fc5d0b2504bd')
for n,h in v['output_pins'].items():check('author output '+n,sha(read(S/n))==h)
for n,h in v['unchanged_live_baseline'].items():check('live baseline '+n,sha(read(n))==h)
for n,h in v['intended_files'].items():check('intended stage '+n,sha(read(S/'staged'/n))==h)
old=ast.parse(read(S/'before/reminder_restart.py'));new=ast.parse(read(S/'staged/tool/reminder_restart.py'))
for name in ['checkpoint','permission','interrupted_errors','switch','recovery_errors','fixture','file_name']:
 a=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name==name);b=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name==name);check('original assertion AST '+name,ast.dump(a)==ast.dump(b))
patch=[]
for name in ['reminder_restart.py','test_reminder_restart.py','test_reminder_clock.py']:
 before=S/'before'/name;after=S/'staged/tool'/name
 patch.extend(difflib.unified_diff(read(before).decode().splitlines(keepends=True) if before.exists() else [],read(after).decode().splitlines(keepends=True),fromfile='a/tool/'+name if before.exists() else '/dev/null',tofile='b/tool/'+name))
check('exact independently reconstructed diff',''.join(patch).encode()==read(S/'clock-protocol.patch'))
check('67 focused methods reproduced','Ran 67 tests' in read(O/'host-tests.log').decode() and read(O/'host-tests.log').decode().rstrip().endswith('OK'))
sys.path[:0]=[str(S/'staged/tool'),str(R/'tool')]
import reminder_restart as rr
import verify_native_reminders as runner
from test_reminder_restart import world,encode,stamp,NOW
check('imported exact reviewed helper',Path(rr.__file__).resolve()==S/'staged/tool/reminder_restart.py')
# Full wrapper admission on a fresh synthetic packet, then independent mutations
# which update hashes so that substantive causal/model checks must reject them.
def mutate_case(name,mutate):
 with tempfile.TemporaryDirectory(dir=O) as tmp:
  B=Path(tmp);prior,c,ctx,sp,op=world(B)
  check('synthetic baseline '+name,rr.validate_predecessor(B/'verification.json',ctx,sp,op,runner.verify_native.native_log_errors)==(prior,c))
  mutate(B,prior,op)
  (B/'verification.json').write_bytes(encode(prior))
  try:rr.validate_predecessor(B/'verification.json',ctx,sp,op,runner.verify_native.native_log_errors)
  except (ValueError,KeyError,TypeError) as e:negative.append({'name':name,'rejection':str(e)});check('negative '+name,True)
  else:check('negative '+name,False)
def ready_before_exports(B,p,op):p['restart_preparation']['host_ready_stamp']=stamp(NOW+2100)
def wrong_raw_pid(B,p,op):
 f=B/'restart-host-receipts.json';rows=json.loads(f.read_bytes());rows[0]['clock_context']['process_id']=99;f.write_bytes(encode(rows));p['evidence_sha256'][f.name]=sha(f.read_bytes())
def absent_before_tap(B,p,op):
 q=json.loads(op.read_bytes());f=op.parent/'pid-observations.json';rows=json.loads(f.read_bytes());rows[1].update(started_stamp=stamp(NOW+10150),finished_stamp=stamp(NOW+10151),started_utc_ms=NOW+10150,finished_utc_ms=NOW+10151);f.write_bytes(encode(rows));q['files_sha256'][f.name]=sha(f.read_bytes());op.write_bytes(encode(q))
def stale_export(B,p,op):
 f=B/'restart-host-receipts.json';rows=json.loads(f.read_bytes());idx=next(i for i,x in enumerate(rows) if 'head' in x['argv']);row=rows.pop(idx);at=next(i for i,x in enumerate(rows) if '/proc/42/cmdline' in x['argv'] and x['started_utc_ms']>NOW+2500);row.update(started_stamp=stamp(NOW+3200),finished_stamp=stamp(NOW+3201),started_utc_ms=NOW+3200,finished_utc_ms=NOW+3201);rows.insert(at+1,row);f.write_bytes(encode(rows));p['evidence_sha256'][f.name]=sha(f.read_bytes())
for name,fn in [('ready-before-final-live-export',ready_before_exports),('rehashed-clock-other-PID',wrong_raw_pid),('rehashed-absent-before-tap',absent_before_tap),('rehashed-export-after-final-alive',stale_export)]:mutate_case(name,fn)
B=R/'release/native-notifications/integration-android-20261025T164440025420Z';prior=j(B/'verification.json');op=R/'release/native-notifications/revoked-restart-operator-20261025T164440025420Z/operator.json'
check('old rejected report unchanged',sha(read(B/'verification.json'))=='f8d460bebd26e7bb63c61ae609f6dc57606a1b3a22442572c1f9c180eb3a2413')
for n,h in prior['evidence_sha256'].items():check('old preserved '+n,sha(read(B/n))==h)
for n,h in j(op)['files_sha256'].items():check('old operator preserved '+n,sha(read(op.parent/n))==h)
try:rr.validate_predecessor(B/'verification.json',{**prior,'scenario':'revoked-recover','verification_id':'qa-negative-only'},prior['source_pins'],op,runner.verify_native.native_log_errors)
except (ValueError,KeyError,TypeError) as e:old_error=str(e)
else:raise AssertionError('old packet incorrectly admitted')
check('old packet lacks prospective clock model','clock_model' in old_error)
read('implementation/program.json');read('implementation/scope_requirements.json');check('all pins unchanged',all(sha((R/n).read_bytes())==h for n,h in pins.items()))
out={'checks':checks,'check_count':len(checks),'pins':pins,'test_methods_reproduced':67,'independent_rehashed_negative_controls':negative,'old_packet_rejection':old_error,'recommendation':'Approve exact three-file test-only prospective protocol for fresh preparation and independent recovery; no retroactive admission or actual native success.','timing_claim':'Measured interval consistency with actual tap-to-OFF sequence, plus causal PID/UI evidence; not proof of kill during adb input.','source_or_status_edits':False,'new_native_execution':False};(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification_sha256':sha((O/'verification.json').read_bytes())}))
