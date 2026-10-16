# Local service operations and release gates

Use the commands from the repository root. These commands operate on explicit local files and do not deploy anything.

```sh
python3 -m services.tideglass_service.ops --database services/local/tideglass.sqlite3 dashboard
python3 -m services.tideglass_service.ops --database services/local/tideglass.sqlite3 backup services/local/backup-unique.sqlite3
python3 -m services.tideglass_service.ops --database services/local/tideglass.sqlite3 feature purchases off
python3 -m services.tideglass_service.ops --database services/local/tideglass.sqlite3 feature ads off
python3 -m services.tideglass_service.ops --database services/local/tideglass.sqlite3 prune
```

Backup uses SQLite's online backup API and checks the destination integrity. A destination must not already exist, is created owner-only before copying, and is not an automatic release rollback. Restore first to an isolated directory, inspect integrity/schema, apply privacy deletions, and replay representative authenticated reads. Keep the original database and its WAL together; never replace an active live database using an arbitrary filesystem copy.

The application refuses an unknown/newer database schema before adding tables. An older executable must not open newer service data, and an older native executable must not import a newer game save. Use a compatible forward repair. Changing a service feature flag cannot rebalance or reinterpret gameplay.

The dashboard counts starts, matched ends, explicitly reported crashes, and unknown outcomes. It reports a conservative lower bound rather than calling missing ends crash-free. Its denominator contains only retained consenting service telemetry; it cannot establish 99.5% crash-free sessions over 10,000 real platform/device sessions, all-install retention, a mature D30 cohort, or a real 28-day season. Synthetic fixtures use platform `test` and must never be mixed into release cohorts.

Purchase acknowledgements must be retried by a configured worker only after durable grant. Alert on pending acknowledgements, failures in resume/save critical flows, storage errors, abnormal branch conflicts and depleted storage quota. The provided dashboard exposes pending delivery/acknowledgement counts and unknown outcomes; it does not send alerts to an operator. Provider notifications and fresh reconciliation must revoke refunded ownership before a cached observation expires. Paid ownership is not authorized from observations older than 24 hours.

Disabling `ads` leaves the free briefing route available; disabling purchases leaves ownership reads/restore recovery metadata available. Disabling cloud leaves account export/deletion available. Telemetry refusal/delete remains available while telemetry collection is disabled. These are service safeguards; native UI must reflect unavailable optional actions and preserve offline play.

## Required before public deployment

1. Select hosting and authority, production HTTPS origin, secret storage, request/time limits, bounded application worker pool, logging policy and operating owner. The built-in development runner binds loopback only.
2. Configure authentic Apple/Google app and product identities; implement provider adapters with application/environment/account binding, signature verification, pending/refund handling, transaction lookup and notification reconciliation. Exercise sandbox purchases, restore, interrupted delivery and acknowledgement on both native stores.
3. Configure approved ad units, consent flow and verified server callbacks. Demonstrate no-fill/refusal leaves six equal briefing slots; never accept a client completion as proof.
4. Integrate account UI and native secure credential storage. Demonstrate guest linking, two-device forks, explicit selection, export, code rotation, lost responses, deletion and outages on actual builds.
5. Qualify encrypted backup storage, scheduled prune, restoration, deletion handling across retained backups, monitoring and alert delivery. Do not operate publicly with a local demonstration process.
6. Freeze cohort definitions and exclusions; audit all SDK/network collection; measure real devices, critical flows, 10,000 observed sessions, mature retention and the required calendar coverage. Staff/automation tests are never player evidence.

## Scope accounting

| Work item | Current service contribution | Why original acceptance stays open |
|---|---|---|
| M2-04 / S13 | Exact cloud snapshots, conflict preservation and CAS selection, exercised with concurrent HTTP clients and actual Dart SaveRepository exports | Native two-device and configured staging evidence absent |
| M3-06 / S02,S13,S39 | Opt-in lifecycle, recovery/rotation, branch selection, export and live-data deletion | Native secure storage/UI, provider ownership restore and backup-deletion drill absent |
| M3-07 / S25 | Independent immutable purchase receipts, six-slot Support ledger, interrupted delivery recovery | Native trusted adapter delivery/claim reconciliation still needs integration |
| M4-04 / S24 | Durable verified-observation grant/revoke/acknowledge state machine, fail-closed external boundary | Real provider integration and both-store sandbox evidence absent |
| M4-05 / S25 | Shared ad/free slot arbitration, no-fill/refusal tests and no unconfigured ad grants | Actual rewarded-ad verification and native consent/SDK evidence absent |
| M5-03 / S27,S39 | Data inventory, consent refusal/clear, export/delete/outage source and tests | Actual native SDK/network audit and working public privacy/support endpoints absent |
| M5-04 / S27,S30,S37 | Event schema, bounded buffer, dashboard, consistent backup, switches and schema guard | Staging/live drill, alert delivery and empirical quality denominator absent |

Independent review is required before author checks can become package evidence. None of these rows waives the original release gates.
