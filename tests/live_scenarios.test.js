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
      const line = W.t2FirmLines[firm * 5 + slot], product = model.T2_PRODUCTS[W.t2LineProduct[line]];
      assert.equal(W.t2LineFirm[line], firm);
      assert.ok(model.relatedSector(W.t2Sector[firm], product.sectorIndex));
      assert.ok(product.complexity <= W.t2Capability[firm]);
      assert.ok(!products.has(product.id)); products.add(product.id);
    }
  }
}

for (const seed of seeds) {
  const worker = createWorker({ seed }), { W, cfg } = worker.inspect(), model = worker.model;
  assert.equal(cfg.endUserCount, 1000000); assert.equal(cfg.t2FirmCount, 50000);
  const capabilities = [0, 0, 0, 0, 0], firmsPerProduct = new Uint32Array(model.T2_PRODUCTS.length);
  for (let firm = 0; firm < cfg.t2FirmCount; firm++) capabilities[W.t2Capability[firm] - 1]++;
  assert.deepEqual(capabilities, [0,0,30000,15000,5000]);
  for (let line = 0; line < W.t2LineCount; line++) firmsPerProduct[W.t2LineProduct[line]]++;
  assert.ok(firmsPerProduct.every((n) => n >= 100));
  assert.ok(W.endPreferredSupplier.every((n) => n === -1));
  invariant(W, cfg, model);
  const traded = new Uint32Array(120), rolling = new Uint32Array(120);
  let minimumFill = 1, totalSales = 0, complexSales = 0, worstTickMs = 0;
  const start = performance.now();
  for (let t = 1; t <= ticks; t++) {
    const previousCash = t % 30 === 0 ? totalCash(W) : 0, before = performance.now();
    worker.step(); worstTickMs = Math.max(worstTickMs, performance.now() - before);
    for (let line = 0; line < W.t2LineCount; line++) {
      const id = W.t2LineProduct[line], sold = W.t2Sold[line];
      traded[id] += sold; rolling[id] += sold; totalSales += sold;
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
      assert.ok(rolling.every((q) => q > 0), `Dead catalogue markets at tick ${t}`); rolling.fill(0);
      invariant(W, cfg, model);
      console.log(`seed ${seed}, tick ${t}, ${((performance.now()-start)/t).toFixed(1)} ms/tick`);
    }
  }
  const snapshot = worker.snapshot();
  assert.ok(traded.every((q) => q > 0));
  assert.ok(minimumFill > 0.5, `Persistent fill rate ${minimumFill}`);
  assert.ok(complexSales > 0 && complexSales / totalSales < 0.2);
  assert.ok(snapshot.tier2Products.filter((p) => p.complexity === 5).every((p) => p.revenue > 0));
  console.log(JSON.stringify({seed,ticks,lines:W.t2LineCount,minimumFill,complexShare:complexSales/totalSales,
    averageTickMs:(performance.now()-start)/ticks,worstTickMs,allProductsTraded:true}));
}
