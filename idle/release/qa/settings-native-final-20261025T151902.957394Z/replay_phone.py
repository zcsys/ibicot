from pathlib import Path
import ast,json,hashlib,re,types,copy
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;pins={};checks=[];rows=[];negatives=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def check(name,ok):checks.append({'name':name,'passed':bool(ok)});assert ok,name
def sha(b):return hashlib.sha256(b).hexdigest()
# Reuse only the prior reviewed pure extractor, not its top-level execution.
old='release/qa/settings-native-20261023T081631.942859Z/replay_reminder_initial.py'
node=next(n for n in ast.parse(read(old)).body if isinstance(n,ast.FunctionDef) and n.name=='pure')
exec(compile(ast.Module(body=[node],type_ignores=[]),'preserved-pure-extractor','exec'))
cp='release/native-notifications/resume-20261025-20261025T150516.353584Z/phone-five-checkpoint.json';batch=j(cp)
check('sealed phone checkpoint',sha(read(cp))=='afdf1f551a119af0e1945c2bd3a33383c587e0377367f83989ec7eec4396e344')
manifest=j('.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/manifest.json')
check('five distinct scenarios',{x['scenario'] for x in batch['phone_five_passed']}=={'default','denied','quiet-cancel','delivery','revoked'})
for cell in batch['phone_five_passed']:
 p=Path(cell['verification']);folder=p.parent;report=j(p)
 check('report '+cell['scenario'],sha(read(p))==cell['verification_sha256'] and report['passed'])
 for name,h in cell['files_sha256'].items():
  check('safe name '+cell['scenario']+':'+name,Path(name).name==name)
  check('pinned actual bytes '+cell['scenario']+':'+name,sha(read(folder/name))==h)
 if cell['scenario'] not in ('delivery','revoked'):
  rows.append({'scenario':cell['scenario'],'basis':'Earlier independent initial review, linked by unchanged actual file hashes','verification':str(p.relative_to(R)),'sha256':cell['verification_sha256']});continue
 payload=j(folder/'result.json');log=read(folder/'run.log').decode();ns=pure(folder)
 check('source archive binding '+cell['scenario'],all(report['source_pins'][k]==report['evidence_sha256'][k] for k in report['source_pins']))
 check('immutable production '+cell['scenario'],report['frozen_source_unchanged'] and not report['production_differences_after'] and not report['source_differences_during_run'] and report['generated_harness_matches'])
 check('exact production input map '+cell['scenario'],all(manifest['source_sha256'][f]==h for f,h in report['production_inputs_before'].items()))
 check('installed artifact comparison '+cell['scenario'],report['installed_artifact']['matches_host_artifact'] and report['installed_artifact']['checked_files']==len(report['artifact_after']))
 check('strict real native and driver completion '+cell['scenario'],ns['payload_errors'](payload,report,log)==[] and report['exit_code']==0 and payload['completed'])
 check('owned process explicit stop '+cell['scenario'],report['stop']['exit_code']==0 and report['stop']['command'][-1]=='dev.tideglass.game')
 check('actual paused/resumed '+cell['scenario'],any(x['state']=='paused' for x in payload['lifecycle_events']) and payload['lifecycle_events'][-1]['state']=='resumed')
 obs=payload['plan_observation'];plan=payload['plan']
 check('actual saved/game state equality '+cell['scenario'],obs['saved_payload']==obs['game_payload'])
 check('actual saved payload digest '+cell['scenario'],sha(json.dumps(obs['saved_payload'],separators=(',',':'),ensure_ascii=False).encode())==plan['saved_payload_sha256'])
 mutations=[('wrong run',lambda x:x.update(run_id=x['run_id']+'-wrong')),('incomplete',lambda x:x.update(completed=False))]
 if cell['scenario']=='delivery':
  check('actual delivered exact Focus body',payload['delivered_records']==[{'id':77101,'title':'A light in the harbor','body':plan['body']}])
  check('five minute actual interval',payload['returned_elapsed_ms']-payload['scheduled_elapsed_ms']>=300000 and payload['returned_utc_ms']>=plan['due_utc_ms'])
  check('actual return cancellation',payload['return_pending_ids']==[] and payload['return_active_ids']==[])
  mutations += [('missing actual delivery',lambda x:x.update(delivered_records=[])),('wrong actual body',lambda x:x['delivered_records'][0].update(body='wrong')),('pending after return',lambda x:x.update(return_pending_ids=[77101]))]
 else:
  check('actual allowed to denied',payload['permission_after_opt_in']=='allowed' and payload['permission_after_revoke']=='denied')
  check('actual revoked cancellation/retry',payload['revoke_pending_ids']==[] and payload['revoked_opt_in_stays_disabled'] is True)
  mutations += [('permission still allowed',lambda x:x.update(permission_after_revoke='allowed')),('pending after revoke',lambda x:x.update(revoke_pending_ids=[77101])),('retry reenabled',lambda x:x.update(revoked_opt_in_stays_disabled=False))]
 for label,mutate in mutations:
  bad=copy.deepcopy(payload);mutate(bad);errors=ns['payload_errors'](bad,report,log);check('reject '+cell['scenario']+':'+label,bool(errors));negatives.append({'scenario':cell['scenario'],'mutation':label,'errors':errors})
 check('reject late exception '+cell['scenario'],bool(ns['payload_errors'](payload,report,log+'\nflutter: Unhandled Exception: negative control\n')))
 rows.append({'scenario':cell['scenario'],'basis':'Fresh independent archived pure-verifier replay plus arithmetic and operator-image inspection','verification':str(p.relative_to(R)),'sha256':cell['verification_sha256'],'permission_after':payload.get('permission_after_revoke',payload.get('permission_after_opt_in')),'real_background_ms':payload.get('returned_elapsed_ms',0)-payload.get('scheduled_elapsed_ms',0) if cell['scenario']=='delivery' else None,'plan':plan})
# Keep the old failures and the explicit goal-pause interruption distinct.
for f,expected in [
('release/qa/settings-native-20261023T081631.942859Z/reminder-initial-seal.json','b03d259a4e6a4a79d2d63b00b5075eb18eb59e1a878b30146d4bb8a04fd18303'),
('release/native-proof/execution-3b00-20261023T040612.562001Z/pause-checkpoint-20261023T090332.189131Z/checkpoint.json',None)]:
 raw=read(f)
 if expected:check('prior independent seal',sha(raw)==expected)
 else:check('pause classification preserved',json.loads(raw)['status']=='paused_incomplete_by_director_request')
after={f:sha((R/f).read_bytes()) for f in pins};check('all review inputs unchanged',after==pins)
report={'checks_passed':len(checks),'checks':checks,'negative_mutations':negatives,'rows':rows,'pins':pins,'native_or_Flutter_calls':False,'actual_phone_five_supported':True,'Android_permission_delivery_cases':'pending supported actual UI; default reviewed separately','M3_05_S26_acceptance':False,'physical_or_banner_visibility_claim':False}
(O/'phone-review-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'negative_mutations':len(negatives),'pins':len(pins)}))
