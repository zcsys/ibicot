'use strict';
const assert = require('node:assert/strict');
const {createWorker}=require('./worker_harness');
// Actual buyer clearing: equal need weights, sharply different order rates.
// A no-purchase product must not lose its need share to a frequently bought one.
const w=createWorker({t2FirmCount:1000,endUserCount:20000,consumerActivation:1});
const {W,cfg}=w.inspect(),M=w.model;
assert.ok(W.endNeedProduct.every(p=>p===-1));
const products=M.T2_PRODUCTS.filter(p=>p.sectorIndex===0).slice(0,2);
const [unbought,frequent]=products;
W.t2SectorCount[0]=2;
W.t2SectorProducts[0]=unbought.id;W.t2SectorProducts[1]=frequent.id;
W.t2SectorProductWeight[0]=.5;W.t2SectorProductWeight[1]=1;
for(let buyer=0;buyer<cfg.endUserCount;buyer++) {
  W.endBasketCount[buyer]=2;W.endBasket[buyer*5]=0;W.endBasket[buyer*5+1]=1;
}
let a=0,b=0,salesA=0,salesB=0;
for(let tick=1;tick<=120;tick++) {
  for(let line=0;line<W.t2LineCount;line++) {
    W.t2Fin[line]=100000;
    W.t2Price[line]=W.t2LineProduct[line]===unbought.id?1e12:W.t2UnitCost[line]*1.25;
  }
  w.kernel.clearEndUsers(W,cfg,M.PRODUCTS,M.T2_PRODUCTS,tick);
  if(tick>60)for(let buyer=0;buyer<cfg.endUserCount;buyer++) {
    a+=W.endLastMarket[buyer]===10+unbought.id;
    b+=W.endLastMarket[buyer]===10+frequent.id;
  }
  salesA+=W.endFulfilled[10+unbought.id];salesB+=W.endFulfilled[10+frequent.id];
}
assert.equal(salesA,0);assert.ok(salesB>0);
assert.ok(Math.abs(a/(a+b)-.5)<.015,JSON.stringify({a,b,share:a/(a+b)}));
assert.ok(W.endNeedProduct.some(p=>p===10+unbought.id));
assert.ok(!W.endPreferredProduct.some(p=>p===10+unbought.id),'Unpurchased goods cannot earn supplier relationships');
assert.ok(W.endPreferredProduct.some(p=>p===10+frequent.id));
console.log(JSON.stringify({result:'PASS',needShare:a/(a+b),noPurchaseUnits:salesA,frequentUnits:salesB,rule:'Neutral need repetition; supplier relationships earned on fulfillment'}));
