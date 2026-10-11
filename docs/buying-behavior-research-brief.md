# Buying behavior research and implementation brief

Date: 2026-10-11. Audience: the AI executing this research and development task.

Develop, test, and recommend a coherent purchasing model for Midbridge Colony. Cover how buyers estimate demand, value quantities, construct baskets, discover suppliers, pay loyalty fees, update preferences, and compete for finite stock. Investigate the economic model as seriously as the implementation. Deliver a reproducible final report, including negative findings and a clear adoption recommendation.

**Company-experienced demand, market intelligence, and hybrid approaches are all open options. Previous conversational equations are hypotheses, not an approved specification.** Do not simply implement the last proposed formula. The present task is to discover which model works, explain why, and establish the limits of that conclusion.

## Purpose and scope

The motivating observation is that upstream producers can retain high margins with spare capacity while downstream manufacturers face rising input costs and price-sensitive final demand. Possible causes include procurement rules, switching friction, supplier search, stock allocation, inventory policies, and sell-side price feedback. Establish causality rather than assuming that one mechanism explains the result. Neither equal company profits nor a predetermined equilibrium price is an acceptance criterion.

Cover every operating purchasing relationship:

| Actor | Relevant behavior |
| --- | --- |
| T-1 Gaia | Environmental source; do not invent supplier competition or purchasing behavior for her. |
| T0 Extractors | Extraction costs, inventory, sales, and demand feedback; verify whether any actual procurement applies. |
| T1 Refineries | Purchases from T0, including wholesale lots, recipes, shared cash, and storage. |
| T2 Manufacturers | Purchases from T1 and other T2 companies; complementary and repeated ingredients; intermediate production. |
| T3 Distributors | Price-sensitive final demand, sampled offers, partial or split purchases, and preferences. |

Audit interactions with machinery purchases and ownership where they exist, but do not add expansion, investment, credit, or capital-goods markets as an incidental part of this task.

Start with an audit, research, and isolated prototypes. Complete experimental implementation and validation before presenting a concrete rollout decision. Do not change the user's live run, active defaults, or preserved baseline while researching. Present the validated implementation and report for the final green light before enabling it in the watched economy.

## Current baseline and evidence

Repository: `/Users/csys/Desktop/ibicot`. Defaults inspected when this brief was written: 20 T0 companies, 1,008 T1 companies, 57,960 T2 companies, one million Distributors; 14 refined materials and 105 invented manufactured products. Distributor activation is 10.5%; expected latent final demand is 2.1 million units per tick. Rent is currently zero. Re-read code and run configuration before execution; these numbers are provenance, not permanent constraints.

The reference implementation is Python; hot paths use NumPy and compiled Numba loops. Stock-dependent trading currently executes sequentially inside compiled loops. Array storage does not imply simultaneous clearing.

Start with these files:

- [Current integration rules](midbridge-integration.md), [design canon](design_canon.md), and [README](../README.md). Some older prose contains superseded populations, recipes, timing, and information restrictions. Record conflicts; current user decisions take precedence.
- [Model](../economy/core/model.py), [configuration](../economy/core/config.py), [state](../economy/core/state.py), and [supplier ranking and affordability](../economy/core/trading.py).
- [Reference tick](../economy/kernel/tick.py), [compiled execution](../economy/kernel/numba.py), and [input market settlement](../economy/kernel/input_market.py).
- [Recording](../economy/server/recording.py), [runtime](../economy/server/runtime.py), [checkpoint persistence](../economy/server/persistence.py), and [tests](../tests/py).

The preserved zero-rent experiment is under `stats/zero-rent-one-generation-20261011-102717/`. Its `served-recovery-path.txt` identifies the latest replay directory. Check manifests, verification records, and tick coverage before combining files: resumed recordings cover different intervals, and some older logs lack product/company detail. Never label incomplete or mismatched replay data as a complete comparison.

Record the starting commit, working-tree patch, configuration, catalog hash, environment, and checkpoint. The workspace already contains unrelated uncommitted changes; preserve them. Audit current behavior independently of prior commentary, especially full-fill supplier preference, fee-aware ranking, unconditional preference updates, price-learning overrides, and purchasing versus production margin checks.

## Confirmed behavioral requirements

1. Supplier choice, preference changes, and loyalty payments are separate decisions. Preferences are per buyer and product.
2. Use five sampled alternatives plus the incumbent as the intended production search scope. Specify distinctness, eligibility, fewer-than-five markets, tie-breaking, and deterministic sampling. Exhaustive market search is a research benchmark, not an assumed replacement.
3. Partial-stock suppliers remain eligible. Do not automatically prefer a higher-priced offer merely because it can fill the whole request.
4. Loyalty fees affect economic selection. A lower sticker price need not justify a purchase when its savings or basket benefit do not cover the fee. Never dilute a fee over units that cannot actually be bought.
5. Incumbent availability affects the comparison before selection. If it cannot fulfill the whole relevant bid, no loyalty fee is payable to it, irrespective of whether the alternative fills the bid or preference changes.
6. If the incumbent could fulfill that bid and the buyer purchases elsewhere, the incumbent receives the fee even when the outside purchase is partial and preference does not change. No completed purchase means no fee.
7. A partial purchase cannot by itself replace the product's incumbent. A qualifying challenger must actually fulfill the whole relevant demand to replace it.
8. Purchased quantity must respond to price. Do not calculate a large quantity at a cheap quote and carry it unchanged into expensive fallback offers.
9. Keep double-entry accounting: goods acquisitions capitalize inventory; fees are separate income/expense transfers. Independently posted earnings reconcile to equity changes after any direct-to-equity transactions. Never define earnings as the equity delta.
10. Performance, determinism, actual-stock settlement, observability, and documentation are requirements, not later cleanup.

For a completed purchase from an alternative, the required distinction is:

| Whole bid delivered by that alternative | Incumbent could fulfill the whole bid | Preference outcome | Loyalty fee |
| --- | --- | --- | --- |
| Yes | Yes | Change if challenger qualifies | Paid |
| Yes | No | Change if challenger qualifies | None |
| No | Yes | Keep incumbent | Paid |
| No | No | Keep incumbent | None |

Research must make “whole relevant bid” and “qualifies” precise under endogenous quantities, different prices, cash constraints, split fills, no incumbent, and equal quotes. Fee frequency for split transactions, order boundaries, and the number of permitted company suppliers per ingredient are not settled by this table. State and test them explicitly; do not silently choose the interpretation most convenient for a shortcut.

Market intelligence, where used, is free in this phase. It may later become a paid service. Keep access and accounting separable, but do not introduce charges now. Do not silently change the existing fee formula, annual loyalty adaptation, production gate, sell-side gross-profit learning, or supply-access timing to make a candidate perform better. Test any proposed change as an identified treatment.

## Research the information and demand model

Compare these information regimes under otherwise matched conditions:

| Regime | Reference signal | Main question |
| --- | --- | --- |
| Company experience | Own incoming requests, fulfilled/unfulfilled quantities, quotes, sales, stock and cost history | Can local adaptation work without trapping firms whose shortages or poor visibility suppress observed demand? |
| Market intelligence | Product-level requested demand, average price, and fulfillment | Does broader information improve decisions or synchronize firms into unstable behavior? |
| Hybrid | Local observations with a justified market prior or correction | Does it improve cold starts and recovery without disguising a central allocation rule? |
| Existing behavior | Storage-target procurement and current market anchor | What improves over the actual baseline, and at what computational cost? |

Define “demand the company feels.” Sales are constrained observations, not automatically demand. Separate incoming requests, repeat attempts, offers observed, lost price-sensitive demand, stockouts, cash-limited intentions, and genuine backorders if any. Do not count hypothetical candidate evaluation as incoming orders. Analyze selection bias when a company is rarely sampled and the self-reinforcing loop from zero sales to zero estimated demand.

For intelligence, specify units, market identity, observation window, publication lag, ownership, and treatment of zero/no-history data. Compute a goods-price average and a fulfillment ratio from consistent quantities. Include both intermediate and final buyers of a product without double-counting their purchases or adding embodied ingredients as extra demand for that same product. Do not divide an already-unfulfilled-inclusive demand total by fulfillment again. Evaluate whether the three proposed aggregates identify the parameters being claimed; average price and a quantity at that price do not identify an entire demand curve.

Investigate price-sensitive derived demand and replenishment under complementary recipes. A candidate bounded family is `q(p) = L / (1 + (p/H)^eta)`, where `H` is the half-demand price. The family, elasticity, scale `L`, planning horizon, and calibration of `H` remain research choices. Specify whether price refers to an individual ingredient, a complete input bundle, or an all-in basket. Separate the curve from hard cash, stock, machinery, and storage constraints.

Inventory targets, coverage, own costs, output demand, and expected sales may help calibrate willingness to pay. They must not be presented as evidence that a forced refill quantity is price-sensitive demand. If a replenishment policy is used as an alternative, label and compare it honestly. Distinguish utility-based final demand from a manufacturer's derived input demand and expected operating return; a consumer-surplus interpretation does not automatically justify an industrial value function.

Previous suggestions to test or reject include `L = 2 * capacity`, `L = 2 * allocated market demand`, equal versus capacity-weighted market shares, half-price anchors from output margin budgets, `min(average input cost, affordable input budget)`, a `2 - fulfillment` multiplier, exponential inventory multipliers, a 30-tick window, and a 5% margin reference. None is an approved calibration. Examine local-experience versions as seriously as market-share versions. Do not guarantee equal earnings, allocate customers to fit capacity, or hide tunable assumptions inside supposedly derived equations.

Explain startup, new products, re-entry after shutdown, missing history, stale quotes, and a market with willing buyers but no sales. Label synthetic initialization separately from observed intelligence. Use completed data for adaptive decisions unless a clearly specified same-tick mechanism is justified; prevent accidental lookahead and circular self-inflation.

## Literature and modeling review

Research established economics, operations research, agent-based simulation, and game-economy practice. Use primary papers, author material, academic teaching sources, and first-party game-development accounts. Record each source's assumptions, relevant mechanism, limitations, and exact proposed use. Do not describe a game-specific formula as industry-standard merely because its terminology is familiar.

Starting sources, not a substitute for the executing AI's review:

- [Sargent, Verification and validation of simulation models](https://ics-websites.science.uu.nl/docs/vakken/msosi/VerificationValidationSargent.pdf): distinguish conceptual validity, implementation verification, data quality, and validity for the intended use.
- [Grimm et al., ODD protocol update](https://www.jasss.org/23/2/7.html): structure the model description, assumptions, scheduling, and reproducible evaluation.
- [Lee, Padmanabhan and Whang, Information Distortion in a Supply Chain](https://courses.ie.bilkent.edu.tr/ie460/wp-content/uploads/sites/12/2019/02/Lee-Padmanabhan-Whang-1997-MS.pdf): investigate upstream amplification from demand processing, order batching, rationing, and price changes.
- [Klemperer, Competition When Consumers Have Switching Costs](https://cepr.org/publications/dp704): examine incumbent protection and competitive effects. Compare its assumptions with this game's fee paid directly to the incumbent.
- [MIT inventory teaching material](https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/6c8fec8f99bcf7059b73b82e96d43901_MIT2_854F16_Inventory.pdf): compare base-stock, lot-sizing, and demand-risk models; do not automatically import their horizons or replenishment rules.
- [Lugosi, Markakis and Neu, On the Hardness of Inventory Management with Censored Demand Data](https://arxiv.org/abs/1710.05739): investigate what a firm can learn when it observes constrained sales rather than complete demand.
- [Dormans, Simulating Mechanics to Study Emergence in Games](https://ojs.aaai.org/index.php/AIIDE/article/download/12477/12336/16005): map resource flows and feedback, and test mechanics before integrating them into the game.

Extend this review to fixed transaction charges, consumer choice and search, complementary production inputs, lost-sales estimation, and exact discrete optimization. “Economically plausible” and “suitable for a playable simulated economy” are separate arguments; support both.

## Specify and prove the basket algorithm

Write a mathematical model and executable pseudocode before optimizing production code. Define the information set, decision horizon, objective, feasible actions, tie rules, integer conventions, and accounting postings for every buyer class. Include the option to buy nothing.

The algorithm must jointly handle:

- Price-dependent desired quantities; existing inputs and their book bases; recipe multiplicities; lot sizes; machinery footprints; finished/input allocations; total storage; shared cash; and operating-cost exposure.
- Ingredients that complement each other, inputs serving multiple routes, and any allowed incomplete buffer purchases. Do not inadvertently ban useful stocking by valuing only immediately producible output.
- Opportunity or replacement value versus historical COGS. No double-counting sunk inventory costs, conversion costs, or loyalty expenses.
- Candidate prices and live stock; full, partial, and split fulfillment; fixed fees; and preference updates per product.
- A noncircular definition of the bid used for incumbent availability. Show explicitly whether desired quantities are evaluated before cash, fees, and supplier-stock limits. Test whether buyers can inflate a bid or split orders to escape a fee.
- Correct demand at each fallback price. Average-cost ranking and a single remaining quantity are not automatically equivalent to optimizing the whole basket.

Bounded search is intentional. Exact optimization means the optimum over the specified sampled offers and allowed actions, not the globally best supplier, perfect foresight, or exact prediction of future sales. Define the numerical convention separately from the economic model.

Investigate the proposed fast paths rather than assuming they are valid: at most 36 pairs for two ingredients with six candidates and one supplier per ingredient; piecewise quantity optimization at stock/lot/fee boundaries; and separate fee-free/fee-bearing cost schedules for Distributor baskets. Prove the assumptions behind each. Multiple suppliers, multiple recipes, shared cash, or quantity-dependent fee eligibility can invalidate a decomposition. If an exact scalable solution is unavailable, demonstrate the limitation and present an explicit scope or algorithm choice rather than silently substituting a heuristic.

## Execution and performance design

Preserve a deterministic transactional interpretation: independent sampling and curve preparation may be batched; stock-dependent selection reads availability after earlier committed buyers and before this buyer changes anything. Solve a company's coupled basket before committing its debits. Recompute affected decisions if implementing reservations or conflicts; never clear independent orders against stale stock and repair overselling afterward without proving equivalent behavior.

Parallelize only work whose inventories, cash, and other mutable state are independent, or use a documented deterministic merge. Preserve and test buyer-order fairness. Do not change retail versus fresh-production access as an incidental optimization. Counter-based randomness keyed by seed, tick, buyer, product, and sampling role should keep treatments comparable where feasible.

Keep the reference implementation understandable. Optimize using typed arrays, compiled loops, structural caches, and justified vectorization. Measure compilation separately from warm execution; measure full ticks, not only the basket subroutine. Include recording and dashboard overhead. Benchmark at the real population and in adverse stock/fee cases, report memory and median/tail tick latency, and establish the acceptable regression budget before selecting the final implementation.

## Validation is a major workstream

Before tuning, define hypotheses, failure conditions, measurements, and acceptance criteria. Distinguish the following gates; passing one does not imply passing another.

| Gate | Required evidence |
| --- | --- |
| Model validity | Dimensional consistency, meaningful limiting cases, justified information and objectives, and explicit feedback-loop analysis. |
| Algorithm correctness | Independent exhaustive enumeration on small markets; exact objective and allocation comparison, including ties and all fee cases. |
| Implementation correctness | Reference/compiled agreement; accounting and goods reconciliation; deterministic checkpoint continuation; no stock, storage, or cash violations. |
| Economic behavior | Controlled experiments, multiple seeds, distributions, transient/recovery analysis, and evidence against specified failure modes. |
| Practical suitability | Full-population performance, interpretable decisions, usable player agency, and a reproducible rollout/rollback procedure. |

Pre-register numerical thresholds where measurable after baseline profiling, before evaluating finalists. Use exact invariants for quantities and a declared monetary/float tolerance where necessary; never choose a tolerance to hide a discrepancy. If there is no external real-economy ground truth, validate against the game's declared purpose and falsifiable behavioral patterns, not a claim of real-world predictive accuracy.

Required microcases include incumbent stock `Q-1`, `Q`, `Q+1`; cheap partial versus expensive full offers; fees greater than savings; waived fees with retained preference; paid fees without a switch; no incumbent; equal quotes; zero purchases; all stock empty; cash sufficient for goods but not fee; repeated ingredients; lot rounding; owned-stock imbalance; simultaneous buyers competing for the same stock; and any supported multi-route firm. Verify that candidate enumeration or draw order cannot manipulate demand or fees.

Test comparative statics under stated ceteris-paribus conditions. Desired quantity should respond correctly to price; discrete fees can cause justified jumps. Do not impose a false global monotonicity assertion when changing one price also changes the selected basket, information, or fee eligibility. Show the half-demand property if that family is selected, and prove that higher-priced fallback units are individually or jointly justified by the declared objective.

## Experimental program and measurements

1. Freeze and reproduce the actual baseline; add trustworthy recording before drawing conclusions. Record known defects separately from proposed behavioral changes.
2. Build small analytic fixtures and the independent brute-force oracle. Derive and reject candidates cheaply here.
3. Compare local, market, and hybrid information with otherwise identical procurement. Separately ablate supplier sampling, fee handling, inventory feedback, demand-curve calibration, and basket optimization. Diagnose interactions with the sell-side market anchor without bundling all changes into one unexplained treatment.
4. Use paired seeds and initial states, with stable random roles where possible. Separate calibration seeds/scenarios from held-out validation. Preserve failed runs. Justify replicate counts and uncertainty estimates; correlated ticks are not independent samples.
5. Run finalists at full population for complete generations, plus multiple-generation tests of drift and annual loyalty recalibration. A single profitable year or visually flat window is insufficient. Choose longer horizons when the observed dynamics require them.
6. Stress demand increases and collapses, supplier outages and recovery, price shocks, stockouts, small cash balances, large fees, no history, and asymmetric firms. Test the current invented subset and valid expanded-catalog scenarios with explicit manifests; do not silently assume that enabling all recipes preserves populations or demand routing.

Report time series and distributions by tier, complexity, product, route, and company. Separate C4 basic-plus-C3 and compound-plus-compound routes. Include:

- Requested and supplied units, sales, production, capacity/utilization, stock coverage, price/stock/cash losses, and inventory age or turnover.
- Realized prices versus initial references and current costs; revenue, COGS, gross/net margins, total and per-company net earnings per tick, cash/equity changes, and reconciliation residuals. Profit per unit alone is insufficient; compute period margins from summed accounts.
- Samples, incumbent retention, alternative partial fills, true preference changes, fee-bearing orders, fee receipts/expenses, and estimated forgone savings with the counterfactual clearly labeled.
- Parameter trajectories and information age; forecast error using only information available at the decision; amplification of order variability upstream; price trends, oscillations, concentration, and entry/recovery behavior.
- Decision traces sufficient to reconstruct selected baskets, quantities, fee eligibility, and preference outcomes. Aggregate normally and retain deterministic diagnostic samples to control recording overhead.

Explicitly try to falsify success: synchronized inventory cycles, demand collapse from censored sales, runaway reference prices, artificial guaranteed shares/margins, permanent lock-in, fee farming through partial fills, bid inflation to waive fees, stable prices caused by collapsed trade, inventory accumulation mistaken for earnings, excessive stocks maintained by unprofitable input purchases, and advantages caused only by buyer order.

Do not claim the final market is at a profit optimum because demand fell or prices stopped moving. Use controlled price perturbations and total-profit comparisons if making that claim. A result that rejects all new models and retains the baseline with targeted corrections is acceptable when supported by evidence.

## Required deliverables and completion

Produce:

1. **`docs/buying-behavior-research-report.md`** — final report with executive findings, current-system audit, source review, alternatives and rejection reasons, complete chosen equations and pseudocode, experiment manifest links, results with uncertainty, failures and limitations, performance, and adoption recommendation. Include worked examples for each buying tier and all four loyalty-table cases. Give every claim enough evidence to inspect.
2. **`docs/buying-behavior-model.md`** — concise implementation contract if a model is recommended: information provenance, timing, parameter meanings and defaults, basket/fee/preference semantics, numerical conventions, and accounting.
3. **`stats/buying-behavior-research/<experiment-id>/`** — configurations, seed lists, version/catalog identifiers, baseline provenance, raw and aggregated measurements, checkpoints where appropriate, and executable reproduction commands. Include code/diff identity and hardware/runtime details in each manifest.
4. Reviewed experimental code, independent oracle, regression/property tests, benchmark commands, schema/checkpoint implications, and the concrete deployment and rollback plan. Update affected production documentation only to reflect the selected, reviewed behavior; keep research hypotheses distinguishable from canon.

The report must end with a decision table: requirement, evidence, pass/fail/inconclusive, and remaining action. Name the preferred demand-information regime and explain why it outperforms the alternatives for this game. State what has actually been implemented and tested versus only analyzed. If recommending rollout, identify the exact configuration and code artifact for the user's final green light.

**Completion means an inspectable, reproducible result and an evidence-backed decision. A plausible equation, passing unit tests, a faster kernel, or a stable-looking dashboard alone is not completion.**
