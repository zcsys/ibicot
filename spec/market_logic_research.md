# Market logic research and calibration protocol

> **Paused at user request, 3 October 2026.** All four background experiments were stopped. Earlier running-status notes below are historical. See [the calibration handoff](economy_calibration_handoff.md) for current evidence, constraints and unfinished tasks. No actual Age result or adopted final calibration is claimed.

The accepted target is similar return on equity for standard bots in all three producer tiers, with approximately twice their opening equity after one Age (0x2A300 ticks). Tier 0 retains $1m starting cash, 10k capacity/tick, 500k target inventory and 1m maximum inventory. Counts remain 20 / 1,000 / 61,950. The annual-v1 working market protocol is now frozen for demand/supply calibration, with its decision recorded below. Final defaults, robustness and full-Age validation remain incomplete.

The human-investor story does not change the bot calibration baseline. Administrative takeover of either Tier 1 or Tier 2 preserves existing company capital and relationships and changes operational control only; no investor payment, capital injection or special customer access is introduced. The future game’s Tier 1 alpha scope does not restrict economy-core admin capabilities.

## Research basis

[Kephart, Hanson and Greenwald (2000), §3.2](https://hpi.de/fileadmin/user_upload/fachgebiete/plattner/teaching/Dynamic_Pricing/kep00.pdf) studies posted prices with comparison-shopping buyers and several pricebot strategies. Its derivative follower changes price experimentally and reverses direction when observed profit falls. The paper also shows different strategies can produce price cycles and different profits. Our finite production, cash, inventory, input chains, reliability and scarce-stock signals are extensions; the paper does not validate this game's parameter values or establish equal returns.

[Gode and Sunder (1993)](https://www.journals.uchicago.edu/doi/10.1086/261868) finds high allocative efficiency under budget constraints in its double-auction experiments. This supports treating transaction constraints seriously, but our posted-price market is different and allocative efficiency is not equal profitability. Neither paper supplies a rule for equalizing company returns. That remains a game calibration objective requiring experiments.

## Candidate rules to establish before calibration

1. Payments transfer cash exactly once. External procurement brings cash into the local economy; extraction and conversion costs and equipment purchases leave it. No payout or price decision references the Age target.
2. Tier 0 supplies raw elements only to companies. Tier 1 supplies ten processed materials only to companies. Tier 2 supplies physical goods to external galactic procurement. Input demand follows complete, affordable manufacturing recipes.
3. Production is constrained by stock, funds, machinery and a company-wide warehouse. Each Tier 2 firm has a pooled output budget and one to four routes within one sector; compounds occupy one input-storage unit each.
4. Buyers have fixed engineering-reference valuations, heterogeneous demand and bounded comparison shopping. Raising a seller's costs or desired markup does not automatically raise buyers' valuations.
5. Higher-complexity goods have fewer unit orders and higher initial markups. The procurement quantity benchmark compensates recipe cost and nominal margin. This is an exogenous purchasing profile, not compensation for a seller's realized losses.
6. Pricebots experiment against their own observed profits. Unfilled funded orders signal scarcity, and idle unsold stock encourages lower quotes. There is no required profit margin or guaranteed return.
7. A Tier 2 factory has one discovery budget divided over its routes. Wider portfolios broaden product coverage while sharing capacity, storage and exposure. Every unordered portfolio has one starting company in every sector, giving each active product 1,160 suppliers and equal allocated capacity.

These semantics have a frozen working calibration version in [annual-v1](../reports/calibration-protocol-annual-v1.json). Earlier experiments below document their research-stage corrections. Demand/supply experiments must share its source fingerprint and fixed behavioral configuration; failed targets cannot justify silently changing decision rules. Any necessary further rule correction requires a separately recorded protocol version.

## Measurement

Use cash plus equipment book value plus inventory acquisition/production basis as book equity. Quoting an unsold item at a higher price does not earn a profit. The dashboard uses the same book bases for all tiers and company/sector views. Main Tier 0 reporting now recognizes the acquisition basis of units sold as COGS and separates extraction spending and operating cash flow. Earlier frozen reports may retain the extraction-spending gross-profit label; their source identities and recorded results remain unchanged.

`tests/economy_research.js` executes the full-size worker and records source hashes, actual configuration, cash reconciliation, equity reconciliation, realized equity multiples, earnings per tick and ROE distributions. It reports each Tier 1 material cohort, Tier 2 sector and portfolio width as well as tier aggregates. Its short runs are diagnostic, not proof of one-Age doubling.

For fixed capacity and approximately constant earnings, the diagnostic stationary doubling time is opening book equity divided by earnings per tick. A compounding assumption uses `ln(2)/172800` as its instantaneous rate; an unchanged plant needs total earnings equal to opening equity over the Age. Final validation must distinguish these trajectories.

## Experimental sequence

- Verify conservation, affordable whole orders, recipe feasibility, warehouse/production limits and deterministic resets.
- Check price responses to demand, costs and capacity, and test that buyer values stay independent of seller costs. Existing pricing, shocks, scarcity and competition tests address these behaviors.
- Check default opportunity analytically across every active recipe, then measure actual firm and market distributions. Equal starting opportunities do not guarantee identical realized histories.
- Run a full-size baseline after initialization fixes. Hold rules fixed; vary external procurement intensity, its fixed product distribution, and downstream supply allocations. Preserve company counts and Tier 0's accepted endowment and limits.
- Assess several seeds, settled windows and longer horizons. Report persistent low-return cohorts and bottlenecks explicitly. Do not flatten profit distributions with transfers, asset inflation or target-aware pricing.
- Verify the eventual Age target with actual book-equity trajectories and ordinary reinvestment decisions. A short-run extrapolation alone is insufficient.

## First full-size baseline

The [0x2D0-tick baseline](../reports/economy-research-baseline.json) uses all 20 / 1,000 / 61,950 companies and one million procurement agents. Its final 0x168-tick window reconciles firm book-equity changes with earned profits (maximum discrepancy below $0.000001). Desired-unit fulfillment was 99.980%.

Average actual equity multiples over the entire run were 2.269× / 2.296× / 1.002824× for Tier 0 / Tier 1 / Tier 2. Median final-window earnings per company per tick were $2,079.04 / $44.54 / $0.789. Median stationary opening-equity doubling estimates among profitable firms were about 0x335 / 0x46D / 0x5D97D ticks. These estimates describe this diagnostic window; they are not full-Age outcomes.

Material cohorts also diverge: basic-refinery median returns are much higher than compound-refinery returns, and some firms earn nothing during the final window. Sector means are closer than firm-level distributions. Therefore neither excellent fulfillment nor equal portfolio enumeration proves profitability symmetry.

Reducing all external demand alone is not a demonstrated solution: it would slow Tier 2 as well as the fast upstream tiers. Subsequent experiments must report both the cross-tier rate gap and the within-tier low-return cohorts. No candidate is accepted solely for hitting the aggregate average.

## Demand and supply counterfactuals

The [low-demand run](../reports/economy-research-low-demand.json) requested a multiplier of 0.005; the worker normalized it to its 0.01 minimum, so the actual reduction was **100-fold**. Counts, Tier 0 capital and market decisions were unchanged. Mean final-window earned profits per company per tick fell to $5.854 / $0.391 / $0.002206 for T0/T1/T2. This brings upstream mean earnings close to an Age-sized scale while effectively halting downstream equity growth; it is rejected as a complete calibration.

The [abundant-refinery run](../reports/economy-research-abundant-refineries.json) increased C-1/C-2 throughput from 320/240 to 3,200/2,400. Mean earned profits became $1,751.29 / $51.265 / $1.185. It did not resolve the cross-tier return gap and increased Tier 1 concentration in this window. Neither counterfactual has been installed as a default.

A further volume/value experiment varies the procurement benchmark margin and a separate starting Tier 2 markup. The existing purchasing formula is unchanged: increasing its exogenous benchmark reduces units and increases valuation while preserving analytical benchmark profit opportunity. Seller costs and quotes still do not rewrite buyers' preferences. These are explicit demand/initial-state parameters, not earned-profit compensation. Defaults remain 0.25 plus 0.05 per complexity step; the optional Tier 2 starting-markup override defaults to −1, inheriting the shared starting markup.

Before this next pair of experiments, the bootstrap stock formula was corrected to use the current procurement quantity profile instead of obsolete 0.45-per-complexity metadata. This is recorded as a research-stage consistency fix. The fresh baseline and volume/value candidate use the same corrected sources, so their results are directly comparable. Older reports retain their original source fingerprints.

The research instrument now groups portfolio widths by both initial and current width, avoiding selection bias from successful firms expanding. It also reports a revenue upper bound: for elasticity at least one, expected revenue is bounded by latent quantity times valuation. A low-volume candidate cannot be accepted if even its expected external revenue cannot support the required retained earnings.

## Paired volume/value result (preliminary)

The [corrected baseline](../reports/economy-research-frozen-baseline.json) and
[volume/value experiment](../reports/economy-research-value-volume.json) have
identical source fingerprints. Each runs 0x2D0 ticks with the final 360 as its
measurement window. “Frozen” in the baseline filename means held constant for
this pair; the overall research stage is not declared finished.

The experiment uses benchmark/starting T2 margins 150/180/210 and demand
multiplier 1.5. This preserves equal analytical benchmark profit opportunities
while greatly reducing physical unit throughput. It is an extreme sensitivity
experiment, not a selected standard configuration. Its Tier 2 mean earned profit
is $1.946 per firm per tick, near the $1.751 constant-earnings target implied by
its opening equity, but 39,578 of 61,950 firms earn nothing in the final window.
T0 mean profit is $0.170 and T1 $0.058. These results do **not** establish a
harmonious economy. Low flow also makes wholesale-lot replenishment cycles
longer than the measurement window, so zero T0 window earnings cannot be
interpreted as a permanently zero long-run return.

A longer 0xE10-tick run of this experimental configuration is in progress. It
records sixty-tick profit windows and downstream quote/markup trajectories,
which can expose price-learning drift and distinguish thin trading from
persistent exclusion. No experimental configuration has replaced the defaults.

## Recipe symmetry design study

[Structural enumeration](../reports/recipe-symmetry-design.json), reproduced by
`node tests/recipe_symmetry_research.js`, shows that an exactly material-permutation
invariant active subset can contain **20 C-3 / 60 C-4 / 120 C-5** recipes.
It uses whole permutation groups, preserving processed-intermediate identities.
Every basic appears 78 times and every compound 49 times in the proposed input
incidence totals. This is structural symmetry within material classes, not equal
actual demand, returns or an optimal catalogue.

The candidate is not installed. Its existing name/sector assignments do not
meet the required 2/6/12 allocation in every sector, so blindly selecting these
keys would break the catalogue. Sector curation and active/reserve assignments
must be resolved together, with application-appropriate names and distinct codes.
The study establishes a feasible symmetric pool; it does not authorize a generic
renaming template or prove economic balance.

For reference, the current opening book equity requires constant aggregate
earnings of approximately **$115.741 / $324.074 / $108,448.351 per tick** for
T0/T1/T2 to double over one Age. These figures are diagnostic targets and are not
inputs to any market decision. At nominal initial quotes, a basic refinery earns
$0.375 per unit and a compound refinery $1.10. Matching their opening-equity
returns would therefore require about 30.864 basic units per market per tick and
42.087 compound units per market per tick (100 firms per material). This flow
identity is a benchmark calculation, not a substitute for price-learning and
stock-cycle experiments.


## Extended rare-order experiment and opening tie correction

The full-size [0xE10-tick value/volume run](../reports/economy-research-value-volume-3600.json) rejected the apparent short-window fit. In its final 0x168 ticks, mean earned profit per company was $0.339 / $0.133 / $0.437 for T0/T1/T2. Tier 2 had 36,000 zero-profit firms in that window; median return was zero. Mean Tier 2 markup by complexity declined from approximately 148/178/207 near startup to 20/23/27 at tick 0xE10. Fulfillment remained 100%. Consequently, fulfillment and an initial aggregate-profit fit do not establish sustainable, comparable returns. The cash ledger and book-equity reconciliations passed.

The 0x1E-tick observation window repeatedly treated sparse order traffic with unsold stock as a reason to lower quotes. A sensitivity run with the existing 0x168-tick observation parameter is being used to distinguish the effect of observation cadence without changing the derivative-following rule. Neither the extreme demand profile nor a new observation cadence has been installed as the default.

Separately, initialization attached every Tier 1 buyer to the lowest-ID equal-price Tier 0 provider. This was an unearned relationship and an identity bias. Initial supplier relationships now begin unset, and successful trade establishes them. Equal effective stocked quotes are selected deterministically from seeded draws with weights proportional to each provider's share of its company-wide capacity (1 / element width). Price, availability and earned switching friction still take precedence. This matches the existing principle that a firm's broader portfolio must not multiply its market exposure. It is a phase-one correction, recorded before the pricing and trading protocol is frozen; company counts, capital, production and inventory settings are unchanged.

The [wholesale neutrality regression](../tests/wholesale_neutrality.test.js) checks identical offers across the real twenty-provider topology: 100,000 equal-price selections give approximately 5,000 per company, independent of one-, two-, three- or four-element width. It also verifies cheaper stocked offers win, earned switching friction persists, and stockouts permit switching. This proves the specified opening opportunity, not equal realized long-run profits.


## Nominal material-flow feasibility

The [offline flow diagnostic](../reports/economy-flow-feasibility.json), generated by [the flow instrument](../tests/economy_flow_research.py), holds nominal input quotes and margins fixed and solves for orders feeding the ten actual material markets. At current opening cash and machinery costs, each basic market requires about 30.864 units/tick and each compound market 42.088 for its hundred firms to earn an opening-equity increment over an Age. Three independent complexity multipliers with reference-cost quantity compensation cannot place all ten flows within 5% of those values. Independent recipe quantities can satisfy the equations, but this particular solution requires departures from its prior demand shape ranging from 0.012× to 33.9×. It is a feasibility witness, not a sensible demand profile or an installed parameter set. It also puts C-3 and C-4 mean quantities at equality, so it does not meet a strict decreasing-complexity preference.

The raw flow implied by those Tier 1 targets yields nominal Tier 0 profit $157.127/tick, versus $115.741 for the Tier 0 Age target. This further demonstrates that upstream margins, capital requirements and material composition must be assessed together. Actual scarcity, prices and supplier concentration are omitted from this diagnostic; the result does not establish impossibility under every market outcome. Neither scattered per-recipe quantities nor changed capital values have been adopted.

## Experimental observation adequacy

`researchPriceMinimumOpportunities` is a phase-one experimental switch, default **0**. It does not alter live default price decisions. With a positive value, the existing derivative-following learner waits both its calendar window and a minimum expected count of funded market orders, allocated using the same shared-factory exposure weights. These are order counts, not unit counts: a 1,000-unit wholesale lot is one observation. Successful sales establish individual relationships; total market arrivals do not assign customers or guarantee revenue. No equity target, required margin or Age appears in this learner.

This addresses a measurable ambiguity: zero sales in a window containing almost no order traffic is weak evidence that a quote failed. Observation counters use 32-bit ticks so long sparse windows do not wrap at 65,536. The [mechanism regression](../tests/price_observation_research.test.js) checks no-traffic patience, learning after informative traffic, counter persistence and the unchanged default. The [reduced pilot](../tests/price_observation_pilot.js) compares calendar-only and minimum-traffic observation under the actual kernel, but its smaller fixture is exclusively a mechanism experiment. It must not be used to choose canonical company counts, calibrate returns or claim an Age result. A pure traffic gate can stall exploration in an entirely overpriced market. The current research candidate therefore also permits exploration after a maximum stale window (`researchPriceMaxObservationTicks`, 0xE10 ticks), independent of the Age target. The no-traffic regression checks eventual timeout exploration as well as short-window patience. Recovery and long-horizon behavior still require validation before adoption.


The [0x1C20-tick mechanism pilot](../reports/price-observation-timeout-pilot.json) retained almost its full initial complexity premiums under the informative-traffic candidate: mean markups ended at about 150/179/209, while calendar-only observations drove them to about 1.8/2.1/2.6. Candidate cumulative earned profit was $17.00m versus $4.84m in this reduced fixture. This confirms that observation adequacy changes the sparse-traffic failure mode; it does not prove profit fairness or calibrate the full economy. A separate [pure-gate pilot](../reports/price-observation-pilot.json) has no stale-window timeout and is retained as a distinct historical variant. Source fingerprints distinguish the variants. The candidate remains off in default settings.


## Neutral need persistence correction

Procurement repeated a product only after a successful purchase. When physical quantities differ, this makes high-order-frequency goods win more retained product preference, even with equal authored choice weights. Successful-purchase memory now records only the earned supplier relationship. A separate need-product memory records every considered product and drives the 65% repeat rule, independent of whether stochastic quantity was zero or a seller fulfilled it. Thus the stationary need-choice prior remains the authored product distribution, while successful suppliers retain customer loyalty within a chosen market.

The [native-clearing regression](../tests/need_persistence.test.js) isolates two equal-weight products, one quoted beyond any buyer's willingness and the other frequently purchased. Their considered-need shares remain approximately 50/50, while only the purchased product can earn supplier relationships. This correction does not force order quantities, sales, stock fulfillment or profit equality. It is a phase-one semantics correction before the protocol is frozen. All preceding research reports retain the old successful-purchase product-repeat behavior; their fingerprints and results are historical comparisons, not a calibration of the corrected protocol. New full-population runs must use this corrected version.

## Completed observation-window comparison (historical need semantics)

The matched full-population experiments with neutral opening wholesale ties now cover 0xE10 ticks. The [0x1E-tick observation run](../reports/economy-research-neutral-ties-window30-3600.json) earned mean Tier 2 profit $0.437 per firm per tick in its final window, with 35,991 firms earning nothing. The [0x168-tick observation run](../reports/economy-research-window360-3600.json) earned $2.186, but 40,311 firms earned nothing. Both filled all requested units. The slower calendar therefore preserves greater aggregate margins without establishing comparable company returns. Neither profile is adopted. These runs precede the neutral need-persistence correction, so they are historical mechanism evidence rather than calibration of the corrected economy.

Corrected-need full-population baseline and informative-observation experiments are being recorded separately, with source fingerprints. All company naming changes are semantic: firm identifiers, portfolios, capacities, capital, pricing rules and random streams remain unchanged.

## Runtime lookup optimization

Immutable procurement profiles are computed once per product per phase, and Tier 2 input buying advances a sorted wholesale-offer cursor as Tier 1 stock depletes. Both preserve current quotes, earned supplier preference, switching friction, inventory and random draws. A [state parity check](../reports/lookup-cache-validation.json) compared every world-state array bit for bit and transaction summaries after each tick, for 0x78 ticks in a mechanism fixture and 0xC ticks at the full 20/1,000/61,950/1m topology. All comparisons matched. Short-run timing suggests improvement at full scale, but concurrent research jobs prevent a stable throughput claim. Existing research reports retain their launch-source fingerprints.

## Recipe-composition and upstream-flow candidate

The corrected-need [standard baseline](../reports/economy-research-neutral-needs-baseline-720.json) still contradicts the Age target: final-window mean profit per firm was $1,800.458 / $59.355 / $1.107 for T0/T1/T2 over 0x2D0 ticks. The [corrected-need sparse-order candidate](../reports/economy-research-neutral-needs-observation-720.json) retained mean Tier 2 earnings of $2.373, but 40,355 firms earned no profit in its final window. All requested units were fulfilled. A short zero-sales window is expected for rare high-value orders and cannot establish permanent failure; nevertheless neither short run proves similar returns or Age growth.

A new [nominal parameter fit](../reports/economy-profile-fit.json), generated reproducibly by [the profile instrument](../tests/economy_profile_research.py), fits a two-coefficient recipe composition shape rather than 200 separate recipe corrections. At initial raw margins, the existing compound-markup premium must be approximately 0.345 instead of 0.15 for the nominal Tier 1 and Tier 0 equity-flow targets to coexist. This is an offline candidate, not a replacement price rule or an adopted default. The fitted flow uses more repeatable batches containing processed compounds and fewer bespoke high-complexity fabrication units. Its largest material-flow mismatch is 8.85%; mean C-3/C-4/C-5 unit orders decline approximately 0.798 / 0.694 / 0.414 per recipe per tick.

Recipe standardization and complexity specialization coefficients are exogenous configuration parameters, all defaulting to zero. They multiply the benchmark margin by `exp(specialization*(C-3) - standardization*compoundInputUnits)`, with inverse quantity compensation and proportional willingness-to-pay compensation. Factory starting quotes and external procurement benchmarks have separate coefficients; neither reads current prices, live costs, earned profit, or equity targets. With matched coefficients, heterogeneous buyer elasticities retain equal benchmark gross-earnings opportunity. Complexity receives fewer units and higher unit gross margins on average. Individual recipes may overlap in their margins because input composition differs. Normal settings retain their earlier profiles exactly.

The candidate's ~309 base premium is a diagnostic high-value/low-volume procurement regime, not a claim that these are sensible default prices. Its full-population simulation tests actual operating outcomes, inventory, startup effects, adaptive quotes and supplier concentration. Material-level units, revenues, acquisition COGS and realized unit gross profits are now recorded to diagnose why a nominal fit succeeds or fails. No company counts, starting cash or book asset values changed.

The earlier [full-population informative-observation run](../reports/economy-research-informative-observation-3600.json) has completed under historical purchase-conditioned product persistence. Final-window mean earned profit was $3.999 / $0.072 / $2.403 per T0/T1/T2 company. Tier 2 had 40,055 firms with zero earnings in that window; Tier 1 had 221. The average Tier 2 result remains well above the constant-profit Age target, while upstream and Tier 1 composition and supplier concentration remain misaligned. This supports further demand/supply research, not adoption of the high-markup regime or proof that any zero-window firm is permanently unprofitable.

## Tier 1 market-local tie correction

A [native selection audit](../reports/intermediate-tie-neutrality.json) found another opening identity bias: equal-price Tier 1 suppliers were ordered by rotation of the entire sparse 10,000-slot inventory array. A market contains only its hundred actual suppliers. The rotation boundary was usually outside that cohort, so its first supplier led all hundred initial ticks in six markets; most suppliers never led. This can establish unearned downstream supplier relationships and amplify apparent return differences.

Equal-price ties now rotate over the actual listed suppliers within each Tier 1 market. Every one of the real hundred companies in each of the ten opening markets leads once per hundred ticks, while cheaper quotes, stock availability and earned switching preference retain priority. The [native regression](../tests/intermediate_neutrality.test.js) verifies all ten real cohorts and those precedence rules. This corrects identity bias before freezing the protocol; it does not assign sales or equal profits. Reports launched before this correction remain historical, including the two startup-prior comparisons subsequently stopped after tick 0x564. Their [cancellation record](../reports/superseded-prior-experiments.json) records terminal status and why corrected-source comparisons replaced them. New calibration evidence must record the corrected source fingerprint.

## Controlled startup results and neutral initial price experiments

With market-local ties corrected, the matched [zero-prior](../reports/economy-research-local-ties-zero-prior-720.json) and [historical-prior](../reports/economy-research-local-ties-original-prior-720.json) runs each cover 0x2D0 ticks and the complete population. Zero-prior mean earned profit was $4.023 / $0.256 / $1.782 per T0/T1/T2 firm, compared with $0.939 / $0.134 / $1.782 under the old prior. Zero-prior production and sales were 103.033 / 103.014 Tier 2 goods per tick in the final window; old-prior production was 88.822 while sales remained 103.014. The latter drew down excess stock by 14.192 goods/tick. Both cash/book-equity and physical output-stock reconciliations passed. Initial demand forecasts now default to zero: these fresh businesses have no observed order history, while an explicit bootstrap shelf target still builds available stock. The research parameter can recreate warm-start assumptions without changing trade rules.

The [initial-direction audit](../reports/initial-quote-neutrality.json) then found array-layout bias in the first price experiment. Using inventory-slot parity made every firm in a Tier 1 product cohort raise together or lower together. Tier 2 exposed only 9.15% to upward experiments in some products and 90.85% in others. Initial directions now follow company parity, not product/inventory-slot parity. Every Tier 1 cohort starts 50/50. Tier 0 starts with balanced company directions within every width cohort. Tier 2 upward exposure stays within 49.56–50.44% across all 200 markets. The [native regression](../tests/initial_quote_neutrality.test.js) checks the complete firm topology and zero-history/bootstrap behavior. These changes remove unearned product/identity advantages before the protocol is frozen. The matched startup reports predate this direction correction and therefore are not final-current calibration evidence.

## Matched engineering benchmarks and complete material balance

The original composition fit reused fixed compound reference cost $3.85 while changing the initial compound premium. That mismatched the factory's actual opening input cost and gave recipes different nominal opportunities. Procurement now has separately authored basic/compound engineering input costs, frozen in world state on reset. Supply markups and live cost shocks do not rewrite those benchmarks. The corrected candidate uses $1.875/$4.386363636363636 and is tested against actual initial engineering costs.

The [matched reference and material fit](../reports/economy-profile-reference-balanced-fit.json) balances all ten nominal Tier 1 material flows using ten small material coefficients. It minimizes displacement from the two-coefficient recipe prior under the ten flow constraints, rather than assigning arbitrary corrections independently to 200 recipes. Multipliers range from 0.743 to 1.254. Required basic/compound units are 30.8642/28.2922 per market per tick. Inverse benchmark-margin compensation preserves equal starting Tier 2 gross earnings; mean quantities decline with complexity. The [material neutrality check](../tests/material_neutrality.test.js) verifies these analytic properties. It does not establish actual trading profitability or one-Age growth. These data profiles remain experimental.

## Completed longer corrected-direction run

The [corrected-direction full-population run](../reports/economy-research-balanced-directions-3600.json) completed 0xE10 ticks. Final-window mean profit per T0/T1/T2 firm was $6.1245/$0.0641/$1.8254. Tier 1 basic-market mean returns were approximately 5.25–5.99e-6 per tick, near the constant-earnings Age target of 5.787e-6. Compound-market mean returns fell to 0.286–0.410e-6, with realized unit gross profits only $0.089–$0.124. Thus nominally balanced input quantities do not keep realized margins balanced under competitive price learning. Tier 2 had 35,424 firms with no earnings in the final 0x168-tick window. All desired units were fulfilled. Complete cash, book-equity and finished-inventory reconciliations passed. This run predates the matched engineering reference and material coefficients; its source fingerprint is retained.

The [matched-reference short run](../reports/economy-research-reference-balanced-720.json) completed 0x2D0 ticks with final-window mean profit $4.2373/$0.2608/$1.7307. It retains substantial within-tier dispersion and cannot override the longer run's evidence of margin erosion. No high-value/low-volume candidate is adopted as a normal default.

## Physical inquiries and rare-order price learning

No-price potential quantities now use the same stochastic draw as priced quantities, rather than rounding every fractional latent need up to one. Consequently potential = desired + price loss and desired = fulfilled + stock unmet hold for every market each tick. Price loss refers to suppression of the same realized physical wishlist. The [regression](../tests/potential_demand.test.js) checks these identities, agreement with continuous expectations, and absence of spurious full-unit inquiries.

An optional research setting, `researchPriceMinimumPotentialOrders`, replaces Tier 2's calendar timeout with accumulated positive no-price inquiries when the funded-order confidence experiment is enabled. This distinguishes a genuinely absent market from an overpriced market that has physical demand but no paid orders. It remains zero/off by default. Price decisions still use earned profit and local stock, never an equity target or externally assigned ideal price.

Supplier comparison is skipped when the coupled rounding draw produces zero no-price units: every non-negative quote necessarily produces zero priced units too. Need memory remains updated. A [native parity audit](../reports/physical-demand-parity.json) found identical monetary, inventory, quote, relationship and transaction state across 0x78 fixture ticks and 0xC full-population ticks. The only changed diagnostic is the absence of a fictitious chosen supplier for a zero-unit need. This is an execution optimization, not a new allocation rule.

## Variable costs and trading-volume experiment

The nominal fit trades roughly a hundred final units per tick across 61,950 firms. An additional controlled candidate scales extraction, refinery conversion, final conversion, fixed procurement engineering costs and absolute switching frictions together by 0.00462962962962963. Book capital, opening cash, company counts, physical capacities and the Age duration stay fixed. At unchanged nominal markups, quantities increase by the inverse scale while expected profits remain unchanged: the required raw flow uses half of the fixed 200,000-unit extraction capacity per tick. This is a demand/supply data experiment; both the unscaled and scaled candidates use the same physical-inquiry confidence settings.

The [cost-scale regression](../tests/unit_cost_scale.test.js) verifies inverse quantity compensation, proportional benchmark valuation, unchanged equity capital, actual production and purchases, and fractional-cent quotes. Final conversion supply costs and the authored procurement conversion benchmark have independent multipliers, both defaulting to one. The quote precision is five decimals, with a numerical minimum of $0.00001 per unit. A $0.01 per-unit floor would create an artificial markup when costs are scaled below a cent; the new guard represents one cent per minimum wholesale lot and still enforces actual variable-cost break-even. These checks establish numerical consistency, not calibrated returns.

## First matched higher-volume results

The [physical-confidence unscaled run](../reports/economy-research-physical-confidence-720.json) and [scaled-volume run](../reports/economy-research-volume-balanced-720.json) share identical source hashes, all firm counts and capital, confidence settings, recipe profile and observation period. Each covers 0x2D0 ticks with its final 0x168 measured. Scaling variable costs and fixed benchmark costs yielded final-window means $6.5865/$0.2493/$1.7248 per T0/T1/T2 firm versus $4.1459/$0.2620/$1.7307 unscaled. Tier 2 zero-earning firms fell from 35,044 to 50; unit fulfillment remained 99.9869%. This supports increasing physical trading intensity, but does not prove neutral returns: one-product Tier 2 firms averaged $3.6629 while four-product firms averaged $1.5863. Recipe exposure is equal at initialization; realized adaptive-price outcomes require further investigation.

The [84/77 refinery-capacity experiment](../reports/economy-research-volume-capacity-720.json) changes only the basic/compound refinery capacities from 320/240. These values place the nominal fitted flows near 80% of refinery capacity, retaining upstream 10,000 per firm and all opening book values. Its means were $6.3532/$0.3497/$1.7279; only one Tier 1 firm and 38 Tier 2 firms earned no profit in the final window. Fulfillment was 99.9878%. A longer paired comparison is running to test margin stability and width effects. Neither these capacities nor the scaled-cost profile is adopted as a normal default.

Future reports distinguish returns on simulation-start equity from returns on opening equity of the measured window. They also record revenue, sold units, gross profit per unit, and quotes relative to initial benchmarks by initial portfolio width, plus elapsed runtime. Optional checkpoint files expose incomplete-run progress explicitly; a checkpoint cannot substitute for a completed report.

## Observation-period counterfactual

The [0x2D0-tick annual-observation trial](../reports/economy-research-volume-annual-observation-720.json) holds the scaled cost and 84/77 refinery-capacity data fixed, changes the existing price observation interval to 0x168 ticks, and disables the optional funded/physical-inquiry confidence gates. It tests the research-stage price-measurement protocol before any standard calibration version is frozen. Trading, demand response, supplier selection and the profit-following update formula are unchanged. This comparison isolates an alternative observation protocol as a whole, not the separate effects of interval length and confidence gates.

Final-window mean earnings per T0/T1/T2 firm were $5.8824/$0.3285/$1.7488, with 99.9972% desired-unit fulfillment. All ten Tier 1 cohort mean initial-equity returns were within 3.1% of the constant-earnings Age target; individual firm outcomes remain dispersed. Tier 2 initial-width 1/2/3/4 means were $1.9281/$1.6519/$1.7069/$1.7617, compared with a nominal $1.7506 per-firm target. Longer observation reduces the early disparity in this experiment, but 0x2D0 ticks include only a few annual price decisions and do not establish settled behavior. Longer trials are measuring quote drift and equity growth before a protocol or parameter set is adopted.

The three diagnostic parameter sets are saved under [parameter candidates](../reports/parameter-candidates/volume-annual-observation.json). Reproduce an actual full-size trial with `RESEARCH_TICKS=3600 RESEARCH_CONFIG=reports/parameter-candidates/volume-annual-observation.json RESEARCH_OUTPUT=reports/economy-research-volume-annual-observation-3600.json node tests/economy_research.js`. Configurations alter no firm counts or opening book-capital values and contain no online target-aware return rule.

## Price-learning execution optimization

Profiling a full-population 0x3C-tick instrumented run found 31.3% of CPU samples in `learnedQuote`. Most calls cannot make a price decision on that date. The core now checks the unchanged decision schedule first and creates references to learning arrays once per tier per phase. Cost reservations still apply on every tick. No decision dates, profit measurements, confidence gates or price formulas change.

The [reproducible parity instrument](../tests/execution_parity_research.js) compares the current actual worker with an immutable compressed [reference kernel](../reports/reference-kernels/before-learning-optimization.js.gz). Every world-state field and transaction summary matched bit for bit in both [0x78 mechanism-fixture ticks](../reports/learning-execution-parity-fixture.json) and [0x3C full-population ticks](../reports/learning-execution-parity-full.json), with no excluded fields. The full fixture includes the scaled-cost/capacity candidate and enabled confidence gates. Paired alternating wall timing after warmup measured a ratio of 0.598 at full scale; concurrent jobs and JIT state make this an indicative measurement, not a throughput guarantee. Earlier ongoing financial runs retain their launch-source hashes, while this audit establishes checked execution equivalence for the optimization.

## Completed unconstrained-refinery longer trial

The [higher-volume 0xE10-tick run](../reports/economy-research-volume-balanced-3600.json), still using 320/240 refinery capacities, completed with final-window means $5.6245/$0.2466/$1.6635 and 99.9813% fulfillment. Its tier averages conceal weak firms: compound-refinery median returns are only 0.2–12.2% of the nominal Age rate, and the lowest Tier 0 firm earns $0.0101/tick. Initial-width Tier 2 means also reverse the short-run pattern: $0.9601/$1.3098/$1.4434/$1.7321 for widths 1–4. These changing relative outcomes reject a claim of settled neutrality from the short run.

A further data-only candidate places nominal extraction and basic/compound refinery use near 80% rather than leaving extraction half idle. It scales variable costs, benchmark costs and switching frictions together to 0.0028935185 and uses refinery capacities 134/123, preserving fixed company counts, Tier 0 10,000 capacity, cash, plant book capital and the annual observation protocol. The short full-population trial is testing whether this improves weak upstream firms without changing nominal profit opportunity. Future reports also identify Tier 0 width cohorts and every Tier 0 firm's actual equity multiple, so averages cannot conceal those firms.


## Completed capacity and observation trials

The [84/77-capacity longer trial](../reports/economy-research-volume-capacity-3600.json) completed 0xE10 ticks with final-window per-firm mean earnings $5.0400/$0.4035/$1.6651 for T0/T1/T2 and 99.9808% desired-unit fulfillment. Basic-refinery cohort mean returns rose to 1.64–1.79 times the constant-earnings Age rate, while compound cohorts reached 1.09–1.25 times. The lowest Tier 0 firm earned $0.0772/tick. Tier 2 initial-width means were $1.1418/$1.2354/$1.3884/$1.7492; 622 firms earned nothing in the final 0x168-tick window. Reduced refinery capacity improves several average margins but does not establish comparable individual returns.

The [annual-observation longer trial](../reports/economy-research-volume-annual-observation-3600.json) also completed 0xE10 ticks. Means were $6.6794/$0.3315/$1.7277, fulfillment 99.9953%. Tier 1 cohort mean initial-equity returns ranged from 0.879 to 1.195 times the Age rate; five Tier 1 firms and 1,560 Tier 2 firms earned nothing in the measured window. Tier 0's minimum profit was $0.0206/tick. Tier 2 width means were $1.6021/$1.3280/$1.5018/$1.7970. The early 0x2D0-tick fit therefore does not persist uniformly as firms adapt prices. These are completed diagnostics, not adopted parameters or proof that zero-window firms never earn again. Cash and physical-stock reconciliations passed in both runs.

## Upstream utilization sweep

The [80%-nominal-utilization short trial](../reports/economy-research-all-tier-utilization-80-720.json) completed 0x2D0 ticks with means $5.8832/$0.3277/$1.7496 and 99.9978% fulfillment. All ten Tier 1 cohort mean returns lay within 3.4% of the nominal Age rate. However, Tier 0 width 1/2/3/4 means were 1.189/1.167/0.735/0.437 times that rate: narrow extractors still outperform companies sharing capacity across more elements. Tier 2 initial-width means were $1.9733/$1.6887/$1.7146/$1.7593, with 61 zero-earning firms. The newly recorded individual Tier 0 rows make the width disparity explicit rather than hiding it in the mean.

A 0xE10-tick extension is running. Separate 90% and 95% nominal-utilization candidates scale variable costs, fixed procurement engineering costs and absolute switching frictions together, using basic/compound refinery capacities 150/138 and 159/146 respectively. Their nominal expected profits and all opening capital, company counts and Tier 0 capacities remain unchanged. All three use the same annual-observation protocol and demand-response, trading and price-learning formulas. They test whether stronger physical demand reduces unused capacity and weak upstream firms; the utilization labels describe nominal fitted flow, not measured actual utilization. Candidate files are retained in `reports/parameter-candidates/`; none replaces normal defaults.

The optimized source passed all 32 quick checks before the extraction-allocation correction below; its source hashes were checked against the gate report at that checkpoint. This verifies the implemented contracts and scenarios; it does not close the economic calibration or Age-horizon requirements.


## Extraction allocation order correction

An isolated actual-worker production experiment found that four equal stock deficits split Tier 0's shared 10,000 capacity as 2,500/1,875/1,406/4,219. The loop applied each original deficit share to the remaining capacity, so listed element order changed production even when needs were equal. This is an implementation bias in physical supply, not a calibrated demand difference.

The allocator now reduces both the remaining capacity and remaining deficit denominator after each element. Equal deficits produce 2,500 each; proportional deficits 4,000/8,000/12,000/16,000 produce 1,000/2,000/3,000/4,000, and reversing them reverses the allocation. [Inventory-limit regressions](../tests/inventory_limits.test.js) exercise the actual worker with downstream purchases disabled to isolate extraction. Shared capacity, warehouse limits, stock targets, extraction costs and cash constraints retain their existing guards. This correction does not assign equal sales or profits.

All previously launched utilization trials retain the old allocator and their launch-source fingerprints. A new full-population 80% candidate run records the corrected source separately in `reports/economy-research-balanced-extraction-80-720.json`; earlier performance parity audits remain evidence about their checked pre-correction versions. Calibration comparisons must distinguish the allocation correction from demand/supply data changes.


The pre-correction [90%](../reports/economy-research-all-tier-utilization-90-720.json) and [95%](../reports/economy-research-all-tier-utilization-95-720.json) short trials have completed. Their T0/T1/T2 mean profits were $5.9027/$0.3282/$1.7501 and $5.8945/$0.3276/$1.7503 respectively; fulfillment exceeded 99.9978%. Tier 0 width 1/2/3/4 mean initial-equity returns were 1.112/1.106/0.881/0.671 times the nominal Age rate at 90%, and 1.060/1.038/0.988/0.853 at 95%. This is evidence that demand intensity reduces the upstream width gap even with the historical allocator. The 95% trial's ten Tier 1 cohort means were within 2.8% of the nominal rate, while Tier 2 width-one mean return was still 18.5% above it. Neither short trial validates full-Age growth or permanently comparable returns.

A 0xE10 corrected-allocation 95% trial is now running in `reports/economy-research-balanced-extraction-95-3600.json`, alongside the matched corrected-allocation 80% short trial. No candidate alters firm counts or capital, and no target enters runtime market decisions.


The corrected extraction core passed all 32 quick checks, including the expanded inventory regressions, and the gate's model/kernel/worker fingerprints match the current files. [The quality report](../reports/scarcity-aware-quality-quick.json) is a contract/scenario checkpoint, not proof of an Age's economic growth.


The [corrected-allocation 80% short trial](../reports/economy-research-balanced-extraction-80-720.json) completed 0x2D0 ticks. Means were $5.8846/$0.3278/$1.7496, fulfillment 99.9979%. Tier 0's p10 profit rose from $2.9742 to $4.9636 in the matched historical-allocation trial, but its minimum fell from $2.0128 to $1.6775; four-element companies still lag. Width 1/2/3/4 means were 1.171/1.128/0.876/0.348 times the nominal Age rate. Correcting the physical bias is necessary but does not itself calibrate company profits. A matched corrected 80% 0xE10 extension is now running alongside the corrected 95% extension. Both retain all firm counts, capital and pricing settings.


## Cumulative-equity protocol comparison

[The completed-run cumulative comparison](../reports/cumulative-equity-protocol-comparison.json) separates actual equity gained over the full run from profit in the last measured window. In the historical 320/240-capacity monthly-observation trial, Tier 2 width 1/2/3/4 cumulative mean growth was 1.033/0.966/0.959/0.964 times the linear Age pace over 0xE10 ticks, despite much lower narrow-firm profit in the last window. In the annual-observation 84/77 trial, those cumulative figures were 0.743/0.790/0.895/1.018. Recent-window profit alone therefore gives an incomplete view of portfolio advantages; cumulative actual equity is the user's leading criterion. These scaled comparisons describe realized growth at the observed horizon and are not extrapolated claims of Age doubling.

A matched corrected-allocation 95% monthly-observation run is now testing 0x1E-tick observation with the existing 10-funded/20-physical-opportunity confidence settings, against the corrected annual-observation 95% run. All demand/supply data, populations and capital are identical between these new trials. This remains protocol research before freezing the standard; it compares interval-plus-confidence protocols together, not the separate causal effects of their fields.


## Unused-material selection experiment

An execution experiment selected suppliers only for materials present in a firm's operating recipes, computing recipe masks once per phase. [Fixture parity](../reports/material-selection-parity-fixture.json) and [full-population parity](../reports/material-selection-parity-full.json) matched every state field and transaction summary for 0x78 and 0x3C ticks. The full paired timing ratio was 1.006, showing no demonstrated full-scale speed benefit despite less supplier selection. The experiment was not adopted; the core was restored byte for byte to the checked pre-experiment kernel, and its model/kernel/worker hashes still match the passing 32-check gate. The immutable reference and parity reports retain this result so it cannot be presented as an achieved speedup.


## Completed historical-allocator 80% extension

The [80% historical-allocation extension](../reports/economy-research-all-tier-utilization-80-3600.json) completed 0xE10 ticks with T0/T1/T2 means $6.9690/$0.3256/$1.7324 and 99.9970% fulfillment. Tier 0 width 1/2/3/4 cumulative mean equity growth was 1.359/1.193/0.939/0.734 times the linear Age pace; Tier 2 width 1/2/3/4 figures were 0.856/0.859/0.932/1.010. The physical demand increase does not remove all cumulative width differences. Its minimum recent upstream profit was $0.0314/tick, while every firm had grown equity over the full run. Cash, acquisition-basis equity and physical-stock reconciliations passed. This report predates the extraction correction and remains a matched historical comparator.

## Actual Age-horizon experiment started

An exploratory **0x2A300-tick (one Age)** run is now executing the corrected extraction core with the 95% annual-observation candidate, seed 12345, all 20/1,000/61,950 firms and one million external procurement agents. Its completed output will be `reports/economy-research-age-95-annual-12345.json`; `reports/economy-research-age-95-annual-12345-progress.json` is explicitly an incomplete checkpoint. It uses actual purchases, production, price learning, input and output inventories, acquisition-basis equity and all company portfolios throughout the horizon. No time compression, company-count reduction, aggregate replacement economy, target-aware payout or automatic capital revaluation is used.

This is a diagnostic candidate run, not adoption of its defaults or a claim of successful Age doubling. The final report will include actual company equity-multiple distributions, material and portfolio cohorts, and monetary/physical reconciliation checks. The source hashes and complete configuration identify exactly what ran; later research changes cannot turn its launch version into a different standard. The paired 0xE10 monthly/annual and 80%/95% corrected-source trials are still completing separately.


## Completed corrected-allocation 95% annual trial

The [corrected 95% annual-observation trial](../reports/economy-research-balanced-extraction-95-3600.json) completed 0xE10 ticks. Final-window mean profit was $8.3188/$0.2981/$1.7374 for T0/T1/T2, fulfillment 99.9979%; all monetary and physical reconciliation checks passed. Cumulative tier mean equity growth was 1.207/0.958/0.992 times the linear Age pace. Tier 0 width 1/2/3/4 cumulative means were 1.307/1.139/1.182/1.064; Tier 2 width means were 0.925/0.896/0.942/1.007. The higher physical-demand intensity reduces the cumulative upstream width gap considerably relative to the historical 80% trial, though it does not eliminate return differences or establish stationarity.

Measured raw sales were approximately 190,553 units/tick, close to 95% of extraction's fixed 200,000 total capacity. Upstream unit gross margins rose above their initial benchmark, while Tier 1 basic cohorts' recent returns fell to 0.759–0.884 of the nominal Age rate. Thus actual quantity symmetry does not itself fix margin allocation along the chain. The Age run tests whether these margins stabilize or continue shifting, and is not grounds for adopting the profile before its results are inspected.

A further primary-source check, [Fonseca and Normann's capacity-pricing experiments](https://www.mohrsiebeck.com/en/article/excess-capacity-and-pricing-in-bertrand-edgeworth-markets-experimental-evidence-101628093245613x666306/), finds lower prices with greater excess capacity and examines myopic price adjustments and cycles. This supports testing capacity slack and averaging over realized trajectories. Their duopoly/triopoly experiments do not validate this multi-tier, inventory-holding worker or imply equal company ROE. Connecting those mechanisms to the observed upstream margin shift here remains an inference to test, not an established causal result.


The [corrected 80% annual trial](../reports/economy-research-balanced-extraction-80-3600.json) completed 0xE10 ticks with means $7.3502/$0.3175/$1.7324 and 99.9970% fulfillment. Upstream minimum recent profit remained $0.1713/tick. The [matched corrected 95% monthly trial](../reports/economy-research-balanced-extraction-95-monthly-3600.json) completed with means $12.8376/$0.2518/$1.6409 and 99.8923% fulfillment. Its cumulative tier mean equity growth was 1.956/0.790/0.951 times the linear Age pace, compared with 1.207/0.958/0.992 for 95% annual observation. Both protocols preserve demand/supply data and use the same underlying profit-following formula. The faster observation-plus-confidence protocol increases upstream capture while reducing downstream returns in this finite-horizon experiment. The expanded [cumulative comparison](../reports/cumulative-equity-protocol-comparison.json) records company and cohort distributions for all three corrected-source trials. Neither protocol is yet adopted or shown to satisfy the Age target.


## Fixed-protocol supply-cost counterfactual

The actual Age candidate's later checkpoints approach $172 upstream profit/tick, above the $115.74 constant-earnings target, while remaining incomplete. A separate 0xE10-tick [supply-cost counterfactual](../reports/parameter-candidates/supply-cost-120-fixed-protocol.json) raises extraction, conversion and matching frozen engineering benchmark costs by 20%. Nominal quantity factors decline by one sixth while initial expected gross-earnings opportunities remain unchanged. Basic/compound refinery capacities are 133/122 and shared final-firm output capacity is five, proportional adjustments that retain approximately the reference manufacturing utilization. Tier 0's prescribed 10,000 capacity stays fixed, giving extraction greater nominal slack. All warehouse limits and starting capital remain fixed.

Unlike the earlier currency-volume sweep, this comparison holds absolute switching frictions fixed, as well as observation period, learning coefficients, sampling, buyer elasticity, activation and all other behavioral configuration fields. It changes only production costs, authored engineering references and manufacturing capacities. [The normalized configuration and initial-state audit](../reports/supply-cost-fixed-protocol-audit.json) verifies the complete allowed difference set, unchanged company portfolios and cash/equipment book values, and the exact inverse quantity/proportional valuation/unchanged initial gross-opportunity identities. This establishes the counterfactual's scope, not its operating returns or Age performance. It jointly tests greater upstream supply slack and changed cost-to-friction ratios; it does not isolate their separate effects. The actual full-population financial report will be `reports/economy-research-supply-cost-120-3600.json`. No candidate is adopted.

The updated full-population default scenario check also passes for 0x168 ticks: all 200 final markets trade; C-3/C-4/C-5 unit orders average 267.45/167.49/114.57 per market per tick. C-5's aggregate unit share is 47.17%, compatible with declining orders per market because it accounts for 60% of active market names. The obsolete 20%-aggregate-share gate would reject this valid ordering. This scenario result verifies complexity/activity behavior at the observed horizon, not calibration of default ROE.


## Completed fixed-protocol supply-cost counterfactual

The [20% supply-cost increase](../reports/economy-research-supply-cost-120-3600.json) completed 0xE10 ticks at full population. Final-window mean profit was $7.0661/$0.3229/$1.7340 per T0/T1/T2 firm and desired-unit fulfillment was 99.9972%. Cash and acquisition-basis equity reconciliations passed, with zero finished-stock reconciliation error. Cumulative mean equity growth reached 1.145/0.988/0.991 times the linear Age pace over this observed interval; these are realized finite-horizon comparisons, not Age forecasts.

Tier 0 width 1/2/3/4 cumulative means were 1.297/1.253/0.915/0.674 times that pace. The weakest extractor earned $0.1295/tick in the final window, despite positive cumulative growth. Tier 2 initial-width means were 0.858/0.866/0.928/1.011, and 1,639 firms earned nothing in the measured window. Compared with the 95% annual reference, tier averages look closer while broad extraction firms lag more. This rejects adoption on average returns alone. The [cumulative comparison](../reports/cumulative-equity-protocol-comparison.json) now includes this completed run.

## Processing-value and raw-flow candidate

The [offline profile fitter](../tests/economy_profile_research.py) now accepts explicit `PROFILE_TIER0_NOMINAL_SHARE` and `PROFILE_CONVERSION_RATIO` assumptions. Its default share 1 and conversion 0.25 reproduce the preserved baseline fit exactly, as checked in [the reproduction audit](../reports/economy-profile-default-reproduction-audit.json). Neither assumption is a runtime target, payout or price-learning input. They set physical order quantities, manufacturing expenses, initial quotes and fixed engineering demand profiles before the simulation starts.

A separate [75%-raw-flow fit](../reports/economy-profile-raw-flow-75-fit.json) uses share 0.75 and conversion 0.75. It reduces nominal raw-unit demand by one quarter and raises Tier 1 processing value added, while retaining the nominal Tier 1 and Tier 2 profit opportunities. The hypothesis is that upstream price learning's observed margin increase may then leave room for the intended realized returns. The 0.75 share is an exploratory finite-trial adjustment, not an established long-run correction. Nominal Tier 0 profit is $86.81/tick; the actual worker can earn more or less through ordinary trading. No nominal profit is credited to any firm.

The [saved candidate](../reports/parameter-candidates/processing-value-raw-flow-75.json) uses the reference cost scale, Tier 1 processing expense $0.001827485/unit, basic/compound initial benchmarks $0.006091618/$0.013235424, initial compound markup premium 0.421328671, and refinery capacities 119/110. Its Tier 2 engineering shape and matching initial markup are refitted to the ten material-flow constraints. Tier 0's capacity, all warehouse caps, Tier 2's shared six-unit capacity, starting cash and machinery book values remain unchanged. The behavioral protocol—including price-learning coefficients and cadence, switching costs, search, demand elasticity and activation—is identical to the 95% annual reference.

[The full-population initial-state audit](../reports/processing-value-fixed-protocol-audit.json) checks every changed configuration field, unchanged cash/equipment/portfolio arrays, exactly matched engineering costs and seller/buyer markups, and all ten fitted material flows. Nominal Tier 1 product profits remain $11.5741/tick for each basic cohort and $46.2963 for each compound cohort; Tier 2 total nominal profit remains $108,448.35/tick. C-3/C-4/C-5 mean nominal orders decline to 242.25/215.43/127.10 units per market per tick, while mean unit gross margins rise to $3.15/$6.31/$10.32. Those identities describe initial expected opportunities, not realized sales or equity growth.

An actual 0x2D0-tick full-population run is testing this candidate in `reports/economy-research-processing-value-75-720.json`; its progress file is explicitly incomplete. The existing actual Age reference run continues independently, having passed 0x40B0 ticks with upstream profit approximately $194/tick in its latest 0x3C-tick window. The earlier $172 checkpoint did not establish a permanent plateau. Neither candidate is adopted or shown to meet the one-Age growth target.


## Working protocol decision

[Annual-v1](../reports/calibration-protocol-annual-v1.json) is frozen as the working protocol for the demand/supply calibration phase. It records the exact three core source fingerprints, every fixed behavioral configuration field, the allowed demand/supply fields, immutable company counts, opening capital and physical topology. Seed changes are explicit replications. The matched annual/monthly full-population experiments support choosing annual observation for further calibration because its cumulative downstream return distortion is smaller at the same input data. Contract and scenario checks support conservation, feasible orders and opening opportunity neutrality. This selects a research protocol; it does not validate the eventual standard parameters, seed robustness or one-Age growth.

Any later runtime-rule correction or change to fixed behavioral fields must have a separately recorded protocol version. Demand/supply-only comparisons under annual-v1 cannot silently change their pricing, supplier or buyer rules. Normal application defaults remain uncalibrated while candidates are tested.

## Completed reduced-flow processing-value trial and capacity-preserving follow-up

The [processing-value short trial](../reports/economy-research-processing-value-75-720.json) completed 0x2D0 ticks, reconciling cash, book equity and physical stock. Final-window mean profit was $4.4209/$0.3278/$1.7492 per T0/T1/T2 firm; fulfillment was 99.9977%. Tier 1 material cohort mean recent returns were 1.002–1.038 times the linear Age rate. Nevertheless, actual cumulative tier mean equity growth reached 0.758/0.999/0.973 times the linear Age pace. Tier 0 width 1/2/3/4 means were 0.842/0.827/0.633/0.465. The reduced physical raw flow leaves broader extraction firms behind, so this candidate is not adopted. There are 74 zero-profit Tier 2 firms in the final window; that is a window result, not lifetime exclusion.

The [capacity-preserving follow-up](../reports/parameter-candidates/processing-value-capacity-95.json) retains the new Tier 1 processing ratio and shape fit, while reducing the reference currency-cost scale by a further quarter. Compared with the initial 95% reference, extraction cost is $0.001827485/unit, Tier 1 processing expense $0.001370614/unit, the basic reference quote is unchanged and the compound reference is $0.009926568. Manufacturing and extraction capacities, all warehouses, starting cash, plant capital and every fixed annual-v1 behavioral field match the reference. Switching costs are also unchanged; this is not a uniform currency rescaling.

[Its initial-state audit](../reports/processing-value-capacity-fixed-protocol-audit.json) verifies nominal raw sales of exactly 190,000 units/tick, the same 95% of Tier 0 total capacity as the reference, and identical nominal flows for all ten Tier 1 materials. Nominal raw profit remains $86.81/tick, leaving the hypothesis about learned upstream margins to be tested in actual trades. Nominal Tier 1/Tier 2 profit opportunities are preserved, C-3/C-4/C-5 mean units still decline and unit margins rise. The audit proves physical-flow and initial-state identities, not operating equity growth.

An actual full-population 0xE10-tick follow-up is running in `reports/economy-research-processing-value-capacity-95-3600.json`. Its incomplete checkpoint and native process handle are recorded separately from completed trials. The original 0x2A300-tick Age reference continues; no new candidate has replaced its launch configuration or been adopted as application defaults.


## Candidate-compatible full market-balance verification

The full-size [market-balance instrument](../tests/long_run_balance.test.js) now accepts a saved `BALANCE_CONFIG`, in addition to explicit seed/horizon/output settings. Defaults still exercise the ordinary application configuration. A candidate run records its full normalized configuration, all three runtime source fingerprints and the launch fingerprints of the verifier and price helper. It retains all existing market-activity, participation, utilization, inventory, cash and pricing assertions.

The price verifier still had a $0.01 numerical floor after the engine moved to $0.00001 for wholesale unit quotes. This would falsely classify profitable fractional-cent transactions as below cost. [The price audit helper](../tests/price_audit_helpers.js) now uses the model's actual numerical floor. A regression attributes 1,000 units bought at $0.005/unit with $0.004/unit cost correctly: $5 revenue and 25% margin over cost in both raw and processed markets. The existing below-cost failure and break-even checks still pass. This is a verifier correction; the frozen runtime market rules are unchanged.

The full verifier also records actual final/opening book-equity distributions for all producer tiers, each Tier 1 material, initial Tier 2 portfolio widths and sectors, and Tier 0 element widths. It reconciles every firm's total actual equity gain against its cumulative acquisition-basis profit. Bought equipment remains paid book capital and inventories retain their acquisition basis; unsold quotes do not increase equity. These additions measure the user's leading criterion without extrapolating a short horizon.

A 0xE10-tick seed-31415 run of the capacity-preserving processing-value candidate is now executing these checks in `reports/processing-value-capacity-95-balance-31415-3600.json`. All 20/1,000/61,950 producers and one million procurement agents remain in the worker. Its first 0x168-tick window has every final firm trading, 11.55% final-factory utilization and 95.08% desired-unit fulfillment including startup. The ongoing seed-12345 financial trial's last observed 0x3C-tick checkpoint has $103.68/$323.02/$108,139.28 total T0/T1/T2 profit per tick at 0x708. The target totals are $115.74/$324.07/$108,448.35. These are incomplete-run observations; neither a gate pass nor the Age target is yet claimed. A fresh quick suite is also running after the verifier change.


## Completed capacity-preserving processing-value trial

The [seed-12345 full-size trial](../reports/economy-research-processing-value-capacity-95-3600.json) completed 0xE10 ticks with final-window per-firm mean profits $6.0768/$0.3105/$1.7374 for T0/T1/T2 and 99.9980% desired-unit fulfillment. Cash, per-firm acquisition-basis equity and finished-stock reconciliation passed. Actual mean equity multiples were 1.018401/1.020568/1.020657. Over the observed interval, these gains are 0.883/0.987/0.992 times the linear Age pace; they are not forecasts of an Age outcome.

Tier 0 width 1/2/3/4 cumulative mean gains were 0.973/0.849/0.826/0.743 times that pace, with recent-window returns 1.236/0.966/0.879/0.900. Broad extractors are catching up in this finite window but still lag cumulatively. Tier 2 initial-width means were 0.880/0.896/0.946/1.006. Final-sector cumulative means ranged 0.985–0.998. Two Tier 1 and 1,337 Tier 2 firms earned nothing in the final window; all had positive cumulative equity growth. Tier 1 material recent mean returns ranged 0.874–1.004 times the target. These differences prevent claiming completed company-level calibration from near-target tier averages.

Measured raw sales were 190,488.89 units/tick, preserving approximately 95% extraction utilization. Compared with the corrected 95% annual reference at the same horizon, extraction average earnings are closer to target while Tier 1/Tier 2 cumulative growth remains near target. The [cumulative comparison](../reports/cumulative-equity-protocol-comparison.json) now includes this trial.

An actual 0x2A300-tick seed-12345 run of this candidate is now executing separately in `reports/economy-research-age-processing-value-95-12345.json`; its progress file is incomplete evidence. The original 95% reference Age run continues as its own experiment, and the seed-31415 market-balance/equity/price audit is still pending. No new defaults are adopted. The corrected verifier passed a fresh complete 32-check quick suite with matching frozen runtime fingerprints.

A [native CPU profile](../reports/economy-processing-value-95-profile-summary.json) of 0x3C actual full-population worker ticks measures manufacturing at 35.2% and final procurement at 25.6% of sampled execution. It is an execution diagnostic, not a smaller calibration world, speedup claim or alternative engine. No runtime optimization has been adopted from this profile; the annual-v1 source fingerprint remains unchanged.


## Completed second-seed financial and market-price audit

The [seed-31415 candidate audit](../reports/processing-value-capacity-95-balance-31415-3600.json) completed 0xE10 ticks and passed every accounting, price, inventory, market-activity, firm-participation and utilization assertion. All 214 active markets trade. The final window has 99.9977% unit fulfillment, 11.88% final-factory utilization and 60,554 of 61,950 final firms trading. Paid asset and inventory bases reconcile each firm's cumulative profit to its actual equity gain, with maximum discrepancy $0.000000972; the whole cash ledger's maximum discrepancy is $0.00001872. None of the active markets is trading below cost on its measured average or pinned to the numerical floor.

The [cross-seed comparison](../reports/processing-value-capacity-cross-seed-comparison.json) verifies identical runtime fingerprints and normalized configuration apart from seed. In seed 12345/31415, actual mean equity gains over ten years are 1.8401%/1.7702% for T0, 2.0568%/2.0809% for T1 and 2.0657%/2.0684% for T2. The constant-earnings reference for that interval is 2.0833%; these measurements do not extrapolate outcomes over 480 years. Tier 0's broad firms and narrow Tier 2 portfolios still lag, and both instruments report their distributions. Passing market health and matching tier averages does not establish the requested company-level harmony or full-Age growth.

The two actual Age processes remain diagnostic and incomplete. These completed candidate replications support continuing the capacity-preserving profile's longer test; they do not constitute final parameter adoption or robustness to all normal disturbances. No company count, opening capital or fixed behavioral rule changed between them.
