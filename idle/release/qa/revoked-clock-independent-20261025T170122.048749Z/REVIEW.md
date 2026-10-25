# Independent prospective revocation-clock review

**Approve the exact three staged test-only files for prospective use with a fresh preparation/recovery pair.** No production code, Dart harness, original deadline or acceptance criterion changes. This approval does not admit the old rejected preparation or establish successful native recovery.

Author packet: `release/native-notifications/revoked-clock-repair-20261025T165159.000038Z/AUTHOR_HANDOFF.md` (1e4397708cdc07d94ff76588d29a0fcb1f3cd3837b88df7aa584fc5d0b2504bd), verification9174d82701ce127801c11210ec901a77df3823fb63302c896098d4d29568bdaa.

| Intended promotion | SHA-256 |
|---|---|
| tool/reminder_restart.py | 5de097fd817e7fb49573e3a73c44ec805182d8dc107f1c86b8546bbb81dc63d0 |
| tool/test_reminder_restart.py | a26fbae8507bb8461859467d867401bb66289846b74a98e8d9783dc0b4ac82b7 |
| tool/test_reminder_clock.py | 11b003659a4798631d3d2a829fccd53fb588be9b8beb7185558498d750c1a2c7 |

The Dart harness remains de04f52b… and runner ddc801d4…. The proposed patch exactly reconstructs from the preserved baseline. Seven original functions (`checkpoint`, `permission`, `interrupted_errors`, `switch`, `recovery_errors`, `fixture`, `file_name`) remain AST-identical, preserving saved-state identity, actual permission, pending/active cancellation, disconnection and final framework requirements.

## Clock and causal reasoning

The helper records three actual device-date nanosecond samples before the pre-kill exports and three after death. Every sample is bound to the same run, device and native PID, with raw stdout/exit and host wall time bracketed by monotonic time. Raw receipts are hashed and the model is recomputed before recovery; an asserted scalar offset is insufficient. Measured request/response intervals produce per-phase offset intersections and a conservative envelope, avoiding a chosen midpoint or arbitrary event slack.

All three prior mixed-domain predicates are addressed. Marker→kill freshness is device epoch on both sides and retains the original180-second bound. Raw alive→exact export→alive ordering is checked in host monotonic chronology, with the ready stamp after the final live package/PID receipt. Device kill translation is a measured interval, including exit-info's millisecond resolution. Actual UI timing must be consistent with that interval and retain fresh ON→live PID→one grounded tap→absent PID→OFF evidence. An asynchronous permission kill may follow input-command completion.

The result means **timing consistency with the actual tap-to-OFF interval plus independent causal PID/UI evidence**, not proof that the kill happened during the adb command. The helper rejects stale/missing/reordered or cross-run samples, excessive request uncertainty, disjoint pre/post offsets, and observed host wall/monotonic jumps. Limits are documented measurement-quality checks:1ms stamp read,250ms round trip,100ms offset envelope,5ms observed host drift,210s total span and30s fresh bracket/observation windows. Finite samples cannot rule out an unobserved excursion that returns between probes; the author protocol explicitly discloses that boundary.

The operator procedure preserves observed UI actions and forbids reconstructed timestamps, borrowed offsets, direct permission APIs or reuse of the prior post-event diagnostic. The two PID receipts must be captured live with host wall/monotonic stamps and hashed in `pid-observations.json`. Preparation remains `passed:false` and expected-interrupted; only independently qualified new-process recovery can support the remaining clause.

## Reproduction and retained evidence

From the repository root, with bytecode writes disabled, I independently executed:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=release/native-notifications/revoked-clock-repair-20261025T165159.000038Z/staged/tool:tool python3 -m unittest -v test_reminder_restart test_native_reminders test_reminder_clock
```

All67 methods passed (43 existing,24 focused). My separate review adds67 source/pin/admission checks over50 input files. Four additional complete-predecessor mutations deliberately recompute relevant evidence hashes so that substantive checks reject: ready before final export/live confirmation; another PID's raw clock receipt; observed absence before the tap; and export after the final alive receipt. The archived old f8d460… packet remains rejected for absent prospective `clock_model`, with every prior referenced native/operator byte unchanged. No retrospective timestamp correction or actual native pass is claimed.

The first failed clock packet and prior preparation stages remain immutable. QA previously missed the clock-domain assumption and recorded that correction in the separate finding; this new different-author review is limited to the client's repair. No Flutter/device action, live source promotion, canonical status change or broad matrix rerun occurred here. Root retains promotion and original-clause adoption authority. A fresh actual preparation plus independent UI packet review is required before dependent recovery.
