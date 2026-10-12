# Bounded industrial decision traces

Status: optional measurement for the isolated D3 replenishment comparison. This does not implement or adopt the proposed industrial value model. It advances the reconstruction requirement in [stage 2 of the master plan](buying-behavior-implementation-plan.md#stage-2-make-observations-trustworthy).

## Capture contract

`IndustrialReferenceEngine` and `IndustrialCompiledEngine` accept `trace_sample=N`, default zero. Each tick has separate samples for T1 procurement and each T2 complexity phase. A SHA-256 rotation of an evenly spaced company sample depends only on the explicit seed, tick, tier, phase and active population. It consumes no simulation random draws. The sample is systematic, not an independent random sample or an estimator of population incidence. Recreating the engine at a checkpoint does not require sampling history; the same identity/population produces the same selection.

Capture occurs after basket validation and before the first financial or goods mutation. It records the complete coupled company basket, not independently funded ingredients. Each sampled row contains opening cash and free storage, wholesale lot, input holdings and unit cost bases, input deficits and storage units, original incumbents, incumbent-quote funded bids, formula fees, selected fees/preferences, and every discovered offer's supplier, quote, opening stock, funded quantity, selected quantity and remaining request. Zero-stock offers and zero allocations remain present. No production or forecast value is inferred from this replenishment snapshot.

The stable order identity is `(tick, tier, phase, firm, material)`. T1 supplier IDs are T0 company indices. T2 supplier IDs are input-book indices: T1 company/product slots followed by T2 production lines. Interpret these with the run's archived catalog and ownership/checkpoint, never a display name. Materials use the tier's existing kernel input indices. T1 phase 1 denotes its single procurement phase, including all installed refinery inputs; it is not a restriction to complexity C1.

A selected company whose callback was not reached has status `callback-not-observed`, with no invented measurements. This can occur when it has no eligible production line or the kernel bypasses procurement. The trace does not infer the reason or equate this status to zero demand. A captured row describes a **validated plan**, not independent proof of committed transactions; the associated run must also pass ledger/conservation checks.

## Bounds and persistence

Typed arrays hold at most 12 inputs and 72 offers per sampled company, matching the currently validated industrial solver bounds. Exceeding capacity or capturing the same company twice in a phase raises before that company's purchase commits. It never silently drops part of a basket. Fields with integer semantics are represented exactly as doubles within the supported identity/quantity range; the verifier rejects nonintegral or unsafe integers. The membership lookup is one integer per active company; detailed arrays are proportional to the requested sample, not the whole population. Only the current tick remains in engine memory.

The experimental runner accepts `--trace-sample N` and saves one exclusive `decision-traces-TICK.json` per tick, schema 1, inside its fresh run directory. The manifest records sample size and archived implementation hashes. JSON uses finite values only. Capture is included in kernel step time; export/write time is recorded separately as `traceWriteMs` and `traceWriteSeconds`. Neither timing alone proves the overall performance gate.

## Reconstruction and checks

`tools.buying_v2.decision_traces.verify_export(document)` reconstructs the full replenishment problem, recomputes funded intentions and selection using the reference solver, and independently checks remaining-request arithmetic, one-fee D2 settlement, D1 preferences, lot/stock/cash/storage bounds. It checks schema and deterministic sample identities. It cannot establish that the economic objective is appropriate, nor does reference replay replace the separate small exhaustive solver tests.

Connected verification compares reference and compiled traces and all world arrays with an uninstrumented compiled control, using a population that exercises both C3 and C4. A hand-specified split fixture checks A2+B6, incumbent retention, fee waiver, and corrupted quantities/requests/preferences/fees. Missing callbacks and a genuine zero-offer decision are tested separately. Production purchasing defaults remain unchanged.

Distributor samples are now covered by the [retail trace extension](buying-behavior-v2-retail-traces.md). Remaining measurement work includes rendered trace inspection, isolated full-population overhead/tail/memory measurements, and connecting traces to the eventual value-model treatment. These traces do not close all stage-2 or rollout gates.

## Preserved evidence

`stats/buying-implementation/20261012-industrial-traces-fullpop-137` records seed 137, full configured population, ticks 1–30, sample 8 per phase, with source identity `7fa0a9e73e7aae54807a6888fba4d764a06d117ba88bae85593fe3442f6e4948`. Its invariant gate passes. `decision-trace-world-proof.json` compares all 211 recorded arrays, checkpoint JSON, schemas/configuration and tick invariants against `20261012-industrial-observed-fullpop-137`: exact equality, excluding explicit timings. New trace JSON files are separate measurement artifacts.

`verify-decision-traces.py` verifies all 30 saved trace files against the run's archived source hashes. All 720 selected company-phase identities are present: 484 captured decisions replay successfully; 236 have explicit callback-not-observed status. The latter are not counted as zero demand or failed orders. The proof is `trace-reconstruction-proof.json` inside the run directory.

`benchmark-decision-traces.py` supplies a separate full-population overhead screen with three alternating-order pairs, seed 137, sample 8, ten warm ticks per pair (ticks 2–11). Every world array and runtime economic state agrees on every tick. Control/traced median milliseconds are 396.03/406.87, 400.94/406.10 and 408.62/416.48, increases of 2.74%, 1.29% and 1.92%. JSON encoding medians are 0.28–0.30 ms and exclude disk writes. Trace arrays use 1,056,384 bytes, excluding small Python metadata and temporary JSON encoding. These are short startup measurements, not mature-state tail latency, process-memory bounds, or a pass of the master plan's total performance gate.

The connected trace test also covers sampled multi-line companies and recreating the compiled engine from a policy-tagged checkpoint between ticks. Its four-test module passes in `decision-trace-continuation-tests.log`. Eight existing baseline fallback/stock-access/preference tests pass in `decision-trace-baseline-tests.log`; no production default is activated by these optional hooks.
