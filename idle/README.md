# Tideglass design package

Start with [Tideglass economy and retention blueprint](TIDEGLASS_DESIGN.md). It contains the requested three sequential phases, sourced comparisons, the original economy, and retention and monetization rules.

For implementation, start with the [AI development team and execution program](AI_IMPLEMENTATION_PROGRAM.md) and [scope audit](V1_SCOPE_AUDIT.md). Six AI delivery roles replace the previously assumed studio. The [v1 roadmap](V1_ROADMAP.md), [detailed work backlog](V1_BACKLOG.md), and [original structured backlog](v1_backlog.json) retain the product scope; their human staffing/calendar estimates are superseded by the AI program.

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

## Reproduce

Requires Python 3.10 or later and only its standard library.

```sh
python3 economy.py
python3 validate.py
```

These commands regenerate the JSON/CSV outputs. The purchase policy is a reproducible heuristic, not a global optimizer. The model is a numerical reference, not a playable client. Proposed live-ops, bonuses and monetization are documented but not implemented in the reference.
