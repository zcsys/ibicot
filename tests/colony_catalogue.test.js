'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({t2FirmCount: 1000, endUserCount: 20000});
const {W, cfg} = worker.inspect(), M = worker.model;
assert.equal(M.T2_SECTOR_DEFINITIONS.length, 10);
assert.deepEqual(M.T2_SECTOR_DEFINITIONS.map(s => s.primaryMaterial), M.PRODUCTS.map(p => p.code));
assert.equal(new Set(M.T2_SECTORS).size, 10);
assert.equal(new Set(M.T2_PRODUCTS.map(p => p.name)).size, 60);
const obsolete = /Coolant|Propellant|Orbital|Plasma|Hull|Cryogenic|Fleet|Regolith|Ceres|Kuiper|Helios|Arcana|Alchemy/;
const initial = worker.snapshot();
for (const name of [...M.PRODUCTS.map(p=>p.name), ...M.T2_PRODUCTS.map(p=>p.name), ...M.T2_SECTORS,
  ...initial.t0Companies.map(c=>c.name), ...initial.companies.map(c=>c.name), ...initial.tier2Companies.rows.map(c=>c.name)])
  assert.ok(!obsolete.test(name), `Obsolete colony-economy name: ${name}`);
for (const row of initial.tier2Industries) {
  const sector = M.T2_SECTOR_DEFINITIONS.find(s=>s.name === row.name);
  assert.equal(row.primaryMaterial, M.PRODUCTS.find(p=>p.code===sector.primaryMaterial).name);
  assert.equal(row.products, M.T2_PRODUCTS.filter(p => p.sector === row.name).length);
}
// Exercise every authored recipe with one controlled line. Depriving its
// designated Tier 1 cohort blocks it; restoring that cohort permits production.
const line = W.t2FirmLines[0]; W.t2FirmLineCount[0] = 1;
for (const product of M.T2_PRODUCTS) {
  const primary = M.PRODUCTS.findIndex(p=>p.code===product.primaryMaterial);
  assert.equal(product.primaryMaterial, M.T2_SECTOR_DEFINITIONS[product.sectorIndex].primaryMaterial);
  assert.ok(product.ingredients.some(([p])=>p===primary));
  const produce = blocked => {
    W.t2LineProduct[line] = product.id; W.t2Fin[line] = 0; W.t2Made[line] = 0;
    W.t2Price[line] = 1000; W.t2Cash[0] = 100000; W.t2Preferred.fill(-1);
    W.t2Raw.fill(0); W.t2T1Raw.fill(0); W.t1Fin.fill(0);
    for (let firm = 0; firm < 1000; firm++) {
      const material = Math.floor(firm / 100), i = firm * 10 + material;
      W.t1Price[i] = 2;
      W.t1Fin[i] = blocked && material === primary ? 0 : 1000;
      W.t1FinBasis[i] = 1;
    }
    worker.kernel.tier2BuyMakePrice(W, {...cfg, t2FirmCount: 1}, M.PRODUCTS, [], M.T2_PRODUCTS, 1);
    return W.t2Made[line];
  };
  assert.equal(produce(true), 0, `${product.name} must depend on its primary cohort`);
  assert.ok(produce(false) > 0, `${product.name} must produce when its cohort is restored`);
}
// Real multi-firm tick: all ten Tier 1 cohorts supply fabricators and reported
// supplier relationships point at Tier 1, including C-1 refined materials.
worker.reset({t2FirmCount:1000,endUserCount:20000});
for(let t=0;t<36;t++) worker.step();
const s = worker.snapshot();
assert.ok(s.products.every(p=>p.intermediateVolume>0));
for(const sector of M.T2_SECTORS) assert.ok(s.tier2Industries.some(row=>row.name===sector));
worker.send({type:'select',tier:'T2',id:0});
assert.ok(worker.self.snapshot.selected.inputs.length>0);
for(const input of worker.self.snapshot.selected.inputs) {
  assert.equal(input.sourceTier,'T1');
  if(input.supplier>=0) assert.equal(input.supplierId,Math.floor(input.supplier/10));
  if(input.supplier>=0) assert.match(input.supplierName,/Refinery/);
}
console.log('10 colony sectors, 60 mandatory cohort dependencies, sourcing and company names: ok');

// Product identity is one-to-one: names, codes, recipes and expanded raw
// compositions are all distinct. Obsolete codes cannot control or add lines.
assert.equal(M.recipeKey({'W+A':1,F:1}),M.recipeKey({F:1,'W+A':1}));
assert.notEqual(M.recipeKey({'W+A':1,F:1}),M.recipeKey({F:2,'W+A':1}));
assert.equal(Object.keys(M.T2_PRODUCT_BY_CODE).length,60);
assert.equal(new Set(Object.values(M.T2_PRODUCT_BY_CODE)).size,60);
assert.equal(new Set(M.T2_PRODUCTS.map(p=>M.recipeKey(p.inputs))).size,60);
assert.equal(new Set(M.T2_PRODUCTS.map(p=>M.recipeKey(p.composition))).size,60);
for(const [i,p] of M.T2_PRODUCTS.entries()) {
  assert.equal(p.code,'T2-'+String(i+1).padStart(3,'0'));
  assert.ok(!('aliases' in p));
  const independentlyExpanded={};
  for(const element of M.ELEMENTS) independentlyExpanded[element]=p.ingredients.reduce((n,[material,q])=>n+q*(M.PRODUCTS[material].inputs[element]||0),0);
  assert.deepEqual(p.composition,independentlyExpanded);
  assert.equal(Object.values(p.composition).reduce((a,b)=>a+b,0),p.complexity);
}
assert.equal(M.T2_PRODUCT_BY_CODE['T2-061'],undefined);
assert.equal(M.T2_PRODUCT_BY_CODE['T2-073'],undefined);
const yoga=M.T2_PRODUCTS.find(p=>p.name==='Yoga Pants');
const yogaLine=worker.inspect().W.t2LineProduct.subarray(0,worker.inspect().W.t2LineCount).indexOf(yoga.id);
assert.ok(yogaLine>=0);
const yogaFirm=worker.inspect().W.t2LineFirm[yogaLine];
worker.send({type:'player',tier:'T2',id:yogaFirm,controller:'PLAYER',online:true,code:yoga.code,price:10});
const beforeLines=worker.inspect().W.t2LineCount, beforeCash=worker.inspect().W.t2Cash[yogaFirm];
worker.send({type:'buyEquipment',tier:'T2',id:yogaFirm,code:'T2-073'});
assert.equal(worker.self.lastMessage.ok,false,'Obsolete codes cannot create product lines');
worker.send({type:'player',tier:'T2',id:yogaFirm,controller:'PLAYER',online:true,code:'T2-073',price:10});
assert.equal(worker.self.lastMessage.type,'actionResult');
assert.equal(worker.self.lastMessage.ok,false);
assert.match(worker.self.lastMessage.msg,/installed product/);
assert.equal(worker.inspect().W.t2LineCount,beforeLines);
assert.equal(worker.inspect().W.t2Cash[yogaFirm],beforeCash);

// Immortality is an ordinary, stock-backed public purchase. The contract is
// story metadata; it adds no demographic or health dynamics to the kernel.
const care=M.T2_PRODUCT_BY_CODE[M.COLONY_STORY.healthcareProductCode];
assert.equal(care.name,'Immortality Treatment');
assert.equal(care.sector,'Healthcare & Wellness');
assert.equal(M.COLONY_STORY.population,1000000);
assert.equal(M.COLONY_STORY.immortal,true);
assert.equal(M.COLONY_STORY.contract,'Infinity contract');
const live=worker.inspect().W, population=worker.inspect().cfg.endUserCount;
live.t2Price.fill(Infinity); live.t2LineProduct[0]=care.id;
live.t2Price[0]=1; live.t2Fin[0]=1000000; live.t2FinBasis[0]=0.5;
live.t2Sold.fill(0); live.t2Revenue.fill(0); live.t2COGS.fill(0);
live.endBasket.fill(care.sectorIndex); live.endPreferredProduct.fill(10+care.id);
live.endPreferredSupplier.fill(0);
const result=worker.kernel.clearEndUsers(live,worker.inspect().cfg,M.PRODUCTS,M.T2_PRODUCTS,37);
assert.ok(live.t2Sold[0]>0);
assert.equal(live.t2Revenue[0],live.t2Sold[0]);
assert.equal(live.t2COGS[0],live.t2Sold[0]*0.5);
assert.ok(result.consumerPayments>0);
assert.equal(worker.inspect().cfg.endUserCount,population);
assert.ok(!Object.keys(live).some(k=>/birth|death|aging|health/i.test(k)));
console.log('60 distinct codes, input recipes and elemental compositions; ordinary immortality purchases: ok');
