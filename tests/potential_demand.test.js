'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({t2FirmCount:100,endUserCount:10000,consumerActivation:1,
  tier2DemandFactor:.1,procurementBaseMarkup:300,procurementMarkupPremium:0,sigma:0});
const {W,cfg} = worker.inspect(), M = worker.model;
let potential=0, expected=0, visits=0;
for(let tick=1;tick<=60;tick++) {
  worker.kernel.clearEndUsers(W,cfg,M.PRODUCTS,M.T2_PRODUCTS,tick);
  for(let market=10;market<W.endPotential.length;market++) {
    assert.equal(W.endPotential[market],W.endActive[market]+W.endPriceLost[market]);
    assert.equal(W.endActive[market],W.endFulfilled[market]+W.endStockUnmet[market]);
    potential+=W.endPotential[market];
  }
  for(let buyer=0;buyer<cfg.endUserCount;buyer++) {
    const product=M.T2_PRODUCTS[W.endLastMarket[buyer]-10];
    expected+=W.endQMax[buyer]*M.procurementProfile(product,cfg,W.t2ReferenceCost[product.id]).quantityFactor;
    visits++;
  }
}
assert.ok(expected>20,'Enough independently rounded fractional needs for a meaningful check');
assert.ok(Math.abs(potential-expected)<6*Math.sqrt(expected),`Physical wishlist ${potential} agrees with expectation ${expected}`);
assert.ok(potential<visits/100,'A fractional need does not count as a full potential unit on every visit');

// The optional experiment waits for actual physical inquiries, rather than
// interpreting a calendar timeout with no market as evidence of rejection.
const patient=createWorker({t2FirmCount:100,endUserCount:1000,consumerActivation:0,sigma:0,
  researchPriceMinimumOpportunities:10,researchPriceMinimumPotentialOrders:20});
const P=patient.inspect().W, opening=P.t2Price[0];
P.t2LearnTicks[0]=100000;
for(let tick=0;tick<60;tick++)patient.step();
assert.equal(P.t2Price[0],opening);
assert.equal(P.t2LearnPotentialOpportunity[0],0);
P.t2LearnPotentialOpportunity[0]=20;
for(let tick=0;tick<30;tick++)patient.step();
assert.ok(P.t2Price[0]<opening,'Positive no-price inquiries allow an overpriced stocked offer to explore');
assert.equal(P.t2LearnOpportunity[0],0,'Exploration does not require paid orders when prices suppress a whole market');
assert.equal(worker.inspect().cfg.researchPriceMinimumPotentialOrders,0,'Physical-inquiry confidence experiment stays off by default');
console.log('Physical demand: coupled rounding, price/stock identities and optional sparse-order confidence: ok');
