# Serving and alert delivery: author handoff

Status: implemented and author-verified on a frozen source copy; different-agent full review remains required. This is narrow local preparation, not completion of M5-04, M6-05, M7-04, S37 or any release gate.

Source inventory SHA-256: `d92c120d8601556f6dbe6281b12cefd0ad11fdb1af17a53b8d9d5f2637c92ccf`. `source-manifest.json` pins all new inputs and their unchanged API/factory/health/runtime context. `verification.json` pins commands, exact copied cwd, logs and the actual rehearsal report; `handoff.json` pins that verification and lists the new owned files. Both snapshot and live input rehashes reported zero drift. Browser static/runtime sources remained unchanged; the separate root-approved WEB-DOC001 documentation fix was not used as an operations drift failure.

| Original clause | Concrete contribution | Remaining original boundary |
|---|---|---|
| M5-04: “Validate economy/session events, entitlement dashboards, alerts, backups, support receipts and feature disable switches in staging.” S37 | Receipt-checked configured alert adapter, bounded local operator cycle, fixed server profile, real isolated receiver tests. | No actual staging host, real receiver/human escalation, provider operation or entire clause/dependency acceptance. Existing closed health/backup/restore/switch checks were reused, not reimplemented or counted as new work. |
| M6-05: “Exercise service load, support recovery, purchase reconciliation and feature disable controls with real opt-in testers.” S30,S37 | Disposable local authenticated/health HTTP and TLS concurrent load; explicit controlled failure recovery. | No real opt-in testers, support/reconciliation exercise, or observed-session denominator. |
| M7-04: “Version-compatible config rollback, feature disables, capacity, backups and entitlement replay are rehearsed and documented.” S37 | Resource/request/worker configuration, repeatable load/failure tool, capacity limits and operator/stop recipes. | No funded-host capacity, Linux cgroup enforcement, production rollback or real provider replay. Preserve newer data; use compatible forward repair. |
| S38 / M7-08 / OPS-14 | Existing handover's unstaffed/unknown status is retained. | Zero actual launch days, public endpoints, assigned operators or installed recurring schedules. |

## Concrete implementation

- `operating_config.py`: strict duplicate/nonfinite/type checks; absolute owner-only bounded regular inputs, no symlinks and nonblocking opens before fstat.
- `deployment.py`: pinned Gunicorn 26.2.0/packaging 26.3; literal loopback HTTP or explicit direct TLS ≥1.2; 1–4 sync workers, requested bounded backlog, 2–30 second worker timeout, request header limits, recycling, no ambient overrides/proxy trust, no sensitive request logging, 512-descriptor/core-dump process policy.
- `alert_transport.py`: disabled by default; one/two explicit private recipients, fixed categorical health projection, normal verified HTTPS, receipt and delivery-ID validation, no redirect, 4096-byte receipt bound, ≤3 killable attempts per recipient. Internal child also requires the same enabled private config digest. Receiver acceptance never means human acknowledgement.
- `operator_cycle.py`: nonoverlap POSIX lock, existing health command bounded to 15 seconds, fixed critical signal on health failure, delivery failure distinct from health severity, no scheduler or participant data.
- Linux service templates: proposed memory/task/CPU/process-group budgets, manual bounded one-shot execution. They are not installed and their Linux resource enforcement was not qualified on the macOS author host.
- `rehearse_deployment.py`: no remote-target option; disposable loopback databases and synthetic verified TLS; records actual response timing, PID transitions and bounded RSS samples, cleans up processes/fixture credentials afterward.

## Actual checks

The frozen copy passed 22 focused tests in `author-tests.log`, including real receiver HTTP acceptance/retry/wrong receipts/oversize/no redirect/lost time budget, disabled behavior, safe projection, private input rejection, FIFO no-writer subprocess, config bounds, overlap lock and actual missing-database health delivery. An additional actual subprocess regression forces the author runner deadline and verifies its sleeping child is no longer running; server/alert children inherit the dedicated verification process group. A mock is used only for otherwise difficult health subprocess timeout/malformed-output paths; these are not mislabeled actual hung health observations.

Nine actual server scenarios passed in `rehearsal/report.json`: HTTP and TLS each performed 64 health requests and 64 authenticated entitlement reads with eight concurrent clients (256 total, all 200); both exercised request bounds and log redaction and actual host SIGKILL worker replacement. HTTP additionally exercised both sync workers stalled on incomplete request bodies, observed supervisor timeout and replacement, then successful health recovery. Rehearsal injected hostile ambient Gunicorn arguments; the observed worker ceiling remained two.

Final local p95 latencies were 9.64 ms HTTP health, 10.89 ms HTTP authenticated, 19.47 ms TLS health and 17.78 ms TLS authenticated. These tiny local fixtures are a smoke/load sample, not sustainable public capacity or a product SLA. The maximum worker RSS sample covers the local health workload only; it does not prove configured Linux memory limits or long-duration growth.

Host SIGKILL and worker timeout are controlled process stops, not native fatal diagnostic evidence, player crashes, physical power-loss or observed sessions. Response loss during a general mutation remains unknown until reconciled. The fixture's incomplete JSON bodies did not execute an account mutation; do not generalize that fact to arbitrary killed requests.

## Preserved findings

- Initial author test rejected the operator's malformed-health handling: it accessed missing status instead of generating a failure signal. Repaired with strict health schema/status/exit agreement validation even when delivery is disabled. Raw failure: `../deployment-preparation/unit-initial.log`.
- Initial real TLS rehearsal returned from HTTP readiness before its second worker spawned. This was a harness observation race. Added a bounded worker readiness wait; failure remains at `../deployment-preparation/rehearsal-initial/`.
- Root independent OPS-PREP001 reproduced a blocking FIFO open. Repaired with O_NONBLOCK before fstat and an actual subprocess regression. Prior source remains at `../deployment-preparation/pre-fifo-repair/`; root's original/repaired probes are in `release/qa/lead-ops-preliminary-20261021T135354.446354Z/`. This one independently closed fix does not imply full deployment acceptance.

## Review and next operator prerequisites

Review source, replay focused tests and `services/rehearse_deployment.py` from the frozen copy using the pinned deployment virtual environment. Inspect actual report/log hashes. Independently challenge receipts/config changes, body/deadline bounds, overlap handling and secrets in error output. No Flutter or device execution is needed.

Before real activation: designate funded hosting and people; qualify Linux service-manager budgets, public TLS/certificate renewal, edge bounds/source-IP policy, actual provider and browser configuration, funded-host load/durable storage, secret/log retention, receiver durable deduplication/escalation, missed-cycle monitoring and delivered human acknowledgement. Keep the existing recovery/deletion-journal and launch-handover gates. Nothing here publishes an endpoint, contacts a person, installs a timer, accepts store transactions or alters canonical acceptance.

Earlier successful source snapshots at `deployment-20261021T135614369198Z` and `deployment-20261021T135903754934Z` are retained. The final snapshot adds process-group cleanup and its real subprocess regression; it is not a relabeling of earlier evidence.
