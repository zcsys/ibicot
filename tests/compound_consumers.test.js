'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const sum = a => a.reduce((n, x) => n + x, 0);
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-6, `${a} != ${b}`);
// Even abundant, free Tier 1 stock and stale material preferences cannot
// induce public orders. Only Tier 2 receipts enter consumer spending.
const worker = createWorker({t2FirmCount:1000,endUserCount:20000,consumerActivation:1});
const {W,cfg} = worker.inspect(), M = worker.model;
W.t1Fin.fill(1000); W.t1Price.fill(0.01);
W.endPreferredProduct.fill(4); W.endPreferredSupplier.fill(4);
for (let line=0;line<W.t2LineCount;line++) {
  W.t2Fin[line]=1000; W.t2Price[line]=1; W.t2FinBasis[line]=0.5;
}
const beforeStock=W.t1Fin.slice(), beforeCash=W.t1Cash.slice();
const counts=worker.kernel.clearEndUsers(W,cfg,M.PRODUCTS,M.T2_PRODUCTS,1);
assert.deepEqual(W.t1Fin,beforeStock); assert.deepEqual(W.t1Cash,beforeCash);
for(const name of ['endPotential','endActive','endFulfilled','endPriceLost','endStockUnmet'])
  assert.ok(W[name].slice(0,10).every(q=>q===0),name);
assert.ok(W.endLastMarket.every(m=>m===-1 || m>=10));
assert.ok(sum(W.endFulfilled)>0);
near(counts.consumerPayments,sum(W.t2Revenue));
near(sum(W.endFulfilled),sum(W.t2Sold));
near(sum(W.t2COGS),sum(W.t2Sold)*0.5);
// Actual million-human colony: material sales are exclusively business
// purchases. Purchase counters count transfers, not orders or input use.
const full=createWorker();
for(let tick=0;tick<2;tick++) {
  full.step(); const s=full.snapshot(), state=full.inspect();
  assert.equal(s.tiers.endUsers.population,1000000);
  assert.equal(s.colony.population,1000000);
  assert.equal(s.colony.immortal,true);
  assert.equal(s.colony.contract,'Infinity contract');
  assert.ok(s.products.every(p=>p.consumerVolume===0 && p.active===0));
  assert.ok(state.W.endLastMarket.every(m=>m===-1 || m>=10));
  near(s.tiers.t0.bought,s.tiers.t0.made);
  near(s.tiers.t1.bought,s.tiers.t0.sold);
  near(s.tiers.t2.bought,s.tiers.t1.sold);
  near(s.tiers.endUsers.revenue,s.tiers.t2.revenue);
  assert.ok(s.tiers.t2.bought>0 && s.tiers.t2.sold>0);
  for(const p of s.products) assert.equal(p.volume,p.intermediateVolume);
}
console.log('Tier 1 public demand is zero; Tier 2 public purchases and inter-tier bought counters: ok');
