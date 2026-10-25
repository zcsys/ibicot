"""QA016 regressions: no real provider credentials or successful store calls."""
import base64
import hashlib
import json
import os
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import test_fulfillment as fixture
from services.tideglass_service.vault import TokenVault, VaultKeys
from services.tideglass_service.verification import VerificationUnavailable


class VaultKeyBindingTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.FulfillmentTests('runTest')
        self.f.setUp()

    def tearDown(self):
        self.f.tearDown()

    def keyfile(self, active='old', existing=False):
        keys = json.loads(self.f.keys.read_text())['keys'] if existing else {}
        if active not in keys:
            keys[active] = base64.b64encode(os.urandom(32)).decode()
        return fixture.secret(self.f.root / (active + '-replacement.json'),
            {'version': 1, 'active_key_id': active, 'keys': keys})

    def legacy(self):
        with self.f.db.transaction() as db:
            db.execute('DROP TABLE provider_vault_key_bindings')

    def test_empty_current_epoch_still_rejects_wrong_same_id_material(self):
        with self.assertRaises(ValueError):
            TokenVault(self.f.db, VaultKeys(self.keyfile()))
        self.f.vault.remember(fixture.TX, fixture.TOKEN, self.f.aid)
        self.assertEqual(self.f.vault.lookup(fixture.TX, self.f.aid), fixture.TOKEN)

    def test_binding_survives_token_account_deletion(self):
        f = self.f
        f.vault.remember(fixture.TX, fixture.TOKEN, f.aid)
        f.app.dispatch('DELETE', '/v1/account',
            {'recovery_code': f.account['recovery_code'], 'confirm_delete': True}, f.token)
        with f.db.read() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM provider_tokens').fetchone()[0], 0)
        with self.assertRaises(ValueError): TokenVault(f.db, VaultKeys(self.keyfile()))

    def test_write_and_rotate_recheck_key_binding_after_initialization(self):
        f = self.f
        f.vault.keys.keys['old'] = os.urandom(32)
        with self.assertRaises(VerificationUnavailable): f.vault.remember(fixture.TX, fixture.TOKEN, f.aid)
        with self.assertRaises(VerificationUnavailable): f.vault.rotate()
        with f.db.read() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM provider_tokens').fetchone()[0], 0)

    def test_legacy_populated_database_authenticates_before_migration(self):
        f = self.f
        f.vault.remember(fixture.TX, fixture.TOKEN, f.aid)
        self.legacy()
        with self.assertRaises(ValueError): TokenVault(f.db, VaultKeys(self.keyfile()))
        restored = TokenVault(f.db, VaultKeys(f.keys))
        self.assertEqual(restored.lookup(fixture.TX, f.aid), fixture.TOKEN)
        with self.assertRaises(ValueError): TokenVault(f.db, VaultKeys(self.keyfile()))

    def test_legacy_migration_checks_all_rows_and_rolls_back_on_corruption(self):
        f = self.f
        f.vault.remember(fixture.TX, fixture.TOKEN, f.aid)
        token = 'second-distinct-test-fixture'
        transaction = hashlib.sha256(token.encode()).hexdigest()
        f.vault.remember(transaction, token, f.aid)
        self.legacy()
        with f.db.transaction() as db:
            db.execute('UPDATE provider_tokens SET ciphertext=? WHERE transaction_id=?', (b'bad', transaction))
        with self.assertRaises(ValueError): TokenVault(f.db, VaultKeys(f.keys))
        with f.db.read() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='provider_vault_key_bindings'").fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM provider_tokens').fetchone()[0], 2)

    def test_legacy_empty_epoch_requires_explicit_new_id_and_old_id_stays_retired(self):
        f = self.f
        self.legacy()
        with self.assertRaises(ValueError): TokenVault(f.db, VaultKeys(f.keys))
        with self.assertRaises(ValueError): TokenVault(f.db, VaultKeys(f.keys), rotation=True)
        replacement = self.keyfile('new')
        rotation = TokenVault(f.db, VaultKeys(replacement), rotation=True)
        self.assertEqual(rotation.rotate(), 0)
        current = TokenVault(f.db, VaultKeys(replacement))
        current.remember(fixture.TX, fixture.TOKEN, f.aid)
        self.assertEqual(current.lookup(fixture.TX, f.aid), fixture.TOKEN)
        old = self.keyfile('old', existing=True)
        value = json.loads(old.read_text())
        value['keys'].update(json.loads(replacement.read_text())['keys'])
        fixture.secret(old, value)
        with self.assertRaises(ValueError): TokenVault(f.db, VaultKeys(old), rotation=True)

    def test_stale_rotation_cannot_overwrite_a_newer_active_epoch(self):
        f = self.f
        one = TokenVault(f.db, VaultKeys(self.keyfile('one', existing=True)), rotation=True)
        two = TokenVault(f.db, VaultKeys(self.keyfile('two', existing=True)), rotation=True)
        two.rotate()
        with self.assertRaises(VerificationUnavailable): one.rotate()
        with f.db.read() as db:
            self.assertEqual(db.execute('SELECT active_key_id FROM provider_vault_state').fetchone()[0], 'two')


if __name__ == '__main__': unittest.main()
