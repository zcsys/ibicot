# Local service operations and release gates

These commands act on explicit local files. They do not deploy, schedule work, contact providers, send alerts, or approve a release. Run from the repository root with the pinned environment. Commands now reject a missing, empty, shared-permission, unsupported or corrupt database before constructing the application database; a mistyped path cannot silently create a healthy empty service.

```sh
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/service.sqlite3 health --backup /absolute/backup.sqlite3
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/service.sqlite3 dashboard
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/service.sqlite3 backup /absolute/new-backup.sqlite3
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/service.sqlite3 feature purchases off
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/service.sqlite3 feature ads off
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/service.sqlite3 prune
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/backup.sqlite3 restore-drill
```

Do not use a live service path as the backup argument. Backup creates a new owner-only file using SQLite's online backup API and checks integrity. Existing destinations are refused. An operator must arrange encrypted backup storage, independent retained keys, authenticated creation records and a verified retention policy. SQLite permissions alone do not encrypt a database.

## Health output and thresholds

`health` prints one JSON report containing check status, stable error codes, aggregate counts, thresholds, and machine-readable `signals`. It never prints account identifiers, credentials, raw telemetry, purchase proofs, provider responses or filesystem paths. It performs no repair. Connections use SQLite `mode=ro`, `query_only` and `trusted_schema=OFF`, with a time budget and lock timeout. WAL data is included; SQLite may maintain its own shared-memory coordination file. Checks do not mutate application rows. Unknown/newer structures, missing constraints, views/triggers and foreign-key violations fail closed. The tool deliberately recognizes only the current base schema and the current optional vault, lease and reconciliation table layouts.

Table definitions and the full explicit-index inventory are compared as SQL tokens as well as column, foreign-key and unique-index metadata, so changed CHECK clauses, collations, conflict policies, missing required indexes and unexpected expression indexes reject. Only whitespace, comments and unquoted case are normalized; quoted content is preserved. An unfamiliar equivalent DDL spelling needs explicit review rather than an automatic compatibility claim.

| Exit | Overall status | Meaning |
|---|---|---|
| 0 | `ok` | All measured local checks passed; external release gates remain unverified. |
| 1 | `warning` | A measured condition needs attention; no unknown or critical check dominates it. |
| 2 | `critical` | Invalid/unreadable database or a critical threshold/consistency failure. |
| 3 | `unknown` | At least one required observation is absent/insufficient, with no critical check. |

Precedence is critical, unknown, warning, ok. Read every signal: an unknown overall status does not hide the warning entries. An empty new database is **unknown**, never a quality pass. Each backup/database scan has its own default five-second budget, bounded to at most 60 seconds. Telemetry processing is limited to 100,000 rows (at most one million when configured through the Python interface). Deadline/SQLite failures produce a fixed error code without exposing engine diagnostics.

| Check | Default rule | Interpretation and limit |
|---|---|---|
| Database | Schema 1 with complete known table structure, integrity and foreign-key checks | Does not verify application deployment, HTTP/TLS availability or provider configuration. |
| Disk | Critical below 1 GiB **or** below 5% free | Measures the database parent filesystem; hosting quotas, inodes, file-descriptor limits and future growth need separate qualification. |
| Backup | Critical for invalid/missing requested backup, future mtime, or mtime older than 24 h | Omitted backup is unknown. Filesystem mtime is not an authenticated backup creation timestamp. |
| Google acknowledgement | Any pending row warns; age of last stored provider observation ≥600 s is critical | This is **not time since first grant**: reconciliation refresh can reset `updated`. Consecutive reconciliation failures provide a separate signal. |
| Apple completion | Pending purchased rows have unknown completion | Current server data cannot establish native StoreKit completion; do not label them Google acknowledgement failures. |
| Support delivery | Any undelivered receipt warns; claim creation age ≥24 h is critical | Some players may not return to deliver a valid receipt; investigate before treating it as data loss. |
| Provider freshness | Purchased observations aged ≥24 h warn; future observations are critical | Grant reads already exclude stale/future data. A timely stored observation is not proof the next provider call will succeed. |
| Reconciliation | Any due/failed row warns; maximum failure streak ≥3 is critical | A missing table is unknown; no scheduler or worker heartbeat is inferred. |
| Consent | Any retained event for an account currently opted out is critical | Checks live retained rows, not disconnected backups or SDK collection. |
| Telemetry timestamps | Any server receipt timestamp later than the check time is critical | A clock/storage anomaly is reported separately and never added to the current quality sample. |
| Save/resume events | Server receipt interval `[now − 24 h, now]`; minimum 100 recognized samples; failure ratio ≥1% is critical | Sparse failures warn; absent/invalid/over-limit data is unknown. Future receipts and `test` platform are excluded. This is an operational event ratio across consenting retained accounts, not native crash-free sessions, all-install retention, or a release denominator. |

CLI options expose database deadline, free-space thresholds and backup max age. All default thresholds, including the Python interface's other thresholds, are printed in each report. These are local operating defaults requiring staging calibration; they are not new product release targets or economic parameters. No alert destination is configured, and no person is assumed to be watching these outputs.

## Isolated restore drill

`restore-drill` treats `--database` as the **backup input**. It validates the existing input read-only, copies it through SQLite's online backup API into a unique owner-only temporary directory, verifies the schema, integrity, foreign keys and a streamed digest/count inventory of all application tables, then exercises actual application dispatch and storage behavior. It has a default 30-second total budget, maximum 60 seconds, one million total application rows and an 8 GiB source-size ceiling, plus a local free-space check. Exceeding a bound fails the drill rather than claiming partial verification. It removes the temporary copy on completion or failure. It has no live-destination or promote flag.

The behavior exercise creates a new synthetic account only in that temporary copy. It checks recovery-code reauthentication, default refusal of telemetry, fresh/stale/revoked entitlement presentation from explicitly synthetic ledger rows, feature disables, free Support with ads disabled, consent withdrawal, export, deletion, rejected deleted sessions and cascades. No synthetic verifier is installed into the service, no server socket is opened, and no real provider transaction is claimed. Exact preserved encrypted rows do not establish availability of the matching retained vault keys.

A successful report returns exit 0 and `status: local_drill_passed`, while **always** returning `eligible_for_live_restore: false`. This means the local procedure succeeded; it does not authorize activation. This is service database recovery preparation, not a native-save migration, season archive or actual purchase replay drill.

### Deletion and consent reconciliation

A historical backup made before account deletion can resurrect the account; one made before consent withdrawal can resurrect telemetry and permission. The service currently has no independently durable external deletion/consent journal. The drill therefore reports that completeness is unknown. Optionally replay an operator-supplied, owner-only JSON manifest into the disposable copy:

```sh
.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/backup.sqlite3 restore-drill --deletion-manifest /absolute/deletions.json
```

Manifest fields are exactly `version: 1`, `account_ids: [UUID strings]` and `telemetry_opt_out_ids: [UUID strings]`. Both lists are required, unique and limited to 5,000 entries each; the file is limited to 256 KiB. Account deletion uses the real foreign-key cascade. Consent withdrawal clears telemetry and advances its revision. The report emits only counts. It cannot verify the authority/completeness of a supplied manifest, and replay never makes a copy eligible for activation.

Before any real recovery, the designated authority must reconcile **all** post-backup deletions, consent withdrawals, session revocations, recovery-code rotations, cloud selections, Support delivery, refunds, acknowledgement state and lease revision high water. Restoring an old lease revision may be rejected by clients that saw a newer revision; restoring old consent or credentials may reopen revoked access. The drill intentionally does not guess fixes or silently clear anti-replay records. Matching retained vault keys and fresh actual provider reconciliation must be demonstrated. If the current schema or save format is newer, preserve it and use a compatible forward repair. Never downgrade a version marker or copy an arbitrary database over a running instance.

## Optional feature switches

Only `cloud`, `purchases`, `ads` and `telemetry` are switchable. No economic parameters can change through this command. Disabling ads preserves free briefing; disabling purchases preserves ownership reads/restore metadata; disabling cloud preserves account export/deletion; telemetry refusal/delete remains available when collection is disabled. Real native UI/outage behavior and configured endpoints require their separate evidence. The local restore drill verifies these service boundaries in its disposable copy.

## Required before public deployment

1. Select hosting, launch/recovery authority, production HTTPS origin, secret storage, request/time limits, bounded worker pool, logging policy, capacity plan and incident owner. The built-in runner binds loopback only.
2. Configure actual Apple/Google application and product identities, notifications, signing/trust material and provider credentials. Existing adapters must be exercised with both stores' real sandbox purchase, restore, refund and interruption flows. Native Apple completion observation remains an explicit gap.
3. Configure approved ad units, consent flow and verified callbacks; demonstrate no-fill/refusal leaves six equal briefing slots on actual devices.
4. Qualify native secure storage, account/branch selection, export, code rotation, lost responses, deletion, offline ownership and outages with actual devices and configured staging.
5. Qualify encrypted retained backups, external deletion/consent journal, scheduled prune/reconciliation, restoration, alert routing and delivery to staffed operators. These local tools install no scheduler or monitoring service.
6. Freeze cohort definitions/exclusions; audit SDK/network collection; measure real critical flows, required quality denominators, retention and actual calendar coverage. Synthetic data cannot become player evidence.

See [the launch handover](../../release/runbooks/LAUNCH_HANDOVER.md) and [the unstaffed coverage template](../../release/runbooks/launch-coverage-template.json). Independent review is required before author checks become package evidence.

## Scope accounting

| Work item | Local contribution from these tools | Original acceptance remains open because |
|---|---|---|
| M5-04 / S27,S30,S37 | Consented event checks, entitlement/receipt backlog signals, schema/integrity/free-space/backup checks, optional switches, isolated recovery | No configured staging alert delivery, hosted recovery, actual provider flow or empirical release denominator. |
| M6-08 / S21,S37 | Refusal of newer/incompatible database structures; isolated backup reconstruction and entitlement-read behavior | No season archive/paid continuation, native migration, actual purchase replay, or authorized live compatible repair. |
| M7-04 / S37 | Concrete switch/recovery commands, bounds, stop conditions and limits | No hosted capacity/rollout rehearsal, credentials, deployment authority or production deletion journal. |
| M7-08 / S37,S38 | Explicit incident/escalation/Season 2 handover and 14-day blank coverage assignments | No assigned people, delivered alerts, launch, elapsed support coverage or public support endpoint. |

In the reverse direction, `health.py` maps to M5-04; `recovery.py` maps to M5-04 and service portions of M6-08/M7-04; `ops.py` routing maps to those same operational tools; `LAUNCH_HANDOVER.md` and the coverage template map to M7-04/M7-08. Tests and manifests substantiate those narrow contributions. They do not add economic scope or waive dependency gates.
