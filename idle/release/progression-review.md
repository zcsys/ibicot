# Independent progression review — 16 October 2026

Reviewer: client implementation agent, separate from the director who authored `game/progression`. Review covers the current headless challenge/campaign module and its authored definitions. It does not approve integrated native campaign play, persistence migrations, content duration or a v1 release.

## Findings and repairs

| Finding reproduced against initial implementation | Repair inspected and independently checked |
|---|---|
| Unknown `construction_mode` silently became manual construction | Definition parsing now rejects unsupported mode values |
| Campaign validation checked catalog counts but accepted invalid IDs/order/prerequisites or objective mode | Explicit six-chapter identity/order/prerequisite checks, objective-kind/value checks, declared non-economic rewards and no paid requirements |
| Direct `CampaignProgress` construction accepted a noncontiguous completion prefix despite strict JSON loading | The constructor now validates the same contiguous prefix invariant |
| Nested chapter/objective maps were mutable under an unmodifiable outer list | Recursive copies and immutable maps/lists prevent caller mutation from changing accepted content |
| Test wording implied persistent 100-Note entry, but only the definition price was checked | Actual `DossierCollection.open` now returns main state and owned-dossier state together, charging 100 Notes once and permitting free owned replay; insufficient Notes and missing chapter unlock reject without mutation |
| Follow-up: paid entry changed Notes without advancing the core revision | A newly paid entry now advances revision once; free replay does not manufacture a main-state change |
| Follow-up: `restart` could replace a different active owned dossier without the explicit replacement check used by `open` | Restarting a different active dossier rejects; callers must use explicit replacement |

## Evidence reproduced after repairs

- `../../tool/dart test` from `game/progression`: **25 tests passed**. This includes twelve independently simulated challenge baselines, two policy alternatives, caps/bulk/max, actual Note entry/replay, malformed content rejection, immutable configuration, isolated power, offline chunk equivalence, and campaign ending conditions.
- `../../tool/dart analyze` from `game/progression`: **no issues**.
- `../../tool/dart test --name 'dossier'`: **5 focused tests passed**, including the two follow-up repairs.
- `game/client/design/progression_review.dart`: **12 independent probes passed**, stored in `game/client/design/progression_review_result.json`. The probes reproduce rejection behavior, nested immutability, actual Note deduction, unchanged insufficient-funds state, free replay, explicit replacement, revision advancement and refusal of an unearned completion.

Probe command from the project root:

```
.tooling/flutter/bin/cache/dart-sdk/bin/dart --packages=game/progression/.dart_tool/package_config.json game/client/design/progression_review.dart
```

The initial four probes all failed before the author repaired the source. They were rerun successfully afterward; this review is not an author restatement of test output.

## Remaining integration requirements

The client must commit `DossierTransition.main` and `DossierTransition.dossiers` atomically in one durable save, expose replacement confirmation, and derive campaign facts from authoritative main/challenge state. A save/import must validate an active challenge against its actual definition. UI must never import main production boosts into a dossier or export challenge wallet/Charts/Notes. Completed cosmetics and archive rewards still need reachable runtime presentation and ownership persistence.

The campaign's 15–30 day duration remains a target, not observed evidence. Passing headless challenge simulations does not satisfy human comprehension, physical-device accessibility, native restore/recovery or long-term retention gates.
