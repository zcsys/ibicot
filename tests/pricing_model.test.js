'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({t2FirmCount:1000,endUserCount:20000}), M=worker.model;

// Economic outcome tests: the seller knows only its own realized results.
// Linear inverse demand has a known profit optimum, used only by the test.
function learn(start, { value=100, cost=10, capacity=Infinity, periods=400 }={}) {
  let price=start, direction=1, previousProfit=NaN, stepScale=1;
  const path=[];
  for(let t=0;t<periods;t++) {
    const sales=Math.min(capacity,Math.max(0,100*(value-price)));
    const profit=(price-cost)*sales;
    const next=M.adaptivePrice({oldPrice:price,unitCost:cost,profit,previousProfit,direction,sales,stock:10000,stepScale});
    path.push(price); price=next.price; direction=next.direction; stepScale=next.stepScale; previousProfit=profit;
  }
  return {price,path};
}
for(const start of [20,80,130]) {
  const result=learn(start);
  assert.ok(Math.abs(result.price-55)<3,`Discovery from ${start}: ${result.price}`);
}
const costly=learn(80,{cost:30}); assert.ok(Math.abs(costly.price-65)<3);
const stronger=learn(55,{value:140}); assert.ok(Math.abs(stronger.price-75)<4);
const scarcity=learn(55,{capacity:2000}); assert.ok(Math.abs(scarcity.price-80)<4);
const expansion=learn(scarcity.price,{capacity:8000}); assert.ok(Math.abs(expansion.price-55)<3);
// Price outcomes are not tied to a normal markup, consumer value or ceiling.
const base={oldPrice:12.5,unitCost:10,profit:10,previousProfit:9,direction:1,sales:3,stock:6};
assert.equal(M.adaptivePrice({...base,normalMargin:0,vmax:0.01}).price,
  M.adaptivePrice({...base,normalMargin:10,vmax:1000}).price);
assert.equal(M.adaptivePrice({...base,k:0}).price,base.oldPrice);
for(const scale of [.1,10,1000]) {
  const scaled=M.adaptivePrice({...base,oldPrice:base.oldPrice*scale,unitCost:base.unitCost*scale,
    profit:base.profit*scale,previousProfit:base.previousProfit*scale});
  assert.ok(Math.abs(scaled.price-M.adaptivePrice(base).price*scale)<1e-8*scale);
}
assert.ok(M.adaptivePrice({...base,profit:0,sales:0,stock:6}).price<base.oldPrice);
assert.equal(M.adaptivePrice({...base,profit:0,sales:0,stock:0}).price,base.oldPrice);
assert.equal(M.adaptivePrice({...base,unitCost:30}).price>=30,true);
const atCost=M.adaptivePrice({...base,oldPrice:10,profit:0,previousProfit:0,direction:-1});
assert.equal(atCost.price,10); assert.equal(atCost.direction,1);
assert.equal(M.adaptivePrice({...base,oldPrice:10,profit:0,previousProfit:0,sales:0,stock:0}).price,10,
  'No higher-than-cost quote is mandated without any market information');
const missing=M.adaptivePrice({...base,sales:0,stock:0,demand:5,available:0,direction:-1});
assert.ok(missing.price>base.oldPrice,'Actual unfilled orders make an empty supplier try a higher quote');
assert.ok(M.adaptivePrice({...base,sales:0,stock:0,demand:0,available:0,direction:-1}).price===base.oldPrice);
assert.equal(M.adaptivePrice({...base,sales:0,stock:0,demand:5,available:0,k:0}).price,base.oldPrice);
const reversal=M.adaptivePrice({...base,profit:8});
assert.equal(reversal.stepScale,.5,'Reverse direction with a smaller experiment');
// A narrow profitable interval previously produced a cost/overpriced cycle.
const narrow=learn(10.10,{cost:10,value:10.10,periods:400});
const narrowProfit=(p)=>(p-10)*Math.max(0,100*(10.10-p));
const narrowAverage=narrow.path.slice(-100).reduce((n,p)=>n+narrowProfit(p),0)/100;
assert.ok(narrowAverage>0.20,'Discover useful profit in an interval narrower than the old step');

// Costly production affects initial offers, not buyers' private values.
const expensive=createWorker({t2FirmCount:1000,endUserCount:20000,baseCost:4,markup:2});
const A=worker.inspect().W,B=expensive.inspect().W;
assert.deepEqual(A.endChoke,B.endChoke); assert.deepEqual(A.endQMax,B.endQMax);
assert.ok(B.t2Price[0]>A.t2Price[0]);
for(const W of [A,B]) {
  W.t1Fin.fill(1000); W.t2Fin.fill(1000); W.t1Price.fill(2); W.t2Price.fill(10);
}
worker.kernel.clearEndUsers(A,worker.inspect().cfg,M.PRODUCTS,M.T2_PRODUCTS,123);
expensive.kernel.clearEndUsers(B,expensive.inspect().cfg,M.PRODUCTS,M.T2_PRODUCTS,123);
assert.deepEqual(A.endActive,B.endActive,'Equal offers face equal demand despite different cost/starting-markup assumptions');

// An unfunded-production shock must not be treated as zero customer demand.
worker.reset({...worker.inspect().cfg,capacity:0});
const {W,cfg}=worker.inspect();
W.t0Inv.fill(0);W.raw.fill(0);W.t1Fin.fill(0);W.t2Raw.fill(0);W.t2T1Raw.fill(0);W.t2Fin.fill(0);
W.t2DemandEMA.fill(0);
worker.step();
assert.equal(W.t2Sold.reduce((a,b)=>a+b,0),0);
assert.ok(W.t2Demand.reduce((a,b)=>a+b,0)>0);
for(let line=0;line<W.t2LineCount;line++)
  assert.ok(Math.abs(W.t2DemandEMA[line]-cfg.alpha*W.t2Demand[line])<1e-9);
assert.equal(W.t2SalesEMA.reduce((a,b)=>a+b,0),0,'Observed requests must not inflate reported realized sales');

// Complete recipes are evaluated before cash is committed to input purchases.
const cautious=createWorker({t2FirmCount:1000,endUserCount:20000});
const C=cautious.inspect().W, before=C.t2Cash.slice();
C.t0Inv.fill(10000); C.t1Fin.fill(100); C.t2Price.fill(.01);
cautious.kernel.tier2BuyMakePrice(C,cautious.inspect().cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1);
assert.deepEqual(C.t2Cash,before,'No new input spending for an unprofitable output quote');
assert.equal(C.t2Made.reduce((a,b)=>a+b,0),0);
assert.equal(C.t2Raw.reduce((a,b)=>a+b,0)+C.t2T1Raw.reduce((a,b)=>a+b,0),0);
console.log('pricing: independent valuations, price discovery, demand/cost/capacity shifts, censored orders and recipe economics: ok');
