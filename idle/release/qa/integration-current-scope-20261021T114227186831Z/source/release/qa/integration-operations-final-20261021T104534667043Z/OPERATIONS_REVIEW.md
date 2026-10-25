# Independent operations review — repaired checkpoint

**OPS001 and OPS002 are closed at this source pin.** Seventeen independent adversarial cases and all 34 operations author cases pass. Four actual CLI rehearsal scenarios also pass. This is local component evidence, not original package acceptance or permission to activate a restored service.

The 40-input source-map fingerprint is `6acdf273bfae1a8012bce248157d23edb52ce3a19263d1a20ed3373676b15271`; final `health.py` SHA256 is `03cc85d2104833765d1a5f84ee8cab882571a11e83fc8199c7ee21e1e8407a3c`. Source copies and all test logs remain bound in `snapshot.json` and `verification.json`. Original 37-input author fingerprint `7b3a5742947907c7025790a56fe044f2832ecf0c2ccb46608e41ddca416f19a1` and initial failures are preserved under `integration-operations-20261021T103218323374Z`; the first incomplete repair and expanded failures are preserved under `integration-operations-repaired-20261021T103746604090Z`.

## Findings, repairs and reproduced evidence

| Finding | Original failure | Final result |
|---|---|---|
| OPS001: incomplete schema semantics | Missing vault singleton CHECK and changed primary-key collation accepted. The first repair still accepted extra/missing/modified nonunique indexes. LIKE `sqlite_%` also hid valid user objects such as a destructive `sqliteXhidden` trigger. | Known table and explicit-index DDL tokens, metadata, exact index inventory and literal reserved-prefix filtering now reject these altered structures. Actual existing vault/signer/reconciliation schemas remain accepted. |
| OPS002: future observations dilute failures | 100 current save events with two failures were critical; 200 tomorrow successes changed the sample to 300 and status to ok. | Current sample uses the closed timestamp interval [now-window, now]. Future receipt timestamps are excluded and separately critical. Now and now+1 boundary tests pass. |

DDL normalization permits harmless comments, whitespace and unquoted case changes while preserving quoted literals and CHECK/operator semantics. It is deliberately conservative: an unfamiliar equivalent spelling requires explicit review; this is not a general SQL semantic-equivalence parser. SQLite internal objects are omitted using a literal `sqlite_` prefix, not a LIKE wildcard. Three user-object types under a deceptively similar prefix are independently refused. An unexpected expression index was also shown to reject an ordinary seed write, establishing its operational effect beyond a metadata difference.

The original ten independent tests pass without changed expected outcomes. Six additional tests and one three-variant hidden-object case make the final 17. One intermediate reviewer harness mistake expected a `future_count` field when the actual report uses `count`; the error log is preserved and the field name was corrected. The expected count, timestamp boundary and critical status were not weakened.

## Verified local boundaries

A real recursive SQLite query is interrupted by a short configured SQL budget; the read-only connection refuses writes. Six CLI commands reject absent paths without creating a directory/database/destination. A live WAL-backed source produces a private new backup containing the committed marker, and an existing destination is unchanged on refusal. The checker permits SQLite shared-memory coordination, as documented; unchanged application rows/main-file bytes are not a claim that no WAL sidecar can exist.

Restore uses a unique private temporary copy and the real dispatch/storage implementation. The independent test observes deletion cascades through accounts, sessions, purchases, reconciliation, ownership leases, encrypted token rows and telemetry; key-binding history remains. The original backup stays byte-identical, temporary copies disappear after success and deadline failure, and output omits fixture account/recovery/bearer/key/ciphertext values. Seven adversarial manifest shapes reject. Existing source inventory/hash, FK and 20 dispatch checks remain in the author suite and actual CLI rehearsal.

The initial independent reproduction also ran the unchanged base-service suite (28 distinct cases; 50 invocations due imported tests) and provider suite (32 distinct cases). These results remain tied to that original snapshot; their source dependencies did not change in this operations repair. They are not misreported as new final-snapshot runs. Existing base-harness ResourceWarnings about unclosed SQLite connections remain in the log. Final operations/independent checks passed without those warnings.

## Limits and scope

The health budget bounds individual SQLite scans and row limits; it is not an end-to-end network SLA or proof of recovery on a busy host. Backup creation through the preexisting Database API has no new global timeout or offsite encryption/retention policy. A failed backup creation may leave an unusable destination for explicit inspection/removal; it is not silently promoted. No live database was selected for these tests.

Pending Google acknowledgement age remains the last provider observation, not the first grant. Telemetry is a retained, consenting operational-event sample, not all-installs retention or a qualified native crash denominator. Sparse/invalid observations remain explicit. Backup mtime is unauthenticated. Exact copied ciphertext does not establish key availability. The optional deletion manifest cannot establish complete post-backup deletion/consent/revocation/refund/lease history. Every successful drill remains ineligible for live activation.

Forward mapping: S27 receives local diagnostic/runbook evidence; S30 only operational signals; S37 local health, switch, backup and disposable recovery behavior; S38 an unstaffed template. S21 season/paid-pass/native migration is explicitly not established by this service drill. Reverse mapping connects health to M5-04, recovery/CLI to service portions of M5-04/M6-08/M7-04, and runbooks to M7-04/M7-08. The accompanying narrow scope audit preserves all 65 original acceptance/dependency records, all 44 reciprocal mappings, four accepted original foundations and three separate bootstrap contributions. It does not substitute for the pending comprehensive requirement-by-requirement current audit.

No new package is accepted. Hosting, approved backup/journal/key operations, delivered alerts, staffed responders, actual providers/devices, public support/privacy pages, real player observations, season/calendar coverage and 14 actual launch-support days remain outstanding. Separate local inventory, measurement-collector and export-cache work is also still active; external resource absence does not make those local tasks complete.
