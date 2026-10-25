"""Bounded local reconciliation from actual provider reads, with durable backoff."""
import json
from .verification import PurchaseObservation, VerificationUnavailable


def purchase_proof(row, vault):
    if row['platform'] == 'apple':
        return {'transaction_id':row['transaction_id'],'expected_product_id':row['product_id']}
    if vault is None: raise VerificationUnavailable('Provider token vault unconfigured.')
    token = vault.lookup(row['transaction_id'],row['account_id'])
    if token is None: raise VerificationUnavailable('Protected purchase token unavailable.')
    return {'purchase_token':token,'expected_product_id':row['product_id']}


def reconcile(application, *, limit=100):
    if type(limit) is not int or not 1 <= limit <= 1000: raise ValueError('Bounded batch size required.')
    now = int(application.clock())
    with application.db.transaction() as db:
        application._enabled(db,'purchases')
        db.execute('''CREATE TABLE IF NOT EXISTS purchase_reconciliation(
          platform TEXT NOT NULL,transaction_id TEXT NOT NULL,next_attempt INTEGER NOT NULL,
          failures INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(platform,transaction_id),
          FOREIGN KEY(platform,transaction_id) REFERENCES purchases(platform,transaction_id) ON DELETE CASCADE)''')
        db.execute('INSERT OR IGNORE INTO purchase_reconciliation(platform,transaction_id,next_attempt) SELECT platform,transaction_id,0 FROM purchases')
        selected = db.execute('''SELECT p.* FROM purchases p JOIN purchase_reconciliation r
          ON p.platform=r.platform AND p.transaction_id=r.transaction_id WHERE r.next_attempt<=?
          ORDER BY r.next_attempt,p.updated,p.platform,p.transaction_id LIMIT ?''',(now,limit)).fetchall()
        # Lease work before network calls, so concurrent operator invocations do
        # not hammer the same provider transaction. Crash retries after 60s.
        for row in selected:
            db.execute('UPDATE purchase_reconciliation SET next_attempt=? WHERE platform=? AND transaction_id=?',(now+60,row['platform'],row['transaction_id']))
    summary = {'attempted':len(selected),'refreshed':0,'revoked':0,'acknowledged':0,'native_completion_pending':0,'failed':0,'deleted':0}
    for row in selected:
        try:
            proof = purchase_proof(row,application.token_vault)
            with application.db.transaction() as db:
                application._enabled(db,'purchases')
                if db.execute('SELECT 1 FROM accounts WHERE id=?',(row['account_id'],)).fetchone() is None:
                    summary['deleted'] += 1
                    continue
                application._purchase(db,row['account_id'],{'platform':row['platform'],'proof':json.dumps(proof)})
                current = db.execute('SELECT * FROM purchases WHERE platform=? AND transaction_id=?',(row['platform'],row['transaction_id'])).fetchone()
            summary['refreshed'] += 1
            if current['state'] == 'revoked': summary['revoked'] += 1
            elif current['state'] == 'purchased' and not current['acknowledged']:
                if current['platform'] == 'apple': summary['native_completion_pending'] += 1
                else:
                    observation = PurchaseObservation(**{k:current[k] for k in ('platform','transaction_id','account_id','product_id','state','version','authority')})
                    application.purchase_verifier.acknowledge(observation)
                    with application.db.transaction() as db:
                        summary['acknowledged'] += db.execute("UPDATE purchases SET acknowledged=1 WHERE platform=? AND transaction_id=? AND version=? AND state='purchased'",(row['platform'],row['transaction_id'],current['version'])).rowcount
            with application.db.transaction() as db:
                db.execute('UPDATE purchase_reconciliation SET failures=0,next_attempt=? WHERE platform=? AND transaction_id=?',(now+(60 if current['state']=='pending' else 21600),row['platform'],row['transaction_id']))
        except Exception:
            # Credentials, token/proof, provider bodies and account IDs never
            # enter logs. Failure is observable without claiming verification.
            summary['failed'] += 1
            with application.db.transaction() as db:
                db.execute('UPDATE purchase_reconciliation SET failures=MIN(failures+1,6),next_attempt=?+MIN(3600,60*(1 << MIN(failures,6))) WHERE platform=? AND transaction_id=?',(now,row['platform'],row['transaction_id']))
    return summary
