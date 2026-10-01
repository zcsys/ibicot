# Phase 0 canonical economic contract

This is the editable contract for the Phase 0 source kernel.

## Authority rule

The source implementation is the single authority for model behavior. New
rules are first specified here, implemented in readable source, and covered by
deterministic tests.

## Fixed topology

- Elements: Water, Earth, Fire, Air.
- Products: four single-element and six two-element products, defined in
  `engine/model.js`.
- Firms: 20 Tier 0 suppliers and 1,000 Tier 1 firms (100 per product cohort).
- Customers: 50,000 Tier 2 buyers, initially 50 attached to each Tier 1 firm.

## Tick order

1. Update each Gaia difficulty using a bounded mean-reverting deterministic
   process.
2. Produce Tier 0 inventory and update unit extraction cost.
3. Plan Tier 1 input purchases from finished-goods coverage and equipment
   capacity; transact purchases subject to cash, lot size, and supplier stock.
4. Manufacture finished goods subject to raw inputs, equipment, target stock,
   and manufacturing cash.
5. Price Tier 0 and Tier 1 offers using the functions in `engine/model.js`.
6. Clear the retail market with atomic orders; record demand, stock loss,
   revenue, COGS, and supplier relationship observations.
7. Update sales EMA. Every 30 ticks, update reliability from fulfillment,
   price stability, and availability.

## Economic invariants

- No inventory, cash, demand quantity, or reliability score may be negative.
- A transaction transfers equal and opposite cash and inventory value.
- Fulfilled quantity never exceeds desired quantity.
- A retail order is fulfilled completely or not at all.
- Tier 0 and Tier 1 price floors are cost plus `minMargin`.
- Given a seed, configuration, actions, and initial state, a source kernel
  must produce the same state on every run.

## Design decisions

Wholesale pricing responds to unfulfilled purchase requests. Tier 1 input
buyers are interleaved by cohort each tick, and an empty supplier is excluded
from input selection so another stocked supplier can serve the request.

Retail supplier selection uses the buyer relationship plus the best current
in-stock alternative; orders remain atomic. Changes to either behavior require
a scenario test. The source-engine test includes a 360-tick sustained-market
scenario: every product must retain effective-price demand and sales, and every
compound market must continue to produce and earn revenue.
