from pathlib import Path
b=Path(__file__).resolve().parent;p=b/'staged/tool/reminder_restart.py';s=p.read_text()
s=s.replace('def kill_record(exit_text, logcat, marker, offset, observed_ms):','def kill_record(exit_text, logcat, marker, offset, after_device_ms):')
s=s.replace("marker['utc_ms']<=at<=observed_ms", "marker['utc_ms']<=at<=after_device_ms")
s=s.replace("        started=int(time.time()*1000)\n        result=subprocess.run(cmd,capture_output=True,timeout=20)\n        self.receipts.append({'argv':cmd,'started_utc_ms':started,'finished_utc_ms':int(time.time()*1000),'exit_code':result.returncode,'stdout':result.stdout.decode(errors='replace'),'stderr':result.stderr.decode(errors='replace')})", "        started=host_stamp()\n        result=subprocess.run(cmd,capture_output=True,timeout=20)\n        finished=host_stamp()\n        self.receipts.append({'argv':cmd,'started_stamp':started,'finished_stamp':finished,'started_utc_ms':started['utc_ns']//1_000_000,'finished_utc_ms':finished['utc_ns']//1_000_000,'exit_code':result.returncode,'stdout':result.stdout.decode(errors='replace'),'stderr':result.stderr.decode(errors='replace')})")
s=s.replace("    def save_receipts(self):", "    def sample_clock(self, phase, pid):\n        for _ in range(3):\n            self.command('shell','date','-u','+%s.%N')\n            self.receipts[-1].update(clock_phase=phase,clock_context={**{k:self.context[k] for k in IDENTITY},'device':self.context['device'],'process_id':pid})\n    def save_receipts(self):")
s=s.replace("    def capture_preparation(self, marker, raw_log):\n        try:\n            self.alive", "    def capture_preparation(self, marker, raw_log):\n        try:\n            self.sample_clock('before_exports',marker['process_id'])\n            self.alive")
s=s.replace("'pre_log_bytes':len(raw_log),'pre_log_sha256':digest(raw_log),'files_sha256':value['files_sha256']}","'pre_log_bytes':len(raw_log),'pre_log_sha256':digest(raw_log),'files_sha256':value['files_sha256'], 'host_ready_stamp':host_stamp()}")
s=s.replace("            at=kill_record(texts['exit-info.txt'],texts['death-logcat.txt'],preparation['marker'],texts['device-offset.txt'].strip(),observed)\n            for name,want in preparation['files_sha256'].items():", "            for name,want in preparation['files_sha256'].items():")
s=s.replace("            return {'kill_utc_ms':at,'observed_utc_ms':observed,'reason':'PERMISSION CHANGE','process_id':preparation['native_pid']}", "            self.sample_clock('after_death',preparation['native_pid'])\n            model=clock_model([r for r in self.receipts if 'clock_phase' in r],self.context,preparation['native_pid'])\n            at=kill_record(texts['exit-info.txt'],texts['death-logcat.txt'],preparation['marker'],texts['device-offset.txt'].strip(),model['device_after_ns']//1_000_000)\n            validate_clock_event(model,self.context,preparation['marker'],at)\n            return {'kill_utc_ms':at,'observed_utc_ms':observed,'reason':'PERMISSION CHANGE','process_id':preparation['native_pid'],'clock_model':model}")
s=s.replace("required={'before.xml','after.xml','before.png','after.png','settings-activities.txt'}", "required={'before.xml','after.xml','before.png','after.png','settings-activities.txt','pid-observations.json'}")
start=s.index("    times=[p.get(k) for k in ('before_utc_ms'")
end=s.index("    for name in ('before.png','after.png'):",start)
s=s[:start]+"    validate_operator_timing(p,prior,json.loads(raw['pid-observations.json']))\n"+s[end:]
s=s.replace("death['observed_utc_ms'])", "death['clock_model']['device_after_ns']//1_000_000)")
s=s.replace("    permission((path.parent/'permission-after.txt').read_text(),False)", "    validate_clock_event(death['clock_model'],prior,prep['marker'],actual)\n    permission((path.parent/'permission-after.txt').read_text(),False)")
start=s.index('def validate_host_receipts(')
s=s[:start]+'''def validate_host_receipts(rows, context, preparation, death):
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
    cmdline=[(i,row) for i,row in matching(['exec-out','run-as',BUNDLE,'cat',f'/proc/{pid}/cmdline']) if row.get('exit_code')==0 and row.get('stdout','').split('\\0',1)[0]==BUNDLE]
    require(len(cmdline)==2 and first<cmdline[0][0]<last<cmdline[1][0], 'Prekill PID/package binding missing')
    require(cmdline[1][1]['finished_stamp']['monotonic_upper_ns']<=ready['monotonic_lower_ns'], 'Ready stamp precedes confirmed live/export/live sequence')
    absent=[(i,row) for i,row in matching(['shell','pidof',BUNDLE]) if row.get('exit_code')==1 and not row.get('stdout') and not row.get('stderr')]
    require(len(absent)==1 and absent[0][0]>cmdline[1][0] and absent[0][0]<rows.index(samples[3]), 'Actual absent PID is not causally after live/export/live and before post-death probes')
    for relative,want in {'revoke-checkpoint.json':preparation['checkpoint_sha256'],**preparation['files_sha256']}.items():
        limit=131072 if relative=='revoke-checkpoint.json' else 2*1024*1024+65536
        captures=matching(['exec-out','run-as',BUNDLE,'head','-c',str(limit+1),fixture(context)+'/'+relative])
        require(any(cmdline[0][0]<i<last and row.get('exit_code')==0 and digest(row.get('stdout','').encode())==want for i,row in captures),'Missing exact file export causally bracketed by alive observations: '+relative)
'''
s+=(b/'staged/tool/clock_addition.txt').read_text();p.write_text(s)
