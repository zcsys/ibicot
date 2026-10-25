# Independent foundation and native slice review

Reviewer: `/root/qa_release_native`, 16 October 2026. Review covers the original B01–B06 package contracts; implementation authors do not receive self-approval from these results. This report distinguishes the immutable native candidate `ce46598c4b513477c643f0dff4f5160400ac800b4ee76579c48ca2a5e08e1ffd` from newer working-tree changes. This is not v1 release acceptance.

## Package decisions

| Package | Independent recommendation | Evidence and limits |
|---|---|---|
| M0-01 release contract | **Accept the scope decision**, subject to director approval recorded in program | `docs/release-contract.md` fixes audience, English native iOS/Android scope, six-chapter/content budget, ethical constraints, target floors and decision roles. `release/device-matrix.json` names targets and now records confirmed unavailability. It preserves store, physical and human gates; acceptance does not assert those gates passed. Director explicitly approved this product decision on 16 October 2026 |
| M0-04 journey prototype | Prototype evidence is sufficient after M0-01 acceptance; director may accept this package separately from full slice | Host tests exercise first purchase, reset/cancel, offline report and real corrupted-save/import recovery. Native seeded purchase/reset and real-clock purchase/reload are independently identified. Narrow/large-text constraints are recorded. New daily/story work requires its own review |
| M0-06 quality/device plan | **Ready for director review**, not self-accepted | QA-authored `docs/quality/V1_QUALITY_PROTOCOL.md`, `PLAYER_STUDY_PROTOCOL.md`, `release/qa/study-instrument.json` and device matrix name severities, reference devices, fixtures, recruitment, measurement and final evidence requirements. No actual participant or physical result claimed |
| M0-07 delivery/operating cost | Remain open | Six logical AI roles and zero authorized external spend are explicit. User confirms no accounts/devices/hosting/testers. Actual service usage/cost model and resource arrangements remain to complete; do not reuse human-week promises |
| M1-01 numbers | Implemented component passes independent numeric review; package held for original prerequisites | 474 non-author mathematical checks; exact discrete thresholds, bounded rate/log errors. Native/global limits and config integration are not inferred from arithmetic |
| M1-02 economy state | Implemented component substantially evidenced; package held for M1-01 and clean candidate suite | Five producers, gift/lifetime ledger, milestones, unlocks/Rechart and event timeline exist. Frozen suite retains one stale version-negative test; current revision requires separate qualification |
| M1-03 local saves | Implemented subset passes; full package remains open | Frozen 18 repository checks and repaired non-author integration review, plus native process reload. Full migrations/fault matrix and current rewards still need complete evidence |
| M1-05 playable shell | Shell exists and host/native critical flows pass; hold original prerequisites | Frozen 33 Flutter tests; purchase/reset/settings/return/recovery. This is not complete localization, accessibility or content acceptance |
| M1-08 oracle/failure fixtures | Runtime fixtures and non-author supplement exist; hold prerequisite completion/review | Original reference covers 113 cases: 91 directly consumed by core tests plus 22 QA supplement cases (39 assertions). Save corruption/rapid reset/rounding/write interruption have runtime tests. A clean final candidate and all supported migration/transaction paths remain required |
| M2-01 first-session economy | Core component evidenced; hold prerequisites | Core first-run command sequence, 10-Chart automation, 25-Chart synergies and offline replay checked. Human first-prestige timing not inferred |
| M2-02 onboarding/Rechart | Communication is implemented; hold prerequisites and final integrated review | Skippable introductory copy, visible loss/retention and no monetization interruption in reviewed flow; human comprehension gate remains separate |
| M2-03 forecasts | Partial; remain open | Marginal network output and static-rate assumptions implemented. Complete conditional reset estimate and final policy/late-game assessment not yet evidenced |

## Executed frozen checks

| Check | Observed result |
|---|---|
| Independent mathematical oracle | 474/474 pass: 120 rational geometric batches each with exact and one-micro-below commands; 11 independently searched Chart boundaries; 80 high-precision output cases; 12 logarithm cases |
| Reference supplement | 22 cases /39 checks pass, covering reset, marginal network value, purchase choice and offline envelope; synthetic reference lifetime normalization documented in output |
| Core package after supplying missing auxiliary test inputs | 120 pass, 1 fail: stale schema-version negative assertion expects v2 rejection although frozen runtime supports v2 |
| Persistence package | Analyze clean; 18/18 tests pass |
| Progression package with frozen content copied into QA workspace | Analyze clean; 21/21 tests pass |
| Mobile package | 33/33 tests pass; analyzer exits 1 on 7 information-level brace lints in frozen source |
| Native export | iOS simulator, Android debug and internal macOS builds pass for exact frozen source; three artifact hashes retained |
| Native seeded flows | iOS/Android phone and tablet records identify their own scope; purchase/reset/disk assertions are engineering seeds, not human pacing |
| Native natural purchase/reload | Strict iOS and Android records demonstrate real elapsed first purchase, explicit process termination, new process IDs and retained native saves/offline credit |

`release/qa/candidate-reproduction.json`, `frozen-test-results.json`, `frozen-rerun-results.json`, `frozen-numeric-probe.json` and `frozen-reference-supplement.json` retain commands/inputs/results. QA's first workspace omitted frozen content and the snapshot omitted the Python schema helper; those test-setup failures were corrected with exact recorded inputs, not by changing product tests. An initial QA supplement accidentally used display-rounded output; it was corrected to compare 24-decimal output before reporting the passing final probe.

## Findings and required disposition

| ID | Severity | Reproduction/impact | Status |
|---|---|---|---|
| QA-001 | P2 candidate validation | Run frozen core suite: `test/economy_test.dart:259` passes schema_version 2 to a runtime that now supports 2, but expects rejection | Current tree uses 999; fixed in working tree, **not fixed in frozen candidate**. Do not attach newer 137-pass result to the old export |
| QA-002 | P2 reproducibility | Core schema integration test invokes `implementation/tools/validate_save_contract.py`; original snapshot omitted it and reference fixtures | Platform has updated future snapshot inclusion; QA recorded exact auxiliary hashes for old reproduction |
| QA-003 | P3 lint/quality | Frozen mobile analyzer reports 7 brace-style infos and exits 1 | Current author reports cleaned; next candidate analyzer must confirm. No claim that frozen analyzer is clean |
| QA-004 | P2 evidence integrity | Native runner can exit 0 after compilation failure and exercise previous binary | Platform hardened candidate/harness/scenario/run/device checks. Invalid attempt `integration-ios-phone-20261016T100415.147682Z` excluded. Strict later natural runs pass. Cleanup-induced reload `100648.818501Z` remains failed; app-preserving rerun is separate evidence |
| QA-005 | P2 coverage plan | iOS16 floor permits older hardware than named SE3 | Device matrix now includes physical iPhone8 and records all physical targets unavailable. Plan corrected; actual execution remains open |

No new economic discrepancy was observed in the independent arithmetic sample. That bounded result is not a proof of all future states, all services or all platforms. The original 44-scope two-direction audit is in `SCOPE_AUDIT.md`/`scope-audit.json`; no full requirement group is marked verified. Current daily/automation/story integration is being reviewed in its own saved snapshot.

Independent native artifact/result hash checks passed and are recorded in `native-provenance-check.json`. Phone purchase and tablet reset-preview screenshots were visually inspected: the reviewed controls and retention/loss text are readable without visible clipping; this is limited visual evidence, not screen-reader or physical-device certification.

The subsequent daily review found and independently closed two P2 defects; see `DAILY_REVIEW.md` and its original/retest logs.
