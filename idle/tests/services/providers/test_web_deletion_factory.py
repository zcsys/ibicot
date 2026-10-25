"""Configured factory uses the existing pinned optional-provider environment."""
import json
import hashlib
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest
from services.tideglass_service.factory import create_runtime
from services.tideglass_service.web_deletion import DeletionWebApplication

class WebDeletionFactoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
    def configure(self,value):
        path=self.root/'config.json';path.write_text(json.dumps(value));path.chmod(0o600);return path
    def test_explicit_web_only_configuration_wraps_existing_application(self):
        config=self.configure({'version':1,'web_deletion':{'origin':'http://127.0.0.1:8765','allow_loopback_http':True}})
        runtime=create_runtime(self.root/'synthetic.sqlite3',config)
        self.assertIsInstance(runtime.wsgi,DeletionWebApplication);self.assertIs(runtime.wsgi.downstream,runtime.application)
        self.assertIsNone(runtime.vault)
    def test_absent_web_section_keeps_existing_wsgi(self):
        runtime=create_runtime(self.root/'synthetic.sqlite3',self.configure({'version':1}))
        self.assertIs(runtime.wsgi,runtime.application)
    def test_confirmed_api_deletion_erases_real_encrypted_vault_rows(self):
        from services.tideglass_service.vault import TokenVault
        runtime=create_runtime(self.root/'synthetic.sqlite3',self.configure({'version':1,'web_deletion':{'origin':'http://127.0.0.1:8765','allow_loopback_http':True}}))
        app=runtime.application
        account=app.dispatch('POST','/v1/accounts',{'consent_cloud':True})[1]
        vault=TokenVault(app.db,SimpleNamespace(active='synthetic',keys={'synthetic':b'k'*32}))
        plaintext='SYNTHETIC provider token, not a purchase'
        vault.remember(hashlib.sha256(plaintext.encode()).hexdigest(),plaintext,account['account_id'])
        with app.db.read() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM provider_tokens').fetchone()[0],1)
            self.assertNotIn(plaintext,'\n'.join(db.iterdump()))
        token=app.dispatch('POST','/v1/sessions',{k:account[k] for k in ('account_id','recovery_code')})[1]['session_token']
        self.assertEqual(app.dispatch('DELETE','/v1/account',{'recovery_code':account['recovery_code'],'confirm_delete':True},token)[0],200)
        with app.db.read() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM provider_tokens').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM provider_vault_key_bindings').fetchone()[0],1)

    def test_invalid_or_insecure_configuration_fails_closed(self):
        for section in [{'origin':'http://example.invalid'},{'origin':'https://example.invalid','allow_loopback_http':'yes'},{'origin':'https://example.invalid','enabled':True}]:
            with self.assertRaises(ValueError):create_runtime(self.root/'synthetic.sqlite3',self.configure({'version':1,'web_deletion':section}))

if __name__=='__main__':unittest.main()
