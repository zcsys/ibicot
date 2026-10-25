#!/usr/bin/env python3
"""Qualify explicit local study records into the schema-2 descriptive input.

Hash chains detect accidental alteration/replay, not a malicious rewritten
history. Independent registry, consent/eligibility and native evidence audits
remain necessary. No network, collection, recruitment or acceptance occurs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

import study_report as analysis

OPAQUE = re.compile(r'[a-f0-9]{32}\Z')
EVENTS = {'app_start','session_start','foreground','background','harbor_interactive',
          'activity','gap','terminal','withdrawal'}
ACTIVITIES = {'interaction','purchase','rechart','navigation','calibration','contract','help'}
GAPS = {'storageFailure','clockDiscontinuity','instrumentationUnavailable','capacity','withdrawalErasure'}
REGISTRY_FIELDS = {'study_id','install_id','enrolled_at','first_launch','protocol_sha256',
    'information_sha256','consent_version','eligibility_evidence_sha256','synthetic',
    'platform','device_group','acquisition','baseline'}
require, keys, integer = analysis.require, analysis.keys, analysis.integer


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def hash_value(value):
    return isinstance(value, str) and analysis.HASH.fullmatch(value) is not None


def opaque(value):
    return isinstance(value, str) and OPAQUE.fullmatch(value) is not None


def config(value):
    if value is None:
        return None
    keys(value, ['candidate_sha256','economy_sha256','content_sha256','config'])
    require(all(hash_value(value[k]) for k in ('candidate_sha256','economy_sha256','content_sha256'))
            and analysis.token(value['config']), 'Invalid exact configuration')
    require(value['config'] != 'unqualified_config', 'Reserved configuration label')
    return value


def evidence_file(folder, reference):
    require(hash_value(reference), 'Invalid evidence reference')
    path = Path(folder)/(reference+'.evidence')
    require(not path.is_symlink() and path.is_file(), 'External evidence missing or unsafe')
    require(path.stat().st_size <= analysis.LIMIT, 'External evidence too large')
    with path.open('rb') as source:
        value = hashlib.file_digest(source, 'sha256').hexdigest()
    require(value == reference, 'External evidence hash mismatch')
    return reference


def _subtract(intervals, gaps):
    answer=[]
    for start,end in intervals:
        parts=[(start,end)]
        for left,right in gaps:
            replacement=[]
            for a,b in parts:
                if right<=a or left>=b: replacement.append((a,b))
                else:
                    if a<left: replacement.append((a,left))
                    if right<b: replacement.append((right,b))
            parts=replacement
        answer.extend(parts)
    return [list(pair) for pair in sorted(answer) if pair[0]<pair[1]]


def validate_registry(row, protocol, protocol_sha256, cutoff):
    keys(row, REGISTRY_FIELDS)
    require(row['study_id']==protocol['study_id'] and type(row['synthetic']) is bool
            and row['synthetic']==protocol['synthetic'], 'Mixed study population')
    require(opaque(row['install_id']) and integer(row['first_launch']) and
            row['enrolled_at']==row['first_launch'] and type(row['enrolled_at']) is int,
            'Invalid first enrolled app-start registry')
    require(protocol['enrollment_start']<=row['first_launch']<protocol['enrollment_end']
            and row['first_launch']<=cutoff, 'Outside fixed enrollment window')
    require(row['protocol_sha256']==protocol_sha256 and hash_value(row['information_sha256'])
            and hash_value(row['eligibility_evidence_sha256']) and analysis.token(row['consent_version']),
            'Enrollment identity missing')
    require(row['platform'] in {'ios','android','test'} and (protocol['synthetic'] or row['platform']!='test'), 'Invalid platform')
    require(row['device_group'] in {'phone_compact','phone_large','tablet','unclassified'} and
            row['acquisition'] in {'moderated','panel','organic','internal_test'} and
            (protocol['synthetic'] or row['acquisition']!='internal_test'), 'Invalid stratum')
    require(config(row['baseline'])==protocol['baseline'], 'Mixed baseline cohort')


def decode_records(raw, registry, cutoff):
    keys(raw, ['schema_version','registry','records','status'])
    require(type(raw['schema_version']) is int and raw['schema_version']==1 and
            raw['status'] in {'active','exhausted','withdrawn'}, 'Invalid raw version/status')
    require(isinstance(raw['records'],list) and len(raw['records'])<=100000, 'Invalid bounded records')
    if raw['registry'] is None:
        require(raw['status']=='withdrawn' and not raw['records'], 'Invalid erased marker')
        return [], [], True
    require(raw['registry']==registry and raw['records'], 'Registry changed or earliest start missing')
    previous=digest(registry); last_at=registry['first_launch']; seen_events=set()
    sessions=[]; by_session={}; seen_processes=set(); current=None
    gaps=[]; withdrawn=False; last_activity=None; foreground=False; interactive=False
    pending_inactivity=None
    configs={registry['baseline']['config']:registry['baseline']}
    for seq,event in enumerate(raw['records']):
        keys(event,['seq','event_id','at','process_id','session_id','kind','payload','previous_sha256','sha256'])
        require(type(event['seq']) is int and event['seq']==seq and opaque(event['event_id']) and
                event['event_id'] not in seen_events and opaque(event['process_id']) and opaque(event['session_id']),
                'Duplicate, replayed or invalid record identity')
        require(integer(event['at']) and last_at<=event['at']<=cutoff and event['kind'] in EVENTS
                and isinstance(event['payload'],dict), 'Invalid chronological record')
        require(not withdrawn, 'Records after withdrawal')
        core={key:value for key,value in event.items() if key!='sha256'}
        require(event['previous_sha256']==previous and event['sha256']==digest(core), 'Broken raw chain')
        previous=event['sha256']; last_at=event['at']; seen_events.add(event['event_id'])
        at,kind,payload=event['at'],event['kind'],event['payload']
        if pending_inactivity is not None:
            require(at==pending_inactivity['start'] and event['session_id']==pending_inactivity['session_id']
                    and event['process_id']==pending_inactivity['_process']
                    and (kind=='foreground' or (kind=='harbor_interactive' and foreground)),
                    'Inactivity start missing its atomic foreground/harbor trigger')
            pending_inactivity=None
        if kind in {'app_start','session_start'}:
            keys(payload,['config','reason']); exact=config(payload['config'])
            if exact is not None:
                label=exact['config'];require(label not in configs or configs[label]==exact, 'Reused config label with different identity');configs[label]=exact
            else: label='unqualified_config'
            require(event['session_id'] not in by_session, 'Replayed session start')
            if kind=='app_start':
                require(event['process_id'] not in seen_processes and payload['reason']==('enrollment' if seq==0 else 'process_restart'), 'Invalid process restart')
                if seq==0: require(at==registry['first_launch'] and exact==registry['baseline'], 'Missing original enrolled start')
                seen_processes.add(event['process_id'])
                foreground=True
            else:
                require(current is not None and current['_terminal'] is None
                        and exact==current['_exact_config'] and event['process_id']==current['_process'] and payload['reason']=='inactivity'
                        and last_activity is not None and at-last_activity>=1800, 'Invalid inactivity boundary')
                # A background app cannot manufacture an inactivity session.
                # Recorder emits the start immediately before a foreground event.
            current={'install_id':registry['install_id'],'session_id':event['session_id'],'start':at,
                     'end':None,'crashed':False,'valid':True,'return_eligible':False,'config':label,
                     '_process':event['process_id'],'_config_complete':exact is not None,
                     '_terminal':None,'_last_at':at,'_interactive':False,'_activity':False,'_exact_config':exact}
            if sessions: sessions[-1]['_next_start']=at
            if kind=='session_start':pending_inactivity=current
            sessions.append(current);by_session[event['session_id']]=current
            interactive=False;last_activity=at
            continue
        require(current is not None and event['session_id']==current['session_id'] and
                event['process_id']==current['_process'] and current['_terminal'] is None,
                'Orphaned, old-session or post-terminal record')
        current['_last_at']=at
        if kind in {'foreground','background','harbor_interactive'}:
            keys(payload,[])
            if kind=='foreground':foreground=True
            elif kind=='background':foreground=False
            else:
                require(foreground, 'Background harbor observation')
                interactive=True;current['_interactive']=True;last_activity=at
        elif kind=='activity':
            keys(payload,['activity']);require(payload['activity'] in ACTIVITIES and foreground and interactive, 'Unobserved foreground activity')
            require(last_activity is not None and at-last_activity<1800, 'Missing inactivity boundary')
            current['_activity']=True;last_activity=at
        elif kind=='gap':
            keys(payload,['reason','from','to'])
            require(payload['reason'] in GAPS and integer(payload['from']) and payload['from']<=at and
                    (payload['to'] is None or (integer(payload['to']) and payload['from']<=payload['to']<=at)), 'Invalid observation gap')
            gaps.append([max(registry['first_launch'],payload['from']),cutoff if payload['to'] is None else payload['to']])
        elif kind=='terminal':
            keys(payload,['reason']);require(payload['reason']=='explicitlyObservedCleanExit','Invalid terminal')
            current['_terminal']=event['sha256']
        elif kind=='withdrawal':
            keys(payload,['retained_registry_policy']);require(payload['retained_registry_policy'] is True,'Invalid withdrawal')
            withdrawn=True;gaps.append([registry['first_launch'],cutoff])
        else:raise ValueError('Unknown event')
    require(pending_inactivity is None,'Truncated atomic inactivity transition')
    require(raw['records'][0]['kind']=='app_start','Missing earliest startup')
    require((raw['status']=='withdrawn')==withdrawn,'Withdrawal status inconsistent')
    if raw['status']=='exhausted':
        require(raw['records'][-1]['kind']=='gap' and raw['records'][-1]['payload']['to'] is None,'Exhaustion missing gap')
    for session in sessions:
        session['return_eligible']=session['_config_complete'] and session['_interactive'] and session['_activity'] and not withdrawn
    return sessions,gaps,withdrawn


def wrapper_evidence(wrapper, enrolled):
    keys(wrapper,['schema_version','raw','eligibility_evidence'])
    require(type(wrapper['schema_version']) is int and wrapper['schema_version']==1,'Invalid export wrapper')
    raw=wrapper['raw'];require(isinstance(raw,dict) and isinstance(raw.get('registry'),dict),'Erased export has no enrollment identity')
    identity=raw['registry'].get('install_id');require(identity in enrolled,'Unknown wrapped enrollment')
    proof=wrapper['eligibility_evidence'];keys(proof,['schema_version','check','checked_at','study_id','candidate_sha256'])
    entry=enrolled[identity]
    require(type(proof['schema_version']) is int and proof['schema_version']==1 and proof['check']=='no_prior_game_directory_entries' and
            proof['study_id']==entry['study_id'] and proof['candidate_sha256']==entry['baseline']['candidate_sha256'] and isinstance(proof['checked_at'],str),'Invalid local eligibility probe')
    observed=datetime.fromisoformat(proof['checked_at'].replace('Z','+00:00'))
    require(observed.tzinfo is not None and int(observed.timestamp())<=entry['enrolled_at'] and
            0<=entry['enrolled_at']-int(observed.timestamp())<=300,'Eligibility check not before enrollment')
    reference=digest(proof);require(reference==entry['eligibility_evidence_sha256'],'Wrapped eligibility evidence changed')
    return identity,raw,reference


def adjudicate(protocol,registry,raw,review,*,protocol_sha256,evidence_dir):
    # Reuse the independently reviewed protocol validation with an empty data
    # body, before consuming any source observations.
    keys(review,['schema_version','study_id','synthetic','cutoff','installs','native_crashes','terminal_reviews'])
    cutoff=review['cutoff'];require(integer(cutoff),'Invalid cutoff')
    analysis.validate(protocol,{'schema_version':2,'synthetic':protocol['synthetic'],'cutoff':cutoff,'installs':[],'sessions':[]})
    require(protocol['registry_population']=='opt_in_study','Collector cannot establish all-install population')
    single_wrapper=isinstance(raw,dict) and set(raw)=={'schema_version','raw','eligibility_evidence'}
    source_bundles=[(registry,'entries')] + ([] if single_wrapper else [(raw,'exports')])
    for bundle,list_key in source_bundles:
        keys(bundle,['schema_version','study_id','synthetic',list_key])
        require(type(bundle['schema_version']) is int and bundle['schema_version']==1 and bundle['study_id']==protocol['study_id'] and
                type(bundle['synthetic']) is bool and bundle['synthetic']==protocol['synthetic'] and isinstance(bundle[list_key],list) and len(bundle[list_key])<=100000,'Invalid source bundle')
    require(type(review['schema_version']) is int and review['schema_version']==1 and review['study_id']==protocol['study_id'] and
            type(review['synthetic']) is bool and review['synthetic']==protocol['synthetic'],'Mixed adjudication population')
    for name in ('installs','native_crashes','terminal_reviews'):
        require(isinstance(review[name],list) and len(review[name])<=100000,'Unbounded adjudication')
    enrolled={}
    for row in registry['entries']:
        validate_registry(row,protocol,protocol_sha256,cutoff)
        require(row['install_id'] not in enrolled,'Duplicate registry install');enrolled[row['install_id']]=row
    exports={};embedded_evidence=set()
    for row in ([raw] if single_wrapper else raw['exports']):
        if set(row)=={'schema_version','raw','eligibility_evidence'}:
            identity,document,reference=wrapper_evidence(row,enrolled);embedded_evidence.add(reference)
        else:
            keys(row,['install_id','raw']);identity,document=row['install_id'],row['raw']
        require(identity in enrolled and identity not in exports,'Unknown or duplicate raw export')
        exports[identity]=document
    judgments={};references=set()
    for row in review['installs']:
        keys(row,['install_id','eligibility_review','eligibility_evidence_sha256','exclusion','coverage'])
        require(row['install_id'] in enrolled and row['install_id'] not in judgments,'Unknown or duplicate enrollment audit')
        require(row['eligibility_review']=='qualified','Unqualified eligibility must be resolved without silently excluding dropout')
        require(row['eligibility_evidence_sha256']==enrolled[row['install_id']]['eligibility_evidence_sha256'],'Eligibility evidence changed')
        reference=row['eligibility_evidence_sha256']
        references.add(reference if reference in embedded_evidence else evidence_file(evidence_dir,reference))
        require(row['exclusion'] is None or row['exclusion'] in analysis.EXCLUSIONS,'Unregistered exclusion')
        require(isinstance(row['coverage'],list) and len(row['coverage'])<=10000,'Invalid coverage audit')
        judgments[row['install_id']]=row
    require(set(judgments)==set(enrolled),'Every fixed-registry entry needs explicit eligibility audit')
    installs=[];sessions=[];lookup={};unknown_streams=withdrawals=incomplete_configs=0
    for identity,entry in enrolled.items():
        if identity not in exports:
            found,gaps,withdrawn=[],[[entry['first_launch'],cutoff]],False;unknown_streams+=1
        else:
            found,gaps,withdrawn=decode_records(exports[identity],entry,cutoff)
            if exports[identity]['registry'] is None:gaps=[[entry['first_launch'],cutoff]]
        withdrawals+=withdrawn
        coverage=[]
        for row in judgments[identity]['coverage']:
            keys(row,['start','end','evidence_sha256'])
            require(integer(row['start']) and integer(row['end']) and entry['first_launch']<=row['start']<row['end']<=cutoff,'Invalid coverage interval')
            references.add(evidence_file(evidence_dir,row['evidence_sha256']));coverage.append([row['start'],row['end']])
        coverage=_subtract(coverage,gaps)
        installs.append({'id':identity,'first_launch':entry['first_launch'],'platform':entry['platform'],
            'device_group':entry['device_group'],'acquisition':entry['acquisition'],'baseline_config':entry['baseline']['config'],
            'exclusion':judgments[identity]['exclusion'],'observable_intervals':coverage})
        for session in found:
            incomplete_configs+=not session['_config_complete'];lookup[(identity,session['session_id'])]=session;sessions.append(session)
    crash_links=set()
    for row in review['native_crashes']:
        keys(row,['install_id','session_id','process_id','crash_at','report_sha256','linkage_reviewed'])
        pair=(row['install_id'],row['session_id']);require(pair in lookup and pair not in crash_links,'Unknown or duplicate crash linkage')
        session=lookup[pair]
        require(row['linkage_reviewed'] is True and row['process_id']==session['_process'] and integer(row['crash_at']) and
                session['_last_at']<=row['crash_at']<=cutoff and session['_terminal'] is None,'Invalid native crash timing/linkage')
        next_process=session.get('_next_start',cutoff+1)
        require(row['crash_at']<next_process,'Crash occurs after a later session start')
        references.add(evidence_file(evidence_dir,row['report_sha256']));session['crashed']=True;crash_links.add(pair)
    ended=set()
    for row in review['terminal_reviews']:
        keys(row,['install_id','session_id','terminal_event_sha256','evidence_sha256'])
        pair=(row['install_id'],row['session_id']);require(pair in lookup and pair not in ended and pair not in crash_links,'Invalid terminal review')
        session=lookup[pair];require(hash_value(row['terminal_event_sha256']) and row['terminal_event_sha256']==session['_terminal'],'Unobserved clean terminal')
        references.add(evidence_file(evidence_dir,row['evidence_sha256']));session['end']=session['_last_at'];ended.add(pair)
    data={'schema_version':2,'synthetic':protocol['synthetic'],'cutoff':cutoff,'installs':installs,
          'sessions':[{k:v for k,v in session.items() if not k.startswith('_')} for session in sessions]}
    analysis.validate(protocol,data)
    audit={'schema_version':1,'status':'synthetic_adjudication' if protocol['synthetic'] else 'qualified_inputs_require_independent_audit',
           'fixed_registry_entries':len(enrolled),'missing_raw_exports':unknown_streams,'withdrawn_exports':withdrawals,
           'sessions_with_incomplete_config':incomplete_configs,'externally_linked_crash_records':len(crash_links),
           'reviewed_terminal_records':len(ended),'evidence_sha256':sorted(references),
           'registry_completeness_independently_verified':False,'native_linkage_independently_verified':False,
           'release_ready':False,'limits':['Source chains and hashes establish reproducibility, not truthful devices, lawful consent or complete enrollment.',
              'Only explicitly audited external intervals establish coverage; gaps/withdrawals remove it.',
              'Pre-Dart and pre-enrollment startup failures are not observed by this recorder.',
              'Missing terminal evidence remains unknown; native reports require actual independent linkage review.',
              'Qualified output contains opaque study identities and is restricted study data, not a public aggregate report.']}
    return data,audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('protocol','registry','raw','review','evidence-dir','output-dir'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    try:
        documents={};hashes={}
        for name in ('protocol','registry','raw','review'):
            documents[name],hashes[name]=analysis.load_json(getattr(args,name))
        data,audit=adjudicate(**documents,protocol_sha256=hashes['protocol'],evidence_dir=args.evidence_dir)
        audit['inputs_sha256']={**hashes,'adjudicator':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                'analyzer':hashlib.sha256(Path(analysis.__file__).read_bytes()).hexdigest()}
        destination=Path(args.output_dir)
        require(not destination.exists(),'Output directory must be new')
        destination.mkdir(mode=0o700)
        for filename,value in [('data.json',data),('adjudication.json',audit)]:
            path=destination/filename
            with path.open('x') as stream:
                path.chmod(0o600);json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')
        print(json.dumps({'status':audit['status'],'registry_entries':len(data['installs']),'session_records':len(data['sessions']),
                          'data_sha256':hashlib.sha256((destination/'data.json').read_bytes()).hexdigest(),'release_ready':False}))
        return 0
    except (OSError,ValueError,TypeError,KeyError,RecursionError):
        print(json.dumps({'status':'invalid_input','message':'Local study evidence failed validation; no records or raw errors are echoed.'}),file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
