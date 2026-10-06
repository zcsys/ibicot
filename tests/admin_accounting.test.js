'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const { createWorker } = require('./worker_harness');
// Small accounting fixture, never calibration evidence. Plenty of starting
// cash permits legitimate purchases without an artificial live cash injection.
const worker = createWorker({ t2FirmCount: 20, endUserCount: 200,
  retailInitialCash: 100000, consumerActivation: .1 });
worker.send({ type: 'setOwnershipEnforcement', enforced: false });
const { W } = worker.inspect(), M = worker.model;
const sum = array => array.reduce((total, value) => total + value, 0);
const cash = () => sum(W.t0Cash) + sum(W.t1Cash) + sum(W.t2Cash);
const initialCash = cash();
let tickInflows = 0, tickCostSinks = 0, tickEquipmentSinks = 0;
let maximumLedgerError = 0;
const receipts = [];
function reconcile(label) {
  const admin = worker.inspect().adminAccounting;
  const error = Math.abs(cash() - initialCash - tickInflows + tickCostSinks + tickEquipmentSinks + admin.equipmentSinks);
  maximumLedgerError = Math.max(maximumLedgerError, error);
  assert.ok(error < 1e-6, `${label}: cash ledger differs by ${error}`);
  assert.deepEqual(worker.snapshot().adminAccounting, admin, `${label}: snapshot ledger differs`);
}
function step(label) {
  worker.step();
  const state = worker.inspect().sourceState;
  tickInflows += state.consumerPayments; tickCostSinks += state.costSinks; tickEquipmentSinks += state.equipmentSinks;
  reconcile(label);
}
function purchase(tier, id, code, expectedSuccess, expectedCost = 0) {
  const beforeCash = cash(), beforeTick = worker.inspect().tick;
  const beforeSource = { ...worker.inspect().sourceState }, beforeTickSink = W.equipmentSinks;
  const beforeAdmin = worker.inspect().adminAccounting;
  worker.send({ type: 'buyEquipment', tier, id, code });
  const result = worker.self.lastMessage;
  assert.equal(result.type, 'equipmentResult'); assert.equal(result.ok, expectedSuccess);
  const receipt = result.receipt; receipts.push(receipt);
  assert.equal(receipt.tier, tier); assert.equal(receipt.companyId, id); assert.equal(receipt.productCode, code);
  assert.equal(receipt.sequence, beforeAdmin.sequence + 1);
  assert.equal(receipt.tick, beforeTick); assert.equal(worker.inspect().tick, beforeTick);
  assert.equal(receipt.equipmentSink, expectedCost); assert.equal(beforeCash - cash(), expectedCost);
  assert.equal(worker.inspect().adminAccounting.equipmentSinks, beforeAdmin.equipmentSinks + expectedCost);
  assert.equal(W.equipmentSinks, beforeTickSink, 'Admin payment contaminated a kernel tick counter');
  assert.deepEqual(worker.inspect().sourceState, beforeSource, 'Admin payment changed previous tick transactions');
  assert.deepEqual(worker.inspect().adminAccounting.lastEquipmentReceipt, receipt);
  reconcile(`${tier} ${expectedSuccess ? 'success' : 'rejection'}`);
}

// Purchase before the first tick must appear immediately, with no pending
// kernel equipment counter or following-tick credit.
worker.send({ type: 'player', tier: 'T1', id: 0, code: 'W', controller: 'PLAYER', price: 10 });
purchase('T1', 0, 'W+E', true, M.PRODUCTS[4].equipmentPrice);
purchase('T1', 0, 'W+E', false);
purchase('T1', 1, 'W+E', false); // Bot-owned firm.
purchase('T1', 0, 'W+F', false); // Insufficient remaining cash.
step('Tick after Tier 1 purchase');

worker.send({ type: 'select', tier: 'T2', id: 0 });
let company = worker.self.snapshot.selected;
worker.send({ type: 'player', tier: 'T2', id: 0, code: company.native,
  controller: 'PLAYER', online: true, price: company.price });
company = worker.self.snapshot.selected;
const route = company.eligibleEquipment[0];
const beforeEquity = company.equity;
purchase('T2', 0, route.code, true, route.price);
assert.equal(worker.snapshot().selected.equity, beforeEquity, 'A paid route changed book equity');
purchase('T2', 0, route.code, false);
purchase('T2', 0, 'T2-999', false);
purchase('T2', 1, company.native, false); // Bot-owned firm.
company = worker.snapshot().selected;
const secondRoute = company.eligibleEquipment[0];
purchase('T2', 0, secondRoute.code, true, secondRoute.price);
company = worker.snapshot().selected;
purchase('T2', 0, company.eligibleEquipment[0].code, false); // Insufficient remaining cash.
step('Tick after Tier 2 purchase');
step('Following actual tick');
assert.equal(worker.inspect().adminAccounting.equipmentSinks, 77000);
assert.equal(tickEquipmentSinks, 0, 'Manual payments were counted again on a later tick');

// A baseline recorded immediately after purchases needs only changes to the
// cumulative admin ledger; an existing total must not be counted again.
const afterPurchaseCash = cash(), afterPurchaseAdmin = worker.inspect().adminAccounting.equipmentSinks;
const beforeFlows = { tickInflows, tickCostSinks, tickEquipmentSinks };
step('Post-purchase audit baseline');
assert.ok(Math.abs(cash() - afterPurchaseCash - (tickInflows - beforeFlows.tickInflows) +
  (tickCostSinks - beforeFlows.tickCostSinks) + (tickEquipmentSinks - beforeFlows.tickEquipmentSinks) +
  worker.inspect().adminAccounting.equipmentSinks - afterPurchaseAdmin) < 1e-6);

const saved = worker.exportState(), resumed = createWorker(saved.state.cfg);
resumed.importState(saved);
assert.deepEqual(resumed.inspect().adminAccounting, worker.inspect().adminAccounting, 'Resume lost admin ledger');
const invalid = { ...saved, state: { ...saved.state, adminAccounting: { ...saved.state.adminAccounting, equipmentSinks: 1 } } };
assert.throws(() => resumed.importState(invalid), /receipt total differs/);
const snapshotLedger = worker.snapshot().adminAccounting;
snapshotLedger.equipmentSinks = 0; snapshotLedger.lastEquipmentReceipt.equipmentSink = 123;
assert.equal(worker.inspect().adminAccounting.equipmentSinks, 77000, 'Snapshot exposed mutable ledger');
assert.equal(worker.inspect().adminAccounting.lastEquipmentReceipt.equipmentSink, 0);
worker.send({ type: 'reset', cfg: saved.state.cfg });
assert.deepEqual(worker.inspect().adminAccounting, { equipmentSinks: 0, sequence: 0, lastEquipmentReceipt: null });
// Exercise separation when the preceding actual tick already contains a bot
// purchase. Seed only this mechanism fixture's monthly utilization evidence.
const bot = createWorker({ t2FirmCount: 10, endUserCount: 1, consumerActivation: 0 });
bot.send({ type: 'setOwnershipEnforcement', enforced: false });
const B = bot.inspect().W;
for (let tick = 0; tick < 29; tick++) bot.step();
B.t2MonthSold[B.t2FirmLines[0]] = 10000;
const botCash = () => sum(B.t0Cash) + sum(B.t1Cash) + sum(B.t2Cash);
const beforeBotTickCash = botCash();
bot.step();
const botTick = { ...bot.inspect().sourceState };
assert.equal(botTick.equipmentSinks, 1000, 'Bot expansion must remain a per-tick equipment sink');
assert.equal(bot.inspect().adminAccounting.equipmentSinks, 0, 'A bot purchase entered the admin ledger');
assert.ok(Math.abs(botCash() - beforeBotTickCash - botTick.consumerPayments + botTick.costSinks + botTick.equipmentSinks) < 1e-6);
bot.send({ type: 'select', tier: 'T2', id: 1 });
const botCompany = bot.self.snapshot.selected;
bot.send({ type: 'player', tier: 'T2', id: 1, code: botCompany.native, controller: 'PLAYER', price: botCompany.price });
const adminRoute = bot.self.snapshot.selected.eligibleEquipment[0], beforeManualCash = botCash();
bot.send({ type: 'buyEquipment', tier: 'T2', id: 1, code: adminRoute.code });
assert.equal(bot.self.lastMessage.ok, true);
assert.equal(beforeManualCash - botCash(), 1000);
assert.equal(B.equipmentSinks, 1000, 'Admin purchase overwrote preceding bot sink');
assert.deepEqual(bot.inspect().sourceState, botTick);
assert.equal(bot.inspect().adminAccounting.equipmentSinks, 1000);
bot.step();
assert.equal(bot.inspect().sourceState.equipmentSinks, 0, 'Earlier admin/bot purchases were counted again');
assert.equal(bot.inspect().adminAccounting.equipmentSinks, 1000);
const report = { status: 'passed; accounting-only action ledger, no price or allocation rule changes',
  scope: 'small regression fixture; not a financial calibration',
  protocolAddition: 'Immediate cumulative administrative equipment sinks and sequenced receipts; kernel sourceState remains per actual tick',
  sourceFingerprint: worker.sourceFingerprint, maximumLedgerError, botExpansionEquipmentSink: botTick.equipmentSinks, receipts };
if (process.env.ADMIN_ACCOUNTING_OUTPUT) fs.writeFileSync(process.env.ADMIN_ACCOUNTING_OUTPUT, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
