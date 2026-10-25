"""Verify a backup in a disposable, isolated copy; never replace a live database."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
import uuid

from .api import Application, ApiError
from .health import CheckError, check_schema, open_existing, private_existing
from .storage import Database


class DrillError(Exception):
    pass


def _deadline(end):
    if time.monotonic() >= end:
        raise DrillError('drill_deadline_exceeded')


def _inventory(db, tables, end):
    """Streaming whole-row digest; output contains no row contents or identities."""
    digest = hashlib.sha256()
    counts = {}
    total = 0
    for table in sorted(tables):
        digest.update(table.encode())
        count = 0
        for row in db.execute(f'SELECT * FROM "{table}" ORDER BY rowid'):
            _deadline(end)
            count += 1
            total += 1
            if total > 1000000:
                raise DrillError('drill_row_limit_exceeded')
            for cell in row:
                value = cell if isinstance(cell, bytes) else repr(cell).encode('utf-8')
                digest.update(type(cell).__name__.encode() + b':' + str(len(value)).encode() + b':' + value)
            digest.update(b'\n')
        counts[table] = count
    return {'sha256': digest.hexdigest(), 'table_rows': counts}


def _deletions(path):
    if path is None:
        return None
    path, info = private_existing(path)
    if info.st_size > 256 * 1024:
        raise DrillError('deletion_manifest_too_large')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DrillError('duplicate_deletion_manifest_field')
            result[key] = value
        return result
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=unique)
        if not isinstance(value, dict) or set(value) != {'version', 'account_ids', 'telemetry_opt_out_ids'} or type(value['version']) is not int or value['version'] != 1:
            raise ValueError()
        for key in ('account_ids', 'telemetry_opt_out_ids'):
            rows = value[key]
            if not isinstance(rows, list) or len(rows) > 5000 or len(set(rows)) != len(rows):
                raise ValueError()
            for item in rows:
                if not isinstance(item, str) or str(uuid.UUID(item)) != item:
                    raise ValueError()
        return value
    except (OSError, TypeError, ValueError, RecursionError):
        raise DrillError('invalid_deletion_manifest') from None


def _apply_deletions(database, manifest):
    if manifest is None:
        return {'status': 'unknown', 'code': 'no_external_deletion_manifest', 'complete_history_verified': False}
    deleted = opted_out = 0
    with database.transaction() as db:
        for aid in manifest['account_ids']:
            deleted += db.execute('DELETE FROM accounts WHERE id=?', (aid,)).rowcount
        for aid in manifest['telemetry_opt_out_ids']:
            opted_out += db.execute('UPDATE accounts SET consent=0,consent_revision=consent_revision+1 WHERE id=?', (aid,)).rowcount
            db.execute('DELETE FROM telemetry WHERE account_id=?', (aid,))
    return {'status': 'replayed_in_isolated_copy', 'requested_account_deletions': len(manifest['account_ids']),
            'deleted_accounts': deleted, 'requested_consent_withdrawals': len(manifest['telemetry_opt_out_ids']),
            'withdrawn_accounts': opted_out, 'complete_history_verified': False}


def _exercise(database, now, end):
    """Actual dispatch/storage behavior; synthetic ledger rows ONLY in temp copy.

    No verifier, signing key, provider request, server socket, or entitlement from
    this drill can enter the running service. The copy is deleted after the run.
    """
    app = Application(database, clock=lambda: now)
    checks = []
    def require(condition, code):
        _deadline(end)
        if not condition:
            raise DrillError(code)
        checks.append(code)
    def call(method, path, body=None, token=None):
        _deadline(end)
        return app.dispatch(method, path, body or {}, token)
    status, account = call('POST', '/v1/accounts', {'consent_cloud': True})
    require(status == 201, 'synthetic_account_creation')
    aid, token = account['account_id'], account['session_token']
    _, recovered = call('POST', '/v1/sessions', {'account_id': aid, 'recovery_code': account['recovery_code']})
    require(recovered['account_id'] == aid, 'synthetic_account_reauthentication')
    _, consent = call('GET', '/v1/telemetry/consent', token=token)
    require(consent['enabled'] is False, 'new_account_telemetry_off')
    # Enable optional switches only inside the isolated copy for this exercise.
    with database.transaction() as db:
        db.execute('UPDATE flags SET enabled=1')
        db.execute('UPDATE accounts SET seed=?,utc_offset=0 WHERE id=?', ('isolated.restore.fixture', aid))
        db.execute('INSERT INTO purchases VALUES(?,?,?,?,?,?,?,?,?,?)', ('google', str(uuid.uuid4()), aid, 'dev.tideglass.cosmetic.01', 'purchased', 1, 'isolated_restore_drill', str(uuid.uuid4()), 1, now))
    _, owned = call('GET', '/v1/entitlements', token=token)
    require([row['id'] for row in owned['entitlements']] == ['cosmetic.shop.01'], 'synthetic_fresh_ledger_read')
    with database.transaction() as db:
        db.execute('UPDATE purchases SET updated=? WHERE account_id=?', (now-86400, aid))
    require(call('GET', '/v1/entitlements', token=token)[1]['entitlements'] == [], 'stale_ledger_has_no_access')
    with database.transaction() as db:
        db.execute("UPDATE purchases SET updated=?,state='revoked' WHERE account_id=?", (now, aid))
    require(call('GET', '/v1/entitlements', token=token)[1]['entitlements'] == [], 'revoked_ledger_has_no_access')
    _, consent = call('PUT', '/v1/telemetry/consent', {'enabled': True}, token)
    event = {'id': str(uuid.uuid4()), 'session_id': str(uuid.uuid4()), 'name': 'session_start', 'observed_at': now, 'properties': {'platform': 'test', 'build': 'restore-drill'}}
    require(call('POST', '/v1/telemetry/events', {'consent_revision': consent['revision'], 'events': [event]}, token)[1]['accepted'] == 1, 'synthetic_consented_event')
    with database.transaction() as db:
        db.execute('UPDATE flags SET enabled=0')
    _, features = call('GET', '/v1/features', token=token)
    require(features['economy_changes_allowed'] is False and not any(features['features'].values()), 'optional_feature_disables')
    try:
        call('GET', '/v1/cloud', token=token)
    except ApiError as error:
        require(error.status == 503 and error.code == 'feature_unavailable', 'disabled_cloud_rejected')
    else:
        raise DrillError('disabled_cloud_not_rejected')
    require(call('GET', '/v1/entitlements', token=token)[0] == 200, 'ownership_read_survives_purchase_disable')
    require(call('POST', '/v1/support/claims', {'day_id': now//86400, 'slot': 0, 'route': 'briefing'}, token)[0] == 200, 'free_support_survives_ad_disable')
    require(call('PUT', '/v1/telemetry/consent', {'enabled': False}, token)[1]['deleted_existing_events'], 'withdrawal_survives_telemetry_disable')
    exported = call('GET', '/v1/account/export', token=token)[1]
    require(not exported['telemetry'] and 'recovery_hash' not in exported['account'] and 'session_token' not in exported['account'], 'export_survives_disables_and_hides_credentials')
    require(call('DELETE', '/v1/account', {'confirm_delete': True, 'recovery_code': account['recovery_code']}, token)[1]['deleted'], 'deletion_survives_disables')
    try:
        call('GET', '/v1/account/export', token=token)
    except ApiError as error:
        require(error.status == 401, 'deleted_session_rejected')
    else:
        raise DrillError('deleted_session_still_authorized')
    with database.read() as db:
        for table in ('sessions', 'purchases', 'support_claims', 'telemetry'):
            require(db.execute(f'SELECT COUNT(*) FROM {table} WHERE account_id=?', (aid,)).fetchone()[0] == 0, 'deletion_cascade_' + table)
        require(db.execute('PRAGMA foreign_key_check').fetchone() is None, 'post_drill_foreign_keys')
    return checks


def restore_drill(backup, *, deletion_manifest=None, seconds=30.0, now=None):
    if type(seconds) not in (int, float) or not 0 < seconds <= 60:
        raise ValueError('Drill deadline must be in (0,60] seconds.')
    now = int(time.time()) if now is None else now
    if type(now) is not int or now < 0:
        raise ValueError('UTC seconds required.')
    start = time.monotonic()
    end = start + seconds
    result = {'format': 'tideglass-isolated-restore-drill-v1', 'generated_at': now,
              'status': 'failed', 'exit_code': 2, 'source_opened_read_only': True,
              'live_database_replaced': False, 'eligible_for_live_restore': False,
              'provider_verification_performed': False, 'production_packages_accepted': False,
              'limits': ['Dispatch checks use a new synthetic account and ledger only in a deleted temporary copy.',
                         'Matching encrypted rows does not prove vault key availability or provider entitlement freshness.',
                         'Deletion/consent history completeness, session revocation, signed-lease high water and provider replay need a recovery authority before live activation.',
                         'No native save migration, season archive, actual purchase replay or hosted recovery was exercised.']}
    try:
        manifest = _deletions(deletion_manifest)
        with tempfile.TemporaryDirectory(prefix='tideglass-restore-drill-') as folder:
            os.chmod(folder, 0o700)
            restored = Path(folder)/'isolated.sqlite3'
            with open_existing(backup, seconds) as (source, _):
                tables = check_schema(source)
                bytes_required = source.execute('PRAGMA page_count').fetchone()[0] * source.execute('PRAGMA page_size').fetchone()[0]
                if bytes_required > 8*1024**3 or shutil.disk_usage(folder).free < bytes_required*2+64*1024**2:
                    raise DrillError('restore_size_or_space_limit')
                result['source_inventory'] = _inventory(source, tables, end)
                descriptor = os.open(restored, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(descriptor)
                with closing(sqlite3.connect(restored)) as target:
                    source.backup(target, pages=128, progress=lambda *args: _deadline(end), sleep=0.01)
            with open_existing(restored, max(0.001, end-time.monotonic())) as (copy, _):
                copied_tables = check_schema(copy)
                copied = _inventory(copy, copied_tables, end)
                if copied != result['source_inventory']:
                    raise DrillError('restored_inventory_mismatch')
            result['copied_inventory_matches'] = True
            database = Database(restored)
            result['deletion_replay'] = _apply_deletions(database, manifest)
            result['behavior_checks'] = _exercise(database, now, end)
            result['status'], result['exit_code'] = 'local_drill_passed', 0
        result['temporary_copy_removed'] = True
    except (CheckError, DrillError) as error:
        result['failure_code'] = str(error)
    except (OSError, sqlite3.Error, ValueError, ApiError):
        result['failure_code'] = 'isolated_drill_io_schema_or_behavior_failure'
    result['elapsed_seconds'] = round(time.monotonic()-start, 6)
    return result
