"""Read-only adoption and daily/challenge evidence reconciliation."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

R=Path('/Users/csys/Desktop/ibicot/idle')
O=Path(__file__).resolve().parent
pins={}; checks=[]
def read(path):
    p=R/path; data=p.read_bytes(); pins[str(p.relative_to(R))]=hashlib.sha256(data).hexdigest(); return data
def js(path): return json.loads(read(path))
def sha(path): return hashlib.sha256(read(path)).hexdigest()
def check(name, ok): checks.append({'name':name,'pass':bool(ok)})
def out(name, value): (O/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def mapping(d, key): return {x['id']:x for x in d[key]}
def delta(a,b,key,expected):
    check('same top-level '+key,set(a)==set(b) and {k:v for k,v in a.items() if k!=key}=={k:v for k,v in b.items() if k!=key})
    aa=mapping(a,key);bb=mapping(b,key);check('same record order '+key,[x['id'] for x in a[key]]==[x['id'] for x in b[key]])
    actual={i:sorted(k for k in set(aa[i])|set(bb[i]) if aa[i].get(k)!=bb[i].get(k)) for i in aa if aa[i]!=bb[i]}
    check('exact permitted structural delta '+key,actual==expected)
    return actual

A='release/qa/lead-prestige-foundation-scope-20261023T055040.665045Z'
B='release/qa/lead-persistence-fixtures-adoption-20261023T055444.443133Z'
ad=js(A+'/adoption.json');bd=js(B+'/adoption.json')
for folder,d in [(A,ad),(B,bd)]:
    for name,h in d['pins'].items(): check('adoption retained pin '+folder+'/'+name,sha(folder+'/'+name)==h)
pa=js(A+'/program-before.json');sa=js(A+'/scope-before.json')
pb=js(B+'/program-before.json');sb=js(B+'/scope-before.json')
program=js('implementation/program.json');scope=js('implementation/scope_requirements.json');backlog=js('v1_backlog.json')
out('program-at-review-start.json',program);out('scope-at-review-start.json',scope)
check('first adoption program byte-unchanged',sha(A+'/program-before.json')==sha(B+'/program-before.json')==ad['program_unchanged_sha256'])
check('first adoption source scope before and after',sha(A+'/scope-before.json')==ad['scope_before_sha256'] and sha(B+'/scope-before.json')==ad['scope_after_sha256'])
changes={'first_scope':delta(sa,sb,'requirements',{k:['delivery_status','evidence','verification_note'] for k in ['S05','S40','S41']}),
 'second_program':delta(pb,program,'items',{k:['evidence','evidence_note','status'] for k in ['M1-03','M1-08']}),
 'second_scope':delta(sb,scope,'requirements',{'S12':['delivery_status','evidence','verification_note']})}
check('second adoption exact after hashes',sha('implementation/program.json')==bd['program_after_sha256'] and sha('implementation/scope_requirements.json')==bd['scope_after_sha256'])
items=mapping(program,'items');reqs=mapping(scope,'requirements')
for x in backlog['items']:
    item=items[x['id']]
    check('original acceptance/dependencies '+x['id'], item['source_acceptance']==x['acceptance'] and item['source_acceptance_dependencies']==x['dependencies'])
counts={'original_accepted':sum(items[x['id']]['status']=='accepted' for x in backlog['items']),
 'bootstrap_accepted':sum(x['id'].startswith('BOOT-') and x['status']=='accepted' for x in program['items']),
 'scope_verified':sum(x['delivery_status']=='verified' for x in scope['requirements']),
 'scope_count':len(scope['requirements'])}
check('current requested counts',counts=={'original_accepted':20,'bootstrap_accepted':3,'scope_verified':18,'scope_count':44})
for i in ['M1-03','M1-08']:
    check('accepted dependency order '+i,all(items[d]['status']=='accepted' for d in items[i]['source_acceptance_dependencies']))
out('metadata-delta.json',{'changes':changes,'counts':counts,'notes':['First decision prose says 14 sealed outputs; exact adoption and source seal contain 13. No change to actual pin coverage or permitted fields.']})
out('original-readiness-clauses.json',{'items':[items[i] for i in ['M3-01','M3-02','M3-04','M3-08','M4-01','M4-06']], 'scope':[reqs[i] for i in ['S09','S16','S17']]})

def verify_seal(folder):
    d=js(folder+'/seal.json')
    for name,h in d['output_sha256'].items(): check('sealed output '+folder+'/'+name,sha(folder+'/'+name)==h)
    return d
verify_seal('release/qa/prestige-scope-20261023T054525.646309Z')
G='release/qa/gameplay-m1-03-android-20261023T054815140862Z'
verify_seal(G)
gp=js(G+'/inputs-before.json'); metadata_drift={}
for path,h in gp.items():
    actual=sha(path)
    if actual!=h: metadata_drift[path]={'before':h,'after':actual}
check('persistence review current pins differ only adopted metadata',set(metadata_drift)=={str(R/'implementation/program.json'),str(R/'implementation/scope_requirements.json')})
out('prior-review-metadata-drift.json',metadata_drift)
read(G+'/REVIEW.md');js(G+'/verification.json')
D='release/qa/director-m1-08-20261023T054139.868139Z'
d=js(D+'/verification.json');check('designated director review report',sha(D+'/REVIEW.md')==d['review_sha256'])
for path,h in d['pins'].items(): check('director inspected source '+path,sha(path)==h)

C='.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
manifest=js(C+'/manifest.json')
sourcepaths=['game/mobile/lib/app.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/daily_icon_label.dart','game/mobile/lib/game_controller.dart',
 'game/mobile/lib/calibration_screen.dart','game/mobile/lib/calibration_pattern.dart','game/mobile/lib/presentation.dart',
 'game/mobile/lib/story_screen.dart','game/mobile/lib/story_state.dart','game/mobile/lib/strings.dart',
 'game/mobile/test/content_presentation_test.dart','game/mobile/test/content_presentation_probe.dart','game/mobile/test/client_test.dart',
 'game/mobile/test/session_progression_test.dart','game/mobile/test/calibration_accessibility_matrix_test.dart',
 'game/progression/lib/tideglass_progression.dart','game/progression/test/progression_test.dart',
 'game/core/test/daily_test.dart','game/core/test/economy_test.dart']
sourcepaths += [str(p.relative_to(R)) for p in (R/'game/core/lib').rglob('*.dart')]
sourcepaths += [str(p.relative_to(R)) for folder in ['game/content/challenges','game/mobile/assets/challenges','game/content/calibrations','game/mobile/assets/calibrations'] for p in (R/folder).glob('*.json')]
for path in sourcepaths:
    h=sha(path);check('current candidate source '+path,h==manifest['source_sha256'][path] and sha(C+'/source/'+path)==h)
corpus=[]
for n in range(1,13):
    name=f'challenge.{n:02}.json';path='game/content/challenges/'+name;d=js(path)
    check('challenge actual packaged identity '+name,sha(path)==sha('game/mobile/assets/challenges/'+name))
    check('challenge fixed entry/isolation contract '+name,d['dossier_cost_notes']==100 and d['replay_cost_notes']==0 and d['main_policy_continues'] and d['dossier_persistent'] and all(d[k] is False for k in ['main_power_import','economic_export','prestige_enabled','focus_enabled','support_enabled']))
    corpus.append({'id':d['id'],'family':d['family'],'goal':d['goal'],'construction_mode':d['construction_mode']})
check('exact unique twelve three families',len({x['id'] for x in corpus})==12 and sorted(Counter(x['family'] for x in corpus).values())==[4,4,4])
out('challenge-corpus.json',corpus)

F='release/content-presentation/full-matrix-repaired-20261021T143209447416Z'
fv=js(F+'/verification.json');selected=[];matrix_deltas={}
for condition in fv['conditions']:
    folder=condition['directory']
    for name,h in condition['evidence_sha256'].items(): check('matrix artifact '+folder+'/'+name,sha(folder+'/'+name)==h)
    run=js(folder+'/run.json');obs=js(folder+'/observations.json')
    check('actual matrix execution '+folder,run['exit_code']==0 and run['source_before']==run['source_after'])
    stream=[json.loads(s) for s in read(folder+'/test.jsonl').decode().splitlines() if s.startswith('{')]
    check('matrix terminal success '+folder,any(x.get('type')=='done' and x.get('success') is True for x in stream))
    for path in ['game/mobile/lib/story_screen.dart','game/mobile/lib/story_state.dart','game/mobile/lib/game_controller.dart','game/mobile/test/content_presentation_test.dart','game/mobile/test/content_presentation_probe.dart']:
        check('unchanged matrix relevant source '+folder+' '+path,sha(path)==run['source_before'][path])
    for path in ['game/mobile/lib/app.dart','game/mobile/lib/daily_panel.dart']:
        matrix_deltas[path]={'matrix':run['source_before'][path],'current':sha(path)}
    rows=[x for x in obs['rows'] if x['id'].startswith('asset.challenge.') or x['id'] in ['flow.daily.storage','flow.daily.contracts']]
    check('exact selected matrix row count '+folder,len(rows)==29 and len({(x['id'],x['state']) for x in rows})==29)
    for row in rows:
        label=folder+' '+row['id']+' '+row['state'];check('matrix assertions '+label,all(x is True for x in row['assertions'].values()))
        b=row['before']['main'];a=row['after']['main']
        if row['id'].startswith('asset.challenge.') and row['state']=='opened':
            check('actual exact Note debit '+label,b['survey_notes']=='150' and a['survey_notes']=='50' and b['wallet_micros']==a['wallet_micros'] and b['charts']==a['charts'])
        if row['state']=='ready-backlog': check('actual all backlog claims '+label,a['survey_notes']=='210' and a['daily']['pass_xp_by_id']['pass.01']=='5250' and all(x['claimed'] for x in a['daily']['contracts']))
        if row['state']=='queued-ready': check('actual Survey claim preserves Focus '+label,a['survey_notes']=='30' and a['completed_surveys']==0 and a['focus_charges']==b['focus_charges'] and a['focus_remaining_micros']==b['focus_remaining_micros'])
        selected.append({'id':row['id'],'state':row['state'],'condition':row['condition'],'assertions':row['assertions']})
out('selected-matrix-rows.json',selected);out('matrix-current-ui-delta.json',matrix_deltas)
I='release/qa/lead-daily-icons-20261023T031715.308630Z'
iv=js(I+'/verification.json');read(I+'/REVIEW.md')
for path,h in iv['outputs_sha256'].items():check('current daily icon reproduction '+path,sha(I+'/'+path)==h)
for label in ['phone-200-true','tablet-200-false']:
    run=js(I+'/'+label+'/run.json')
    for path in ['game/mobile/lib/app.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/daily_icon_label.dart']:
        check('current final icon actual source '+label+' '+path,sha(path)==run['source_before'][path])
    check('current icon actual stable success '+label,run['exit_code']==0 and run['source_before']==run['source_after'])

K='release/qa/integration-accessibility-20261021T125317256764Z'
kp=js(K+'/review-source-sha256.json');js(K+'/verification.json');read(K+'/CALIBRATION_REVIEW.md')
for path in ['game/mobile/lib/calibration_screen.dart','game/mobile/lib/calibration_pattern.dart','game/mobile/lib/game_controller.dart','game/mobile/test/calibration_accessibility_matrix_test.dart']:
    check('independent calibration reviewed source '+path,sha(path)==kp[path])
for path in ['release/qa/lead-content-matrix-20261021T144134.921859Z/MATRIX_REVIEW.md','release/qa/lead-content-matrix-20261021T144134.921859Z/verification.json','release/qa/lead-calibration-scope-acceptance-20261021T130612.263921Z/DECISIONS.md']:
    read(path)
H='release/native-proof/20261023T040548.338966Z'
host=js(H+'/build-report.json')
for name in ['core','progression','mobile']:
    check('current suite passed '+name,host['host_checks'][name+'-test']['exit_code']==0 and 'All tests passed!' in read(H+'/'+name+'-test.log').decode())
pure=js(str((O/'earned-note-isolation.json').relative_to(R)))
check('new actual earned Note isolation proof',pure['passed'] and pure['assertions']==183 and len(pure['rows'])==12)
out('inputs-before.json',pins)
after={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in pins};out('inputs-after.json',after)
check('review input pins unchanged',pins==after)
out('verification.json',{'checks':checks,'all_passed':all(x['pass'] for x in checks),'check_count':len(checks),'input_files':len(pins),'failed':[x['name'] for x in checks if not x['pass']], 'counts_at_start':counts,'new_pure_assertions':183,'new_flutter_or_native_commands':False,'status_changed':False,'M3_04_original_prerequisites':{i:items[i]['status'] for i in items['M3-04']['source_acceptance_dependencies']},'selected_matrix_rows':len(selected)})
print(json.dumps({'checks':len(checks),'inputs':len(pins),'failed':[x['name'] for x in checks if not x['pass']]},indent=2))
