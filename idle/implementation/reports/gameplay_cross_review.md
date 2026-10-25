# Gameplay engineer cross-review

Reviewer: AI Gameplay and Economy Engineer. Reviewed 16 October 2026. This review covers the **platform save-envelope contract/checker and the client launch registry/checker**, authored by other agents. It does not count my economy fixture exporter as independent evidence.

## Current result

The supplied save fixtures and launch inventory pass their intended bootstrap checks. The release check correctly rejects the unfinished registry. The integration lead repaired both omission bypasses found in this review, and I independently reran their reproductions and closed them. No unresolved bootstrap defect remains from this review. These results do not certify a production game, durable storage, reward delivery, authored content, or native devices.

| Check run | Result | Interpretation |
|---|---|---|
| `python3 implementation/tools/validate_save_contract.py --config economy.json` | 43/43 cases passed | Envelope shape and explicit domain invariants, including pinned config digest |
| `python3 implementation/tools/validate_content_manifest.py --self-test` | Plan contract valid; 33 rejection cases passed after repairs | Registry counts/relationships and listed negative cases |
| `python3 implementation/tools/validate_content_manifest.py --content-gate` | Expected exit 1; 362 unfinished/invalid obligations | B14 content gate excludes later support deliverables while preserving production-content checks |
| `python3 implementation/tools/validate_content_manifest.py --release` | Expected exit 1; 380 unfinished/invalid obligations | The registry does not claim finished v1 content |
| Independent in-memory economic mutations | 11/11 rejected | Extra cross-review coverage listed below |

The baseline registry contains 164 asset packages, all explicitly unfinished. No source/evidence status was changed by the review: mutation probes operated on copies in memory.

## Findings repaired and independently rechecked

**CR-GE-01 — Authoring-field omission bypasses verified-content checks. Priority P2. Status: fixed by integration lead `/root`; independently rechecked and closed.**

At review time, `implementation/tools/validate_content_manifest.py` lines 83–88 validate authoring status/specification only when those keys exist. This allows an entry to claim `production_status: verified` while omitting the authoring fields that demonstrate its specifications are complete.

Reproduction:

1. Copy the registry in memory and mark `chapter.01` verified. Supply existing local evidence paths and mark its referenced asset verified with existing source/evidence/license paths, solely to isolate the authoring guard.
2. With its original `objectives_status: not_authored` and `objective_spec: null`, validation reports the two expected errors.
3. Remove `objectives_status` and `objective_spec`. Validation returns an empty error list.

The lead added category-specific required fields, nonempty verified specifications, and seven omission regressions. Re-running the original reproduction now produces three errors: required objective status, required objective specification, and nonempty verified specification. Chapters, challenges, calibrations, main archive entries, seasonal fragments and ending copy now have explicit authoring-field obligations. This is a repaired bootstrap contract defect; it is not evidence that any actual production content was incorrectly shipped.

**CR-GE-02 — Implementation and fulfillment state omission bypasses verified-content checks. Priority P2. Status: fixed by integration lead `/root`; independently rechecked and closed.**

Follow-up probes found the same omission pattern at UI and commerce registry boundaries. Marking a UI flow verified with existing evidence/ref assets rejected its original `implementation_status: not_implemented`; deleting that field removed the guard. A verified supporter bundle likewise passed after deleting `fulfillment_status`. The lead now requires constrained implementation/fulfillment states, implemented state for verified records, and actual acceptance evidence for verified UI. Three deletion regressions were added. My original UI and bundle probes now produce explicit required-field/implemented-state errors. No current record claims verified, so this was a completion-guard defect rather than observed game malfunction.

## Economic and resource boundary checks

The following independently constructed mutations were rejected:

| Boundary | Mutation |
|---|---|
| Offline settlement | Start before the committed settlement cursor |
| Revision guard | Pending operation targets a different revision |
| Config pinning | Pending operation uses another digest |
| Cloud branch handling | Replace branch selection with summed wallets |
| Campaign access | Add paid-pass requirement to the ending |
| Cosmetic isolation | Add an output multiplier to a cosmetic |
| Accessible calibration parity | Change only the accessible route's Focus cost |
| Seasonal isolation | Enable event prestige |
| Seasonal rules | Replace the documented source/target synergy coefficients |
| Reward shape | Add a Chart award field to a pass reward |
| Collectible identity | Reuse one pass reward's collectible in another slot |

I checked the current inventory against the economic blueprint: six chapters plus continued play; five producer families and 25 presentations; twelve 100-Note dossiers; twelve equivalent-value calibrations; eighteen main archive entries; six 50-Note archive decorations; 36 cosmetics split 12/10/10/4; a 30-level, 15,000-XP pass; shared daily-contract XP; no paid XP multiplier; isolated 28-day Season 1 with the specified changed coefficients; and a supporter bundle that reuses shop items. No contradiction was found in these current values.

The five 50-Note extra automation slots are runtime economy obligations rather than content rewards in this registry. They remain covered by the gameplay handoff and original backlog; do not infer their implementation from the content inventory.

## Integration obligations that remain open by design

- The envelope deliberately leaves gameplay payload opaque. Numeric correctness, Notes, fractional timers, policy versions, campaign progress and real-time event order require the production core/state contract.
- `applied_operation_ids` alone is not a durable history of claimed reward sources. The claim implementation must persist stable source/component identity across retries, including a regenerated transport operation ID; shared event/daily XP must not double-pay. The envelope correctly labels this as outside its proof.
- Config digests and branch recovery references do not prove that referenced bytes or backup snapshots remain available. Loading, atomic commit, crash recovery and cloud preconditions need executable integration tests.
- All pass, challenge, chapter, cosmetic and calibration paths still need authored data, actual assets, reachable runtime paths and independent acceptance evidence. File existence is not semantic proof of content quality or licensing.
- UTC envelope timestamps have whole-second precision. Production timer remainders and fractional earnings must be carried in the versioned gameplay state so repeated save/return boundaries do not discard fractions.
- Device performance, actual StoreKit/Play purchase flows, player understanding, D30 retention and launch support remain external or runtime gates; none is satisfied by these Python checks.

## Ownership alignment

Read `implementation/program.json` and aligned the gameplay handoff to the agreed logical paths: `game/core/**`, `game/simulation/**`, and `tests/core/**`. B02 maps them into the chosen native stack. No parallel native runtime is planned under `implementation/core`.

Only this report and `implementation/handoffs/gameplay.json` were edited during the cross-review.
