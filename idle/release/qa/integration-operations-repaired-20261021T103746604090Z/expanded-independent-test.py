"""Independent operations probes. Always run against a pinned isolated source copy."""
from contextlib import closing
from dataclasses import replace
import hashlib
import importlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(os.environ['OPERATIONS_REVIEW_SOURCE']).resolve()
sys.path.insert(0, str(ROOT))
from services.tideglass_service.api import Application
from services.tideglass_service.storage import Database, SCHEMA
from services.tideglass_service.health import (CheckError, OPTIONAL_SCHEMA, Thresholds,
    check_schema, health, open_existing, require_existing_database)
from services.tideglass_service.recovery import restore_drill

NOW = 1792576800

class IndependentOperations(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tideglass-qa-operations-')
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        self.path=self.folder/'service.sqlite3'
        self.database=Database(self.path)
        self.app=Application(self.database,clock=lambda:NOW)
        self.account=self.app.dispatch('POST','/v1/accounts',{'consent_cloud':True})[1]
        self.aid=self.account['account_id']
        with self.database.transaction() as db:
            db.execute('UPDATE accounts SET consent=1')
        self.thresholds=replace(Thresholds(),minimum_free_bytes=1,minimum_free_fraction=0)

    def report(self, **kwargs):
        return health(self.path,now=NOW,thresholds=self.thresholds,**kwargs)

    def check(self, name, report=None):
        return next(x for x in (report or self.report())['checks'] if x['name']==name)

    def events(self,n,*,failed=0,received=NOW,platform='ios'):
        with self.database.transaction() as db:
            for i in range(n):
                props={'platform':platform,'outcome':'failed' if i<failed else 'saved'}
                db.execute('INSERT INTO telemetry VALUES(?,?,?,?,?,?,?)',
                    (self.aid,str(uuid.uuid4()),str(uuid.uuid4()),'save_result',received,received,json.dumps({'properties':props})))

    def alternate_schema(self,name,script):
        path=self.folder/name
        with closing(sqlite3.connect(path,isolation_level=None)) as db:
            db.executescript(script)
            db.execute('INSERT INTO schema_version VALUES(1)')
            db.executemany('INSERT INTO flags VALUES(?,1)',[(x,) for x in ('cloud','purchases','ads','telemetry')])
        path.chmod(0o600)
        return path

    def assert_rejected(self,path):
        before=path.read_bytes()
        with self.assertRaises(CheckError):
            require_existing_database(path)
        self.assertEqual(before,path.read_bytes())

    def test_schema_missing_singleton_check_is_refused(self):
        path=self.alternate_schema('no-check.sqlite3',SCHEMA+OPTIONAL_SCHEMA.replace(' CHECK(id=1)',''))
        # This is a valid SQLite database, but not the singleton vault schema.
        with closing(sqlite3.connect(path)) as db:
            db.execute("INSERT INTO provider_vault_state VALUES(2,'unrecognized-epoch')")
            db.commit()
        self.assert_rejected(path)

    def test_schema_changed_primary_key_collation_is_refused(self):
        path=self.alternate_schema('nocase.sqlite3',SCHEMA.replace('id TEXT PRIMARY KEY, recovery_hash','id TEXT PRIMARY KEY COLLATE NOCASE, recovery_hash'))
        self.assert_rejected(path)

    def test_future_events_cannot_dilute_present_failure_alert(self):
        self.events(100,failed=2)
        self.assertEqual(self.check('critical_flows')['status'],'critical')
        self.events(200,received=NOW+86400)
        result=self.check('critical_flows')
        self.assertEqual(result['sample_count'],100,result)
        self.assertEqual(result['failure_count'],2,result)
        self.assertEqual(result['status'],'critical',result)

    def test_current_events_window_boundary_and_synthetic_exclusion(self):
        self.events(100,received=NOW-86400)
        self.events(17,failed=17,received=NOW-86401)
        self.events(9,failed=9,platform='test')
        result=self.check('critical_flows')
        self.assertEqual((result['sample_count'],result['failure_count'],result['excluded_synthetic_count']),(100,0,9))
        self.assertFalse(self.report()['release_gate_verified'])

    def test_actual_sql_deadline_interrupts_and_never_writes(self):
        before=self.path.read_bytes();start=time.monotonic()
        with self.assertRaises(CheckError):
            with open_existing(self.path,.015) as (db,_):
                db.execute('WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt WHERE x<1000000000) SELECT SUM(x) FROM cnt').fetchone()
        self.assertLess(time.monotonic()-start,1)
        self.assertEqual(before,self.path.read_bytes())
        with open_existing(self.path) as (db,_):
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM accounts')

    def test_cli_missing_all_commands_cannot_create_database(self):
        missing=self.folder/'absent-parent'/'absent.sqlite3'
        for command in [('health',),('restore-drill',),('dashboard',),('backup',str(self.folder/'never.sqlite3')),('prune',),('feature','cloud','off')]:
            with self.subTest(command=command):
                run=subprocess.run([sys.executable,'-m','services.tideglass_service.ops','--database',str(missing),*command],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(run.returncode,2,run.stderr)
                self.assertEqual(json.loads(run.stdout)['exit_code'],2)
                self.assertFalse(missing.parent.exists())
                self.assertFalse((self.folder/'never.sqlite3').exists())

    def test_restore_replay_deletes_all_provider_rows_without_changing_source(self):
        with self.database.transaction() as db:
            db.executescript(OPTIONAL_SCHEMA)
            db.execute('INSERT INTO purchases VALUES(?,?,?,?,?,?,?,?,?,?)',('google','qa-purchase',self.aid,'dev.tideglass.cosmetic.01','purchased',1,'qa','qa-verify',1,NOW))
            db.execute('INSERT INTO purchase_reconciliation VALUES(?,?,?,?)',('google','qa-purchase',NOW,3))
            db.execute('INSERT INTO ownership_leases VALUES(?,?,?)',(self.aid,19,NOW))
            db.execute('INSERT INTO provider_tokens VALUES(?,?,?,?,?)',('qa-purchase',self.aid,'qa-key',b'nonce',b'ciphertext'))
            db.execute('INSERT INTO provider_vault_state VALUES(1,?)',('qa-key',))
            db.execute('INSERT INTO provider_vault_key_bindings VALUES(?,?)',('qa-key',b'commitment'))
        self.events(2)
        backup=self.folder/'backup.sqlite3';self.database.backup(backup)
        before=backup.read_bytes()
        manifest=self.folder/'deletions.json';manifest.write_text(json.dumps({'version':1,'account_ids':[self.aid],'telemetry_opt_out_ids':[]}));manifest.chmod(0o600)
        recovery=importlib.import_module('services.tideglass_service.recovery')
        real_exercise=recovery._exercise; captured=[]
        def inspect(database,now,end):
            with database.read() as db:
                for table in ('accounts','sessions','purchases','purchase_reconciliation','ownership_leases','provider_tokens','telemetry'):
                    self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],0,table)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM provider_vault_key_bindings').fetchone()[0],1)
                self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())
            captured.append(database.path)
            return real_exercise(database,now,end)
        with patch.object(recovery,'_exercise',side_effect=inspect):
            result=restore_drill(backup,deletion_manifest=manifest,now=NOW)
        self.assertEqual(result['status'],'local_drill_passed',result)
        self.assertEqual(len(captured),1)
        self.assertFalse(captured[0].parent.exists())
        self.assertEqual(before,backup.read_bytes())
        self.assertFalse(result['eligible_for_live_restore'])
        self.assertFalse(result['deletion_replay']['complete_history_verified'])
        for secret in (self.aid,self.account['session_token'],self.account['recovery_code'],'ciphertext','qa-key'):
            self.assertNotIn(secret,json.dumps(result))

    def test_restore_tiny_deadline_removes_temporary_copy_and_preserves_source(self):
        recovery=importlib.import_module('services.tideglass_service.recovery')
        original=recovery.tempfile.TemporaryDirectory; folders=[]
        def observed(*args,**kwargs):
            result=original(*args,**kwargs);folders.append(Path(result.name));return result
        before=self.path.read_bytes()
        with patch.object(recovery.tempfile,'TemporaryDirectory',side_effect=observed):
            result=restore_drill(self.path,seconds=.000001,now=NOW)
        self.assertEqual(result['status'],'failed')
        self.assertFalse(result['eligible_for_live_restore'])
        self.assertEqual(before,self.path.read_bytes())
        self.assertTrue(folders)
        self.assertTrue(all(not folder.exists() for folder in folders))

    def test_backup_new_private_wal_aware_and_existing_destination_preserved(self):
        destination=self.folder/'new-backup.sqlite3'
        with closing(self.database.connect()) as keeper:
            keeper.execute('PRAGMA wal_autocheckpoint=0')
            keeper.execute('INSERT INTO operations(happened,kind,detail) VALUES(?,?,?)',(NOW,'qa-marker','{}'))
            self.assertTrue(Path(str(self.path)+'-wal').exists())
            self.database.backup(destination)
        self.assertEqual(destination.stat().st_mode&0o777,0o600)
        with open_existing(destination) as (db,_):
            self.assertEqual(db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],1)
        before=destination.read_bytes()
        with self.assertRaises(FileExistsError):self.database.backup(destination)
        self.assertEqual(before,destination.read_bytes())

    def test_deletion_manifest_adversarial_shapes_reject_without_private_output(self):
        good={'version':1,'account_ids':[],'telemetry_opt_out_ids':[]}
        values=[{**good,'account_ids':[self.aid,self.aid]},{**good,'account_ids':[{}]},
            {**good,'version':True},{**good,'extra':'private-sentinel'},
            {**good,'telemetry_opt_out_ids':[self.aid.upper()]},
            {**good,'account_ids':['private-sentinel']},
            {**good,'account_ids':[str(uuid.uuid4()) for _ in range(5001)]}]
        manifest=self.folder/'manifest.json'
        before=self.path.read_bytes()
        for value in values:
            manifest.write_text(json.dumps(value));manifest.chmod(0o600)
            result=restore_drill(self.path,deletion_manifest=manifest,now=NOW)
            self.assertEqual(result['status'],'failed')
            self.assertNotIn('private-sentinel',json.dumps(result))
        self.assertEqual(before,self.path.read_bytes())

    def test_schema_unrecognized_expression_index_is_refused(self):
        with self.database.transaction() as db:
            db.execute("CREATE INDEX unrecognized_expression ON accounts(json_extract(seed,'$'))")
        # The unrecognized index has executable expression semantics, not just
        # an innocent extra lookup path: an ordinary non-JSON seed now fails.
        with self.assertRaises(sqlite3.OperationalError):
            with self.database.transaction() as db:
                db.execute('UPDATE accounts SET seed=? WHERE id=?',('ordinary.harbor.seed',self.aid))
        self.assert_rejected(self.path)

    def test_schema_required_index_missing_is_refused(self):
        with self.database.transaction() as db:db.execute('DROP INDEX snapshot_parents')
        self.assert_rejected(self.path)

    def test_schema_required_index_changed_expression_is_refused(self):
        with self.database.transaction() as db:
            db.execute('DROP INDEX snapshot_parents')
            db.execute('CREATE INDEX snapshot_parents ON snapshots(account_id,lower(parent_id))')
        self.assert_rejected(self.path)

    def test_ddl_whitespace_case_comments_are_allowed_but_literals_preserved(self):
        altered=SCHEMA.replace('CREATE TABLE','create /* harmless comment */ table').replace('INTEGER','integer').replace('TEXT','text')
        path=self.alternate_schema('equivalent.sqlite3',altered)
        require_existing_database(path)
        health_module=importlib.import_module('services.tideglass_service.health')
        with closing(sqlite3.connect(':memory:')) as a, closing(sqlite3.connect(':memory:')) as b:
            a.execute("CREATE TABLE token_probe(x TEXT DEFAULT 'A/*not a comment*/B')")
            b.execute("CREATE TABLE token_probe(x TEXT DEFAULT 'AB')")
            self.assertNotEqual(health_module._table_definition(a,'token_probe'),health_module._table_definition(b,'token_probe'))

    def test_future_boundary_has_explicit_critical_timestamp_signal(self):
        self.events(100,received=NOW)
        self.events(1,received=NOW+1)
        result=self.report()
        self.assertEqual(self.check('critical_flows',result)['sample_count'],100)
        self.assertEqual(self.check('critical_flows',result)['status'],'ok')
        timestamp=self.check('telemetry_timestamps',result)
        self.assertEqual(timestamp['status'],'critical')
        self.assertEqual(timestamp['future_count'],1)
        self.assertEqual(result['exit_code'],2)

    def test_empty_optional_schema_and_full_valid_snapshot_still_restore(self):
        with self.database.transaction() as db:db.executescript(OPTIONAL_SCHEMA)
        require_existing_database(self.path)
        result=restore_drill(self.path,now=NOW)
        self.assertEqual(result['status'],'local_drill_passed',result)
        self.assertFalse(result['eligible_for_live_restore'])

if __name__=='__main__':unittest.main(verbosity=2)
