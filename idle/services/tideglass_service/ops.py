"""Local operator commands; no unauthenticated administrator HTTP endpoint."""
import argparse
import json
import time
from .storage import Database


def dashboard(database):
    with database.read() as db:
        # An unfinished session is an unknown outcome, never assumed crash-free.
        rows = db.execute('''SELECT account_id,session_id,
          MAX(CASE WHEN name='session_start' THEN 1 ELSE 0 END) started,
          MAX(CASE WHEN name='session_end' THEN 1 ELSE 0 END) ended,
          MAX(CASE WHEN name='session_crash' THEN 1 ELSE 0 END) crashed
          FROM telemetry GROUP BY account_id,session_id''').fetchall()
        started = sum(row['started'] for row in rows)
        crashed = sum(row['crashed'] and row['started'] for row in rows)
        completed = sum(row['ended'] and row['started'] and not row['crashed'] for row in rows)
        uncertain = started - completed - crashed
        by_platform = {}
        for row in db.execute("SELECT body FROM telemetry WHERE name='session_start'"):
            event = json.loads(row[0]); platform = event['properties']['platform']
            by_platform[platform] = by_platform.get(platform,0)+1
        pending_ack = db.execute("SELECT COUNT(*) FROM purchases WHERE state='purchased' AND acknowledged=0").fetchone()[0]
        return {'generated_at':int(time.time()), 'observed_sessions':started,
            'completed_without_reported_crash':completed,'reported_crash_sessions':crashed,
            'unknown_outcome_sessions':uncertain,
            'crash_free_lower_bound':completed/started if started else None,
            'per_platform_start_events':by_platform,
            'claim_delivery_pending':db.execute('SELECT COUNT(*) FROM support_claims WHERE delivered_save_id IS NULL').fetchone()[0],
            'purchase_acknowledgements_pending':pending_ack,
            'cloud_snapshot_bytes':db.execute('SELECT COALESCE(SUM(bytes),0) FROM snapshots').fetchone()[0],
            'alerts':(['purchase_acknowledgement_pending'] if pending_ack else []) + (['session_outcomes_incomplete'] if uncertain else []),
            'release_quality_gate_verified':False,
            'limitation':'Consenting, retained service telemetry only; never a substitute for native crash reports or all-install retention.'}


def set_feature(database, name, enabled):
    if name not in {'cloud','purchases','ads','telemetry'}:
        raise ValueError('Only optional services may be disabled; no economic remote parameters.')
    with database.transaction() as db:
        db.execute('UPDATE flags SET enabled=? WHERE name=?',(int(enabled),name))
        db.execute('INSERT INTO operations(happened,kind,detail) VALUES(?,?,?)',(int(time.time()),'feature_switch',json.dumps({'name':name,'enabled':enabled})))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    commands = parser.add_subparsers(dest='command',required=True)
    commands.add_parser('dashboard')
    backup = commands.add_parser('backup'); backup.add_argument('destination')
    flag = commands.add_parser('feature'); flag.add_argument('name'); flag.add_argument('state',choices=['on','off'])
    commands.add_parser('prune')
    args = parser.parse_args(); db = Database(args.database)
    if args.command=='dashboard':result=dashboard(db)
    elif args.command=='backup':result={'backup':db.backup(args.destination)}
    elif args.command=='feature':set_feature(db,args.name,args.state=='on');result={'updated':True}
    else:
        with db.transaction() as connection:
            now=int(time.time())
            connection.execute('DELETE FROM telemetry WHERE received<?',(now-90*86400,))
            connection.execute('DELETE FROM sessions WHERE expires<=?',(now,))
            connection.execute('DELETE FROM rate_limits WHERE window<?',(now//60-2,))
            connection.execute('DELETE FROM support_claims WHERE created<?',(now-9*86400,))
            connection.execute('DELETE FROM ad_receipts WHERE day_id<?',(now//86400-9,))
        result={'pruned':True}
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
