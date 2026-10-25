"""Local operator commands; no unauthenticated administrator HTTP endpoint."""
import argparse
import json
import time
from .storage import Database
from .health import CheckError, Thresholds, health, require_existing_database


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
    check = commands.add_parser('health')
    check.add_argument('--backup')
    check.add_argument('--database-seconds', type=float, default=5.0)
    check.add_argument('--minimum-free-bytes', type=int, default=1024**3)
    check.add_argument('--minimum-free-fraction', type=float, default=0.05)
    check.add_argument('--backup-max-age-seconds', type=int, default=86400)
    drill = commands.add_parser('restore-drill')
    drill.add_argument('--deletion-manifest')
    drill.add_argument('--seconds', type=float, default=30.0)
    backup = commands.add_parser('backup'); backup.add_argument('destination')
    flag = commands.add_parser('feature'); flag.add_argument('name'); flag.add_argument('state',choices=['on','off'])
    commands.add_parser('prune')
    rotate=commands.add_parser('rotate-vault'); rotate.add_argument('--key-file',required=True)
    args = parser.parse_args()
    # Diagnostic paths never initialize/migrate a missing or unknown database.
    if args.command == 'health':
        try:
            result = health(args.database, backup=args.backup, thresholds=Thresholds(
                database_seconds=args.database_seconds,
                minimum_free_bytes=args.minimum_free_bytes,
                minimum_free_fraction=args.minimum_free_fraction,
                backup_max_age_seconds=args.backup_max_age_seconds))
        except ValueError:
            result = {'status': 'critical', 'exit_code': 2, 'failure_code': 'invalid_health_thresholds'}
        print(json.dumps(result, indent=2))
        raise SystemExit(result['exit_code'])
    if args.command == 'restore-drill':
        from .recovery import restore_drill
        try:
            result = restore_drill(args.database, deletion_manifest=args.deletion_manifest, seconds=args.seconds)
        except ValueError:
            result = {'status': 'failed', 'exit_code': 2, 'failure_code': 'invalid_drill_parameters'}
        print(json.dumps(result, indent=2))
        raise SystemExit(result['exit_code'])
    try:
        require_existing_database(args.database)
    except CheckError as error:
        print(json.dumps({'status': 'critical', 'exit_code': 2, 'failure_code': str(error)}))
        raise SystemExit(2)
    db = Database(args.database)
    if args.command=='dashboard':result=dashboard(db)
    elif args.command=='backup':result={'backup':db.backup(args.destination)}
    elif args.command=='feature':set_feature(db,args.name,args.state=='on');result={'updated':True}
    elif args.command=='rotate-vault':
        from .vault import TokenVault,VaultKeys
        result={'rotated_tokens':TokenVault(db,VaultKeys(args.key_file),rotation=True).rotate()}
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
