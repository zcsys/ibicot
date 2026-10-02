'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { createWorker } = require('./worker_harness');
const config = { t2FirmCount: 1000, endUserCount: 20000 };
function digest(W) {
  const hash = crypto.createHash('sha256');
  for (const [name, array] of Object.entries(W)) {
    if (!array?.byteLength) continue;
    hash.update(name); hash.update(Buffer.from(array.buffer, array.byteOffset, array.byteLength));
  }
  return hash.digest('hex');
}
const worker = createWorker(config), { W, cfg } = worker.inspect(), model = worker.model;
for (let id = 0; id < cfg.endUserCount; id++) {
  const basket = W.endBasket.slice(id * 5, id * 5 + W.endBasketCount[id]);
  assert.ok(basket.length >= 2 && basket.length <= 5);
  assert.equal(new Set(basket).size, basket.length);
}
assert.ok(W.endPreferredSupplier.every((id) => id === -1));
for (let t = 0; t < 35; t++) worker.step();
for (let id = 0; id < cfg.endUserCount; id++) {
  assert.ok(W.endLastFulfilled[id] === 0 || W.endLastFulfilled[id] === W.endLastQ[id], 'Atomic order');
  const market = W.endLastMarket[id];
  if (market >= model.PRODUCTS.length) {
    const sector = model.T2_PRODUCTS[market - model.PRODUCTS.length].sectorIndex;
    assert.ok(W.endBasket.slice(id * 5, id * 5 + W.endBasketCount[id]).includes(sector), 'Need belongs to the basket');
  }
}
assert.ok(W.endPreferredSupplier.some((id) => id >= 0));
assert.ok(W.t2Rel.slice(0, W.t2LineCount).some((r) => r !== 0.5));
const firstDigest = digest(W);
worker.reset(config); for (let t = 0; t < 35; t++) worker.step();
assert.equal(digest(W), firstDigest, 'Reset must reproduce all numerical state');

// A takeover preserves the company balance sheet, portfolio and relationships.
const firm = 0, line = W.t2FirmLines[0], product = model.T2_PRODUCTS[W.t2LineProduct[line]];
const cash = W.t2Cash[firm], stock = W.t2Fin[line], supplier = W.t2Preferred.slice(0, 10);
worker.send({ type: 'select', tier: 'T2', id: firm });
assert.equal(worker.self.snapshot.selected.tier, 'T2');
worker.send({ type: 'player', tier: 'T2', id: firm, controller: 'PLAYER', online: true, code: product.code, price: 0.01 });
assert.equal(W.t2Cash[firm], cash); assert.equal(W.t2Fin[line], stock);
assert.deepEqual(W.t2Preferred.slice(0, 10), supplier);
assert.equal(W.t2Online[firm], 1); assert.equal(W.t2Controller[firm], 1);
assert.ok(W.t2Price[line] >= (W.t2FinBasis[line] || W.t2UnitCost[line]));
assert.equal(W.t2Controller[1], 0);
const purchase = model.T2_PRODUCTS.find((p) => p.complexity <= W.t2Capability[firm] &&
  model.relatedSector(W.t2Sector[firm], p.sectorIndex) && !worker.kernel.hasTier2Product(W, firm, p.id));
W.t2Cash[firm] = purchase.equipmentPrice * 2;
const beforeLines = W.t2LineCount, beforeBook = W.t2EqBook[firm];
worker.send({ type: 'buyEquipment', tier: 'T2', id: firm, code: purchase.code });
assert.equal(worker.self.lastMessage.ok, true);
assert.equal(W.t2LineCount, beforeLines + 1); assert.equal(W.t2Cash[firm], purchase.equipmentPrice);
assert.equal(W.t2EqBook[firm], beforeBook + purchase.equipmentPrice);
worker.send({ type: 'buyEquipment', tier: 'T2', id: firm, code: purchase.code });
assert.equal(worker.self.lastMessage.ok, false, 'Reject duplicate machinery');
assert.equal(W.t2LineCount, beforeLines + 1);
worker.send({ type: 'buyEquipment', tier: 'T2', id: 1, code: purchase.code });
assert.equal(worker.self.lastMessage.ok, false, 'Bots cannot use player purchase command');

// Material transactions preserve cash and transfer the exact inventory, basis,
// supplier sales, and relationship for both Tier 1 material complexities.
for (const [material, offer] of [[0, 10], [4, 4004]]) {
  const basic = material < 4, stockArray = W.t1Fin;
  const quoteArray = W.t1Price, supplierCash = W.t1Cash;
  const seller = Math.floor(offer / 10);
  stockArray[offer] = 2000; quoteArray[offer] = 2; W.t2Cash[firm] = 10000;
  const index = firm * (basic ? 4 : 10) + material, rawArray = basic ? W.t2Raw : W.t2T1Raw;
  const oldRaw = rawArray[index], oldSupplierCash = supplierCash[seller];
  const sales = W.t1Sold, revenues = W.t1Rev;
  const oldSales = sales[offer], oldRevenue = revenues[offer];
  const bought = worker.kernel.transferTier2Input(W, cfg, firm, material, offer, 12);
  assert.equal(bought, 12); assert.equal(rawArray[index] - oldRaw, bought);
  assert.equal(stockArray[offer], 2000 - bought);
  assert.equal(W.t2Cash[firm], 10000 - bought * 2);
  assert.equal(supplierCash[seller] - oldSupplierCash, bought * 2);
  assert.equal(sales[offer] - oldSales, bought);
  assert.ok(Math.abs(revenues[offer] - oldRevenue - bought * 2) < 1e-8, 'Exact payment within floating-point precision');
}

// Monthly expansion uses a full-month utilization observation, accepts only
// an adjacent eligible product, and does not expand a player-controlled firm.
W.t2Controller[firm] = 0; W.t2Cash[firm] = 1000000;
for (let slot = 0; slot < W.t2FirmLineCount[firm]; slot++) {
  const l = W.t2FirmLines[slot]; W.t2MonthlyCapacity[l] = 100; W.t2MonthSold[l] = 80;
}
const oldCount = W.t2FirmLineCount[firm]; worker.kernel.expandTier2Bots(W, cfg, model.T2_PRODUCTS, 60);
assert.equal(W.t2FirmLineCount[firm], oldCount + 1);

// Different schedulers use the identical tick; compare full state, not just a
// handful of dashboard metrics. Run Max starts with one time-bounded batch.
const fixed = createWorker(config), max = createWorker(config);
fixed.send({type:'run',mode:'fixed'}); fixed.send({type:'pause'});
max.send({type:'run',mode:'max'}); max.send({type:'pause'});
const count = max.inspect().tick;
while (fixed.inspect().tick < count) fixed.step();
assert.equal(digest(fixed.inspect().W), digest(max.inspect().W));
console.log('tier2 contract: ok');
