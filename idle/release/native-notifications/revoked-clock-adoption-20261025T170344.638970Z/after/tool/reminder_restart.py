"""Android permission-revocation restart protocol; no permission/UI mutations.

Preparation is an interrupted process, never a passed integration test. Recovery
requires independently inspectable actual UI evidence and actual OS kill records.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

SCENARIOS = frozenset({'revoked-prepare', 'revoked-recover'})
BUNDLE = 'dev.tideglass.game'
IDENTITY = ('verification_id','candidate_fingerprint','harness_sha256','scenario','run_id','device_label','platform')
HEX = re.compile(r'^[a-f0-9]{64}$')
FILES = {'notification_preferences.json','save/progress.0.json','save/progress.1.json'}
READY = 'revoke_in_os_settings_expect_process_death'
MARKER = re.compile(r'^(?:flutter:|I/flutter\s*\(\s*\d+\):)\s*TIDEGLASS_REMINDER_ACTION (\{[^\n]+\})\s*$', re.M)


def require(value, message):
    if not value: raise ValueError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def read_json(path): return json.loads(Path(path).read_bytes())


def fixture(context):
    require(context['platform']=='android', 'Restart protocol is Android only')
    for key in ('device_label','run_id'):
        require(re.fullmatch(r'[A-Za-z0-9_-]{1,80}',context[key]), 'Unsafe fixture identity')
    return f'/data/user/0/{BUNDLE}/files/native-reminders/{context["device_label"]}-{context["run_id"]}-revoked-prepare'


def file_name(relative):
    require(relative in FILES, 'Unexpected predecessor file')
    return relative.replace('/','-')


def checkpoint(raw, context, marker):
    require(0 < len(raw) <= 131072, 'Checkpoint size invalid')
    require(digest(raw)==marker.get('checkpoint_sha256'), 'Checkpoint digest mismatch')
    value=json.loads(raw); require(type(value) is dict and value.get('version')==1, 'Unsupported checkpoint')
    prior=value.get('preparation',{})
    for key in IDENTITY:
        require(type(prior.get(key)) is type(context[key]) and prior[key]==context[key], 'Checkpoint identity mismatch: '+key)
        require(marker.get(key)==context[key], 'Marker identity mismatch: '+key)
    pid=prior.get('process_id'); require(type(pid) is int and pid>1 and marker.get('process_id')==pid, 'Checkpoint PID mismatch')
    require(marker.get('action')==READY and marker.get('checkpoint')==fixture(context)+'/revoke-checkpoint.json', 'Checkpoint path/action mismatch')
    require(type(marker.get('utc_ms')) is int and type(value.get('written_utc_ms')) is int and 0<=marker['utc_ms']-value['written_utc_ms']<=30000, 'Checkpoint must precede its marker')
    expected={'completed':False,'default_opted_out':True,'default_preferences_file_absent':True,'default_pending_ids':[],
              'permission_after_opt_in':'allowed','gateway':'NativeNotificationGateway','preference_store':'FileNotificationPreferences'}
    for key,want in expected.items(): require(type(prior.get(key)) is type(want) and prior[key]==want, 'Preparation observation missing: '+key)
    require(prior.get('permission_before_initialize') in ('allowed','denied') and prior.get('permission_after_initialize')==prior['permission_before_initialize'], 'Preparation initialization changed permission')
    require(prior.get('preferences_after_opt_in',{}).get('enabled') is True, 'No persisted opt-in')
    actions=prior.get('actions',[])
    require(len(actions)==1 and actions[0].get('action')=='allow_permission_if_prompted'
        and all(actions[0].get(key)==context[key] for key in IDENTITY)
        and actions[0].get('process_id')==pid, 'Preparation lacks exact actual opt-in action')
    require(prior.get('lifecycle_callback_failures')==[], 'Preparation callback failed')
    require(isinstance(prior.get('initialization_lifecycle_events'),list) and all(row.get('state')=='resumed' for row in prior['initialization_lifecycle_events']), 'Initialization opened permission UI')
    plan=prior.get('plan',{}); observed=prior.get('plan_observation',{})
    require(plan.get('ids')==[77101] and plan.get('kinds')==['focus'] and plan.get('production_lifecycle') is True, 'Wrong production plan')
    require(plan.get('body')=='Focus is available for your next constellation. Return whenever you like.', 'Wrong Focus body')
    require(all(type(plan.get(k)) is int for k in ('due_utc_ms','background_call_utc_ms','scheduled_observed_utc_ms')), 'Missing real plan time')
    require(plan['due_utc_ms']-plan['background_call_utc_ms']>=300000 and plan['due_utc_ms']>plan['scheduled_observed_utc_ms'], 'Production minimum/future schedule missing')
    require(observed.get('pending_ids')==[77101] and observed.get('warning_key') is None, 'No actual pending plan')
    require(observed.get('saved_payload')==observed.get('game_payload') and isinstance(observed.get('saved_payload'),dict), 'Saved gameplay differs')
    require(observed.get('saved_settled_through_utc_micros')==observed.get('game_settled_through_utc_micros') and type(observed.get('saved_settled_through_utc_micros')) is int, 'Saved cursor differs')
    require(digest(json.dumps(observed['saved_payload'],separators=(',',':'),ensure_ascii=False).encode())==plan.get('saved_payload_sha256'), 'Saved payload digest differs')
    require(observed.get('saved_snapshot_id')==plan.get('saved_snapshot_id') and isinstance(plan.get('saved_snapshot_id'),str) and plan['saved_snapshot_id'], 'Saved snapshot missing')
    hashes=value.get('files_sha256',{})
    require(isinstance(hashes,dict) and set(hashes)<=FILES and 'notification_preferences.json' in hashes and any(k.startswith('save/') for k in hashes), 'Missing or unsafe durable files')
    require(all(isinstance(h,str) and HEX.fullmatch(h) for h in hashes.values()), 'Invalid durable digest')
    require(hashes['notification_preferences.json']==prior.get('preferences_sha256'), 'Preference hash differs')
    return value


def permission(package_text, granted):
    require(re.search(r'^\s*Package \[dev\.tideglass\.game\]',package_text,re.M), 'Wrong package observation')
    wanted='true' if granted else 'false'
    matches=re.findall(r'android\.permission\.POST_NOTIFICATIONS: granted=(true|false),',package_text)
    require(matches==[wanted], 'Actual OS notification permission differs')


def kill_record(exit_text, logcat, marker, offset, after_device_ms):
    require(re.fullmatch(r'[+-][0-9]{4}',offset), 'Missing actual OS UTC offset')
    blocks=re.split(r'ApplicationExitInfo #[0-9]+:',exit_text)[1:]
    matches=[]
    for block in blocks:
        head=re.search(r'timestamp=([0-9-]+ [0-9:.]+) pid=([0-9]+)\b',block)
        if head and int(head[2])==marker['process_id']:
            require(re.search(r'process=dev\.tideglass\.game reason=8 \(PERMISSION CHANGE\)',block), 'Bound PID did not die from permission change')
            require('description=PermissionHelper' in block, 'Unexpected permission kill origin')
            stamp=datetime.strptime(head[1]+offset,'%Y-%m-%d %H:%M:%S.%f%z')-datetime(1970,1,1,tzinfo=timezone.utc)
            at=stamp.days*86400000+stamp.seconds*1000+stamp.microseconds//1000
            require(marker['utc_ms']<=at<=after_device_ms and at-marker['utc_ms']<=180000, 'Kill outside fresh preparation bound')
            matches.append(at)
    require(len(matches)==1, 'Exactly one fresh bound PID exit required')
    require(re.search(r'Killing '+str(marker['process_id'])+r':dev\.tideglass\.game/[^\n]+: PermissionHelper\s*$',logcat,re.M), 'Missing corroborating actual kill log')
    return matches[0]


class Host:
    def __init__(self, root, context, evidence):
        self.root=Path(root); self.context=context; self.evidence=Path(evidence); self.receipts=[]
        require(re.fullmatch(r'emulator-[0-9]+', context['device']), 'Only an explicit emulator')
        self.adb=str(self.root/'.tooling/android-sdk/platform-tools/adb')
    def command(self,*parts,allow_absent=False):
        cmd=[self.adb,'-s',self.context['device'],*parts]
        started=host_stamp()
        result=subprocess.run(cmd,capture_output=True,timeout=20)
        finished=host_stamp()
        self.receipts.append({'argv':cmd,'started_stamp':started,'finished_stamp':finished,'started_utc_ms':started['utc_ns']//1_000_000,'finished_utc_ms':finished['utc_ns']//1_000_000,'exit_code':result.returncode,'stdout':result.stdout.decode(errors='replace'),'stderr':result.stderr.decode(errors='replace')})
        require(result.returncode==0 or (allow_absent and result.returncode==1 and not result.stdout and not result.stderr), 'Read-only Android observation failed: '+str(parts))
        return result.stdout
    def sample_clock(self, phase, pid):
        for _ in range(3):
            self.command('shell','date','-u','+%s.%N')
            self.receipts[-1].update(clock_phase=phase,clock_context={**{k:self.context[k] for k in IDENTITY},'device':self.context['device'],'process_id':pid})
    def save_receipts(self):
        (self.evidence/'restart-host-receipts.json').write_text(json.dumps(self.receipts,indent=2)+'\n')
    def read_private(self, relative):
        require(relative in FILES|{'revoke-checkpoint.json'}, 'Private file not allowlisted')
        base=Path(fixture(self.context)); path=base/relative
        for component in [base, *[p for p in reversed(path.parents) if p.is_relative_to(base) and p!=base], path]:
            # Inputs belong to our stopped/paused synthetic fixture; reject links.
            self.command('shell','run-as',BUNDLE,'test','!','-L',str(component))
        self.command('shell','run-as',BUNDLE,'test','-f',str(path))
        limit=131072 if relative=='revoke-checkpoint.json' else 2*1024*1024+65536
        raw=self.command('exec-out','run-as',BUNDLE,'head','-c',str(limit+1),str(path))
        require(0<len(raw)<=limit, 'Private file exceeds bound')
        return raw
    def alive(self, pid):
        raw=self.command('shell','pidof',BUNDLE,allow_absent=True).decode().split()
        require(raw==[str(pid)], 'Expected sole exact native process is not alive')
        cmd=self.command('exec-out','run-as',BUNDLE,'cat',f'/proc/{pid}/cmdline')
        require(cmd.split(b'\0',1)[0]==BUNDLE.encode(), 'Native PID package mismatch')
    def capture_preparation(self, marker, raw_log):
        try:
            self.sample_clock('before_exports',marker['process_id'])
            self.alive(marker['process_id'])
            raw=self.read_private('revoke-checkpoint.json')
            value=checkpoint(raw,self.context,marker)
            (self.evidence/'revoke-checkpoint.json').write_bytes(raw)
            for name,want in value['files_sha256'].items():
                data=self.read_private(name); require(digest(data)==want,'Prekill durable file mismatch')
                (self.evidence/file_name(name)).write_bytes(data)
            prefs=read_json(self.evidence/'notification_preferences.json'); require(prefs.get('enabled') is True,'Stored preference not enabled')
            permission(self.command('shell','dumpsys','package',BUNDLE).decode(),True)
            self.alive(marker['process_id'])
            (self.evidence/'pre-revocation.log').write_bytes(raw_log)
            return {'marker':marker,'checkpoint_sha256':digest(raw),'native_pid':marker['process_id'],
                    'pre_log_bytes':len(raw_log),'pre_log_sha256':digest(raw_log),'files_sha256':value['files_sha256'], 'host_ready_stamp':host_stamp()}
        finally: self.save_receipts()
    def capture_death(self, preparation):
        try:
            texts={}
            for name,args in [('exit-info.txt',('shell','dumpsys','activity','exit-info',BUNDLE)),('permission-after.txt',('shell','dumpsys','package',BUNDLE)),('death-logcat.txt',('logcat','-d','-t','2000','-v','threadtime')),('device-offset.txt',('shell','date','+%z')),('pid-after.txt',('shell','pidof',BUNDLE))]:
                data=self.command(*args,allow_absent=name=='pid-after.txt'); (self.evidence/name).write_bytes(data); texts[name]=data.decode()
            observed=int(time.time()*1000)
            require(not texts['pid-after.txt'].strip(), 'Predecessor process still alive or was replaced')
            permission(texts['permission-after.txt'],False)
            for name,want in preparation['files_sha256'].items():
                require(digest(self.read_private(name))==want,'Durable predecessor changed during OS kill')
            self.sample_clock('after_death',preparation['native_pid'])
            model=clock_model([r for r in self.receipts if 'clock_phase' in r],self.context,preparation['native_pid'])
            at=kill_record(texts['exit-info.txt'],texts['death-logcat.txt'],preparation['marker'],texts['device-offset.txt'].strip(),model['device_after_ns']//1_000_000)
            validate_clock_event(model,self.context,preparation['marker'],at)
            return {'kill_utc_ms':at,'observed_utc_ms':observed,'reason':'PERMISSION CHANGE','process_id':preparation['native_pid'],'clock_model':model}
        finally:self.save_receipts()


def interrupted_errors(log, raw_log, preparation, death, exit_code, native_log_errors):
    errors=[]
    try:
        require(preparation and death,'Missing prekill or actual OS termination evidence')
        require(type(exit_code) is int and exit_code!=0,'Killed preparation cannot report successful test exit')
        require(digest(raw_log[:preparation['pre_log_bytes']])==preparation['pre_log_sha256'],'Native prekill log prefix changed')
        markers=[json.loads(raw) for raw in MARKER.findall(log)]
        require(len(markers)==2 and [m.get('action') for m in markers]==['allow_permission_if_prompted',READY] and markers[1]==preparation['marker'], 'Missing, duplicate or stale preparation markers')
        require(all(all(m.get(key)==preparation['marker'][key] for key in IDENTITY) and m.get('process_id')==preparation['native_pid'] for m in markers), 'Preparation action identity differs')
        negative=[x for x in native_log_errors(log) if not x.startswith('No successful')]
        require(not negative,'Unexpected native failure: '+str(negative))
        require('DriverError: Failed to fulfill RequestData due to remote error' in log and 'Service has disappeared' in log,'Expected driver disconnection absent')
        require(death['process_id']==preparation['native_pid'],'OS kill differs from prepared PID')
    except (ValueError,KeyError,TypeError) as error:errors.append(str(error))
    return errors


def switch(xml_text, checked):
    start=xml_text.find('<?xml'); end=xml_text.find('</hierarchy>')
    require(start>=0 and end>=0,'Missing actual UI hierarchy')
    tree=ET.fromstring(xml_text[start:end+len('</hierarchy>')])
    nodes=list(tree.iter('node'))
    require(any(n.get('resource-id')=='com.android.settings:id/switch_text' and n.get('text')=='All Tideglass notifications' for n in nodes),'Wrong Settings notification page')
    matches=[n for n in nodes if n.get('resource-id')=='android:id/switch_widget' and n.get('package')=='com.android.settings']
    require(len(matches)==1 and matches[0].get('enabled')=='true' and matches[0].get('checked')==str(checked).lower(),'Actual Settings switch state differs')
    bounds=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',matches[0].get('bounds',''))
    require(bounds is not None,'Missing actual switch bounds')
    return tuple(map(int,bounds.groups()))


def validate_operator(packet_path, prior):
    """Prospective packet made by the actual UI operator, never generated here.

    JSON has identity, process_id, before/action_started/action_finished/after UTC
    milliseconds plus their bounded wall/monotonic host_timeline, tap_argv/exit_code,
    and files_sha256 of before/after XML+PNG, Settings activity dump, and raw
    live-before/absent-after PID command receipts. Raw UI screenshots also require independent viewing.
    """
    packet_path=Path(packet_path); p=read_json(packet_path)
    for key in IDENTITY:require(p.get(key)==prior.get(key),'Operator run identity differs: '+key)
    require(p.get('process_id')==prior['restart_preparation']['native_pid'],'Operator PID differs')
    required={'before.xml','after.xml','before.png','after.png','settings-activities.txt','pid-observations.json'}
    hashes=p.get('files_sha256',{}); require(set(hashes)==required,'Incomplete/extra operator evidence')
    raw={}
    for name,want in hashes.items():
        path=packet_path.parent/name; require(path.is_file() and not path.is_symlink() and digest(path.read_bytes())==want,'Operator evidence hash mismatch: '+name); raw[name]=path.read_bytes()
    x0,y0,x1,y1=switch(raw['before.xml'].decode(),True); switch(raw['after.xml'].decode(),False)
    activity=raw['settings-activities.txt'].decode()
    require('android.settings.APP_NOTIFICATION_SETTINGS' in activity and 'launchedFromPackage='+BUNDLE in activity and 'com.android.settings' in activity and re.search(r'ProcessRecord\{[^\n]*\b'+str(p['process_id'])+r':dev\.tideglass\.game/',activity), 'Settings activity lacks bound package/PID route')
    cmd=p.get('tap_argv',[]); require(len(cmd)==9 and Path(cmd[0]).name=='adb' and cmd[1:7]==['-s',prior['device'],'shell','input','touchscreen','tap'],'Not an actual targeted UI tap')
    require(all(re.fullmatch(r'\d+',str(n)) for n in cmd[7:]),'Invalid tap coordinates')
    require(x0<=int(cmd[7])<x1 and y0<=int(cmd[8])<y1 and p.get('tap_exit_code')==0,'Tap outside observed enabled switch or failed')
    validate_operator_timing(p,prior,json.loads(raw['pid-observations.json']))
    for name in ('before.png','after.png'):require(raw[name].startswith(b'\x89PNG\r\n\x1a\n') and len(raw[name])>100,'Missing raw UI screenshot')
    return p


def validate_predecessor(path, context, current_pins, operator_path, native_log_errors):
    path=Path(path); prior=read_json(path)
    for key in ('candidate_fingerprint','harness_sha256','device','device_label','platform','run_id'):
        require(prior.get(key)==context[key], 'Predecessor mismatch: '+key)
    require(prior.get('scenario')=='revoked-prepare' and prior.get('status')=='os-interrupted-awaiting-ui-evidence' and prior.get('passed') is False and prior.get('errors')==[],'Not a qualified interrupted preparation')
    require(prior.get('production_differences_after')==[] and prior.get('frozen_source_unchanged') is True and prior.get('source_differences_during_run')==[] and prior.get('generated_harness_matches') is True,'Predecessor source integrity failed')
    require(prior.get('source_pins')==current_pins,'Predecessor tool/harness revision differs')
    hashes=prior.get('evidence_sha256',{})
    required={'run.log','revoke-checkpoint.json','pre-revocation.log','restart-host-receipts.json','exit-info.txt','permission-after.txt','death-logcat.txt','device-offset.txt','pid-after.txt',*current_pins}
    require(required<=hashes.keys(),'Predecessor evidence incomplete')
    for name,want in hashes.items():
        require(Path(name).name==name and name not in ('.','..','verification.json'),'Unsafe predecessor evidence path')
        p=path.parent/name; require(p.is_file() and not p.is_symlink() and digest(p.read_bytes())==want,'Predecessor evidence changed: '+name)
    require(all(hashes.get(name)==want for name,want in current_pins.items()), 'Archived reviewed source hash differs')
    raw=(path.parent/'revoke-checkpoint.json').read_bytes(); prep=prior['restart_preparation']
    c=checkpoint(raw,prior,prep['marker']); require(digest(raw)==prep['checkpoint_sha256'],'Checkpoint pin differs')
    require((path.parent/'pre-revocation.log').read_bytes()==(path.parent/'run.log').read_bytes()[:prep['pre_log_bytes']],'Prekill log bytes differ')
    for name,want in c['files_sha256'].items():require(hashes.get(file_name(name))==want,'Predecessor durable export missing')
    death=prior['restart_death']
    actual=kill_record((path.parent/'exit-info.txt').read_text(),(path.parent/'death-logcat.txt').read_text(),prep['marker'],(path.parent/'device-offset.txt').read_text().strip(),death['clock_model']['device_after_ns']//1_000_000)
    require(actual==death['kill_utc_ms'] and not (path.parent/'pid-after.txt').read_text().strip(),'Death evidence differs')
    validate_clock_event(death['clock_model'],prior,prep['marker'],actual)
    permission((path.parent/'permission-after.txt').read_text(),False)
    require(not interrupted_errors((path.parent/'run.log').read_text(),(path.parent/'run.log').read_bytes(),prep,death,prior['exit_code'],native_log_errors),'Interrupted log evidence invalid')
    validate_host_receipts(read_json(path.parent/'restart-host-receipts.json'), prior, prep, death)
    validate_operator(operator_path,prior)
    return prior,c


def recovery_errors(payload, context, prior, checkpoint_value, log, marker_pattern, native_log_errors):
    errors=[]
    def check(value,message):
        if not value:errors.append(message)
    if not isinstance(payload,dict):return ['Recovery result absent']
    for key in IDENTITY:check(type(payload.get(key)) is type(context[key]) and payload.get(key)==context[key],'Recovery identity mismatch: '+key)
    for key,want in {'gateway':'NativeNotificationGateway','preference_store':'FileNotificationPreferences','fixture_kind':'SYNTHETIC GAMEPLAY SNAPSHOT; REAL OS NOTIFICATION API','clock':'actual_utc_and_monotonic_stopwatch'}.items():
        check(payload.get(key)==want,'Missing actual recovery API/provenance: '+key)
    events=payload.get('lifecycle_events')
    check(isinstance(events,list) and all(isinstance(e,dict) and e.get('state') in ('resumed','inactive','hidden','paused','detached') and type(e.get('utc_ms')) is int for e in events),'Missing recovery lifecycle observations')
    pid=payload.get('process_id'); check(type(pid) is int and pid>1 and pid!=prior['restart_preparation']['native_pid'],'Recovery requires a different actual PID')
    check(payload.get('previous_process_id')==prior['restart_preparation']['native_pid'],'Wrong previous PID')
    check(payload.get('predecessor_verification_id')==prior['verification_id'] and payload.get('predecessor_checkpoint_sha256')==prior['restart_preparation']['checkpoint_sha256'],'Recovery predecessor differs')
    check(payload.get('completed') is True and payload.get('predecessor_default_opted_out') is True,'Recovery incomplete/default proof missing')
    for key in ('permission_before_initialize','permission_after_initialize','permission_after_reoptin'):check(payload.get(key)=='denied','Actual denied permission missing: '+key)
    check(payload.get('remembered_opt_in_after_initialize') is True,'Restored preference was replaced with fresh default')
    for key in ('pending_before_initialize','active_before_initialize'):
        rows=payload.get(key);check(isinstance(rows,list) and all(type(n) is int and n in (77101,77102,77103) for n in rows),'Missing actual pre-initialization observation')
    for key in ('pending_after_initialize','active_after_initialize','denied_schedule_pending_ids','denied_schedule_active_ids','return_pending_ids','return_active_ids'):check(payload.get(key)==[],'Effective cancellation/no-scheduling missing: '+key)
    files=checkpoint_value['files_sha256'];saves={k:v for k,v in files.items() if k.startswith('save/')}
    for key in ('recovery_files_before','recovery_files_before_reoptin'):check(payload.get(key)==files,'Predecessor durable bytes changed: '+key)
    check(payload.get('recovery_save_files_after')==saves,'Recovered save changed')
    observed=checkpoint_value['preparation']['plan_observation']; plan=checkpoint_value['preparation']['plan']
    check(payload.get('restored_snapshot_id')==observed['saved_snapshot_id'] and payload.get('restored_payload_sha256')==plan['saved_payload_sha256'] and payload.get('restored_settled_through_utc_micros')==observed['saved_settled_through_utc_micros'],'Restored durable payload/cursor/snapshot differs')
    check(payload.get('preferences_after_reoptin',{}).get('enabled') is False and bool(HEX.fullmatch(str(payload.get('preferences_sha256','')))),'Denied re-opt-in was not persisted')
    init=payload.get('initialization_lifecycle_events');check(isinstance(init,list) and all(row.get('state')=='resumed' for row in init),'Boot unexpectedly opened OS permission UI')
    try:
        markers=[json.loads(x) for x in marker_pattern.findall(log)]
        check(markers==payload.get('actions') and len(markers)==1 and markers[0].get('action')=='deny_permission_again_if_prompted','Wrong recovery action sequence')
        for m in markers:check(all(m.get(k)==context[k] for k in IDENTITY) and m.get('process_id')==pid and type(m.get('utc_ms')) is int,'Recovery action identity differs')
    except (ValueError,TypeError):errors.append('Malformed recovery action')
    errors.extend(native_log_errors(log));return errors


def validate_host_receipts(rows, context, preparation, death):
    require(isinstance(rows,list) and rows,'Missing raw host observations')
    pid=preparation['native_pid']
    stamps=[]
    for row in rows:
        command=row.get('argv',[])
        require(len(command)>=4 and Path(command[0]).name=='adb' and command[1:3]==['-s',context['device']], 'Host observation targeted another device')
        stamps.extend(receipt_stamps(row))
    require(all(stamps[i]['monotonic_upper_ns']<=stamps[i+1]['monotonic_lower_ns'] for i in range(len(stamps)-1)), 'Host receipt monotonic chronology invalid')
    ready=checked_stamp(preparation.get('host_ready_stamp'))
    host_clock_consistency(stamps+[ready])
    samples=[row for row in rows if 'clock_phase' in row]
    require(clock_model(samples,context,pid)==death['clock_model'],'Raw same-run clock receipts differ from model')
    validate_clock_event(death['clock_model'],context,preparation['marker'],death['kill_utc_ms'])
    def matching(parts): return [(i,row) for i,row in enumerate(rows) if row['argv'][3:]==parts]
    live=[(i,row) for i,row in matching(['shell','pidof',BUNDLE]) if row.get('exit_code')==0 and row.get('stdout','').strip()==str(pid)]
    require(len(live)==2,'Exact PID must be observed alive before and after export')
    first,last=live[0][0],live[1][0]
    require(max(rows.index(r) for r in samples[:3])<first<last<min(rows.index(r) for r in samples[3:]),'Clock probes do not bracket the causal live/export/live sequence')
    cmdline=[(i,row) for i,row in matching(['exec-out','run-as',BUNDLE,'cat',f'/proc/{pid}/cmdline']) if row.get('exit_code')==0 and row.get('stdout','').split('\0',1)[0]==BUNDLE]
    require(len(cmdline)==2 and first<cmdline[0][0]<last<cmdline[1][0], 'Prekill PID/package binding missing')
    require(cmdline[1][1]['finished_stamp']['monotonic_upper_ns']<=ready['monotonic_lower_ns'], 'Ready stamp precedes confirmed live/export/live sequence')
    absent=[(i,row) for i,row in matching(['shell','pidof',BUNDLE]) if row.get('exit_code')==1 and not row.get('stdout') and not row.get('stderr')]
    require(len(absent)==1 and absent[0][0]>cmdline[1][0] and absent[0][0]<rows.index(samples[3]), 'Actual absent PID is not causally after live/export/live and before post-death probes')
    for relative,want in {'revoke-checkpoint.json':preparation['checkpoint_sha256'],**preparation['files_sha256']}.items():
        limit=131072 if relative=='revoke-checkpoint.json' else 2*1024*1024+65536
        captures=matching(['exec-out','run-as',BUNDLE,'head','-c',str(limit+1),fixture(context)+'/'+relative])
        require(any(cmdline[0][0]<i<last and row.get('exit_code')==0 and digest(row.get('stdout','').encode())==want for i,row in captures),'Missing exact file export causally bracketed by alive observations: '+relative)

# These limits reject poor measurements; they are not a guessed clock offset or
# a tolerance added to the event time. Event translation uses measured bounds.
MAX_PROBE_RTT_NS = 250_000_000
MAX_OFFSET_WIDTH_NS = 100_000_000
MAX_HOST_DRIFT_NS = 5_000_000
MAX_STAMP_READ_NS = 1_000_000
MAX_CLOCK_SPAN_NS = 210_000_000_000
MAX_CLOCK_STALE_NS = 30_000_000_000


def host_stamp():
    lower=time.monotonic_ns()
    wall=time.time_ns()
    upper=time.monotonic_ns()
    return {'utc_ns':wall,'monotonic_lower_ns':lower,'monotonic_upper_ns':upper}


def checked_stamp(value):
    require(isinstance(value,dict) and set(value)=={'utc_ns','monotonic_lower_ns','monotonic_upper_ns'},'Missing bounded host clock stamp')
    require(all(type(n) is int and n>0 for n in value.values()),'Invalid host clock stamp')
    require(0<=value['monotonic_upper_ns']-value['monotonic_lower_ns']<=MAX_STAMP_READ_NS,'Host clock read too broad/reversed')
    return value


def host_clock_consistency(stamps):
    values=[checked_stamp(s) for s in stamps]
    require(values,'Host clock observations missing')
    lower=min(s['utc_ns']-s['monotonic_upper_ns'] for s in values)
    upper=max(s['utc_ns']-s['monotonic_lower_ns'] for s in values)
    require(upper-lower<=MAX_HOST_DRIFT_NS,'Host wall/monotonic clock jumped or drifted beyond measurement quality bound')
    return {'wall_minus_monotonic_lower_ns':lower,'wall_minus_monotonic_upper_ns':upper}


def receipt_stamps(row):
    start=checked_stamp(row.get('started_stamp'));end=checked_stamp(row.get('finished_stamp'))
    require(start['monotonic_upper_ns']<=end['monotonic_lower_ns'],'Host command chronology reversed')
    require(row.get('started_utc_ms')==start['utc_ns']//1_000_000 and row.get('finished_utc_ms')==end['utc_ns']//1_000_000,'Legacy receipt milliseconds differ from raw host clock stamps')
    return start,end


def device_nanoseconds(raw):
    require(isinstance(raw,str) and re.fullmatch(r'[0-9]{10,12}\.[0-9]{9}\r?\n?',raw),'Invalid actual device nanosecond date output')
    seconds,fraction=raw.strip().split('.')
    return int(seconds)*1_000_000_000+int(fraction)


def clock_model(samples, context, pid):
    require(isinstance(samples,list) and len(samples)==6,'Exactly three prospective and three post-death clock samples required')
    require([s.get('clock_phase') for s in samples]==['before_exports']*3+['after_death']*3,'Clock samples are missing, reordered or borrowed')
    expected={k:context[k] for k in IDENTITY};expected.update(device=context['device'],process_id=pid)
    bounds=[];stamps=[];device=[]
    for sample in samples:
        require(sample.get('clock_context')==expected,'Clock sample run/device/PID identity mismatch')
        cmd=sample.get('argv',[])
        require(len(cmd)==7 and Path(cmd[0]).name=='adb' and cmd[1:]==['-s',context['device'],'shell','date','-u','+%s.%N'],'Clock sample was not the exact read-only device date command')
        require(sample.get('exit_code')==0 and not sample.get('stderr'),'Clock probe failed')
        start,end=receipt_stamps(sample);stamps += [start,end]
        require(end['monotonic_upper_ns']-start['monotonic_lower_ns']<=MAX_PROBE_RTT_NS,'Clock probe round trip too broad')
        d=device_nanoseconds(sample.get('stdout'));device.append(d)
        # Device date was sampled sometime during this host request/response.
        bounds.append((start['utc_ns']-d,end['utc_ns']-d))
    require(all(stamps[i]['monotonic_upper_ns']<=stamps[i+1]['monotonic_lower_ns'] for i in range(len(stamps)-1)),'Clock samples overlap or reorder')
    require(device==sorted(set(device)),'Device clock samples did not increase')
    require(stamps[-1]['monotonic_upper_ns']-stamps[0]['monotonic_lower_ns']<=MAX_CLOCK_SPAN_NS,'Clock brackets are stale for this bounded preparation')
    host=host_clock_consistency(stamps)
    groups=[(max(x[0] for x in bounds[i:i+3]),min(x[1] for x in bounds[i:i+3])) for i in (0,3)]
    require(all(lo<=hi for lo,hi in groups),'Inconsistent device/host clock samples within phase')
    require(max(g[0] for g in groups)<=min(g[1] for g in groups),'Device/host offset changed between pre/post brackets')
    # Retain the conservative envelope of both phase intervals rather than a
    # selected midpoint or the narrower cross-phase intersection.
    low=min(g[0] for g in groups);high=max(g[1] for g in groups)
    require(high-low<=MAX_OFFSET_WIDTH_NS,'Measured offset uncertainty too broad')
    return {'version':1,'samples':samples,'host_minus_device_lower_ns':low,
            'host_minus_device_upper_ns':high,'device_before_ns':device[0],
            'device_pre_end_ns':device[2],'device_after_ns':device[3],
            'device_post_end_ns':device[-1],**host}


def validate_clock_event(model, context, marker, kill_ms):
    expected=clock_model(model.get('samples'),context,marker['process_id'])
    require(model==expected,'Recorded measured clock model differs from raw brackets')
    marker_ns=marker['utc_ms']*1_000_000;kill_ns=kill_ms*1_000_000
    require(marker_ns<=model['device_before_ns']<=marker_ns+MAX_CLOCK_STALE_NS,'Prospective clock bracket is stale or precedes this device marker')
    require(model['device_pre_end_ns']<kill_ns<=model['device_after_ns'],'Clock samples do not prospectively bracket this actual device kill')
    require(model['device_after_ns']-kill_ns<=MAX_CLOCK_STALE_NS,'Post-death clock bracket too late')
    return (kill_ns+model['host_minus_device_lower_ns'],
            kill_ns+1_000_000+model['host_minus_device_upper_ns'])


def validate_operator_timing(packet, prior, pid_rows):
    prep=prior['restart_preparation'];death=prior['restart_death'];model=death['clock_model']
    kill_low,kill_high=validate_clock_event(model,prior,prep['marker'],death['kill_utc_ms'])
    timeline=packet.get('host_timeline',{})
    names=('before','action_started','action_finished','after')
    require(set(timeline)==set(names),'Missing actual operator wall/monotonic timeline')
    stamps=[checked_stamp(timeline[name]) for name in names]
    require(all(stamps[i]['monotonic_upper_ns']<=stamps[i+1]['monotonic_lower_ns'] for i in range(3)),'Operator monotonic order invalid')
    for name,stamp in zip(names,stamps):require(packet.get(name+'_utc_ms')==stamp['utc_ns']//1_000_000,'Operator milliseconds differ from raw host stamp')
    ready=checked_stamp(prep.get('host_ready_stamp'))
    require(ready['monotonic_upper_ns']<=stamps[0]['monotonic_lower_ns'],'Operator began before confirmed prekill export')
    require(isinstance(pid_rows,list) and len(pid_rows)==2,'Require actual live-before and absent-after PID receipts')
    pid_stamps=[]
    for row,alive in zip(pid_rows,(True,False)):
        cmd=row.get('argv',[])
        require(len(cmd)==6 and Path(cmd[0]).name=='adb' and cmd[1:]==['-s',prior['device'],'shell','pidof',BUNDLE],'Operator PID observation targets wrong process/device')
        require(not row.get('stderr') and row.get('exit_code')==(0 if alive else 1) and row.get('stdout','').strip()==(str(prep['native_pid']) if alive else ''),'Missing actual live/absent PID state')
        start,end=receipt_stamps(row);pid_stamps += [start,end]
    require(stamps[0]['monotonic_upper_ns']<=pid_stamps[0]['monotonic_lower_ns'] and pid_stamps[1]['monotonic_upper_ns']<=stamps[1]['monotonic_lower_ns'],'PID was not observed alive between actual ON observation and tap')
    require(stamps[1]['monotonic_upper_ns']-pid_stamps[1]['monotonic_lower_ns']<=5_000_000_000,'Pre-tap alive observation is stale')
    require(stamps[2]['monotonic_upper_ns']<=pid_stamps[2]['monotonic_lower_ns'] and pid_stamps[3]['monotonic_upper_ns']<=stamps[3]['monotonic_lower_ns'],'PID absence was not observed after actual tap and before final OFF observation')
    require(stamps[3]['monotonic_upper_ns']-stamps[1]['monotonic_lower_ns']<=MAX_CLOCK_STALE_NS,'Actual OFF observation too late')
    require(stamps[3]['monotonic_upper_ns']<=model['samples'][-1]['finished_stamp']['monotonic_upper_ns']+MAX_CLOCK_STALE_NS,'Operator observations stale relative to this run clock bracket')
    # An asynchronous permission kill may follow command completion. Require
    # consistency with the measured tap-to-OFF interval, not exact sub-RTT
    # ordering that the calibration cannot prove. Alive-before/absent-after,
    # ON/OFF UI, unique PID/reason, and the same-device180s guard supply the
    # independent causal evidence. Do not call an interval overlap a timestamp
    # proof that the kill occurred during the shell command.
    require(kill_high>=stamps[1]['utc_ns'] and kill_low<=stamps[3]['utc_ns'],'Measured kill interval is inconsistent with actual tap-to-OFF observations')
    host_clock_consistency(stamps+pid_stamps+[ready]+[s[k] for s in model['samples'] for k in ('started_stamp','finished_stamp')])
    return {'kill_host_interval_ns':[kill_low,kill_high],'timing_relation':'consistent_with_actual_tap_to_off_interval; causal_PID_UI_evidence_also_required'}
