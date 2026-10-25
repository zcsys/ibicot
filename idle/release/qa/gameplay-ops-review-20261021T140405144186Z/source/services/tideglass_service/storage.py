from contextlib import contextmanager, closing
from pathlib import Path
import os
import sqlite3

SCHEMA = '''
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS accounts(
 id TEXT PRIMARY KEY, recovery_hash TEXT UNIQUE NOT NULL, created INTEGER NOT NULL,
 seed TEXT, utc_offset INTEGER, selected TEXT, generation INTEGER NOT NULL DEFAULT 0,
 consent INTEGER NOT NULL DEFAULT 0, consent_revision INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sessions(
 token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 created INTEGER NOT NULL, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots(
 account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 save_id TEXT NOT NULL, branch_id TEXT NOT NULL, revision INTEGER NOT NULL,
 parent_id TEXT, settled TEXT NOT NULL, digest TEXT NOT NULL, body TEXT NOT NULL,
 bytes INTEGER NOT NULL, received INTEGER NOT NULL,
 PRIMARY KEY(account_id,save_id)
);
CREATE INDEX IF NOT EXISTS snapshot_parents ON snapshots(account_id,parent_id);
CREATE TABLE IF NOT EXISTS purchases(
 platform TEXT NOT NULL, transaction_id TEXT NOT NULL, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 product_id TEXT NOT NULL, state TEXT NOT NULL, version INTEGER NOT NULL,
 authority TEXT NOT NULL, verification_id TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0,
 updated INTEGER NOT NULL, PRIMARY KEY(platform,transaction_id)
);
CREATE TABLE IF NOT EXISTS support_claims(
 account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 day_id INTEGER NOT NULL, slot INTEGER NOT NULL, route TEXT NOT NULL,
 receipt_id TEXT UNIQUE NOT NULL, source_id TEXT NOT NULL, authority TEXT NOT NULL,
 created INTEGER NOT NULL, delivered_save_id TEXT,
 PRIMARY KEY(account_id,day_id,slot)
);
CREATE TABLE IF NOT EXISTS ad_receipts(
 transaction_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 day_id INTEGER NOT NULL, slot INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS telemetry(
 account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 event_id TEXT NOT NULL, session_id TEXT NOT NULL, name TEXT NOT NULL,
 observed INTEGER NOT NULL, received INTEGER NOT NULL, body TEXT NOT NULL,
 PRIMARY KEY(account_id,event_id)
);
CREATE TABLE IF NOT EXISTS flags(name TEXT PRIMARY KEY, enabled INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS rate_limits(key TEXT PRIMARY KEY, window INTEGER NOT NULL, count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS operations(id INTEGER PRIMARY KEY AUTOINCREMENT, happened INTEGER NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL);
'''


class Database:
    def __init__(self, path, fault=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fault = fault
        # Inspect an existing database before applying even additive schema DDL.
        # Unknown/newer databases must be preserved for a compatible executable.
        if self.path.exists() and self.path.stat().st_size:
            with closing(sqlite3.connect(self.path)) as existing:
                tables = {row[0] for row in existing.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if 'schema_version' not in tables:
                    raise RuntimeError('Unknown service database; preserve it.')
                versions = existing.execute('SELECT version FROM schema_version').fetchall()
                if versions != [(1,)]:
                    raise RuntimeError('Unsupported service database; preserve it and use a compatible version.')
        with self.read() as db:
            db.executescript(SCHEMA)
            versions = db.execute('SELECT version FROM schema_version').fetchall()
            if not versions:
                db.execute('INSERT INTO schema_version VALUES(1)')
            elif len(versions) != 1 or versions[0][0] != 1:
                raise RuntimeError('Unsupported service database; preserve it and use a compatible version.')
            for name in ('cloud', 'purchases', 'ads', 'telemetry'):
                db.execute('INSERT OR IGNORE INTO flags VALUES(?,1)', (name,))
        os.chmod(self.path, 0o600)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA secure_delete=ON')
        return db

    @contextmanager
    def read(self):
        with closing(self.connect()) as db:
            yield db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            if self.fault:
                self.fault('before_commit')
            db.commit()
            if self.fault:
                self.fault('after_commit')
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def backup(self, destination):
        destination = Path(destination)
        if destination.exists():
            raise FileExistsError('Backup destination must be new.')
        handle = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(handle)
        with self.read() as source, closing(sqlite3.connect(destination)) as target:
            source.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Backup integrity check failed.')
        os.chmod(destination, 0o600)
        return str(destination)
