# Tideglass

Tideglass is an in-development native incremental game for iOS and Android. The repository now contains the Dart economy, durable saves, Flutter client, authored campaign/challenges/season, original visual/audio assets, optional-service adapters and local backend. macOS is an internal development target. **The finished v1 release is not yet verified.** Store accounts, signed distribution, physical-device qualification, deployed services and real-player/calendar/support gates remain outstanding.

## Run locally

On the configured macOS ARM64 development host, use the pinned wrappers:

```sh
cd game/mobile
../../tool/flutter pub get --enforce-lockfile
../../tool/flutter run -d macos
```

For a booted iOS simulator or Android emulator, list targets with `../../tool/flutter devices` and use its actual device ID with `run -d`. See [native toolchain setup](docs/decisions/native-toolchain.md) for a fresh host. Coordinate Flutter commands with any running native build/test lane because the SDK and device tools are shared.

The default build opens guest play. Purchases, ads, cloud and signed paid ownership require explicit service configuration; missing configuration is shown as unavailable. Local development does not require a store purchase. The Logbook and Settings include the harbor handbook, and existing save export/import controls preserve recovery confirmation. See [service integration](docs/decisions/ownership-and-soundtrack-integration.md) before configuring optional capabilities.

## Implementation and evidence

| Area | Location |
|---|---|
| Exact economy and daily timeline | `game/core/` |
| Atomic local persistence and recovery | `game/persistence/` |
| Campaign, challenges and cosmetic purchases | `game/progression/` |
| Isolated season and pass | `game/events/` |
| Native client, accessibility, audio and platform adapters | `game/mobile/` |
| Service client, signed ownership and soundtrack streaming | `game/platform/` |
| Account, receipt, cloud, telemetry and operator services | `services/` |
| Production-engine balance experiments | `game/simulation/` |
| Current work, source pins and handoff | [execution checkpoint](implementation/team/EXECUTION_CHECKPOINT.md) |
| Reviewed corrected economy evidence | [independent balance review](release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md) |
| Native candidate/build/runtime records | `release/native-proof/` |
| Fixed-denominator study instrument; synthetic examples only | [study README](release/study/README.md) |

Read the exact candidate/source hash and limitations in each review. Old failed runs and invalidated simulations are retained; their existence is not a current pass. Native exports, host tests, provider fixtures and observed human studies are separate kinds of evidence. The content manifest records production/verification status without equating an asset count to completion.

For task ownership and dependencies use the [AI implementation program](AI_IMPLEMENTATION_PROGRAM.md), [structured dispatch record](implementation/program.json) and [scope register](implementation/scope_requirements.json). The [original scope audit](V1_SCOPE_AUDIT.md) describes the initial program review; later implementation evidence lives in the checkpoint and pinned QA reports. Six delivery roles replace the previously assumed studio, with at most three active specialists alongside the lead. The [roadmap](V1_ROADMAP.md) and [backlog](v1_backlog.json) retain the original product/acceptance scope; their historical human staffing forecast is not an AI delivery promise.

## Files

| File | Purpose |
|---|---|
| `TIDEGLASS_DESIGN.md` | Complete three-phase blueprint |
| `AI_IMPLEMENTATION_PROGRAM.md` | AI team ownership, tools, dispatch rules and 24 ordered delivery batches |
| `V1_SCOPE_AUDIT.md` | Two-direction scope audit, fixes, verified foundations and remaining production work |
| `implementation/program.json` | 69 work items with AI authors/reviewers, dependencies, status and evidence |
| `implementation/scope_requirements.json` | 44 requirement groups traced to implementation and verification |
| `implementation/team/ASSIGNMENTS.md` | Readable author/reviewer and batch assignment for every work item |
| `implementation/content/launch_manifest.json` | Full content inventory with unfinished assets explicitly marked |
| `V1_ROADMAP.md` | Scope, staffing, milestones, acceptance gates and release plan |
| `V1_BACKLOG.md` | 65 planned work packages with owners, dependencies and acceptance evidence |
| `v1_backlog.json` | Machine-readable version of the same backlog |
| `economy.json` | Exact baseline parameters |
| `economy.py` | Deterministic core-economy reference and experiment generator |
| `validate.py` | Economic invariants and independent integration check |
| `simulation_results.json` | Computed results and explicit assumptions |
| `validation_results.json` | Validation count, outcome and scope |
| `first_run_purchases.csv` | First-run purchase history |
| `growth_sensitivity.csv` | Purchase-growth sensitivity |
| `repeated_prestiges.csv` | Twelve resets under a doubling-entitlement heuristic |
| `reset_sweep.csv` | Restricted one-reset timing search |
| `synergy_diagnostics.csv` | Marginal-value comparisons |

## Reproduce the original numerical reference

Requires Python 3.10 or later and only its standard library.

```sh
python3 economy.py
python3 validate.py
```

These commands regenerate the JSON/CSV outputs. The purchase policy is a reproducible heuristic, not a global optimizer. The model is a numerical reference, not a playable client. Proposed live-ops, bonuses and monetization are documented but not implemented in the reference.
