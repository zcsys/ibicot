from pathlib import Path
s=Path('release/native-notifications/revoked-clock-repair-20261025T165159.000038Z/staged/tool')
p=s/'reminder_restart.py'
t=p.read_text().replace("at=int(datetime.strptime(head[1]+offset,'%Y-%m-%d %H:%M:%S.%f%z').timestamp()*1000)","stamp=datetime.strptime(head[1]+offset,'%Y-%m-%d %H:%M:%S.%f%z')-datetime(1970,1,1,tzinfo=timezone.utc)\n            at=stamp.days*86400000+stamp.seconds*1000+stamp.microseconds//1000")
t=t.replace('milliseconds, tap_argv/exit_code, and files_sha256 of before/after XML+PNG and\n    Settings activity dump.', 'milliseconds plus their bounded wall/monotonic host_timeline, tap_argv/exit_code,\n    and files_sha256 of before/after XML+PNG, Settings activity dump, and raw\n    live-before/absent-after PID command receipts.')
p.write_text(t)
p=s/'test_reminder_restart.py';t=p.read_text()
insert='''def stamp(at_ms):
    # Synthetic one-host clock: host UTC and monotonic elapsed have fixed offset.
    utc=at_ms*1_000_000;mono=1_000_000_000_000+(at_ms-NOW)*1_000_000
    return {'utc_ns':utc,'monotonic_lower_ns':mono,'monotonic_upper_ns':mono+1000}


def receipt(parts,stdout,at,code=0,duration_ms=1):
    return {'argv':['/sdk/adb','-s','emulator-5556',*parts],
            'started_stamp':stamp(at),'finished_stamp':stamp(at+duration_ms),
            'started_utc_ms':at,'finished_utc_ms':at+duration_ms,
            'exit_code':code,'stdout':stdout,'stderr':''}


def clock_receipts(context,offset_ms=440):
    rows=[]
    for phase,base in [('before_exports',1000),('after_death',12000)]:
        for i in range(3):
            at=NOW+base+i*50
            device=(at+10-offset_ms)*1_000_000
            raw=f'{device//1_000_000_000}.{device%1_000_000_000:09d}\\n'
            row=receipt(['shell','date','-u','+%s.%N'],raw,at,duration_ms=20)
            row.update(clock_phase=phase,clock_context={**{k:context[k] for k in restart.IDENTITY},'device':context['device'],'process_id':42})
            rows.append(row)
    return rows


'''
t=t.replace('def world(base):',insert+'def world(base):')
a=t.index("    preparation={'marker':m");b=t.index("    files={**source",a)
t=t[:a]+'''    preparation={'marker':m,'checkpoint_sha256':restart.digest(raw),'native_pid':42,'pre_log_bytes':len(prelog),'pre_log_sha256':restart.digest(prelog),'files_sha256':c['files_sha256'],'host_ready_stamp':stamp(NOW+4000)}
    samples=clock_receipts(context)
    death={'process_id':42,'kill_utc_ms':NOW+10000,'observed_utc_ms':NOW+13000,'reason':'PERMISSION CHANGE','clock_model':restart.clock_model(samples,context,42)}
    receipts=[*samples[:3],receipt(['shell','pidof',restart.BUNDLE],'42\\n',NOW+2000),receipt(['exec-out','run-as',restart.BUNDLE,'cat','/proc/42/cmdline'],restart.BUNDLE+'\\0',NOW+2010)]
    for i,(relative,content) in enumerate({'revoke-checkpoint.json':raw,**data}.items()):
        limit=131072 if relative=='revoke-checkpoint.json' else 2*1024*1024+65536
        receipts.append(receipt(['exec-out','run-as',restart.BUNDLE,'head','-c',str(limit+1),restart.fixture(context)+'/'+relative],content.decode(),NOW+2200+i*10))
    receipts += [receipt(['shell','pidof',restart.BUNDLE],'42\\n',NOW+3000),receipt(['exec-out','run-as',restart.BUNDLE,'cat','/proc/42/cmdline'],restart.BUNDLE+'\\0',NOW+3010),receipt(['shell','pidof',restart.BUNDLE],'',NOW+11000,1),*samples[3:]]
''' +t[b:]
t=t.replace("'settings-activities.txt':b'com.android.settings", "'pid-observations.json':encode([receipt(['shell','pidof',restart.BUNDLE],'42\\n',NOW+10100),receipt(['shell','pidof',restart.BUNDLE],'',NOW+11000,1)]),\n             'settings-activities.txt':b'com.android.settings")
t=t.replace("'before_utc_ms':NOW+2000,'action_started_utc_ms':NOW+9000,'action_finished_utc_ms':NOW+10001,'after_utc_ms':NOW+15000,", "'before_utc_ms':NOW+6000,'action_started_utc_ms':NOW+10200,'action_finished_utc_ms':NOW+10260,'after_utc_ms':NOW+11500,\n        'host_timeline':{k:stamp(NOW+v) for k,v in [('before',6000),('action_started',10200),('action_finished',10260),('after',11500)]},")
p.write_text(t)
