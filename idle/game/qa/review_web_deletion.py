"""Independent local HTTP rejection probes; synthetic temporary SQLite only."""
import concurrent.futures
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from wsgiref.simple_server import make_server
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from services.tideglass_service.api import Application, SESSION_SECONDS
from services.tideglass_service.__main__ import ThreadedServer, QuietHandler
from services.tideglass_service.web_deletion import DeletionWebApplication

class BrowserDeletionReview(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='tideglass-review-deletion-')
        self.addCleanup(self.temporary.cleanup)
        self.now=2000000
        self.app=Application(Path(self.temporary.name)/'synthetic.sqlite3',clock=lambda:self.now)
        self.server=make_server('127.0.0.1',0,self.app,server_class=ThreadedServer,handler_class=QuietHandler)
        self.origin=f'http://127.0.0.1:{self.server.server_port}'
        self.server.set_app(DeletionWebApplication(self.app,origin=self.origin,allow_loopback_http=True))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop)
        self.account=self.app.dispatch('POST','/v1/accounts',{'consent_cloud':True})[1]
    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
    def request(self,path,body,token=None,method='POST',raw=None,changes=None):
        headers={'Content-Type':'application/json','Origin':self.origin,'X-Tideglass-Deletion':'1'}
        if token:headers['Authorization']='Bearer '+token
        headers.update(changes or {})
        data=raw if raw is not None else json.dumps(body).encode()
        try:
            with urlopen(Request(self.origin+path,method=method,headers=headers,data=data),timeout=5) as r:
                return r.status,json.loads(r.read())
        except HTTPError as e:
            raw=e.read()
            try:return e.code,json.loads(raw)
            except ValueError:return e.code,{'plain_response':True}
    def login(self):
        status,data=self.request('/v1/sessions',{k:self.account[k] for k in ('account_id','recovery_code')})
        self.assertEqual(status,200);return data['session_token']
    def delete(self,token,body=None):
        return self.request('/v1/account',body or {'confirm_delete':True,'recovery_code':self.account['recovery_code']},token,'DELETE')
    def account_count(self):
        with self.app.db.read() as db:return db.execute('SELECT count(*) FROM accounts').fetchone()[0]
    def test_duplicate_json_keys_do_not_authenticate_or_delete(self):
        valid={k:self.account[k] for k in ('account_id','recovery_code')}
        raw=json.dumps(valid)[:-1]+',"account_id":"'+self.account['account_id']+'"}'
        self.assertEqual(self.request('/v1/sessions',None,raw=raw.encode())[0],400)
        token=self.login()
        raw=json.dumps({'recovery_code':self.account['recovery_code'],'confirm_delete':False})[:-1]+',"confirm_delete":true}'
        self.assertEqual(self.request('/v1/account',None,token,'DELETE',raw=raw.encode())[0],400)
        self.assertEqual(self.account_count(),1)
        self.assertEqual(self.delete(token)[0],200)
    def test_confirmation_types_and_cross_account_code_do_not_delete(self):
        other=self.app.dispatch('POST','/v1/accounts',{'consent_cloud':True})[1]
        token=self.login()
        for confirmation in (1,'true',None,[],{}):
            with self.subTest(confirmation=type(confirmation).__name__):
                self.assertEqual(self.delete(token,{'confirm_delete':confirmation,'recovery_code':self.account['recovery_code']})[0],403)
        self.assertEqual(self.delete(token,{'confirm_delete':True,'recovery_code':other['recovery_code']})[0],403)
        self.assertEqual(self.account_count(),2)
        self.assertEqual(self.delete(token)[0],200)
        self.assertEqual(self.account_count(),1)
    def test_expired_session_cannot_delete_but_fresh_recovery_can(self):
        token=self.login()
        self.now+=SESSION_SECONDS
        self.assertEqual(self.delete(token)[0],401)
        self.assertEqual(self.account_count(),1)
        self.assertEqual(self.delete(self.login())[0],200)
    def test_concurrent_duplicate_deletion_has_only_one_confirmed_commit(self):
        token=self.login()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.delete(token)[0],range(2)))
        self.assertEqual(sorted(results),[200,401])
        self.assertEqual(self.account_count(),0)
    def test_malformed_auth_shapes_are_rejected_without_session_issuance(self):
        with self.app.db.read() as db:before=db.execute('SELECT count(*) FROM sessions').fetchone()[0]
        for body in (None,[],True,{'account_id':self.account['account_id'],'recovery_code':True},
                     {'account_id':self.account['account_id'],'recovery_code':self.account['recovery_code'],'extra':1}):
            with self.subTest(shape=type(body).__name__):self.assertIn(self.request('/v1/sessions',body)[0],(400,401))
        with self.app.db.read() as db:self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0],before)
        self.assertTrue(self.login())
    def test_cross_origin_and_navigation_metadata_reject_mutation(self):
        body={k:self.account[k] for k in ('account_id','recovery_code')}
        for headers in ({'Origin':'null'},{'Origin':'https://other.invalid'},{'Sec-Fetch-Site':'cross-site'},
                        {'Sec-Fetch-Site':'same-site'},{'Cookie':'synthetic=1'},{'X-Tideglass-Deletion':'0'}):
            with self.subTest(headers=list(headers)):self.assertIn(self.request('/v1/sessions',body,changes=headers)[0],(400,403))
        self.assertEqual(self.account_count(),1)
        self.assertTrue(self.login())

if __name__=='__main__':unittest.main(verbosity=2)
