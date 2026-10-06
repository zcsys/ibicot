'use strict';
const assert=require('node:assert/strict');
const {createWorker}=require('./worker_harness');
const baseline=createWorker({t2FirmCount:100,endUserCount:1000,sigma:0});
const {cfg}=baseline.inspect(),M=baseline.model,scale=.00462962962962963;
const scaled=createWorker({...cfg,baseCost:cfg.baseCost*scale,
  manufacturingCostPerUnit:cfg.manufacturingCostPerUnit*scale,
  tier2ConversionCostScale:scale,procurementConversionReferenceScale:scale,
  procurementBasicReferenceCost:cfg.procurementBasicReferenceCost*scale,
  procurementCompoundReferenceCost:cfg.procurementCompoundReferenceCost*scale,
  taumin:cfg.taumin*scale,taumax:cfg.taumax*scale});
const S=scaled.inspect().W,C=scaled.inspect().cfg;
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-10,`${a} != ${b}`);
for(const p of M.T2_PRODUCTS) {
  const oldCost=M.initialTier2Cost(p,cfg),newCost=M.initialTier2Cost(p,C);
  near(newCost,oldCost*scale);
  const oldReference=M.referenceTier2Cost(p,cfg),newReference=M.referenceTier2Cost(p,C);
  near(newReference,oldReference*scale);
  const a=M.procurementProfile(p,cfg,oldReference),b=M.procurementProfile(p,C,newReference);
  near(b.quantityFactor*scale,a.quantityFactor);
  near(b.valuation,a.valuation*scale);
  near(b.quantityFactor*newCost*b.markup,a.quantityFactor*oldCost*a.markup);
}
assert.equal(C.initialCash,1000000);
assert.deepEqual(Array.from(S.t2Cash),Array.from(baseline.inspect().W.t2Cash),'Fixed minimum operating capital remains unchanged');
assert.deepEqual(Array.from(S.t2EqBook),Array.from(baseline.inspect().W.t2EqBook),'Plant book capital remains unchanged');
assert.equal(C.minWholesaleLot,1000);
// An economic quote below a cent remains expressible and above its actual cost.
const result=M.adaptivePrice({oldPrice:.005,unitCost:.004,profit:1,previousProfit:0,
  direction:1,sales:10,stock:100});
assert.ok(result.price>.005&&result.price<.01);
scaled.send({type:'player',tier:'T1',id:0,controller:'PLAYER',online:true,code:'W',price:.00912});
assert.equal(S.playerPrice[0],.00912);
for(let tick=0;tick<90;tick++)scaled.step();
assert.ok(S.t0Cash.every(x=>Number.isFinite(x)&&x>=0));
assert.ok(S.t2Cash.every(x=>Number.isFinite(x)&&x>=0));
assert.ok(S.t1FinBasis.some((x,i)=>S.t1Operates[i]&&x>0&&x<.01));
assert.ok(S.t2FinBasis.slice(0,S.t2LineCount).every(x=>x>=0&&x<1),'Actual conversion and input acquisition costs both scale');
assert.ok(S.t2Revenue.some(x=>x>0),'Scaled costs and quotes permit actual end purchases');
console.log('Variable-cost scaling: frozen benchmark compensation, unchanged capital, fractional-cent quotes and actual trading: ok');
