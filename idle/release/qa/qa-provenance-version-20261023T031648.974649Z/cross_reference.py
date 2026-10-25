from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;seen={};checks=[]
def raw(path):
 p=Path(path);p=p if p.is_absolute() else ROOT/p;b=p.read_bytes();seen[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest();return b
def load(path):return json.loads(raw(path))
def sha(path):return hashlib.sha256(raw(path)).hexdigest()
def ck(v,label):assert v,label;checks.append(label)
prop=load('release/asset-current-bridges/current-version-20261023/proposal.json');deltas={d['path']:d for d in prop['source_differences']}
# Existing independently accepted matrix is retained at its actual source version.
lead=load('release/qa/lead-content-matrix-20261021T144134.921859Z/verification.json');base=Path('release/content-presentation/full-matrix-repaired-20261021T143209447416Z');matrix=load(base/'verification.json');ck(sha(base/'verification.json')==lead['aggregate_sha256'],'matrix independently pinned aggregate');ck(sha(base/'per-id-evidence.json')==lead['per_id_evidence_sha256'],'matrix independently pinned per-ID evidence')
matrix_sources={}
for c in matrix['conditions']:
 p=Path(c['directory'])
 for name,d in c['evidence_sha256'].items():ck(sha(p/name)==d,'old matrix actual evidence unchanged')
 run=load(p/'run.json');pins=run['source_before'];ck(pins==run['source_after'],'historical matrix stable source')
 for name in deltas:
  if name in pins:
   ck(sha(p/'source'/name)==pins[name],'archived matrix source exact');matrix_sources.setdefault(name,set()).add(pins[name])
ck(matrix_sources['game/mobile/lib/story_screen.dart']=={deltas['game/mobile/lib/story_screen.dart']['current_sha256']},'current Story source covered by matrix')
ck(matrix_sources['game/mobile/lib/season_screen.dart']=={deltas['game/mobile/lib/season_screen.dart']['current_sha256']},'current Season source covered by matrix')
localization=load('release/qa/integration-current-ui-20261021T133115456638Z/verification.json');ck(localization['source_before']['game/mobile/lib/season_screen.dart']==deltas['game/mobile/lib/season_screen.dart']['current_sha256'],'Season source matches independent localization repair')
raw('release/qa/integration-current-ui-20261021T133115456638Z/CURRENT_UI_REVIEW.md');raw('release/qa/integration-public-pages-refresh-20261021T141933905061Z/DOCUMENTATION_BRIDGE_REVIEW.md')
# Current App is an explicit chain, not a claim that prior whole-App captures changed.
reset=load('release/qa/qa-reset-20261023T025256.370588Z/verification.json');promotion=load('release/daily-icons/integration-20261023T031147.160461Z/promotion.json');ck(reset['final_source_sha256']['game/mobile/lib/app.dart']==promotion['baseline']['game/mobile/lib/app.dart'],'reset tested App is daily promotion baseline');ck(promotion['promoted_sha256']['game/mobile/lib/app.dart']==deltas['game/mobile/lib/app.dart']['current_sha256'],'daily promoted App is proposed source')
for name,d in promotion['promoted_sha256'].items():ck(sha(name)==d,'actual daily promoted source')
# Reconcile actual targeted author/reviewer output; no test process is rerun.
author_path=Path('release/daily-icons/author-matrix-20261023T031243.068903Z');author=load(author_path/'verification.json');lead_path=Path('release/qa/lead-daily-icons-20261023T031715.308630Z');daily_lead=load(lead_path/'verification.json');ck(sha(author_path/'verification.json')==daily_lead['author_verification_sha256'],'author aggregate matches independent root review')
for name,d in daily_lead['outputs_sha256'].items():ck(sha(lead_path/name)==d,'root actual output digest')
conditions=[]
for c in author['conditions']:
 p=Path(c['directory'])
 for name,d in c['sha256'].items():ck(sha(p/name)==d,'author actual output digest')
 conditions.append((p,'author'))
conditions.extend([(lead_path/'phone-200-true','independent_root'),(lead_path/'tablet-200-false','independent_root')])
run_counts=[]
for p,kind in conditions:
 run=load(p/'run.json');ck(run['exit_code']==0 and run['source_before']==run['source_after'],'targeted run finished stable')
 for name,d in run['source_before'].items():ck(sha(p/'source'/name)==d and sha(name)==d,'targeted archived and live input exact')
 for name,d in run['output_hashes'].items():ck(sha(p/name)==d,'targeted runtime output bound')
 events=[json.loads(line) for line in raw(p/'test.jsonl').decode().splitlines() if line.startswith('{')];done=[e for e in events if e.get('type')=='done'];ck(len(done)==1 and done[0]['success'] is True,'final actual Flutter success')
 bodies=[e for e in events if e.get('type')=='testDone' and not e.get('hidden')];ck(len(bodies)==4 and all(e['result']=='success' and not e['skipped'] for e in bodies),'four successful unskipped actual bodies')
 rows=load(p/'observations.json')['rows'];ck(len(rows)==5,'five exact daily status rows');ck(all(all(v is True for v in row['assertions'].values()) for row in rows),'daily assertions observed true');run_counts.append({'directory':str(p),'kind':kind,'cases':len(bodies),'rows':len(rows)})
prior=load('release/qa/client-assets-current-20261023T025348.813709Z/asset-review.json');producer_pins={p:s for p,s in prior['source_pins'].items() if p.startswith(('source/art/producers/','game/assets/producers/')) or p=='game/mobile/lib/producer_art.dart'}
ck(bool(producer_pins),'prior named client producer input set present')
for name,d in producer_pins.items():ck(sha(name)==d,'named client producer input unchanged')
raw('release/art/producer-independent-review.md');raw('release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md');raw('release/qa/client-assets-current-20261023T025348.813709Z/ASSET_REVIEW.md')
program=load('implementation/program.json');items={x['id']:x for x in program['items']};ck(items['M2-05']['status']=='accepted','original M3-09 prerequisite accepted');ck(items['M3-09']['reviewer']=='client','original client reviewer role retained');ck(items['M3-09']['source_acceptance']=='Five producer families each have base plus four milestone presentations; daily-loop icons and status states are final.','original M3-09 clause retained')
# Source meaning inspection is recorded separately from rendered states.
for path in ['game/mobile/lib/daily_icon_label.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/app.dart','game/mobile/lib/strings.dart','game/mobile/test/daily_icons_test.dart','game/mobile/test/daily_flow_test.dart','game/mobile/test/localization_test.dart']:raw(path)
changed=[p for p,d in seen.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=d];ck(not changed,'review input set stable')
result={'reviewer':'/root/qa_release','assigned_clause_review_role':'client','no_flutter_executed':True,'metadata_source_chain_reconciled':True,'matrix_source_pins':{k:sorted(v) for k,v in matrix_sources.items()},'daily_actual_runs':run_counts,'prior_named_client_producer_inputs_unchanged':len(producer_pins),'M3_09_recommendation':'accept original clause','all_original_variant_or_native_approval':False,'checks':len(checks),'input_sha256':seen}
(OUT/'cross-reference.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['input_sha256','matrix_source_pins','daily_actual_runs']},indent=2))
