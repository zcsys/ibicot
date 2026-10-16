"""Adapter/cryptographic tests, not real store transaction or ad-view evidence."""
import base64
from dataclasses import replace
import io
import tempfile
from pathlib import Path
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from urllib.parse import urlencode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from google.auth.credentials import AnonymousCredentials
from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier
from appstoreserverlibrary.models.Environment import Environment
from services.tideglass_service.providers.stores import ApplePurchaseVerifier,GooglePurchaseVerifier,CombinedPurchaseVerifier
from services.tideglass_service.providers.admob import AdMobVerifier,AdMobCallbackApplication
from services.tideglass_service.api import Application
from services.tideglass_service.verification import VerificationUnavailable

ACCOUNT='00000000-0000-4000-8000-000000000001';PRODUCT='dev.tideglass.pass.01'
class Response:
    def __init__(self,data,status=200):self.data=data;self.status_code=status
    def json(self):return self.data

class ProviderTests(unittest.TestCase):
    def google(self):
        vault={}
        verifier=GooglePurchaseVerifier(credentials=AnonymousCredentials(),package_name='dev.tideglass.game',allow_test_purchases=False,
            purchase_token_lookup=lambda key,account:vault.get((key,account)),remember_purchase_token=lambda key,token,account:vault.__setitem__((key,account),token))
        data={'productLineItem':[{'productId':PRODUCT,'productOfferDetails':{'quantity':1}}], 'obfuscatedExternalAccountId':ACCOUNT,
            'purchaseStateContext':{'purchaseState':'PURCHASED'},'acknowledgementState':'ACKNOWLEDGEMENT_STATE_PENDING'}
        verifier.http=Mock();verifier.http.get.return_value=Response(data);verifier.http.post.return_value=Response({},204)
        return verifier,data
    def proof(self):return json.dumps({'purchase_token':'opaque-token','expected_product_id':PRODUCT})
    def test_google_binds_account_product_and_hashed_transaction(self):
        verifier,data=self.google();obs=verifier.verify('google',self.proof(),ACCOUNT)
        self.assertEqual(obs.state,'purchased');self.assertNotIn('opaque-token',obs.transaction_id);self.assertEqual(len(obs.transaction_id),64)
        verifier.acknowledge(obs);self.assertEqual(verifier.http.post.call_count,1)
        data['obfuscatedExternalAccountId']='other'
        with self.assertRaises(VerificationUnavailable):verifier.verify('google',self.proof(),ACCOUNT)
    def test_google_pending_refund_and_test_environment_fail_closed(self):
        verifier,data=self.google()
        data['purchaseStateContext']['purchaseState']='PENDING';pending=verifier.verify('google',self.proof(),ACCOUNT);self.assertEqual((pending.state,pending.version),('pending',0))
        data['purchaseStateContext']['purchaseState']='CANCELLED';revoked=verifier.verify('google',self.proof(),ACCOUNT);self.assertEqual((revoked.state,revoked.version),('revoked',2))
        data['testPurchaseContext']={'fopType':'TEST'}
        with self.assertRaises(VerificationUnavailable):verifier.verify('google',self.proof(),ACCOUNT)
        data.pop('testPurchaseContext');data['productLineItem'][0]['productId']='forged.product'
        with self.assertRaises(VerificationUnavailable):verifier.verify('google',self.proof(),ACCOUNT)
    def test_google_acknowledged_retries_do_not_repeat_post(self):
        verifier,data=self.google();obs=verifier.verify('google',self.proof(),ACCOUNT)
        data['acknowledgementState']='ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED';verifier.acknowledge(obs);verifier.http.post.assert_not_called()
        data['purchaseStateContext']['purchaseState']='CANCELLED'
        with self.assertRaises(VerificationUnavailable):verifier.acknowledge(obs)
    def test_apple_fetches_fresh_view_and_checks_binding_then_refund(self):
        # API/decoded-response doubles test policy mapping only. The next test
        # exercises the real Apple SDK's rejection of a forged signature.
        verifier=ApplePurchaseVerifier.__new__(ApplePurchaseVerifier);verifier.bundle_id='dev.tideglass.game';verifier.environment='Sandbox'
        verifier.client=Mock();verifier.client.get_transaction_info.return_value=SimpleNamespace(signedTransactionInfo='provider-response')
        decoded=SimpleNamespace(transactionId='123456',productId=PRODUCT,bundleId='dev.tideglass.game',appAccountToken=ACCOUNT,rawEnvironment='Sandbox',quantity=1,rawType='Non-Consumable',signedDate=123,revocationDate=None)
        verifier.verifier=Mock();verifier.verifier.verify_and_decode_signed_transaction.return_value=decoded
        proof=json.dumps({'transaction_id':'123456','expected_product_id':PRODUCT})
        self.assertEqual(verifier.verify('apple',proof,ACCOUNT).state,'purchased');verifier.client.get_transaction_info.assert_called_once_with('123456')
        decoded.revocationDate=100;decoded.signedDate=124;self.assertEqual(verifier.verify('apple',proof,ACCOUNT).state,'revoked')
        decoded.appAccountToken='other'
        with self.assertRaises(VerificationUnavailable):verifier.verify('apple',proof,ACCOUNT)
    def test_real_apple_sdk_rejects_forged_jws(self):
        verifier=ApplePurchaseVerifier.__new__(ApplePurchaseVerifier);verifier.bundle_id='dev.tideglass.game';verifier.environment='Sandbox'
        verifier.client=Mock();verifier.client.get_transaction_info.return_value=SimpleNamespace(signedTransactionInfo='eyJhbGciOiJub25lIn0.eyJwcm9kdWN0SWQiOiJwYXNzLjAxIn0.')
        verifier.verifier=SignedDataVerifier([],True,Environment.SANDBOX,'dev.tideglass.game')
        with self.assertRaises(VerificationUnavailable):verifier.verify('apple',json.dumps({'transaction_id':'123','expected_product_id':PRODUCT}),ACCOUNT)
    def admob(self,account=ACCOUNT):
        private=ec.generate_private_key(ec.SECP256R1());verifier=AdMobVerifier(ad_unit_ids={'verified-unit'},clock=lambda:100000)
        verifier._keys={'1':private.public_key()};verifier._keys_until=200000
        fields={'ad_network':'network','ad_unit':'verified-unit','custom_data':json.dumps({'day_id':1,'slot':0}), 'reward_amount':'1','reward_item':'Support token','timestamp':'100000000','transaction_id':'ad.transaction.01','user_id':account}
        prefix=urlencode(fields);signature=private.sign(prefix.encode(),ec.ECDSA(hashes.SHA256()))
        query=prefix+'&signature='+base64.urlsafe_b64encode(signature).decode().rstrip('=')+'&key_id=1'
        return verifier,query
    def test_real_ecdsa_ad_signature_binding_and_tamper(self):
        verifier,query=self.admob();self.assertEqual(verifier.verify(query,ACCOUNT,1,0).transaction_id,'ad.transaction.01')
        for candidate,account,day,slot in [(query.replace('reward_amount=1','reward_amount=2'),ACCOUNT,1,0),(query,'other',1,0),(query,ACCOUNT,1,1),(query.replace('timestamp=100000000','timestamp=200000000'),ACCOUNT,1,0)]:
            with self.assertRaises(VerificationUnavailable):verifier.verify(candidate,account,day,slot)
    def test_signed_callback_commits_once_and_forgery_cannot_use_duplicate_fast_path(self):
        with tempfile.TemporaryDirectory() as directory:
            app=Application(Path(directory)/'service.sqlite3',clock=lambda:100000)
            _,created=app.dispatch('POST','/v1/accounts',{'consent_cloud':True})
            account=created['account_id'];verifier,query=self.admob(account);app.ad_verifier=verifier
            with app.db.transaction() as db:db.execute('UPDATE accounts SET seed=?,utc_offset=0 WHERE id=?',('main.seed',account))
            wrapped=AdMobCallbackApplication(app)
            def call(value):
                statuses=[]
                result=wrapped({'REQUEST_METHOD':'GET','PATH_INFO':'/providers/admob/callback','QUERY_STRING':value},lambda status,headers:statuses.append(status))
                return statuses[0],json.loads(b''.join(result))
            self.assertEqual(call(query)[0],'200 OK');self.assertEqual(call(query)[0],'200 OK')
            self.assertEqual(call(query.replace('reward_amount=1','reward_amount=2'))[0],'400 Bad Request')
            with app.db.read() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM support_claims').fetchone()[0],1)

    def test_ad_expiry_and_unconfigured_provider_reject(self):
        verifier,query=self.admob();verifier.clock=lambda:105000
        with self.assertRaises(VerificationUnavailable):verifier.verify(query,ACCOUNT,1,0)
        with self.assertRaises(VerificationUnavailable):CombinedPurchaseVerifier().verify('apple','proof',ACCOUNT)

if __name__=='__main__':unittest.main()
