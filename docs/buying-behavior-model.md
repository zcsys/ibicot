# Experimental purchasing contract (candidate R1)

Status: **rejected experimental candidate**, retained as a research specification,
not canon or an approved rollout. Initial
equations were frozen before implementation and candidate results; subsequent
clarifications and counterexamples are recorded here and in the protocol/review.
Recommendations and tested scope belong in the final report. Production
purchasing remains unchanged.

## Confirmed fallback quantity rule (user instruction, 2026-10-11)

At each successive supplier's price p, recompute **total** desired quantity
`q(p)`, then request `max(0, q(p) - units_already_bought)`. Buy the lesser of
that remaining request and the supplier's available stock. For A with demand
10 and stock 2, then B with demand 8 and adequate stock, the allocation is
A=2, B=6, total=8. If B can supply only 1 and C's price implies demand 5,
C supplies `5 - (2+1) = 2`; total=5. Never carry A's unfilled 8 unchanged to B,
and never apply B's demand curve only to the remaining fraction of the original
order. Use one rounding draw across quotes.

The reference specification is [fallback.py](../tools/buying_research/fallback.py).
This rule is confirmed independently of R1's value function and canonical-bid
convention below. At ascending prices it agrees with the fee-free R1 allocation
and the existing T3 fallback loop. Loyalty selection and preference qualification
are separate: the user has not yet specified whether B's complete *remaining*
fill alone qualifies it as the next incumbent. R1's historical treatment retains
the incumbent on every split order; that is recorded behavior, not a newly
accepted user decision. Industry still requires a coherent complementary basket;
this same-product quantity example does not establish an independent willingness
to buy each ingredient regardless of its complements or shared cash.
It does establish that a same-product request may use partial stock from one
supplier and continue with another. R1's industrial one-supplier-per-ingredient
restriction does not implement that behavior. The
[industrial counterexample](../tools/buying_research/industrial_fallback_case.py)
uses derived quantities 10 and 8: the confirmed split buys `[2,6]` for $68.63,
while R1 buys `[0,8]` for $71.89. Both support eight outputs. An independent
split-allocation enumeration confirms the cheaper basket. This is an explicit
failed requirement for historical R1, not an approved production restriction.

## Information and timing

One tick is the decision period. Gaia supplies the environment; T0 extracts and
does not procure raw inputs. T1 buys raw elements. T2 buys refined and intermediate
products. T3 buys one assigned final product. Machinery ownership is an input to
feasibility, not a new investment decision. Preserve retail access to opening T2
stock and C3-before-C4 production. Read stock after earlier buyers have committed.
Prepare forecasts from completed ticks only, never from candidate evaluations.

An order boundary is `(tick, buyer company, input market)` for companies, and
`(tick, Distributor, product)` for T3. Each supplier offer represents a production
line with a stable company owner and product ID. An eligible seller must offer the
product at a finite positive quote. Zero-stock sellers remain observable.
Sample five **distinct non-incumbent** sellers without replacement, plus a valid
incumbent. Include all alternatives if fewer than five exist. Sampling uses a
separate deterministic role keyed by seed, tick, buyer and product; sort sampled
IDs before optimization. Sorting or enumerating offers cannot alter demand.

R1 submits one funded first intention using the sampled quotes and fixed payable
fees, before accepting the finite-stock response. It then selects the feasible
basket. This is a declared request protocol, not a count of every hypothetical
candidate evaluation. Unique requested quantity is at least the realized fill;
the first intended recipient receives the request observation. Actual fallback
units are recorded separately as retries. There are no persistent backorders.
This is a modeled quote-stage message protocol: the first proposal ignores
supplier stock when choosing its funded quantities, while fee eligibility already
uses incumbent availability. A seller with no stock can therefore receive the
first message. It is not an empirical estimate of every seller's latent customer
opportunity. Changing that communication protocol changes the local signal even
if the eventual merchandise allocation is unchanged; the retained sell-side
learner can also react to these unfilled messages. Treat that interaction as a
modeling limitation, not an innocuous instrumentation detail.

The primary local estimator uses these first incoming requests. It can omit
fallback sales received by a seller; the explicit local-sales-floor alternative
uses `max(first requests, actual sales)`, not their sum. Actual sales alone are a
separate censored-signal treatment. These choices must not be conflated with a
claim to have observed every buyer's unconstrained demand.
The sales floor can credit the first recipient's unfilled request and a different
seller's fallback sale in separate company forecasts. Their sum therefore need
not equal unique product demand. This is a local opportunity-learning policy,
not an additive market-demand estimator; the unique market ledger is unchanged.
Market intelligence is a product's unique buyer intentions, supplied quantities
and merchandise value, published next tick. Final and intermediate buyers enter
the same product ledger; embodied ingredients do not. Price is summed goods value
divided by sold units. Fulfillment is supplied units divided by unique requested
units, undefined at zero requests. Empty/no-sales price history is missing,
not zero or an observed quote average. Never divide requested demand by
fulfillment a second time. These aggregates cannot identify a demand curve.

Research compares local, equal-share market and hybrid forecasts under identical
procurement. Equal and capacity-weighted shares coincide for the current
identical-capacity lines of a product; heterogeneous capacities are a distinct
model. A share is an uncertain forecast, not assigned customers or guaranteed
sales. Default EMA window is 30 (`alpha=2/31`), horizon three ticks, synthetic
cold-start daily mean half nominal capacity, and hybrid market weight 0.5. These
are calibration assumptions, frozen before held-out results. Window is an EMA
decay parameter, not a rectangular 30-tick sample; mean observation age is 14.5
ticks, plus the one-tick decision lag. Quotes in an order are current posted
quotes, which may reflect earlier agents' permitted same-tick production/pricing.
Market information is free. R1 forecasts from requested quantities; realized
goods price and fulfillment remain diagnostics, not identified curve parameters.

## Industry objective and allowed actions

For route r, current finished stock is F_r items, posted sale price P_r dollars per
item, conversion c_r dollars per item, capacity K_r items/tick. Given forecast
mu_r > 0 of requested output over H ticks, the research return function is

`V_r(y) = P_r * mu_r * exp(-F_r/mu_r) * (1-exp(-y/mu_r)) - d_r*y`,

where `d_r = c_r + max(0, forecast line overhead)/K_r`. At mu=0, set the
sales term to zero. This is an explicit exponential demand-survival assumption:
incremental expected goods revenue less future conversion/overhead. It is **not**
consumer utility, historical COGS, a claim to have estimated willingness to pay,
or a promise of the posted selling price. H and the distribution require tests.
Historical input cost remains in accounting and the unchanged production gate;
it is sunk for the procurement objective and is not subtracted again.
The prototype does not impose the retained historical-cost production gate as
a constraint inside this future-output planning problem. The executable gate
counterexample now demonstrates that a positive-return input purchase can be
followed by zero permitted production at those same quotes. This is an unresolved
conceptual mismatch. Respecting the existing gate would require an additional
planning constraint; changing the gate itself is a separate behavior decision.

Choose integer planned outputs `0 <= y_r <= floor(H*K_r)` with input requirement
`A_m(y)=sum_r a_mr*y_r`. For owned inputs I_m and purchase lot l_m,
`x_m(y)=l_m*ceil(max(0,A_m(y)-I_m)/l_m)`. Choose at most one sampled supplier per
ingredient for this industry candidate. All inputs in the company's basket share
cash and storage. Purchases must respect each input slot, total goods storage
(machinery already deducted), and live supplier stock. Reserve cash for the
planned conversion exposure in addition to goods and fees. No credit is added.

Maximize `sum_r V_r(y_r) - sum_m(goods payment + fee)` over the feasible actions,
including buying nothing and optimizing output from owned inputs. Only incremental
score above the best no-purchase plan can justify spending. The value of existing
finished goods cancels. Fixed overhead is a forecast per-unit exposure here; this
does not change actual rent settlement. Default single-line firms are the first
compiled target. The general small reference covers shared inputs/multiple routes.

This action set intentionally permits future complete kits, including quantities
beyond immediate capacity, and lot-rounding residuals. It does not buy a purely
unmatched buffer for unspecified future complements. That restriction needs a
separate positive-terminal-value buffer comparison and outage tests; it must not
be silently generalized to all industrial stocking. Full production suitability
also requires a scalable multi-route solution and explicit internal transfers.

## Canonical bid, fixed fee and preference

Freeze a canonical bid before cash, fees and supplier-stock caps. For industry,
solve the same economic output problem using each incumbent's own current quote;
where absent, use the median sampled quote. Ignore supplier stock, fees and cash,
retain physical capacity/slot bounds. Its per-input x_m is Q_m. For T3, Q is the
price-dependent integer demand at the incumbent quote, or median sampled quote
if none. This bid is an explicit order-protocol choice, distinct from the actual
chosen quantity, and identical across candidate evaluations. Report both.

For Q>0, a valid incumbent is available iff its opening stock for this buyer is
at least Q. If any positive purchase is made outside an available incumbent, pay
it **one** fixed fee per order boundary. Keep the existing fee formula
`M * reference unit cost * (1+clamp(reliability,0,1))` and annual adaptation.
No purchase means no fee; an unavailable/absent incumbent receives no fee.
Industry uses one seller per ingredient. T3 can split across sampled sellers,
with the same single fee even if the incumbent also sells part of the basket.

A single alternative establishes/replaces preference only when Q>0 and it alone
delivers at least Q for that product. A split order retains the old preference.
Qualification follows the specified objective and numerical tie order. A
small actual fill therefore can owe a fee while retaining preference. Q is never
recomputed after a fill. Buyers cannot submit an arbitrary Q or make additional
same-product suborders within the tick. Test the remaining economic discontinuity:
price/forecast changes can make Q exceed incumbent stock and waive the fee.
An unaffordable canonical bid may waive a fee; explicitly measure this sensitivity
rather than asserting strategic immunity. Zero Q never creates a preference.

Qualification is relative to this canonical bid, not necessarily the buyer's
larger funded intention at a cheaper quote. The verified bounded-demand example
with incumbent price $30 and alternative price $1 has Q=2 but a 20-unit
quote-stage intention; an alternative delivering three units replaces the
incumbent while filling only 15% of that intention. This is an explicit and
unapproved interpretation of “whole relevant bid.” If the requirement means
the whole cheaper-quote intention, R1 fails that interpretation. The oracle
verifies the implemented rule; it cannot settle the intended semantics.

## Final demand and exact retail baskets

Retain the existing `q(p)=L/(1+(p/Half)^eta)` family and existing L, Half, eta
initialization. With a single deterministic rounding draw u per buyer/tick,
use `u_eff=max(u,1e-12)` consistently in canonical stochastic rounding and
marginal values `v_k=Half*(L/(k-1+u_eff)-1)^(1/eta)` for feasible positive k.
Values beyond L are zero. The common finite endpoint convention avoids the
singularity at a zero hash draw; for positive RNG draws it is exactly the
unmodified draw. `U(q)=sum(k=1..q,v_k)`.
Choose integer allocations maximizing `U(sum x_s)-sum(p_s*x_s)-fee`, subject to
live stock and any stated budget. T3 payments are external inflows in the current
economy; there is no persistent T3 cash balance to invent. Include q=0.

Enumerate total quantity up to ceil(L), comparing (a) incumbent-only cost and
(b) minimum goods cost with at least one outside unit, plus the single fixed fee
when applicable. For (b), take cheapest units in quote/ID order; if all would be
incumbent units, replace one with the cheapest feasible outside unit. This is
exact because the fee is constant across all allocations containing outside
units and goods costs are linear. Evaluate each total, so expensive fallback
units must justify their marginal value or the basket's joint gain after fees.
This proof fails with per-seller fees, nonlinear prices, endogenous fee eligibility
or multiple products sharing cash. Those are different models.

## Executable algorithm outline and numerical rules

```python
offers = distinct_sample(seed, tick, buyer, product, role) + valid_incumbent
snapshot = read_current_stock_cash_inventory(offers, buyer)
forecast = completed_information_at_tick_minus_one
bid = solve_without_stock_cash_or_fees(forecast, canonical_quotes, physical_bounds)
fee = baseline_fee if incumbent_stock >= bid > 0 else 0
best = no_purchase_action
for allowed_integer_plan in complete_feasible_action_space:
    cost, allocation = exact_minimum_goods_cost(allowed_integer_plan, offers, fee)
    if storage_and_shared_cash_and_conversion_reserve_fit(allocation):
        best = deterministic_better(best, value(allowed_integer_plan)-cost, allocation)
commit_whole_basket(best)  # no intervening buyer; no partial debit/repair
post_inventory_basis_sales_COGS_and_separate_fee_transfers(best)
update_preferences_from_frozen_bid_and_actual_deliveries(best)
record_one_intention_and_actual_requests_fills_losses(best)
```

Optimize only after comparing to an independently structured exhaustive oracle.
For a fixed industry output plan, independent product inventories and one seller
per input make the cheapest payable supplier per input sufficient. Shared cash
then checks their sum. Enumerate all plans to obtain the exact allowed optimum.
Six-by-six pairs alone do not solve the quantities or multiple routes. Wholesale
lots create steps: include both sides of every input-lot boundary and the
integer neighbors of stationary points within intervals before claiming a
piecewise shortcut. Do not invoke concavity across a fee/lot discontinuity.

Units are whole items and whole lots. Floats are binary64 without fast-math.
Canonical order of summation is stable input ID then stable seller ID. Ties use
the preregistered monetary tolerance. Retail then prefers lower expenditure,
more incumbent units and lexicographically more units at lower stable seller IDs.
Industry prefers lower expenditure, lower planned output, and for a fixed input
quantity an equally priced incumbent before lower stable seller IDs. Supplier
count is not an additional implemented tie rule. Do not spend on zero-gain ties.
Supply access remains sequential; rotate industry buyer order as baseline,
and test T3 priority separately. Counter-based sampling is independent of the
number of candidate evaluations.

## Measurement semantics

`orders` counts completed positive ingredient purchases for T1/T2, and positive
whole baskets for T3. `samples` includes observed incumbents as well as sampled
alternatives, including decisions that buy nothing. `alternativePartial` counts
outside supplier fills below the canonical bid, so a split basket may contribute
more than one. `retained` counts completed orders that keep an existing incumbent;
it does not mean every purchased unit came from that incumbent. Preference
changes and fee-bearing orders are independently counted events.
`preferenceChanges` counts a change in the stored preference, including an
initial assignment from no incumbent. It is not exclusively a switch between
two previously selected suppliers; the aggregate counter does not separately
identify those first assignments.
For the three intervention-free, fixed-market 1–1,080 controls, the separate
[preference audit](../stats/buying-behavior-research/final-preference-event-audit.json)
decomposes the counter exactly. Preferences start empty and are never cleared;
the number of occupied final slots therefore equals first assignments. Subtract
it from the recorded counter to obtain changes between selected suppliers.
This endpoint identity does not reconstruct event times or cover arbitrary
product reassignment, resets or ownership transitions.

`cashLimitedUnits` sums positive per-ingredient differences between the
cash-unconstrained and funded quote-stage plans, holding the same quotes and
payable fees. The historical field name `unfundedUnits` means the **total units
in that cash-unconstrained plan**, not units lost for lack of cash. T3 has no
persistent cash constraint and records zero cash-limited units. Canonical bids
are a separate pre-fee/pre-cash quantity. These three totals are not additive.

`feeWaivedUnavailable` is a decision-stage flag for an incumbent whose stock is
below the canonical bid, including decisions without a completed purchase; it is
not the number of completed waived-fee orders. `forgoneGoodsSavings` compares
the same realized quantity with cheaper sampled merchandise at the recorded
availability, disregarding fees. It is a partial counterfactual, not foregone
future profit or an estimate of a re-equilibrated fee-free economy. Retail
price/fee loss and stock loss use the declared intention protocol. Industrial
unfilled quantities can combine complement shortages and basket adjustments,
so they are not isolated own-input causal shortage estimates.

Turnover is period units sold divided by mean finished inventory, and coverage
is mean finished inventory divided by mean units sold per tick. Physical item
age is not recorded. Undefined zero-denominator ratios remain unavailable.
The recorder's T0 `complexity=0` metadata is a raw-tier label, not zero storage
space or zero embodied material; every raw item counts as one raw-equivalent
unit in conservation. Refined/manufactured recipe complexity supplies their
respective raw-equivalent multipliers.

The recorder's `companies` field allocates each company's unit weight equally
across its installed lines. It sums to the actual tier company count. In the
tested single-product T1/T2 groups it is also the actual product-company count.
For a **T0 raw-product row**, it is a fractional company-equivalent denominator,
not a count of unique owners. Any `earningsPerCompanyTick` value in that row is
therefore per allocated company equivalent, not the owner's full portfolio
earnings. The analyzer labels this meaning explicitly. T0 company distributions
use the actual 20 portfolios; raw-product net accounts allocate company-wide
fees/rent rather than inventing unrecorded product-specific fee receipts.

`recordedUnitCostMean` averages the engine's stored production unit costs across
active lines and observations. For T1/T2 each stored value is the last successful
batch cost (or synthetic initial cost), so it can be stale. It is neither current
input replacement cost nor period COGS per unit sold. The original 23-field
baseline recording lacks this history; keep it missing. The checkpoint cost
extractor separately computes a recipe bill from current mean posted input quotes
plus conversion, explicitly ignoring stocks, sampling, fees, rent and owned
inventory. That calculated snapshot comparator must not be called an executable
procurement cost or silently substituted for historical COGS.

## Accounting, persistence and deployment boundary

Goods purchase: buyer cash decreases and inventory acquisition basis increases
by merchandise payment; seller cash/revenue increase and inventory/COGS move at
seller historical basis. Fee: buyer cash/expense decrease and incumbent
cash/income increase separately. T3 goods and fee payments enter from outside.
Production capitalizes conversion and historical inputs. Net earnings are posted
revenue minus COGS plus fees received minus fees paid minus actual rent. Reconcile
to equity change independently. No balancing entry or demand-driven transfer.

Research information, bid telemetry and random-role version require separate
persisted state and an explicit schema. Existing production v8 checkpoints cannot
silently synthesize observed histories. Cold-start metadata must say synthetic.
Rollout and rollback must use matched engine/state versions, complete source
identity and a retained pre-adoption checkpoint. Neither schema nor active defaults
has been changed by this specification.
