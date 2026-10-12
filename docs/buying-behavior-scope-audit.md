# Buying behavior scope and documentation audit

Updated 2026-10-12 following the user's explicit purchasing-only restriction. The inspected implementation has **not restored the old 60,000-manufacturer/C5 model**. The README had stale text from the starting commit; it has now been corrected. This audit distinguishes that verified finding from the unfinished validation of the replacement purchasing model.

## Scope that must remain fixed

Do not change populations, catalog/recipes, complexity activation, capacities, sell-side pricing rules, production and historical-cost gates, storage, rent, demand settings, phase order or other non-purchasing mechanics for this task. Purchasing can change realized quantities, revenue and later prices through existing rules; those endogenous effects do not authorize changing the rules. Synthetic test inputs and explicitly labeled diagnostic solver budgets are not production parameter changes.

D1/D2 remain accepted purchasing decisions. D3–D6 were resolved on 2026-10-12 by the user with the price-sensitive fill-to-brim rule (see the plan's decision register). An incompatible candidate must be reported as such, not repaired by changing an outside rule. The master plan and handoff now state this boundary explicitly.

## Verified current model

| Item | Loaded current value | Evidence |
| --- | --- | --- |
| T2 population default | 57,960 | `economy/core/model.py`, `default_cfg()` |
| Active T2 products | 105: 36 C3 and 69 C4 | Loaded `M.T2_PRODUCTS`, invented selection adapter |
| T2 companies by complexity | 38,088 C3; 19,872 C4 | Loaded per-product allocation |
| Production phases | C3 then C4; no C5 phase | Loaded `M.TIER_BOUNDARIES['T2']` |
| T1 | 14 products, 1,008 firms | Loaded catalog/model |
| Baseline experiment | 57,960 T2 firms | Preserved stage-0 `config.json` |
| Effective browser metadata | 57,960 firms, 105 products, C3/C4 | Node execution of `catalog.js` then `midbridge-catalog.js`, matching index script order |

`web/catalog.js` contains legacy seed metadata, including 60,000. The generated Midbridge adapter overrides it before app initialization. Python likewise loads the Midbridge adapter over the legacy catalog. Those legacy literals are not the effective model. No generator or active catalog was changed during this audit.

## Implementation boundaries inspected

Compared with starting commit `572e586fae665e10edd9ea5ea459d5f165f1dfd4`, `economy/core/`, `catalogs/` and runtime configuration/orchestration files have no tracked changes. The changed production files are:

| File | Change and boundary |
| --- | --- |
| `economy/kernel/tick.py` | Optional T1/T2 purchasing callbacks and phase observer; default callbacks are absent. A rent-timing comment was corrected; its function body is unchanged. |
| `economy/kernel/numba.py` | Optional purchasing callbacks/observation arrays and experimental compiled-kernel injection. Retained production logic stays in the shared kernel. |
| `economy/kernel/input_market.py` | Optional vectorized offer-book construction for experimental purchasing; ordinary callers retain the existing path. |
| `economy/server/persistence.py` | Reject loading an experimental purchasing-policy checkpoint into a mismatched engine. This deliberately changes compatibility validation, not an economic parameter. |

The reproducible `audit_scope.py` removes only explicit purchase-hook conditionals and the phase observer, then compares the four affected phase bodies as ASTs. All four match their original bodies: reference T1/T2 and compiled T1/T2. This verifies the retained bodies, not every possible runtime trajectory. The wrapper changes and optional vectorized book path still depend on integration/parity tests for dynamic correctness.

The experimental `RetailEngine` retains the same non-purchasing calls and order: environment, T0 extraction, T1 production/pricing, opening-stock retail, C3/C4 phases, observations, reliability, expansion, loyalty, rent and earnings. Industrial compiled adapters compile the retained production functions with purchasing callbacks. Production runtime calls the ordinary tick; there is no production import or activation of the continuation solver. Research forecast probes construct isolated small worlds; those fixtures do not overwrite the default configuration.

## Documentation corrections

- README population/product table, C3/C4 allocation, inactive C5 statement and T3 terminology now match loaded defaults.
- README benchmark defaults now state 57,960; the actual 2026-10-10 measurements retain their historical 60,000 population with an explicit label. Historical measurements were not rewritten as current evidence.
- README execution order now places Distributor purchases before fresh T2 production and records the later settlement phases. The test command is labeled a curated subset.
- The design canon's status now explicitly defers to its existing dated superseding integration update. Its old population/C5 passages remain historical, not active authority.
- The master plan no longer suggests that an outside amendment can be implemented as an isolated treatment under this task. The production gate remains fixed.
- Progress and handoff retain separate small-solver results, integration checks and open economic gates. Even 16/16 synthetic cases would not complete the master plan.

## Evidence and limits

Evidence directory: `stats/buying-implementation/20261012-connected-integration-checkpoint/`. `scope-audit.json` and `audit_scope.py` preserve the loaded-model and retained-body checks. JavaScript formatting, profitability and buying-inspector tests passed, and `web/app.js` passed syntax checking. Full Python discovery completed successfully: **587 tests in 388.463 seconds**. All 273 source snapshot hashes matched both working and archived files at that checkpoint; `verification.json` records the checkpoint. This is not a new rendered-browser or population-economics verification.

No live configuration or process was reset, and no outside economic rule was changed to address the documentation issue. This is a scope audit of the current changes and relevant model documentation, not a proof that every historical document is current or that the experimental solver is economically suitable. Full-world integration and the master plan's economic/performance gates remain unfinished.

## 2026-10-12 scope re-audit

Rechecked the current workspace at the user’s request. Evidence is in `stats/buying-implementation/20261012-scope-reaudit/`: `audit_scope.py`, `scope-audit.json`, `browser.json`, `source-hashes.json`, `working.patch` and `tests.log`. Backend and effective browser metadata both retain 57,960 manufacturers and 105 C3/C4 products. The four retained reference/compiled phase bodies still match the base commit after removing explicit purchasing/observation hooks. Protected core, catalog, runtime, scheduler, recording, projections, service and browser catalog files remain unchanged. Production runtime has no experimental purchasing import.

Fresh targeted verification passed: **14 tests in 58.463 seconds**, covering D1/D2 contracts, transaction/accounting and checkpoint-policy checks, plus reference/compiled world equality with multiple-line ownership. Command: `PYTHONPATH=.pydeps:.:tests/py /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m unittest test_buying_contract test_buying_v2_world test_buying_v2_compiled_world`. This is a targeted suite, not a new full discovery or population-economics validation. The existing NumPy/SciPy compatibility warning was nonfatal; dependencies were unchanged.

README’s current settings and the canon’s superseding notice are correct; historical C5/60,000 measurements remain explicitly historical. Older source-hash statements were clarified to mean their checkpoint’s working tree, not all later source. No implementation or outside economic parameter was changed in this re-audit. The checkpoint-policy mismatch guard remains the documented compatibility change. No live process was operated. The implementation goal remains unfinished; the next implementation step remains the representative pre-purchase-state capture/adapter contract, with unresolved forecasts and production integration kept explicit.

## Audit refreshed after native Resident support

Evidence: `stats/buying-implementation/20261012-scope-docs-final-audit/`. Re-executed the retained-body AST audit and loaded backend/browser metadata checks: 57,960 manufacturers, 105 active products (36 C3 and 69 C4), C3/C4 phases only. Protected tracked configuration, catalog and runtime paths remain unchanged against `572e586fae665e10edd9ea5ea459d5f165f1dfd4`. All nine files in the preceding scope-audit manifest still match, including the four modified production files and three contract/world test modules. The preceding 14-test result is historical verification, not a fresh run; no redundant economy experiment was needed for these documentation corrections.

A documentation defect was found: accumulated handoff milestones used “Latest” and “Next” for superseded intermediate states, including the old rejection of native compiled state. The handoff now starts with a current support/remaining-work statement and labels older milestones as historical. Native Resident prescribed execution is implemented; native connected/event-tree search and fractional raw projection remain guarded. No search guard was relaxed by this audit.

The inspected changes do not restore the old model or alter outside economic parameters. Optional purchasing hooks and the explicit checkpoint-policy compatibility guard remain the production-code changes described above. This finding is not a blanket correctness or economic-suitability certification of the experimental planner. No implementation code, configuration, live run or dependency was changed during this refresh.

## 2026-10-12 price-sensitive buying change (user-directed, authorized)

The user directed a buying-behavior change replacing the unresolved D3–D6 model: latent demand = "fill to brim" (storage slot), quantity = the Tier 3 curve with the input's reference cost as the halving price (elasticity 2). This modified `transfer_tier2_input` (`economy/kernel/tick.py`), the `_operate_tier2_nb` buying loop (`economy/kernel/numba.py`), and added `M.input_reference_cost` (`economy/core/model.py`) plus a cached `input_reference_arrays`. The change is confined to the buying quantity — the uncommitted diff is 55 insertions / 4 deletions across those three files — and no production, pricing, demand, capacity, storage, rent, phase-order or accounting logic changed. Reference/compiled parity and the full 664-test discovery pass. This is an authorized buying-behavior change, not a scope violation.
