'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');

const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
const M = worker.model;
const { W } = worker.inspect();

const firstCode = (id) => {
  const line = W.t2FirmLines[id * M.T2_MAX_PRODUCTS_PER_FIRM + 0];
  return M.T2_PRODUCTS[W.t2LineProduct[line]].code;
};

// Initial ownership: start with a Tier 1 license, no house.
worker.snapshot();
assert.deepEqual(worker.self.snapshot.ownership.licenses, ['T1']);
assert.equal(worker.self.snapshot.ownership.house, null);

// Pick two Tier 2 firms in different sectors.
const firmA = 0;
const sectorA = W.t2Sector[firmA];
let firmB = -1;
for (let i = 1; i < 1000; i++) if (W.t2Sector[i] !== sectorA) { firmB = i; break; }
assert.ok(firmB >= 0, 'expected a second sector');
const sectorB = W.t2Sector[firmB];
assert.notEqual(sectorA, sectorB);

// 1. T2 control is blocked without a Tier 2 license.
worker.send({ type: 'player', tier: 'T2', id: firmA, code: firstCode(firmA), controller: 'PLAYER', price: 100, online: true });
assert.equal(worker.self.lastMessage.type, 'actionResult');
assert.equal(worker.self.lastMessage.ok, false);
assert.match(worker.self.lastMessage.msg, /license/);

// 2. Buy the Tier 2 license.
worker.send({ type: 'buyLicense', tier: 'T2' });
assert.equal(worker.self.lastMessage.type, 'licenseResult');
assert.equal(worker.self.lastMessage.ok, true);
assert.deepEqual(worker.self.lastMessage.licenses, ['T1', 'T2']);

// 3. Control the first T2 firm (single sector, no house needed yet).
worker.send({ type: 'player', tier: 'T2', id: firmA, code: firstCode(firmA), controller: 'PLAYER', price: 100, online: true });
assert.equal(worker.self.lastMessage.type, 'snapshot');

// 4. A second sector is blocked without a holding company.
worker.send({ type: 'player', tier: 'T2', id: firmB, code: firstCode(firmB), controller: 'PLAYER', price: 100, online: true });
assert.equal(worker.self.lastMessage.type, 'actionResult');
assert.equal(worker.self.lastMessage.ok, false);
assert.match(worker.self.lastMessage.msg, /house|holding company/);

// 5. Found a house.
worker.send({ type: 'foundHouse', name: 'House Atlas' });
assert.equal(worker.self.lastMessage.type, 'houseResult');
assert.equal(worker.self.lastMessage.ok, true);

// 6. The second sector now succeeds.
worker.send({ type: 'player', tier: 'T2', id: firmB, code: firstCode(firmB), controller: 'PLAYER', price: 100, online: true });
assert.equal(worker.self.lastMessage.type, 'snapshot');

// 7. Snapshot ownership reflects licenses and house.
worker.snapshot();
assert.deepEqual(worker.self.snapshot.ownership.licenses, ['T1', 'T2']);
assert.equal(worker.self.snapshot.ownership.house.name, 'House Atlas');
assert.equal(worker.self.snapshot.ownership.houseFoundingCost, M.PROGRESSION_DEFAULTS.houseFoundingCost);
assert.equal(worker.self.snapshot.ownership.accounting.licensesSpent, M.PROGRESSION_DEFAULTS.licenseCosts.T2);

// 8. The Tier 0 license is not for sale.
worker.send({ type: 'buyLicense', tier: 'T0' });
assert.equal(worker.self.lastMessage.type, 'licenseResult');
assert.equal(worker.self.lastMessage.ok, false);
assert.match(worker.self.lastMessage.msg, /not for sale/);

// 9. Releasing a firm is never gated.
worker.send({ type: 'player', tier: 'T2', id: firmB, code: firstCode(firmB), controller: 'BOT', price: 100, online: false });
assert.equal(worker.self.lastMessage.type, 'snapshot');

console.log('ownership structure: ok');
