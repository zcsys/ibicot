# Experimental forecast contract

Status: implementation candidate; no adopted parameters or production use. `tools/buying_v2/forecast.py` supplies one-phase empirical payoff scenarios for the [industrial value model](buying-behavior-v2-value-model.md). This is a proposed information/estimation experiment, not a literature-derived optimal forecast or recovered latent-demand curve.

## Publication and permitted observations

A `PublishedChannel` freezes one seller-history channel for decision tick t and uses only rows with tick < t. It rejects a gap before the latest required completed observation. It never reads current-tick sales, current purchases, private future Distributor valuations, or realized future supply. Views are detached from the collector. History, model version and explicit parameter values determine the forecast; history reload preserves it exactly.

Local forecasts use the seller's own observations. Market forecasts use product totals and an equal share `1 / current eligible seller count`, with an offered-quote mean as the price reference. Hybrid forecasts mix the two probability distributions. A market total is never assigned in full to every company. Current market size must come from declared structural information, not future sales. Multiple lines remain separate seller identities; company planning must combine them without duplicating the same product market.

The inquiry-feedback candidate grants a seller access to its own sampled quote-check counts and publishes aggregated diagnostics after each tick. That is an explicit information assumption. The collector's ability to measure a lookup does not prove that a seller observes it in the approved economy. Version 2 also implements a transaction-only comparison, specified below. Neither feedback mode converts quote checks into actual orders or reliability failures, and neither is adopted.

## Missing and constrained observations

Under inquiry feedback, a row contributes an observation only when that seller was offered and at least one buyer discovered it. No discovery means missing information about interest, even though zero realized sales was measured. A discovered offer with no positive funded checks contributes measured zero, including when inventory was empty: zero intended quantity was not constrained by stock.

An informed row is marked stock-constrained if it had positive funded checks and either a short check occurred or closing stock is below one lot. This marker survives earlier stock constraints; it is not inferred from terminal world inventory. It is not a causal lost-sales estimate. In the market regime a product row is informed when any seller was informed, and constrained when any informed seller was constrained. Pooling those diagnostics can overstate an individual seller's opportunity; measure that failure mode.

## Explicit scenario equations

For a usable historical row j, let s_j be realized sales, p_j its posted quote (product total/mean quote for market), p the contemplated quote, N the current eligible seller count and U the fixed physical payoff cap for this decision.

- Local anchor: a_j = s_j. Market anchor: a_j = s_j / N.
- Price-adjusted anchor: q_j = min(U, a_j × (p_j / p)^e).
- Row weight: w_j = decay^(t − 1 − tick_j).
- Complete row: mass w_j on q_j.
- Constrained row: mass w_j × (1 − tail_weight) on q_j and mass w_j × tail_weight on `min(U, max(a_j, U) × (p_j / p)^e)`.

The tail is one finite sensitivity scenario which saturates the payoff cap at the historical quote. It is not an upper bound on latent demand at every counterfactual quote; the true tail is unidentified. In particular, clipping quantities before evaluating price changes is not equivalent to learning demand beyond inventory. One observation does not identify elasticity e. A fixed e, including zero, is an explicit assumption to test.

A cold-start prior places `cold_start_positive_weight` on an explicitly supplied quantity at an explicitly supplied reference quote, and the remaining mass on zero. Its positive quantity uses the same price adjustment and payoff cap. It does not expand automatically when the action's capacity increases. If usable observations exist, `prior_weight` is a pseudo-observation weight; zero removes it completely. If none exist, the explicit cold-start distribution is used. There is no hidden permanent demand floor. The prior's quote must not be replaced by the company's contemplated quote, which would make arbitrarily high quotes generate artificial prior revenue.

Normalize row/prior weights, then split fractional quantities between adjacent integers to preserve their expected value. Hybrid mixing occurs after each component distribution is normalized. All parameters are mandatory; no default set is shipped or adopted. Quote response, decay, tail weights, prior support/weight and hybrid weights require calibration sensitivity and fresh held-out validation.

## Valuing output

U must cover every feasible action in the decision and remain fixed while comparing baskets. It is not the quantity the optimizer chose to make. `expected_sales(x)` evaluates E[min(x,D)] for integral available finished stock x ≤ U. For existing finished stock F and q new units, incremental value is:

`p × (E[min(F + q, D)] − E[min(F, D)])`.

This prevents already-owned finished goods from being credited again as new output. The function is nonnegative, nondecreasing and discretely concave for a fixed forecast/quote. It does not make expected receipts available as current cash, replace the production margin gate or define net earnings. Multi-phase correlation, supply scenarios, horizon extension, fees, rent and conditional input continuation remain separate requirements. Independent line forecasts are not proof that independent scenario draws are economically appropriate.

## Verification and rollout boundary

Analytical tests cover independent local/market/hybrid values, no-exposure versus measured-zero rows, stock constraints, exact mixture weights, price shocks, cold-start sensitivity, lag/no-lookahead, decay denominators, shutdown/re-entry, old finished stock, invalid input and deterministic history reload. These tests establish the equations above, not forecast suitability. The implementation is currently a reference evaluator, not a population-scale purchasing path. Ordinary production and experimental replenishment decisions are unchanged.

## Historical calibration screen

The explicit specification is `stats/buying-implementation/forecast-calibration-spec.json`, written before scoring. It compares two illustrative tail weights (0 and 0.5) with otherwise identical parameters: decay 1, elasticity 1, no ongoing prior mass, a 50/50 local/market hybrid and an arbitrary one-item/$1 cold-start probe with positive probability 0.25. These are sensitivity fixtures, not selected defaults. Seed 137 was already used for calibration; this is not held-out evidence.

`20261012-forecast-calibration-137-v2` preserves source hashes, source copies, the specification and results. The first attempt failed a channel-selection check before scoring; its failed manifest is preserved separately. The successful screen selects up to two tick-1 offered sellers per product, using a declared independent sampling seed, and evaluates ticks 2–30. It conditions predictions on the actual phase-entry quote and stock. Empty-stock rows cannot test demand prediction and are excluded with counts. The sample is not weighted to represent the company population.

| Channel | Sampled sellers | Nonempty seller-phase observations | Empty-stock observations excluded | Actual items sold in scored observations | Local MAE, tail 0 | Local MAE, tail 0.5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Retail | 210 | 244 | 5,846 | 7,724 | 24.451 | 12.244 |
| Input C3 | 100 | 820 | 2,080 | 4,392,706 | 710.187 | 612.235 |
| Input C4 | 100 | 451 | 2,449 | 467,402 | 909.439 | 456.510 |

All six regime/profile combinations and their bias/RMSE/counts are in `result.json`. The larger tail scenario reduces absolute error in this screen, but it also raises C3 local overprediction bias from 311.254 to 412.768 items per scored observation. Most retail inventory observations are empty; 234 of the 244 nonempty scored retail observations carry a stock-constraint marker. Thus this screen cannot identify the missing demand tail or justify selecting 0.5. Saturating more of actual available stock can improve conditional-sales scores mechanically. It does not prove that manufacturing that much new stock would find buyers.

The strong phase differences, sparse nonempty coverage and remaining bias require controlled availability/quote probes and closed-loop policy comparisons. Do not tune to this table and call the same observations validation. Initial-state prior, local shutdown/re-entry, market synchronization and joint multi-line uncertainty remain substantive model questions.

## Transaction-only feedback comparison

`PublishedChannel(..., feedback="transactions")` uses only phase-offered status, posted quote, sold items and closing stock. It removes discovery, funded-check and short-check arrays from the publication view. The default `feedback="inquiries"` preserves the original experimental API and equations; it is not a production default. Every forecast now records version 2 and its feedback mode. Saved seller-history schema remains unchanged; existing forecast results retain their archived version and are not reinterpreted.

The collector verifies `opening stock = sold items + closing stock` for these fixed-stock, fixed-quote phases. The transaction-only observation rule is:

- Offered with opening stock at least one lot: include the realized sales observation, including zero sales when nobody purchases.
- Offered with less than one opening lot, or not offered: missing opportunity information. Do not interpret zero sales as measured zero demand; apply the same explicit prior rules as other missing observations.
- An included row with closing stock below one lot: mark stock-constrained and apply the declared tail sensitivity mixture.

This captures realized selling opportunities under the observed search/allocation process, not latent product demand. Without inquiry feedback, a rejected large request cannot be identified while a smaller lot remains in stock. Conversely, the model cannot distinguish an undiscovered stocked seller from one whose discovered quote attracted no purchase. These are information limitations, not events to reconstruct from unavailable counters. The market/hybrid candidates still assume lagged publication of product sales, quotes and availability; transaction-only does not mean those regimes receive local information only.

The payoff equations, local/market share rules, prior parameters, quote response, lag, cash timing and inventory valuation remain the same. `forecast_screen.py` accepts an explicit `feedbackModes` list and uses identical sampled seller IDs and scoring targets across modes. Target inquiry diagnostics remain evaluator-only fields; they are not forecast inputs in transaction-only mode. Retrospective scores are conditional on the preserved inventory policy and cannot establish closed-loop economic suitability.

## Paired historical feedback screen

The specification was frozen before evaluation in `20261012-forecast-feedback-proof/specification.json`. The run `20261012-forecast-feedback-screen-137` uses the same preserved seed-137/ticks-2–30 history, seller sample, payoff caps and two parameter profiles as the earlier calibration screen. Every one of the 18 inquiry-mode score rows and all sampled seller identities exactly reproduce the archived v1 results. The additional mode changes the information rule only.

Local mean absolute errors, in items per scored seller-phase (lower is better for this stock-conditional prediction task):

| Channel | Scored observations | Inquiry, tail 0 | Transactions, tail 0 | Inquiry, tail 0.5 | Transactions, tail 0.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| retail | 244 | 24.451 | 4.997 | 12.244 | 4.815 |
| input-C3 | 820 | 710.187 | 564.981 | 612.235 | 564.981 |
| input-C4 | 451 | 909.439 | 257.237 | 456.510 | 215.983 |

This comparison is descriptive. The information rule also changes which historical rows contribute; it is not an isolated estimate of the value of observing inquiries. The transaction-only local half-tail bias remains −3.983 items for retail, +462.544 for C3 and −211.235 for C4. Empty-stock targets remain excluded (5,846 retail, 2,080 C3 and 2,449 C4 observations); their demand cannot be validated from sales alone. No feedback mode or calibration is selected. Controlled stock/quote probes, closed-loop policy comparisons and fresh held-out validation remain required.

Seventeen targeted tests pass, including forecasts with all inquiry fields physically absent, stocked-zero versus empty-missing cases, wholesale depletion, lag/history continuation, paired target equality and invalid-mode rejection. Source copies, hashes, the frozen specification, results and an inquiry-parity proof are preserved. No world purchasing path consumes the new mode yet.

## Controlled stock and quote probes: candidate limitations

`forecast_probe.py` exercises the actual experimental Distributor clearing phase under declared fixture conditions. The frozen specification is `20261012-forecast-probe-proof/specification.json`; complete results, source archive/identity, runtime versions, per-treatment configurations and seller histories are in `20261012-forecast-probes-137-271-811`. Seeds 137, 271 and 811 are historical calibration seeds, not held-out seeds.

Each fixture has 500 active buyers, latent quantity 20, half-price 10, elasticity 1, and three suppliers of the same product. Training spans eight phases with quotes $10/$12/$14. The focal supplier receives zero, 100 or 10,000 opening items per training phase. Target phases replenish every supplier to 10,000 items and change only the focal quote to $5, $10 or $20. Each target uses the same seed/tick/buyer random roles. Forecasts are constructed before target clearing from completed training history only, with unchanged historical parameter profiles.

This is a controlled sales-phase fixture. Input inventories are cleared, seller storage is explicitly 50,000 spaces, and physical storage is validated at each phase entry. Stock is externally set for every probe phase, preferences reset and loyalty fees zero. No production, adaptive pricing, rent, cash-constrained industry or whole-economy trajectory is simulated. Recorded sales reconcile to stock removal, seller cash/revenue and original-basis COGS within each phase; initial fixture stock is not represented as endogenous production. Forecast inputs do not include private buyer valuations used by the test setup.

Selected seed-137 focal-supplier outcomes (items per target phase):

| Training stock | Target quote | Actual sales | Local anchor forecast | Local half-tail forecast |
| --- | ---: | ---: | ---: | ---: |
| Ample | $5 | 6,669 | 10,000 | 10,000 |
| Ample | $10 | 5,000 | 5,000 | 5,000 |
| Ample | $20 | 0 | 2,500 | 2,500 |
| Limited | $10 | 5,000 | 100 | 5,050 |
| Limited | $20 | 0 | 50 | 2,525 |

Those rows agree across both feedback modes. With empty-stock training, inquiry feedback predicts 0/5,000 at the $10 quote under anchor/half-tail profiles; transaction-only feedback uses its explicit cold-start prior and predicts 0.025 in both profiles. The arbitrary prior therefore determines re-entry in that case. The half-tail prediction of exactly 5,000 is a consequence of its cap/weight assumptions, not evidence that censored demand was identified.

All 27 target phases have identical actual outcomes across training-stock treatments for the same seed/quote. An independent calculation from cheapest-offer quantity and declared rounding roles matches actual sales; the seed-137 $5 total is 6,669, with seed-specific rounding retained in the complete report. Nineteen targeted tests pass, including reference/compiled phase parity, partial stock and frozen-publication checks. The initial test mistakenly omitted the market mean-quote adjustment when calculating the expected equal-share forecast; its failed log is preserved and the expectation is corrected explicitly.

These probes prevent promotion of the current empirical forecast merely because its historical MAE improved. Its smooth own-quote elasticity adjustment misses competitive displacement: a seller priced at $20 has zero sales while $12/$14 rivals have ample stock. Equal-share market allocation also misstates the successful cheapest seller's share. Future candidates need a justified competitive price/share response, a tested cold-start/re-entry treatment, and joint scenario generation before closed-loop industrial use. No parameter was tuned to these outcomes and no feedback regime is adopted.

## Explicit joint forecast assumptions

`tools/buying_v2/joint_forecast.py` now couples finite marginal forecasts for distinct owned products in one sales channel and decision tick. The caller must select either independent Cartesian outcomes or a common-quantile coupling (the same uniform quantile selects each product's outcome). Neither is a calibrated or adopted dependence model. Both preserve supplied marginal probabilities within floating-point precision; zero-probability atoms are omitted. Publication metadata rejects history from the decision tick or later.

Scenario count has an explicit caller budget. Independence can grow exponentially; exceeding the budget raises an error rather than silently sampling or truncating. Probability underflow and collapsed positive cumulative intervals also fail explicitly. The common-quantile construction uses the union of marginal cumulative boundaries, so its scenario count is at most one plus the sum of nonterminal marginal atoms.

`sales_scenarios` inserts one uncertain opening/settlement pair into an explicit shared event calendar for the small oracle. The caller must match forecast product order to installed-line order, align company quotes with contemplated forecast quotes, and supply terminal value tables. This helper is not a world adapter and does not enforce those identity/quote mappings. Future outcomes remain hidden until settlement; subsequent decisions can use observed receipts through the oracle's information history.

A three-line financing fixture illustrates why dependence matters. Two initially stocked products each sell one item at $2 with probability one half. A later third-product purchase costs $1 plus $0.50 conversion and then sells for $2. There is no opening cash. Under independence, at least one first sale occurs with probability 0.75; under common-quantile dependence it occurs with probability 0.50. Expected initial receipts are $2 in both cases, but expected total incremental cash is respectively $2.375 and $2.25. The optimizer buys the later input only after sufficient receipts. These are analytical assumptions, not measured company demand.

Twenty-four targeted joint-forecast, marginal-forecast and observed-history tests pass. Evidence is preserved in `stats/buying-implementation/20261012-joint-forecast/`, including source hashes/archive, explicit coupling tables and test logs. The initial 23-test run predates the additional positive-tail precision regression. This completes a small scenario-construction utility, not calibrated competitive forecasting, cross-time demand dependence, a scalable optimizer or production integration. The marginal competitive-displacement and cold-start failures above remain unresolved.

## Competitive peer-rank comparator

`competitive_forecast.py` implements a reference market-information candidate. For a contemplated own quote, it holds rivals at their latest published quotes and computes the signature `(offered supplier count, strictly cheaper rival count, equal-price rival count)`. It searches completed same-product books for seller observations with the same signature, chooses the nearest absolute quote in log space within an explicit distance bound, and applies the existing explicit elasticity adjustment. Equal-distance observations receive time-decay weights. All parameters and an existing fallback forecast are mandatory; there is no production default.

This assumes sellers are exchangeable conditional on rank and nearest quote. It does not infer buyer valuations, competitive price gaps, loyalty composition, discovery probabilities, or current rival stock. Rival quote persistence is an assumption, not current information. Tied quotes require a matching tied-rank observation; a new seller changes the required market size. Unsupported signatures or quote distances return the supplied fallback unchanged in quantities/probabilities and label its use. These assumptions prevent claiming calibrated market share.

Only fully informed product books with no recorded supply constraint are eligible. An exhausted rival can redirect purchases to otherwise unsuccessful sellers, so excluding only the focal seller's constrained observations would contaminate the rank comparison. The comparator therefore excludes the entire book when any offered seller lacks discovery, has a short check, is marked constrained, or has no opening stock. This conservative rule can leave sparse or zero support. Transaction-only publications are rejected because they lack the inquiry evidence required by this candidate. Product IDs, timing, quote and cap must agree with the fallback.

The retrospective 27-target comparison reuses preserved probe histories and actual outcomes from seeds 137/271/811; no new private buyer data enters prediction. Parameters are decay 1, elasticity 1 and maximum log-quote distance 2; fallback is the existing local empirical-anchor forecast. These are declared comparison assumptions, not estimated or adopted calibration. Outcomes were previously inspected, so this is not held-out validation.

| Historical training stock | Local baseline MAE | Peer-rank MAE | Target phases |
| --- | ---: | ---: | ---: |
| Empty | 3,890.89 | 3,890.89 | 9 |
| Limited | 3,807.56 | 3,807.56 | 9 |
| Ample | 1,942.44 | 1,109.11 | 9 |

MAE is absolute item error averaged over the nine seed/quote targets per row. With ample seed-137 training, a $20 quote now predicts zero instead of 2,500, matching actual zero sales against $12/$14 rivals. At $10 both forecasts predict 5,000. At $5 both still predict 10,000 against 6,669 actual. Empty and limited training lack eligible books and retain the fallback, including its re-entry failures. The improvement isolates one competitive-displacement failure; it does not resolve the value model's forecast gate.

Twenty-seven targeted competitive/marginal/joint tests pass in 0.042 seconds. They cover competitor displacement, retained extrapolation error, constrained rival exclusion, ties, bounded quote support, new sellers, no history, identity permutation, frozen publication and fallback metadata. The initial run had one overly strict exact-float expectation (5,000 versus 5,000.000000000004); the preserved failed log and corrected approximate assertion distinguish this numerical test issue from an economic change. `stats/buying-implementation/20261012-competitive-peer-forecast/` preserves evaluator, results, source archive/hashes, input hashes, and a byte-identical replay in the current environment. No standalone archived-environment replay is claimed.

This candidate remains reference-only and unfit for full industrial adoption. Next model work must address price-response identification, scarce-stock fallback and cold-start/re-entry, temporal dependence, and realistic heterogeneous supplier/loyalty behavior before scalable integration.

## Explicit temporal coupling and observed-information checks

`tools/buying_v2/temporal_forecast.py` now connects a sequence of supplied `JointForecast` distributions to the multi-period phase oracle. It introduces no fitted demand model or production default. Every period must share the same decision tick and installed-product order; each has explicit target tick offset, quote vector, channel and fixed payoff caps. Joint quantity vectors preserve within-period product dependence. All forecasts refer to information available at the common decision point, not forecasts reconstructed later using future data.

`couple_periods` requires either explicit independence or a supplied transition matrix for each adjacent pair of periods. For joint states `s_t`, the constructed probability is `p_0(s_0) × ∏ K_t(s_t,s_(t+1))`. Each row is a finite nonnegative probability distribution, and propagated probabilities must match every supplied period marginal to absolute tolerance `1e−12`. Small normalization rounding is allowed; inconsistent assumptions fail instead of replacing the supplied forecasts. Matrices use the input atom order. No historical estimator, persistence coefficient, cold-start kernel or censoring correction is invented by this adapter.

All positive paths are counted before allocation, and an explicit scenario budget is mandatory. The adapter does not merge different histories merely because their final states agree, sample paths, or truncate small outcomes. Probability underflow raises an error. This makes exponential scenario growth visible; it does not solve that growth or establish population suitability. Multiple phases may share a target tick, but offsets cannot decrease.

`sales_scenarios` inserts the hidden sales outcomes into common explicit calendar prefixes and unique book labels. Target offsets must equal the number of preceding `EndTick` events. Forecast quotes must match initial quotes plus explicit `SetQuotes` events; the adapter does not set prices automatically. It validates the temporal path distribution again and leaves ordinary calendar/state/accounting validation to the phase ledger. Current scopes use common predetermined quote/calendar paths. Action-dependent competitors, learned temporal kernels and forecasts that adapt to hypothetical future information remain separate work.

### Controlled temporal-risk counterexample

A one-line company starts with $100 cash and no inventory. One output requires two inputs, each costing $2 in period one and $3 in period two, plus $0.50 conversion. Its quote is $10. Each period's sales opportunity is independently specified as zero or one item with equal marginal probabilities. Fees and terminal inventory value are zero; the experiment varies only the supplied temporal relationship.

| Temporal assumption | Positive paths | Expected horizon cash-return objective |
| --- | ---: | ---: |
| Independent periods | 4 | $3.00 |
| Persistent: zero follows zero, one follows one | 2 | $2.25 |
| Alternating: one follows zero, zero follows one | 2 | $5.50 |

These are conditional planning results under synthetic supplied probabilities, not measured forecasts or posted net earnings. Identical marginal distributions do not determine a unique multi-period value. After a first-period sale, independent demand makes a new $6.50 batch unattractive against $5 expected receipts; persistence makes the same batch attractive against $10 conditional receipts. With no first sale, existing finished inventory can meet later demand without another input purchase.

A separate stockless-first-book case verifies information timing. The first hidden demand state produces zero observed sales on both persistent paths. The company therefore chooses the same second-period purchase on both paths; the adapter does not reveal the hidden state through labels or other event metadata. That fixture uses $2 second-period input quotes and returns $0.50 in expectation.

Thirty targeted tests pass across temporal/joint forecasts, observed history and existing forecasts. Coverage includes nonstationary marginal consistency, two-product joint states, zero atoms, underflow, scenario limits, malformed kernels, mixed decision ticks, immutable metadata, quote/calendar disagreement and altered path distributions. An initial fixture-construction error omitted event labels; its failed test log is retained, and corrected fixtures pass. Four complete inputs, forecast assumptions, policies, traces and final states are preserved in `stats/buying-implementation/20261012-temporal-forecast/`. Replay from its source archive outside repository imports is byte-identical. No live purchaser consumes this adapter, and no transition model is adopted; empirical calibration, closed-loop tests, held-out validation and the other model/solver/integration gates remain open.

## Temporal-history coverage audit: do not fit a population kernel from pooled counts

`temporal_history_audit.py` audits existing seller-history evidence before any temporal kernel is fitted. The specification was saved before evaluation. The source history is `20261012-industrial-seller-history-fullpop-137/seller-history-000030.npz`, observed ticks 1–30, with decision tick 31. Nine existing controlled retail histories cover ticks 1–8 and use decision tick 9. These are previously examined calibration/startup records, not held-out validation or a new simulation.

The universe is seller columns offered at least once before the decision tick within retained history. Future observations, newly appended seller columns and future-only channels cannot change past results. Candidate pairs are consecutive retained rows for each such seller. Exclusions are mutually exclusive in this order: nonconsecutive tick, either row unoffered, either opening stock below one lot, either recorded short check or closing stock below one lot, then changed own quote. The selected subset has unchanged quotes and no *recorded* stock constraint; this does not identify uncensored or stationary latent demand. Product IDs and input hashes remain attached to every report.

Full-population startup-window results:

| Sales channel | Candidate seller-phase pairs | Selected pairs | Selected / candidates | Seller columns with both zero- and positive-sales origin states in selected pairs |
| --- | ---: | ---: | ---: | ---: |
| Input C3 | 1,133,784 | 4,407 | 0.389% | 90 |
| Input C4 | 1,133,784 | 107,260 | 9.460% | 7 |
| Retail | 1,680,840 | 1,569 | 0.093% | 154 |
| T0 wholesale | 1,160 | 1,109 | 95.603% | 0 |

The mixed-origin sellers occur in only five of 50 input-C3 product markets, two of 50 input-C4 markets, seven of 105 retail markets and none of four T0 markets. These are seller-column counts, not an inference about unique companies or full supported ownership. Product-level denominators and exclusions reconcile to channel totals.

Interpretation needs care. Input C4's 107,260 selected pairs contain 107,238 zero→zero pairs, 15 zero→positive, seven positive→zero and no positive→positive pairs; only 996 selected pairs have discoveries at both endpoints. T0's selected pairs are all positive→positive, so its zero-origin conditional probability is unavailable, not zero. Retail has only eight selected pairs with exactly equal opening stocks. Quote changes excluded no additional pairs *after the earlier exclusions*; this does not establish that every recorded quote was unchanged. Opening-stock and discovery subsets are reported separately rather than used to manufacture a larger clean sample.

The controlled ample-stock probes provide 21 selected pairs per seed (three seller columns × seven intervals). Empty/limited focal-stock treatments provide 14, all from the other two sellers after exclusions. None has a seller observed in both binary origin states. Such histories may still inform conditional positive-quantity behavior, but they do not supply both rows of a zero/positive transition model. Pooling sellers with different persistent sales propensities can also produce apparent persistence without within-seller temporal evidence. The reported pooled correlation and conditional frequencies are descriptive diagnostics, never adopted kernels.

Consequently, this audit does not select independence, persistence or any estimated temporal model. Next calibration work needs declared state definitions, coverage of those states within sellers, explicit treatment of stock/quote/competitor selection, and controlled or subsequently held-out evidence. Unobserved transition rows require an explicit prior or an unavailable result; they must not be filled with arbitrary zeros or interpreted as measured certainty. This remains separate from the correctness of the temporal scenario adapter.

Twelve targeted history/audit tests pass, covering disjoint exclusions, per-product reconciliation, undefined ratios, zero/one-row histories, invalid history metadata and future rows/columns/channels. All ten source histories produce thirteen channel reports; their complete outputs replay byte-identically using archived source outside repository imports. `stats/buying-implementation/20261012-temporal-history-audit/` preserves the frozen specification, input hashes, full product reports, tests, source/catalog/runtime manifest, analysis script and verification. No source recording, live configuration or production policy was changed.

## Bounded quote-response comparator with explicit identification requirements

`bounded_response_forecast.py` adds a reference-only candidate for the large price-cut error. It retains the prior peer-rank assumptions and fully informed, unconstrained-book filter, but fits a bounded response from multiple distinct positive-sales quotes rather than applying an inverse-price adjustment to one quote. Every forecast receives an explicit existing fallback; no current world purchaser or production default changes.

At observed quote `p_j`, compute the time-weighted mean sales `y_j` and total observation weight `w_j`. Fit `1/y_j = a + b p_j` by weighted, centered, scaled least squares. Require `a > 0` and `b >= 0`, giving the proposed mean curve `m(p) = 1/(a + b p)` with finite zero-price limit `1/a`. Quantities are items per seller sales phase; `a` has inverse-item units and `b` inverse-item-per-dollar-quote units. This functional family is an explicit modeling hypothesis, not a demand curve identified from one quote or adopted for heterogeneous industrial buyers.

For each eligible observation `(p_i, y_i)`, transport its multiplicative residual: `y_i × m(p)/m(p_i)`. Retain declared time-decay weights and use the existing adjacent-integer mixture and fixed payoff cap. This residual transport is an unvalidated uncertainty assumption. Its weighted mean need not equal the nominal fitted curve exactly, and cap truncation can change it further; `fit.meanAtQuote` describes the fitted curve, while `Forecast.mean` describes the resulting bounded distribution. Historical costs, production gates and buying decisions are not changed by fitting.

At least two distinct positive-sales quotes are required. Observations must share the contemplated peer-rank signature, with rivals held at their last published quotes. Mixed zero-sales support, unavailable eligible books, inadmissible coefficients, declared quote-range violations, decay-weight underflow and nonfinite fitted responses trigger the supplied fallback. Interpolation is allowed within observed quote range; extrapolation is limited by the explicit maximum log distance outside that range. The candidate does not fill empty-stock history with invented demand, guarantee seller shares or infer private buyer valuations.

### Controlled quote-variation screen

The specification in `20261012-bounded-response/specification.json` was saved before running this screen. It uses historical seeds 137, 271 and 811, 500 homogeneous buyers, three suppliers, nine training ticks cycling own quotes $4/$8/$11, and rivals fixed at $20/$24. Target own quotes are $3/$6/$9/$13/$18/$26. Stock treatments are ample (10,000), limited (100) and empty (0); all target phases supply 10,000 items per seller. Preferences reset and fees are zero, as in the earlier controlled retail probe. No production or adaptive pricing is simulated. The known homogeneous buyer response family motivated this comparator, so this is calibration/implementation evidence, not held-out model validation.

Forecasts are computed from the tick-nine publication before target outcomes. They receive no private buyer quantity, valuation or elasticity arrays; those remain fixture inputs. Declared comparison parameters are time decay 1 and maximum log extrapolation 2. The fallback is the existing peer-rank forecast (elasticity 1, maximum log-quote distance 2), backed by the earlier local empirical-anchor profile.

| Training stock | Target phases | Peer-rank MAE, items | Bounded-response MAE, items | Bounded-model fallback count |
| --- | ---: | ---: | ---: | ---: |
| Ample | 18 | 716.221 | 10.583 | 3 |
| Limited | 18 | 4,434.623 | 4,434.623 | 18 |
| Empty | 18 | 4,524.722 | 4,524.722 | 18 |

MAE is mean absolute focal-seller item error across the stated seed/quote targets. The three ample-stock fallbacks are the $26 displaced-seller cases: the preceding rank comparator predicts zero correctly. At seed 137/$3, actual sales are 7,682, the peer baseline predicts 9,535.56, and the fitted candidate predicts 7,697.94. This addresses a controlled multi-quote response failure. Limited/empty histories retain the old errors, and no re-entry or scarce-stock forecasting success is claimed. Real markets may provide insufficient eligible quote variation, especially under the conservative whole-book filter.

Thirty targeted bounded/competitive/marginal/joint forecast tests pass, including an independently specified saturating curve, interpolation/extrapolation, insufficient price variation, constrained books, wrong-signed fit, quote scales, frozen publication and fallback identity. All 54 target outputs replay byte-identically from archived source outside repository imports. Actual targets are identical across training-stock treatments for each seed/quote; 15 seed-137 training/target phases match the reference and compiled clearing paths, whose internal stock/cash/revenue/COGS checks pass. The artifact directory preserves source/catalog/runtime identity, specification, configurations, nine seller histories, forecasts, outcomes, tests and verification scripts.

This remains unsuitable for production adoption by itself. Heterogeneous response-family misspecification, realistic discovery and loyalty, unavailable market books, cold-start/re-entry, industrial buyers, temporal calibration and closed-loop behavior remain unresolved. Improved error under a correctly specified controlled response family does not close the master plan's forecast gate.

## Response-family stress: the bounded curve is not a universal replacement

`forecast_response_stress.py` tests the preceding forecaster without changing its source or parameters. The specification was frozen before evaluation in `20261012-response-family-stress/specification.json`. It retains the previous nine training quotes, six target quotes, three historical seeds and ample-stock setup. This isolates response-family assumptions; it does not add loyalty, limited discovery, production, adaptive pricing or scarce inventory. Private buyer profiles are supplied only to the fixture and independent outcome calculation, never to either forecast.

Each buyer's declared fixture quantity is `Q / (1 + (p/H)^eta)`, with the existing deterministic rounding role. Profiles contain 500 buyers in total:

| Profile | Buyer composition |
| --- | --- |
| Homogeneous control | 500 × Q=20, H=$10, eta=1 |
| Split valuations | 250 × Q=20, H=$2, eta=1; 250 × Q=20, H=$50, eta=1 |
| Correlated size/value | 250 × Q=5, H=$5, eta=1; 250 × Q=35, H=$20, eta=1 |
| Steeper response | 500 × Q=20, H=$10, eta=2 |

Results are across 18 target phases per profile. MAE is mean absolute focal-seller item error. WAPE is summed absolute error divided by summed actual focal-seller items across those phases; zero-sale targets are retained in the error numerator.

| Profile | Peer-rank MAE | Bounded-response MAE | Peer WAPE | Bounded WAPE |
| --- | ---: | ---: | ---: | ---: |
| Homogeneous control | 716.221 | 10.583 | 15.829% | 0.234% |
| Split valuations | 867.379 | 99.955 | 19.711% | 2.271% |
| Correlated size/value | 920.631 | 13.872 | 16.887% | 0.254% |
| Steeper response | 367.359 | 400.313 | 7.829% | 8.531% |

The homogeneous control exactly reproduces the previous screen's predictions, diagnostics and outcomes, and the forecaster source hash is unchanged. The fitted curve still improves these two heterogeneous examples, but is worse than the older model on the steeper response. For eta=2, inverse mean quantity is quadratic in quote, whereas this candidate fits a line; its good performance under eta=1 cannot establish general suitability. A mixture of buyer valuation scales also need not follow a single fitted hyperbola. These results are calibration counterexamples, not estimates of population prevalence or a completed held-out validation gate.

All 180 training/target phases match an independent calculation from declared buyer curves and the existing rounding roles; actual phase assertions also reconcile inventory, cash, revenue and COGS. Seven targeted stress/bounded/probe tests pass, including reference/compiled parity for small multi-profile fixtures, active-population slices and invalid profile/cap rejection. All 72 target rows replay byte-identically using archived source outside repository imports. The artifact directory preserves specification, full forecasts/outcomes, source/catalog/runtime manifest, tests and checks.

The evidence rules out promoting the fitted curve uniformly on the strength of its original homogeneous result. Next candidate work should check predictive adequacy at withheld observed quote levels or compare broader response families using only published training data, with future target outcomes excluded from selection. Cold-start/re-entry, stock scarcity, heterogeneous supplier/loyalty behavior, industrial forecasting, temporal calibration and closed-loop validation remain separately unresolved. No model choice or production policy changed during this stress screen.


## Published quote validation for response selection

`validated_response_forecast.py` now compares the existing peer path and bounded curve using only published training observations. It withholds every eligible book at one distinct quote, including repeated observations at that quote, and refits both candidates on the remaining books. The caller's publication is unchanged. At least three distinct eligible positive-sales quotes are required; unsupported fits, changed rank signatures, incomplete folds or weight underflow retain the peer path with an explicit reason.

For model M, score `L_M = sum_i w_i * abs(prediction_M_without_quote_i - min(payoff_cap, sold_i)) / sum_i w_i`, where `w_i = decay ** (decision_tick - 1 - tick_i)`. Select the bounded curve only when its loss is lower by more than `1e-12 * max(1, L_peer, L_bounded)`; otherwise retain peer. The selected full-history distribution is returned unchanged. The payoff cap is fixed across contemplated actions and influences the comparison: a test deliberately demonstrates that the same steeper-response history selects peer at cap 10,000 but bounded at cap 20,000. This is a comparison of capped item predictions, not a universal classifier of private demand curves or a validation of uncertainty calibration.

An explicit positive integer `max_quote_folds` limits cross-validation work. More quote levels cause fallback rather than sampling or silent truncation. This bounds the extra fold count, not initial history scans or total population execution cost. The current experiment uses 16; it is not a production default.

The existing four-profile screen was rerun with selection enabled before each target outcome. Across 18 targets per profile, selected MAE is 10.583 items for homogeneous control, 99.955 for split valuations, 13.872 for correlated size/value, and 367.359 for steeper response. The first three profiles select bounded at 15 targets and peer at the three displaced-seller targets; the steeper profile retains peer at all 18. All 72 original raw predictions, diagnostics and outcomes remain unchanged. These profiles had already been inspected before this selector was designed: these results are retrospective calibration evidence, not independent held-out validation.

Fifteen targeted selector, bounded, competitive and stress tests pass. The initial test incorrectly expected cap-independent selection; its failure is preserved as `tests-cap-expectation.log`, and the corrected test explicitly checks both caps. Complete results replay byte-identically from archived source outside repository imports. `stats/buying-implementation/20261012-validated-response/` contains the specification, source/catalog/runtime manifest, result, replay, test logs and verification. Production defaults and live behavior remain unchanged. Scarcity/re-entry, industrial and temporal forecasts, closed-loop validation and population performance remain open.


## Full-population quote-support audit

`quote_support_audit.py` measures necessary structural support for the quote-validation selector at each latest offered seller's latest quote. It groups historical offers by product and price rank, applying the actual inquiry publication's whole-book eligibility rules. Book exclusions are disjoint: changed offered-seller count, uninformed offer, recorded constraint, then empty opening stock. Seller classifications are also disjoint: no eligible observations, any nonpositive matching sales, fewer than three distinct matching quotes, more quotes than the declared fold budget, then structurally supported. This does not fit either model or test coefficient admissibility, omitted-fold support, extrapolation, time decay or accuracy. Structural support is necessary, not sufficient.

At decision tick 31 in preserved full-population seed-137 startup history (ticks 1–30), the counts are:

| Channel | Latest offered seller columns | No eligible observations | Nonpositive matching sales | Insufficient quotes | Structurally supported |
| --- | ---: | ---: | ---: | ---: | ---: |
| Input C3 | 39,096 | 38,592 | 360 | 144 | 0 |
| Input C4 | 39,096 | 39,096 | 0 | 0 | 0 |
| Retail | 57,960 | 57,960 | 0 | 0 | 0 |
| T0 wholesale | 40 | 0 | 0 | 40 | 0 |

No seller exceeds the explicit 16-fold budget. Denominators are seller columns within each channel, not unique companies across channels. All product-level counts reconcile. The nine older constant-quote probes also lack structural support: ample-stock probes have two sellers with nonpositive matching sales and one with insufficient quotes; empty/limited probes have no eligible books. They are distinct from the newer deliberately varying-quote calibration fixtures.

This startup window rules out relying on this selector as the general population forecast at those observed quotes. It does not prove that later histories or different contemplated quotes never provide support. In particular, improving a curve fit cannot repair absent whole-book coverage. Next forecast work must address incomplete discovery and stock-censored observations explicitly, while retaining stock/competition effects and avoiding interpretation of scarce realized sales as unconstrained demand. Simply relaxing the filter would remove an identification safeguard without supplying a replacement model.

Eight targeted audit/selector tests pass, covering tied quotes, repeated quote levels, zero sales, constrained books, book-exclusion denominators, future data, missing phases and invalid budgets. Initial fixture errors were corrected to respect the history format; the exclusion-fixture failure is preserved. Ten saved histories produce thirteen channel reports, replayed byte-identically from archived source outside repository imports. `stats/buying-implementation/20261012-quote-support/` preserves input hashes, specification, source manifest, results, replay and tests. No forecast parameters, saved histories or production behavior changed.


## Identical censored histories can conceal different replenished demand

`forecast_identification_probe.py` constructs two controlled populations whose complete retained seller histories are identical. Both contain 500 buyers with response `Q / (1 + p/H)`; one uses Q=20/H=$10, the other Q=40/H=$10/3. The evaluator knows these private profiles; the forecast receives only the published history. Every training phase has one item at each of three sellers, focal quotes $4/$8/$11 repeated three times, and rival quotes $20/$24. Preferences reset and fees are zero. The worlds therefore record positive sales, rather than relying solely on an empty-history example.

For each historical seed 137, 271 and 811, all retained fields match exactly: seller identities, products, owners, lots, ticks, offered masks, quotes, sales, closing stocks and discovery/funded/short counts. Each seller sells nine items over nine ticks, receives 4,500 discoveries and records 4,500 short checks. The current selector produces identical distributions and diagnostics on the paired publications, as any deterministic function of those same inputs must. Target predictions are frozen before measuring replenished outcomes.

After replenishing each seller to 20,000 items, seed-137 focal sales are:

| Focal quote | Q=20/H=10 sales | Q=40/H=10/3 sales | Minimum possible worst absolute error of a common point prediction |
| --- | ---: | ---: | ---: |
| $3 | 7,682 | 10,529 | 1,423.5 |
| $6 | 6,239 | 7,130 | 445.5 |
| $9 | 5,253 | 5,408 | 77.5 |
| $13 | 4,355 | 4,079 | 138.0 |
| $18 | 3,573 | 3,119 | 227.0 |

For two outcomes y1 and y2, every common prediction m satisfies `max(abs(m-y1), abs(m-y2)) >= abs(y1-y2)/2`. This is an elementary identification limit for this pair and information set, not an estimated population error rate or calibrated prediction interval. The curves cross: a blanket quantity multiplier does not resolve the discrepancy. Even changing training prices is insufficient while all observations remain stock constrained. Additional signals, informative stocked observations, or explicit prior assumptions are required. Short-check counts alone cannot quantify missing demand or justify a chosen tail probability.

This adds an acceptance condition for an incomplete-observation model: it must label its replenishment extrapolation as assumed when histories are indistinguishable, retain explicit sensitivity to that assumption, and avoid presenting a fitted point value as identified demand. It does not authorize changes to discovery, prices, replenishment, consumer curves or private-information access in production. The existing local tail-mixture remains an explicitly assumed comparator, not a calibrated solution; a new uncertainty distribution has not been inferred from these counts.

Six targeted probe/stress tests pass, including paired reference/compiled equality and the zero-stock boundary. All 30 target phases match an independent curve-and-rounding calculation; the shared phase harness reconciles goods, cash, revenue and COGS. The full 15-pair result replays byte-identically from archived source outside repository imports. `stats/buying-implementation/20261012-forecast-identification/` preserves specifications, per-seed shared-history hashes, results, source/catalog/runtime identity, tests and verification. The first large fixture failed storage validation before target measurement; its insufficient-storage specification/log are preserved, and the final fixture increases storage to hold the declared ample inventory. This changes fixture capacity only, not demand parameters or forecast tuning.


## Purchasing sensitivity to explicit forecast alternatives

`forecast_sensitivity.compare` connects alternative forecast distributions to the existing single-closing-decision optimizer. Each named model describes the same seller, products, information date, fixed payoff caps and catalog. Cash, stock, quotes, fees, funded demand and terminal values are held fixed. Every model is solved under an explicit per-model search budget; failure propagates rather than returning an approximate answer. A separate model-count budget limits the diagnostic workload.

The adapter cross-evaluates the union of selected optimal allocations and no purchase under every model using the reference procurement/production evaluator. Physical execution must be identical across models, and each compiled optimum must agree with reference valuation. For candidate allocation a and model m, report incremental planning return V_m(a) and regret `max(0, V_m(a*_m) - V_m(a))`, allowing only the existing numerical comparison tolerance. Existing finished-stock payoff is reported separately through a second return field that adds its model-dependent baseline; it is not counted twice in incremental return. These planning returns are not posted earnings.

This is sensitivity analysis, not a new risk preference. No probability over models is inferred; the listed worst regret is over the supplied alternatives only. The candidate union is not the complete feasible allocation set, so no minimax-regret optimum is claimed. Identical selected allocations establish invariance only across the supplied alternatives. Multi-phase recourse, endogenous funding and production integration remain outside this closing-decision adapter.

The preserved fixture starts with one recorded stock-constrained sale at quote $4. Input cost is $1, conversion $0.50, maximum output four, and terminal values zero. The existing local forecast places its explicit tail probability on the fixed cap; weights 0, 0.25, 0.5, 0.75 and 1 are sensitivity settings, not estimated probabilities. With $10 cash and no finished stock, weights 0/0.25 select one input, while 0.5/0.75/1 select four. Under the endpoint demand-one model, buying four returns −$2 instead of the optimal $2.50; regret is $4.50. Under demand-four, buying one returns $2.50 instead of $10; regret is $7.50. The model uncertainty therefore changes an economically consequential decision.

With only $1 cash, all alternatives choose no purchase because conversion cannot be funded. With two existing finished items, low-tail alternatives choose no purchase and high-tail alternatives choose four inputs; the adapter preserves the differing existing-stock baseline. No test treats zero purchases as universally desirable or adopts either tail endpoint.

Nine targeted sensitivity/allocation tests pass. They cover independently calculated cross-returns/regrets, existing stock, cash/conversion limits, shared-input multiple lines, mismatched model identities/caps and the earlier 120 randomized allocation-oracle comparisons. Three complete sensitivity reports replay byte-identically from archived source outside repository imports. `stats/buying-implementation/20261012-forecast-sensitivity/` preserves specification, runner, results, tests, source/catalog/runtime manifest and verification. This provides a decision-level diagnostic for the earlier identification counterexample; it does not calibrate the missing tail or close the forecast adoption gate.
