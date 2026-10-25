"""Pure synthetic protocol checks only: no sockets, native process or device calls."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import offline_support as subject

P = {'device': subject.DEVICE, 'candidate_fingerprint': subject.CANDIDATE,
     'harness_sha256': 'a'*64, 'nonce': 'b'*64, 'server_id': 'c'*32,
     'run_id': 'qa-offline-fixture', 'port': 43210}

def iso(seconds):
    return datetime.fromtimestamp(1792910000+seconds, timezone.utc).isoformat()


def fixture(scenario='natural-start', predecessor=None):
    identity = {**{k:P[k] for k in subject.IDENTITY}, 'verification_id': 'integration-offline-20261025T100000000000Z',
                'platform':'android', 'device_label':'android-offline', 'scenario':scenario,
                'process_id': 101 if scenario=='natural-start' else 202}
    rows=[]; journal=[]
    def log(row, t):
        journal.append({**row, 'sequence': len(journal)+1, 'host_utc':iso(t), 'host_monotonic_ns':int((t+1)*1e9)})
    # Real host implementation creates an accepted health request followed by a
    # separately successful client read. Fixtures model both, not bare booleans.
    for t in range(0,200):
        request={**{k:P[k] for k in subject.IDENTITY},'kind':'health','probe_id':f'health-{t}'}
        response=subject.challenge(P,request,f'health-receipt-{t}',iso(t))
        log({'type':'receipt','request':request,'response':response},t)
        log({'type':'health','ok':True,'receipt_id':response['receipt_id']},t)
    def sample(phase, reachable, t):
        request={**identity,'kind':'app','probe_id':f'{scenario}-{len(rows)}'}
        row={**request,'phase':phase,'started_utc':iso(t),'completed_utc':iso(t+0.1),'reachable':reachable}
        if reachable:
            response=subject.challenge(P,request,f'app-receipt-{scenario}-{len(rows)}',iso(t+0.05))
            row['receipt']=response
            log({'type':'receipt','request':request,'response':response},t+0.05)
        else:
            row['error_type']='SocketException'
        rows.append(row)
    if scenario=='natural-start':
        for t in (10,11,12): sample('before-online',True,t)
        sample('await-disabled',False,15)
    sample('offline-ready',False,20)
    sample('bootstrap',False,22)
    if scenario=='natural-start':
        for t in range(24,60,2): sample('elapsed-earnings',False,t)
        sample('before-purchase',False,61);sample('after-save',False,62)
    else: sample('before-reload-check',False,30)
    sample('after-gameplay',False,64)
    if scenario=='natural-reload':
        for t in (70,71,72): sample('after-restored',True,t)
    offline={**identity,'samples':rows,'checkpoint_sha256':'d'*64,
             'predecessor_checkpoint_sha256':'d'*64 if predecessor else None}
    payload={**identity,'offline_network':offline,'before_core':{'counts':[1 if scenario=='natural-start' else 2,0,0,0,0]},'after_core':{'counts':[2,0,0,0,0]}}
    phases=['before-online','offline-ready','offline-complete'] if scenario=='natural-start' else ['offline-ready','offline-complete','after-restored']
    snapshots={'marker_errors':[],'snapshots':[]}
    for phase in phases:
        active=not phase.startswith('offline-')
        outputs={'airplane':'0' if active else '1','wifi':'1' if active else '0','data':'1', 'sdk':'35','routes':'', 'connectivity':'Active default network: '+('101' if active else 'none')}
        snapshots['snapshots'].append({'marker':{**identity,'phase':phase},'device':subject.DEVICE,
           'commands':{k:{'exit_code':0,'stdout':v,'stderr':''} for k,v in outputs.items()}})
    return payload,deepcopy(P),journal,snapshots


class ProtocolTests(unittest.TestCase):
    def test_full_synthetic_start_and_new_process_reload(self):
        start=fixture();self.assertTrue(subject.qualify(*start)['qualified_local_network_path'])
        reload=fixture('natural-reload',start[0]);self.assertTrue(subject.qualify(*reload,predecessor=start[0])['qualified_local_network_path'])

    def test_profile_rejects_other_target_candidate_port_or_traversal(self):
        for field,value in [('device','emulator-5554'),('candidate_fingerprint','f'*64),('run_id','../../save'),('run_id','x'*101),('port',True),('port',80),('nonce','bad'),('harness_sha256','bad')]:
            with self.subTest(field=field,value=value):
                item=deepcopy(P);item[field]=value
                with self.assertRaises(ValueError):subject.validate_profile(item)

    def test_challenge_accepts_only_bound_requests(self):
        request={**{k:P[k] for k in subject.IDENTITY},'kind':'health','probe_id':'health-1'}
        self.assertTrue(subject.challenge(P,request,'id',iso(1))['ok'])
        for key in subject.IDENTITY:
            changed={**request,key:'wrong'}
            with self.subTest(key=key),self.assertRaises(ValueError):subject.challenge(P,changed,'id',iso(1))

    def test_wrong_app_platform_or_native_pid_rejected(self):
        req=fixture()[0]['offline_network']['samples'][0]
        for key,value in [('platform','ios'),('scenario','seeded'),('verification_id','../bad'),('process_id',0),('probe_id','../bad'),('kind','other')]:
            with self.subTest(key=key),self.assertRaises(ValueError):subject.challenge(P,{**req,key:value},'id',iso(1))

    def reject(self, mutate, reload=False):
        prior=fixture()[0] if reload else None
        args=list(fixture('natural-reload' if reload else 'natural-start',prior))
        mutate(args,prior)
        with self.assertRaises((ValueError,KeyError)):subject.qualify(*args,predecessor=prior)

    def test_visible_airplane_with_network_still_present_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'][1]['commands']['connectivity'].update(stdout='Active default network: 101'))

    def test_wifi_remains_enabled_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'][1]['commands']['wifi'].update(stdout='1'))

    def test_unknown_os_output_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'][1]['commands']['connectivity'].update(stdout='unknown'))

    def test_runtime_api36_claim_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'][1]['commands']['sdk'].update(stdout='36'))

    def test_failed_snapshot_command_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'][1]['commands']['airplane'].update(exit_code=1))

    def test_actual_socket_still_reachable_rejected(self):
        self.reject(lambda a,p:next(x for x in a[0]['offline_network']['samples'] if x['phase']=='bootstrap').update(reachable=True))

    def test_host_listener_health_absence_rejected(self):
        self.reject(lambda a,p:a[2].clear())

    def test_unbound_host_health_boolean_rejected(self):
        self.reject(lambda a,p:next(x for x in a[2] if x['type']=='health').update(receipt_id='missing'))

    def test_missing_success_receipt_rejected(self):
        self.reject(lambda a,p:a[0]['offline_network']['samples'][0]['receipt'].update(receipt_id='missing'))

    def test_invalid_protocol_error_is_not_outage(self):
        self.reject(lambda a,p:next(x for x in a[0]['offline_network']['samples'] if x['phase']=='bootstrap').update(error_type='AssertionError'))

    def test_missing_bootstrap_sample_rejected(self):
        self.reject(lambda a,p:next(x for x in a[0]['offline_network']['samples'] if x['phase']=='bootstrap').update(phase='unrelated'))

    def test_short_elapsed_window_rejected(self):
        self.reject(lambda a,p:[x.update(phase='unrelated') for x in a[0]['offline_network']['samples'] if x['phase']=='elapsed-earnings' and subject.timestamp(x['started_utc'])>subject.timestamp(iso(30))])

    def test_out_of_order_marker_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'].reverse())

    def test_wrong_marker_run_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'][1]['marker'].update(run_id='other'))

    def test_wrong_sample_harness_rejected(self):
        self.reject(lambda a,p:a[0]['offline_network']['samples'][0].update(harness_sha256='f'*64))

    def test_wrong_purchase_count_rejected(self):
        self.reject(lambda a,p:a[0]['after_core'].update(counts=[1,0,0,0,0]))

    def test_same_process_reload_rejected(self):
        self.reject(lambda a,p:p.update(process_id=a[0]['process_id']),True)

    def test_wrong_predecessor_checkpoint_rejected(self):
        self.reject(lambda a,p:a[0]['offline_network'].update(predecessor_checkpoint_sha256='e'*64),True)

    def test_restore_missing_rejected(self):
        self.reject(lambda a,p:a[3]['snapshots'].pop(),True)

    def test_restore_endpoint_unreachable_rejected(self):
        self.reject(lambda a,p:[x.update(reachable=False,error_type='SocketException') for x in a[0]['offline_network']['samples'] if x['phase']=='after-restored'],True)

    def test_reload_cannot_change_fleet(self):
        self.reject(lambda a,p:a[0]['before_core'].update(counts=[3,0,0,0,0]),True)

    def test_listener_failure_overlapping_outage_rejected(self):
        def mutate(a,p):
            row=next(x for x in a[2] if x['type']=='health' and x['host_utc']==iso(22));row['ok']=False
        self.reject(mutate)

    def test_no_live_sources_edited_and_original_flow_assertions_retained(self):
        stage=Path(__file__).parent;root=stage.parents[2]
        for path,pin in json.loads((stage/'source-before.json').read_text()).items():
            self.assertEqual(subject.digest(root/path),pin,path)
        old=(stage/'before/game/mobile/integration_test/platform_smoke_test.dart').read_text()
        new=(stage/'platform_smoke_offline_test.dart').read_text()
        start=old.index('void naturalScenario(');end=old.index('/// Deliberately seeded content/state:',start)
        newstart=new.index('void naturalScenario(');newend=new.index('/// Deliberately seeded content/state:',newstart)
        self.assertEqual(old[:start],new[:newstart]);self.assertTrue(new[newend:].startswith(old[end:]))
        for assertion in ["expect(game.state.counts, [1, 0, 0, 0, 0]);","expect(game.state.counts, [2, 0, 0, 0, 0]);","greaterThanOrEqualTo(BigInt.from(33600000))","reason: 'This must be a new native process'","expect(game.state.walletMicros, greaterThanOrEqualTo(saved.walletMicros));","expect(game.saveError, isNull);"]:
            self.assertIn(assertion,new[newstart:newend])
        runner=(stage/'verify_offline_native.py').read_text()
        for gate in ['build_native.source_hashes(candidate / \'source\')','fcntl.LOCK_EX | fcntl.LOCK_NB','errors.extend(native_log_errors(log_text))','production_input_differences_after_run','source_snapshot_unchanged','harness_source_differences_during_run']:
            self.assertIn(gate,runner)

if __name__=='__main__':unittest.main(verbosity=2)
