from pathlib import Path
p=Path(__file__).parent/'staged/tool/reminder_restart.py';s=p.read_text()
s=s.replace("READY = 'revoke_in_os_settings_expect_process_death'", "READY = 'revoke_in_os_settings_expect_process_death'\nMARKER = re.compile(r'^(?:flutter:|I/flutter\\s*\\(\\s*\\d+\\):)\\s*TIDEGLASS_REMINDER_ACTION (\\{[^\\n]+\\})\\s*$', re.M)")
s=s.replace("    plan=prior.get('plan',{}); observed=prior.get('plan_observation',{})", """    actions=prior.get('actions',[])
    require(len(actions)==1 and actions[0].get('action')=='allow_permission_if_prompted'
        and all(actions[0].get(key)==context[key] for key in IDENTITY)
        and actions[0].get('process_id')==pid, 'Preparation lacks exact actual opt-in action')
    require(prior.get('lifecycle_callback_failures')==[], 'Preparation callback failed')
    require(isinstance(prior.get('initialization_lifecycle_events'),list) and all(row.get('state')=='resumed' for row in prior['initialization_lifecycle_events']), 'Initialization opened permission UI')
    plan=prior.get('plan',{}); observed=prior.get('plan_observation',{})""")
s=s.replace("        negative=[x for x in native_log_errors(log) if not x.startswith('No successful')]", """        markers=[json.loads(raw) for raw in MARKER.findall(log)]
        require(len(markers)==2 and [m.get('action') for m in markers]==['allow_permission_if_prompted',READY] and markers[1]==preparation['marker'], 'Missing, duplicate or stale preparation markers')
        require(all(all(m.get(key)==preparation['marker'][key] for key in IDENTITY) and m.get('process_id')==preparation['native_pid'] for m in markers), 'Preparation action identity differs')
        negative=[x for x in native_log_errors(log) if not x.startswith('No successful')]""")
s=s.replace("    require(hashes['", "    require(hashes['")
s=s.replace("    raw=(path.parent/'revoke-checkpoint.json').read_bytes(); prep=prior['restart_preparation']", "    require(all(hashes.get(name)==want for name,want in current_pins.items()), 'Archived reviewed source hash differs')\n    raw=(path.parent/'revoke-checkpoint.json').read_bytes(); prep=prior['restart_preparation']")
s=s.replace("    validate_operator(operator_path,prior)\n    return prior,c", "    validate_host_receipts(read_json(path.parent/'restart-host-receipts.json'), prior, prep, death)\n    validate_operator(operator_path,prior)\n    return prior,c")
s += '''\n\ndef validate_host_receipts(rows, context, preparation, death):
    require(isinstance(rows,list) and rows,'Missing raw host observations')
    pid=preparation['native_pid']; marker=preparation['marker']
    for row in rows:
        command=row.get('argv',[])
        require(len(command)>=4 and Path(command[0]).name=='adb' and command[1:3]==['-s',context['device']], 'Host observation targeted another device')
        require(type(row.get('started_utc_ms')) is int and type(row.get('finished_utc_ms')) is int and row['started_utc_ms']<=row['finished_utc_ms'], 'Host observation time missing')
    def matching(parts): return [row for row in rows if row['argv'][3:]==parts]
    live=[row for row in matching(['shell','pidof',BUNDLE]) if row.get('exit_code')==0 and row.get('stdout','').strip()==str(pid) and marker['utc_ms']<=row['started_utc_ms']<=row['finished_utc_ms']<death['kill_utc_ms']]
    require(len(live)>=2,'Exact PID not observed alive around checkpoint export')
    cmdline=[row for row in matching(['exec-out','run-as',BUNDLE,'cat',f'/proc/{pid}/cmdline']) if row.get('exit_code')==0 and row.get('stdout','').split('\\0',1)[0]==BUNDLE and row['finished_utc_ms']<death['kill_utc_ms']]
    require(len(cmdline)>=2,'Prekill PID/package binding missing')
    absent=[row for row in matching(['shell','pidof',BUNDLE]) if row.get('exit_code')==1 and not row.get('stdout') and not row.get('stderr') and row['started_utc_ms']>=death['kill_utc_ms']]
    require(absent,'Actual absent PID observation missing')
    for relative,want in {'revoke-checkpoint.json':preparation['checkpoint_sha256'],**preparation['files_sha256']}.items():
        limit=131072 if relative=='revoke-checkpoint.json' else 2*1024*1024+65536
        captures=matching(['exec-out','run-as',BUNDLE,'head','-c',str(limit+1),fixture(context)+'/'+relative])
        require(any(row.get('exit_code')==0 and marker['utc_ms']<=row['started_utc_ms']<=row['finished_utc_ms']<death['kill_utc_ms'] and digest(row.get('stdout','').encode())==want for row in captures),'Missing exact prekill file export: '+relative)
'''
p.write_text(s)
