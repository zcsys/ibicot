'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
const { W, cfg } = worker.inspect();
worker.send({ type: 'select', tier: 'T2', id: cfg.t2FirmCount - 1 });
for (let t = 0; t < 35; t++) { worker.step(); worker.publish(); }
const snapshot = worker.snapshot();
worker.send({type:'tier2Query',search:snapshot.selected.name});
assert.equal(worker.self.snapshot.tier2Companies.total,1,'Company search uses the displayed corporate name');
assert.equal(worker.self.snapshot.tier2Companies.rows[0].id,snapshot.selected.id);
worker.send({type:'tier2Query',search:''});
const sum = (rows, key) => rows.reduce((total, row) => total + row[key], 0);
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < Math.max(1e-6, Math.abs(expected) * 1e-10), `${actual} != ${expected}`);
assert.equal(snapshot.tier2Industries.length, 10);
assert.equal(snapshot.tier2Complexity.length, 3);
assert.equal(sum(snapshot.tier2Industries, 'products'), worker.model.T2_PRODUCTS.length);
assert.equal(sum(snapshot.tier2Cohorts, 'firms'), cfg.t2FirmCount);
assert.equal(sum(snapshot.tier2Industries, 'lines'), W.t2LineCount);
for (const key of ['capacity','made','sold','revenue','cogs','grossProfit']) {
  near(sum(snapshot.tier2Industries, key), snapshot.tiers.t2[key]);
  near(sum(snapshot.tier2Complexity, key), snapshot.tiers.t2[key]);
  near(sum(snapshot.tier2Cohorts, key), snapshot.tiers.t2[key]);
}
near(sum(snapshot.tier2Cohorts, 'cash'), snapshot.tiers.t2.cash);
near(sum(snapshot.tier2Cohorts, 'equity'), snapshot.tiers.t2.equity);
near(sum(snapshot.tier2Industries, 'active'), snapshot.tiers.t2.desired);
near(sum(snapshot.tier2Industries, 'fulfilled'), snapshot.tiers.t2.fulfilled);
near(sum(snapshot.tier2Industries, 'readyStock'), snapshot.tiers.t2.finished);
near(snapshot.tiers.t2.stockCoverage, snapshot.tiers.t2.finished /
  W.t2SalesEMA.subarray(0, W.t2LineCount).reduce((sum, x) => sum + x, 0));
assert.equal(snapshot.tiers.t2.tradingFirms360, W.t2LastSaleTick.subarray(0, cfg.t2FirmCount)
  .reduce((count, last) => count + (last > 0 && snapshot.tick - last < 360), 0));
for (const row of [...snapshot.tier2Industries, ...snapshot.tier2Complexity, ...snapshot.tier2Products]) {
  for (const key of ['utilization','fillRate','margin','reliability']) assert.ok(Number.isFinite(row[key]) && row[key] >= 0 && row[key] <= 1);
  near(row.margin, row.revenue ? row.grossProfit / row.revenue : 0);
}
const company = snapshot.selected;
near(sum(company.products, 'capacity'), company.capacity);
near(sum(company.products, 'revenue'), company.revenue);
near(sum(company.inputs, 'stock'), company.raw);
for (const input of company.inputs) {
  let consumed = 0, capacityNeed = 0;
  for (const line of company.products) {
    const product = worker.model.T2_PRODUCTS.find((p) => p.code === line.code);
    for (const [material, quantity] of product.ingredients) if (worker.model.PRODUCTS[material].name === input.name) {
      consumed += line.made * quantity; capacityNeed += line.capacity * quantity;
    }
  }
  assert.equal(input.consumed, consumed); assert.equal(input.capacityNeed, capacityNeed);
  near(input.value, input.stock * input.basis);
  if (input.supplier >= 0) {
    assert.ok(input.supplierName);
    assert.ok(Number.isFinite(input.supplierPrice) && input.supplierPrice > 0);
  }
}
const oldHistoryLength = snapshot.analyticsHistory.length, oldCompanyLength = snapshot.tier2CompanyHistory.length;
for (let i = 0; i < 5; i++) worker.send({ type: 'tier2Query', sort: 'utilization', descending: true });
assert.equal(worker.self.snapshot.analyticsHistory.length, oldHistoryLength, 'Queries must not duplicate chart ticks');
assert.equal(worker.self.snapshot.tier2CompanyHistory.length, oldCompanyLength);
for (const [index, row] of worker.self.snapshot.tier2Companies.rows.entries())
  if (index) assert.ok(row.utilization <= worker.self.snapshot.tier2Companies.rows[index - 1].utilization);
worker.send({ type: 'select', tier: 'T2', id: 0 });
assert.equal(worker.self.snapshot.tier2CompanyHistory.length, 1);
assert.ok(worker.self.snapshot.tier2CompanyHistory.every((row) => row.id === 0));
worker.send({ type: 'select', tier: 'T1', id: 0 });
assert.equal(worker.self.snapshot.tier2CompanyHistory.length, 0);
worker.send({ type: 'select', tier: 'T2', id: 0 });
for (let t = 0; t < 250; t++) { worker.step(); worker.publish(); }
assert.equal(worker.self.snapshot.tier2CompanyHistory.length, 240);
assert.equal(worker.self.snapshot.analyticsHistory.length, 240);
assert.equal(new Set(worker.self.snapshot.analyticsHistory.map((point) => point.tick)).size, 240);
worker.reset({ t2FirmCount: 1000, endUserCount: 20000 });
assert.ok(W.t2LastSaleTick.every((last) => last === 0));
assert.equal(worker.self.snapshot.analyticsHistory.length, 1);
assert.ok(worker.self.snapshot.tier2CompanyHistory.length <= 1);
assert.ok(!Object.hasOwn(snapshot, 'consumers'));
console.log('tier2 analytics: ok');
