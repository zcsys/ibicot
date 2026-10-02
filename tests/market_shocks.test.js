'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker(), { W, cfg } = worker.inspect();
const fill = () => {
  const desired = W.endActive.reduce((a,b)=>a+b,0), fulfilled = W.endFulfilled.reduce((a,b)=>a+b,0);
  return desired ? fulfilled / desired : 0;
};
for (let i=0;i<120;i++) worker.step();
const baseline = fill(); assert.ok(baseline > 0.8);

// A real supply interruption drains stock across the chain. Cash is retained;
// this is a missing-material shock, not a reset or a consumer-demand rewrite.
worker.send({type:'applyConfig',cfg:{capacity:0}});
for (const name of ['t0Inv','raw','t1Fin','t2Raw','t2T1Raw','t2Fin']) W[name].fill(0);
for(let i=0;i<30;i++)worker.step();
const scarcity = fill(); assert.ok(scarcity < baseline * 0.25);
assert.ok(W.endStockUnmet.reduce((a,b)=>a+b,0)>0);
assert.ok(W.endPreferredSupplier.some((s)=>s>=0), 'Supply shocks retain relationships');
worker.send({type:'applyConfig',cfg:{capacity:worker.model.ECONOMY_DEFAULTS.capacity}});
for(let i=0;i<120;i++)worker.step();
const recovery=fill(); assert.ok(recovery>0.7 && recovery>scarcity);

// Run paired populations with identical needs and random streams. A broad
// final-good price shock must decrease Tier 2 desired quantity, without a cash
// affordability limit or any change to end-user preferences.
const prices = W.t2Price.slice(), ordinary={...cfg};
const preferredProducts = W.endPreferredProduct.slice(), preferredSuppliers = W.endPreferredSupplier.slice();
W.t2Fin.fill(1000); W.t1Fin.fill(1000);
worker.kernel.clearEndUsers(W, ordinary, worker.model.PRODUCTS, worker.model.T2_PRODUCTS, 500);
const baseDemand=W.endActive.slice(10).reduce((a,b)=>a+b,0);
W.endPreferredProduct.set(preferredProducts); W.endPreferredSupplier.set(preferredSuppliers);
W.t1Fin.fill(1000);
for(let line=0;line<W.t2LineCount;line++){W.t2Price[line]=prices[line]*8;W.t2Fin[line]=1000;}
worker.kernel.clearEndUsers(W, ordinary, worker.model.PRODUCTS, worker.model.T2_PRODUCTS, 500);
const expensiveDemand=W.endActive.slice(10).reduce((a,b)=>a+b,0);
assert.ok(expensiveDemand<baseDemand*0.3);
for(const name of ['t0Cash','t1Cash','t2Cash','t0Inv','t1Fin','t2Fin'])assert.ok(W[name].every((v)=>v>=0 && Number.isFinite(v)));
console.log(JSON.stringify({scenario:'supply-interruption-and-price-shock',population:cfg.endUserCount,firms:cfg.t2FirmCount,baseline,scarcity,recovery,baseDemand,expensiveDemand}));
