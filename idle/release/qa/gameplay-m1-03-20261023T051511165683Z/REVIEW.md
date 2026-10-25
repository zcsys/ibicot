# Original gameplay-role review: M1-03 crash-safe local saves

**Recommendation: the shared implementation and current iOS process-interruption clauses are supported. Keep M1-03 target qualification open until the current Android save/lock and transition appendix is terminal, sealed and reviewed.** No pending Android result is accepted here. No production defect was found in this focused inspection. No program, scope, production source or prior evidence file was edited.

This is the original `gameplay` reviewer recommendation for M1-03, not release approval. The original clause is preserved verbatim:

> Atomic saves, rolling backups, checksums, export/import and versioned migration recover from interruption without double rewards.

The sole original prerequisite remains **M1-02**, whose program status is `accepted`. The original owner remains `platform`, reviewer `gameplay`, and linked requirement S12. S12 still requires runtime fault injection after contract validation; schemas alone do not establish acceptance. No extra account, human study, released historical economy, physical-device or sudden-power-loss condition is introduced into this local implementation clause.

## Source and evidence identity

Candidate: `.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122`.

- Source fingerprint: `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`.
- Candidate manifest SHA256: `b4322606cd0207425b801feacc0bf4084ac9c460b23a028576204b766eeaeada`.
- Sealed phone terminal checkpoint SHA256: `e6ed8e685ba0fd9d697261ffa02354def41be377588c03bbe649bfaa39b3a303`.
- Different-author current native QA: `release/qa/current-native-20261023T044903.849353Z/REVIEW.md`, `CLAUSE_MATRIX.md`, `clause-source-bridge.json` and `seal.json`.

The 13 selected persistence/core-migration/client source and test files match both the frozen candidate manifest and current working-tree bytes. `recheck.py` independently verifies all output pins in that earlier QA seal and every archived evidence pin for the nine selected iOS cells. Its **291 recorded assertions** cover **193 unique input files**, **nine native cells** and **14 save envelopes** with no before/after drift. The assertions are evidence-validation counts, not 291 newly executed game tests. Each saved envelope's recursive canonical JSON SHA256 is recomputed independently in Python. Fourteen one-field corruption controls are rejected by that checksum calculation; these controls do not claim to rerun the Dart import API.

The current 28-case persistence host log has the successful terminal marker and was already inspected in the different-author current QA bridge. This review does not repeat closed host suites or run Flutter, mobile/device commands, subprocesses, process signals or network operations. The raw native kill/termination commands are inspected as archived data only.

`inputs/program.json` and `inputs/v1_backlog.json` preserve the criteria snapshot. The earlier whole-program pin differs because root appended M3-10 evidence and its evidence note; the complete M1-03 record remains byte-equivalent as parsed data to the earlier sealed record. No status, clause, dependency or reviewer was changed for this review.

## Clause-by-clause assessment

| Original obligation | Actual implementation and evidence | Recommendation at this cutoff |
|---|---|---|
| Atomic saves | `game/persistence/lib/tideglass_persistence.dart:303` writes a same-directory pending generation with `flush: true`, then renames it over the selected parity slot. Payload and settlement cursor are inside the same checksummed envelope. No independently updated reward cursor is used. Current native kill/recover fixtures interrupt before write, after flush, and after rename. | Supported on shared host and current iOS for process interruption. Current Android execution remains pending. |
| Rolling backups | Two alternating committed generations retain the immediate predecessor. `_read` validates both, selects the highest valid revision, checks parent identity and contiguous lineage, reports corrupt-generation fallback, and refuses an all-corrupt silent restart. The current host corruption/backup cases pass. All two-generation native captures inspected here have exact parent identity and consecutive revisions. | Source and runtime fixture obligation supported; no claim of unlimited historical backups. |
| Checksums | SHA256 covers recursive canonical JSON, including state, cursor, versions and lineage. Decode rejects corrupted bytes before payload selection/import. The focused replay recomputes all 14 selected captured envelopes; every checksum matches. | Supported. This is integrity checking, not authentication against intentional local-save editing. |
| Export/import | Export selects the current committed envelope under the same writer lock. Import validates before replacing, creates a new branch, preserves the displaced branch in recovery storage, clears the ownership display cache and transition receipt, and does not add progress from two branches. Explicit corrupt recovery preserves raw files. Current host tests cover altered-checksum rejection, branch selection, retained recovery copy, huge exact integer strings and fractional cursor survival. | Shared implementation and executed host clauses supported. Explicitly selecting an earlier branch is intentional rollback, not a normal-save reward replay. No native share-sheet or cloud/store delivery acceptance is implied. |
| Versioned migration | Strict core decoding accepts explicit schemas 1/2/3/4 and rejects unknown economic/event-order identities. Genuine prior-schema fixtures preserve exact money and frozen legacy deny-lists; repeated upgrade remains stable. Client validators also bind main/season/pending-replay cursors. Economic-rule migration additionally requires a code-owned compatible predecessor with both source/destination cursor validators; unknown rules reject before replacement. | Source and host migration clauses supported. Native iOS synthetic old-rate transition/reopen passed; same Android path remains pending. No historical released economy or arbitrary remote migration is invented. |
| Recovery without double rewards | Normal writes cannot rewind the committed cursor. Stale writers fail revision/save/branch checks. Structured replay identities and exact cursor/remainder round-trips are covered by current core/mobile host cases. Native interruption recovers old/old/new generations, then makes one new successful commit. The separate actual bootstrap transition earns 90 R under old rules, adds 1 R under baseline and stays at 91 R when reopened at the same cursor. | Supported in the reviewed bounded cases. Native amount fixtures prove commit selection/exclusion; actual-core host and native transition evidence supply economic replay coverage. No universal absence-of-defects claim is made. |

## Actual iOS interruption results

The process interruption rows are **expected interruptions, not passing test completions**. Their paired recovery executions are passing cells. The review confirms the captured pre-kill log prefix, one actual recorded SIGKILL bound to the native PID, immutable checkpoint binding, a distinct recovery PID, correct saved amount and successful later write.

| Boundary | Killed PID → new recovery PID | Value loaded after interruption | Value committed after recovery | Evidence |
|---|---:|---:|---:|---|
| `beforeWrite` | 68331 → 69053 | 0 | 2 | `current-runtime-ios-phone-20261023T043259564984Z` / `...043347563069Z` |
| `afterFlush` | 69785 → 70567 | 0 | 2 | `current-runtime-ios-phone-20261023T043434202567Z` / `...043522664543Z` |
| `afterRename` | 71300 → 72030 | 1 | 2 | `current-runtime-ios-phone-20261023T043612069360Z` / `...043658778696Z` |

All evidence paths in that table are under `release/native-proof/`. The separate `runtime-lock-exclusion` execution holds the actual native FFI lock in one isolate, observes the contender still waiting, releases the first writer, then rejects the stale contender. This tests cooperative application writer exclusion. The stable lock file is not unlinked; kernel descriptor closure releases the lock after process death.

The two economic-transition executions use PIDs 72756 and 73513. Their source explicitly registers a synthetic 1.5 R/s predecessor for the first bootstrap only. Sixty old seconds yield exactly `90000000` currency micro-units. The later default bootstrap yields `91000000` after one baseline second and verifies no change on a same-cursor reopen. The shipping predecessor registry remains empty.

These are iOS simulator executions, recorded as Version 26.3.1 (Build 23D8133), against the current candidate. They demonstrate process death and recovery, not sudden device power loss, filesystem durability under physical storage faults, hostile same-user file replacement, or a production crash-free rate. Those distinctions limit the claim; they do not add new gates to the quoted M1-03 clause.

## Reviewer independence

This gameplay reviewer authored earlier core and transition/flock changes. The source inspection above is therefore **not claimed as independent reapproval of those authored components**. Their independent component basis remains `/root/qa_integration`'s `release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md`, which reran the 28 persistence cases, wrote/reran 12 additional transition probes, reproduced the old FileLock failure, and checked the repaired alias/nested-callback and receipt behavior. Its initial failures and repairs remain preserved. The current native execution author is separate, and `/root/qa_release` independently replayed the sealed current iOS evidence. This recommendation reconciles those different-author findings with the unchanged original gameplay-reviewer clause; it does not substitute self-review for them.

The focused Python verification in this directory is newly authored evidence checking. It verifies real input pins, exact checksums, generation lineage and result/predecessor identities, and explicitly retains the prior independent-review attribution. It does not assert that checking a success label alone proves correctness.

## Exact remaining gate

Receive and review a **sealed terminal Android appendix for this candidate** containing:

1. Actual Android native `libc.so` / `flock` exclusion, release and stale-writer conflict. iOS/macOS symbol resolution is not evidence of Android symbol availability or behavior.
2. `beforeWrite`, `afterFlush`, `afterRename` externally interrupted preparations and separate-process recoveries with old/old/new selected state; retained generations, checksums, kill/checkpoint/PID binding, and one later successful write. Keep interrupted preparations classified as expected interruptions.
3. Actual Android compatible-transition start/reopen showing old-rule settlement once, new rules only after the boundary, and unchanged same-cursor replay. Bind all logs, harness and result bytes to the candidate, including any explicitly reviewed test-only harness delta.

The current Android batch is active and is not counted. Builds, elapsed waiting or an unsealed progress message cannot close this gate. After its reviewed completion, the director may adopt the original M1-03 recommendation with M1-02 unchanged; no additional broad host-suite rerun is requested absent changed source or a new finding. This report does not accept S28 release-wide zero-major-defect status, verified purchases, cloud account recovery, physical performance or the finished v1 release.
