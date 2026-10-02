'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
const model = worker.model, { W, cfg } = worker.inspect(), initial = worker.snapshot();
assert.equal(initial.tiers.t1.equity, 56000000);
assert.equal(initial.companies.filter((c) => c.native.length === 1).length, 400);
for (const company of initial.companies) {
  const product = model.PRODUCTS.find((p) => p.code === company.native);
  assert.equal(company.cash, 5000);
  assert.equal(company.equity, product.complexity === 1 ? 20000 : 80000);
}
assert.equal(initial.tiers.t2.activeLines, 2500);
assert.ok(W.t2Capability.slice(0, cfg.t2FirmCount).every((c) => c >= 3 && c <= 5));
assert.equal(new Set(W.endPrimarySector.slice(0, cfg.endUserCount)).size, 10);
const oldLines = W.t2LineCount, oldCash = W.t2Cash[0], oldEquipment = W.t2EqBook[0];
for (const material of model.PRODUCTS) assert.throws(() => worker.kernel.addTier2Line(W, cfg, 0, material), /C-3 through C-5/);
assert.equal(W.t2LineCount, oldLines); assert.equal(W.t2Cash[0], oldCash); assert.equal(W.t2EqBook[0], oldEquipment);
for (let tick = 0; tick < 60; tick++) worker.step();
for (let market = 4; market < 10; market++) {
  assert.equal(W.endPotential[market], 0);
  assert.equal(W.endActive[market], 0);
  assert.equal(W.endFulfilled[market], 0);
}
assert.ok(W.endPreferredProduct.every((p) => p < 4 || p >= 10), 'No consumer relationship with C-2 intermediates');
for (let user = 0; user < cfg.endUserCount; user++) {
  const market = W.endLastMarket[user];
  assert.ok(market < 4 || market >= 10);
  const basket = W.endBasket.slice(user * 5, user * 5 + W.endBasketCount[user]);
  assert.ok(basket.every((sector) => sector < 10));
}
const snapshot = worker.snapshot();
for (const [index, product] of snapshot.products.entries()) {
  assert.equal(product.volume, product.consumerVolume + product.intermediateVolume);
  if (index >= 4) assert.ok(product.intermediateVolume > 0);
}
assert.equal(snapshot.endUsers.revenue, worker.inspect().sourceState.consumerPayments, 'Retail revenue excludes intermediate transactions');
assert.equal(snapshot.tier2Industries.length, 10);
assert.deepEqual(snapshot.tier2Complexity.map((row) => row.complexity), [3,4,5]);
assert.ok(Number.isFinite(snapshot.wholesaleAvg));
// Tier 1 buys C-2 equipment at the identical global complexity price.
W.t1Cash[0] = 200000;
worker.send({ type: 'player', tier: 'T1', id: 0, controller: 'PLAYER', online: true, code: 'W', price: 2 });
const cash = W.t1Cash[0], book = W.t1EqBook[0];
worker.send({ type: 'buyEquipment', tier: 'T1', id: 0, code: 'W+E' });
assert.equal(worker.self.lastMessage.ok, true);
assert.equal(W.t1Cash[0], cash - 75000); assert.equal(W.t1EqBook[0], book + 75000);
const beforeRejected = W.t1Cash[0];
worker.send({ type: 'buyEquipment', tier: 'T1', id: 0, code: model.T2_PRODUCTS[0].code });
assert.equal(worker.self.lastMessage.ok, false); assert.equal(W.t1Cash[0], beforeRejected);
console.log('tier boundaries and unified machinery: ok');
