# Purchasing contract decisions

Date: 2026-10-12. Status: D1 and D2 accepted by the user on 2026-10-12; D3 remains a proposed mechanics experiment. This implements the decision-pack step of the [master plan](buying-behavior-implementation-plan.md); it specifies accepted fee and preference rules; live activation still requires completed validation.

## D1 Which delivery qualifies a new incumbent

The confirmed quantity example is A demand 10, A delivery 2, B demand 8, B delivery 6. Total purchases are eight in either interpretation below.

| Case with old incumbent I | Completing the remaining request qualifies | One supplier must supply the whole demand at its quote |
| --- | --- | --- |
| A supplies 2, B supplies the remaining 6 | B becomes incumbent | I remains incumbent |
| A supplies 2, B supplies 1, C supplies the remaining 2 at demand 5 | C becomes incumbent | I remains incumbent |
| A supplies only 2 against demand 10; no completion | I remains incumbent | I remains incumbent |
| A supplies all 8 against demand 8 | A becomes incumbent | A becomes incumbent |
| No purchase | I remains incumbent | I remains incumbent |

Accepted decision: keep the old preference unless one supplier alone supplies the whole demand at its own quote. The user explicitly chose this over terminal-remainder qualification. Thus A=2/B=6 retains the old incumbent. Repeated split purchases can retain an incumbent indefinitely; preserve this consequence in tests and diagnostics rather than silently changing qualification to eliminate it. No universal no-lock-in claim is made.

With no existing incumbent, apply the same qualification rule to first assignment. Equal quotes follow a deterministic declared tie rule, not candidate enumeration order. Cash/storage/lot feasibility defines the funded demand before testing delivery completion; this funding rule must not let an unaffordable fee count as a completed purchase. Preference changes only at the end of the product order.

## D2 Define the fee once for the product order

Accepted decision: freeze the original incumbent and its live stock at the beginning of this buyer's product order. Derive a feasible intended quantity at the incumbent's quote using the buyer's pre-order information, cash, storage, and lots, without capping by supplier stock. If the incumbent can supply that positive quantity, charge the existing loyalty formula once when any outside supplier actually sells goods. Otherwise waive it. Pay the original incumbent, even if preference changes after completion.

For multiple recipes, the funded bid must come from the coupled company plan; independent per-ingredient budgets cannot each spend the company's whole cash balance. A separate feasibility check reserves all payable fees and operating exposure. No extra fee is due for retries or additional suppliers within the same product order. The order boundary is buyer, input/final product, and purchasing phase within a tick; all eligible lines share that order. Reopening the same phase cannot manufacture a second order.

| Opening incumbent stock versus frozen funded bid Q | Outside delivery | Preference | Fee |
| --- | --- | --- | --- |
| At least Q | Qualifies under D1 | Changes | One existing-formula fee |
| Less than Q | Qualifies under D1 | Changes | Zero |
| At least Q | Positive but does not qualify | Retained | One existing-formula fee |
| Less than Q | Positive but does not qualify | Retained | Zero |
| Any | Zero | Retained | Zero |

This includes orders where the incumbent sells first and a challenger later sells a remainder. The first seller alone must not determine whether a fee is payable. Freeze availability before this order's own purchases, but after earlier buyers' committed transactions. Do not freeze it at tick opening.

Alternative: charge per outside supplier transaction. This makes splitting mechanically multiply the charge and creates additional order-boundary incentives. It is not recommended. Another alternative is a bid based on a challenger's cheap quote; the existing research shows how a larger cheap-quote intention can change fee eligibility without changing the incumbent's ability to meet demand at its own price.

The recommended reference avoids discretionary bid inflation but still requires adversarial testing of endogenous industrial forecasts, cash truncation, manipulated quotes, and small terminal fills. Its resemblance to R1's incumbent-quote reference does not adopt R1's preference threshold, industrial action space, or value equation.

## D3 Mechanics-only supplier objective

Proposed experiment: retain the existing bounded replenishment target, maximize the feasible target fulfillment, then minimize actual goods spend plus payable fees among allocations with that same fulfillment. Include partial suppliers and splits. Respect complementary inputs and shared company resources; report whether the objective favors isolated buffers over executable batches. Compare against a batch-first alternative in small fixtures before selecting a scalable rule.

This is a procurement-cost/replenishment policy, not a derived industrial willingness-to-pay curve. It can still buy expensive stock simply to fill a target. That limitation is reserved for the later industrial model, and must not be disguised by an arbitrary margin cap. The reference solver should demonstrate the choices explicitly before any production port.

## Executable evidence and boundaries

`tools/buying_v2/contract_cases.py` evaluates both D1 alternatives and the accepted D2 settlement boundary. `tests/py/test_buying_contract.py` supplies independent expected outcomes for split completion, first assignment, partial-only orders, Q−1/Q/Q+1 availability, no purchase, and repeated outside deliveries.

These fixtures verify the rule outcomes; user decisions above establish which rules are accepted. The fixtures alone do not derive a funded bid, implement a basket optimizer, or establish strategic robustness. The existing retail integration test continues to verify A=2/B=6 against both actual production engines and posted goods/money/COGS.

The user chose whole-demand qualification and the one-fee product-order boundary in response to the implementation questions. These choices now govern dependent selection, fee, and preference behavior. The terminal-remainder alternative remains in the executable fixtures solely as a comparison, never the default.
