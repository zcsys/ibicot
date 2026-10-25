# Independent current native review — sealed iPhone evidence

**Result: the reviewed record contains 21 passed cells, four valid expected interruptions, and one retained failed withdrawal precondition.** The interrupted preparations are not passing tests. The failure is not a demonstrated production withdrawal defect and does not establish successful withdrawal. Android, tablet and reminder results are pending at this review cutoff.

Reviewer: `/root/qa_release`, independent of the native execution author. This review writes only this new QA directory. It executes no Flutter, simulator/emulator command, UI operation, provider request, native build or production mutation. Python replay explicitly blocks subprocess creation and process signalling. It does not repeat the previously closed five-export/3,262-check review.

## Exact evidence and independent reproduction

Candidate: `.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122`; fingerprint `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`; manifest SHA256 `b4322606cd0207425b801feacc0bf4084ac9c460b23a028576204b766eeaeada`.

| Sealed input | SHA256 | Result retained |
|---|---|---|
| `execution-3b00-20261023T040612.562001Z/sealed-completed-phone-20261023T044235.533865Z/checkpoint.json` | `d7c82bab429c67e26fb2d546ce791b2b70891a54a7e266101cd098d4b6d232f0` | 18 pass, three expected interruptions |
| `execution-3b00-20261023T040612.562001Z/sealed-phone-terminal-20261023T044845.379377Z/checkpoint.json` | `e6ed8e685ba0fd9d697261ffa02354def41be377588c03bbe649bfaa39b3a303` | 20 pass, four expected interruptions, one failure |
| `current-runtime-ios-phone-20261023T045232665362Z/verification.json` | `b26d39d5411d75df070bd2c7ddc6dba74f8c2a771999e794202d534afb10b348` | Independently completed cache case appended: 21 pass total |

Paths in this table are under `release/native-proof/`. The second checkpoint preserves all prior report and file pins; its additional empty `errors` arrays and omitted redundant embedded observer summaries are explicitly reconciled with the first checkpoint. Neither sealed input was edited.

`replay.py` completes **1,748 recorded checks**, including successful rejection controls, and records **76 negative-control applications**; these counts overlap and are not additive test-case totals. It pins 401 files. `clause_bridge.py` records another 66 checks across 76 files. The combined input set has 471 unique files. All before/after pins match. The existing native-author host gate is inspected, not rerun: current core206, persistence28 and mobile640 tests have successful terminal markers and exit0 on the same candidate. All eight historical independent numeric-bridge core sources exactly match this candidate; the five referenced raw numeric outputs/logs retain their old pins.

The four initial replay bring-up logs remain. They exposed review-code assumptions about the nested predecessor field, redundant checkpoint summary shape, placement of the leading process-identity bracket, and the hash-named harness stack filename. The final replay uses the inspected real schemas and exact source control flow. They are not production failures or successful evidence runs. A separate initial clause read stopped at the already disclosed capture-harness delta; the final bridge records that delta explicitly.

## What the actual cells establish

| Area | Actual evidence | Limits |
|---|---|---|
| Baseline iPhone | Nine cells: seeded buy/reset; fresh real elapsed start/reload; seeded24h session/reload; clock start/reload; cancelled share; gallery | Gallery contains a Flutter touch pointer and is engineering evidence only. Root owns fresh capture review. |
| Save exclusion and interruption | Actual native FFI `flock`; three externally recorded SIGKILL boundaries and three new-process recoveries. Before-write/after-flush recover amount0; after-rename recovers amount1; each then commits2. | Cooperative application locking and process death, not sudden power loss, hostile private-file manipulation or physical storage-pressure evidence. |
| Actual saved bytes | 24 retained generation envelopes have independently reconstructed recursive canonical JSON SHA256 checksums; version/revision and generation metadata match. All checkpoint/predecessor/result/archive pins match. | Checksums establish integrity, not authorization against a player rewriting a local save. |
| Compatible economic transition | Synthetic old1.5R/s settles60s to90R, new baseline adds1R, same-cursor reopen stays91R; distinct process and original checkpoint verified. | Explicit synthetic compatibility edge; shipped predecessor registry remains empty. No released historical economy is invented. |
| Study lifecycle | Default creates no study artifacts; synthetic opt-in writes actual PID/app/build/UTC context; restart and SIGKILL reopen retain the chain without invented terminal. Capacity fixture stops at7 records/4,158bytes with visible capacity state. | Synthetic registry and injected8-record/32,768-byte limit. Not real consent, participation, fatal-report adjudication or crash-free denominator. |
| Cache grace | Real native files with injected backward/23h/25h clock, fourth-export refusal, bounded cache, held receiving-action and oversized-file rejection | Three exports/192MiB/24h grace are validated; no real receiving app or purchased download is claimed. |

Actual recorded OS is iOS simulator Version26.3.1, Build23D8133. Native process IDs are bound to the declared iPhone simulator and actual executable. Current runtime normal completion requires both native framework and driver success, valid scenario payload, no negative native markers, and host-observed process termination. Baseline runner termination has an explicit successful OS command; it does not record the stronger current-runner identity/absence ledger. Both distinctions are retained.

Negative controls reject late exceptions after success, a driver-only completion, incomplete results, wrong recovery predecessor PID, fake completion in an interrupted preparation, corrupted pre-kill prefix hashes, wrong observation PID/collector hash and a sample extending one millisecond beyond the native window. The failed withdrawal log is independently rejected by both completion and payload validators.

Fresh natural progression waits36,546ms, buys the second Skiff, and reloads in another native process. The session fixture deliberately seeds a24h absence; bootstrap-to-App is a **single692ms sample**, with12 Focus charges and3 Surveys loaded. This is neither24 real elapsed hours nor a p95/physical-device performance claim. The actual Apple clock bridge preserves an epoch within a process, invalidates ownership evidence before foreground refresh, and changes epoch on restart. It does not assert cross-process Apple ownership continuity or a device wall-clock/reboot test. The native share sheet returns `cancelled` and retains a synthetic201-byte ZIP; account session is absent and download was explicitly substituted.

## Observer finalization

Both default and synthetic-enroll observations use the candidate-pinned runner/harness/completion verifier and collector `f3374fb77c83e2b12ff91a48b4c688aa07c7b66042dd75681f7ec2b5fc00febd`. Each finalizes with three paired socket/storage samples after normal native completion. QA replays actual archived `ps` identity outputs, `lsof` rows, storage-worker JSON, command-output hashes, exact opening prefix, native open/close pair, host monotonic and native UTC containment, final verification/result/log hashes and candidate/source bindings. Six samples are qualified.

These are selected-PID point observations after bootstrap/consent, not packet captures or evidence of no network traffic. They exclude startup, activity between samples, other PIDs/OS services, and all but seven fixed synthetic files. Native debug/VM sockets are not release or physical-device behavior. Android private-storage observation remains explicitly unavailable; a future socket-only Android observation must remain partial. Packaged SDK presence was separately established by export review; default-disabled providers do not mean SDK absence. Full S39 remains open.

## Retained failure and pending rows

The original failed report is `current-runtime-ios-phone-20261023T044453553593Z/verification.json`, SHA256 `d18dee13def9fbc4e892741ed1f235ed33464dae859a29398dbbcb0da5ab2616`. The actual stack points to the hash-named copy of original harness line845: the CAS guard was present when the test expected absence. This precedes exclusive guard injection, simulated storage refusal and withdrawal. Later read-only inspection finds that guard absent and preserves exact raw fixture bytes and successful app termination. It cannot retroactively turn the failed assertion into a pass.

Root's separately pinned review `release/qa/lead-withdraw-barrier-20261023T045309.713695Z/REVIEW.md` clears a test-only serialized-recorder barrier for later execution. This audit does not claim its native completion. Fresh withdrawal/reopen pairs must retain their new harness pin and the original failed row.

| Pending at cutoff | Disposition |
|---|---|
| iPhone storage-withdrawal and dependent reopen | Original withdrawal failed; fresh reviewed-harness pair pending |
| Android baseline/current runtime and observer | Do not infer success from builds or iPhone results; append sealed terminal evidence only |
| iPad baseline | Pending; no protected-device action was taken by QA |
| Real native reminder permission/scheduling/quiet-hour delivery/revocation | Separate harness; current runtime intentionally uses a no-native-reminder adapter |
| Store screenshots/preview | Root/client own pointer-free capture and visual review; old gallery is not approved media |

## Original-clause recommendations

`CLAUSE_MATRIX.md` and `clause-matrix.json` preserve all five original package clauses/dependencies/reviewers and all seven requested scope clauses. Shared-host plus current-iPhone evidence supports the local persistence, oracle/failure fixtures and event-timeline implementation subsets. Original dependencies and the named gameplay/platform/director reviewers remain unchanged. No package status is edited.

The bounded S08 replay mechanics and S10/S11 deterministic Survey/contract verification are supported by exact current source, current host execution and the explicit historical bridge. This does not accept S31 physical performance or M3-10 collision testing. Full M3-05/S26, S28 release defects/verified purchases and S39 remain open for the precise reasons in the matrix.

**Concrete uncovered local clause:** M3-10 requires reset/day-boundary collisions. Existing named cases independently cover reset thresholds, midnight rollover, bonuses and chunk parity, but no executed named fixture in this evidence forces an eligible automatic Rechart at the same account-day boundary and asserts order/rewards. Root independently confirmed this and is preparing a focused core-only test. This is a verification gap, not a reported production defect; planned work does not close it. The original M3-10 prerequisites also remain open.

The separate S04 control-evidence question was subsequently resolved by the client/root review; it is outside this assignment and is not reopened. Our archived status snapshot remains unchanged. External developer accounts, physical devices, live provider/hosting resources, human participation, calendar observation and store acceptance are neither supplied nor inferred by this review.
