# Joint funded intentions for continuation planning

Status: experimental v2 contract and small-instance implementation. It extends the [phase oracle](buying-behavior-v2-phase-oracle.md), does not change production purchasing, and is not an adopted calibration or proof of strategic robustness. Accepted D1/D2 settlement rules remain unchanged.

## Question answered at each decision

The new `funding='continuation'` mode derives quantities inside the same conditional event tree used for actual selection. Its objective remains closing cash less opening cash, adjusted for the change in rent arrears, plus explicit terminal inventory values. Actual production, existing finished goods, future receipt timing, input complements, cash, storage, lot sizes and observed information remain binding.

For each discovered offer for material m:

1. Fix material m to that offer's quote and lot size. No other supplier of m participates in this hypothetical.
2. Retain **all discovered quotes for other materials**. Give every hypothetical offer enough stock to cover the remaining input slots; shared slots and storage still constrain total purchases.
3. Remove current-order switching fees and hold current incumbent identities fixed through this hypothetical decision. Keep actual future fees, future preference updates, rent and their financial consequences.
4. Optimize the complete conditional continuation plan, with one common current action across indistinguishable future scenarios. Record the selected whole-lot quantity of m and the complete jointly funded vector supporting it.
5. Use that quantity as the offer's funded intention. The original incumbent's own-quote quantity supplies D2's frozen availability reference. Actual supplier selection then uses live stock, all payable fees and the funded fallback caps; actual D1 preferences update normally.

Holding hypothetical preferences fixed is an explicit candidate boundary: funding values goods before current relationship acquisition, avoiding a circular quantity → qualification → future fee → quantity definition. It does not freeze actual preferences. This boundary may exclude some relationship-motivated intentions and requires strategic comparison; no claim of global optimality outside the declared funded-quantity model is made.

Each per-quote vector is a coupled, resource-feasible company plan. Different quote queries are different counterfactuals: their quantities must not be added together as one funded basket or counted as incoming orders. The trace includes each complete `quoteVector`, `referenceDemands` at incumbent/cheapest reference quotes, and an independently optimized all-quotes `jointQuantities`/`jointGoods` comparison. The latter is one jointly feasible basket; the vector of per-market reference demands need not be.

The oracle uses the conditional distribution available to the whole observation group. It does not calculate each hidden demand state's intention separately and then let the realized state choose its own current action. It does not cache intentions across different conditional groups merely because their cash and inventory happen to match. All hypothetical searches count against the same explicit node budget.

## Rejected reference-only version

The first implementation fixed every other material to its incumbent quote, or cheapest quote if no incumbent existed. This loses joint opportunities when another input has a cheaper discovered alternative. It remains executable as `funding='continuation-reference-v1'` solely for comparison; `continuation` selects v2.

Counterexample: $5 cash; one A and one B produce an output sold for $5, with $0.50 conversion. A costs $1; incumbent B costs $2, and another B supplier offers $1. Two units of each are available.

- Fixing B at $2 while funding A authorizes only one A. Actual selection buys one A and one cheap B: $2 goods plus $0.50 conversion, $5 receipts, $2.50 return.
- Keeping other inputs' quotes flexible authorizes two A. Actual selection buys two A and two cheap B: $4 goods plus $1 conversion, $10 receipts, $5 return.

This is a structural defect in the reference-only decomposition, not a calibration issue. The v1 source and unsuccessful/intermediate test logs are preserved. The corrected version also checks 100 independently enumerated single-quote two-input cases with varied cash, inventory, basis, conversion, capacity and sales. In that test domain output prices keep the production ramp fully open, permitting an independent direct physical/cash calculation rather than reusing the oracle's production function.

## Exposed fee-avoidance incentive

The coupled model exposes a further consequence of using a feasible incumbent-quote intention for fee eligibility. It does not silently remove the unmatched-buffer action to conceal it.

Start with $7 and no inputs. One A plus one B makes an output selling for $10, with $0.25 conversion. A costs $1 now. B becomes available later: incumbent B costs $5, while an outsider costs $1. Switching costs $3 if the incumbent can fill its positive funded demand. One output can be sold; leftover inputs have zero terminal value.

| Current A purchase | Cash before B | Incumbent B funded quantity | Later goods/fee/conversion | Final cash return |
| --- | ---: | ---: | --- | ---: |
| One A | $6 | 1 | $1 outside B + $3 fee + $0.25 conversion | $4.75 |
| Two A | $5 | 0 | $1 outside B + $0 fee + $0.25 conversion | $6.75 |

With two A, $5 can buy the incumbent's goods but cannot fund their conversion. The incumbent intention is zero, so D2's positive-bid fee condition does not activate. One A remains unused, yet buying it improves the company's return by avoiding the larger transfer. The exact planner selects two A. With fees removed, it selects one A and returns $7.75.

This is a strategic counterexample, not a claim that the behavior is desirable. It arises from this continuation funding interpretation combined with the accepted waiver rule; changing D1/D2 silently would be inappropriate. Alternative funding boundaries and long-run incentive effects must be evaluated before adoption. Accounting still reconciles; no money is created by the strategy.

The initial hand calculation used a synthetic zero-conversion case and expected three A; the oracle returned two because its retained epsilon cash-cap guard blocks free production at exactly zero cash. Normalized world configuration requires a positive conversion factor. The final fixture above uses $0.25 conversion and explicitly demonstrates the incentive in that supported domain. The failed expectation is preserved in `continuation-funding-final-tests.log`; it is not presented as passing evidence or hidden by tuning production parameters.

## Evidence and remaining work

`20261012-continuation-funding-examples` contains complete inputs, outcomes, source hashes and a self-contained copy of the report/oracle/ledger source. It includes joint complements, the rejected reference-only comparison and the fee-incentive/no-fee control. `continuation-funding-positive-conversion-tests.log` passes 42 targeted tests, including the 100 exhaustive comparisons, conditional buffers, hidden demand, receipt timing, real future fees/rent, lots, node-budget failure and earlier ledger/oracle contracts.

This is still a small exhaustive reference model against supplied external scenarios. It is not integrated into population purchasing. Required next work includes an explicit response to the fee incentive, transaction-only versus inquiry feedback, controlled forecast probes, conditional supply scenarios, a scalable solver, and the remaining world, performance, UI and adoption gates. The explicit-callback oracle and current replenishment comparison retain their previous semantics; the new v2 rule does not silently change them.

The subsequent [fee-incentive sensitivity study](buying-behavior-v2-fee-incentives.md) compares a transfer-neutral funding alternative over 100 cases and demonstrates that it can reject useful fee-financed buffers. Neither elimination of one incentive nor solver correctness establishes model adoption.

## Stock carry-over in continuation scenarios

The oracle's optional [persistent-arrival supply mode](buying-behavior-v2-phase-oracle.md#persistent-supplier-inventory-and-explicit-arrivals) now deducts actual purchases from later offers. In a stock-relaxed funding query, additional hypothetical current units do not consume separately declared future arrivals; real current units do reduce later availability. This boundary is explicit and tested. It does not alter accepted D1/D2, whose availability checks use actual remaining stock at each real decision. The original independent-snapshot mode remains available for historical scenario reproduction and must not be described as conserving one supplier's inventory over time.

The [ownership audit](buying-behavior-v2-phase-oracle.md#ownership-scope-correction-from-the-authoritative-catalog) establishes that self-supply is unreachable under the current sector-restricted installations and complete recipe universe. Earlier notes listing it as unconditional implementation work were mistaken; it becomes relevant only if those model constraints change. Coupled resources and uncertainty across distinct owned products remain required.
