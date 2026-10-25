# Study UI repair — author handoff

Date: 2026-10-21. Scope: M5-04 / M6-01 preparation for S30, S34 and S39. This handoff records a working opt-in study interface and failure recovery, not satisfaction of the original human-study or v1 acceptance criteria.

## Implemented repairs

- Validate the retained original study identity before exposing either active or pending-withdrawal controls. A stop marker with no registry permits cleanup only; it never supplies a fabricated enrollment or export.
- Stop new captures synchronously on withdrawal. Keep erasure retryable when the registry is already tombstoned but eligibility-sidecar cleanup failed, including after reopen. Reject non-file sidecar paths rather than following them.
- Disable export during erasure, pending durable withdrawal and tombstoned state. Check again after asynchronous eligibility reading and before clipboard delivery. Ordinary failed recording can still export its valid existing evidence with a missing-record disclosure.
- Wait for registry preparation before showing consent controls. Declining during the read cannot later attach collection. Invalid provisioning and corrupt registries preserve guest play without silently enrolling or replacing records.
- Await the restored session's app-start write attempt before ordinary bootstrap can build. QA supplied the held-CAS probe that exposed the earlier ordering defect; it now passes against this exact source.
- Use the shared accessible theme, scrolling content, ReadingDialog and presentation-only pseudolocalization. The real narrow-flow test uses 320 logical pixels, 200% text, scrolls to hit-testable controls and completes consent and withdrawal.

The root-owned recorder supplies the durable withdrawal stop marker and CAS behavior. This lane did not modify that implementation, app study hooks, economic logic, rewards or collection acceptance rules.

## Exact frozen source

| File | SHA-256 |
|---|---|
| `game/mobile/lib/study_gate.dart` | `bc019a763d72476ddd38594c96f90c081ffb9992b0e650aa1defd8a3514d923b` |
| `game/mobile/test/study_gate_test.dart` | `5ce105a33599571d44d39063167eaefaf5bd3f0a4d4c3500e4b0c3d7587b128a` |
| `game/platform/lib/study_recorder.dart` | `40be5e8ae640edfe67c6704074bbfb5a2f62fca2e8060b0d96cf50d22b72904f` |
| `game/mobile/test/qa_integration_study_start_test.dart` | `6a10da9bce039214b784e851c7e577d08aa7394153fd64b1402e06c0812e3b30` |

## Executed checks

`platform_release` ran all Flutter commands sequentially in its exclusive lane. I read the final raw logs and verification record, checked their hashes and matched the four current sources to the before/after pins. No per-command source drift occurred.

| Check | Result | Evidence |
|---|---|---|
| English author suite plus independent durable-start probe | 13/13 pass (12 author, 1 QA) | `release/native-proof/root-study-final-20261021T113721.329611Z/english-qa.log` |
| Same author suite with `TIDEGLASS_PSEUDO=true` | 12/12 pass | `release/native-proof/root-study-final-20261021T113721.329611Z/pseudo.log` |
| Whole-mobile analyzer | No issues | `release/native-proof/root-study-final-20261021T113721.329611Z/analyzer.log` |

These are 25 passing test invocations, not 25 unique independent scenarios. Exact commands, log hashes and source copies are in the native-proof directory; the machine-readable companion is `release/study/ui-author-handoff.json`.

The 12 author cases cover default-off no-I/O behavior, decline without backfill, durable initial start/interaction/withdrawal, existing-harbor rejection, corrupt registry preservation, pending-read decline, invalid provisioning, pending withdrawal identity, export blocking/retry across reopen, sidecar cleanup after tombstone, marker-only cleanup and narrow expanded consent/withdrawal. The thirteenth English case is QA's independently authored held-write startup-order probe.

## Failed evidence retained and test repair

- Original root run: `release/native-proof/root-study-repaired-20261021T110906.780697Z/` (4/7 passed); baseline source retained in `root-study-baseline-20261021T112223.477917Z`.
- Intermediate repaired run: `root-study-ui-repaired-20261021T112730.297218Z` (8/12 English and pseudo; recorder drift recorded, unsuitable for final attribution).
- Stable diagnostic run: `root-study-diagnostic-20261021T113317.022817Z` (8/12). Diagnostics showed the assertions observing ongoing filesystem work: `erasing=true`, pending cleanup and CAS guard still held. The interaction record was likewise still pending, with no recording failure.

The final tests begin real pointer taps in `tester.runAsync` and wait for bounded durable conditions with real-I/O/frame pairs. They still assert the same written interaction, tombstone, erased sidecar, stopped reopen state and actual hit-tested controls. No failed durability expectation was removed. Independent startup-order reproduction and its initial unsafe source remain in QA's `integration-study-ui-initial-20261021T113047448400Z` evidence.

## Limits and review handoff

All provisioned tests are explicitly synthetic. There are no participant results, recruitment, ethics approval, real approved study contact, physical-device tests or human comprehension observations here. This source is outside the previously frozen native candidate 152; host passing evidence does not transfer native candidate acceptance.

If a previously consented app-start write is already in flight when the loading-page decline is pressed, that one attempt may finish; the gate does not attach the session afterward. Decline during a held initial read prevents the start attempt. If both durable withdrawal writes fail, stopping is guaranteed only in the open process; the interface accurately shows incomplete erasure and a retry action. A local empty-game-directory check is evidence for later eligibility adjudication, not proof of first-ever installation or absence of restored backups.

Independent QA owns final boundary review and the overall scope audit. No v1 scope or study acceptance status changed. Source is frozen and handed back to the lead; further changes require a concrete review finding.

The separate bounded ART-G01 client review is already recorded in `release/art/entry-gates/CLIENT_STYLE_REVIEW.md` and `client-style-review.json`. It approves a sampled visual direction only, with prior authorship disclosed, and does not verify all assets or close physical-device import gates.
