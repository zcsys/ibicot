"""Local HTTP, crypto and failure tests; no live store success is simulated as evidence."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock,patch
from types import SimpleNamespace
import time
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from wsgiref.simple_server import make_server
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from google.auth import jwt, crypt
from google.auth.credentials import AnonymousCredentials
from services.tideglass_service.storage import Database
from services.tideglass_service.api import Application,ApiError
from services.tideglass_service.__main__ import ThreadedServer,QuietHandler
from services.tideglass_service.vault import VaultKeys,TokenVault
from services.tideglass_service.soundtrack import SoundtrackAsset,CHUNK
from services.tideglass_service.leases import OwnershipSigner
from services.tideglass_service.reconcile import reconcile
from services.tideglass_service.factory import create_runtime
from services.tideglass_service.providers.stores import GooglePurchaseVerifier
from services.tideglass_service.providers.notifications import StoreNotificationApplication,GooglePushIdentity
from services.tideglass_service.verification import VerificationUnavailable

NOW=1792368000
PRODUCT='dev.tideglass.supporter'
TOKEN='purchase-token-kept-only-in-encrypted-vault'
TX=hashlib.sha256(TOKEN.encode()).hexdigest()

def secret(path,value):
    path.write_text(json.dumps(value));path.chmod(0o600);return path
class Response:
    status_code=200
    def __init__(self,data):self.data=data
    def json(self):return self.data
class FulfillmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.now=NOW
        self.db=Database(self.root/'service.sqlite3')
        self.keys=secret(self.root/'keys.json',{'version':1,'active_key_id':'old','keys':{'old':base64.b64encode(os.urandom(32)).decode()}})
        self.vault=TokenVault(self.db,VaultKeys(self.keys))
        self.app=Application(self.db,clock=lambda:self.now,token_vault=self.vault)
        _,self.account=self.app.dispatch('POST','/v1/accounts',{'consent_cloud':True})
        self.aid=self.account['account_id'];self.token=self.account['session_token']
        with self.db.transaction() as db:db.execute('UPDATE accounts SET seed=?,utc_offset=0 WHERE id=?',('harbor.seed',self.aid))
        self.server=None
    def tearDown(self):
        if self.server:self.server.shutdown();self.server.server_close();self.thread.join()
        self.temp.cleanup()
    def serve(self,app=None):
        self.server=make_server('127.0.0.1',0,app or self.app,server_class=ThreadedServer,handler_class=QuietHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.origin=f'http://127.0.0.1:{self.server.server_port}'
    def http(self,path,*,token=True,body=None,method='GET'):
        headers={'Authorization':'Bearer '+self.token} if token else {}
        data=json.dumps(body).encode() if body is not None else None
        if data:headers['Content-Type']='application/json'
        try:
            with urlopen(Request(self.origin+path,data=data,headers=headers,method=method),timeout=5) as response:return response.status,response.headers,response.read()
        except HTTPError as e:return e.code,e.headers,e.read()
    def grant(self,state='purchased',updated=None):
        with self.db.transaction() as db:
            db.execute('INSERT OR REPLACE INTO purchases VALUES(?,?,?,?,?,?,?,?,?,?)',('google',TX,self.aid,PRODUCT,state,1,'test-fixture-only','verification-test',0,updated if updated is not None else self.now))
    def google(self):
        verifier=GooglePurchaseVerifier(credentials=AnonymousCredentials(),package_name='dev.tideglass.game',allow_test_purchases=False,purchase_token_lookup=self.vault.lookup,remember_purchase_token=self.vault.remember)
        data={'productLineItem':[{'productId':PRODUCT,'productOfferDetails':{'quantity':1}}],'obfuscatedExternalAccountId':self.aid,'purchaseStateContext':{'purchaseState':'PURCHASED'},'acknowledgementState':'ACKNOWLEDGEMENT_STATE_PENDING'}
        verifier.http=Mock();verifier.http.get.return_value=Response(data);verifier.http.post.return_value=Response({})
        self.app.purchase_verifier=verifier
        return verifier,data
    def purchase(self):return self.app.dispatch('POST','/v1/purchases/verify',{'platform':'google','proof':json.dumps({'purchase_token':TOKEN,'expected_product_id':PRODUCT})},self.token)
    def signer(self):
        key=Ed25519PrivateKey.generate()
        path=secret(self.root/'signer.json',{'version':1,'key_id':'test-only','private_key':base64.b64encode(key.private_bytes_raw()).decode()})
        self.app.ownership_signer=OwnershipSigner(path,'https://service.example.invalid')
        return key
    def test_vault_binding_ciphertext_and_cascade_deletion(self):
        self.vault.remember(TX,TOKEN,self.aid)
        self.assertEqual(self.vault.lookup(TX,self.aid),TOKEN)
        self.assertIsNone(self.vault.lookup(TX,'other-account'))
        with self.assertRaises(VerificationUnavailable):self.vault.remember(TX,TOKEN,'other-account')
        with self.db.read() as db:
            row=db.execute('SELECT * FROM provider_tokens').fetchone();self.assertNotIn(TOKEN.encode(),row['ciphertext'])
        for path in self.root.glob('service.sqlite3*'):self.assertNotIn(TOKEN.encode(),path.read_bytes())
        self.app.dispatch('DELETE','/v1/account',{'recovery_code':self.account['recovery_code'],'confirm_delete':True},self.token)
        self.assertIsNone(self.vault.lookup(TX,self.aid))
    def test_ciphertext_account_and_key_tampering_fail_closed(self):
        self.vault.remember(TX,TOKEN,self.aid)
        with self.db.transaction() as db:db.execute('UPDATE provider_tokens SET ciphertext=?',(b'corrupt',))
        with self.assertRaises(VerificationUnavailable):self.vault.lookup(TX,self.aid)
    def test_key_permissions_symlinks_missing_key_and_rotation_crash(self):
        self.keys.chmod(0o644)
        with self.assertRaises(ValueError):VaultKeys(self.keys)
        self.keys.chmod(0o600);link=self.root/'linked';link.symlink_to(self.keys)
        with self.assertRaises(OSError):VaultKeys(link)
        self.vault.remember(TX,TOKEN,self.aid)
        value=json.loads(self.keys.read_text());value['active_key_id']='new';value['keys']['new']=base64.b64encode(os.urandom(32)).decode()
        new=secret(self.root/'new.json',value)
        with self.assertRaises(ValueError):TokenVault(self.db,VaultKeys(new))
        rotation=TokenVault(self.db,VaultKeys(new),rotation=True)
        def fault(stage):
            if stage=='before_commit':raise RuntimeError('simulated commit failure')
        self.db.fault=fault
        with self.assertRaises(RuntimeError):rotation.rotate()
        self.db.fault=None
        self.assertEqual(self.vault.lookup(TX,self.aid),TOKEN)
        self.assertEqual(rotation.rotate(),1)
        with self.assertRaises(VerificationUnavailable):self.vault.remember(TX,TOKEN,self.aid)
        self.assertEqual(TokenVault(self.db,VaultKeys(new)).lookup(TX,self.aid),TOKEN)
        value['keys'].pop('new');value['active_key_id']='old';secret(new,value)
        with self.assertRaises(ValueError):TokenVault(self.db,VaultKeys(new))
    def test_encrypted_backup_restores_only_with_matching_keys(self):
        self.vault.remember(TX,TOKEN,self.aid)
        backup=self.root/'backup.sqlite3';self.db.backup(backup)
        self.assertNotIn(TOKEN.encode(),backup.read_bytes())
        restored=Database(backup);self.assertEqual(TokenVault(restored,VaultKeys(self.keys)).lookup(TX,self.aid),TOKEN)
        wrong=secret(self.root/'wrong.json',{'version':1,'active_key_id':'old','keys':{'old':base64.b64encode(os.urandom(32)).decode()}})
        with self.assertRaises(ValueError):TokenVault(restored,VaultKeys(wrong))
    def test_verification_ledger_and_vault_commit_together(self):
        self.google()
        def fault(stage):
            if stage=='before_commit':raise RuntimeError('simulated failure')
        self.db.fault=fault
        with self.assertRaises(RuntimeError):self.purchase()
        self.db.fault=None
        self.assertIsNone(self.vault.lookup(TX,self.aid))
        self.assertEqual(self.purchase()[0],200)
        self.assertEqual(self.vault.lookup(TX,self.aid),TOKEN)
    def test_reconcile_pending_purchase_ack_refund_and_provider_failure(self):
        verifier,data=self.google();data['purchaseStateContext']['purchaseState']='PENDING';self.purchase()
        result=reconcile(self.app);self.assertEqual(result['refreshed'],1);self.assertEqual(result['acknowledged'],0)
        self.now+=61;data['purchaseStateContext']['purchaseState']='PURCHASED'
        result=reconcile(self.app);self.assertEqual(result['acknowledged'],1)
        self.assertEqual(reconcile(self.app)['attempted'],0)
        self.now+=21601;data['productLineItem'][0]['productOfferDetails']['refundableQuantity']=0
        self.assertEqual(reconcile(self.app)['revoked'],1)
        self.assertEqual(self.app.dispatch('GET','/v1/entitlements',{},self.token)[1]['entitlements'],[])
        self.now+=21601;verifier.http.get.side_effect=OSError('provider unavailable')
        self.assertEqual(reconcile(self.app)['failed'],1)
        self.assertEqual(reconcile(self.app)['attempted'],0)
    def test_reconciliation_ack_crash_retries_idempotently(self):
        verifier,data=self.google();self.purchase();verifier.http.post.side_effect=OSError('lost response')
        self.assertEqual(reconcile(self.app)['failed'],1)
        data['acknowledgementState']='ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED';self.now+=61
        self.assertEqual(reconcile(self.app)['acknowledged'],1)
        self.assertEqual(verifier.http.post.call_count,1)
    def test_authenticated_google_notification_refreshes_and_never_trusts_event_state(self):
        verifier,data=self.google();self.purchase()
        identity=Mock();identity.verify.side_effect=VerificationUnavailable()
        app=StoreNotificationApplication(self.app,google=verifier,google_identity=identity)
        self.serve(app)
        event={'packageName':'dev.tideglass.game','oneTimeProductNotification':{'purchaseToken':TOKEN,'notificationType':2}}
        body={'message':{'data':base64.b64encode(json.dumps(event).encode()).decode()}}
        self.assertEqual(self.http('/providers/google/notifications',body=body,method='POST')[0],503)
        identity.verify.side_effect=None
        # A declared cancellation cannot revoke while the actual API says purchased.
        self.assertEqual(self.http('/providers/google/notifications',body=body,method='POST')[0],200)
        self.assertTrue(self.app.dispatch('GET','/v1/entitlements',{},self.token)[1]['entitlements'])
        data['purchaseStateContext']['purchaseState']='CANCELLED'
        self.assertEqual(self.http('/providers/google/notifications',body=body,method='POST')[0],200)
        self.assertEqual(self.app.dispatch('GET','/v1/entitlements',{},self.token)[1]['entitlements'],[])
    def test_real_google_oidc_signature_identity_audience_and_tamper(self):
        # Actual google-auth RSA verification, using a locally generated test
        # certificate response. No provider endpoint or credential is used.
        private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        signer=crypt.RSASigner(private,'test-key')
        public=private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        response=SimpleNamespace(status=200,data=json.dumps({'test-key':public}).encode())
        audience='https://service.example.invalid/providers/google/notifications'
        email='push@test.iam.gserviceaccount.com'
        identity=GooglePushIdentity(audience,email)
        payload={'iss':'https://accounts.google.com','aud':audience,'email':email,'email_verified':True,'iat':int(time.time()),'exp':int(time.time())+300,'sub':'fixture-subject'}
        with patch('google.auth.transport.requests.Request.__call__',return_value=response):
            valid=jwt.encode(signer,payload).decode();identity.verify('Bearer '+valid)
            for changes in [{'aud':'https://wrong.invalid'},{'email':'wrong@test.iam.gserviceaccount.com'},{'email_verified':False}]:
                with self.assertRaises(VerificationUnavailable):identity.verify('Bearer '+jwt.encode(signer,{**payload,**changes}).decode())
            parts=valid.split('.');parts[2]='A'*len(parts[2])
            with self.assertRaises(VerificationUnavailable):identity.verify('Bearer '+'.'.join(parts))

    def test_actual_soundtrack_archive_authenticated_stream_has_expected_hash(self):
        asset=Path(__file__).resolve().parents[3]/'release/downloads/tideglass-original-soundtrack.zip'
        with asset.open('rb') as source:expected=hashlib.file_digest(source,'sha256').hexdigest()
        self.app.soundtrack=SoundtrackAsset(asset,expected);self.grant();self.serve()
        status,headers,body=self.http('/v1/soundtrack/download')
        self.assertEqual(status,200);self.assertEqual(len(body),52699186)
        self.assertEqual(hashlib.sha256(body).hexdigest(),expected)

    def test_soundtrack_http_authorization_hash_chunks_refund_and_missing_asset(self):
        asset=self.root/'album.zip';asset.write_bytes(b'PK'+os.urandom(CHUNK*3))
        self.app.soundtrack=SoundtrackAsset(asset,hashlib.sha256(asset.read_bytes()).hexdigest());self.serve()
        self.assertEqual(self.http('/v1/soundtrack/manifest',token=False)[0],401)
        self.assertEqual(self.http('/v1/soundtrack/download')[0],403)
        self.grant();status,headers,raw=self.http('/v1/soundtrack/manifest');manifest=json.loads(raw)
        self.assertEqual(status,200);self.assertNotIn(self.token,raw.decode());self.assertEqual(manifest['download_path'],'/v1/soundtrack/download')
        status,headers,raw=self.http(manifest['download_path']);self.assertEqual(status,200);self.assertEqual(hashlib.sha256(raw).hexdigest(),manifest['sha256'])
        self.assertEqual(headers['Cache-Control'],'private, no-store')
        download=self.app.soundtrack.download();self.assertTrue(all(len(chunk)<=CHUNK for chunk in download))
        self.grant('revoked');self.assertEqual(self.http('/v1/soundtrack/download')[0],403)
        self.grant();asset.unlink();self.assertEqual(self.http('/v1/soundtrack/download')[0],503)
    def test_soundtrack_expiry_and_changed_file_rejected(self):
        asset=self.root/'album.zip';asset.write_bytes(b'PKfixture')
        self.app.soundtrack=SoundtrackAsset(asset,hashlib.sha256(asset.read_bytes()).hexdigest());self.serve();self.grant(updated=self.now-86400)
        self.assertEqual(self.http('/v1/soundtrack/download')[0],403)
        self.grant();asset.write_bytes(b'changed');self.assertEqual(self.http('/v1/soundtrack/download')[0],503)
    def test_signed_lease_crypto_expiry_revision_and_refund(self):
        key=self.signer();self.serve();self.grant(updated=self.now-86300)
        status,_,raw=self.http('/v1/entitlements/lease');self.assertEqual(status,200);first=json.loads(raw)['lease']
        payload=base64.urlsafe_b64decode(first['payload']+'==');key.public_key().verify(base64.urlsafe_b64decode(first['signature']+'=='),payload)
        claims=json.loads(payload);self.assertEqual(claims['expires_at'],self.now+100);self.assertIn('soundtrack.01',claims['entitlements'])
        self.grant('revoked');second=json.loads(self.http('/v1/entitlements/lease')[2])['lease'];claims2=json.loads(base64.urlsafe_b64decode(second['payload']+'=='))
        self.assertEqual(claims2['entitlements'],[]);self.assertGreater(claims2['revision'],claims['revision'])
        self.now-=1;self.assertEqual(self.http('/v1/entitlements/lease')[0],503)
    def test_commerce_capabilities_requires_login_and_checks_asset_before_ownership(self):
        self.serve()
        self.assertEqual(self.http('/v1/commerce/capabilities',token=False)[0],401)
        self.assertEqual(json.loads(self.http('/v1/commerce/capabilities')[2])['soundtrack_delivery_ready'],False)
        asset=self.root/'album.zip';asset.write_bytes(b'PKfixture')
        self.app.soundtrack=SoundtrackAsset(asset,hashlib.sha256(asset.read_bytes()).hexdigest());self.signer()
        capabilities=json.loads(self.http('/v1/commerce/capabilities')[2])
        self.assertTrue(capabilities['soundtrack_delivery_ready']);self.assertTrue(capabilities['ownership_lease_available'])
        self.assertEqual(self.http('/v1/soundtrack/download')[0],403)
        asset.unlink();self.assertFalse(json.loads(self.http('/v1/commerce/capabilities')[2])['soundtrack_delivery_ready'])
        with self.db.transaction() as db:db.execute("UPDATE flags SET enabled=0 WHERE name='purchases'")
        self.assertFalse(json.loads(self.http('/v1/commerce/capabilities')[2])['ownership_lease_available'])

    def test_signer_development_origin_requires_explicit_loopback_opt_in(self):
        self.signer();path=self.root/'signer.json'
        with self.assertRaises(ValueError):OwnershipSigner(path,'http://localhost:8765')
        OwnershipSigner(path,'http://localhost:8765',allow_local_development=True)
        with self.assertRaises(ValueError):OwnershipSigner(path,'http://external.invalid',allow_local_development=True)

    def test_unconfigured_factory_has_no_fabricated_grants_or_download(self):
        runtime=create_runtime(self.root/'default.sqlite3',clock=lambda:self.now)
        _,account=runtime.application.dispatch('POST','/v1/accounts',{'consent_cloud':True})
        for route in ['/v1/entitlements/lease','/v1/soundtrack/manifest']:
            with self.assertRaises(ApiError) as result:runtime.application.dispatch('GET',route,{},account['session_token'])
            self.assertEqual(result.exception.status,503)
    def test_configured_factory_soundtrack_and_lease_load_without_provider_secrets(self):
        self.signer();asset=self.root/'album.zip';asset.write_bytes(b'PKfixture')
        config=secret(self.root/'service.json',{'version':1,'ownership':{'private_key_file':str(self.root/'signer.json'),'issuer':'https://service.example.invalid'},'soundtrack':{'archive_file':str(asset),'sha256':hashlib.sha256(asset.read_bytes()).hexdigest()}})
        runtime=create_runtime(self.root/'configured.sqlite3',config)
        self.assertIsNotNone(runtime.application.soundtrack);self.assertIsNotNone(runtime.application.ownership_signer)
        with self.assertRaises(VerificationUnavailable):runtime.application.purchase_verifier.verify('google','fake','account')

if __name__=='__main__':unittest.main()
