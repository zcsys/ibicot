"""Short-lived Ed25519 ownership leases; never a gameplay/economy authority."""
import base64
import json
import uuid
from urllib.parse import urlsplit
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .vault import private_file, unique_object, KEY_ID
from .verification import PRODUCTS, VerificationUnavailable


def b64(value): return base64.urlsafe_b64encode(value).decode().rstrip('=')

class OwnershipSigner:
    def __init__(self, key_file, issuer, *, ttl=86400, allow_local_development=False):
        parsed = urlsplit(issuer)
        local = allow_local_development is True and parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1','localhost','::1'}
        if (parsed.scheme != 'https' and not local) or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError('Lease issuer must be the exact public HTTPS origin.')
        if type(ttl) is not int or not 1 <= ttl <= 86400: raise ValueError('Ownership lease lifetime must be at most 24 hours.')
        config = json.loads(private_file(key_file, 4096), object_pairs_hook=unique_object)
        if set(config) != {'version','key_id','private_key'} or config['version'] != 1 or not KEY_ID.fullmatch(config['key_id']):
            raise ValueError('Invalid signing key file.')
        self.private = Ed25519PrivateKey.from_private_bytes(base64.b64decode(config['private_key'],validate=True))
        self.key_id, self.issuer, self.ttl = config['key_id'], issuer, ttl

    def issue(self, db, account, now):
        if account['seed'] is None: raise VerificationUnavailable('Link a main-game branch before issuing ownership.')
        db.execute('''CREATE TABLE IF NOT EXISTS ownership_leases(
          account_id TEXT PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
          revision INTEGER NOT NULL, issued_at INTEGER NOT NULL)''')
        old = db.execute('SELECT * FROM ownership_leases WHERE account_id=?',(account['id'],)).fetchone()
        if old and now < old['issued_at']: raise VerificationUnavailable('Service clock moved backwards; lease issuance paused.')
        revision = old['revision']+1 if old else 1
        entitlements = {}
        for row in db.execute("SELECT product_id,updated FROM purchases WHERE account_id=? AND state='purchased'",(account['id'],)):
            # A future-dated observation cannot turn a server clock rollback into
            # another 24 hours of commercial access.
            if row['updated'] > now or row['updated']+86400 <= now: continue
            for entitlement in PRODUCTS[row['product_id']]:
                entitlements[entitlement] = max(entitlements.get(entitlement,0),row['updated']+86400)
        expires = min([now+self.ttl,*entitlements.values()])
        payload = {'v':1,'issuer':self.issuer,'account_id':account['id'],'linked_account_seed':account['seed'],
                   'issued_at':now,'expires_at':expires,'revision':revision,'lease_id':str(uuid.uuid4()),
                   'entitlements':sorted(entitlements)}
        encoded = json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        db.execute('INSERT INTO ownership_leases VALUES(?,?,?) ON CONFLICT(account_id) DO UPDATE SET revision=excluded.revision,issued_at=excluded.issued_at',(account['id'],revision,now))
        return {'key_id':self.key_id,'payload':b64(encoded),'signature':b64(self.private.sign(encoded))}
