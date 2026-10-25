# Revoked preparation: clock-domain finding

**Do not authorize dependent recovery from this packet under the current protocol.** The native preparation is an expected OS interruption, `passed:false`, `errors:[]`; its operator packet is rejected. No completed revocation qualification or production defect is established. M3-05/S26 remain open.

The exact report is `release/native-notifications/integration-android-20261025T164440025420Z/verification.json` (f8d460bebd26e7bb63c61ae609f6dc57606a1b3a22442572c1f9c180eb3a2413). The separately sealed operator checkpoint is `release/native-notifications/revoked-restart-operator-20261025T164440025420Z/checkpoint.json` (355eb30af3a914e09c2c9a9885b1df21a8c19ee90d15c9aaf1d2f77e9ecc74d8). The original files remain unchanged.

## Actual observations

I viewed the raw Settings screenshots. They show the current Tideglass lighthouse identity with All Tideglass notifications ON before the grounded tap and OFF afterward. The exact PID 10359 was alive before export and absent afterward. A pre-kill checkpoint, opt-in preferences and two save slots were captured while the process was alive, with exact source/run/PID binding. Actual exit-info and logcat identify this PID's reason 8 PERMISSION CHANGE / PermissionHelper kill. Production differences are empty and installed artifact binding is intact.

The archived checkpoint and kill/host-receipt validators reproduce successfully; the exact operator rejection reproduces. This is not a completed native test and is not an approval of recovery. The setting, PID and OS evidence are useful, but the specific timing relation demanded by the protocol is not established.

| Observation | Raw time |
|---|---:|
| Device native preparation marker | 1792946709790 ms |
| Device exit-info kill, converted using device timezone +0300 | 1792946734623 ms |
| Host tap started | 1792946734991 ms |
| Host tap finished | 1792946735051 ms |
| Host observed death | 1792946735911 ms |

`tool/reminder_restart.py:225` compares the device kill timestamp directly to host action timestamps and requires the kill inside the 60 ms host command interval. The raw device kill is 368 ms before the host start. **Timezone conversion is not host/device clock synchronization.** The packet has no prospective same-run calibration of the two clocks. Therefore these numbers do not prove that the OS kill physically preceded the UI gesture; they prove that the current check assumes a clock relationship the protocol did not establish.

The same domain assumption appears in `kill_record` at line 103 (device event versus host observed time) and `validate_host_receipts` at lines 300–309 (host file/PID receipts versus device marker/kill). A narrow protocol repair should account for all affected comparisons, not add a fixed tolerance to one line.

A later read-only diagnostic at `release/native-notifications/revocation-clock-diagnostic-20261025T164645.898891Z/diagnostic.json` (637eb1f3ffd56701ad3f56498656b0baf47d8bf8b2d3979917229909988bc934) brackets the host ahead of the device by approximately 420–472 ms, 440–471 ms and 439–472 ms. Those raw samples and bounds are reproduced in this review. They were collected after the event. They support the clock-domain diagnosis but cannot retroactively calibrate this event or rewrite the packet. Likewise, the preceding S02 run's measured offset is not transferable proof for this revocation run.

## Minimal prospective disposition

Preserve this rejected packet and the prior revocation failures. Stage a test-protocol-only repair that captures explicit device/host timing brackets for the same new preparation and UI gesture, checks freshness/order and uncertainty, and retains actual ON→OFF, bound PID, PermissionHelper reason, pre-kill export, unchanged source/save files and strict recovery framework gates. Do not silently use an arbitrary fixed offset, ignore the ordering predicate, or relabel this packet as passed. If asynchronous kill timing extends beyond input-command completion, its bound must be explicit and checked against actual post-action observations rather than assumed synchronous.

This is a verifier evidence defect, not a diagnosed production notification defect. No Flutter/device work or source edits were performed by QA. The bounded replay completed 52 checks and pinned 43 files. My earlier independent protocol review missed this cross-clock assumption; this addendum corrects that review without rewriting its seal.
