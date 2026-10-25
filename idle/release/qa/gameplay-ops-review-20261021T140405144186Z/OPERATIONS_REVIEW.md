# Independent local deployment and alert review

The repaired local preparation passes this bounded review. **OPS-GE001 and OPS-GE002 are closed** at source inventory `2173e6ec85a78cbc72df5dc87e91bb5355dda80ad918d888a6c96bd0f2a60d87`. This is not acceptance of complete M5-04, S37, a deployed staging environment, or release operations.

Reviewer: `/root/gameplay_engineer`. Author and repair owner: `/root/platform_release`. I edited only review artifacts. The 13 new service/configuration/test files and their 23 unchanged runtime context files were read, copied, and rehashed. The API, browser deletion, health, provider, and database sources remain unchanged. No Flutter/native command, external message, public listener, scheduler installation, real account, or real recipient was used.

| Frozen execution | Independent result |
|---|---|
| Original author suite, source `d92c120d…` | 22 tests pass |
| Original independent probes | 12 methods: nine pass and three failing methods, containing eight failed assertions/subtests that demonstrate the two findings |
| Original actual HTTP/TLS rehearsal | Nine scenarios pass; 256 concurrent fixture requests return HTTP 200 |
| Repaired author suite | 25 tests pass |
| Same independent probes, unchanged | All 12 methods pass |
| Repaired actual HTTP/TLS rehearsal | All nine scenarios pass; 256 concurrent fixture requests return HTTP 200 |

Original and repaired runs are separate. The final result is 37 test methods plus nine local rehearsal scenarios; repeated executions are not additional distinct scenarios. `verification.json` pins inputs, logs, probe source, source deltas, and outcomes. Both source copies and the 36 current repaired files were rehashed with no drift. Author verification hashes are `20bbbea596da42a7945befb7733aa195c84e445aea52488edb3ac0ab9a5833f5` (original) and `bcdd336f5b033882fe9e35ef74eb473b6eb5a9a0c485867bf8c1c6c30ac36a67` (repaired).

## Findings and preserved failures

**OPS-GE001, P2 — overall severity could contradict its signals.** The original envelope accepted `status: warning` with a critical `database_missing` signal. A mocked malformed health-command result with exit1 then passed the operator validator, including when alert delivery was disabled. This was an input-validation defect; the existing health calculator was not observed producing an incorrect report. The repair derives the exact aggregate in the same order as that calculator: critical, unknown, warning, then OK when empty. Every other declared overall status is rejected. The unchanged independent full mismatch matrix and operator fallback test now pass. Invalid health reports become a critical `health_command_failed` operator signal. `independent-negative-initial.log` retains the failures.

**OPS-GE002, P2 — numeric host coercion bypassed the string contract.** `ipaddress.ip_address(2130706433)` was accepted as loopback while the original numeric value remained in the returned configuration and bind string. This contradicted the documented literal IPv4 input. The repair rejects non-string host values before parsing. The unchanged test now rejects the integer, Boolean, null, list, shortened address, and numeric string while preserving `127.0.0.1` exactly. No claim of observed public exposure is made.

**OPS-PREP001 — prior independent lead finding, retained.** Root's earlier FIFO probe timed out because reading a named pipe could block before type validation. The existing repair uses nonblocking open and checks the descriptor is a private bounded regular file. Root's original and repaired probes remain at `release/qa/lead-ops-preliminary-20261021T135354.446354Z`; their hashes are included here. I independently reran the permanent FIFO regression in both final suites. This report does not claim discovery of that finding.

Only `alert_transport.py`, `deployment.py`, the author test file, and two narrow documentation sentences changed in the repair; see `repaired.diff`. No acceptance criterion was relaxed.

## Additional checks

The independent receiver tests use actual sockets and child delivery processes. They cover response loss after receipt followed by the same payload/Idempotency-Key, duplicate JSON keys, the exact 4096/4097-byte receipt boundary, a trickled body stopped by the overall child deadline, configuration disabled between retries preventing another POST, valid credential rotation without changing payload identity, and ignored ambient proxy variables. The TLS test trusts an isolated fixture certificate through the child process environment, then separately proves an untrusted chain and a trusted certificate with the wrong IP name are rejected before any POST. No verification bypass or machine trust-store change is used.

An independent process holds the operator lock while another invocation reports `already_running`; after SIGKILL the next actual missing-database health cycle succeeds with a critical report and the same lock inode. This proves cooperative process exclusion and kernel release on this host, not power-loss durability or protection against another process with the same user's filesystem permissions.

The author rehearsal was independently executed from copied source. Each HTTP and TLS profile handles 64 health and 64 authenticated synthetic-entitlement requests with eight clients. It checks request bounds, redacted logs, two-worker limits despite hostile ambient Gunicorn options, killed-worker replacement, and the HTTP incomplete-body timeout/recovery path. Those controlled worker terminations are not natural crashes or observed player sessions. The incomplete mutation body is invalid and never commits; general mutation response-loss recovery is not qualified by that scenario. The systemd files are inspected, uninstalled Linux templates; no cgroup/systemd enforcement is inferred from this macOS run.

## Scope comparison

M5-04's unchanged original acceptance is: “Validate economy/session events, entitlement dashboards, alerts, backups, support receipts and feature disable switches in staging.” Its original prerequisites remain M3-07 and M4-04. This contribution establishes a bounded serving entry point, validated opt-in delivery, and one manual operator cycle locally. It cannot substitute for all those operating functions working in actual staging. S37's observation and operational release obligations also remain open. Receiver acceptance is explicitly not a human acknowledgement; real receiver durability, escalation, operator response, public TLS/DNS, target hosting limits, and calendar observations remain untested.

Reproduce from either copied source directory with the project deployment virtual environment: `python -m unittest discover -s tests/services/operations -p test_operating_delivery.py -v`; `PYTHONPATH=. python ../independent_ops_probes.py`; and `python services/rehearse_deployment.py --output <new-empty-local-directory>`. No status file was changed by this reviewer. Recommendation: retain this as independently reviewed local M5-04/S37 implementation evidence, without accepting either full obligation.
