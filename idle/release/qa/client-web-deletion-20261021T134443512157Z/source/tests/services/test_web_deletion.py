"""Isolated synthetic HTTP/SQLite deletion qualification, never a hosted service."""
import hashlib
import io
import json
from pathlib import Path
import secrets
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from wsgiref.simple_server import make_server

from services.tideglass_service.api import Application, digest
from services.tideglass_service.factory import create_runtime
from services.tideglass_service.__main__ import ThreadedServer, QuietHandler
from services.tideglass_service.web_deletion import DeletionWebApplication, PREFIX


class WebDeletionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.app=Application(self.root/'synthetic.sqlite3')
        self.server=make_server('127.0.0.1',0,self.app,server_class=ThreadedServer,handler_class=QuietHandler)
        self.origin=f'http://127.0.0.1:{self.server.server_port}'
        self.web=DeletionWebApplication(self.app,origin=self.origin,allow_loopback_http=True)
        self.server.set_app(self.web);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop)
        self.account=self.app.dispatch('POST','/v1/accounts',{'consent_cloud':True})[1]
    def stop(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def count(self,table):
        with self.app.db.read() as db:return db.execute('SELECT count(*) FROM '+table).fetchone()[0]
    def call(self,method,path,body=None,*,token=None,web=True,headers=None,raw=None):
        values={'Origin':self.origin,'X-Tideglass-Deletion':'1'} if web else {}
        if token:values['Authorization']='Bearer '+token
        data=raw if raw is not None else json.dumps(body).encode() if body is not None else None
        if data is not None:values['Content-Type']='application/json'
        values.update(headers or {})
        try:
            with urlopen(Request(self.origin+path,method=method,data=data,headers=values),timeout=3) as response:
                return response.status,dict(response.headers),response.read()
        except HTTPError as error:return error.code,dict(error.headers),error.read()
    def login(self):
        status,_,raw=self.call('POST','/v1/sessions',{k:self.account[k] for k in ('account_id','recovery_code')})
        self.assertEqual(status,200);return json.loads(raw)['session_token']
    def deletion(self,token,**changes):
        body={'recovery_code':self.account['recovery_code'],'confirm_delete':True};body.update(changes)
        return self.call('DELETE','/v1/account',body,token=token)
    def direct(self,environ):
        result=[]
        body=b''.join(self.web({'REQUEST_METHOD':'GET','PATH_INFO':PREFIX,'wsgi.url_scheme':'http','HTTP_HOST':self.origin.split('://')[1],'wsgi.input':io.BytesIO(),**environ},lambda status,headers,exc_info=None:result.append((status,headers))))
        return int(result[0][0].split()[0]),body

    def test_page_assets_and_head_have_no_database_side_effects(self):
        before={t:self.count(t) for t in ('accounts','sessions','rate_limits','operations')}
        for path in [PREFIX,PREFIX+'/delete.js',PREFIX+'/delete.css']:
            status,headers,raw=self.call('GET',path,web=False)
            self.assertEqual(status,200);self.assertTrue(raw);self.assertNotIn('Set-Cookie',headers)
            self.assertIn('no-store',headers['Cache-Control']);self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
            self.assertEqual(headers['Referrer-Policy'],'no-referrer');self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertEqual(self.call('HEAD',PREFIX,web=False)[2],b'')
        self.assertEqual(before,{t:self.count(t) for t in before})
    def test_wrong_code_does_not_create_session_or_delete(self):
        status,_,_=self.call('POST','/v1/sessions',{'account_id':self.account['account_id'],'recovery_code':'x'*43})
        self.assertEqual(status,401);self.assertEqual(self.count('accounts'),1);self.assertEqual(self.count('sessions'),1)
    def test_explicit_confirmation_required_after_real_recovery_authentication(self):
        token=self.login()
        self.assertEqual(self.deletion(token,confirm_delete=False)[0],403)
        self.assertEqual(self.deletion(token,recovery_code='x'*43)[0],403)
        self.assertEqual(self.count('accounts'),1)
        status,_,raw=self.deletion(token);self.assertEqual(status,200)
        self.assertTrue(json.loads(raw)['deleted']);self.assertTrue(json.loads(raw)['guest_progress_unchanged'])
        self.assertTrue(json.loads(raw)['store_purchases_not_cancelled']);self.assertEqual(self.count('accounts'),0)
    def test_account_delete_cascades_all_base_account_records_and_sessions(self):
        aid=self.account['account_id']
        with self.app.db.transaction() as db:
            db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?,?,?)',(aid,'synthetic-save','branch',0,None,'utc','digest','{}',2,1))
            db.execute('INSERT INTO purchases VALUES(?,?,?,?,?,?,?,?,?,?)',('test','synthetic-transaction',aid,'appearance','owned',1,'synthetic','synthetic',1,1))
            db.execute('INSERT INTO support_claims VALUES(?,?,?,?,?,?,?,?,?)',(aid,1,0,'free','synthetic-receipt','source','synthetic',1,None))
            db.execute('INSERT INTO ad_receipts VALUES(?,?,?,?)',('synthetic-ad',aid,1,0))
            db.execute('INSERT INTO telemetry VALUES(?,?,?,?,?,?,?)',(aid,'event','session','session_start',1,1,'{}'))
        token=self.login();self.assertEqual(self.deletion(token)[0],200)
        for table in ('accounts','sessions','snapshots','purchases','support_claims','ad_receipts','telemetry'):
            self.assertEqual(self.count(table),0,table)
        self.assertEqual(self.call('GET','/v1/cloud',token=self.account['session_token'],web=False)[0],401)
    def test_failed_deletion_session_can_be_revoked_without_all_device_logout(self):
        token=self.login();self.assertEqual(self.deletion(token,confirm_delete=False)[0],403)
        self.assertEqual(self.call('POST','/v1/sessions/revoke',{'all_devices':False},token=token)[0],200)
        self.assertEqual(self.call('GET','/v1/cloud',token=token,web=False)[0],401)
        self.assertEqual(self.call('GET','/v1/cloud',token=self.account['session_token'],web=False)[0],200)
    def test_transaction_failure_before_commit_rolls_back(self):
        token=self.login();calls=0
        def fault(stage):
            nonlocal calls
            if stage=='before_commit':
                calls+=1
                if calls==2:raise RuntimeError('synthetic commit fault')
        self.app.db.fault=fault
        self.assertEqual(self.deletion(token)[0],500);self.app.db.fault=None
        self.assertEqual(self.count('accounts'),1)
    def test_response_failure_after_commit_does_not_mean_account_survived(self):
        token=self.login();calls=0
        def fault(stage):
            nonlocal calls
            if stage=='after_commit':
                calls+=1
                if calls==2:raise RuntimeError('synthetic response loss')
        self.app.db.fault=fault
        self.assertEqual(self.deletion(token)[0],500);self.app.db.fault=None
        self.assertEqual(self.count('accounts'),0)
    def test_cross_origin_null_origin_and_same_site_are_rejected_before_api(self):
        for header in [{'Origin':'https://elsewhere.invalid'},{'Origin':'null'},{'Sec-Fetch-Site':'cross-site'},{'Sec-Fetch-Site':'same-site'}]:
            self.assertEqual(self.call('POST','/v1/sessions',{k:self.account[k] for k in ('account_id','recovery_code')},headers=header)[0],403)
        self.assertEqual(self.count('sessions'),1);self.assertEqual(self.count('rate_limits'),0)
        self.assertEqual(self.call('OPTIONS','/v1/account',headers={'Origin':'https://elsewhere.invalid'})[0],403)
    def test_browser_marker_requires_same_origin_and_allowed_route(self):
        self.assertEqual(self.call('POST','/v1/accounts',{'consent_cloud':True})[0],403)
        self.assertEqual(self.direct({'REQUEST_METHOD':'POST','PATH_INFO':'/v1/sessions','HTTP_X_TIDEGLASS_DELETION':'1','CONTENT_LENGTH':'10'})[0],403)
        self.assertEqual(self.call('POST','/v1/sessions',{},web=False,headers={'Origin':self.origin})[0],403)
        self.assertEqual(self.count('accounts'),1)
    def test_query_cookie_host_and_forwarded_scheme_cannot_relax_policy(self):
        for headers in [{'Cookie':'synthetic=1'},{'Host':'attacker.invalid'},{'Host':'attacker.invalid','X-Forwarded-Host':self.origin.split('://')[1]}]:
            self.assertIn(self.call('GET',PREFIX,web=False,headers=headers)[0],(400,403))
        self.assertEqual(self.call('GET',PREFIX+'?recovery_code=synthetic',web=False)[0],400)
        self.assertEqual(self.direct({'wsgi.url_scheme':'http','HTTP_HOST':'secure.example.invalid','HTTP_X_FORWARDED_PROTO':'https'})[0],403)
    def test_bounded_body_content_type_and_read_only_routes(self):
        self.assertEqual(self.call('POST','/v1/sessions',raw=b'x'*1025)[0],413)
        self.assertEqual(self.call('POST','/v1/sessions',raw=b'{}',headers={'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.call('POST',PREFIX,{},web=False)[0],405)
        self.assertEqual(self.call('GET',PREFIX+'/../api.py',web=False)[0],404)
        self.assertEqual(self.direct({'CONTENT_LENGTH':'1'})[0],400)
        self.assertEqual(self.count('accounts'),1);self.assertEqual(self.count('rate_limits'),0)
    def test_native_api_without_browser_origin_remains_existing_contract(self):
        self.assertEqual(self.call('POST','/v1/sessions',{k:self.account[k] for k in ('account_id','recovery_code')},web=False)[0],200)
    def test_production_requires_actual_secure_scheme_and_exact_host(self):
        self.web=DeletionWebApplication(self.app,origin='https://deletion.example.invalid')
        self.assertEqual(self.direct({'HTTP_HOST':'deletion.example.invalid','HTTP_X_FORWARDED_PROTO':'https'})[0],403)
        result=[]
        environ={'REQUEST_METHOD':'GET','PATH_INFO':PREFIX,'HTTP_HOST':'deletion.example.invalid','wsgi.url_scheme':'https','wsgi.input':io.BytesIO()}
        b''.join(self.web(environ,lambda status,headers,exc_info=None:result.append((status,dict(headers)))))
        self.assertEqual(result[0][0],'200 OK');self.assertEqual(result[0][1]['Strict-Transport-Security'],'max-age=31536000')
    def test_invalid_configuration_and_explicit_factory_opt_in(self):
        for origin,allowed in [('http://example.invalid',True),('http://localhost:8765',True),('https://user:secret@example.invalid',False),('https://example.invalid/path',False),('https://example.invalid?code=x',False),('https://example.invalid',True),('http://127.0.0.1:8765',False)]:
            with self.subTest(origin=origin),self.assertRaises(ValueError):DeletionWebApplication(self.app,origin=origin,allow_loopback_http=allowed)
        runtime=create_runtime(self.root/'default.sqlite3');self.assertIs(runtime.wsgi,runtime.application)
    def test_no_plaintext_credentials_or_token_stored_in_database(self):
        token=self.login()
        with self.app.db.read() as db:
            dump='\n'.join(db.iterdump())
        for value in (self.account['recovery_code'],self.account['session_token'],token):self.assertNotIn(value,dump)
        self.assertIn(digest(token),dump)

if __name__=='__main__':unittest.main()
