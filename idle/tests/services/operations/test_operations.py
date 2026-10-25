"""Actual SQLite/CLI faults; fixture telemetry is never a release cohort."""
from contextlib import closing
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

from services.tideglass_service.api import Application
from services.tideglass_service.health import (CheckError, OPTIONAL_SCHEMA, Thresholds,
    health, open_existing, require_existing_database)
from services.tideglass_service.recovery import restore_drill
from services.tideglass_service.storage import Database

ROOT = Path(__file__).resolve().parents[3]
NOW = 1792570000


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.path = self.folder/'service.sqlite3'
        self.database = Database(self.path)
        self.app = Application(self.database, clock=lambda: NOW)
        self.account = self.app.dispatch('POST', '/v1/accounts', {'consent_cloud': True})[1]
        self.aid = self.account['account_id']
        self.backup = self.folder/'backup.sqlite3'

    def backup_now(self):
        self.database.backup(self.backup)
        os.utime(self.backup, (NOW, NOW))

    def check(self, **kwargs):
        return health(self.path, now=NOW, **kwargs)

    def check_named(self, report, name):
        return next(check for check in report['checks'] if check['name'] == name)

    def purchase(self, *, platform='google', updated=NOW, acknowledged=0, state='purchased'):
        with self.database.transaction() as db:
            db.execute('INSERT INTO purchases VALUES(?,?,?,?,?,?,?,?,?,?)',
                (platform, str(uuid.uuid4()), self.aid, 'dev.tideglass.cosmetic.01', state, 1,
                 'test_fixture', str(uuid.uuid4()), acknowledged, updated))

    def events(self, count, *, failed=0, platform='ios', invalid=False):
        with self.database.transaction() as db:
            db.execute('UPDATE accounts SET consent=1 WHERE id=?', (self.aid,))
            for i in range(count):
                event = {'properties': {'platform': platform, 'outcome': 'failed' if i < failed else 'saved'}}
                db.execute('INSERT INTO telemetry VALUES(?,?,?,?,?,?,?)',
                    (self.aid, str(uuid.uuid4()), str(uuid.uuid4()), 'save_result', NOW, NOW,
                     '{broken' if invalid else json.dumps(event)))

    def worker(self):
        with self.database.transaction() as db:
            db.executescript(OPTIONAL_SCHEMA)

    def test_no_data_is_unknown_and_has_no_release_claim(self):
        result = self.check()
        self.assertEqual((result['status'], result['exit_code']), ('unknown', 3))
        self.assertFalse(result['release_gate_verified'])
        self.assertFalse(result['outbound_notifications_sent'])
        self.assertIsNone(self.check_named(result, 'critical_flows')['failure_fraction'])
        self.assertEqual(self.check_named(result, 'backup')['status'], 'unknown')

    def test_missing_path_does_not_create_directories_or_database(self):
        missing = self.folder/'wrong'/'missing.sqlite3'
        result = health(missing, now=NOW)
        self.assertEqual(result['exit_code'], 2)
        self.assertFalse(missing.parent.exists())
        self.assertEqual(self.check_named(result, 'database')['code'], 'database_missing')

    def test_empty_corrupt_and_nonprivate_are_rejected_without_repair(self):
        for content in (b'', b'not a sqlite database'):
            with self.subTest(content=content):
                broken = self.folder/'broken'
                broken.write_bytes(content); broken.chmod(0o600)
                result = health(broken, now=NOW)
                self.assertEqual(result['status'], 'critical')
                self.assertEqual(broken.read_bytes(), content)
        self.path.chmod(0o644)
        self.assertEqual(self.check_named(self.check(), 'database')['code'], 'database_not_private')

    def test_symlink_and_directory_rejected(self):
        link = self.folder/'link'; link.symlink_to(self.path)
        for path in (link, self.folder):
            self.assertEqual(self.check_named(health(path, now=NOW), 'database')['code'], 'database_not_regular')

    def test_unknown_newer_schema_is_not_migrated(self):
        with self.database.transaction() as db:
            db.execute('UPDATE schema_version SET version=2')
        before = self.path.read_bytes()
        result = self.check()
        self.assertEqual(self.check_named(result, 'database')['code'], 'unsupported_schema_version')
        self.assertEqual(before, self.path.read_bytes())
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT version FROM schema_version').fetchone()[0], 2)

    def test_incomplete_schema_and_unknown_extra_table_are_rejected(self):
        with self.database.transaction() as db:
            db.execute('DROP TABLE telemetry')
        self.assertEqual(self.check_named(self.check(), 'database')['code'], 'unsupported_or_incomplete_schema')
        with self.database.transaction() as db:
            db.execute('CREATE TABLE future_feature(secret TEXT)')
        self.assertEqual(self.check()['exit_code'], 2)

    def test_missing_foreign_key_constraint_is_rejected(self):
        with self.database.transaction() as db:
            db.execute('DROP TABLE telemetry')
            db.execute('CREATE TABLE telemetry(account_id TEXT NOT NULL,event_id TEXT NOT NULL,session_id TEXT NOT NULL,name TEXT NOT NULL,observed INTEGER NOT NULL,received INTEGER NOT NULL,body TEXT NOT NULL,PRIMARY KEY(account_id,event_id))')
        self.assertEqual(self.check_named(self.check(), 'database')['code'], 'unsupported_table_structure')

    def test_trigger_rejected_before_restore_behavior(self):
        with self.database.transaction() as db:
            db.execute('CREATE TRIGGER sabotage AFTER INSERT ON accounts BEGIN DELETE FROM accounts; END')
        self.assertEqual(self.check_named(self.check(), 'database')['code'], 'unsupported_database_objects')
        self.assertEqual(restore_drill(self.path, now=NOW)['failure_code'], 'unsupported_database_objects')

    def test_orphan_row_and_invalid_feature_state_are_unhealthy(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)', ('opaque', str(uuid.uuid4()), NOW, NOW+30)); db.commit()
        self.assertEqual(self.check_named(self.check(), 'database')['code'], 'database_foreign_key_failure')
        with self.database.transaction() as db:
            db.execute('DELETE FROM sessions WHERE token_hash=?', ('opaque',))
            db.execute("UPDATE flags SET enabled=3 WHERE name='ads'")
        self.assertEqual(self.check_named(self.check(), 'database')['code'], 'invalid_feature_configuration')

    def test_readonly_connection_refuses_mutation(self):
        with self.assertRaises(CheckError):
            with open_existing(self.path) as (db, _):
                db.execute('DELETE FROM accounts')
        with self.database.read() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0], 1)

    def test_tiny_deadline_and_invalid_thresholds_fail_closed(self):
        result = self.check(thresholds=Thresholds(database_seconds=0.0000001))
        self.assertEqual(result['exit_code'], 2)
        for kwargs in ({'database_seconds': float('nan')}, {'minimum_free_bytes': 0}, {'minimum_free_fraction': 2}, {'telemetry_max_rows': 1000001}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.check(thresholds=Thresholds(**kwargs))

    def test_pending_acknowledgement_exact_boundary_and_future(self):
        self.purchase(updated=NOW-600)
        check = self.check_named(self.check(), 'google_acknowledgements')
        self.assertEqual((check['status'], check['count'], check['oldest_age_seconds']), ('critical', 1, 600))
        with self.database.transaction() as db:
            db.execute('UPDATE purchases SET updated=?', (NOW-599,))
        self.assertEqual(self.check_named(self.check(), 'google_acknowledgements')['status'], 'warning')
        with self.database.transaction() as db:
            db.execute('UPDATE purchases SET updated=?', (NOW+1,))
        self.assertEqual(self.check_named(self.check(), 'ownership_observations')['status'], 'critical')

    def test_apple_completion_is_unknown_not_google_ack_alarm(self):
        self.purchase(platform='apple', updated=NOW-1000)
        result = self.check()
        self.assertEqual(self.check_named(result, 'google_acknowledgements')['count'], 0)
        self.assertEqual(self.check_named(result, 'apple_native_completion')['status'], 'unknown')

    def test_stale_ownership_and_reconciliation_queue(self):
        self.purchase(updated=NOW-86400, acknowledged=1)
        self.worker()
        with self.database.transaction() as db:
            db.execute('INSERT INTO purchase_reconciliation SELECT platform,transaction_id,?,2 FROM purchases', (NOW,))
        result = self.check()
        self.assertEqual(self.check_named(result, 'ownership_observations')['stale_count'], 1)
        self.assertEqual(self.check_named(result, 'reconciliation')['failing_count'], 1)
        self.assertEqual(self.check_named(result, 'reconciliation')['due_count'], 1)

    def test_actual_vault_and_signer_optional_layouts_are_recognized(self):
        import base64
        from services.tideglass_service.vault import TokenVault, VaultKeys
        from services.tideglass_service.leases import OwnershipSigner
        from services.tideglass_service.reconcile import reconcile
        keys = self.folder/'keys.json'
        keys.write_text(json.dumps({'version': 1, 'active_key_id': 'test', 'keys': {'test': base64.b64encode(os.urandom(32)).decode()}})); keys.chmod(0o600)
        TokenVault(self.database, VaultKeys(keys))
        signer_file = self.folder/'signer.json'
        signer_file.write_text(json.dumps({'version': 1, 'key_id': 'test', 'private_key': base64.b64encode(os.urandom(32)).decode()})); signer_file.chmod(0o600)
        signer = OwnershipSigner(signer_file, 'https://example.invalid')
        with self.database.transaction() as db:
            db.execute('UPDATE accounts SET seed=? WHERE id=?', ('test', self.aid))
            signer.issue(db, db.execute('SELECT * FROM accounts WHERE id=?', (self.aid,)).fetchone(), NOW)
        reconcile(self.app)
        self.assertEqual(self.check_named(self.check(), 'database')['status'], 'ok')
        self.backup_now()
        self.assertEqual(restore_drill(self.backup, now=NOW)['status'], 'local_drill_passed')

    def test_failure_streak_signals_critical_despite_fresh_observation(self):
        self.purchase(updated=NOW, acknowledged=0); self.worker()
        with self.database.transaction() as db:
            db.execute('INSERT INTO purchase_reconciliation SELECT platform,transaction_id,?,3 FROM purchases', (NOW+300,))
        result = self.check()
        self.assertEqual(self.check_named(result, 'google_acknowledgements')['status'], 'warning')
        self.assertEqual(self.check_named(result, 'reconciliation')['status'], 'critical')
        self.assertEqual(result['exit_code'], 2)

    def test_undelivered_support_exact_day_threshold(self):
        with self.database.transaction() as db:
            db.execute('INSERT INTO support_claims VALUES(?,?,?,?,?,?,?,?,?)', (self.aid, NOW//86400-1, 0, 'briefing', str(uuid.uuid4()), 'test', 'test', NOW-86400, None))
        result = self.check_named(self.check(), 'support_delivery')
        self.assertEqual((result['status'], result['oldest_age_seconds']), ('critical', 86400))

    def test_telemetry_excludes_synthetic_and_reports_bad_rows(self):
        self.events(100, failed=100, platform='test')
        result = self.check_named(self.check(), 'critical_flows')
        self.assertEqual((result['status'], result['sample_count'], result['excluded_synthetic_count']), ('unknown', 0, 100))
        self.events(1, invalid=True)
        self.assertEqual(self.check_named(self.check(), 'critical_flows')['invalid_count'], 1)

    def test_telemetry_failure_threshold_low_sample_and_scan_limit(self):
        self.events(1, failed=1)
        result = self.check_named(self.check(), 'critical_flows')
        self.assertEqual((result['status'], result['sufficient_samples']), ('warning', False))
        self.events(99)
        result = self.check_named(self.check(), 'critical_flows')
        self.assertEqual((result['status'], result['failure_fraction']), ('critical', 0.01))
        result = self.check_named(self.check(thresholds=Thresholds(telemetry_max_rows=50)), 'critical_flows')
        self.assertEqual((result['status'], result['code']), ('unknown', 'scan_limit_exceeded'))

    def test_consent_violation_is_critical(self):
        self.events(1)
        with self.database.transaction() as db:
            db.execute('UPDATE accounts SET consent=0')
        self.assertEqual(self.check_named(self.check(), 'telemetry_consent')['status'], 'critical')

    def test_fully_observed_local_health_and_warning_exit(self):
        self.worker(); self.events(100); self.backup_now()
        result = self.check(backup=self.backup)
        self.assertEqual((result['status'], result['exit_code']), ('ok', 0))
        self.purchase(updated=NOW-1)
        result = self.check(backup=self.backup)
        self.assertEqual((result['status'], result['exit_code']), ('warning', 1))
        self.assertFalse(result['release_gate_verified'])

    def test_backup_freshness_samefile_missing_and_modified_clock(self):
        self.backup_now()
        self.assertEqual(self.check_named(self.check(backup=self.backup), 'backup')['status'], 'ok')
        os.utime(self.backup, (NOW-86401, NOW-86401))
        self.assertEqual(self.check_named(self.check(backup=self.backup), 'backup')['status'], 'critical')
        os.utime(self.backup, (NOW+1, NOW+1))
        self.assertEqual(self.check_named(self.check(backup=self.backup), 'backup')['status'], 'critical')
        self.assertEqual(self.check_named(self.check(backup=self.path), 'backup')['code'], 'backup_is_live_database')
        missing = self.folder/'absent'
        self.assertEqual(self.check_named(self.check(backup=missing), 'backup')['status'], 'critical')
        self.assertFalse(missing.exists())

    def test_disk_space_threshold_and_unavailable(self):
        usage = shutil_usage(total=1000, used=999, free=1)
        with patch('services.tideglass_service.health.shutil.disk_usage', return_value=usage):
            self.assertEqual(self.check_named(self.check(), 'disk')['status'], 'critical')
        with patch('services.tideglass_service.health.shutil.disk_usage', side_effect=OSError('sensitive path')):
            result = self.check()
            self.assertEqual(self.check_named(result, 'disk')['status'], 'unknown')
            self.assertNotIn('sensitive', json.dumps(result))

    def test_restore_preserves_source_and_removes_temporary_copy(self):
        self.purchase(); self.events(2); self.worker(); self.backup_now()
        before = hashlib.sha256(self.backup.read_bytes()).hexdigest()
        result = restore_drill(self.backup, now=NOW)
        self.assertEqual(result['status'], 'local_drill_passed', result)
        self.assertTrue(result['copied_inventory_matches'])
        self.assertTrue(result['temporary_copy_removed'])
        self.assertEqual(len(result['behavior_checks']), 20)
        self.assertEqual(before, hashlib.sha256(self.backup.read_bytes()).hexdigest())
        self.assertEqual(result['source_inventory']['table_rows']['accounts'], 1)
        self.assertFalse(result['eligible_for_live_restore'])
        self.assertFalse(result['provider_verification_performed'])
        output = json.dumps(result)
        for secret in (self.account['recovery_code'], self.account['session_token'], self.aid):
            self.assertNotIn(secret, output)

    def test_restore_reads_committed_wal_not_just_main_file(self):
        # Keep a connection alive so committed data remains in WAL during copy.
        with closing(self.database.connect()) as keeper:
            keeper.execute('PRAGMA wal_autocheckpoint=0')
            keeper.execute("INSERT INTO operations(happened,kind,detail) VALUES(?, 'test', '{}')", (NOW,))
            self.assertTrue(Path(str(self.path)+'-wal').exists())
            result = restore_drill(self.path, now=NOW)
            self.assertEqual(result['status'], 'local_drill_passed', result)
            self.assertEqual(result['source_inventory']['table_rows']['operations'], 1)

    def test_restore_missing_corrupt_newer_and_low_space_fail_without_touch(self):
        missing = self.folder/'missing'
        self.assertEqual(restore_drill(missing, now=NOW)['failure_code'], 'database_missing')
        self.assertFalse(missing.exists())
        with self.database.transaction() as db:
            db.execute('UPDATE schema_version SET version=2')
        self.assertEqual(restore_drill(self.path, now=NOW)['failure_code'], 'unsupported_schema_version')
        with self.database.transaction() as db:
            db.execute('UPDATE schema_version SET version=1')
        with patch('services.tideglass_service.recovery.shutil.disk_usage', return_value=shutil_usage(1000, 999, 1)):
            self.assertEqual(restore_drill(self.path, now=NOW)['failure_code'], 'restore_size_or_space_limit')

    def test_restore_deletion_and_optout_replay_is_isolated_and_incomplete(self):
        self.events(1)
        second = self.app.dispatch('POST', '/v1/accounts', {'consent_cloud': True})[1]
        self.backup_now()
        manifest = self.folder/'deletions.json'
        manifest.write_text(json.dumps({'version': 1, 'account_ids': [second['account_id']], 'telemetry_opt_out_ids': [self.aid]})); manifest.chmod(0o600)
        result = restore_drill(self.backup, deletion_manifest=manifest, now=NOW)
        self.assertEqual(result['status'], 'local_drill_passed', result)
        self.assertEqual(result['deletion_replay']['deleted_accounts'], 1)
        self.assertEqual(result['deletion_replay']['withdrawn_accounts'], 1)
        self.assertFalse(result['deletion_replay']['complete_history_verified'])
        with open_existing(self.backup) as (db, _):
            self.assertEqual(db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0], 2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM telemetry').fetchone()[0], 1)

    def test_restore_deletion_manifest_validation(self):
        manifest = self.folder/'manifest.json'
        for value in ('{"version":1,"version":1,"account_ids":[],"telemetry_opt_out_ids":[]}', '{"version":1,"account_ids":["secret"],"telemetry_opt_out_ids":[]}', '[]'):
            manifest.write_text(value); manifest.chmod(0o600)
            result = restore_drill(self.path, deletion_manifest=manifest, now=NOW)
            self.assertEqual(result['status'], 'failed')
            self.assertNotIn('secret', json.dumps(result))
        manifest.chmod(0o644)
        self.assertEqual(restore_drill(self.path, deletion_manifest=manifest, now=NOW)['failure_code'], 'database_not_private')

    def test_cli_health_and_restore_json_exit_and_wrong_old_command_path(self):
        missing = self.folder/'does-not-exist'
        for command in ('health', 'dashboard', 'prune'):
            result = subprocess.run([sys.executable, '-m', 'services.tideglass_service.ops', '--database', str(missing), command], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stdout)['exit_code'], 2)
            self.assertFalse(missing.exists())
        self.backup_now()
        result = subprocess.run([sys.executable, '-m', 'services.tideglass_service.ops', '--database', str(self.backup), 'restore-drill'], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'local_drill_passed')


from collections import namedtuple
shutil_usage = namedtuple('usage', 'total used free')

if __name__ == '__main__':
    unittest.main()
