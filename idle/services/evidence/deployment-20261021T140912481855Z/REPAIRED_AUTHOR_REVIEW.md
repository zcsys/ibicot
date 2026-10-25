# OPS-GE001 / OPS-GE002 author repair

The two independently reproduced validation defects are repaired on a new frozen source pin, `2173e6ec85a78cbc72df5dc87e91bb5355dda80ad918d888a6c96bd0f2a60d87`. Independent re-review remains pending. This is not a change to original scope or release acceptance.

- **OPS-GE001:** the alert envelope now requires overall severity to equal the actual signal aggregate, using the existing health order **critical > unknown > warning > OK**. It rejects both understated and overstated severity. The operator's existing validation catches this failure and replaces malformed output with a critical `health_command_failed` signal and exit 2, even when delivery is disabled. It cannot retain a forged warning/exit 1 when a critical signal is present.
- **OPS-GE002:** the serving configuration rejects a non-string host before calling `ipaddress.ip_address`. Numeric `2130706433`, floats, booleans, null and lists can no longer exploit address coercion while leaving a different Gunicorn bind string. The existing parser still requires IPv4, and loopback mode still requires literal `127.0.0.1`.

Only four input files changed: `alert_transport.py`, `deployment.py`, their focused author test file and two narrow documentation sentences. The exact before/after hashes and the complete small diff are pinned by `repair-handoff.json` and `OPS-GE001-002.diff`. Operator, API, health, provider, browser, economic and mobile runtime source is unchanged.

The new exact-source replay passed **25 author tests** and **nine real local HTTP/TLS scenarios**, including 256/256 concurrent health/authenticated requests. Snapshot and live input rehashes reported no drift. The three new regression methods exercise all signal-severity combinations, operator fallback from a forged downgraded health result, and strict host types with an unchanged valid literal bind.

The different-author probe file from `release/qa/gameplay-ops-review-20261021T140405144186Z/independent_ops_probes.py` was copied and hashed, then replayed by this author from the frozen source: **12/12 methods passed**. The original independent run had nine passing methods and three failing methods covering precisely these two findings. This author replay is supporting evidence, not the reviewer's closure decision. The probe/log hash, command and cwd are in `repair-handoff.json`.

All original d92c source, 22-test/nine-scenario proof and independent failing evidence remain intact. `services/evidence/deployment-preparation/FINAL_HANDOFF-before-ops-ge-repair.json` preserves the previous latest pointer. The original local handoff's boundaries still apply: no public hosting, installed scheduler, real alert recipient, human acknowledgement, physical/native evidence, observed sessions, Linux resource qualification or 14-day coverage was introduced.

The source is frozen for independent re-review; no further edits are planned during that review.
