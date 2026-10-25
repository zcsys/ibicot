"""Independent local adversarial QA. Provider replies and identities are fixtures."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path.cwd() / 'tests/services/providers'))
import test_fulfillment as author
from services.tideglass_service.vault import TokenVault, VaultKeys
from services.tideglass_service.verification import VerificationUnavailable
from services.tideglass_service.reconcile import reconcile
from services.tideglass_service.providers.notifications import StoreNotificationApplication
from services.tideglass_service.soundtrack import SoundtrackAsset

class IndependentFulfillmentTests(unittest.TestCase):
    def setUp(self):
        self.f = author.FulfillmentTests('runTest'); self.f.setUp()
    def tearDown(self): self.f.tearDown()
    def rotation(self):
        f = self.f; value = json.loads(f.keys.read_text())
        value['active_key_id'] = 'new'; value['keys']['new'] = base64.b64encode(os.urandom(32)).decode()
        path = author.secret(f.root/'replacement.json', value)
        return path, TokenVault(f.db, VaultKeys(path), rotation=True)
    def test_same_key_id_wrong_material_cannot_create_split_vault(self):
        f = self.f; f.vault.remember(author.TX, author.TOKEN, f.aid)
        bad = author.secret(f.root/'wrong-material.json', {'version':1, 'active_key_id':'old', 'keys':{'old':base64.b64encode(os.urandom(32)).decode()}})
        token2 = 'independent-second-fixture-token'; tx2 = hashlib.sha256(token2.encode()).hexdigest()
        accepted = False
        try:
            wrong = TokenVault(f.db, VaultKeys(bad)); wrong.remember(tx2, token2, f.aid); accepted = True
        except (ValueError, VerificationUnavailable): pass
        if accepted:
            self.assertEqual(f.vault.lookup(author.TX, f.aid), author.TOKEN)
            self.assertEqual(wrong.lookup(tx2, f.aid), token2)
            with self.assertRaises(VerificationUnavailable): f.vault.lookup(tx2, f.aid)
            with self.assertRaises(VerificationUnavailable): wrong.lookup(author.TX, f.aid)
        self.assertFalse(accepted, 'QA016: same key ID accepted different AES material and wrote an incompatible second row; neither keyring can read the whole vault')
    def test_rotation_after_commit_response_loss_recovers_and_old_writer_stops(self):
        f = self.f; f.vault.remember(author.TX, author.TOKEN, f.aid); path, rotation = self.rotation()
        def fault(stage):
            if stage == 'after_commit': raise RuntimeError('fixture response loss')
        f.db.fault = fault
        with self.assertRaises(RuntimeError): rotation.rotate()
        f.db.fault = None
        restored = TokenVault(f.db, VaultKeys(path)); self.assertEqual(restored.lookup(author.TX, f.aid), author.TOKEN)
        with self.assertRaises(VerificationUnavailable): f.vault.remember(author.TX, author.TOKEN, f.aid)
        self.assertEqual(restored.rotate(), 1)
    def test_rotation_corrupt_later_row_rolls_back_entire_epoch(self):
        f=self.f; f.vault.remember(author.TX, author.TOKEN, f.aid)
        token2='second-token-fixture'; tx2=hashlib.sha256(token2.encode()).hexdigest(); f.vault.remember(tx2,token2,f.aid)
        with f.db.transaction() as db: db.execute('UPDATE provider_tokens SET ciphertext=? WHERE transaction_id=?',(b'corrupt',tx2))
        with f.db.read() as db: before=[tuple(r) for r in db.execute('SELECT * FROM provider_tokens ORDER BY transaction_id')]
        _, rotation=self.rotation()
        with self.assertRaises(VerificationUnavailable): rotation.rotate()
        with f.db.read() as db:
            self.assertEqual(before,[tuple(r) for r in db.execute('SELECT * FROM provider_tokens ORDER BY transaction_id')]); self.assertEqual(db.execute('SELECT active_key_id FROM provider_vault_state').fetchone()[0],'old')
        self.assertEqual(f.vault.lookup(author.TX,f.aid),author.TOKEN)
    def test_foreign_account_aad_transplant_rejects_and_nonce_collision_preserves_first(self):
        f=self.f; _,second=f.app.dispatch('POST','/v1/accounts',{'consent_cloud':True})
        with patch('services.tideglass_service.vault.os.urandom',return_value=b'Q'*12):
            f.vault.remember(author.TX,author.TOKEN,f.aid)
            other='nonce-second'; other_tx=hashlib.sha256(other.encode()).hexdigest()
            with self.assertRaises(Exception): f.vault.remember(other_tx,other,f.aid)
        self.assertEqual(f.vault.lookup(author.TX,f.aid),author.TOKEN)
        with f.db.transaction() as db: db.execute('UPDATE provider_tokens SET account_id=? WHERE transaction_id=?',(second['account_id'],author.TX))
        self.assertIsNone(f.vault.lookup(author.TX,f.aid))
        with self.assertRaises(VerificationUnavailable): f.vault.lookup(author.TX,second['account_id'])
    def event(self):
        event={'packageName':'dev.tideglass.game','oneTimeProductNotification':{'purchaseToken':author.TOKEN,'notificationType':1}}
        return {'message':{'data':base64.b64encode(json.dumps(event).encode()).decode()}}
    def test_deleted_account_callback_never_reads_provider_or_recreates_state(self):
        f=self.f; verifier,_=f.google(); f.purchase(); f.signer(); f.app.dispatch('GET','/v1/entitlements/lease',{},f.token); reconcile(f.app)
        identity=Mock(); f.serve(StoreNotificationApplication(f.app,google=verifier,google_identity=identity))
        f.app.dispatch('DELETE','/v1/account',{'recovery_code':f.account['recovery_code'],'confirm_delete':True},f.token)
        calls=verifier.http.get.call_count
        self.assertEqual(f.http('/providers/google/notifications',body=self.event(),method='POST')[0],200)
        self.assertEqual(verifier.http.get.call_count,calls)
        with f.db.read() as db:
            for table in ['accounts','sessions','purchases','provider_tokens','purchase_reconciliation','ownership_leases']:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0,table)
    def test_callback_fresh_provider_foreign_binding_preserves_original_grant(self):
        f=self.f; verifier,data=f.google(); f.purchase(); original=f.app.dispatch('GET','/v1/entitlements',{},f.token)[1]
        data['obfuscatedExternalAccountId']='foreign-fixture-account'; data['purchaseStateContext']['purchaseState']='CANCELLED'
        f.serve(StoreNotificationApplication(f.app,google=verifier,google_identity=Mock()))
        self.assertEqual(f.http('/providers/google/notifications',body=self.event(),method='POST')[0],503)
        self.assertEqual(f.app.dispatch('GET','/v1/entitlements',{},f.token)[1],original)
    def test_ack_refund_between_refresh_and_preflight_does_not_acknowledge(self):
        f=self.f; verifier,data=f.google(); f.purchase()
        refunded=copy.deepcopy(data);refunded['productLineItem'][0]['productOfferDetails']['refundableQuantity']=0
        verifier.http.get.side_effect=[author.Response(copy.deepcopy(data)),author.Response(refunded)]
        result=reconcile(f.app);self.assertEqual(result['failed'],1);self.assertEqual(verifier.http.post.call_count,0)
        with f.db.read() as db:self.assertEqual(db.execute('SELECT acknowledged FROM purchases').fetchone()[0],0)
    def test_lease_commit_failure_leaves_revision_reusable_and_expiry_is_exclusive(self):
        f=self.f; f.signer(); f.grant(updated=f.now-86399)
        def fault(stage):
            if stage=='before_commit':raise RuntimeError('fixture failure')
        f.db.fault=fault
        with self.assertRaises(RuntimeError):f.app.dispatch('GET','/v1/entitlements/lease',{},f.token)
        f.db.fault=None
        first=f.app.dispatch('GET','/v1/entitlements/lease',{},f.token)[1]['lease']; payload=json.loads(base64.urlsafe_b64decode(first['payload']+'=='))
        self.assertEqual(payload['revision'],1);self.assertEqual(payload['expires_at'],f.now+1)
        f.now+=1; second=f.app.dispatch('GET','/v1/entitlements/lease',{},f.token)[1]['lease']; claims=json.loads(base64.urlsafe_b64decode(second['payload']+'=='))
        self.assertEqual(claims['revision'],2); self.assertEqual(claims['entitlements'],[])
    def test_soundtrack_query_credentials_feature_disable_and_replaced_inode_reject(self):
        f=self.f; asset=f.root/'fixture.zip';asset.write_bytes(b'PKindependent-fixture');digest=hashlib.sha256(asset.read_bytes()).hexdigest()
        f.app.soundtrack=SoundtrackAsset(asset,digest);f.grant();f.serve()
        self.assertEqual(f.http('/v1/soundtrack/download?token='+f.token,token=False)[0],400)
        with f.db.transaction() as db:db.execute("UPDATE flags SET enabled=0 WHERE name='purchases'")
        self.assertEqual(f.http('/v1/soundtrack/download')[0],503)
        with f.db.transaction() as db:db.execute("UPDATE flags SET enabled=1 WHERE name='purchases'")
        replacement=f.root/'new.zip';replacement.write_bytes(asset.read_bytes());replacement.replace(asset)
        self.assertEqual(f.http('/v1/soundtrack/download')[0],503)
        self.assertFalse(json.loads(f.http('/v1/commerce/capabilities')[2])['soundtrack_delivery_ready'])

if __name__=='__main__':unittest.main(verbosity=2)
