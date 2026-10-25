from pathlib import Path
import ast,json,hashlib,re,types,copy
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).resolve().parent;pins={};checks=[];rows=[];negatives=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def check(name,ok):checks.append({'name':name,'passed':bool(ok)});assert ok,name
def sha(b):return hashlib.sha256(b).hexdigest()
def pure(folder):
 ns={'re':re,'json':json}
 source=read(folder/'verify_native.py').decode();fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='native_log_errors')
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'archived-native-completion','exec'),ns);ns['verify_native']=types.SimpleNamespace(native_log_errors=ns['native_log_errors'])
 source=read(folder/'verify_native_reminders.py').decode();wanted={'HEX','MARKER','IDENTITY','ACTIONS'}
 nodes=[n for n in ast.parse(source).body if (isinstance(n,ast.FunctionDef) and n.name in ['payload_errors','actual_departure_return']) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in wanted for t in n.targets))]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'archived-reminder-verifier-pure-only','exec'),ns);return ns
checkpoint='release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-reminders-phone-initial-20261023T083715.440231Z/checkpoint.json';batch=j(checkpoint)
check('checkpoint-pin',sha(read(checkpoint))=='02d01dec046c9df8dfc03a3e6c850aef3ded771b779de879f40bc44aa01ddad3')
manifest=j('.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/manifest.json');check('candidate-binding',batch['candidate_fingerprint']==manifest['source_fingerprint'])
for cell in batch['rows']:
 p=Path(cell['verification']);folder=p.parent;report=j(p);payload=j(folder/'result.json');log=read(folder/'run.log').decode(errors='replace');key=folder.name
 check('report-pin:'+key,sha(read(p))==cell['verification_sha256'])
 for name,h in cell['native_evidence_sha256'].items():
  check('safe-archived-name:'+key+':'+name,Path(name).name==name)
  check('archive-pin:'+key+':'+name,sha(read(folder/name))==h)
  check('checkpoint-report-pin:'+key+':'+name,report['evidence_sha256'][name]==h)
 check('complete-evidence-map:'+key,set(report['evidence_sha256'])==set(cell['native_evidence_sha256']))
 check('source-binding:'+key,all(report['source_pins'][k]==report['evidence_sha256'][k] for k in report['source_pins']))
 check('production-unchanged:'+key,report['frozen_source_unchanged'] and not report['production_differences_after'] and not report['source_differences_during_run'] and report['generated_harness_matches'])
 check('original-production-inputs:'+key,all(manifest['source_sha256'][f]==h for f,h in report['production_inputs_before'].items()))
 check('installed-native-binding-record:'+key,report['installed_artifact']['matches_host_artifact'] and report['installed_artifact']['checked_files']==len(report['artifact_after']))
 check('preserved-errors:'+key,report['errors']==cell['actual_report_errors']==cell['verification_errors'])
 ns=pure(folder);errors=ns['payload_errors'](payload,report,log)
 check('actual-completion-classification:'+key,(not errors)==cell['passed']==report['passed'])
 check('actual-errors-reproduced:'+key,set(errors)<=set(report['errors']))
 check('explicit-owned-process-stop:'+key,report['stop']['exit_code']==0 and report['stop']['command'][-1]=='dev.tideglass.game')
 if cell['passed']:
  check('normal-exit:'+key,report['exit_code']==0 and payload['completed'] is True)
  for label,mutate in [('wrong-run',lambda x:x.update(run_id=x['run_id']+'-wrong')),('incomplete',lambda x:x.update(completed=False)),('mock-gateway',lambda x:x.update(gateway='FakeGateway'))]:
   bad=copy.deepcopy(payload);mutate(bad);e=ns['payload_errors'](bad,report,log);check('reject-'+label+':'+key,bool(e));negatives.append({'run':key,'mutation':label,'errors':e})
  badlog=log+'\nflutter: Unhandled Exception: review-only\n';check('reject-late-error:'+key,bool(ns['payload_errors'](payload,report,badlog)));negatives.append({'run':key,'mutation':'late-exception'})
 else:
  check('failed-native-stays-incomplete:'+key,payload.get('completed') is not True and bool(report['errors']))
  if cell['scenario']=='default':check('invalid-ID-original-failure:'+key,'native_reminders_test.dart' in read(folder/'harness.dart').decode() or 'RegExp(r\'^[A-Za-z0-9_-]{1,160}$\')' in read(folder/'harness.dart').decode())
  if cell['scenario']=='delivery':
   check('delivery-no-plan-or-due-marker:'+key,'plan' not in payload and not any(a['action']=='wait_until_due_then_return_via_app_icon' for a in payload['actions']))
   check('delivery-real-paused-before-failure:'+key,any(e['state']=='paused' for e in payload['lifecycle_events']) and 'OutsideTestException' in log)
 if cell['passed'] and cell['scenario']=='quiet-cancel':
  plan=payload['plan'];due=datetime.fromtimestamp(plan['due_utc_ms']/1000,timezone.utc).astimezone(ZoneInfo(plan['zone']))
  check('independent-quiet-local-time',due.hour*60+due.minute==payload['quiet_window']['end_minute']==payload['quiet_due_local_minute'] and due.second==0)
  check('independent-minimum-delay',plan['due_utc_ms']-plan['background_call_utc_ms']>=300000)
  check('independent-return-cancel',payload['return_pending_ids']==[])
  for label,mutate in [('too-early',lambda x:x['plan'].update(due_utc_ms=x['plan']['background_call_utc_ms']+299999)),('wrong-quiet-end',lambda x:x.update(quiet_due_local_minute=(x['quiet_due_local_minute']+1)%1440)),('pending-after-return',lambda x:x.update(return_pending_ids=[77101]))]:
   bad=copy.deepcopy(payload);mutate(bad);e=ns['payload_errors'](bad,report,log);check('reject-'+label,bool(e));negatives.append({'run':key,'mutation':label,'errors':e})
  b=j(folder/'operator-settings-preflight-binding.json');check('operator-binding-identity',b['verification_id']==report['verification_id'] and b['run_id']==report['run_id'] and b['device']==report['device'] and b['candidate_fingerprint']==manifest['source_fingerprint'])
  for f,h in b['files_sha256'].items():check('operator-preflight-pin:'+f,sha(read(Path(b['source_folder'])/f))==h)
 rows.append({'scenario':cell['scenario'],'passed':cell['passed'],'verification':str(p.relative_to(R)),'sha256':cell['verification_sha256'],'reproduced_errors':errors,'permission_before_initialize':payload.get('permission_before_initialize'),'permission_after_initialize':payload.get('permission_after_initialize'),'permission_after_opt_in':payload.get('permission_after_opt_in'),'process_id':payload.get('process_id'),'plan':payload.get('plan'),'pending_after_return':payload.get('return_pending_ids'),'physical_or_banner_claim':False})
for f,h in batch['actual_settings_preflight'].items():check('checkpoint-preflight-pin:'+f,sha(read(f))==h)
f=batch['delivery_failure_packet'];check('delivery-failure-packet-pin',sha(read(f['path']))==f['sha256']);failure=j(f['path'])
check('no-production-failure-attribution',failure['production_fault_demonstrated'] is False and failure['delivery_success_claim'] is False)
check('three-pass-two-fail',sum(x['passed'] for x in rows)==batch['pass_count']==3 and sum(not x['passed'] for x in rows)==batch['failed_count']==2)
after={f:sha((R/f).read_bytes()) for f in pins};check('unchanged-review-inputs',after==pins)
for name,value in [('reminder-initial-inputs-before.json',pins),('reminder-initial-inputs-after.json',after),('reminder-initial-verification.json',{'checks':checks,'negative_controls':negatives,'rows':rows,'all_checks_passed':True,'native_commands_run':False,'Flutter_run':False,'actual_delivery_completed':False,'pending':['iOS successful delivery','iOS actual revocation','Android all five reminder scenarios'],'new_scope_or_package_acceptance':False})]:(O/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'negatives':len(negatives),'pins':len(pins),'passed':3,'failed_preserved':2}))
