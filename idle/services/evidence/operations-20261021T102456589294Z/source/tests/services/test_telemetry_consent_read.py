"""Actual HTTP consent reads must never create or renew consent."""
import unittest
from tests.services import test_service as base


class ConsentReadTests(unittest.TestCase):
    setUp = base.ServiceTests.setUp
    tearDown = base.ServiceTests.tearDown
    call = base.ServiceTests.call

    def assert_consent(self, enabled, revision, **kwargs):
        status, body = self.call('GET', '/v1/telemetry/consent', **kwargs)
        self.assertEqual(status, 200)
        self.assertEqual(body['enabled'], enabled)
        self.assertEqual(body['revision'], revision)
        self.assertTrue(body['request_id'])

    def test_authenticated_read_does_not_mutate_revision(self):
        self.assertEqual(self.call('GET', '/v1/telemetry/consent', auth=False)[0], 401)
        self.assert_consent(False, 0)
        self.call('PUT', '/v1/telemetry/consent', {'enabled': True})
        for _ in range(3):
            self.assert_consent(True, 1)

    def test_remote_withdrawal_read_cannot_authorize_old_revision(self):
        self.call('PUT', '/v1/telemetry/consent', {'enabled': True})
        self.call('PUT', '/v1/telemetry/consent', {'enabled': False})
        self.assert_consent(False, 2)
        event = {'id': base.uid(), 'session_id': base.uid(),
                 'name': 'session_start', 'observed_at': self.now,
                 'properties': {'platform': 'test'}}
        self.assertEqual(self.call('POST', '/v1/telemetry/events',
                         {'consent_revision': 1, 'events': [event]})[0], 403)
        other = self.call('POST', '/v1/accounts', {'consent_cloud': True}, auth=False)[1]
        self.assert_consent(False, 0, token=other['session_token'])


if __name__ == '__main__':
    unittest.main()
