"""Synthetic finalizer qualification of the exact staged bridge; no device calls."""
import ast, copy, hashlib, importlib.util, json, sys
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path('/Users/csys/Desktop/ibicot/idle')
OUT=Path(__file__).resolve().parent
AUTHOR=ROOT/'release/native-privacy/android-probe-binding-staged-20261023T052041.391323Z'
CANDIDATE=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
spec=importlib.util.spec_from_file_location('independent_bridge_finalizer',AUTHOR/'runtime_observation.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
results=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def check(name,value):
    assert value,name
    results.append({'check':name,'passed':True})

original=(AUTHOR/'collector-before.py').read_text()
staged=(AUTHOR/'runtime_observation.py').read_text()
oldtree=ast.parse(original);newtree=ast.parse(staged)
oldfunctions={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
newfunctions={n.name:ast.dump(n,include_attributes=False) for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
changed=[name for name in oldfunctions if oldfunctions[name]!=newfunctions.get(name)]
check('only source binding + its two call sites change',set(changed)=={'source_binding','validate_source_binding','collect'} and oldfunctions.keys()==newfunctions.keys())
check('full finalizer and every observation/parser/limit/host guard AST unchanged',all(oldfunctions[n]==newfunctions[n] for n in oldfunctions if n not in changed))
oldrunner=(CANDIDATE/'source/tool/verify_current_runtime.py').read_bytes()
newrunner=(ROOT/'release/qa/native-android-probe-repair-staged-20261023T051836.017647Z/verify_current_runtime.py').read_bytes()
check('exact original and actual runner hashes',o.sha(oldrunner)==o.ANDROID_PROBE_BRIDGE['candidate_runner_sha256'] and o.sha(newrunner)==o.ANDROID_PROBE_BRIDGE['executed_runner_sha256'])
check('exact one replacement reconstructs native author revision',oldrunner.count(o._PROBE_BEFORE)==1 and oldrunner.replace(o._PROBE_BEFORE,o._PROBE_AFTER,1)==newrunner)

def prepare(name):
    base=OUT/'fixtures'/name;base.mkdir(parents=True)
    evidence=base/'synthetic-bridge-proof';evidence.mkdir()
    output=base/'observation';output.mkdir()
    for archive,relative in o.SOURCE_ARCHIVES.items():
        (evidence/archive).write_bytes(newrunner if archive=='runner.py' else (CANDIDATE/'source'/relative).read_bytes())
    manifest,ctx=o.context_for(CANDIDATE,evidence,'emulator-5556')
    ctx.update(scenario='runtime-study-default',run_id='qa-bridge',device_label='android')
    opened=dict(ctx,process_id=123,fixture_directory='/data/user/0/dev.tideglass.game/files/native-current-verification/android-qa-bridge/study',mode='default-unprovisioned',window_id=evidence.name+'-privacy',maximum_ms=20000,native_elapsed_us=2,native_utc_ms=100000)
    closed=dict(opened,native_elapsed_us=15000002,native_utc_ms=115000)
    prefix='I/flutter ( 123): TIDEGLASS_PRIVACY_WINDOW_OPEN '+json.dumps(opened)+'\n'
    log=prefix+'I/flutter ( 123): TIDEGLASS_PRIVACY_WINDOW_CLOSE '+json.dumps(closed)+'\nI/flutter ( 123): 00:20 +1: All tests passed!\nAll tests passed.\n'
    payload=dict(ctx,process_id=123,completed=True,privacy_observation_window={'opened':opened,'closed':closed})
    (evidence/'run.log').write_text(log);write(evidence/'result.json',payload)
    binding,archives=o.source_binding(CANDIDATE,evidence,manifest,platform='android')
    for name,data in archives.items():(output/name).write_bytes(data)
    verification=dict(ctx,candidate_path=str(CANDIDATE),source_pins=binding['native_source_sha256'],label='android',device='emulator-5556',passed=True,status='passed',exit_code=0,verification_errors=[],native_process_id=123,source_snapshot_unchanged=True,source_changes_during_run=[],production_input_differences_after_run=[],privacy_observation_enabled=True,command=['--dart-define=TIDEGLASS_PRIVACY_OBSERVATION=true'],evidence_sha256={p.name:h(p) for p in evidence.iterdir()})
    write(evidence/'verification.json',verification)
    (output/'open-prefix.log').write_text(prefix)
    identity={'pid':123,'uid':10231,'start_ticks':99,'boot_id':'12345678-1234-1234-1234-123456789abc','package':o.BUNDLE,'uid_scope':'synthetic package UID plus exact PID'}
    report=dict(status='collected-pending-native-completion',errors=[],native_evidence=str(evidence),candidate=str(CANDIDATE),source_binding=binding,context=ctx,device='emulator-5556',opened=opened,open_prefix_sha256=o.sha(prefix.encode()),process_identity=identity,opened_observed_ns=1,collector_sha256=o.COLLECTOR_SHA256,samples=[dict(process_identity=identity,started_ns=2,finished_ns=3,started_utc_ms=100001,finished_utc_ms=114999,sockets={'status':'observed','rows':[]},storage={'status':'unavailable','reason':'Synthetic fixture preserves actual Android storage limitation'})])
    write(output/'observation.json',report)
    return evidence,output,verification,report

def forbidden(*args,**kwargs):raise AssertionError('External execution forbidden in independent finalizer probe')
with patch.object(o.subprocess,'run',forbidden),patch.object(o.subprocess,'Popen',forbidden),patch.object(o.os,'system',forbidden):
    evidence,output,verification,report=prepare('positive')
    result=o.finalize(output,ROOT)
    check('complete bridged finalizer admits only partial Android sample',result['status']=='finalized-partial-observation' and result['paired_socket_storage_samples']==0 and result['storage_statuses']==['unavailable'])
    check('exact bridge retained with both runner archives',result['source_binding']['verification_tool_bridge']==report['source_binding']['verification_tool_bridge'] and (output/'candidate-native-runner.py').read_bytes()==oldrunner and (output/'native-runner.py').read_bytes()==newrunner)
    check('completion verifier candidate-exact',result['completion_verifier_sha256']==h(CANDIDATE/'source/tool/verify_native.py'))
    check('no traffic absence or release acceptance',result['traffic_absence_claim'] is False and result['release_acceptance'] is False)
    for defect in ['old-runner-pin','missing-bridge','original-archive-modified','late-sample','native-failure','driver-failure']:
        evidence,output,verification,report=prepare(defect)
        if defect=='old-runner-pin':
            verification['source_pins']=dict(verification['source_pins'],**{'runner.py':o.sha(oldrunner)})
        if defect=='missing-bridge':del report['source_binding']['verification_tool_bridge']
        if defect=='original-archive-modified':(output/'candidate-native-runner.py').write_bytes(oldrunner+b'\n')
        if defect=='late-sample':report['samples'][0]['finished_utc_ms']=115001
        if defect in ['native-failure','driver-failure']:
            data=(evidence/'run.log').read_text()
            if defect=='native-failure':data+='E/flutter ( 123): [ERROR:flutter/runtime/dart_vm_initializer.cc(40)] Unhandled Exception: synthetic failure\n'
            else:data=data.replace('All tests passed.\n','Driver failed.\n')
            (evidence/'run.log').write_text(data);verification['evidence_sha256']['run.log']=h(evidence/'run.log')
        write(evidence/'verification.json',verification);write(output/'observation.json',report)
        try:o.finalize(output,ROOT)
        except ValueError as error:
            check('reject '+defect,not (output/'finalization.json').exists())
            results[-1]['reason']=str(error)
        else:raise AssertionError('incorrectly admitted '+defect)
write(OUT/'independent-results.json',{'checks':results,'all_passed':True,'positive':'synthetic exact-3b00 Android bridge, partial storage limitation','negative_finalizers':6,'actual_native_or_device_calls':0})
print(json.dumps({'passed':True,'checks':len(results),'negative_finalizers':6,'actual_native_calls':0}))
