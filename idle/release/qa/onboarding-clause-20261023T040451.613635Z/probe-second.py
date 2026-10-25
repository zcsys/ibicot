from pathlib import Path
import json, hashlib, difflib, re
ROOT=Path('/Users/csys/Desktop/ibicot/idle')
OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda f:json.loads((ROOT/f).read_text())
checks=[]; evidence={}
def check(name,condition,detail=None):
 checks.append({'name':name,'pass':bool(condition),'detail':detail})
 if not condition: raise AssertionError(name)
def pin(f):
 p=ROOT/f; evidence[str(f)]=sha(p.read_bytes());return p
sources=['v1_backlog.json','implementation/program.json','implementation/scope_requirements.json','game/mobile/lib/app.dart','game/mobile/lib/strings.dart','game/mobile/lib/presentation.dart','game/mobile/lib/help_content.dart','game/mobile/lib/help_screen.dart','game/mobile/lib/bootstrap.dart','game/mobile/lib/main.dart','game/mobile/lib/native_services.dart','game/mobile/lib/service_support_screen.dart','game/mobile/lib/support_screen.dart','game/mobile/lib/support_service_bridge.dart','game/mobile/lib/service_cosmetics.dart','game/mobile/lib/cosmetics_screen.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/game_controller.dart','game/mobile/lib/game_telemetry.dart','game/mobile/lib/reminder_lifecycle.dart','game/mobile/lib/rechart_estimate.dart','game/mobile/test/client_test.dart','game/mobile/test/native_services_test.dart','game/mobile/test/help_test.dart','game/mobile/test/localization_test.dart','game/mobile/test/content_presentation_test.dart','game/mobile/test/qa_client_shell_clauses_test.dart','game/mobile/test/qa_rechart_forecast_review_test.dart','game/mobile/test/bootstrap_test.dart','game/mobile/test/bootstrap_service_configuration_test.dart']
source_before={}
for f in sources:
 p=pin(f);source_before[f]=evidence[f];target=OUT/'source'/f;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
(OUT/'source-before.json').write_text(json.dumps(source_before,indent=2)+'\n')
program=read('implementation/program.json');items={i['id']:i for i in program['items']};original={i['id']:i for i in read('v1_backlog.json')['items']}
criterion='Teach costs, production, retained progress and automation with skippable guidance; no monetization prompt interrupts onboarding.'
check('M2-02 exact original clause',items['M2-02']['source_acceptance']==criterion and original['M2-02']['acceptance']==criterion)
check('M2-02 assigned QA reviewer',items['M2-02']['reviewer']=='qa_release')
check('original prerequisite identities',items['M2-02']['source_acceptance_dependencies']==['M1-05','M2-01'])
for i in ['M1-05','M2-01']:check(i+' prerequisite accepted',items[i]['status']=='accepted')
(OUT/'original-item-and-prerequisites.json').write_text(json.dumps({i:items[i] for i in ['M2-02','M1-05','M2-01']},indent=2)+'\n')
old='release/qa/integration-services-repaired-20261016T114721906724Z'
snapshot=read(old+'/snapshot.json');index=read(old+'/evidence-index.json')
for name in ['snapshot.json','evidence-index.json','verification.json','INTEGRATION_REVIEW.md','mobile-test.log']:pin(old+'/'+name)
check('named onboarding log exact historical index',evidence[old+'/mobile-test.log']==index['files']['mobile-test.log'])
events=[]
for line in (ROOT/old/'mobile-test.log').read_text().splitlines():
 try:events.append(json.loads(line))
 except json.JSONDecodeError:pass
named=[]
for phrase in ['onboarding action moves the first purchase into view','unconfigured guest initialization touches neither secure store nor billing']:
 start=next(e for e in events if e.get('type')=='testStart' and e['test']['name']==phrase)
 done=next(e for e in events if e.get('type')=='testDone' and e['testID']==start['test']['id'])
 check('historical named success: '+phrase,done['result']=='success' and not done['skipped'])
 named.append({'testStart':start,'testDone':done})
for f in ['game/mobile/test/client_test.dart','game/mobile/test/native_services_test.dart','game/mobile/lib/app.dart','game/mobile/lib/strings.dart']:
 p=Path(snapshot['workspace'])/f;check('historical archived bytes: '+f,sha(p.read_bytes())==snapshot['files'][f]);pin(str(p))
 if f.endswith('_test.dart'):check('unchanged exact executed test: '+f,p.read_bytes()==(ROOT/f).read_bytes())
oldapp=(Path(snapshot['workspace'])/'game/mobile/lib/app.dart').read_text();app=(ROOT/'game/mobile/lib/app.dart').read_text()
def section(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
bridges=[]
for label,a,b,normalize in [
 ('preference schema','class ClientPreferences','class TideglassApp',False),
 ('dismiss and scroll callbacks','  void updatePrefs(','  String number(',False),
 ('optional introductory panel','          if (!prefs.onboardingDismissed)','          if (game.state.charts >= BigInt.from(10))',True)]:
 before=section(oldapp,a,b);after=section(app,a,b)
 if normalize:after=after.replace('LocalizedText(', 'Text(')
 check('historical onset bridge: '+label,before==after)
 bridges.append({'section':label,'old_sha256':sha(before.encode()),'comparison_sha256':sha(after.encode()),'normalization':'LocalizedText wrapper -> Text only' if normalize else 'none'})
oldstrings=(Path(snapshot['workspace'])/'game/mobile/lib/strings.dart').read_text();strings=(ROOT/'game/mobile/lib/strings.dart').read_text()
for name in ['introduction','introductionBody','introductionDismiss']:
 pattern=rf'  static const {name} =.*?;';a=re.search(pattern,oldstrings,re.S).group();b=re.search(pattern,strings,re.S).group();check('unchanged intro copy '+name,a==b)
ui='release/qa/integration-current-ui-20261021T133115456638Z';u=read(ui+'/verification.json')
for name in ['verification.json','CURRENT_UI_REVIEW.md','QA_SUMMARY.json','navigation-corrected/verification.json']:pin(ui+'/'+name)
for run in u['runs']:
 if not run['name'].startswith(('public-help','critical-phone200')):continue
 f=ui+'/'+run['name']+'.log';pin(f);check('independent current Help/critical log '+run['name'],run['exit_code']==0 and not run['source_differences'] and evidence[f]==run['log_sha256'])
for f in ['game/mobile/lib/help_content.dart','game/mobile/lib/help_screen.dart','game/mobile/lib/strings.dart','game/mobile/lib/presentation.dart','game/mobile/test/client_test.dart','game/mobile/test/native_services_test.dart','game/mobile/test/help_test.dart','game/mobile/test/localization_test.dart']:
 archived=ROOT/ui/'source'/f;pin(str(archived));check('archived executed UI input '+f,sha(archived.read_bytes())==u['source_before'][f])
 if f != 'game/mobile/lib/help_screen.dart':check('current unchanged executed UI input '+f,u['source_before'][f]==source_before[f])
oldhelp=(ROOT/ui/'source/game/mobile/lib/help_screen.dart').read_text();newhelp=(ROOT/'game/mobile/lib/help_screen.dart').read_text()
resolved200=oldhelp.replace('    final scrollHeading = MediaQuery.textScalerOf(context).scale(16) > 24;\n','').replace('appBar: scrollHeading ? AppBar() : readingAppBar(context, title: title),','appBar: AppBar(),').replace('                    if (scrollHeading) ...[\n','').replace('                    ],\n                    ...(article == null','                    ...(article == null')
check('current Help equals previously executed 200-percent branch',re.sub(r'\s+',' ',resolved200)==re.sub(r'\s+',' ',newhelp))
uiapp=(ROOT/ui/'source/game/mobile/lib/app.dart').read_text();check('current UI archived App pin',sha(uiapp.encode())==u['source_before']['game/mobile/lib/app.dart']);pin(ui+'/source/game/mobile/lib/app.dart')
for label,a,b in [('startup and optional guide','class ClientPreferences','  Widget _atlas('),('commercial navigation','  Widget _journal(','  Widget _daily('),('handbook route','  Future<void> _openHandbook(','  Future<void> _localRecoveryActions(')]:
 check('unchanged October21 executed App section '+label,section(uiapp,a,b)==section(app,a,b))
(OUT/'App-current-ui.diff').write_text('\n'.join(difflib.unified_diff(uiapp.splitlines(),app.splitlines(),fromfile=ui+'/source/game/mobile/lib/app.dart',tofile='game/mobile/lib/app.dart'))+'\n')
clauses='release/qa/integration-client-clauses-20261021T143635184485Z'
for f in ['CLAUSE_RECOMMENDATIONS.md','verification.json','source-before.json']:pin(clauses+'/'+f)
c=read(clauses+'/verification.json')
for condition in c['matrix']:
 f=clauses+'/final/'+condition['condition']+'.jsonl';pin(f)
 check('independent real shell condition '+condition['condition'],condition['tests_passed']==1 and condition['source_unchanged'] and evidence[f]==condition['log_sha256'])
for f in ['release/qa/qa-reset-20261023T025256.370588Z/RESET_REVIEW.md','release/qa/qa-reset-20261023T025256.370588Z/verification.json','release/qa/lead-daily-icons-20261023T031715.308630Z/REVIEW.md','release/qa/lead-daily-icons-20261023T031715.308630Z/verification.json','release/qa/lead-automation-acceptance-20261021T143015.491121Z/DECISIONS.md','release/qa/platform-package-clauses-20261021T141913194277Z/PACKAGE_RECOMMENDATIONS.md','release/qa/platform-package-clauses-20261021T141913194277Z/verification.json','release/qa/lead-client-shell-acceptance-20261021T145030.603397Z/DECISIONS.md','release/qa/lead-content-matrix-20261021T144134.921859Z/MATRIX_REVIEW.md']:pin(f)
content='release/content-presentation/full-matrix-repaired-20261021T143209447416Z';matrix=read(content+'/verification.json');pin(content+'/verification.json');help_rows=[]
for cond in matrix['conditions']:
 d=cond['directory']
 for f in ['test.jsonl','observations.json','verification.json']:
  pin(d+'/'+f);check('existing content digest '+d+'/'+f,evidence[d+'/'+f]==cond['evidence_sha256'][f])
 rows=read(d+'/observations.json')['rows']
 for topic in ['play','rechart','away']:
  r=next(r for r in rows if r['route']=='HelpScreen/'+topic)
  check('actual help row '+d+'/'+topic,r['before_sha256']==r['after_sha256'] and all(t['complete_text'] and t['untruncated'] and t['all_lines_in_viewport'] for t in r['texts']) and all(c['minimum_48'] and c['whole_control_visible'] and c['semantic_tap'] and c['hit_points']==5 and c['callback_invoked'] for c in r['controls']))
  help_rows.append({'directory':d,'topic':topic,'condition':r['condition'],'texts':len(r['texts']),'controls':len(r['controls']),'before_sha256':r['before_sha256'],'after_sha256':r['after_sha256'],'current_geometry_bridge':r['condition']['text_percent']==200})
# This is a source/evidence review. The author content matrix is adopted by its existing different-author review, not relabeled as a new execution here.
frozen='release/native-proof/20261023T032749.977866Z';manifest=read(frozen+'/candidate-manifest.json');report=read(frozen+'/build-report.json')
for f in ['candidate-manifest.json','build-report.json','mobile-test.log']:pin(frozen+'/'+f)
for f in sources:
 if not f.startswith('game/mobile/') or f not in manifest['source_sha256']:continue
 p=Path(manifest['source_directory'])/f;check('a052 archived guidance input '+f,sha(p.read_bytes())==manifest['source_sha256'][f])
 if f != 'game/mobile/lib/help_screen.dart':check('a052 current guidance input '+f,manifest['source_sha256'][f]==source_before[f])
 else:check('a052 Help archived equals independent prior Help',p.read_text()==oldhelp)
log=(ROOT/frozen/'mobile-test.log').read_text()
check('a052 unfiltered suite command',report['host_checks']['mobile-test']['command']==['/Users/csys/Desktop/ibicot/idle/tool/flutter','test'])
check('a052 failed suite remains explicitly failed',report['host_checks']['mobile-test']['exit_code']==1 and '+639 -1: Some tests failed.' in log and 'Expected: <2>' in log and 'Actual: <3>' in log)
check('a052 sole listed failure is separate stale calibration fixture',log.split('Failing tests:')[-1].strip().endswith('minimal campaign uses three actual accessible Focus activations; none does not'))
for f in sources:check('review leaves live source/status unchanged '+f,sha((ROOT/f).read_bytes())==source_before[f])
result={'reviewer':'qa_release','scope':'Original M2-02 only','recommendation':'accept','criterion':criterion,'prerequisites':['M1-05','M2-01'],'status_changed':False,'new_flutter_or_device_commands':False,'new_runtime_tests':0,'static_and_evidence_checks':len(checks),'all_checks_passed':all(c['pass'] for c in checks),'source_before_sha256':source_before,'checks':checks,'named_historical_execution':named,'source_bridge':bridges,'existing_content_help_rows':help_rows,'a052_limit':'The combined host gate failed: 639 successes and one stale optional-calibration expectation; it is not an all-pass or export qualification. Named original onboarding success is independently preserved and bridged above.','non_claims':['S05 human comprehension','M2-06 human alpha','S32 human/physical findings','native/store release readiness','other packages or global asset acceptance']}
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'inspected-file-pins.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps({'folder':str(OUT.relative_to(ROOT)),'checks':len(checks),'evidence_files':len(evidence),'verification_sha256':sha((OUT/'verification.json').read_bytes()),'pins_sha256':sha((OUT/'inspected-file-pins.json').read_bytes())},indent=2))
