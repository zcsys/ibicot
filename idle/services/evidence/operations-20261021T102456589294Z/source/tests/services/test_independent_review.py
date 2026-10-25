"""Lead's non-author review probes, using the author's HTTP transport fixture.

Provider observations are explicitly test-only; these are not store evidence.
"""
from concurrent.futures import ThreadPoolExecutor
import unittest
from test_service import ServiceTests, snapshot, SyntheticPurchaseVerifier
from services.tideglass_service.ops import set_feature
from services.tideglass_service.verification import PurchaseObservation


class IndependentServiceReview(unittest.TestCase):
    setUp = ServiceTests.setUp
    tearDown = ServiceTests.tearDown
    call = ServiceTests.call
    upload = ServiceTests.upload
    link = ServiceTests.link

    def test_cloud_disable_preserves_privacy_export_and_deletion(self):
        original = self.link()
        set_feature(self.app.db, 'cloud', False)
        self.assertEqual(self.call('GET', '/v1/cloud')[0], 503)
        self.assertEqual(self.upload(snapshot(original), 1)[0], 503)
        status, data = self.call('GET', '/v1/account/export')
        self.assertEqual(status, 200)
        self.assertEqual(data['snapshots'][0]['envelope']['save_id'], original['save_id'])
        self.assertEqual(self.call('DELETE', '/v1/account', {
            'recovery_code': self.account['recovery_code'], 'confirm_delete': True})[0], 200)
        self.assertEqual(self.call('GET', '/v1/account/export')[0], 401)

    def test_deleted_account_cannot_be_recreated_by_inflight_snapshot_writes(self):
        original = self.link()
        candidates = [snapshot(original) for _ in range(6)]
        with ThreadPoolExecutor(max_workers=7) as pool:
            writes = [pool.submit(self.upload, value, 1) for value in candidates]
            deletion = pool.submit(self.call, 'DELETE', '/v1/account', {
                'recovery_code': self.account['recovery_code'], 'confirm_delete': True})
            self.assertEqual(deletion.result()[0], 200)
            for write in writes:
                self.assertIn(write.result()[0], [200, 401])
        with self.app.db.read() as db:
            for table in ['accounts', 'sessions', 'snapshots']:
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0)

    def test_fresh_independent_reverification_can_renew_expired_ownership(self):
        self.link()
        provider = SyntheticPurchaseVerifier()
        provider.observations['review-fixture'] = PurchaseObservation(
            'google', 'independent-review-only', self.account['account_id'],
            'dev.tideglass.cosmetic.01', 'purchased', 1, 'synthetic_test_only')
        self.app.purchase_verifier = provider
        request = {'platform': 'google', 'proof': 'review-fixture'}
        status, first = self.call('POST', '/v1/purchases/verify', request)
        self.assertEqual(status, 200)
        receipt = first['entitlements'][0]['verification_receipt_id']
        self.now += 86401
        self.assertEqual(self.call('GET', '/v1/entitlements')[1]['entitlements'], [])
        status, renewed = self.call('POST', '/v1/purchases/verify', request)
        self.assertEqual(status, 200)
        self.assertEqual(renewed['entitlements'][0]['verification_receipt_id'], receipt)
        set_feature(self.app.db, 'purchases', False)
        self.assertEqual(self.call('POST', '/v1/purchases/verify', request)[0], 503)
        self.assertEqual(len(self.call('GET', '/v1/entitlements')[1]['entitlements']), 1)

    def test_nested_credentials_and_conflicting_identity_never_replace_cloud(self):
        original = self.link()
        candidate = snapshot(original)
        candidate['gameplay_state']['payload']['preferences'] = {
            'nested': [{'Session_Token': 'must-never-be-uploaded'}]}
        self.assertEqual(self.upload(candidate, 1)[0], 400)
        alternate = snapshot()
        alternate['save_id'] = original['save_id']
        self.assertEqual(self.upload(alternate, 1)[0], 409)
        index = self.call('GET', '/v1/cloud')[1]
        self.assertEqual(len(index['snapshots']), 1)
        self.assertEqual(index['selected_save_id'], original['save_id'])


if __name__ == '__main__':
    unittest.main()
