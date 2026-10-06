'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
require('../engine/model');
const M = global.Phase0Model;
// Expose the real private production function only in this isolated test
// compilation. No worker/harness/runner instrumentation or live rules change.
const source = fs.readFileSync(path.join(__dirname, '../engine/reference_kernel.js'), 'utf8');
assert.equal(source.split('Object.freeze({ zero, tick,').length, 2);
const root = { Phase0Model: M };
new Function('self', source.replace('Object.freeze({ zero, tick,', 'Object.freeze({ produceTier0, zero, tick,'))(root);
const produce = root.Phase0ReferenceKernel.produceTier0;
const E = M.ELEMENTS;
function fixture({ elements = [0,1,2,3], stock = [0,0,0,0], targets = [20000,20000,20000,20000],
  capacity = 10000, cash = 1e6, warehouse = 1e6, costs = [1,1,1,1], basis = [2,3,4,5] } = {}) {
  const cfg = { seed: 12345, capacity, targetInventory: 500000, maxInventory: warehouse,
    inventoryCoverageTicks: 1, minWholesaleLot: 1000, baseCost: 1, markup: .25 };
  const W = { costSinks: 0, difficulty: Float64Array.from(costs), t0Cash: new Float64Array(20),
    t0Inv: new Float64Array(80), t0InvBasis: new Float64Array(80), t0Cost: new Float64Array(80),
    t0Price: new Float64Array(80), t0DemandEMA: new Float64Array(80) };
  W.t0Cash.fill(1e6); W.t0Cash[0] = cash; W.t0Price.fill(7);
  for (let firm = 1; firm < 20; firm++) W.t0Inv[firm * 4] = Math.max(1000,Math.ceil(capacity * .1));
  for (const e of elements) { W.t0Inv[e] = stock[e]; W.t0InvBasis[e] = basis[e]; W.t0DemandEMA[e] = targets[e]; }
  const profiles = Array.from({ length: 20 }, (_, firm) => ({ elements: (firm === 0 ? elements : [0]).map(e => E[e]) }));
  return { W, cfg, profiles };
}
function run(options, tick = 1) {
  const { W, cfg, profiles } = fixture(options);
  const oldStock = W.t0Inv.slice(0, 4), oldBasis = W.t0InvBasis.slice(0, 4), oldCash = W.t0Cash[0];
  const prices = W.t0Price.slice(0, 4);
  produce(W, cfg, profiles, tick);
  const made = Array.from(W.t0Inv.subarray(0, 4), (stock, e) => stock - oldStock[e]);
  const spending = made.reduce((sum, quantity, e) => sum + quantity * W.difficulty[e], 0);
  const expectedTargets = profiles[0].elements.map(name => {
    const e = E.indexOf(name);
    return [e, M.finishedStockTarget({ salesEMA: W.t0DemandEMA[e], coverageTicks: cfg.inventoryCoverageTicks,
      bootstrapStock: Math.max(cfg.minWholesaleLot, Math.ceil(cfg.capacity * .1 / profiles[0].elements.length)),
      capacity: cfg.capacity, targetInventory: cfg.targetInventory / profiles[0].elements.length,
      maxInventory: cfg.maxInventory / profiles[0].elements.length })];
  });
  assert.ok(made.every(value => value >= -1e-9));
  assert.ok(made.reduce((a,b) => a+b, 0) <= cfg.capacity + 1e-9, 'Shared capacity exceeded');
  assert.ok(W.t0Inv.slice(0,4).reduce((a,b) => a+b,0) <= Math.max(cfg.maxInventory, oldStock.reduce((a,b) => a+b,0)) + 1e-9,
    'Shared warehouse exceeded or grandfathered stock destroyed');
  for (const [e,target] of expectedTargets) {
    assert.ok(W.t0Inv[e] <= Math.max(target, oldStock[e]) + 1e-9, 'Stock target exceeded');
    if (W.t0Inv[e] > 0) assert.ok(Math.abs(W.t0Inv[e] * W.t0InvBasis[e]
      - (oldStock[e] * oldBasis[e] + made[e] * W.difficulty[e])) < 1e-7, 'Production basis is incorrect');
  }
  assert.ok(W.t0Cash[0] >= -1e-9, 'Production spent unavailable cash');
  assert.ok(Math.abs(oldCash - W.t0Cash[0] - spending) < 1e-7, 'Cash debit differs from real production');
  assert.ok(Math.abs(W.costSinks - spending) < 1e-7, 'Cost sink differs from cash debit');
  assert.deepEqual(W.t0Price.slice(0,4), prices, 'Valid quotes changed during production');
  return { made, W, cfg };
}

// Tiny bootstrap deficits cannot lose every integer remainder to sustained
// large sibling deficits. Every material position must regain lot eligibility.
for (let e = 0; e < 4; e++) for (const missing of [1,2]) {
  const stock = [0,0,0,0], targets = [20000,20000,20000,20000];
  stock[e] = 1000 - missing; targets[e] = 1000;
  const first = run({ stock, targets });
  assert.ok(first.made[e] >= 1, 'Positive bootstrap route received no quantum');
  stock[e] = first.W.t0Inv[e];
  const second = run({ stock, targets }, 2);
  assert.ok(second.W.t0Inv[e] >= 1000, 'Bootstrap route remains undiscoverable after two ticks');
}
assert.deepEqual(run({ stock: [999,999,0,0], targets: [1000,1000,20000,20000] }).made, [1,1,4999,4999]);
assert.deepEqual(run({ stock: [999,998,0,0], targets: [1000,1000,20000,20000] }).made, [1,1,4999,4999]);
for (const targets of [[10000,10000,10000,10000], [3000,3000,3000,3000]])
  assert.deepEqual(run({ targets }).made, [2500,2500,2500,2500]);
assert.deepEqual(run({ targets: [4000,8000,12000,16000] }).made, [1000,2000,3000,4000]);
assert.deepEqual(run({ targets: [16000,12000,8000,4000] }).made, [4000,3000,2000,1000]);

// Profile permutation cannot alter allocation by actual material identity.
function permutations(values) {
  return values.length ? values.flatMap((value,index) => permutations(values.filter((_,i) => i !== index)).map(tail => [value,...tail])) : [[]];
}
for (const tick of [1,2,3,17]) {
  const options = { stock: [999,998,0,0], targets: [1000,1000,20000,20000] };
  const reference = run(options,tick).made;
  for (const elements of permutations([0,1,2,3])) assert.deepEqual(run({ ...options,elements },tick).made, reference);
}

// Rotation must service every active route equally with insufficient capacity
// and with a tied last remainder. Subsets cannot inherit raw-ID gap priority.
for (const elements of [[0,1,2,3], [0,3], [1,2,3]]) {
  const totals = [0,0,0,0];
  for (let tick = 0; tick < elements.length; tick++) {
    const made = run({ elements,capacity:1 },tick).made;
    assert.equal(made.reduce((a,b) => a+b,0),1);
    made.forEach((quantity,e) => totals[e] += quantity);
  }
  for (const e of elements) assert.equal(totals[e],1, 'Low capacity schedule favors one material');
}
const tiedTotals = [0,0,0,0];
for (let tick = 0; tick < 4; tick++) run({ capacity:5 },tick).made.forEach((quantity,e) => tiedTotals[e] += quantity);
assert.deepEqual(tiedTotals,[5,5,5,5], 'Remainder tie favors a material');

// Probe highly unequal positive deficits, including successive sub-unit
// quota reservations. Adequate funding/storage and >=4 units must give every
// integer route a unit without weakening shared constraints.
for (let index = 0; index < 200; index++) {
  const deficits = [1 + index % 3, 1 + index * 7 % 29, 1 + index * 41 % 701, 1000 + index * 131];
  const stock = deficits.map(deficit => Math.max(0, 1000 - deficit));
  const targets = deficits.map((deficit,e) => deficit + stock[e]);
  const made = run({ stock,targets,capacity:4 + index % 97 },index).made;
  assert.ok(made.every(quantity => quantity >= 1), 'A positive integer route was starved');
}

// Binding shared cash/storage, cost heterogeneity, fractional admin settings,
// unchanged quotes, and old acquisition basis all retain real accounting.
run({ warehouse:4003,stock:[1000,1000,1000,1000],targets:[5000,5000,5000,5000] });
run({ cash:5,costs:[1,2,3,4],capacity:10000 });
assert.deepEqual(run({ elements:[0,1],cash:2,targets:[10000,10000,0,0] }).made,[1,1,0,0],
  'A bulk route consumed cash which could fund all sibling quanta');
assert.deepEqual(run({ elements:[0,1,2],cash:11,costs:[1,5,5,1],targets:[10000,10000,10000,0] }).made,[1,1,1,0],
  'Heterogeneous costs starved an affordable quantum');
const cashLimited = run({ cash:20,costs:[1,9,9,9],capacity:10000 });
assert.ok(cashLimited.made.reduce((a,b) => a+b,0) > 2, 'Affordable alternatives did not receive clamped allocation');
run({ cash:20000.3,costs:[1,2,3,4],capacity:10000.5 });
run({ stock:[999.5,998.25,0,0],targets:[1000,1000,20000,20000],capacity:10000.5 });
for (const e of [0,1,2,3]) {
  const stock=[0,0,0,0],targets=[0,0,0,0]; stock[e]=999;targets[e]=1000;
  assert.equal(run({ elements:[e],stock,targets }).made[e],1, 'Narrow route cannot restore its lot');
}
console.log('Tier 0 apportionment: bootstrap eligibility, proportional bulk, neutral order/low capacity, shared limits and real basis accounting PASS');
