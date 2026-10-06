'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({t2FirmCount: 1000, endUserCount: 20000});
const {W, cfg} = worker.inspect(), M = worker.model;
assert.equal(M.T2_SECTOR_DEFINITIONS.length, 10);
assert.ok(M.T2_SECTOR_DEFINITIONS.every(s => s.description && !('primaryMaterial' in s)));
assert.equal(new Set(M.T2_SECTORS).size, 10);
assert.equal(new Set(M.T2_PRODUCTS.map(p => p.name)).size, 200);
const obsolete = /Midbridge|Immortality|Infinity Contract|Service|Subscription|Membership/;
const initial = worker.snapshot();
for (const name of [...M.PRODUCTS.map(p=>p.name), ...M.T2_PRODUCTS.map(p=>p.name), ...M.T2_SECTORS,
  ...initial.t0Companies.map(c=>c.name), ...initial.companies.map(c=>c.name), ...initial.tier2Companies.rows.map(c=>c.name)])
  assert.ok(!obsolete.test(name), `Obsolete colony or service-market name: ${name}`);
for (const row of initial.tier2Industries) {
  const sector = M.T2_SECTOR_DEFINITIONS.find(s=>s.name === row.name);
  assert.equal(row.description, sector.description);
  assert.equal(row.products, M.T2_PRODUCTS.filter(p => p.sector === row.name).length);
}
// Exercise every authored recipe with one controlled line. Depriving its
// actual Tier 1 ingredients block it individually; restoring supply permits production.
assert.ok(W.t2LineProduct instanceof Uint16Array);
assert.ok(W.t2SectorProducts.includes(M.T2_PRODUCTS.length-1));
const line = W.t2FirmLines[0]; W.t2FirmLineCount[0] = 1;
for (const product of M.T2_PRODUCTS) {
  const primary = M.PRODUCTS.findIndex(p=>p.code===product.primaryMaterial);

  assert.ok(product.ingredients.some(([p])=>p===primary));
  const produce = blocked => {
    W.t2LineProduct[line] = product.id; W.t2Fin[line] = 0; W.t2Made[line] = 0;
    W.t2Price[line] = 1000; W.t2Cash[0] = 100000; W.t2Preferred.fill(-1);
    W.t2Raw.fill(0); W.t2T1Raw.fill(0); W.t1Fin.fill(0);
    for (let firm = 0; firm < 1000; firm++) {
      const material = Math.floor(firm / 100), i = firm * 10 + material;
      W.t1Price[i] = 2;
      W.t1Fin[i] = material === blocked ? 0 : 1000;
      W.t1FinBasis[i] = 1;
    }
    worker.kernel.tier2BuyMakePrice(W, {...cfg, t2FirmCount: 1}, M.PRODUCTS, [], M.T2_PRODUCTS, 1);
    return W.t2Made[line];
  };
  for (const [material] of product.ingredients)
    assert.equal(produce(material), 0, `${product.name} must depend on ${M.PRODUCTS[material].name}`);
  assert.ok(produce(-1) > 0, `${product.name} must produce when its inputs are restored`);
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
  if(input.supplier>=0) assert.ok(M.PRODUCTS.some(product => input.supplierName.startsWith(product.companyName + ' ')));
}
console.log('10 galactic sectors, 420 recipe input dependencies, sourcing and company names: ok');

// Product identity is one-to-one: names, codes and processed-input recipes are distinct.
// Expanded raw totals may coincide; unknown codes cannot control or add lines.
assert.equal(M.recipeKey({'W+A':1,F:1}),M.recipeKey({F:1,'W+A':1}));
assert.notEqual(M.recipeKey({'W+A':1,F:1}),M.recipeKey({F:2,'W+A':1}));
assert.equal(Object.keys(M.T2_PRODUCT_BY_CODE).length,200);
assert.equal(new Set(Object.values(M.T2_PRODUCT_BY_CODE)).size,200);
assert.equal(new Set(M.T2_PRODUCTS.map(p=>M.recipeKey(p.inputs))).size,200);
assert.equal(new Set(M.T2_RECIPE_POOL.map(p=>M.recipeKey(p.composition))).size,111);
for(const [i,p] of M.T2_PRODUCTS.entries()) {
  assert.equal(p.id,i);
  assert.ok(M.T2_CATALOGUE.some(r=>r.code===p.code&&r.recipeKey===p.recipeKey));
  assert.ok(!('aliases' in p));
  const independentlyExpanded={};
  for(const element of M.ELEMENTS) independentlyExpanded[element]=p.ingredients.reduce((n,[material,q])=>n+q*(M.PRODUCTS[material].inputs[element]||0),0);
  assert.deepEqual(p.composition,independentlyExpanded);
  assert.equal(Object.values(p.composition).reduce((a,b)=>a+b,0),p.complexity);
}
assert.equal(M.T2_PRODUCT_BY_CODE['T2-421'],undefined);
assert.equal(M.T2_PRODUCT_BY_CODE['T2-999'],undefined);
const robot=M.T2_PRODUCTS[worker.inspect().W.t2LineProduct[0]];
const robotLine=worker.inspect().W.t2LineProduct.subarray(0,worker.inspect().W.t2LineCount).indexOf(robot.id);
assert.ok(robotLine>=0);
const robotFirm=worker.inspect().W.t2LineFirm[robotLine];
worker.send({type:'player',tier:'T2',id:robotFirm,controller:'PLAYER',online:true,code:robot.code,price:10});
const beforeLines=worker.inspect().W.t2LineCount, beforeCash=worker.inspect().W.t2Cash[robotFirm];
worker.send({type:'buyEquipment',tier:'T2',id:robotFirm,code:'T2-999'});
assert.equal(worker.self.lastMessage.ok,false,'Unknown codes cannot create product lines');
worker.send({type:'player',tier:'T2',id:robotFirm,controller:'PLAYER',online:true,code:'T2-999',price:10});
assert.equal(worker.self.lastMessage.type,'actionResult');
assert.equal(worker.self.lastMessage.ok,false);
assert.match(worker.self.lastMessage.msg,/installed product/);
assert.equal(worker.inspect().W.t2LineCount,beforeLines);
assert.equal(worker.inspect().W.t2Cash[robotFirm],beforeCash);

// A high-ID physical good retains its recipe identity in actual purchases.
assert.equal(M.WORLD_STORY.name,'Robotic Space Generation');
assert.equal(M.WORLD_STORY.population,1000000);
assert.equal(M.WORLD_STORY.consumers,'External galactic procurement agents');
assert.match(M.WORLD_STORY.society,/Human civilization/);
assert.match(M.WORLD_STORY.purpose,/galactic war.*civilian life/);
assert.match(M.WORLD_STORY.demandScope,/healthcare.*learning hardware/);
// Civilian continuity and readiness remain physical applications of the same
// manufacturing pool, not new services, war events or demographic dynamics.
for(const name of ['Nutrient Synthesis Plant','Hospital Isolation Module',
  'Instruction Simulation Computer','Medical Imaging Scanner','Fleet Deflection Shield'])
  assert.ok(M.T2_CATALOGUE.some(p=>p.name===name && p.kind==='Good'),name);
const catalogueDoc=require('node:fs').readFileSync('spec/product_catalogue.md','utf8');
for(const product of M.T2_CATALOGUE)
  assert.ok(catalogueDoc.includes('| '+product.name+' |'),`${product.code}: documented catalogue name`);
assert.ok(!('immortal' in M.WORLD_STORY));
assert.ok(!('contract' in M.WORLD_STORY));
assert.ok(M.T2_PRODUCTS.every(p=>p.kind==='Good'));
const good=M.T2_PRODUCTS.find(p=>Number(p.code.slice(3))>255 && p.complexity===5);
const live=worker.inspect().W, population=worker.inspect().cfg.endUserCount;
live.t2Price.fill(Infinity); live.t2LineProduct[0]=good.id;
live.t2Price[0]=1; live.t2Fin[0]=1000000; live.t2FinBasis[0]=0.5;
live.t2Sold.fill(0); live.t2Revenue.fill(0); live.t2COGS.fill(0);
live.endBasket.fill(good.sectorIndex); live.endPreferredProduct.fill(10+good.id);
live.endPreferredSupplier.fill(0);
const result=worker.kernel.clearEndUsers(live,worker.inspect().cfg,M.PRODUCTS,M.T2_PRODUCTS,37);
assert.equal(live.t2LineProduct[0],good.id);
assert.ok(live.t2Sold[0]>0);
assert.equal(live.t2Revenue[0],live.t2Sold[0]);
assert.equal(live.t2COGS[0],live.t2Sold[0]*0.5);
assert.equal(live.t2Fin[0],1000000-live.t2Sold[0]);
assert.ok(result.consumerPayments>0);
assert.equal(worker.inspect().cfg.endUserCount,population);
assert.ok(!Object.keys(live).some(k=>/birth|death|aging|health/i.test(k)));
console.log('200 invented goods and 220 reserves, exhaustive recipe identities and stable catalogue codes above byte range: ok');
