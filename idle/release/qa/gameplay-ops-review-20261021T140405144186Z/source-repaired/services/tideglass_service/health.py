"""Bounded local checks. No network, scheduler, repair, or release acceptance."""
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import time

from .storage import SCHEMA

# Optional tables are added by existing provider components, all at schema 1.
# Compare actual structural metadata, not just the integer version marker.
OPTIONAL_SCHEMA = '''
CREATE TABLE purchase_reconciliation(platform TEXT NOT NULL,transaction_id TEXT NOT NULL,next_attempt INTEGER NOT NULL,failures INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(platform,transaction_id),FOREIGN KEY(platform,transaction_id) REFERENCES purchases(platform,transaction_id) ON DELETE CASCADE);
CREATE TABLE ownership_leases(account_id TEXT PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,revision INTEGER NOT NULL,issued_at INTEGER NOT NULL);
CREATE TABLE provider_vault_state(id INTEGER PRIMARY KEY CHECK(id=1),active_key_id TEXT NOT NULL);
CREATE TABLE provider_tokens(transaction_id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,key_id TEXT NOT NULL,nonce BLOB NOT NULL,ciphertext BLOB NOT NULL,UNIQUE(key_id,nonce));
CREATE TABLE provider_vault_key_bindings(key_id TEXT PRIMARY KEY,commitment BLOB);
'''
EXIT_CODES = {'ok': 0, 'warning': 1, 'critical': 2, 'unknown': 3}


class CheckError(Exception):
    """Fixed error codes only: never emit DB contents, paths, or exceptions."""


@dataclass(frozen=True)
class Thresholds:
    database_seconds: float = 5.0
    minimum_free_bytes: int = 1024**3
    minimum_free_fraction: float = 0.05
    backup_max_age_seconds: int = 86400
    acknowledgement_age_seconds: int = 600
    delivery_age_seconds: int = 86400
    reconciliation_failure_streak: int = 3
    telemetry_window_seconds: int = 86400
    telemetry_max_rows: int = 100000
    critical_flow_failure_fraction: float = 0.01
    critical_flow_min_samples: int = 100

    def validate(self):
        if type(self.database_seconds) not in (float, int) or not math.isfinite(self.database_seconds) or not 0 < self.database_seconds <= 60:
            raise ValueError('Invalid bounded database deadline.')
        for value in (self.minimum_free_bytes, self.backup_max_age_seconds,
                      self.acknowledgement_age_seconds, self.delivery_age_seconds, self.reconciliation_failure_streak,
                      self.telemetry_window_seconds, self.telemetry_max_rows,
                      self.critical_flow_min_samples):
            if type(value) is not int or value <= 0:
                raise ValueError('Positive integer threshold required.')
        for value in (self.minimum_free_fraction, self.critical_flow_failure_fraction):
            if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Threshold fraction must be in [0,1].')
        if self.telemetry_max_rows > 1000000:
            raise ValueError('Telemetry scan limit is at most one million rows.')
        return self


def private_existing(path):
    path = Path(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise CheckError('database_missing') from None
    except OSError:
        raise CheckError('database_unreadable') from None
    if not stat.S_ISREG(info.st_mode):
        raise CheckError('database_not_regular')
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise CheckError('database_not_private')
    if info.st_size == 0:
        raise CheckError('database_empty')
    return path, info


@contextmanager
def open_existing(path, seconds=5.0):
    """Read-only WAL-aware SQLite connection; deliberately never Database(path)."""
    path, before = private_existing(path)
    deadline = time.monotonic() + seconds
    try:
        with closing(sqlite3.connect(path.absolute().as_uri() + '?mode=ro', uri=True,
                                     timeout=min(seconds, 0.25), isolation_level=None)) as db:
            after = path.lstat()
            if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
                raise CheckError('database_changed_while_opening')
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA trusted_schema=OFF')
            db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
            db.execute('BEGIN')
            yield db, deadline
            if time.monotonic() >= deadline:
                raise CheckError('database_deadline_exceeded')
            db.rollback()
    except sqlite3.Error:
        raise CheckError('database_deadline_or_sqlite_failure') from None
    except OSError:
        raise CheckError('database_unreadable') from None


def _layout(db, table):
    # Names come from the fixed expected schema, never SQL supplied by the DB.
    columns = [tuple(row)[1:] for row in db.execute(f'PRAGMA table_xinfo("{table}")')]
    foreign = sorted(tuple(row)[2:] for row in db.execute(f'PRAGMA foreign_key_list("{table}")'))
    indexes = []
    for row in db.execute(f'PRAGMA index_list("{table}")'):
        if row[2]:
            name = row[1].replace('"', '""')
            indexes.append((row[3], row[4], tuple(tuple(x)[1:] for x in db.execute(f'PRAGMA index_info("{name}")'))))
    return columns, foreign, sorted(indexes)


_SQL_TOKENS = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`(?:``|[^`])*`|\[[^\]]*\]|--[^\n]*|/\*[\s\S]*?\*/|[A-Za-z_][A-Za-z_0-9]*|\d+|[^\s]")


def _sql_definition(db, kind, name):
    """Conservative DDL equality, including semantics omitted by PRAGMAs.

    Only whitespace, SQL comments and unquoted keyword/identifier case vary.
    Quoted literals/identifiers are preserved; unknown equivalent spellings
    require review rather than silently accepting a changed CHECK/collation.
    """
    row = db.execute("SELECT sql FROM sqlite_master WHERE type=? AND name=?", (kind, name)).fetchone()
    if row is None or not isinstance(row[0], str):
        raise CheckError('missing_schema_definition')
    return tuple(token if token[0] in "'\"`[" else token.casefold()
                 for token in _SQL_TOKENS.findall(row[0])
                 if not token.startswith(('--', '/*')))


def _table_definition(db, table):
    return _sql_definition(db, 'table', table)


def _explicit_indexes(db):
    names = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT GLOB 'sqlite_*'")]
    return {name: _sql_definition(db, 'index', name) for name in names}


def check_schema(db):
    objects = db.execute("SELECT type,name FROM sqlite_master WHERE name NOT GLOB 'sqlite_*'").fetchall()
    if any(row['type'] not in ('table', 'index') for row in objects):
        raise CheckError('unsupported_database_objects')
    actual = {row['name'] for row in objects if row['type'] == 'table'}
    with closing(sqlite3.connect(':memory:')) as expected:
        expected.executescript(SCHEMA)
        base = {row[0] for row in expected.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'")}
        expected.executescript(OPTIONAL_SCHEMA)
        known = {row[0] for row in expected.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*'")}
        if not base <= actual or not actual <= known:
            raise CheckError('unsupported_or_incomplete_schema')
        if _explicit_indexes(db) != _explicit_indexes(expected):
            raise CheckError('unsupported_or_missing_indexes')
        for table in actual:
            if (_layout(db, table) != _layout(expected, table)
                    or _table_definition(db, table) != _table_definition(expected, table)):
                raise CheckError('unsupported_table_structure')
    if [tuple(row) for row in db.execute('SELECT version FROM schema_version')] != [(1,)]:
        raise CheckError('unsupported_schema_version')
    flags = {row[0]: row[1] for row in db.execute('SELECT name,enabled FROM flags')}
    if set(flags) != {'cloud', 'purchases', 'ads', 'telemetry'} or any(value not in (0, 1) for value in flags.values()):
        raise CheckError('invalid_feature_configuration')
    if [row[0] for row in db.execute('PRAGMA integrity_check(1)')] != ['ok']:
        raise CheckError('database_integrity_failure')
    if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
        raise CheckError('database_foreign_key_failure')
    return actual


def require_existing_database(path, seconds=5.0):
    with open_existing(path, seconds) as (db, _):
        return check_schema(db)


def _check(name, status, code, **data):
    return {'name': name, 'status': status, 'code': code, **data}


def health(database, *, backup=None, thresholds=None, now=None):
    thresholds = (thresholds or Thresholds()).validate()
    now = int(time.time()) if now is None else now
    if type(now) is not int or now < 0:
        raise ValueError('UTC seconds required.')
    checks = []
    try:
        with open_existing(database, thresholds.database_seconds) as (db, _):
            tables = check_schema(db)
            checks.append(_check('database', 'ok', 'schema_1_integrity_and_foreign_keys_verified'))
            for name, sql, age_limit in (
                ('google_acknowledgements', "SELECT COUNT(*),MIN(updated) FROM purchases WHERE platform='google' AND state='purchased' AND acknowledged=0", thresholds.acknowledgement_age_seconds),
                ('support_delivery', 'SELECT COUNT(*),MIN(created) FROM support_claims WHERE delivered_save_id IS NULL', thresholds.delivery_age_seconds),
            ):
                count, oldest = db.execute(sql).fetchone()
                age = now - oldest if oldest is not None else None
                status = 'critical' if count and age is not None and age >= age_limit else ('warning' if count else 'ok')
                if age is not None and age < 0:
                    status = 'critical'
                checks.append(_check(name, status, 'pending_age_threshold' if count else 'no_pending_rows', count=count, oldest_age_seconds=age, critical_age_seconds=age_limit, age_basis='last_provider_observation' if name == 'google_acknowledgements' else 'claim_creation'))
            apple = db.execute("SELECT COUNT(*) FROM purchases WHERE platform='apple' AND state='purchased' AND acknowledged=0").fetchone()[0]
            checks.append(_check('apple_native_completion', 'unknown' if apple else 'ok', 'no_server_completion_observation' if apple else 'no_pending_rows', count=apple))
            stale, future = db.execute("SELECT COALESCE(SUM(updated<=?),0),COALESCE(SUM(updated>?),0) FROM purchases WHERE state='purchased'", (now-86400, now)).fetchone()
            checks.append(_check('ownership_observations', 'critical' if future else ('warning' if stale else 'ok'), 'provider_freshness_counts', stale_count=stale, future_count=future, freshness_seconds=86400))
            if 'purchase_reconciliation' in tables:
                failed, overdue, maximum = db.execute('SELECT COALESCE(SUM(failures>0),0),COALESCE(SUM(next_attempt<=?),0),COALESCE(MAX(failures),0) FROM purchase_reconciliation', (now,)).fetchone()
                checks.append(_check('reconciliation', 'critical' if maximum >= thresholds.reconciliation_failure_streak else ('warning' if failed or overdue else 'ok'), 'durable_queue_counts', failing_count=failed, due_count=overdue, maximum_failure_streak=maximum, critical_failure_streak=thresholds.reconciliation_failure_streak))
            else:
                checks.append(_check('reconciliation', 'unknown', 'no_worker_table'))
            consent_rows = db.execute('SELECT COUNT(*) FROM telemetry t JOIN accounts a ON a.id=t.account_id WHERE a.consent=0').fetchone()[0]
            checks.append(_check('telemetry_consent', 'critical' if consent_rows else 'ok', 'events_without_current_consent', count=consent_rows))
            future_events = db.execute('SELECT COUNT(*) FROM telemetry WHERE received>?', (now,)).fetchone()[0]
            checks.append(_check('telemetry_timestamps', 'critical' if future_events else 'ok',
                                 'future_server_receipt_timestamps', count=future_events))
            events = db.execute("SELECT body FROM telemetry WHERE received>=? AND received<=? AND name IN ('save_result','resume_result') ORDER BY received LIMIT ?", (now-thresholds.telemetry_window_seconds, now, thresholds.telemetry_max_rows+1)).fetchall()
            if len(events) > thresholds.telemetry_max_rows:
                checks.append(_check('critical_flows', 'unknown', 'scan_limit_exceeded'))
            else:
                valid = failures = invalid = synthetic = 0
                for row in events:
                    try:
                        props = json.loads(row[0])['properties']
                        if props.get('platform') == 'test':
                            synthetic += 1
                            continue
                        outcome = props.get('outcome')
                        if props.get('platform') not in ('ios', 'android', 'macos') or outcome not in ('failed', 'saved', 'settled'):
                            invalid += 1
                        else:
                            valid += 1
                            failures += outcome == 'failed'
                    except (KeyError, TypeError, ValueError, AttributeError, RecursionError):
                        invalid += 1
                fraction = failures/valid if valid else None
                status = 'unknown' if valid < thresholds.critical_flow_min_samples or invalid else ('critical' if fraction >= thresholds.critical_flow_failure_fraction else 'ok')
                if failures and status == 'unknown':
                    # Even sparse known failures deserve an operator signal;
                    # insufficiency remains explicit in the sample fields.
                    status = 'warning'
                checks.append(_check('critical_flows', status, 'retained_consented_event_sample', sample_count=valid, failure_count=failures, failure_fraction=fraction, invalid_count=invalid, excluded_synthetic_count=synthetic, sufficient_samples=valid>=thresholds.critical_flow_min_samples, window_seconds=thresholds.telemetry_window_seconds))
    except CheckError as error:
        checks.append(_check('database', 'critical', str(error)))
    try:
        usage = shutil.disk_usage(Path(database).absolute().parent)
        fraction = usage.free/usage.total if usage.total else 0
        low = usage.free < thresholds.minimum_free_bytes or fraction < thresholds.minimum_free_fraction
        checks.append(_check('disk', 'critical' if low else 'ok', 'filesystem_free_space', free_bytes=usage.free, free_fraction=fraction))
    except OSError:
        checks.append(_check('disk', 'unknown', 'disk_usage_unavailable'))
    if backup is None:
        checks.append(_check('backup', 'unknown', 'backup_not_specified'))
    else:
        try:
            path, info = private_existing(backup)
            if os.path.samefile(path, database):
                raise CheckError('backup_is_live_database')
            require_existing_database(path, thresholds.database_seconds)
            age = now-int(info.st_mtime)
            checks.append(_check('backup', 'critical' if age < 0 or age > thresholds.backup_max_age_seconds else 'ok', 'integrity_and_filesystem_mtime_only', age_seconds=age, maximum_age_seconds=thresholds.backup_max_age_seconds, creation_time_authenticated=False))
        except (CheckError, OSError) as error:
            checks.append(_check('backup', 'critical', str(error) if isinstance(error, CheckError) else 'backup_unavailable'))
    statuses = {check['status'] for check in checks}
    status = next(value for value in ('critical', 'unknown', 'warning', 'ok') if value in statuses)
    return {'format': 'tideglass-local-health-v1', 'generated_at': now, 'status': status,
            'exit_code': EXIT_CODES[status], 'thresholds': asdict(thresholds), 'checks': checks,
            'signals': [{'check': row['name'], 'status': row['status'], 'code': row['code']} for row in checks if row['status'] != 'ok'],
            'outbound_notifications_sent': False, 'release_gate_verified': False,
            'limits': ['Local database state only; no endpoint, provider or scheduler availability proof.',
                       'Telemetry covers retained consenting accounts, not all installs or native crash reporting.',
                       'Backup mtime can be changed; encrypted storage, offsite retention and deletion replay are not verified.']}
