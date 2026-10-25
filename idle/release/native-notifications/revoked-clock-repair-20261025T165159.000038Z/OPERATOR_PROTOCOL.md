# Prospective revocation-clock protocol

This is a proposed test-only procedure for a **fresh** Android `revoked-prepare` / `revoked-recover` pair after independent review and promotion. It does not approve, repair, or reclassify the rejected f8d460 preparation or any prior failure. No permission-setting API, direct grant/revoke, reset, production change, deadline extension, or new Flutter harness is involved.

## Capture contract

The unchanged runner imports the reviewed helper and archives its bytes with the other exact sources. The helper automatically captures three `adb -s <selected emulator> shell date -u +%s.%N` receipts before its first live-process observation and pre-kill fixture export. It then verifies actual live PID/package → exact checkpoint/preferences/save export → actual live PID/package. Its `host_ready_stamp` is after that complete sequence. The operator must wait for the runner's actual preparation-ready handoff, as before.

After actual process death, the helper records the exact OS exit/PID/permission evidence, verifies unchanged fixture bytes, and captures three further device-date receipts. These all carry the same preparation identity and native PID, phase, actual stdout/stderr/exit, and host request/response `started_stamp` / `finished_stamp`. The unchanged runner pins `restart-host-receipts.json` in `evidence_sha256`, along with raw kill records and original saved files. Recovery recomputes the model from this hash-checked raw file, compares it to the report's derived model, and independently rechecks the event and causal sequence. There is no trusted offset scalar.

## Actual UI operator packet addition

Keep the exact observed Tideglass Settings ON/OFF XML, raw screenshots, originating activity/PID route, and actual single grounded `input touchscreen tap` receipt. No guessed coordinates or automatic permission APIs. Add:

- `host_timeline` with exactly `before`, `action_started`, `action_finished`, `after`. Each value is the actual `reminder_restart.host_stamp()` result: UTC nanoseconds bracketed by two monotonic nanosecond reads. Keep the original four `*_utc_ms` fields equal to `stamp['utc_ns'] // 1000000`.
- `before` is recorded after fresh actual ON XML/screenshot collection, after the runner's preparation-ready handoff. Then obtain an actual PID receipt proving the sole bound native PID is alive. Start the one observed tap within five seconds of that receipt.
- `action_started` and `action_finished` bracket the actual tap command. Record its real argv, exit status, stdout/stderr through the existing operator receipts. No retry.
- After the command returns, obtain an actual PID receipt showing it is absent. Then collect actual OFF XML/screenshot and take `after`. Complete OFF observation within 30 seconds of tap start. A process that is still present or replaced cannot qualify.
- Add `pid-observations.json` to the existing `files_sha256`, making six required operator files. It contains exactly the before/after actual `adb -s <same emulator> shell pidof dev.tideglass.game` receipts, with the same stamp/legacy-ms fields as helper command receipts, actual argv/exit/stdout/stderr. Before must be exit0 with the sole expected PID; after must be exit1 with empty stdout/stderr. Hash this actual file. Using `Host.command` for just these two reads records this schema; use a separate operator Host instance and do not overwrite the runner's receipt file.

`host_stamp()` must execute at observation time on the same host. Do not reconstruct monotonic timestamps later, substitute nearby runs, stamp archived observations anew, or attach the later diagnostic to the old event. UI XML after app launch remains prohibited until native framework termination under the separately reviewed semantics procedure; the OFF XML here is taken while the killed process is absent, before any recovery launch.

## Time-domain reasoning and quality bounds

For each read-only device sample `D` during host request `[Hstart,Hend]`, the measured host-minus-device interval is `[Hstart−D,Hend−D]`. The three intervals in each phase must intersect; the pre/post phase intervals must overlap. The model retains the conservative envelope of both phase intersections, never a midpoint or arbitrary fixed offset. Samples are exact increasing nanoseconds, same identity/PID, and chronologically ordered by host monotonic time.

| Check | Bound and meaning |
|---|---|
| Host wall read | Monotonic bracket ≤1 ms |
| Device-date request round trip | ≤250 ms |
| Observed host wall-minus-monotonic drift | ≤5 ms across all sample, export, ready and operator receipts |
| Measured offset envelope width | ≤100 ms |
| Whole pre/post measurement span | ≤210 s (original180s event window plus at most30s post observation) |
| First prospective sample | After actual native marker, within30s, in device epoch |
| Actual kill | Strictly after last pre sample and no later than first post sample, in device epoch |
| First post sample | Within30s of actual kill, in device epoch |
| Original marker→kill bound | **Unchanged ≤180 s**, device epoch on both sides |

The bounds reject measurement quality problems; they do not add guessed slack to the event. Disjoint pre/post offsets or host wall/monotonic inconsistency fail closed. A finite sample set cannot exclude an unobserved clock excursion that returns between probes. Qualification is bounded by the observed stable-clock model, measured uncertainty, and independent causal evidence; it is not perfect synchronization.

ApplicationExitInfo is millisecond precision. Its translated host interval includes that one-millisecond resolution plus measured offset uncertainty and must intersect the actual tap-start → OFF-observed interval. An asynchronous OS kill may occur **after the tap command completes**. This check does not claim that the kill happened within the shell-command interval or that interval overlap alone proves causation. Fresh ON → live PID → one actual tap → absent PID → OFF, matching package/reason8/PermissionHelper, native180s limit, and pre-kill live→export→live supply the causal evidence. `restart_death.observed_utc_ms` is retained as descriptive host time only and is not used as a device event bound.

If any fresh packet fails, preserve it and diagnose; never relax the180s window, measured limits, original save/source/pending/permission checks, or native framework-success requirement to pass. Successful preparation remains `passed:false`, expected OS interruption. Only a separately validated recovery can complete native qualification.
