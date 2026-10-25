# M1-03 gameplay-reviewer Android completion addendum

**Recommendation: accept the exact original M1-03 implementation clause and mark S12's persistence verification satisfied for the reviewed candidate.** The original prerequisite M1-02 is accepted. The previously pending Android target evidence is now terminal, sealed and successfully replayed. No remaining gate in this original local persistence clause was identified. Director adoption and metadata changes remain root-owned; this reviewer changed neither production nor status files.

This addendum supplements, without editing or replacing, `release/qa/gameplay-m1-03-20261023T051511165683Z/REVIEW.md`. Its prior cutoff and then-pending Android finding remain historically accurate. The original acceptance remains:

> Atomic saves, rolling backups, checksums, export/import and versioned migration recover from interruption without double rewards.

Its sole dependency remains **M1-02**; owner `platform`, original reviewer `gameplay`, and linked scope S12 are unchanged. S12 remains “Atomic saves, rolling backups, export/import, migrations and interruption recovery,” with verification “Contract validation is followed by runtime fault injection; schemas alone cannot pass persistence acceptance.” Actual runtime faults, rather than schema validation alone, support this recommendation.

## Exact sealed inputs and independent replay

Candidate `.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122` retains fingerprint `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59` and manifest SHA256 `b4322606cd0207425b801feacc0bf4084ac9c460b23a028576204b766eeaeada`.

The new packet is `release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-m1-03-20261023T054217.678143Z/checkpoint.json`, SHA256 `eb1f40c77da66ce4c1910c0c76a1085c1abb05f029e68eba005cd44593270256`. It contains **18 cells: 12 normal passes and six expected interrupted preparations**, split evenly between iPhone and Android. Interrupted preparations are never counted as passing tests.

This review's `replay.py` completes **497 recorded assertions, including 25 negative controls**, across **311 unique input files**, without drift. Counts overlap; they are not additive game-test totals. It:

- Rechecks the prior review seal, retains the original nine iOS report/archive pins, and compares relevant frozen/current production and test source bytes.
- Pins every report and archived log/checkpoint/harness/source file in the new nine-cell Android set.
- Calls the archived pure completion, scenario, interruption and predecessor validators against actual captured data, while blocking subprocess creation and process signalling.
- Independently reconstructs canonical JSON SHA256 for **14 Android saved envelopes**, verifies each exact byte sequence against its recorded Android private-storage read, and checks the committed generation lineage and integer amounts.
- Rejects incomplete completion, late native exceptions, wrong predecessor PID, damaged pre-kill prefix, fabricated completion in killed preparation, and Boolean values substituted for required integer amounts.

At final sealing, a whole-file drift guard detected concurrent root adoption of S05, S40 and S41. Only their status, evidence and verification-note fields changed; all original scope clauses, the complete S12 record and M1-03 remain unchanged. Both scope snapshots and the exact lead decision pin are preserved in `metadata-reconciliation.json`. The completed replay itself had no input drift. This unrelated metadata change is explicitly reconciled rather than hidden or treated as runtime drift.

No Flutter, emulator/device operation, native command, service call or closed host suite was run by this reviewer. The command is `python3 release/qa/gameplay-m1-03-android-20261023T054815140862Z/replay.py`. The initial attempt stopped before replay because the isolated review-tool copy omitted the `native_recording` import dependency. That initial log remains. The exact already-pinned dependency was copied into this review directory and the unchanged assertions then completed. This was review setup, not a production failure or accepted runtime result.

## Android results

The actual recorded target is `emulator-5556`, Android 15 `sdk_gphone64_arm64-userdebug 15 AE3A.240806.043 12960925 dev-keys`.

| Scenario | Actual native PID | Result |
|---|---:|---|
| `runtime-lock-exclusion` | 4240 | Actual Android FFI `flock` holds a separate-isolate contender; after release, the stale writer conflicts. |
| Before-write interruption → recovery | 5048 → 5370 | Kill selects old amount0; new process commits amount2. |
| After-flush interruption → recovery | 5667 → 5929 | Uncommitted pending write does not replace old amount0; new process commits amount2. |
| After-rename interruption → recovery | 6207 → 6483 | Already committed amount1 survives; new process commits amount2. |
| Synthetic old-economy transition → reopen | 6806 → 7146 | Old1.5 R/s ×60s =90 R; baseline1 R/s adds1 R; same-cursor reopen remains91 R. |

For each interruption the archived observations show the exact package PID alive, `/proc/<PID>/cmdline` identifying `dev.tideglass.game`, a successful recorded `kill -9 <PID>`, and subsequent absence. The pre-kill marker, full prefix bytes, checkpoint SHA, run/device/harness identities and recovery predecessor all agree. Each recovery is a separate process, and its latest saved generation is exactly the integer amount2. This proves actual lock release and old/old/new commit selection, not merely a test's success label.

Transition snapshots independently contain wallet and lifetime strings `90000000` at `2026-10-21T12:01:00.000Z`, then `91000000` at `2026-10-21T12:01:01.000Z`. The normal completion payload verifies the same-cursor second reopen. Synthetic predecessor registration is explicit; the production default registry remains empty. No shipped historical economy is invented.

## Retained failure and exact tool repair

The original Android before-write preparation `current-runtime-android-20261023T051542413435Z/verification.json` remains **failed**, SHA256 `fc847ee2532e600070f76884efba0d5b704dd337579d687455ed1564d8308eed`, with `ValueError: Native fixture component is a symlink`. It is outside the 18 completed/expected-interruption cells. This addendum rehashes its actual archived evidence and does not relabel it as a successful fault preparation.

The root's different-author review `release/qa/lead-android-probe-review-20261023T0524Z` traced the failure to Boolean test exit-status transport. The correction changes only `adb exec-out … test` to `adb shell … test`; bounded binary reads still use `exec-out`, and guards remain intact. This review independently reconstructs the entire new runner from that one exact replacement.

Old runner SHA256 `d849ab8feb642eb1b988f9a6d82558491b7ebef4c63768fb4fa132f49edf3804` remains bound to the original iOS cells and the successful Android lock cell. Fresh Android preparation/recovery and transition pairs use corrected runner `d1ea6d05085f05a0a3bb6c768531ef7659272e41993858c0551618f74ce5c847`, the same original Dart harness `102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5`, and fresh run IDs. The explicit adoption packet `android-probe-binding-adoption-20261023T053444.391240Z/adoption.json` is pinned at `dc0e778f2464d08b39ca9f67b34fe681ad57b1a4595d39011008c1fb94db5275`. Its separate observer-tool adoption does not supply or claim privacy acceptance here.

## Whole original clause disposition

| Obligation | Combined current evidence | Disposition |
|---|---|---|
| Atomic saves and interruption recovery | Same-directory flush/rename and atomic state/cursor envelope; three real kill boundaries and separate recoveries on current iOS and Android, plus host fault cases. | Satisfied for the quoted process-interruption implementation clause. |
| Rolling backups | Alternating valid generations, exact contiguous parent lineage, latest-corrupt fallback warning and all-corrupt refusal. Current28 host cases and captured native generations. | Satisfied. |
| Checksums | Strict decoder rejects altered checksum before import selection; independently reconstructed iOS and Android canonical save checksums. | Satisfied; integrity is distinct from local-save authentication. |
| Export/import | Existing current-source host tests cover exact export/reload, explicit branch selection, displaced and corrupt-byte preservation, checksum refusal, clearing ownership caches, and no additive merge. Source was inspected in the unchanged prior review. | Satisfied. No receiving-app/cloud-store delivery claim is required or inferred. |
| Versioned migration | Current genuine schema1/2/3→4 fixtures preserve exact money and old replay deny-lists; unknown identities reject. Different-author transition probes and both native target pairs settle a compiled predecessor once before baseline adoption. | Satisfied at the explicit supported versions/compatible-edge scope. |
| No double rewards after interruption | Exact fractional cursor/remainder tests, stale-writer/rewind rejection, actual-core after-rename replay tests, bounded receipt identity tests, and both native economic transition/reopen pairs. Native amount fixtures add atomic-selection proof. | Satisfied in the required fault/replay verification scope; no universal zero-defect promise. |

The original M1-02 prerequisite is accepted and remains unchanged. Root's separate director review `release/qa/director-m1-08-20261023T054139.868139Z/REVIEW.md` supports the original production-fixture criterion pending M1-03. This addendum supplies the M1-03 recommendation; it does not edit or automatically accept M1-08 or any other linked package. Other work items listed under S12 retain their own full clauses and dependencies.

## Independence and limits

The original gameplay reviewer historically authored core and transition/flock changes. Their independent implementation basis remains `/root/qa_integration`'s repaired transition review, including independent additional probes, and `/root/qa_release`'s current native iOS replay. That limitation from the earlier review is retained. This addendum independently checks another author's native Android execution and the different-author reviewed runner correction; it does not claim independent self-review of the authored runtime. Original role assignment and separate evidence authors remain explicit.

No local M1-03/S12 gate remains open at this candidate pin. These are synthetic simulator/emulator process-interruption results, not sudden physical power-loss, physical storage-pressure, a crash-free rate, store transactions or participant evidence. Those limits do not introduce additional conditions into the unchanged local-save clause. S28 release-wide defect/purchase disposition, cloud/provider behavior, physical performance and overall finished-v1 release approval remain separate.
