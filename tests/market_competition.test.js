'use strict';
const assert=require('node:assert/strict');
const {createWorker}=require('./worker_harness');
// Isolate the actual consumer-clearing phase. Identical buyers, posted offers
// and feasible shelf stocks differ only in one seller's quote/availability.
const worlds=Array.from({length:3},()=>createWorker({t2FirmCount:1000,endUserCount:20000}));
const chosen=Array.from(worlds[0].inspect().W.t2LineProduct).findIndex(id=>id===0);
assert.ok(chosen>=0);
const outcomes=[];
for(const [scenario,w] of worlds.entries()) {
  const {W,cfg}=w.inspect(),M=w.model;
  for(let line=0;line<W.t2LineCount;line++) {
    W.t2FinBasis[line]=W.t2UnitCost[line];
    W.t2Price[line]=W.t2UnitCost[line]*1.5;
  }
  if(scenario>0)W.t2Price[chosen]=W.t2UnitCost[chosen]*1.2;
  let units=0,unmet=0,initialStock=0;
  for(let tick=1;tick<=60;tick++) {
    for(let line=0;line<W.t2LineCount;line++) W.t2Fin[line]=2*M.T2_PRODUCTS[W.t2LineProduct[line]].capacity;
    for(let i=0;i<W.t1Fin.length;i++)W.t1Fin[i]=W.t1Operates[i]?16:0;
    if(scenario===2)W.t2Fin[chosen]=0;
    initialStock+=W.t2Fin[chosen];
    w.kernel.clearEndUsers(W,cfg,M.PRODUCTS,M.T2_PRODUCTS,1000+tick);
    units+=W.endFulfilled[10];unmet+=W.endStockUnmet[10];
    for(let line=0;line<W.t2LineCount;line++)assert.ok(W.t2Fin[line]>=0);
    assert.equal(W.endActive[10],W.endFulfilled[10]+W.endStockUnmet[10]);
  }
  outcomes.push({sold:W.t2Sold[chosen],orders:W.t2Demand[chosen],profit:W.t2Revenue[chosen]-W.t2COGS[chosen],
    marketUnits:units,unmet,initialStock});
}
const [ordinary,undercut,stockout]=outcomes;
assert.ok(ordinary.sold>0 && undercut.sold>ordinary.sold*1.5,JSON.stringify(outcomes));
assert.ok(undercut.sold<=undercut.initialStock,'Cheaper quotes do not create free inventory');
assert.equal(stockout.sold,0);assert.ok(stockout.orders>0,'A sold-out cheap seller still observes attempted orders');
assert.ok(stockout.marketUnits>0,'Other discovered suppliers serve stockout buyers');
assert.ok(stockout.marketUnits>undercut.marketUnits*.7,JSON.stringify(outcomes));
console.log(JSON.stringify({scenario:'actual-undercut-and-stockout',ordinary,undercut,stockout}));
