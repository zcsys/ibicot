# Age and galactic procurement rebalance — work in progress

> **Paused at user request, 3 October 2026.** All four background experiments were stopped. Earlier running-status notes below are historical. See [the calibration handoff](economy_calibration_handoff.md) for current evidence, constraints and unfinished tasks. No actual Age result or adopted final calibration is claimed.

The outside economy procures physical goods from the simulated producers. Tier 3 is an external demand boundary, not a population of households and not a simulated producer cohort with profits. Its one million agents represent procurement channels. Their payments enter the local cash ledger; extraction, conversion and equipment purchases leave it. No services are introduced.

## Time and target

0x1E ticks/month × 12 months/year × 480 years/Age = **0x2A300 ticks/Age**. Completed Ages display in decimal: 0, 1, …, 15, 16. Tick counts display with a hexadecimal 0x prefix; one Age is 0x2A300 ticks. Years and months retain decimal notation. The compound growth target for doubling equity is `2^(1/172800)-1`, approximately 0.000004011276 per tick. This is a calibration target, not a guaranteed transfer or automatic equity multiplier.

Normal-condition evidence must distinguish startup inventory accumulation from settled earnings. Equity includes cash, equipment and inventory; cash growth alone does not prove the target. Short-window annualized earnings are preliminary estimates and do not prove a full Age of compounded behavior. Validation must include multi-seed, market-level returns, stock fulfillment, working cash sufficiency and ledger reconciliation.

## Catalogue allocation

The confirmed decision is **20 invented goods per sector**, **2 C-3 / 6 C-4 / 12 C-5**: 200 markets active and 220 reserved. Hamilton apportionment of 20 slots from the complete 44/116/260 pool gives quotas 2.095/5.524/12.381 and integer allocation 2/6/12. Raw ancestry remains C-3/C-4/C-5; there is no conflicting relabeling of refinery C-1/C-2 products.

Sector demand priors are now equal. Equal slot counts alone do not prove equal economic opportunity: recipe input costs, machinery values, capability allocation, procurement quantities and reservation prices must be audited together. The temporary selection minimizes material imbalance within four basic and six compound material groups; it is not proof of exact symmetry.

## Accepted profitability target (all tiers)

The user confirmed return on equity and equity growth as the primary measures, and extended the one-Age doubling target to **Tier 0 as well as Tier 1 and Tier 2**. Larger absolute profits are consistent with the same percentage return on a larger equity base. Tier 0 retains its $1m starting cash per company.

The target is approximately twice the starting book equity after 0x2A300 ticks under standard bots. `ln(2)/172800` is the continuously compounded equivalent, not a mandatory profit credited each tick. For an unchanged factory earning constant profits, doubling requires average earnings of `startingEquity/172800`, rather than `startingEquity*ln(2)/172800`. Report the actual trajectory and distinguish both assumptions. Inventory price appreciation cannot stand in for operating equity growth.

Work proceeds in two steps: first research and test market behavior; then hold those rules fixed while calibrating demand and supply. The working [annual-v1 protocol](../reports/calibration-protocol-annual-v1.json) is now frozen for that second step; standard application parameters have not yet been selected. The Age target must never enter supplier selection, buyer valuation, price learning, payments, or a company's profit calculation. Firm-level and cohort distributions matter: aggregate tier averages can hide winners and permanently unprofitable firms.

## Remaining calibration work

- Preserve Tier 0’s prescribed $1m opening book equity and verify acquisition-cost inventory accounting against downstream paid machinery and working inventory.
- Calibrate normal Tier 0, Tier 1 and Tier 2 returns against the Age target without crediting artificial profits or silently changing time duration.
- Verify typical single downstream firms remain much smaller than Tier 0 giants; separately report aggregate tiers.
- Complete the economic validation below; wartime/civilian naming, all 420 documented catalogue names, 2:6:12 active allocation and company-name search are verified.
- Validate adopted parameters over multiple seeds and the Age horizon; the current contract/scenario gate and browser checks pass for the research core.

## Historical baseline evidence

The [200-market baseline](../reports/age-baseline-200-products.json) ran the actual kernel for 0x2D0 ticks at the full 50,000 firms and one million external buyers. The final window sampled twelve ticks at 0x1E-tick intervals. Mean reported gross profits per tick were approximately $66,013 upstream, $83,912 Tier 1 and $87,326 Tier 2. Final equity/profit ratios implied stationary doubling times of 0x37E, 0x566 and 0x210513 ticks respectively. They contradict the intended Age scale and upstream hierarchy. These estimates are diagnostic, not proof of compounded growth.

The [capital candidate](../reports/age-capital-candidate.json) proposes line capital equal to observed mean line profit × 0x2A300 ticks and includes an extraction asset basis per channel. It is rejected as a calibration method: manufacturing larger asset values from measured profits would disguise the return imbalance.

## Fixed calibration constraints

Tier 0 starts with **$1,000,000 cash per company**, unchanged. Calibration preserves **20 Tier 0 / 1,000 Tier 1 / 61,950 Tier 2 companies**. The user explicitly authorized the revised Tier 2 population: each sector has one firm for each of its 6,195 unordered portfolios of one to four products. Reduced-size regression fixtures are not economic calibration worlds. The large extraction-asset endowment proposed in the earlier candidate is rejected as a shortcut; do not install it. Rebalance production and ultimate demand within these fixed counts. Starting cash and asset values are not adjusted to force growth ratios.

Per-company opening equity follows the tier hierarchy: **Tier 0 > Tier 1 > Tier 2**, with lower tiers far larger than higher tiers. In aggregate the ordering inverts because of company counts: **Tier 2 > Tier 1 > Tier 0**. Opening equity is fixed at $1,000,000 per Tier 0 firm, $20,000/$80,000 per basic/compound Tier 1 firm, and $1,000 per Tier 2 route plus $2,500 working cash ($3,500–$6,500 for one to four routes). Each Tier 2 firm owns its routes outright; there is no shared factory asset.

Age now displays in decimal, while tick counts display in hexadecimal with the 0x prefix, including chart axes, tooltips, accessibility labels and retained history counts. The actual time arithmetic is unchanged.

## Current research evidence

The [market logic research](market_logic_research.md) records primary sources,
full-size baseline and demand/supply counterfactuals. Inventory now uses book
bases consistently in reports, so changing unsold quotes does not create equity.
The Tier 0 target is now the same one-Age percentage-growth target as downstream
firms. Default profitability remains uncalibrated; initial equality of demand
opportunities is tested separately from actual returns. The longer volume/value
experiments have rejected short-window aggregate fits as proof of comparable returns.
The working annual-v1 rules are fixed while the capacity-preserving processing-value
candidate is tested at full population. The first seed measures company and material
returns; a second seed exercises the complete market-balance and price verifier,
including per-firm equity reconciliation. None of these candidates is adopted.

## Initialization and supplier fairness checkpoint

The current core removes three sources of unearned starting advantage: purchase-conditioned product-repeat memory, sparse-array supplier tie rotation, and product-slot parity in initial price experiments. Tier 1 equal-price ties rotate locally; each hundred-firm market starts with 50 firms exploring up and 50 down. Tier 2 initial experiment exposure is within 0.5 percentage points of 50/50 in every market. Fresh firms have no observed demand history, and bootstrap stock targets provide initial goods without fictitious sales forecasts. The earlier initialization checkpoint passed 29 quick checks; the expanded current gate passes 32, including material balance, physical demand and variable-cost scaling.

The matched startup comparison confirmed that excess initial stock was temporarily replacing new manufacturing orders. Its physical production/sales bridge reconciles exactly. Updated full-population runs use the corrected initial directions and record both material flows and book-equity trajectories, including a second seed. The Age target remains unverified; the high-value/low-volume profile remains experimental.

## Current scope audit

Completed: the far-future human-vessel story, wartime and civilian product/company naming, one-to-one 420-recipe catalogue, 200 active/220 reserved allocation, fixed firm counts and portfolios, Tier 0 prescribed cash/capacity/warehouse limits, decimal Age/hex tick presentation, book-basis accounting, company-only Tier 1 demand and admin access to both downstream tiers. The 32-check quick gate passes with matching current engine source hashes. Browser checks show the new T0/T1/T2 company names, exact-name company search, five-decimal unit-price controls and enabled admin tier selection.

The first matched higher-volume trial completed 0x2D0 ticks with mean earned profit $6.5865/$0.2493/$1.7248 per T0/T1/T2 firm and 99.9869% desired-unit fulfillment. Tier 2 zero-earning firms in its final 0x168-tick window fell from 35,044 in the matched unscaled run to 50. The separate 84/77 basic/compound refinery-capacity candidate produced $6.3532/$0.3497/$1.7279, with one Tier 1 and 38 Tier 2 zero-earning firms. Neither result is a settled calibration. Tier 2 portfolio-width advantages change with the measurement horizon; completed longer trials show wider portfolios earning more on average. This instability remains unresolved. All numerical candidates remain separate from normal defaults.

Outstanding: resolve persistent product/portfolio-width and firm-level return gaps with demand/supply data, select standard parameters, verify robustness across seeds and disruptions, and test actual one-Age equity trajectories. Full-Age doubling is not achieved or claimed. Short diagnostic stationary-return estimates are insufficient to complete the goal.

The existing-observation-interval counterfactual has also completed 0x2D0 ticks. With a 0x168-tick observation interval and the optional confidence gates off, the same higher-volume/84–77-capacity data yielded $5.8824/$0.3285/$1.7488 mean earnings, 99.9972% fulfillment, and all ten Tier 1 cohort mean returns within 3.1% of the nominal Age target. Tier 2 width means lie between $1.6519 and $1.9281. This is promising evidence for selecting an observation protocol during the first research step; it is not an adopted default or long-horizon validation.


The completed 0xE10 capacity and annual-observation trials reject a uniform long-run fit from the earlier 0x2D0 windows. The annual-observation tier averages remain near the nominal Age rate, but individual upstream firms and narrow Tier 2 portfolios lag. A higher-utilization demand/supply sweep is now testing this disparity with the same price protocol. The 80% short trial has all ten Tier 1 cohort mean returns within 3.4% of the target, while explicit Tier 0 width cohorts expose a continuing narrow-versus-wide gap. No candidate is adopted. The optimized current source passes the full 32-check quick gate; actual Age doubling remains unverified.


A subsequent isolated supply audit found element-order bias in multi-element extraction: equal deficits yielded 2,500/1,875/1,406/4,219 rather than 2,500 each. The allocator now divides remaining capacity by remaining deficits, with actual-worker equal, proportional and reversed-deficit regressions. New calibration runs use this correction explicitly; earlier utilization trials retain their launch fingerprints and cannot stand in for the corrected core. The correction is part of establishing a symmetric physical-supply implementation before freezing the protocol.


The corrected extraction source now passes all 32 quick checks with matching core fingerprints. Physical-supply symmetry is verified in isolation; full-population corrected-allocation experiments remain in progress.


The first actual one-Age full-population candidate run has started: corrected extraction, 95% nominal utilization, annual price observation, seed 12345. It executes 0x2A300 real ticks with 20/1,000/61,950 firms and one million external buyers. Checkpoints remain incomplete evidence; no candidate is adopted and success is not yet claimed. The final evidence must inspect actual equity multiples and company/cohort distributions, rather than extrapolating recent profits.


The [current full-population startup audit](../reports/current-economy-goal-audit.json) verifies every firm portfolio, all 420 recipe/name/code identities, 200 active/220 reserved products, shared limits and the exact company counts against current source. It distinguishes verified initial structure from unverified Age growth, calibrated-default adoption and adopted-parameter robustness. Documentation tick quantities now use hexadecimal. A historical full-scale scenario gate capping aggregate C-5 unit share at 20% was replaced with the actual complexity policy: orders per market decline with complexity. C-5 has 120 of 200 active markets, so its aggregate share is a separate diagnostic. The 214 active market count includes four raw, ten intermediary and 200 final markets.


## Fixed protocol and current verification

The annual-v1 working protocol records the source version and every fixed pricing, search, switching, elasticity and activation setting. Calibration may vary only its listed production-cost, capacity and fixed engineering demand-profile data; company counts, startup capital and Tier 0's prescribed limits remain fixed. A rule change would require a separately recorded protocol version.

With constant production capital, the desired one-Age equity increment has these average per-firm earnings references. They are targets, not payments or validated outcomes:

| Producer | Opening book equity | Required average earnings/tick |
| --- | ---: | ---: |
| Tier 0 | $1,000,000 | $5.787037 |
| Tier 1 basic material | $20,000 | $0.115741 |
| Tier 1 compound material | $80,000 | $0.462963 |
| Tier 2 (1 route) | $3,500 | $0.020255 |
| Tier 2 (2 routes) | $4,500 | $0.026042 |
| Tier 2 (3 routes) | $5,500 | $0.031829 |
| Tier 2 (4 routes) | $6,500 | $0.037616 |

This preserves the intended per-company hierarchy: **Tier 0 > Tier 1 > Tier 2**, with lower tiers far larger than higher tiers. Aggregate Tier 2 starts much larger because it contains 61,950 firms; that aggregate is distinct from the size of one company.

The full market-balance verifier now accepts saved candidate configurations and records actual book-equity multiples by tier, Tier 1 material, Tier 0 width, Tier 2 sector and initial portfolio width. Each firm's cumulative earned profit must reconcile with its actual book-equity gain. Its stale one-cent numerical price floor was corrected to the engine's $0.00001; the fractional-cent and below-cost regressions pass. Source runtime rules retain the frozen protocol fingerprint. Two full-population 0xE10-tick candidate seeds have completed, including the full price/inventory/accounting gate in seed 31415. Their [actual equity distributions](../reports/processing-value-capacity-cross-seed-comparison.json) remain finite-horizon evidence. The original actual Age reference and the capacity-preserving processing-value Age candidate are executing; their checkpoints are incomplete evidence. Final defaults, cross-seed/disruption robustness and one-Age growth remain unverified.
