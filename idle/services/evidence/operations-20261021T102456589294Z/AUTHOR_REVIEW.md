# Local operating readiness — author review

Recorded 2026-10-21. Author verification passed against the immutable `source/` snapshot. Independent review is pending. These changes are a separate source delta from native candidate c73; they are Python operations/tools and internal runbooks, not a native binary acceptance claim.

## Source and reproducibility

`verification.json` records 37 source/artifact hashes and this source-map fingerprint:

`7b3a5742947907c7025790a56fe044f2832ecf0c2ccb46608e41ddca416f19a1`

Recipe: SHA-256 of UTF-8 JSON serialization of `source_sha256` with sorted keys and comma/colon separators. The snapshot includes actual service source, tests, contract validator, scope/program context, exact runbooks, provider dependency lock and the soundtrack archive needed by an existing provider test. No production secret, credential, live database or synthetic account database is retained. Current-source drift during the recorded checks was empty.

The exact Python interpreter and command arrays are recorded in the manifest. Reproduce from `source/` using the pinned repository environment:

```sh
/Users/csys/Desktop/ibicot/idle/.tooling/services-venv/bin/python -m unittest discover -s tests/services/operations -v
/Users/csys/Desktop/ibicot/idle/.tooling/services-venv/bin/python -m unittest discover -s tests/services -v
/Users/csys/Desktop/ibicot/idle/.tooling/services-venv/bin/python -m unittest discover -s tests/services/providers -v
PYTHONPATH=. /Users/csys/Desktop/ibicot/idle/.tooling/services-venv/bin/python ../rehearse.py
```

`services/verify_operations.py` can create a **new** separately timestamped snapshot and repeat the procedure; it does not overwrite this evidence. Rehearsal uses only disposable synthetic local data and actual CLI subprocesses. It sends no provider requests, alerts or network messages.

## Verified behavior

| Check | Actual result | Evidence |
|---|---|---|
| New operations faults | 29/29 distinct tests passed | `operations.log` |
| Existing base service regression | 50 invocations passed; 28 distinct test IDs (22 rediscovered imports) | `base-services.log` |
| Existing provider/vault/fulfillment regression | 32/32 distinct tests passed | `providers.log` |
| Actual CLI rehearsal | 4 scenarios passed: healthy structure without samples exits 3; missing path exits 2 without creating a file; isolated restore exits 0; old pending acknowledgement exits 2 | `rehearsal.json`, `rehearse.py` |
| Isolated restore behavior | 20 actual dispatch/storage checks passed; preexisting application-row digest/count inventory matched; source backup hash unchanged; temporary copy removed | `rehearsal.json` |
| Snapshot integrity | 37 hashes captured; no current-source drift during checks | `verification.json` |

The three suites contain **89 distinct test IDs** across 111 invocations. Existing base tests emitted four `ResourceWarning` notices about unclosed SQLite connections; logs retain them. The new operations suite emitted none. A passing test invocation is not a zero-warning assertion about the whole preexisting test harness.

Health faults include missing/empty/corrupt/private-file/symlink/schema/constraint/trigger/foreign-key/feature-flag rejection without initialization; read-only write rejection; tiny deadline failure; exact acknowledgement, Support and freshness thresholds; failure streaks despite fresh observation timestamps; absent/malformed/synthetic/insufficient/over-limit telemetry; consent violation; backup age/future-clock/same-file rejection; disk failures; and actual optional vault/signer/reconciliation schema recognition.

Restore faults include absent/newer/tampered input, disk bounds, WAL-aware copying, matching source inventory, removal of the temporary copy, and isolated replay of external account-deletion/consent-withdrawal lists. Reports omit generated account identities, bearer/recovery credentials and row bodies. Runtime failures use fixed codes. Restored copies are always ineligible for live activation because a local synthetic drill cannot establish complete recovery history or actual provider truth.

## Implementation and scope audit in both directions

| Original package / scope | Implemented contribution | Unmet original acceptance |
|---|---|---|
| M5-04 / S27,S30,S37 | `health.py` checks and JSON signals; guarded `ops.py` routes; explicit thresholds/unknowns; tested optional service boundaries; isolated recovery and exact runbook | Configured staging, end-to-end delivered alerts, real entitlement/receipt operation, native/empirical quality denominator and dependencies. |
| M6-08 / S21,S37 | `recovery.py` preserves newer/incompatible structures, copies and verifies known service data, tests synthetic fresh/stale/revoked ownership presentation | S21 season archive/paid-pass continuation and native save migration are not covered. Actual purchase replay and authorized compatible release recovery remain open. |
| M7-04 / S37 | Disposable restore, switch/stop commands, bounds and recovery limitations | Hosted capacity/rollout rehearsal, production backup/deletion journal, provider reconciliation and approval authority remain absent. |
| M7-08 / S37,S38 | `release/runbooks/LAUNCH_HANDOVER.md` and unstaffed 14-day template explicitly identify authority, escalation, stops, incident fields, ongoing costs and Season 2 handover | No assigned responders, public support, delivered alerts, live launch or 14 actual days of incident/support coverage. |

Reverse audit: health source serves M5-04; isolated recovery and diagnostic CLI serve the local service portions of M5-04/M6-08/M7-04; operations documentation and release runbooks serve M5-04/M7-04/M7-08. Tests and evidence support those contributions only. No schema, provider/cache implementation, app, economy, package acceptance, source scope or program state was changed by this task.

## Limits the lead and independent reviewer must retain

- `health` is a local file observation. It cannot prove HTTP/TLS availability, scheduler execution, provider readiness, physical devices, alert delivery or staffing. Unknown outranks warning in the overall exit; all warning/unknown/critical signals remain listed.
- Pending acknowledgement age uses the last provider observation, not the first grant. A refresh can reset it. Durable reconciliation failure streaks are separate; true historical pending duration needs an additional qualified instrument.
- Backup mtime is not authenticated. Exact copied ciphertext is not proof the matching retained key is available. The tool does not encrypt, upload or retain backups.
- No external durable deletion/consent/revocation journal exists. Supplied deletion lists are replayed only in the disposable copy and cannot establish completeness. Historical credentials, consent, cloud selections, Support delivery, refunds and lease high water need an authorized reconciliation design before live activation.
- Newer/unrecognized schema is refused, never downgraded. The local drill does not mutate a live destination, publish a service, start a schedule or perform native season/save migration.
- The 14-day template has zero elapsed days and no names/dates/contacts. Season 2 work remains a separate decision brief, not new content production.

No original package or scope requirement is accepted by this author review.
