from pathlib import Path
import json, hashlib, difflib
R=Path('/Users/csys/Desktop/ibicot/idle'); O=Path(__file__).resolve().parent
pins={}; checks=[]
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p); p=p if p.is_absolute() else R/p
 b=p.read_bytes(); pins[str(p.relative_to(R))]=sha(b); return b
def jread(p):return json.loads(read(p))
def check(name,value,detail=None):
 checks.append({'name':name,'passed':bool(value),'detail':detail}); assert value,(name,detail)
def dump(name,value):(O/name).write_text(json.dumps(value,indent=2)+'\n')
candidate='.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
manifest=jread(candidate+'/manifest.json'); production=sorted([str(p.relative_to(R)) for p in (R/'game/mobile/lib').glob('*.dart')]+['game/mobile/pubspec.yaml','game/mobile/pubspec.lock','game/mobile/android/app/src/main/AndroidManifest.xml','game/mobile/ios/Runner/Info.plist','game/mobile/ios/Runner/AppDelegate.swift','game/mobile/android/app/src/main/kotlin/com/tideglass/game/MainActivity.kt'])
# Use actual manifest inventory for native source spelling; no invented source path.
production=[p for p in production if (R/p).exists()]
for p in production:
 b=read(p); expected=manifest['source_sha256'][p]
 check('candidate-production:'+p,sha(b)==expected)
 check('archived-production:'+p,sha(read(Path(manifest['source_directory'])/p))==expected)
for p in sorted((R/'game/mobile/test').glob('*test.dart')):
 if any(n in p.name for n in ['notification','reminder','audio','localization','help','public_link','bootstrap','client','number']):read(p)
for p in ['game/mobile/.dart_tool/package_config.json','game/mobile/.flutter-plugins-dependencies','tool/flutter','.tooling/flutter/bin/cache/dart-sdk/bin/dart', 'implementation/program.json','implementation/scope_requirements.json','v1_backlog.json','docs/quality/V1_QUALITY_PROTOCOL.md']:
 if (R/p).exists():read(p)
program=jread('implementation/program.json'); items={x['id']:x for x in program['items']}
check('M3-05-original-criterion',items['M3-05']['source_acceptance']=='Text scale, number notation, motion/audio controls, input navigation and opt-in quiet-hour notifications function across targets.')
check('M3-05-original-deps',items['M3-05']['source_acceptance_dependencies']==['M1-05','M3-01'])
check('M3-05-deps-accepted',all(items[x]['status']=='accepted' for x in items['M3-05']['source_acceptance_dependencies']))
check('M3-05-not-accepted',items['M3-05']['status']=='in_progress')
ui='release/qa/integration-current-ui-20261021T133115456638Z'
idx=jread(ui+'/evidence-index.json')
for p,h in idx.items():check('ui-archive:'+p,sha(read(ui+'/'+p))==h)
uv=jread(ui+'/verification.json'); us=jread(ui+'/QA_SUMMARY.json'); check('independent-ui-invocations',us['total']==54)
changes=[]
for p,h in uv['source_before'].items():
 if not p.startswith('game/mobile/lib/'):continue
 current=sha(read(p)); old=read(ui+'/source/'+p)
 check('historical-ui-source:'+p,sha(old)==h)
 if current!=h:
  changes.append(p); (O/(Path(p).stem+'-current-ui.diff')).write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),read(p).decode().splitlines(True),fromfile=ui+'/source/'+p,tofile=p)))
check('exact-ui-production-differences',changes==['game/mobile/lib/app.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/help_screen.dart','game/mobile/lib/main.dart','game/mobile/lib/native_services.dart','game/mobile/lib/service_settings.dart','game/mobile/lib/story_screen.dart','game/mobile/lib/study_gate.dart'],changes)
# Settings and preference/lifecycle portions in the changed App remain exact.
old=read(ui+'/source/game/mobile/lib/app.dart').decode(); current=read('game/mobile/lib/app.dart').decode()
sections=[('preferences','class ClientPreferences','class TideglassApp'),('lifecycle','  Future<void> _resume()', '  void updatePrefs'),('preference update and builder','  void updatePrefs','  Widget _harbor'),('settings','  Future<void> _settings','  Widget _page')]
section_rows=[]
for name,start,end in sections:
 if start not in old or end not in old:continue
 a=old[old.index(start):old.index(end,old.index(start))]; b=current[current.index(start):current.index(end,current.index(start))]
 check('unchanged-App-section:'+name,a==b);section_rows.append({'name':name,'start':start,'end':end,'sha256':sha(a.encode())})
rem='release/qa/integration-reminders-initial-20261016T115431767720Z'; rv=jread(rem+'/verification.json'); snap=jread(rem+'/snapshot.json')
read(rem+'/REMINDERS_REVIEW.md')
for p,h in snap['files'].items(): check('reminder-archive:'+p,sha(read(Path(snap['workspace'])/p))==h)
for p in ['game/mobile/lib/notification_service.dart','game/mobile/lib/reminder_lifecycle.dart']:
 check('same-reminder-runtime:'+p,sha(read(p))==snap['files'][p])
check('historical-reminder-pass-counts',sum(rv['test_passes'][k] for k in rv['test_passes'] if isinstance(rv['test_passes'][k],int))>=30,rv['test_passes'])
check('historical-reminder-departures',rv['timezone_departure_cases']==384)
check('reminder-native-limit',rv['actual_os_delivery_tested'] is False)
# Fully executed current candidate host gate qualifies current test files, without a broad rerun.
br='release/native-proof/20261023T040548.338966Z'; build=jread(br+'/build-report.json')
check('current-host-gate',build['host_test_gate']=='passed' and not build['failed_host_checks'])
check('host-candidate-binding',build['candidate_fingerprint']==manifest['source_fingerprint'])
for name in ['mobile-analyze','mobile-test']:
 check('host-exit:'+name,build['host_checks'][name]['exit_code']==0);log=read(br+'/'+name+'.log').decode(errors='replace')
 if name=='mobile-test':check('host-test-success', 'All tests passed!' in log)
# Existing current all-condition Help path evidence was independently checked for M2-02.
on='release/qa/onboarding-clause-20261023T040451.613635Z'; ov=jread(on+'/verification.json');read(on+'/M2_02_RECOMMENDATION.md')
check('independent-Help-review',ov['all_checks_passed'] and len(ov['existing_content_help_rows'])==36)
for p in ['game/mobile/lib/help_screen.dart','game/mobile/lib/help_content.dart']:
 check('current-Help-source:'+p,sha(read(p))==ov['source_before_sha256'][p])
# Recheck full12 content terminal evidence and actual Help rows, not merely the summary.
cm='release/content-presentation/full-matrix-repaired-20261021T143209447416Z'; mv=jread(cm+'/verification.json')
check('content-12',len(mv['conditions'])==12)
help_rows=[]
for condition in mv['conditions']:
 d=condition['directory']
 for p,h in condition['evidence_sha256'].items():check('content-artifact:'+d+'/'+p,sha(read(d+'/'+p))==h)
 obs=jread(d+'/observations.json'); rows=obs if isinstance(obs,list) else obs.get('rows',[])
 # Actual schema is retained separately for inspection without guessing acceptance fields.
 help_rows.append({'condition':condition['condition'],'observation_schema':list(obs) if isinstance(obs,dict) else 'list','row_count':len(rows)})
font='release/qa/qa-reset-20261023T025256.370588Z'; fv=jread(font+'/verification.json'); read(font+'/FONT_NOTICE_REVIEW.md')
for p,h in fv['evidence_sha256'].items():
 target=p if (R/p).exists() else font+'/'+p
 check('font-evidence:'+p,sha(read(target))==h)
check('font-known-overlap-preserved',fv['font_sdk_overlap']=='preserved_nonblocking_original_requirement_not_full_tile_five_point_pass')
dump('settings-inputs-before.json',pins);dump('settings-source-review.json',{'checks':checks,'passed':all(x['passed'] for x in checks),'candidate':manifest['source_fingerprint'],'source_files':len(pins),'App_sections':section_rows,'old_ui_changed_files':changes,'content_observation_schema':help_rows,'new_runtime_tests_run':0,'native_reminders_pending':True,'original_status_edits':False})
print(json.dumps({'passed':True,'checks':len(checks),'pins':len(pins),'new_runtime_tests':0}))
