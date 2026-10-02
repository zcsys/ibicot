'use strict';
const assert=require('node:assert/strict');
const {createWorker}=require('./worker_harness');
const setup={t2FirmCount:1000,endUserCount:20000,capacity:0,sigma:0,consumerActivation:0,
  markup:0,compoundMarkupPremium:0};
// Same offers/capacities/preferences. Only buyers' ability to fund input orders
// differs. Offers start at cost, with no initial positive margin. No output is
// supplied: this isolates business stockout information.
const funded=createWorker(setup), unfunded=createWorker(setup);
const A=funded.inspect().W, B=unfunded.inspect().W;
B.t1Cash.fill(0);B.t2Cash.fill(0);
const initial=Array.from(A.t0Price), initialT1=Array.from(A.t1Price);
let requests0=0,requests1=0,empty0=0,empty1=0;
for(let tick=1;tick<=120;tick++) {
  funded.step();unfunded.step();
  requests0+=A.t0Demand.reduce((a,b)=>a+b,0);
  requests1+=A.t1Demand.reduce((a,b)=>a+b,0);
  empty0+=B.t0Demand.reduce((a,b)=>a+b,0);
  empty1+=B.t1Demand.reduce((a,b)=>a+b,0);
  assert.equal(A.t0Sold.reduce((a,b)=>a+b,0),0);
  assert.equal(A.t1Sold.reduce((a,b)=>a+b,0),0);
}
assert.ok(requests0>0 && requests1>0,'Affordable orders must reach empty extraction/material suppliers');
assert.equal(empty0+empty1,0,'Unfunded needs are not scarcity orders');
assert.ok(Array.from(A.t0Price).some((p,i)=>Number.isFinite(p)&&p>initial[i]),'Actual input scarcity changes posted extraction offers');
assert.ok(Array.from(A.t1Price).some((p,i)=>Number.isFinite(p)&&p>initialT1[i]),'Material stockout orders reach pricing');
for(let i=0;i<B.t0Price.length;i++)if(Number.isFinite(B.t0Price[i]))assert.equal(B.t0Price[i],initial[i]);

// Apply genuine input scarcity to a functioning market, then restore supply.
// Price and delivered quantity come from the same worker, not a synthetic curve.
const live=createWorker({t2FirmCount:1000,endUserCount:20000,sigma:0});
const control=createWorker({t2FirmCount:1000,endUserCount:20000,sigma:0});
for(let t=0;t<120;t++){live.step();control.step();}
const {W,cfg}=live.inspect();
const sum=a=>a.reduce((n,x)=>n+(Number.isFinite(x)?x:0),0);
const before=sum(W.t0Price), capacity=cfg.capacity;
cfg.capacity=0; W.t0Inv.fill(0);W.raw.fill(0);W.t2Raw.fill(0);
const C=control.inspect().W;
C.t0Inv.fill(0);C.raw.fill(0);C.t2Raw.fill(0);
let shortageOrders=0;
for(let t=0;t<120;t++){live.step();control.step();shortageOrders+=sum(W.t0Demand);}
const scarcePrice=sum(W.t0Price);
const abundantPrice=sum(C.t0Price);
assert.ok(shortageOrders>0);
assert.ok(scarcePrice>before,'Exhausting extraction capacity creates a price response');
assert.ok(scarcePrice>abundantPrice,'Scarce capacity raises price relative to the identical replenished control');
cfg.capacity=capacity;
let recoveredSales=0;
for(let t=0;t<120;t++){live.step();recoveredSales+=sum(W.t0Sold);}
assert.ok(recoveredSales>0,'Restored physical supply trades again');
console.log(JSON.stringify({scenario:'funded-stockout-scarcity-and-recovery',requests0,requests1,unfundedRequests:empty0+empty1,
  zeroMarkupStartingPriceSum:initial.reduce((n,p)=>n+(Number.isFinite(p)?p:0),0),
  zeroMarkupFundedPriceSum:sum(A.t0Price),zeroMarkupUnfundedPriceSum:sum(B.t0Price),
  beforePriceSum:before,abundantPriceSum:abundantPrice,scarcePriceSum:scarcePrice,recoveredSales}));

// The same installed workshops face either ordinary or greater activation of
// the same private consumer needs. No capacity, valuation, cost or margin rule
// changes. Actual quantity shortfalls must create a higher output offer.
const outputWorlds=[createWorker({t2FirmCount:1000,endUserCount:20000,sigma:0}),
  createWorker({t2FirmCount:1000,endUserCount:20000,sigma:0})];
for(let t=0;t<120;t++)for(const w of outputWorlds)w.step();
outputWorlds[1].inspect().cfg.consumerActivation=1;
const outputResults=[];
for(const w of outputWorlds) {
  let wanted=0,sold=0;
  for(let t=0;t<240;t++) {
    w.step();const S=w.inspect().W;
    wanted+=sum(S.endActive.slice(10));sold+=sum(S.endFulfilled.slice(10));
  }
  const S=w.inspect().W;let quote=0,contribution=0;
  for(let i=0;i<S.t2LineCount;i++) {
    quote+=S.t2Price[i];contribution+=S.t2Price[i]-(S.t2FinBasis[i]||S.t2UnitCost[i]);
  }
  outputResults.push({activation:w.inspect().cfg.consumerActivation,wanted,sold,fill:sold/wanted,
    meanQuote:quote/S.t2LineCount,meanContribution:contribution/S.t2LineCount});
}
const [ordinaryOutput,scarceOutput]=outputResults;
assert.ok(scarceOutput.fill<ordinaryOutput.fill && scarceOutput.wanted>scarceOutput.sold);
assert.ok(scarceOutput.meanQuote>ordinaryOutput.meanQuote,'Finite workshop supply produces higher offers under greater demand');
assert.ok(scarceOutput.meanContribution>ordinaryOutput.meanContribution,'The higher output offer is not merely higher input cost');
console.log(JSON.stringify({scenario:'same-workshops-greater-demand',ordinaryOutput,scarceOutput}));
