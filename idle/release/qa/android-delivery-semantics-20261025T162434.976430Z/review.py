from pathlib import Path
import ast,json,hashlib,re,types
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;pins={};checks=[]
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
node=next(n for n in ast.parse(read('release/qa/settings-native-20261023T081631.942859Z/replay_reminder_initial.py')).body if isinstance(n,ast.FunctionDef) and n.name=='pure');exec(compile(ast.Module(body=[node],type_ignores=[]),'preserved-pure-extractor','exec'))
P=R/'release/native-notifications/integration-android-20261025T161006684764Z';CP='release/native-notifications/resume-20261025-20261025T150516.353584Z/android-delivery-observed2-checkpoint.json';cp=j(CP);r=j(P/'verification.json');p=j(P/'result.json');log=read(P/'run.log').decode();ns=pure(P)
check('exact failed checkpoint',sha(read(CP))=='693b28281dee21f5a397d6e8510e7a3244f176c3995a6b704abb63fe2a5f11fc')
check('exact failed report',sha(read(P/'verification.json'))==cp['verification_sha256']=='96e56315397749e294f1c03e7c0fb2c61a978118c8d5648b2566fad6a03da9fb')
for n,h in r['evidence_sha256'].items():check('archive '+n,Path(n).name==n and sha(read(P/n))==h==cp['native_evidence_sha256'][n])
for n,h in cp['late_operator_files_sha256'].items():check('late archive '+n,Path(n).name==n and sha(read(P/n))==h)
errors=ns['payload_errors'](p,r,log);check('strict end failure reproduced',bool(errors) and set(errors)<=set(r['errors']) and r['passed'] is False and r['exit_code']==1)
check('actual native delivery and cancellation facts',p['completed'] is True and p['lifecycle_callback_failures']==[] and p['delivered_records']==[{'id':77101,'title':'A light in the harbor','body':'Focus is available for your next constellation. Return whenever you like.'}] and p['return_pending_ids']==[] and p['return_active_ids']==[] and p['actual_background_and_return'])
check('real duration retained',p['returned_elapsed_ms']-p['scheduled_elapsed_ms']==601745)
check('actual lifecycle bound',ns['actual_departure_return'](p['lifecycle_events'],p['actions'],'background_app_now_using_os_home',0))
check('end invariant failure explicit','WidgetTester._verifySemanticsHandlesWereDisposed' in log and 'A SemanticsHandle was active at the end of the test.' in log and 'Some tests failed.' in log)
check('source and installed artifact binding',r['frozen_source_unchanged'] and r['generated_harness_matches'] and not r['production_differences_after'] and not r['source_differences_during_run'] and r['installed_artifact']['matches_host_artifact'])
receipts=j(P/'operator-return-receipts.json');tap=j(P/'operator-return-action.json');stamp=lambda text:datetime.fromisoformat(text).timestamp()*1000
start=stamp(receipts[0]['utc']);end=stamp(receipts[1]['utc']);returned=p['returned_utc_ms']
check('real return is within new UiAutomation interval',receipts[0]['argv'][-3:]==['uiautomator','dump','/dev/tty'] and stamp(tap['utc'])<start<returned<end)
check('pre-action grounding retained',tap['observed_node']['text']=='Tideglass' and tap['pre_image_sha256']==sha(read(P/'operator-delivered-home.png')) and tap['pre_hierarchy_sha256']==sha(read(P/'operator-delivered-home-hierarchy.txt')))
flutter='.tooling/flutter/';sem=read(flutter+'packages/flutter/lib/src/semantics/binding.dart').decode();widget=read(flutter+'packages/flutter_test/lib/src/widget_tester.dart').decode();binding=read(flutter+'packages/flutter_test/lib/src/binding.dart').decode();java=read(flutter+'engine/src/flutter/shell/platform/android/io/flutter/view/AccessibilityBridge.java').decode();channel=read(flutter+'engine/src/flutter/shell/platform/android/io/flutter/embedding/engine/systemchannels/AccessibilityChannel.java').decode();version=j(flutter+'bin/cache/flutter.version.json')
check('pinned Flutter version',version['frameworkRevision']=='abaf9c523780a608bd46686fd5e53740a07077f8' and version['frameworkVersion']=='3.47.7')
check('platform owns separate semantics handle','if (platformDispatcher.semanticsEnabled)' in sem and '_semanticsHandle ??= ensureSemantics();' in sem and '_semanticsHandle?.dispose();' in sem)
check('framework records and retains leak gate','tester._recordNumberOfSemanticsHandles();' in widget and 'binding.debugOutstandingSemanticsHandles +' in widget and '_currentSemanticsHandles - knownWebEngineLeakForLiveTestsCorrection >' in widget)
check('Android forwards accessibility enable to engine','accessibilityChannel.onAndroidAccessibilityEnabled();' in java and 'flutterJNI.setSemanticsEnabled(true);' in channel and 'flutterJNI.setSemanticsEnabled(false);' in channel)
aosp=read(O/'aosp/DumpCommand.java').decode();check('API35 dump owns external automation session','automationWrapper.connect();' in aosp and 'finally {' in aosp and 'automationWrapper.disconnect();' in aosp)
check('archived harness has no manual semantics handles','ensureSemantics(' not in read(P/'harness.dart').decode())
read('game/mobile/integration_test/native_reminders_test.dart');read('tool/verify_native_reminders.py');read('docs/quality/android-ui-operator.md');read('implementation/program.json');read('implementation/scope_requirements.json')
check('all pins unchanged',all(sha((R/f).read_bytes())==h for f,h in pins.items()))
out={'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'pins':pins,'pure_errors':errors,'timing_utc_ms':{'return_tap_command_completed':stamp(tap['utc']),'uiautomator_command_started':start,'native_returned':returned,'next_command_started_upper_bound':end},'inference':'External UiAutomation accessibility request explains an SDK-owned platform semantics handle at teardown; actual allocation-level handle trace was not recorded. Fresh strict pass required.','recommendation':'Refine operator only: no UiAutomation after app-icon return until terminal framework result. No source or assertion changes.','runtime_or_device_execution':False,'native_pass_claim':False}
(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':len(checks),'pins':len(pins),'verification_sha256':sha((O/'verification.json').read_bytes())}))
