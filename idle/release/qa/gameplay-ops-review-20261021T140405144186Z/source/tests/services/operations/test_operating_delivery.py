"""Isolated receivers and command faults. No real operators or player records."""
from contextlib import contextmanager
import fcntl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from services.tideglass_service.alert_transport import deliver, envelope, read_config, _attempt
from services.tideglass_service.deployment import read_config as deployment_config, settings
from services.tideglass_service.operating_config import decode, private_bytes
from services.tideglass_service.operator_cycle import run

REPORT = {'format': 'tideglass-local-health-v1', 'generated_at': 1792570000,
          'status': 'critical', 'signals': [{'check': 'database', 'status': 'critical', 'code': 'database_missing'}]}
TOKEN = 'SyntheticReceiverCredential_123456789'


@contextmanager
def receiver(plan=('accepted',)):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            value = json.loads(body)
            requests.append((self.path, dict(self.headers), value))
            action = plan[min(len(requests)-1, len(plan)-1)]
            status = 202
            headers = {}
            if action == 'slow': time.sleep(2)
            if action == 'error': status = 503
            if action == 'redirect':
                status = 307; headers['Location'] = '/must-not-follow'
            if action == 'oversize': data = b'x'*5000
            else:
                data = json.dumps({'accepted': action != 'rejected', 'delivery_id': 'wrong' if action == 'wrong' else value['delivery_id']}).encode()
            try:
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                for key, val in headers.items(): self.send_header(key, val)
                self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try: yield server.server_port, requests
    finally: server.shutdown(); server.server_close(); thread.join(2)


class OperatingDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name); self.folder.chmod(0o700)
        self.token = self.folder/'token'; self.token.write_text(TOKEN); self.token.chmod(0o600)
    def private_json(self, value, name='config'):
        path = self.folder/name; path.write_text(json.dumps(value)); path.chmod(0o600); return path
    def config(self, port, **overrides):
        value = {'version': 1, 'enabled': True, 'environment': 'synthetic-local',
                 'recipients': [{'id': 'primary-fixture', 'url': f'http://127.0.0.1:{port}/alerts', 'token_file': str(self.token)}],
                 'attempts': 2, 'attempt_seconds': 1, 'backoff_seconds': 0, 'allow_loopback_http': True}
        value.update(overrides); return self.private_json(value)
    def profile(self, **overrides):
        value = {'version': 1, 'mode': 'loopback_http', 'host': '127.0.0.1', 'port': 8765,
                 'database': str(self.folder/'database'), 'workers': 2, 'timeout_seconds': 5,
                 'backlog': 32, 'max_requests': 100}
        value.update(overrides); return self.private_json(value, 'deployment')
    def test_disabled_has_no_transport_or_report_read(self):
        with patch('subprocess.run', side_effect=AssertionError('no command')):
            self.assertEqual(deliver(None)['status'], 'disabled')
            self.assertEqual(deliver(None,self.private_json({'version':1,'enabled':False}))['status'],'disabled')
    def test_private_inputs_reject_symlink_permissions_duplicate_and_oversize(self):
        path = self.private_json({'version': 1, 'enabled': False})
        link = self.folder/'link'; link.symlink_to(path)
        with self.assertRaises(OSError): private_bytes(link)
        path.chmod(0o644)
        with self.assertRaises(ValueError): read_config(path)
        with self.assertRaises(ValueError): decode('{"version":1,"version":2}')
        with self.assertRaises(ValueError): private_bytes(self.token,2)
    def test_fifo_private_input_is_refused_without_waiting_for_writer(self):
        fifo=self.folder/'config-fifo';os.mkfifo(fifo,0o600)
        probe="from services.tideglass_service.operating_config import private_bytes; import sys; private_bytes(sys.argv[1])"
        child=subprocess.run([sys.executable,'-c',probe,str(fifo)],capture_output=True,timeout=1)
        self.assertNotEqual(child.returncode,0)
        self.assertIn(b'Owner-only bounded regular file required',child.stderr)
    def test_strict_configuration_types_bounds_and_unknown_fields(self):
        for field, bad in [('version',True),('version',1.0),('enabled',1),('attempts',4),('attempt_seconds',6),('backoff_seconds',2),('allow_loopback_http',1),('environment','a@example.com'),('extra',1)]:
            with self.subTest(field=field,bad=bad),self.assertRaises(ValueError): read_config(self.config(8765,**{field:bad}))
    def test_url_no_plain_public_query_credentials_fragment_or_loopback_alias(self):
        path=self.config(8765); original=decode(path.read_bytes())
        for url in ['http://example.invalid/a','http://localhost/a','https://user:password@example.invalid/a','https://example.invalid/a?token=secret','https://example.invalid/a#x','https://example.invalid/\r\nX: bad','ftp://example.invalid/a']:
            with self.subTest(url=url),self.assertRaises(ValueError):
                value=decode(json.dumps(original));value['recipients'][0]['url']=url;read_config(self.private_json(value))
    def test_duplicate_receivers_and_bad_credentials_are_rejected(self):
        value=decode(self.config(8765).read_bytes());value['recipients']*=2
        with self.assertRaises(ValueError): read_config(self.private_json(value))
        self.token.write_text(TOKEN+'\nHeader: injected')
        with self.assertRaises(ValueError): read_config(self.config(8765))
    def test_only_fixed_categories_can_leave_process(self):
        report=decode(json.dumps(REPORT)); report['signals'][0]['code']='SECRET';report['account_id']='SECRET';report['checks']=[{'password':'SECRET'}]
        result=envelope(report,'synthetic-local')
        self.assertNotIn('SECRET',json.dumps(result));self.assertEqual(result['signals'][0]['code'],'unrecognized_health_code')
        self.assertFalse(result['release_gate_verified'])
        report['signals'][0]['check']='private-account'
        with self.assertRaises(ValueError): envelope(report,'synthetic-local')
    def test_inconsistent_report_and_unbounded_signals_refused(self):
        for report in [dict(REPORT,status='ok'),dict(REPORT,signals=[]),dict(REPORT,signals=REPORT['signals']*17),dict(REPORT,generated_at=True)]:
            with self.assertRaises(ValueError): envelope(report,'synthetic-local')
    def test_private_child_protocol_cannot_bypass_disabled_config(self):
        value={'version':1,'enabled':False};path=self.private_json(value)
        import hashlib
        request={'config_path':str(path),'config_digest':hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest(),
                 'recipient_id':'primary-fixture','payload':envelope(REPORT,'synthetic-local')}
        with self.assertRaises(ValueError):_attempt(request)
    def test_private_child_refuses_changed_config(self):
        path=self.config(8765)
        request={'config_path':str(path),'config_digest':'0'*64,'recipient_id':'primary-fixture','payload':envelope(REPORT,'synthetic-local')}
        with self.assertRaises(ValueError):_attempt(request)
    def test_real_http_receipt_and_payload_idempotency(self):
        with receiver() as (port,requests):
            result=deliver(REPORT,self.config(port))
            self.assertEqual(result['status'],'receiver_accepted');self.assertFalse(result['human_acknowledged'])
            self.assertEqual(len(requests),1);_,headers,body=requests[0]
            self.assertEqual(headers['Authorization'],'Bearer '+TOKEN)
            self.assertEqual(headers['Idempotency-Key'],body['delivery_id'])
            self.assertNotIn(TOKEN,json.dumps(result)+json.dumps(body))
    def test_retry_keeps_delivery_identity_and_is_bounded(self):
        with receiver(('error','accepted')) as (port,requests):
            result=deliver(REPORT,self.config(port))
            self.assertEqual(result['receipts'][0]['attempts'],2)
            self.assertEqual(requests[0][2],requests[1][2])
    def test_wrong_receipt_rejected_response_size_bound_and_no_redirect(self):
        for action in ['wrong','rejected','oversize','redirect']:
            with self.subTest(action=action),receiver((action,)) as (port,requests):
                result=deliver(REPORT,self.config(port,attempts=1))
                self.assertEqual(result['status'],'delivery_incomplete');self.assertEqual(len(requests),1)
    def test_slow_receiver_killed_by_parent_deadline(self):
        with receiver(('slow',)) as (port,requests):
            start=time.monotonic();result=deliver(REPORT,self.config(port,attempts=1))
            self.assertLess(time.monotonic()-start,1.8)
            self.assertEqual(result['receipts'][0]['code'],'attempt_deadline_exceeded')
    def test_independent_receivers_and_failed_second_delivery(self):
        with receiver() as (first,_),receiver(('error',)) as (second,_):
            value=decode(self.config(first,attempts=1).read_bytes())
            value['recipients'].append({'id':'secondary-fixture','url':f'http://127.0.0.1:{second}/alerts','token_file':str(self.token)})
            result=deliver(REPORT,self.private_json(value))
            self.assertEqual([r['receipt'] for r in result['receipts']],[True,False]);self.assertEqual(result['status'],'delivery_incomplete')
    def test_no_signals_produces_no_network(self):
        with patch('subprocess.run',side_effect=AssertionError('no network')):
            self.assertEqual(deliver(dict(REPORT,status='ok',signals=[]),self.config(8765))['status'],'no_signals')
    def test_server_limits_no_overrides_and_tls_required(self):
        value=deployment_config(self.profile());result=settings(value)
        self.assertEqual((result['worker_class'],result['threads'],result['forwarded_allow_ips']),('sync',1,''))
        self.assertFalse(result['secure_scheme_headers']);self.assertIsNone(result['accesslog'])
        for changes in [{'host':'0.0.0.0'},{'workers':5},{'timeout_seconds':0},{'backlog':129},{'max_requests':1001},{'version':1.0},{'mode':'tls'},{'database':'relative'}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):deployment_config(self.profile(**changes))
    def test_cycle_actual_missing_database_is_alerted_without_creation(self):
        missing=self.folder/'missing.sqlite3'
        with receiver() as (port,requests):
            result=run(missing,lock_file=self.folder/'cycle.lock',alert_config=self.config(port,attempts=1))
            self.assertEqual(result['health_status'],'critical');self.assertEqual(result['exit_code'],2)
            self.assertEqual(result['delivery']['status'],'receiver_accepted');self.assertFalse(missing.exists())
            self.assertIn({'check':'database','status':'critical','code':'database_missing'},requests[0][2]['signals'])
    def test_cycle_lock_prevents_overlap(self):
        lock=self.folder/'cycle.lock';fd=os.open(lock,os.O_CREAT|os.O_RDWR,0o600);self.addCleanup(os.close,fd)
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with patch('subprocess.run',side_effect=AssertionError('must not start')):
            self.assertEqual(run(self.folder/'missing',lock_file=lock)['status'],'already_running')
    def test_cycle_deadline_emits_operator_signal_and_delivery_failure_exit(self):
        with patch('services.tideglass_service.operator_cycle.subprocess.run',side_effect=subprocess.TimeoutExpired('health',1)),patch('services.tideglass_service.operator_cycle.deliver',return_value={'status':'delivery_incomplete'}) as sender:
            result=run(self.folder/'missing',lock_file=self.folder/'cycle.lock')
            self.assertEqual(result['exit_code'],4)
            self.assertEqual(sender.call_args.args[0]['signals'][0]['code'],'health_deadline_exceeded')
    def test_author_deadline_stops_entire_rehearsal_process_group(self):
        from services.verify_deployment_preparation import bounded_run
        probe="import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print(p.pid,flush=True); time.sleep(30)"
        log=self.folder/'probe.log'
        with log.open('wb') as stream:
            code=bounded_run([sys.executable,'-c',probe],cwd=Path.cwd(),stream=stream,deadline=.3,environment=os.environ.copy())
        self.assertEqual(code,124)
        pid=int(log.read_text().strip())
        status=subprocess.run(['ps','-p',str(pid),'-o','stat='],capture_output=True,text=True,timeout=1)
        # An already-dead adopted zombie may await the OS reaper briefly.
        self.assertTrue(status.returncode==1 or status.stdout.strip().startswith('Z'),status.stdout)
    def test_failed_health_command_never_promoted_to_healthy(self):
        child=subprocess.CompletedProcess([],0,b'{"exit_code":0}',b'')
        with patch('services.tideglass_service.operator_cycle.subprocess.run',return_value=child),patch('services.tideglass_service.operator_cycle.deliver',return_value={'status':'disabled'}):
            # Report schema must be validated even when delivery is disabled.
            result=run(self.folder/'missing',lock_file=self.folder/'cycle.lock')
            self.assertEqual(result['health_failure_code'],'health_command_failed')


if __name__=='__main__':unittest.main()
