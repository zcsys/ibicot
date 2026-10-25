"""Fail closed on incomplete/filtered/drifting content presentation evidence."""
import argparse,hashlib,json,math,re
from pathlib import Path
from content_contract import load,digest,write


def require(ok,message):
    if not ok: raise ValueError(message)
def numeric(x): return type(x) in (int,float) and math.isfinite(x)
def rect(value):
    require(type(value)is list and len(value)==4 and all(numeric(v)for v in value),'invalid rectangle')
    require(value[2]>=value[0] and value[3]>=value[1],'inverted rectangle');return value

def contained(bounds,view):
    b,v=rect(bounds),rect(view)
    require(v[2]>v[0] and v[3]>v[1],'empty viewport')
    require(b[0]>=v[0]-.5 and b[1]>=v[1]-.5 and b[2]<=v[2]+.5 and b[3]<=v[3]+.5,'not wholly visible')

def pseudo(text,enabled):
    if not enabled or not text or text.startswith('[!'): return text
    if re.fullmatch(r'[+\-−]?\d[\d.,eE+\-\sKMBT%/×]*',text) or not re.search('[A-Za-z]',text):return text
    chars=str.maketrans('AaEeIiOoUuYy','ÁáÉéÍíÓóÚúÝý')
    words=max(1,min(100,math.ceil(len(text.encode('utf-16-le'))/2*.35/5)))
    return '[!'+text.translate(chars)+' '+' '.join(['éxtra']*words)+'!]'

def valid_condition(condition):
    require(type(condition)is dict and set(condition)=={'viewport','text_percent','pseudo'},'condition keys')
    require(type(condition['viewport'])is str and condition['viewport'] in ['phone','tablet'],'viewport type/value')
    require(type(condition['text_percent'])is int and condition['text_percent'] in [100,150,200],'text scale type/value')
    require(type(condition['pseudo'])is bool,'pseudo exact bool')

def validate_row(row,wanted,condition):
    valid_condition(condition);valid_condition(row['condition'])
    require(row['id']==wanted['id'] and row['state']==wanted['state'],'wrong identity')
    require(row['route']==wanted['route'],'wrong production route')
    require(row['condition']==condition,'wrong display condition')
    require(type(row['fixture'])is str and len(row['fixture'])>10,'fixture qualification missing')
    require(row['before_sha256']==digest(row['before']) and row['after_sha256']==digest(row['after']),'ledger digest mismatch')
    require(set(row['assertions'])==set(wanted['assertions']),'missing or unexpected assertion')
    require(all(v is True for v in row['assertions'].values()),'assertion not true')
    texts=row['texts'];fields=[t['field']for t in texts]
    required=wanted['fields']
    for field in required:require(fields.count(field)==1,'missing or duplicate required field '+field)
    extra=[f for f in fields if f not in required]
    if row['id']=='flow.daily.contracts' and row['state'] in ['pending-reroll','ready-backlog']:
        # pending has 3 cards plus one reread after reroll; backlog reads all21.
        expected=8 if row['state']=='pending-reroll' else 42
        require(len(extra)==expected and all(re.fullmatch(r'contract-[0-2]-\d+-(title|progress)',f)for f in extra),'incomplete daily card text')
    else:require(not extra,'unexpected text fields')
    for t in texts:
        require(type(t['english'])is str and type(t['display'])is str,'missing actual text')
        require(t['display']==pseudo(t['english'],condition['pseudo']),'incorrect pseudolocale payload')
        require(t['english_sha256']==digest(t['english']) and t['display_sha256']==digest(t['display']),'text hash mismatch')
        require(type(t['code_units'])is int and t['code_units']==len(t['display'].encode('utf-16-le'))//2,'text length mismatch')
        for flag in ['complete_text','untruncated','all_lines_in_viewport']:require(t.get(flag)is True,'missing text assertion '+flag)
        require(type(t['line_boxes'])is int and t['line_boxes']>0,'no actual line boxes')
        require(len(t['observed_line_boxes'])==t['line_boxes'],'missing line observation')
        for line in t['observed_line_boxes']:contained(line['rect'],line['viewport'])
        exact=wanted['exact_english'].get(t['field'])
        if exact is not None:require(t['english']==exact,'registered/runtime text differs: '+t['field'])
    controls=row['controls'];require(len(controls)>=wanted['minimum_controls'],'missing controls')
    require(sum(c['callback_invoked']is True for c in controls)>=wanted['minimum_callbacks'],'missing actual callbacks')
    for c in controls:
        require(type(c['enabled'])is bool and type(c['callback_invoked'])is bool,'nonboolean action flags')
        b=rect(c['rect']);contained(b,c['viewport'])
        require(b[2]-b[0]>=48 and b[3]-b[1]>=48,'undersized control')
        require(c.get('minimum_48')is True and c.get('whole_control_visible')is True,'missing control bounds flags')
        require(type(c['semantic_name'])is str and c['semantic_name'].strip(),'missing semantics')
        require(c['semantic_tap']is c['enabled'],'enabled semantics mismatch')
        require(type(c['hit_points'])is int and c['hit_points']==(5 if c['enabled'] else 0),'incomplete hit points')
        require(not c['callback_invoked'] or c['enabled'],'disabled callback')
    before,after=row['before'],row['after']; bm,am=before['main'],after['main'];bs,ast=before['story'],after['story']
    if row['assertions'].get('read_only') or row['assertions'].get('game_unchanged'):require(before==after,'read-only mutation')
    if row['assertions'].get('main_ledger_unchanged'):require(bm==am,'main state changed')
    if row['state']=='opened':
        id=row['id'].removeprefix('asset.').removesuffix('.copy')
        require(int(bm['survey_notes'])-int(am['survey_notes'])==100,'wrong dossier price')
        require(ast['dossiers']['owned']==[id] and ast['dossiers']['active']['dossier_id']==id,'wrong dossier identity')
        require(am['wallet_micros']==bm['wallet_micros'] and am['charts']==bm['charts'],'dossier imported main power')
    if row['state']=='reflected':
        require(int(am['daily']['discovery_sequence'])==int(bm['daily']['discovery_sequence'])+1,'reflection sequence')
        require(int(am['daily']['discovery_totals']['archive'])==int(bm['daily']['discovery_totals'].get('archive','0'))+1,'reflection total')
        require(am['survey_notes']==bm['survey_notes'] and am['wallet_micros']==bm['wallet_micros'] and am['daily']['pass_xp_by_id']==bm['daily']['pass_xp_by_id'],'reflection direct economic reward')
    if row['id']=='flow.daily.contracts':
        c=am['daily']['contracts']
        if row['state']=='ready-backlog':
            require(len(c)==21 and all(v['claimed']for v in c),'backlog claim inventory')
            require(int(am['survey_notes'])-int(bm['survey_notes'])==210,'wrong backlog Notes')
            require(int(am['daily']['pass_xp_by_id']['pass.01'])-int(bm['daily']['pass_xp_by_id'].get('pass.01','0'))==5250,'wrong backlog XP')
        if row['state']=='pending-reroll':require(len(c)==3 and sum(v['rerolled']for v in c)==1 and am['survey_notes']==bm['survey_notes'] and am['daily']['pass_xp_by_id']==bm['daily']['pass_xp_by_id'],'reroll grants or duplicates')
    if row['id']=='flow.daily.storage' and row['state']=='queued-ready':
        require(bm['completed_surveys']==3 and am['completed_surveys']==0 and int(am['survey_notes'])-int(bm['survey_notes'])==30,'wrong Survey transition')
        require(am['focus_charges']==bm['focus_charges']==10 and am['focus_remaining_micros']==bm['focus_remaining_micros']=='1200000000','Focus queue changed')
    if row['state']=='archive-resume-pause':require(am==bm and ast['season']['archive_active']is False and ast['season']['fleet']['wallet_micros']==bs['season']['fleet']['wallet_micros'],'archive pause grants economy')


def validate(report,contract,condition):
    require(report.get('schema_version')==1 and type(report['schema_version'])is int,'report schema')
    require(report.get('kind')=='production_widget_content_observations','report kind')
    wanted={(r['id'],r['state']):r for r in contract['rows']}; rows=report['rows']
    require(len(rows)==contract['rows_per_condition'],'wrong row count')
    require(len({(r['id'],r['state'])for r in rows})==len(rows),'duplicate identity')
    require({(r['id'],r['state'])for r in rows}==set(wanted),'missing or unexpected identity')
    for row in rows:validate_row(row,wanted[(row['id'],row['state'])],condition)


def validate_run(directory,contract):
    directory=Path(directory);run=load(directory/'run.json')
    require(run['exit_code']==0,'unsuccessful command')
    require(run['source_before']==run['source_after'],'source drift')
    require(run['source_before'],'missing source pin')
    archived_contract=directory/'source/release/content-presentation/staged/expected-rows.json'
    require(load(archived_contract)==contract,'supplied contract differs from archived executed contract')
    for name,h in run['source_before'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe source path')
        require(sha(directory/'source'/name)==h,'archived input differs '+name)
    required={'game/mobile/test/content_presentation_test.dart','game/mobile/test/content_presentation_probe.dart','game/mobile/lib/story_screen.dart','game/mobile/lib/season_screen.dart','game/mobile/lib/help_screen.dart','game/mobile/lib/daily_panel.dart','game/mobile/lib/game_controller.dart'}
    require(required.issubset(run['source_before']),'missing production inputs')
    require(set(run['output_hashes'])=={'test.jsonl','observations.json'},'missing result hashes')
    command=run['command'];require(type(command)is list and len(command)==8,'exact unfiltered command required')
    require(command[1:4]==['test','--reporter=json','test/content_presentation_test.dart'],'unexpected test invocation')
    require(command[-1]==f'--dart-define=TIDEGLASS_CONTENT_REPORT={directory.resolve()/"observations.json"}','report destination mismatch')
    forbidden=['--name','--plain-name','--tags','--exclude-tags','--test-randomize-ordering-seed']
    require(not any(x in ['-n','-N','-t','-x'] or any(x==k or x.startswith(k+'=')for k in forbidden)for x in command),'filtered run')
    require(command.count('test/content_presentation_test.dart')==1,'wrong suite')
    cond=run['condition'];require(cond in contract['conditions'],'unknown condition')
    for key,value in [('VIEWPORT',cond['viewport']),('TEXT_PERCENT',cond['text_percent']),('PSEUDO',str(cond['pseudo']).lower())]:
        env='TIDEGLASS_'+('TEST_'+key if key!='PSEUDO' else key)
        require(command.count(f'--dart-define={env}={value}')==1,'command/condition mismatch')
    for f,h in run['output_hashes'].items():require(sha(directory/f)==h,'output hash changed')
    events=[]
    for line in (directory/'test.jsonl').read_text().splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:pass
    done=[e for e in events if e.get('type')=='done']
    require(len(done)==1 and done[0].get('success')is True and events[-1] is done[0],'missing, duplicate or nonfinal successful completion')
    require(not any(e.get('type')=='error' for e in events),'test errors')
    finished=[e for e in events if e.get('type')=='testDone' and not e.get('hidden',False)]
    require(len(finished)==contract['tests_per_condition'],'missing test cases')
    require(len({e.get('testID')for e in finished})==len(finished),'duplicate test completion')
    require(all(e.get('result')=='success' and not e.get('skipped',False)for e in finished),'skipped or failing tests')
    validate(load(directory/'observations.json'),contract,cond)
    return {'condition':cond,'rows':contract['rows_per_condition'],'tests':len(finished),'source_fingerprint':digest(run['source_before']),'host_only':True,'release_acceptance':False}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    result=validate_run(a.run,load(a.contract));print(json.dumps(result));
    if a.output:write(a.output,result)
