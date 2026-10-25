"""Different-author review probes; all listeners are literal loopback fixtures.

Run with PYTHONPATH pointing to the copied, pinned source under review.
No production data, recipients, trust stores, scheduler, or service configuration.
"""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from services.tideglass_service.alert_transport import deliver, envelope
from services.tideglass_service.deployment import read_config as deployment_config
from services.tideglass_service.operator_cycle import run

REPORT = {'format': 'tideglass-local-health-v1', 'generated_at': 1792570000,
          'status': 'critical', 'signals': [{'check': 'database', 'status': 'critical', 'code': 'database_missing'}]}
TOKEN = 'SyntheticReviewCredential_123456789'


@contextmanager
def receiver(action, tls=None):
    received = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            received.append((dict(self.headers), payload))
            try:
                action(self, payload, len(received))
            except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
                pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    if tls:
        server.socket = tls.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port, received
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)


def receipt(handler, payload, status=202, data=None):
    data = data if data is not None else json.dumps({'accepted': True, 'delivery_id': payload['delivery_id']}).encode()
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Content-Length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class IndependentOpsReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.folder.chmod(0o700)
        self.token = self.folder/'token'
        self.token.write_text(TOKEN)
        self.token.chmod(0o600)

    def private_json(self, value, name='config'):
        path = self.folder/name
        path.write_text(json.dumps(value))
        path.chmod(0o600)
        return path

    def config(self, port, *, tls=False, attempts=1, seconds=1):
        return self.private_json({'version': 1, 'enabled': True, 'environment': 'review-local',
            'recipients': [{'id': 'synthetic', 'url': f'{"https" if tls else "http"}://127.0.0.1:{port}/alerts',
                            'token_file': str(self.token)}],
            'attempts': attempts, 'attempt_seconds': seconds, 'backoff_seconds': 0,
            'allow_loopback_http': not tls})

    def certificate(self, name='fixture', ip='127.0.0.1'):
        key, cert = self.folder/(name+'.key'), self.folder/(name+'.crt')
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                        '-subj', '/CN=synthetic-local-review', '-addext', f'subjectAltName=IP:{ip}',
                        '-keyout', str(key), '-out', str(cert)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        key.chmod(0o600)
        cert.chmod(0o600)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(cert, key)
        return context, cert

    def test_ops_ge001_severity_exactly_matches_highest_signal(self):
        rank = {'warning': 1, 'unknown': 2, 'critical': 3}
        for signal_status in rank:
            for overall in rank:
                with self.subTest(signal=signal_status, overall=overall):
                    report = dict(REPORT, status=overall, signals=[dict(REPORT['signals'][0], status=signal_status)])
                    if overall == signal_status:
                        self.assertEqual(envelope(report, 'review-local')['status'], overall)
                    else:
                        with self.assertRaises(ValueError):
                            envelope(report, 'review-local')
        report = dict(REPORT, status='unknown', signals=[dict(REPORT['signals'][0], status=s) for s in ('warning', 'unknown')])
        self.assertEqual(envelope(report, 'review-local')['status'], 'unknown')

    def test_ops_ge001_operator_refuses_downgraded_critical_even_disabled(self):
        report = dict(REPORT, status='warning', exit_code=1)
        child = subprocess.CompletedProcess([], 1, json.dumps(report).encode(), b'')
        with patch('services.tideglass_service.operator_cycle.subprocess.run', return_value=child):
            result = run(self.folder/'missing', lock_file=self.folder/'cycle.lock')
        self.assertEqual(result['health_failure_code'], 'health_command_failed')
        self.assertEqual((result['health_status'], result['exit_code']), ('critical', 2))

    def test_ops_ge002_host_requires_string_literal(self):
        profile = {'version': 1, 'mode': 'loopback_http', 'host': '127.0.0.1', 'port': 8765,
                   'database': str(self.folder/'database'), 'workers': 1, 'timeout_seconds': 2,
                   'backlog': 1, 'max_requests': 10}
        self.assertEqual(deployment_config(self.private_json(profile))['host'], '127.0.0.1')
        for bad in (2130706433, True, None, ['127.0.0.1'], '127.1', '2130706433'):
            with self.subTest(host=bad), self.assertRaises(ValueError):
                deployment_config(self.private_json(dict(profile, host=bad)))

    def test_response_loss_retries_same_envelope_and_identity(self):
        def action(handler, payload, ordinal):
            if ordinal == 1:
                handler.connection.shutdown(socket.SHUT_RDWR)
                handler.connection.close()
            else:
                receipt(handler, payload)
        with receiver(action) as (port, received):
            result = deliver(REPORT, self.config(port, attempts=2))
        self.assertEqual(result['status'], 'receiver_accepted')
        self.assertEqual(len(received), 2)
        self.assertEqual(received[0][1], received[1][1])
        self.assertEqual(received[0][0]['Idempotency-Key'], received[1][0]['Idempotency-Key'])
        self.assertFalse(result['human_acknowledged'])

    def test_duplicate_key_receipt_rejected(self):
        def action(handler, payload, ordinal):
            data = ('{"accepted":false,"accepted":true,"delivery_id":"'+payload['delivery_id']+'"}').encode()
            receipt(handler, payload, data=data)
        with receiver(action) as (port, received):
            result = deliver(REPORT, self.config(port))
        self.assertEqual(result['status'], 'delivery_incomplete')
        self.assertEqual(len(received), 1)

    def test_exact_receipt_size_boundary(self):
        for size in (4096, 4097):
            def action(handler, payload, ordinal):
                data = json.dumps({'accepted': True, 'delivery_id': payload['delivery_id']}).encode()
                receipt(handler, payload, data=data+b' '*(size-len(data)))
            with self.subTest(size=size), receiver(action) as (port, received):
                result = deliver(REPORT, self.config(port))
                self.assertEqual(result['status'], 'receiver_accepted' if size == 4096 else 'delivery_incomplete')

    def test_trickled_body_cannot_extend_child_wall_deadline(self):
        def action(handler, payload, ordinal):
            handler.send_response(202)
            handler.send_header('Content-Type', 'application/json')
            handler.send_header('Content-Length', '100')
            handler.end_headers()
            for _ in range(20):
                handler.wfile.write(b' ')
                handler.wfile.flush()
                time.sleep(.15)
        with receiver(action) as (port, received):
            start = time.monotonic()
            result = deliver(REPORT, self.config(port))
            elapsed = time.monotonic()-start
        self.assertLess(elapsed, 1.8)
        self.assertEqual(result['receipts'][0]['code'], 'attempt_deadline_exceeded')

    def test_disabled_between_attempts_stops_further_sends(self):
        path = None
        def action(handler, payload, ordinal):
            path.write_text('{"version":1,"enabled":false}')
            receipt(handler, payload, status=503)
        with receiver(action) as (port, received):
            path = self.config(port, attempts=3)
            result = deliver(REPORT, path)
        self.assertEqual(len(received), 1)
        self.assertEqual(result['status'], 'delivery_incomplete')

    def test_valid_credential_rotation_keeps_payload_identity(self):
        rotated = TOKEN+'_rotated'
        def action(handler, payload, ordinal):
            if ordinal == 1:
                self.token.write_text(rotated)
                receipt(handler, payload, status=503)
            else:
                receipt(handler, payload)
        with receiver(action) as (port, received):
            result = deliver(REPORT, self.config(port, attempts=2))
        self.assertEqual(result['status'], 'receiver_accepted')
        self.assertEqual([row[0]['Authorization'] for row in received], ['Bearer '+TOKEN, 'Bearer '+rotated])
        self.assertEqual(received[0][1], received[1][1])

    def test_ambient_proxy_is_not_used(self):
        def action(handler, payload, ordinal):
            receipt(handler, payload)
        with receiver(action) as (port, received):
            with patch.dict(os.environ, {'HTTP_PROXY': 'http://127.0.0.1:1', 'http_proxy': 'http://127.0.0.1:1',
                                         'HTTPS_PROXY': 'http://127.0.0.1:1', 'ALL_PROXY': 'http://127.0.0.1:1',
                                         'NO_PROXY': '', 'no_proxy': ''}):
                result = deliver(REPORT, self.config(port))
        self.assertEqual(result['status'], 'receiver_accepted')
        self.assertEqual(len(received), 1)

    def test_tls_requires_trusted_certificate_and_matching_literal_host(self):
        context, cert = self.certificate()
        def action(handler, payload, ordinal):
            receipt(handler, payload)
        with receiver(action, context) as (port, received):
            path = self.config(port, tls=True, seconds=2)
            with patch.dict(os.environ, {'SSL_CERT_FILE': str(cert)}):
                trusted = deliver(REPORT, path)
            empty = self.folder/'empty-ca-directory'
            empty.mkdir()
            with patch.dict(os.environ, {'SSL_CERT_FILE': str(empty/'nonexistent'), 'SSL_CERT_DIR': str(empty)}):
                untrusted = deliver(REPORT, path)
        self.assertEqual(trusted['status'], 'receiver_accepted')
        self.assertEqual(untrusted['status'], 'delivery_incomplete')
        self.assertEqual(len(received), 1)
        wrong_context, wrong_cert = self.certificate('wrong-name', '192.0.2.1')
        with receiver(action, wrong_context) as (port, received):
            with patch.dict(os.environ, {'SSL_CERT_FILE': str(wrong_cert)}):
                wrong_host = deliver(REPORT, self.config(port, tls=True, seconds=2))
        self.assertEqual(wrong_host['status'], 'delivery_incomplete')
        self.assertEqual(len(received), 0)

    def test_operator_process_death_releases_stable_lock(self):
        lock = self.folder/'cycle.lock'
        ready = self.folder/'ready'
        script = """from pathlib import Path
from unittest.mock import patch
import sys,time
from services.tideglass_service.operator_cycle import run
def hold(*a,**kw):
    Path(sys.argv[2]).write_text('held')
    time.sleep(30)
with patch('services.tideglass_service.operator_cycle.subprocess.run',side_effect=hold):
    run(sys.argv[3],lock_file=Path(sys.argv[1]))
"""
        child = subprocess.Popen([sys.executable, '-c', script, str(lock), str(ready), str(self.folder/'missing')],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic()+3
            while not ready.exists() and time.monotonic()<deadline:
                time.sleep(.02)
            self.assertTrue(ready.exists())
            inode = lock.stat().st_ino
            self.assertEqual(run(self.folder/'missing', lock_file=lock)['status'], 'already_running')
            child.kill()
            child.wait(2)
            result = run(self.folder/'missing', lock_file=lock)
            self.assertEqual((result['status'], result['health_status']), ('completed', 'critical'))
            self.assertEqual(lock.stat().st_ino, inode)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(2)
            child.stderr.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
