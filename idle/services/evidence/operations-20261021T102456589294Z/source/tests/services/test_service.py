"""Real HTTP/SQLite fault tests. Synthetic provider observations stay in tests."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import http.client
from pathlib import Path
import sqlite3
import secrets
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid
from wsgiref.simple_server import make_server

from services.tideglass_service.api import Application, canonical, digest
from services.tideglass_service.storage import Database
from services.tideglass_service.__main__ import ThreadedServer, QuietHandler
from services.tideglass_service.verification import PurchaseObservation, AdObservation, VerificationUnavailable
from services.tideglass_service.ops import dashboard, set_feature

NOW = 1792108800  # fixed UTC account-day fixture, not a real observation

def uid():return str(uuid.uuid4())


def snapshot(parent=None, *, balance='1000000', branch=None, seed='fixture.account'):
    envelope = {
        'format':'tideglass-save-envelope','schema_version':1,'save_id':uid(),
        'branch_id':branch or (parent['branch_id'] if parent else uid()),
        'revision':parent['revision']+1 if parent else 0,
        'parent':{key:parent[key] for key in ('save_id','branch_id','revision')} if parent else None,
        'written_at_utc':'2026-10-16T00:00:00.000000Z','settled_through_utc':'2026-10-16T00:00:00.000000Z',
        'economic_config':{'version':'tideglass-economy-1.0.0','sha256':'a'*64},
        'gameplay_state':{'schema_version':1,'payload':{'core':{'wallet_micros':balance,'daily':{'account_seed':seed,'utc_offset_minutes':0},'support':{'grant_source_ids':[]}}}},
        'merge_policy':'select_one_progression_branch','preserved_branches':[],
        'pending_operations':[],'applied_operation_ids':[],
        'commerce_cache':{'trust':'display_cache_only','authority':'independent_verifier_required','snapshot_reference':None,'entries':[]}}
    if parent and envelope['branch_id']!=parent['branch_id']:
        envelope['preserved_branches']=[{**envelope['parent'],'recovery_reference':'local:preserved'}]
    return envelope


def export(envelope):
    return canonical({'format':'tideglass-checksummed-save','checksum':digest(canonical(envelope)),'envelope':envelope})


class SyntheticPurchaseVerifier:
    """Fault fixture only. Never loaded by the runner or application default."""
    def __init__(self):self.observations={};self.acks=[];self.fail_ack=False
    def verify(self,platform,proof,account_id):
        if proof not in self.observations:raise VerificationUnavailable()
        return self.observations[proof]
    def acknowledge(self,observation):
        if self.fail_ack:raise VerificationUnavailable()
        self.acks.append(observation.transaction_id)


class SyntheticAdVerifier:
    def verify(self,proof,account_id,day_id,slot):
        if proof=='no-fill':raise VerificationUnavailable()
        return AdObservation(proof,account_id,day_id,slot,'synthetic_test_only')


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'service.sqlite3'
        self.now=NOW
        self.app=Application(self.path,clock=lambda:self.now)
        self.server=make_server('127.0.0.1',0,self.app,server_class=ThreadedServer,handler_class=QuietHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.account=self.call('POST','/v1/accounts',{'consent_cloud':True},auth=False)[1]
        self.token=self.account['session_token']
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def call(self,method,path,body=None,*,token=None,auth=True,raw=None):
        headers={}
        if auth:headers['Authorization']='Bearer '+(token or self.token)
        data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        if data is not None:headers['Content-Type']='application/json'
        try:
            with urlopen(Request(self.base+path,data=data,headers=headers,method=method),timeout=10) as response:
                return response.status,json.load(response)
        except HTTPError as error:return error.code,json.load(error)
    def upload(self,value,generation=0):return self.call('POST','/v1/cloud/snapshots',{'export_json':export(value),'expected_generation':generation})
    def link(self):
        value=snapshot();self.assertEqual(self.upload(value)[0],200);return value
    def test_opt_in_required_and_no_unauthenticated_cloud(self):
        self.assertEqual(self.call('POST','/v1/accounts',{'consent_cloud':False},auth=False)[0],400)
        self.assertEqual(self.call('GET','/v1/cloud',auth=False)[0],401)
        self.assertEqual(self.call('GET','/health',auth=False)[1]['store_verification_configured'],False)
    def test_recovery_rotation_revokes_all_old_sessions(self):
        old_code=self.account['recovery_code']
        recovered=self.call('POST','/v1/sessions',{'account_id':self.account['account_id'],'recovery_code':old_code},auth=False)[1]
        status,rotated=self.call('POST','/v1/account/recovery-code',{'recovery_code':old_code,'new_recovery_code':secrets.token_urlsafe(32)})
        self.assertEqual(status,200)
        self.assertEqual(self.call('GET','/v1/cloud')[0],401)
        self.assertEqual(self.call('GET','/v1/cloud',token=recovered['session_token'])[0],401)
        self.assertEqual(self.call('POST','/v1/sessions',{'account_id':self.account['account_id'],'recovery_code':old_code},auth=False)[0],401)
        self.token=rotated['session_token'];self.assertEqual(self.call('GET','/v1/cloud')[0],200)
    def test_snapshot_replay_conflict_and_explicit_selection_no_merge(self):
        root=self.link();one=snapshot(root,balance='25');two=snapshot(root,balance='700')
        self.assertFalse(self.upload(one,1)[1]['selection_required'])
        result=self.upload(two,1)[1]
        self.assertTrue(result['selection_required']);self.assertEqual(result['selected_save_id'],one['save_id'])
        self.assertEqual(len(result['snapshots']),3)
        selected=self.call('POST','/v1/cloud/select',{'save_id':two['save_id'],'expected_generation':2,'confirm_selection':True})
        self.assertEqual(selected[0],200)
        self.assertEqual(self.upload(two,0)[1]['generation'],3)
        for value in (root,one,two):
            stored=self.call('GET','/v1/cloud/snapshots/'+value['save_id'])[1]['export_json']
            self.assertEqual(stored,export(value))
        one['gameplay_state']['payload']['core']['wallet_micros']='725'
        self.assertEqual(self.upload(one,3)[0],409)
    def test_two_real_concurrent_devices_preserve_both_and_cas_selection(self):
        root=self.link();children=[snapshot(root,balance=str(i)) for i in (2,3)]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda child:self.upload(child,1),children))
        self.assertTrue(all(status==200 for status,_ in results))
        self.assertEqual(sum(not result['selection_required'] for _,result in results),1)
        state=self.call('GET','/v1/cloud')[1];self.assertEqual(len(state['snapshots']),3)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda child:self.call('POST','/v1/cloud/select',{'save_id':child['save_id'],'expected_generation':state['generation'],'confirm_selection':True}),children))
        self.assertEqual(sorted(status for status,_ in results),[200,409])
    def test_unknown_parent_preserved_requires_selection_and_no_cross_account_reads(self):
        root=self.link();middle=snapshot(root);last=snapshot(middle)
        self.assertTrue(self.upload(last,1)[1]['selection_required'])
        another=self.call('POST','/v1/accounts',{'consent_cloud':True},auth=False)[1]
        self.assertEqual(self.call('GET','/v1/cloud/snapshots/'+root['save_id'],token=another['session_token'])[0],404)
    def test_checksum_parent_cursor_and_secrets_rejected(self):
        root=self.link();child=snapshot(root);child['settled_through_utc']='2026-10-15T23:59:59Z'
        self.assertEqual(self.upload(child,1)[0],409)
        child=snapshot(root);child['gameplay_state']['payload']['session_token']='secret'
        self.assertEqual(self.upload(child,1)[0],400)
        raw=json.loads(export(root));raw['checksum']='f'*64
        self.assertEqual(self.call('POST','/v1/cloud/snapshots',{'export_json':json.dumps(raw),'expected_generation':1})[0],400)
    def test_restart_persistence_and_consistent_backup(self):
        root=self.link();backup=Path(self.temp.name)/'backup.sqlite3';self.app.db.backup(backup)
        reopened=Application(backup,clock=lambda:self.now)
        status,result=reopened.dispatch('GET','/v1/cloud',{},self.token)
        self.assertEqual(status,200);self.assertEqual(result['selected_save_id'],root['save_id'])
        self.assertEqual(reopened.dispatch('GET','/v1/cloud/snapshots/'+root['save_id'],{},self.token)[1]['export_json'],export(root))
    def test_before_and_after_commit_fault_no_partial_or_duplicate(self):
        root=self.link();child=snapshot(root)
        def fail_before(stage):
            if stage=='before_commit':raise RuntimeError('injected process interruption')
        self.app.db.fault=fail_before
        with self.assertRaises(RuntimeError):self.app.dispatch('POST','/v1/cloud/snapshots',{'export_json':export(child),'expected_generation':1},self.token)
        self.app.db.fault=None
        self.assertEqual(len(self.call('GET','/v1/cloud')[1]['snapshots']),1)
        def fail_after(stage):
            if stage=='after_commit':raise RuntimeError('lost response after commit')
        self.app.db.fault=fail_after
        with self.assertRaises(RuntimeError):self.app.dispatch('POST','/v1/cloud/snapshots',{'export_json':export(child),'expected_generation':1},self.token)
        self.app.db.fault=None
        replay=self.upload(child,1)[1];self.assertTrue(replay['duplicate']);self.assertEqual(replay['generation'],2)
    def test_unconfigured_store_and_ad_cannot_grant(self):
        self.link()
        self.assertEqual(self.call('POST','/v1/purchases/verify',{'platform':'apple','proof':'client says purchased'})[0],503)
        self.assertEqual(self.call('GET','/v1/entitlements')[1]['entitlements'],[])
        self.assertEqual(self.call('POST','/v1/support/claims',{'day_id':self.now//86400,'slot':0,'route':'ad','proof':'ad completed'})[0],503)
        self.assertEqual(self.call('POST','/v1/support/claims',{'day_id':self.now//86400,'slot':0,'route':'briefing'})[0],200)
    def test_purchase_grant_restore_ack_failure_refund_and_stale_observation(self):
        verifier=SyntheticPurchaseVerifier();self.app.purchase_verifier=verifier
        obs=PurchaseObservation('google','transaction.01',self.account['account_id'],'dev.tideglass.pass.01','pending',1,'synthetic_test_only')
        verifier.observations['proof']=obs
        request={'platform':'google','proof':'proof'}
        self.assertEqual(self.call('POST','/v1/purchases/verify',request)[1]['entitlements'],[])
        verifier.observations['proof']=replace(obs,state='purchased',version=2)
        result=self.call('POST','/v1/purchases/verify',request)[1]
        self.assertEqual([e['id'] for e in result['entitlements']],['pass.01'])
        receipt=result['entitlements'][0]['verification_receipt_id']
        self.assertEqual(self.call('POST','/v1/purchases/verify',request)[1]['entitlements'][0]['verification_receipt_id'],receipt)
        verifier.fail_ack=True
        with self.assertRaises(VerificationUnavailable):self.app.reconcile_acknowledgements()
        self.assertEqual(len(self.call('GET','/v1/entitlements')[1]['entitlements']),1)
        verifier.fail_ack=False;self.assertEqual(self.app.reconcile_acknowledgements(),1)
        self.assertEqual(self.app.reconcile_acknowledgements(),0)
        verifier.observations['proof']=replace(obs,state='revoked',version=3)
        self.assertEqual(self.call('POST','/v1/purchases/verify',request)[1]['entitlements'],[])
        verifier.observations['proof']=replace(obs,state='purchased',version=2)
        self.assertEqual(self.call('POST','/v1/purchases/verify',request)[0],409)
    def test_stale_provider_verification_cannot_authorize_forever(self):
        verifier=SyntheticPurchaseVerifier();self.app.purchase_verifier=verifier
        verifier.observations['proof']=PurchaseObservation('apple','transaction.expiry',self.account['account_id'],'dev.tideglass.pass.01','purchased',1,'synthetic_test_only')
        request={'platform':'apple','proof':'proof'}
        self.assertEqual(len(self.call('POST','/v1/purchases/verify',request)[1]['entitlements']),1)
        self.now+=86401
        self.assertEqual(self.call('GET','/v1/entitlements')[1]['entitlements'],[])
        self.assertEqual(len(self.call('POST','/v1/purchases/verify',request)[1]['entitlements']),1)

    def test_local_commerce_cache_never_grants_ownership(self):
        value=snapshot();value['commerce_cache']['entries']=[{'entitlement_id':'pass.01','receipt_reference':'invented','display_status':'active'}]
        self.assertEqual(self.upload(value)[0],200)
        self.assertEqual(self.call('GET','/v1/entitlements')[1]['entitlements'],[])
    def test_briefing_and_ad_share_six_slots_and_retry_identity(self):
        self.link();self.app.ad_verifier=SyntheticAdVerifier();day=self.now//86400
        for slot in range(6):
            body={'day_id':day,'slot':slot,'route':'ad' if slot%2 else 'briefing'}
            if slot%2:body['proof']=f'ad.{slot}'
            first=self.call('POST','/v1/support/claims',body)
            self.assertEqual(first[0],200)
            replay=self.call('POST','/v1/support/claims',{'day_id':day,'slot':slot,'route':'briefing'})
            self.assertEqual(replay[1]['claim']['receipt_id'],first[1]['claim']['receipt_id'])
        self.assertEqual(len(self.call('GET','/v1/support/claims')[1]['claims']),6)
        self.assertEqual(self.call('POST','/v1/support/claims',{'day_id':day,'slot':6,'route':'briefing'})[0],400)
        self.now+=86400
        self.assertEqual(self.call('POST','/v1/support/claims',{'day_id':day,'slot':0,'route':'briefing'})[0],409)
    def test_no_fill_and_feature_disable_preserve_free_route(self):
        self.link();self.app.ad_verifier=SyntheticAdVerifier();day=self.now//86400
        self.assertEqual(self.call('POST','/v1/support/claims',{'day_id':day,'slot':0,'route':'ad','proof':'no-fill'})[0],503)
        set_feature(self.app.db,'ads',False)
        self.assertEqual(self.call('POST','/v1/support/claims',{'day_id':day,'slot':0,'route':'briefing'})[0],200)
        set_feature(self.app.db,'cloud',False)
        self.assertEqual(self.call('GET','/v1/cloud')[0],503)
        self.assertEqual(self.call('GET','/v1/account/export')[0],200)
    def event(self,name='session_start',session=None):
        return {'id':uid(),'session_id':session or uid(),'name':name,'observed_at':self.now,'properties':{'platform':'test','build':'fixture.1','device_class':'host'}}
    def test_consent_refusal_dedup_revocation_and_no_freeform_telemetry(self):
        event=self.event();body={'consent_revision':0,'events':[event]}
        self.assertEqual(self.call('POST','/v1/telemetry/events',body)[0],403)
        revision=self.call('PUT','/v1/telemetry/consent',{'enabled':True})[1]['revision'];body['consent_revision']=revision
        self.assertEqual(self.call('POST','/v1/telemetry/events',body)[1]['accepted'],1)
        self.assertEqual(self.call('POST','/v1/telemetry/events',body)[1]['duplicate'],1)
        event['properties']['email']='not allowed'
        self.assertEqual(self.call('POST','/v1/telemetry/events',body)[0],400)
        self.call('PUT','/v1/telemetry/consent',{'enabled':False})
        self.assertEqual(self.call('GET','/v1/account/export')[1]['telemetry'],[])
    def test_dashboard_does_not_call_unknown_session_crash_free(self):
        revision=self.call('PUT','/v1/telemetry/consent',{'enabled':True})[1]['revision']
        first,second,third=self.event(),self.event(),self.event()
        events=[first,second,third,self.event('session_end',first['session_id']),self.event('session_crash',second['session_id'])]
        self.call('POST','/v1/telemetry/events',{'consent_revision':revision,'events':events})
        result=dashboard(self.app.db)
        self.assertEqual(result['observed_sessions'],3);self.assertEqual(result['unknown_outcome_sessions'],1)
        self.assertEqual(result['crash_free_lower_bound'],1/3);self.assertFalse(result['release_quality_gate_verified'])
    def test_delete_requires_recovery_erases_rows_revokes_tokens_guest_copy_retained(self):
        root=self.link();local_copy=export(root)
        self.assertEqual(self.call('DELETE','/v1/account',{'recovery_code':'incorrect','confirm_delete':True})[0],403)
        self.assertEqual(self.call('DELETE','/v1/account',{'recovery_code':self.account['recovery_code'],'confirm_delete':True})[0],200)
        self.assertEqual(self.call('GET','/v1/cloud')[0],401)
        self.assertEqual(local_copy,export(root))
        with self.app.db.read() as db:
            for table in ('accounts','sessions','snapshots','purchases','support_claims','telemetry'):
                self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0)
    def test_grant_delivery_ack_requires_saved_token_and_retry_is_safe(self):
        root=self.link();day=self.now//86400
        claim=self.call('POST','/v1/support/claims',{'day_id':day,'slot':0,'route':'briefing'})[1]['claim']
        body={'receipt_id':claim['receipt_id'],'save_id':root['save_id']}
        self.assertEqual(self.call('POST','/v1/support/acknowledge',body)[0],409)
        child=snapshot(root)
        child['gameplay_state']['payload']['core']['support']['tokens']=[{'source_id':claim['source_id'],'account_day':day,'slot':0,'spent':False}]
        self.assertEqual(self.upload(child,1)[0],200)
        body['save_id']=child['save_id']
        self.assertEqual(self.call('POST','/v1/support/acknowledge',body)[0],200)
        self.assertEqual(self.call('POST','/v1/support/acknowledge',body)[0],200)
        self.assertEqual(len(self.call('GET','/v1/support/claims')[1]['claims']),1)
    def test_recovery_rotation_lost_response_keeps_known_new_code_usable(self):
        new_code=secrets.token_urlsafe(32)
        def lost_response(stage):
            if stage=='after_commit':raise RuntimeError('lost response')
        self.app.db.fault=lost_response
        with self.assertRaises(RuntimeError):
            self.app.dispatch('POST','/v1/account/recovery-code',{'recovery_code':self.account['recovery_code'],'new_recovery_code':new_code},self.token)
        self.app.db.fault=None
        self.assertEqual(self.call('GET','/v1/cloud')[0],401)
        self.assertEqual(self.call('POST','/v1/sessions',{'account_id':self.account['account_id'],'recovery_code':new_code},auth=False)[0],200)
    def test_future_database_is_rejected_without_applying_schema(self):
        future=Path(self.temp.name)/'future.sqlite3'
        with sqlite3.connect(future) as db:
            db.execute('CREATE TABLE schema_version(version INTEGER)');db.execute('INSERT INTO schema_version VALUES(999)')
        with self.assertRaises(RuntimeError):Database(future)
        with sqlite3.connect(future) as db:
            self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[('schema_version',)])
    def test_export_excludes_credentials_and_purchase_proofs(self):
        self.link()
        exported=json.dumps(self.call('GET','/v1/account/export')[1])
        self.assertNotIn(self.token,exported);self.assertNotIn(self.account['recovery_code'],exported)
        with self.app.db.read() as db:
            self.assertNotIn(self.token,str(db.execute('SELECT * FROM sessions').fetchall()))
            self.assertNotIn(self.account['recovery_code'],str(db.execute('SELECT * FROM accounts').fetchall()))

    def test_duplicate_json_keys_and_oversized_request_rejected(self):
        self.assertEqual(self.call('POST','/v1/accounts',raw=b'{"consent_cloud":true,"consent_cloud":false}',auth=False)[0],400)
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        connection.putrequest('POST','/v1/accounts')
        connection.putheader('Content-Type','application/json')
        connection.putheader('Content-Length',str(2*1024*1024+65537))
        connection.endheaders()
        self.assertEqual(connection.getresponse().status,413)
        connection.close()

if __name__=='__main__':unittest.main()
