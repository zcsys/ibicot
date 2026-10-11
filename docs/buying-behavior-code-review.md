# Experimental code review record

This is a self-review plus independently structured enumeration and replay,
not an external reviewer endorsement. Production files are unchanged. No claim
of general purchasing optimality follows from restricted-scope test agreement.

The final combined `test_buying_research`, `test_buying_world` and
`test_buying_fallback` run passed 20 tests in 32.054 seconds. The complete
[log](../stats/buying-behavior-research/final-research-regression-tests.log)
preserves the environment's nonfatal SciPy/NumPy version warning. No additional
production behavior was changed to obtain this result.

## Verified design boundaries

- The population loop reads live inventory/cash and commits one coupled company
  basket before advancing to the next company. Product markets are independent
  within the supported single-route basket; different buyers remain sequential.
- Six offers per input are not a proof of a 36-case solution. The scalar unit-lot
  solver also partitions output quantities at owned-stock, supplier-stock and
  incumbent/alternative fee crossings. Within each interval the minimum goods
  cost is affine and expected return is concave. Integer neighbors of the
  stationary point, clipped to physical and cash bounds, suffice. Wholesale lots
  use constant-purchase-vector intervals instead. Neither proof covers arbitrary
  multiple-route firms or nonlinear contracts.
- Historical input basis affects COGS and the unchanged production gate. It is
  not charged again by the prospective purchasing objective. Conversion exposure
  is subtracted once from the objective and separately reserved in the cash
  feasibility check; reservation does not post an expense.
- Fee eligibility uses a fixed canonical bid and the incumbent's stock before
  this buyer's settlement. Alternative selection, the payment and preference
  update are distinct operations. Split retail orders pay at most one fee.
- The reference settlement test runs the Python bodies of the compiled population
  functions with compiled numerical helpers. The independent retail/industry
  oracles import no optimized solver. These are complementary checks, not three
  independent economic models.
- The campaign's cash, goods, equity and minimum-stock checks run every tick.
  Independent whole-world storage validation runs every 360 ticks and at the
  end, with additional per-step validation in the four-tick world fixture.
  Solvers enforce basket storage bounds directly; the recording gate does not
  independently rescan all storage after every transaction. Initial cash shocks
  occur before opening accounts are captured and need no balancing entry.

## Findings and fixes

1. The original equal-price retail fast path used a strictly positive marginal
   gain even where the general solver treated that gain as a monetary tie.
   Ambiguous cases now use the general comparator, with a regression case at
   `price + 1e-10`.
2. Small worlds with fewer than 4,033 T2 companies lacked any C3 suppliers under
   the current allocation order. They remain mechanical smoke tests only; the
   reference/checkpoint test now includes 4,200 firms, and economic comparisons
   use the full population.
3. Full-population prototype 01 was much too slow. Array-allocation removal and
   the proved lower-envelope solver improved runtime substantially. Performance
   gates have not been relaxed. Earlier slow runs remain archived.
4. Product-level research net earnings initially allocated each T0 company's
   total profit equally across its installations. The independent legacy audit
   found all 28,800 affected T0 product/tick entries. Correct product profit is
   line revenue minus line COGS plus allocated company fees minus expenses/rent.
   The recorder is fixed; analysis reconstructs that identity from preserved raw
   accounts. Tier totals and company earnings were correct. After correction,
   885,600 product/tick records match the preserved 7,200-tick replay exactly
   across revenue, COGS, units, fees, rent and net earnings.
5. Industry request counters initially omitted unsuccessful fills. They now
   record submitted units before the positive-purchase branch. Retry units are
   separate; only the first submitted intention contributes to local learning.
6. Initial diagnostic traces were too narrow to reconstruct decisions. They now
   include the sampled live offers, canonical bid, preferences, inputs, storage,
   cash, objective parameters, selected quantities, fee and preference outcome.
   Market seed 137's first-year archive replayed 24 refinery, 708 manufacturer
   and 125 Distributor decisions successfully without reading the final world.
7. At the singular rounding draw `u=0`, the first marginal value was capped but
   the canonical demand still used the uncapped endpoint. A fixture at a $1e9
   quote exposed one canonical item versus zero valued items. Both now use the
   same `max(u,1e-12)` numerical convention. Inverting the bijective RNG proves
   there are no activated zero draws in any executed/planned study window:
   seeds 137/271 through 14,400 and held-out seeds through 1,080. Thus the repair
   cannot change those recorded economic trajectories. The counterexample and
   endpoint audit are retained; the seed-1597/2027 audit includes activated zero
   draws at later, untested ticks, which must not be silently generalized away.

## Open scope and model concerns

The user's fallback clarification exposes an industrial action-set failure:
R1 permits only one supplier per ingredient. In the derived-demand witness with
quantities 10 and 8 and stocks `[2,20]`, R1 buys `[0,8]` for $71.89, while the
confirmed fallback and independent split oracle buy `[2,6]` for $68.63. Both
support eight outputs. `industrial-fallback-scope-counterexample.json` records
the exact values and `industrial_fallback_case.py` reproduces them. This is a
failed requirement, not an approved restriction justified by solver speed.

The user-confirmed fallback quantity rule is already present in both production
retail paths. Dedicated tests verify A=2, B=6 and 500 fee-free oracle markets.
This does not validate every demand metric. The terminal-quote counterexample
in `fallback-demand-ledger-audit.json` buys `[2,3,0]` at quote demands `[10,8,5]`,
yet baseline retains `LastQ=8` and stock-unmet=3 after seeing the final quote with
zero remaining need. R1 uses its first funded quote-stage intention instead.
Loss denominators must be labeled by their reference protocol; cross-policy
comparisons of actual transactions and accounts do not have this ambiguity.

Canonical-bid qualification is not full fulfillment of a cheaper-quote intended
purchase. In `canonical-versus-intended-bid.json`, the canonical quantity is two,
the intended cheap-quote quantity is twenty, and delivery of three changes
preference with a $2 fee. The independent oracle agrees. The brief deliberately
requires this boundary to be made precise; R1 meets its own frozen-bid convention
but fails an interpretation requiring the entire funded cheap-quote intention.
That unresolved design choice must not be hidden behind passing loyalty-table
unit tests.

The procurement objective and retained production gate can disagree about
feasibility. With one owned input at $100 basis, a missing complement at $1,
conversion $0.75 and output quote $10, R1 buys the complement for $8.085 modeled
incremental return. The actual compiled historical-cost gate permits zero output
at $101.75 unit cost. `production-gate-counterexample.json` verifies both the
independent basket optimum and gate outcome. This is a conceptual constraint
omission in future planning, not an accounting residual or solver mismatch.

The repeated split-fill fixture falsifies a universal no-fee-farming claim:
two one-unit challengers jointly fill a canonical bid of two, neither replaces
the incumbent, and an available incumbent collects $2 per order without selling
goods. Ten independently checked orders preserve that state. This follows the
implemented loyalty/split contract; it is a design limitation rather than a
posting error. `fee-split-lock-in-counterexample.json` records the bounded-demand
parameters and seeded draws, with fixed offers explicitly labeled.

The stable-ID equal-price tie rule has a demonstrated identity bias even with
uniform distinct sampling. With 100 sellers and five alternatives, the lowest
20 IDs receive 68.07% of first requests versus 0.0206% for the highest 20 in an
ample-stock/no-incumbent fixture. The exact distribution and three sampled
replications are saved in `equal-quote-tie-audit.json`. This is a model/fairness
concern in the declared tie rule, not a mismatch between solver and oracle.
Changing it would require an identified behavior treatment.

Request construction is itself part of the model. The recorded first intention
comes from one funded quote-stage plan with supplier stocks relaxed, while its
fee eligibility already incorporates incumbent availability. It can address an
empty seller. This deliberately specified message is recorded once rather than
counting every candidate evaluation, but it remains an endogenous protocol
choice that feeds both forecasts and the existing scarcity price response.
It must not be described as directly observed exogenous or uncensored demand.

R1's `t2ReplacementCost` diagnostic records current input basis plus conversion;
baseline purchasing writes its weighted owned-input/missing-quote prospective
estimate. Repository search found no decision consumer of that diagnostic.
Both production gates use actual input basis, and the differential production
fixture tests that behavior. The research records `t2UnitCost`, not replacement
cost, in its cost comparisons. Restoring the diagnostic's production semantics
is nevertheless necessary before integration; it must not silently acquire a
different meaning in existing projections or future consumers.

The full engine explicitly rejects companies with multiple production lines.
The exact small multi-route oracle is not a scalable production implementation.
There are no internal-transfer semantics in the prototype. Pure unmatched buffer
purchases are excluded by its complete-kit action space. The industrial expected
return uses the firm's posted output quote rather than an estimated realized
future price. Market demand shares are forecasts and never allocate customers;
the equal-share assumption can still synchronize orders. These are substantive
model/coverage limitations, not issues an implementation test can dismiss.

The user's live run, checkpoint schema, default purchasing and sell-side learning
have not been replaced. The final evidence table rejects R1. A later replacement
would require its own validated artifact and the user's green light; approval
cannot be inferred from this review record.

## Final evidence review, 2026-10-12

The 93-run archive/coverage audit passes for 82 economic runs, one measurement
replay and ten isolated timing profiles. The final study and diagnostics contain
exactly the same 82 economic identities. The measurement replay matches all 23
common product fields over 1,771,200 product/tick records, 1,280 company-array
comparisons and both complete checkpoints exactly. Added normalized counters
supplement only that proven trajectory. Three early calibration runs still
lack historical price-contact counters; no snapshot fills that gap.

All five matched timing pairs fail the unchanged relative median/p95 budgets;
absolute median and memory budgets pass. Mature repetitions are exactly equal
in their economic state, recording and R1 sidecar. The report distinguishes
first-tick/JIT-inclusive cost, warm simulation, recording, publication and
encoding; browser rendering is unmeasured.

The stored preference-change event includes assignments from no incumbent.
The final read-only `preference_event_audit.py` verifies reviewed source hashes,
empty initialized preferences, unchanged configuration, fixed Distributor
products, no sparse history and no interventions before using final occupied
slots to count first assignments. Settlement only changes these preferences to
nonnegative supplier IDs and never clears them. The exact aggregate difference
therefore counts changes between suppliers for the three ordinary controls;
the method explicitly rejects other scenarios and source versions. Historical
events are not rewritten or assigned invented timestamps.

The final self-review conclusion is to retain the independently verified code
as an experimental artifact and reject production integration. Solver and
accounting correctness do not resolve industrial splits, incomplete buffers,
multiple-route ownership, production-gate mismatch, incentive exploits, trade
collapse or fairness. All supporting result identities and deliverable hashes
are recorded in the [delivery manifest](../stats/buying-behavior-research/delivery-manifest.json).
