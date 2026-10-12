# Fee incentives: sensitivity and model-choice evidence

Status: controlled small-case evidence, not an adopted purchasing policy or an economy-wide incidence estimate. The [joint continuation candidate](buying-behavior-v2-continuation-funding.md) exposed an incentive to accumulate otherwise unused inventory to lower future fee eligibility. This document tests its scope and one possible funding alternative. Accepted D1/D2 settlement rules are retained throughout.

## Compared models

- **Finance-aware continuation (`continuation`, v2):** current fee-free own-quote funding retains future actual switching income/expense, future funded quantities and actual future preferences in its objective.
- **Transfer-neutral funding (`continuation-transfer-neutral`, v1):** only inside the funded-intention counterfactual, omit all subsequent switching income and expense. Keep actual current cash, inventory, historical basis and prior transfer EMA; retain rent and real goods receipts. Actual selection and settlement still post every required fee and income, reserve real cash, and apply D1/D2 normally.

The second model is an explicit alternative belief/quantity rule. It does not forgive actual fees or create cash. It can change funded caps and therefore which baskets remain available to actual selection. It must not be described as behavior-preserving or as automatically equivalent to the full financial objective.

## Frozen microcase grid

`fee-boundary-spec.json` was saved before evaluation. The grid combines cash of $5/$6/$7/$8/$9, fees of $0/$1/$2/$3/$5, and A-input limits of 1/2/3/4: 100 cases per model. One A costs $1 now; B later costs $5 from its incumbent or $1 from an outsider. One A+B produces one $10 output with $0.25 conversion. There is capacity and demand for one output; leftover inputs have zero terminal value. Both models retain the same physical action space, with their declared funded-quantity limits.

| Observation | Finance-aware continuation | Transfer-neutral funding |
| --- | ---: | ---: |
| Cases evaluated | 100 | 100 |
| Cases buying more A than their matched zero-fee control | 14 | 0 |
| Sum of company returns over these 100 artificial cases | $680 | $655 |

The return sum is a grid diagnostic, not total game earnings or a population average. The 14 cases are not a 14% estimate of real-world prevalence: parameters were deliberately chosen near the cash threshold. In these cases the extra input has no productive use. It changes the next order's feasible incumbent-quote intention and thus the fee condition. Accounting still reconciles; the incentive concerns allocation and transfers, not money creation.

An independent calculation checks all 100 outcomes. After buying q A, the incumbent's input plus conversion is feasible iff `cash − q ≥ $5.25`. If feasible, the cheapest actual B cost is `min($5, $1 + fee)`; otherwise an affordable outside B costs $1 without a fee. Enumerating q and charging its actual cost produces the same choices/returns as the event-tree planner. The transfer-neutral candidate chooses one A throughout this grid.

## A useful buffer the alternative rejects

Start with $1 cash and one already-owned finished unit. A costs $1 now; B costs $1 later; A+B converts for $0.25 and produces another unit selling for $4. Closing demand can buy both the old and new units. Before B procurement the company may receive a $2 switching payment. Its existing finished inventory can support a legitimate incumbent availability check; the outside buyer purchases elsewhere, so the payment does not consume this inventory. The receipt is an explicitly supplied scenario, not guaranteed or advanced into current cash.

| Probability of receiving $2 before B procurement | Finance-aware initial A purchase | Finance-aware return | Transfer-neutral initial A purchase | Transfer-neutral return |
| --- | ---: | ---: | ---: | ---: |
| 0% | 0 | $4.0000 | 0 | $4.0000 |
| 25% | 0 | $4.5000 | 0 | $4.5000 |
| 50% | 1 | $5.3750 | 0 | $5.0000 |
| 75% | 1 | $6.5625 | 0 | $5.5000 |
| 100% | 1 | $7.7500 | 0 | $6.0000 |

At 50%, buying one A loses $1 if no transfer arrives, but allows profitable production if it does. Both branches use the same initial decision; only later procurement may react to the actual receipt. Ignoring that potential receipt in intentions excludes a useful buffer. The old finished unit is sold exactly once and is common to both models; the reported quantity/value difference concerns the additional output.

## Decision implication

Do not promote transfer-neutral funding simply because it eliminates the first incentive. It also sacrifices useful contingent production and is not a general solution under the full financial objective. Conversely, a profitable finance-aware strategy is not automatically a desirable gameplay outcome. The master plan has not specified whether fee-avoiding inventory accumulation is itself disqualifying or should be judged by resulting waste, trade, company health and stability.

Recommended research treatment: retain finance-aware optimization as the explicit economic benchmark, preserve this adverse case, and measure its economic effects. Keep the transfer-neutral rule as an ablation. Do not silently prohibit unmatched buffers, alter D1/D2, or claim either model has passed the strategic/economic adoption gates. A different anti-gaming requirement would need an explicit objective/quantity-model decision and fresh comparisons against these two counterexamples.

## Reproduction and boundaries

`20261012-fee-boundary-sensitivity-v2` contains the frozen specification, results, code identities and self-contained source. Run `python -m tools.buying_v2.fee_boundary_study --spec <specification.json> --output <fresh-directory>` from the archived package to reproduce it. `test_buying_v2_transfer_neutral.py` covers the grid's independent calculation, actual fee posting, no-fee equivalence and the useful contingent-buffer counterexample. Earlier exact oracle/ledger tests remain applicable.

The study does not establish how often the incentive occurs at actual company cash/price scales, its long-run effects, equilibrium welfare, or fairness. Those require the retained baseline, closed-loop candidates, stress scenarios and held-out campaigns specified by the master plan. No production default or live run changed.

The v2 study makes the tick boundary between early and later procurement explicit. All scored choices, returns and accounts match the preserved first study (`calendar-comparison.json`). Both archived versions reproduce exactly outside the repository directory. `fee-boundary-final-tests.log` passes 38 targeted tests; the four-test `fee-boundary-calendar-tests.log` additionally verifies the explicit-calendar version, including the independent 100-case grid.
