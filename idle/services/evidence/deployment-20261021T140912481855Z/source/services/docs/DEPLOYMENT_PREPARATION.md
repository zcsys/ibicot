# Bounded serving and alert-delivery preparation

This is implemented local preparation for **M5-04/S37**, and preparation for **M6-05/M7-04**. No listener, scheduler, receiver, operator identity or public endpoint is activated by importing these modules. The existing development runner, API, provider factory, health, backup/restore and feature-switch implementations are unchanged.

The original M5-04 sentence is “Validate economy/session events, entitlement dashboards, alerts, backups, support receipts and feature disable switches in staging.” M6-05 requires service load, recovery, reconciliation and controls **with real opt-in testers**. M7-04 requires compatible rollback, feature disables, capacity, backups and entitlement replay rehearsals. This package contributes local serving/alert/load machinery only. It does not satisfy those complete sentences or dependencies. S30's observed sessions and S38's 14 actual days remain wholly separate. Existing operating and launch handover documents remain authoritative for those open gates.

## Serving profile

`python -m services.tideglass_service.deployment --config /absolute/private/serving.json` loads only an explicit owner-only JSON file. `--check` validates configuration, installed dependency versions and TLS material without binding or initializing a database. File paths must be absolute; database directory is private and already exists. Run as a dedicated unprivileged account. The optional `service_config` points to the existing private provider/browser configuration; absent configuration retains disabled providers.

| Variable | Implemented bound | Interpretation |
|---|---|---|
| Dependencies | Gunicorn 26.2.0, packaging 26.3; hashed wheels | Separate optional environment; existing provider lock is unchanged. |
| Connection mode | `tls`, or explicit `loopback_http` at literal 127.0.0.1 | Public bind without TLS is refused. TLS needs `certificate_file` and `private_key_file`, private files, matching certificate/key, TLS ≥1.2. |
| Workers | 1–4 sync processes, one request each | Example uses 2; environment Gunicorn options are discarded. No thread pool or HTTP/2. |
| Worker silence timeout | 2–30 seconds, example 15 | Gunicorn kills a silent sync worker; detection adds its monitor scheduling delay. This is **not** an exact end-to-end request SLA. |
| Backlog | requested 1–128, example 32 | Kernel pending-connection setting, subject to OS behavior; not an application queue-depth guarantee. |
| Recycling/shutdown | 10–1000 requests plus up to 10 jitter; 10-second graceful timeout | Killed requests may lose a response. Never infer non-commit from disconnection. |
| Request headers | line 2048 bytes, ≤32 fields, each ≤4096 bytes | API already caps body at 2 MiB + 64 KiB and enforces endpoint rate limits. |
| Trust/logging | no forwarded headers/proxy protocol; no access logs | Only fixed event categories and OS PID are logged, never request bytes, tokens, provider bodies or tracebacks. |
| Process limits | 512 descriptors, core dump disabled | Applied before worker creation. Linux example additionally proposes 512 MiB memory, 32 tasks and 200% CPU for the whole service group. |

Gunicorn's [settings](https://gunicorn.org/reference/settings/) and [sync-worker design](https://gunicorn.org/design/) describe the timeout and one-request-per-worker behavior. The exact package pin was checked against [PyPI](https://pypi.org/project/gunicorn/26.2.0/). Version upgrades require a new qualified profile; this is not a promise of future security support.

Install a new isolated serving environment, not the native build environment. From the repository root:

```sh
python3 -m venv /absolute/serving-venv
/absolute/serving-venv/bin/python -m pip install --require-hashes --only-binary=:all: -r services/requirements-deployment.lock
```

If configured provider/browser features are required, also install the existing exact `services/requirements-providers.lock` into that environment and run the existing provider-environment checker and provider tests. The current author HTTP/TLS serving rehearsal deliberately uses the default disabled-provider factory; it does not qualify real provider credentials or public deletion routing.

Copy the loopback example, replace the absolute directory, make it 0700 and the config 0600, then run `--check`. For TLS, use mode `tls`, an explicit IPv4 string host (numeric JSON values are rejected), port ≥1024 and the two certificate fields. Certificate acquisition, public DNS and a public operator are not provided. HTTPS hostname/chain validity must be verified from the client side before activation. The rehearsal uses a one-day synthetic self-signed certificate trusted only by its isolated client; it never disables certificate checking.

The Linux systemd examples are **uninstalled templates**, with 512 MiB/32-task/CPU bounds for serving and 256 MiB/8-task/55-second runtime for the one-shot operator. Provision paths and OS identity, configure retained-journal limits and verify the target host's cgroup/systemd enforcement. No Linux cgroup limit was measured on this macOS author host. A layer-4 TLS pass-through edge may precede this direct-TLS profile. An HTTP reverse proxy or TLS terminator requires a separately reviewed source-IP/scheme policy; do not enable blanket forwarded-header trust. Confirm edge connection/rate controls and certificate renewal under the real hosting plan.

## Alert adapter and receiver contract

`alert_transport.deliver` is disabled with no config or exactly `{"version":1,"enabled":false}`. Enabling requires explicit recipients and a bounded private bearer credential file. No email, messaging provider, analytics, cookies or ambient proxy settings are used. Nothing sends to an external operator in the author tests.

Example structure (reserved invalid hostname, not a configured service):

```json
{
  "version": 1,
  "enabled": true,
  "environment": "staging",
  "recipients": [
    {"id":"primary", "url":"https://receiver.example.invalid/tideglass", "token_file":"/absolute/private/receiver-token"}
  ],
  "attempts": 3,
  "attempt_seconds": 5,
  "backoff_seconds": 1
}
```

Recipient/environment IDs are nonidentifying operator-chosen labels. There may be one or two unique configured recipients. Credentials are 24–256 ASCII token characters in owner-only files, never arguments/stdout/logs. URLs cannot carry userinfo, query parameters or fragments. Production requires HTTPS with normal certificate validation. Tests alone use `allow_loopback_http:true` and literal 127.0.0.1. The internal child protocol also validates the enabled private configuration and its exact digest; it is not a bypass entrypoint.

Each POST contains format `tideglass-operator-alert-v1`, environment, generated UTC time, severity, predefined categorical `{check,status,code}` signals, a SHA-256 `delivery_id`, and `release_gate_verified:false`. Overall severity must equal the signal aggregate in the order critical > unknown > warning > OK; contradictory reports are rejected. Raw report details, counts, account IDs, file paths and arbitrary future codes are omitted; unknown codes become `unrecognized_health_code`. `Idempotency-Key` equals the delivery ID. A receiver must authenticate the bearer, durably deduplicate by delivery ID and acknowledge only after durable acceptance with HTTP 200 or 202, JSON content type, and exactly:

```json
{"accepted":true,"delivery_id":"the received 64-character SHA-256 identity"}
```

Redirects are refused, receipt bodies are ≤4096 bytes and a 2xx alone is insufficient. Each attempt is a subprocess killed at the configured 1–5 second deadline, including blocked DNS or trickled responses. There are ≤3 attempts and ≤1-second fixed backoff, sequentially for ≤2 recipients: maximum configured network/backoff budget 34 seconds plus process overhead. There is no hidden queue or infinite retry. Retries reuse the identity; a later health cycle creates a new timestamp/identity. Configure receiver-side escalation, retention and repeat-alert grouping before real use.

A matching receiver receipt is **not human acknowledgement** and the output always says so. A lost receipt means delivery is incomplete even when the receiver may have accepted the request. Do not announce “operator notified” or reclassify critical health as healthy because transport succeeded. No actual receiver policy, on-call schedule or primary/secondary human assignment exists in this package.

## Bounded operator cycle

From the frozen release root and its explicit serving/provider virtual environment:

```sh
python -m services.tideglass_service.operator_cycle --database /absolute/private/service.sqlite3 --lock-file /absolute/private/operator.lock --backup /absolute/private/backup.sqlite3 --alert-config /absolute/private/alerts.json
```

This invokes the **existing** health CLI in a subprocess with a 15-second deadline, then delivers only its safe signal projection. A timeout/malformed result becomes a critical fixed operator signal. Missing databases are not created. A private nonblocking POSIX file lock rejects overlapping cycles; leave its inode in place after completion. Closing or killing the process releases the kernel lock. The proposed service manager kills the entire cycle process group after 55 seconds, including children; an unexpected filesystem hang is thereby separately bounded. No scheduler is installed.

| Exit | Meaning |
|---|---|
| 0,1,2,3 | Existing health result: OK, warning, critical, unknown; inspect delivery state separately. |
| 4 | At least one configured receiver did not return a valid receipt. |
| 5 | Another cycle holds the lock; do not start competing workers. |
| 6 | Invalid configuration or execution failure; no successful cycle is claimed. |

Proposed future cadence is one health/delivery cycle per minute, with receiver grouping/escalation and a separately staffed missed-cycle alert. A process that never runs cannot notify about its own absence. Validate this cadence with the designated operators before installing anything. Retain only bounded categorical results; schedule prune/reconciliation and encrypted backups using their existing independently reviewed recipes and limits. This package does not redo or activate them.

Stop rollout on unexpected save/ownership mutation, unbounded queue/resource growth, failed delivery, repeated worker exits, provider reconciliation failure or incorrect deletion/consent behavior. Preserve the newest supported data and use compatible forward repair; never run a newer save/database through an unsupported older executable. Response loss around a mutation is **unknown**, requiring the endpoint's existing read/reconciliation path. Worker replacement is availability behavior, not proof that in-flight writes did or did not commit.

## Reproduction and scope limits

```sh
python3 -m unittest discover -s tests/services/operations -p test_operating_delivery.py -v
.tooling/deployment-venv/bin/python services/rehearse_deployment.py --output /absolute/new-empty-evidence-directory
```

The rehearsal has no target-URL argument and binds literal loopback only. It creates disposable synthetic databases, a synthetic TLS certificate and fresh server processes, then stops them and deletes all fixture credentials/database files. It records only timings, status counts, worker PID/RSS samples and redacted logs. Raw failed attempts remain preserved.

Local tests exercise fixed limits, actual authenticated/health HTTP loads, host-killed worker replacement, incomplete-body timeout recovery, secret-free logs, receipt failures/retries/timeouts and overlap handling. They do not estimate funded-host capacity, sustainable production throughput, long-term memory growth, real purchase reconciliation, real opt-in testers, public TLS/deletion endpoints, delivered human escalation, native crash rates or 14-day coverage. Only independent review may accept this narrow local preparation.
