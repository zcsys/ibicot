'use strict';

const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');
const { createWorker } = require('./worker_harness');

const ticks = Number(process.env.SCENARIO_TICKS || 360);
const seeds = (process.env.SCENARIO_SEEDS || '12345').split(',').map(Number);
function totalCash(W) {
  let cash = 0;
  for (const array of [W.t0Cash, W.t1Cash, W.t2Cash]) for (const value of array) cash += value;
  return cash;
}
function invariant(W, cfg, model) {
  for (const name of ['t0Inv','t0Cash','raw','t1Fin','t1Cash','t2Cash','t2Raw','t2T1Raw','t2Fin'])
    for (const value of W[name]) assert.ok(Number.isFinite(value) && value >= -1e-7, `${name}: ${value}`);
  for (let line = 0; line < W.t2LineCount; line++) {
    assert.ok(W.t2Price[line] + 1e-8 >= (W.t2FinBasis[line] || W.t2UnitCost[line]));
    assert.ok(W.t2Rel[line] >= 0 && W.t2Rel[line] <= 1);
  }
  for (let firm = 0; firm < cfg.t2FirmCount; firm++) {
    const products = new Set();
    for (let slot = 0; slot < W.t2FirmLineCount[firm]; slot++) {
      const line = W.t2FirmLines[firm * model.T2_MAX_PRODUCTS_PER_FIRM + slot], product = model.T2_PRODUCTS[W.t2LineProduct[line]];
      assert.equal(W.t2LineFirm[line], firm);
      assert.equal(W.t2Sector[firm], product.sectorIndex);
      assert.ok(product.complexity <= W.t2Capability[firm]);
      assert.ok(!products.has(product.id)); products.add(product.id);
    }
  }
}

for (const seed of seeds) {
  const worker = createWorker({ seed }), { W, cfg } = worker.inspect(), model = worker.model;
  assert.equal(cfg.endUserCount, 1000000); assert.equal(cfg.t2FirmCount, 61950);
  const capabilities = [0, 0, 0, 0, 0], firmsPerProduct = new Uint32Array(model.T2_PRODUCTS.length);
  for (let firm = 0; firm < cfg.t2FirmCount; firm++) capabilities[W.t2Capability[firm] - 1]++;
  assert.deepEqual(capabilities, [0,0,0,0,61950]);
  for (let line = 0; line < W.t2LineCount; line++) firmsPerProduct[W.t2LineProduct[line]]++;
  assert.equal(W.t2LineCount, 232000);
  assert.ok(firmsPerProduct.every(n => n === 1160));
  assert.ok(W.endPreferredSupplier.every((n) => n === -1));
  invariant(W, cfg, model);
  const traded = new Uint32Array(model.T2_PRODUCTS.length), rolling = new Uint32Array(model.T2_PRODUCTS.length);
  const recentRevenue = new Float64Array(model.T2_PRODUCTS.length);
  let minimumFill = 1, totalSales = 0, complexSales = 0, worstTickMs = 0;
  const start = performance.now();
  for (let t = 1; t <= ticks; t++) {
    const previousCash = t % 30 === 0 ? totalCash(W) : 0, before = performance.now();
    worker.step(); worstTickMs = Math.max(worstTickMs, performance.now() - before);
    for (let line = 0; line < W.t2LineCount; line++) {
      const id = W.t2LineProduct[line], sold = W.t2Sold[line];
      traded[id] += sold; rolling[id] += sold; totalSales += sold;
      recentRevenue[id] += W.t2Revenue[line];
      if (model.T2_PRODUCTS[id].complexity === 5) complexSales += sold;
    }
    if (t % 30 === 0) {
      const state = worker.inspect().sourceState;
      const delta = totalCash(W) - previousCash;
      const expected = state.consumerPayments - state.costSinks - state.equipmentSinks;
      assert.ok(Math.abs(delta - expected) < 0.02, `Cash ledger mismatch at ${t}: ${delta} vs ${expected}`);
      let desired = 0, fulfilled = 0;
      for (const q of W.endActive) desired += q;
      for (const q of W.endFulfilled) fulfilled += q;
      if (t >= 120) minimumFill = Math.min(minimumFill, fulfilled / desired);
      assert.ok(fulfilled <= desired);
    }
    if (t % 360 === 0) {
      // Rare components can have intermittent sales while their supply chains
      // bootstrap. Require receipts over the same window as catalogue activity.
      for (const product of model.T2_PRODUCTS.filter(p => p.complexity === 5))
        assert.ok(recentRevenue[product.id] > 0, `Inactive C-5 product over 360 ticks: ${product.name}`);
      recentRevenue.fill(0);
      assert.ok(rolling.every((q) => q > 0), `Dead catalogue markets at tick ${t}`); rolling.fill(0);
      invariant(W, cfg, model);
      console.log(`seed ${seed}, tick ${t}, ${((performance.now()-start)/t).toFixed(1)} ms/tick`);
    }
  }
  const snapshot = worker.snapshot();
  assert.ok(traded.every((q) => q > 0));
  assert.ok(minimumFill > 0.5, `Persistent fill rate ${minimumFill}`);
  // Complexity reduces unit orders per market. C-5 occupies 120 of 200
  // markets, so its aggregate share cannot be compared with a fixed 20% cap.
  const unitsByComplexity = [3,4,5].map(complexity => {
    const markets = model.T2_PRODUCTS.filter(p => p.complexity === complexity);
    const units = markets.reduce((n,p) => n + traded[p.id], 0);
    return { complexity, markets: markets.length, units,
      unitsPerMarketPerTick: units / markets.length / ticks };
  });
  assert.ok(unitsByComplexity.every(b => b.unitsPerMarketPerTick > 0));
  assert.ok(unitsByComplexity[0].unitsPerMarketPerTick > unitsByComplexity[1].unitsPerMarketPerTick &&
    unitsByComplexity[1].unitsPerMarketPerTick > unitsByComplexity[2].unitsPerMarketPerTick,
    `Unit orders must decrease per market as complexity rises: ${JSON.stringify(unitsByComplexity)}`);
  assert.equal(snapshot.tier2Products.filter(p=>p.complexity===5).length,model.T2_COMPLEXITY_COUNTS[4]);
  if (ticks % 360) for (const product of model.T2_PRODUCTS.filter(p => p.complexity === 5))
    assert.ok(recentRevenue[product.id]>0, `Inactive C-5 product in final partial window: ${product.name}`);
  console.log(JSON.stringify({seed,ticks,lines:W.t2LineCount,minimumFill,complexShare:complexSales/totalSales,
    unitsByComplexity,
    averageTickMs:(performance.now()-start)/ticks,worstTickMs,allProductsTraded:true}));
}
