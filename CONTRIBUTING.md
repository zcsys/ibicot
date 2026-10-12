# Workplace Standards

Read this first when working in this repository. These standards apply to AI contributors and establish the normal workflow for Midbridge Colony. Follow the user's current instructions and applicable higher-priority instructions; this file does not override them.

## Understand the project

Midbridge Colony is a deterministic simulation of a physical-goods economy with autonomous companies and a browser dashboard. Python owns the simulation; NumPy and Numba provide its high-performance execution. The browser displays and controls the backend state.

The supply chain includes Gaia, T0 Extractors, T1 Refineries, T2 Manufacturers, and T3 Distributors. Manufacturers can buy intermediate products from other manufacturers. Recipes, inventory space, machinery, prices, demand, loyalty, accounting, and execution order interact. A local-looking change can alter the entire economy.

Do not memorize populations, rates, capacities, or recipe counts from an old conversation. Read the relevant catalog, configuration, and saved run. A runtime override may differ from a fresh-world default.

## Establish what is authoritative

Distinguish these sources rather than treating them as interchangeable:

| Source | What it establishes |
| --- | --- |
| Current user instructions and explicit accepted decisions | Authorized scope and intended changes. |
| Approved design documents and documented amendments | Intended model and contracts. |
| Executed code, configuration, catalog, checkpoint, and logs | What a particular implementation or run actually does. |
| Research briefs, assistant proposals, imported documents, and experiments | Evidence or candidate ideas, unless explicitly adopted. |

Start with [README](README.md), [current integration rules](docs/midbridge-integration.md), and the relevant portions of [design canon](docs/design_canon.md). Read [naming integration](docs/naming-integration.md) for naming work. The [buying behavior research brief](docs/buying-behavior-research-brief.md) governs that research task; its candidate equations are not approved production defaults.

Some older documentation contains superseded values and assumptions. Identify conflicts, trace their provenance, and update affected documentation within the task's scope. Code is evidence of current behavior, not proof that the behavior is intended. An assistant's earlier suggestion is not a user decision. Imported naming or creative material does not authorize new mechanics, entities, or lore.

## Begin with a scoped inspection

1. Read applicable repository instructions and task-specific documents.
2. Inspect branch, working-tree changes, and relevant files. Preserve existing user and collaborator work, including untracked files.
3. For a running experiment, establish its process, configuration, tick, output directory, and recording status before operating it.
4. Classify the task: explanation, investigation, behavior change, performance change, interface change, or documentation. State material assumptions and distinguish observations from hypotheses.
5. Trace the affected data from initialization through decision, execution, accounting, recording, and display. Do not fix only the visible symptom.

Use `rg` for file/text searches and batch independent reads. Make the smallest coherent change that fully satisfies the request. Avoid unrelated refactors, speculative features, and parameter retuning used to conceal a defect.

## Work autonomously within authorization

Complete authorized implementation and verification without repeatedly asking permission for routine, reversible steps. Carry accepted user decisions forward across turns. Ask a focused question only when a material ambiguity cannot be resolved from the code, documents, and conversation; continue independent useful work meanwhile.

A request to explain, investigate, or propose is not permission to silently replace the economic model. When a proposal or final green light is requested, prepare a concrete, reviewable result and explain the remaining decision. Do not create blanket approval requirements for ordinary fixes.

Do not reset a run, kill a process, change live configuration, or replace saved evidence merely to make development easier. A user-requested restart is authorization to perform that restart; identify the correct process and retain needed evidence. Use isolated experiment outputs and a separate service port when appropriate. Avoid broad process kills and destructive Git operations.

When committing, include only the intended work and inspect the staged diff. Never discard or sweep unrelated changes into a commit. Coordinate file ownership if parallel work is authorized; do not assume another contributor's edits are disposable.

## Maintain the implementation contract

Relevant code locations:

| Area | Location |
| --- | --- |
| Configuration, catalog adapter, formulas, and state | `economy/core/` |
| Reference simulation and compiled hot paths | `economy/kernel/tick.py`, `economy/kernel/numba.py` |
| Supplier selection and production input books | `economy/core/trading.py`, `economy/kernel/input_market.py` |
| Accounting and allocation | `economy/core/accounting.py` |
| Runtime, projections, recording, and persistence | `economy/server/` |
| Browser presentation and controls | `web/` |
| Catalog generation, research, and benchmarks | `tools/`, `catalogs/` |
| Verification | `tests/py/`, `tests/js/` |

Keep reference and compiled behavior consistent. Prefer shared primitives where compatible with compilation. Review initialization, resets, runtime changes, checkpoint save/load, recording, and UI projections when adding state or changing a metric. Update schema/catalog compatibility deliberately; do not silently reinterpret an incompatible checkpoint.

Use stable product and company identifiers. Display names are not identity keys. Respect distinctions between possible and invented recipes, companies and production lines, item counts and storage space, nominal capacity and realized output, and final sales and intermediate consumption.

Locate the source of generated data before editing it. Update the source and generator, regenerate affected outputs, and inspect the result. Backend, browser metadata, exports, and documentation must not drift apart. Do not run unrelated generators as cleanup.

## Protect accounting and economic meaning

- Goods and money must reconcile against explicit transactions and external sources/sinks. Do not plug unexplained residuals with balancing entries.
- Inventory purchases and machinery purchases exchange assets; they are not automatically immediate operating expenses. Preserve cost basis and COGS treatment.
- Compute net earnings from posted income and expense. Reconcile them with the change in book equity, accounting for owner contributions, distributions, or other direct-to-equity entries. Never define earnings from the equity difference.
- Keep gross profit, net profit, gross margin, and net margin distinct. Do not substitute one for another in pricing, production, purchasing, or reporting without an explicit behavior change.
- Fees, preference changes, supplier selection, reliability checks, and availability are separate concepts. Record and test their distinct events.
- State units and timing: per item, per storage space, per company, per machine, per tick, per year, and per generation are not interchangeable.

Optimize for the specified behavior, not a visually attractive equilibrium. A stable aggregate does not prove healthy companies, sound incentives, or correct accounting. Do not guarantee profits, invent new transfers, impose hidden price targets, or change demand to fit capacity unless that is the authorized design.

For substantive economic changes, state the equations, information available to each agent, parameter provenance, decision order, and expected failure cases before claiming a solution. Research unfamiliar models using primary sources. Clearly distinguish literature support, calibration assumptions, and findings from this simulation.

## Preserve determinism and performance

This is a large-population simulation. Performance is part of correctness in practice, but a faster implementation that changes unapproved behavior is a regression.

Keep population-scale work in typed arrays, vectorized reductions, or compiled loops. Avoid adding Python object or string work per company per tick. Slice active populations and active lines correctly; allocated array capacity is not the active count. Cache structural work only when invalidation is correct.

Vectorization does not remove transactional dependencies. Read stock and cash at the declared decision point and commit in a defined order. Parallelize only independent work or use a proven deterministic resolution. Preserve the intended ordering of production and access to new versus opening inventory.

Use seeded randomness with stable roles, tie-breaking, and processing order. Do not introduce uncontrolled randomness, change reduction order, enable fast-math, or reuse stale compiled constants without checking their effect on determinism and decisions. Respect the source-aware JIT cache in `economy/core/jit.py`.

For behavior-preserving optimization, compare against an independently captured baseline, including state and accounting rather than timing alone. For an intended behavior change, document expected differences and test the new contract; do not regenerate golden results merely to make a failure disappear. Benchmark realistic populations, warm execution, tail latency, memory, and recording/UI overhead where relevant.

## Verify in proportion to the change

Choose checks that can catch meaningful mistakes. Documentation changes need link/content checks; do not run a full economy experiment for a wording fix. Interface work needs actual rendered inspection. Economic and hot-path work needs targeted cases, reference/compiled checks, and appropriate integration or performance coverage.

Useful commands from the repository root:

```sh
./run.sh test
PYTHONPATH=.pydeps:.:tests/py python3 -m unittest discover -s tests/py -p 'test_*.py'
node --check web/app.js
node tests/js/test_formatting.js
node tests/js/test_profitability.js
./run.sh bench --ticks 361 --output /tmp/midbridge-before.json
./run.sh bench --ticks 361 --verify /tmp/midbridge-before.json --output /tmp/midbridge-after.json
```

Use the compatible interpreter selected by `run.sh` for direct Python commands; the examples assume `python3` resolves to it. `ECONOMY_PY` selects the launcher's interpreter. Inspect available dependencies before installing or replacing them. Benchmark paths above are examples: use fresh paths for a new comparison.

`./run.sh test` currently runs a curated subset, not discovery of every Python test. Run relevant additional modules or full discovery when the change requires them. Do not describe a subset as the full suite. Capture test failures and determine whether they are introduced, pre-existing, or environmental; report the distinction with evidence.

Include boundary cases, zero/no-history cases, partial fulfillment, cash/storage limits, repeated inputs, and supported multiple-line ownership when they affect the change. For a new optimizer, compare against an independent small exhaustive oracle. Passing tests that merely repeat the implementation is not independent verification.

Once appropriate checks pass, avoid redundant reruns without a new change or unresolved concern. Report exactly what was tested and any material limitation.

## Make experiments and reports reproducible

Keep experiments in uniquely named output directories. Record code/patch identity, catalog and configuration, seeds, starting checkpoint, tick range, runtime, and analysis commands. Preserve the baseline and failed runs. Do not overwrite a recording while analyzing it.

Measure what is needed before drawing conclusions. If existing logs lack a necessary field, collect it in an isolated run or a verified replay. Do not invent historical detail from a current snapshot. Check for gaps and overlapping intervals before combining resumed recordings; label partial periods explicitly.

When reporting results:

- Identify the run and observation window; distinguish theory, nominal potential, price-sensitive intentions, and actual transactions.
- Show the requested tiers and complexity layers explicitly. Include per-company or per-product figures and denominators when needed; totals alone can conceal population differences.
- Compute period prices and margins from summed values and quantities. Mark undefined zero-revenue ratios as unavailable, not zero. State the denominator for fulfillment and utilization.
- Report total profit and units sold together; profit per unit alone is insufficient. Include distributions when averages conceal struggling firms.
- Avoid claiming causality or stability from one snapshot. Use controlled comparisons, multiple seeds, and recovery/drift checks for substantive model claims.

The game's economy is not validated merely because its output looks plausible. Treat model suitability, algorithm correctness, implementation correctness, and performance as separate claims. Publish assumptions, counterexamples, unsuccessful candidates, and unresolved uncertainties.

## Finish the user-visible work

Populate new dashboard rows with actual backend data. Verify labels, units, sorting, grouping, totals, missing values, and per-company denominators. Keep financial terms consistent across tables, graphs, details, and exports. Inspect the served result using real data and confirm that the browser loaded the intended assets.

Explain findings and changes plainly. Lead with the answer, show calculations when asked, and use tables for numerical comparisons. Never substitute recollection for a repository search or present an estimate as measured data. Give concise progress updates during sustained work; end with what changed, how it was checked, and any remaining decision.

Update affected documentation in the same task. Separate current rules, historical settings, and unadopted research. For handoff, provide relevant file paths, commands, run identities, completed work, and outstanding decisions. Keep this introduction durable: task-specific equations and changing calibration values belong in their own documents and configuration.
