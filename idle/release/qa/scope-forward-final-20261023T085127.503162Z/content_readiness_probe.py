"""Read-only current M3-08/M4-06 clause and source-binding audit; no runtime suite."""
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
pins={};checks=[]
def read(path):
 p=ROOT/path;pins[path]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
program=read('implementation/program.json');by={x['id']:x for x in program['items']}
current=read('implementation/scope_requirements.json')
campaign=read('game/content/progression/campaign.json');chapters=campaign['chapters'];archive=read('game/content/narrative/archive.en.json')['entries']
check('exact six sequential chapter IDs',[x['id'] for x in chapters]==[f'chapter.{n:02}' for n in range(1,7)])
for n,x in enumerate(chapters,1):
 check(x['id']+' objectives/copy/rewards',bool(x['objectives']) and all(x[k] for k in ('title','intro','completion','hints','reward_cosmetic_id','harbor_state','archive_ids')))
 check(x['id']+' explicit prerequisite',x['prerequisite']==(None if n==1 else f'chapter.{n-1:02}'))
 check(x['id']+' zero economic or paid budget',x['economic_rewards']==[] and x['paid_requirements']==[])
check('exact eighteen archive IDs',[x['id'] for x in archive]==[f'archive.main.{n:02}' for n in range(1,19)])
check('archive text complete',all(x['title'] and x['text'] and x['chapter_id'] in {c['id'] for c in chapters} for x in archive))
check('all archive rewards resolve',sorted(y for x in chapters for y in x['archive_ids'])==sorted(x['id'] for x in archive))
ending=read('game/content/locales/en-US/ending.main.json');check('ending text matches actual sixth chapter',ending['text']==chapters[-1]['completion'])
challenges=[]
for n in range(1,13):
 x=read(f'game/content/challenges/challenge.{n:02}.json');challenges.append(x)
 check(x['id']+' full objective unlock completion budget',bool(x['goal']) and bool(x['unlock']) and all(x[k] for k in ('title','intro','completion')) and x['dossier_cost_notes']==100 and x['replay_cost_notes']==0 and x['completion_rewards']==[])
 check(x['id']+' no power import/export',x['main_power_import'] is False and x['economic_export'] is False and x['main_policy_continues'] is True)
 x=read(f'game/content/calibrations/calibration.{n:02}.pattern.json')
 check(x['id']+' actual graph/copy/equal route',len(x['nodes'])>=2 and len(x['edges'])>=1 and len(x['solution'])==len(x['nodes']) and all(x[k] for k in ('title','intro','instructions','accessible_label','accessible_description','reward_profile_id')) and x['focus_cost']==1 and x['time_limit_seconds'] is None)
check('three exact four-dossier families',{f:sum(x['family']==f for x in challenges) for f in {x['family'] for x in challenges}}=={'constrained_fleets':4,'synergy_priorities':4,'automation_planning':4})
season=read('game/events/content/season.01.json');copy=read('game/content/locales/en-US/season.01.copy.json')
check('season full declared copy and reward agreement',all(season['copy'].values()) and copy['copy']==season['copy'] and copy['rewards']==[{k:x[k] for k in ('id','level','track','content_id','title','body')} for x in season['rewards']] and copy['milestones']==[{k:x[k] for k in ('id','title','body')} for x in season['milestones']])
check('season reward identities and text',len(season['rewards'])==40 and len({x['id'] for x in season['rewards']})==40 and all(x['title'] and x['body'] and x['content_id'] for x in season['rewards']))
check('season no economic import/export',season['main_power_import'] is False and season['paid_effects'] is False and season['economic_exports']==[])
manifest=read('game/mobile/assets/config/manifest.json')
for file,meta in manifest['files'].items():
 path='game/mobile/'+file;p=ROOT/path;pins[path]=hashlib.sha256(p.read_bytes()).hexdigest()
 check('actual packaged hash '+file,pins[path]==meta['sha256'] and len(p.read_bytes())==meta['bytes'])
 candidate=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122/source'/path
 check('candidate exact '+file,candidate.read_bytes()==p.read_bytes())
for old,new in [('game/content/progression/campaign.json','game/mobile/assets/progression/campaign.json'),('game/content/narrative/archive.en.json','game/mobile/assets/progression/archive.en.json'),('game/events/content/season.01.json','game/mobile/assets/events/season.01.json')]:
 check('authored/runtime exact '+old,(ROOT/old).read_bytes()==(ROOT/new).read_bytes())
for n in range(1,13):
 for kind,suffix in [('challenges','.json'),('calibrations','.pattern.json')]:
  prefix='challenge' if kind=='challenges' else 'calibration';file=f'{prefix}.{n:02}{suffix}'
  check('authored/runtime exact '+file,(ROOT/'game/content'/kind/file).read_bytes()==(ROOT/'game/mobile/assets'/kind/file).read_bytes())
references=[
 'release/qa/daily-challenge-20261023T060000Z/READINESS_REVIEW.md',
 'release/qa/daily-challenge-20261023T060000Z/verification.json',
 'release/qa/lead-earned-note-reproduction-20261023T080225.313756Z/verification.json',
 'release/qa/scope-forward-20261023T033420.755364Z/S33_BRIDGE.md',
 'release/qa/scope-forward-20261023T033420.755364Z/balance-source-bridge.json',
 'release/content-presentation/full-matrix-repaired-20261021T143209447416Z/verification.json',
 'release/qa/lead-content-matrix-20261021T144134.921859Z/MATRIX_REVIEW.md',
 'release/qa/integration-accessibility-20261021T125317256764Z/CALIBRATION_REVIEW.md',
 'release/qa/client-reverse-current-20261023T084431.965005Z/m4-07/CLIENT_JUDGMENT.md',
 'game/progression/lib/tideglass_progression.dart','game/progression/test/progression_test.dart',
 'game/mobile/lib/story_screen.dart','game/mobile/lib/story_state.dart','game/mobile/lib/season_screen.dart',
 'game/mobile/lib/calibration_screen.dart','game/mobile/test/content_presentation_test.dart']
for f in references:pins[f]=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
report={'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'checks_passed':len(checks),'runtime_executions':0,'original_items':{key:{k:by[key][k] for k in ('source_acceptance','source_acceptance_dependencies','reviewer','status')} for key in ('M3-08','M4-06','M4-07')},'unaccepted_dependencies':{key:[dep for dep in by[key]['source_acceptance_dependencies'] if by[dep]['status']!='accepted'] for key in ('M3-08','M4-06','M4-07')},'pins':pins}
(OUT/'content-readiness-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'pins':len(pins),'unaccepted_dependencies':report['unaccepted_dependencies']}))
