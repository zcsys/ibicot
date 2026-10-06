'use strict';
const assert=require('node:assert/strict');const {createWorker}=require('./worker_harness');
// Audit the actual population and company counts; no calibration rescaling.
const w=createWorker(),{W,cfg}=w.inspect(),M=w.model,K=w.kernel;
assert.equal(cfg.initialCash,1000000);assert.equal(cfg.t2FirmCount,61950);
assert.equal(W.t2LineCount,232000);
assert.ok(W.t0Cash.every(c=>c===1000000));
const incidence=Array(200).fill(0),capacity=Array(200).fill(0),firms=Array(10).fill(0),focus={};
for(let f=0;f<cfg.t2FirmCount;f++){
 firms[W.t2Sector[f]]++;focus[W.t2FirmLineCount[f]]=(focus[W.t2FirmLineCount[f]]||0)+1;
 const unique=new Set();
 for(let slot=0;slot<W.t2FirmLineCount[f];slot++){
  const line=W.t2FirmLines[f*M.T2_MAX_PRODUCTS_PER_FIRM+slot],p=M.T2_PRODUCTS[W.t2LineProduct[line]];
  assert.equal(p.sectorIndex,W.t2Sector[f]);assert.ok(!unique.has(p.id));unique.add(p.id);
  incidence[p.id]++;capacity[p.id]+=cfg.tier2CompanyCapacity/W.t2FirmLineCount[f];
 }
}
assert.deepEqual(firms,Array(10).fill(6195));
assert.deepEqual(focus,{1:200,2:1900,3:11400,4:48450});
assert.ok(incidence.every(n=>n===1160));
assert.ok(capacity.every(n=>Math.abs(n-1858.5)<1e-8));
// A compound unit consumes one storage unit, with ancestry counted separately.
const f=0,first=W.t2FirmLines[0];W.t2Raw[0]=2;W.t2T1Raw[4]=3;W.t2Fin[first]=4;
assert.equal(K.tier2InventoryUnits(W,f),9);
W.t2Raw[0]=0;W.t2Fin[first]=0;W.t2T1Raw[4]=59;
const supplier=400*10+4;W.t1Price[supplier]=2;W.t1Fin[supplier]=100;W.t1FinBasis[supplier]=1;W.t2Cash[f]=1000;
assert.equal(K.transferTier2Input(W,cfg,f,4,supplier,7),1);
assert.equal(K.tier2InventoryUnits(W,f),60);
assert.equal(K.transferTier2Input(W,cfg,f,4,supplier,7),0);
assert.throws(()=>K.addTier2Line(W,cfg,0,M.T2_PRODUCTS.find(p=>p.sectorIndex!==W.t2Sector[0]),false),/sector/);
// A shared output budget holds even when every installed line wants production.
const small=createWorker({t2FirmCount:1,endUserCount:1});const A=small.inspect();
A.W.t2Cash[0]=100000;A.W.t2Price.fill(1000);A.W.t1Fin.fill(10000);A.W.t1Price.fill(2);A.W.t1FinBasis.fill(1);
small.kernel.tier2BuyMakePrice(A.W,A.cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1);
assert.ok(A.W.t2Made.reduce((a,b)=>a+b,0)<=A.cfg.tier2CompanyCapacity);
assert.ok(small.kernel.tier2InventoryUnits(A.W,0)<=A.cfg.tier2InventoryCapacity);
console.log('Full-size symmetric sector portfolios; shared output and combined input/output inventory caps: ok');
