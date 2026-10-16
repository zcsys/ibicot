"""Persistent local player identity, employment, wallet ledger and ownership.

SQLite is authoritative for people; the economy checkpoint owns physical assets.
All amounts in the personal ledger are integer cents. A cookie is a local device
credential, not a multiplayer account/login system.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import uuid

from ..core import model as M


def database_path():
    return Path(os.environ.get('ECONOMY_PLAYERS_DB', 'data/players.sqlite3'))


@contextmanager
def transaction():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    if db.execute('PRAGMA user_version').fetchone()[0] not in (0, 1):
        db.close()
        raise ValueError('Unsupported player database schema version.')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS world_catalog (
            world TEXT PRIMARY KEY, catalog_revision TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY, name TEXT NOT NULL,
            wallet_cents INTEGER NOT NULL DEFAULT 0 CHECK(wallet_cents >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, player_id TEXT NOT NULL REFERENCES players(id));
        CREATE TABLE IF NOT EXISTS employment (
            player_id TEXT PRIMARY KEY REFERENCES players(id),
            employer TEXT NOT NULL, state_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY, player_id TEXT NOT NULL REFERENCES players(id),
            kind TEXT NOT NULL, amount_cents INTEGER NOT NULL,
            balance_cents INTEGER NOT NULL CHECK(balance_cents >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS ownership (
            world TEXT NOT NULL, tier TEXT NOT NULL, company_id INTEGER NOT NULL,
            player_id TEXT NOT NULL REFERENCES players(id), paid_cents INTEGER NOT NULL,
            price REAL NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(world, tier, company_id));
        PRAGMA user_version=1;
    ''')
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT OR IGNORE INTO world_catalog VALUES (?,?)', (world_key(), str(M.CATALOG_REVISION)))
        revision = db.execute('SELECT catalog_revision FROM world_catalog WHERE world=?', (world_key(),)).fetchone()[0]
        if revision != str(M.CATALOG_REVISION):
            raise ValueError('The player database requires a catalog migration before use.')
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def world_key():
    # A deployment names its shared world. Alternate experiments must use a
    # different DB/world key; ownership never comes from the demo state.
    return os.environ.get('ECONOMY_WORLD_ID', 'local')


def identity(db, token, create):
    digest = hashlib.sha256((token or '').encode()).hexdigest()
    row = db.execute('SELECT p.* FROM players p JOIN sessions s ON p.id=s.player_id WHERE token_hash=?', (digest,)).fetchone()
    if row:
        return dict(row), None
    if not create:
        raise ValueError('Your player session has expired. Reload to reconnect.')
    token = secrets.token_urlsafe(32)
    pid = str(uuid.uuid4())
    db.execute('INSERT INTO players(id,name) VALUES (?,?)', (pid, 'New arrival'))
    db.execute('INSERT INTO sessions VALUES (?,?)', (hashlib.sha256(token.encode()).hexdigest(), pid))
    return {'id': pid, 'name': 'New arrival', 'wallet_cents': 0}, token


def post_money(db, pid, kind, amount):
    cents = round(amount * 100)
    row = db.execute('SELECT wallet_cents FROM players WHERE id=?', (pid,)).fetchone()
    balance = row[0] + cents
    if balance < 0:
        raise ValueError('Insufficient personal funds.')
    db.execute('UPDATE players SET wallet_cents=? WHERE id=?', (balance, pid))
    db.execute('INSERT INTO ledger(player_id,kind,amount_cents,balance_cents) VALUES (?,?,?,?)', (pid, kind, cents, balance))


def load_employment(db, pid):
    row = db.execute('SELECT state_json FROM employment WHERE player_id=?', (pid,)).fetchone()
    return json.loads(row[0]) if row else None


def save_employment(db, pid, state):
    state = dict(state)
    state.pop('wallet', None)
    db.execute('INSERT INTO employment VALUES (?,?,?) ON CONFLICT(player_id) DO UPDATE SET state_json=excluded.state_json',
               (pid, 'Meridian Works', json.dumps(state, allow_nan=False)))


def sync_ownership(rt, db=None):
    if db is None:
        with transaction() as connection:
            sync_ownership(rt, connection)
        return
    for row in db.execute('SELECT * FROM ownership WHERE world=?', (world_key(),)):
        cid = row['company_id']
        if row['tier'] != 'T1' or not 0 <= cid < M.N1 or not rt.world.t1Operates[cid * M.NP]:
            raise ValueError('The player database belongs to an incompatible company catalog.')
        rt.world.t1Controller[cid] = rt.controller[cid] = 1
        rt.world.playerPrice[cid * M.NP] = row['price']
        rt.world.t1Price[cid * M.NP] = row['price']
        rt.playerPrices[cid][M.PRODUCTS[0]['code']] = row['price']
