from pathlib import Path
import ast,json,hashlib,re,copy
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).resolve().parent; pins={};checks=[];rows=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def check(name,value):checks.append({'name':name,'passed':bool(value)});assert value,name
def sha(b):return hashlib.sha256(b).hexdigest()
base='release/native-proof/execution-3b00-20261023T040612.562001Z/'
batches=[('sealed-completed-phone-20261023T044235.533865Z','d7c82bab429c67e26fb2d546ce791b2b70891a54a7e266101cd098d4b6d232f0'),('sealed-android-original-harness-terminal-20261023T055058.407892Z','094ac05b46cb83b531594ce3c494b2a5c34b856c3fadcc29d47c8a5525960acb'),('sealed-ios-tablet-completed-20261023T052930.349369Z','c4a73aeb872cb261a79ae61d3dbc62b1dd8f69a141469ad24335d86f69f92b1e')]
manifest=j('.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/manifest.json')
for folder,pin in batches:
 p=base+folder+'/checkpoint.json';batch=j(p);check('sealed-batch:'+folder,sha(read(p))==pin)
 check('batch-source:'+folder,batch['candidate_fingerprint']==manifest['source_fingerprint'])
 for cell in batch['cells']:
  if cell['scenario'] not in ['seeded','session-start']:continue
  path=Path(cell['verification']);report=j(path);root=path.parent;scenario=cell['scenario'];label=report['label'];key=label+':'+scenario
  check('report-pin:'+key,sha(read(path))==cell['verification_sha256'])
  check('actual-pass:'+key,cell['status']=='passed' and report['passed'] and report['exit_code']==0 and not report['verification_errors'])
  check('production-unchanged:'+key,report['production_inputs_match_snapshot'] and report['source_snapshot_unchanged'] and not report['production_input_differences_after_run'] and not report['harness_source_differences_during_run'])
  for f,h in cell['native_evidence_sha256'].items():
   check('safe-archive-name:'+key+':'+f,Path(f).name==f)
   check('raw-native-pin:'+key+':'+f,sha(read(root/f))==h)
   check('checkpoint-report-pin:'+key+':'+f,report['evidence_sha256'].get(f)==h)
  check('all-report-pins-present:'+key,set(report['evidence_sha256'])<=set(cell['native_evidence_sha256']))
  payload=j(root/'result.json');log=read(root/'run.log').decode(errors='replace');source=read(root/'verify_native.py').decode()
  # Execute only exact pure completion function, not module entry points/device helpers.
  fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='native_log_errors');ns={'re':re}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(root/'verify_native.py'),'exec'),ns)
  errs=ns['native_log_errors']
  check('strict-both-completion:'+key,not errs(log))
  check('late-exception-rejected:'+key,bool(errs(log+'\nflutter: Unhandled Exception: QA negative only\n')))
  missing=re.sub(r'(?m)^.*(?:flutter:|I/flutter\s*\(\s*\d+\):).*All tests passed!.*$','',log)
  check('driver-alone-rejected:'+key,bool(errs(missing)))
  for k,value in [('verification_id',root.name),('candidate_fingerprint',manifest['source_fingerprint']),('harness_sha256',report['harness_sha256']['harness.dart']),('platform',report['platform']),('device_label',label),('scenario',scenario),('run_id',report['run_id'])]:check('payload-identity:'+key+':'+k,payload[k]==value)
  check('real-process:'+key,type(payload['process_id']) is int and payload['process_id']>0)
  if scenario=='session-start':
   probe=payload['audio_probe'];check('eleven-decoders:'+key,len(probe['decoded'])==11 and len({x['asset'] for x in probe['decoded']})==11 and all(x['duration_ms']>0 for x in probe['decoded']))
   check('playback-clock:'+key,probe['state']=='playing' and any(t>0 for t in probe['position_samples_ms']))
   check('native-production-audio-check:'+key,'Production native audio driver initialized, switched all three tracks and respected foreground cue gating' in payload['checks'])
  else:
   check('seeded-real-purchase-reset-checks:'+key,any('Rechart' in x or 'rechart' in x for x in payload['checks']) and any('purchase' in x.lower() for x in payload['checks']))
  rows.append({'target':label,'scenario':scenario,'native_platform':report['platform'],'device':report['device'],'report':str(path.relative_to(R)),'report_sha256':sha(read(path)),'process_id':payload['process_id'],'checks':payload['checks'],'audio_probe':payload.get('audio_probe'),'provenance':payload['provenance'],'physical_human_audibility_claim':False})
check('six-selected-cells',len(rows)==6)
after={p:sha((R/p).read_bytes()) for p in pins};check('input-pins-unchanged',after==pins)
for name,value in [('settings-native-baseline-inputs-before.json',pins),('settings-native-baseline-inputs-after.json',after),('settings-native-baseline-review.json',{'checks':checks,'rows':rows,'passed':True,'native_commands_run':False,'flutter_run':False,'reminder_evidence_included':False,'release_acceptance':False})]:(O/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(checks),'cells':len(rows),'negative_controls':12,'pins':len(pins)}))
