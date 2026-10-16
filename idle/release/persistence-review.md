# Independent persistence implementation review

Reviewer: `/root/gameplay_engineer`. Implementation author and repair owner: `/root`. Reviewed 16 October 2026.

**Result:** the implemented local persistence subset passes this non-author host review after three repaired defects. This does not accept the complete M1/M3 save/claim scope, native power-loss durability, cloud recovery, migrations from released versions, or verified commerce.

## Repaired findings and independent reruns

| Finding | Impact | Repair and verification |
|---|---|---|
| P1: fractional cursor truncated to a whole second | A fully simulated fractional interval could be earned again after reload | Runtime preserves microseconds; the envelope accepts one to six fractional digits. An independent real-core test advances 10.123456 s, saves/reloads, then advances to 20 s and proves exactly 20 R total |
| P1: normal save accepted a settlement cursor earlier than the committed cursor | Subsequent return settlement could replay already earned time | Normal save rejects cursor rewind. Independent test checks the previous snapshot ID/cursor remain unchanged after rejection. An explicit selected-branch import can deliberately restore older progress |
| P2: `save_id` reused while parent referenced the same ID | Runtime snapshots contradicted the reviewed envelope's unique snapshot identity and no-self-parent invariant | Each snapshot gets a fresh ID; parent links the previous ID. Independent integration checks both identities and invokes the existing Python schema validator on an actual saved envelope |

All three fixes were made by the implementation author. The independent reviewer reran original reproductions against the repaired runtime; no exception was accepted merely because a unit test expectation changed.

## Executed evidence

| Command / suite | Result |
|---|---|
| `../../tool/dart test test/persistence_integration_test.dart --reporter expanded` from `game/core` | 8/8 independent integration tests pass |
| `../../tool/dart test --reporter expanded` from `game/persistence` | 18/18 implementation tests pass |
| `../../tool/dart analyze` from `game/core` | No issues found |
| `python3 implementation/tools/validate_save_contract.py --config economy.json` from repository root | 47/47 envelope cases pass |

The independent tests are retained in `game/core/test/persistence_integration_test.dart`. They use actual `GameState` quantities and `TideglassEngine` advancement through the production repository, rather than a simplified floating wallet fixture. Covered paths:

- Exact quantities beyond `2^53`, including a 120-digit wallet and retained fractional earning numerator, survive JSON/file round-trip.
- Fractional elapsed settlement is not replayed after reload.
- Normal writes cannot rewind the committed cursor.
- Native repository output conforms to the reviewed envelope and pinned economic digest.
- A stale real-core writer cannot overwrite newer progression.
- An injected failure after the committed rename reloads the advanced cursor, so the same interval earns no second reward.
- Explicit import chooses the imported progression and preserves the displaced snapshot; wallets are not added.
- An unavailable economic configuration is rejected before settlement or overwrite.

Read review also checked the checksum verification path, alternating committed generations, captured input copy, repository revision preconditions, explicit recovery/import semantics and untrusted commerce display cache. Author tests exercise corruption, checksum changes, interleaved writers and interruption before write, after flush and after rename.

## Remaining boundaries

The local checksum detects corruption; it is not a cryptographic authorization mechanism against a user editing a local single-player save. The current runtime rejects nonempty pending operations and does not implement the service's durable entitlement/source-receipt ledger. Do not claim claim-level exactly-once guarantees from the local repository until that ledger and its retry/migration cases exist. Clearing display-only commerce data during import does not restore or revoke independently verified paid ownership.

Process interruption is exercised on the host filesystem. Actual mobile process lifecycle, filesystem behavior, abrupt power loss, backups under storage pressure and cross-device/cloud conflict paths remain native or service tests. The repository's caller still must supply the correctly simulated payload and corresponding cursor together; persistence cannot infer whether arbitrary payload income matches elapsed time.

The schema change preserves existing whole-second UTC saves and permits exact microsecond timestamps. Interval ordering now compares parsed instants, including whole-second/fractional mixtures. The clock may move backward for `written_at_utc`; the settled cursor for ordinary progression cannot.

The provisional core's broad economic and daily-system tests are separate evidence. This review is independent of the persistence author, but it does not independently certify the reviewer's own economy implementation.
