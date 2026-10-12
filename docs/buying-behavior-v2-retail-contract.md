# Replacement retail implementation contract

Status: isolated implementation, not adopted production behavior. Policy `v2-retail-only-v2` implements the accepted [D1 and D2 decisions](buying-behavior-contract-decisions.md) for Distributors while leaving industrial procurement unchanged. It is an intermediate component of the [master plan](buying-behavior-implementation-plan.md).

## Information and objective

Each activated Distributor keeps its existing product, activation draw, latent quantity, elasticity, valuation, and per-order rounding draw. It sees five distinct eligible production lines plus its valid incumbent. Eligibility includes active finite-quote lines even with empty stock. Uniform sampling without replacement uses stable buyer, market, tick and seed roles. Incumbents remain line identifiers as in the current runtime; company-versus-line weighting for multiple owned suppliers remains an explicit fairness review item.

Convert the existing price-sensitive quantity curve to descending marginal values using the same rounding draw. For each sampled feasible basket, maximize sum of marginal values for purchased units minus actual goods payment minus the single payable fee. Include buying nothing. This is a retail-surplus objective; it is not used as an industrial expected-profit objective.

The solver enumerates all quantities along the cheapest goods prefix and the incumbent-only prefix. For each fixed quantity, all outside-bearing baskets share the same fee, so their cheapest goods allocation suffices; the incumbent-only family separately captures avoidance of that fee. A small independent oracle enumerates every allocation to verify this reduction.

## Fees and preferences

Freeze the original incumbent and its live available stock at this buyer's decision, after earlier buyers settle. The reference bid is demand at its own quote. Distributors currently have no stored cash balance or storage restriction; the generic solver accepts a cash cap for fixtures but the world adapter does not invent one.

If the original incumbent can supply the positive reference bid and any outside supplier actually sells goods, pay one existing-formula fee to that incumbent. Multiple outside suppliers do not multiply it. No purchase means no fee. Availability waiver and preference qualification are independent.

A supplier qualifies for preference only if its own delivery alone covers the whole demand at its quote. A=2/B=6 retains the old incumbent, and with no incumbent the same split leaves preference unassigned. A challenger filling a small incumbent-quote bid but only part of demand at its own cheap quote does not qualify.

## Settlement and observation

Retail uses opening manufactured inventory before industrial production. It debits actual seller stock and posts seller cash, revenue and historical-basis COGS. Fee income is posted separately to the original incumbent's owner. Total Distributor external payments include goods and fees. The later standard accounting finalization reconciles posted earnings.

Selected deliveries are traced in ascending quote order; remaining requests subtract all previous purchases. Quote evaluation alone creates no supplier demand or reliability attempt. If no delivery occurs and the cheapest observed offer has zero stock and positive demand, the adapter records that actual empty-stock request. Fee or valuation rejection alone creates no supplier request. This final distinction corrects the initial `v2-retail-only-v1` screening implementation; that archived run remains separate evidence.

The versioned observation reducer separates discovery, actual request legs, initial and terminal quote quantities, purchased units, fees, first assignments and true preference changes. Terminal shortfall does not identify whether cash, stock, fees, or choice caused a gap. Existing dashboard loss names are not a validated presentation of this experimental policy; integration must version/relabel them before adoption. In particular, zero requests after fee rejection cannot be advertised as measured latent demand loss.

## Determinism and persistence

A source-aware cache includes all replacement Python modules plus production dependencies. Stable-ID quote ties are deterministic but not proof of identity fairness; fair tie treatment and reversed-priority tests remain open.

Native checkpoints carry `runtime.purchasePolicy`. The production loader defaults to `baseline` and rejects a different policy marker. Experimental continuation must explicitly request the matching policy. Missing markers denote historical baseline checkpoints. This guards interpretation; it does not migrate baseline state into a new policy.

## Verification and outstanding work

Tests cover 600 independent exhaustive small-market baskets, distinct discovery in small/empty markets, actual stock/cash/revenue/COGS postings in both execution paths, A=2/B=6 retention, one fee for split purchases, full-tick conservation, and exact continuation through native save/load with policy rejection in the baseline loader.

A 360-tick full-population screening run checks the initial retail integration. It does not establish generation-scale trade, unbiased sampling across owned lines, final performance, UI compatibility, or industrial behavior. These remain master-plan requirements rather than implied approvals.

Optional [Distributor decision traces](buying-behavior-v2-retail-traces.md) capture bounded pre-settlement samples without changing this contract. The Python adapter uses explicit double precision for latent quantity and inverse-curve arithmetic to match the compiled path; full-population comparisons preserve the existing compiled trajectory.

## Reachable-value optimization

The world adapter computes only the marginal-value prefix that discovered whole-item stock can support, capped by the unchanged latent potential quantity. Any feasible basket uses at most this prefix, so the same exact basket solver and arithmetic apply. When no whole item is available, the only feasible allocation is empty; request, reliability, exposure and trace reporting still execute. In particular, an empty-stock positive request is not erased. Original potential quantities and each supplier's own-quote demand remain unchanged for observations, fee eligibility and preference qualification.

Identical quotes within one buyer's discovered offers reuse the same rounded quantity. This is exact because latent demand, elasticity, valuation and the rounding draw are shared within that order. Supplier identity and availability still enter the separate fee and allocation checks. This does not introduce a new demand curve or industrial assumption.

Evidence in `stats/buying-implementation/20261012-retail-prefix-optimization/` includes independently archived pre-edit source, 90 exact full-array/trace comparison fixtures and ten passing targeted tests. Three alternating-order full-population pairs resume the same corrected-policy checkpoint at tick 30, warm tick 31 and measure ticks 32–41. Median kernel time improves by 5.80–6.92%, with every world array, checked scalar ledger, supplier history, observation and runtime economic state equal each tick. A fresh seed-137/ticks-1–30 recording also matches all 211 archived arrays and checkpoint/schema/invariant fields. These are startup screens; no mature-state, overall performance-budget or adoption pass is claimed.

The shared supplier-discovery primitive now sorts its bounded selected IDs in place, preserving the exact IDs and ascending order of the previous implementation. Archived reference/compiled comparisons and full-state year-end timing pairs are recorded in the [discovery optimization evidence](buying-behavior-v2-industrial-contract.md#year-end-profiling-and-exact-discovery-sort); this changes neither retail selection nor its fee/preference rules.
