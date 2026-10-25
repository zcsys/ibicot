"""Account-bound AES-256-GCM provider token storage; keys never enter SQLite."""
from contextlib import contextmanager
from contextvars import ContextVar
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .verification import VerificationUnavailable

KEY_ID = re.compile(r'^[A-Za-z0-9._-]{1,64}$')
TRANSACTION = re.compile(r'^[0-9a-f]{64}$')


def private_file(path, maximum=65536):
    """Reject symlinks, non-regular/shared files, wrong owner and oversized keys."""
    fd = os.open(Path(path), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or not 0 < info.st_size <= maximum:
            raise ValueError('Private configuration must be an owner-only regular file.')
        with os.fdopen(fd, 'rb', closefd=False) as source:
            return source.read(maximum + 1)
    finally:
        os.close(fd)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('Duplicate configuration field.')
        result[key] = value
    return result


class VaultKeys:
    def __init__(self, path):
        value = json.loads(private_file(path, 16384), object_pairs_hook=unique_object)
        if set(value) != {'version', 'active_key_id', 'keys'} or value['version'] != 1 or not isinstance(value['keys'], dict) or not 1 <= len(value['keys']) <= 16:
            raise ValueError('Invalid vault key file.')
        self.active = value['active_key_id']
        self.keys = {}
        for key_id, encoded in value['keys'].items():
            if not KEY_ID.fullmatch(key_id): raise ValueError('Invalid vault key identity.')
            key = base64.b64decode(encoded, validate=True)
            if len(key) != 32: raise ValueError('AES-256 key required.')
            self.keys[key_id] = key
        if self.active not in self.keys: raise ValueError('Active vault key is missing.')
        if len(set(self.keys.values())) != len(self.keys): raise ValueError('Each key identity requires distinct key material.')


class TokenVault:
    def __init__(self, database, keys, *, rotation=False):
        self.db, self.keys = database, keys
        self._connection = ContextVar('vault_connection', default=None)
        with self.db.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS provider_vault_state(id INTEGER PRIMARY KEY CHECK(id=1),active_key_id TEXT NOT NULL)')
            db.execute('''CREATE TABLE IF NOT EXISTS provider_tokens(
              transaction_id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
              key_id TEXT NOT NULL, nonce BLOB NOT NULL, ciphertext BLOB NOT NULL,
              UNIQUE(key_id,nonce))''')
            # Nonsecret commitments persist even when all account tokens are
            # deleted. A key ID can never silently identify different material.
            # NULL means a legacy empty epoch was explicitly retired: its old
            # material cannot be proven, so that identity must never be reused.
            db.execute('CREATE TABLE IF NOT EXISTS provider_vault_key_bindings(key_id TEXT PRIMARY KEY,commitment BLOB)')
            state = db.execute('SELECT active_key_id FROM provider_vault_state WHERE id=1').fetchone()
            needed = {row[0] for row in db.execute('SELECT DISTINCT key_id FROM provider_tokens')}
            if not needed <= keys.keys.keys():
                raise ValueError('Vault decryption keys missing; preserve database and recover key file.')
            if state is None:
                if needed: raise ValueError('Vault epoch missing; recover the intact database.')
                db.execute('INSERT INTO provider_vault_state VALUES(1,?)', (keys.active,))
                self._expected_active = keys.active
            else:
                self._expected_active = state[0]
                if state[0] != keys.active and not rotation:
                    raise ValueError('Vault active key differs; run explicit rotation with old and new keys available.')
            bindings = {row['key_id']: row['commitment'] for row in db.execute('SELECT * FROM provider_vault_key_bindings')}
            for key_id in keys.keys.keys() & bindings.keys():
                commitment = bindings[key_id]
                if commitment is None:
                    if key_id == keys.active or key_id in needed:
                        raise ValueError('Legacy empty vault key identity is retired; use a new identity.')
                elif not hmac.compare_digest(commitment, self._commitment(key_id)):
                    raise ValueError('Vault key material differs for an existing key identity; recover the correct key file.')
            if state is not None and state[0] not in bindings and state[0] not in needed:
                if not rotation or state[0] == keys.active:
                    raise ValueError('Legacy empty vault epoch cannot prove its key; explicitly rotate to a new key identity.')
                db.execute('INSERT INTO provider_vault_key_bindings VALUES(?,NULL)', (state[0],))
            for key_id in (needed | {keys.active}) - bindings.keys():
                if key_id in needed:
                    # Upgrade legacy databases only after EVERY ciphertext for
                    # that key authenticates; one good row cannot hide a split.
                    try:
                        for row in db.execute('SELECT * FROM provider_tokens WHERE key_id=?', (key_id,)):
                            self._decrypt(row)
                    except VerificationUnavailable:
                        raise ValueError('Legacy vault ciphertext cannot authenticate; preserve and recover its keys.') from None
                db.execute('INSERT INTO provider_vault_key_bindings VALUES(?,?)', (key_id, self._commitment(key_id)))

    def _commitment(self, key_id):
        return hmac.digest(self.keys.keys[key_id], b'tideglass.vault-key-binding.v1\0' + key_id.encode(), 'sha256')

    def _assert_binding(self, db, key_id):
        row = db.execute('SELECT commitment FROM provider_vault_key_bindings WHERE key_id=?', (key_id,)).fetchone()
        if row is None or row[0] is None or not hmac.compare_digest(row[0], self._commitment(key_id)):
            raise VerificationUnavailable('Vault key binding changed; recover configuration before writing.')

    @contextmanager
    def using(self, connection):
        token = self._connection.set(connection)
        try: yield
        finally: self._connection.reset(token)

    @contextmanager
    def _db(self, write=False):
        existing = self._connection.get()
        if existing is not None:
            yield existing
        else:
            with (self.db.transaction() if write else self.db.read()) as db: yield db

    @staticmethod
    def _aad(transaction, account, key_id):
        return json.dumps(['tideglass-google-token-v1', transaction, account, key_id], separators=(',', ':')).encode()

    def _decrypt(self, row):
        try:
            plaintext = AESGCM(self.keys.keys[row['key_id']]).decrypt(row['nonce'], row['ciphertext'], self._aad(row['transaction_id'], row['account_id'], row['key_id'])).decode()
            if hashlib.sha256(plaintext.encode()).hexdigest() != row['transaction_id']: raise ValueError()
            return plaintext
        except Exception:
            raise VerificationUnavailable('Protected provider token cannot be recovered.') from None

    def remember(self, transaction, plaintext, account):
        if not isinstance(plaintext, str) or not 0 < len(plaintext.encode()) <= 65536 or not TRANSACTION.fullmatch(transaction) or hashlib.sha256(plaintext.encode()).hexdigest() != transaction:
            raise VerificationUnavailable('Invalid protected provider token.')
        with self._db(write=True) as db:
            state = db.execute('SELECT active_key_id FROM provider_vault_state WHERE id=1').fetchone()
            if state[0] != self.keys.active: raise VerificationUnavailable('Vault key changed; reload configuration.')
            self._assert_binding(db, self.keys.active)
            old = db.execute('SELECT * FROM provider_tokens WHERE transaction_id=?', (transaction,)).fetchone()
            if old and old['account_id'] != account: raise VerificationUnavailable('Provider token is already bound.')
            if old:
                if self._decrypt(old) != plaintext: raise VerificationUnavailable('Provider token identity mismatch.')
                return
            nonce = os.urandom(12)
            encrypted = AESGCM(self.keys.keys[self.keys.active]).encrypt(nonce, plaintext.encode(), self._aad(transaction, account, self.keys.active))
            db.execute('INSERT INTO provider_tokens VALUES(?,?,?,?,?)', (transaction, account, self.keys.active, nonce, encrypted))

    def lookup(self, transaction, account):
        with self._db() as db:
            row = db.execute('SELECT * FROM provider_tokens WHERE transaction_id=? AND account_id=?', (transaction, account)).fetchone()
            return self._decrypt(row) if row else None

    def rotate(self):
        """All rows and active identity commit atomically; old processes fail closed."""
        with self.db.transaction() as db:
            state = db.execute('SELECT active_key_id FROM provider_vault_state WHERE id=1').fetchone()
            if state[0] not in {self._expected_active, self.keys.active}:
                raise VerificationUnavailable('Vault epoch changed; reload configuration before rotation.')
            self._assert_binding(db, self.keys.active)
            for row in db.execute('SELECT DISTINCT key_id FROM provider_tokens'):
                self._assert_binding(db, row[0])
            rows = db.execute('SELECT * FROM provider_tokens').fetchall()
            for row in rows:
                plaintext = self._decrypt(row)
                nonce = os.urandom(12)
                encrypted = AESGCM(self.keys.keys[self.keys.active]).encrypt(nonce, plaintext.encode(), self._aad(row['transaction_id'], row['account_id'], self.keys.active))
                db.execute('UPDATE provider_tokens SET key_id=?,nonce=?,ciphertext=? WHERE transaction_id=?', (self.keys.active, nonce, encrypted, row['transaction_id']))
            db.execute('UPDATE provider_vault_state SET active_key_id=? WHERE id=1', (self.keys.active,))
        return len(rows)
