"""Host-only controls for restart qualification. No device/Flutter invocation."""
import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import reminder_restart as restart
import verify_native_reminders as runner

GOOD_LOG='I/flutter ( 43): 00:10 +1: All tests passed!\nAll tests passed.\n'
DISCONNECT='Unhandled exception:\nDriverError: Failed to fulfill RequestData due to remote error\nOriginal error: ext.flutter.driver: (112) Service has disappeared\n'
NOW=1792944470000


def encode(value):return json.dumps(value,separators=(',',':')).encode()


def shape():
    context={'verification_id':'fresh-preparation','candidate_fingerprint':'a'*64,'harness_sha256':'b'*64,
             'scenario':'revoked-prepare','run_id':'pair-one','device_label':'android','platform':'android','device':'emulator-5556'}
    action={k:context[k] for k in restart.IDENTITY}; action.update(process_id=42,action='allow_permission_if_prompted',utc_ms=NOW-100)
    payload={'radiance':'synthetic-control'}
    observed={'warning_key':None,'pending_ids':[77101],'saved_payload':payload,'game_payload':payload,
              'saved_settled_through_utc_micros':NOW*1000,'game_settled_through_utc_micros':NOW*1000,'saved_snapshot_id':'snapshot-one'}
    plan={'ids':[77101],'kinds':['focus'],'production_lifecycle':True,'body':'Focus is available for your next constellation. Return whenever you like.',
          'background_call_utc_ms':NOW-1000,'scheduled_observed_utc_ms':NOW-500,'due_utc_ms':NOW+300000,
          'saved_snapshot_id':'snapshot-one','saved_payload_sha256':restart.digest(encode(payload))}
    data={'notification_preferences.json':encode({'enabled':True}),'save/progress.0.json':b'{"save_id":"snapshot-one"}'}
    prep={**{k:context[k] for k in restart.IDENTITY},'process_id':42,'completed':False,'default_opted_out':True,'default_preferences_file_absent':True,'default_pending_ids':[],
          'permission_before_initialize':'allowed','permission_after_initialize':'allowed','permission_after_opt_in':'allowed',
          'gateway':'NativeNotificationGateway','preference_store':'FileNotificationPreferences','preferences_after_opt_in':{'enabled':True},
          'actions':[action],'initialization_lifecycle_events':[],'lifecycle_callback_failures':[],
          'plan':plan,'plan_observation':observed,'preferences_sha256':restart.digest(data['notification_preferences.json'])}
    check={'version':1,'written_utc_ms':NOW,'preparation':prep,'files_sha256':{k:restart.digest(v) for k,v in data.items()}}
    raw=encode(check)
    marker={**{k:context[k] for k in restart.IDENTITY},'process_id':42,'action':restart.READY,'utc_ms':NOW+1,
            'checkpoint':restart.fixture(context)+'/revoke-checkpoint.json','checkpoint_sha256':restart.digest(raw)}
    return context,check,marker,data


def native_log(check,marker):
    return ''.join('I/flutter ( 42): TIDEGLASS_REMINDER_ACTION '+json.dumps(v)+'\n' for v in [*check['preparation']['actions'],marker])


def exit_text(pid=42,reason=8,at=NOW+10000):
    stamp=datetime.fromtimestamp(at/1000,timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return f'package: dev.tideglass.game\nApplicationExitInfo #0:\n timestamp={stamp} pid={pid} realUid=123\n process=dev.tideglass.game reason={reason} (PERMISSION CHANGE) subreason=0\n description=PermissionHelper\n'


def xml(checked):
    return ('<?xml version="1.0"?><hierarchy><node resource-id="com.android.settings:id/switch_text" text="All Tideglass notifications"/>'
            '<node resource-id="android:id/switch_widget" package="com.android.settings" enabled="true" checked="'+str(checked).lower()+'" bounds="[10,20][40,50]"/></hierarchy>UI hierchary dumped to: /dev/tty')


def world(base):
    context,c,m,data=shape();raw=encode(c); prelog=native_log(c,m).encode();full=prelog+DISCONNECT.encode()
    source={'harness.dart':b'reviewed harness','driver.dart':b'reviewed driver','verify_native_reminders.py':b'reviewed runner','reminder_restart.py':b'reviewed restart','verify_native.py':b'reviewed verify','build_native.py':b'reviewed build'}
    # Keep context and checkpoint consistent with the reviewed harness bytes.
    h=restart.digest(source['harness.dart']);context['harness_sha256']=h;c['preparation']['harness_sha256']=h;c['preparation']['actions'][0]['harness_sha256']=h;m['harness_sha256']=h
    raw=encode(c);m['checkpoint_sha256']=restart.digest(raw);prelog=native_log(c,m).encode();full=prelog+DISCONNECT.encode()
    preparation={'marker':m,'checkpoint_sha256':restart.digest(raw),'native_pid':42,'pre_log_bytes':len(prelog),'pre_log_sha256':restart.digest(prelog),'files_sha256':c['files_sha256']}
    death={'process_id':42,'kill_utc_ms':NOW+10000,'observed_utc_ms':NOW+20000,'reason':'PERMISSION CHANGE'}
    def receipt(parts,stdout,at,code=0):return {'argv':['/sdk/adb','-s','emulator-5556',*parts],'started_utc_ms':at,'finished_utc_ms':at+1,'exit_code':code,'stdout':stdout,'stderr':''}
    receipts=[]
    for at in (NOW+10,NOW+1000):
        receipts += [receipt(['shell','pidof',restart.BUNDLE],'42\n',at),receipt(['exec-out','run-as',restart.BUNDLE,'cat','/proc/42/cmdline'],restart.BUNDLE+'\0',at+2)]
    for relative,content in {'revoke-checkpoint.json':raw,**data}.items():
        limit=131072 if relative=='revoke-checkpoint.json' else 2*1024*1024+65536
        receipts.append(receipt(['exec-out','run-as',restart.BUNDLE,'head','-c',str(limit+1),restart.fixture(context)+'/'+relative],content.decode(),NOW+100))
    receipts.append(receipt(['shell','pidof',restart.BUNDLE],'',NOW+11000,1))
    files={**source,'run.log':full,'pre-revocation.log':prelog,'revoke-checkpoint.json':raw,
           'restart-host-receipts.json':encode(receipts),'exit-info.txt':exit_text().encode(),
           'permission-after.txt':b'  Package [dev.tideglass.game]\n android.permission.POST_NOTIFICATIONS: granted=false, flags=[]\n',
           'death-logcat.txt':b'10-25 16:08:00.000 1 2 I ActivityManager: Killing 42:dev.tideglass.game/u0a2 (adj 700): PermissionHelper\n',
           'device-offset.txt':b'+0000\n','pid-after.txt':b'',
           **{restart.file_name(k):v for k,v in data.items()}}
    for name,content in files.items():(base/name).write_bytes(content)
    pins={k:restart.digest(v) for k,v in source.items()}
    prior={**context,'source_pins':pins,'status':'os-interrupted-awaiting-ui-evidence','passed':False,'errors':[],
           'production_differences_after':[],'frozen_source_unchanged':True,'source_differences_during_run':[],
           'generated_harness_matches':True,'restart_preparation':preparation,'restart_death':death,'exit_code':1,
           'evidence_sha256':{k:restart.digest(v) for k,v in files.items()}}
    (base/'verification.json').write_bytes(encode(prior))
    opdir=base/'operator';opdir.mkdir()
    opfiles={'before.xml':xml(True).encode(),'after.xml':xml(False).encode(),'before.png':b'\x89PNG\r\n\x1a\n'+b'a'*150,'after.png':b'\x89PNG\r\n\x1a\n'+b'b'*150,
             'settings-activities.txt':b'com.android.settings/.Settings$AppNotificationSettingsActivity\nandroid.settings.APP_NOTIFICATION_SETTINGS\nlaunchedFromPackage=dev.tideglass.game\napp=ProcessRecord{abc 42:dev.tideglass.game/u0a2}\n'}
    for name,content in opfiles.items():(opdir/name).write_bytes(content)
    op={**{k:prior[k] for k in restart.IDENTITY},'process_id':42,'before_utc_ms':NOW+2000,'action_started_utc_ms':NOW+9000,'action_finished_utc_ms':NOW+10001,'after_utc_ms':NOW+15000,
        'tap_argv':['/sdk/adb','-s','emulator-5556','shell','input','touchscreen','tap','25','35'],'tap_exit_code':0,'files_sha256':{k:restart.digest(v) for k,v in opfiles.items()}}
    (opdir/'operator.json').write_bytes(encode(op))
    recover={**context,'scenario':'revoked-recover','verification_id':'fresh-recovery'}
    return prior,c,recover,pins,opdir/'operator.json'


class RestartProtocolTests(unittest.TestCase):
    def test_fresh_checkpoint_positive(self):
        ctx,c,m,_=shape();self.assertEqual(restart.checkpoint(encode(c),ctx,m),c)
    def test_checkpoint_rejects_stale_identity_pid_path_hash_and_minimum(self):
        ctx,c,m,_=shape()
        for key,value in [('process_id',43),('candidate_fingerprint','f'*64),('checkpoint','/tmp/checkpoint'),('checkpoint_sha256','c'*64),('utc_ms',NOW-1)]:
            bad=copy.deepcopy(m);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):restart.checkpoint(encode(c),ctx,bad)
        bad=copy.deepcopy(c);bad['preparation']['plan']['due_utc_ms']=NOW+1000
        cm={**m,'checkpoint_sha256':restart.digest(encode(bad))}
        with self.assertRaises(ValueError):restart.checkpoint(encode(bad),ctx,cm)
    def test_checkpoint_rejects_replaced_save_and_fresh_optout(self):
        ctx,c,m,_=shape()
        for mutate in [lambda q:q['preparation']['plan_observation'].update(game_payload={}),lambda q:q['files_sha256'].update({'../private':'c'*64}),lambda q:q['preparation']['preferences_after_opt_in'].update(enabled=False),lambda q:q['preparation'].update(completed=True),lambda q:q['preparation'].update(lifecycle_callback_failures=[{'error':'x'}])]:
            bad=copy.deepcopy(c);mutate(bad);cm={**m,'checkpoint_sha256':restart.digest(encode(bad))}
            with self.assertRaises(ValueError):restart.checkpoint(encode(bad),ctx,cm)
    def test_actual_permission_kill_positive_and_wrong_old_pid_reason_time_rejected(self):
        _,_,m,_=shape();log='Killing 42:dev.tideglass.game/u0a2 (adj 700): PermissionHelper\n'
        self.assertEqual(restart.kill_record(exit_text(),log,m,'+0000',NOW+20000),NOW+10000)
        for text in [exit_text(pid=41),exit_text(reason=10),exit_text(at=NOW-10000),exit_text(at=NOW+181000),exit_text()+exit_text()]:
            with self.subTest(text=text),self.assertRaises(ValueError):restart.kill_record(text,log,m,'+0000',NOW+200000)
        with self.assertRaises(ValueError):restart.kill_record(exit_text(),'unrelated',m,'+0000',NOW+20000)
    def test_permission_observation_cannot_be_other_package_or_allowed(self):
        restart.permission('Package [dev.tideglass.game]\nandroid.permission.POST_NOTIFICATIONS: granted=false, flags=[]',False)
        for text in ['Package [other]\nandroid.permission.POST_NOTIFICATIONS: granted=false,','Package [dev.tideglass.game]\nandroid.permission.POST_NOTIFICATIONS: granted=true,']:
            with self.assertRaises(ValueError):restart.permission(text,False)
    def test_full_predecessor_positive_with_realistic_raw_evidence(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp);prior,c,ctx,pins,op=world(base)
            self.assertEqual(restart.validate_predecessor(base/'verification.json',ctx,pins,op,runner.verify_native.native_log_errors),(prior,c))
    def test_full_predecessor_rejects_same_process_old_scenario_or_false_pass(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp);prior,c,ctx,pins,op=world(base)
            for field,value in [('scenario','revoked'),('passed',True),('errors',['old failure']),('frozen_source_unchanged',False),('device','emulator-5554'),('status','passed')]:
                bad={**prior,field:value};(base/'verification.json').write_bytes(encode(bad))
                with self.subTest(field=field),self.assertRaises(ValueError):restart.validate_predecessor(base/'verification.json',ctx,pins,op,runner.verify_native.native_log_errors)
    def test_changed_archived_harness_durable_file_and_unsafe_evidence_rejected(self):
        for name in ['harness.dart','save-progress.0.json','run.log']:
            with TemporaryDirectory() as tmp:
                base=Path(tmp);prior,c,ctx,pins,op=world(base);(base/name).write_text('changed')
                with self.subTest(name=name),self.assertRaises(ValueError):restart.validate_predecessor(base/'verification.json',ctx,pins,op,runner.verify_native.native_log_errors)
        with TemporaryDirectory() as tmp:
            base=Path(tmp);prior,c,ctx,pins,op=world(base);prior['evidence_sha256']['../outside']='c'*64;(base/'verification.json').write_bytes(encode(prior))
            with self.assertRaises(ValueError):restart.validate_predecessor(base/'verification.json',ctx,pins,op,runner.verify_native.native_log_errors)
    def test_host_observations_require_actual_live_pid_cmdline_and_prekill_bytes(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp);prior,_,_,_,_=world(base);rows=restart.read_json(base/'restart-host-receipts.json')
            restart.validate_host_receipts(rows,prior,prior['restart_preparation'],prior['restart_death'])
            for mutation in [lambda x:[r for r in x if 'pidof' not in r['argv']],lambda x:[r for r in x if 'cmdline' not in ' '.join(r['argv'])],lambda x:[r for r in x if 'head' not in r['argv']]]:
                with self.assertRaises(ValueError):restart.validate_host_receipts(mutation(copy.deepcopy(rows)),prior,prior['restart_preparation'],prior['restart_death'])
    def test_actual_ui_packet_rejects_wrong_device_pid_tap_and_temporal_binding(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp);prior,_,_,_,op=world(base);valid=restart.read_json(op)
            self.assertEqual(restart.validate_operator(op,prior),valid)
            for field,value in [('process_id',99),('action_started_utc_ms',NOW+11000),('tap_exit_code',1),('tap_argv',['adb','-s','emulator-5554','shell','input','touchscreen','tap','25','35']),('tap_argv',['adb','-s','emulator-5556','shell','input','touchscreen','tap','99','99'])]:
                op.write_bytes(encode({**valid,field:value}))
                with self.subTest(field=field),self.assertRaises(ValueError):restart.validate_operator(op,prior)
    def test_ui_switched_state_and_package_route_are_required(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp);prior,_,_,_,op=world(base);valid=restart.read_json(op)
            for name,content in [('after.xml',xml(True).encode()),('settings-activities.txt',b'other package')]:
                (op.parent/name).write_bytes(content);bad=copy.deepcopy(valid);bad['files_sha256'][name]=restart.digest(content);op.write_bytes(encode(bad))
                with self.assertRaises(ValueError):restart.validate_operator(op,prior)
    def test_unexpected_test_failure_or_fake_success_is_not_permission_interruption(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp);prior,_,_,_,_=world(base);raw=(base/'run.log').read_bytes();args=(prior['restart_preparation'],prior['restart_death'])
            self.assertEqual(restart.interrupted_errors(raw.decode(),raw,*args,1,runner.verify_native.native_log_errors),[])
            for log,code in [(raw.decode()+'\nEXCEPTION CAUGHT BY FLUTTER TEST FRAMEWORK',1),(raw.decode(),0),(raw.decode().replace('Service has disappeared','some unrelated error'),1)]:
                self.assertTrue(restart.interrupted_errors(log,log.encode(),*args,code,runner.verify_native.native_log_errors))
    def test_private_path_refuses_unlisted_files_before_any_command(self):
        ctx,_,_,_=shape()
        with TemporaryDirectory() as tmp,patch.object(restart.subprocess,'run') as execute:
            host=restart.Host(Path(tmp),ctx,Path(tmp))
            with self.assertRaises(ValueError):host.read_private('../ordinary-save')
            execute.assert_not_called()
    def test_readonly_host_timeout_is_not_a_success(self):
        ctx,_,_,_=shape()
        with TemporaryDirectory() as tmp,patch.object(restart.subprocess,'run',side_effect=subprocess.TimeoutExpired('adb',20)):
            host=restart.Host(Path(tmp),ctx,Path(tmp))
            with self.assertRaises(subprocess.TimeoutExpired):host.command('shell','pidof',restart.BUNDLE)
    def test_original_request_refusals_and_android_only_restart(self):
        for device in [runner.PROTECTED_DEVICE,'R58-physical','01234567-1234-1234-1234-123456789abc']:
            with self.assertRaises(ValueError):runner.validate_request(device,'android','revoked-prepare','fresh')
        self.assertEqual(runner.validate_request('emulator-5556','android','revoked-prepare','fresh'),'android')


class RecoveryResultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.prior,self.c,self.ctx,self.pins,self.op=world(self.base)
        act={k:self.ctx[k] for k in restart.IDENTITY};act.update(process_id=43,action='deny_permission_again_if_prompted',utc_ms=NOW+50000)
        saved=self.c['preparation']['plan_observation'];plan=self.c['preparation']['plan'];files=self.c['files_sha256']
        self.value={**{k:self.ctx[k] for k in restart.IDENTITY},'process_id':43,'previous_process_id':42,'completed':True,
            'gateway':'NativeNotificationGateway','preference_store':'FileNotificationPreferences','fixture_kind':'SYNTHETIC GAMEPLAY SNAPSHOT; REAL OS NOTIFICATION API','clock':'actual_utc_and_monotonic_stopwatch','lifecycle_events':[],
            'predecessor_verification_id':self.prior['verification_id'],'predecessor_checkpoint_sha256':self.prior['restart_preparation']['checkpoint_sha256'],
            'predecessor_default_opted_out':True,'permission_before_initialize':'denied','permission_after_initialize':'denied','permission_after_reoptin':'denied',
            'remembered_opt_in_after_initialize':True,'pending_before_initialize':[77101],'active_before_initialize':[],
            'pending_after_initialize':[],'active_after_initialize':[],'denied_schedule_pending_ids':[],'denied_schedule_active_ids':[],'return_pending_ids':[],'return_active_ids':[],
            'recovery_files_before':files,'recovery_files_before_reoptin':files,'recovery_save_files_after':{k:v for k,v in files.items() if k.startswith('save/')},
            'restored_snapshot_id':saved['saved_snapshot_id'],'restored_payload_sha256':plan['saved_payload_sha256'],'restored_settled_through_utc_micros':saved['saved_settled_through_utc_micros'],
            'preferences_after_reoptin':{'enabled':False},'preferences_sha256':'d'*64,'initialization_lifecycle_events':[],'actions':[act]}
    def check(self,value):
        log=''.join('I/flutter ( 43): TIDEGLASS_REMINDER_ACTION '+json.dumps(a)+'\n' for a in value['actions'])+GOOD_LOG
        return restart.recovery_errors(value,self.ctx,self.prior,self.c,log,runner.MARKER,runner.verify_native.native_log_errors)
    def test_gateway_clock_and_native_observations_cannot_be_substituted(self):
        for key,val in [('gateway','MockGateway'),('clock','fake_clock'),('lifecycle_events',None)]:
            bad=copy.deepcopy(self.value);bad[key]=val
            with self.subTest(key=key):self.assertTrue(self.check(bad))
    def test_complete_restart_positive(self):self.assertEqual(self.check(self.value),[])
    def test_same_pid_wrong_predecessor_or_absent_real_denial_fail(self):
        for key,val in [('process_id',42),('previous_process_id',99),('predecessor_verification_id','other'),('permission_before_initialize','allowed'),('permission_after_reoptin','allowed'),('completed',False)]:
            bad=copy.deepcopy(self.value);bad[key]=val
            with self.subTest(key=key):self.assertTrue(self.check(bad))
    def test_pending_after_boot_and_changed_save_fail(self):
        for key,val in [('pending_after_initialize',[77101]),('active_after_initialize',[77101]),('denied_schedule_pending_ids',[77101]),('recovery_files_before',{}),('recovery_save_files_after',{}),('restored_snapshot_id','other'),('remembered_opt_in_after_initialize',False),('preferences_after_reoptin',{'enabled':True})]:
            bad=copy.deepcopy(self.value);bad[key]=val
            with self.subTest(key=key):self.assertTrue(self.check(bad))
    def test_android_already_cleared_pending_is_recorded_honestly(self):
        self.value['pending_before_initialize']=[];self.assertEqual(self.check(self.value),[])
    def test_absent_before_observation_or_permission_prompt_on_boot_fail(self):
        for key,val in [('pending_before_initialize',None),('active_before_initialize',None),('initialization_lifecycle_events',[{'state':'paused','utc_ms':NOW}]),('actions',[])]:
            bad=copy.deepcopy(self.value);bad[key]=val
            with self.subTest(key=key):self.assertTrue(self.check(bad))


if __name__=='__main__':unittest.main()
