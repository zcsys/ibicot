from pathlib import Path
import difflib,hashlib,json,shutil,re
O=Path(__file__).resolve().parent;R=O.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((O/'baseline.json').read_text());checks={}
for group,pins in b.items():
 checks[group]={p:sha(R/p)==digest for p,digest in pins.items()}
 assert all(checks[group].values()),(group,[p for p,v in checks[group].items() if not v])
paths={'platform_smoke_test.dart':'game/mobile/integration_test/platform_smoke_test.dart','native_recording.py':'tool/native_recording.py','native_integration_driver.dart':'tool/native_integration_driver.dart'}
patch=[];pins={}
for name,target in paths.items():
 old=O/'before'/name;new=O/'staged'/name
 patch+=list(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='a/'+target,tofile='b/'+target))
 pins[target]={'expected_live_before_sha256':sha(old),'staged_path':str(new.relative_to(R)),'staged_sha256':sha(new)}
(O/'android-capture.patch').write_text(''.join(patch))
old=(O/'before/platform_smoke_test.dart').read_text();new=(O/'staged/platform_smoke_test.dart').read_text()
def gallery(s):a=s.index('void captureGalleryScenario(');z=s.index('\nvoid naturalScenario(',a);return s[:a],s[a:z],s[z:]
op,og,os=gallery(old);np,ng,ns=gallery(new);assert op==np and os==ns
assert 'convertFlutterSurfaceToImage' not in ng
assert re.findall(r'await until\(const Duration\(seconds: (\d+)\)\);',og)==re.findall(r'await until\(const Duration\(seconds: (\d+)\)\);',ng)==['4','8','14','20','25']
assert og[og.index('    final catalogue ='):og.index('    if (Platform.isAndroid) await binding.convertFlutterSurfaceToImage();')]==ng[ng.index('    final catalogue ='):ng.index('    await pumpNativeUi(tester);',ng.index('    final catalogue ='))]
a='    Future<void> tap(Finder target) async {';z='    await until(const Duration(seconds: 4));'
assert og[og.index(a):og.index(z)]==ng[ng.index(a):ng.index(z)]
for line in ["    final beforeCount = subject.state.counts.first;","    await tap(find.byKey(const ValueKey('buy-0')));","    expect(subject.state.counts.first, beforeCount + 1);","    await tester.pageBack();","    expect(captureBinding.routedTestPointerEvents, greaterThan(0));","    expect(tester.takeException(), isNull);"]:
 assert line in og and line in ng
assert "await binding.takeScreenshot('$label-capture-$screen');" in ng
od=(O/'before/native_integration_driver.dart').read_text();nd=(O/'staged/native_integration_driver.dart').read_text();k='      for (final raw in screenshots)';assert od[od.index(k):]==nd[nd.index(k):]
native=(O/'staged/native_recording.py').read_text();assert "if not 15 <= metadata['duration_seconds'] <= 30:" in native and "'--time-limit', '27', self.remote" in native
assert "pidof" not in native and "pkill" not in native
checks['source_assertions']={'outside_gallery_harness_byte_identical':True,'seeded_state_and_production_widget_identical':True,'real_4_8_14_20_25_schedule_identical':True,'hit_tested_tap_helper_identical':True,'purchase_and_pointer_and_exception_assertions_preserved':True,'ios_screenshot_delegate_preserved':True,'existing_driver_screenshot_loop_identical':True,'duration_gate_15_to_30_unchanged':True,'no_pidof_or_broad_kill':True}
(O/'preservation-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(O/'staged-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps({'staged':pins,'patch_sha256':sha(O/'android-capture.patch'),'tests_sha256':sha(O/'test_staged_recording.py'),'failed_gallery_files_unchanged':len(checks['failed_gallery']),'preservation_passed':True},indent=2))
